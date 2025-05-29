// Success Notifier Function for Materials Library Extraction
// Used by the Success Notifier node in n8n workflow

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

// Format Success Email Function
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
  
  // Build the product list for display
  let productList = '';
  if (productCount === 1) {
    const product = item.json.products[0].extracted_values;
    productList = `Material: ${product.name || 'Unnamed Material'}\n`;
    productList += `Brand: ${product.brand || 'Unspecified Brand'}\n`;
  } else {
    productList = 'Products:\n';
    const maxToList = Math.min(productCount, 5);
    for (let i = 0; i < maxToList; i++) {
      const product = item.json.products[i].extracted_values;
      productList += `${i+1}. ${product.name || 'Unnamed Material'} (${product.brand || 'Unspecified Brand'})\n`;
    }
    
    if (productCount > maxToList) {
      productList += `... and ${productCount - maxToList} more\n`;
    }
  }
  
  // Build the notes section
  let notes = '';
  const fallbackNote = item.json.products.some(p => p.fallback_applied) ? 
    'Note: Simplified metadata extracted for some products due to confidence thresholds.' : 
    '';
  
  if (fallbackNote) {
    notes += `\n${fallbackNote}\n`;
  }
  
  if (partialSuccess) {
    notes += `\nNote: Some products could not be fully verified and were excluded from the results.\n`;
  }
  
  // Build the product description
  let productDescription = '';
  if (productCount === 1) {
    productDescription = 'The extracted metadata is included below in JSON format.';
  } else {
    productDescription = `${productCount} products were extracted and their metadata is included below in JSON format.`;
  }
  
  // Load and populate the template
  const templateVars = {
    sender: sender,
    productCountSuffix: productCount > 1 ? ` (${productCount} products)` : '',
    productDescription: productDescription,
    productList: productList,
    notes: notes
  };
  
  const emailContent = loadEmailTemplate('success', templateVars);
  
  // Extract subject and body from template
  const lines = emailContent.split('\n');
  const subject = lines[0].replace('Subject: ', '');
  const body = lines.slice(2).join('\n');
  
  return {
    json: {
      to: sender,
      subject: subject,
      body: body,
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

module.exports = { formatSuccessEmail };
