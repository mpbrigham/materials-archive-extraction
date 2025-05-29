// Enhanced Extractor Node Implementation for IMIS V1.5
// Multi-turn extraction and verification with page images and crops

/**
 * Processes metadata extraction with visual verification
 * @param {Object} items - Input items from n8n workflow
 * @param {number} runIndex - Current run index
 * @returns {Object} - Output with extracted and verified metadata
 */
const enhancedExtractor = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Enhanced Extractor");
  }
  
  const item = items[0];
  
  // Get necessary input data
  const documentId = item.json.document_id;
  
  // Check if this is the initial extraction or verification with crops
  const isVerification = item.json.field_crops !== undefined;
  
  try {
    if (isVerification) {
      // This is the verification step with crops
      return processVerification(item);
    } else {
      // This is the initial extraction with full pages
      return processInitialExtraction(item);
    }
  } catch (error) {
    // Handle errors gracefully
    console.error(`Enhanced Extractor error: ${error.message}`);
    
    const errorEntry = {
      document_id: documentId,
      from_state: isVerification ? "CROPS_GENERATED" : "PAGINATED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "enhanced_extractor_v1.5",
      notes: `Extraction failed: ${error.message}`
    };
    
    return {
      json: {
        success: false,
        error: `Extraction failed: ${error.message}`,
        document_id: documentId,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

/**
 * Process initial extraction from full page images
 * @param {Object} item - Input item
 * @returns {Object} - Initial extraction result
 */
function processInitialExtraction(item) {
  // In a real implementation, this would call the LLM API with page images
  // For this demonstration, we'll simulate results
  
  const documentId = item.json.document_id;
  const pageImages = item.json.page_images || [];
  
  // Simulated extraction result with location data
  const extractedFields = {
    name: {
      value: "Porcelain Matte",
      confidence: 0.85,
      location: {
        page: 1,
        bbox: [120, 210, 285, 230]
      }
    },
    brand: {
      value: "SampleTileCo",
      confidence: 0.78,
      location: {
        page: 1,
        bbox: [140, 250, 300, 270]
      }
    },
    category: {
      value: "Ceramic",
      confidence: 0.92,
      location: {
        page: 1,
        bbox: [150, 290, 250, 310]
      }
    },
    dimensions: {
      value: "300x300 mm",
      confidence: 0.75,
      location: {
        page: 2,
        bbox: [210, 350, 310, 370]
      }
    },
    certifications: {
      value: ["ISO 14001", "LEED v4"],
      confidence: 0.82,
      location: {
        page: 2,
        bbox: [200, 400, 350, 440]
      }
    },
    performance: {
      value: {
        thermal_resistance: "R-3.5",
        fire_rating: "Class A"
      },
      confidence: 0.79,
      location: {
        page: 2,
        bbox: [180, 450, 400, 520]
      }
    },
    summary: {
      value: "High-quality porcelain ceramic tile with matte finish, suitable for interior and exterior applications",
      confidence: 0.88,
      location: {
        page: 1,
        bbox: [100, 320, 500, 380]
      }
    },
    keywords: {
      value: ["porcelain", "ceramic", "matte", "tile", "interior", "exterior"],
      confidence: 0.85,
      location: {
        page: 3,
        bbox: [150, 200, 450, 250]
      }
    }
  };
  
  // Create lifecycle log entry
  const logEntry = {
    document_id: documentId,
    from_state: "PAGINATED",
    to_state: "EXTRACTION_INITIAL",
    timestamp: new Date().toISOString(),
    agent: "enhanced_extractor_v1.5",
    notes: `Initial extraction complete with ${Object.keys(extractedFields).length} fields`
  };
  
  // Return the extracted data
  return {
    json: {
      ...item.json,
      extracted_fields: extractedFields,
      extraction_stage: "initial",
      needs_verification: true,
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

/**
 * Process verification with cropped field images
 * @param {Object} item - Input item with field crops
 * @returns {Object} - Final verified extraction result
 */
function processVerification(item) {
  const documentId = item.json.document_id;
  const fieldCrops = item.json.field_crops || {};
  const extractedFields = item.json.extracted_fields || {};
  
  // Final verified fields with evidence
  const verifiedFields = {};
  
  // Process each field with its crop
  for (const [fieldName, fieldData] of Object.entries(extractedFields)) {
    const cropInfo = fieldCrops[fieldName];
    
    // Skip fields without crops
    if (!cropInfo) {
      verifiedFields[fieldName] = {
        ...fieldData,
        verification: {
          verified: false,
          reason: "No crop available for verification",
          final_confidence: fieldData.confidence * 0.7 // Penalize unverified fields
        }
      };
      continue;
    }
    
    // Simulate crop-based verification
    // In a real implementation, this would call the LLM with the crop image
    
    // For most fields, we'll confirm the initial extraction
    let verifiedValue = fieldData.value;
    let detailConfidence = fieldData.confidence + 0.1; // Slightly boost confidence
    let verified = true;
    let matchesInitial = true;
    
    // For one field, simulate a correction
    if (fieldName === 'dimensions') {
      verifiedValue = "300x600 mm"; // Changed from 300x300
      detailConfidence = 0.95;
      matchesInitial = false;
    }
    
    // Calculate final confidence
    const contextAgreementFactor = matchesInitial ? 1.0 : 0.8;
    const finalConfidence = Math.min(
      0.99, 
      fieldData.confidence * detailConfidence * contextAgreementFactor
    );
    
    // Add the verified field
    verifiedFields[fieldName] = {
      value: verifiedValue, // Use the verified (possibly corrected) value
      original_value: fieldData.value,
      confidence: finalConfidence,
      location: fieldData.location,
      verification: {
        verified: true,
        crop_path: cropInfo.crop_path,
        matches_initial: matchesInitial,
        reason: matchesInitial ? 
          "Confirmed match between context and detail" : 
          "Detail view provides correction to initial extraction",
        context_confidence: fieldData.confidence,
        detail_confidence: detailConfidence,
        final_confidence: finalConfidence
      }
    };
  }
  
  // Calculate overall document confidence
  const confidenceValues = Object.values(verifiedFields).map(f => f.confidence);
  const overallConfidence = confidenceValues.reduce((sum, val) => sum + val, 0) / confidenceValues.length;
  
  // Extract simpler metadata_json for downstream processing
  const metadata_json = {};
  for (const [field, data] of Object.entries(verifiedFields)) {
    metadata_json[field] = data.value;
  }
  
  // Create lifecycle log entry
  const logEntry = {
    document_id: documentId,
    from_state: "CROPS_GENERATED",
    to_state: "EXTRACTED",
    timestamp: new Date().toISOString(),
    agent: "enhanced_extractor_v1.5",
    notes: `Visual verification complete. Overall confidence: ${overallConfidence.toFixed(2)}`
  };
  
  // Return the verified data
  return {
    json: {
      ...item.json,
      verified_fields: verifiedFields,
      metadata_json: metadata_json,
      extraction_stage: "verified",
      overall_confidence: overallConfidence,
      _metadata: {
        prompt_id: "v1.5-visual",
        model_version: "multimodal-vision",
        generated_ts: new Date().toISOString(),
        verification_method: "multi-turn visual"
      },
      _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
    }
  };
}

module.exports = {
  enhancedExtractor
};