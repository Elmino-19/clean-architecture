---
name: software-design-document
description: Use when writing a Software Design Document (SDD) for a software system, especially a FastAPI backend on Clean Architecture + DDD with the four-layer module layout (domain/application/infrastructure/presentation). Triggers on SDD, software design document, design doc, clean architecture, DDD, bounded context, module, architecture layers. For implementing code use backend-development instead.
---

# Software Design Document (SDD)

Produces a reusable **design document** for any software system. The template
fixes the architecture and conventions; everything product-specific is extracted
from the current product, never copied from a reference project.

Read only what you need:

| File | Read it for |
|---|---|
| `references/architecture.md` | the fixed rules: layers, import direction, module tree, error shapes, transactions |
| `references/conventions.md` | naming table, API contracts (envelope, pagination, errors), shared infra checklist |
| `references/output-template.md` | the exact `docs/sdd.md` section skeleton |
| `references/workflow.md` | the process, the validation checklist, and anti-patterns |

## Fixed vs. variable

| Fixed (mandatory) | Variable (extracted from the product) |
|---|---|
| Clean Architecture + DDD, four layers per module | module names and boundaries |
| the module tree and import direction | each file's content |
| error shapes (3-branch / 2-branch / never-raise) | domain-specific rules |
| naming conventions and snake_case API | endpoints, tables, error messages |
| transaction model | requirements and features |

**Golden rule:** anything tied to one product — a module name, a table name, a
domain error code — must come from the product description, not from this
template. If something does not fit the product, record it under
"domain-specific rules", not as a fixed rule.

## Workflow

1. **Take input.** If only a rough idea was given, ask a few key questions (who
   uses it, what is stored, what must happen). Do not guess — or log the guess.
2. **Extract candidate modules.** Group the requirements; show the list to the
   user and get confirmation **before** writing the document.
3. **Scaffold** every module as four folders (see
   `references/architecture.md`). A file that has no content yet is kept with a
   reason comment, not deleted.
4. **Write the document** using `references/output-template.md`. Write it in
   **Persian** with English technical terms (this is the reader's language; change
   it only if the user asks).
5. **Validate** against the checklist in `references/workflow.md`.
6. **Note the provenance** at the end: which skill was used and what was assumed.

## Output

`docs/sdd.md`. This skill produces a **document, not code**. If code is also
wanted, finish the document, get sign-off, then load `backend-development`.

## Scope note

This template deliberately excludes complex auth (nested JWT, cookies, token
rotation) and WebSockets — those are product decisions, not architecture rules.
Add them to the document if the product needs them; the four-layer structure and
the contracts stay fixed.
