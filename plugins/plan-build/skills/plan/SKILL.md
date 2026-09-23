---
name: plan
description: "Turn a request into a plan the user can approve, or a reasoned no. Use before any change that touches more than one file or more than one step, for any 'should we', and whenever the user says plan, even if they did not ask for a plan by name."
---

# Plan

One document, one approval. The user reads the Summary; the builder
reads the Tasks. Nothing is built here.

## 1. Verdict first

Before any question: **do it**, **do not**, or **not yet**, with a table:

| What it costs | What it fixes | What it breaks or risks |

Costs and fixes come from what was read, not guesses. A **do not** or
**not yet** ends with one sentence on what would change the answer, and
no document: a plan for work that should not happen invites doing it.

## 2. A plan or a design

- **A plan** drives one build. Where the project keeps a design page, the
  plan derives from the build's issue and the section of that page the
  issue names, and a plan that needs the design to change stops; the page
  is edited first. Where it does not, the plan derives from the request.
- **A design**, bigger than one build, is agreed in chat the same way and
  then written into the design page: what the system is for, its parts,
  its data, its operation; nothing about how it is built. The builds it
  implies become GitHub issues, one each, naming the section. The PR that
  closes the issue is the record.

## 3. The plan

```markdown
# <Title>

## Summary (what the user approves)
Verdict and its evidence. Goal, and the design section each task serves;
a task serving none is a proposal, listed apart. The simplest version that
would work and what this adds beyond it. How it is tested. Cost if wrong.

| # | Task | Model | Why |

## Constraints
Repo and branch state. Test command, or "none". What is not touched.

## Tasks
### Task N: <name>
- [ ] done
**Files.** Create / modify, exact paths.
**Produces.** What later tasks use from this one: names, signatures.
**Intent.** What to build and why. Complete code when known (then haiku).
**Accepts when.** A check someone can run.
**Model.** haiku | sonnet | opus. Omit for sonnet.
```

- A task is one commit's worth of work with its own test; the build gates
  each task on that test alone.
- Same-shape edits across several files are one task.
- haiku when the task contains the exact edit; opus when it touches several
  files or a stated invariant; omit otherwise.
- No placeholders: no "handle edge cases", no "similar to Task N". The
  builder that reads a task has no memory of this conversation.
- A decision a task depends on goes in that task's Intent.

## 4. Check

Every Summary claim has a task; every task has Files, Produces, Intent and
Accepts when; names agree across tasks.
