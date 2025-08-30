import os
from flask import Flask, send_from_directory, request, render_template, redirect, url_for
from flask_cors import CORS
from flask_talisman import Talisman
from dotenv import load_dotenv
from src.models.user import db, User
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.face_recognition import face_bp

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tora_face_security_key_2024_burundi_rwanda')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))  # 16MB max file size
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security
if os.getenv('FLASK_ENV') == 'production':
    Talisman(app, force_https=True)
    
    @app.before_request
    def force_https():
        if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
            return redirect(request.url.replace('http://', 'https://'))

# Enable CORS
CORS(app, origins="*")

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="murikimpanotv@gmail.com").first():
        default_user = User(username="Admin", email="murikimpanotv@gmail.com", password="685194Gn.")
        db.session.add(default_user)
        db.session.commit()
        print("Default admin account created successfully!")

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(face_bp, url_prefix='/api/face')

# Serve static files and SPA index.html
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    full_path = os.path.join(static_folder_path, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(static_folder_path, path)
    index_path = os.path.join(static_folder_path, 'index.html')
    if os.path.exists(index_path):
        return send_from_directory(static_folder_path, 'index.html')
    return "index.html not found", 404

# Signup page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Hano shyiramo code yo kubika muri database
        return f"Account created successfully for {username}"
    return render_template('signup.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Hano shyiramo code yo kugenzura credentials
        return f"Welcome back {email}!"
    return render_template('login.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
