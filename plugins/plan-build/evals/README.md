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

## What a rebuild has to solve

Three problems were found while attempting the rebuild. The first two were
expected; the third was not, and it constrains where cases can come from.

**1. Class balance is solvable, but only by widening the pool.** The
original 20 cases were all drawn from sessions where the skill fired.
Labelled by evidence, that pool yields roughly 17 "should plan" to 3
"should hand back", which cannot discriminate. Drawing from every session
instead, and labelling by how many implementation subagents the request
actually led to, gives roughly 56 to 42. The imbalance was an artefact of
where cases were sampled from, not of the phenomenon.

**2. Counting subagents mislabels questions.** The count records what
eventually happened, not what should happen on the turn being scored.
Several requests that led to 16 or more subagents are questions: "did you
test that", "what is the proposed next step", "do we have enough data to
draw conclusions". The skill's own rule is that a question gets answered
first, and the answer decides whether a plan is needed. Scoring those as
"must produce a document immediately" contradicts the rule the suite exists
to test. A usable label needs both signals, shape and outcome, and a stated
rule for which wins when they disagree.

**3. A real transcript corpus cannot be published.** This is the blocker.
Prompts sampled across a whole corpus carry medical details, family
logistics, employer names and other personal content that has nothing to do
with software and must not ship. The first suite avoided this by accident:
it sampled only sessions where the skill fired, and those happened to be
all work. Widening the pool to fix problem 1 reintroduces it directly. A
keyword denylist does not solve this, because the categories are open
ended.

So a working suite needs prompts that are either screened one by one by a
person, or written to match the shape of real ones without being real. The
second is the honest option for a public repo, with the transcript corpus
used only to derive the distribution of shapes, never quoted.

## What is still true about the current 20

They are real, they are all work, and they are safe to publish. Their
graders score invocation, which is the wrong event. They remain a starting
point for shape, not for labels.
