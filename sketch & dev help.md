*+-----------+      +-----------+*

*| Cameras   | ---> | C++ OpenCV |*

*+-----------+      +-----------+*

                        *|*

                        *v*

                  *Python API (FastAPI)*

                        *|*

                   *Mobile App / Web*



If priority is a working prototype → *use Python + OpenCV + FastAPI.*



If priority is low-level performance right away → *write the OpenCV detection logic in C++ and either:*



* Expose it as a CLI tool the Python server calls.
* Compile it as a shared library and call from Python (via ctypes or pybind11).
* Or skip Python entirely and build your own REST server in C++ (harder).



https://viso.ai/applications/parking-lot-occupancy-detection/
https://blog-ko.superb-ai.com/smart-parking-with-existing-cctv/
https://www.milesight.com/security/product/ai-outdoor-parking-management-pro-bullet-plus-camera

**In OpenCV (and images in general):**

(0,0) ───────────> x (width)
|
|
|
v
y (height)

* (0,0) is the top-left corner of your image.
* x increases to the right, y increases downward.
* Rectangles are usually defined as (x, y, width, height) or (top-left, bottom-right).


**LabelIMG**
https://github.com/HumanSignal/labelImg



**DEV RUN without API or APPS:**

uvicorn app.main:app --reload

http://127.0.0.1:8000/parking/spots



**Next Steps**
🔹 Immediate Next Steps (Prototype)

Dataset Collection
* Take photos (ground or drone).
* Label parking spaces (x, y, w, h).
* Store them in JSON so your app knows where to “look” for cars.

Vision Logic Improvements
* Replace the “all open” dummy logic with something like:
* Check average pixel intensity in a region (darker = car).
* OR use background subtraction (compare to an empty lot image).
* Keep it rule-based at first (no ML needed yet).

Toggle Stub vs Real
* Confirm you can switch between dummy data and real OpenCV detection with VISION_MODE.
* This way, you can develop without needing the camera every time.

Visual Debugging
* Modify vision.py to draw rectangles around detected spots.
* Display using cv2.imshow() or save annotated frames.
* Helps verify correctness.

🔹 Medium-Term Steps (MVP App)

Persist State
* Save detection results to a database (SQLite or Postgres).
* This lets you analyze usage over time.

Frontend
* Simple web page (React, or even plain HTML) that calls your FastAPI endpoint and shows:
* of open spots
* Green/red markers on an image map of the lot

Testing Dataset
* Start small (5 cars, 5 spots).
* Scale up to 10, 20, 50 spots as you refine detection.

Deployment
* Dockerize the app so you can run it anywhere.
* Test on your laptop before trying something like a Raspberry Pi at UTSA.

🔹 Long-Term (Future Vision 🚀)

Drone/Camera Integration
* Use drone captures to simulate real-world coverage.
* Later: fixed cameras in the lot.

Better Detection
* Move from “rectangle pixel checks” → object detection (YOLO, SSD, etc.).
* ML models can robustly detect cars, even with shadows/lighting changes.

UTSA-Ready Version
* Map UTSA parking lot layouts.
* Create a UI that students can check: “Lot X: 73 spots free”.
