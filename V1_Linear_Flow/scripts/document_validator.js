// Document Validator Function for Materials Library Extraction
// Used by the Document Validator node in n8n workflow

const documentValidator = function(items, runIndex) {
  // Wrap everything in try/catch to prevent undefined errors
  try {
    // Input validation with better error handling
    if (!items || items.length === 0) {
      const fallback_document_id = `doc-${Date.now()}-fallback`;
      return {
        json: {
          task_status: "failed",
          error_summary: "No items received by Document Validator",
          document_id: fallback_document_id,
          from_state: "RECEIVED",
          to_state: "FAILED",
          timestamp: new Date().toISOString(),
          agent: "document_validator_v1",
          notes: "No input data received"
        }
      };
    }
    
    const item = items[0];
    
    // Check if this is a retry attempt
    if (item.json && item.json.retry_extraction) {
      const documentId = item.json.document_id || `doc-${Date.now()}-retry`;
      const originalRequest = item.json.original_request || {};
      const errorSummary = item.json.error_summary || "Unknown error";
      const retryCount = item.json.retry_count || 1;
      
      // Create retry log entry
      const retryLogEntry = {
        document_id: documentId,
        from_state: "VALIDATION_FAILED",
        to_state: "RETRY_EXTRACTION",
        timestamp: new Date().toISOString(),
        agent: "document_validator_v1",
        notes: `Retry attempt ${retryCount}: ${errorSummary}`
      };
      
      // Return retry request with original data
      return {
        json: {
          ...originalRequest,
          retry_count: retryCount,
          error_summary: errorSummary,
          document_id: documentId,
          task: "retry_extraction",
          _lifecycle_log: [...((item.json._lifecycle_log || []), retryLogEntry)]
        }
      };
    }
    
    // Normal first-time processing
    // Validate that we have PDF content
    if (!item.binary || !item.binary.attachment_1 || item.binary.attachment_1.mimeType !== 'application/pdf') {
      const fallback_document_id = `doc-${Date.now()}-missing-pdf`;
      return {
        json: {
          task_status: "failed",
          error_summary: "Invalid or missing PDF attachment",
          document_id: fallback_document_id,
          from_state: "RECEIVED",
          to_state: "FAILED",
          timestamp: new Date().toISOString(),
          agent: "document_validator_v1",
          notes: "Missing PDF or invalid format"
        }
      };
    }
    
    // Extract email metadata with fallbacks
    const sender = (item.json && item.json.from) ? item.json.from : "unknown_sender";
    const subject = (item.json && item.json.subject) ? item.json.subject : "No Subject";
    const timestamp = new Date().toISOString();
    const document_id = `doc-${Date.now()}-${sender.replace(/[^a-zA-Z0-9]/g, '')}`;
    
    // Determine language (simplified - expand as needed)
    let language = "en";
    if (subject.match(/\b(nl|dutch|nederlands)\b/i)) {
      language = "nl";
    } else if (subject.match(/\b(de|german|deutsch)\b/i)) {
      language = "de";
    }
    
    // Create document lifecycle log entry
    const logEntry = {
      document_id: document_id,
      from_state: "RECEIVED",
      to_state: "INTERPRETED",
      timestamp: timestamp,
      agent: "document_validator_v1",
      notes: `Document language = '${language}'`
    };
    
    // Store the file path reference
    const file_path = (item.binary && item.binary.attachment_1 && item.binary.attachment_1.path) ? 
                      item.binary.attachment_1.path : 
                      `attachments/${document_id}.pdf`;
    
    // Return output for multimodal extraction
    return {
      json: {
        file_path: file_path,
        sender: sender,
        timestamp: timestamp,
        subject: subject,
        language: language,
        document_id: document_id,
        task: "extract_metadata",
        document_type: "supplier_material",
        retry_count: 0, // Initialize retry counter
        _lifecycle_log: [logEntry],
        // Add multimodal flag to indicate this is for multimodal processing
        multimodal_processing: true
      }
    };
  } catch (error) {
    // Fallback for any unexpected errors
    const fallback_document_id = `doc-${Date.now()}-error`;
    return {
      json: {
        task_status: "failed",
        error_summary: `Document validator error: ${error.message}`,
        document_id: fallback_document_id,
        from_state: "RECEIVED",
        to_state: "FAILED",
        timestamp: new Date().toISOString(),
        agent: "document_validator_v1",
        notes: `Unexpected error: ${error.stack || error.message}`
      }
    };
  }
};

module.exports = { documentValidator };
