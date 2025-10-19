# app/routers/parking.py
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.services.vision import detect_open_spots
import cv2
import os
import numpy as np

router = APIRouter(prefix="/parking", tags=["parking"])

VISION_MODE = os.getenv("VISION_MODE", "dummy")

cap = None
if VISION_MODE == "real":
    CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "0")  # webcam or file
    try:
        cam_index = int(CAMERA_SOURCE)
        cap = cv2.VideoCapture(cam_index)
    except ValueError:
        cap = cv2.VideoCapture(CAMERA_SOURCE)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera source: {CAMERA_SOURCE}")


def generate_video_stream(debug=False):
    """Generator function for MJPEG streaming (loops videos automatically)."""
    while True:
        if VISION_MODE == "real":
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        _, annotated = detect_open_spots(frame, debug=debug)
        success, buffer = cv2.imencode('.jpg', annotated)
        if not success:
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@router.get("/video_feed")
def video_feed(debug: bool = Query(False, description="Enable debug overlays")):
    """Live MJPEG stream showing parking lot detection."""
    return StreamingResponse(generate_video_stream(debug=debug),
                             media_type='multipart/x-mixed-replace; boundary=frame')


@router.get("/spots")
def get_open_spots(debug: bool = Query(False, description="Include detailed metrics")):
    """Returns a JSON list of all parking spots and their statuses."""
    if VISION_MODE == "real":
        ret, frame = cap.read()
        if not ret:
            return {"error": "Could not read camera frame"}
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

    results, annotated = detect_open_spots(frame, debug=debug)
    cv2.imwrite("latest_frame.jpg", annotated)

    total = len(results)
    occupied = len([s for s in results if s["status"] == "occupied"])
    available = total - occupied

    return {
        "summary": {"total": total, "occupied": occupied, "available": available},
        "spots": results
    }
