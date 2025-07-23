# Materials Archive Extraction

A modular system for extracting structured metadata from architectural materials PDFs using LLMs.

## Overview

This repository provides multiple pipeline implementations for automated PDF processing and metadata extraction. Each pipeline offers different approaches to solving the same core problem: converting unstructured PDF documents into structured, searchable metadata.

## Available Pipelines

| Pipeline | Platform | Description |
|----------|----------|-------------|
| [`v0_initial_flow_n8n`](./v0_initial_flow_n8n) | n8n | Email-triggered extraction with automated response |
| [`v0_initial_flow_ap`](./v0_initial_flow_ap) | ActivePieces | Email-triggered extraction (alternative platform) |
| [`v0_simplified_flow`](./v0_simplified_flow) | n8n | Simplified webhook-based extraction |
| [`v1_linear_flow`](./v1_linear_flow) | n8n | Linear processing with Python webhook handler |
| [`v1.5_enhanced_verification`](./v1.5_enhanced_verification) | n8n | Multi-turn verification with evidence collection |
| [`v2_modular_expansion`](./v2_modular_expansion) | n8n | Modular agent architecture |
| [`v3_intent_driven_minimalism`](./v3_intent_driven_minimalism) | n8n | Intent-based stateless dispatch |

## Project Structure

```
├── v0_initial_flow_n8n/      # Production-ready email pipeline
├── v0_initial_flow_ap/       # ActivePieces alternative
├── v1_linear_flow/           # Webhook-based linear flow
├── v1.5_enhanced_verification/ # Enhanced accuracy pipeline
├── v2_modular_expansion/     # Modular architecture
├── v3_intent_driven_minimalism/ # Intent-driven approach
├── samples/                  # Example PDFs and outputs
├── evaluation/              # Evaluation tools and metrics
└── notebooks/               # Jupyter notebooks for analysis
```

## Core Components

Each pipeline typically includes:
- **Prompts**: LLM instructions for extraction
- **Schema**: JSON schema for structured output
- **Workflow**: Platform-specific workflow definition
- **Email Templates**: Response formatting
- **Docker Configuration**: Containerized deployment

## Technology Stack

- **Workflow Platforms**: n8n, ActivePieces
- **LLM**: Google Gemini AI
- **Infrastructure**: Docker, Docker Compose
- **Languages**: JavaScript, Python

## Getting Started

Choose a pipeline based on your needs:

- **Email-based processing**: Start with `v0_initial_flow_n8n` or `v0_initial_flow_ap`
- **API/Webhook integration**: Use `v1_linear_flow`
- **High accuracy requirements**: Consider `v1.5_enhanced_verification`
- **Complex workflows**: Explore `v2_modular_expansion` or `v3_intent_driven_minimalism`

Each pipeline directory contains its own README with specific setup instructions.

## Repository Standards

- All pipelines follow consistent schema definitions
- Docker-based deployment for all implementations
- Comprehensive documentation in each pipeline directory
