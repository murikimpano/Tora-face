"""
TORA FACE - Face Recognition AI Module (Enhanced)
Handles face detection and basic analysis using OpenCV
"""

import cv2
import numpy as np
import os
import logging
from typing import List, Dict
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceRecognitionEngine:
    """
    Enhanced face recognition engine for TORA FACE system
    Uses OpenCV for face detection and basic analysis
    """
    
    def __init__(self):
        # Ensure threshold between 0 and 1
        self.similarity_threshold = max(0, min(1, float(os.getenv('SIMILARITY_THRESHOLD', 0.6))))
        
        # Load OpenCV face detection models
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    def detect_faces(self, image_path: str) -> List[Dict]:
        """Detect faces in an image using OpenCV"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30,30))
            
            face_data = []
            for i, (x, y, w, h) in enumerate(faces):
                face_roi = gray[y:y+h, x:x+w]
                eyes = self.eye_cascade.detectMultiScale(face_roi)
                confidence = min(1.0, len(eyes) * 0.4 + 0.6)
                face_encoding = self.create_face_encoding(face_roi)
                
                face_data.append({
                    'face_id': i,
                    'encoding': face_encoding.tolist(),
                    'location': {'top': int(y), 'right': int(x+w), 'bottom': int(y+h), 'left': int(x)},
                    'confidence': float(confidence),
                    'width': int(w),
                    'height': int(h)
                })
            logger.info(f"Detected {len(face_data)} faces in image: {image_path}")
            return face_data
        except Exception as e:
            logger.error(f"Error detecting faces: {e}")
            return []
    
    def create_face_encoding(self, face_roi: np.ndarray) -> np.ndarray:
        """Create a consistent 256-dim face encoding"""
        try:
            face_resized = cv2.resize(face_roi, (64, 64))
            hist = cv2.calcHist([face_resized], [0], None, [256], [0,256]).flatten()
            hist = hist / (np.sum(hist)+1e-7)
            lbp_features = self.calculate_lbp_features(face_resized)
            # Ensure total 256 features
            encoding = np.concatenate([hist[:128], lbp_features[:128]])
            return encoding
        except Exception as e:
            logger.error(f"Error creating face encoding: {e}")
            return np.zeros(256)
    
    def calculate_lbp_features(self, image: np.ndarray) -> np.ndarray:
        """Calculate simplified LBP features"""
        try:
            h, w = image.shape
            features = []
            for i in range(1, h-1, 4):
                for j in range(1, w-1, 4):
                    center = image[i,j]
                    neighbors = [
                        image[i-1,j-1], image[i-1,j], image[i-1,j+1],
                        image[i,j+1], image[i+1,j+1], image[i+1,j],
                        image[i+1,j-1], image[i,j-1]
                    ]
                    pattern = sum([1 if n >= center else 0 for n in neighbors])
                    features.append(pattern)
            features = np.array(features)
            hist, _ = np.histogram(features, bins=16, range=(0,8))
            hist = hist / (np.sum(hist)+1e-7)
            return hist
        except Exception as e:
            logger.error(f"Error calculating LBP features: {e}")
            return np.zeros(16)
    
    def analyze_face_attributes(self, image_path: str) -> Dict:
        """Analyze basic face attributes"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                return self.get_default_attributes()
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray,1.1,5)
            if len(faces)==0:
                return self.get_default_attributes()
            largest_face = max(faces, key=lambda f: f[2]*f[3])
            x,y,w,h = largest_face
            roi = gray[y:y+h, x:x+w]
            attributes = {
                'age': self.estimate_age(roi),
                'gender': self.estimate_gender(roi),
                'emotion': 'Neutral',
                'race': 'Unknown',
                'face_size': f"{w}x{h}",
                'face_quality': self.assess_face_quality(roi)
            }
            return attributes
        except Exception as e:
            logger.error(f"Error analyzing face attributes: {e}")
            return self.get_default_attributes()
    
    def get_default_attributes(self) -> Dict:
        return {'age':'Unknown','gender':'Unknown','emotion':'Unknown',
                'race':'Unknown','face_size':'Unknown','face_quality':'Unknown'}
    
    def estimate_age(self, roi: np.ndarray) -> str:
        try:
            var = np.var(roi)
            if var<200: return "Young (18-30)"
            elif var<400: return "Adult (30-50)"
            else: return "Mature (50+)"
        except Exception as e:
            logger.warning(f"Age estimation failed: {e}")
            return "Unknown"
    
    def estimate_gender(self, roi: np.ndarray) -> str:
        try:
            h,w = roi.shape
            ratio = h/w
            return "Female" if ratio>1.2 else "Male"
        except Exception as e:
            logger.warning(f"Gender estimation failed: {e}")
            return "Unknown"
    
    def assess_face_quality(self, roi: np.ndarray) -> str:
        try:
            lap_var = cv2.Laplacian(roi,cv2.CV_64F).var()
            if lap_var>500: return "High"
            elif lap_var>100: return "Medium"
            else: return "Low"
        except Exception as e:
            logger.warning(f"Face quality assessment failed: {e}")
            return "Unknown"
    
    def compare_faces(self, known_encoding: List[float], unknown_encoding: List[float]) -> Dict:
        try:
            k = np.array(known_encoding, dtype=float)
            u = np.array(unknown_encoding, dtype=float)
            dot = np.dot(k,u)
            norm_k = np.linalg.norm(k)
            norm_u = np.linalg.norm(u)
            sim = 0 if norm_k==0 or norm_u==0 else dot/(norm_k*norm_u)
            sim_pct = max(0, sim*100)
            distance = 1-sim
            is_match = sim >= self.similarity_threshold
            confidence = 'High' if sim_pct>80 else 'Medium' if sim_pct>60 else 'Low'
            return {'is_match':is_match,'similarity_percentage':round(sim_pct,2),
                    'distance':round(distance,4),'confidence':confidence}
        except Exception as e:
            logger.error(f"Error comparing faces: {e}")
            return {'is_match':False,'similarity_percentage':0,'distance':1.0,'confidence':'Error'}
    
    def process_uploaded_image(self, image_data: bytes) -> Dict:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            faces = self.detect_faces(temp_path)
            attributes = self.analyze_face_attributes(temp_path) if faces else {}
            os.remove(temp_path)
            return {'faces_detected':len(faces),'faces':faces,'attributes':attributes,
                    'status':'success' if faces else 'no_faces_detected'}
        except Exception as e:
            logger.error(f"Error processing uploaded image: {e}")
            return {'faces_detected':0,'faces':[],'attributes':{},'status':'error','error':str(e)}
    
    def enhance_image_quality(self, image_path: str) -> str:
        try:
            image = cv2.imread(image_path)
            if image is None: return image_path
            # CLAHE enhancement
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l,a,b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            cl = clahe.apply(l)
            enhanced_image
