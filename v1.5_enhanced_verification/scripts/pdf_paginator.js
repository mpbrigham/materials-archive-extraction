// PDF Paginator Node Implementation for IMIS V1.5
// Converts PDFs to sequences of page images for multimodal LLM processing

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const util = require('util');
const execPromise = util.promisify(exec);

/**
 * Converts a PDF file to a sequence of page images
 * @param {Object} items - Input items from n8n workflow
 * @param {number} runIndex - Current run index
 * @returns {Object} - Output with page image information
 */
const pdfPaginator = async function(items, runIndex) {
  if (!items || items.length === 0) {
    throw new Error("No items received by PDF Paginator");
  }
  
  const item = items[0];
  
  // Get PDF file path from input
  const pdfPath = item.json.file_path;
  if (!pdfPath) {
    return {
      json: {
        success: false,
        error: "No PDF file path provided",
        document_id: item.json.document_id
      }
    };
  }
  
  // Get document ID for tracking
  const documentId = item.json.document_id || `doc-${Date.now()}`;
  
  // Setup output directories
  const storageRoot = process.env.STORAGE_PATH || './storage';
  const pagesDir = path.join(storageRoot, documentId, 'pages');
  
  try {
    // Ensure the directories exist
    if (!fs.existsSync(path.join(storageRoot, documentId))) {
      fs.mkdirSync(path.join(storageRoot, documentId), { recursive: true });
    }
    if (!fs.existsSync(pagesDir)) {
      fs.mkdirSync(pagesDir, { recursive: true });
    }
    
    // Run the Python paginator script
    const pythonScript = path.join(__dirname, 'utils', 'image_processing.py');
    const command = `python "${pythonScript}" paginate "${pdfPath}" --output "${pagesDir}" --dpi 300`;
    
    const { stdout, stderr } = await execPromise(command);
    
    if (stderr && !stderr.includes('INFO')) {
      console.error(`Paginator error: ${stderr}`);
      throw new Error(`PDF pagination failed: ${stderr}`);
    }
    
    // Parse the output to get image paths
    const pageImages = [];
    const lines = stdout.split('\n');
    
    for (const line of lines) {
      if (line.includes('Page') && line.includes(':')) {
        const pagePart = line.split('Page ')[1];
        if (pagePart) {
          const [pageNum, imagePath] = pagePart.split(':').map(s => s.trim());
          if (pageNum && imagePath) {
            pageImages.push({
              page: parseInt(pageNum, 10),
              path: imagePath
            });
          }
        }
      }
    }
    
    // Sort images by page number
    pageImages.sort((a, b) => a.page - b.page);
    
    // Create lifecycle log entry
    const logEntry = {
      document_id: documentId,
      from_state: item.json.from_state || "RECEIVED",
      to_state: "PAGINATED",
      timestamp: new Date().toISOString(),
      agent: "pdf_paginator_v1.5",
      notes: `PDF converted to ${pageImages.length} page images`
    };
    
    // Return the processed data
    return {
      json: {
        ...item.json,
        page_images: pageImages,
        pages_directory: pagesDir,
        document_id: documentId,
        _lifecycle_log: [...(item.json._lifecycle_log || []), logEntry]
      }
    };
  } catch (error) {
    // Handle errors gracefully
    console.error(`PDF Paginator error: ${error.message}`);
    
    const errorEntry = {
      document_id: documentId,
      from_state: item.json.from_state || "RECEIVED",
      to_state: "FAILED",
      timestamp: new Date().toISOString(),
      agent: "pdf_paginator_v1.5",
      notes: `PDF pagination failed: ${error.message}`
    };
    
    return {
      json: {
        success: false,
        error: `PDF pagination failed: ${error.message}`,
        document_id: documentId,
        file_path: pdfPath,
        _lifecycle_log: [...(item.json._lifecycle_log || []), errorEntry]
      }
    };
  }
};

module.exports = {
  pdfPaginator
};