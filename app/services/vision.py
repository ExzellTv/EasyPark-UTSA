# app/services/vision.py
import os
import cv2
import json
import logging
import time
import numpy as np
from typing import List, Dict, Tuple

# --- Mode setup ---
VISION_MODE = os.getenv("VISION_MODE", "dummy")
logging.basicConfig(level=logging.INFO)
logging.info(f"[vision] Starting in {VISION_MODE.upper()} mode")

# --- Load parking spot polygons ---
SPOTS_FILE = os.path.join("data", "spots.json")
if os.path.exists(SPOTS_FILE):
    with open(SPOTS_FILE, "r") as f:
        SPOTS = json.load(f)
else:
    logging.warning("[vision] No data/spots.json found, using empty list")
    SPOTS = []

# --- Background subtractor for motion detection ---
fgbg = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=40, detectShadows=False)


def detect_open_spots(frame) -> Tuple[List[Dict], any]:
    """
    Detects parking spot occupancy (real or dummy).
    Hybrid detection in real mode: brightness + motion mask.
    """
    results = []
    annotated = frame.copy()

    if VISION_MODE == "real":
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        motion_mask = fgbg.apply(gray)
        _, motion_mask = cv2.threshold(motion_mask, 200, 255, cv2.THRESH_BINARY)

        for spot in SPOTS:
            pts = np.array(spot["points"], np.int32)

            # Create polygon mask
            mask = np.zeros(gray.shape, dtype=np.uint8)
            cv2.fillPoly(mask, [pts], 255)

            # Compute metrics
            mean_brightness = cv2.mean(gray, mask=mask)[0]
            motion_activity = cv2.countNonZero(cv2.bitwise_and(motion_mask, motion_mask, mask=mask))
            area = cv2.countNonZero(mask)
            motion_ratio = motion_activity / area if area > 0 else 0

            # Combine signals — thresholds can be tuned
            bright_occupied = mean_brightness < 100
            motion_occupied = motion_ratio > 0.03
            occupied = bright_occupied or motion_occupied

            status = "occupied" if occupied else "open"
            color = (0, 0, 255) if occupied else (0, 255, 0)

            # Draw polygon & label
            cv2.polylines(annotated, [pts], True, color, 2)
            label_pos = tuple(pts[0])
            cv2.putText(annotated, f"{spot['id']} {status}", label_pos,
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            results.append({
                "id": spot["id"],
                "status": status,
                "brightness": round(mean_brightness, 2),
                "motion_ratio": round(motion_ratio, 4)
            })

    else:
        # DUMMY MODE — simulation for testing
        current_time = time.time()
        for spot in SPOTS:
            pts = np.array(spot["points"], np.int32)
            spot_id = spot["id"]

            # Cycle open/occupied state visually
            cycle_time = 6
            phase_offset = (spot_id - 1) * 1.5
            time_in_cycle = (current_time + phase_offset) % cycle_time
            status = "open" if time_in_cycle < 3 else "occupied"

            color = (0, 255, 0) if status == "open" else (0, 0, 255)
            cv2.polylines(annotated, [pts], True, color, 2)
            cv2.putText(annotated, f"{spot_id} {status}", tuple(pts[0]),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            results.append({
                "id": spot_id,
                "status": status
            })

    return results, annotated
