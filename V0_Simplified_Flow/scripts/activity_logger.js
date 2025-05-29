// Activity Logger - Log all document lifecycle stages to a file

const activityLogger = function(items) {
  const fs = require('fs');
  const path = require('path');

  try {
    const logPath = '/home/node/data/logs';
    const logFile = path.join(logPath, 'document_lifecycle.json');

    // Ensure log directory exists
    if (!fs.existsSync(logPath)) {
      fs.mkdirSync(logPath, { recursive: true });
    }

    // Get existing logs or create new array
    let logs = [];
    if (fs.existsSync(logFile)) {
      try {
        const data = fs.readFileSync(logFile, 'utf8');
        logs = JSON.parse(data);
      } catch (err) {
        console.error('Error reading logs file:', err);
      }
    }

    // Add new log entries
    if (items[0].json._lifecycle_log && Array.isArray(items[0].json._lifecycle_log)) {
      logs = logs.concat(items[0].json._lifecycle_log);
      
      // Write updated logs
      try {
        fs.writeFileSync(logFile, JSON.stringify(logs, null, 2));
      } catch (err) {
        console.error('Error writing logs file:', err);
      }
    }

    // Pass through the original items
    return items;
  } catch (error) {
    console.error('Error in Activity Logger:', error);
    // Pass through the original items even if logging fails
    return items;
  }
};

module.exports = { activityLogger };