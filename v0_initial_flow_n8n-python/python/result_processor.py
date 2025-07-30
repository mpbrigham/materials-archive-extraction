#!/usr/bin/env python3
"""
Result Processor - Format extraction results and prepare email response
"""

import json
import sys
import os
from datetime import datetime
import html

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

def parse_n8n_input(input_data):
    """Parse input that may be wrapped by n8n's Execute Command node"""
    
    # If input is a string, parse it
    if isinstance(input_data, str):
        input_data = json.loads(input_data)
    
    # If it's a single item with n8n wrapper structure
    if (len(input_data) == 1 and 
        isinstance(input_data[0], dict) and 
        'json' in input_data[0] and 
        'stdout' in input_data[0].get('json', {})):
        # Extract the actual output from stdout
        stdout_data = input_data[0]['json']['stdout']
        return json.loads(stdout_data)
    
    return input_data
def escape_html(text):
    """Escape HTML special characters"""
    
    if not text:
        return ''
    return html.escape(str(text))

def format_value(field):
    """Format field value for display"""
    
    if isinstance(field.get('value'), list):
        return ', '.join(field['value'])
    return str(field.get('value', ''))

def create_product_table(product, file_name):
    """Create HTML table for a product"""
    
    supplier = format_value(product.get('supplier', {}))
    product_name = format_value(product.get('product_name', {}))
    sku = format_value(product.get('sku_number', {}))
    
    html_parts = [
        '<table class="header-table">',
        '<tr>',
        '<th>Supplier</th>',
        '<th>Product Name</th>',
        '<th>SKU</th>',
        '<th>Source File</th>',
        '</tr>',
        '<tr>',
        f'<td>{escape_html(supplier)}</td>',
        f'<td>{escape_html(product_name)}</td>',
        f'<td>{escape_html(sku)}</td>',
        f'<td>{escape_html(file_name)}</td>',
        '</tr>',
        '</table>',
        '<table class="data-table">',
        '<tr>',
        '<th>Field</th>',
        '<th>Value</th>',
        '</tr>'
    ]
    
    # Add other fields
    skip_fields = ['supplier', 'product_name', 'sku_number', 'source_file_name']
    
    for field_key, field_data in product.items():
        if field_key in skip_fields:
            continue
            
        if isinstance(field_data, dict) and field_data.get('value') is not None:
            value = format_value(field_data)
            if value and value.strip():
                field_label = field_key.replace('_', ' ').title()
                html_parts.extend([
                    '<tr>',
                    f'<td>{field_label}</td>',
                    f'<td>{escape_html(value)}</td>',
                    '</tr>'
                ])
    
    html_parts.append('</table>')
    return '\n'.join(html_parts)

def create_request_details_table(email_context):
    """Create HTML table for request details"""
    
    return f'''
    <table>
      <tr>
        <th>From</th>
        <td>{escape_html(email_context.get('from'))}</td>
      </tr>
      <tr>
        <th>Subject</th>
        <td>{escape_html(email_context.get('subject'))}</td>
      </tr>
      <tr>
        <th>Date</th>
        <td>{escape_html(email_context.get('date'))}</td>
      </tr>
      <tr>
        <th>Message ID</th>
        <td>{escape_html(email_context.get('messageId'))}</td>
      </tr>
    </table>
    '''

def create_failed_files_section(files):
    """Create HTML section for failed files"""
    
    failed_files = [f for f in files if f.get('status') == 'failed']
    
    if not failed_files:
        return ''
    
    html_parts = [
        '<div class="failed-files">',
        '<h3>Processing Issues</h3>',
        '<p>The following files could not be processed:</p>',
        '<ul>'
    ]
    
    for file_info in failed_files:
        html_parts.append(
            f'<li><strong>{escape_html(file_info["fileName"])}:</strong> {escape_html(file_info.get("error", "Unknown error"))}</li>'
        )
    
    html_parts.extend(['</ul>', '</div>'])
    return '\n'.join(html_parts)
def main():
    """Main processing logic"""
    
    try:
        # Read input from command-line argument
        if len(sys.argv) < 2:
            raise ValueError('No input data provided. Expected JSON data as command-line argument.')
        
        input_data = parse_n8n_input(sys.argv[1])
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Get model name for display
        model_name = os.environ.get('LLM_MODEL', 'Unknown')
        model_info = f' using model <strong>{escape_html(model_name)}</strong>'
        
        # Extract state object
        if isinstance(input_data, list) and len(input_data) > 0:
            state = input_data[0].get('json', {})
        else:
            raise ValueError('Invalid input format. Expected state object.')
        
        # Log input
        log_debug(execution_id, "Result Processor", "input", state)
        
        # Extract components from state
        email_context = state.get('email_context', {})
        files = state.get('files', [])
        global_errors = state.get('errors', [])
        
        # Validate email context
        if not email_context.get('from'):
            raise ValueError('Email context missing required "from" field')
        
        # Process results
        all_products = []
        summaries = []
        exceptions = []
        
        # Count files by status
        processed_files = [f for f in files if f.get('status') == 'processed']
        failed_files = [f for f in files if f.get('status') == 'failed']
        pdf_files = [f for f in files if 'pdf' in f.get('mimeType', '').lower() or f.get('fileName', '').lower().endswith('.pdf')]
        
        total_attachments = len(files)
        total_pdfs = len(pdf_files)
        
        # Extract products from processed files
        for file_info in processed_files:
            extracted_data = file_info.get('extractedData', {})
            products = extracted_data.get('products', [])
            summary = extracted_data.get('processing_summary')
            processing_exceptions = extracted_data.get('processing_exceptions')
            
            if summary:
                summaries.append(f"{file_info['fileName']}: {summary}")
            
            if processing_exceptions:
                if isinstance(processing_exceptions, list):
                    exceptions.extend([f"{file_info['fileName']}: {ex}" for ex in processing_exceptions])
                elif isinstance(processing_exceptions, str):
                    exceptions.append(f"{file_info['fileName']}: {processing_exceptions}")
            
            for product in products:
                all_products.append({
                    'product': product,
                    'fileName': file_info['fileName']
                })

        # Generate email response
        status = 'success' if all_products else 'failure'
        request_details = create_request_details_table(email_context)
        
        if status == 'success':
            # Read success template
            with open('/data/email_templates/success.html', 'r') as f:
                template = f.read()
            
            # Create product tables
            product_tables = []
            for idx, product_info in enumerate(all_products):
                if idx > 0:
                    product_tables.append('<br>')
                product_tables.append(create_product_table(product_info['product'], product_info['fileName']))
            
            # Create extraction summary
            if summaries:
                extraction_summary = '<ul>' + ''.join([f'<li>{escape_html(s)}</li>' for s in summaries]) + '</ul>'
            else:
                extraction_summary = f'<ul><li>Processed {len(all_products)} product(s) from {total_pdfs} PDF file(s).</li></ul>'
            
            # Add model info to extraction summary
            extraction_summary += f'<div>{model_info}</div>'
            
            # Create exceptions section
            exceptions_section = ''
            if exceptions:
                exceptions_section = '<div class="exceptions"><h3>Processing Exceptions</h3><ul>'
                exceptions_section += ''.join([f'<li>{escape_html(ex)}</li>' for ex in exceptions])
                exceptions_section += '</ul></div>'
            
            # Create failed files section
            failed_files_section = create_failed_files_section(files)
            
            # Replace placeholders
            email_body = template.replace('{{productTables}}', ''.join(product_tables))
            email_body = email_body.replace('{{extractionSummary}}', extraction_summary)
            email_body = email_body.replace('{{exceptionsSection}}', exceptions_section)
            email_body = email_body.replace('{{failedFilesSection}}', failed_files_section)
            email_body = email_body.replace('{{requestDetails}}', request_details)
            email_body = email_body.replace('{{totalProducts}}', str(len(all_products)))
            email_body = email_body.replace('{{totalAttachments}}', str(total_attachments))
            
        else:
            # Read failure template
            with open('/data/email_templates/failure.html', 'r') as f:
                template = f.read()
            
            # Create error details
            error_messages = []
            
            # Add global errors
            for error in global_errors:
                error_messages.append(error.get('error', 'Unknown error'))
            
            # Add file-specific errors
            for file_info in failed_files:
                error_messages.append(f'<strong>{file_info["fileName"]}:</strong> {file_info.get("error", "Unknown error")}')
            
            if error_messages:
                error_details = '<br>'.join(error_messages)
            else:
                error_details = 'No specific error details available.'
            
            # Replace placeholders
            email_body = template.replace('{{errorDetails}}', error_details)
            email_body = email_body.replace('{{requestDetails}}', request_details)
            email_body = email_body.replace('{{totalAttachments}}', str(total_attachments))
        
        # Create result - only include fields needed by Send Notification node
        result = {
            'json': {
                'to': email_context['from'],
                'subject': f"Re: {email_context['subject']} - Materials Extraction {'Complete' if status == 'success' else 'Failed'}",
                'body': email_body
            }
        }
        
        # Log output
        log_debug(execution_id, "Result Processor", "output", [result])
        
        # Return result to n8n
        print(json.dumps([result]))
        
    except Exception as e:
        error_result = [{
            'json': {
                'error': str(e)
            }
        }]
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == '__main__':
    main()
