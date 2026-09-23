# Eval suite: does `plan` fire correctly

**This suite is not a gate, and its score should not be quoted as one.** It
was run once, it did not measure what it was built to measure, and the
write-up of that failure is in `docs/trigger-eval-attempt.md`. Read it
before reading anything into these cases.

Twenty cases, each one prompt paired with a grader. Every prompt is a
verbatim line from one person's real work transcripts, taken over three
weeks (2026-09-01 to 2026-09-23). The wording is the data: nothing here is
invented or reworded. That is the reason the suite is still in the repo. A
later suite should start from these prompts rather than from made-up ones.

## What the graders actually score

Each grader is deterministic (`type: tool_used`), not an LLM judge: it
counts calls to the `Skill` tool whose input matches the plan skill's
namespaced identifier, with `weight: 1` and, for the must-not-fire
direction, `min: 0` and `max: 0` (the plan skill must be called zero times).
No case here needed a judge call.

So a case scores one thing: was the `plan` skill invoked. It does not score
whether a plan was written, whether a plan was any good, or whether the
resulting build was any good.

**Invocation is no longer the cost event.** The skill's section `1a` hands
work back when the simplest version that would work is one or two edits, and
writes no document. Invoking `plan` is now cheap; producing a plan
document, a branch and a branch-end review is what costs. These graders
watch the invocation, which means they watch the wrong event. That is not
fixable by relabelling the cases.

Each case restricts the model to the `Skill` tool only (`allowed_tools:
[Skill]` in `prompt.md`). With no `Read`, `Grep` or `Glob` available, the
model cannot investigate anything. That was deliberate, so that a case
measured one thing. It is also part of why the suite failed: deciding
whether a request is one edit or ten means looking at the code.

## Known weaknesses of this set

1. **Every prompt comes from one person.** The trigger is tested against
   one person's phrasing. Someone else's wording for the same intent, for
   example "can you sort out the deploy", is not represented.
2. **No conversational context.** In the real transcripts, some firings
   followed several earlier turns of conversation. Single-word continuations
   like "Yes" or "Go" are excluded because standalone they are meaningless,
   which means how the trigger behaves mid-conversation is untested here.
3. **Most labels are a judgment call, not a confirmed report.** Three of the
   twenty cases were confirmed misfires or catches by the person whose
   transcripts they come from; two more are read from a recorded verdict at
   the time. The remaining fifteen are labelled by inference from the
   prompt's content, not by a report of what actually happened. Checked
   against the transcripts after the run, 7 of the 10 must-not-fire prompts
   led to real builds of 5 to 17 tasks, so those labels are wrong.
4. **Firing is not quality, and that is deliberate.** This set scores
   whether the skill fires, never whether the plan that follows is any
   good. Between the two, firing correctly without wasting anyone's tokens
   was judged the more important thing to get right first, so a
   plan-quality suite is a later question, not a gap in this one.
