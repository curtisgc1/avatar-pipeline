#!/usr/bin/env python3
import cv2
import numpy as np
import time

cv2.namedWindow('Avatar', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

while True:
    frame = np.zeros((1080, 1920, 3), np.uint8)
    frame[:] = (20, 20, 30)
    
    # Simple avatar
    cv2.circle(frame, (960, 540), 200, (100, 100, 100), -1)
    cv2.putText(frame, "Avatar Working!", (700, 540), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    
    cv2.imshow('Avatar', frame)
    if cv2.waitKey(1) == 27:  # ESC to exit
        break

cv2.destroyAllWindows()
