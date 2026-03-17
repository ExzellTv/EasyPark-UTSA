# app/services/video_capture.py
"""Threaded video capture for efficient frame processing."""

import cv2
import numpy as np
import threading
import time
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

# Constants for video capture
DEFAULT_FPS = 30
FRAME_READ_INTERVAL = 1.0 / DEFAULT_FPS  # ~30 FPS


class VideoCaptureThreaded:
    """
    Thread-safe video capture that reads frames in the background.

    This class runs a background thread that continuously reads frames from
    a video source, ensuring that the latest frame is always available without
    blocking the main processing loop.

    Attributes:
        cap: OpenCV VideoCapture object
        ret: Boolean indicating if the last frame read was successful
        frame: Most recent frame captured (numpy array)
        stopped: Flag to stop the background thread
    """

    def __init__(self, source: str):
        """
        Initialize the threaded video capture.

        Args:
            source: Video source (file path, camera index, or stream URL)
        """
        self.source = source
        self.cap = cv2.VideoCapture(source)
        self.ret = False
        self.frame: Optional[np.ndarray] = None
        self.stopped = False
        self._lock = threading.Lock()

        if not self.cap.isOpened():
            logger.error(f"Failed to open video source: {source}")
            raise RuntimeError(f"Failed to open video source: {source}")

        logger.info(f"Video capture initialized with source: {source}")

        # Launch background thread immediately
        self._thread = threading.Thread(target=self.update, daemon=True)
        self._thread.start()

    def update(self) -> None:
        """
        Background thread that continuously reads frames from the video source.

        This method runs in a loop until stopped, reading frames and automatically
        restarting the video when it reaches the end.
        """
        logger.debug("Video capture thread started")
        while not self.stopped:
            if self.cap.isOpened():
                ret, frame = self.cap.read()

                if not ret:
                    # Restart video when it ends or drops a frame
                    logger.debug("Restarting video from beginning")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = self.cap.read()

                with self._lock:
                    self.ret = ret
                    if ret:
                        self.frame = frame

            time.sleep(FRAME_READ_INTERVAL)

        self.cap.release()
        logger.debug("Video capture thread stopped")

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read the latest frame from the video capture.

        Returns:
            Tuple of (success, frame) where:
            - success: Boolean indicating if a frame is available
            - frame: Copy of the latest frame (numpy array) or None
        """
        with self._lock:
            if self.frame is not None:
                return True, self.frame.copy()
            return False, None

    def stop(self) -> None:
        """
        Stop the background thread and release the video capture.

        This should be called when the video capture is no longer needed.
        """
        logger.info(f"Stopping video capture for source: {self.source}")
        self.stopped = True
        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def __del__(self):
        """Ensure resources are released when the object is destroyed."""
        if not self.stopped:
            self.stop()
