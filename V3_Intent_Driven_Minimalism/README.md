# V3 – Intent-Driven Minimalism

This is the production-grade design for the IMIS pipeline, built on modular, stateless agent contracts with context-aware routing.

## Design Highlights

- Stateless-by-default, state-aware-by-design
- CE-driven fallback (ok | uncertain | fail)
- All messages carry intent + context
- Prompt routing based on layout signature
- Versioned prompt metadata

## Full Support Includes

- `DocumentLifecycleLog_template.json`
- `AGENT_INTERFACE_CONTRACTS_v3.txt`
- `CONFIDENCE_POLICY_GUIDELINES_v3.txt`
- `feedback_loop_spec.txt`

This is the recommended base for scale deployment.