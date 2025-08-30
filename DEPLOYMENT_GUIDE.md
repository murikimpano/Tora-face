TORA FACE – Complete Deployment Guide

1️⃣ Overview

TORA FACE ni system ikoresha AI facial recognition mu gushakisha abantu babuze, ikaba igenewe abashinzwe umutekano mu Burundi na Rwanda.
Intego:

Gutahura abantu babuze bifashishijwe isura yabo

Kuhuza ababuze n’imiryango yabo

Gutanga amakuru afasha inzego z’umutekano n’ubutabazi



---

2️⃣ Prerequisites

1. Firebase project (Authentication, Firestore, Storage enabled)


2. Domain name (e.g., www.tora-face.bi)


3. SSL certificate


4. Server na Python 3.11+ support


5. Gunicorn cyangwa Docker (production deployment)




---

3️⃣ Firebase Configuration

3.1 Create Firebase Project

Go to Firebase Console

Create project: tora-face-security

Enable Email/Password Authentication

Enable Firestore Database

Enable Storage


3.2 Authentication Settings

Email verification required

Password reset endpoint

Add authorized domains

Only verified users can login


3.3 Firestore Security Rules

rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {

    match /police_users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null &&
                  get(/databases/$(database)/documents/police_users/$(request.auth.uid)).data.role == 'admin';
    }

    match /search_history/{docId} {
      allow read, write: if request.auth != null && resource.data.user_uid == request.auth.uid;
      allow read: if request.auth != null &&
                  get(/databases/$(database)/documents/police_users/$(request.auth.uid)).data.role == 'admin';
    }
  }
}

3.4 Storage Security Rules

rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /uploads/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}


---

4️⃣ Environment Configuration

4.1 .env File

# Firebase Configuration
FIREBASE_PROJECT_ID=tora-face-security
FIREBASE_PRIVATE_KEY_ID=your_actual_private_key_id
FIREBASE_PRIVATE_KEY=your_actual_private_key
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@tora-face-security.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your_actual_client_id
FIREBASE_AUTH_URI=https://accounts.google.com/o/oauth2/auth
FIREBASE_TOKEN_URI=https://oauth2.googleapis.com/token
FIREBASE_AUTH_PROVIDER_X509_CERT_URL=https://www.googleapis.com/oauth2/v1/certs
FIREBASE_CLIENT_X509_CERT_URL=your_actual_client_cert_url

# Firebase Web Config
FIREBASE_API_KEY=your_actual_api_key
FIREBASE_AUTH_DOMAIN=tora-face-security.firebaseapp.com
FIREBASE_DATABASE_URL=https://tora-face-security-default-rtdb.firebaseio.com
FIREBASE_STORAGE_BUCKET=tora-face-security.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_actual_sender_id
FIREBASE_APP_ID=your_actual_app_id

# Security
SECRET_KEY=generate_a_strong_secret_key_here
JWT_SECRET_KEY=generate_a_strong_jwt_secret_here

# Production Settings
FLASK_ENV=production
DEBUG=False
MAX_CONTENT_LENGTH=16777216

4.2 Update Frontend Firebase Config

Update src/static/js/firebase-config.js na credentials zawe.



---

5️⃣ Backend Setup

5.1 Install Dependencies

pip install -r requirements.txt

5.2 Database Initialization

db.create_all() muri main.py cyangwa migrations niba ukoresha Flask-Migrate


5.3 Run Server

Local:


python src/main.py

Production with Gunicorn:


gunicorn src.main:app --bind 0.0.0.0:8000 --workers 4

5.4 Optional Docker Deployment

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]


---

6️⃣ Security Enhancements

1. Authentication

Email verification required

Password hashing with SHA256

JWT tokens for session management

Rate limiting login attempts



2. Input Validation

Sanitize all inputs (signup/login/search)

Validate image uploads (size, type, format)



3. Role-based Access

Admin vs Police officer

Only authorized users can access sensitive endpoints



4. Data Security

HTTPS enforced

Sensitive data encrypted at rest

Audit logs for user actions

File upload validation



5. CORS

Restrict to allowed domains instead of *





---

7️⃣ Domain & SSL

DNS:


Type: A     Name: @     Value: [Firebase Hosting IP]
Type: CNAME Name: www   Value: tora-face-security.web.app

SSL:

Firebase automatic SSL or custom certificate




---

8️⃣ Monitoring & Logging

Python logging: /var/log/tora-face/

Firebase Analytics: user behavior

Server monitoring: CPU, RAM, image processing

Security monitoring: failed login attempts, unusual activity



---

9️⃣ Backup & Recovery

Firestore: automatic + scheduled exports

Storage: automatic replication + retention policy

Test restore procedures regularly



---

🔟 User Management

Police officer registration: manual approval, badge verification

Admin creation: via Firebase console, role='admin'



---

1️⃣1️⃣ Legal & Compliance

GDPR compliance for EU data

Local data protection laws

Law enforcement authorization and audit trails

Data retention policies



---

1️⃣2️⃣ Support

Technical: monitoring, patches, updates

User: help docs, training materials, contact info



---

1️⃣3️⃣ Troubleshooting

Firebase connection errors → check API keys

Face detection failures → verify OpenCV and image format

Authentication issues → check Firebase Auth config

Performance issues → monitor resources, optimize queries
