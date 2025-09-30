# app/routers/parking.py
from fastapi import APIRouter
from app.services.vision import detect_open_spots
import cv2
import os

router = APIRouter(prefix="/parking", tags=["parking"])

VISION_MODE = os.getenv("VISION_MODE", "dummy")

cap = None
if VISION_MODE == "real":
    CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "0")  # default webcam
    try:
        cam_index = int(CAMERA_SOURCE)
        cap = cv2.VideoCapture(cam_index)
    except ValueError:
        cap = cv2.VideoCapture(CAMERA_SOURCE)


@router.get("/spots")
def get_open_spots():
    if VISION_MODE == "real":
        ret, frame = cap.read()
        if not ret:
            return {"error": "Could not read camera frame"}
        results, annotated = detect_open_spots(frame)
    else:
        # Dummy mode just generates fake rectangles, no camera needed
        # Pass in a blank frame to keep API consistent
        import numpy as np
        frame = np.zeros((480, 640, 3), dtype=np.uint8)  # blank black image
        results, annotated = detect_open_spots(frame)

    # Always save annotated frame for debugging
    cv2.imwrite("latest_frame.jpg", annotated)

    return {"spots": results}
