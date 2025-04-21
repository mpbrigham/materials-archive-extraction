# V3 – Intent-Driven Minimalism

Production-grade IMIS pipeline using intent-routing, fallback logic, and modular prompts.

## Flow Diagram

```mermaid
flowchart TD
    A[IN: Email/Webhook] --> B[Intake Agent]
    B --> C[Interpreter Agent]
    C --> D{Confidence OK?}
    D -->|Yes| E[Verifier Agent]
    D -->|No| F[Fallback to MVS]
    E --> G{All Verified?}
    G -->|Yes| H[Outbound Agent → Archive + Email]
    G -->|No| I[Flagged → Feedback Email]
```

## Highlights

- CE scoring and fallback routing
- Prompt versioning metadata
- Audit trail via DocumentLifecycleLog
- Stateless-by-default, state-aware-by-design