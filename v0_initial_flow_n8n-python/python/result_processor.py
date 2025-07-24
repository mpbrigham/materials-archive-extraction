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
        "timestamp": datetime.utcnow().isoformat(),
        "executionId": execution_id,
        "node": node_name,
        "phase": phase,
        "data": data
    }
    with open('/home/node/data/debug.log', 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

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

def create_failed_files_section(errors):
    """Create HTML section for failed files"""
    if not errors:
        return ''
    
    html_parts = [
        '<div class="failed-files">',
        '<h3>Processing Issues</h3>',
        '<p>The following files could not be processed:</p>',
        '<ul>'
    ]
    
    for error in errors:
        html_parts.append(
            f'<li><strong>{escape_html(error["fileName"])}:</strong> {escape_html(error["error"])}</li>'
        )
    
    html_parts.extend(['</ul>', '</div>'])
    return '\n'.join(html_parts)

def main():
    """Main processing logic"""
    try:
        # Read input from n8n
        input_data = json.loads(sys.stdin.read())
        execution_id = os.environ.get('EXECUTION_ID', 'unknown')
        
        # Get model name for display
        model_name = os.environ.get('LLM_MODEL', 'Unknown')
        model_info = f' using model <strong>{escape_html(model_name)}</strong>'
        
        # Log input
        log_debug(execution_id, "Result Processor", "input", input_data)
        
        # Find email context
        email_context_item = None
        pdf_items = []
        
        for item in input_data:
            if item.get('json', {}).get('email') and not item.get('json', {}).get('fileName'):
                email_context_item = item
            elif item.get('json', {}).get('fileName') or item.get('json', {}).get('error'):
                pdf_items.append(item)
        
        if not email_context_item:
            raise ValueError('Email context item not found in input')
        
        email_context = email_context_item['json']['email']
        
        # Process results
        all_products = []
        errors = []
        summaries = []
        exceptions = []
        
        valid_pdfs = [i for i in pdf_items if i.get('json', {}).get('fileName') != 'no-pdfs-found']
        total_attachments = len(valid_pdfs)
        
        for item in pdf_items:
            if not item.get('json', {}).get('valid'):
                errors.append({
                    'fileName': item['json'].get('fileName'),
                    'error': item['json'].get('error'),
                    'errorType': item['json'].get('errorType')
                })
                continue
            
            extracted_data = item['json'].get('extractedData', {})
            products = extracted_data.get('products', [])
            summary = extracted_data.get('processing_summary')
            processing_exceptions = extracted_data.get('processing_exceptions')
            
            if summary:
                summaries.append(f"{item['json']['fileName']}: {summary}")
            
            if processing_exceptions:
                if isinstance(processing_exceptions, list):
                    exceptions.extend([f"{item['json']['fileName']}: {ex}" for ex in processing_exceptions])
                elif isinstance(processing_exceptions, str):
                    exceptions.append(f"{item['json']['fileName']}: {processing_exceptions}")
            
            for product in products:
                all_products.append({
                    'product': product,
                    'fileName': item['json']['fileName']
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
                extraction_summary = f'<ul><li>Processed {len(all_products)} product(s) from {total_attachments} attachment(s).</li></ul>'
            
            # Add model info to extraction summary
            extraction_summary += f'<div>{model_info}</div>'
            
            # Create exceptions section
            exceptions_section = ''
            if exceptions:
                exceptions_section = '<div class="exceptions"><h3>Processing Exceptions</h3><ul>'
                exceptions_section += ''.join([f'<li>{escape_html(ex)}</li>' for ex in exceptions])
                exceptions_section += '</ul></div>'
            
            # Create failed files section
            failed_files_section = create_failed_files_section(errors)
            
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
            if errors:
                error_details = '<br>'.join([f'<strong>{e["fileName"]}:</strong> {e["error"]}' for e in errors])
            else:
                error_details = 'No specific error details available.'
            
            # Replace placeholders
            email_body = template.replace('{{errorDetails}}', error_details)
            email_body = email_body.replace('{{requestDetails}}', request_details)
            email_body = email_body.replace('{{totalAttachments}}', str(total_attachments))
        
        # Create result
        result = {
            'json': {
                'to': email_context['from'],
                'subject': f"Re: {email_context['subject']} - Materials Extraction {'Complete' if status == 'success' else 'Failed'}",
                'body': email_body,
                'messageId': email_context['messageId'],
                'status': status,
                'processingTimestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Log output
        log_debug(execution_id, "Result Processor", "output", [result])
        
        # Return result to n8n
        print(json.dumps([result]))
        
    except Exception as e:
        error_result = [{
            'json': {
                'error': str(e),
                'errorType': 'system'
            }
        }]
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == '__main__':
    main()
