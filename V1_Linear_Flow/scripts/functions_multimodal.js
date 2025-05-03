// Enhanced Multimodal Functions for Materials Library Information Extraction
// Implements LLM-based data processing with dynamic MVS assessment

// Document Validator Function Node Implementation
const documentValidator = function(items, runIndex) {
  // Input validation
  if (!items || items.length === 0) {
    throw new Error("No items received by Document Validator");
  }
  
  const item = items[0];
  
  // Check if this is a retry attempt
  if (item.json && item.json.retry_extraction) {
    const documentId = item.json.document_id;
    const originalRequest = item.json.original_request;
    const errorSummary = item.json.error_summary;
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
        _lifecycle_log: [...(item.json._lifecycle_log || []), retryLogEntry]
      }
    };
  }
  
  // Normal first-time processing
  // Validate that we have PDF content
  if (!item.binary || !item.binary.attachment_1 || !item.binary.attachment_1.mimeType !== 'application/pdf') {
    return {
      json: {
        task_status: "failed",
        error_summary: "Invalid or missing PDF attachment",
        document_id: `doc-${Date.now()}`,
        from_state: "RECEIVED",
        to_state: "FAILED",
        timestamp: new Date().toISOString(),
        agent: "document_validator_v1",
        notes: "Missing PDF or invalid format"
      }
    };
  }
  
  // Extract email metadata
  const sender = item.json.from || "unknown_sender";
  const subject = item.json.subject || "No Subject";
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
  const file_path = item.binary.attachment_1.path || `attachments/${document_id}.pdf`;
  
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
};

// Multimodal Metadata Extractor Function Node Implementation
const multimodalMetadataExtractor = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Multimodal Metadata Extractor");
  }
  
  const item = items[0];
  
  // Extract the document info
  const filePath = item.json.file_path || "";
  const isRetry = item.json.task === "retry_extraction";
  const retryCount = item.json.retry_count || 0;
  const errorSummary = item.json.error_summary || "";
  
  try {
    // In a production implementation, this would use the multimodal LLM API
    // Here we're simulating a response with enhanced visual data
    
    // Simulate extraction with visual coordinate information
    const extractedMetadata = {
      name: {
        value: "Example Material Name",
        location: {
          page: 1,
          bbox: [120, 210, 285, 230]
        },
        confidence: 0.98
      }, 
      brand: {
        value: "Example Brand",
        location: {
          page: 1,
          bbox: [140, 250, 300, 270]
        },
        confidence: 0.97
      },
      summary: {
        value: "High-performance sustainable wood panel for architectural applications",
        location: {
          page: 1,
          bbox: [100, 320, 500, 380]
        },
        confidence: 0.96
      },
      category: {
        value: "Wood",
        location: {
          page: 1,
          bbox: [150, 290, 250, 310]
        },
        confidence: 0.93
      },
      dimensions: {
        value: {
          width_mm: 2400,
          height_mm: 1200,
          length_mm: null
        },
        location: {
          page: 2,
          bbox: [210, 350, 310, 370]
        },
        confidence: 0.95
      },
      certifications: {
        value: ["ISO 14001", "FSC"],
        location: {
          page: 2,
          bbox: [200, 400, 350, 440]
        },
        confidence: 0.91
      },
      performance: {
        value: {
          thermal_resistance: "R-4.5",
          fire_rating: "EN 13501-1",
          acoustic_rating: "NRC 0.65"
        },
        location: {
          page: 2,
          bbox: [180, 450, 400, 520]
        },
        confidence: 0.89
      },
      keywords: {
        value: ["sustainable", "wood", "panel", "architectural"],
        location: {
          page: 3,
          bbox: [150, 200, 450, 250]
        },
        confidence: 0.92
      }
    };
    
    // Convert to standard metadata_json format
    const standardMetadata = {};
    for (const [key, data] of Object.entries(extractedMetadata)) {
      standardMetadata[key] = data.value;
    }
    
    // Add metadata about the extraction
    const metadata_json = {
      metadata_json: standardMetadata,
      field_extractions: extractedMetadata,
      _metadata: {
        prompt_id: isRetry ? "multimodal-v1.0-retry" : "multimodal-v1.0",
        model_version: "gemini-pro-vision",
        generated_ts: new Date().toISOString(),
        is_retry: isRetry,
        retry_count: retryCount,
        multimodal_extraction: true,
        source_file_name: filePath.split('/').pop() || "unknown"
      },
      field_locations: extractedMetadata,
      field_confidences: Object.entries(extractedMetadata).reduce((obj, [key, data]) => {
        obj[key] = data.confidence;
        return obj;
      }, {}),
      _lifecycle_log: item.json._lifecycle_log || [],
      document_id: item.json.document_id,
      retry_count: retryCount,
      original_request: isRetry ? item.json.original_request : item.json
    };
    
    // Add lifecycle log entry
    metadata_json._lifecycle_log.push({
      document_id: item.json.document_id,
      from_state: isRetry ? "RETRY_EXTRACTION" : "INTERPRETED",
      to_state: "EXTRACTED",
      timestamp: new Date().toISOString(),
      agent: "multimodal_metadata_extractor_v1",
      notes: isRetry ? 
        `Retry extraction attempt ${retryCount} completed` : 
        "Multimodal extraction with visual coordinates completed"
    });
    
    return { json: metadata_json };
  } catch (error) {
    // Proper error handling with fallback
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: isRetry ? "RETRY_EXTRACTION" : "INTERPRETED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "multimodal_metadata_extractor_v1",
      notes: `Multimodal extraction failed: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Multimodal metadata extraction failed: ${error.message}`,
        document_id: item.json.document_id,
        retry_count: retryCount,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// LLM Data Processor Function Node Implementation
const llmDataProcessor = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by LLM Data Processor");
  }
  
  const item = items[0];
  
  // Check for required fields
  if (!item.json.metadata_json || !item.json.field_confidences) {
    return {
      json: {
        task_status: "failed",
        error_summary: "Invalid input: missing metadata or confidence scores",
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), {
          document_id: item.json.document_id,
          from_state: "EXTRACTED",
          to_state: "FAILED",
          timestamp: new Date().toISOString(),
          agent: "llm_data_processor_v1",
          notes: "Missing required input fields"
        }]
      }
    };
  }
  
  try {
    // Prepare input for LLM data processor
    // In production, this would be sent to an LLM API with the data_processor.txt prompt
    // Here we simulate the LLM response
    
    const metadata = item.json.metadata_json;
    const fieldConfidences = item.json.field_confidences;
    
    // Simplified simulation of LLM processing decision
    // In production, this entire block would be replaced with an actual LLM call
    let decision = "PROCEED";
    let overallConfidence = 0.95;
    let validatedMetadata = {...metadata};
    let reason = "All required fields present with high confidence";
    let to_state = "VALIDATED";
    
    // Simulated decision logic - in production this would be handled by the LLM
    const mvsFields = ['name', 'brand', 'summary'];
    const mvsConfidences = mvsFields.map(field => fieldConfidences[field] || 0);
    const minMvsConfidence = Math.min(...mvsConfidences);
    
    if (minMvsConfidence < 0.7 || mvsFields.some(field => !metadata[field])) {
      decision = "FAIL";
      overallConfidence = minMvsConfidence;
      reason = `Critical fields missing or low confidence: min confidence ${minMvsConfidence.toFixed(2)}`;
      to_state = "FAILED";
    } else if (minMvsConfidence < 0.9) {
      decision = "FALLBACK";
      overallConfidence = minMvsConfidence;
      
      // Create optimized subset based on field confidence
      validatedMetadata = Object.entries(metadata).reduce((result, [key, value]) => {
        if (mvsFields.includes(key) || (fieldConfidences[key] && fieldConfidences[key] >= 0.7)) {
          result[key] = value;
        }
        return result;
      }, {});
      
      reason = `Falling back to optimized schema with fields above 0.7 confidence`;
      to_state = "FALLBACK";
    }
    
    // Simulate LLM response
    const llmResponse = {
      decision: decision,
      confidence: overallConfidence,
      validated_metadata: validatedMetadata,
      reason: reason,
      from_state: "EXTRACTED",
      to_state: to_state,
      notes: `MVS fields confidence: name=${fieldConfidences.name}, brand=${fieldConfidences.brand}, summary=${fieldConfidences.summary}`
    };
    
    // Create lifecycle log entry
    const logEntry = {
      document_id: item.json.document_id,
      from_state: "EXTRACTED",
      to_state: llmResponse.to_state,
      timestamp: new Date().toISOString(),
      agent: "llm_data_processor_v1",
      notes: llmResponse.reason
    };
    
    // Return processor results based on decision
    if (llmResponse.decision === "FAIL") {
      return {
        json: {
          task_status: "failed",
          error_summary: llmResponse.reason,
          document_id: item.json.document_id,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
        }
      };
    }
    
    // For PROCEED or FALLBACK
    return {
      json: {
        ...item.json,
        metadata_json: llmResponse.validated_metadata,
        llm_decision: llmResponse.decision,
        confidence: llmResponse.confidence,
        fallback_applied: llmResponse.decision === "FALLBACK",
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        processor_notes: llmResponse.notes
      }
    };
    
  } catch (error) {
    // Error handling
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "EXTRACTED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "llm_data_processor_v1",
      notes: `LLM data processing failed: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `LLM data processing failed: ${error.message}`,
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Multimodal Verifier Function Node Implementation
const multimodalVerifier = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Multimodal Verifier");
  }
  
  const item = items[0];
  
  // Check if we already have a task failure
  if (item.json.task_status === "failed") {
    return item; // Pass through the failure
  }
  
  const metadata = item.json.metadata_json;
  const confidence = item.json.confidence || 0.9;
  const fieldLocations = item.json.field_locations || {};
  const fallbackApplied = item.json.fallback_applied || false;
  
  try {
    // In a production implementation, this would call the multimodal LLM 
    // with the document and extracted metadata for verification
    
    // Simulate multimodal verification results
    const verificationResults = {
      verification_passed: true,
      verified_fields: Object.keys(metadata),
      unverified_fields: [],
      confidence: 0.95,
      mvs_verification: {
        passed: true,
        confidence: 0.97,
        notes: "All MVS fields verified with high confidence"
      },
      evidence: Object.entries(metadata).reduce((obj, [key, value]) => {
        obj[key] = { 
          page: fieldLocations[key]?.location?.page || 1, 
          location: "detected location", 
          verified: true,
          confidence: 0.95,
          notes: `Field '${key}' successfully verified`
        };
        return obj;
      }, {})
    };
    
    // Check if any fields could not be verified
    if (verificationResults.unverified_fields.length > 0) {
      verificationResults.verification_passed = false;
      verificationResults.mvs_verification.notes = "Some fields could not be verified";
    }
    
    // Create lifecycle log entry
    const verifierState = fallbackApplied ? "FALLBACK" : "VALIDATED";
    const targetState = verificationResults.verification_passed ? 
      (fallbackApplied ? "COMPLETED_WITH_FALLBACK" : "VERIFIED") : 
      "FAILED";
    
    const logEntry = {
      document_id: item.json.document_id,
      from_state: verifierState,
      to_state: targetState,
      timestamp: new Date().toISOString(),
      agent: "multimodal_verifier_v1",
      notes: verificationResults.verification_passed ? 
        `Verified ${verificationResults.verified_fields.length} fields successfully` : 
        `Verification failed: ${verificationResults.unverified_fields.join(', ')}`
    };
    
    // Return verification results
    return {
      json: {
        verification_passed: verificationResults.verification_passed,
        reason: verificationResults.verification_passed ? 
          "Verification successful" : 
          `Failed to verify: ${verificationResults.unverified_fields.join(', ')}`,
        cleaned_json: metadata,
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        verifier_version: "multimodal-v1.5",
        original_request: item.json.original_request,
        verification_results: verificationResults,
        fallback_applied: fallbackApplied
      }
    };
  } catch (error) {
    // Error handling
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: fallbackApplied ? "FALLBACK" : "VALIDATED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "multimodal_verifier_v1",
      notes: `Verification failed: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Verification failed: ${error.message}`,
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Format Success Email Function Node Implementation
const formatSuccessEmail = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Email Formatter");
  }
  
  const item = items[0];
  
  // Extract original request data
  const originalRequest = item.json.original_request || {};
  const sender = originalRequest.sender || "materials-team@example.com";
  
  // Format JSON for attachment
  const cleanedJson = item.json.cleaned_json || {};
  const jsonStr = JSON.stringify(cleanedJson, null, 2);
  
  // Add fallback note if applicable
  const fallbackNote = item.json.fallback_applied ? 
    'Note: Simplified metadata extracted due to confidence thresholds.' : 
    '';
  
  // Create email content
  const emailBody = `Subject: ✅ Material Metadata Extracted
  
Dear ${sender},

The attached PDF has been successfully processed. The extracted metadata is included below in JSON format.

Material: ${cleanedJson.name || 'Unnamed Material'}
Brand: ${cleanedJson.brand || 'Unspecified Brand'}
${fallbackNote}
${item.json.verification_passed ? '' : 'Note: Some issues were detected during processing: ' + item.json.reason}

Best regards,
Materials Library Bot`;

  return {
    json: {
      to: sender,
      subject: "✅ Material Metadata Extracted",
      body: emailBody,
      attachments: [
        {
          data: Buffer.from(jsonStr).toString('base64'),
          name: 'extracted_metadata.json',
          type: 'application/json'
        }
      ],
      document_id: item.json.document_id,
      _lifecycle_log: item.json._lifecycle_log || []
    }
  };
};

// Format Error Email Function Node Implementation
const formatErrorEmail = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Error Email Formatter");
  }
  
  const item = items[0];
  
  // Extract original request data
  const originalRequest = item.json.original_request || {};
  const sender = originalRequest.sender || "materials-team@example.com";
  
  // Get error reason
  const reason = item.json.error_summary || item.json.reason || "Unknown error occurred";
  
  // Create email content
  const emailBody = `Subject: ❌ Metadata Extraction Failed

Dear ${sender},

The attached PDF could not be processed due to the following issue:

${reason}

Please check the document and try again.

Best regards,
Materials Library Bot`;

  return {
    json: {
      to: sender,
      subject: "❌ Metadata Extraction Failed",
      body: emailBody,
      document_id: item.json.document_id,
      _lifecycle_log: item.json._lifecycle_log || []
    }
  };
};

module.exports = {
  // Core multimodal functions
  documentValidator,
  multimodalMetadataExtractor,
  llmDataProcessor,
  multimodalVerifier,
  
  // Email formatters
  formatSuccessEmail,
  formatErrorEmail
};