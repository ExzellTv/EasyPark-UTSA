import cv2
import numpy as np

def empty_or_not(spot_crop):
    """
    Determine if a parking spot is empty using adaptive thresholding.

    Args:
        spot_crop: BGR image crop of a parking spot

    Returns:
        True if spot appears empty, False if occupied
    """
    # Validate input
    if spot_crop is None or spot_crop.size == 0:
        raise ValueError("Invalid spot crop: empty or None")

    if len(spot_crop.shape) != 3 or spot_crop.shape[2] != 3:
        raise ValueError(f"Expected BGR image with 3 channels, got shape {spot_crop.shape}")

    gray = cv2.cvtColor(spot_crop, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 19, 16
    )
    mean_val = np.mean(thresh)
    return mean_val < 15  # <15 => empty, otherwise occupied
