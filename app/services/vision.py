# app/services/vision.py
import os
import cv2
import json
import numpy as np
from typing import List, Dict, Tuple
from collections import deque
from app.util import empty_or_not

SPOTS_FILE = os.path.join("data", "spots.json")

# Load parking spot definitions with error handling
try:
    with open(SPOTS_FILE, "r") as f:
        data = json.load(f)
        SPOTS = data["spots"]
        FRAME_SHAPE = data["frame_shape"]
except FileNotFoundError:
    raise RuntimeError(f"Parking spots file not found: {SPOTS_FILE}. Please run tools/mask_creator.py to create it.")
except KeyError as e:
    raise RuntimeError(f"Invalid spots.json format. Missing key: {e}")

cap_cache = {"prev": None}
SPOT_HISTORY = {}
MAX_HISTORY = 10
STABILITY_THRESHOLD = 0.6

def smooth_status(spot_id, occupied_now):
    """Apply temporal smoothing to reduce detection flickering."""
    if spot_id not in SPOT_HISTORY:
        SPOT_HISTORY[spot_id] = deque(maxlen=MAX_HISTORY)
    history = SPOT_HISTORY[spot_id]
    history.append(occupied_now)
    return sum(history) / len(history) > STABILITY_THRESHOLD

def detect_open_spots(frame, debug: bool = False) -> Tuple[List[Dict], any]:
    """
    Detect parking spot occupancy using frame differencing and temporal smoothing.

    Args:
        frame: Current video frame (BGR image)
        debug: If True, add diagnostic information to annotated frame

    Returns:
        Tuple of (results_list, annotated_frame)
    """
    annotated = frame.copy()
    prev_frame = cap_cache.get("prev")
    results = []
    frame_h, frame_w = frame.shape[:2]

    if prev_frame is not None:
        diffs = []
        for spot in SPOTS:
            x, y, w, h = spot["bbox"]

            # Validate bounding box is within frame
            if x < 0 or y < 0 or x + w > frame_w or y + h > frame_h:
                print(f"Warning: Spot {spot['id']} bbox {spot['bbox']} exceeds frame dimensions {frame_w}x{frame_h}")
                diffs.append(0)
                continue

            crop = frame[y:y+h, x:x+w]
            prev_crop = prev_frame[y:y+h, x:x+w]

            # Skip if crop is empty
            if crop.size == 0 or prev_crop.size == 0:
                diffs.append(0)
                continue

            diff = np.abs(np.mean(crop) - np.mean(prev_crop))
            diffs.append(diff)

        for spot, diff in zip(SPOTS, diffs):
            x, y, w, h = spot["bbox"]

            # Skip invalid spots
            if x < 0 or y < 0 or x + w > frame_w or y + h > frame_h:
                results.append({"id": spot["id"], "status": "error", "diff": 0})
                continue

            crop = frame[y:y+h, x:x+w]

            if crop.size == 0:
                results.append({"id": spot["id"], "status": "error", "diff": 0})
                continue

            try:
                occupied_raw = not empty_or_not(crop)
                occupied = smooth_status(spot["id"], occupied_raw)
            except (ValueError, cv2.error) as e:
                print(f"Error processing spot {spot['id']}: {e}")
                results.append({"id": spot["id"], "status": "error", "diff": round(diff, 2)})
                continue

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

            # Validate bounding box
            if x < 0 or y < 0 or x + w > frame_w or y + h > frame_h:
                results.append({"id": spot["id"], "status": "error"})
                continue

            cv2.rectangle(annotated, (x, y), (x+w, y+h), (255, 255, 0), 1)
            results.append({"id": spot["id"], "status": "unknown"})

    cap_cache["prev"] = frame.copy()
    return results, annotated