1️⃣ Project Structure (Full Todo Version)

tora-face/
│
├─ src/
│   ├─ __init__.py
│   ├─ main.py                  # Full backend Flask app
│   ├─ main_simple.py           # Simple backend for demo
│   ├─ models/
│   │   ├─ __init__.py
│   │   └─ user.py              # SQLAlchemy User model
│   ├─ routes/
│   │   ├─ __init__.py
│   │   ├─ auth.py              # signup/login
│   │   ├─ user.py              # user management
│   │   └─ face_recognition.py  # AI face detection routes
│   ├─ ai/
│   │   └─ face_recognition.py  # OpenCV face detection
│   └─ firebase/
│       └─ auth.py              # Firebase placeholder
│
├─ static/
│   ├─ css/
│   │   └─ style.css
│   ├─ js/
│   │   └─ firebase-config.js
│   └─ images/
│
├─ templates/
│   ├─ signup.html
│   └─ login.html
│
├─ database/
│   └─ app.db
│
├─ social_media_scraper.py
├─ security_check.py
├─ requirements.txt
├─ requirements_simple.txt
├─ .env
├─ LICENSE
└─ README.md


---

2️⃣ Backend – main.py (Full Version)

import os
from flask import Flask, send_from_directory, request, redirect, url_for, jsonify, render_template
from flask_cors import CORS
from flask_talisman import Talisman
from dotenv import load_dotenv
from src.models.user import db, User
from src.routes.auth import auth_bp
from src.routes.user import user_bp
from src.routes.face_recognition import face_bp

load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'tora_face_security_key_2024_burundi_rwanda')
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join('database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="murikimpanotv@gmail.com").first():
        default_user = User(username="Admin", email="murikimpanotv@gmail.com", password="685194Gn.")
        db.session.add(default_user)
        db.session.commit()

if os.getenv('FLASK_ENV') == 'production':
    Talisman(app, force_https=True)

CORS(app, origins="*")

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api/user')
app.register_blueprint(face_bp, url_prefix='/api/face')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)


---

3️⃣ Models – user.py

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="user")


---

4️⃣ Routes – auth.py

from flask import Blueprint, request, jsonify, render_template
from src.models.user import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.form
        user = User(username=data['username'], email=data['email'], password=data['password'])
        db.session.add(user)
        db.session.commit()
        return jsonify({"status":"success","message":"Account created"})
    return render_template("signup.html")

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        user = User.query.filter_by(email=data['email'], password=data['password']).first()
        if user:
            return jsonify({"status":"success","message":"Login successful"})
        return jsonify({"status":"error","message":"Invalid credentials"})
    return render_template("login.html")


---

5️⃣ AI Module – face_recognition.py

import cv2
import numpy as np

def detect_faces(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return faces


---

6️⃣ Social Media Scraper – social_media_scraper.py

import requests, logging
from bs4 import BeautifulSoup
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent':'Mozilla/5.0'})

    def search_google_images(self, query:str, num:int=10)->List[Dict]:
        url = f"https://www.google.com/search?q={query}&tbm=isch"
        r = self.session.get(url)
        soup = BeautifulSoup(r.content,'html.parser')
        imgs = []
        for i,img in enumerate(soup.find_all('img')[:num]):
            imgs.append({'url':img.get('src'),'alt':img.get('alt','')})
        logger.info(f"Found {len(imgs)} images for {query}")
        return imgs

social_scraper = SocialMediaScraper()


---

7️⃣ Templates – signup.html & login.html

signup.html (already provided)

login.html:


<!DOCTYPE html>
<html>
<head>
<title>Login - Tora Face</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<h2>Login</h2>
<form action="/api/auth/login" method="POST">
<label>Email:</label>
<input type="email" name="email" required><br><br>
<label>Password:</label>
<input type="password" name="password" required><br><br>
<button type="submit">Login</button>
</form>
<p>Don't have an account? <a href="signup.html">Sign Up</a></p>
</body>
</html>


---

8️⃣ Security Check – security_check.py

> Koresha script yawe ya security_check.py (yuzuye kandi igenzura environment variables, file permissions, dependencies, logging, HTTPS, Firebase, input validation).




---

9️⃣ Requirements.txt

flask==3.1.1
flask-cors==6.0.0
flask-talisman==1.0.1
python-dotenv==1.1.1
gunicorn==23.0.0
pillow==11.3.0
opencv-python==4.11.0.86
numpy==2.3.1
requests==2.32.4
beautifulsoup4==4.12.2

