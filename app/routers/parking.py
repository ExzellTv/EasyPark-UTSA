# app/routers/parking.py
import os
from fastapi import APIRouter
from app.services import vision
import logging

VISION_MODE = os.getenv("VISION_MODE", "dummy")
logging.info(f"[parking router] Mode: {VISION_MODE}")

router = APIRouter(prefix="/parking", tags=["parking"])

if VISION_MODE == "real":
    import cv2
    # cap = cv2.VideoCapture("rtsp://user:pass@ipaddress/stream")
    cap = cv2.VideoCapture(0)  # Use 0 for webcam or replace with actual stream URL
    if not cap.isOpened():
        logging.error("Error: Could not open video stream.")

@router.get("/spots")
def get_open_spots():
    if VISION_MODE == "real":
        ret, frame = cap.read()
        if not ret:
            return {"error": "Could not read camera frame"}
        results = vision.detect_open_spots(frame)
    else:
        results = vision.detect_open_spots()
    return {"spots": results}
