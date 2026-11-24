"""Tool 3 — Public-signal sourcing via the official GitHub REST API.

Searches *public* GitHub profiles/repos (official API, no scraping), then ranks people by
signal that matters for a technical role: relevant languages, stars on relevant repos,
recent activity, location match. Output is a shortlist for *manual review and opt-in outreach*.

Compliance notes (say these in the interview):
  - Official API only; respect rate limits (unauthenticated 10 search req/min; set GITHUB_TOKEN for more).
  - Only public profile fields. Email is used only if the person publicly lists it.
  - Taiwan PDPA / GDPR: tell candidates where you found them, honour opt-out, don't build a shadow database.
  - LinkedIn / job-board scraping violates their ToS — use Recruiter / approved integrations instead.

Usage:
  export GITHUB_TOKEN=...   # optional but recommended
  python github_sourcer.py --lang Cuda --location Taiwan --min-followers 10 --limit 15 --out gh_candidates.csv
"""
import argparse
import csv
import datetime as dt
import os
import time

import requests

API = "https://api.github.com"


def session():
    s = requests.Session()
    s.headers["Accept"] = "application/vnd.github+json"
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        s.headers["Authorization"] = f"Bearer {tok}"
    return s


def get(s, url, **params):
    r = s.get(url, params=params, timeout=20)
    if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
        wait = max(int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - int(time.time()), 1)
        print(f"rate limited, sleeping {min(wait, 90)}s")
        time.sleep(min(wait, 90))
        r = s.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()


def search_users(s, lang, location, min_followers, limit):
    q = f"language:{lang} location:{location} followers:>={min_followers} repos:>3 type:user"
    data = get(s, f"{API}/search/users", q=q, sort="followers", per_page=min(limit, 30))
    return [u["login"] for u in data.get("items", [])][:limit]


def profile_signal(s, login, lang):
    u = get(s, f"{API}/users/{login}")
    repos = get(s, f"{API}/users/{login}/repos", sort="pushed", per_page=30, type="owner")
    rel = [r for r in repos if (r.get("language") or "").lower() == lang.lower() and not r.get("fork")]
    stars = sum(r["stargazers_count"] for r in rel)
    last_push = max((r["pushed_at"] for r in repos), default=None)
    days = None
    if last_push:
        days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(last_push.replace("Z", "+00:00"))).days
    # transparent heuristic score
    score = min(stars, 200) / 200 * 40 + min(u["followers"], 200) / 200 * 20 + min(len(rel), 10) / 10 * 20
    score += 20 if (days is not None and days < 90) else (10 if days is not None and days < 365 else 0)
    return {
        "login": login, "name": u.get("name") or "", "company": u.get("company") or "",
        "location": u.get("location") or "", "public_email": u.get("email") or "",
        "blog": u.get("blog") or "", "followers": u["followers"],
        f"{lang}_repos": len(rel), f"{lang}_stars": stars, "days_since_push": days,
        "score": round(score, 1), "profile_url": u["html_url"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="Cuda")
    ap.add_argument("--location", default="Taiwan")
    ap.add_argument("--min-followers", type=int, default=10)
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--out", default="gh_candidates.csv")
    a = ap.parse_args()

    s = session()
    logins = search_users(s, a.lang, a.location, a.min_followers, a.limit)
    rows = []
    for lg in logins:
        try:
            rows.append(profile_signal(s, lg, a.lang))
        except requests.HTTPError as e:
            print("skip", lg, e)
    rows.sort(key=lambda r: -r["score"])
    if rows:
        with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    for r in rows[:10]:
        print(r["score"], r["login"], r["location"], r["profile_url"])
    print(f"Saved {len(rows)} -> {a.out}")


if __name__ == "__main__":
    main()
