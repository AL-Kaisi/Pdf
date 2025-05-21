#!/usr/bin/env python3
"""
PDF extraction script using Ollama for parsing and extracting content from a PDF.
This script will extract text and attempt to identify diagrams/images.
"""

import argparse
import json
import os
import requests
import fitz  # PyMuPDF
import tempfile
from PIL import Image
import io
import base64

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF using PyMuPDF."""
    text_by_page = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            text_by_page.append(text)
        return text_by_page
    except Exception as e:
        print(f"Error extracting text: {e}")
        return []

def extract_images_from_pdf(pdf_path, output_dir):
    """Extract images from a PDF using PyMuPDF."""
    image_paths = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Check if it's a diagram (we'll use size as a simple heuristic)
                # You might want to improve this with more sophisticated checks
                img_obj = Image.open(io.BytesIO(image_bytes))
                width, height = img_obj.size
                if width > 100 and height > 100:  # Simple size filter
                    image_filename = f"page{page_num+1}_img{img_index}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    image_paths.append(image_path)
        
        return image_paths
    except Exception as e:
        print(f"Error extracting images: {e}")
        return []

def analyze_with_ollama(text, model="llama3"):
    """Process text with Ollama API."""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": f"""
                You are a pharmacy curriculum expert. Analyze the following text from a pharmacy curriculum PDF 
                and identify key concepts, definitions, and important information. 
                Structure your response in a clean, organized format with headers, bullet points for key concepts,
                and clear explanations. If you detect any technical terms, provide brief explanations.
                
                Here's the text:
                
                {text}
                
                Format your response in both English and Arabic. First provide the English version,
                then add "ARABIC TRANSLATION:" and provide the Arabic translation of the same content.
                """
            }
        )
        
        if response.status_code == 200:
            result = response.text
            # Process the streaming response
            lines = result.strip().split('\n')
            full_text = ""
            
            for line in lines:
                try:
                    data = json.loads(line)
                    if "response" in data:
                        full_text += data["response"]
                except:
                    continue
                    
            return full_text
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error connecting to Ollama: {e}"

def analyze_image_with_ollama(image_path, model="llama3"):
    """Analyze an image with Ollama's vision capabilities."""
    try:
        # Read image and convert to base64
        with open(image_path, "rb") as img_file:
            img_bytes = img_file.read()
        
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": """
                Analyze this diagram from a pharmacy curriculum. Describe what it shows in detail.
                Provide your description in both English and Arabic.
                """,
                "images": [img_base64]
            }
        )
        
        if response.status_code == 200:
            result = response.text
            lines = result.strip().split('\n')
            full_text = ""
            
            for line in lines:
                try:
                    data = json.loads(line)
                    if "response" in data:
                        full_text += data["response"]
                except:
                    continue
                    
            return full_text
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error analyzing image with Ollama: {e}"

def save_result_to_file(content, filename):
    """Save the extracted content to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved content to {filename}")

def main():
    parser = argparse.ArgumentParser(description="Extract and analyze PDF content using Ollama")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--model", default="llama3", help="Ollama model to use (default: llama3)")
    parser.add_argument("--output-dir", default="extracted_content", help="Directory to save extracted content")
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    images_dir = os.path.join(args.output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    # Extract text from PDF
    print(f"Extracting text from {args.pdf_path}...")
    text_by_page = extract_text_from_pdf(args.pdf_path)
    
    # Process each page with Ollama
    for i, page_text in enumerate(text_by_page):
        if not page_text.strip():
            continue
            
        print(f"Processing page {i+1} with Ollama...")
        analyzed_text = analyze_with_ollama(page_text, args.model)
        
        # Save the analyzed text
        output_file = os.path.join(args.output_dir, f"page_{i+1}_content.md")
        save_result_to_file(analyzed_text, output_file)
    
    # Extract and analyze images
    print("Extracting images from PDF...")
    image_paths = extract_images_from_pdf(args.pdf_path, images_dir)
    
    for i, img_path in enumerate(image_paths):
        print(f"Analyzing image {i+1} with Ollama...")
        image_analysis = analyze_image_with_ollama(img_path, args.model)
        
        # Save the image analysis
        img_output_file = os.path.join(args.output_dir, f"image_{i+1}_analysis.md")
        save_result_to_file(image_analysis, img_output_file)
    
    print(f"\nExtraction complete! Results saved to {args.output_dir}/")
    print(f"Total pages processed: {len(text_by_page)}")
    print(f"Total images extracted: {len(image_paths)}")

if __name__ == "__main__":
    main()