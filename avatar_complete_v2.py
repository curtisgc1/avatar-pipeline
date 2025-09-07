#!/usr/bin/env python3
import cv2
import numpy as np
import subprocess
import asyncio
import edge_tts
import tempfile
import os
import requests
import threading
import time

class CompleteAvatar:
    def __init__(self):
        self.is_speaking = False
        self.voice = "en-US-AriaNeural"
        self.llm_url = "http://localhost:8000/v1/chat/completions"
        self.stt_url = "http://localhost:9000/asr"
        
    async def speak_text(self, text):
        self.is_speaking = True
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            subprocess.run(["ffplay", "-nodisp", "-autoexit", "-volume", "30", tmp.name], 
                         capture_output=True)
            os.unlink(tmp.name)
        self.is_speaking = False
        
    def display_loop(self):
        cv2.namedWindow('Avatar', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        blink_counter = 0
        
        while True:
            frame = np.zeros((1080, 1920, 3), np.uint8)
            frame[:] = (25, 25, 35)
            t = time.time()
            blink_counter += 1
            
            # Female avatar head
            cv2.circle(frame, (960, 540), 250, (95, 90, 100), -1)
            
            # Eyes with lashes
            if blink_counter % 120 < 5:
                cv2.line(frame, (860, 480), (920, 480), (200, 200, 200), 3)
                cv2.line(frame, (1000, 480), (1060, 480), (200, 200, 200), 3)
            else:
                cv2.circle(frame, (890, 480), 40, (250, 250, 250), -1)
                cv2.circle(frame, (1030, 480), 40, (250, 250, 250), -1)
                cv2.circle(frame, (890, 480), 25, (120, 180, 220), -1)
                cv2.circle(frame, (1030, 480), 25, (120, 180, 220), -1)
                # Eyelashes
                for i in range(3):
                    cv2.line(frame, (860+i*10, 440), (860+i*10, 430), (100, 100, 100), 2)
                    cv2.line(frame, (1000+i*10, 440), (1000+i*10, 430), (100, 100, 100), 2)
            
            # Animated mouth
            if self.is_speaking:
                mouth_h = int(15 + 25 * abs(np.sin(t * 12)))
                cv2.ellipse(frame, (960, 640), (60, mouth_h), 0, 0, 180, (80, 60, 70), -1)
            else:
                cv2.ellipse(frame, (960, 640), (60, 15), 0, 30, 150, (100, 70, 80), 3)
            
            # Status
            status = "Speaking..." if self.is_speaking else "Press SPACE to talk"
            cv2.putText(frame, status, (700, 950), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (100, 255, 100), 2)
            cv2.putText(frame, "ESC to exit", (900, 1000), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 1)
            
            cv2.imshow('Avatar', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                threading.Thread(target=self.handle_conversation).start()
                
        cv2.destroyAllWindows()
        
    def handle_conversation(self):
        # Record audio
        print("Listening...")
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", "4", "-q", "recording.wav"
        ])
        
        # Send to STT service
        try:
            with open("recording.wav", "rb") as f:
                files = {"audio": f}
                response = requests.post(self.stt_url, files=files)
                
            if response.status_code == 200:
                user_text = response.json().get("text", "").strip()
                print(f"You said: {user_text}")
            else:
                user_text = "Hello"  # Fallback
                
        except:
            user_text = "Hello"  # Fallback if STT fails
            
        # Get LLM response
        try:
            response = requests.post(self.llm_url, json={
                "model": "Qwen/Qwen2.5-3B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are Aria, a friendly AI assistant. Keep responses brief and conversational."},
                    {"role": "user", "content": user_text}
                ],
                "max_tokens": 60,
                "temperature": 0.7
            })
            
            if response.status_code == 200:
                ai_text = response.json()['choices'][0]['message']['content']
                print(f"Aria: {ai_text}")
                
                # Speak with the good voice
                asyncio.run(self.speak_text(ai_text))
            else:
                asyncio.run(self.speak_text("I'm having trouble connecting"))
                
        except Exception as e:
            print(f"Error: {e}")
            asyncio.run(self.speak_text("Let me think about that"))
    
    def run(self):
        self.display_loop()

if __name__ == "__main__":
    print("Starting Aria - Your AI Avatar")
    print("Press SPACE to talk, ESC to exit")
    avatar = CompleteAvatar()
    avatar.run()
