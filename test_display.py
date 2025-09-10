#!/usr/bin/env python3
import cv2
import numpy as np
import time

print("Testing display output to TV...")

try:
    # Create a test window
    cv2.namedWindow('TV Test', cv2.WINDOW_NORMAL)
    cv2.setWindowProperty('TV Test', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Create a colorful test image
    img = np.zeros((1080, 1920, 3), np.uint8)
    img[:] = (50, 100, 150)  # Blue-ish background

    # Add text
    cv2.putText(img, "Hello TV!", (700, 500), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 255, 255), 5)
    cv2.putText(img, "Lip Sync Avatar Test", (600, 600), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
    cv2.putText(img, "Press any key to continue...", (650, 700), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)

    cv2.imshow('TV Test', img)
    cv2.waitKey(5000)  # Show for 5 seconds
    cv2.destroyAllWindows()

    print("✅ Display test successful!")

except Exception as e:
    print(f"❌ Display test failed: {e}")
    print("Make sure DISPLAY=:0 is set and X11 is running")
