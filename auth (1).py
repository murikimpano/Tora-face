"""
TORA FACE - Firebase Authentication Module
Handles police officer authentication and authorization
"""

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
import os
import json
import logging
from typing import Dict, Optional, List
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FirebaseAuth:
    """
    Firebase authentication and authorization handler
    """
    
    def __init__(self):
        self.app = None
        self.db = None
        self.bucket = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Load Firebase credentials from environment or service account file
                if os.getenv('FIREBASE_PRIVATE_KEY'):
                    # Use environment variables
                    cred_dict = {
                        "type": "service_account",
                        "project_id": os.getenv('FIREBASE_PROJECT_ID'),
                        "private_key_id": os.getenv('FIREBASE_PRIVATE_KEY_ID'),
                        "private_key": os.getenv('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
                        "client_email": os.getenv('FIREBASE_CLIENT_EMAIL'),
                        "client_id": os.getenv('FIREBASE_CLIENT_ID'),
                        "auth_uri": os.getenv('FIREBASE_AUTH_URI'),
                        "token_uri": os.getenv('FIREBASE_TOKEN_URI'),
                        "auth_provider_x509_cert_url": os.getenv('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
                        "client_x509_cert_url": os.getenv('FIREBASE_CLIENT_X509_CERT_URL')
                    }
                    cred = credentials.Certificate(cred_dict)
                else:
                    # Use service account file (for development)
                    cred = credentials.Certificate('path/to/serviceAccountKey.json')
                
                # Initialize Firebase
                self.app = firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'tora-face-security.appspot.com')
                })
                
                # Initialize Firestore and Storage
                self.db = firestore.client()
                self.bucket = storage.bucket()
                
                logger.info("Firebase initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                self.db = firestore.client()
                self.bucket = storage.bucket()
                
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            # For development, create mock objects
            self.db = None
            self.bucket = None
    
    def verify_token(self, id_token: str) -> Optional[Dict]:
        """
        Verify Firebase ID token
        
        Args:
            id_token: Firebase ID token
            
        Returns:
            Decoded token data or None if invalid
        """
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None
    
    def create_police_user(self, email: str, password: str, user_data: Dict) -> Dict:
        """
        Create a new police user account
        
        Args:
            email: User email
            password: User password
            user_data: Additional user information
            
        Returns:
            User creation result
        """
        try:
            # Create user in Firebase Auth
            user = auth.create_user(
                email=email,
                password=password,
                email_verified=False,
                disabled=False
            )
            
            # Store additional user data in Firestore
            user_doc_data = {
                'uid': user.uid,
                'email': email,
                'role': 'police_officer',
                'badge_number': user_data.get('badge_number'),
                'department': user_data.get('department'),
                'rank': user_data.get('rank'),
                'country': user_data.get('country'),
                'region': user_data.get('region'),
                'created_at': datetime.utcnow(),
                'last_login': None,
                'active': True,
                'verified': False,
                'search_count': 0,
                'permissions': {
                    'can_search': True,
                    'can_export': True,
                    'can_view_history': True
                }
            }
            
            if self.db:
                self.db.collection('police_users').document(user.uid).set(user_doc_data)
            
            logger.info(f"Police user created: {email}")
            
            return {
                'success': True,
                'uid': user.uid,
                'email': email,
                'message': 'Police user created successfully'
            }
            
        except Exception as e:
            logger.error(f"Error creating police user: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_user_profile(self, uid: str) -> Optional[Dict]:
        """
        Get police user profile data
        
        Args:
            uid: User UID
            
        Returns:
            User profile data or None
        """
        try:
            if self.db:
                doc = self.db.collection('police_users').document(uid).get()
                if doc.exists:
                    return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    def update_last_login(self, uid: str):
        """
        Update user's last login timestamp
        
        Args:
            uid: User UID
        """
        try:
            if self.db:
                self.db.collection('police_users').document(uid).update({
                    'last_login': datetime.utcnow()
                })
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
    
    def log_search_activity(self, uid: str, search_data: Dict):
        """
        Log user search activity
        
        Args:
            uid: User UID
            search_data: Search activity data
        """
        try:
            if self.db:
                # Add to search history
                search_log = {
                    'user_uid': uid,
                    'timestamp': datetime.utcnow(),
                    'search_type': search_data.get('search_type', 'face_recognition'),
                    'faces_detected': search_data.get('faces_detected', 0),
                    'matches_found': search_data.get('matches_found', 0),
                    'image_hash': search_data.get('image_hash'),
                    'results_summary': search_data.get('results_summary', {}),
                    'ip_address': request.remote_addr if request else 'Unknown'
                }
                
                self.db.collection('search_history').add(search_log)
                
                # Update user search count
                user_ref = self.db.collection('police_users').document(uid)
                user_ref.update({
                    'search_count': firestore.Increment(1)
                })
                
        except Exception as e:
            logger.error(f"Error logging search activity: {str(e)}")
    
    def get_search_history(self, uid: str, limit: int = 50) -> List[Dict]:
        """
        Get user's search history
        
        Args:
            uid: User UID
            limit: Number of records to return
            
        Returns:
            List of search history records
        """
        try:
            if self.db:
                docs = self.db.collection('search_history')\
                    .where('user_uid', '==', uid)\
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                    .limit(limit)\
                    .stream()
                
                history = []
                for doc in docs:
                    data = doc.to_dict()
                    data['id'] = doc.id
                    history.append(data)
                
                return history
            return []
            
        except Exception as e:
            logger.error(f"Error getting search history: {str(e)}")
            return []
    
    def upload_image_to_storage(self, image_data: bytes, filename: str, uid: str) -> Optional[str]:
        """
        Upload image to Firebase Storage
        
        Args:
            image_data: Image bytes
            filename: Image filename
            uid: User UID
            
        Returns:
            Download URL or None
        """
        try:
            if self.bucket:
                # Create unique filename with user ID and timestamp
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                blob_name = f"uploads/{uid}/{timestamp}_{filename}"
                
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(image_data, content_type='image/jpeg')
                
                # Make the blob publicly readable (optional, for police use)
                blob.make_public()
                
                return blob.public_url
            return None
            
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return None

# Decorator for protecting routes
def require_auth(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            # Verify token
            firebase_auth = FirebaseAuth()
            decoded_token = firebase_auth.verify_token(token)
            
            if not decoded_token:
                return jsonify({'error': 'Invalid token'}), 401
            
            # Add user info to request context
            request.current_user = decoded_token
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Authentication failed'}), 401
    
    return decorated_function

# Initialize Firebase Auth
firebase_auth = FirebaseAuth()

