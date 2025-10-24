import cv2

cap = cv2.VideoCapture(0)  # replace 0 with your RTSP URL if needed

if not cap.isOpened():
    print("Failed to open camera")
else:
    ret, frame = cap.read()
    if ret:
        cv2.imshow("Test", frame)
        cv2.waitKey(0)
    cap.release()
    cv2.destroyAllWindows()
