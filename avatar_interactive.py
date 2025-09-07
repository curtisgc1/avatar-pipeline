#!/usr/bin/env python3
import cv2
import numpy as np
import time
import requests
import subprocess
import threading

class InteractiveAvatar:
    def __init__(self):
        self.is_speaking = False
        self.llm_url = "http://localhost:8000/v1/chat/completions"
        
    def speak_text(self, text):
        self.is_speaking = True
        # Use female voice with espeak
        subprocess.run(["espeak", "-v", "en+f3", "-s", "150", text])
        self.is_speaking = False
        
    def animate(self):
        cv2.namedWindow('Avatar', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        blink_counter = 0
        
        while True:
            frame = np.zeros((1080, 1920, 3), np.uint8)
            frame[:] = (20, 20, 30)
            t = time.time()
            blink_counter += 1
            
            # Head - make it rounder/softer
            cv2.circle(frame, (960, 540), 250, (90, 85, 95), -1)
            
            # Eyes - larger and friendlier
            if blink_counter % 100 < 5:
                cv2.line(frame, (860, 480), (920, 480), (200, 200, 200), 3)
                cv2.line(frame, (1000, 480), (1060, 480), (200, 200, 200), 3)
            else:
                cv2.circle(frame, (890, 480), 40, (245, 245, 245), -1)
                cv2.circle(frame, (1030, 480), 40, (245, 245, 245), -1)
                cv2.circle(frame, (890, 480), 22, (100, 150, 200), -1)
                cv2.circle(frame, (1030, 480), 22, (100, 150, 200), -1)
            
            # Mouth - softer smile
            if self.is_speaking:
                mouth_h = int(20 + 30 * abs(np.sin(t * 10)))
                cv2.ellipse(frame, (960, 640), (70, mouth_h), 0, 0, 180, (80, 60, 70), -1)
            else:
                cv2.ellipse(frame, (960, 640), (70, 20), 0, 20, 160, (80, 60, 70), 3)
            
            status = "SPEAKING..." if self.is_speaking else "Press SPACE - then speak"
            cv2.putText(frame, status, (650, 950), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
            
            cv2.imshow('Avatar', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                self.interact()
                
        cv2.destroyAllWindows()
        
    def interact(self):
        print("Recording 3 seconds...")
        subprocess.run([
            "arecord", "-D", "plughw:1,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", "3", "-q", "user_speech.wav"
        ])
        
        try:
            print("Getting AI response...")
            response = requests.post(self.llm_url, json={
                "model": "Qwen/Qwen2.5-3B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are a friendly female avatar assistant. Respond in one short sentence."},
                    {"role": "user", "content": "Hello, how are you today?"}
                ],
                "max_tokens": 30
            })
            
            if response.status_code == 200:
                text = response.json()['choices'][0]['message']['content']
                print(f"AI says: {text}")
                
                thread = threading.Thread(target=self.speak_text, args=(text,))
                thread.start()
            else:
                print(f"LLM error: {response.status_code}")
                self.speak_text("Connection error")
                
        except Exception as e:
            print(f"Error: {e}")
            self.speak_text("Cannot connect to AI")
    
    def run(self):
        self.animate()

if __name__ == "__main__":
    avatar = InteractiveAvatar()
    avatar.run()
