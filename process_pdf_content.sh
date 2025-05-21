#!/bin/bash
# Master script to process PDF content, extract text and images,
# summarize content, and update the website.

# Configuration
PDF_FILE="منهاج تنافسي صيدلة تكريت 2025 FE.pdf"
EXTRACTED_DIR="extracted_content"
HTML_OUTPUT_DIR="website_content"
OLLAMA_MODEL="llama3"
BATCH_SIZE=10  # Number of pages to process in each batch
MAX_WORKERS=1  # Number of parallel workers for summarization

# Check if Python and required packages are installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "Error: Ollama doesn't appear to be running. Please start Ollama first."
    echo "You can start it with: ollama serve"
    exit 1
fi

# Check if the model is available
if ! curl -s http://localhost:11434/api/tags | grep -q "\"$OLLAMA_MODEL\""; then
    echo "Model $OLLAMA_MODEL is not available. Pulling it now..."
    ollama pull $OLLAMA_MODEL
fi

# Install required Python packages if not already installed
echo "Checking required Python packages..."
pip3 install PyMuPDF pillow requests

# Step 1: Extract text and images from the PDF
echo "Step 1: Extracting content from PDF..."
python3 pdf_extractor.py "$PDF_FILE" --output-dir "$EXTRACTED_DIR"

# Get total page count
TOTAL_PAGES=$(grep "total_pages" "$EXTRACTED_DIR/raw_text/metadata.json" | sed 's/[^0-9]//g')
echo "Total pages in PDF: $TOTAL_PAGES"

# Step 2: Process content in batches
echo "Step 2: Processing content in batches of $BATCH_SIZE pages..."

# Create a template file for HTML generation
cat > template.html << 'EOL'
<div class="content-section" id="section-{{PAGE_NUMBER}}">
    <span class="en">
        {{ENGLISH_CONTENT}}
    </span>
    <span class="ar">
        {{ARABIC_CONTENT}}
    </span>
</div>
EOL

# Process batches
for ((i=1; i<=$TOTAL_PAGES; i+=$BATCH_SIZE)); do
    end=$((i+$BATCH_SIZE-1))
    if [ $end -gt $TOTAL_PAGES ]; then
        end=$TOTAL_PAGES
    fi
    
    echo "Processing batch: pages $i to $end"
    python3 summarize_content.py \
        --input-dir "$EXTRACTED_DIR/raw_text" \
        --output-dir "$EXTRACTED_DIR/summaries" \
        --html-dir "$HTML_OUTPUT_DIR" \
        --model "$OLLAMA_MODEL" \
        --workers $MAX_WORKERS \
        --start-page $i \
        --end-page $end \
        --template template.html
    
    # Small pause between batches to avoid rate limiting
    echo "Batch complete. Pausing before next batch..."
    sleep 5
done

# Step 3: Copy images to the website directory
echo "Step 3: Copying images to the website..."
mkdir -p "$HTML_OUTPUT_DIR/images"
cp -r "$EXTRACTED_DIR/raw_images"/* "$HTML_OUTPUT_DIR/images/"

# Step 4: Create entry points for the website
echo "Step 4: Creating entry points for the website..."

# Create index.html that links to the first page
cat > "$HTML_OUTPUT_DIR/index.html" << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tikrit Pharmacy Curriculum - Complete Study Materials</title>
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
                    <li><a href="../en/index.html"><i class="fas fa-book"></i> <span class="en">English</span><span class="ar">الإنجليزية</span></a></li>
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
                    <h2><span class="en">Pharmacy Curriculum - Complete Content</span><span class="ar">منهج الصيدلة - المحتوى الكامل</span></h2>
                    
                    <div class="note-box">
                        <strong><span class="en">Note:</span><span class="ar">ملاحظة:</span></strong>
                        <span class="en">This page contains all content from the Tikrit Pharmacy Competitive Curriculum PDF, summarized and organized for easier studying.</span>
                        <span class="ar">تحتوي هذه الصفحة على كل محتويات منهج صيدلة تكريت التنافسي، ملخصة ومنظمة لتسهيل الدراسة.</span>
                    </div>
                    
                    <!-- Table of Contents will be included here -->
                    <!-- Content from index.html will be included here -->
                    
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
</html>
EOL

# Copy table of contents to index.html
sed -i '' -e '/<!-- Table of Contents will be included here -->/r '"$HTML_OUTPUT_DIR/index.html" "$HTML_OUTPUT_DIR/index.html"

# Final step: Update the main website with the new content
echo "Step 5: Updating website structure..."

# Create directories for en and ar content if they don't exist
mkdir -p en/content
mkdir -p ar/content

# Copy the HTML content to the website directories
cp -r "$HTML_OUTPUT_DIR"/* en/content/
cp -r "$HTML_OUTPUT_DIR"/* ar/content/

echo ""
echo "Process complete! The PDF content has been extracted and summarized."
echo "Next steps:"
echo "1. Review the generated content in $HTML_OUTPUT_DIR"
echo "2. Update the website with the new content"
echo "3. Deploy to GitHub Pages"
echo ""