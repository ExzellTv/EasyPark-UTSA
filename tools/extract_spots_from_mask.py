# tools/extract_spots_from_mask.py
import cv2, json, numpy as np

mask_path = "data/mask_1920_1080.png"
mask = cv2.imread(mask_path, 0)
connected_components = cv2.connectedComponentsWithStats(mask, 4, cv2.CV_32S)

spots = []
for label, stat in enumerate(connected_components[2]):
    if label == 0:
        continue
    x, y, w, h, area = stat
    spots.append({"id": label, "bbox": [int(x), int(y), int(w), int(h)]})

json.dump({"frame_shape": mask.shape, "spots": spots}, open("data/spots.json", "w"), indent=4)
print(f"Saved {len(spots)} spots to data/spots.json")
