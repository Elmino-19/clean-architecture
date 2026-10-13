# Workflow, validation and anti-patterns

## Workflow

1. **Take input.** If only a rough idea was given, ask a few key questions before
   writing (who uses it, what is stored, what must happen). Do not guess — or
   record the guess in Open Questions.
2. **Extract candidate modules.** Group the requirements. Show the list to the
   user and get confirmation **before** writing the document.
3. **Scaffold.** Every module = four folders (`references/architecture.md`). A
   file that is not needed yet is kept with a reason comment.
4. **Write the document** using `references/output-template.md`. Write it in
   Persian with English technical terms.
5. **Validate** against the checklist below.
6. **Note provenance.** At the end of the document, state which skill was used
   and what was assumed.

## Validation checklist

- [ ] Every module has exactly four folders, and every file has a decision
      (content, or a reason for being empty).
- [ ] No endpoint without a use case; no use case without a port; every port has
      an implementation.
- [ ] `domain` has no external import (no FastAPI, SQLAlchemy, Pydantic).
- [ ] No module depends on another module's `infrastructure`/`presentation`.
- [ ] The module graph is acyclic.
- [ ] No `commit` inside a repository; `flush` only.
- [ ] The three error shapes are used in the right places
      (`except StandardException` first).
- [ ] The JSON contract is snake_case throughout.
- [ ] No physical deletes; soft delete everywhere.
- [ ] No name copied from a reference project — all come from the product.

## Anti-patterns

- ❌ Copying modules or names from a reference project.
- ❌ Business logic inside a router or repository.
- ❌ Importing ORM models or FastAPI inside `domain`.
- ❌ `commit` inside a repository (and any `IUnitOfWork` — it does not exist here).
- ❌ `Any` or ambiguous types.
- ❌ An endpoint without a defined error contract.
- ❌ Physical deletes.
- ❌ camelCase in JSON.
- ❌ Guessing a requirement without recording it in Open Questions.
- ❌ Deviating from the four-layer structure, or merging layers for convenience.
