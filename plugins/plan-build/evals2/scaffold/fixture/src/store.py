"""Load and save a list of record dicts as JSON."""
import json


def load(path):
    """Read a JSON file and return the list of records in it."""
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save(path, rows):
    """Write a list of record dicts to a JSON file."""
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(rows, handle, indent=2)
