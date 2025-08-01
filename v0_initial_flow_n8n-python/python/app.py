#!/usr/bin/env python3
"""
FastAPI microservice for materials extraction pipeline
"""

from fastapi import FastAPI, Request
import document_validator
import llm_extraction
import result_processor
    
app = FastAPI(title="Materials Extraction Service")

@app.post("/validate")
async def validate(request: Request):
    """Validate PDF attachments from email"""
    data = await request.json()
    return document_validator.process(data)

@app.post("/extract")
async def extract(request: Request):
    """Extract material data using LLM"""
    data = await request.json()
    return llm_extraction.process(data)

@app.post("/process")
async def process_results(request: Request):
    """Process results into email format"""
    data = await request.json()
    return result_processor.process(data)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
