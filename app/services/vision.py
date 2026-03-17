# app/services/vision.py
import os
import cv2
import json
import numpy as np
from typing import List, Dict, Tuple, Optional, Deque
from collections import deque
from pathlib import Path
import logging
from app.util import empty_or_not

logger = logging.getLogger(__name__)

# Constants for vision processing
SPOTS_FILE = Path("data") / "spots.json"
MAX_HISTORY = 10
STABILITY_THRESHOLD = 0.6
DEFAULT_FRAME_SHAPE = (480, 640)

# Colors for annotation (BGR format)
COLOR_OCCUPIED = (0, 0, 255)  # Red
COLOR_OPEN = (0, 255, 0)  # Green
COLOR_UNKNOWN = (255, 255, 0)  # Yellow
COLOR_TEXT = (255, 255, 255)  # White
COLOR_DEBUG = (0, 255, 255)  # Cyan

# Load parking spot definitions with error handling
try:
    with open(SPOTS_FILE, "r") as f:
        data = json.load(f)
        SPOTS: List[Dict] = data["spots"]
        FRAME_SHAPE: Tuple[int, int] = tuple(data.get("frame_shape", DEFAULT_FRAME_SHAPE))
        logger.info(f"Loaded {len(SPOTS)} parking spots from {SPOTS_FILE}")
except FileNotFoundError:
    logger.error(f"Parking spots file not found: {SPOTS_FILE}")
    raise RuntimeError(
        f"Parking spots file not found: {SPOTS_FILE}. Please run tools/mask_creator.py to create it."
    )
except KeyError as e:
    logger.error(f"Invalid spots.json format. Missing key: {e}")
    raise RuntimeError(f"Invalid spots.json format. Missing key: {e}")
except json.JSONDecodeError as e:
    logger.error(f"Failed to parse spots.json: {e}")
    raise RuntimeError(f"Failed to parse spots.json: {e}")

# Global state for frame caching and spot history
cap_cache: Dict[str, Optional[np.ndarray]] = {"prev": None}
SPOT_HISTORY: Dict[int, Deque[bool]] = {}

def smooth_status(spot_id: int, occupied_now: bool) -> bool:
    """
    Apply temporal smoothing to reduce detection flickering.

    Uses a rolling window of recent detections to determine if a spot is truly occupied.
    This prevents rapid flashing between occupied/empty states due to noise.

    Args:
        spot_id: Unique identifier for the parking spot
        occupied_now: Current frame's occupancy detection result

    Returns:
        Smoothed occupancy status (True if occupied, False if empty)
    """
    if spot_id not in SPOT_HISTORY:
        SPOT_HISTORY[spot_id] = deque(maxlen=MAX_HISTORY)

    history = SPOT_HISTORY[spot_id]
    history.append(occupied_now)

    # Calculate average occupancy over history window
    occupancy_ratio = sum(history) / len(history)
    is_occupied = occupancy_ratio > STABILITY_THRESHOLD

    logger.debug(
        f"Spot {spot_id}: occupancy_ratio={occupancy_ratio:.2f}, "
        f"is_occupied={is_occupied} (history_len={len(history)})"
    )

    return is_occupied

def detect_open_spots(frame: np.ndarray, debug: bool = False) -> Tuple[List[Dict], np.ndarray]:
    """
    Detect parking spot occupancy using frame differencing and temporal smoothing.

    This function analyzes each defined parking spot by:
    1. Comparing current frame to previous frame to detect changes
    2. Using adaptive thresholding to determine occupancy
    3. Applying temporal smoothing to reduce false positives
    4. Annotating the frame with colored bounding boxes and labels

    Args:
        frame: Current video frame (BGR numpy array)
        debug: If True, add diagnostic information (frame differences) to annotated frame

    Returns:
        Tuple of (results_list, annotated_frame) where:
        - results_list: List of dicts with {id, status, diff} for each spot
        - annotated_frame: Copy of input frame with bounding boxes and labels
    """
    annotated = frame.copy()
    prev_frame = cap_cache.get("prev")
    results: List[Dict] = []
    frame_h, frame_w = frame.shape[:2]

    logger.debug(f"Processing frame of shape {frame_h}x{frame_w}, debug={debug}")

    if prev_frame is not None:
        diffs = []
        for spot in SPOTS:
            x, y, w, h = spot["bbox"]

            # Validate bounding box is within frame
            if x < 0 or y < 0 or x + w > frame_w or y + h > frame_h:
                logger.warning(
                    f"Spot {spot['id']} bbox {spot['bbox']} exceeds frame dimensions {frame_w}x{frame_h}"
                )
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
                logger.error(f"Error processing spot {spot['id']}: {e}")
                results.append({"id": spot["id"], "status": "error", "diff": round(diff, 2)})
                continue

            status = "occupied" if occupied else "open"
            color = COLOR_OCCUPIED if occupied else COLOR_OPEN
            cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
            cv2.putText(
                annotated,
                f"{spot['id']} {status}",
                (x+5, y+15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                COLOR_TEXT,
                1
            )
            if debug:
                cv2.putText(
                    annotated,
                    f"Δ:{diff:.1f}",
                    (x+5, y+30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    COLOR_DEBUG,
                    1
                )

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

            cv2.rectangle(annotated, (x, y), (x+w, y+h), COLOR_UNKNOWN, 1)
            results.append({"id": spot["id"], "status": "unknown"})

    cap_cache["prev"] = frame.copy()
    return results, annotated