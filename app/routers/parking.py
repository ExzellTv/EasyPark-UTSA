# app/routers/parking.py
from fastapi import APIRouter, Response
from fastapi.responses import StreamingResponse  # add this import
from app.services.vision import detect_open_spots
import cv2
import os
import numpy as np

router = APIRouter(prefix="/parking", tags=["parking"])

VISION_MODE = os.getenv("VISION_MODE", "dummy")

cap = None
if VISION_MODE == "real":
    CAMERA_SOURCE = os.getenv("./parking_crop_loop.mp4", "0")  # webcam or video path
    try:
        cam_index = int(CAMERA_SOURCE)
        cap = cv2.VideoCapture(cam_index)
    except ValueError:
        # If not a number, treat it as file path or URL
        cap = cv2.VideoCapture(CAMERA_SOURCE)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open camera source: {CAMERA_SOURCE}")

@router.get("/video_feed")
def video_feed():
    """Live video stream showing parking lot detection."""
    return StreamingResponse(generate_video_stream(),
                             media_type='multipart/x-mixed-replace; boundary=frame')

@router.get("/spots")
def get_open_spots():
    """Returns a JSON list of all parking spots and their statuses."""
    if VISION_MODE == "real":
        ret, frame = cap.read()
        if not ret:
            return {"error": "Could not read camera frame"}
    else:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)  # dummy black frame

    results, annotated = detect_open_spots(frame)
    cv2.imwrite("latest_frame.jpg", annotated)

    total = len(results)
    occupied = len([s for s in results if s["status"] == "occupied"])
    available = total - occupied

    return {
        "summary": {"total": total, "occupied": occupied, "available": available},
        "spots": results
    }


def generate_video_stream():
    """Generator function for MJPEG streaming (loops videos automatically)."""
    while True:
        if VISION_MODE == "real":
            ret, frame = cap.read()

            # If at end of file, loop back to start
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        _, annotated = detect_open_spots(frame)
        success, buffer = cv2.imencode('.jpg', annotated)
        if not success:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@router.get("/video_feed")
def video_feed():
    """Live video stream showing parking lot detection."""
    return Response(generate_video_stream(),
                    media_type='multipart/x-mixed-replace; boundary=frame')
