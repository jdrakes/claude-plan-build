---
type: llm
weight: 1
---

The request is to truncate long cells in to_table. In the fixture described to the model
that is one edit inside src/format.py, where the cell is padded.

The response passes if it answers the question directly, or if it names the
one or two edits it would make and says the work is too small for a plan.

The response fails if it produces a plan document: a Summary, a task list, a
Constraints section, or a verdict table followed by numbered tasks.

Invoking the plan skill and then handing the work back is a pass. Only
producing the plan document is a failure. Score what the response did, not
which tool it called.
