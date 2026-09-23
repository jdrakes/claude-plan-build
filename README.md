# plan-build

An opinionated Claude Code plugin for planning and building software
changes: one approved plan, one fresh subagent per task, the project's
tests as the gate, and one review at the end of the branch.

## The opinions

These are the argument, and they come before the install instructions on
purpose. If you disagree with them, the plugin is not for you.

1. **One review at the end of the branch, not one per task.** (`build` 3.2)
2. **Interruption is the cost, not the safety.** No progress summaries, and
   no asking whether to continue between tasks. (`build` opening)
3. **The orchestrator runs the gate itself and never trusts the builder's
   report.** (`build` 2.2)
4. **A subagent never ticks its own checkbox.** The tick records that the
   work passed a gate the subagent has not seen. (`builder` 3)
5. **An instruction conflict is a hard stop however obvious the fix looks.**
   Quote the conflicting text; do not edit the plan to remove it.
   (`build` Stops)
6. **Escalate models on failure, do not retry the same one.** (`build`
   Models)
7. **Subagents never spawn subagents, and say stuck after two failed
   approaches.** (`builder` 5)
8. **A test that checks source text contains a string is not a test.**
   (`builder` 6)
9. **Verdict before questions, and a "no" ships no document.** A plan for
   work that should not happen invites doing it. (`plan` 1)
10. **A task with a placeholder is not a task.** (`plan` 3)
11. **No praise, and no summary of what the branch does.** The person has
    the plan for that. (`reviewer` 5)
12. **Instructions rot when every mistake becomes a rule.**
    (`claude-md-rules`)
13. **Work that is one or two edits is handed back, not planned.** A plan
    costs the same whether it carries one task or ten. (`plan` 1a)

## Install

```
/plugin marketplace add jdrakes/claude-plan-build
/plugin install plan-build@jdrakes
```

## What is in it

**`plan`** turns a request into a plan you can approve, or a reasoned no.
It gives a verdict first, with a table of what the change costs, what it
fixes and what it risks, before it asks you anything. If the simplest
version that would work is one or two edits, it names the edits and hands
them back instead of writing a document. What it does write is a Summary
you read and approve, and a Tasks section only the builder reads.

**`build`** executes an approved plan without checking in. It creates a
worktree, dispatches one fresh subagent per task, runs the project's test
command itself as the gate after each one, and ticks the checkbox only when
the gate passed. A failed task is dispatched again on the next model up,
never retried on the same one. At the end of the branch it dispatches one
review, then carries out the project's stated integration default.

**`claude-md-rules`** is a gatekeeper that runs before a rule is added to
`CLAUDE.md` or `AGENTS.md`. It filters the proposed rule: is it universal,
could a deterministic tool do it instead, would the model infer it from the
codebase anyway, is it a one off patch for a single mistake, and can it
point instead of paste. It also flags a file that has grown past the point
where instructions get followed.

**`builder`** is the subagent `build` dispatches per task. It reads the
plan's Constraints and its own task, nothing else; it makes exactly one
commit with the reasoning in the body; it reports in under 15 lines; and it
stops and reports rather than resolving a conflict between the task and the
project's rules.

**`reviewer`** is the read only subagent dispatched once at the end of the
branch. It gives two verdicts, whether the branch does what the Summary
says and whether it is well built, then lists findings ranked most severe
first, each with the input or state that makes it fail.

## What your project needs to provide

| Requirement | Why |
|---|---|
| A test command, named in the plan's Constraints | It is the gate after every task |
| `.claude/worktrees/` in `.gitignore` | `build` works in a worktree there, and it will not commit that line to your repo for you |
| An `Integration default` line in `CLAUDE.md` or `README.md` | It says what happens when the branch is finished |

The `Integration default` line must read one of `push, PR, verify, merge`,
`merge locally`, `keep the branch` or `ask each time`. If it is absent,
`build` offers the three choices and waits.

A design page is optional. Where a project keeps one, a plan derives from
the build's issue and the section of that page the issue names.

## Does it work?

Measured over three weeks and four projects. Verdict: Adopt, as an override
of the cost-per-task criterion and not a pass on it, because cost per task is
a wash and attention is what the flow fixed. [Write up](docs/evaluation.md).

| Measure | Replaced flow | This flow |
|---|---:|---:|
| Output tokens per task | 60.7k | 38k |
| Interruptions per task | 1.47 | 0.66 |
| Context tokens, always on / on invoke, all components | 840 / 61k | 405 / 5.2k |

## Does the eval work?

No, not yet. A 20 case suite ran clean and answers nothing: must-fire 5 of
10, must-not-fire 10 of 10, overall 0.767. That score is not a pass mark.
The graders score whether the `plan` skill was invoked, and since section
`1a` landed invocation is no longer the cost event: writing a document, a
branch and a review is. Checked afterwards, 7 of the 10 must-not-fire
prompts had led to real builds, so the half that scored perfectly is
mislabelled. Record: [docs/trigger-eval-attempt.md](docs/trigger-eval-attempt.md),
[evals/README.md](plugins/plan-build/evals/README.md).

## What this cost to find out

Nine runs measured by hand, then a corpus of runs across four projects, to
learn that attention is what the flow fixes and cost per task is a wash.
Section `1a` exists because of one number out of that: a run costs about
172k output tokens and 32 minutes before it builds anything, so at one task
the ceremony is 94 percent of the tokens. The eval suite cost 4.20 USD and
653 seconds to produce a result that cannot be used as a gate.
