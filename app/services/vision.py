# app/services/vision.py
import os
import cv2
import json
import numpy as np
from typing import List, Dict, Tuple
from collections import deque
from app.util import empty_or_not  # <-- you’ll need to move this util into your project

VISION_MODE = os.getenv("VISION_MODE", "real")
SPOTS_FILE = os.path.join("data", "spots.json")

with open(SPOTS_FILE, "r") as f:
    data = json.load(f)
    SPOTS = data["spots"]
    REF_SHAPE = data["frame_shape"]

cap_cache = {"prev": None}
SPOT_HISTORY = {}
MAX_HISTORY = 10
STABILITY_THRESHOLD = 0.6

def smooth_status(spot_id, occupied_now):
    if spot_id not in SPOT_HISTORY:
        SPOT_HISTORY[spot_id] = deque(maxlen=MAX_HISTORY)
    history = SPOT_HISTORY[spot_id]
    history.append(occupied_now)
    return sum(history) / len(history) > STABILITY_THRESHOLD

def detect_open_spots(frame, debug: bool = False) -> Tuple[List[Dict], any]:
    annotated = frame.copy()
    prev_frame = cap_cache.get("prev")
    results = []

    if prev_frame is not None:
        diffs = []
        for spot in SPOTS:
            x, y, w, h = spot["bbox"]
            crop = frame[y:y+h, x:x+w]
            prev_crop = prev_frame[y:y+h, x:x+w]
            diff = np.abs(np.mean(crop) - np.mean(prev_crop))
            diffs.append(diff)

        max_diff = np.max(diffs) if len(diffs) else 1
        for spot, diff in zip(SPOTS, diffs):
            x, y, w, h = spot["bbox"]
            crop = frame[y:y+h, x:x+w]
            occupied_raw = not empty_or_not(crop)  # your classifier or threshold

            # Optionally include diff weighting for stability
            occupied = smooth_status(spot["id"], occupied_raw)

            status = "occupied" if occupied else "open"
            color = (0, 0, 255) if occupied else (0, 255, 0)
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            cv2.putText(annotated, f"{spot['id']} {status}", (x+5, y+15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            if debug:
                cv2.putText(annotated, f"Δ:{diff:.1f}", (x+5, y+30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

            results.append({
                "id": spot["id"],
                "status": status,
                "diff": round(diff, 2)
            })
    else:
        # First frame fallback
        for spot in SPOTS:
            x, y, w, h = spot["bbox"]
            cv2.rectangle(annotated, (x, y), (x+w, y+h), (255, 255, 0), 1)
            results.append({"id": spot["id"], "status": "unknown"})

    cap_cache["prev"] = frame.copy()
    return results, annotated