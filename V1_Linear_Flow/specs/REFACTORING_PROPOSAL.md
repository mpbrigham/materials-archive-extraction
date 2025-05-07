# Refactoring Proposal: Data Structure Consolidation

## Context

The current V1 pipeline uses three redundant data structures to represent product information:
1. `field_extractions` - Complete extraction data with values, locations, and confidence
2. `metadata_json` - Flattened object with just values
3. `field_confidences` - Flattened mapping of field names to confidence scores

This redundancy creates maintenance overhead and potential for inconsistency.

## Proposed Change

Consolidate to a single `field_extractions` structure that serves as the canonical source of truth throughout the pipeline.

### Benefits

- **Simplicity**: Single source of truth for all product data
- **DRY principle**: Eliminates duplicate storage of the same information
- **Maintenance**: Reduces risk of data inconsistency between structures
- **Performance**: Slightly reduced memory usage and transformation overhead

### Considerations

- **Pipeline Consumers**: All stages of the pipeline (processor, verifier, formatter) would access data directly from the nested structure
- **Cognitive Load**: For LLM agents, the nested structure presents no cognitive burden
- **Interface Changes**: AGENT_INTERFACE_CONTRACTS.txt would need updating to reflect the consolidated structure

## Impact Assessment

### Low Risk Areas
- Processing logic (changes are straightforward access pattern updates)
- Verification logic (already uses field_extractions extensively)
- Error handling (remains functionally equivalent)

### Medium Risk Areas
- Interface contracts (requires updates to maintain consistency)
- Downstream consumers (may expect specific formats)

### High Risk Areas
- None identified (no complex logic depends on the specific structure)

## Implementation Plan

### Phase 1: Refactor Multimodal Extraction Agent
- Remove creation of redundant structures
- Simplify product representation
- Update metadata structure

### Phase 2: Update LLM Data Processor
- Revise field access patterns
- Update confidence assessment logic
- Modify fallback handling

### Phase 3: Update Multimodal Verifier
- Adjust verification to work with consolidated structure
- Update evidence generation

### Phase 4: Update Email Formatter
- Revise template to extract values directly

### Phase 5: Update Interface Contracts
- Update AGENT_INTERFACE_CONTRACTS.txt to reflect changes

### Phase 6: Test and Validate
- Verify functionality with single/multi-product documents
- Test fallback scenarios and error conditions

### Phase 7: Documentation Updates
- Update README and related documentation

## Timeline Estimate

- Implementation: 3 days
- Testing: 1.5 days
- Documentation: 0.5 days

Total: ~5 days

## Recommended Approach

1. Implement changes in a development branch
2. Perform thorough regression testing
3. Deploy with careful monitoring
4. Maintain temporary backward compatibility if needed

## Alignment with Design Guidelines

- **Simple**: Reduces complexity by eliminating redundant structures
- **Complete**: Maintains all necessary information in a single structure
- **Occam's Razor**: Provides the minimal solution that solves the problem
- **DRY**: Eliminates duplication of data
- **Maintenance burden**: Reduces long-term maintenance costs
- **Reversibility**: Changes are localized and reversible if needed

This proposal follows the "Modification Protocol" outlined in the design guidelines by providing a change summary for approval before implementation.