#!/bin/bash
# ActivePieces API Setup Script
# This script automates the creation of connections and workflow import

# Configuration
AP_URL="${AP_URL:-http://localhost:5679}"
AP_API_KEY="${AP_API_KEY}"
AP_PROJECT_ID="${AP_PROJECT_ID}"

# Email configuration from environment
IMAP_HOST="${IMAP_HOST}"
IMAP_PORT="${IMAP_PORT:-993}"
SMTP_HOST="${SMTP_HOST}"
SMTP_PORT="${SMTP_PORT:-465}"
EMAIL_USER="${EMAIL_USER}"
EMAIL_PASS="${EMAIL_PASS}"
LLM_API_KEY="${LLM_API_KEY}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a variable is set
check_var() {
    local var_name=$1
    local var_value=${!var_name}
    if [ -z "$var_value" ]; then
        echo -e "${RED}Error: $var_name is not set${NC}"
        return 1
    fi
    return 0
}

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -z "$data" ]; then
        curl -s -X "$method" \
            -H "Authorization: Bearer $AP_API_KEY" \
            -H "Content-Type: application/json" \
            "$AP_URL/api/v1$endpoint"
    else
        curl -s -X "$method" \
            -H "Authorization: Bearer $AP_API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$AP_URL/api/v1$endpoint"
    fi
}

# Function to check if connection exists
connection_exists() {
    local conn_name=$1
    local response=$(api_call GET "/app-connections?name=$conn_name")
    if echo "$response" | grep -q "\"name\":\"$conn_name\""; then
        return 0
    else
        return 1
    fi
}

echo "=== ActivePieces API Setup Script ==="
echo

# Check required environment variables
echo "Checking environment variables..."
check_var "AP_API_KEY" || exit 1
check_var "IMAP_HOST" || exit 1
check_var "SMTP_HOST" || exit 1
check_var "EMAIL_USER" || exit 1
check_var "EMAIL_PASS" || exit 1
check_var "LLM_API_KEY" || exit 1

# Get project ID if not set
if [ -z "$AP_PROJECT_ID" ]; then
    echo "Fetching project ID..."
    projects_response=$(api_call GET "/projects")
    AP_PROJECT_ID=$(echo "$projects_response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
    
    if [ -z "$AP_PROJECT_ID" ]; then
        echo -e "${RED}Error: Could not fetch project ID${NC}"
        exit 1
    fi
    echo -e "${GREEN}Using project ID: $AP_PROJECT_ID${NC}"
fi

# Create IMAP Connection
echo
echo "Creating IMAP connection..."
if connection_exists "imap_connection"; then
    echo -e "${YELLOW}IMAP connection already exists, skipping...${NC}"
else
    imap_data=$(cat <<EOF
{
    "name": "imap_connection",
    "pieceName": "@activepieces/piece-imap",
    "projectId": "$AP_PROJECT_ID",
    "type": "OAUTH2",
    "value": {
        "host": "$IMAP_HOST",
        "port": $IMAP_PORT,
        "username": "$EMAIL_USER",
        "password": "$EMAIL_PASS",
        "tls": true
    }
}
EOF
    )
    
    response=$(api_call POST "/app-connections" "$imap_data")
    if echo "$response" | grep -q '"id"'; then
        echo -e "${GREEN}IMAP connection created successfully${NC}"
    else
        echo -e "${RED}Failed to create IMAP connection${NC}"
        echo "Response: $response"
    fi
fi

# Create SMTP Connection
echo
echo "Creating SMTP connection..."
if connection_exists "smtp_connection"; then
    echo -e "${YELLOW}SMTP connection already exists, skipping...${NC}"
else
    smtp_data=$(cat <<EOF
{
    "name": "smtp_connection",
    "pieceName": "@activepieces/piece-smtp",
    "projectId": "$AP_PROJECT_ID",
    "type": "OAUTH2",
    "value": {
        "host": "$SMTP_HOST",
        "port": $SMTP_PORT,
        "username": "$EMAIL_USER",
        "password": "$EMAIL_PASS",
        "from_email": "$EMAIL_USER"
    }
}
EOF
    )
    
    response=$(api_call POST "/app-connections" "$smtp_data")
    if echo "$response" | grep -q '"id"'; then
        echo -e "${GREEN}SMTP connection created successfully${NC}"
    else
        echo -e "${RED}Failed to create SMTP connection${NC}"
        echo "Response: $response"
    fi
fi

# Create Gemini AI Connection
echo
echo "Creating Gemini AI connection..."
if connection_exists "gemini_connection"; then
    echo -e "${YELLOW}Gemini AI connection already exists, skipping...${NC}"
else
    gemini_data=$(cat <<EOF
{
    "name": "gemini_connection",
    "pieceName": "@activepieces/piece-google-gemini",
    "projectId": "$AP_PROJECT_ID",
    "type": "CUSTOM_AUTH",
    "value": {
        "apiKey": "$LLM_API_KEY"
    }
}
EOF
    )
    
    response=$(api_call POST "/app-connections" "$gemini_data")
    if echo "$response" | grep -q '"id"'; then
        echo -e "${GREEN}Gemini AI connection created successfully${NC}"
    else
        echo -e "${RED}Failed to create Gemini AI connection${NC}"
        echo "Response: $response"
    fi
fi

# Import workflow
echo
echo "Importing workflow..."
if [ -f "/data/ap.json" ]; then
    # First, we need to add the projectId to the workflow
    workflow_json=$(cat /data/ap.json | jq --arg pid "$AP_PROJECT_ID" '. + {projectId: $pid}')
    
    response=$(api_call POST "/flows" "$workflow_json")
    if echo "$response" | grep -q '"id"'; then
        flow_id=$(echo "$response" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
        echo -e "${GREEN}Workflow imported successfully${NC}"
        echo "Flow ID: $flow_id"
        
        # Activate the flow
        echo "Activating workflow..."
        activate_data='{"type":"CHANGE_STATUS","request":{"status":"ENABLED"}}'
        response=$(api_call POST "/flows/$flow_id" "$activate_data")
        if echo "$response" | grep -q '"status":"ENABLED"'; then
            echo -e "${GREEN}Workflow activated successfully${NC}"
        else
            echo -e "${YELLOW}Warning: Could not activate workflow${NC}"
        fi
    else
        echo -e "${RED}Failed to import workflow${NC}"
        echo "Response: $response"
    fi
else
    echo -e "${RED}Error: ap.json not found${NC}"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "1. Access ActivePieces at $AP_URL"
echo "2. Verify connections under 'Connections' tab"
echo "3. Check workflow under 'Flows' tab"
echo "4. Send a test email with PDF attachments"
