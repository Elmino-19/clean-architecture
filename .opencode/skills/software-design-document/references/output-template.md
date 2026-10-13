# Output template — `docs/sdd.md`

Use this exact section skeleton. The generated document is written in **Persian**
(the reader's language) with English technical terms inline — render each heading
and section in Persian. Every section that does not apply is closed with one line
("not in this system") — never removed.

```markdown
# Software Design Document — {product name}

## 1) Vision and scope
   1.1 The problem it solves
   1.2 Users and stakeholders
   1.3 In scope / out of scope

## 2) Requirements
   2.1 Main capabilities (numbered list)
   2.2 Business rules (each rule + its effect on a module)

## 3) Architecture principles
   3.1 Layers, import table and dependency direction
   3.2 Project and module tree
   3.3 The three error shapes
   3.4 Domain-specific rules (only these are optional)

## 4) Naming conventions
   (the naming table + project decisions such as the table prefix)

## 5) API contracts
   5.1 Envelope
   5.2 Pagination
   5.3 Error catalogue

## 6) Shared infrastructure
   (the shared infrastructure checklist)

## 7) Module catalogue
   For each module, four subsections in this order:
   7.x.1 domain          → Entities, ValueObjects, Enums, Domain Services, Exceptions
   7.x.2 application     → Ports, UseCases, Mappers, Exceptions, Utils
   7.x.3 infrastructure  → Models, Repositories, Caches, Services
   7.x.4 presentation    → Schemas, Dependencies, Routers, Docs

## 8) Composition root and data flow
   8.1 Wiring implementations to ports
   8.2 One request's flow: router → mapper → use case → port → adapter → model
   8.3 Module graph (DAG — no cycles) and the dependency table

## 9) Seed data and testing
   9.1 seed (idempotent)
   9.2 Test strategy: pure domain / use case with fake port / integration with the database
   9.3 Definition of Done per module

## 10) Open Questions
   Anything not asked of the product and assumed is listed here.
```
