#!/usr/bin/env python3
import os
import cv2
import numpy as np
import time

# Force display to the local monitor
os.environ['DISPLAY'] = ':0'

def test_display():
    """Test displaying on the physical monitor"""
    # Create a simple avatar window
    img = np.zeros((720, 1280, 3), np.uint8)
    img[:] = (30, 30, 40)  # Dark background
    
    # Draw simple avatar face
    cv2.circle(img, (640, 360), 150, (200, 180, 160), -1)  # Head
    cv2.circle(img, (590, 320), 30, (255, 255, 255), -1)   # Left eye
    cv2.circle(img, (690, 320), 30, (255, 255, 255), -1)   # Right eye
    cv2.circle(img, (590, 320), 15, (50, 50, 200), -1)     # Left pupil
    cv2.circle(img, (690, 320), 15, (50, 50, 200), -1)     # Right pupil
    cv2.ellipse(img, (640, 420), (60, 30), 0, 0, 180, (50, 50, 50), 3)  # Mouth
    
    # Add text
    cv2.putText(img, "Avatar Pipeline Test", (450, 100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)
    cv2.putText(img, "Press 'q' to quit", (520, 650), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
    
    # Try to display
    print("Attempting to display on monitor...")
    print("If you see this error: 'Can't open display'")
    print("Run this in a terminal ON the Ubuntu desktop GUI")
    
    try:
        cv2.imshow('Avatar', img)
        print("Window created! Check your monitor.")
        print("Press 'q' to close")
        
        while True:
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"Display error: {e}")
        print("\nALTERNATIVE: Run this script from a terminal in the Ubuntu GUI")
        print("Or we can set up a web-based display instead")

if __name__ == "__main__":
    test_display()
