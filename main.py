import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, request, redirect, url_for
from flask_cors import CORS
from flask_talisman import Talisman
from dotenv import load_dotenv
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.face_recognition import face_bp

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tora_face_security_key_2024_burundi_rwanda')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB max file size

# Security configuration
if os.getenv('FLASK_ENV') == 'production':
    # Force HTTPS in production
    Talisman(app, force_https=True)
    
    @app.before_request
    def force_https():
        if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'))

# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(face_bp, url_prefix='/api/face')

# uncomment if you need to use database
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()
from src.models.user import User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="murikimpanotv@gmail.com").first():
        default_user = User(username="Admin", email="murikimpanotv@gmail.com", password="685194Gn.")
        db.session.add(default_user)
        db.session.commit()
        print("Default admin account created successfully!")
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Signup
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Aha twoshira code ibika mu database (nk'ukoresha SQLite, Firebase, MongoDB)
        return f"Account created successfully for {username}"
    return render_template('signup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Aha twoshira code igenzura niba email/password bihuye na database
        return f"Welcome back {email}!"
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
