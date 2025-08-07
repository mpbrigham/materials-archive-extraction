"""
Email Formatting - Transform extraction results into structured email data
"""

import os
from datetime import datetime
import constants

service_name = "Email Formatting"

# Status configuration for visual hierarchy
STATUS_CONFIG = {
    'complete': {'icon': '✅', 'color': '#22c55e', 'level': 'complete'},
    'warning': {'icon': '⚠️', 'color': '#f59e0b', 'level': 'warning'},
    'error': {'icon': '❌', 'color': '#ef4444', 'level': 'error'}
}

def process(state):
    """Process aggregated attachments and format email response."""
    
    email_context = state['emailContext']
    attachments = state['attachments']
    
    # Transform data for template
    email_data = format_email_data(attachments, email_context)
    
    # Determine template based on extraction results
    template_name = 'success' if email_data['pdf_groups'] else 'failure'
    
    return {
        'from': os.environ['EMAIL_USER'],
        'to': email_context['from'],
        'subject': format_subject(email_context['subject'], template_name == 'success'),
        'body': render_template(template_name, email_data, state['errors'])
    }

def format_email_data(attachments, email_context):
    """Transform raw attachments into structured email context grouped by PDF."""
    
    # Group products by their source PDF
    pdf_groups = []
    total_products = 0
    pdf_count = len(attachments)
    
    for attachment in attachments:
        pdf_group = {
            'filename': attachment['fileName'],
            'products': [],
            'processing_summary': None,
            'processing_exceptions': [],
            'status': analyze_attachment_status(attachment)
        }
        
        # Extract products from this PDF
        if attachment['status'] == 'LLM Extraction pass' and 'products' in attachment:
            for product in attachment['products']:
                formatted_product = format_product(product, attachment)
                pdf_group['products'].append(formatted_product)
                total_products += 1
        
        # Extract PDF-level processing notes
        if 'processing_summary' in attachment and attachment['processing_summary']:
            pdf_group['processing_summary'] = attachment['processing_summary']
        
        if 'processing_exceptions' in attachment and attachment['processing_exceptions']:
            pdf_group['processing_exceptions'] = attachment['processing_exceptions']
        
        pdf_groups.append(pdf_group)
    
    overall_status = determine_overall_status(attachments)
    
    return {
        'summary': {
            'status': overall_status,
            'status_icon': STATUS_CONFIG[overall_status]['icon'],
            'product_count': total_products,
            'pdf_count': pdf_count,
            'model': os.environ['LLM_MODEL']
        },
        'pdf_groups': pdf_groups,
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'system': 'Materials Library System',
            'contact': 'data@materiatek.com'
        }
    }

def format_product(product, attachment):
    """Structure single product data with all properties visible."""
    
    status = analyze_product_status(product)
    
    return {
        'name': product['product_name'],
        'status': status,
        'company': {
            'supplier': product['supplier'],
            'category': product['material_category']
        },
        'sku': product['sku_number'] if product['sku_number'] else None,
        'properties': extract_all_properties(product)
    }

def extract_all_properties(product):
    """Extract all properties in schema order."""
    
    # Fields already shown in header section
    EXCLUDE_FIELDS = {
        'product_name', 'supplier', 'material_category', 
        'sku_number', 'fileName', 'status'
    }
    
    properties = []
    
    # Process all fields from the product
    for field, value in product.items():
        if field not in EXCLUDE_FIELDS and value:
            properties.append({
                'name': format_field_name(field),
                'value': format_field_value(value)
            })
    
    return properties

def analyze_attachment_status(attachment):
    """Determine extraction status based on attachment status."""
    
    if attachment['status'] == 'failed':
        return STATUS_CONFIG['error'].copy()
    
    # Check if there are processing exceptions
    if 'processing_exceptions' in attachment and attachment['processing_exceptions']:
        return STATUS_CONFIG['warning'].copy()
    
    return STATUS_CONFIG['complete'].copy()

def analyze_product_status(product):
    """Determine product-level status."""
    
    # Check for missing critical fields
    if not product.get('sku_number'):
        return STATUS_CONFIG['warning'].copy()
    
    return STATUS_CONFIG['complete'].copy()

def determine_overall_status(attachments):
    """Determine overall extraction status."""
    
    if not attachments:
        return 'error'
    
    has_any_success = False
    has_any_warning = False
    
    for attachment in attachments:
        if attachment['status'] == 'LLM Extraction pass':
            has_any_success = True
            if 'processing_exceptions' in attachment and attachment['processing_exceptions']:
                has_any_warning = True
        
    if not has_any_success:
        return 'error'
    elif has_any_warning:
        return 'warning'
    else:
        return 'complete'

def format_field_name(field):
    """Convert field name to display format."""
    
    if field in constants.field_names:
        return constants.field_names[field]
    
    # Default formatting
    return field.replace('_', ' ').title()

def format_field_value(value):
    """Format field value for display."""
    
    if value is None or value == '':
        return 'Not specified'
    elif isinstance(value, bool):
        return 'Yes' if value else 'No'
    elif isinstance(value, list):
        return ', '.join(str(v) for v in value)
    else:
        return str(value)

def format_subject(original_subject, success):
    """Format email subject line."""
    
    status = "Complete" if success else "Failed"
    return f"Re: {original_subject} - Materials Extraction {status}"

def render_template(template_name, email_data, errors):
    """Load template and substitute data."""
    
    import html
    
    template_path = f'/app/email_templates/{template_name}.html'
    with open(template_path, 'r') as f:
        template = f.read()
    
    if template_name == 'success':
        return render_success_template(template, email_data)
    else:
        return render_failure_template(template, email_data, errors)

def render_success_template(template, email_data):
    """Render success template with structured data."""
    
    import html
    
    # Replace template variables with actual data
    body = template
    
    # Replace summary section - using simple placeholders now
    body = body.replace('{{ summary.status }}', email_data['summary']['status'])
    body = body.replace('{{ summary.status_icon }}', email_data['summary']['status_icon'])
    body = body.replace('{{ summary.product_count }}', str(email_data['summary']['product_count']))
    body = body.replace('{{ summary.pdf_count }}', str(email_data['summary']['pdf_count']))
    body = body.replace('{{ summary.model }}', html.escape(email_data['summary']['model']))
    
    # Build PDF groups HTML
    pdf_groups_html = []
    for pdf_group in email_data['pdf_groups']:
        pdf_html = render_pdf_group(pdf_group)
        pdf_groups_html.append(pdf_html)
    
    body = body.replace('{{ pdf_groups_html }}', '\n'.join(pdf_groups_html))
    
    # Replace metadata
    body = body.replace('{{ metadata.system }}', html.escape(email_data['metadata']['system']))
    body = body.replace('{{ metadata.contact }}', html.escape(email_data['metadata']['contact']))
    
    return body

def render_failure_template(template, email_data, errors):
    """Render failure template with errors."""
    
    import html
    
    # Replace template variables
    body = template
    
    # Format error details
    if errors:
        error_list = '<ul>' + ''.join(f'<li>{html.escape(error)}</li>' for error in errors) + '</ul>'
    else:
        error_list = '<p>No valid products could be extracted from the provided PDFs.</p>'
    
    body = body.replace('{{ error_details }}', error_list)
    body = body.replace('{{ summary.pdf_count }}', str(email_data['summary']['pdf_count']))
    body = body.replace('{{ metadata.system }}', html.escape(email_data['metadata']['system']))
    body = body.replace('{{ metadata.contact }}', html.escape(email_data['metadata']['contact']))
    
    return body

def render_pdf_group(pdf_group):
    """Render a PDF group with all its products and extraction notes."""
    
    import html
    
    group_html_parts = []
    
    # Render each product in this PDF
    for product in pdf_group['products']:
        product_html = render_product_card(product, pdf_group['filename'])
        group_html_parts.append(product_html)
    
    # Add PDF-level extraction notes if any exist
    if pdf_group['processing_summary'] or pdf_group['processing_exceptions']:
        notes_html = render_pdf_extraction_notes(
            pdf_group['filename'],
            pdf_group['processing_summary'],
            pdf_group['processing_exceptions']
        )
        group_html_parts.append(notes_html)
    
    return '\n'.join(group_html_parts)

def render_product_card(product, filename):
    """Render single product card HTML."""
    
    import html
    
    # Determine status class
    status_class = f"product-card-{product['status']['level']}"
    
    # Build properties rows
    properties_html = []
    for prop in product['properties']:
        properties_html.append(f'''
            <tr class="property-row">
                <td class="property-name">{html.escape(prop['name'])}:</td>
                <td class="property-value">{html.escape(prop['value'])}</td>
            </tr>
        ''')
    
    # Build complete product card
    card_html = f'''
        <div class="product-card {status_class}">
            <div class="product-header">
                {product['status']['icon']} {html.escape(product['name']).upper()}
            </div>
            
            <div class="product-meta">
                📄 {html.escape(filename)}<br>
                🏢 {html.escape(product['company']['supplier'])} · {html.escape(product['company']['category'])}<br>
                🏷️ {html.escape(product['sku']) if product['sku'] else 'Missing SKU'}
            </div>
            
            {'<div class="properties-section"><div class="section-header">PROPERTIES</div><table class="properties-table" role="presentation">' + ''.join(properties_html) + '</table></div>' if properties_html else ''}
        </div>
    '''
    
    return card_html

def render_pdf_extraction_notes(filename, processing_summary, processing_exceptions):
    """Render PDF-level extraction notes section."""
    
    import html
    
    notes_items = []
    
    # Add processing summary with info icon
    if processing_summary:
        notes_items.append(f'''
            <div class="note-item note-info">
                ℹ️ {html.escape(processing_summary)}
            </div>
        ''')
    
    # Add each exception with warning icon
    for exception in processing_exceptions:
        notes_items.append(f'''
            <div class="note-item note-warning">
                ⚠️ {html.escape(exception)}
            </div>
        ''')
    
    # Only render if there are notes to show
    if not notes_items:
        return ''
    
    notes_html = f'''
        <div class="pdf-notes-section">
            <div class="section-header">EXTRACTION NOTES - {html.escape(filename)}</div>
            {''.join(notes_items)}
        </div>
    '''
    
    return notes_html
