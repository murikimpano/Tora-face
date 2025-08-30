"""
TORA FACE - Firebase Authentication Module (Enhanced)
Handles police officer authentication, authorization, and secure file uploads
"""

import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
import os
import logging
from typing import Dict, Optional, List
from functools import wraps
from flask import request, jsonify
from datetime import datetime

# ================= Logging Setup =================
log_file = os.getenv('LOG_FILE', 'tora_face.log')
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ================= Multilingual Messages =================
MESSAGES = {
    "en": {
        "no_token": "No token provided",
        "invalid_token": "Invalid token",
        "auth_failed": "Authentication failed",
        "access_denied": "Access denied"
    },
    "rw": {
        "no_token": "Ntacyo wakoresheje token",
        "invalid_token": "Token siyo",
        "auth_failed": "Kwinjira byanze",
        "access_denied": "Uburenganzira bwawe burahari"
    },
    "fr": {
        "no_token": "Aucun token fourni",
        "invalid_token": "Token invalide",
        "auth_failed": "Échec de l'authentification",
        "access_denied": "Accès refusé"
    },
    "sw": {
        "no_token": "Hakuna token imetolewa",
        "invalid_token": "Token sio sahihi",
        "auth_failed": "Authentication imeshindikana",
        "access_denied": "Ufikiaji umezuiwa"
    }
}

def get_message(key: str) -> str:
    lang = request.headers.get('Accept-Language', 'en')
    return MESSAGES.get(lang, MESSAGES['en']).get(key, key)

# ================= Firebase Auth Class =================
class FirebaseAuth:
    def __init__(self):
        self.app = None
        self.db = None
        self.bucket = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        try:
            if not firebase_admin._apps:
                if os.getenv('FIREBASE_PRIVATE_KEY'):
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
                    cred = credentials.Certificate('path/to/serviceAccountKey.json')
                
                self.app = firebase_admin.initialize_app(cred, {
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'tora-face-security.appspot.com')
                })
                self.db = firestore.client()
                self.bucket = storage.bucket()
                logger.info("Firebase initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                self.db = firestore.client()
                self.bucket = storage.bucket()
        except Exception as e:
            logger.error(f"Error initializing Firebase: {str(e)}")
            self.db = None
            self.bucket = None
    
    # ========== Authentication ==========
    def verify_token(self, id_token: str) -> Optional[Dict]:
        try:
            decoded_token = auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Error verifying token: {str(e)}")
            return None

    def create_police_user(self, email: str, password: str, user_data: Dict) -> Dict:
        try:
            user = auth.create_user(email=email, password=password, email_verified=False, disabled=False)
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
            return {'success': True, 'uid': user.uid, 'email': email, 'message': 'Police user created successfully'}
        except Exception as e:
            logger.error(f"Error creating police user: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ========== Profile & Logging ==========
    def get_user_profile(self, uid: str) -> Optional[Dict]:
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
        try:
            if self.db:
                self.db.collection('police_users').document(uid).update({'last_login': datetime.utcnow()})
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")

    def log_search_activity(self, uid: str, search_data: Dict):
        try:
            if self.db:
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
                self.db.collection('police_users').document(uid).update({'search_count': firestore.Increment(1)})
        except Exception as e:
            logger.error(f"Error logging search activity: {str(e)}")

    # ========== Image Upload ==========
    def upload_image_to_storage(self, image_data: bytes, filename: str, uid: str) -> Optional[str]:
        try:
            if self.bucket:
                if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    logger.warning(f"Invalid file type: {filename}")
                    return None
                if len(image_data) > int(os.getenv('MAX_CONTENT_LENGTH', 16*1024*1024)):
                    logger.warning(f"File too large: {filename}")
                    return None
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                blob_name = f"uploads/{uid}/{timestamp}_{filename}"
                blob = self.bucket.blob(blob_name)
                blob.upload_from_string(image_data, content_type='image/jpeg')
                blob.make_public()
                return blob.public_url
            return None
        except Exception as e:
            logger.error(f"Error uploading image: {str(e)}")
            return None

# ========== Route Decorator ==========
def require_auth(role: Optional[str] = None):
    """Decorator to require authentication and optional role for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': get_message("no_token")}), 401
            if token.startswith('Bearer '):
                token = token[7:]
            firebase_auth = FirebaseAuth()
            decoded_token = firebase_auth.verify_token(token)
            if not decoded_token:
                return jsonify({'error': get_message("invalid_token")}), 401
            # Role check
            if role and decoded_token.get('role') != role:
                return jsonify({'error': get_message("access_denied")}), 403
            request.current_user = decoded_token
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ================= Initialize =================
firebase_auth = FirebaseAuth()
