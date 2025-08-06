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
    """Validate PDF attachments"""
    
    try:
        data = await request.json()
        return document_validator.process(data)
    except Exception as e:
        # Return state with error, don't crash
        return {
            "status": "Document Validator failed", 
            "errors": [f"[Document Validator] Unexpected error: {str(e)}"]
        }

@app.post("/extract")
async def extract(request: Request):
    """Extract material data using LLM"""
    
    try:
        data = await request.json()
        return llm_extraction.process(data)
    except Exception as e:
        # Return state with error, don't crash
        return {
            "status": "LLM Extraction failed",
            "errors": [f"[LLM Extraction] Unexpected error: {str(e)}"]
        }

@app.post("/process")
async def process_results(request: Request):
    """Process results into email format"""
    
    try:
        data = await request.json()
        return result_processor.process(data)
    except Exception as e:
        # Return state with error, don't crash
        return {
            "from": "",
            "to": "",
            "subject": "Materials Extraction Failed",
            "body": f"<p>An unexpected error occurred: {str(e)}</p>"
        }

@app.get("/health")
async def health():
    """Health check endpoint"""
    
    return {"status": "healthy"}
