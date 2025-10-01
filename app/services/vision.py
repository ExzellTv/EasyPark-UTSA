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

# Load parking spots from spots.json (always the source of truth)
with open("data/spots.json", "r") as f:
    SPOTS = json.load(f)


def detect_open_spots(frame) -> Tuple[List[Dict], any]:
    """
    Detect parking spots depending on mode (real or dummy).
    Always returns (results, annotated_frame).
    """
    results = []
    annotated = frame.copy()

    if VISION_MODE == "real":
        # For now: mark everything open
        for spot in SPOTS:
            x, y, w, h = spot["x"], spot["y"], spot["w"], spot["h"]
            spot_id = spot["id"]

            status = "open"  # placeholder — later use detection logic
            color = (0, 255, 0) if status == "open" else (0, 0, 255)

            cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)

            results.append({
                "id": spot_id,
                "coordinates": ((x, y), (x + w, y + h)),
                "status": status
            })

    else:  # dummy mode
        current_time = int(time.time())

        for spot in SPOTS:
            x, y, w, h = spot["x"], spot["y"], spot["w"], spot["h"]
            spot_id = spot["id"]

            # Cycle spot status
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
