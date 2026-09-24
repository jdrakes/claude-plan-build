#!/usr/bin/env python3
"""Report how close a render sits to a reference document from another tool.

`check-fidelity.sh` is the gate, not this file. It is what CI runs, and it
wraps `snapshot.py`, which compares a render against its own previous
render, elementwise, and fails the build. This one compares a render
against a foreign document and only reports. The reason is structural
and anyone can check it: matching lines by their text asks whether a line
exists *somewhere* in the other document, so a page overflow, a whole column
sliding sideways and a stray extra line all read as clean. That tolerance is
correct here and disqualifying in a build check.

The question this answers is the one a new user has: you have a document
whose layout you like, and you want to know how close this template gets.
The two sides come out of different renderers, so line order, line breaking
and pagination all differ for legitimate reasons, and a line has to be found
by its text rather than by its position in the list.

    python3 tools/calibrate.py reference.pdf generated.pdf

The report is three blocks. The table is every reference line that was
matched and how far it moved, in points. The unmatched block is reference
lines with no counterpart, which between two renderers usually means the two
broke a line differently. The orphan block is lines in your render with no
counterpart in the reference, which is what tells you the render gained
something the reference never had.

This recovers a matcher that used to live in a private resume repository,
without three things it should not have had.

  * It ended by returning 1 when anything was unmatched. That turns a report
    into a gate for any caller that checks the exit status. This exits 0
    whenever it ran and non-zero only when it could not run: a missing PDF,
    a missing `pdftotext`, or a PDF with no text in it.
  * Both paths had defaults, pointing at one person's own export. Both are
    required arguments here.
  * A --tolerance flag hid rows that had moved less than a threshold. Every
    row prints. A filtered table a reader cannot tell is filtered is worse
    than a long one, and `head` and `grep` are already installed.

Requires `pdftotext` (poppler): brew install poppler
"""

import argparse
import os
import re
import shutil
import sys
from collections import defaultdict
from typing import NamedTuple

# One definition, two callers: `snapshot.py` owns the PDF-to-lines step and
# has no module-level side effects, so importing it here costs nothing.
from snapshot import lines_of


class Match(NamedTuple):
    """A reference line and the render line carrying the same text."""

    reference: dict
    generated: dict
    dx: float
    dy: float
    dpage: int


class Comparison(NamedTuple):
    matches: list
    unmatched: list  # reference lines no render line carried
    orphans: list  # render lines no reference line claimed


# Em dash, en dash, non-breaking hyphen, minus: everything a renderer might
# write where another writes a plain ASCII hyphen. U+2011 is not defensive
# padding. This template emits it deliberately: `components.typ`'s `nbh()`
# replaces the hyphen in a compound so a line break cannot split it, which
# is the text-extraction fix `design-spec.md` section 7c explains. Any
# reference document from another renderer has an ASCII hyphen in that same
# place, so without this fold two copies of one document disagree on every
# hyphenated compound, and those lines report as unmatched on one side and
# orphaned on the other.
HYPHENS = re.compile("[—–‑−]")


def norm(text):
    """Key a line by its text alone.

    Whitespace and the choice of hyphen glyph are things two renderers
    disagree about for the same semantic line, so neither belongs in the key.
    """
    return HYPHENS.sub("-", re.sub(r"\s+", "", text))


def compare(reference, generated):
    """Match each reference line to a render line carrying the same text."""
    candidates = defaultdict(list)
    for index, candidate in enumerate(generated):
        candidates[norm(candidate["text"])].append(index)

    matches = []
    unmatched = []
    claimed = set()
    for line in reference:
        pool = candidates.get(norm(line["text"]))
        if not pool:
            unmatched.append(line)
            continue
        # A tuple key, so the same page wins by construction. An arithmetic
        # page penalty wins only while a page is shorter than the penalty,
        # which is an inequality a reader has to check.
        index = min(pool, key=lambda i: (abs(generated[i]["page"] - line["page"]),
                                         abs(generated[i]["y"] - line["y"])))
        # Consumed, so two reference lines carrying the same text need two
        # counterparts. Leaving the winner in the pool lets one render line
        # answer for both and overstates the match count.
        pool.remove(index)
        claimed.add(index)
        found = generated[index]
        matches.append(Match(reference=line, generated=found,
                             dx=found["x"] - line["x"],
                             dy=found["y"] - line["y"],
                             dpage=found["page"] - line["page"]))

    orphans = [candidate for index, candidate in enumerate(generated)
               if index not in claimed]
    return Comparison(matches=matches, unmatched=unmatched, orphans=orphans)


def describe(line):
    column = "SIDE" if line["side"] else "main"
    return f"  p{line['page']} {column} y={line['y']:7.2f}  {line['text'][:68]}"


def render(comparison, reference_path, generated_path):
    """The whole report, as one string."""
    reference_total = len(comparison.matches) + len(comparison.unmatched)
    generated_total = len(comparison.matches) + len(comparison.orphans)
    worst = max((abs(match.dy) for match in comparison.matches), default=0.0)

    out = [f"reference : {reference_path}",
           f"generated : {generated_path}",
           f"lines: {reference_total} reference, {generated_total} generated",
           "",
           f"{'pg':>2} {'dy':>7} {'dx':>7} {'dpage':>5}  text",
           "-" * 92]
    for match in comparison.matches:
        out.append(f"{match.reference['page']:>2} {match.dy:>7.2f} "
                   f"{match.dx:>7.2f} {match.dpage:>5}  "
                   f"{match.reference['text'][:62]}")
    out.append("-" * 92)
    out.append(f"matched {len(comparison.matches)}/{reference_total}   "
               f"worst |dy| = {worst:.2f}pt")

    if comparison.unmatched:
        out.append("")
        out.append(f"IN THE REFERENCE ONLY ({len(comparison.unmatched)}): these "
                   "reference lines have no counterpart, which usually means the "
                   "two renderers broke a line differently.")
        out.extend(describe(line) for line in comparison.unmatched)

    if comparison.orphans:
        out.append("")
        out.append(f"IN YOUR RENDER ONLY ({len(comparison.orphans)}): these lines "
                   "have no counterpart in the reference.")
        out.extend(describe(line) for line in comparison.orphans)

    return "\n".join(out)


def load_lines(path):
    """Return (lines, error); exactly one of the two is None.

    The file check comes before the toolchain check so that a mistyped path
    reports as a mistyped path on a machine that has no poppler.
    """
    if not os.path.exists(path):
        return None, f"missing PDF: {path}"
    if not shutil.which("pdftotext"):
        return None, "pdftotext not found. Install poppler: brew install poppler"
    lines = lines_of(path)
    if not lines:
        return None, f"no text extracted from: {path}"
    return lines, None


def main(argv=None, read_lines=load_lines):
    """Print the report. The reader is an argument so the tests can pin the
    exit code without a PDF or a poppler install."""
    parser = argparse.ArgumentParser(
        description="Report how far a render sits from a reference document.")
    parser.add_argument("reference", help="the PDF whose layout you like")
    parser.add_argument("generated", help="the PDF this template produced")
    args = parser.parse_args(argv)

    lines = []
    for path in (args.reference, args.generated):
        loaded, error = read_lines(path)
        if error:
            print(error, file=sys.stderr)
            return 2
        lines.append(loaded)

    print(render(compare(*lines), args.reference, args.generated))
    # Zero whatever the report said. Any other code here makes a caller's
    # `$?` a verdict, and this comparison is far too tolerant to be one.
    return 0


if __name__ == "__main__":
    sys.exit(main())
