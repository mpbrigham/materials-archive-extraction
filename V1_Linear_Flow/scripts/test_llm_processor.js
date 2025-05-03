// Test script for the LLM-based data processor implementation
// Run with: node test_llm_processor.js

const { llmDataProcessor } = require('./functions_multimodal_enhanced');

// Sample test cases with varying confidence levels
const testCases = [
  {
    name: "High confidence test - PROCEED",
    input: {
      json: {
        metadata_json: {
          name: "EcoBoard Pro X-340",
          brand: "GreenMaterials Inc.",
          summary: "High-performance sustainable wood panel for architectural applications",
          category: "Wood",
          dimensions: {
            width_mm: 2400,
            height_mm: 1200,
            length_mm: null
          },
          certifications: ["ISO 14001", "FSC"]
        },
        field_confidences: {
          name: 0.98,
          brand: 0.97,
          summary: 0.96,
          category: 0.93,
          dimensions: 0.95,
          certifications: 0.91
        },
        document_id: "doc-1234567890",
        _lifecycle_log: [{
          document_id: "doc-1234567890",
          from_state: "INTERPRETED",
          to_state: "EXTRACTED",
          timestamp: new Date().toISOString(),
          agent: "multimodal_metadata_extractor_v1",
          notes: "Multimodal extraction with visual coordinates completed"
        }]
      }
    },
    expectedDecision: "PROCEED"
  },
  {
    name: "Medium confidence test - FALLBACK",
    input: {
      json: {
        metadata_json: {
          name: "EcoBoard Pro X-340",
          brand: "GreenMaterials Inc.",
          summary: "High-performance sustainable wood panel",
          category: "Wood",
          dimensions: {
            width_mm: 2400,
            height_mm: 1200,
            length_mm: null
          },
          certifications: ["ISO 14001"]
        },
        field_confidences: {
          name: 0.88,
          brand: 0.87,
          summary: 0.85,
          category: 0.80,
          dimensions: 0.75,
          certifications: 0.73
        },
        document_id: "doc-2345678901",
        _lifecycle_log: [{
          document_id: "doc-2345678901",
          from_state: "INTERPRETED",
          to_state: "EXTRACTED",
          timestamp: new Date().toISOString(),
          agent: "multimodal_metadata_extractor_v1",
          notes: "Multimodal extraction with visual coordinates completed"
        }]
      }
    },
    expectedDecision: "FALLBACK"
  },
  {
    name: "Low confidence test - FAIL",
    input: {
      json: {
        metadata_json: {
          name: "EcoBoard Pro",
          brand: null,
          summary: "Wood panel",
          category: "Wood",
          dimensions: {
            width_mm: 2400,
            height_mm: null,
            length_mm: null
          }
        },
        field_confidences: {
          name: 0.72,
          brand: 0.65,
          summary: 0.70,
          category: 0.68,
          dimensions: 0.60
        },
        document_id: "doc-3456789012",
        _lifecycle_log: [{
          document_id: "doc-3456789012",
          from_state: "INTERPRETED",
          to_state: "EXTRACTED",
          timestamp: new Date().toISOString(),
          agent: "multimodal_metadata_extractor_v1",
          notes: "Multimodal extraction with visual coordinates completed"
        }]
      }
    },
    expectedDecision: "FAIL"
  },
  {
    name: "Missing required field test - FAIL",
    input: {
      json: {
        metadata_json: {
          name: "EcoBoard Pro X-340",
          brand: "GreenMaterials Inc.",
          // Missing summary
          category: "Wood",
          dimensions: {
            width_mm: 2400,
            height_mm: 1200,
            length_mm: null
          }
        },
        field_confidences: {
          name: 0.95,
          brand: 0.92,
          category: 0.90,
          dimensions: 0.88
        },
        document_id: "doc-4567890123",
        _lifecycle_log: [{
          document_id: "doc-4567890123",
          from_state: "INTERPRETED",
          to_state: "EXTRACTED",
          timestamp: new Date().toISOString(),
          agent: "multimodal_metadata_extractor_v1",
          notes: "Multimodal extraction with visual coordinates completed"
        }]
      }
    },
    expectedDecision: "FAIL"
  }
];

// Run all test cases
async function runTests() {
  console.log("Testing LLM Data Processor...\n");
  
  for (const [index, test] of testCases.entries()) {
    console.log(`Test ${index + 1}: ${test.name}`);
    
    try {
      const result = await llmDataProcessor([test.input], 0);
      
      // Check the decision path
      let actualDecision;
      if (result.json.task_status === "failed") {
        actualDecision = "FAIL";
      } else if (result.json.fallback_applied) {
        actualDecision = "FALLBACK";
      } else {
        actualDecision = "PROCEED";
      }
      
      // Log the result
      console.log(`  Expected: ${test.expectedDecision}`);
      console.log(`  Actual: ${actualDecision}`);
      
      if (actualDecision === test.expectedDecision) {
        console.log("  ✅ PASS");
      } else {
        console.log("  ❌ FAIL");
        console.log("  Decision details:", result.json.processor_notes || result.json.error_summary);
      }
      
      // Show key output data
      console.log("  Confidence:", result.json.confidence || "N/A");
      console.log("  Fields retained:", result.json.metadata_json ? Object.keys(result.json.metadata_json).length : 0);
      
      // Show state transition
      const logEntry = result.json._lifecycle_log[result.json._lifecycle_log.length - 1];
      console.log(`  State transition: ${logEntry.from_state} → ${logEntry.to_state}`);
      
    } catch (error) {
      console.log(`  ❌ ERROR: ${error.message}`);
    }
    
    console.log(""); // Empty line between tests
  }
  
  console.log("Test run complete!");
}

// Run the tests
runTests().catch(error => {
  console.error("Test execution error:", error);
});