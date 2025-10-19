# tools/mask_creator.py
import cv2
import json
import os
import numpy as np
import random

VIDEO_SOURCE = os.getenv("CAMERA_SOURCE", "./parking_crop_loop.mp4")
OUTPUT_FILE = "data/spots.json"

spots = []           # list of dicts: {id, points}
current_points = []  # points of polygon being drawn
selected_id = None   # currently selected spot for edit
frame = None
base_frame = None

# Utility: random pastel colors for visualization
def random_color():
    return tuple(int(x) for x in np.random.randint(80, 255, 3))

def draw_all():
    """Redraw all existing spots on top of the base frame."""
    global frame
    frame = base_frame.copy()
    for s in spots:
        pts = np.array(s["points"], np.int32)
        color = (0, 255, 255) if s["id"] == selected_id else random_color()
        cv2.polylines(frame, [pts], True, color, 2)
        cv2.putText(frame, str(s["id"]), pts[0],
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    if current_points:
        for i, p in enumerate(current_points):
            cv2.circle(frame, p, 4, (0, 255, 0), -1)
            if i > 0:
                cv2.line(frame, current_points[i - 1], p, (0, 255, 0), 2)

def click_event(event, x, y, flags, param):
    global current_points, selected_id
    if event == cv2.EVENT_LBUTTONDOWN:
        current_points.append((x, y))
        draw_all()
    elif event == cv2.EVENT_RBUTTONDOWN:
        if len(current_points) >= 3:
            polygon = np.array(current_points, np.int32)
            new_id = max([s["id"] for s in spots], default=0) + 1
            spots.append({"id": new_id, "points": current_points.copy()})
            print(f"✅ Spot {new_id} saved ({len(current_points)} points).")
            current_points.clear()
            draw_all()
        else:
            print("❗ Need at least 3 points for a polygon.")

def save_spots(frame_shape):
    """Save all spots + frame metadata."""
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    data = {
        "frame_shape": [frame_shape[0], frame_shape[1]],  # (h, w)
        "spots": spots
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"💾 Saved {len(spots)} spots and frame {frame_shape} to {OUTPUT_FILE}")

def load_spots():
    """Load existing spots (if any)."""
    if not os.path.exists(OUTPUT_FILE):
        print("📂 No existing spots found.")
        return []
    with open(OUTPUT_FILE, "r") as f:
        data = json.load(f)
    loaded = data.get("spots", [])
    print(f"📂 Loaded {len(loaded)} existing spots from {OUTPUT_FILE}")
    return loaded

def select_spot(x, y):
    """Find spot whose polygon contains a point."""
    for s in spots:
        pts = np.array(s["points"], np.int32)
        mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        cv2.fillPoly(mask, [pts], 255)
        if mask[y, x] > 0:
            return s["id"]
    return None

def main():
    global frame, base_frame, selected_id
    cap = cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        print("❌ Could not open video file.")
        return
    ret, base_frame = cap.read()
    cap.release()
    if not ret:
        print("❌ Could not read frame.")
        return

    h, w = base_frame.shape[:2]
    print(f"📏 Frame size: {w}x{h}")
    print("🖱️ Left-click = draw | Right-click = finish polygon")
    print("🧭 Click existing polygon = select | D = delete | S = save | R = reset")

    cv2.namedWindow("Mask Editor")
    cv2.setMouseCallback("Mask Editor", click_event)

    global spots
    spots = load_spots()
    draw_all()

    while True:
        cv2.imshow("Mask Editor", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            save_spots((h, w))
            break
        elif key == ord('d'):
            if selected_id:
                spots[:] = [s for s in spots if s["id"] != selected_id]
                print(f"🗑️ Deleted spot {selected_id}")
                selected_id = None
                draw_all()
        elif key == ord('r'):
            spots.clear()
            current_points.clear()
            selected_id = None
            draw_all()
            print("🔁 Reset all spots.")
        elif key == ord('c'):
            # clear current unfinished polygon
            current_points.clear()
            draw_all()
            print("🧹 Cleared current drawing.")
        elif key == ord('q') or key == 27:
            print("❌ Quit without saving.")
            break
        elif key == ord('e'):
            print("✏️ Click inside a polygon to select for deletion/edit.")
            x, y = cv2.getWindowImageRect("Mask Editor")[:2]
            selected_id = select_spot(x, y)
            if selected_id:
                print(f"Selected spot {selected_id}")
                draw_all()

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
