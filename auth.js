/**
 * TORA FACE - Authentication Module (Enhanced)
 * Handles user login, logout, password reset, and authentication state
 */

class AuthManager {
    constructor() {
        this.currentUser = null;
        this.idToken = null;
        this.notifications = [];
        this.init();
    }

    // ========== Initialization ==========
    init() {
        // Listen for Firebase auth state changes
        auth.onAuthStateChanged(user => {
            if (user) {
                this.handleAuthSuccess(user);
            } else {
                this.handleAuthFailure();
            }
        });

        this.setupEventListeners();
    }

    setupEventListeners() {
        const loginForm = document.getElementById('login-form');
        if (loginForm) loginForm.addEventListener('submit', e => this.handleLogin(e));

        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) logoutBtn.addEventListener('click', () => this.handleLogout());

        const forgotPassword = document.getElementById('forgot-password');
        if (forgotPassword) forgotPassword.addEventListener('click', e => this.handleForgotPassword(e));

        const langSwitcher = document.getElementById('lang-switcher');
        if (langSwitcher) langSwitcher.addEventListener('change', e => {
            document.documentElement.lang = e.target.value;
        });
    }

    // ========== Multilingual Messages ==========
    messages = {
        en: {
            missing_fields: "Please enter both email and password",
            login_failed: "Login failed. Please try again.",
            logout_success: "Logged out successfully",
            forgot_email: "Please enter your email address first",
            password_reset: "Password reset email sent! Check your inbox."
        },
        rw: {
            missing_fields: "Injiza email na password",
            login_failed: "Kwinjira byanze. Ongera ugerageze.",
            logout_success: "Uvuye muri system neza",
            forgot_email: "Injiza email yawe mbere",
            password_reset: "Email yo guhindura password yoherejwe!"
        },
        fr: {
            missing_fields: "Veuillez entrer email et mot de passe",
            login_failed: "Échec de connexion. Réessayez.",
            logout_success: "Déconnexion réussie",
            forgot_email: "Veuillez entrer votre adresse email",
            password_reset: "Email de réinitialisation envoyé !"
        },
        sw: {
            missing_fields: "Weka email na password",
            login_failed: "Kuingia kwa kosa. Jaribu tena.",
            logout_success: "Umeondoka kwa mafanikio",
            forgot_email: "Weka email yako kwanza",
            password_reset: "Barua ya reset password imetumwa!"
        }
    };

    getMessage(key) {
        const lang = document.documentElement.lang || 'en';
        return this.messages[lang]?.[key] || key;
    }

    // ========== Login ==========
    async handleLogin(e) {
        e.preventDefault();

        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        if (!email || !password) {
            this.showNotification(this.getMessage('missing_fields'), 'error');
            return;
        }

        try {
            this.showLoading(true);

            const userCredential = await auth.signInWithEmailAndPassword(email, password);
            const user = userCredential.user;

            const idToken = await user.getIdToken();
            this.idToken = idToken;

            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id_token: idToken })
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = data.user;
                this.showDashboard();
                this.showNotification('Login successful!', 'success');
            } else {
                throw new Error(data.error || this.getMessage('login_failed'));
            }

        } catch (error) {
            console.error('Login error:', error);
            this.showNotification(error.message || this.getMessage('login_failed'), 'error');
        } finally {
            this.showLoading(false);
        }
    }

    // ========== Logout ==========
    async handleLogout() {
        try {
            if (this.idToken) {
                await fetch('/api/auth/logout', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${this.idToken}`,
                        'Content-Type': 'application/json'
                    }
                });
            }
            await auth.signOut();
            this.currentUser = null;
            this.idToken = null;
            this.showLoginScreen();
            this.showNotification(this.getMessage('logout_success'), 'success');
        } catch (error) {
            console.error('Logout error:', error);
            this.showNotification('Error during logout', 'error');
        }
    }

    // ========== Forgot Password ==========
    async handleForgotPassword(e) {
        e.preventDefault();
        const email = document.getElementById('login-email').value.trim();
        if (!email) {
            this.showNotification(this.getMessage('forgot_email'), 'error');
            return;
        }
        try {
            await auth.sendPasswordResetEmail(email);
            this.showNotification(this.getMessage('password_reset'), 'success');
        } catch (error) {
            console.error('Password reset error:', error);
            this.showNotification('Error sending password reset email', 'error');
        }
    }

    // ========== Auth State Handlers ==========
    handleAuthSuccess(user) {
        console.log('User authenticated:', user.email);
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
                headers: { 'Authorization': `Bearer ${this.idToken}` }
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
            this.showNotification('Error loading profile', 'error');
        }
    }

    // ========== UI Updates ==========
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
        if (!this.currentUser) return;

        const userBadge = document.getElementById('user-badge');
        if (userBadge) {
            userBadge.textContent = `${this.currentUser.rank} ${this.currentUser.badge_number} - ${this.currentUser.department}`;
        }

        const searchCount = document.getElementById('search-count');
        if (searchCount) {
            searchCount.textContent = this.currentUser.search_count || 0;
        }
    }

    // ========== Loading & Notifications ==========
    showLoading(show) {
        const loginForm = document.getElementById('login-form');
        if (!loginForm) return;
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        if (!submitBtn) return;

        if (show) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Logging in...';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Login';
        }
    }

    showNotification(message, type='success') {
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
        this.notifications.push(notification);

        setTimeout(() => {
            if (notification.parentNode) notification.parentNode.removeChild(notification);
            this.notifications.shift();
        }, 5000);
    }

    // ========== Getters ==========
    getAuthToken() { return this.idToken; }
    getCurrentUser() { return this.currentUser; }
    isAuthenticated() { return this.currentUser && this.idToken; }
}

// Initialize authentication manager
const authManager = new AuthManager();
