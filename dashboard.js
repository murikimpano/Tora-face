/**
 * TORA FACE - Dashboard Module (Refactored)
 * Handles dashboard functionality and user interface interactions
 */

class DashboardManager {
    constructor() {
        // References to event handlers for cleanup
        this.resizeHandler = this.handleResize.bind(this);
        this.keyboardHandler = this.handleKeyboardShortcuts.bind(this);
        this.refreshInterval = null;

        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    // -------------------------
    // Event Listeners & Handlers
    // -------------------------
    setupEventListeners() {
        window.addEventListener('resize', this.resizeHandler);
        document.addEventListener('keydown', this.keyboardHandler);
    }

    cleanupEventListeners() {
        window.removeEventListener('resize', this.resizeHandler);
        document.removeEventListener('keydown', this.keyboardHandler);
        if (this.refreshInterval) clearInterval(this.refreshInterval);
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            if (authManager.isAuthenticated()) {
                this.loadDashboardData();
            }
        }, 30000); // Every 30 seconds
    }

    // -------------------------
    // Data Fetching
    // -------------------------
    async fetchWithTimeout(url, options = {}, timeout = 10000) {
        return Promise.race([
            fetch(url, options),
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Request timed out')), timeout)
            )
        ]);
    }

    async loadDashboardData() {
        if (!authManager.isAuthenticated()) return;
        await Promise.all([this.loadProfile(), this.loadSearchHistory()]);
    }

    async loadProfile() {
        try {
            const res = await this.fetchWithTimeout('/api/auth/profile', {
                headers: { 'Authorization': `Bearer ${authManager.getAuthToken()}` }
            });
            const data = await res.json();
            if (data.success) this.updateSearchCount(data.profile.search_count || 0);
        } catch (e) {
            console.error('Error loading profile:', e);
        }
    }

    async loadSearchHistory(limit = 5) {
        try {
            const res = await this.fetchWithTimeout(`/api/face/search-history?limit=${limit}`, {
                headers: { 'Authorization': `Bearer ${authManager.getAuthToken()}` }
            });
            const data = await res.json();
            if (data.success) this.updateSearchHistory(data.history);
        } catch (e) {
            console.error('Error loading search history:', e);
        }
    }

    // -------------------------
    // Dashboard Updates
    // -------------------------
    updateSearchCount(count) {
        const el = document.getElementById('search-count');
        if (el) el.textContent = count;
    }

    updateSearchHistory(history) {
        const container = document.getElementById('search-history');
        if (!container) return;

        if (!history || history.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No recent searches</p>';
            return;
        }

        container.innerHTML = history.map(item => `
            <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div class="flex-1">
                    <div class="flex items-center">
                        <i class="fas ${this.getSearchTypeIcon(item.search_type)} mr-2 text-blue-600"></i>
                        <span class="font-medium">${this.formatSearchType(item.search_type)}</span>
                    </div>
                    <div class="text-sm text-gray-600 mt-1">
                        <span class="mr-4"><i class="fas fa-user-friends mr-1"></i>${item.faces_detected} faces</span>
                        <span class="mr-4"><i class="fas fa-search mr-1"></i>${item.matches_found} matches</span>
                        <span><i class="fas fa-clock mr-1"></i>${this.formatTimestamp(item.timestamp)}</span>
                    </div>
                </div>
                <div class="text-right">
                    <div class="text-sm text-gray-500">${this.getRelativeTime(item.timestamp)}</div>
                </div>
            </div>
        `).join('');
    }

    // -------------------------
    // Helpers
    // -------------------------
    parseTimestamp(ts) {
        return ts && ts.seconds ? new Date(ts.seconds * 1000) : new Date(ts);
    }

    formatTimestamp(ts) {
        return this.parseTimestamp(ts).toLocaleString();
    }

    getRelativeTime(ts) {
        const now = new Date();
        const time = this.parseTimestamp(ts);
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

    // -------------------------
    // Responsive UI
    // -------------------------
    handleResize() {
        const width = window.innerWidth;
        if (width < 768) this.adjustForMobile();
        else this.adjustForDesktop();
    }

    adjustForMobile() {
        document.querySelectorAll('.container').forEach(c => c.classList.add('px-2'));
    }

    adjustForDesktop() {
        document.querySelectorAll('.container').forEach(c => c.classList.remove('px-2'));
    }

    // -------------------------
    // Keyboard Shortcuts
    // -------------------------
    handleKeyboardShortcuts(e) {
        if (['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)) return;

        // Ctrl/Cmd + U: Upload new photo
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'u') {
            e.preventDefault();
            document.getElementById('photo-input')?.click();
        }

        // Ctrl/Cmd + N: New search
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'n') {
            e.preventDefault();
            window.faceRecognitionManager?.startNewSearch();
        }

        // Escape: Clear selection
        if (e.key === 'Escape') window.faceRecognitionManager?.clearSelection();
    }

    // -------------------------
    // Notifications
    // -------------------------
    showNotification(message, type = 'info') {
        const colors = { info: 'bg-blue-500', success: 'bg-green-500', error: 'bg-red-500', warning: 'bg-yellow-500' };
        const icons = { info: 'fa-info-circle', success: 'fa-check-circle', error: 'fa-exclamation-circle', warning: 'fa-exclamation-triangle' };

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
        setTimeout(() => notification.remove(), 5000);
    }

    // -------------------------
    // Welcome & Status
    // -------------------------
    showWelcomeMessage() {
        const user = authManager.getCurrentUser();
        if (user) {
            const message = `Welcome back, ${user.rank} ${user.badge_number}! Ready to analyze photos and identify individuals.`;
            this.showNotification(message, 'info');
        }
    }

    showSystemStatus() {
        console.log('TORA FACE System Status:', {
            'AI Engine': 'Online',
            'Database': 'Connected',
            'Social Media APIs': 'Active',
            'Firebase': 'Connected'
        });
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

    // -------------------------
    // User Login/Logout Hooks
    // -------------------------
    onUserLogin() {
        this.loadDashboardData();
        this.showWelcomeMessage();
        this.showSystemStatus();
    }

    onUserLogout() {
        this.updateSearchCount(0);
        this.updateSearchHistory([]);
    }
}

// -------------------------
// Initialize dashboard manager
// -------------------------
const dashboardManager = new DashboardManager();

if (typeof authManager !== 'undefined') {
    const origSuccess = authManager.handleAuthSuccess.bind(authManager);
    authManager.handleAuthSuccess = function(user) {
        origSuccess(user);
        dashboardManager.onUserLogin();
    };

    const origFailure = authManager.handleAuthFailure.bind(authManager);
    authManager.handleAuthFailure = function() {
        origFailure();
        dashboardManager.onUserLogout();
    };
    }
