// LLM Extraction Function for Materials Library Extraction
// Enhanced LLM Extraction with File Upload
// Makes two sequential HTTP requests: upload PDF then generate content

const llmExtraction = async function(items) {
  const fs = require('fs');
  const https = require('https');
  const http = require('http');

  // Log node start with input
  fs.appendFileSync('/home/node/data/debug.log', 
    `${new Date().toISOString()} - llm_extraction - START\n` +
    `INPUT: ${JSON.stringify(items, null, 2)}\n`
  );

  if (!items || items.length === 0) {
    throw new Error('No items received by LLM Extraction');
  }

  // Process each item (one per PDF attachment)
  const results = [];
  
  for (const item of items) {
    const documentId = item.json.document_id;
    const groupId = item.json.group_id;
    const isRetry = item.json.task === "retry_extraction";
    const retryCount = item.json.retry_count;
    const attachmentIndex = item.json.attachment_index;
    const totalAttachments = item.json.total_attachments;
    const attachmentKey = item.json.attachment_key;
    
    try {
      // Step 1: Upload PDF to Gemini Files API
      const fileContent = Buffer.from(item.binary[attachmentKey].data, 'base64');
      const fileName = item.binary[attachmentKey].fileName;
      
      const uploadOptions = {
        hostname: 'generativelanguage.googleapis.com',
        port: 443,
        path: '/upload/v1beta/files',
        method: 'POST',
        headers: {
          'X-goog-api-key': process.env.LLM_API_KEY,
          'Content-Type': 'application/pdf',
          'Content-Length': fileContent.length
        }
      };
      
      // Make upload request
      const uploadResponse = await new Promise((resolve, reject) => {
        const req = https.request(uploadOptions, (res) => {
          let data = '';
          res.on('data', (chunk) => { data += chunk; });
          res.on('end', () => {
            try {
              resolve(JSON.parse(data));
            } catch (err) {
              reject(new Error(`Upload response parse error: ${err.message}`));
            }
          });
        });
        
        req.on('error', reject);
        req.write(fileContent);
        req.end();
      });
      
      if (!uploadResponse.file || !uploadResponse.file.uri) {
        throw new Error('File upload failed - no URI returned');
      }
      
      const uploadedFileUri = uploadResponse.file.uri;
      
      // Step 2: Generate content using uploaded file
      const promptContent = fs.readFileSync('/home/node/prompts/llm_extraction.txt', 'utf8');
      const materialsSchema = JSON.parse(fs.readFileSync('/home/node/specs/MATERIALS_SCHEMA.json', 'utf8'));
      
      const generatePayload = {
        contents: [{
          parts: [{
            text: `${promptContent}\n\nNow analyze the document: ${fileName}`
          }, {
            fileData: {
              mimeType: 'application/pdf',
              fileUri: uploadedFileUri
            }
          }]
        }],
        generationConfig: {
          temperature: 0.2,
          maxOutputTokens: 8000,
          responseMimeType: 'application/json',
          responseSchema: materialsSchema
        }
      };
      
      const generateOptions = {
        hostname: 'generativelanguage.googleapis.com',
        port: 443,
        path: `/v1beta/models/gemini-2.0-flash:generateContent`,
        method: 'POST',
        headers: {
          'X-goog-api-key': process.env.LLM_API_KEY,
          'Content-Type': 'application/json',
          'Content-Length': JSON.stringify(generatePayload).length
        }
      };
      
      // Make generation request
      const generateResponse = await new Promise((resolve, reject) => {
        const req = https.request(generateOptions, (res) => {
          let data = '';
          res.on('data', (chunk) => { data += chunk; });
          res.on('end', () => {
            try {
              resolve(JSON.parse(data));
            } catch (err) {
              reject(new Error(`Generation response parse error: ${err.message}`));
            }
          });
        });
        
        req.on('error', reject);
        req.write(JSON.stringify(generatePayload));
        req.end();
      });
      
      // Process the generation response
      const extractedData = generateResponse.candidates[0].content.parts[0].text;
      if (!extractedData) {
        throw new Error('No content generated from LLM');
      }
      
      const parsedData = JSON.parse(extractedData);
      if (!parsedData.products || !parsedData.processing_summary) {
        throw new Error('Invalid response structure from LLM API');
      }
      
      // Transform products to include confidence scoring
      const transformedProducts = parsedData.products.map(product => {
        let totalConfidence = 0;
        let fieldCount = 0;
        
        Object.keys(product).forEach(key => {
          if (product[key] && typeof product[key] === 'object' && product[key].confidence !== undefined) {
            totalConfidence += product[key].confidence;
            fieldCount++;
          }
        });
        
        const avgConfidence = fieldCount > 0 ? totalConfidence / fieldCount : 0;
        
        return {
          field_extractions: product,
          average_confidence: avgConfidence
        };
      });
      
      // Extract language
      let language_detected = "unknown";
      if (parsedData.products.length > 0 && parsedData.products[0].language_detected && parsedData.products[0].language_detected.value) {
        language_detected = parsedData.products[0].language_detected.value;
      }
      
      // Build result
      const result = {
        products: transformedProducts,
        language_detected: language_detected,
        processing_summary: parsedData.processing_summary,
        verification_passed: transformedProducts.length > 0,
        document_id: documentId,
        group_id: groupId,
        attachment_index: attachmentIndex,
        total_attachments: totalAttachments,
        product_count: transformedProducts.length,
        sender: item.json.sender,
        subject: item.json.subject,
        timestamp: item.json.timestamp,
        retry_count: retryCount,
        uploaded_file_uri: uploadedFileUri,
        _lifecycle_log: [...item.json._lifecycle_log, {
          document_id: documentId,
          from_state: isRetry ? "RETRY_EXTRACTION" : "INTERPRETED",
          to_state: "UPLOADED",
          timestamp: new Date().toISOString(),
          agent: "enhanced_metadata_extractor",
          notes: `PDF uploaded to Gemini: ${uploadedFileUri}`
        }, {
          document_id: documentId,
          from_state: "UPLOADED",
          to_state: "EXTRACTED",
          timestamp: new Date().toISOString(),
          agent: "enhanced_metadata_extractor",
          notes: isRetry ? 
            `Schema-constrained retry extraction attempt ${retryCount} completed - ${transformedProducts.length} product(s) extracted, language=${language_detected}` : 
            `Schema-constrained extraction completed - ${transformedProducts.length} product(s) extracted, language=${language_detected}`
        }],
        original_request: isRetry ? item.json.original_request : item.json
      };
      
      results.push({ json: result });
      
    } catch (error) {
      console.error(`Error processing ${documentId}: ${error.message}`);
      
      // Log error to file
      const fs = require('fs');
      fs.appendFileSync('/home/node/data/debug.log', 
        `${new Date().toISOString()} - llm_extraction - ERROR: Document ${documentId} - ${error.message}\n`
      );
      
      // Error handling
      const errorEntry = {
        document_id: documentId,
        from_state: isRetry ? "RETRY_EXTRACTION" : "INTERPRETED",
        to_state: "FAILED",
        timestamp: new Date().toISOString(),
        agent: "enhanced_metadata_extractor",
        notes: `Upload and extraction failed: ${error.message}`
      };
      
      results.push({
        json: {
          task_status: "failed",
          error_summary: `Upload and metadata extraction failed: ${error.message}`,
          document_id: documentId,
          group_id: groupId,
          verification_passed: false,
          retry_count: retryCount,
          _lifecycle_log: [...item.json._lifecycle_log, errorEntry]
        }
      });
    }
  }
  
  // Log node completion with output
  fs.appendFileSync('/home/node/data/debug.log', 
    `${new Date().toISOString()} - llm_extraction - SUCCESS\n` +
    `OUTPUT: ${JSON.stringify(results, null, 2)}\n`
  );
  
  return results;
};

module.exports = { llmExtraction };
