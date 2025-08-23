"""
TORA FACE - Face Recognition AI Module (Simplified)
Handles face detection and basic analysis using OpenCV
"""

import cv2
import numpy as np
import os
import logging
from typing import List, Dict, Tuple, Optional
import base64
from PIL import Image
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FaceRecognitionEngine:
    """
    Simplified face recognition engine for TORA FACE system
    Uses OpenCV for face detection and basic analysis
    """
    
    def __init__(self):
        self.similarity_threshold = float(os.getenv('SIMILARITY_THRESHOLD', 0.6))
        
        # Load OpenCV face detection models
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        
    def detect_faces(self, image_path: str) -> List[Dict]:
        """
        Detect faces in an image using OpenCV
        
        Args:
            image_path: Path to the image file
            
        Returns:
            List of dictionaries containing face data
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                logger.error(f"Could not load image: {image_path}")
                return []
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )
            
            face_data = []
            for i, (x, y, w, h) in enumerate(faces):
                # Extract face region
                face_roi = gray[y:y+h, x:x+w]
                
                # Detect eyes in face region for confidence scoring
                eyes = self.eye_cascade.detectMultiScale(face_roi)
                confidence = min(1.0, len(eyes) * 0.4 + 0.6)  # Higher confidence if eyes detected
                
                # Create simple face encoding (histogram of face region)
                face_encoding = self.create_face_encoding(face_roi)
                
                face_info = {
                    'face_id': i,
                    'encoding': face_encoding.tolist(),
                    'location': {
                        'top': int(y),
                        'right': int(x + w),
                        'bottom': int(y + h),
                        'left': int(x)
                    },
                    'confidence': float(confidence),
                    'width': int(w),
                    'height': int(h)
                }
                face_data.append(face_info)
                
            logger.info(f"Detected {len(face_data)} faces in image: {image_path}")
            return face_data
            
        except Exception as e:
            logger.error(f"Error detecting faces: {str(e)}")
            return []
    
    def create_face_encoding(self, face_roi: np.ndarray) -> np.ndarray:
        """
        Create a simple face encoding using histogram features
        
        Args:
            face_roi: Face region of interest
            
        Returns:
            Face encoding vector
        """
        try:
            # Resize face to standard size
            face_resized = cv2.resize(face_roi, (64, 64))
            
            # Calculate histogram features
            hist = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
            hist = hist.flatten()
            
            # Normalize histogram
            hist = hist / (np.sum(hist) + 1e-7)
            
            # Add some basic texture features
            # Calculate Local Binary Pattern-like features
            lbp_features = self.calculate_lbp_features(face_resized)
            
            # Combine histogram and texture features
            encoding = np.concatenate([hist[:128], lbp_features])  # Limit to 256 features total
            
            return encoding
            
        except Exception as e:
            logger.error(f"Error creating face encoding: {str(e)}")
            return np.zeros(256)
    
    def calculate_lbp_features(self, image: np.ndarray) -> np.ndarray:
        """
        Calculate simplified Local Binary Pattern features
        
        Args:
            image: Grayscale image
            
        Returns:
            LBP feature vector
        """
        try:
            # Simple LBP-like calculation
            h, w = image.shape
            features = []
            
            # Sample points around center pixels
            for i in range(1, h-1, 4):  # Sample every 4th pixel
                for j in range(1, w-1, 4):
                    center = image[i, j]
                    
                    # Compare with 8 neighbors
                    neighbors = [
                        image[i-1, j-1], image[i-1, j], image[i-1, j+1],
                        image[i, j+1], image[i+1, j+1], image[i+1, j],
                        image[i+1, j-1], image[i, j-1]
                    ]
                    
                    # Create binary pattern
                    pattern = sum([1 if n >= center else 0 for n in neighbors])
                    features.append(pattern)
            
            # Convert to histogram
            features = np.array(features)
            hist, _ = np.histogram(features, bins=16, range=(0, 8))
            hist = hist / (np.sum(hist) + 1e-7)
            
            return hist
            
        except Exception as e:
            logger.error(f"Error calculating LBP features: {str(e)}")
            return np.zeros(16)
    
    def analyze_face_attributes(self, image_path: str) -> Dict:
        """
        Analyze basic face attributes using OpenCV
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing face attributes
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return self.get_default_attributes()
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
            
            if len(faces) == 0:
                return self.get_default_attributes()
            
            # Take the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Basic attribute estimation
            attributes = {
                'age': self.estimate_age(gray[y:y+h, x:x+w]),
                'gender': self.estimate_gender(gray[y:y+h, x:x+w]),
                'emotion': 'Neutral',  # Simplified - would need more complex analysis
                'race': 'Unknown',     # Simplified - would need more complex analysis
                'face_size': f"{w}x{h}",
                'face_quality': self.assess_face_quality(gray[y:y+h, x:x+w])
            }
            
            return attributes
            
        except Exception as e:
            logger.error(f"Error analyzing face attributes: {str(e)}")
            return self.get_default_attributes()
    
    def get_default_attributes(self) -> Dict:
        """Return default attributes when analysis fails"""
        return {
            'age': 'Unknown',
            'gender': 'Unknown',
            'emotion': 'Unknown',
            'race': 'Unknown',
            'face_size': 'Unknown',
            'face_quality': 'Unknown'
        }
    
    def estimate_age(self, face_roi: np.ndarray) -> str:
        """
        Simple age estimation based on face characteristics
        """
        try:
            # Very basic age estimation based on face texture
            # Calculate variance as a proxy for wrinkles/texture
            variance = np.var(face_roi)
            
            if variance < 200:
                return "Young (18-30)"
            elif variance < 400:
                return "Adult (30-50)"
            else:
                return "Mature (50+)"
                
        except:
            return "Unknown"
    
    def estimate_gender(self, face_roi: np.ndarray) -> str:
        """
        Simple gender estimation (very basic)
        """
        try:
            # Very basic estimation - in reality would need trained models
            # This is just a placeholder
            h, w = face_roi.shape
            aspect_ratio = h / w
            
            if aspect_ratio > 1.2:
                return "Female"
            else:
                return "Male"
                
        except:
            return "Unknown"
    
    def assess_face_quality(self, face_roi: np.ndarray) -> str:
        """
        Assess the quality of the detected face
        """
        try:
            # Calculate sharpness using Laplacian variance
            laplacian_var = cv2.Laplacian(face_roi, cv2.CV_64F).var()
            
            if laplacian_var > 500:
                return "High"
            elif laplacian_var > 100:
                return "Medium"
            else:
                return "Low"
                
        except:
            return "Unknown"
    
    def compare_faces(self, known_encoding: List[float], unknown_encoding: List[float]) -> Dict:
        """
        Compare two face encodings using cosine similarity
        
        Args:
            known_encoding: Face encoding of known person
            unknown_encoding: Face encoding of unknown person
            
        Returns:
            Dictionary containing comparison results
        """
        try:
            # Convert to numpy arrays
            known_np = np.array(known_encoding)
            unknown_np = np.array(unknown_encoding)
            
            # Calculate cosine similarity
            dot_product = np.dot(known_np, unknown_np)
            norm_known = np.linalg.norm(known_np)
            norm_unknown = np.linalg.norm(unknown_np)
            
            if norm_known == 0 or norm_unknown == 0:
                similarity = 0
            else:
                similarity = dot_product / (norm_known * norm_unknown)
            
            # Convert to percentage
            similarity_percentage = max(0, similarity * 100)
            
            # Calculate distance (inverse of similarity)
            distance = 1 - similarity
            
            # Determine if it's a match
            is_match = similarity >= self.similarity_threshold
            
            return {
                'is_match': is_match,
                'similarity_percentage': round(similarity_percentage, 2),
                'distance': round(distance, 4),
                'confidence': 'High' if similarity_percentage > 80 else 'Medium' if similarity_percentage > 60 else 'Low'
            }
            
        except Exception as e:
            logger.error(f"Error comparing faces: {str(e)}")
            return {
                'is_match': False,
                'similarity_percentage': 0,
                'distance': 1.0,
                'confidence': 'Error'
            }
    
    def process_uploaded_image(self, image_data: bytes) -> Dict:
        """
        Process uploaded image and extract face data
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary containing processed face data
        """
        try:
            # Save temporary image
            temp_path = '/tmp/uploaded_image.jpg'
            with open(temp_path, 'wb') as f:
                f.write(image_data)
            
            # Detect faces
            faces = self.detect_faces(temp_path)
            
            # Analyze attributes for the first face
            attributes = {}
            if faces:
                attributes = self.analyze_face_attributes(temp_path)
            
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                'faces_detected': len(faces),
                'faces': faces,
                'attributes': attributes,
                'status': 'success' if faces else 'no_faces_detected'
            }
            
        except Exception as e:
            logger.error(f"Error processing uploaded image: {str(e)}")
            return {
                'faces_detected': 0,
                'faces': [],
                'attributes': {},
                'status': 'error',
                'error': str(e)
            }
    
    def enhance_image_quality(self, image_path: str) -> str:
        """
        Enhance image quality for better face recognition
        
        Args:
            image_path: Path to the original image
            
        Returns:
            Path to the enhanced image
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            
            # Apply image enhancement techniques
            # 1. Histogram equalization for better contrast
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            enhanced_gray = cv2.equalizeHist(gray)
            enhanced_image = cv2.cvtColor(enhanced_gray, cv2.COLOR_GRAY2BGR)
            
            # 2. Gaussian blur to reduce noise
            enhanced_image = cv2.GaussianBlur(enhanced_image, (3, 3), 0)
            
            # 3. Sharpen the image
            kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
            enhanced_image = cv2.filter2D(enhanced_image, -1, kernel)
            
            # Save enhanced image
            enhanced_path = image_path.replace('.jpg', '_enhanced.jpg').replace('.png', '_enhanced.png')
            cv2.imwrite(enhanced_path, enhanced_image)
            
            return enhanced_path
            
        except Exception as e:
            logger.error(f"Error enhancing image: {str(e)}")
            return image_path  # Return original path if enhancement fails

# Initialize the face recognition engine
face_engine = FaceRecognitionEngine()

