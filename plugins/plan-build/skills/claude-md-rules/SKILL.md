---
name: claude-md-rules
description: Use when adding, editing or reconsidering a rule in CLAUDE.md, AGENTS.md or any instructions file one of those points at, and when a mistake is about to become a new rule. Filters the rule before it is added, and flags a file that has grown past the point where instructions are followed.
---
# CLAUDE.md Rule Gatekeeper
Most CLAUDE.md files rot the same way: each mistake Claude makes turns into a new appended rule, the file grows past the point where instructions get followed reliably, and nobody prunes it. This skill is a checkpoint that runs *before* a rule gets added, plus a periodic audit of the file as a whole.
## Before adding any rule, run it through this filter
1. **Is this universal?**
   Will it apply to most tasks in this repo, or just one workflow/feature/directory?
   - Universal → CLAUDE.md.
   - Narrow → a separate reference doc (e.g. `agent_docs/database_schema.md`, `agent_docs/deploy.md`), with a one-line pointer in CLAUDE.md ("For database work, read agent_docs/database_schema.md first"). A pointed-at doc is loaded on the same terms as CLAUDE.md, so every rule in it goes through this same filter; moving a rule there is not a way around it.
2. **Could a deterministic tool do this instead?**
   Formatting, linting, import order, naming conventions, "always run X before committing" — these belong in a linter config, a pre-commit hook, or a Stop hook, not in prose Claude has to remember every time.
   - If yes → set up the tool/hook, don't write the rule. Mention this tradeoff to the user if they're proposing a style rule.
3. **Would Claude already infer this from the codebase?**
   If the pattern is visible and consistent in existing code, it doesn't need to be stated — in-context learning from the surrounding files handles it. Only write down what isn't already obvious from reading the code.
4. **Is this a one-off patch for a single mistake?**
   This is the most common anti-pattern: Claude does something wrong once, and the instinct is to append a rule like "don't do X" that only makes sense in light of that specific incident. Before adding:
   - Ask whether this generalizes into a real, reusable rule, or whether it's really a one-time correction that doesn't need to live in the file permanently.
   - If it doesn't generalize cleanly, prefer *not* adding it — flag this tension to the user rather than silently appending.
5. **Can I point instead of paste?**
   Prefer a `path:line` reference or "check X before doing Y" over inlining content (schemas, API details, long explanations) that will drift out of date. CLAUDE.md should orient, not document.
When a proposed rule fails checks 2-4, say so plainly and suggest the better home for it (hook, reference doc, or "let's not add this"), rather than adding it anyway just because the user asked.
## Periodic file audit
Whenever you're touching CLAUDE.md for another reason, take a moment to sanity-check the file as a whole and flag concerns to the user (don't restructure unprompted):
- **Length**: aiming for roughly 60-100 lines, uncomfortable past ~300. If it's grown large, look for what can move into `agent_docs/` with a pointer left behind.
- **Instruction budget**: all instructions in context (system prompt + CLAUDE.md + rules + skills) degrade together once the total gets large — a commonly cited rough ceiling is 150-200 instructions combined. Treat this as directional, not a hard number, but if things feel crowded, that's a signal to prune rather than keep appending.
- **Staleness**: any rule that references a mistake from months ago, a since-removed workflow, or an incident nobody remembers the context for — candidate for removal.
- **Duplication with tooling**: any rule that's really a linter/formatter rule that never got automated — candidate for converting into a hook instead of prose.
## How to respond when the user proposes a rule
1. Run the filter above.
2. If it passes cleanly: add it, in the right file, phrased concisely.
3. If it fails one or more checks: say which one, explain briefly why, and propose the alternative (hook / reference doc / skip it). Still let the user override if they insist — this is a filter, not a veto.
4. Don't silently "improve" the wording or scope of what they asked for beyond what's needed to place it correctly.
