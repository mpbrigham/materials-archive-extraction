// Image Cropper Node Implementation for IMIS V1.5
// Crops regions from page images based on bounding box coordinates

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const util = require('util');
const execPromise = util.promisify(exec);

/**
 * Crops regions from page images based on field coordinates
 * @param {Object} items - Input items from n8n workflow
 * @param {number} runIndex - Current run index
 * @returns {Object} - Output with cropped image information
 */
const imageCropper = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by Image Cropper");
  }
  
  const item = items[0];
  
  // Get necessary input data
  const documentId = item.json.document_id;
  const pageImages = item.json.page_images || [];
  const extractedFields = item.json.extracted_fields || {};
  
  if (!documentId || pageImages.length === 0 || Object.keys(extractedFields).length === 0) {
    return {
      json: {
        success: false,
        error: "Missing required input: document ID, page images, or extracted fields",
        document_id: documentId
      }
    };
  }
  
  // Setup output directory for cropped images
  const storageRoot = process.env.STORAGE_PATH || './storage';
  const cropsDir = path.join(storageRoot, documentId, 'crops');
  
  try {
    // Ensure the directory exists
    if (!fs.existsSync(cropsDir)) {
      fs.mkdirSync(cropsDir, { recursive: true });
    }
    
    // Create a map of page number to image path
    const pageImageMap = {};
    for (const img of pageImages) {
      pageImageMap[img.page] = img.path;
    }
    
    // Process each field with location data
    const fieldCrops = {};
    const pythonScript = path.join(__dirname, 'utils', 'image_processing.py');
    
    for (const [fieldName, fieldData] of Object.entries(extractedFields)) {
      // Skip fields without location data
      if (!fieldData.location || !fieldData.location.page || !fieldData.location.bbox) {
        continue;
      }
      
      const page = fieldData.location.page;
      const bbox = fieldData.location.bbox;
      
      // Find the image for this page
      const imagePath = pageImageMap[page];
      if (!imagePath) {
        console.warn(`No image found for page ${page} of field ${fieldName}`);
        continue;
      }
      
      // Convert bbox array to string
      const bboxString = bbox.join(',');
      
      // Execute the cropping
      const command = `python "${pythonScript}" crop "${imagePath}" ${bboxString} --output "${cropsDir}" --padding 20`;
      
      const { stdout, stderr } = await execPromise(command);
      
      if (stderr && !stderr.includes('INFO')) {
        console.error(`Cropper error for ${fieldName}: ${stderr}`);
        continue;
      }
      
      // Parse the output to get cropped image path
      const cropPathLine = stdout.split('\n').find(line => line.includes('Cropped image:'));
      if (cropPathLine) {
        const cropPath = cropPathLine.split('Cropped image:')[1].trim();
        
        // Store the crop information
        fieldCrops[fieldName] = {
          original_field: fieldData,
          crop_path: cropPath,
          source_page: page,
          source_bbox: bbox
        };
      }
    }
    
    // Create lifecycle log entry
    const logEntry = {
      document_id: documentId,
      from_state: "EXTRACTION_INITIAL",
      to_state: "CROPS_GENERATED",
      timestamp: new Date().toISOString(),
      agent: "image_cropper_v1.5",
      notes: `Generated ${Object.keys(fieldCrops).length} field crops for verification`
    };
    
    // Return the processed data
    return {
      json: {
        ...item.json,
        field_crops: fieldCrops,
        crops_directory: cropsDir,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
      }
    };
  } catch (error) {
    // Handle errors gracefully
    console.error(`Image Cropper error: ${error.message}`);
    
    const errorEntry = {
      document_id: documentId,
      from_state: "EXTRACTION_INITIAL",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "image_cropper_v1.5",
      notes: `Image cropping failed: ${error.message}`
    };
    
    return {
      json: {
        success: false,
        error: `Image cropping failed: ${error.message}`,
        document_id: documentId,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

module.exports = {
  imageCropper
};