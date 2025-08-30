// firebase-config.js
/**
 * TORA FACE - Firebase Full Configuration & Helpers
 * Handles authentication, storage, and database operations
 */

import { initializeApp } from "firebase/app";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, sendPasswordResetEmail, onAuthStateChanged, setPersistence, browserLocalPersistence } from "firebase/auth";
import { getStorage, ref, uploadBytes, getDownloadURL } from "firebase/storage";
import { getDatabase, ref as dbRef, set, push, get, child } from "firebase/database";

// =====================
// Firebase configuration
// =====================
const firebaseConfig = {
    apiKey: "AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    authDomain: "tora-face-security.firebaseapp.com",
    databaseURL: "https://tora-face-security-default-rtdb.firebaseio.com",
    projectId: "tora-face-security",
    storageBucket: "tora-face-security.appspot.com",
    messagingSenderId: "123456789012",
    appId: "1:123456789012:web:abcdef1234567890abcdef"
};

// =====================
// Initialize Firebase
// =====================
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const storage = getStorage(app);
const database = getDatabase(app);

// Use device language and persistent login
auth.useDeviceLanguage();
setPersistence(auth, browserLocalPersistence);

// =====================
// Authentication Helpers
// =====================
export const signup = async (email, password) => {
    try {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        return { success: true, user: userCredential.user };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

export const login = async (email, password) => {
    try {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        return { success: true, user: userCredential.user };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

export const logout = async () => {
    try {
        await signOut(auth);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

export const resetPassword = async (email) => {
    try {
        await sendPasswordResetEmail(auth, email);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

export const onAuthChange = (callback) => {
    return onAuthStateChanged(auth, callback);
};

// =====================
// Storage Helpers
// =====================
export const uploadImage = async (file, path) => {
    try {
        const storageRef = ref(storage, path);
        const snapshot = await uploadBytes(storageRef, file);
        const url = await getDownloadURL(snapshot.ref);
        return { success: true, url };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

// =====================
// Database Helpers
// =====================
export const logSearchActivity = async (uid, searchData) => {
    try {
        const activityRef = push(dbRef(database, `search_logs/${uid}`));
        await set(activityRef, { ...searchData, timestamp: new Date().toISOString() });
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
};

export const getSearchHistory = async (uid, limit = 50) => {
    try {
        const userRef = dbRef(database, `search_logs/${uid}`);
        const snapshot = await get(userRef);
        if (!snapshot.exists()) return [];
        const allLogs = Object.values(snapshot.val());
        return allLogs.slice(-limit).reverse(); // return latest logs first
    } catch (error) {
        return [];
    }
};

export const getUserProfile = async (uid) => {
    try {
        const profileRef = dbRef(database, `users/${uid}`);
        const snapshot = await get(profileRef);
        if (!snapshot.exists()) return {};
        return snapshot.val();
    } catch (error) {
        return {};
    }
};

// =====================
// Export modules
// =====================
export { auth, storage, database };
