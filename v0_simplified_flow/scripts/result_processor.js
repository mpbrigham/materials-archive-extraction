// Result Processor Function for Materials Library Extraction
// Consolidates Validation Router + Success Notifier + Error Notifier
// Handles both success and error scenarios with multi-attachment support
// Uses email templates for formatting

const fs = require('fs');

const processResults = function(items) {
  // Log node start with input
  fs.appendFileSync('/home/node/data/debug.log', 
    `${new Date().toISOString()} - result_processor - START\n` +
    `INPUT: ${JSON.stringify(items, null, 2)}\n`
  );
  
  try {
    if (!items || items.length === 0) {
      throw new Error("No items received by Result Processor");
    }

    // Group items by group_id (multiple attachments from same email)
    const groupedItems = {};
    
    items.forEach(item => {
      const groupId = item.json.group_id;
      if (!groupedItems[groupId]) {
        groupedItems[groupId] = [];
      }
      groupedItems[groupId].push(item);
    });

    // Process each email group
    const result = Object.keys(groupedItems).map(groupId => {
      const groupItems = groupedItems[groupId];
      
      // Determine overall success/failure for this email group
      const hasSuccessfulItems = groupItems.some(item => item.json.verification_passed === true);
      const hasFailedItems = groupItems.some(item => item.json.verification_passed === false);
      
      let emailResult;
      if (hasSuccessfulItems) {
        // Route to success processing (even if some items failed - partial success)
        emailResult = formatSuccessEmail(groupItems, groupId);
        
        // Log success summary
        const fs = require('fs');
        const productCount = groupItems.reduce((sum, item) => 
          sum + (item.json.products ? item.json.products.length : 0), 0);
        fs.appendFileSync('/home/node/data/debug.log', 
          `${new Date().toISOString()} - result_processor - SUCCESS: Group ${groupId} - ${productCount} products extracted from ${groupItems.length} PDFs\n`
        );
      } else {
        // Route to error processing (all items failed)
        emailResult = formatErrorEmail(groupItems, groupId);
        
        // Log failure summary
        const fs = require('fs');
        fs.appendFileSync('/home/node/data/debug.log', 
          `${new Date().toISOString()} - result_processor - FAILED: Group ${groupId} - All ${groupItems.length} PDFs failed processing\n`
        );
      }
      return emailResult;
    });
    
    // Log node completion with output
    fs.appendFileSync('/home/node/data/debug.log', 
      `${new Date().toISOString()} - result_processor - SUCCESS\n` +
      `OUTPUT: ${JSON.stringify(result, null, 2)}\n`
    );
    
    return result;

  } catch (error) {
    console.error(`Error in Result Processor: ${error.message}`);
    
    // Log error to file
    const fs = require('fs');
    fs.appendFileSync('/home/node/data/debug.log', 
      `${new Date().toISOString()} - result_processor - ERROR: ${error.message}\n`
    );
    
    // If we can't process results, we can't determine who to email
    // Let this error bubble up to Global Error Handler instead of sending to fake email
    throw new Error(`Result processor system failure: ${error.message}`);
  }
};

// SUCCESS EMAIL FORMATTING FUNCTION (Template-based)
function formatSuccessEmail(groupItems, groupId) {
  const firstItem = groupItems[0];
  
  // Collect all products across all attachments in this email
  const allProducts = [];
  const allProcessingSummaries = [];
  let allLogs = [];
  
  groupItems.forEach(item => {
    if (item.json.products && Array.isArray(item.json.products)) {
      item.json.products.forEach(product => {
        allProducts.push({
          ...product,
          source_attachment: item.json.attachment_index,
          document_id: item.json.document_id
        });
      });
    }
    
    if (item.json.processing_summary) {
      allProcessingSummaries.push({
        attachment_index: item.json.attachment_index,
        summary: item.json.processing_summary
      });
    }
    
    if (item.json._lifecycle_log) {
      allLogs = allLogs.concat(item.json._lifecycle_log);
    }
  });

  // Group products by confidence levels
  const highConfidenceProducts = [];
  const mediumConfidenceProducts = [];
  const lowConfidenceProducts = [];

  allProducts.forEach(product => {
    const avgConfidence = product.average_confidence || 0;
    
    if (avgConfidence >= 0.9) {
      highConfidenceProducts.push(product);
    } else if (avgConfidence >= 0.7) {
      mediumConfidenceProducts.push(product);
    } else {
      lowConfidenceProducts.push(product);
    }
  });

  // Load email template
  const template = loadTemplate('success');
  
  // Prepare template data
  const templateData = {
    emailSubject: firstItem.json.subject,
    totalAttachments: groupItems.length,
    totalProducts: allProducts.length,
    highCount: highConfidenceProducts.length,
    mediumCount: mediumConfidenceProducts.length,
    lowCount: lowConfidenceProducts.length,
    highConfidenceSection: buildConfidenceSection("HIGH CONFIDENCE PRODUCTS (≥90% - Ready for immediate use)", highConfidenceProducts),
    mediumConfidenceSection: buildConfidenceSection("MEDIUM CONFIDENCE PRODUCTS (70-89% - Requires review)", mediumConfidenceProducts),
    lowConfidenceSection: buildConfidenceSection("LOW CONFIDENCE PRODUCTS (<70% - Needs manual verification)", lowConfidenceProducts),
    processingSummariesSection: buildProcessingSummariesSection(allProcessingSummaries)
  };
  
  // Apply template substitution
  const emailBody = applyTemplate(template, templateData);
  
  const sender = firstItem.json.sender;
  const totalProducts = allProducts.length;
  const totalAttachments = groupItems.length;

  return {
    json: {
      to: sender,
      subject: `Materials Extraction Complete: ${totalProducts} products from ${totalAttachments} attachment(s)`,
      body: emailBody,
      attachments: [],
      document_id: firstItem.json.document_id,
      group_id: groupId,
      _lifecycle_log: allLogs
    }
  };
}

// ERROR EMAIL FORMATTING FUNCTION (Template-based)
function formatErrorEmail(groupItems, groupId) {
  const firstItem = groupItems[0];
  
  // Collect error information across all attachments in this email
  let allLogs = [];
  const errorDetails = [];
  
  groupItems.forEach(item => {
    if (item.json._lifecycle_log) {
      allLogs = allLogs.concat(item.json._lifecycle_log);
    }
    
    errorDetails.push({
      attachment_index: item.json.attachment_index,
      document_id: item.json.document_id,
      error_summary: item.json.error_summary,
      task_status: item.json.task_status
    });
  });

  // Load email template
  const template = loadTemplate('failure');
  
  // Prepare template data
  const templateData = {
    emailSubject: firstItem.json.subject,
    totalAttachments: groupItems.length,
    errorDetails: buildErrorDetailsSection(errorDetails)
  };
  
  // Apply template substitution
  const emailBody = applyTemplate(template, templateData);
  
  const sender = firstItem.json.sender;
  const totalAttachments = groupItems.length;

  return {
    json: {
      to: sender,
      subject: `Materials Extraction Failed: ${totalAttachments} attachment(s) could not be processed`,
      body: emailBody,
      attachments: [],
      document_id: firstItem.json.document_id,
      group_id: groupId,
      _lifecycle_log: allLogs
    }
  };
}

// TEMPLATE UTILITY FUNCTIONS

function loadTemplate(templateName) {
  const templatePath = `/home/node/email_templates/${templateName}.txt`;
  return fs.readFileSync(templatePath, 'utf8');
}

function applyTemplate(template, data) {
  let result = template;
  
  // Simple placeholder substitution
  Object.keys(data).forEach(key => {
    const placeholder = `{{${key}}}`;
    result = result.replace(new RegExp(placeholder, 'g'), data[key]);
  });
  
  return result;
}

function buildConfidenceSection(title, products) {
  if (products.length === 0) {
    return '';
  }
  
  let section = `${title}:\n`;
  section += `═══════════════════════════════════════════════════════════\n`;
  
  products.forEach((product, index) => {
    section += `\n${index + 1}. ${getProductName(product)}\n`;
    section += `   Brand: ${getProductBrand(product)}\n`;
    section += `   Summary: ${getProductSummary(product)}\n`;
    section += `   Confidence: ${Math.round(product.average_confidence * 100)}%\n`;
    section += `   Source: Attachment ${product.source_attachment + 1}\n`;
  });
  section += `\n`;
  
  return section;
}

function buildProcessingSummariesSection(summaries) {
  if (summaries.length === 0) {
    return '';
  }
  
  let section = `PROCESSING SUMMARIES:\n`;
  section += `═══════════════════════════════════════════════════════════\n`;
  
  summaries.forEach(summary => {
    section += `\nAttachment ${summary.attachment_index + 1}: ${summary.summary}\n`;
  });
  section += `\n`;
  
  return section;
}

function buildErrorDetailsSection(errorDetails) {
  let section = '';
  
  errorDetails.forEach((error, index) => {
    section += `\nAttachment ${error.attachment_index + 1}:\n`;
    section += `  Document ID: ${error.document_id}\n`;
    section += `  Status: ${error.task_status}\n`;
    section += `  Error: ${error.error_summary}\n`;
  });
  
  return section;
}

// HELPER FUNCTIONS
function getProductName(product) {
  if (product.field_extractions && product.field_extractions.name) {
    return product.field_extractions.name.value;
  }
  return "Unknown Product";
}

function getProductBrand(product) {
  if (product.field_extractions && product.field_extractions.brand) {
    return product.field_extractions.brand.value;
  }
  return "Unknown Brand";
}

function getProductSummary(product) {
  if (product.field_extractions && product.field_extractions.summary) {
    return product.field_extractions.summary.value;
  }
  return "No summary available";
}

module.exports = { processResults };