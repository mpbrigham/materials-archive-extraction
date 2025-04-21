# V1 Linear Flow – Intelligent Materials Intake

This version represents the first functional pipeline prototype with a simple, linear agent chain.

## Flow Summary

Supervisor → Metadata Extractor → Verifier → Response

Each agent operates in sequence and uses a tightly scoped prompt.

## Updates (Post-Patch)

- ✅ ConfidenceEnvelope-based fallback to MVS
- ✅ Prompt metadata (prompt_id, model_version) embedded in outputs
- ✅ DocumentLifecycleLog for state traceability
- ✅ Optional feedback handling via manual email routing

## Limitations

- Synchronous only
- Minimal failure recovery