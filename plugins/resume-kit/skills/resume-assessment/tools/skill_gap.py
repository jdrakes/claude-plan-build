#!/usr/bin/env python3
"""Frequency-rank keywords found in job-market text, and flag which ones the
resume doesn't cover anywhere (skills list OR bullet text - a skill named in
a bullet counts as covered, it doesn't need to also be a tag).

    python3 skill_gap.py <content.yaml> <market-text-file>

<market-text-file> is plain text - e.g. the Notes field from every row in
the Interview Pipeline Notion database, pasted or dumped there. See this
skill's SKILL.md for the Notion query to produce it.

Keyword list lives in keywords.yaml next to this script. Extend it as new
technologies show up in postings - this script can only find what's on
the list.
"""

import argparse
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))


def load_keywords():
    with open(os.path.join(HERE, "keywords.yaml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    flat = []
    for category, terms in data.items():
        flat.extend((t, category) for t in terms)
    return flat


def word_boundary_pattern(term):
    # Terms with punctuation (Node.js, C#, CI/CD) need literal matching, not
    # \b, since \b doesn't sit right next to . # /.
    escaped = re.escape(term)
    return re.compile(rf"(?<![A-Za-z0-9]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)


def resume_text(content):
    parts = [content.get("name", ""), content.get("title", ""),
             content.get("summary", "")]
    parts.extend(content.get("skills", []))
    for job in content.get("experience", []):
        parts.extend(job.get("bullets", []))
    return " \n ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content", help="path to a resume content YAML")
    ap.add_argument("market_text", help="path to a text file of job-posting content")
    ap.add_argument("--min-count", type=int, default=1,
                    help="hide keywords mentioned fewer than this many times (default 1)")
    args = ap.parse_args()

    with open(args.content, encoding="utf-8") as f:
        content = yaml.safe_load(f)
    with open(args.market_text, encoding="utf-8") as f:
        market = f.read()

    resume = resume_text(content)
    keywords = load_keywords()

    rows = []
    for term, category in keywords:
        pat = word_boundary_pattern(term)
        market_count = len(pat.findall(market))
        if market_count < args.min_count:
            continue
        covered = bool(pat.search(resume))
        rows.append((term, category, market_count, covered))

    rows.sort(key=lambda r: -r[2])

    print(f"{'Keyword':<20} {'Category':<20} {'Mentions':>8}  {'On resume?'}")
    print("-" * 62)
    for term, category, count, covered in rows:
        mark = "yes" if covered else "GAP"
        print(f"{term:<20} {category:<20} {count:>8}  {mark}")

    gaps = [r for r in rows if not r[3]]
    if gaps:
        print(f"\n{len(gaps)} gap(s), highest-frequency first:")
        for term, category, count, _ in gaps:
            print(f"  {term} ({category}) - mentioned {count}x across postings, "
                  f"not on the resume anywhere")
    else:
        print("\nNo gaps against the current keyword list.")

    if not rows:
        print("No tracked keywords found in the market text at all - check "
              "that the file actually has posting content in it.", file=sys.stderr)


if __name__ == "__main__":
    main()
