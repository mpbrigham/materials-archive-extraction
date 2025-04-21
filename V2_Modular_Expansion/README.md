# V2 Modular Expansion – Intelligent Materials Intake System (IMIS)

This version introduces modular agent design with observability and fallback logic.

## Workflow

```mermaid
flowchart TD
    A[Intake Orchestrator] --> B[Preprocessing Agent]
    B --> C{Valid File?}
    C -->|Yes| D[Metadata Extraction Agent]
    C -->|No| E[Routing Error Handler]
    D --> F[Verifier Agent]
    F --> G[Supervisor Response Agent]
```

## Features

- Asynchronous orchestration
- Fallback logic (CE-driven)
- Prompt versioning
- Feedback loop support
- DocumentLifecycleLog enabled