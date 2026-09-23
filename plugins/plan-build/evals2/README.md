# Eval suite: does `plan` produce a document when it should

Sixteen cases, eight labelled `hand-back` and eight labelled `plan`. Each is
one written prompt against one scaffolded repository, paired with one LLM
grader.

## What this suite measures

**Whether a plan document was produced, not whether the plan skill fired.**

The first suite in `evals/` scored invocation with a deterministic
`tool_used` grader. Since the skill's section `1a` landed, invocation is
cheap: the skill can correctly fire, look at the code, decide the work is one
or two edits and hand it back without writing anything. The cost event is the
document, the branch and the branch-end review that follow it. A grader that
counts `Skill` calls therefore watches an event that no longer matters, and a
correct fire-then-hand-back scores as a failure.

So every grader here is `type: llm`, `weight: 1`, and reads what the response
did:

- A `hand-back` case passes when the response answers the question, or names
  the one or two edits and says the work is too small for a plan. It fails
  only when a plan document appears. Firing the skill and handing back is a
  pass.
- A `plan` case passes when the response produces a plan document or an
  explicit reasoned verdict not to do the work. It fails when it edits
  silently or answers as though the request were one small change.

## The labelling rule

Stated once, so every case can be checked against it:

> A case is `hand-back` when the request is a question, or when the simplest
> version that would work is one or two edits. It is `plan` when the work
> needs a document a subagent will build from. Where shape and size disagree,
> shape wins for questions: the skill's own rule is that a question is
> answered first and the answer decides whether a plan is needed.

## Every prompt here is written, not quoted

The first suite used verbatim lines from one person's real work transcripts.
That set cannot be published: a real corpus carries medical, family and
employer detail, and it represents exactly one person's phrasing. Nothing
from any transcript is reproduced here. What carried over is a distribution,
measured over 100 work-initiating turns:

| Shape | Share | Median implementation subagents it led to |
|---|---|---|
| Plain change request | 54% | 0 |
| Question | 32% | 0 |
| Multi-part change request | 7% | 0 |
| Complaint about existing behaviour | 5% | 11 |
| "Should we" | 2% | 9 |

Median length 79 characters, quartiles 52 and 119. Complaints and should-we's
are the shapes that earn a plan; plain requests and questions overwhelmingly
do not. The sixteen prompts were written to that distribution, in the
register of a working developer typing quickly, and every one of them refers
truthfully to the scaffolded code.

## The scaffold

`scaffold/scaffold.sh` lays down `scaffold/fixture/`, a small Python CLI that
reads records from a JSON file and prints them as a table: `src/store.py`,
`src/format.py`, `src/cli.py`, `tests/test_format.py`, a `Makefile` with a
`test` target. Every case names it as its `scaffold_script`, so the suite must
be run with `--scaffold`; without that flag the fixture is never laid down and
every case decides blind.

Each case allows `Skill`, `Read`, `Grep` and `Glob`. Read access is the point:
deciding whether a request is one edit or a project means looking at the code,
which the first suite made impossible. `Bash`, `Write` and `Edit` are absent,
so nothing can be built or changed.

## The sixteen cases

| Case | Label | Shape |
|---|---|---|
| `truncate-long-cells` | hand-back | plain change request |
| `what-does-store-do` | hand-back | question |
| `column-order-wrong` | hand-back | bug report |
| `why-is-the-table-ragged` | hand-back | question |
| `add-a-version-flag` | hand-back | plain change request |
| `is-there-a-test-for-padding` | hand-back | question |
| `rename-to-table` | hand-back | plain change request |
| `drop-quiet-flag` | hand-back | plain change request |
| `output-is-unreadable` | plan | complaint |
| `should-we-use-a-real-table-lib` | plan | should we |
| `add-csv-and-json-output` | plan | multi-part change request |
| `store-is-too-slow` | plan | complaint |
| `should-we-split-cli-from-core` | plan | should we |
| `sorting-filtering-and-paging` | plan | multi-part change request |
| `no-error-handling-anywhere` | plan | complaint |
| `should-we-add-a-config-file` | plan | should we |

## What it still does not measure

Whether the plan that gets written is any good. A case scores the decision to
write one, nothing past it.
