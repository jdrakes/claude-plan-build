# The trigger eval: what was tried, and why it did not work

This is a record of a failed experiment. The suite ran, it produced
numbers, and the numbers do not answer the question it was built to answer.
The suite is still in the repo, under `plugins/plan-build/evals/`, because
its 20 prompts are real data. Its score is not a gate and should not be
quoted as one.

## The headline numbers

| Measure | Result |
|---|---|
| Must-fire cases passed | 5 of 10 |
| Must-not-fire cases passed | 10 of 10 |
| Overall score | 0.767 |

## What was run

| Setting | Value |
|---|---|
| Cases | 20, 10 labelled must fire and 10 must not fire |
| Prompt source | Verbatim user messages from real transcripts |
| Runs per case | 3, so 60 runs |
| Ablation | `none`, a single arm with the plugin installed |
| Graders | Deterministic `tool_used` on `Skill` with `input_match: plan-build:plan` |
| Tools offered to the model | `Skill` only |
| Turn ceiling | 10 |
| Harness | `claude plugin eval`, CLI 2.1.280 |
| Wall clock | 653 seconds |
| API cost | 4.20 USD |

A must-fire case passes when the `plan` skill is invoked at least once. A
must-not-fire case passes when it is invoked zero times. No LLM judge was
used, so no grader made a subjective call.

The raw result JSON is not committed. It records absolute paths from the
machine that ran it, which the repo's leak test rejects, and the figures
worth keeping are the ones in this file.

## The result in detail

Every run completed. Zero errored, and the deepest run used 7 turns against
a ceiling of 10, so nothing was truncated. The numbers are real
measurements of exactly what was asked.

| Half of the suite | Cases passed | Runs where `plan` fired |
|---|---|---|
| Must fire | 5 of 10 | 16 of 30 |
| Must not fire | 10 of 10 | 0 of 30 |

Nineteen of the twenty cases behaved the same way on all three of their
runs, whether that matched the label or not. One must-fire case fired on 1
run of 3, and it is the only run-to-run disagreement in the set, so the
result is not noisy. It is consistent and half wrong.

## Why it does not answer the question

Four reasons. Each one alone is enough to stop the score being used.

1. **The suite has no counterfactual.** It ran one arm, `--ablation none`.
   There is no run with the skill absent, and none with its description
   altered. Nothing in this data can support a claim about what the skill's
   description causes, only about what happened once with it present.

2. **It reproduces none of the behaviour it was built from.** All 20
   prompts come from sessions where `plan` did fire. The 10 must-not-fire
   cases are therefore a catalogue of real firings, and the harness fired on
   zero of their 30 runs. Scoring 10 out of 10 on known positives is not a
   pass. It means the instrument does not reproduce the thing being
   measured, and the 5 of 10 on the other half has to be read in that
   light.

3. **The labels were judgment, not evidence.** Checked afterwards against
   the transcripts the prompts came from, 7 of the 10 must-not-fire prompts
   led to real builds of between 5 and 17 tasks. Those should have been
   labelled must fire. Only 3 led to no work at all. So the half of the
   suite that scored 10 of 10 is mostly mislabelled, and the perfect score
   is an artefact of that.

4. **A bare prompt is not the setting the trigger fires in.** Cases run
   with no repository, no prior turns, and `allowed_tools: [Skill]`. Most of
   the real firings followed earlier conversation, and several of these
   prompts are mid-conversation fragments whose pronouns have no referent
   when they stand alone. The model was asked to decide on less information
   than it has in the situation being modelled.

## What changed underneath it

While this was being built, the `plan` skill gained section `1a`: before
writing anything, say what the simplest version that would work is, and if
that is one or two edits, hand it back and write no document.

That moves the cost. Invoking `plan` is no longer the expensive event;
producing a plan document, a branch and a review is. The suite scores
invocation. So it now measures an event that does not carry the cost it was
built to control, and relabelling the cases would not fix that, because the
graders are watching the wrong thing.

## What a working suite would need

| Needs | Instead of |
|---|---|
| Graders that read the response for whether a document was produced or the work was handed back | Graders that count whether a tool was called |
| Labels taken from how much work the request really led to | Labels assigned by reading the prompt and judging |
| Cases drawn from the 164 transcripts where `plan` never fired as well as the 50 where it did | Cases drawn only from sessions where it fired, which leaves the hand-back class empty |
| `Read`, `Grep` and `Glob` plus a scaffolded repository | A bare prompt with `Skill` as the only tool |

The last row is not a convenience. Deciding whether a request is one edit or
ten means looking at the code, so a harness that forbids looking cannot
model the decision.

## What happens to the suite

It stays. The 20 prompts are verbatim real requests and a later suite starts
from them rather than from invented examples. `evals/README.md` says
plainly what the graders score and that the suite is not a gate.
