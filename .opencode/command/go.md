---
description: Composite workflow runner — verbs + flags, parsed and dispatched by the orchestrator
agent: orchestrator
subtask: true
---

Execute this composite command line as the project orchestrator:

```text
$ARGUMENTS
```

Parse it per your grammar, resolve every missing argument with your defaults table,
understand the project once with CodeGraph, dispatch the role agents for the
requested stages (auto-inserting `plan`/`review`/`scan` where the pipeline requires
them, and announcing each insertion), then deliver the staged report and the final
table.

Examples:

```text
/go scan --modules key,example
/go scan,plan,craft,review -n 2 -- ماژول key را به CRUD کامل با تست برسان
/go mend --scope layer --layers application --kind transaction -- اصلاح commit در یوزکیس‌ها
/go explore --modules knowledge
/go plan --files app/modules/user/application/use_cases.py -- هدف آزاد
```

If a verb, a flag or an objective that the verb needs is missing, ask **one**
`question` with all gaps at once. Never invent scope.