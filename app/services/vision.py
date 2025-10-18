# app/services/vision.py
import os
import cv2
import json
import logging
import time
from typing import List, Dict, Tuple

VISION_MODE = os.getenv("VISION_MODE", "dummy")
logging.basicConfig(level=logging.INFO)
logging.info(f"[vision] Starting in {VISION_MODE.upper()} mode")

# Load parking spots from JSON
with open("data/spots.json", "r") as f:
    SPOTS = json.load(f)

# Create background subtractor for real mode
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=False)

def detect_open_spots(frame) -> Tuple[List[Dict], any]:
    """
    Detect parking spots depending on mode (real or dummy).
    Returns: (list of spot info, annotated_frame)
    """
    results = []
    annotated = frame.copy()

    if VISION_MODE == "real":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = fgbg.apply(gray)
        _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

        for spot in SPOTS:
            x, y, w, h = spot["x"], spot["y"], spot["w"], spot["h"]
            roi = mask[y:y + h, x:x + w]
            filled = cv2.countNonZero(roi)
            occupancy_ratio = filled / (w * h)

            status = "occupied" if occupancy_ratio > 0.10 else "open"
            color = (0, 0, 255) if status == "occupied" else (0, 255, 0)

            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(annotated, status, (x + 5, y + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            results.append({
                "id": spot["id"],
                "status": status,
                "coordinates": ((x, y), (x + w, y + h))
            })

    else:  # Dummy mode
        current_time = int(time.time())
        for spot in SPOTS:
            x, y, w, h = spot["x"], spot["y"], spot["w"], spot["h"]
            spot_id = spot["id"]
            cycle_time = 6
            phase_offset = (spot_id - 1) * 1.5
            time_in_cycle = (current_time + phase_offset) % cycle_time
            status = "open" if time_in_cycle < 3 else "occupied"
            color = (0, 255, 0) if status == "open" else (0, 0, 255)

            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
            cv2.putText(annotated, status, (x + 5, y + 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            results.append({
                "id": spot_id,
                "coordinates": ((x, y), (x + w, y + h)),
                "status": status
            })

    return results, annotated
