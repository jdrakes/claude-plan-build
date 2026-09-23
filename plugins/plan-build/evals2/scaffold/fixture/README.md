# records-table

A tiny command-line tool that reads a list of records from a JSON file
and prints them as a plain-text table.

`src/store.py` loads and saves the JSON file.
`src/format.py` turns rows into a padded table string.
`src/cli.py` wires the two together and prints the result.

Run `make test` to run the tests.
