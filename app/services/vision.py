# app/services/vision.py
import os
import logging
from typing import List, Dict

VISION_MODE = os.getenv("VISION_MODE", "dummy")
logging.basicConfig(level=logging.INFO)
logging.info(f"[vision] Starting in {VISION_MODE.upper()} mode")

if VISION_MODE == "real":
    import cv2
    # put your real detection code here
    def detect_open_spots(frame) -> List[Dict]:
        # TO DO: your OpenCV detection logic goes here
        # return list of {id, coordinates, status}
        return []
else:
    # dummy mode
    def detect_open_spots() -> List[Dict]:
        """
        Return a list of open parking spots (dummy data).
        """
        return [
            {"id": 1, "coordinates": ((100, 200), (150, 250)), "status": "open"},
            {"id": 2, "coordinates": ((200, 200), (250, 250)), "status": "open"},
            {"id": 3, "coordinates": ((300, 200), (350, 250)), "status": "occupied"},
        ]



"""
# app/services/vision.py
import cv2
import numpy as np
from app.utils.parking_map import PARKING_SPOTS

def detect_open_spots(frame):
    
    frame: a single image from your camera (BGR, as returned by cv2.VideoCapture)
    returns: list of spot states [{'id':1, 'occupied':True/False}, ...]
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # optional: blur to reduce noise
    gray = cv2.GaussianBlur(gray, (5, 5), 3)

    results = []
    for spot in PARKING_SPOTS:
        x, y, w, h = spot["coords"]
        roi = gray[y:y+h, x:x+w]

        # Simple metric: mean pixel intensity (empty spot brighter than car)
        mean_intensity = np.mean(roi)

        # You’ll need to calibrate this threshold per camera
        threshold = 120  
        occupied = mean_intensity < threshold

        results.append({"id": spot["id"], "occupied": occupied})

        # Optional: draw boxes for debugging
        color = (0, 255, 0) if not occupied else (0, 0, 255)
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

    return results, frame  # return annotated frame if you want to show it
"""