// JSON Schema Validator for Material Metadata
// This module validates the metadata structure and formats before passing to the verifier agent

/**
 * Validates extracted metadata against JSON schema
 * @param {Object} items - Input items from n8n workflow
 * @param {number} runIndex - Current run index
 * @returns {Object} Validation results with flags for next steps
 */
const validateMetadataSchema = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Schema Validator");
  }
  
  const item = items[0];
  
  // Check if we already have a task failure
  if (item.json.task_status === "failed") {
    return item; // Pass through the failure
  }
  
  const metadata = item.json.metadata_json;
  const retryCount = item.json.retry_count || 0;
  const documentId = item.json.document_id;
  const originalRequest = item.json.original_request || {};
  
  // Initialize validation results
  const validationResults = {
    isValid: true,
    errors: [],
    missingRequiredFields: [],
    formatErrors: [],
    hasMvs: false
  };
  
  // 1. Required fields validation
  const requiredFields = ['name', 'brand', 'category', 'dimensions'];
  const mvsFields = ['name', 'dimensions', 'brand', 'summary'];
  
  validationResults.missingRequiredFields = requiredFields.filter(field => 
    !metadata || metadata[field] === undefined || metadata[field] === null || metadata[field] === ''
  );
  
  if (validationResults.missingRequiredFields.length > 0) {
    validationResults.isValid = false;
    validationResults.errors.push(`Missing required fields: ${validationResults.missingRequiredFields.join(', ')}`);
    
    // Check if we have Minimum Viable Schema (MVS)
    validationResults.hasMvs = mvsFields.every(field => 
      metadata && metadata[field] !== undefined && metadata[field] !== null && metadata[field] !== ''
    );
  }
  
  // 2. Format validations
  if (metadata) {
    // Dimension format check
    if (metadata.dimensions && !String(metadata.dimensions).match(/^\d+x\d+\s*mm$|^Ø\d+\s*mm$/)) {
      validationResults.isValid = false;
      validationResults.formatErrors.push("Dimension format is invalid");
      validationResults.errors.push("Dimension format is invalid");
    }
    
    // Check certifications
    if (metadata.certifications !== undefined) {
      if (!Array.isArray(metadata.certifications) || metadata.certifications.length === 0) {
        validationResults.isValid = false;
        validationResults.formatErrors.push("Certifications must be a non-empty array");
        validationResults.errors.push("Certifications must be a non-empty array");
      }
    }
    
    // Check performance data
    if (metadata.performance) {
      const performance = metadata.performance;
      const hasPerformanceData = performance.thermal_resistance || 
                                performance.fire_rating || 
                                performance.acoustic_rating;
      
      if (!hasPerformanceData) {
        validationResults.isValid = false;
        validationResults.formatErrors.push("No performance data available");
        validationResults.errors.push("No performance data available");
      }
    }
    
    // Keywords check
    if (metadata.keywords !== undefined) {
      if (!Array.isArray(metadata.keywords) || metadata.keywords.length < 2) {
        validationResults.isValid = false;
        validationResults.formatErrors.push("Keywords must be an array with at least 2 items");
        validationResults.errors.push("Keywords must be an array with at least 2 items");
      }
    }
  } else {
    validationResults.isValid = false;
    validationResults.errors.push("No metadata object found");
  }
  
  // Create lifecycle log entry
  const logEntry = {
    document_id: documentId,
    from_state: "EXTRACTED",
    to_state: validationResults.isValid ? "VALIDATED" : "VALIDATION_FAILED",
    timestamp: new Date().toISOString(),
    agent: "schema_validator_v1",
    notes: validationResults.isValid ? 
      "Schema validation passed" : 
      `Schema validation failed: ${validationResults.errors.join(', ')}`
  };
  
  // Determine next steps based on validation and retry count
  if (!validationResults.isValid) {
    // If we've already retried too many times, try fallback or fail
    if (retryCount >= 2) {
      if (validationResults.hasMvs) {
        // We have minimum viable schema - create fallback
        const fallbackMetadata = {
          name: metadata.name,
          dimensions: metadata.dimensions,
          brand: metadata.brand,
          summary: metadata.summary || "No summary available"
        };
        
        return {
          json: {
            metadata_json: fallbackMetadata,
            _metadata: item.json._metadata,
            confidence: 0.7, // Set to fallback threshold
            document_id: documentId,
            _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
            fallback_applied: true,
            original_request: originalRequest,
            schema_validation: validationResults
          }
        };
      } else {
        // Can't even create MVS after multiple retries
        return {
          json: {
            task_status: "failed",
            error_summary: `Schema validation failed after ${retryCount} retries: ${validationResults.errors.join(', ')}`,
            document_id: documentId,
            _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
            schema_validation: validationResults
          }
        };
      }
    } else {
      // We still have retries left, request another extraction
      return {
        json: {
          retry_extraction: true,
          retry_count: retryCount + 1,
          document_id: documentId,
          original_request: originalRequest,
          error_summary: validationResults.errors.join(', '),
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
          schema_validation: validationResults
        }
      };
    }
  }
  
  // Validation passed, continue to verifier
  return {
    json: {
      ...item.json,
      confidence: 0.95, // High confidence from schema validation
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
      schema_validation: validationResults
    }
  };
};

module.exports = {
  validateMetadataSchema
};