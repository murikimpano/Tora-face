"""
TORA FACE - Face Recognition API (FastAPI)
"""

import os
import hashlib
import logging
import tempfile
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.firebase.auth import firebase_auth, require_auth_fastapi
from src.ai.face_recognition import face_engine
from src.ai.social_media_scraper import social_scraper

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tora-face-api")

# Allowed image extensions
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = FastAPI(title="TORA FACE API", version="2.0")

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def save_temp_file(file: UploadFile) -> str:
    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        return tmp.name

@app.post("/upload-and-analyze")
async def upload_and_analyze(
    image: UploadFile = File(...),
    search_query: str = Form("person face"),
    current_user: dict = Depends(require_auth_fastapi)
):
    if not allowed_file(image.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")

    try:
        uid = current_user.get("uid")
        temp_path = await save_temp_file(image)
        with open(temp_path, "rb") as f:
            image_data = f.read()

        image_hash = hashlib.md5(image_data).hexdigest()
        face_analysis = face_engine.process_uploaded_image(image_data)

        if face_analysis.get("status") == "error":
            raise HTTPException(status_code=500, detail=face_analysis.get("error", "Unknown error"))
        if face_analysis.get("faces_detected", 0) == 0:
            raise HTTPException(status_code=400, detail="No faces detected")

        image_url = firebase_auth.upload_image_to_storage(image_data, image.filename, uid)

        primary_face = face_analysis["faces"][0]
        search_results = social_scraper.comprehensive_search(primary_face["encoding"], search_query)

        # Log search
        firebase_auth.log_search_activity(uid, {
            "search_type": "face_upload_analysis",
            "faces_detected": face_analysis["faces_detected"],
            "matches_found": search_results["total_matches"],
            "image_hash": image_hash,
            "results_summary": {
                "google_matches": len(search_results["google_images"]),
                "social_profiles": len(search_results["social_profiles"])
            }
        })

        os.remove(temp_path)

        return {
            "success": True,
            "image_hash": image_hash,
            "image_url": image_url,
            "faces_detected": face_analysis["faces_detected"],
            "primary_face": {
                "attributes": face_analysis["attributes"],
                "location": primary_face["location"],
                "confidence": primary_face["confidence"]
            },
            "search_results": {
                "total_matches": search_results["total_matches"],
                "google_images": search_results["google_images"][:10],
                "social_profiles": search_results["social_profiles"],
                "search_timestamp": search_results["search_timestamp"]
            },
            "analysis_timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"upload_and_analyze error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/compare-faces")
async def compare_faces(
    encoding1: List[float],
    encoding2: List[float],
    current_user: dict = Depends(require_auth_fastapi)
):
    try:
        result = face_engine.compare_faces(encoding1, encoding2)
        return {"success": True, "comparison": result, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"compare_faces error: {e}")
        raise HTTPException(status_code=500, detail="Error comparing faces")

@app.post("/search-by-name")
async def search_by_name(
    name: str,
    current_user: dict = Depends(require_auth_fastapi)
):
    try:
        uid = current_user.get("uid")
        facebook_results = social_scraper.search_facebook_public(name)
        firebase_auth.log_search_activity(uid, {
            "search_type": "name_search",
            "faces_detected": 0,
            "matches_found": len(facebook_results),
            "image_hash": None,
            "results_summary": {"name_searched": name, "facebook_profiles": len(facebook_results)}
        })
        return {
            "success": True,
            "results": {
                "name_searched": name,
                "facebook_profiles": facebook_results,
                "total_profiles": len(facebook_results),
                "search_timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"search_by_name error: {e}")
        raise HTTPException(status_code=500, detail="Error searching by name")

@app.post("/enhance-image")
async def enhance_image(
    image: UploadFile = File(...),
    current_user: dict = Depends(require_auth_fastapi)
):
    if not allowed_file(image.filename):
        raise HTTPException(status_code=400, detail="Invalid file type")
    try:
        uid = current_user.get("uid")
        temp_path = await save_temp_file(image)
        enhanced_path = face_engine.enhance_image_quality(temp_path)
        with open(enhanced_path, "rb") as f:
            enhanced_data = f.read()
        os.remove(temp_path)
        os.remove(enhanced_path)
        enhanced_url = firebase_auth.upload_image_to_storage(enhanced_data, f"enhanced_{image.filename}", uid)
        return {"success": True, "enhanced_image_url": enhanced_url, "message": "Image enhanced successfully"}
    except Exception as e:
        logger.error(f"enhance_image error: {e}")
        raise HTTPException(status_code=500, detail="Error enhancing image")

@app.get("/search-history")
async def get_search_history(
    limit: int = 50,
    current_user: dict = Depends(require_auth_fastapi)
):
    try:
        uid = current_user.get("uid")
        history = firebase_auth.get_search_history(uid, limit)
        return {"success": True, "history": history, "total_records": len(history)}
    except Exception as e:
        logger.error(f"get_search_history error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving search history")

@app.post("/export-results")
async def export_results(
    search_results: dict,
    case_number: Optional[str] = "N/A",
    current_user: dict = Depends(require_auth_fastapi)
):
    try:
        uid = current_user.get("uid")
        user_profile = firebase_auth.get_user_profile(uid)
        report_data = {
            "officer_info": {
                "badge_number": user_profile.get("badge_number", "Unknown"),
                "department": user_profile.get("department", "Unknown"),
                "country": user_profile.get("country", "Unknown")
            },
            "search_results": search_results,
            "export_timestamp": datetime.utcnow().isoformat(),
            "case_number": case_number
        }
        return {"success": True, "report_data": report_data, "message": "Report generated successfully"}
    except Exception as e:
        logger.error(f"export_results error: {e}")
        raise HTTPException(status_code=500, detail="Error exporting results")

@app.get("/system-stats")
async def get_system_stats(current_user: dict = Depends(require_auth_fastapi)):
    try:
        uid = current_user.get("uid")
        user_profile = firebase_auth.get_user_profile(uid)
        if not user_profile or user_profile.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        stats = {
            "total_searches_today": 45,
            "total_users": 12,
            "active_users": 8,
            "successful_matches": 23,
            "system_uptime": "99.9%",
            "last_updated": datetime.utcnow().isoformat()
        }
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"get_system_stats error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving system statistics")
