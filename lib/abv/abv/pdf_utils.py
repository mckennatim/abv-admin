"""PDF utility functions for ABV - Convert markdown to PDF"""

import os
import markdown


def markdown_to_pdf_weasyprint(markdown_file_path, output_pdf_path=None, css_styling=None):
    """
    Convert markdown file to PDF using weasyprint
    
    Args:
        markdown_file_path (str): Path to the markdown file
        output_pdf_path (str, optional): Output PDF path. If None, uses same name with .pdf extension
        css_styling (str, optional): Custom CSS styling
    
    Returns:
        str: Path to created PDF file
    """
    try:
        from weasyprint import HTML, CSS
    except ImportError:
        raise ImportError("weasyprint not installed. Run: pip install weasyprint")
    
    # Read markdown file
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
    
    # Default CSS for better formatting
    default_css = """
    @page {
        margin: 1in;
        size: letter;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: none;
    }
    h1 {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-top: 30px;
    }
    h2 {
        color: #34495e;
        margin-top: 25px;
    }
    h3 {
        color: #7f8c8d;
    }
    ul, ol {
        margin-left: 20px;
    }
    li {
        margin-bottom: 5px;
    }
    strong {
        color: #2c3e50;
    }
    a {
        color: #3498db;
        text-decoration: none;
    }
    code {
        background-color: #f8f9fa;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    }
    pre {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
    }
    """
    
    # Use custom CSS if provided, otherwise use default
    css_content = css_styling if css_styling else default_css
    
    # Wrap HTML with proper structure
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>ABV Notes</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Determine output path
    if output_pdf_path is None:
        base_name = os.path.splitext(markdown_file_path)[0]
        output_pdf_path = f"{base_name}.pdf"
    
    # Create PDF
    html_doc = HTML(string=full_html)
    css_doc = CSS(string=css_content)
    html_doc.write_pdf(output_pdf_path, stylesheets=[css_doc])
    
    print(f"✓ Created PDF: {output_pdf_path}")
    return output_pdf_path


def markdown_to_pdf_pdfkit(markdown_file_path, output_pdf_path=None):
    """
    Convert markdown file to PDF using pdfkit (requires wkhtmltopdf)
    
    Args:
        markdown_file_path (str): Path to the markdown file
        output_pdf_path (str, optional): Output PDF path
    
    Returns:
        str: Path to created PDF file
    """
    try:
        import pdfkit
    except ImportError:
        raise ImportError("pdfkit not installed. Run: pip install pdfkit")
    
    # Read markdown file
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['extra'])
    
    # Determine output path
    if output_pdf_path is None:
        base_name = os.path.splitext(markdown_file_path)[0]
        output_pdf_path = f"{base_name}.pdf"
    
    # PDF options
    options = {
        'page-size': 'Letter',
        'margin-top': '1in',
        'margin-right': '1in',
        'margin-bottom': '1in',
        'margin-left': '1in',
        'encoding': "UTF-8",
        'no-outline': None
    }
    
    # Create PDF
    pdfkit.from_string(html_content, output_pdf_path, options=options)
    
    print(f"✓ Created PDF: {output_pdf_path}")
    return output_pdf_path


def convert_notes_to_pdf(notes_directory, output_directory=None):
    """
    Convert all markdown files in notes directory to PDF
    
    Args:
        notes_directory (str): Path to notes directory
        output_directory (str, optional): Output directory for PDFs
    
    Returns:
        list: List of created PDF files
    """
    if output_directory is None:
        output_directory = notes_directory
    
    os.makedirs(output_directory, exist_ok=True)
    
    pdf_files = []
    
    # Find all markdown files
    for filename in os.listdir(notes_directory):
        if filename.endswith('.md'):
            markdown_path = os.path.join(notes_directory, filename)
            pdf_filename = filename.replace('.md', '.pdf')
            pdf_path = os.path.join(output_directory, pdf_filename)
            
            try:
                # Try weasyprint first
                result_path = markdown_to_pdf_weasyprint(markdown_path, pdf_path)
                pdf_files.append(result_path)
            except ImportError:
                try:
                    # Fall back to pdfkit
                    result_path = markdown_to_pdf_pdfkit(markdown_path, pdf_path)
                    pdf_files.append(result_path)
                except ImportError:
                    print(f"✗ Cannot convert {filename} - no PDF libraries available")
                    print("Install with: pip install weasyprint  OR  pip install pdfkit")
                    continue
            except Exception as e:
                print(f"✗ Error converting {filename}: {e}")
                continue
    
    return pdf_files


# Convenience function for the specific notes file
def convert_notes_10_19_to_pdf(base_directory="./"):
    """
    Convert the specific notes10_19.md file to PDF
    """
    notes_file = os.path.join(base_directory, "notes", "notes10_19.md")
    
    if not os.path.exists(notes_file):
        print(f"✗ Notes file not found: {notes_file}")
        return None
    
    try:
        pdf_path = markdown_to_pdf_weasyprint(notes_file)
        return pdf_path
    except ImportError:
        try:
            pdf_path = markdown_to_pdf_pdfkit(notes_file)
            return pdf_path
        except ImportError:
            print("✗ No PDF conversion libraries available")
            print("Install with: pip install weasyprint  OR  pip install pdfkit")
            return None


def convert_notes_to_html(markdown_file_path, output_html_path=None):
    """
    Convert markdown file to styled HTML (fallback when PDF conversion fails)
    
    Args:
        markdown_file_path (str): Path to the markdown file
        output_html_path (str, optional): Output HTML path
    
    Returns:
        str: Path to created HTML file
    """
    # Read markdown file
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    html_content = markdown.markdown(markdown_content, extensions=['extra', 'codehilite'])
    
    # Determine output path
    if output_html_path is None:
        base_name = os.path.splitext(markdown_file_path)[0]
        output_html_path = f"{base_name}.html"
    
    # Create styled HTML
    styled_html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ABV Notes</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-top: 30px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 25px;
        }}
        h3 {{
            color: #7f8c8d;
        }}
        ul, ol {{
            margin-left: 20px;
        }}
        li {{
            margin-bottom: 5px;
        }}
        strong {{
            color: #2c3e50;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        code {{
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        @media print {{
            body {{ 
                margin: 0; 
                max-width: none;
            }}
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>'''
    
    # Write HTML file
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(styled_html)
    
    print(f"✓ Created HTML: {output_html_path}")
    print("  You can open this in a browser and use Print > Save as PDF")
    return output_html_path