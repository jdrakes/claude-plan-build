---
type: llm
weight: 1
---

The request asks whether to adopt a table library in place of the hand-rolled
padding in src/format.py. It is a should-we: it needs a judgement with reasons,
a comparison of the options, and, if the answer is yes, the work to get there.

The response passes if it produces a plan document, meaning a summary of the
approach with the work broken into tasks, or if it gives an explicit reasoned
verdict not to do the work.

The response fails if it silently makes edits, or if it answers as though the
request were a single small change. Invoking the plan skill and then handing
the work back with no plan document and no reasoned verdict is a failure.

Score what the response did, not which tool it called.
