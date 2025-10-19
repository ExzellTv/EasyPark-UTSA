import cv2
import json
import numpy as np
import os

# Paths
JSON_PATH = "data/spots.json"          # existing polygon spots
OUTPUT_MASK = "data/mask_1920_1080.png"

# Load data
if not os.path.exists(JSON_PATH):
    raise FileNotFoundError(f"❌ Couldn't find {JSON_PATH}")

with open(JSON_PATH, "r") as f:
    data = json.load(f)

spots = data.get("spots", [])
frame_shape = data.get("frame_shape", [1080, 1920])  # fallback
height, width = frame_shape[0], frame_shape[1]

# Create empty mask
mask = np.zeros((height, width), dtype=np.uint8)

# Draw each polygon on mask
for i, spot in enumerate(spots, start=1):
    points = np.array(spot["points"], np.int32)
    cv2.fillPoly(mask, [points], color=i)  # label each region with unique ID

# Save mask
cv2.imwrite(OUTPUT_MASK, mask)
print(f"✅ Mask saved: {OUTPUT_MASK}")
print(f"   Regions drawn: {len(spots)}")
print(f"   Mask size: {mask.shape[::-1]}")
