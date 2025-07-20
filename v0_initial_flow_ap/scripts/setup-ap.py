#!/usr/bin/env python3
"""
ActivePieces API Setup Script
Automates the creation of connections and workflow import
"""

import os
import sys
import json
import requests
from typing import Dict, Any, Optional

class ActivePiecesAPI:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        self.project_id = None
    
    def get_or_create_project(self, project_name: str) -> str:
        """Get existing project by name or create a new one"""
        try:
            # Search for existing project by external ID
            response = requests.get(
                f"{self.base_url}/api/v1/projects",
                headers=self.headers,
                params={'externalId': project_name}
            )
            response.raise_for_status()
            projects = response.json()
            
            # Check if we have a 'data' wrapper
            if isinstance(projects, dict) and 'data' in projects:
                projects = projects['data']
            
            # Return existing project if found
            if projects and len(projects) > 0:
                print(f"Found existing project: {projects[0]['id']}")
                return projects[0]['id']
            
            # Create new project if not found
            print(f"Creating new project: {project_name}")
            create_response = requests.post(
                f"{self.base_url}/api/v1/projects",
                headers=self.headers,
                json={
                    'displayName': project_name,
                    'externalId': project_name,
                    'metadata': {}
                }
            )
            create_response.raise_for_status()
            new_project = create_response.json()
            
            print(f"✅ Created project: {new_project['id']}")
            return new_project['id']
            
        except Exception as e:
            print(f"❌ Error managing project: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            raise
    
    def connection_exists(self, name: str) -> bool:
        """Check if a connection with the given name exists"""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/app-connections",
                headers=self.headers,
                params={'name': name}
            )
            response.raise_for_status()
            connections = response.json()
            
            return any(conn.get('name') == name for conn in connections)
        except Exception:
            return False
    
    def create_connection(self, name: str, piece_name: str, connection_data: Dict[str, Any]) -> bool:
        """Create a new connection"""
        if self.connection_exists(name):
            print(f"⚠️  Connection '{name}' already exists, skipping...")
            return True
        
        payload = {
            'name': name,
            'pieceName': piece_name,
            'projectId': self.project_id,
            'type': 'CUSTOM_AUTH',
            'value': connection_data
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/app-connections",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            print(f"✅ Connection '{name}' created successfully")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"❌ Failed to create connection '{name}': {e}")
            if e.response:
                print(f"   Response: {e.response.text}")
            return False
    
    def import_workflow(self, workflow_path: str) -> Optional[str]:
        """Import a workflow from JSON file"""
        try:
            with open(workflow_path, 'r') as f:
                workflow = json.load(f)
            
            # Add project ID to workflow
            workflow['projectId'] = self.project_id
            
            response = requests.post(
                f"{self.base_url}/api/v1/flows",
                headers=self.headers,
                json=workflow
            )
            response.raise_for_status()
            
            flow_data = response.json()
            flow_id = flow_data.get('id')
            print(f"✅ Workflow imported successfully (ID: {flow_id})")
            return flow_id
            
        except Exception as e:
            print(f"❌ Failed to import workflow: {e}")
            return None
    
    def activate_workflow(self, flow_id: str) -> bool:
        """Activate a workflow"""
        payload = {
            'type': 'CHANGE_STATUS',
            'request': {
                'status': 'ENABLED'
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/flows/{flow_id}",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            print("✅ Workflow activated successfully")
            return True
        except Exception as e:
            print(f"⚠️  Failed to activate workflow: {e}")
            return False

def main():
    print("=== ActivePieces API Setup Script ===\n")
    
    # Get configuration from environment
    config = {
        'AP_URL': os.getenv('AP_URL', 'http://localhost:5679'),
        'AP_API_KEY': os.getenv('AP_API_KEY'),
        'IMAP_HOST': os.getenv('IMAP_HOST'),
        'IMAP_PORT': int(os.getenv('IMAP_PORT', '993')),
        'SMTP_HOST': os.getenv('SMTP_HOST'),
        'SMTP_PORT': int(os.getenv('SMTP_PORT', '465')),
        'EMAIL_USER': os.getenv('EMAIL_USER'),
        'EMAIL_PASS': os.getenv('EMAIL_PASS'),
        'LLM_API_KEY': os.getenv('LLM_API_KEY'),
    }
    
    # Validate required variables
    required = ['AP_API_KEY', 'IMAP_HOST', 'SMTP_HOST', 'EMAIL_USER', 'EMAIL_PASS', 'LLM_API_KEY']
    missing = [var for var in required if not config.get(var)]
    
    if missing:
        print("❌ Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set these variables and try again.")
        sys.exit(1)
    
    # Initialize API client
    api = ActivePiecesAPI(config['AP_URL'], config['AP_API_KEY'])
    
    # Get or create project with consistent name
    print("Managing project...")
    project_name = os.getenv('AP_PROJECT_ID', 'materials-archive-extraction')
    
    try:
        project_id = api.get_or_create_project(project_name)
        api.project_id = project_id
        print(f"Using project ID: {project_id} (name: {project_name})\n")
    except Exception as e:
        print(f"❌ Failed to manage project: {e}")
        sys.exit(1)
    
    # Create IMAP connection
    print("Creating IMAP connection...")
    imap_success = api.create_connection(
        name='imap_connection',
        piece_name='@activepieces/piece-imap',
        connection_data={
            'host': config['IMAP_HOST'],
            'port': config['IMAP_PORT'],
            'username': config['EMAIL_USER'],
            'password': config['EMAIL_PASS'],
            'tls': True
        }
    )
    
    # Create SMTP connection
    print("\nCreating SMTP connection...")
    smtp_success = api.create_connection(
        name='smtp_connection',
        piece_name='@activepieces/piece-smtp',
        connection_data={
            'host': config['SMTP_HOST'],
            'port': config['SMTP_PORT'],
            'username': config['EMAIL_USER'],
            'password': config['EMAIL_PASS'],
            'from_email': config['EMAIL_USER']
        }
    )
    
    # Create Gemini AI connection
    print("\nCreating Gemini AI connection...")
    gemini_success = api.create_connection(
        name='gemini_connection',
        piece_name='@activepieces/piece-google-gemini',
        connection_data={
            'apiKey': config['LLM_API_KEY']
        }
    )
    
    # Import workflow
    print("\nImporting workflow...")
    workflow_path = '/data/ap.json'
    
    if not os.path.exists(workflow_path):
        print(f"❌ Workflow file not found: {workflow_path}")
        sys.exit(1)
    
    flow_id = api.import_workflow(workflow_path)
    
    if flow_id:
        # Activate workflow
        print("\nActivating workflow...")
        api.activate_workflow(flow_id)
    
    # Summary
    print("\n=== Setup Complete ===\n")
    print("Next steps:")
    print(f"1. Access ActivePieces at {config['AP_URL']}")
    print("2. Verify connections under 'Connections' tab")
    print("3. Check workflow under 'Flows' tab")
    print("4. Send a test email with PDF attachments")
    
    if not all([imap_success, smtp_success, gemini_success, flow_id]):
        print("\n⚠️  Some steps failed. Please check the errors above.")
        sys.exit(1)

if __name__ == '__main__':
    main()
