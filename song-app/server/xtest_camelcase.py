#!/usr/bin/env python3
"""
Test script for camelCase filename conversion
"""

def camel_case_filename(filename):
    """Convert filename to camelCase, removing spaces and special characters"""
    if '.' in filename:
        name, extension = filename.rsplit('.', 1)
    else:
        name, extension = filename, ''
    
    # Split on spaces, underscores, hyphens
    words = name.replace('_', ' ').replace('-', ' ').split()
    
    if not words:
        return filename  # Return original if no valid words
    
    # First word lowercase, subsequent words capitalized
    camel_name = words[0].lower()
    for word in words[1:]:
        if word:  # Skip empty words
            camel_name += word.capitalize()
    
    # Remove any remaining special characters except alphanumeric
    camel_name = ''.join(char for char in camel_name if char.isalnum())
    
    # Add extension back
    if extension:
        return f"{camel_name}.{extension.lower()}"
    return camel_name

# Test cases
test_files = [
    "My Song File.mp3",
    "ale_brider_soprano.mp3", 
    "Sheet Music - Updated.pdf",
    "pronunciation guide.mp3",
    "Listen and Repeat.mp3",
    "Background-Image.jpg",
    "simple.txt",
    "Multi Word File Name.html"
]

print("CamelCase Filename Conversion Test:")
print("=" * 50)

for original in test_files:
    converted = camel_case_filename(original)
    print(f"{original:25} -> {converted}")