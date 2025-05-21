#!/bin/bash
# Script to process PDF and update website content

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Ollama doesn't appear to be running. Please start Ollama first."
    echo "You can start it with: ollama serve"
    exit 1
fi

# Check if the model is available
MODEL=${2:-"llama3"}
if ! ollama list | grep -q "$MODEL"; then
    echo "Model $MODEL is not available. Please pull it with: ollama pull $MODEL"
    exit 1
fi

# Check if PyMuPDF is installed
pip3 show PyMuPDF > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing required Python packages..."
    pip3 install -r requirements.txt
fi

# Ensure PDF path is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <path-to-pdf> [model-name]"
    echo "Example: $0 \"منهاج تنافسي صيدلة تكريت 2025 FE.pdf\" llama3"
    exit 1
fi

PDF_PATH="$1"
if [ ! -f "$PDF_PATH" ]; then
    echo "PDF file not found: $PDF_PATH"
    exit 1
fi

# Create directories for extracted content
mkdir -p extracted_content/images

# Run the extraction and update process
echo "Starting PDF processing with Ollama ($MODEL)..."
python3 update_website.py "$PDF_PATH" --model "$MODEL"

echo ""
echo "PDF processing complete! The website has been updated with content from the PDF."
echo "You can now browse the website by opening index.html in your web browser."
echo ""
echo "To deploy the website to GitHub Pages:"
echo "1. Create a new repository on GitHub"
echo "2. Push the entire directory to the repository"
echo "3. Enable GitHub Pages in the repository settings"