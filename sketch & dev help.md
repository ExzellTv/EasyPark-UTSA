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







**DEV RUN without API or APPS:**

uvicorn app.main:app --reload

http://127.0.0.1:8000/parking/spots

