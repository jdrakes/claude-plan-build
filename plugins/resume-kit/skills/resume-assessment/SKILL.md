---
name: resume-assessment
description: "Measures a resume: page count, bullet balance, how much is quantified, and which skills the postings the user supplies ask for that the page does not name. Use whenever the user asks how strong a resume or draft is, what gaps it has, or how a change compares to the last version, even if they do not say assessment."
---

# resume-assessment

Numbers about a resume, not opinions about it. Reads the content YAML and
the postings the user supplies; never edits either.

A gap is a skill postings ask for that the page does not name. It is
information, never an instruction to add a skill the user lacks: a true gap
costs less than an overstated stack. If they say they have it, that is a
content change through the normal draft workflow.

## Paths

Run from the user's resume directory. The content YAML, the posting file
and the output directory are theirs and resolve against the working
directory. The analysis scripts ship with this plugin and are always
addressed through `${CLAUDE_SKILL_DIR}`; the renderer lives in a sibling
skill and is addressed through `${CLAUDE_PLUGIN_ROOT}`.

## Run

1. Content file: the one the user names, else the newest `*.yaml` in the
   working directory.
2. Structure: `python3 ${CLAUDE_SKILL_DIR}/tools/analyze.py <content.yaml>`
   (bullets per job, quantified count, long bullets, unquantified ones).
3. Pages: `${CLAUDE_PLUGIN_ROOT}/skills/resume/bin/build <content.yaml> -o
   /tmp/a.pdf && pdfinfo /tmp/a.pdf | grep Pages`
4. Market text: a file the user supplies and names, one posting per line,
   each line being that posting's company, title and body run together.
   With no such file, say so, skip steps 4 and 5, and report structure and
   pages only; a gap list invented without postings would be the model's
   opinion, which is what this skill exists not to give.
5. Gaps: `python3 ${CLAUDE_SKILL_DIR}/tools/skill_gap.py <content.yaml>
   <market file>`. It only sees terms in
   `${CLAUDE_SKILL_DIR}/tools/keywords.yaml`; after a batch of new
   postings, `python3 ${CLAUDE_SKILL_DIR}/tools/keyword_staleness.py
   <market file>` lists frequent untracked terms to add by hand if they are
   real skills.
6. Report in chat, then offer to save it as
   `assessments/<date>-<content stem>.md` in the working directory for the
   next before/after.

## Report

```
# Resume Assessment, <content file>, <date>
## Structural health      pages, quantified rate, bullet balance, what stands out
## Skill gaps             ranked by frequency; each: pursue, or known and accepted
## Recommendations        concrete, ordered, each doable next session
```
