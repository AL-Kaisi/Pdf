// Dynamic content loader for pharmacy curriculum
class ContentLoader {
    constructor() {
        this.textFiles = [];
        this.metadata = null;
        this.currentPages = [];
        this.searchIndex = new Map();
        this.init();
    }

    async init() {
        try {
            await this.loadMetadata();
            await this.preloadContent();
            this.buildSearchIndex();
            if (window.notificationManager) {
                window.notificationManager.show({
                    type: 'success',
                    title: '✅ Content Loaded',
                    message: `Successfully loaded ${this.metadata.total_pages} pages of study material`,
                    duration: 3000
                });
            }
        } catch (error) {
            console.error('Failed to load content:', error);
            if (window.notificationManager) {
                window.notificationManager.show({
                    type: 'error',
                    title: '❌ Loading Error',
                    message: 'Failed to load content. Please refresh the page.',
                    persistent: true
                });
            }
        }
    }

    async loadMetadata() {
        try {
            const response = await fetch('../extracted_content/raw_text/metadata.json');
            this.metadata = await response.json();
        } catch (error) {
            console.error('Failed to load metadata:', error);
            // Fallback metadata
            this.metadata = {
                total_pages: 406,
                page_info: Array.from({length: 406}, (_, i) => ({
                    page_number: i + 1,
                    text_file: `page_${String(i + 1).padStart(4, '0')}.txt`,
                    char_count: 3000,
                    word_count: 500
                }))
            };
        }
    }

    async loadPageContent(pageNumber) {
        if (this.textFiles[pageNumber]) {
            return this.textFiles[pageNumber];
        }

        try {
            const fileName = `page_${String(pageNumber).padStart(4, '0')}.txt`;
            const response = await fetch(`../extracted_content/raw_text/${fileName}`);
            const content = await response.text();
            this.textFiles[pageNumber] = content;
            return content;
        } catch (error) {
            console.error(`Failed to load page ${pageNumber}:`, error);
            return `Error loading page ${pageNumber}. Please try again later.`;
        }
    }

    async preloadContent() {
        // Preload first 10 pages for better performance
        const preloadPromises = [];
        for (let i = 1; i <= Math.min(10, this.metadata.total_pages); i++) {
            preloadPromises.push(this.loadPageContent(i));
        }
        await Promise.all(preloadPromises);
    }

    buildSearchIndex() {
        // Build search index from preloaded content
        Object.keys(this.textFiles).forEach(pageNum => {
            const content = this.textFiles[pageNum];
            const words = content.toLowerCase().split(/\s+/);
            words.forEach(word => {
                const cleanWord = word.replace(/[^\w\u0600-\u06FF]/g, '');
                if (cleanWord.length > 2) {
                    if (!this.searchIndex.has(cleanWord)) {
                        this.searchIndex.set(cleanWord, []);
                    }
                    if (!this.searchIndex.get(cleanWord).includes(parseInt(pageNum))) {
                        this.searchIndex.get(cleanWord).push(parseInt(pageNum));
                    }
                }
            });
        });
    }

    async searchContent(query, options = {}) {
        const {
            maxResults = 50,
            includePreview = true,
            fuzzyMatch = true
        } = options;

        const results = [];
        const queryWords = query.toLowerCase().split(/\s+/).map(word => 
            word.replace(/[^\w\u0600-\u06FF]/g, '')
        );

        // Search in search index first
        const matchingPages = new Set();
        queryWords.forEach(word => {
            if (this.searchIndex.has(word)) {
                this.searchIndex.get(word).forEach(pageNum => {
                    matchingPages.add(pageNum);
                });
            }
            
            // Fuzzy search
            if (fuzzyMatch) {
                this.searchIndex.forEach((pages, indexedWord) => {
                    if (indexedWord.includes(word) || word.includes(indexedWord)) {
                        pages.forEach(pageNum => matchingPages.add(pageNum));
                    }
                });
            }
        });

        // Load content for matching pages and calculate relevance
        for (const pageNum of Array.from(matchingPages).slice(0, maxResults)) {
            const content = await this.loadPageContent(pageNum);
            const relevance = this.calculateRelevance(content, queryWords);
            
            if (relevance > 0) {
                const result = {
                    pageNumber: pageNum,
                    relevance,
                    title: this.generatePageTitle(content, pageNum),
                    preview: includePreview ? this.generatePreview(content, queryWords) : '',
                    wordCount: this.metadata.page_info[pageNum - 1]?.word_count || 0,
                    link: this.generatePageLink(pageNum)
                };
                results.push(result);
            }
        }

        // Sort by relevance
        results.sort((a, b) => b.relevance - a.relevance);
        return results.slice(0, maxResults);
    }

    calculateRelevance(content, queryWords) {
        const lowerContent = content.toLowerCase();
        let score = 0;
        
        queryWords.forEach(word => {
            const matches = (lowerContent.match(new RegExp(word, 'g')) || []).length;
            score += matches;
        });
        
        return score;
    }

    generatePageTitle(content, pageNumber) {
        // Extract first meaningful line as title
        const lines = content.split('\n').filter(line => line.trim().length > 0);
        let title = lines[0]?.substring(0, 100) || `Page ${pageNumber}`;
        
        // Clean up title
        title = title.replace(/^\d+\s*/, ''); // Remove leading numbers
        title = title.replace(/[^\w\s\u0600-\u06FF]/g, ' '); // Clean special chars
        title = title.trim();
        
        return title || `صفحة ${pageNumber}`;
    }

    generatePreview(content, queryWords) {
        const sentences = content.split(/[.!?؟]/);
        let bestMatch = sentences[0] || '';
        let bestScore = 0;
        
        sentences.forEach(sentence => {
            if (sentence.trim().length < 20) return;
            
            let score = 0;
            queryWords.forEach(word => {
                if (sentence.toLowerCase().includes(word)) {
                    score++;
                }
            });
            
            if (score > bestScore) {
                bestScore = score;
                bestMatch = sentence;
            }
        });
        
        return bestMatch.trim().substring(0, 200) + (bestMatch.length > 200 ? '...' : '');
    }

    generatePageLink(pageNumber) {
        return `full_content.html#page-${pageNumber}`;
    }

    async getPageRange(startPage, endPage) {
        const pages = [];
        for (let i = startPage; i <= endPage && i <= this.metadata.total_pages; i++) {
            const content = await this.loadPageContent(i);
            pages.push({
                pageNumber: i,
                content,
                title: this.generatePageTitle(content, i),
                wordCount: this.metadata.page_info[i - 1]?.word_count || 0
            });
        }
        return pages;
    }

    getRandomPages(count = 5) {
        const randomPages = [];
        const totalPages = this.metadata.total_pages;
        
        for (let i = 0; i < count; i++) {
            const randomPage = Math.floor(Math.random() * totalPages) + 1;
            randomPages.push({
                pageNumber: randomPage,
                title: this.generatePageTitle('', randomPage),
                link: this.generatePageLink(randomPage),
                preview: `صفحة رقم ${randomPage} من منهج الصيدلة التنافسي`
            });
        }
        
        return randomPages;
    }

    getPageStats() {
        return {
            totalPages: this.metadata.total_pages,
            loadedPages: Object.keys(this.textFiles).length,
            totalWords: this.metadata.page_info.reduce((sum, page) => sum + (page.word_count || 0), 0),
            averageWordsPerPage: Math.round(
                this.metadata.page_info.reduce((sum, page) => sum + (page.word_count || 0), 0) / 
                this.metadata.total_pages
            )
        };
    }

    async exportContent(format = 'txt', pageRange = null) {
        const pages = pageRange ? 
            await this.getPageRange(pageRange.start, pageRange.end) :
            await this.getPageRange(1, this.metadata.total_pages);

        let content = '';
        
        if (format === 'txt') {
            content = pages.map(page => 
                `=== صفحة ${page.pageNumber} ===\n\n${page.content}\n\n`
            ).join('');
        } else if (format === 'json') {
            content = JSON.stringify(pages, null, 2);
        }

        // Create download
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `pharmacy-curriculum-${pageRange ? `pages-${pageRange.start}-${pageRange.end}` : 'complete'}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Enhanced page browser with real content
class EnhancedPageBrowser {
    constructor(contentLoader) {
        this.contentLoader = contentLoader;
        this.currentFilter = 'all';
        this.currentSearchTerm = '';
        this.displayedPages = [];
        this.pageSize = 20;
        this.currentPage = 1;
        this.categories = this.detectCategories();
    }

    detectCategories() {
        // Analyze content to detect categories
        return {
            'drug-design': ['تصميم', 'design', 'structure', 'molecular'],
            'pharmacology': ['أدوية', 'drug', 'pharmacology', 'receptor'],
            'chemistry': ['كيمياء', 'chemistry', 'chemical', 'reaction'],
            'calculations': ['حساب', 'calculation', 'formula', 'equation'],
            'toxicology': ['سميات', 'toxicity', 'poison', 'toxic'],
            'formulation': ['تركيب', 'formulation', 'tablet', 'capsule']
        };
    }

    async renderBrowser(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Create search and filter UI
        const searchHTML = this.createSearchInterface();
        const paginationHTML = this.createPaginationInterface();
        
        container.innerHTML = `
            ${searchHTML}
            <div id="search-results" class="search-results"></div>
            <div id="page-grid" class="page-grid"></div>
            ${paginationHTML}
        `;

        this.attachEventListeners();
        await this.loadAndDisplayPages();
    }

    createSearchInterface() {
        return `
            <div class="enhanced-search-box">
                <div class="search-input-container">
                    <input type="text" id="enhanced-search" placeholder="البحث في المحتوى...">
                    <button id="search-btn" class="search-btn">
                        <i class="fas fa-search"></i>
                    </button>
                </div>
                
                <div class="filter-controls">
                    <select id="category-filter" class="category-select">
                        <option value="all">جميع المواضيع</option>
                        <option value="drug-design">تصميم الأدوية</option>
                        <option value="pharmacology">علم الأدوية</option>
                        <option value="chemistry">الكيمياء الصيدلانية</option>
                        <option value="calculations">الحسابات الصيدلانية</option>
                        <option value="toxicology">علم السموم</option>
                        <option value="formulation">تركيب الأدوية</option>
                    </select>
                    
                    <select id="sort-by" class="sort-select">
                        <option value="relevance">الأكثر صلة</option>
                        <option value="page-number">رقم الصفحة</option>
                        <option value="word-count">عدد الكلمات</option>
                    </select>
                </div>

                <div class="quick-actions">
                    <button id="random-pages" class="quick-btn">
                        <i class="fas fa-random"></i> صفحات عشوائية
                    </button>
                    <button id="export-content" class="quick-btn">
                        <i class="fas fa-download"></i> تصدير المحتوى
                    </button>
                </div>
            </div>
        `;
    }

    createPaginationInterface() {
        return `
            <div class="pagination-container">
                <button id="prev-page" class="pagination-btn">
                    <i class="fas fa-chevron-right"></i> السابق
                </button>
                <span id="page-info" class="page-info"></span>
                <button id="next-page" class="pagination-btn">
                    التالي <i class="fas fa-chevron-left"></i>
                </button>
            </div>
        `;
    }

    attachEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('enhanced-search');
        const searchBtn = document.getElementById('search-btn');
        
        const performSearch = async () => {
            const query = searchInput.value.trim();
            this.currentSearchTerm = query;
            this.currentPage = 1;
            await this.loadAndDisplayPages();
        };

        searchInput.addEventListener('input', debounce(performSearch, 300));
        searchBtn.addEventListener('click', performSearch);

        // Filter controls
        document.getElementById('category-filter').addEventListener('change', async (e) => {
            this.currentFilter = e.target.value;
            this.currentPage = 1;
            await this.loadAndDisplayPages();
        });

        document.getElementById('sort-by').addEventListener('change', async () => {
            await this.loadAndDisplayPages();
        });

        // Quick actions
        document.getElementById('random-pages').addEventListener('click', () => {
            this.displayRandomPages();
        });

        document.getElementById('export-content').addEventListener('click', () => {
            this.showExportOptions();
        });

        // Pagination
        document.getElementById('prev-page').addEventListener('click', async () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                await this.loadAndDisplayPages();
            }
        });

        document.getElementById('next-page').addEventListener('click', async () => {
            this.currentPage++;
            await this.loadAndDisplayPages();
        });
    }

    async loadAndDisplayPages() {
        const loadingIndicator = this.showLoading();
        
        try {
            let pages = [];

            if (this.currentSearchTerm) {
                // Perform search
                const searchResults = await this.contentLoader.searchContent(this.currentSearchTerm, {
                    maxResults: 100,
                    includePreview: true
                });
                pages = searchResults;
            } else {
                // Load page range
                const startPage = (this.currentPage - 1) * this.pageSize + 1;
                const endPage = Math.min(startPage + this.pageSize - 1, this.contentLoader.metadata.total_pages);
                const pageRange = await this.contentLoader.getPageRange(startPage, endPage);
                
                pages = pageRange.map(page => ({
                    pageNumber: page.pageNumber,
                    title: page.title,
                    preview: page.content.substring(0, 200) + '...',
                    wordCount: page.wordCount,
                    link: this.contentLoader.generatePageLink(page.pageNumber),
                    relevance: 1
                }));
            }

            // Apply category filter
            if (this.currentFilter !== 'all') {
                pages = pages.filter(page => this.matchesCategory(page, this.currentFilter));
            }

            // Apply sorting
            const sortBy = document.getElementById('sort-by').value;
            this.sortPages(pages, sortBy);

            this.displayedPages = pages;
            this.renderPages(pages);
            this.updatePagination();
            
        } catch (error) {
            console.error('Error loading pages:', error);
            this.showError('خطأ في تحميل الصفحات');
        } finally {
            this.hideLoading(loadingIndicator);
        }
    }

    matchesCategory(page, category) {
        const keywords = this.categories[category] || [];
        const searchText = (page.title + ' ' + page.preview).toLowerCase();
        return keywords.some(keyword => searchText.includes(keyword.toLowerCase()));
    }

    sortPages(pages, sortBy) {
        switch (sortBy) {
            case 'page-number':
                pages.sort((a, b) => a.pageNumber - b.pageNumber);
                break;
            case 'word-count':
                pages.sort((a, b) => (b.wordCount || 0) - (a.wordCount || 0));
                break;
            case 'relevance':
            default:
                pages.sort((a, b) => (b.relevance || 0) - (a.relevance || 0));
                break;
        }
    }

    renderPages(pages) {
        const grid = document.getElementById('page-grid');
        const searchResults = document.getElementById('search-results');
        
        if (this.currentSearchTerm && pages.length > 0) {
            searchResults.innerHTML = `
                <div class="search-summary">
                    <i class="fas fa-search"></i>
                    عثر على ${pages.length} نتيجة للبحث عن "${this.currentSearchTerm}"
                </div>
            `;
            searchResults.style.display = 'block';
        } else {
            searchResults.style.display = 'none';
        }

        if (pages.length === 0) {
            grid.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <h3>لم يتم العثور على نتائج</h3>
                    <p>حاول تعديل مصطلحات البحث أو الفلاتر</p>
                </div>
            `;
            return;
        }

        grid.innerHTML = pages.map(page => `
            <div class="enhanced-page-card" data-page="${page.pageNumber}">
                <div class="page-header">
                    <div class="page-number">صفحة ${page.pageNumber}</div>
                    <div class="page-stats">
                        <span class="word-count">${page.wordCount || 0} كلمة</span>
                        ${page.relevance > 1 ? `<span class="relevance-score">صلة: ${Math.round(page.relevance * 10)}/10</span>` : ''}
                    </div>
                </div>
                
                <h3 class="page-title">${page.title}</h3>
                <div class="page-preview">${page.preview}</div>
                
                <div class="page-actions">
                    <a href="${page.link}" class="view-btn primary">
                        <i class="fas fa-eye"></i> عرض الصفحة
                    </a>
                    <button class="bookmark-btn" onclick="bookmarkPage(${page.pageNumber})">
                        <i class="fas fa-bookmark"></i>
                    </button>
                    <button class="share-btn" onclick="sharePage(${page.pageNumber})">
                        <i class="fas fa-share"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    updatePagination() {
        const totalPages = Math.ceil(this.contentLoader.metadata.total_pages / this.pageSize);
        const pageInfo = document.getElementById('page-info');
        
        pageInfo.textContent = `صفحة ${this.currentPage} من ${totalPages}`;
        
        document.getElementById('prev-page').disabled = this.currentPage === 1;
        document.getElementById('next-page').disabled = this.currentPage >= totalPages;
    }

    displayRandomPages() {
        const randomPages = this.contentLoader.getRandomPages(this.pageSize);
        this.renderPages(randomPages);
        
        document.getElementById('search-results').innerHTML = `
            <div class="search-summary">
                <i class="fas fa-random"></i>
                صفحات عشوائية من المنهج
            </div>
        `;
        document.getElementById('search-results').style.display = 'block';
    }

    showExportOptions() {
        if (window.notificationManager) {
            window.notificationManager.show({
                type: 'info',
                title: '📋 تصدير المحتوى',
                message: 'اختر نوع التصدير والنطاق المطلوب',
                persistent: true,
                actions: [
                    {
                        text: 'تصدير الكل',
                        action: () => this.contentLoader.exportContent('txt')
                    },
                    {
                        text: 'تصدير النتائج الحالية',
                        action: () => this.exportCurrentResults()
                    }
                ]
            });
        }
    }

    showLoading() {
        const loading = document.createElement('div');
        loading.className = 'loading-overlay';
        loading.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
                <p>جاري التحميل...</p>
            </div>
        `;
        document.body.appendChild(loading);
        return loading;
    }

    hideLoading(loadingElement) {
        if (loadingElement && loadingElement.parentNode) {
            loadingElement.parentNode.removeChild(loadingElement);
        }
    }

    showError(message) {
        if (window.notificationManager) {
            window.notificationManager.show({
                type: 'error',
                title: '❌ خطأ',
                message,
                duration: 5000
            });
        }
    }
}

// Utility function for debouncing
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Global functions for page actions
window.bookmarkPage = function(pageNumber) {
    const bookmarks = JSON.parse(localStorage.getItem('bookmarked_pages') || '[]');
    if (!bookmarks.includes(pageNumber)) {
        bookmarks.push(pageNumber);
        localStorage.setItem('bookmarked_pages', JSON.stringify(bookmarks));
        
        if (window.notificationManager) {
            window.notificationManager.show({
                type: 'success',
                title: '🔖 تم الحفظ',
                message: `تم حفظ الصفحة ${pageNumber} في المفضلة`,
                duration: 2000
            });
        }
    }
};

window.sharePage = function(pageNumber) {
    const url = `${window.location.origin}${window.location.pathname}#page-${pageNumber}`;
    
    if (navigator.share) {
        navigator.share({
            title: `صفحة ${pageNumber} - منهج صيدلة تكريت`,
            url: url
        });
    } else {
        navigator.clipboard.writeText(url).then(() => {
            if (window.notificationManager) {
                window.notificationManager.show({
                    type: 'success',
                    title: '📋 تم النسخ',
                    message: 'تم نسخ رابط الصفحة',
                    duration: 2000
                });
            }
        });
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    window.contentLoader = new ContentLoader();
    window.pageBrowser = new EnhancedPageBrowser(window.contentLoader);
    
    // Initialize browser if page grid exists
    const pageGrid = document.getElementById('pageGrid');
    if (pageGrid) {
        await window.pageBrowser.renderBrowser('pageGrid');
    }
});