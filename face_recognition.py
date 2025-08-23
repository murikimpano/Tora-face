"""
TORA FACE - Face Recognition API Routes
Handles face recognition, search, and analysis endpoints
"""

from flask import Blueprint, request, jsonify, current_app
import os
import hashlib
import json
from datetime import datetime
import logging
from werkzeug.utils import secure_filename

from src.firebase.auth import require_auth, firebase_auth
from src.ai.face_recognition import face_engine
from src.ai.social_media_scraper import social_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
face_bp = Blueprint('face_recognition', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@face_bp.route('/upload-and-analyze', methods=['POST'])
@require_auth
def upload_and_analyze():
    """
    Upload image and perform face recognition analysis
    """
    try:
        # Check if file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, GIF allowed'}), 400
        
        # Get current user
        current_user = request.current_user
        uid = current_user.get('uid')
        
        # Read file data
        image_data = file.read()
        
        # Create image hash for tracking
        image_hash = hashlib.md5(image_data).hexdigest()
        
        # Process the uploaded image
        face_analysis = face_engine.process_uploaded_image(image_data)
        
        if face_analysis['status'] == 'error':
            return jsonify({
                'success': False,
                'error': face_analysis.get('error', 'Unknown error')
            }), 500
        
        if face_analysis['faces_detected'] == 0:
            return jsonify({
                'success': False,
                'message': 'No faces detected in the uploaded image',
                'faces_detected': 0
            }), 400
        
        # Upload image to Firebase Storage
        filename = secure_filename(file.filename)
        image_url = firebase_auth.upload_image_to_storage(image_data, filename, uid)
        
        # Perform comprehensive social media search
        search_query = request.form.get('search_query', 'person face')
        primary_face = face_analysis['faces'][0]  # Use first detected face
        
        search_results = social_scraper.comprehensive_search(
            primary_face['encoding'], 
            search_query
        )
        
        # Prepare response
        response_data = {
            'success': True,
            'image_hash': image_hash,
            'image_url': image_url,
            'faces_detected': face_analysis['faces_detected'],
            'primary_face': {
                'attributes': face_analysis['attributes'],
                'location': primary_face['location'],
                'confidence': primary_face['confidence']
            },
            'search_results': {
                'total_matches': search_results['total_matches'],
                'google_images': search_results['google_images'][:10],  # Limit results
                'social_profiles': search_results['social_profiles'],
                'search_timestamp': search_results['search_timestamp']
            },
            'analysis_timestamp': datetime.utcnow().isoformat()
        }
        
        # Log search activity
        search_data = {
            'search_type': 'face_upload_analysis',
            'faces_detected': face_analysis['faces_detected'],
            'matches_found': search_results['total_matches'],
            'image_hash': image_hash,
            'results_summary': {
                'google_matches': len(search_results['google_images']),
                'social_profiles': len(search_results['social_profiles'])
            }
        }
        firebase_auth.log_search_activity(uid, search_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in upload_and_analyze: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during analysis'
        }), 500

@face_bp.route('/compare-faces', methods=['POST'])
@require_auth
def compare_faces():
    """
    Compare two face encodings
    """
    try:
        data = request.get_json()
        
        if not data or 'encoding1' not in data or 'encoding2' not in data:
            return jsonify({'error': 'Two face encodings required'}), 400
        
        encoding1 = data['encoding1']
        encoding2 = data['encoding2']
        
        # Compare faces
        comparison_result = face_engine.compare_faces(encoding1, encoding2)
        
        return jsonify({
            'success': True,
            'comparison': comparison_result,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in compare_faces: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error comparing faces'
        }), 500

@face_bp.route('/search-by-name', methods=['POST'])
@require_auth
def search_by_name():
    """
    Search for person by name across social media platforms
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Name parameter required'}), 400
        
        name = data['name']
        current_user = request.current_user
        uid = current_user.get('uid')
        
        # Search across platforms
        facebook_results = social_scraper.search_facebook_public(name)
        
        # Combine results
        search_results = {
            'name_searched': name,
            'facebook_profiles': facebook_results,
            'total_profiles': len(facebook_results),
            'search_timestamp': datetime.utcnow().isoformat()
        }
        
        # Log search activity
        search_data = {
            'search_type': 'name_search',
            'faces_detected': 0,
            'matches_found': len(facebook_results),
            'image_hash': None,
            'results_summary': {
                'name_searched': name,
                'facebook_profiles': len(facebook_results)
            }
        }
        firebase_auth.log_search_activity(uid, search_data)
        
        return jsonify({
            'success': True,
            'results': search_results
        })
        
    except Exception as e:
        logger.error(f"Error in search_by_name: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error searching by name'
        }), 500

@face_bp.route('/enhance-image', methods=['POST'])
@require_auth
def enhance_image():
    """
    Enhance image quality for better face recognition
    """
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save temporary file
        temp_path = f'/tmp/{secure_filename(file.filename)}'
        file.save(temp_path)
        
        # Enhance image
        enhanced_path = face_engine.enhance_image_quality(temp_path)
        
        # Read enhanced image
        with open(enhanced_path, 'rb') as f:
            enhanced_data = f.read()
        
        # Clean up temporary files
        if os.path.exists(temp_path):
            os.remove(temp_path)
        if os.path.exists(enhanced_path):
            os.remove(enhanced_path)
        
        # Upload enhanced image to Firebase
        current_user = request.current_user
        uid = current_user.get('uid')
        enhanced_url = firebase_auth.upload_image_to_storage(
            enhanced_data, 
            f"enhanced_{file.filename}", 
            uid
        )
        
        return jsonify({
            'success': True,
            'enhanced_image_url': enhanced_url,
            'message': 'Image enhanced successfully'
        })
        
    except Exception as e:
        logger.error(f"Error in enhance_image: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error enhancing image'
        }), 500

@face_bp.route('/search-history', methods=['GET'])
@require_auth
def get_search_history():
    """
    Get user's search history
    """
    try:
        current_user = request.current_user
        uid = current_user.get('uid')
        
        limit = request.args.get('limit', 50, type=int)
        
        history = firebase_auth.get_search_history(uid, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'total_records': len(history)
        })
        
    except Exception as e:
        logger.error(f"Error getting search history: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving search history'
        }), 500

@face_bp.route('/export-results', methods=['POST'])
@require_auth
def export_results():
    """
    Export search results as PDF report
    """
    try:
        data = request.get_json()
        
        if not data or 'search_results' not in data:
            return jsonify({'error': 'Search results data required'}), 400
        
        current_user = request.current_user
        uid = current_user.get('uid')
        
        # Get user profile for report header
        user_profile = firebase_auth.get_user_profile(uid)
        
        # Create PDF report (simplified implementation)
        report_data = {
            'officer_info': {
                'badge_number': user_profile.get('badge_number', 'Unknown'),
                'department': user_profile.get('department', 'Unknown'),
                'country': user_profile.get('country', 'Unknown')
            },
            'search_results': data['search_results'],
            'export_timestamp': datetime.utcnow().isoformat(),
            'case_number': data.get('case_number', 'N/A')
        }
        
        # In a real implementation, you would generate a PDF here
        # For now, return the structured data
        
        return jsonify({
            'success': True,
            'report_data': report_data,
            'message': 'Report generated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error exporting results: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error exporting results'
        }), 500

@face_bp.route('/system-stats', methods=['GET'])
@require_auth
def get_system_stats():
    """
    Get system statistics (for admin users)
    """
    try:
        current_user = request.current_user
        uid = current_user.get('uid')
        
        # Get user profile to check permissions
        user_profile = firebase_auth.get_user_profile(uid)
        
        if not user_profile or user_profile.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        # Return mock statistics
        stats = {
            'total_searches_today': 45,
            'total_users': 12,
            'active_users': 8,
            'successful_matches': 23,
            'system_uptime': '99.9%',
            'last_updated': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting system stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving system statistics'
        }), 500

