import os
import cv2
import logging
from typing import List, Dict

VISION_MODE = os.getenv("VISION_MODE", "dummy")
logging.basicConfig(level=logging.INFO)
logging.info(f"[vision] Starting in {VISION_MODE.upper()} mode")

# Example parking spots coordinates
PARKING_SPOTS = [
    {"id": 1, "coords": (100, 200, 50, 50)},
    {"id": 2, "coords": (200, 200, 50, 50)},
    {"id": 3, "coords": (300, 200, 50, 50)}
]

if VISION_MODE == "real":
    def detect_open_spots(frame) -> List[Dict]:
        """
        Draws rectangles for each parking spot on the frame
        and returns a dummy status for now.
        """
        results = []
        for spot in PARKING_SPOTS:
            x, y, w, h = spot["coords"]
            # Draw rectangle on frame (green = open)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            results.append({
                "id": spot["id"],
                "coordinates": ((x, y), (x + w, y + h)),
                "status": "open"  # just a placeholder
            })

        # Optional: show frame in a window
        cv2.imshow("Parking Test", frame)
        cv2.waitKey(1)  # 1 ms delay to refresh window

        return results

else:
    # dummy mode
    def detect_open_spots() -> List[Dict]:
        logging.info("[vision] Dummy detect_open_spots called")
        return [
            {"id": 1, "coordinates": ((100, 200), (150, 250)), "status": "open"},
            {"id": 2, "coordinates": ((200, 200), (250, 250)), "status": "open"},
            {"id": 3, "coordinates": ((300, 200), (350, 250)), "status": "occupied"},
        ]