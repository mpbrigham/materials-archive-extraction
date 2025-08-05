"""
Common utilities for materials extraction pipeline
"""

def create_error_response(e):
    """Create standard error response structure"""
    return [{
        "json": {
            "email_context": {},
            "files": [],
            "errors": [{"error": str(e)}]
        }
    }]
    
def dict_to_html_table(d, headers=None, skip_fields=None, css_class=''):
    """Render a dict as an HTML table, with optional header mapping and skip-fields."""

    skip_fields = skip_fields or set()
    headers = headers or {}

    html = [f'<table class="{css_class}">'] if css_class else ['<table>']
    html.append('<tbody>')

    for key, value in d.items():
        if key in skip_fields:
            continue
        label = headers.get(key, key)
        html.append(f'<tr><th>{label}</th><td>{value}</td></tr>')

    html.append('</tbody></table>')
    return ''.join(html)
