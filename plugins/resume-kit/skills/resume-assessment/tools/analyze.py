#!/usr/bin/env python3
"""Structural analysis of a resume content YAML.

Measures the things that are easy to get wrong without noticing: bullet
count balance across jobs, how many bullets carry an actual number, and
which bullets are long enough to be stacking multiple claims (a pattern
this repo's CLAUDE.md flags as worth tightening).

    python3 analyze.py <content.yaml>

Does not judge writing quality - flags candidates for a human/Claude
read, same as a linter flags a line, not a rewrite.
"""

import argparse
import re
import statistics
import sys

import yaml

QUANT_RE = re.compile(r"\d|%|\$")
# Roughly where a bullet starts reading as "several claims stacked into one
# sentence" - found in practice across several drafts: past this length a
# bullet stops being read. Not a hard rule, just a flag.
LONG_BULLET_WORDS = 28


def measure(content):
    """Return the structural numbers for a resume content dict.

    {jobs: [{label, company, bullets, quantified, avg_words, longest}],
     total_bullets, quantified_total, quantified_pct, median_bullets,
     skills_count, outliers, long_bullets, unquantified}
    """
    jobs_raw = content.get("experience", [])

    jobs = []
    counts = []
    all_bullets = []
    long_bullets = []

    for job in jobs_raw:
        label = f"{job.get('role', '?')}, {job.get('company', '?')}"[:42]
        company = job.get("company", "?")
        bullets = job.get("bullets", [])
        counts.append(len(bullets))
        word_counts = [len(b.split()) for b in bullets]
        quantified = sum(1 for b in bullets if QUANT_RE.search(b))
        avg_words = statistics.mean(word_counts) if word_counts else 0
        longest = max(word_counts) if word_counts else 0
        jobs.append({
            "label": label,
            "company": company,
            "bullets": bullets,
            "quantified": quantified,
            "avg_words": avg_words,
            "longest": longest,
        })
        all_bullets.extend(bullets)
        for b, wc in zip(bullets, word_counts):
            if wc >= LONG_BULLET_WORDS:
                long_bullets.append((company, wc, b))

    total_bullets = len(all_bullets)
    quantified_total = sum(1 for b in all_bullets if QUANT_RE.search(b))
    quantified_pct = (100 * quantified_total / total_bullets) if total_bullets else None
    median_bullets = statistics.median(counts) if counts else 0

    outliers = [(j["company"], len(j["bullets"])) for j in jobs
                if abs(len(j["bullets"]) - median_bullets) >= 3]

    unquantified = [(j["company"], b) for j in jobs
                    for b in j["bullets"] if not QUANT_RE.search(b)]

    return {
        "jobs": jobs,
        "total_bullets": total_bullets,
        "quantified_total": quantified_total,
        "quantified_pct": quantified_pct,
        "median_bullets": median_bullets,
        "skills_count": len(content.get("skills", [])),
        "outliers": outliers,
        "long_bullets": long_bullets,
        "unquantified": unquantified,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("content", help="path to a resume content YAML")
    args = ap.parse_args()

    with open(args.content, encoding="utf-8") as f:
        content = yaml.safe_load(f)

    if not content.get("experience", []):
        sys.exit("no experience entries found")

    m = measure(content)

    print(f"{'Job':<42} {'Bullets':>7} {'Quant.':>7} {'AvgWords':>9} {'Longest':>7}")
    print("-" * 76)

    for job in m["jobs"]:
        bullets = job["bullets"]
        print(f"{job['label']:<42} {len(bullets):>7} {job['quantified']:>3}/{len(bullets):<3} "
              f"{job['avg_words']:>9.1f} {job['longest']:>7}")

    print("-" * 76)
    if m["quantified_pct"] is None:
        print(f"Total bullets: {m['total_bullets']}   Quantified: 0/0 (n/a)   "
              f"Median bullets/job: {m['median_bullets']:.0f}")
    else:
        print(f"Total bullets: {m['total_bullets']}   Quantified: {m['quantified_total']}/{m['total_bullets']} "
              f"({m['quantified_pct']:.0f}%)   Median bullets/job: {m['median_bullets']:.0f}")
    print(f"Skills listed: {m['skills_count']}   "
          f"Jobs: {len(m['jobs'])}")

    if m["outliers"]:
        print(f"\nBullet-count outliers (>=3 from median of {m['median_bullets']:.0f}):")
        for company, n in m["outliers"]:
            print(f"  {company}: {n}")
        print("  Not automatically bad - the oldest/least-relevant jobs are "
              "supposed to be thin. Worth a glance if one is unintentional.")

    if m["long_bullets"]:
        print(f"\nLong bullets (>={LONG_BULLET_WORDS} words) - candidates for "
              f"'too many claims in one sentence':")
        for company, wc, text in sorted(m["long_bullets"], key=lambda x: -x[1]):
            print(f"  [{company}, {wc}w] {text[:90]}{'...' if len(text) > 90 else ''}")

    if m["unquantified"]:
        print(f"\nUnquantified bullets ({len(m['unquantified'])}) - not automatically weak, "
              f"but each is a candidate for a number if one exists:")
        for company, text in m["unquantified"]:
            print(f"  [{company}] {text[:90]}{'...' if len(text) > 90 else ''}")


if __name__ == "__main__":
    main()
