# TORA FACE - Deployment Guide

## Overview
TORA FACE is a secure facial recognition system designed for police and national security officers in Burundi and Rwanda.

## Prerequisites
1. Firebase project with Authentication, Firestore, and Storage enabled
2. Domain name (www.tora-face.bi)
3. SSL certificate
4. Server with Python 3.11+ support

## Firebase Configuration

### 1. Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project named "tora-face-security"
3. Enable Authentication with Email/Password provider
4. Enable Firestore Database
5. Enable Storage

### 2. Configure Authentication
- Enable Email/Password authentication
- Set up email verification
- Configure password reset
- Add authorized domains (including your custom domain)

### 3. Firestore Security Rules
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Police users collection
    match /police_users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      allow read: if request.auth != null && 
        get(/databases/$(database)/documents/police_users/$(request.auth.uid)).data.role == 'admin';
    }
    
    // Search history
    match /search_history/{document} {
      allow read, write: if request.auth != null && 
        resource.data.user_uid == request.auth.uid;
      allow read: if request.auth != null && 
        get(/databases/$(database)/documents/police_users/$(request.auth.uid)).data.role == 'admin';
    }
  }
}
```

### 4. Storage Security Rules
```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /uploads/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## Environment Configuration

### 1. Update .env file
```bash
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
```

### 2. Update Firebase Config in Frontend
Update `src/static/js/firebase-config.js` with your actual Firebase configuration.

## Deployment Options

### Option 1: Firebase Hosting (Recommended)
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize Firebase in project directory
firebase init hosting

# Deploy
firebase deploy
```

### Option 2: Traditional Server Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn src.main:app --bind 0.0.0.0:8000 --workers 4
```

### Option 3: Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

## Security Checklist

### 1. Authentication Security
- [x] Email verification required
- [x] Strong password requirements
- [x] Rate limiting on login attempts
- [x] Secure session management
- [x] Role-based access control

### 2. Data Security
- [x] All data encrypted in transit (HTTPS)
- [x] Sensitive data encrypted at rest
- [x] User activity logging
- [x] Secure file upload validation
- [x] Input sanitization

### 3. API Security
- [x] Authentication required for all endpoints
- [x] CORS properly configured
- [x] Request rate limiting
- [x] Input validation
- [x] Error handling without information disclosure

### 4. Infrastructure Security
- [x] HTTPS enforced
- [x] Security headers configured
- [x] Regular security updates
- [x] Monitoring and alerting
- [x] Backup and recovery procedures

## Domain Configuration

### 1. DNS Settings for www.tora-face.bi
```
Type: A
Name: @
Value: [Firebase Hosting IP]

Type: CNAME
Name: www
Value: tora-face-security.web.app
```

### 2. SSL Certificate
- Use Firebase Hosting automatic SSL
- Or configure custom SSL certificate

## Monitoring and Maintenance

### 1. Logging
- Application logs via Python logging
- Firebase Analytics for user behavior
- Error tracking and alerting

### 2. Performance Monitoring
- Response time monitoring
- Database query optimization
- Image processing performance

### 3. Security Monitoring
- Failed login attempt monitoring
- Unusual activity detection
- Regular security audits

## User Management

### 1. Police Officer Registration
Only authorized personnel should be able to register. Consider:
- Manual approval process
- Verification of badge numbers
- Department confirmation

### 2. Admin Users
- Create admin users through Firebase Console
- Set role to 'admin' in Firestore
- Grant additional permissions

## Backup and Recovery

### 1. Database Backup
- Firestore automatic backups
- Regular export of critical data
- Test recovery procedures

### 2. File Backup
- Firebase Storage automatic replication
- Regular backup of uploaded images
- Retention policy configuration

## Legal and Compliance

### 1. Data Protection
- GDPR compliance for EU data
- Local data protection laws
- User consent management

### 2. Law Enforcement Use
- Proper authorization procedures
- Audit trail maintenance
- Data retention policies

## Support and Maintenance

### 1. Technical Support
- Monitor system health
- Regular updates and patches
- Performance optimization

### 2. User Support
- Training materials for officers
- Help documentation
- Support contact information

## Troubleshooting

### Common Issues
1. **Firebase Connection Errors**: Check API keys and project configuration
2. **Face Detection Failures**: Verify OpenCV installation and image formats
3. **Authentication Issues**: Check Firebase Auth configuration
4. **Performance Issues**: Monitor server resources and optimize queries

### Logs Location
- Application logs: `/var/log/tora-face/`
- Firebase logs: Firebase Console
- Server logs: System log files

## Contact Information
For technical support and maintenance:
- System Administrator: [contact information]
- Firebase Project Owner: [contact information]
- Emergency Contact: [contact information]

