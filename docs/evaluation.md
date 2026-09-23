# Does this flow work better than what it replaced?

This is the evaluation that decided the flow was worth keeping. It was
opened on 2026-09-06 and closed on 2026-09-08 with a verdict of **Adopt**,
recorded as an override of one of its own criteria rather than a clean
pass. It has been rewritten here for a reader who has never seen the setup
it was measured in.

The flow replaced a general purpose agent workflow plugin. Everything below
compares the two.

## Why it was built

Three measured problems with the previous workflow over three days, not a
preference:

| # | Problem | Measure |
|---|---|---|
| 1 | Work stalled waiting for usage limits to reset | 10.7 hours lost in two days |
| 2 | Approval took far too many turns from the person | 86 turns to get three designs approved |
| 3 | Review was duplicated per task | 93 reviewer dispatches for 50 tasks |

So "better" had to mean cheaper per unit of work and cheaper in the
person's attention, without shipping more defects. Anything else is a
proxy.

## The three criteria

All three had to hold. Each is read per run, and a run is one request taken
from plan through to merge.

| # | Criterion | How it is read |
|---|---|---|
| 1 | Attention | Interruptions per run and the person's turns per run. Lower than baseline. |
| 2 | Cost per task | Orchestrator output tokens divided by the tasks in the plan's first approved version. Lower than baseline. |
| 3 | Defects reaching the main branch | Anything found after merge that the branch-end review should have caught. Counted by hand. Not higher than baseline. |

Criterion 2's denominator excludes tasks the branch-end review appended:
those are the review's output, not the plan's.

## Why tokens per diff line was rejected

It was the original bar and it is a bad one. It rewards verbose output and
punishes concise work, so a twenty line change that took real thought
scores worse than a thousand lines of boilerplate. Diff size is still
recorded below, because separating a run's fixed cost from its per line
cost needs it, but it does not decide anything.

## The baseline

One run of the previous workflow, on one project, 2026-09-05. Fifteen
planned tasks, 6,214 changed lines.

| Measure | Value |
|---|---|
| Output tokens, plan plus build plus close | 911k |
| Per planned task | 60.7k |
| Dispatches | 46, being 19 builder and 27 reviewer |
| Interruptions | 22 |
| Defects reaching the main branch | never counted |

Criterion 3 has no baseline number and never will. It is treated as an
absolute: a defect reaching the main branch on a flow run is worth
recording either way.

## Eight runs

Eight runs of the new flow at deliberately different sizes, because one run
cannot separate a fixed cost from a per line cost. Each is scoped to the
flow window, from the `plan` call to the first merge command. Runs are
labelled A to H here and ordered by cost.

| Run | Flow tokens | Diff lines | Approved tasks | Per task | Turns | Asks |
|---|---:|---:|---:|---:|---:|---:|
| A | 93k | 839 | 5 | 19k | 3 | 3 |
| B | 102k | 122 | 4 | 26k | 4 | 2 |
| C | 142k | 381 | 2 | 71k | 2 | 0 |
| D | 207k | 887 | 5 | 41k | 3 | 2 |
| E | 220k | 1,273 | 4 | 55k | 9 | 2 |
| F | 270k | 263 | 6 | 45k | 17 | 7 |
| G | 352k | 920 | 5 | 70k | 4 | 1 |
| H | 647k | 2,021 | 6 | 108k | 25 | 5 |

Turns are typed turns plus answers to a question the session asked; asks
are the subset where the session stopped and waited.

What the eight show:

- **Attention is settled.** Every run's interruption count sits far under
  the baseline's 22. The highest is 7.
- **Diff size does not predict cost.** The 839 line run was the cheapest
  and the 122 line run cost more than the 381 line one.
- **Turn count does not predict cost either.** Runs with two to four turns
  range from 93k to 352k, and run E has nine turns and still costs less
  than run G's four.
- **Cost per task is a wash.** Five of the eight are under the 60.7k
  baseline and three are over. Two of the three over-baseline runs shipped
  tasks the review appended beyond the approved count, which criterion 2's
  denominator excludes by design. The third spent its turns on two genuine
  off topic detours, and stays over baseline even with one of them removed.
- **Defects reaching the main branch: 2**, both self corrected the same
  day.

One more thing the runs showed, which the defect count understates: on the
largest run the single branch-end review raised seven findings, all seven
real, one of which would have degraded something the person relied on. It
also caused a task to be unticked. One review at the end did the job that
27 reviewer dispatches were doing in the baseline.

## The verdict: Adopt

Recorded 2026-09-08. It **overrides criterion 2 rather than satisfying
it**, and is written that way so no later reader mistakes it for a criteria
pass.

| Measure | Old flow | New flow |
|---|---|---|
| Interruptions per run | 22 | 0 to 7 |
| Turns from the person | 86 to approve three designs | 2 to 25 for a whole run, median 4 |
| Hours lost to usage limit resets | 10.7 in two days | not the failure mode any more |
| Cost per task | 60.7k | a wash, see above |
| Defects reaching the main branch | never counted | 2, both self corrected the same day |

Criterion 1 is decisive on its own. Criterion 2's denominator was argued
across three separate plans and never settled, and the runs show it does
not predict which side of the baseline a run lands on, so it is not a bar
worth holding a decision against. Criterion 3 has no baseline and could
never have carried the verdict either way.

The turn comparison is kept but is not like for like, and is stated that
way rather than dropped: the baseline's 86 turns bought three approved
designs, while the new flow's figure covers a whole run from plan to merge.
The mismatch runs against the new flow, and it still wins on it.

## What the wider corpus says

The eight runs above were the decision. The flow has since been measured
over three weeks across four separate projects, which answers a different
question: whether it only worked on the project it was built on. It did
not.

| Measure | Old flow baseline | This flow |
|---|---:|---:|
| Output tokens per task | 60.7k | 38k |
| Interruptions per task | 1.47 | 0.66 |

The cost that remains is the fixed one. Fitted over the 44 runs that built
at least one task:

- A run costs about **172k output tokens and 32 minutes before it builds
  anything**, plus about 11k tokens and 8 minutes per task.
- At one task, that fixed cost is **94 percent of the tokens and 80 percent
  of the time**.

That number is why the `plan` skill hands back work that comes to one or
two edits instead of writing a document for it. A plan, a fresh subagent
and a branch-end review cost the same whether they carry one task or ten.

## Known gaps

Recorded as accepted, not as pending work:

- The model escalation ladder's retry has never fired. No run has failed a
  gate.
- One stop condition was tested and did not hold. A plan whose task
  instructed something the project's `CLAUDE.md` forbids was handed blind
  to a fresh session. It recognised the conflict, cited the rule correctly,
  and then resolved it itself rather than stopping: it edited the plan,
  committed the edited version, built and merged, and disclosed the
  conflict afterwards. The failure mode is not missing the rule. It is
  judging that upholding the rule was obvious enough to skip the
  confirmation. Opinion 5 in the README is a direct response to that
  result.
- Four other stop conditions remain untested: destructive actions,
  spending, side effects outside the worktree, and a plan whose every path
  forward is a guess.
