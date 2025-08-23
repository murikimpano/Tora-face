/**
 * TORA FACE - Dashboard Module
 * Handles dashboard functionality and user interface interactions
 */

class DashboardManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadDashboardData();
    }

    setupEventListeners() {
        // Refresh dashboard data periodically
        setInterval(() => {
            if (authManager.isAuthenticated()) {
                this.loadDashboardData();
            }
        }, 30000); // Every 30 seconds

        // Handle window resize for responsive design
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    async loadDashboardData() {
        if (!authManager.isAuthenticated()) {
            return;
        }

        try {
            // Load user profile to update search count
            const profileResponse = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${authManager.getAuthToken()}`
                }
            });

            const profileData = await profileResponse.json();

            if (profileData.success) {
                this.updateSearchCount(profileData.profile.search_count || 0);
            }

            // Load recent search history
            const historyResponse = await fetch('/api/face/search-history?limit=5', {
                headers: {
                    'Authorization': `Bearer ${authManager.getAuthToken()}`
                }
            });

            const historyData = await historyResponse.json();

            if (historyData.success) {
                this.updateSearchHistory(historyData.history);
            }

        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    updateSearchCount(count) {
        const searchCountElement = document.getElementById('search-count');
        if (searchCountElement) {
            searchCountElement.textContent = count;
        }
    }

    updateSearchHistory(history) {
        const historyContainer = document.getElementById('search-history');
        
        if (!historyContainer) return;

        if (history.length === 0) {
            historyContainer.innerHTML = '<p class="text-gray-500 text-center py-4">No recent searches</p>';
            return;
        }

        historyContainer.innerHTML = history.map(item => `
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div class="flex-1">
                    <div class="flex items-center">
                        <i class="fas ${this.getSearchTypeIcon(item.search_type)} mr-2 text-blue-600"></i>
                        <span class="font-medium">${this.formatSearchType(item.search_type)}</span>
                    </div>
                    <div class="text-sm text-gray-600 mt-1">
                        <span class="mr-4">
                            <i class="fas fa-user-friends mr-1"></i>
                            ${item.faces_detected} faces
                        </span>
                        <span class="mr-4">
                            <i class="fas fa-search mr-1"></i>
                            ${item.matches_found} matches
                        </span>
                        <span>
                            <i class="fas fa-clock mr-1"></i>
                            ${this.formatTimestamp(item.timestamp)}
                        </span>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-500">
                        ${this.getRelativeTime(item.timestamp)}
                    </div>
                </div>
            </div>
        `).join('');
    }

    getSearchTypeIcon(searchType) {
        const icons = {
            'face_upload_analysis': 'fa-camera',
            'name_search': 'fa-user-search',
            'face_recognition': 'fa-eye',
            'reverse_search': 'fa-search-plus'
        };
        return icons[searchType] || 'fa-search';
    }

    formatSearchType(searchType) {
        const types = {
            'face_upload_analysis': 'Photo Analysis',
            'name_search': 'Name Search',
            'face_recognition': 'Face Recognition',
            'reverse_search': 'Reverse Search'
        };
        return types[searchType] || searchType.replace('_', ' ').toUpperCase();
    }

    formatTimestamp(timestamp) {
        if (timestamp && timestamp.seconds) {
            return new Date(timestamp.seconds * 1000).toLocaleString();
        }
        return new Date(timestamp).toLocaleString();
    }

    getRelativeTime(timestamp) {
        const now = new Date();
        const time = timestamp.seconds ? new Date(timestamp.seconds * 1000) : new Date(timestamp);
        const diffMs = now - time;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return time.toLocaleDateString();
    }

    handleResize() {
        // Handle responsive design adjustments
        const width = window.innerWidth;
        
        if (width < 768) {
            // Mobile adjustments
            this.adjustForMobile();
        } else {
            // Desktop adjustments
            this.adjustForDesktop();
        }
    }

    adjustForMobile() {
        // Add mobile-specific adjustments
        const containers = document.querySelectorAll('.container');
        containers.forEach(container => {
            container.classList.add('px-2');
        });
    }

    adjustForDesktop() {
        // Add desktop-specific adjustments
        const containers = document.querySelectorAll('.container');
        containers.forEach(container => {
            container.classList.remove('px-2');
        });
    }

    handleKeyboardShortcuts(e) {
        // Ctrl/Cmd + U: Upload new photo
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            const photoInput = document.getElementById('photo-input');
            if (photoInput) {
                photoInput.click();
            }
        }

        // Ctrl/Cmd + N: New search
        if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
            e.preventDefault();
            if (window.faceRecognitionManager) {
                window.faceRecognitionManager.startNewSearch();
            }
        }

        // Escape: Clear current selection
        if (e.key === 'Escape') {
            if (window.faceRecognitionManager) {
                window.faceRecognitionManager.clearSelection();
            }
        }
    }

    showWelcomeMessage() {
        const user = authManager.getCurrentUser();
        if (user) {
            const message = `Welcome back, ${user.rank} ${user.badge_number}! Ready to analyze photos and identify individuals.`;
            this.showNotification(message, 'info');
        }
    }

    showSystemStatus() {
        // Show system status information
        const statusInfo = {
            'AI Engine': 'Online',
            'Database': 'Connected',
            'Social Media APIs': 'Active',
            'Firebase': 'Connected'
        };

        console.log('TORA FACE System Status:', statusInfo);
    }

    exportSystemReport() {
        if (!authManager.isAuthenticated()) {
            this.showNotification('Please log in to export system reports', 'error');
            return;
        }

        const user = authManager.getCurrentUser();
        const report = `
TORA FACE SYSTEM REPORT
=======================

Officer: ${user.rank} ${user.badge_number}
Department: ${user.department}
Country: ${user.country}
Total Searches: ${user.search_count || 0}
Report Generated: ${new Date().toLocaleString()}

System Status: Operational
Last Login: ${new Date().toLocaleString()}

This report was generated by the TORA FACE National Security System.
        `;

        const blob = new Blob([report], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `TORA_FACE_System_Report_${Date.now()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    showNotification(message, type = 'info') {
        const colors = {
            'info': 'bg-blue-500',
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500'
        };

        const icons = {
            'info': 'fa-info-circle',
            'success': 'fa-check-circle',
            'error': 'fa-exclamation-circle',
            'warning': 'fa-exclamation-triangle'
        };

        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${colors[type]} fade-in`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icons[type]} mr-2"></i>
                <span>${message}</span>
                <button class="ml-4 text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Initialize dashboard when user logs in
    onUserLogin() {
        this.loadDashboardData();
        this.showWelcomeMessage();
        this.showSystemStatus();
    }

    // Cleanup when user logs out
    onUserLogout() {
        // Clear any cached data
        this.updateSearchCount(0);
        this.updateSearchHistory([]);
    }
}

// Initialize dashboard manager
const dashboardManager = new DashboardManager();

// Listen for auth state changes
if (typeof authManager !== 'undefined') {
    // Override auth success handler to include dashboard initialization
    const originalHandleAuthSuccess = authManager.handleAuthSuccess;
    authManager.handleAuthSuccess = function(user) {
        originalHandleAuthSuccess.call(this, user);
        dashboardManager.onUserLogin();
    };

    const originalHandleAuthFailure = authManager.handleAuthFailure;
    authManager.handleAuthFailure = function() {
        originalHandleAuthFailure.call(this);
        dashboardManager.onUserLogout();
    };
}

