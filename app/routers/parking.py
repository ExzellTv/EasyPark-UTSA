# app/routers/parking.py
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from app.services.vision import detect_open_spots
import cv2
import os
import numpy as np
import threading, time

router = APIRouter(prefix="/parking", tags=["parking"])

VISION_MODE = os.getenv("VISION_MODE", "dummy")


# ---------- Threaded Video Capture ----------
class VideoCaptureThreaded:
    def __init__(self, source):
        self.cap = cv2.VideoCapture(source)
        self.ret = False
        self.frame = None
        self.stopped = False
        # Launch background thread immediately
        threading.Thread(target=self.update, daemon=True).start()

    def update(self):
        while not self.stopped:
            if self.cap.isOpened():
                self.ret, self.frame = self.cap.read()
                if not self.ret:
                    # Restart video when it ends or drops a frame
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            time.sleep(0.03)  # ~30 FPS reader loop
        self.cap.release()

    def read(self):
        # Return the latest frame safely
        if self.frame is not None:
            return True, self.frame.copy()
        return False, None

    def stop(self):
        self.stopped = True


# ---------- Initialize Camera ----------
cap = None
if VISION_MODE == "real":
    CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "./parking_crop_loop.mp4")
    cap = VideoCaptureThreaded(CAMERA_SOURCE)


# ---------- Streaming Generator ----------
def generate_video_stream(debug=False):
    """Thread-safe MJPEG streaming generator."""
    while True:
        if VISION_MODE == "real":
            ret, frame = cap.read()
            if not ret or frame is None:
                time.sleep(0.05)
                continue
        else:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)

        _, annotated = detect_open_spots(frame, debug=debug)
        success, buffer = cv2.imencode(".jpg", annotated)
        if not success:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")
        time.sleep(0.05)  # 20 FPS output limiter


# ---------- Routes ----------
@router.get("/video_feed")
def video_feed(debug: bool = Query(False, description="Enable debug overlays")):
    """Live MJPEG stream showing parking lot detection."""
    return StreamingResponse(generate_video_stream(debug=debug),
                             media_type="multipart/x-mixed-replace; boundary=frame")


@router.get("/spots")
def get_open_spots(debug: bool = Query(False, description="Include detailed metrics")):
    """Return JSON list of all parking spots and their statuses."""
    if VISION_MODE == "real":
        ret, frame = cap.read()
        if not ret or frame is None:
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
