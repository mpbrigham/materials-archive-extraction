"""
Result Processor - Format extraction results and prepare email response
"""

import os
import html
from common import dict_to_html_table

service_name = "Result Processor"

def format_email_response(state):
    """Format state into email response data"""
    email_context = state['emailContext']
    attachments = state['attachments']
    products = collect_products(attachments)
    template_name = 'success' if products else 'failure'

    return {
        'from': os.environ['EMAIL_USER'],
        'to': email_context['from'],
        'subject': format_subject(email_context['subject'], bool(products)),
        'body': render_template(template_name, state, products)
    }

def collect_products(attachments):
    """Extract all products from processed attachments"""
    products = []
    for attachment in attachments:
        if attachment['status'] == f"LLM Extraction pass":
            extracted_data = attachment['extractedData']
            for product in extracted_data['products']:
                products.append({'data': product, 'fileName': attachment['fileName']})
    return products
    
def format_subject(original_subject, success):
    """Format email subject line"""
    status = "Complete" if success else "Failed"
    return f"Re: {original_subject} - Materials Extraction {status}"

def render_template(template_name, state, products):
    """Load template and substitute data"""
    template_path = f'/app/email_templates/{template_name}.html'
    with open(template_path, 'r') as f:
        template = f.read()
    
    if template_name == 'success':
        return render_success_template(template, state, products)
    else:
        return render_failure_template(template, state)

def render_success_template(template, state, products):
    """Render success template with products"""
    product_html = build_products_html(products)
    request_details = build_request_details(state['emailContext'])
    model_name = os.environ['LLM_MODEL']
    
    summaries = []
    exceptions = []
    for attachment in state['attachments']:
        if attachment['status'] == f"LLM Extraction pass":
            extracted_data = attachment['extractedData']
            if 'processing_summary' in extracted_data:
                summaries.append(f"{attachment['fileName']}: {extracted_data['processing_summary']}")
            if 'processing_exceptions' in extracted_data:
                for exception in extracted_data['processing_exceptions']:
                    exceptions.append(f"{attachment['fileName']}: {exception}")
    
    if summaries:
        extraction_summary = '<ul>' + ''.join(f'<li>{html.escape(s)}</li>' for s in summaries) + '</ul>'
    else:
        extraction_summary = f'<ul><li>Processed {len(products)} product(s) from attachments.</li></ul>'
    extraction_summary += f'<div> using model <strong>{html.escape(model_name)}</strong></div>'
    
    exceptions_section = ''
    if exceptions:
        exceptions_section = '<div class="exceptions"><h3>Processing Exceptions</h3><ul>'
        exceptions_section += ''.join(f'<li>{html.escape(ex)}</li>' for ex in exceptions)
        exceptions_section += '</ul></div>'
    
    failed_attachments = [a for a in state['attachments'] if 'failed' in a['status']]
    failed_section = ''
    if failed_attachments:
        failed_section = '<div class="failed-attachments"><h3>Processing Issues</h3><ul>'
        for attachment in failed_attachments:
            error = state['errors'][-1] if state['errors'] else 'Processing failed'
            failed_section += f'<li><strong>{html.escape(attachment["fileName"])}:</strong> {html.escape(error)}</li>'
        failed_section += '</ul></div>'
    
    body = template.replace('{{productTables}}', product_html)
    body = body.replace('{{extractionSummary}}', extraction_summary)
    body = body.replace('{{exceptionsSection}}', exceptions_section)
    body = body.replace('{{failedAttachmentsSection}}', failed_section)
    body = body.replace('{{requestDetails}}', request_details)
    body = body.replace('{{totalProducts}}', str(len(products)))
    body = body.replace('{{totalAttachments}}', str(len(state['attachments'])))
    
    return body

def render_failure_template(template, state):
    """Render failure template with errors"""
    errors = state['errors']
    error_details = '<br>'.join(html.escape(error) for error in errors)
    request_details = build_request_details(state['emailContext'])
    
    body = template.replace('{{errorDetails}}', error_details)
    body = body.replace('{{requestDetails}}', request_details)
    body = body.replace('{{totalAttachments}}', str(len(state['attachments'])))
    
    return body

def build_products_html(products):
    """Build HTML for all products"""
    if not products:
        return '<p>No products extracted.</p>'
    
    html_parts = []
    for idx, product_info in enumerate(products):
        if idx > 0:
            html_parts.append('<br>')        
        product = product_info['data']
        file_name = product_info['fileName']
        
        header_data = {
            'supplier': product.get('supplier', ''),
            'product_name': product.get('product_name', ''),
            'sku_number': product.get('sku_number', ''),
            'source_file': file_name
        }
        
        header_labels = {
            'supplier': 'Supplier',
            'product_name': 'Product Name', 
            'sku_number': 'SKU',
            'source_file': 'Source File'
        }
        
        header_html = dict_to_html_table(
            header_data,
            headers=header_labels,
            css_class='header-table'
        )
        html_parts.append(header_html)
        
        skip_fields = {'supplier', 'product_name', 'sku_number', 'sourceFileName'}
        data_html = dict_to_html_table(
            product,
            skip_fields=skip_fields,
            css_class='data-table'
        )
        html_parts.append(data_html)
    
    return '\n'.join(html_parts)

def build_request_details(email_context):
    """Build request details HTML"""

    request_data = {
        'from': email_context['from'],
        'subject': email_context['subject'],
        'date': email_context['date'],
        'messageId': email_context['messageId']
    }
    
    headers = {
        'from': 'From',
        'subject': 'Subject',
        'date': 'Date',
        'messageId': 'Message ID'
    }
    
    return dict_to_html_table(request_data, headers=headers)

def process(state):
    """Process state object and format email response"""
    state = format_email_response(state)
    return state
