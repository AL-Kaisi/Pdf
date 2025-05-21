#!/usr/bin/env python3
"""
Script to integrate summarized pages into the website structure.
This script combines the existing HTML summaries with the website's bilingual format.
"""

import os
import glob
import re
from pathlib import Path

def read_html_file(file_path):
    """Read HTML file and return its content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def write_html_file(file_path, content):
    """Write content to HTML file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")
        return False

def extract_content_from_html(html_content):
    """Extract the main content from generated HTML files."""
    # Find content between content-section div tags
    pattern = r'<div class="content-section"[^>]*>(.*?)</div>'
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return html_content

def create_combined_content():
    """Create a combined HTML file with all summarized content."""
    html_dir = "html_content"
    if not os.path.exists(html_dir):
        print(f"HTML content directory {html_dir} not found")
        return False
    
    # Get all HTML files except index
    html_files = sorted([f for f in glob.glob(os.path.join(html_dir, "page_*.html"))])
    
    if not html_files:
        print("No HTML content files found")
        return False
    
    combined_content = ""
    toc_entries = []
    
    print(f"Processing {len(html_files)} HTML files...")
    
    for i, file_path in enumerate(html_files, 1):
        print(f"Processing {os.path.basename(file_path)}...")
        
        content = read_html_file(file_path)
        if not content:
            continue
        
        # Extract the main content
        main_content = extract_content_from_html(content)
        
        # Update section ID to be sequential
        main_content = re.sub(r'id="section-\d+"', f'id="section-{i}"', main_content)
        
        # Extract title for TOC
        en_title_match = re.search(r'<h2>(.*?)</h2>', main_content)
        ar_title_match = re.search(r'<h2>\[(.*?)\]</h2>', main_content)
        
        en_title = en_title_match.group(1) if en_title_match else f"Section {i}"
        ar_title = ar_title_match.group(1) if ar_title_match else f"القسم {i}"
        
        # Clean up the titles
        en_title = re.sub(r'<[^>]+>', '', en_title).strip()
        ar_title = re.sub(r'<[^>]+>', '', ar_title).strip()
        
        toc_entries.append({
            "id": f"section-{i}",
            "title_en": en_title,
            "title_ar": ar_title
        })
        
        combined_content += f'\n<div class="content-section" id="section-{i}">\n{main_content}\n</div>\n'
    
    # Create table of contents
    toc_html = '<div id="table-of-contents">\n'
    toc_html += '    <h3><span class="en">Table of Contents</span><span class="ar">جدول المحتويات</span></h3>\n'
    toc_html += '    <ul class="toc-list">\n'
    
    for entry in toc_entries:
        toc_html += f'''        <li>
            <a href="#{entry['id']}">
                <span class="en">{entry['title_en']}</span>
                <span class="ar">{entry['title_ar']}</span>
            </a>
        </li>\n'''
    
    toc_html += '    </ul>\n</div>\n'
    
    # Combine TOC and content
    full_content = toc_html + combined_content
    
    return full_content, len(html_files)

def update_english_page(content):
    """Update the English page with summarized content."""
    en_file = "en/index.html"
    
    if not os.path.exists(en_file):
        print(f"English page {en_file} not found")
        return False
    
    html = read_html_file(en_file)
    if not html:
        return False
    
    # Replace the content container
    pattern = r'<div class="content-container">(.*?)</div>\s*<div class="content-navigation">'
    replacement = f'<div class="content-container">\n                    <h2><span class="en">English Study Materials</span><span class="ar">المواد الدراسية الإنجليزية</span></h2>\n                    <p><span class="en">Comprehensive study notes from the Tikrit Pharmacy Competitive Curriculum 2025.</span><span class="ar">ملاحظات دراسية شاملة من منهاج تنافسي صيدلة تكريت 2025.</span></p>\n                    <div class="note-box">\n                        <strong><span class="en">Note:</span><span class="ar">ملاحظة:</span></strong> <span class="en">The content below is summarized from the original curriculum for efficient studying.</span><span class="ar">المحتوى أدناه ملخص من المنهج الأصلي للدراسة الفعالة.</span>\n                    </div>\n                    {content}\n                </div>\n                <div class="content-navigation">'
    
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    return write_html_file(en_file, new_html)

def update_arabic_page(content):
    """Update the Arabic page with summarized content."""
    ar_file = "ar/index.html"
    
    if not os.path.exists(ar_file):
        print(f"Arabic page {ar_file} not found")
        return False
    
    html = read_html_file(ar_file)
    if not html:
        return False
    
    # Replace the content container
    pattern = r'<div class="content-container">(.*?)</div>\s*<div class="content-navigation">'
    replacement = f'<div class="content-container">\n                    <h2><span class="en">Arabic Study Materials</span><span class="ar">المواد الدراسية العربية</span></h2>\n                    <p><span class="en">Comprehensive study notes from the Tikrit Pharmacy Competitive Curriculum 2025.</span><span class="ar">ملاحظات دراسية شاملة من منهاج تنافسي صيدلة تكريت 2025.</span></p>\n                    <div class="note-box">\n                        <strong><span class="en">Note:</span><span class="ar">ملاحظة:</span></strong> <span class="en">The content below is summarized from the original curriculum for efficient studying.</span><span class="ar">المحتوى أدناه ملخص من المنهج الأصلي للدراسة الفعالة.</span>\n                    </div>\n                    {content}\n                </div>\n                <div class="content-navigation">'
    
    new_html = re.sub(pattern, replacement, html, flags=re.DOTALL)
    
    return write_html_file(ar_file, new_html)

def create_full_content_pages():
    """Create comprehensive content pages with all summaries."""
    # Create English full content page
    en_content, num_sections = create_combined_content()
    if not en_content:
        return False
    
    # Save to en/full_content.html
    en_full_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Complete Study Materials - Tikrit Pharmacy 2025</title>
    <link rel="stylesheet" href="../css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header>
        <div class="container">
            <h1><span class="en">Tikrit Pharmacy Competitive Curriculum 2025</span><span class="ar">منهاج تنافسي صيدلة تكريت 2025</span></h1>
            <nav>
                <ul>
                    <li><a href="../index.html"><i class="fas fa-home"></i> <span class="en">Home</span><span class="ar">الرئيسية</span></a></li>
                    <li><a href="index.html"><i class="fas fa-book"></i> <span class="en">English</span><span class="ar">الإنجليزية</span></a></li>
                    <li><a href="../ar/index.html"><i class="fas fa-book-open"></i> <span class="en">Arabic</span><span class="ar">العربية</span></a></li>
                    <li><a href="../resources/index.html"><i class="fas fa-file-pdf"></i> <span class="en">Resources</span><span class="ar">المصادر</span></a></li>
                    <li><a href="../blog/index.html"><i class="fas fa-blog"></i> <span class="en">Study Tips</span><span class="ar">نصائح الدراسة</span></a></li>
                </ul>
            </nav>
            <div class="language-toggle">
                <button id="toggleLanguage"><i class="fas fa-language"></i> <span class="toggle-text">عربي</span></button>
            </div>
        </div>
    </header>

    <main>
        <section class="content-section">
            <div class="container">
                <div class="content-container">
                    <h2><span class="en">Complete Study Materials</span><span class="ar">المواد الدراسية الكاملة</span></h2>
                    <p><span class="en">All {num_sections} sections from the Tikrit Pharmacy Competitive Curriculum 2025, summarized for efficient study.</span><span class="ar">جميع {num_sections} أقسام من منهاج تنافسي صيدلة تكريت 2025، ملخصة للدراسة الفعالة.</span></p>
                    
                    <div class="note-box">
                        <strong><span class="en">Study Guide:</span><span class="ar">دليل الدراسة:</span></strong> 
                        <span class="en">Use the table of contents to navigate between sections. Each section contains key concepts, definitions, and important information in both English and Arabic.</span>
                        <span class="ar">استخدم جدول المحتويات للتنقل بين الأقسام. يحتوي كل قسم على المفاهيم الرئيسية والتعريفات والمعلومات المهمة باللغتين الإنجليزية والعربية.</span>
                    </div>
                    
                    {en_content}
                </div>
                
                <div class="content-navigation">
                    <a href="index.html" class="btn secondary"><i class="fas fa-arrow-left"></i> <span class="en">Back to Summary</span><span class="ar">العودة إلى الملخص</span></a>
                    <a href="../resources/index.html" class="btn primary"><span class="en">Download PDF</span><span class="ar">تحميل PDF</span> <i class="fas fa-download"></i></a>
                </div>
            </div>
        </section>
    </main>

    <footer>
        <div class="container">
            <p>&copy; 2025 Tikrit Pharmacy Curriculum | <span class="en">Created to help students excel</span><span class="ar">تم إنشاؤه لمساعدة الطلاب على التفوق</span></p>
        </div>
    </footer>

    <script src="../js/main.js"></script>
</body>
</html>"""
    
    os.makedirs("en", exist_ok=True)
    write_html_file("en/full_content.html", en_full_template)
    
    # Create Arabic version
    os.makedirs("ar", exist_ok=True)
    ar_full_template = en_full_template.replace('lang="en"', 'lang="ar"').replace('../ar/index.html', 'index.html').replace('href="index.html"', 'href="../en/index.html"')
    write_html_file("ar/full_content.html", ar_full_template)
    
    return True, num_sections

def main():
    print("Integrating summarized pages into website...")
    
    # Create combined content
    content, num_sections = create_combined_content()
    if not content:
        print("Failed to create combined content")
        return
    
    # Create full content pages
    success, sections = create_full_content_pages()
    if success:
        print(f"✓ Created full content pages with {sections} sections")
    
    # Update existing pages
    if update_english_page(content):
        print("✓ Updated English page")
    else:
        print("✗ Failed to update English page")
    
    if update_arabic_page(content):
        print("✓ Updated Arabic page")
    else:
        print("✗ Failed to update Arabic page")
    
    print(f"\nIntegration complete!")
    print(f"- {num_sections} sections integrated")
    print("- Full content pages created at en/full_content.html and ar/full_content.html")
    print("- Main English and Arabic pages updated")
    print("\nYou can now view the website by opening index.html in your browser.")

if __name__ == "__main__":
    main()