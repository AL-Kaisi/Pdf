// Enhanced notification system for the pharmacy curriculum website

class NotificationManager {
    constructor() {
        this.notifications = [];
        this.container = null;
        this.init();
    }

    init() {
        // Create notification container
        this.container = document.createElement('div');
        this.container.id = 'notification-container';
        this.container.className = 'notification-container';
        document.body.appendChild(this.container);

        // Add CSS styles
        this.addStyles();
        
        // Show welcome notification
        this.showWelcomeMessage();
        
        // Track user progress
        this.trackProgress();
    }

    addStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            }

            .notification {
                background: white;
                border-radius: 12px;
                padding: 1rem 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 8px 32px rgba(0,0,0,0.12);
                border-left: 4px solid #007bff;
                transform: translateX(450px);
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                opacity: 0;
                backdrop-filter: blur(10px);
                position: relative;
                overflow: hidden;
            }

            .notification.show {
                transform: translateX(0);
                opacity: 1;
            }

            .notification.success {
                border-left-color: #28a745;
                background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            }

            .notification.info {
                border-left-color: #17a2b8;
                background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
            }

            .notification.warning {
                border-left-color: #ffc107;
                background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
            }

            .notification.error {
                border-left-color: #dc3545;
                background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            }

            .notification-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 0.5rem;
            }

            .notification-icon {
                font-size: 1.2rem;
                margin-right: 0.5rem;
            }

            .notification-title {
                font-weight: 600;
                font-size: 1rem;
                color: #2c3e50;
                display: flex;
                align-items: center;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                opacity: 0.5;
                transition: opacity 0.2s;
                color: #6c757d;
            }

            .notification-close:hover {
                opacity: 1;
            }

            .notification-body {
                color: #495057;
                line-height: 1.4;
                font-size: 0.9rem;
            }

            .notification-actions {
                margin-top: 1rem;
                display: flex;
                gap: 0.5rem;
            }

            .notification-btn {
                padding: 0.5rem 1rem;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 0.85rem;
                font-weight: 500;
                transition: all 0.2s;
            }

            .notification-btn.primary {
                background: #007bff;
                color: white;
            }

            .notification-btn.primary:hover {
                background: #0056b3;
            }

            .notification-btn.secondary {
                background: #6c757d;
                color: white;
            }

            .notification-btn.secondary:hover {
                background: #545b62;
            }

            .progress-indicator {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 3px;
                background: rgba(0,123,255,0.3);
                transition: width 0.1s linear;
            }

            .study-progress {
                background: white;
                border-radius: 12px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }

            .progress-bar-container {
                background: #e9ecef;
                border-radius: 10px;
                height: 8px;
                overflow: hidden;
                margin: 1rem 0;
            }

            .progress-bar-fill {
                height: 100%;
                background: linear-gradient(90deg, #007bff, #28a745);
                transition: width 0.3s ease;
                border-radius: 10px;
            }

            .progress-stats {
                display: flex;
                justify-content: space-between;
                font-size: 0.85rem;
                color: #6c757d;
                margin-top: 0.5rem;
            }

            @media (max-width: 768px) {
                .notification-container {
                    right: 10px;
                    left: 10px;
                    max-width: none;
                }
                
                .notification {
                    transform: translateY(-100px);
                }
                
                .notification.show {
                    transform: translateY(0);
                }
            }

            .floating-help {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                cursor: pointer;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
                transition: all 0.3s ease;
                z-index: 9999;
            }

            .floating-help:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 25px rgba(102, 126, 234, 0.4);
            }

            .floating-help i {
                font-size: 1.5rem;
            }
        `;
        document.head.appendChild(style);
    }

    show(options) {
        const {
            type = 'info',
            title,
            message,
            duration = 5000,
            actions = [],
            persistent = false
        } = options;

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        
        const iconMap = {
            success: 'fas fa-check-circle',
            info: 'fas fa-info-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle'
        };

        notification.innerHTML = `
            <div class="notification-header">
                <div class="notification-title">
                    <i class="notification-icon ${iconMap[type]}"></i>
                    ${title}
                </div>
                <button class="notification-close">&times;</button>
            </div>
            <div class="notification-body">${message}</div>
            ${actions.length > 0 ? `
                <div class="notification-actions">
                    ${actions.map(action => `
                        <button class="notification-btn ${action.type || 'primary'}" 
                                onclick="${action.action}">${action.text}</button>
                    `).join('')}
                </div>
            ` : ''}
            ${!persistent && duration > 0 ? '<div class="progress-indicator"></div>' : ''}
        `;

        this.container.appendChild(notification);

        // Show animation
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Progress indicator
        if (!persistent && duration > 0) {
            const indicator = notification.querySelector('.progress-indicator');
            let progress = 0;
            const increment = 100 / (duration / 100);
            
            const progressInterval = setInterval(() => {
                progress += increment;
                if (indicator) {
                    indicator.style.width = progress + '%';
                }
                if (progress >= 100) {
                    clearInterval(progressInterval);
                    this.remove(notification);
                }
            }, 100);
        }

        // Close button
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.remove(notification);
        });

        return notification;
    }

    remove(notification) {
        notification.style.transform = 'translateX(450px)';
        notification.style.opacity = '0';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 400);
    }

    showWelcomeMessage() {
        const isFirstVisit = !localStorage.getItem('pharmacy_visited');
        
        if (isFirstVisit) {
            setTimeout(() => {
                this.show({
                    type: 'success',
                    title: '🎉 مرحباً بك في منهج صيدلة تكريت',
                    message: 'اكتشف مواد دراسية شاملة مع ملخصات باللغتين العربية والإنجليزية. استخدم أدوات البحث والتصفح للعثور على المواضيع بسرعة.',
                    duration: 8000,
                    actions: [
                        {
                            text: 'ابدأ التصفح',
                            action: "window.location.href='en/browse.html'"
                        },
                        {
                            text: 'تجاهل',
                            type: 'secondary',
                            action: 'void(0)'
                        }
                    ]
                });
            }, 1000);
            
            localStorage.setItem('pharmacy_visited', 'true');
        }
    }

    trackProgress() {
        // Track pages visited
        const visitedPages = JSON.parse(localStorage.getItem('visited_pages') || '[]');
        const currentPage = window.location.pathname;
        
        if (!visitedPages.includes(currentPage)) {
            visitedPages.push(currentPage);
            localStorage.setItem('visited_pages', JSON.stringify(visitedPages));
            
            // Show progress notification
            if (visitedPages.length > 1 && visitedPages.length % 5 === 0) {
                this.show({
                    type: 'info',
                    title: '📚 تقدم رائع!',
                    message: `لقد زرت ${visitedPages.length} صفحة. استمر في الدراسة!`,
                    duration: 4000
                });
            }
        }
    }

    showStudyReminder() {
        const lastStudy = localStorage.getItem('last_study_time');
        const now = new Date().getTime();
        const dayInMs = 24 * 60 * 60 * 1000;
        
        if (!lastStudy || (now - parseInt(lastStudy)) > dayInMs) {
            this.show({
                type: 'warning',
                title: '⏰ تذكير للدراسة',
                message: 'لم تدرس منذ فترة. الممارسة المنتظمة تحسن الذاكرة والفهم.',
                persistent: true,
                actions: [
                    {
                        text: 'ابدأ الدراسة الآن',
                        action: "window.location.href='en/full_content.html'"
                    },
                    {
                        text: 'تذكيرني لاحقاً',
                        type: 'secondary',
                        action: `localStorage.setItem('last_study_time', '${now}'); this.remove(this.closest('.notification'))`
                    }
                ]
            });
        }
    }

    addFloatingHelp() {
        const helpButton = document.createElement('div');
        helpButton.className = 'floating-help';
        helpButton.innerHTML = '<i class="fas fa-question"></i>';
        
        helpButton.addEventListener('click', () => {
            this.show({
                type: 'info',
                title: '💡 نصائح للاستخدام',
                message: `
                    <strong>كيفية استخدام الموقع:</strong><br>
                    • استخدم أزرار التنقل في الأعلى<br>
                    • اضغط على "تصفح" لرؤية جميع الصفحات<br>
                    • استخدم البحث للعثور على مواضيع محددة<br>
                    • يمكنك التبديل بين العربية والإنجليزية
                `,
                duration: 10000,
                actions: [
                    {
                        text: 'تصفح الصفحات',
                        action: "window.location.href='en/browse.html'"
                    }
                ]
            });
        });
        
        document.body.appendChild(helpButton);
    }

    showConnectionStatus() {
        if (!navigator.onLine) {
            this.show({
                type: 'warning',
                title: '📶 لا يوجد اتصال بالإنترنت',
                message: 'بعض الميزات قد لا تعمل بشكل صحيح. تحقق من اتصالك بالإنترنت.',
                persistent: true
            });
        }
    }
}

// Initialize notification manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.notificationManager = new NotificationManager();
    
    // Add floating help button
    window.notificationManager.addFloatingHelp();
    
    // Check connection status
    window.notificationManager.showConnectionStatus();
    
    // Show study reminder after 5 minutes
    setTimeout(() => {
        window.notificationManager.showStudyReminder();
    }, 5 * 60 * 1000);
    
    // Listen for online/offline events
    window.addEventListener('online', () => {
        window.notificationManager.show({
            type: 'success',
            title: '✅ تم استعادة الاتصال',
            message: 'اتصال الإنترنت متاح الآن.',
            duration: 3000
        });
    });
    
    window.addEventListener('offline', () => {
        window.notificationManager.show({
            type: 'error',
            title: '❌ انقطع الاتصال',
            message: 'تحقق من اتصالك بالإنترنت.',
            persistent: true
        });
    });
});

// Utility functions for easy access
window.showNotification = (type, title, message, options = {}) => {
    if (window.notificationManager) {
        window.notificationManager.show({
            type,
            title,
            message,
            ...options
        });
    }
};

window.showSuccess = (title, message) => showNotification('success', title, message);
window.showError = (title, message) => showNotification('error', title, message);
window.showWarning = (title, message) => showNotification('warning', title, message);
window.showInfo = (title, message) => showNotification('info', title, message);