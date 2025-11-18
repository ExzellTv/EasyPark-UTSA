# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EasyPark UTSA is a smart parking management platform for the UTSA campus. It uses computer vision (OpenCV) to detect parking spot occupancy in real-time from camera/drone footage and provides a REST API (FastAPI) for clients to query availability.

**Tech Stack:** Python, FastAPI, OpenCV, future PostgreSQL/MySQL integration

## Development Commands

### Running the Server

```bash
# Start the development server (default port 8000)
uvicorn main:app --reload

# Access the API
# - Web UI: http://127.0.0.1:8000/
# - Parking spots API: http://127.0.0.1:8000/parking/spots
# - Live video feed: http://127.0.0.1:8000/parking/video_feed
```

### Dependencies

```bash
# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Core Components

**Entry Point (`main.py`)**
- FastAPI application initialization
- Static file mounting (handles both `./static` and `./app/static` locations)
- Router registration

**API Router (`app/routers/parking.py`)**
- `/parking/spots` - Returns JSON with parking spot statuses and availability summary
- `/parking/video_feed` - MJPEG stream with annotated video showing spot detection
- Implements `VideoCaptureThreaded` class for background frame reading (~30 FPS)
- Supports `debug` query parameter for detailed metrics

**Vision Service (`app/services/vision.py`)**
- `detect_open_spots(frame, debug)` - Main detection logic
- Uses frame differencing and temporal smoothing (10-frame history)
- Loads parking spot coordinates from `data/spots.json`
- Depends on `app/util.py::empty_or_not()` for occupancy classification
- Returns: `(results_list, annotated_frame)`

**Occupancy Detector (`app/util.py`)**
- `empty_or_not(spot_crop)` - Determines if a parking spot is empty
- Uses adaptive thresholding on grayscale/blurred image
- Threshold: mean < 15 = empty, otherwise occupied

### Vision Modes

Controlled by `VISION_MODE` environment variable:
- `"real"` - Process actual camera feed (source from `CAMERA_SOURCE` env var, defaults to `./parking_crop_loop.mp4`)
- `"dummy"` - Use blank frames for development without camera

### Data Files

**`data/spots.json`** - Parking spot definitions
```json
{
  "frame_shape": [height, width],
  "spots": [
    {"id": 1, "bbox": [x, y, width, height]},
    ...
  ]
}
```

### Tools

**`tools/mask_creator.py`** - Interactive OpenCV GUI to define parking spots
- Load video, draw bounding boxes with mouse
- Keyboard: `S` = save, `D` = delete last, `R` = reset, `ESC` = exit
- Outputs to `data/spots.json`

**`tools/extract_spots_from_mask.py`** - Extract spots from mask image

**`tools/generate_mask_from_json.py`** - Convert spots.json back to mask visualization

## Configuration

Create a `.env` file based on `.env.example`:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/easypark
CAMERA_FEED_URL=rtsp://user:pass@192.168.0.10/stream  # Not currently used
SECRET_KEY=super-secret-key
VISION_MODE=real  # or "dummy"
CAMERA_SOURCE=./parking_crop_loop.mp4  # or video file path
```

## Detection Algorithm

1. **Frame capture** - Threaded background capture ensures no dropped frames
2. **Frame differencing** - Compare current frame to previous frame for each spot
3. **Occupancy check** - `empty_or_not()` analyzes spot crop using adaptive thresholding
4. **Temporal smoothing** - 10-frame rolling history with 60% stability threshold to reduce flicker
5. **Annotation** - Draw colored rectangles (green=open, red=occupied) with spot IDs

## Testing

```bash
# Run tests
pytest tests/

# Test specific file
pytest tests/test_parking.py
```

## Frontend

Static HTML files in `static/`:
- `index.html` - Main dashboard
- `live_feed.html` - Video stream viewer
- `debug_feed.html` - Video stream with debug overlays
- `analytics_placeholder.html` - Future analytics page

## Important Notes

- **Coordinate system**: OpenCV uses (0,0) at top-left, x increases right, y increases down
- **Frame caching**: `vision.py` maintains previous frame in `cap_cache` dict for differencing
- **Thread safety**: Video capture runs in background thread, main thread reads latest frame
- **Video looping**: When video source ends, it automatically restarts from frame 0
- The project is currently in prototype phase - no database persistence yet, all state is in-memory
