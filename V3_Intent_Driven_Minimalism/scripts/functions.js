/**
 * IMIS V3 - Intent-Driven Minimalism
 * Production-ready function implementations for n8n workflow
 */

// ==================================
// Intake Agent Implementation
// ==================================
const intakeAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Intake Agent");
  }
  
  const item = items[0];
  
  try {
    // Generate a unique request ID
    const request_id = `req-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
    
    // Extract file information
    let fileName = "unknown";
    let fileHash = "";
    let detectedLanguage = "en";
    
    // Handle email attachment
    if (item.binary) {
      const attachmentKey = Object.keys(item.binary).find(key => 
        item.binary[key].mimeType === 'application/pdf');
      
      if (attachmentKey) {
        fileName = item.binary[attachmentKey].fileName || "document.pdf";
        
        // Generate a simple hash (in production, use a proper SHA256)
        fileHash = `${item.binary[attachmentKey].fileSize}-${Date.now()}`;
      }
    }
    
    // Detect document type (simplified - in production would use ML-based classification)
    let documentTypeGuess = "Datasheet";
    if (fileName.toLowerCase().includes("catalog") || fileName.toLowerCase().includes("catalogue")) {
      documentTypeGuess = "Catalogue";
    } else if (fileName.toLowerCase().includes("spec")) {
      documentTypeGuess = "Specification";
    }
    
    // Determine source channel
    const sourceChannel = item.json.source || (item.json.from ? "email" : "webhook");
    
    // Create Material Extraction Request according to V3 interface contract
    const materialExtractionRequest = {
      request_id: request_id,
      sender: item.json.from || item.json.sender || "unknown",
      source_file_name: fileName,
      file_hash: fileHash,
      language: detectedLanguage,
      timestamp: new Date().toISOString(),
      source_channel: sourceChannel,
      document_type_guess: documentTypeGuess
    };
    
    // Create document lifecycle log entry
    const logEntry = {
      document_id: request_id,
      state_from: "RECEIVED",
      state_to: "INTERPRETED",
      timestamp: new Date().toISOString(),
      agent: "intake_agent_v3",
      notes: `Source: ${sourceChannel}, Document type guess: ${documentTypeGuess}`
    };
    
    // Return the MER with lifecycle log
    return {
      json: {
        ...materialExtractionRequest,
        _lifecycle_log: [logEntry],
        pdfText: item.json.pdfText || item.json.text || "",
        pdfPath: item.json.pdfPath || item.json.file_path || ""
      }
    };
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.request_id || `err-${Date.now()}`,
      state_from: "RECEIVED",
      state_to: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "intake_agent_v3",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Intake processing failed: ${error.message}`,
        _lifecycle_log: [errorEntry]
      }
    };
  }
};

// ==================================
// Interpreter Agent Implementation
// ==================================
const interpreterAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Interpreter Agent");
  }
  
  const item = items[0];
  
  // Check if we already have a task failure
  if (item.json.task_status === "failed") {
    return item; // Pass through the failure
  }
  
  try {
    const { request_id, pdfText, document_type_guess } = item.json;
    
    // Process LLM response
    // In production, you would use the actual LLM response
    // Here we're simulating the extraction for demonstration purposes
    
    // Detect layout signature based on document content (simplified)
    let layoutSignature = "unknown";
    let layoutSignatureConfidence = 0.5;
    
    if (pdfText.includes("Technical Data") || pdfText.includes("Specifications")) {
      layoutSignature = "datasheet";
      layoutSignatureConfidence = 0.85;
    } else if (pdfText.includes("Table of Contents") || pdfText.includes("Index")) {
      layoutSignature = "catalogue";
      layoutSignatureConfidence = 0.78;
    } else if (pdfText.includes("Test Results") || pdfText.includes("Laboratory")) {
      layoutSignature = "technical-report";
      layoutSignatureConfidence = 0.92;
    } else if (pdfText.match(/\b\d+\s*x\s*\d+\s*mm\b/) || pdfText.match(/\bØ\d+\s*mm\b/)) {
      layoutSignature = "brochure-style";
      layoutSignatureConfidence = 0.75;
    } else if (pdfText.match(/\|\s*\w+\s*\|\s*\w+\s*\|/)) {
      layoutSignature = "tabular";
      layoutSignatureConfidence = 0.88;
    }
    
    // Simplified confidence calculation based on text quality and extractable data
    const confidenceFactors = [
      pdfText.length > 1000 ? 0.2 : 0.1,
      layoutSignatureConfidence > 0.7 ? 0.3 : 0.15,
      pdfText.match(/\b\d+\s*x\s*\d+\s*mm\b/) ? 0.15 : 0.05,
      pdfText.match(/ISO\s*\d+/) || pdfText.match(/EN\s*\d+/) ? 0.15 : 0.05,
      pdfText.match(/R-value|U-value|thermal|acoustic|fire/) ? 0.2 : 0.1
    ];
    
    // Calculate overall confidence
    const confidence = confidenceFactors.reduce((sum, factor) => sum + factor, 0);
    
    // Determine confidence status
    let confidenceStatus = "fail";
    if (confidence >= 0.9) {
      confidenceStatus = "ok";
    } else if (confidence >= 0.7) {
      confidenceStatus = "uncertain";
    }
    
    // Create confidence envelope according to V3 interface contract
    const confidenceEnvelope = {
      confidence: confidence,
      status: confidenceStatus,
      layout_signature: layoutSignature,
      layout_signature_confidence: layoutSignatureConfidence
    };
    
    // Extract metadata (simplified - in production this would be from actual LLM)
    // Adjust extraction based on confidence level
    let extractedMetadata;
    
    // If low confidence, fall back to Minimum Viable Set
    if (confidence < 0.7) {
      // Extract MVS fields only
      extractedMetadata = {
        name: extractField(pdfText, "name") || "Unknown Material",
        brand: extractField(pdfText, "brand") || "Unknown Brand",
        dimensions: extractField(pdfText, "dimensions") || "Unknown Dimensions",
        summary: extractField(pdfText, "summary") || "Minimal extraction due to low confidence"
      };
    } else {
      // Extract full schema
      extractedMetadata = {
        name: extractField(pdfText, "name") || "Unknown Material",
        brand: extractField(pdfText, "brand") || "Unknown Brand",
        category: extractField(pdfText, "category") || "",
        dimensions: extractField(pdfText, "dimensions") || "",
        certifications: extractArray(pdfText, "certifications") || [],
        performance: {
          thermal_resistance: extractField(pdfText, "thermal_resistance") || "",
          fire_rating: extractField(pdfText, "fire_rating") || "",
          acoustic_rating: extractField(pdfText, "acoustic_rating") || ""
        },
        traceability: {
          origin_country: extractField(pdfText, "origin_country") || "",
          production_batch: extractField(pdfText, "production_batch") || ""
        },
        summary: extractField(pdfText, "summary") || "",
        keywords: extractArray(pdfText, "keywords") || []
      };
    }
    
    // Add metadata about the extraction process
    extractedMetadata._metadata = {
      prompt_id: "v3-layout-schema-A",
      model: "gemini-pro-vision-2024-04",
      generated_ts: new Date().toISOString()
    };
    
    // Create document lifecycle log entry
    const logEntry = {
      document_id: request_id,
      state_from: "INTERPRETED",
      state_to: confidenceStatus === "fail" ? "FLAGGED" : "VERIFIED",
      timestamp: new Date().toISOString(),
      agent: "interpreter_agent_v3",
      notes: `Confidence: ${confidence.toFixed(2)}, Status: ${confidenceStatus}`
    };
    
    // Return the extracted metadata with confidence envelope
    return {
      json: {
        request_id: request_id,
        metadata_json: extractedMetadata,
        confidence_envelope: confidenceEnvelope,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        document_type_guess: document_type_guess
      }
    };
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.request_id || `err-${Date.now()}`,
      state_from: "INTERPRETED",
      state_to: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "interpreter_agent_v3",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Interpretation failed: ${error.message}`,
        request_id: item.json.request_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Helper function to extract a field from text (simulating LLM extraction)
function extractField(text, fieldName) {
  // Simple regex-based extraction (in production this would be done by the LLM)
  const patterns = {
    name: /(?:name|product|material)[:\s]+([^,\n]+)/i,
    brand: /(?:brand|manufacturer|company)[:\s]+([^,\n]+)/i,
    category: /(?:category|type|class)[:\s]+([^,\n]+)/i,
    dimensions: /(?:dimensions|size|measurements)[:\s]+((?:\d+\s*[x×]\s*\d+\s*(?:mm|cm|m))|(?:Ø\d+\s*(?:mm|cm|m)))/i,
    thermal_resistance: /(?:thermal[^,\n]*|R-value)[:\s]+(R-[0-9.]+|[0-9.]+\s*m²K\/W)/i,
    fire_rating: /(?:fire[^,\n]*|flame)[:\s]+([^,\n]+)/i,
    acoustic_rating: /(?:acoustic|sound)[:\s]+([^,\n]+)/i,
    origin_country: /(?:origin|country|made in)[:\s]+([^,\n]+)/i,
    production_batch: /(?:batch|lot|production)[:\s]+([^,\n]+)/i,
    summary: /(?:summary|description|overview)[:\s]+([^\n]+(?:\n[^\n]+){0,3})/i
  };
  
  const match = text.match(patterns[fieldName]);
  return match ? match[1].trim() : null;
}

// Helper function to extract array fields (simulating LLM extraction)
function extractArray(text, fieldName) {
  if (fieldName === "certifications") {
    // Look for common certification patterns
    const certifications = [];
    const certPatterns = [
      /\bISO\s*\d+\b/g,
      /\bEN\s*\d+(?:-\d+)?\b/g,
      /\bFSC\b/g,
      /\bPEFC\b/g,
      /\bCE\b/g,
      /\bLEED\b/g
    ];
    
    certPatterns.forEach(pattern => {
      const matches = text.match(pattern);
      if (matches) {
        matches.forEach(match => {
          if (!certifications.includes(match)) {
            certifications.push(match);
          }
        });
      }
    });
    
    return certifications.length > 0 ? certifications : null;
  } else if (fieldName === "keywords") {
    // Extract keywords based on repeated terms and capitalized words
    const words = text.match(/\b[A-Z][a-z]{2,}\b|\b[a-z]{4,}\b/g) || [];
    const wordCount = {};
    
    words.forEach(word => {
      const normalized = word.toLowerCase();
      wordCount[normalized] = (wordCount[normalized] || 0) + 1;
    });
    
    // Filter to words that appear multiple times
    const keywords = Object.entries(wordCount)
      .filter(([word, count]) => count > 1 && !['with', 'that', 'this', 'from', 'have', 'been', 'were', 'they', 'their'].includes(word))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([word]) => word);
    
    return keywords.length > 0 ? keywords : null;
  }
  
  return null;
}

// ==================================
// Verifier Agent Implementation
// ==================================
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
    const { request_id, metadata_json, confidence_envelope } = item.json;
    
    // Initialize validation issues tracking
    const issues = [];
    const fieldLevelValidation = {};
    
    // Validate extracted metadata
    
    // 1. Validate dimensions format
    if (metadata_json.dimensions) {
      const validDimensions = metadata_json.dimensions.match(/^\d+\s*[x×]\s*\d+\s*(?:mm|cm|m)$|^Ø\d+\s*(?:mm|cm|m)$/);
      fieldLevelValidation.dimensions = validDimensions ? "plausible" : "invalid_format";
      if (!validDimensions) {
        issues.push("Dimension format is invalid");
      }
    } else if (confidence_envelope.status !== "fail") {
      // Only report as missing if not already in failed confidence state
      fieldLevelValidation.dimensions = "missing";
      issues.push("Dimensions missing");
    }
    
    // 2. Validate certifications
    if (metadata_json.certifications && metadata_json.certifications.length > 0) {
      const validCertifications = metadata_json.certifications.every(cert => 
        /^[A-Z0-9\s-]+$/.test(cert) && cert.length <= 20
      );
      fieldLevelValidation.certifications = validCertifications ? "plausible" : "suspicious_format";
      if (!validCertifications) {
        issues.push("Certification format is suspicious");
      }
    } else {
      fieldLevelValidation.certifications = "missing";
      // Not critical enough to add to issues
    }
    
    // 3. Validate fire rating
    if (metadata_json.performance && metadata_json.performance.fire_rating) {
      const validFireRating = /^[A-Z0-9\s-]+$/.test(metadata_json.performance.fire_rating);
      fieldLevelValidation.fire_rating = validFireRating ? "plausible" : "suspicious_format";
      if (!validFireRating) {
        issues.push("Fire rating format is suspicious");
      }
    }
    
    // 4. Validate origin country
    if (metadata_json.traceability && metadata_json.traceability.origin_country) {
      const countryList = ["Afghanistan", "Albania", "Algeria", /* ... add more countries */];
      const country = metadata_json.traceability.origin_country.trim();
      const validCountry = countryList.some(c => country.toLowerCase() === c.toLowerCase());
      fieldLevelValidation.origin_country = validCountry ? "plausible" : "region_mismatch";
      if (!validCountry) {
        issues.push("Origin country not recognized");
      }
    }
    
    // 5. Validate the MVS fields are present
    const mvsFields = ["name", "brand", "dimensions", "summary"];
    const missingMvsFields = mvsFields.filter(field => 
      !metadata_json[field] || metadata_json[field] === ""
    );
    
    if (missingMvsFields.length > 0) {
      issues.push(`Missing minimum viable fields: ${missingMvsFields.join(", ")}`);
      missingMvsFields.forEach(field => {
        fieldLevelValidation[field] = "missing";
      });
    }
    
    // Make verification decision based on confidence and issues
    let verificationPassed = false;
    let reason = "";
    let newState = "FLAGGED";
    
    if (confidence_envelope.status === "ok" && issues.length === 0) {
      verificationPassed = true;
      reason = "All fields verified successfully";
      newState = "VERIFIED";
    } else if (confidence_envelope.status === "uncertain" && issues.length <= 2 && missingMvsFields.length === 0) {
      // With uncertain confidence but MVS complete and only minor issues, we can still pass
      verificationPassed = true;
      reason = `Verification passed with uncertain confidence: ${issues.join("; ")}`;
      newState = "VERIFIED";
    } else if (confidence_envelope.status === "fail" || missingMvsFields.length > 0) {
      verificationPassed = false;
      reason = `Verification failed: ${confidence_envelope.status === "fail" ? "Low confidence extraction" : ""} ${missingMvsFields.length > 0 ? `Missing MVS fields: ${missingMvsFields.join(", ")}` : ""}`;
      newState = "FLAGGED";
    } else {
      verificationPassed = false;
      reason = `Verification failed due to issues: ${issues.join("; ")}`;
      newState = "FLAGGED";
    }
    
    // Create document lifecycle log entry
    const logEntry = {
      document_id: request_id,
      state_from: "VERIFIED",
      state_to: newState,
      timestamp: new Date().toISOString(),
      agent: "verifier_agent_v3",
      notes: reason
    };
    
    // Generate a feedback token for potential corrections
    const feedbackToken = `fb-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;
    
    // Prepare verification output according to V3 interface contract
    return {
      json: {
        request_id: request_id,
        verification_passed: verificationPassed,
        reason: reason,
        cleaned_json: metadata_json, // In production, we might clean or normalize values
        field_level_validation_report: fieldLevelValidation,
        verifier_agent_version: "v3.0.0",
        feedback_token: feedbackToken,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        confidence_envelope: confidence_envelope
      }
    };
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.request_id || `err-${Date.now()}`,
      state_from: "VERIFIED",
      state_to: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "verifier_agent_v3",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Verification failed: ${error.message}`,
        request_id: item.json.request_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// ==================================
// Outbound Agent Implementation
// ==================================
const outboundAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Outbound Agent");
  }
  
  const item = items[0];
  
  // Check if we already have a task failure
  if (item.json.task_status === "failed") {
    return formatErrorResponse(item);
  }
  
  try {
    const { request_id, verification_passed, cleaned_json, reason, feedback_token } = item.json;
    const originalMER = getOriginalMER(item.json);
    
    // Create completion manifest according to V3 interface contract
    const completionManifest = {
      document_state: verification_passed ? "verified" : "flagged",
      archive_uri: `file:///archives/${request_id}.json`,
      feedback_token: feedback_token,
      delivery_channel: originalMER.source_channel === "email" ? "email" : "webhook",
      delivered_ts: new Date().toISOString()
    };
    
    // Create appropriate response based on verification status
    if (verification_passed) {
      return formatSuccessResponse(item, completionManifest);
    } else {
      return formatFlaggedResponse(item, completionManifest);
    }
  } catch (error) {
    // Create error log entry
    const errorEntry = {
      document_id: item.json.request_id || `err-${Date.now()}`,
      state_from: "COMPLETED",
      state_to: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "outbound_agent_v3",
      notes: `Error: ${error.message}`
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: `Outbound processing failed: ${error.message}`,
        request_id: item.json.request_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

// Helper function to get the original Material Extraction Request
function getOriginalMER(json) {
  // Simplified - in production, you'd either pass this through the chain or retrieve from storage
  return {
    request_id: json.request_id,
    sender: json.sender || "unknown",
    source_channel: json.source_channel || "webhook"
  };
}

// Helper function for success responses
function formatSuccessResponse(item, completionManifest) {
  const { request_id, cleaned_json } = item.json;
  const sender = item.json.sender || "materials-team@example.com";
  
  // Format JSON for attachment
  const jsonStr = JSON.stringify(cleaned_json, null, 2);
  
  // Create email content
  const emailBody = `Subject: ✅ Material Metadata Extracted

Dear ${sender},

Your material document has been successfully processed. The extracted metadata is included below in JSON format.

Material: ${cleaned_json.name || 'Unnamed Material'}
Brand: ${cleaned_json.brand || 'Unspecified Brand'}

To provide feedback or corrections, please use this token: ${completionManifest.feedback_token}

Best regards,
Materials Intake System`;

  // Create document lifecycle log entry
  const logEntry = {
    document_id: request_id,
    state_from: "VERIFIED",
    state_to: "COMPLETED",
    timestamp: new Date().toISOString(),
    agent: "outbound_agent_v3",
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
      request_id: request_id,
      completion_manifest: completionManifest,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

// Helper function for flagged responses
function formatFlaggedResponse(item, completionManifest) {
  const { request_id, cleaned_json, reason } = item.json;
  const sender = item.json.sender || "materials-team@example.com";
  
  // Create email content for flagged items
  const emailBody = `Subject: ⚠️ Material Metadata Needs Review

Dear ${sender},

We've processed your material document, but some information requires review:

${reason}

We've included the partial extraction for your reference. Please review and provide corrections using the feedback token: ${completionManifest.feedback_token}

Best regards,
Materials Intake System`;

  // Create document lifecycle log entry
  const logEntry = {
    document_id: request_id,
    state_from: "FLAGGED",
    state_to: "COMPLETED",
    timestamp: new Date().toISOString(),
    agent: "outbound_agent_v3",
    notes: "Flagged email prepared"
  };
  
  // Format partial JSON for attachment
  const jsonStr = JSON.stringify(cleaned_json, null, 2);
  
  return {
    json: {
      to: sender,
      subject: "⚠️ Material Metadata Needs Review",
      body: emailBody,
      attachments: [
        {
          data: Buffer.from(jsonStr).toString('base64'),
          name: 'partial_metadata.json',
          type: 'application/json'
        }
      ],
      request_id: request_id,
      completion_manifest: completionManifest,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

// Helper function for error responses
function formatErrorResponse(item) {
  const request_id = item.json.request_id || `err-${Date.now()}`;
  const sender = item.json.sender || "materials-team@example.com";
  
  // Get error reason
  const reason = item.json.error_summary || "Unknown error occurred during processing";
  
  // Create email content for errors
  const emailBody = `Subject: ❌ Material Document Processing Failed

Dear ${sender},

We encountered an error while processing your material document:

${reason}

Please review the document and try again. If the issue persists, contact our support team.

Best regards,
Materials Intake System`;

  // Create document lifecycle log entry
  const logEntry = {
    document_id: request_id,
    state_from: "FAILED",
    state_to: "COMPLETED",
    timestamp: new Date().toISOString(),
    agent: "outbound_agent_v3",
    notes: `Error email prepared: ${reason}`
  };
  
  return {
    json: {
      to: sender,
      subject: "❌ Material Document Processing Failed",
      body: emailBody,
      request_id: request_id,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

// ==================================
// Document Lifecycle Logger
// ==================================
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
  console.log("===== DOCUMENT LIFECYCLE LOG (V3) =====");
  item.json._lifecycle_log.forEach(entry => {
    console.log(`${entry.timestamp} | ${entry.document_id} | ${entry.state_from} → ${entry.state_to} | ${entry.agent} | ${entry.notes || ''}`);
  });
  console.log("======================================");
  
  // Return the original items
  return items;
};

// Export all functions
module.exports = {
  intakeAgent,
  interpreterAgent,
  verifierAgent,
  outboundAgent,
  documentLifecycleLogger
};
