// Document Validator Function for Materials Library Extraction
// Used by the Document Validator node in n8n workflow

const documentValidator = function(items) {
  // Log node start with input
  const fs = require('fs');
  fs.appendFileSync('/home/node/data/debug.log', 
    `${new Date().toISOString()} - document_validator - START\n` +
    `INPUT: ${JSON.stringify(items, null, 2)}\n`
  );
  
  try {
    if (!items || items.length === 0) {
      throw new Error('No items received by Document Validator - email processing pipeline is broken');
    }

    const item = items[0];

    // Generate deterministic timestamp and group ID based on email metadata
    const sender = item.json.from;
    const subject = item.json.subject;
    const timestamp = Date.now();
    const isoTimestamp = new Date().toISOString();
    const group_id = `email-${timestamp}`;
    
    // Validate essential email data
    if (!sender) {
      throw new Error('Email sender (from field) is missing - cannot process email');
    }
    
    // Find all PDF attachments
    const pdfAttachments = [];
    
    // Check if binary attachments exist
    if (!item.binary || Object.keys(item.binary).length === 0) {
      throw new Error('No binary attachments found in email - email may be malformed');
    }
    
    // Scan for all PDF attachments
    Object.keys(item.binary).forEach((key, index) => {
      if (item.binary[key].mimeType === 'application/pdf') {
        pdfAttachments.push({
          key: key,
          index: index,
          document_id: `doc-${timestamp}-${index}`
        });
      }
    });
    
    // If no PDF attachments found
    if (pdfAttachments.length === 0) {
      throw new Error('No PDF attachments found in email - only PDF files are supported for materials extraction');
    }
    
    // Create email level lifecycle log entry
    const emailLogEntry = {
      group_id: group_id,
      document_count: pdfAttachments.length,
      from_state: "RECEIVED",
      to_state: "VALIDATED",
      timestamp: isoTimestamp,
      agent: "document_validator",
      notes: `Email with ${pdfAttachments.length} PDF attachment(s) validated`
    };
    
    // Return array of items, one per attachment
    const validatedAttachments = pdfAttachments.map(attachment => {
      // Create log entry for this specific attachment
      const attachmentLogEntry = {
        document_id: attachment.document_id,
        group_id: group_id,
        attachment_index: attachment.index,
        from_state: "VALIDATED",
        to_state: "INTERPRETED",
        timestamp: isoTimestamp,
        agent: "document_validator",
        notes: `Attachment ${attachment.index + 1}/${pdfAttachments.length} interpreted and routed for extraction`
      };
      
      return {
        json: {
          sender,
          timestamp: isoTimestamp,
          subject,
          document_id: attachment.document_id,
          group_id: group_id,
          attachment_key: attachment.key,
          attachment_index: attachment.index,
          total_attachments: pdfAttachments.length,
          task: "extract_metadata",
          document_type: "supplier_material",
          _lifecycle_log: [emailLogEntry, attachmentLogEntry]
        },
        binary: {
          [attachment.key]: item.binary[attachment.key]
        }
      };
    });
    
    // Return the already mapped attachments
    const result = validatedAttachments;
    
    // Log node completion with output
    fs.appendFileSync('/home/node/data/debug.log', 
      `${new Date().toISOString()} - document_validator - SUCCESS\n` +
      `OUTPUT: ${JSON.stringify(result, null, 2)}\n`
    );
    
    return result;
    
  } catch (error) {
    // Log error before re-throwing
    const fs = require('fs');
    fs.appendFileSync('/home/node/data/debug.log', 
      `${new Date().toISOString()} - document_validator - ERROR: ${error.message}\n`
    );
    // Let the error bubble up to Global Error Handler instead of creating fake document IDs
    throw error;
  }
};

module.exports = { documentValidator };
