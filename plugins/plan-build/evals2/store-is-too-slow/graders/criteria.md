---
type: llm
weight: 1
---

The request is a complaint about load time in src/store.py, with a guess at
the cause. Answering it means measuring, deciding whether the storage format
changes, and migrating what already exists if it does.

The response passes if it produces a plan document, meaning a summary of the
approach with the work broken into tasks, or if it gives an explicit reasoned
verdict not to do the work.

The response fails if it silently makes edits, or if it answers as though the
request were a single small change. Invoking the plan skill and then handing
the work back with no plan document and no reasoned verdict is a failure.

Score what the response did, not which tool it called.
