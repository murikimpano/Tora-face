/**
 * TORA FACE - Firebase Configuration
 * Configure Firebase for authentication and data storage
 */

// Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    authDomain: "tora-face-security.firebaseapp.com",
    databaseURL: "https://tora-face-security-default-rtdb.firebaseio.com",
    projectId: "tora-face-security",
    storageBucket: "tora-face-security.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abcdef1234567890abcdef"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);

// Initialize Firebase Auth
const auth = firebase.auth();

// Configure auth settings
auth.useDeviceLanguage();

// Auth state persistence
auth.setPersistence(firebase.auth.Auth.Persistence.LOCAL);

console.log('Firebase initialized successfully');

