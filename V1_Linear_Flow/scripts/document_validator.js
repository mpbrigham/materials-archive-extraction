// Document Validator Function for Materials Library Extraction
// Used by the Document Validator node in n8n workflow

const documentValidator = function(items, runIndex) {
  // Wrap everything in try/catch to prevent undefined errors
  try {
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

      const retryLogEntry = {
        document_id: documentId,
        from_state: "VALIDATION_FAILED",
        to_state: "RETRY_EXTRACTION",
        timestamp: new Date().toISOString(),
        agent: "document_validator_v1",
        notes: `Retry attempt ${retryCount}: ${errorSummary}`
      };

      return {
        json: {
          ...originalRequest,
          retry_count: retryCount,
          error_summary: errorSummary,
          document_id: documentId,
          task: "retry_extraction",
          _lifecycle_log: [...(item.json._lifecycle_log || []), retryLogEntry]  // ✅ FIXED HERE
        }
      };
    }

    // First-time processing
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

    const sender = item.json?.from || "unknown_sender";
    const subject = item.json?.subject || "No Subject";
    const timestamp = new Date().toISOString();
    const document_id = `doc-${Date.now()}-${sender.replace(/[^a-zA-Z0-9]/g, '')}`;

    const logEntry = {
      document_id,
      from_state: "RECEIVED",
      to_state: "INTERPRETED",
      timestamp,
      agent: "document_validator_v1",
      notes: `Document validated successfully`
    };

    const file_path = item.binary?.attachment_1?.path || `attachments/${document_id}.pdf`;

    return {
      json: {
        file_path,
        sender,
        timestamp,
        subject,
        document_id,
        task: "extract_metadata",
        document_type: "supplier_material",
        retry_count: 0,
        _lifecycle_log: [logEntry],
        multimodal_processing: true
      }
    };
  } catch (error) {
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
