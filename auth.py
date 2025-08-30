"""
TORA FACE - Authentication API Routes
Handles police officer authentication, registration, and user management
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime
import re

from src.firebase.auth import firebase_auth, require_auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new police officer
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'badge_number', 'department', 'rank', 'country']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        email = data['email'].lower().strip()
        password = data['password']
        
        # Validate email
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Validate password
        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        # Validate country (only Burundi and Rwanda allowed)
        allowed_countries = ['burundi', 'rwanda']
        if data['country'].lower() not in allowed_countries:
            return jsonify({'error': 'Only Burundi and Rwanda police officers are allowed'}), 400
        
        # Prepare user data
        user_data = {
            'badge_number': data['badge_number'],
            'department': data['department'],
            'rank': data['rank'],
            'country': data['country'].title(),
            'region': data.get('region', ''),
            'phone': data.get('phone', ''),
            'full_name': data.get('full_name', '')
        }
        
        # Create user
        result = firebase_auth.create_police_user(email, password, user_data)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Police officer registered successfully. Please verify your email.',
                'uid': result['uid']
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error in register: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Registration failed. Please try again.'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login endpoint (client-side Firebase Auth handles actual login)
    This endpoint updates last login time and returns user profile
    """
    try:
        data = request.get_json()
        
        if 'id_token' not in data:
            return jsonify({'error': 'ID token required'}), 400
        
        # Verify the ID token
        decoded_token = firebase_auth.verify_token(data['id_token'])
        
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        uid = decoded_token['uid']
        
        # Get user profile
        user_profile = firebase_auth.get_user_profile(uid)
        
        if not user_profile:
            return jsonify({'error': 'User profile not found'}), 404
        
        if not user_profile.get('active', True):
            return jsonify({'error': 'Account is deactivated'}), 403
        
        # Update last login
        firebase_auth.update_last_login(uid)
        
        # Return user profile (excluding sensitive data)
        profile_data = {
            'uid': uid,
            'email': user_profile.get('email'),
            'badge_number': user_profile.get('badge_number'),
            'department': user_profile.get('department'),
            'rank': user_profile.get('rank'),
            'country': user_profile.get('country'),
            'region': user_profile.get('region'),
            'search_count': user_profile.get('search_count', 0),
            'permissions': user_profile.get('permissions', {}),
            'last_login': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'user': profile_data,
            'message': 'Login successful'
        })
        
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Login failed'
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get current user profile
    """
    try:
        current_user = request.current_user
        uid = current_user.get('uid')
        
        user_profile = firebase_auth.get_user_profile(uid)
        
        if not user_profile:
            return jsonify({'error': 'Profile not found'}), 404
        
        # Return profile data (excluding sensitive information)
        profile_data = {
            'uid': uid,
            'email': user_profile.get('email'),
            'badge_number': user_profile.get('badge_number'),
            'department': user_profile.get('department'),
            'rank': user_profile.get('rank'),
            'country': user_profile.get('country'),
            'region': user_profile.get('region'),
            'full_name': user_profile.get('full_name'),
            'phone': user_profile.get('phone'),
            'search_count': user_profile.get('search_count', 0),
            'permissions': user_profile.get('permissions', {}),
            'created_at': user_profile.get('created_at'),
            'last_login': user_profile.get('last_login')
        }
        
        return jsonify({
            'success': True,
            'profile': profile_data
        })
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving profile'
        }), 500

@auth_bp.route('/update-profile', methods=['PUT'])
@require_auth
def update_profile():
    """
    Update user profile
    """
    try:
        current_user = request.current_user
        uid = current_user.get('uid')
        
        data = request.get_json()
        
        # Fields that can be updated
        updatable_fields = ['full_name', 'phone', 'region']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Update in Firestore
        if firebase_auth.db:
            firebase_auth.db.collection('police_users').document(uid).update(update_data)
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error updating profile'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """
    Change user password
    """
    try:
        data = request.get_json()
        
        if 'new_password' not in data:
            return jsonify({'error': 'New password required'}), 400
        
        new_password = data['new_password']
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({'error': message}), 400
        
        current_user = request.current_user
        uid = current_user.get('uid')
        
        # Update password in Firebase Auth
        from firebase_admin import auth
        auth.update_user(uid, password=new_password)
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error changing password'
        }), 500

@auth_bp.route('/verify-email', methods=['POST'])
def verify_email():
    """
    Send email verification
    """
    try:
        data = request.get_json()
        
        if 'id_token' not in data:
            return jsonify({'error': 'ID token required'}), 400
        
        # Verify token
        decoded_token = firebase_auth.verify_token(data['id_token'])
        
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        # In a real implementation, you would send verification email
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': 'Verification email sent'
        })
        
    except Exception as e:
        logger.error(f"Error sending verification email: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error sending verification email'
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Send password reset email
    """
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({'error': 'Email required'}), 400
        
        email = data['email'].lower().strip()
        
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # In a real implementation, you would send password reset email
        # For now, just return success
        
        return jsonify({
            'success': True,
            'message': 'Password reset email sent if account exists'
        })
        
    except Exception as e:
        logger.error(f"Error sending password reset: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error sending password reset email'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    Logout endpoint (mainly for logging purposes)
    """
    try:
        current_user = request.current_user
        uid = current_user.get('uid')
        
        # Log logout activity
        logger.info(f"User {uid} logged out")
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in logout: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error during logout'
        }), 500

from flask import Blueprint, request, jsonify
from src.models.user import db, User

auth_bp = Blueprint('auth', __name__)

# --- Signup ---
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists"}), 400

    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"Account created successfully for {username}"}), 201

# --- Login ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password).first()
    if user:
        return jsonify({"message": f"Welcome back {user.username}!"}), 200
    else:
        return jsonify({"error": "Invalid email or password"}), 401
