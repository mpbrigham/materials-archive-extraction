// Error Formatter - Create proper lifecycle log structure for Activity Logger

const errorFormatter = function(items) {
  const item = items[0];
  const errorMessage = item.json.error;
  const documentId = item.json.document_id;
  const groupId = item.json.group_id;
  const timestamp = new Date().toISOString();

  // Create proper lifecycle log entry for errors
  const errorLifecycleEntry = {
    document_id: documentId,
    group_id: groupId,
    from_state: "GLOBAL_ERROR",
    to_state: "FAILED",
    timestamp: timestamp,
    agent: "global_error_handler",
    notes: `Global error captured: ${errorMessage}`
  };

  // Return structured error data compatible with Activity Logger
  return [{
    json: {
      error_message: errorMessage,
      document_id: documentId,
      group_id: groupId,
      timestamp: timestamp,
      task_status: "failed",
      error_summary: `Global workflow error: ${errorMessage}`,
      verification_passed: false,
      _lifecycle_log: [errorLifecycleEntry]
    }
  }];
};

module.exports = { errorFormatter };