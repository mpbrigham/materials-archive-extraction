// JSON Schema Validator for Material Metadata - V1.5 Enhanced
// This module validates the metadata structure and formats from the enhanced visual extraction

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
  const verifiedFields = item.json.verified_fields || {};
  const documentId = item.json.document_id;
  const overallConfidence = item.json.overall_confidence || 0.8;
  
  // Initialize validation results
  const validationResults = {
    isValid: true,
    errors: [],
    missingRequiredFields: [],
    formatErrors: [],
    hasMvs: false,
    verificationDetails: {
      verifiedFieldCount: Object.keys(verifiedFields).length,
      correctedFields: [],
      highConfidenceFields: [],
      lowConfidenceFields: []
    }
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
      const hasPerformanceData = 
        (typeof performance === 'object' && Object.keys(performance).length > 0) || 
        (typeof performance === 'string' && performance.trim() !== '');
      
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
  
  // 3. Verification analysis
  if (Object.keys(verifiedFields).length > 0) {
    // Analyze verification results
    for (const [field, data] of Object.entries(verifiedFields)) {
      if (data.verification) {
        // Track fields that were corrected during verification
        if (data.verification.matches_initial === false) {
          validationResults.verificationDetails.correctedFields.push(field);
        }
        
        // Track confidence levels
        if (data.confidence >= 0.9) {
          validationResults.verificationDetails.highConfidenceFields.push(field);
        } else if (data.confidence < 0.7) {
          validationResults.verificationDetails.lowConfidenceFields.push(field);
        }
      }
    }
    
    // Add verification summary to errors if needed
    if (validationResults.verificationDetails.correctedFields.length > 0) {
      validationResults.errors.push(`${validationResults.verificationDetails.correctedFields.length} fields were corrected during verification: ${validationResults.verificationDetails.correctedFields.join(', ')}`);
    }
    
    if (validationResults.verificationDetails.lowConfidenceFields.length > 0) {
      validationResults.errors.push(`${validationResults.verificationDetails.lowConfidenceFields.length} fields have low confidence: ${validationResults.verificationDetails.lowConfidenceFields.join(', ')}`);
    }
  }
  
  // Create lifecycle log entry
  const logEntry = {
    document_id: documentId,
    from_state: "EXTRACTED",
    to_state: validationResults.isValid ? "VALIDATED" : "VALIDATION_FAILED",
    timestamp: new Date().toISOString(),
    agent: "schema_validator_v1.5",
    notes: validationResults.isValid ? 
      "Schema validation passed" : 
      `Schema validation failed: ${validationResults.errors.join(', ')}`
  };
  
  // Determine next steps based on validation
  if (!validationResults.isValid) {
    // For V1.5, we don't retry since we already had visual verification
    // We just apply the fallback if possible
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
          verified_fields: item.json.verified_fields,
          _metadata: item.json._metadata,
          confidence: 0.7, // Set to fallback threshold
          document_id: documentId,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
          fallback_applied: true,
          extraction_stage: "verified_fallback",
          schema_validation: validationResults
        }
      };
    } else {
      // Can't even create MVS
      return {
        json: {
          task_status: "failed",
          error_summary: `Schema validation failed: ${validationResults.errors.join(', ')}`,
          document_id: documentId,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
          schema_validation: validationResults
        }
      };
    }
  }
  
  // Calculate final confidence based on schema validation and verification
  const schemaConfidence = 0.95;
  const finalConfidence = (schemaConfidence + overallConfidence) / 2;
  
  // Add summary of corrections if any
  let validationNotes = "";
  if (validationResults.verificationDetails.correctedFields.length > 0) {
    validationNotes = `Note: ${validationResults.verificationDetails.correctedFields.length} fields were corrected during visual verification.`;
  }
  
  // Validation passed, return final result
  return {
    json: {
      ...item.json,
      confidence: finalConfidence,
      _lifecycle_log: [...(item.json._lifecycle_log || []), {
        ...logEntry,
        notes: logEntry.notes + (validationNotes ? ` ${validationNotes}` : "")
      }],
      schema_validation: validationResults,
      extraction_stage: "verified_validated"
    }
  };
};

module.exports = {
  validateMetadataSchema
};