import cv2
import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Constants for occupancy detection
GAUSSIAN_BLUR_KERNEL = (5, 5)
ADAPTIVE_THRESHOLD_BLOCK_SIZE = 19
ADAPTIVE_THRESHOLD_C = 16
EMPTY_THRESHOLD = 15


def empty_or_not(spot_crop: np.ndarray) -> bool:
    """
    Determine if a parking spot is empty using adaptive thresholding.

    Args:
        spot_crop: BGR image crop of a parking spot (numpy array with shape HxWx3)

    Returns:
        True if spot appears empty, False if occupied

    Raises:
        ValueError: If spot_crop is invalid (None, empty, or wrong shape)
    """
    # Validate input
    if spot_crop is None or spot_crop.size == 0:
        raise ValueError("Invalid spot crop: empty or None")

    if len(spot_crop.shape) != 3 or spot_crop.shape[2] != 3:
        raise ValueError(f"Expected BGR image with 3 channels, got shape {spot_crop.shape}")

    try:
        gray = cv2.cvtColor(spot_crop, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, GAUSSIAN_BLUR_KERNEL, 0)
        thresh = cv2.adaptiveThreshold(
            blur,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            ADAPTIVE_THRESHOLD_BLOCK_SIZE,
            ADAPTIVE_THRESHOLD_C
        )
        mean_val = np.mean(thresh)
        is_empty = mean_val < EMPTY_THRESHOLD

        logger.debug(f"Spot analysis: mean={mean_val:.2f}, is_empty={is_empty}")
        return is_empty

    except cv2.error as e:
        logger.error(f"OpenCV error during spot analysis: {e}")
        raise ValueError(f"Failed to process spot crop: {e}") from e
