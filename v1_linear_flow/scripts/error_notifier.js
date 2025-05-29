// Error Notifier Function for Materials Library Extraction
// Used by the Error Notifier node in n8n workflow

// Template loader function for email templates
const loadEmailTemplate = function(templateName, variables) {
  const fs = require('fs');
  const templatePath = `/home/node/email_templates/${templateName}.txt`;
  
  try {
    let template = fs.readFileSync(templatePath, 'utf8');
    
    // Replace placeholders with actual values
    for (const [key, value] of Object.entries(variables)) {
      const placeholder = new RegExp(`{{${key}}}`, 'g');
      template = template.replace(placeholder, value || '');
    }
    
    return template;
  } catch (error) {
    console.error(`Error loading email template ${templateName}:`, error);
    // Fallback to hardcoded template if file not found
    return `Subject: Email Template Error\n\nError loading email template: ${error.message}`;
  }
};

// Format Error Email Function
try {
  if (!items || items.length === 0) {
    throw new Error("No items received by Error Email Formatter");
  }
  
  const item = items[0];
  
  // Extract original request data
  const originalRequest = item.json.original_request || {};
  const sender = originalRequest.sender || "materials-team@example.com";
  
  // Get error reason - this could come from different paths
  const errorReason = item.json.error_summary || item.json.reason || "Unknown error occurred";
  
  // Check for failed products from different stages
  const failedProducts = item.json.failed_products || [];
  const failedCount = Array.isArray(failedProducts) ? failedProducts.length : 0;
  
  // Check for partial success scenarios
  const partialSuccess = item.json.partial_success || false;
  const products = item.json.products || [];
  const successCount = Array.isArray(products) ? products.length : 0;
  
  // Get language
  const language = item.json.language_detected || "undetected";
  
  // Build error details
  let errorDetails = '';
  
  // If this is a partial success, mention that some products succeeded
  if (partialSuccess && successCount > 0) {
    errorDetails += `Partial Success: ${successCount} product(s) were successfully processed.\n\n`;
  }
  
  // Add failed product details
  if (failedCount > 0) {
    errorDetails += `${failedCount} product(s) failed processing:\n`;
    
    // List reasons for first few failures
    const maxToList = Math.min(failedCount, 3);
    for (let i = 0; i < maxToList; i++) {
      const failedProduct = failedProducts[i];
      
      // Extract product name from various possible locations
      let productName = "Unknown product";
      if (failedProduct.extracted_values?.name) {
        productName = failedProduct.extracted_values.name;
      } else if (failedProduct.data?.field_extractions?.name?.value) {
        productName = failedProduct.data.field_extractions.name.value;
      } else if (failedProduct.data?.name?.value) {
        productName = failedProduct.data.name.value;
      }
      
      const productError = failedProduct.error || failedProduct.reason || "Validation failed";
      const productConfidence = failedProduct.confidence ? ` (confidence: ${failedProduct.confidence.toFixed(2)})` : '';
      
      errorDetails += `• ${productName}: ${productError}${productConfidence}\n`;
    }
    
    if (failedCount > maxToList) {
      errorDetails += `... and ${failedCount - maxToList} more\n`;
    }
    
    errorDetails += '\n';
  }
  
  // Add general error reason if no specific product failures
  if (failedCount === 0 && !partialSuccess) {
    errorDetails += `Error: ${errorReason}\n`;
  }
  
  // Load and populate the template
  const templateVars = {
    sender: sender,
    errorReason: errorReason,
    failedProductDetails: errorDetails,
    language: language
  };
  
  const emailContent = loadEmailTemplate('failure', templateVars);
  
  // Extract subject and body from template
  const lines = emailContent.split('\n');
  const subject = lines[0].replace('Subject: ', '');
  const body = lines.slice(2).join('\n');
  
  return [
    {
      json: {
        to: sender,
        subject: subject,
        body: body,
        document_id: item.json.document_id,
        _lifecycle_log: item.json._lifecycle_log || []
      }
    }
  ];
} catch (error) {
  // Error handling
  return [
    {
      json: {
        to: "materials-team@example.com",
        subject: "Error Formatting Error Email",
        body: `There was an error creating the error email: ${error.message}`,
        document_id: items[0]?.json?.document_id || "unknown",
        _lifecycle_log: items[0]?.json?._lifecycle_log || []
      }
    }
  ];
}