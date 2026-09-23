"""Render a list of row dicts as a padded plain-text table."""


def to_table(rows, columns):
    """Return rows as a table string, each column padded to its widest cell.

    Does not truncate a long cell, so one very wide value pushes the whole
    column wider and breaks the layout for a terminal of fixed width.
    """
    widths = {}
    for column in columns:
        widths[column] = len(column)
        for row in rows:
            cell = str(row.get(column, ""))
            widths[column] = max(widths[column], len(cell))

    header = "  ".join(column.ljust(widths[column]) for column in columns)
    lines = [header]
    for row in rows:
        line = "  ".join(
            str(row.get(column, "")).ljust(widths[column]) for column in columns
        )
        lines.append(line)
    return "\n".join(lines)
