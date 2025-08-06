"""
Result Processor - Format extraction results from aggregated attachments
"""

import os
import html
from common import dict_to_html_table

service_name = "Result Processor"

def format_email_response(attachments):
    """Format aggregated attachments into email response data"""
    
    if not attachments:
        raise ValueError(f"[{service_name}] No attachments to process")
    
    email_context = attachments[0]['emailContext']
    products = collect_products(attachments)
    errors = collect_errors(attachments)
    
    template_name = 'success' if products else 'failure'

    return {
        'from': os.environ['EMAIL_USER'],
        'to': email_context['from'],
        'subject': format_subject(email_context['subject'], bool(products)),
        'body': render_template(template_name, attachments, email_context, products, errors)
    }

def collect_products(attachments):
    """Extract all products from processed attachments"""
    
    all_products = []
    for attachment in attachments:
        if attachment['attachments']['status'] == f"LLM Extraction pass":
            all_products.extend(attachment['products'])

    return all_products

def collect_errors(attachments):
    """Collect all errors from processed attachments"""
    
    all_errors = []
    for attachment in attachments:
        all_errors.extend(attachment['errors'])
        
    return all_errors
    
def format_subject(original_subject, success):
    """Format email subject line"""
    
    status = "Complete" if success else "Failed"
    return f"Re: {original_subject} - Materials Extraction {status}"

def render_template(template_name, attachments, email_context, products, errors):
    """Load template and substitute data"""
    
    template_path = f'/app/email_templates/{template_name}.html'
    with open(template_path, 'r') as f:
        template = f.read()
    
    if template_name == 'success':
        return render_success_template(template, attachments, email_context, products)
    else:
        return render_failure_template(template, email_context, errors, attachments)

def render_success_template(template, attachments, email_context, products):
    """Render success template with products"""
    
    product_html = build_products_html(products)
    request_details = build_request_details(email_context)
    model_name = os.environ['LLM_MODEL']
    
    summaries = []
    exceptions = []
    for attachment in attachments:
        if attachment['attachments']['status'] == f"LLM Extraction pass":
            products = attachment['products']
            file_name = attachment['attachments']['fileName']
            if 'processing_summary' in products:
                summaries.append(f"{file_name}: {products['processing_summary']}")
            if 'processing_exceptions' in products:
                for exception in products['processing_exceptions']:
                    exceptions.append(f"{file_name}: {exception}")
    
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
    
    failed_attachments = [a for a in attachments if 'failed' in a['attachments']['status']]
    failed_section = ''
    if failed_attachments:
        failed_section = '<div class="failed-attachments"><h3>Processing Issues</h3><ul>'
        for attachment in failed_attachments:
            file_name = attachment['fileName']
            attachment_errors = attachment.get('errors', [])
            error = attachment_errors[-1] if attachment_errors else 'Processing failed'
            failed_section += f'<li><strong>{html.escape(file_name)}:</strong> {html.escape(error)}</li>'
        failed_section += '</ul></div>'
    
    body = template.replace('{{productTables}}', product_html)
    body = body.replace('{{extractionSummary}}', extraction_summary)
    body = body.replace('{{exceptionsSection}}', exceptions_section)
    body = body.replace('{{failedAttachmentsSection}}', failed_section)
    body = body.replace('{{requestDetails}}', request_details)
    body = body.replace('{{totalProducts}}', str(len(products)))
    body = body.replace('{{totalAttachments}}', str(len(attachments)))
    
    return body

def render_failure_template(template, email_context, errors, attachments):
    """Render failure template with errors"""
    
    error_details = '<br>'.join(html.escape(error) for error in errors) if errors else 'No specific errors recorded'
    request_details = build_request_details(email_context)
    
    body = template.replace('{{errorDetails}}', error_details)
    body = body.replace('{{requestDetails}}', request_details)
    body = body.replace('{{totalAttachments}}', str(len(attachments)))
    
    return body

def build_products_html(products):
    """Build HTML for all products"""
    
    if not products:
        return '<p>No products extracted.</p>'
    
    html_parts = []
    for idx, product in enumerate(products):
        if idx > 0:
            html_parts.append('<br>')
        
        header_data = {
            'supplier': product['supplier'],
            'product_name': product['product_name'],
            'sku_number': product['sku_number'],
            'material_category': product['material_category'],
            'source_file': product['fileName']
        }
        header_labels = {
            'supplier': 'Supplier',
            'product_name': 'Product Name', 
            'sku_number': 'SKU',
            'material_category': 'Material Category',
            'source_file': 'Source File'
        }
        
        header_html = dict_to_html_table(
            header_data,
            headers=header_labels,
            css_class='header-table'
        )
        html_parts.append(header_html)
        
        skip_fields = {'supplier', 'product_name', 'sku_number', 'material_category', 'fileName'}
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
        'from': email_context.get('from', ''),
        'subject': email_context.get('subject', ''),
        'date': email_context.get('date', ''),
        'messageId': email_context.get('messageId', '')
    }
    
    headers = {
        'from': 'From',
        'subject': 'Subject',
        'date': 'Date',
        'messageId': 'Message ID'
    }
    
    return dict_to_html_table(request_data, headers=headers)

def process(state):
    """Process aggregated attachments array and format email response"""   
    return format_email_response(state)
