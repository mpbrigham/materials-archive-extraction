// Supervisor Agent Function Node Implementation
const supervisorAgent = function(items, runIndex) {
  // Input validation
  if (!items || items.length === 0) {
    throw new Error("No items received by Supervisor Agent");
  }
  
  const item = items[0];
  
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
        agent: "supervisor_agent_v1",
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
    agent: "supervisor_agent_v1",
    notes: `Document language = '${language}'`
  };
  
  // Store the file path reference (adjust as needed for your environment)
  const file_path = item.binary.attachment_1.path || `attachments/${document_id}.pdf`;
  
  // Return output matching the Supervisor → Metadata Extraction Agent contract
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
      _lifecycle_log: [logEntry]
    }
  };
};

// Metadata Extraction Function Node Implementation
const metadataExtractor = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Metadata Extractor");
  }
  
  const item = items[0];
  
  // Extract the PDF text from previous node
  const pdfText = item.json.pdfText || ""; 
  
  // Prepare prompt with the PDF text
  // Note: In a real implementation, you would make an API call to an LLM
  // This is a mockup for the patch
  
  try {
    // In production, replace this with actual API call to OpenAI/Claude/etc.
    // For the patch, we'll simulate a successful extraction
    
    const extractedMetadata = {
      name: "Example Material Name", 
      brand: "Example Brand",
      category: "Wood",
      dimensions: "2400x1200 mm",
      certifications: ["ISO 14001", "FSC"],
      performance: {
        thermal_resistance: "R-4.5",
        fire_rating: "EN 13501-1",
        acoustic_rating: "NRC 0.65"
      },
      asset_urls: ["https://example.com/datasheet.pdf"],
      traceability: {
        origin_country: "Sweden",
        production_batch: "LOT-2025-04-123"
      },
      summary: "High-performance sustainable wood panel for architectural applications",
      keywords: ["sustainable", "wood", "panel", "architectural"]
    };
    
    // Add metadata about the extraction
    const metadata_json = {
      metadata_json: extractedMetadata,
      _metadata: {
        prompt_id: "v1.0",
        model_version: "gemini-flash-1",
        generated_ts: new Date().toISOString()
      },
      _lifecycle_log: item.json._lifecycle_log || [],
      document_id: item.json.document_id,
      original_request: item.json
    };
    
    // Add lifecycle log entry
    metadata_json._lifecycle_log.push({
      document_id: item.json.document_id,
      from_state: "INTERPRETED",
      to_state: "EXTRACTED",
      timestamp: new Date().toISOString(),
      agent: "metadata_extraction_agent_v1",
      notes: "Extraction successful"
    });
    
    return { json: metadata_json };
  } catch (error) {
    // Proper error handling with fallback
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "INTERPRETED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "metadata_extraction_agent_v1",
      notes: `Extraction failed: ${error.message}`
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

// Check Required Fields Function Node Implementation
const checkRequiredFields = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Required Fields checker");
  }
  
  const item = items[0];
  
  // Check for required fields according to the schema
  const requiredFields = ['name', 'brand', 'category', 'dimensions'];
  const metadata = item.json.metadata_json;
  
  const missingFields = requiredFields.filter(field => 
    !metadata || metadata[field] === undefined || metadata[field] === null || metadata[field] === ''
  );
  
  if (missingFields.length > 0) {
    // Apply confidence policy - fallback to MVS if possible
    const mvs = ['name', 'dimensions', 'brand', 'summary'];
    const hasMvs = mvs.every(field => 
      metadata && metadata[field] !== undefined && metadata[field] !== null && metadata[field] !== ''
    );
    
    // Create lifecycle log entry
    const logEntry = {
      document_id: item.json.document_id,
      from_state: "EXTRACTED",
      to_state: hasMvs ? "FALLBACK" : "FAILED",
      timestamp: new Date().toISOString(),
      agent: "field_validator_v1",
      notes: `Missing required fields: ${missingFields.join(', ')}`
    };
    
    if (hasMvs) {
      // We have minimum viable schema - create fallback
      const fallbackMetadata = {
        name: metadata.name,
        dimensions: metadata.dimensions,
        brand: metadata.brand,
        summary: metadata.summary
      };
      
      return {
        json: {
          metadata_json: fallbackMetadata,
          _metadata: item.json._metadata,
          confidence: 0.7, // Set to fallback threshold
          document_id: item.json.document_id,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
          fallback_applied: true,
          original_request: item.json.original_request
        }
      };
    } else {
      // Can't even create MVS
      return {
        json: {
          task_status: "failed",
          error_summary: `Missing required fields: ${missingFields.join(', ')}`,
          document_id: item.json.document_id,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
        }
      };
    }
  }
  
  // All required fields are present
  const logEntry = {
    document_id: item.json.document_id,
    from_state: "EXTRACTED",
    to_state: "VALIDATED",
    timestamp: new Date().toISOString(),
    agent: "field_validator_v1",
    notes: "All required fields present"
  };
  
  return {
    json: {
      ...item.json,
      confidence: 0.95, // High confidence
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
};

// Verifier Agent Function Node Implementation
const verifierAgent = function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Verifier Agent");
  }
  
  const item = items[0];
  
  // Check if we already have a task failure
  if (item.json.task_status === "failed") {
    return item; // Pass through the failure
  }
  
  const metadata = item.json.metadata_json;
  const confidence = item.json.confidence || 0.9;
  
  // Apply confidence policy
  let verificationPassed = true;
  let reason = "Verification successful";
  let to_state = "VERIFIED";
  
  // Verification checks
  const issues = [];
  
  // Dimension format check
  if (metadata.dimensions && !metadata.dimensions.match(/^\d+x\d+\s*mm$|^Ø\d+\s*mm$/)) {
    issues.push("Dimension format is invalid");
  }
  
  // Check certifications
  if (!metadata.certifications || !Array.isArray(metadata.certifications) || metadata.certifications.length === 0) {
    issues.push("Certifications missing or invalid");
  }
  
  // Check performance data
  const performance = metadata.performance || {};
  if (!performance.thermal_resistance && !performance.fire_rating && !performance.acoustic_rating) {
    issues.push("No performance data available");
  }
  
  // Keywords check
  if (!metadata.keywords || !Array.isArray(metadata.keywords) || metadata.keywords.length < 2) {
    issues.push("Insufficient keywords");
  }
  
  // Handle verification results
  if (issues.length > 0) {
    // If fallback already applied, don't apply again
    if (item.json.fallback_applied) {
      verificationPassed = confidence >= 0.7; // Accept MVS at fallback threshold
      reason = `Fallback schema applied. Known issues: ${issues.join(', ')}`;
      to_state = "COMPLETED_WITH_FALLBACK";
    } else if (confidence >= 0.9) {
      // High confidence but with issues - still pass
      verificationPassed = true;
      reason = `Passed with issues: ${issues.join(', ')}`;
      to_state = "VERIFIED_WITH_ISSUES";
    } else if (confidence >= 0.7) {
      // Apply fallback
      metadata = {
        name: metadata.name,
        dimensions: metadata.dimensions || "UNKNOWN",
        brand: metadata.brand,
        summary: metadata.summary || "No summary available"
      };
      verificationPassed = true;
      reason = `Fallback schema applied due to issues: ${issues.join(', ')}`;
      to_state = "COMPLETED_WITH_FALLBACK";
    } else {
      // Fail verification
      verificationPassed = false;
      reason = `Verification failed: ${issues.join(', ')}`;
      to_state = "FAILED";
    }
  }
  
  // Create lifecycle log entry
  const logEntry = {
    document_id: item.json.document_id,
    from_state: item.json.fallback_applied ? "FALLBACK" : "VALIDATED",
    to_state: to_state,
    timestamp: new Date().toISOString(),
    agent: "verifier_agent_v1",
    notes: reason
  };
  
  // Return verification results
  return {
    json: {
      verification_passed: verificationPassed,
      reason: reason,
      cleaned_json: metadata,
      document_id: item.json.document_id,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
      verifier_version: "v1.0",
      original_request: item.json.original_request
    }
  };
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
  
  // Create email content
  const emailBody = `Subject: ✅ Material Metadata Extracted

Dear ${sender},

The attached PDF has been successfully processed. The extracted metadata is included below in JSON format.

Material: ${cleanedJson.name || 'Unnamed Material'}
Brand: ${cleanedJson.brand || 'Unspecified Brand'}
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

// Create a production-ready configuration file for environment variables
const productionConfig = {
  smtp: {
    host: "process.env.SMTP_HOST",
    port: "process.env.SMTP_PORT",
    secure: true,
    auth: {
      user: "process.env.SMTP_USER",
      pass: "process.env.SMTP_PASS"
    }
  },
  imap: {
    host: "process.env.IMAP_HOST",
    port: "process.env.IMAP_PORT",
    secure: true,
    auth: {
      user: "process.env.IMAP_USER",
      pass: "process.env.IMAP_PASS"
    },
    mailbox: "INBOX",
    pollInterval: 60 // seconds
  },
  llm: {
    provider: "process.env.LLM_PROVIDER", // openai, gemini, anthropic
    apiKey: "process.env.LLM_API_KEY",
    model: "process.env.LLM_MODEL" // gemini-flash-1, gpt-4, etc.
  },
  storage: {
    type: "process.env.STORAGE_TYPE", // filesystem, s3, database
    path: "process.env.STORAGE_PATH", // for filesystem
    url: "process.env.STORAGE_URL" // for s3 or database
  },
  logging: {
    level: "process.env.LOG_LEVEL",
    path: "process.env.LOG_PATH",
    enableStructuredLogs: true
  }
};

module.exports = {
  supervisorAgent,
  metadataExtractor,
  checkRequiredFields,
  verifierAgent,
  formatSuccessEmail,
  formatErrorEmail,
  productionConfig
};
