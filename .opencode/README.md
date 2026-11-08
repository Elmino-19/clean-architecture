# Workflow framework — commands and agents

> Full reference for the bundle in `.opencode/`. Persian translation:
> [README.fa.md](README.fa.md).
>
> If you read one thing: **Quick start** and **Grammar**.

---

## 0. Quick start

```text
/go scan --modules key,example                    ← find deviations, read-only
/explore --modules knowledge                      ← explain architecture and flow
/plan  --modules user -n 2 -- هدف آزاد             ← ordered task list, no code
/craft --modules example -- ماژول نمونه را کامل کن    ← plan → coder×3 → reviewer
/mend  --modules key -- اصل commit در یوزکیس‌ها      ← scan → planner → editor×N → reviewer
/review --modules key                             ← verify only, never fix
/design -- محصول جدید                             ← docs/sdd.md only
```

---

## 1. The shape

```text
user ──▶ /go | /scan | /explore | /plan | /craft | /mend | /review | /design
             │  (8 thin files, no logic)
             ▼
         orchestrator  (the secretary)
         parses · applies defaults · one CodeGraph pass · dispatches · reports
             │  subagent
             ├── analyzer   (read-only)          ── analyze
             ├── planner    (writes .me/runs)    ── plan
             ├── coder      (writes app/, test/) ── implement new
             ├── editor     (writes app/, test/) ── implement fixes
             ├── reviewer   (runs make test/lint)── verify
             └── sdd-writer (writes docs/)       ── design (separate branch)
```

The orchestrator has **no** permission to read code, write code or load a skill. It
knows the *catalog* (skill names + one-line purpose, agent names + scope) and nothing
else. That is what keeps its token cost flat and its behaviour predictable.

---

## 2. Grammar

```text
<verbs> [--app be|both] [--scope all|module|layer|file] [--modules a,b]
        [--layers domain,application,infrastructure,presentation] [--files path,…]
        [--kind word,…] [-n N] [-- free-text objective]
```

| Token | Values | Meaning |
|---|---|---|
| `verbs` | `explore`, `scan`, `plan`, `craft`, `mend`, `review`, `design` | stages to run, in order |
| `--app` | `be` \| `both` | which application side (this repo is backend-only) |
| `--scope` | `all` \| `module` \| `layer` \| `file` | the unit of work |
| `--modules` | comma list | module names under `app/modules/` |
| `--layers` | comma list | the four DDD layers |
| `--files` | comma list | explicit paths |
| `--kind` | comma list | restrict a scan to specific rule categories |
| `-n` | integer | number of workers (parallel partitions) |
| `-- …` | free text | the objective; never parsed |

Anything after `--` is the objective and is never interpreted as a flag. An unknown
verb or flag is **never** guessed: the orchestrator stops and asks.

---

## 3. Defaults (the exception table)

Missing arguments are resolved silently and never widen the *intent*.

| Missing | Default |
|---|---|
| verbs | ask (which verb?) |
| `--app` | `both` → the whole repository |
| `--scope` | `all` → every module under `app/modules/` |
| `--modules` | every module |
| `--layers` | all four |
| `--kind` | every kind |
| `-n` | **3** |
| objective for `scan` / `explore` / `review` | derived from the scope — nothing to ask |
| objective for `craft` / `mend` / `plan` | **one** `question`, offering the scope-derived draft |
| `-n` > number of work items | clamp, and say so in the report |
| `.codegraph/` missing | one line, then stop |
| a worker hits its step cap | report the partial status, ask "continue?" |

Auto-inserted stages, announced in the report and never hidden:

- `craft` / `mend` without `plan` → `plan` runs first.
- `craft` / `mend` without `review` → `review` runs last.
- `mend` without `scan` → `scan` runs first (you cannot fix unnamed findings).

---

## 4. Pipeline and the task list

```text
analyze (explore|scan) → plan → implement (craft|mend) → verify (review) → report
```

The planner writes, under `.me/runs/<timestamp>-<slug>/`:

| File | Writer | Purpose |
|---|---|---|
| `plan.md` | planner | goal, current state, ordered steps, fixed boundaries, worker partition, verification, risks |
| `tasks-1.md … tasks-N.md` | planner | one file **per worker** — ownership is unique, so parallel ticks cannot collide |
| `scan.md` / `map.md` | analyzer | the findings or the architecture map |
| `review.md` | reviewer | done / partial / not done + the real `make test` / `make lint` output |

Item format:

```markdown
- [ ] #3 · app/modules/key/application/use_cases.py
      operation: add GetKeyUseCase with an is_active filter
      rules: flush only, no commit; error shape from references/cross-cutting.md
      accepts: `make test` green; use case covered by a fake-repository unit test
```

**Partitioning rules for `-n > 1`**

- One work item belongs to **exactly one** worker. A module's file set is never split
  between two workers.
- Shared registration points (`migrations/env.py`, `app/app.py`,
  `migrations/versions/**`) are assigned to one worker and flagged in its task file.
- Workers of one stage run in parallel; stages run sequentially.

---

## 5. Roles, strictly separated

| Agent | Skill | `steps` | May write | Runs tests | Forbidden |
|---|---|---|---|---|---|
| `orchestrator` | none (catalog only) | 25 | `.me/**` | no | reading code, writing code, loading a skill |
| `analyzer` | `backend-development` | 20 | `.me/**` | no | any fix, any dispatch |
| `planner` | `backend-development` | 15 | `.me/**` | no | writing code |
| `coder` | `backend-development` | 40 | `app/**`, `test/**`, `migrations/versions/**`, `migrations/env.py`, `.me/**` | no | anything outside its task file |
| `editor` | `backend-development` | 30 | same as coder | no | widening scope, unlisted fixes |
| `reviewer` | `backend-development` | 20 | `.me/**` | **yes, once** | fixing anything |
| `sdd-writer` | `software-design-document` | 25 | `docs/**` | no | production code |

The contract between roles:

- The analyzer and planner **write the task list**.
- The coder and editor **only follow it**, item by item, and tick `- [x]` when done.
- The reviewer **only checks** whether the ticked items are really done; it never
  repairs, it hands open items back for a `mend` run.
- `make test` and `make lint` run **once per run**, in the reviewer.

---

## 6. Dispatch protocol

Every `subagent` call is self-contained — workers share no context:

```text
agent:         coder
description:   craft — modules key, example
prompt:        ROLE: coder
               RUN: .me/runs/20260101-1200-key-crud/
               TASK FILE: .me/runs/20260101-1200-key-crud/tasks-2.md
               SCOPE: modules=[key] layers=[domain,application] files=[] kind=[]
               OBJECTIVE: add CRUD with cache tombstones
               OWNERSHIP: you own exactly these paths: app/modules/key/**
               FORBIDDEN: no other file; no test runs; report ≤10 lines
```

Each worker returns at most **10 lines**: items done, items open, files touched, test
status. The orchestrator never opens their files.

---

## 7. Reporting

After each stage:

```text
stage 2/4 · plan — planner · 11 items · tasks-1..3.md
```

At the end:

```text
| Stage | Agent | Scope | Result | Verification |
|---|---|---|---|---|
| analyze | analyzer | modules key, example | 14 findings (2 blocker) | — |
| plan | planner | same | 11 items / 3 task files | — |
| implement | coder ×3 | same | 9/11 done | — |
| verify | reviewer | diff + task list | 2 items open | make test ✓ · make lint ✓ |

Open items: <list>   ·   Next step: <what to run next>
```

A stage is never reported as done without the worker's own words or the real command
output.

---

## 8. CodeGraph first

Every role follows the repository rule: the **first** tool call is `codegraph_explore`
(or `codegraph explore "<question>"` in the shell). `grep`/`rg` are forbidden in every
agent; `read`/`glob` are only for files CodeGraph names. The orchestrator makes
**exactly one** CodeGraph call per run, at the start.

If `.codegraph/` does not exist, the run stops with one line — never a silent fallback
to text search.

---

## 9. Configuration and reload

Agents live in `.opencode/agents/`, commands in `.opencode/commands/`. Both directories
are loaded automatically when the repository is the working directory. To use the same
bundle in every project:

```bash
make opencode      # copies skills, commands and agents into ~/.config/opencode/
```

OpenCode V2 **reloads configuration automatically** after a change under `.opencode/`
or `opencode.jsonc`. Use `/reload` only to force a full reload.

---

## 10. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Command missing from the palette | the command file was not saved under `.opencode/commands/` | save it there, then run `/reload` |
| "Which verb?" was asked | no verb given to `/go` | add a verb, or use a preset |
| 3 workers ran instead of your number | `-n` omitted (default is 3) | add `-n N` at the end |
| A stage ran that you did not name | pipeline auto-insertion | announced in the report; use a preset to fix the verb set |
| The orchestrator refused to read a file | by design — it never reads code | ask a preset/worker for the detail, or `@mention` a worker directly |
| `make test` appears twice | a worker ran it (stale config) | run `/reload` and check the worker's `shell` permissions |