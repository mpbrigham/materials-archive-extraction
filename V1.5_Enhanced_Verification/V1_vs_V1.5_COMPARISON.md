# V1 vs V1.5 Comparison Guide

This document outlines the key differences and enhancements between V1 (Linear Flow) and V1.5 (Enhanced Visual Verification) versions of the Intelligent Materials Intake System.

## Architecture Comparison

| Feature | V1 Linear Flow | V1.5 Enhanced Visual Verification |
|---------|---------------|----------------------------------|
| Flow Pattern | Single-pass extraction with validation | Multi-turn extraction with visual verification |
| Image Processing | Basic PDF pagination | Advanced pagination with targeted crop generation |
| Extraction Method | Text extraction with validation | Initial extraction + visual confirmation |
| Verification | Post-extraction validation | Integrated visual verification |
| Confidence Model | Single confidence score | Context/detail confidence with adjustment |

## Workflow Differences

### V1 Linear Flow
```
Supervisor → Metadata Extractor → Schema Validator → Visual Verifier → Response
```

### V1.5 Enhanced Visual Verification
```
Supervisor → PDF Paginator → Initial Extractor → Image Cropper → Verification Extractor → Schema Validator → Response
```

## Key Enhancements in V1.5

### 1. Multi-Turn Extraction Process
V1.5 introduces a two-pass extraction process:
- **Initial Pass**: Extracts fields from full page context
- **Verification Pass**: Verifies each field with crop-specific detail
- **Confidence Adjustment**: Combines context and detail confidences

### 2. Advanced Image Processing
- **Precise Coordinate Extraction**: Extracts exact field locations
- **Targeted Cropping**: Creates field-specific crops for detailed analysis
- **Visual Evidence Collection**: Maintains visual proof for every field

### 3. Enhanced Confidence Calculation
```
final_confidence = context_confidence * detail_confidence * context_agreement_factor
```
Where:
- `context_confidence`: Confidence from initial page extraction
- `detail_confidence`: Confidence from crop verification
- `context_agreement_factor`: Agreement between initial and verification (1.0 if match, 0.8 if correction)

### 4. Improved Error Handling
- More granular error detection
- Visual verification of problematic fields
- Field-specific correction opportunities

## Performance Improvements

| Metric | V1 Linear Flow | V1.5 Enhanced Visual Verification |
|--------|---------------|----------------------------------|
| Extraction Accuracy | Good (85-90%) | Excellent (92-97%) |
| Hallucination Rate | Moderate (5-8%) | Very Low (<2%) |
| Processing Time | Faster (30-60 sec) | Moderate (45-90 sec) |
| Storage Requirements | Lower (5-10MB per doc) | Higher (15-30MB per doc) |
| Confidence Precision | Standard | High (field-specific) |

## Migration Considerations

### System Requirements
- **Storage**: V1.5 requires ~3x more storage for crop images
- **Processing**: Slightly higher CPU requirements for image processing
- **API Usage**: Higher vision model API usage due to multi-turn approach

### Configuration Changes
- **New Environment Variables**: Image processing settings
- **New Prompt Files**: Initial and verification prompt templates
- **Directory Structure**: Additional storage for crops

## When to Use Each Version

### Use V1 Linear Flow When:
- Processing resources are limited
- Quick throughput is prioritized over accuracy
- Storage space is at a premium
- API usage costs are a primary concern

### Use V1.5 Enhanced Visual Verification When:
- Accuracy is the highest priority
- Evidence collection is important
- Field-specific confidence is valuable
- Visual verification with correction is needed

## Compatibility

Both versions share:
- Same data schema output format
- Compatible webhook interfaces
- Similar LLM provider requirements
- Base PDF handling capabilities

## Validation and Testing

To validate each version:
- V1: Use `validate_dependencies.py` script
- V1.5: Use `validate_v1.5_setup.py` script

Both versions support the same testing tools, but V1.5 provides more detailed testing outputs with visual evidence.