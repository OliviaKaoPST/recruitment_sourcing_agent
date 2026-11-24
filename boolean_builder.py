"""Tool 1 — Boolean / X-ray search string generator.

Turns a role family (or custom must/nice list) into search strings for:
  - LinkedIn Recruiter / Sales Navigator keyword box
  - Google X-ray (site:linkedin.com/in) — for public profiles only
  - GitHub user search qualifiers
Includes Taiwan location variants and synonym expansion from the taxonomy.

Usage:
  python boolean_builder.py --role cuda_engineer --location taiwan
  python boolean_builder.py --must cuda "gpu architecture" --nice pytorch hpc
"""
import argparse
from skills_taxonomy import TAXONOMY, ROLE_PRESETS

LOCATIONS = {
    "taiwan": ["Taiwan", "Taipei", "Hsinchu", "新竹", "台北", "Zhubei", "竹北", "Taichung", "Tainan"],
    "india": ["India", "Bengaluru", "Bangalore", "Hyderabad", "Pune"],
    "singapore": ["Singapore"],
    "china": ["Shanghai", "Shenzhen", "Beijing"],
}

TITLE_SYNONYMS = ["engineer", "developer", "architect", "scientist", "researcher", "工程師"]


def q(term: str) -> str:
    return f'"{term}"' if " " in term or "/" in term else term


def or_group(terms):
    terms = sorted(set(terms), key=lambda s: (len(s), s))
    return "(" + " OR ".join(q(t) for t in terms) + ")" if len(terms) > 1 else q(terms[0])


def expand(skill: str):
    return TAXONOMY.get(skill, [skill])


def build(must, nice, location=None, exclude=None):
    must_groups = [or_group(expand(s)) for s in must]
    nice_group = or_group([a for s in nice for a in expand(s)]) if nice else ""
    parts = must_groups[:]
    if nice_group:
        parts.append(nice_group)
    core = " AND ".join(parts)
    titles = or_group(TITLE_SYNONYMS)
    loc = or_group(LOCATIONS[location]) if location else ""
    neg = ""
    if exclude:
        neg = " NOT " + or_group(exclude)

    linkedin = f"{core} AND {titles}" + (f" AND {loc}" if loc else "") + neg
    xray = f'site:linkedin.com/in {core}' + (f" {loc}" if loc else "") + ' -"open to work" -intitle:recruiter -intitle:"talent"'
    strict = " AND ".join(must_groups) + (f" AND {loc}" if loc else "")
    return {
        "linkedin_broad": linkedin,
        "linkedin_strict_must_only": strict,
        "google_xray": xray,
    }


def github_qualifiers(must, location):
    lang_map = {"c++": "C++", "python": "Python", "cuda": "Cuda", "rtl design": "Verilog",
                "design verification": "SystemVerilog", "linux kernel": "C"}
    langs = [lang_map[m] for m in must if m in lang_map]
    loc = {"taiwan": "Taiwan", "india": "India", "singapore": "Singapore", "china": "China"}.get(location, "")
    qs = []
    for lang in langs or [""]:
        parts = []
        if lang:
            parts.append(f"language:{lang}")
        if loc:
            parts.append(f"location:{loc}")
        parts.append("repos:>5 followers:>10")
        qs.append(" ".join(parts))
    return qs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=ROLE_PRESETS.keys())
    ap.add_argument("--must", nargs="*", default=[])
    ap.add_argument("--nice", nargs="*", default=[])
    ap.add_argument("--location", choices=LOCATIONS.keys())
    ap.add_argument("--exclude", nargs="*", default=["intern", "student"])
    a = ap.parse_args()

    must, nice = a.must, a.nice
    if a.role:
        must = must or ROLE_PRESETS[a.role]["must"]
        nice = nice or ROLE_PRESETS[a.role]["nice"]
    if not must:
        ap.error("give --role or --must")

    for name, s in build(must, nice, a.location, a.exclude).items():
        print(f"\n## {name}\n{s}")
    print("\n## github_user_search_qualifiers")
    for s in github_qualifiers(must, a.location):
        print(s)


if __name__ == "__main__":
    main()
