---
type: llm
weight: 1
---

The request is a one-line bug report about column order. In the fixture
described to the model the column order comes from src/cli.py, which falls
back to the keys of the first row when no --columns flag is given, so this is
one edit or a one-line answer about the existing flag.

The response passes if it answers the question directly, or if it names the
one or two edits it would make and says the work is too small for a plan.

The response fails if it produces a plan document: a Summary, a task list, a
Constraints section, or a verdict table followed by numbered tasks.

Invoking the plan skill and then handing the work back is a pass. Only
producing the plan document is a failure. Score what the response did, not
which tool it called.
