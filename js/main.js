document.addEventListener('DOMContentLoaded', function() {
    // Language toggle functionality
    const toggleButton = document.getElementById('toggleLanguage');
    const toggleText = toggleButton.querySelector('.toggle-text');
    
    if (toggleButton) {
        toggleButton.addEventListener('click', function() {
            document.body.classList.toggle('ar-mode');
            
            // Update toggle button text
            if (document.body.classList.contains('ar-mode')) {
                toggleText.textContent = 'English';
            } else {
                toggleText.textContent = 'عربي';
            }
            
            // Save language preference
            localStorage.setItem('language', document.body.classList.contains('ar-mode') ? 'ar' : 'en');
        });
    }
    
    // Check for saved language preference
    const savedLanguage = localStorage.getItem('language');
    if (savedLanguage === 'ar') {
        document.body.classList.add('ar-mode');
        toggleText.textContent = 'English';
    }
    
    // Chapter navigation functionality
    const prevButton = document.querySelector('.content-navigation .btn.secondary');
    const nextButton = document.querySelector('.content-navigation .btn.primary');
    
    if (prevButton && nextButton) {
        const sections = document.querySelectorAll('.content-section[id^="section-"]');
        
        if (sections.length > 0) {
            // Get current section from URL hash or default to first section
            let currentSectionId = window.location.hash || `#${sections[0].id}`;
            let currentSectionElement = document.querySelector(currentSectionId);
            
            // If hash doesn't match any section, default to first section
            if (!currentSectionElement) {
                currentSectionId = `#${sections[0].id}`;
                currentSectionElement = sections[0];
            }
            
            // Extract section number
            const currentSectionNumber = parseInt(currentSectionId.split('-')[1]);
            
            // Update navigation links
            if (currentSectionNumber === 1) {
                prevButton.classList.add('disabled');
                prevButton.href = '#';
            } else {
                prevButton.classList.remove('disabled');
                prevButton.href = `#section-${currentSectionNumber - 1}`;
            }
            
            if (currentSectionNumber === sections.length) {
                nextButton.classList.add('disabled');
                nextButton.href = '#';
            } else {
                nextButton.classList.remove('disabled');
                nextButton.href = `#section-${currentSectionNumber + 1}`;
            }
            
            // Add click event listeners to navigation buttons
            nextButton.addEventListener('click', function(e) {
                if (!this.classList.contains('disabled')) {
                    window.location.hash = this.getAttribute('href');
                    
                    // Update buttons after clicking
                    const newSectionId = this.getAttribute('href');
                    const newSectionNumber = parseInt(newSectionId.split('-')[1]);
                    
                    if (newSectionNumber === 1) {
                        prevButton.classList.add('disabled');
                        prevButton.href = '#';
                    } else {
                        prevButton.classList.remove('disabled');
                        prevButton.href = `#section-${newSectionNumber - 1}`;
                    }
                    
                    if (newSectionNumber === sections.length) {
                        nextButton.classList.add('disabled');
                        nextButton.href = '#';
                    } else {
                        nextButton.classList.remove('disabled');
                        nextButton.href = `#section-${newSectionNumber + 1}`;
                    }
                }
                e.preventDefault();
            });
            
            prevButton.addEventListener('click', function(e) {
                if (!this.classList.contains('disabled')) {
                    window.location.hash = this.getAttribute('href');
                    
                    // Update buttons after clicking
                    const newSectionId = this.getAttribute('href');
                    const newSectionNumber = parseInt(newSectionId.split('-')[1]);
                    
                    if (newSectionNumber === 1) {
                        prevButton.classList.add('disabled');
                        prevButton.href = '#';
                    } else {
                        prevButton.classList.remove('disabled');
                        prevButton.href = `#section-${newSectionNumber - 1}`;
                    }
                    
                    if (newSectionNumber === sections.length) {
                        nextButton.classList.add('disabled');
                        nextButton.href = '#';
                    } else {
                        nextButton.classList.remove('disabled');
                        nextButton.href = `#section-${newSectionNumber + 1}`;
                    }
                }
                e.preventDefault();
            });
        }
    }
    
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Table of contents generation (if present)
    const tocContainer = document.getElementById('table-of-contents');
    if (tocContainer) {
        const headings = document.querySelectorAll('.content-container h2, .content-container h3');
        if (headings.length > 0) {
            const toc = document.createElement('ul');
            toc.className = 'toc-list';
            
            headings.forEach((heading, index) => {
                // Add ID to the heading if it doesn't have one
                if (!heading.id) {
                    heading.id = `heading-${index}`;
                }
                
                const listItem = document.createElement('li');
                listItem.className = heading.tagName.toLowerCase();
                
                const link = document.createElement('a');
                link.href = `#${heading.id}`;
                link.innerHTML = heading.innerHTML;
                
                listItem.appendChild(link);
                toc.appendChild(listItem);
            });
            
            tocContainer.appendChild(toc);
        }
    }
    
    // Make PDF viewer responsive (if present)
    const pdfViewer = document.getElementById('pdf-viewer');
    if (pdfViewer) {
        // Adjust height based on window size
        function adjustPdfHeight() {
            const windowHeight = window.innerHeight;
            const headerHeight = document.querySelector('header').offsetHeight;
            const footerHeight = document.querySelector('footer').offsetHeight;
            const containerPadding = 80; // Account for container padding
            
            pdfViewer.style.height = `${windowHeight - headerHeight - footerHeight - containerPadding}px`;
        }
        
        // Initial adjustment and on resize
        adjustPdfHeight();
        window.addEventListener('resize', adjustPdfHeight);
    }
    
    // Mobile navigation toggle (for smaller screens)
    const menuToggle = document.getElementById('menu-toggle');
    const navItems = document.querySelector('nav ul');
    
    if (menuToggle && navItems) {
        menuToggle.addEventListener('click', function() {
            navItems.classList.toggle('show');
            menuToggle.classList.toggle('active');
        });
    }
});