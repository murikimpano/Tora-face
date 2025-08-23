/**
 * TORA FACE - Authentication Module
 * Handles user login, logout, and authentication state
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.idToken = null;
        this.init();
    }

    init() {
        // Listen for authentication state changes
        auth.onAuthStateChanged((user) => {
            if (user) {
                this.handleAuthSuccess(user);
            } else {
                this.handleAuthFailure();
            }
        });

        // Setup event listeners
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('login-form');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.handleLogout());
        }

        // Forgot password
        const forgotPassword = document.getElementById('forgot-password');
        if (forgotPassword) {
            forgotPassword.addEventListener('click', (e) => this.handleForgotPassword(e));
        }
    }

    async handleLogin(e) {
        e.preventDefault();
        
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        if (!email || !password) {
            this.showError('Please enter both email and password');
            return;
        }

        try {
            this.showLoading(true);
            
            // Sign in with Firebase
            const userCredential = await auth.signInWithEmailAndPassword(email, password);
            const user = userCredential.user;

            // Get ID token
            const idToken = await user.getIdToken();
            
            // Send login request to backend
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id_token: idToken })
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = data.user;
                this.idToken = idToken;
                this.showDashboard();
                this.showSuccess('Login successful!');
            } else {
                throw new Error(data.error || 'Login failed');
            }

        } catch (error) {
            console.error('Login error:', error);
            this.showError(error.message || 'Login failed. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    async handleLogout() {
        try {
            // Send logout request to backend
            if (this.idToken) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.idToken}`,
                        'Content-Type': 'application/json'
                    }
                });
            }

            // Sign out from Firebase
            await auth.signOut();
            
            this.currentUser = null;
            this.idToken = null;
            this.showLoginScreen();
            this.showSuccess('Logged out successfully');

        } catch (error) {
            console.error('Logout error:', error);
            this.showError('Error during logout');
        }
    }

    async handleForgotPassword(e) {
        e.preventDefault();
        
        const email = document.getElementById('login-email').value;
        
        if (!email) {
            this.showError('Please enter your email address first');
            return;
        }

        try {
            await auth.sendPasswordResetEmail(email);
            this.showSuccess('Password reset email sent! Check your inbox.');
        } catch (error) {
            console.error('Password reset error:', error);
            this.showError('Error sending password reset email');
        }
    }

    handleAuthSuccess(user) {
        console.log('User authenticated:', user.email);
        
        // Get user profile from backend
        user.getIdToken().then(idToken => {
            this.idToken = idToken;
            this.fetchUserProfile();
        });
    }

    handleAuthFailure() {
        console.log('User not authenticated');
        this.showLoginScreen();
    }

    async fetchUserProfile() {
        try {
            const response = await fetch('/api/auth/profile', {
                headers: {
                    'Authorization': `Bearer ${this.idToken}`
                }
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = data.profile;
                this.showDashboard();
                this.updateUserInfo();
            } else {
                throw new Error(data.error || 'Failed to fetch profile');
            }

        } catch (error) {
            console.error('Profile fetch error:', error);
            this.showError('Error loading profile');
        }
    }

    showLoginScreen() {
        document.getElementById('login-screen').classList.remove('hidden');
        document.getElementById('dashboard').classList.add('hidden');
    }

    showDashboard() {
        document.getElementById('login-screen').classList.add('hidden');
        document.getElementById('dashboard').classList.remove('hidden');
        document.getElementById('user-info').classList.remove('hidden');
    }

    updateUserInfo() {
        if (this.currentUser) {
            const userBadge = document.getElementById('user-badge');
            if (userBadge) {
                userBadge.textContent = `${this.currentUser.rank} ${this.currentUser.badge_number} - ${this.currentUser.department}`;
            }

            const searchCount = document.getElementById('search-count');
            if (searchCount) {
                searchCount.textContent = this.currentUser.search_count || 0;
            }
        }
    }

    showLoading(show) {
        const loginForm = document.getElementById('login-form');
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        
        if (show) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Login';
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg text-white z-50 ${
            type === 'error' ? 'bg-red-500' : 'bg-green-500'
        }`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${type === 'error' ? 'fa-exclamation-circle' : 'fa-check-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 5000);
    }

    // Get current user token for API requests
    getAuthToken() {
        return this.idToken;
    }

    // Get current user data
    getCurrentUser() {
        return this.currentUser;
    }

    // Check if user is authenticated
    isAuthenticated() {
        return this.currentUser !== null && this.idToken !== null;
    }
}

// Initialize authentication manager
const authManager = new AuthManager();

