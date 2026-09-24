"""Tests for skills/resume/tools/calibrate.py.

The invariant this file exists to pin is the exit code, which is why it is
tested first below. calibrate.py reports how far a render sits from a
reference document produced by some other renderer; check-fidelity.sh, which
wraps snapshot.py, is the gate.
A comparison that indexes lines by their text can only ask whether a line
exists somewhere in the other document, so it reads a page overflow and a
shifted column as clean. If any comparison outcome reached a caller's `$?`,
a caller would eventually gate on it, and that is the gate this plugin
already has a stricter tool for.

Every case runs on hand-written line lists in the shape `lines_of` returns,
so no PDF, no fixture and no poppler binary is involved. The expected
numbers are written out by hand rather than computed from the module under
test.
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(PLUGIN, "skills", "resume", "tools")
BASELINE = os.path.join(PLUGIN, "skills", "resume", "examples",
                        "sample-resume.baseline.json")
sys.path.insert(0, TOOLS)

import calibrate  # noqa: E402


def line(text, page=1, side=False, x=42.0, y=100.0):
    return {"text": text, "page": page, "side": side, "x": x, "y": y}


def reader(reference, generated):
    """Stand in for the PDF reader: hand back these two line lists in order.

    main() takes the reader as an argument precisely so the exit code can be
    pinned without a PDF or a poppler install.
    """
    documents = [reference, generated]
    return lambda _path: (documents.pop(0), None)


def run(reference, generated):
    """Return (exit_code, stdout) for one comparison."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = calibrate.main(["reference.pdf", "generated.pdf"],
                              read_lines=reader(reference, generated))
    return code, out.getvalue()


class ExitCodeTests(unittest.TestCase):
    """The exit code says whether the run happened, never what it found."""

    def test_an_identical_render_exits_zero(self):
        lines = [line("Alex Rivera", y=43.5), line("Skills", side=True, y=240.3)]
        code, _ = run(lines, list(lines))
        self.assertEqual(code, 0)

    def test_an_unmatched_reference_line_exits_zero(self):
        code, _ = run([line("Alex Rivera"), line("Employment History", y=194.3)],
                      [line("Alex Rivera")])
        self.assertEqual(code, 0)

    def test_a_line_only_in_the_render_exits_zero(self):
        code, _ = run([line("Alex Rivera")],
                      [line("Alex Rivera"), line("Referees on request", y=700.0)])
        self.assertEqual(code, 0)

    def test_two_documents_with_nothing_in_common_exit_zero(self):
        code, _ = run([line("Alex Rivera")], [line("Sam Okafor")])
        self.assertEqual(code, 0)

    def test_a_missing_input_file_exits_non_zero(self):
        # The real reader, not the stand-in: this is the one failure the
        # exit code is allowed to carry.
        with tempfile.TemporaryDirectory() as folder:
            absent = os.path.join(folder, "not-here.pdf")
            errors = io.StringIO()
            with contextlib.redirect_stderr(errors):
                code = calibrate.main([absent, absent])
        self.assertNotEqual(code, 0)
        self.assertIn(absent, errors.getvalue())


class NormTests(unittest.TestCase):
    """Two renderers do not agree on whitespace or on which dash glyph."""

    def test_dashes_and_spacing_fold_to_one_key(self):
        self.assertEqual(calibrate.norm("Lead  Engineer — Northwind"),
                         "LeadEngineer-Northwind")
        self.assertEqual(calibrate.norm("Lead Engineer – Northwind"),
                         "LeadEngineer-Northwind")
        self.assertEqual(calibrate.norm("Lead Engineer - Northwind"),
                         "LeadEngineer-Northwind")

    def test_every_hyphen_in_the_family_folds_to_one_key(self):
        # U+2011 is in this list because this template emits it on purpose:
        # components.typ's nbh() writes a non-breaking hyphen so that a
        # hyphenated compound cannot be split across a line break. Every
        # other renderer writes a plain ASCII hyphen in the same place, so
        # without the fold two copies of one document disagree on the line.
        for hyphen in ("-", "—", "–", "‑", "−"):
            with self.subTest(hyphen=hyphen):
                self.assertEqual(calibrate.norm(f"end{hyphen}to{hyphen}end"),
                                 "end-to-end")

    def test_a_shipped_baseline_line_folds_to_its_ascii_spelling(self):
        # A hand-written U+2011 only proves the fold works. This line comes
        # out of the committed baseline, so it also proves the fold is aimed
        # at a glyph this repository actually renders.
        with open(BASELINE, encoding="utf-8") as handle:
            texts = [entry["text"] for entry in json.load(handle)]
        shipped = [text for text in texts if text == "Event‑driven systems"]
        self.assertEqual(len(shipped), 1,
                         "the baseline no longer carries this U+2011 line")
        self.assertEqual(calibrate.norm(shipped[0]), "Event-drivensystems")

    def test_different_text_keys_differently(self):
        self.assertNotEqual(calibrate.norm("Lead Engineer"),
                            calibrate.norm("Lead Engineers"))


class CompareTests(unittest.TestCase):
    def test_an_identical_render_matches_everything_with_no_movement(self):
        lines = [line("Alex Rivera", y=43.5),
                 line("Employment History", y=194.3),
                 line("Skills", side=True, x=437.3, y=240.3)]
        result = calibrate.compare(lines, list(lines))
        self.assertEqual(len(result.matches), 3)
        self.assertEqual(result.unmatched, [])
        self.assertEqual(result.orphans, [])
        for match in result.matches:
            self.assertEqual((match.dx, match.dy, match.dpage), (0.0, 0.0, 0))

    def test_a_reference_line_the_render_lacks_is_unmatched(self):
        absent = line("Employment History", y=194.3)
        result = calibrate.compare([line("Alex Rivera"), absent],
                                   [line("Alex Rivera")])
        self.assertEqual(len(result.matches), 1)
        self.assertEqual(result.unmatched, [absent])
        self.assertEqual(result.orphans, [])

    def test_a_render_line_the_reference_lacks_is_an_orphan(self):
        # The recovered tool looped over the reference only and could not
        # see this line at all: not matched, not unmatched, not printed.
        extra = line("Referees on request", y=700.0)
        result = calibrate.compare([line("Alex Rivera")],
                                   [line("Alex Rivera"), extra])
        self.assertEqual(len(result.matches), 1)
        self.assertEqual(result.unmatched, [])
        self.assertEqual(result.orphans, [extra])

    def test_a_matched_candidate_is_consumed(self):
        # Two reference lines carrying the same text against one counterpart:
        # the first claims it, the second has nowhere to go. The recovered
        # tool left the winner in the index, so both matched it and the
        # matched count overstated.
        first = line("Contractor", y=300.0)
        second = line("Contractor", y=520.0)
        only = line("Contractor", y=305.0)
        result = calibrate.compare([first, second], [only])
        self.assertEqual(len(result.matches), 1)
        self.assertEqual(result.matches[0].reference, first)
        self.assertEqual(result.unmatched, [second])
        self.assertEqual(result.orphans, [])

    def test_a_same_page_candidate_beats_a_nearer_one_on_another_page(self):
        reference = [line("Contractor", page=2, y=400.0)]
        nearer_but_elsewhere = line("Contractor", page=1, y=400.0)
        same_page = line("Contractor", page=2, y=700.0)
        result = calibrate.compare(reference, [nearer_but_elsewhere, same_page])
        self.assertEqual(result.matches[0].generated, same_page)
        self.assertEqual(result.matches[0].dpage, 0)
        self.assertEqual(result.matches[0].dy, 300.0)
        self.assertEqual(result.orphans, [nearer_but_elsewhere])


class ReportTests(unittest.TestCase):
    def test_the_report_counts_matches_and_names_both_leftover_blocks(self):
        _, output = run([line("Alex Rivera"), line("Employment History", y=194.3)],
                        [line("Alex Rivera"), line("Referees on request", y=700.0)])
        self.assertIn("matched 1/2", output)
        self.assertIn("Employment History", output)
        self.assertIn("Referees on request", output)

    def test_the_header_counts_a_render_only_line_on_the_generated_side(self):
        # One line each side is shared, one each side is not, so the two
        # totals are equal and neither can be read off the matched count.
        _, output = run([line("Alex Rivera"), line("Employment History", y=194.3)],
                        [line("Alex Rivera"), line("Referees on request", y=700.0)])
        self.assertIn("lines: 2 reference, 2 generated", output)

    def test_the_leftover_blocks_name_the_column_each_line_sits_in(self):
        _, output = run([line("Employment History", y=194.3)],
                        [line("Skills", side=True, x=437.3, y=240.3)])
        self.assertIn("p1 main y= 194.30  Employment History", output)
        self.assertIn("p1 SIDE y= 240.30  Skills", output)

    def test_the_worst_figure_is_vertical_movement_not_horizontal(self):
        # dx and dy differ here, so a figure taken from the wrong one shows.
        _, output = run([line("Alex Rivera", x=42.0, y=100.0)],
                        [line("Alex Rivera", x=95.0, y=112.5)])
        self.assertIn("worst |dy| = 12.50pt", output)

    def test_a_row_prints_however_little_it_moved(self):
        # The recovered tool had a --tolerance flag that dropped these rows.
        _, output = run([line("Alex Rivera", y=43.5)],
                        [line("Alex Rivera", y=43.6)])
        self.assertIn("Alex Rivera", output)
        self.assertIn("0.10", output)


if __name__ == "__main__":
    unittest.main()
