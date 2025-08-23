import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, redirect, url_for, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tora_face_security_key_2024_burundi_rwanda')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB max file size

# Enable CORS for all routes
CORS(app, origins="*")

@app.route('/')
def index():
    """Serve the main application page"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'TORA FACE',
        'version': '1.0.0'
    })

@app.route('/api/face/analyze', methods=['POST'])
def analyze_face():
    """Face analysis endpoint (simplified)"""
    return jsonify({
        'status': 'success',
        'message': 'Face analysis service is ready. Please configure Firebase to enable full functionality.',
        'faces_detected': 0,
        'demo_mode': True
    })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

