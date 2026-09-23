"""Command-line entry point: load a JSON file and print it as a table."""
import argparse
import sys

from format import to_table
from store import load


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Print a JSON file of records as a table."
    )
    parser.add_argument("path", help="path to a JSON file holding a list of records")
    parser.add_argument(
        "--columns", help="comma-separated column names", default=None
    )
    args = parser.parse_args(argv)

    rows = load(args.path)
    if args.columns:
        columns = args.columns.split(",")
    elif rows:
        columns = list(rows[0].keys())
    else:
        columns = []

    print(to_table(rows, columns))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
