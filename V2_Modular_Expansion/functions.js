/**
 * IMIS V2 - Function Node Implementations
 * Production-ready implementation for V2_Modular_Expansion
 */

// Intake Orchestrator Agent Implementation
const intakeOrchestratorAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Intake Orchestrator");
  }
  
  const item = items[0];
  
  // Validate that we have a PDF attachment
  if (!item.binary || !Object.keys(item.binary).some(key => 
    item.binary[key].mimeType === 'application/pdf')) {
    return {
      json: {
        task_status: "failed",
        error_summary: "Invalid or missing PDF attachment",
        document_id: `doc-${Date.now()}`,
        from_state: "RECEIVED",
        to_state: "FAILED",
        timestamp: new Date().toISOString(),
        agent: "intake_orchestrator_v2",
        notes: "Missing PDF or invalid format"
      }
    };
  }
  
  // Find the PDF attachment
  const attachmentKey = Object.keys(item.binary).find(key => 
    item.binary[key].mimeType === 'application/pdf');
  
  // Extract email metadata
  const sender = item.json.from || "unknown_sender";
  const subject = item.json.subject || "No Subject";
  const timestamp = new Date().toISOString();
  const document_id = `doc-${Date.now()}-${sender.replace(/[^a-zA-Z0-9]/g, '')}`;
  
  // Generate file hash (simplified for example)
  const file_hash = item.binary[attachmentKey].fileSize + '-' + Date.now();
  
  // Store the file path reference
  const file_path = item.binary[attachmentKey].path || `attachments/${document_id}.pdf`;
  
  // Create document lifecycle log entry
  const logEntry = {
    document_id: document_id,
    from_state: "RECEIVED",
    to_state: "PREPROCESSING",
    timestamp: timestamp,
    agent: "intake_orchestrator_v2",
    notes: `Document received from ${sender}`
  };
  
  // Output according to V2 interface contract
  return {
    json: {
      document_id: document_id,
      sender: sender,
      subject: subject,
      timestamp: timestamp,
      file_path: file_path,
      file_hash: file_hash,
      _lifecycle_log: [logEntry]
    }
  };
};

// Preprocessing Agent Implementation
const preprocessingAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Preprocessing Agent");
  }
  
  const item = items[0];
  
  try {
    // Extract data from previous node
    const { document_id, file_path, sender, timestamp } = item.json;
    const pdfText = item.json.pdfText || "";
    
    // Determine document language (simplified)
    let language = "en";
    if (pdfText.match(/\b(de|der|das|ein|eine)\b/gi) && 
        pdfText.match(/\b(der|die|das)\b/gi)) {
      language = "de";
    } else if (pdfText.match(/\b(het|de|een|van)\b/gi) && 
               pdfText.match(/\b(het|zij|aan)\b/gi)) {
      language = "nl";
    }
    
    // Detect layout type and quality
    const isScanned = pdfText.length < 500 || 
                      pdfText.match(/[^a-zA-Z0-9\s.,;:!?'"()\[\]{}\/\\\-_+=<>@#$%^&*|~`]/) > 
                      (pdfText.length * 0.05);
    
    const layout_type = isScanned ? "scanned" : "digital";
    
    // Assess quality (simplified)
    const poorQualityIndicators = [
      pdfText.length < 200,
      pdfText.match(/[a-zA-Z]/).length < (pdfText.length * 0.3),
      (pdfText.match(/\?/g) || []).length > (pdfText.length * 0.01)
    ];
    
    const quality = poorQualityIndicators.filter(Boolean).length >= 2 ? "poor" : "good";
    
    // Determine if fallback might be needed
    const fallback_required = quality === "poor" || layout_type === "scanned";
    
    // Create document lifecycle log entry
    const logEntry = {
      document_id: document_id,
      from_state: "PREPROCESSING",
      to_state: "EXTRACTION",
      timestamp: new Date().toISOString(),
      agent: "preprocessing_agent_v2",
      notes: `Language: ${language}, Type: ${layout_type}, Quality: ${quality}`
    };
    
    // Output according to V2 interface contract
    return {
      json: {
        document_id: document_id,
        language: language,
        layout_type: layout_type,
        quality: quality,
        fallback_required: fallback_required,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        original_request: {
          file_path: file_path,
          sender: sender,
          timestamp: timestamp
        }
      }
    };
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "PREPROCESSING",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "preprocessing_agent_v2",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Preprocessing failed: ${error.message}`,
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Metadata Extraction Processing Function
const metadataExtractionProcessor = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Metadata Extraction Processor");
  }
  
  const item = items[0];
  
  try {
    // Extract the LLM response from previous node
    const llmResponse = item.json.choices?.[0]?.message?.content || item.json.pdfText || "";
    const { document_id, fallback_required } = item.json;
    
    // Parse the JSON from the LLM response
    // In production, you would implement more robust extraction
    let metadata_json = {};
    try {
      // Find JSON object in the response (simplified)
      const jsonMatch = llmResponse.match(/\{[\s\S]*\}/);
      if (jsonMatch) {
        metadata_json = JSON.parse(jsonMatch[0]);
      } else {
        throw new Error("No valid JSON found in LLM response");
      }
    } catch (parseError) {
      // If fallback required, create minimal schema
      if (fallback_required) {
        // Extract basic info with regex (simplified)
        const nameMatch = llmResponse.match(/name["\s:]+([^"]+)/);
        const brandMatch = llmResponse.match(/brand["\s:]+([^"]+)/);
        const dimensionsMatch = llmResponse.match(/dimensions["\s:]+([^"]+)/);
        
        metadata_json = {
          name: nameMatch ? nameMatch[1].trim() : "Unknown Material",
          brand: brandMatch ? brandMatch[1].trim() : "Unknown Brand",
          dimensions: dimensionsMatch ? dimensionsMatch[1].trim() : "Unknown Dimensions",
          summary: "Extracted with fallback due to parsing issues"
        };
      } else {
        throw new Error(`Failed to parse LLM output: ${parseError.message}`);
      }
    }
    
    // Calculate confidence score (simplified implementation)
    const requiredFields = ['name', 'brand', 'category', 'dimensions'];
    const presentFields = requiredFields.filter(field => 
      metadata_json && metadata_json[field] !== undefined && 
      metadata_json[field] !== null && metadata_json[field] !== ''
    );
    
    const confidence = presentFields.length / requiredFields.length;
    
    // Determine confidence envelope status
    let confidence_status = "ok";
    if (confidence < 0.7) {
      confidence_status = "fail";
    } else if (confidence < 0.9) {
      confidence_status = "fallback";
    }
    
    // Apply fallback if needed
    if (confidence_status === "fallback" || fallback_required) {
      // Ensure we have MVS fields
      metadata_json = {
        name: metadata_json.name || "Unknown Material",
        brand: metadata_json.brand || "Unknown Brand",
        dimensions: metadata_json.dimensions || "Unknown Dimensions",
        summary: metadata_json.summary || "Extracted with fallback schema"
      };
    }
    
    // Create document lifecycle log entry
    const logEntry = {
      document_id: document_id,
      from_state: "EXTRACTION",
      to_state: confidence_status === "fail" ? "FAILED" : "VERIFICATION",
      timestamp: new Date().toISOString(),
      agent: "metadata_extraction_agent_v2",
      notes: `Confidence: ${confidence.toFixed(2)}, Status: ${confidence_status}`
    };
    
    // Output according to V2 interface contract
    if (confidence_status === "fail") {
      return {
        json: {
          task_status: "failed",
          error_summary: "Extraction confidence too low",
          document_id: document_id,
          confidence_envelope: {
            confidence: confidence,
            status: confidence_status
          },
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
        }
      };
    }
    
    return {
      json: {
        document_id: document_id,
        metadata_json: metadata_json,
        _metadata: {
          prompt_version: "v2.3",
          model: "gemini-pro-vision",
          generated_ts: new Date().toISOString()
        },
        confidence_envelope: {
          confidence: confidence,
          status: confidence_status
        },
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        original_request: item.json.original_request
      }
    };
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "EXTRACTION",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "metadata_extraction_agent_v2",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Metadata extraction failed: ${error.message}`,
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Verifier Agent Implementation
const verifierAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Verifier Agent");
  }
  
  const item = items[0];
  
  // Check if we already have a task failure
  if (item.json.task_status === "failed") {
    return item; // Pass through the failure
  }
  
  try {
    const { document_id, metadata_json, confidence_envelope } = item.json;
    
    // Initialize validation issues array
    const issues = [];
    const validationReport = {
      summary: "",
      fields: {}
    };
    
    // Validation checks
    
    // 1. Validate dimensions format
    if (metadata_json.dimensions) {
      const validDimensions = metadata_json.dimensions.match(/^\d+x\d+\s*mm$|^Ø\d+\s*mm$/);
      validationReport.fields.dimensions = validDimensions ? "ok" : "invalid_format";
      if (!validDimensions) {
        issues.push("Dimension format is invalid");
      }
    } else {
      validationReport.fields.dimensions = "missing";
      issues.push("Dimensions missing");
    }
    
    // 2. Validate certifications
    if (metadata_json.certifications) {
      const validCertifications = Array.isArray(metadata_json.certifications) && 
                                metadata_json.certifications.length > 0;
      validationReport.fields.certifications = validCertifications ? "ok" : "invalid";
      if (!validCertifications) {
        issues.push("Certifications missing or invalid");
      }
    } else {
      validationReport.fields.certifications = "missing";
    }
    
    // 3. Validate performance data
    const performance = metadata_json.performance || {};
    const hasPerformanceData = performance.thermal_resistance || 
                             performance.fire_rating || 
                             performance.acoustic_rating;
    
    if (performance) {
      validationReport.fields.performance = hasPerformanceData ? "ok" : "insufficient";
      if (!hasPerformanceData) {
        issues.push("No performance data available");
      }
    } else {
      validationReport.fields.performance = "missing";
    }
    
    // 4. Validate keywords
    if (metadata_json.keywords) {
      const validKeywords = Array.isArray(metadata_json.keywords) && metadata_json.keywords.length >= 2;
      validationReport.fields.keywords = validKeywords ? "ok" : "insufficient";
      if (!validKeywords) {
        issues.push("Insufficient keywords");
      }
    } else {
      validationReport.fields.keywords = "missing";
    }
    
    // Make verification decision
    let verification_passed = issues.length === 0;
    let reason = verification_passed ? "Verification successful" : `Verification failed: ${issues.join(', ')}`;
    
    // Consider confidence envelope for borderline cases
    if (!verification_passed && confidence_envelope?.status === "fallback") {
      // In fallback mode, we're more lenient
      verification_passed = true;
      reason = `Fallback schema accepted with known issues: ${issues.join(', ')}`;
    }
    
    // Set validation report summary
    validationReport.summary = reason;
    
    // Create document lifecycle log entry
    const to_state = verification_passed ? "COMPLETED" : "FAILED";
    
    const logEntry = {
      document_id: document_id,
      from_state: "VERIFICATION",
      to_state: to_state,
      timestamp: new Date().toISOString(),
      agent: "verifier_agent_v2",
      notes: reason
    };
    
    // Output according to V2 interface contract
    return {
      json: {
        document_id: document_id,
        verification_passed: verification_passed,
        validated_json: metadata_json,
        validation_report: validationReport,
        verifier_version: "v2.1",
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        original_request: item.json.original_request
      }
    };
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "VERIFICATION",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "verifier_agent_v2",
      notes: `Error: ${error.message}`
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

// Supervisor Response Agent Implementation
const supervisorResponseAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Supervisor Response Agent");
  }
  
  const item = items[0];
  
  try {
    // Check if we already have a task failure
    if (item.json.task_status === "failed") {
      return formatErrorResponse(item);
    }
    
    const { document_id, verification_passed, validated_json, validation_report, original_request } = item.json;
    
    // Handle based on verification result
    if (verification_passed) {
      return formatSuccessResponse(item);
    } else {
      return formatErrorResponse(item);
    }
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.document_id || "unknown-doc",
      from_state: "RESPONSE",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "supervisor_response_agent_v2",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Response creation failed: ${error.message}`,
        document_id: item.json.document_id || "unknown-doc",
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Helper function for success responses
function formatSuccessResponse(item) {
  const { document_id, validated_json, original_request } = item.json;
  const sender = original_request?.sender || "materials-team@example.com";
  
  // Format JSON for attachment
  const jsonStr = JSON.stringify(validated_json, null, 2);
  
  // Create email content
  const emailBody = `Subject: ✅ Material Metadata Extracted

Dear ${sender},

Your PDF has been successfully processed. The extracted metadata is included below in JSON format.

Material: ${validated_json.name || 'Unnamed Material'}
Brand: ${validated_json.brand || 'Unspecified Brand'}

Best regards,
Materials Intake System`;

  // Create document lifecycle log entry
  const logEntry = {
    document_id: document_id,
    from_state: "COMPLETED",
    to_state: "DELIVERED",
    timestamp: new Date().toISOString(),
    agent: "supervisor_response_agent_v2",
    notes: "Success email prepared"
  };
  
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
      document_id: document_id,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

// Helper function for error responses
function formatErrorResponse(item) {
  const { document_id, validation_report, error_summary, original_request } = item.json;
  const sender = original_request?.sender || "materials-team@example.com";
  
  // Get error reason
  const reason = error_summary || 
                validation_report?.summary || 
                "Unknown error occurred during processing";
  
  // Create email content
  const emailBody = `Subject: ❌ Metadata Extraction Failed

Dear ${sender},

We could not extract metadata from your PDF. Reason:

${reason}

Please review the document and try again.

Best regards,
Materials Intake System`;

  // Create document lifecycle log entry
  const logEntry = {
    document_id: document_id,
    from_state: "FAILED",
    to_state: "ERROR_DELIVERED",
    timestamp: new Date().toISOString(),
    agent: "supervisor_response_agent_v2",
    notes: `Error email prepared: ${reason}`
  };
  
  return {
    json: {
      to: sender,
      subject: "❌ Metadata Extraction Failed",
      body: emailBody,
      document_id: document_id,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

// Function to log document lifecycle events
const documentLifecycleLogger = function(items, runIndex) {
  if (!items || items.length === 0) {
    return items; // Nothing to log
  }
  
  const item = items[0];
  
  // Only log if we have lifecycle entries
  if (!item.json._lifecycle_log || !Array.isArray(item.json._lifecycle_log)) {
    return items;
  }
  
  // In a production environment, you would write these to a database or file
  console.log("===== DOCUMENT LIFECYCLE LOG =====");
  item.json._lifecycle_log.forEach(entry => {
    console.log(`${entry.timestamp} | ${entry.document_id} | ${entry.from_state} → ${entry.to_state} | ${entry.agent} | ${entry.notes || ''}`);
  });
  console.log("=================================");
  
  // Return the original items
  return items;
};

module.exports = {
  intakeOrchestratorAgent,
  preprocessingAgent,
  metadataExtractionProcessor,
  verifierAgent,
  supervisorResponseAgent,
  documentLifecycleLogger,
  formatSuccessResponse,
  formatErrorResponse
};
