#!/usr/bin/env python3
"""Record a rendered resume's line geometry, and check a render against it.

The renderer's only regression test looks at the rendered page rather than
the source. A baseline is every line the PDF contains, with the page it
landed on, which column it is in, and where on the page it sits. Checking is
an elementwise comparison: same count, same lines in the same order, each
within TOL of where it was.

    tools/snapshot.py out.pdf --write examples/sample-resume.baseline.json
    tools/snapshot.py out.pdf --check examples/sample-resume.baseline.json

Both sides of a check come from the same renderer, the same content and the
same sort below, so line N of one is line N of the other. There is
deliberately no matching of lines by their text: text matching answers "does
this line exist somewhere in the document", which a page overflow, a whole
column shifting sideways and a stray extra line all survive. Position in the
sequence is the stronger claim, and it is the one available here.

Requires `pdftotext` (poppler).
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict

# Left edge of the navy band; splits the two columns.
SIDEBAR_X = 403.28

# Points a line may move before the check fails. Never raise this to quiet a
# host difference: a render that depends on the host's installed fonts is
# fixed by bin/build's --ignore-system-fonts, not by a wider tolerance. This
# is the only check that looks at the rendered page, and loosening it blunts
# exactly what it exists to catch.
TOL = 1.0


def lines_of(pdf):
    """Group a PDF's words into lines: (page, is_sidebar, x, y, text)."""
    out = subprocess.run(["pdftotext", "-bbox", pdf, "-"],
                         capture_output=True, text=True).stdout
    result = []
    for page_no, page in enumerate(re.findall(r"<page .*?</page>", out, re.S), 1):
        words = [(float(a), float(b), float(c), float(d), t) for a, b, c, d, t in
                 re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" '
                            r'xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', page)]
        buckets = defaultdict(list)
        for w in words:
            buckets[(w[0] >= SIDEBAR_X, round(w[1], 0))].append(w)
        for (is_side, _), group in buckets.items():
            group.sort(key=lambda w: w[0])
            result.append({
                "page": page_no, "side": is_side,
                "x": group[0][0], "y": group[0][1],
                "text": " ".join(w[4] for w in group),
            })
    result.sort(key=lambda r: (r["page"], r["side"], r["y"]))
    return result


def compare(baseline, generated):
    """Return the first difference as a message, or None if they agree."""
    if len(baseline) != len(generated):
        return f"line count changed: {len(baseline)} -> {len(generated)}"
    for want, got in zip(baseline, generated):
        if (want["text"], want["page"], want["side"]) != (got["text"], got["page"], got["side"]):
            return (f"line changed: {want['text'][:60]!r} on page {want['page']}"
                    f" -> {got['text'][:60]!r} on page {got['page']}")
        if abs(want["y"] - got["y"]) > TOL or abs(want["x"] - got["x"]) > TOL:
            return (f"moved {got['x'] - want['x']:.2f},{got['y'] - want['y']:.2f}pt:"
                    f" {want['text'][:60]}")
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", metavar="BASELINE",
                      help="record this PDF's geometry as the baseline")
    mode.add_argument("--check", metavar="BASELINE",
                      help="compare this PDF against a recorded baseline")
    args = parser.parse_args()

    if not shutil.which("pdftotext"):
        return "pdftotext not found. Install poppler."
    if not os.path.exists(args.pdf):
        return f"missing PDF: {args.pdf}"

    generated = lines_of(args.pdf)
    if not generated:
        return f"no text extracted from {args.pdf}"

    if args.write:
        with open(args.write, "w", encoding="utf-8") as handle:
            # Indented and sorted so the committed baseline diffs line by
            # line when geometry moves. That readable diff is the whole
            # reason to commit JSON rather than the PDF itself.
            json.dump(generated, handle, indent=2, sort_keys=True)
            handle.write("\n")
        print(f"wrote {len(generated)} lines to {args.write}")
        return None

    with open(args.check, encoding="utf-8") as handle:
        baseline = json.load(handle)
    difference = compare(baseline, generated)
    if difference:
        return f"FAIL: {difference}"
    print(f"PASS: renderer fidelity intact ({len(generated)} lines match the baseline)")
    return None


if __name__ == "__main__":
    sys.exit(main())
