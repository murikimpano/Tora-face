import os
import sys
import hashlib
from datetime import datetime
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Optional: Import your Firebase utils
try:
    from src.firebase.auth import firebase_auth
    from src.ai.face_recognition import face_engine
    from src.ai.social_media_scraper import social_scraper
    USE_FIREBASE = True
except ImportError:
    USE_FIREBASE = False

# Load environment variables
load_dotenv()

# Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tora_face_security_key_2025')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB

# Enable CORS
CORS(app, origins="*")

# ---------- Routes ----------

@app.route('/')
def index():
    """Serve main SPA"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'TORA FACE',
        'version': '1.0.0'
    })

@app.route('/api/face/analyze', methods=['POST'])
def analyze_face():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    image_data = file.read()
    image_hash = hashlib.md5(image_data).hexdigest()

    # Demo response if Firebase or face_engine is missing
    if not USE_FIREBASE:
        return jsonify({
            'status': 'success',
            'message': 'Demo mode: Face recognition not configured.',
            'faces_detected': 0,
            'image_hash': image_hash,
            'demo_mode': True
        })

    # Process uploaded image
    face_analysis = face_engine.process_uploaded_image(image_data)

    if face_analysis['status'] == 'error':
        return jsonify({'error': face_analysis.get('error', 'Unknown error')}), 500

    if face_analysis['faces_detected'] == 0:
        return jsonify({
            'status': 'success',
            'message': 'No faces detected',
            'faces_detected': 0
        })

    # Upload image to Firebase Storage
    filename = f"{image_hash}_{file.filename}"
    current_user = request.form.get('uid', 'demo_user')
    image_url = firebase_auth.upload_image_to_storage(image_data, filename, current_user)

    # Optional: Social media search
    primary_face = face_analysis['faces'][0]
    search_query = request.form.get('search_query', 'person face')
    search_results = social_scraper.comprehensive_search(primary_face['encoding'], search_query)

    # Log search
    firebase_auth.log_search_activity(current_user, {
        'search_type': 'face_upload_analysis',
        'faces_detected': face_analysis['faces_detected'],
        'matches_found': search_results['total_matches'],
        'image_hash': image_hash
    })

    return jsonify({
        'status': 'success',
        'image_url': image_url,
        'faces_detected': face_analysis['faces_detected'],
        'primary_face': primary_face,
        'search_results': search_results,
        'analysis_timestamp': datetime.utcnow().isoformat()
    })

@app.route('/api/search-history/<uid>')
def search_history(uid):
    if not USE_FIREBASE:
        return jsonify({'history': [], 'demo_mode': True})
    history = firebase_auth.get_search_history(uid, limit=50)
    return jsonify({'history': history})

# ---------- Error handlers ----------

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# ---------- Run App ----------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
