#!/usr/bin/env python3
"""
Script to automatically update the website with extracted content.
This script combines the extraction and organization steps and updates
the website's English and Arabic pages with the processed content.
"""

import os
import argparse
import subprocess
import re
import json
from pathlib import Path

def update_html_file(file_path, content_html, content_type="body"):
    """Update an HTML file by inserting content into a specific section."""
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    if content_type == "body":
        # Find the content container div in the main section
        pattern = r'<div class="content-container">(.*?)</div>\s*<div class="content-navigation">'
        replacement = f'<div class="content-container">\n{content_html}\n</div>\n<div class="content-navigation">'
        new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    else:
        # For other content types, you could add specific patterns here
        new_html = html
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_html)

def create_toc(sections):
    """Create a table of contents from section titles."""
    toc_html = '<ul class="toc-list">\n'
    
    for section in sections:
        section_id = section["id"]
        title_en = section["title_en"]
        title_ar = section["title_ar"]
        
        toc_html += f'''
        <li>
            <a href="#{section_id}">
                <span class="en">{title_en}</span>
                <span class="ar">{title_ar}</span>
            </a>
        </li>
        '''
    
    toc_html += '</ul>\n'
    return toc_html

def extract_section_titles(extracted_dir):
    """Extract section titles from the processed content files."""
    sections = []
    content_files = sorted([f for f in os.listdir(extracted_dir) 
                           if f.startswith("page_") and f.endswith("_content.md")])
    
    for i, file_name in enumerate(content_files):
        file_path = os.path.join(extracted_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to extract a title from the content
        # This assumes the first line containing a # is the title
        en_title = "Section " + str(i+1)
        ar_title = "القسم " + str(i+1)
        
        en_match = re.search(r'^# (.*?)$', content, re.MULTILINE)
        if en_match:
            en_title = en_match.group(1)
        
        # Look for Arabic title after the translation marker
        ar_content = ""
        if "ARABIC TRANSLATION:" in content:
            ar_content = content.split("ARABIC TRANSLATION:")[1]
            ar_match = re.search(r'^# (.*?)$', ar_content, re.MULTILINE)
            if ar_match:
                ar_title = ar_match.group(1)
        
        sections.append({
            "id": f"section-{i+1}",
            "title_en": en_title,
            "title_ar": ar_title
        })
    
    return sections

def main():
    parser = argparse.ArgumentParser(description="Update website with extracted PDF content")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--model", default="llama3", help="Ollama model to use")
    parser.add_argument("--extracted-dir", default="extracted_content", help="Directory for extracted content")
    args = parser.parse_args()
    
    # 1. Extract content from PDF
    print("Step 1: Extracting content from PDF...")
    extract_cmd = [
        "python3", "extract_pdf_with_ollama.py", 
        args.pdf_path, 
        "--model", args.model,
        "--output-dir", args.extracted_dir
    ]
    subprocess.run(extract_cmd)
    
    # 2. Organize content
    print("\nStep 2: Organizing content into website structure...")
    organize_cmd = [
        "python3", "organize_content.py",
        args.extracted_dir
    ]
    subprocess.run(organize_cmd)
    
    # 3. Update website pages
    print("\nStep 3: Updating website pages...")
    
    # a. Extract section titles for TOC
    sections = extract_section_titles(args.extracted_dir)
    
    # b. Create TOC HTML
    toc_html = create_toc(sections)
    
    # c. Get combined content
    en_content_path = os.path.join("en", "all_content.html")
    if os.path.exists(en_content_path):
        with open(en_content_path, 'r', encoding='utf-8') as f:
            combined_content = f.read()
    else:
        combined_content = "<p>No content has been extracted yet.</p>"
    
    # d. Update English and Arabic pages
    update_html_file("en/index.html", toc_html + combined_content)
    update_html_file("ar/index.html", toc_html + combined_content)
    
    print("\nWebsite update complete!")
    print(f"- {len(sections)} sections processed")
    print("- Table of contents generated")
    print("- English and Arabic content pages updated")
    print("\nYou can now view the website by opening index.html in your browser.")

if __name__ == "__main__":
    main()