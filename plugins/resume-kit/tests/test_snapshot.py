"""The snapshot comparison must catch the regressions a text-matching diff
misses.

Each failing case below is a real class of layout regression that an
index-by-text comparison reports as clean, because every line still exists
somewhere in the document. The baselines here are written by hand, not
produced by rendering anything, so a change in the renderer cannot move the
expectation along with the result.
"""

import os
import sys
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                     "skills", "resume", "tools")
sys.path.insert(0, TOOLS)

import snapshot  # noqa: E402


def line(text, page=1, side=False, x=42.0, y=100.0):
    return {"text": text, "page": page, "side": side, "x": x, "y": y}


BASELINE = [
    line("Alex Rivera", y=43.5),
    line("Employment History", y=194.3),
    line("Senior Software Engineer, Northwind Systems", y=220.6),
    line("Skills", side=True, x=437.3, y=240.3),
]


class CompareTests(unittest.TestCase):
    def test_an_identical_render_agrees(self):
        self.assertIsNone(snapshot.compare(BASELINE, list(BASELINE)))

    def test_a_shift_under_the_tolerance_agrees(self):
        # 0.1pt is font-rounding noise, not a layout change.
        nudged = [dict(row, y=row["y"] + 0.1) for row in BASELINE]
        self.assertIsNone(snapshot.compare(BASELINE, nudged))

    def test_a_line_moving_to_another_page_fails(self):
        # The line still exists, with the same text and the same y. Only its
        # page changed, which is what a document overflowing looks like.
        overflowed = [dict(row) for row in BASELINE]
        overflowed[2] = dict(overflowed[2], page=2)
        message = snapshot.compare(BASELINE, overflowed)
        self.assertIsNotNone(message)
        self.assertIn("page 1 -> ", message)
        self.assertIn("on page 2", message)

    def test_a_whole_column_shifting_sideways_fails(self):
        shifted = [dict(row, x=row["x"] + 60.0) for row in BASELINE]
        message = snapshot.compare(BASELINE, shifted)
        self.assertIsNotNone(message)
        self.assertIn("moved 60.00,0.00pt", message)

    def test_an_extra_line_fails(self):
        extra = list(BASELINE) + [line("Stray footer", y=700.0)]
        self.assertEqual(snapshot.compare(BASELINE, extra),
                         "line count changed: 4 -> 5")

    def test_changed_text_fails(self):
        edited = [dict(row) for row in BASELINE]
        edited[1] = dict(edited[1], text="Employment Historyy")
        message = snapshot.compare(BASELINE, edited)
        self.assertIsNotNone(message)
        self.assertIn("'Employment History'", message)
        self.assertIn("'Employment Historyy'", message)


class ToleranceTests(unittest.TestCase):
    def test_the_tolerance_is_one_point(self):
        # Pinned deliberately: raising it to quiet a host difference is the
        # mistake this check exists to make impossible.
        self.assertEqual(snapshot.TOL, 1.0)

    def test_a_shift_just_over_the_tolerance_fails(self):
        moved = [dict(row) for row in BASELINE]
        moved[0] = dict(moved[0], y=moved[0]["y"] + 1.5)
        message = snapshot.compare(BASELINE, moved)
        self.assertIsNotNone(message)
        self.assertIn("moved 0.00,1.50pt", message)


if __name__ == "__main__":
    unittest.main()
