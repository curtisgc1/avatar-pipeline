#!/usr/bin/env python3
import cv2
import numpy as np
import time

cv2.namedWindow('Avatar', cv2.WINDOW_NORMAL)
cv2.setWindowProperty('Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

speaking = False
blink_counter = 0

while True:
    frame = np.zeros((1080, 1920, 3), np.uint8)
    frame[:] = (20, 20, 30)
    
    t = time.time()
    blink_counter += 1
    
    # Head
    cv2.circle(frame, (960, 540), 250, (80, 80, 90), -1)
    
    # Eyes with blinking
    if blink_counter % 100 < 5:  # Blink every 100 frames
        cv2.line(frame, (860, 480), (920, 480), (200, 200, 200), 3)
        cv2.line(frame, (1000, 480), (1060, 480), (200, 200, 200), 3)
    else:
        cv2.circle(frame, (890, 480), 35, (240, 240, 240), -1)
        cv2.circle(frame, (1030, 480), 35, (240, 240, 240), -1)
        cv2.circle(frame, (890, 480), 20, (50, 50, 200), -1)
        cv2.circle(frame, (1030, 480), 20, (50, 50, 200), -1)
    
    # Animated mouth
    mouth_h = int(20 + 15 * abs(np.sin(t * 3)))
    cv2.ellipse(frame, (960, 640), (70, mouth_h), 0, 0, 180, (60, 60, 70), -1)
    
    cv2.putText(frame, "Animated Avatar - Press ESC to exit", (600, 900), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    
    cv2.imshow('Avatar', frame)
    
    if cv2.waitKey(1) == 27:  # ESC
        break

cv2.destroyAllWindows()
