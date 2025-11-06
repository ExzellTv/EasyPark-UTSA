import cv2
import numpy as np

def empty_or_not(spot_crop):
    gray = cv2.cvtColor(spot_crop, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 19, 16
    )
    mean_val = np.mean(thresh)
    return mean_val < 15  # <15 => empty, otherwise occupied
