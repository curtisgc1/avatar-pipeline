#!/usr/bin/env python3
import cv2
import numpy as np
import json
import time
import socket
import threading
import subprocess

class AvatarDisplay:
    def __init__(self):
        # Socket to receive commands from voice system
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', 5555))
        self.sock.settimeout(0.1)
        
        self.is_speaking = False
        self.mouth_state = 0
        self.text = ""
        
        # Try to create window
        try:
            cv2.namedWindow('Avatar', cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty('Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        except:
            print("Cannot open display. Using virtual display.")
            
    def listen_for_commands(self):
        """Listen for speaking/viseme data"""
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = json.loads(data.decode())
                
                if msg.get('speaking'):
                    self.is_speaking = msg['speaking']
                if msg.get('text'):
                    self.text = msg['text']
                if msg.get('mouth'):
                    self.mouth_state = msg['mouth']
                    
            except socket.timeout:
                pass
            except:
                pass
                
    def draw_simple_avatar(self, frame):
        """Draw a simple 2D avatar"""
        h, w = frame.shape[:2]
        cx, cy = w//2, h//2
        
        # Head
        cv2.circle(frame, (cx, cy-50), 150, (200, 180, 160), -1)
        cv2.circle(frame, (cx, cy-50), 150, (100, 80, 60), 3)
        
        # Eyes
        eye_y = cy - 80
        cv2.ellipse(frame, (cx-50, eye_y), (25, 20), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, (cx+50, eye_y), (25, 20), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (cx-50, eye_y), 10, (50, 50, 200), -1)
        cv2.circle(frame, (cx+50, eye_y), 10, (50, 50, 200), -1)
        
        # Mouth animation
        mouth_y = cy + 20
        if self.is_speaking:
            # Animate mouth based on time for simple lip sync
            mouth_open = int(20 * abs(np.sin(time.time() * 10)))
            cv2.ellipse(frame, (cx, mouth_y), (40, mouth_open+10), 0, 0, 180, (50, 50, 50), -1)
        else:
            # Closed mouth
            cv2.arc(frame, (cx, mouth_y), (40, 20), 0, 0, 180, (50, 50, 50), 3)
            
        # Display text
        if self.text:
            cv2.putText(frame, self.text[-50:], (50, h-50), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                       
        return frame
        
    def run(self):
        # Start command listener
        listener = threading.Thread(target=self.listen_for_commands, daemon=True)
        listener.start()
        
        print("Avatar Display Running (Press 'q' to quit)")
        
        while True:
            # Create frame
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            frame[:] = (30, 30, 40)  # Dark background
            
            # Draw avatar
            frame = self.draw_simple_avatar(frame)
            
            # Show frame
            cv2.imshow('Avatar', frame)
            
            if cv2.waitKey(30) & 0xFF == ord('q'):
                break
                
        cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test if display works
    try:
        avatar = AvatarDisplay()
        avatar.run()
    except Exception as e:
        print(f"Display error: {e}")
        print("Try: export DISPLAY=:0 or use SSH with -X flag")
