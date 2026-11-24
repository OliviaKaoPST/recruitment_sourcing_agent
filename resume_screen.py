"""Tool 2 — Resume parser + JD matcher + explainable ranking.

Reads a folder of resumes (.txt / .pdf / .docx), extracts skills via the taxonomy,
scores each against a JD config, and writes a ranked CSV with a reason column
(so a recruiter can defend every ranking to a hiring manager).

Score (0-100):
  50  must-have coverage
  20  nice-to-have coverage
  20  TF-IDF cosine similarity to JD text (catches skills outside the taxonomy)
  10  years-of-experience fit

Usage:
  python resume_screen.py --resumes samples --jd samples/jd_cuda.json --out ranked.csv
"""
import argparse
import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

from skills_taxonomy import TAXONOMY

STOP = set("the a an and or of to in for with on at by is are be as from this that we you our will your".split())


# ---------- loading ----------
def read_resume(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    if ext == ".docx":
        import docx
        return "\n".join(p.text for p in docx.Document(str(path)).paragraphs)
    return ""


# ---------- extraction ----------
def find_skills(text: str):
    low = text.lower()
    found = {}
    for canon, aliases in TAXONOMY.items():
        hits = 0
        for al in aliases:
            pat = r"(?<![a-z0-9+#])" + re.escape(al.lower()) + r"(?![a-z0-9+#])"
            hits += len(re.findall(pat, low))
        if hits:
            found[canon] = hits
    return found


def years_experience(text: str):
    nums = [int(n) for n in re.findall(r"(\d{1,2})\+?\s*(?:years|yrs|年)", text.lower())]
    return max(nums) if nums else None


def email_phone(text: str):
    email = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    phone = re.search(r"(?:\+?886|0)9\d{2}[- ]?\d{3}[- ]?\d{3}|\+?\d[\d -]{8,14}\d", text)
    return (email.group(0) if email else ""), (phone.group(0) if phone else "")


def location_flag(text: str, targets):
    low = text.lower()
    return any(t.lower() in low for t in targets)


# ---------- tf-idf ----------
def tokens(text):
    return [w for w in re.findall(r"[a-z0-9+#]+|[一-鿿]", text.lower()) if w not in STOP]


def tfidf_vectors(docs):
    toks = [tokens(d) for d in docs]
    df = Counter(w for t in toks for w in set(t))
    n = len(docs)
    vecs = []
    for t in toks:
        tf = Counter(t)
        vecs.append({w: (c / max(len(t), 1)) * (math.log((1 + n) / (1 + df[w])) + 1) for w, c in tf.items()})
    return vecs


def cosine(a, b):
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# ---------- scoring ----------
def score_all(resumes: dict, jd: dict):
    jd_text = jd["description"]
    names = list(resumes)
    vecs = tfidf_vectors([jd_text] + [resumes[n] for n in names])
    jd_vec, rvecs = vecs[0], vecs[1:]
    rows = []
    for name, rv in zip(names, rvecs):
        text = resumes[name]
        skills = find_skills(text)
        must, nice = jd["must"], jd.get("nice", [])
        m_hit = [s for s in must if s in skills]
        n_hit = [s for s in nice if s in skills]
        m_cov = len(m_hit) / len(must) if must else 0
        n_cov = len(n_hit) / len(nice) if nice else 0
        sim = cosine(jd_vec, rv)
        yrs = years_experience(text)
        lo, hi = jd.get("years_range", [0, 99])
        if yrs is None:
            yfit = 0.5
        elif lo <= yrs <= hi:
            yfit = 1.0
        else:
            gap = (lo - yrs) if yrs < lo else (yrs - hi)
            yfit = max(0.0, 1 - gap / 5)
        score = 50 * m_cov + 20 * n_cov + 20 * min(sim * 3, 1) + 10 * yfit  # sim*3: rescale small tf-idf cosines
        email, phone = email_phone(text)
        in_loc = location_flag(text, jd.get("locations", []))
        reason = (f"must {len(m_hit)}/{len(must)}"
                  + (f" (missing: {', '.join(s for s in must if s not in m_hit)})" if len(m_hit) < len(must) else "")
                  + f"; nice {len(n_hit)}/{len(nice)}; yrs={yrs if yrs is not None else 'n/a'}; sim={sim:.2f}"
                  + ("; in target location" if in_loc else "; location unclear"))
        rows.append({
            "candidate": name, "score": round(score, 1), "must_hit": "|".join(m_hit),
            "nice_hit": "|".join(n_hit), "years": yrs if yrs is not None else "",
            "in_target_location": in_loc, "email": email, "phone": phone, "reason": reason,
        })
    return sorted(rows, key=lambda r: -r["score"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resumes", required=True)
    ap.add_argument("--jd", required=True)
    ap.add_argument("--out", default="ranked.csv")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()

    jd = json.loads(Path(a.jd).read_text(encoding="utf-8"))
    resumes = {}
    for p in sorted(Path(a.resumes).iterdir()):
        if p.suffix.lower() in {".txt", ".pdf", ".docx"} and not p.name.startswith("jd"):
            resumes[p.stem] = read_resume(p)
    rows = score_all(resumes, jd)

    with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"{'rank':<5}{'candidate':<22}{'score':<7}reason")
    for i, r in enumerate(rows[: a.top], 1):
        print(f"{i:<5}{r['candidate']:<22}{r['score']:<7}{r['reason']}")
    print(f"\nSaved -> {a.out}")


if __name__ == "__main__":
    main()
