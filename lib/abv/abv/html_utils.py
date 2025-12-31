"""HTML utility functions for ABV - Pattern transformation and fixes"""

import re
import os


def fix_html_list_pattern(html_content):
    """
    Transform HTML list pattern from:
    <li><a href="...">Song Name</a></li>
    
    To:
    <li>Song Name<ul><a href="...">link_text</a></ul></li>
    
    Args:
        html_content (str): HTML content to transform
    
    Returns:
        str: Transformed HTML content
    """
    
    # Pattern to match the original structure
    # Captures: href attribute, song name text
    pattern = r'<li>\s*<a\s+href="([^"]+)"\s*>\s*([^<]+)\s*</a>\s*</li>'
    
    def replace_match(match):
        href = match.group(1).strip()
        song_name = match.group(2).strip()
        
        # Determine link text based on filename
        if 'translation' in href.lower():
            link_text = 'translation'
        elif 'sheet' in href.lower() or 'music' in href.lower():
            link_text = 'sheet music'
        elif '.pdf' in href.lower():
            link_text = 'PDF'
        elif '.mp3' in href.lower() or '.m4a' in href.lower():
            link_text = 'audio'
        else:
            # Default to filename without extension
            link_text = os.path.splitext(os.path.basename(href))[0]
        
        # Return the new pattern
        return f'''  <li>
    {song_name}
    <ul>
    <a href="{href}">{link_text}</a>
    </ul>
  </li>'''
    
    # Apply the transformation
    result = re.sub(pattern, replace_match, html_content, flags=re.MULTILINE | re.IGNORECASE)
    
    return result


def fix_html_file_pattern(input_file, output_file=None):
    """
    Apply the HTML pattern fix to a file
    
    Args:
        input_file (str): Path to input HTML file
        output_file (str, optional): Path to output file. If None, overwrites input file
    
    Returns:
        str: Fixed HTML content
    """
    if output_file is None:
        output_file = input_file
    
    # Read the file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply the transformation
    fixed_content = fix_html_list_pattern(content)
    
    # Write back to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"✓ Fixed HTML patterns in {input_file}")
    if output_file != input_file:
        print(f"  Output saved to {output_file}")
    
    return fixed_content


def batch_fix_html_files(directory, file_patterns=None):
    """
    Apply HTML pattern fixes to multiple files in a directory
    
    Args:
        directory (str): Directory containing HTML files
        file_patterns (list, optional): List of filenames to process. 
                                       If None, processes common HTML files
    
    Returns:
        dict: Results of processing each file
    """
    if file_patterns is None:
        file_patterns = [
            "music-complete.html",
            "music-current.html", 
            "index.html"
        ]
    
    results = {}
    
    for filename in file_patterns:
        filepath = os.path.join(directory, filename)
        
        try:
            if os.path.exists(filepath):
                print(f"\nProcessing {filename}...")
                
                # Read original content
                with open(filepath, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                # Count original patterns
                original_pattern = r'<li>\s*<a\s+href="[^"]+"\s*>\s*[^<]+\s*</a>\s*</li>'
                original_matches = len(re.findall(original_pattern, original_content, re.MULTILINE | re.IGNORECASE))
                
                # Apply fix
                fixed_content = fix_html_file_pattern(filepath)
                
                results[filename] = {
                    'success': True,
                    'patterns_fixed': original_matches,
                    'message': f"Fixed {original_matches} patterns"
                }
                
                if original_matches > 0:
                    print(f"  ✓ Fixed {original_matches} list item patterns")
                else:
                    print("  ℹ No matching patterns found")
                    
            else:
                results[filename] = {
                    'success': False,
                    'message': f"File not found: {filepath}"
                }
                print(f"✗ File not found: {filepath}")
                
        except Exception as e:
            results[filename] = {
                'success': False,
                'message': f"Error: {str(e)}"
            }
            print(f"✗ Error processing {filename}: {e}")
    
    return results


def clean_html_whitespace(html_content):
    """
    Clean up excessive whitespace in HTML while preserving structure
    
    Args:
        html_content (str): HTML content to clean
    
    Returns:
        str: Cleaned HTML content
    """
    # Remove excessive blank lines (more than 2 consecutive)
    html_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', html_content)
    
    # Clean up whitespace around tags
    html_content = re.sub(r'>\s+<', '><', html_content)
    
    # Fix indentation in list items
    html_content = re.sub(r'<li>\s+', '<li>', html_content)
    html_content = re.sub(r'\s+</li>', '</li>', html_content)
    
    return html_content