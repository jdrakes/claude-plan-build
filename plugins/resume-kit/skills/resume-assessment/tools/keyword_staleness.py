#!/usr/bin/env python3
"""Surface terms that show up often in job-posting market text but aren't
tracked in keywords.yaml at all - candidates to add, not gaps to fake.

    python3 keyword_staleness.py <market-text-file> [--top N] [--min-count N]

Same market-text-file format skill_gap.py consumes: company/role/notes per
line, one line per posting/pipeline row (see this skill's SKILL.md for the
Notion query that produces it). Run this occasionally, not as part of every
assessment - keywords.yaml changes slowly.

This never edits keywords.yaml - it prints candidates for a human to look
at and add by hand if they're a genuine, recurring skill. A frequent word
is not automatically a skill (company names, generic verbs, plurals of
something already tracked under a different form all show up too); this
script's job is narrowing the list a human has to read, not deciding for
them. Candidates are single words only - a tracked multi-word term like
"GitHub Actions" is correctly masked out as a whole phrase before counting,
but a genuinely new untracked multi-word skill surfaces as its separate
words rather than as a phrase; a human reading two co-occurring untracked
words will notice. Tokens are normalized before counting - edge punctuation
stripped, punctuation-glued alternatives ("Terraform/Pulumi") counted as one
mention of each, mentions aggregated case-insensitively - so one term is one
row rather than several that each fall under --min-count and vanish.
"""

import argparse
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from skill_gap import load_keywords, word_boundary_pattern

# Generic English words common enough in job postings to swamp real
# candidates if left in - not an attempt at a complete stopword list, just
# enough to keep the output usable. Extend this if a new posting corpus
# surfaces more noise, the same way keywords.yaml itself grows.
STOPWORDS = {
    "the", "and", "or", "with", "for", "you", "your", "our", "we", "will",
    "have", "has", "are", "is", "be", "to", "of", "in", "on", "a", "an",
    "as", "at", "by", "from", "that", "this", "it", "its", "their", "they",
    "team", "work", "working", "experience", "years", "year", "role",
    "job", "company", "strong", "including", "such", "other", "using", "use",
    "across", "within", "all", "who", "what", "can", "able", "ability",
    "skills", "skill", "knowledge", "understanding", "looking", "join",
    "new", "one", "more", "most", "best", "us", "about", "into", "up",
    "out", "if", "not", "but", "so", "than", "then", "when", "where",
    "how", "why", "which", "while", "any", "some", "each", "both", "these",
    "those", "there", "here", "also", "very", "must", "should", "need",
}

TERM_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#./]*")

# Punctuation that is sentence furniture at a token's edge but meaningful
# inside one. Stripped from both ends only, so "Datadog..." is "Datadog" and
# "Terraform/" is "Terraform", while "Node.js" and "CI/CD" keep their
# interior punctuation. "/" belongs here even though it never ends a
# *sentence*: TERM_RE lets it end a *token*, and the token is what gets
# counted. TERM_RE admits only "." and "/" of these today; the rest are
# listed so widening TERM_RE does not reintroduce the bug.
EDGE_PUNCT = ".,;:!?()[]\"'/"

# Splits a token into the parts a human would read as separate words:
# "Terraform/Pulumi" is two tools, "and/or" is two stopwords, "Datadog.We" is
# a term and a missing space. See _terms for what each shape counts as.
COMPONENT_RE = re.compile(r"[./]")


def _is_noise(part, min_len):
    """True if part is a stopword or shorter than min_len - the two ways a
    component fails to be a candidate on its own."""
    return len(part) < min_len or part.casefold() in STOPWORDS


def _terms(token, min_len):
    """The terms a single token contributes one mention each to.

    Every returned string is counted verbatim, so what gets filtered here is
    always exactly what becomes a key - a token is never checked in one form
    and counted in another.

    Three shapes, by what the token's punctuation-separated components are:

    - no real component ("and/or", "e.g", "CI/CD"): noise, contributes
      nothing. Accepted: a genuinely untracked CI/CD-shaped acronym (every
      part short or a stopword) is dropped too, but such terms are already
      tracked and masked, or vanishingly rare — the cost is one missed row
      on a human-reviewed list.
    - every component real ("Terraform/Pulumi", or the ordinary one-component
      "Datadog"): each component is its own mention, so a term named three
      times across glued and bare forms totals three rather than splitting
      into rows that each fall under --min-count.
    - a mix: the noise components decide. All stopwords ("Datadog.We", a
      missing space after a period) means they are sentence furniture, so
      only the real components count. Otherwise the short part is likely part
      of the name itself ("Node.js", "Vue.js") and the token stays whole -
      splitting it would drop a suffix the text never wrote alone.
    """
    parts = [part for part in COMPONENT_RE.split(token) if part]
    real = [part for part in parts if not _is_noise(part, min_len)]
    if not real:
        return []
    noise = [part for part in parts if _is_noise(part, min_len)]
    if all(part.casefold() in STOPWORDS for part in noise):
        return real
    return [token]


def candidates(market_text, tracked_terms, min_len=3):
    """Return a Counter of candidate terms: single-word tokens from
    market_text that are not noise and not already matched by any tracked
    keyword pattern (including multi-word tracked terms, masked out whole
    before tokenizing).

    Tokens are normalized once, before every check and before counting, so
    each real term is one row: edge punctuation is stripped, glued
    alternatives are split into the terms they name (see _terms), and
    mentions are aggregated case-insensitively. The Counter is keyed on a
    display form -
    the most frequent original casing of each term, ties going to the one
    seen first - carrying the aggregated total, so callers read "PagerDuty",
    not "pagerduty". Without this a term written three ways ("Terraform",
    "terraform", "TERRAFORM") becomes three rows of one mention each, all
    below --min-count, and a frequent term disappears entirely."""
    masked = market_text
    for term, _category in tracked_terms:
        masked = word_boundary_pattern(term).sub(" ", masked)

    totals = Counter()
    surface_forms = {}
    for match in TERM_RE.finditer(masked):
        token = match.group(0).strip(EDGE_PUNCT)
        for term in _terms(token, min_len):
            key = term.casefold()
            totals[key] += 1
            surface_forms.setdefault(key, Counter())[term] += 1

    counts = Counter()
    for key, total in totals.items():
        # max() returns the first maximal item, and the form Counter is in
        # first-seen order, so ties break toward the earliest spelling.
        display = max(surface_forms[key].items(), key=lambda pair: pair[1])[0]
        counts[display] = total
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market_text", help="path to a text file of job-posting content")
    ap.add_argument("--top", type=int, default=30,
                     help="show at most this many candidates (default 30)")
    ap.add_argument("--min-count", type=int, default=2,
                     help="hide candidates mentioned fewer than this many times (default 2)")
    args = ap.parse_args()

    with open(args.market_text, encoding="utf-8") as f:
        market = f.read()

    tracked = load_keywords()
    counts = candidates(market, tracked)

    rows = [(term, n) for term, n in counts.items() if n >= args.min_count]
    rows.sort(key=lambda r: -r[1])
    rows = rows[: args.top]

    if not rows:
        print("No untracked candidates at or above --min-count. Either the "
              "keyword list already covers this text, or lower --min-count.")
        return

    print(f"{'Candidate':<24} {'Mentions':>8}")
    print("-" * 34)
    for term, n in rows:
        print(f"{term:<24} {n:>8}")
    print(f"\n{len(rows)} candidate(s) shown, not on keywords.yaml. Add a "
          f"term here only if it's a genuine, recurring skill - see "
          f"keywords.yaml's own header comment.")


if __name__ == "__main__":
    main()
