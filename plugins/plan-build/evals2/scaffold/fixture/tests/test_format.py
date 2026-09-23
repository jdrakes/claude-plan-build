"""Tests for to_table. Expected strings are written by hand, not generated
by running the code under test."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from format import to_table


def test_pads_columns_to_widest_cell():
    rows = [{"name": "Al", "role": "Engineer"}, {"name": "Bo", "role": "PM"}]
    result = to_table(rows, ["name", "role"])
    assert result == "name  role    \nAl    Engineer\nBo    PM      "


def test_header_widens_for_a_short_column_name():
    rows = [{"id": "1"}, {"id": "22"}]
    result = to_table(rows, ["id"])
    assert result == "id\n1 \n22"


def test_empty_rows_produce_only_the_header():
    result = to_table([], ["a", "b"])
    assert result == "a  b"
