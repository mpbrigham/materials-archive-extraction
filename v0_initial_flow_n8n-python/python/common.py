#!/usr/bin/env python3
"""
Common utilities for materials extraction pipeline
"""

import json
from datetime import datetime

def log_debug(execution_id, node_name, phase, data):
    """Log debug information to file"""
    log_entry = {
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "executionId": execution_id,
        "node": node_name,
        "phase": phase,
        "data": data
    }
    with open('/home/node/data/debug.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')
