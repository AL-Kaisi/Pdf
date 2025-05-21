#!/usr/bin/env python3
"""
Script to summarize extracted PDF content and prepare it for the website.
This script processes raw text files, summarizes them, and generates HTML content.
"""

import os
import argparse
import json
import glob
import time
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

def read_text_file(file_path):
    """Read a text file and return its contents."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def save_text_file(file_path, content):
    """Save content to a text file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")
        return False

def summarize_with_ollama(text, model_name="llama3"):
    """Use Ollama to summarize text."""
    if not text or len(text.strip()) < 50:
        return "Insufficient text to summarize."
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": f"""
                You are a pharmacy curriculum expert. I need you to summarize the following text
                from a pharmacy curriculum document. The summary should be concise yet comprehensive,
                highlighting key concepts, definitions, and important information.

                CRITICAL INSTRUCTION: THE OUTPUT MUST BE IN ENGLISH AND ARABIC (NOT FRENCH).
                
                You are translating pharmacy curriculum content. All technical terms should be properly translated 
                into Modern Standard Arabic (MSA). DO NOT use Latin characters, Chinese characters, or any 
                non-Arabic script in the Arabic section.

                Format your response in both English and Arabic with clear section breaks:
                1. First provide a title for this section in both languages
                2. Then list key concepts or terminology with brief explanations
                3. Then summarize the main points in bullet form
                4. Finally highlight any important facts or figures

                Here's the text to summarize:

                {text}

                Format your response like this:
                # [English Title]
                ## Key Concepts
                * **Concept 1**: Explanation
                * **Concept 2**: Explanation

                ## Summary
                * Main point 1
                * Main point 2

                ## Important Information
                * Key fact 1
                * Key fact 2

                # [استراتيجيات تصميم الأدوية]
                ## المفاهيم الرئيسية
                * **المفهوم 1**: الشرح
                * **المفهوم 2**: الشرح

                ## ملخص
                * النقطة الرئيسية 1
                * النقطة الرئيسية 2

                ## معلومات مهمة
                * حقيقة أساسية 1
                * حقيقة أساسية 2
                
                IMPORTANT REMINDERS:
                1. Second language MUST be proper Arabic (MSA), not French or any other language
                2. DO NOT mix character sets in the Arabic section - use only Arabic script
                3. Ensure all technical pharmacy terms are properly translated to Arabic
                4. Put the Arabic title in square brackets with proper Arabic text
                5. Make sure the Arabic translation is high quality and natural-sounding
                """
            }
        )
        
        if response.status_code == 200:
            result = response.text
            # Process the streaming response
            content = ""
            for line in result.strip().split('\n'):
                try:
                    data = json.loads(line)
                    if "response" in data:
                        content += data["response"]
                except:
                    continue
            
            return content
        else:
            return f"Error: {response.status_code} - {response.text}"
    
    except Exception as e:
        return f"Error: {str(e)}"

def summarize_files(input_dir, output_dir, model_name="llama3", max_workers=1, start_index=1, end_index=None):
    """Summarize all text files in the input directory."""
    input_files = sorted(glob.glob(os.path.join(input_dir, "page_*.txt")))
    
    if not input_files:
        print(f"No text files found in {input_dir}")
        return
    
    # Filter files by index if specified
    if start_index or end_index:
        filtered_files = []
        for file_path in input_files:
            file_name = os.path.basename(file_path)
            match = re.search(r'page_(\d+)', file_name)
            if match:
                page_num = int(match.group(1))
                if (not start_index or page_num >= start_index) and \
                   (not end_index or page_num <= end_index):
                    filtered_files.append(file_path)
        input_files = filtered_files
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Function to process a single file
    def process_file(file_path):
        file_name = os.path.basename(file_path)
        output_file = os.path.join(output_dir, file_name.replace('.txt', '_summary.md'))
        
        # Skip if the output file already exists
        if os.path.exists(output_file):
            print(f"Skipping {file_name} - summary already exists")
            return file_name, "skipped"
        
        print(f"Processing {file_name}...")
        text = read_text_file(file_path)
        
        if not text:
            return file_name, "error reading file"
        
        summary = summarize_with_ollama(text, model_name)
        
        if summary.startswith("Error"):
            return file_name, summary
        
        success = save_text_file(output_file, summary)
        
        if success:
            return file_name, "success"
        else:
            return file_name, "error saving file"
    
    # Process files in parallel
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for file_path, status in zip(input_files, executor.map(process_file, input_files)):
            file_name = os.path.basename(file_path)
            results[file_name] = status
            
            # Small delay to avoid overwhelming the API
            time.sleep(0.5)
    
    print("\nSummarization Results:")
    for file_name, status in results.items():
        print(f"{file_name}: {status}")
    
    return results

def generate_html_from_summaries(summary_dir, output_dir, template_file=None):
    """Generate HTML content from markdown summaries."""
    summary_files = sorted(glob.glob(os.path.join(summary_dir, "*_summary.md")))
    
    if not summary_files:
        print(f"No summary files found in {summary_dir}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load template if provided
    template = None
    if template_file and os.path.exists(template_file):
        with open(template_file, 'r', encoding='utf-8') as f:
            template = f.read()
    
    # Process each summary file
    for file_path in summary_files:
        file_name = os.path.basename(file_path)
        match = re.search(r'page_(\d+)', file_name)
        
        if not match:
            continue
        
        page_num = int(match.group(1))
        output_file = os.path.join(output_dir, f"page_{page_num:04d}.html")
        
        # Read summary content
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Split English and Arabic content
        parts = markdown_content.split("# [")
        english_content = parts[0] if len(parts) > 0 else markdown_content
        arabic_content = ""
        if len(parts) > 1:
            for part in parts[1:]:
                if part.startswith("استراتيجيات") or "العربية" in part or "أدوية" in part:
                    arabic_content = "# [" + part
                    break
        
        # Convert markdown to HTML
        english_html = convert_markdown_to_html(english_content)
        arabic_html = convert_markdown_to_html(arabic_content)
        
        # Format content for the website
        if template:
            html_content = template.replace("{{ENGLISH_CONTENT}}", english_html)
            html_content = html_content.replace("{{ARABIC_CONTENT}}", arabic_html)
            html_content = html_content.replace("{{PAGE_NUMBER}}", str(page_num))
        else:
            # Create a basic HTML file if no template is provided
            html_content = f"""
            <div class="content-section" id="section-{page_num}">
                <span class="en">
                    {english_html}
                </span>
                <span class="ar">
                    {arabic_html}
                </span>
            </div>
            """
        
        # Save HTML file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Generated HTML for page {page_num}")
    
    print(f"\nHTML generation complete. Files saved to: {output_dir}")

def convert_markdown_to_html(markdown_text):
    """Convert markdown to HTML."""
    # This is a simple conversion - for production, use a proper markdown library
    # Replace headers
    html = markdown_text
    html = re.sub(r'# (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'## (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
    
    # Replace lists
    html = re.sub(r'^\* (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = re.sub(r'(<li>.*?</li>\n)+', r'<ul>\n\g<0></ul>\n', html, flags=re.DOTALL)
    
    # Replace bold text
    html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
    
    # Replace paragraphs
    html = re.sub(r'([^\n])\n([^\n])', r'\1<br>\2', html)
    paragraphs = re.split(r'\n\n+', html)
    html = ""
    for p in paragraphs:
        if not p.startswith('<h') and not p.startswith('<ul') and p.strip():
            html += f"<p>{p}</p>\n\n"
        else:
            html += p + "\n\n"
    
    return html

def create_index_page(summary_dir, output_file):
    """Create an index page with links to all summaries."""
    summary_files = sorted(glob.glob(os.path.join(summary_dir, "*_summary.md")))
    
    if not summary_files:
        print(f"No summary files found in {summary_dir}")
        return
    
    # Extract titles from summaries
    sections = []
    for file_path in summary_files:
        file_name = os.path.basename(file_path)
        match = re.search(r'page_(\d+)', file_name)
        
        if not match:
            continue
        
        page_num = int(match.group(1))
        
        # Read the file and extract the title
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        english_title = f"Page {page_num}"
        arabic_title = f"صفحة {page_num}"
        
        # Try to extract the title from the content
        en_match = re.search(r'# \[(.*?)\]', content)
        if en_match:
            english_title = en_match.group(1)
        
        ar_match = re.search(r'# \[(.*?)\]', content.split("# [")[1] if len(content.split("# [")) > 1 else "")
        if ar_match:
            arabic_title = ar_match.group(1)
        
        sections.append({
            "id": f"section-{page_num}",
            "page": page_num,
            "title_en": english_title,
            "title_ar": arabic_title,
            "link": f"page_{page_num:04d}.html"
        })
    
    # Create index HTML
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("""
        <div id="table-of-contents">
            <h3><span class="en">Table of Contents</span><span class="ar">جدول المحتويات</span></h3>
            <ul class="toc-list">
        """)
        
        for section in sections:
            f.write(f"""
                <li>
                    <a href="{section['link']}">
                        <span class="en">{section['title_en']}</span>
                        <span class="ar">{section['title_ar']}</span>
                    </a>
                </li>
            """)
        
        f.write("""
            </ul>
        </div>
        """)
    
    print(f"Index page created: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Summarize and process extracted PDF content")
    parser.add_argument("--input-dir", default="extracted_content/raw_text", help="Directory with extracted text files")
    parser.add_argument("--output-dir", default="extracted_content/summaries", help="Directory to save summarized content")
    parser.add_argument("--html-dir", default="html_content", help="Directory to save HTML files")
    parser.add_argument("--model", default="llama3", help="Ollama model to use")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker threads")
    parser.add_argument("--start-page", type=int, help="Starting page (1-indexed)")
    parser.add_argument("--end-page", type=int, help="Ending page (1-indexed)")
    parser.add_argument("--template", help="HTML template file")
    parser.add_argument("--skip-summarize", action="store_true", help="Skip summarization")
    parser.add_argument("--skip-html", action="store_true", help="Skip HTML generation")
    
    args = parser.parse_args()
    
    # Check if Ollama is running
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            print("Warning: Ollama API does not seem to be responding correctly")
    except:
        print("Error: Ollama does not appear to be running. Please start it with 'ollama serve'")
        return
    
    # Create output directories
    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs(args.html_dir, exist_ok=True)
    
    # Summarize content
    if not args.skip_summarize:
        summarize_files(
            args.input_dir, 
            args.output_dir, 
            args.model, 
            args.workers,
            args.start_page,
            args.end_page
        )
    
    # Generate HTML
    if not args.skip_html:
        generate_html_from_summaries(
            args.output_dir, 
            args.html_dir,
            args.template
        )
        
        # Create index page
        create_index_page(
            args.output_dir,
            os.path.join(args.html_dir, "index.html")
        )
    
    print("\nProcess complete!")
    print(f"Summarized content is in: {args.output_dir}")
    print(f"HTML content is in: {args.html_dir}")

if __name__ == "__main__":
    main()