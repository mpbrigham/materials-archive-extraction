# Multi-Product Extraction Pipeline Tests

This directory contains tests for validating the multi-product extraction capabilities of the Materials Library pipeline.

## Test Overview

These tests validate the pipeline's ability to:

1. Extract metadata from documents containing multiple products
2. Process fields with varying confidence levels
3. Verify the accuracy of extracted information
4. Handle partial success scenarios

## Test Structure

### Expected Output Files

The `test_samples/expected` directory contains the expected JSON output for different test scenarios:

- `single_product.json`: Expected output for a document with one product
- `multi_product.json`: Expected output for a document with multiple products
- `mixed_confidence.json`: Expected output for a document with products of varying quality

### Sample PDF Documents

To run the tests, you need to provide sample PDF documents in the `test_samples/pdfs` directory:

- `single_product.pdf`: A document with one product
- `multi_product.pdf`: A document with multiple products
- `mixed_confidence.pdf`: A document with products of varying quality

## Running Tests

To run all tests:

```bash
node tests/run_pipeline_tests.js
```

## Test Results

Test results are saved in the `tests/results` directory and include:
- Individual test results with detailed field comparison
- A summary of all test executions

## Adding New Test Cases

To add a new test case:

1. Add the expected output JSON in `test_samples/expected/`
2. Add the corresponding PDF in `test_samples/pdfs/`
3. Update the TEST_CONFIG in `run_pipeline_tests.js`