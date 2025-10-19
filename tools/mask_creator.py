import cv2
import json
import os
import numpy as np
import random

VIDEO_SOURCE = os.getenv("CAMERA_SOURCE", "./parking_crop_loop.mp4")
OUTPUT_FILE = "data/spots.json"

spots = []          # list of {"id": int, "points": [(x, y), ...]}
current_points = [] # points of the polygon being drawn
frame = None
drawing = False

# random pastel color generator
def random_color():
    return tuple(int(x) for x in np.random.randint(60, 255, 3))

def click_event(event, x, y, flags, param):
    global current_points, frame, drawing

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        current_points.append((x, y))
        cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)
        if len(current_points) > 1:
            cv2.line(frame, current_points[-2], current_points[-1], (0, 255, 0), 2)
        cv2.imshow("Select Spots", frame)

    elif event == cv2.EVENT_RBUTTONDOWN and len(current_points) >= 3:
        # Close polygon cleanly (don’t duplicate first/last points)
        polygon = np.array(current_points, np.int32)
        color = random_color()
        cv2.polylines(frame, [polygon], True, color, 2)
        cv2.putText(frame, f"{len(spots)+1}", polygon[0], cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        spots.append({
            "id": len(spots) + 1,
            "points": current_points.copy(),
            "color": color
        })
        print(f"✅ Spot {len(spots)} saved ({len(current_points)} points).")
        current_points.clear()
        cv2.imshow("Select Spots", frame)

def redraw_all(base_frame):
    """Redraws all saved polygons on a fresh copy of the frame."""
    disp = base_frame.copy()
    for spot in spots:
        pts = np.array(spot["points"], np.int32)
        color = tuple(map(int, spot.get("color", random_color())))
        cv2.polylines(disp, [pts], True, color, 2)
        cv2.putText(disp, str(spot["id"]), pts[0], cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return disp

def save_spots():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    export = [{"id": s["id"], "points": s["points"]} for s in spots]
    with open(OUTPUT_FILE, "w") as f:
        json.dump(export, f, indent=4)
    print(f"\n💾 Saved {len(spots)} spots to {OUTPUT_FILE}")

def load_existing_spots():
    if not os.path.exists(OUTPUT_FILE):
        return []
    with open(OUTPUT_FILE, "r") as f:
        data = json.load(f)
    for spot in data:
        spot["color"] = random_color()
    print(f"📂 Loaded {len(data)} existing spots.")
    return data

def main():
    global frame
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print("❌ Could not open video file.")
        return

    ret, base_frame = cap.read()
    if not ret:
        print("❌ Could not read frame.")
        return

    cap.release()

    print("🖱️ Left-click to mark corners of a parking spot.")
    print("➡️ Right-click to complete a spot.")
    print("🗑️ Press 'D' to delete last spot.")
    print("💾 Press 'S' to save and exit.")

    # Load any existing spots
    global spots
    spots = load_existing_spots()
    frame = redraw_all(base_frame)

    cv2.namedWindow("Select Spots")
    cv2.setMouseCallback("Select Spots", click_event)

    while True:
        cv2.imshow("Select Spots", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('d'):
            if spots:
                removed = spots.pop()
                frame = redraw_all(base_frame)
                print(f"🗑️ Deleted spot {removed['id']}")
        elif key == ord('s'):
            save_spots()
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
