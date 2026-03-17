# app/routers/parking.py
"""API routes for parking spot detection and video streaming."""

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse
from app.services.vision import detect_open_spots
from app.services.video_capture import VideoCaptureThreaded
import cv2
import os
import numpy as np
import time
import logging
from typing import Dict, Any, Generator, Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/parking", tags=["parking"])

# Constants
VISION_MODE = os.getenv("VISION_MODE", "dummy")
CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "./parking_crop_loop.mp4")
DUMMY_FRAME_SHAPE = (480, 640, 3)
VIDEO_OUTPUT_FPS = 20
MJPEG_BOUNDARY = b"frame"

# ---------- Initialize Camera ----------
cap: Optional[VideoCaptureThreaded] = None

if VISION_MODE == "real":
    try:
        cap = VideoCaptureThreaded(CAMERA_SOURCE)
        logger.info(f"Video capture initialized in REAL mode with source: {CAMERA_SOURCE}")
    except RuntimeError as e:
        logger.error(f"Failed to initialize video capture: {e}")
        logger.warning("Falling back to DUMMY mode")
        cap = None
else:
    logger.info("Running in DUMMY mode (no real video source)")


# ---------- Streaming Generator ----------
def generate_video_stream(debug: bool = False) -> Generator[bytes, None, None]:
    """
    Thread-safe MJPEG streaming generator for video feed.

    Continuously yields JPEG frames with parking spot annotations.
    Supports both real video mode and dummy mode for testing.

    Args:
        debug: If True, include debug overlays (frame differences) on the video

    Yields:
        Bytes representing multipart MJPEG stream frames
    """
    logger.info(f"Starting video stream (debug={debug}, mode={VISION_MODE})")
    frame_count = 0

    while True:
        try:
            if VISION_MODE == "real" and cap is not None:
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.05)
                    continue
            else:
                # Generate dummy black frame for testing
                frame = np.zeros(DUMMY_FRAME_SHAPE, dtype=np.uint8)

            # Detect parking spots and annotate frame
            _, annotated = detect_open_spots(frame, debug=debug)

            # Encode frame as JPEG
            success, buffer = cv2.imencode(".jpg", annotated)
            if not success:
                logger.warning("Failed to encode frame as JPEG")
                continue

            # Yield MJPEG multipart frame
            yield (
                b"--" + MJPEG_BOUNDARY + b"\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                buffer.tobytes() +
                b"\r\n"
            )

            frame_count += 1
            if frame_count % 100 == 0:
                logger.debug(f"Streamed {frame_count} frames")

            time.sleep(1.0 / VIDEO_OUTPUT_FPS)

        except Exception as e:
            logger.error(f"Error in video stream generation: {e}", exc_info=True)
            time.sleep(0.1)  # Prevent tight loop on repeated errors


# ---------- Routes ----------
@router.get("/video_feed")
def video_feed(debug: bool = Query(False, description="Enable debug overlays")) -> StreamingResponse:
    """
    Live MJPEG stream showing parking lot detection.

    This endpoint streams a continuous video feed with parking spot annotations.
    Green boxes indicate available spots, red boxes indicate occupied spots.

    Args:
        debug: Enable debug overlays showing frame difference metrics

    Returns:
        StreamingResponse with MJPEG video stream
    """
    logger.info(f"Video feed requested (debug={debug})")
    return StreamingResponse(
        generate_video_stream(debug=debug),
        media_type=f"multipart/x-mixed-replace; boundary={MJPEG_BOUNDARY.decode()}"
    )


@router.get("/spots")
def get_open_spots(debug: bool = Query(False, description="Include detailed metrics")) -> Dict[str, Any]:
    """
    Return JSON list of all parking spots and their statuses.

    Provides real-time parking occupancy data including:
    - Summary statistics (total, occupied, available)
    - Individual spot status for each parking space
    - Optional debug metrics (frame differences)

    Args:
        debug: Include detailed debug metrics in response

    Returns:
        Dictionary containing:
        - summary: Total, occupied, and available spot counts
        - spots: List of individual spot statuses

    Raises:
        HTTPException: If unable to read video frame in real mode
    """
    logger.debug(f"Spots data requested (debug={debug})")

    try:
        if VISION_MODE == "real" and cap is not None:
            ret, frame = cap.read()
            if not ret or frame is None:
                logger.error("Could not read camera frame")
                raise HTTPException(
                    status_code=503,
                    detail="Could not read camera frame. Camera may be unavailable."
                )
        else:
            # Generate dummy frame for testing
            frame = np.zeros(DUMMY_FRAME_SHAPE, dtype=np.uint8)

        # Detect parking spots
        results, annotated = detect_open_spots(frame, debug=debug)

        # Save latest annotated frame for debugging
        cv2.imwrite("latest_frame.jpg", annotated)

        # Calculate summary statistics
        total = len(results)
        occupied = len([s for s in results if s["status"] == "occupied"])
        available = total - occupied

        logger.debug(f"Spots summary: {available}/{total} available")

        return {
            "summary": {
                "total": total,
                "occupied": occupied,
                "available": available
            },
            "spots": results
        }

    except Exception as e:
        logger.error(f"Error getting spot data: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal error processing parking data: {str(e)}"
        )