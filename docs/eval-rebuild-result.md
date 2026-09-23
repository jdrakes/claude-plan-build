# The rebuilt eval: what it measured, and why half of it is unreadable

A record of the second attempt. It is better than the first and it is still
not a usable instrument. Three defects are named below; all three are in the
suite, not in the skill.

## The command

```
claude plugin eval plugins/plan-build --eval-dir evals2 --trust-plugin \
  --ablation none --max-cost-usd 10 --json docs/eval-rebuild-result.json
```

Run 2026-09-23. 16 cases, 3 runs each, 48 runs, 781 seconds, 4.08 USD.
Zero runs errored and the result is not partial, so every number below is a
real measurement of what was asked.

## The result

| Half | Cases passed |
|---|---|
| Hand back | **6 of 8** |
| Plan | **0 of 8** |
| Overall | 0.479 |

| Label | Case | Score |
|---|---|---|
| hand-back | add-a-version-flag | 1.00 |
| hand-back | column-order-wrong | 1.00 |
| hand-back | drop-quiet-flag | 1.00 |
| hand-back | truncate-long-cells | 1.00 |
| hand-back | what-does-store-do | 1.00 |
| hand-back | why-is-the-table-ragged | 1.00 |
| hand-back | is-there-a-test-for-padding | 0.00 |
| hand-back | rename-to-table | 0.00 |
| plan | should-we-split-cli-from-core | 0.67 |
| plan | no-error-handling-anywhere | 0.33 |
| plan | should-we-add-a-config-file | 0.33 |
| plan | sorting-filtering-and-paging | 0.33 |
| plan | add-csv-and-json-output | 0.00 |
| plan | output-is-unreadable | 0.00 |
| plan | should-we-use-a-real-table-lib | 0.00 |
| plan | store-is-too-slow | 0.00 |

The first suite scored 5 of 10 on its must-fire half and 10 of 10 on its
must-not-fire half, overall 0.767. It did produce a split; what made it
unreadable was that it ran a single arm with no counterfactual, and that most
of the must-not-fire prompts were mislabelled, so the perfect half measured
nothing. This suite fixes the labelling method and adds a judge that reads
the response. It does not yet produce a readable number: the plan half below
cannot be read, for the three reasons that follow.

## Defect 1: the fixture is described but absent

Scaffolding was abandoned because `scaffold_script` does not execute, so
the fixture is described to the model through `append_system_prompt`
instead. The model therefore knows the code exists but cannot open it.

**37 of the 48 responses open by complaining that the working directory is
empty.** A representative opening:

> "I couldn't open the files: `src/format.py` doesn't exist ... and the
> directory looks empty. This answer is based on your description of the
> code, not on the code itself."

That apology is the first thing every judge reads. It is noise in the signal
and it plausibly pushes judges toward failure. Nothing in the plan half can
be trusted while it is there.

## Defect 2: the graders contradict themselves on a "should we"

Every should-we grader passes "a plan document, or an explicit reasoned
verdict not to do the work", and fails a response that "answers as though
the request were a single small change".

A correct answer to a should-we is frequently both at once. From
`should-we-use-a-real-table-lib`, which three judges failed unanimously on
all three runs:

> "**My answer is don't add a library.**" ... a cost table ... "That's one
> or two edits, which is too small to need a written plan." ... "**What
> would change my answer:** if you later need wrapping inside cells,
> Unicode wide-character widths, or column alignment by type..."

That is exactly what the skill prescribes for a negative verdict: reasons,
no document, and one sentence on what would change the answer. It satisfies
the pass clause and trips the fail clause simultaneously.

The deeper error is the label, not the wording. **A should-we case cannot be
labelled plan-or-hand-back in advance**, because which one is correct
depends on the verdict, and the verdict is the thing under test. Should-we
cases need a third label: "gives a reasoned verdict either way".

## Defect 3: the fixture may be too small to need a plan at all

The fixture is about 150 lines across three files. In a codebase that size,
almost no request needs a document a subagent builds from, so the plan class
may be unsatisfiable by construction.

One result cuts the other way and is worth keeping. From
`sorting-filtering-and-paging`, a three-feature request:

> "**Verdict: do it.** It's also too small for a plan, so I'd skip the plan
> document and just make the edits in this session."

Sorting, filtering and paging is three features. Calling that one or two
edits looks like section `1a` reaching too far. That is a signal about the
skill rather than the suite, and it is the single most interesting thing
this run produced. It cannot be confirmed while defect 1 stands, because the
same response also could not see the code.

## What a third attempt needs

1. A fixture the model can actually open. Either a working scaffold
   mechanism, or the relevant file contents inlined in the case prompt,
   accepting that prompts then stop matching real length.
2. A third label for should-we cases, scored on whether a reasoned verdict
   was given, not on whether a document appeared.
3. A fixture large enough that some requests genuinely need more than two
   edits, or a plan class drawn only from requests that are unambiguously
   multi-task.

## What was not done

Nothing was tuned to improve the number. No grader was reworded and no case
relabelled after seeing the result. The instruction for this task was to
report what came back, including a failure, and that is what this is.
