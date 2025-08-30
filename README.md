
**Tora Face** ni application ikoresha ubwenge bw’ubukorano (AI) mu gufasha gushakisha abantu babuze.  
Ukoresheje isura (photo), system irasesengura amakuru yerekeye uwo muntu, harimo ibimuranga, aho aheruka kugaragara, n’ahashobora kuba ari. Ibi bifasha guhuza uwo muntu n’umuryango we ndetse na Leta.

---

## 🌍 Switch Language / Multilingual

- 🇧🇮 Kirundi
- 🇷🇼 Kinyarwanda
- 🇬🇧 English
- 🇰🇪 Swahili
- 🇫🇷 Français

*(Gushyiramo frontend button ihindura language niyo byakora.)*

---

## 🎯 Intego

- Gutahura abantu babuze bifashishijwe isura yabo  
- Kuhuza ababuze n’imiryango yabo  
- Gutanga amakuru afasha inzego zishinzwe umutekano n’ubutabazi  

---

## ⚙️ Ikoreshwa

Iyi website ikoreshwa na:

- Abanyeshuri biga ikoranabuhanga  
- Abashakashatsi mu bijyanye na AI na Data Science  
- Inzego z’igihugu zishinzwe umutekano n’ubutabazi  

---

## 💻 Ikozwe hifashishijwe

- HTML, CSS, JavaScript  
- Python (mu gutahura amasura)  
- OpenCV na face-recognition  
- Bootstrap (mu gutunganya imbonerahamwe)  
- Firebase / MongoDB (kubika amakuru)  

---

## 📦 Ibisabwa (Dependencies)

- Python 3.10+  
- face_recognition  
- opencv-python  
- Flask / Django  
- Firebase SDK (niba ukoresha Firebase)  

---

## 🚀 Uko wakwifashisha

1. **Clone project**:
```bash
git clone https://github.com/Murikimpano/tora-face.git

2. Injira muri folder yayo:



cd tora-face

3. Shyiraho dependencies:



pip install -r requirements.txt

4. Tangira server:



python app.py


---

🔧 Deployment Options

1. Firebase Hosting (Recommended)

npm install -g firebase-tools
firebase login
firebase init hosting
firebase deploy

2. Traditional Server Deployment

pip install -r requirements.txt
gunicorn src.main:app --bind 0.0.0.0:8000 --workers 4

3. Docker Deployment

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]


---

🔒 Security Checklist

1. Authentication Security

Email verification required

Strong password requirements

Rate limiting on login attempts

Secure session management

Role-based access control



2. Data Security

All data encrypted in transit (HTTPS)

Sensitive data encrypted at rest

User activity logging

Secure file upload validation

Input sanitization



3. API Security

Authentication required for all endpoints

CORS properly configured

Request rate limiting

Input validation

Error handling without information disclosure



4. Infrastructure Security

HTTPS enforced

Security headers configured

Regular security updates

Monitoring and alerting

Backup and recovery procedures





---

🌐 Firebase Configuration

Enable Authentication (Email/Password)

Firestore Database

Storage

Add authorized domains

Update .env and firebase-config.js na credentials zawe



---

📄 License

Iyi project yatanzwe hakoreshejwe MIT License.

Abandi bashobora kuyikoresha, kuyihindura no kuyisakaza

Bagomba kugaragaza ko yakozwe na Muriki Mpano

Ntigira garanti: ukoresha uko iri, nta burinzi cyangwa inshingano nyiri software agufitiye



---

🤝 Umwanditsi

MurikiMpano
*DJ GNB FLASH BOY*
AI & Tech Enthusiast
Email: murikimpanotv@gmail.com
GitHub: github.com/Murikimpano


---

💬 Ibitekerezo

Niba ufite igitekerezo, ikibazo cyangwa ubufasha kuri iyi project, ntutindiganye kuwandikira.

---
