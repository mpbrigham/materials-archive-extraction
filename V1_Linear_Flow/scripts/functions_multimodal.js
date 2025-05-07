// Enhanced Multimodal Functions for Materials Library Information Extraction
// Implements LLM-based data processing with dynamic MVS assessment and multiple product support

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
    // Example with two products
    const extractedProducts = [
      {
        name: {
          value: "EcoBoard Pro X-340",
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
        }
      },
      {
        name: {
          value: "EcoBoard Pro X-350",
          location: {
            page: 3,
            bbox: [120, 210, 285, 230]
          },
          confidence: 0.98
        }, 
        brand: {
          value: "Example Brand",
          location: {
            page: 3,
            bbox: [140, 250, 300, 270]
          },
          confidence: 0.97
        },
        summary: {
          value: "Premium sustainable wood panel with enhanced durability",
          location: {
            page: 3,
            bbox: [100, 320, 500, 380]
          },
          confidence: 0.96
        },
        category: {
          value: "Wood",
          location: {
            page: 3,
            bbox: [150, 290, 250, 310]
          },
          confidence: 0.93
        },
        dimensions: {
          value: {
            width_mm: 3000,
            height_mm: 1500,
            length_mm: null
          },
          location: {
            page: 4,
            bbox: [210, 350, 310, 370]
          },
          confidence: 0.95
        }
      }
    ];
    
    // This would come from the actual LLM response in production
    // For simulation, we're checking if there's a number in the subject to determine
    // if we should return multiple products
    const hasMultipleProducts = item.json.subject && item.json.subject.match(/\d/) ? true : false;
    
    // If we detect just one product, only return the first product
    const productsToUse = hasMultipleProducts ? extractedProducts : [extractedProducts[0]];
    
    // Process the extracted products
    const processedProducts = [];
    
    for (const product of productsToUse) {
      // Simplified structure - only keep field_extractions
      processedProducts.push({
        field_extractions: product
      });
    }
    
    // Add metadata about the extraction
    const metadata_json = {
      products: processedProducts,
      _metadata: {
        prompt_id: isRetry ? "multimodal-v1.0-retry" : "multimodal-v1.0",
        model_version: "gemini-pro-vision",
        generated_ts: new Date().toISOString(),
        is_retry: isRetry,
        retry_count: retryCount,
        multimodal_extraction: true,
        source_file_name: filePath.split('/').pop() || "unknown",
        product_count: processedProducts.length
      },
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
        `Multimodal extraction with visual coordinates completed, found ${processedProducts.length} products`
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
  if (!item.json.products) {
    return {
      json: {
        task_status: "failed",
        error_summary: "Invalid input: missing products array",
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
    // Process each product independently
    const processedProducts = [];
    const failedProducts = [];
    
    for (const product of item.json.products) {
      // Check for required field_extractions
      if (!product.field_extractions) {
        failedProducts.push({
          error: "Missing field_extractions",
          data: product
        });
        continue;
      }
      
      const fieldExtractions = product.field_extractions;
      
      // Simplified simulation of LLM processing decision for this product
      // In production, this entire block would be replaced with an actual LLM call
      let decision = "PROCEED";
      let overallConfidence = 0.95;
      let reason = "All required fields present with high confidence";
      let to_state = "VALIDATED";
      
      // Simulated decision logic - in production this would be handled by the LLM
      const mvsFields = ['name', 'brand', 'summary'];
      const mvsConfidences = mvsFields.map(field => fieldExtractions[field]?.confidence || 0);
      const minMvsConfidence = Math.min(...mvsConfidences);
      
      if (minMvsConfidence < 0.7 || mvsFields.some(field => !fieldExtractions[field])) {
        decision = "FAIL";
        overallConfidence = minMvsConfidence;
        reason = `Critical fields missing or low confidence: min confidence ${minMvsConfidence.toFixed(2)}`;
        to_state = "FAILED";
        
        failedProducts.push({
          error: reason,
          confidence: overallConfidence,
          data: product
        });
      } else if (minMvsConfidence < 0.9) {
        decision = "FALLBACK";
        overallConfidence = minMvsConfidence;
        
        // Remove low-confidence fields directly from field_extractions
        for (const key in fieldExtractions) {
          if (!mvsFields.includes(key) && fieldExtractions[key].confidence < 0.7) {
            delete fieldExtractions[key];
          }
        }
        
        reason = `Falling back to optimized schema with fields above 0.7 confidence`;
        to_state = "FALLBACK";
        
        // Add the processed product with fallback
        processedProducts.push({
          field_extractions: fieldExtractions,
          llm_decision: decision,
          confidence: overallConfidence,
          fallback_applied: true,
          processor_notes: `MVS fields confidence: name=${fieldExtractions.name.confidence}, brand=${fieldExtractions.brand.confidence}, summary=${fieldExtractions.summary.confidence}`
        });
      } else {
        // Add the processed product
        processedProducts.push({
          field_extractions: fieldExtractions,
          llm_decision: decision,
          confidence: overallConfidence,
          fallback_applied: false,
          processor_notes: `MVS fields confidence: name=${fieldExtractions.name.confidence}, brand=${fieldExtractions.brand.confidence}, summary=${fieldExtractions.summary.confidence}`
        });
      }
    }
    
    // Create lifecycle log entry
    const logEntry = {
      document_id: item.json.document_id,
      from_state: "EXTRACTED",
      to_state: processedProducts.length > 0 ? "VALIDATED" : "FAILED",
      timestamp: new Date().toISOString(),
      agent: "llm_data_processor_v1",
      notes: processedProducts.length > 0 ? 
        `Successfully processed ${processedProducts.length} products` : 
        `Failed to process any products`
    };
    
    // If no products were processed successfully, return a failure
    if (processedProducts.length === 0) {
      return {
        json: {
          task_status: "failed",
          error_summary: "All products failed validation",
          document_id: item.json.document_id,
          failed_products: failedProducts,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
        }
      };
    }
    
    // Return processor results with all successfully processed products
    return {
      json: {
        ...item.json,
        products: processedProducts,
        product_count: processedProducts.length,
        failed_products: failedProducts.length > 0 ? failedProducts : undefined,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
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
  
  // Check for the products array
  if (!item.json.products || !Array.isArray(item.json.products) || item.json.products.length === 0) {
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "VALIDATED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "multimodal_verifier_v1",
      notes: "Missing or empty products array"
    };
    
    return {
      json: {
        task_status: "failed",
        error_summary: "Missing or empty products array",
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
  
  try {
    // Process each product individually for verification
    const verifiedProducts = [];
    const failedVerificationProducts = [];
    
    for (const product of item.json.products) {
      const fieldExtractions = product.field_extractions;
      const confidence = product.confidence || 0.9;
      const fallbackApplied = product.fallback_applied || false;
      
      // Simulate multimodal verification results for this product
      const verificationResults = {
        verification_passed: true,
        verified_fields: Object.keys(fieldExtractions),
        unverified_fields: [],
        confidence: 0.95,
        mvs_verification: {
          passed: true,
          confidence: 0.97,
          notes: "All MVS fields verified with high confidence"
        },
        evidence: Object.entries(fieldExtractions).reduce((obj, [key, field]) => {
          obj[key] = { 
            page: field.location?.page || 1, 
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
      
      // Prepare object with extracted values for cleaner response
      const extractedValues = {};
      for (const [key, field] of Object.entries(fieldExtractions)) {
        extractedValues[key] = field.value;
      }
      
      if (verificationResults.verification_passed) {
        verifiedProducts.push({
          extracted_values: extractedValues,
          verification_passed: true,
          reason: "Verification successful",
          verification_results: verificationResults,
          fallback_applied: fallbackApplied
        });
      } else {
        failedVerificationProducts.push({
          extracted_values: extractedValues,
          verification_passed: false,
          reason: `Failed to verify: ${verificationResults.unverified_fields.join(', ')}`,
          verification_results: verificationResults,
          fallback_applied: fallbackApplied
        });
      }
    }
    
    // Create lifecycle log entry
    const allVerifiedPassed = verifiedProducts.length > 0 && failedVerificationProducts.length === 0;
    const partialVerificationPassed = verifiedProducts.length > 0;
    const verifierState = item.json.products.some(p => p.fallback_applied) ? "FALLBACK" : "VALIDATED";
    const targetState = allVerifiedPassed ? 
      (item.json.products.some(p => p.fallback_applied) ? "COMPLETED_WITH_FALLBACK" : "VERIFIED") : 
      partialVerificationPassed ? "COMPLETED_WITH_PARTIAL" : "FAILED";
    
    const logEntry = {
      document_id: item.json.document_id,
      from_state: verifierState,
      to_state: targetState,
      timestamp: new Date().toISOString(),
      agent: "multimodal_verifier_v1",
      notes: allVerifiedPassed ? 
        `Verified ${verifiedProducts.length} products successfully` : 
        partialVerificationPassed ?
        `Partially verified: ${verifiedProducts.length} products passed, ${failedVerificationProducts.length} failed` :
        `Verification failed for all ${failedVerificationProducts.length} products`
    };
    
    // If no products were verified, return a failure
    if (verifiedProducts.length === 0) {
      return {
        json: {
          task_status: "failed",
          error_summary: "All products failed verification",
          document_id: item.json.document_id,
          failed_verifications: failedVerificationProducts,
          _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
        }
      };
    }
    
    // Return verification results with all successfully verified products
    return {
      json: {
        verification_passed: allVerifiedPassed,
        reason: allVerifiedPassed ? 
          "All products verified successfully" : 
          `${verifiedProducts.length} products verified, ${failedVerificationProducts.length} failed verification`,
        products: verifiedProducts,
        failed_products: failedVerificationProducts.length > 0 ? failedVerificationProducts : undefined,
        document_id: item.json.document_id,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry],
        verifier_version: "multimodal-v1.5",
        original_request: item.json.original_request,
        partial_success: !allVerifiedPassed && partialVerificationPassed
      }
    };
  } catch (error) {
    // Error handling
    const errorEntry = {
      document_id: item.json.document_id,
      from_state: "VALIDATED",
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
  
  // Get product count
  const productCount = item.json.products ? item.json.products.length : 0;
  const partialSuccess = item.json.partial_success || false;
  
  // Format JSON for attachment - use extracted_values
  const cleanedProducts = item.json.products.map(product => product.extracted_values);
  const jsonStr = JSON.stringify(cleanedProducts, null, 2);
  
  // Add fallback note if applicable
  const fallbackNote = item.json.products.some(p => p.fallback_applied) ? 
    'Note: Simplified metadata extracted for some products due to confidence thresholds.' : 
    '';
  
  // Create email content
  let emailBody = `Subject: ✅ Material Metadata Extracted\n\nDear ${sender},\n\n`;
  
  if (productCount === 1) {
    // Single product email
    const product = item.json.products[0].extracted_values;
    emailBody += `The attached PDF has been successfully processed. The extracted metadata is included below in JSON format.\n\n`;
    emailBody += `Material: ${product.name || 'Unnamed Material'}\n`;
    emailBody += `Brand: ${product.brand || 'Unspecified Brand'}\n`;
  } else {
    // Multiple product email
    emailBody += `The attached PDF has been successfully processed. ${productCount} products were extracted and their metadata is included below in JSON format.\n\n`;
    emailBody += `Products:\n`;
    
    // List first few products
    const maxToList = Math.min(productCount, 5);
    for (let i = 0; i < maxToList; i++) {
      const product = item.json.products[i].extracted_values;
      emailBody += `${i+1}. ${product.name || 'Unnamed Material'} (${product.brand || 'Unspecified Brand'})\n`;
    }
    
    if (productCount > maxToList) {
      emailBody += `... and ${productCount - maxToList} more\n`;
    }
  }
  
  // Add notes
  if (fallbackNote) {
    emailBody += `\n${fallbackNote}\n`;
  }
  
  if (partialSuccess) {
    emailBody += `\nNote: Some products could not be fully verified and were excluded from the results.\n`;
  }
  
  emailBody += `\nBest regards,\nMaterials Library Bot`;
  
  return {
    json: {
      to: sender,
      subject: `✅ Material Metadata Extracted (${productCount} product${productCount !== 1 ? 's' : ''})`,
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
  
  // Check if there were partial failures
  const failedProducts = item.json.failed_products || [];
  const failedCount = Array.isArray(failedProducts) ? failedProducts.length : 0;
  
  // Create email content
  let emailBody = `Subject: ❌ Metadata Extraction Failed\n\nDear ${sender},\n\n`;
  
  emailBody += `The attached PDF could not be processed due to the following issue:\n\n${reason}\n\n`;
  
  if (failedCount > 0) {
    emailBody += `${failedCount} product(s) failed processing:\n`;
    // List reasons for first few failures
    const maxToList = Math.min(failedCount, 3);
    for (let i = 0; i < maxToList; i++) {
      const product = failedProducts[i];
      // Access product values differently now
      const productName = product.extracted_values?.name || 
                         product.data?.field_extractions?.name?.value || 
                         "Unknown product";
      const productError = product.error || "Validation failed";
      emailBody += `- ${productName}: ${productError}\n`;
    }
    
    if (failedCount > maxToList) {
      emailBody += `... and ${failedCount - maxToList} more\n`;
    }
  }
  
  emailBody += `\nPlease check the document and try again.\n\nBest regards,\nMaterials Library Bot`;
  
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
  // multimodalMetadataExtractor removed (integrated into LLM Extraction node)
  llmDataProcessor,
  multimodalVerifier,
  
  // Email formatters
  formatSuccessEmail,
  formatErrorEmail
};