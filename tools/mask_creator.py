import cv2
import json
import numpy as np
import os

SPOTS_PATH = os.path.join("data", "spots.json")
VIDEO_PATH = os.getenv("CAMERA_SOURCE", "./data2.mp4")

# --- Load existing spots ---
if os.path.exists(SPOTS_PATH):
    with open(SPOTS_PATH, "r") as f:
        data = json.load(f)
        SPOTS = data.get("spots", [])
        FRAME_SHAPE = data.get("frame_shape", [2160, 3840])
else:
    SPOTS = []
    FRAME_SHAPE = [2160, 3840]

drawing = False
ix, iy = -1, -1
current_rect = None

print(f"📏 Frame size: {FRAME_SHAPE[1]}x{FRAME_SHAPE[0]}")
print("🖱️ Left-click & drag = draw box | Right-click = finish | D = delete last | S = save | R = reset | ESC = exit")

# --- Mouse callback ---
def draw_rect(event, x, y, flags, param):
    global ix, iy, drawing, current_rect

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            frame_copy = frame.copy()
            cv2.rectangle(frame_copy, (ix, iy), (x, y), (0, 255, 255), 2)
            draw_all(frame_copy)
            cv2.imshow("Mask Editor", frame_copy)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = min(ix, x), min(iy, y)
        x2, y2 = max(ix, x), max(iy, y)
        w, h = x2 - x1, y2 - y1
        SPOTS.append({"id": len(SPOTS) + 1, "bbox": [x1, y1, w, h]})
        print(f"✅ Added spot {len(SPOTS)}: ({x1}, {y1}, {w}, {h})")
        draw_all()

# --- Draw all boxes ---
def draw_all(custom_frame=None):
    canvas = custom_frame if custom_frame is not None else frame.copy()
    for s in SPOTS:
        x, y, w, h = s["bbox"]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(canvas, str(s["id"]), (x + 5, y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    if custom_frame is None:
        cv2.imshow("Mask Editor", canvas)

# --- Save all boxes ---
def save_spots():
    data = {"frame_shape": FRAME_SHAPE, "spots": SPOTS}
    with open(SPOTS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Saved {len(SPOTS)} spots to {SPOTS_PATH}")

# --- Main ---
if __name__ == "__main__":
    cap = cv2.VideoCapture(VIDEO_PATH)
    ret, frame = cap.read()
    if not ret:
        frame = np.zeros((FRAME_SHAPE[0], FRAME_SHAPE[1], 3), dtype=np.uint8)
        print("⚠️ Could not read video, starting with blank frame.")
    cap.release()

    cv2.namedWindow("Mask Editor")
    cv2.setMouseCallback("Mask Editor", draw_rect)
    draw_all()

    while True:
        cv2.imshow("Mask Editor", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            save_spots()
        elif key == ord('d'):
            if SPOTS:
                removed = SPOTS.pop()
                print(f"🗑️ Deleted spot {removed['id']}")
                draw_all()
        elif key == ord('r'):
            SPOTS.clear()
            print("🔄 Reset all spots.")
            draw_all()
        elif key == 27:  # ESC
            break

    cv2.destroyAllWindows()
