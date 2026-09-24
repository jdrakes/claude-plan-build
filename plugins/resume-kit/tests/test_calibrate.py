"""Tests for skills/resume/tools/calibrate.py.

The invariant this file exists to pin is the exit code, which is why it is
tested first below. calibrate.py reports how far a render sits from a
reference document produced by some other renderer; snapshot.py is the gate.
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
import os
import sys
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "skills", "resume", "tools")
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

    def test_a_row_prints_however_little_it_moved(self):
        # The recovered tool had a --tolerance flag that dropped these rows.
        _, output = run([line("Alex Rivera", y=43.5)],
                        [line("Alex Rivera", y=43.6)])
        self.assertIn("Alex Rivera", output)
        self.assertIn("0.10", output)


if __name__ == "__main__":
    unittest.main()
