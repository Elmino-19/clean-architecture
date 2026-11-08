<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->

## Workflow commands and agents

Work in this repository goes through the orchestrator, never ad-hoc:

```text
/go <verbs> [flags] [-- objective]     ← composite entry point
/scan · /explore · /plan · /craft · /mend · /review · /design   ← presets
```

- Every command runs on `agents/orchestrator.md`. It parses the line, applies the
  defaults table, understands the project once via CodeGraph, dispatches the role
  agents, and reports each stage.
- The orchestrator **cannot** read code, write code or load a skill — its permissions
  deny it. It only knows the skill/agent catalog.
- Roles: `analyzer` (read-only) → `planner` (task list) → `coder` (new code) /
  `editor` (fixes) → `reviewer` (gate: `make test` + `make lint`, once). Workers act
  only on their own task file and tick items; `reviewer` never fixes.
- Full reference: `.opencode/README.md` (English) and `.opencode/README.fa.md`
  (Persian), plus the table of contents in `README.md` / `README.fa.md`.

## Verification

- `make test` and `make lint` are run **once**, by the `reviewer`, at the end of a run.
  Workers never run them.
- Never report a stage as done without the worker's own words or the real command
  output.

## Reload

OpenCode V2 reloads agents, commands, skills, and `opencode.jsonc` automatically
after a save. Use `/reload` only to force a full reload after a change that did not
apply.
