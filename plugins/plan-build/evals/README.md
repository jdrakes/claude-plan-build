# Eval suite: does `plan` fire correctly

Twenty cases, each one prompt paired with a grader. Every prompt is a
verbatim line from one person's real work transcripts, taken over three
weeks (2026-09-01 to 2026-09-23). The wording is the data: nothing here is
invented or reworded.

## What this measures

Whether the `plan` skill's trigger fires on a given request, nothing else.
Ten cases are labelled "must fire" and ten "must not fire". A case's grader
checks only that: it does not score plan quality, whether a plan (if one
starts) is any good, or whether the resulting build is any good. A plan
quality suite is a separate, larger, and harder problem, deferred rather
than attempted here.

Each case restricts the model to the `Skill` tool only (`allowed_tools:
[Skill]` in `prompt.md`). With no `Read`, `Grep` or `Glob` available, the
model cannot investigate anything, so a case measures exactly one thing:
does the trigger fire on this text, with no way to route around the
question by looking something up first.

Each grader is deterministic (`type: tool_used`), not an LLM judge: it
counts calls to the `Skill` tool whose input matches the plan skill's
namespaced identifier, with `weight: 1` and, for the must-not-fire
direction, `min: 0` and `max: 0` (the plan skill must be called zero times).
No case here needed a judge call.

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
   prompt's content, not by a report of what actually happened.
4. **Firing is not quality, and that is deliberate.** This set scores
   whether the skill fires, never whether the plan that follows is any
   good. Between the two, firing correctly without wasting anyone's tokens
   was judged the more important thing to get right first, so a
   plan-quality suite is a later question, not a gap in this one.
