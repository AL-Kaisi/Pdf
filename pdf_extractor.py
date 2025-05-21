#!/usr/bin/env python3
"""
Comprehensive PDF extraction tool for extracting text and images from a large PDF
and storing them in a structured format.
"""

import os
import argparse
import json
from datetime import datetime
import fitz  # PyMuPDF
from PIL import Image
import io
import re

def create_directory_structure(base_dir):
    """Create directory structure for extracted content."""
    directories = [
        "raw_text",
        "raw_images",
        "processed_text",
        "processed_images",
        "summaries",
        "translations"
    ]
    
    for directory in directories:
        os.makedirs(os.path.join(base_dir, directory), exist_ok=True)
    
    return {dir_name: os.path.join(base_dir, dir_name) for dir_name in directories}

def extract_text_from_pdf(pdf_path, output_dir, start_page=None, end_page=None):
    """Extract text from PDF and save each page as a separate file."""
    print(f"Extracting text from: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        print(f"Total pages in document: {total_pages}")
        
        # Validate page range
        if start_page is None:
            start_page = 0
        else:
            start_page = max(0, min(start_page, total_pages - 1))
            
        if end_page is None:
            end_page = total_pages - 1
        else:
            end_page = max(0, min(end_page, total_pages - 1))
            
        print(f"Processing pages {start_page+1} to {end_page+1}")
        
        # Metadata for extracted content
        metadata = {
            "filename": os.path.basename(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "total_pages": total_pages,
            "processed_pages": end_page - start_page + 1,
            "page_info": []
        }
        
        # Extract text page by page
        for page_num in range(start_page, end_page + 1):
            print(f"Processing page {page_num+1}/{end_page+1}...", end="\r")
            
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Clean the text
            text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
            text = text.strip()
            
            # Save the text to a file
            output_file = os.path.join(output_dir, f"page_{page_num+1:04d}.txt")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Add page info to metadata
            metadata["page_info"].append({
                "page_number": page_num + 1,
                "text_file": os.path.basename(output_file),
                "char_count": len(text),
                "word_count": len(text.split())
            })
        
        # Save metadata
        metadata_file = os.path.join(output_dir, "metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"\nText extraction completed. Files saved to: {output_dir}")
        return metadata
        
    except Exception as e:
        print(f"Error extracting text: {e}")
        return None

def extract_images_from_pdf(pdf_path, output_dir, start_page=None, end_page=None):
    """Extract images from PDF and save them."""
    print(f"Extracting images from: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Validate page range
        if start_page is None:
            start_page = 0
        else:
            start_page = max(0, min(start_page, total_pages - 1))
            
        if end_page is None:
            end_page = total_pages - 1
        else:
            end_page = max(0, min(end_page, total_pages - 1))
        
        # Metadata for extracted images
        metadata = {
            "filename": os.path.basename(pdf_path),
            "extraction_date": datetime.now().isoformat(),
            "total_pages": total_pages,
            "processed_pages": end_page - start_page + 1,
            "image_info": []
        }
        
        image_count = 0
        
        # Extract images page by page
        for page_num in range(start_page, end_page + 1):
            print(f"Processing page {page_num+1}/{end_page+1} for images...", end="\r")
            
            page = doc.load_page(page_num)
            image_list = page.get_images(full=True)
            
            page_image_count = 0
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # Filter small images (likely icons, bullets, etc.)
                    img_obj = Image.open(io.BytesIO(image_bytes))
                    width, height = img_obj.size
                    
                    if width < 50 or height < 50:  # Filter very small images
                        continue
                        
                    # Save the image
                    image_filename = f"page_{page_num+1:04d}_img_{img_index+1:03d}.{image_ext}"
                    image_path = os.path.join(output_dir, image_filename)
                    
                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)
                    
                    # Add image info to metadata
                    metadata["image_info"].append({
                        "page_number": page_num + 1,
                        "image_file": image_filename,
                        "width": width,
                        "height": height,
                        "format": image_ext
                    })
                    
                    image_count += 1
                    page_image_count += 1
                    
                except Exception as img_error:
                    print(f"\nError extracting image from page {page_num+1}: {img_error}")
            
            # Try to extract any images drawn on the page (diagrams, charts)
            pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI rendering
            img_obj = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            if page_image_count == 0 and width > 100 and height > 100:
                # If no images were extracted, save the whole page as an image
                image_filename = f"page_{page_num+1:04d}_fullpage.png"
                image_path = os.path.join(output_dir, image_filename)
                img_obj.save(image_path)
                
                metadata["image_info"].append({
                    "page_number": page_num + 1,
                    "image_file": image_filename,
                    "width": pix.width,
                    "height": pix.height,
                    "format": "png",
                    "type": "full_page"
                })
                
                image_count += 1
        
        # Save metadata
        metadata_file = os.path.join(output_dir, "image_metadata.json")
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
            
        print(f"\nImage extraction completed. {image_count} images saved to: {output_dir}")
        return metadata
        
    except Exception as e:
        print(f"Error extracting images: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Extract content from PDF files")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("--output-dir", default="extracted_content", help="Directory to save extracted content")
    parser.add_argument("--start-page", type=int, help="Starting page (1-indexed)")
    parser.add_argument("--end-page", type=int, help="Ending page (1-indexed)")
    parser.add_argument("--skip-text", action="store_true", help="Skip text extraction")
    parser.add_argument("--skip-images", action="store_true", help="Skip image extraction")
    
    args = parser.parse_args()
    
    # Adjust page numbers to 0-indexed
    start_page = args.start_page - 1 if args.start_page else None
    end_page = args.end_page - 1 if args.end_page else None
    
    # Create directory structure
    directories = create_directory_structure(args.output_dir)
    
    # Extract content
    if not args.skip_text:
        extract_text_from_pdf(args.pdf_path, directories["raw_text"], start_page, end_page)
    
    if not args.skip_images:
        extract_images_from_pdf(args.pdf_path, directories["raw_images"], start_page, end_page)
    
    print("Extraction complete!")
    print(f"Raw text files are in: {directories['raw_text']}")
    print(f"Raw image files are in: {directories['raw_images']}")
    print("\nNow you can process and summarize the extracted content.")

if __name__ == "__main__":
    main()