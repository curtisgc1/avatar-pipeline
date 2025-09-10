#!/usr/bin/env python3
import cv2
import numpy as np
import time
import requests
import subprocess
import threading
import whisper

class ConversationalAvatar:
    def __init__(self):
        self.is_speaking = False
        self.llm_url = "http://localhost:8000/v1/chat/completions"
        self.stt_url = "http://localhost:9000/asr"
        print("Loading Whisper for speech recognition...")
        self.whisper_model = whisper.load_model("base")
        
    def speak_text(self, text):
        self.is_speaking = True
        # Female voice
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
            
            # Head
            cv2.circle(frame, (960, 540), 250, (90, 85, 95), -1)
            
            # Eyes
            if blink_counter % 100 < 5:
                cv2.line(frame, (860, 480), (920, 480), (200, 200, 200), 3)
                cv2.line(frame, (1000, 480), (1060, 480), (200, 200, 200), 3)
            else:
                cv2.circle(frame, (890, 480), 40, (245, 245, 245), -1)
                cv2.circle(frame, (1030, 480), 40, (245, 245, 245), -1)
                cv2.circle(frame, (890, 480), 22, (100, 150, 200), -1)
                cv2.circle(frame, (1030, 480), 22, (100, 150, 200), -1)
            
            # Mouth
            if self.is_speaking:
                mouth_h = int(20 + 30 * abs(np.sin(t * 10)))
                cv2.ellipse(frame, (960, 640), (70, mouth_h), 0, 0, 180, (80, 60, 70), -1)
            else:
                cv2.ellipse(frame, (960, 640), (70, 20), 0, 20, 160, (80, 60, 70), 3)
            
            status = "SPEAKING..." if self.is_speaking else "Press SPACE to talk"
            cv2.putText(frame, status, (650, 950), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 2)
            
            cv2.imshow('Avatar', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
            elif key == 32:  # SPACE
                self.have_conversation()
                
        cv2.destroyAllWindows()
        
    def have_conversation(self):
        # Record what you actually say
        print("Listening... (speak now)")
        subprocess.run([
            "arecord", "-D", "plughw:1,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", "4", "-q", "user_speech.wav"
        ])
        
        # Transcribe what you said
        print("Processing your speech...")
        result = self.whisper_model.transcribe("user_speech.wav")
        user_text = result["text"].strip()
        
        if not user_text:
            self.speak_text("I didn't hear anything")
            return
            
        print(f"You said: {user_text}")
        
        # Get AI response to what you actually said
        try:
            response = requests.post(self.llm_url, json={
                "model": "Qwen/Qwen2.5-3B-Instruct",
                "messages": [
                    {"role": "system", "content": "You are a friendly AI avatar. Have a natural conversation."},
                    {"role": "user", "content": user_text}
                ],
                "max_tokens": 60
            })
            
            if response.status_code == 200:
                ai_response = response.json()['choices'][0]['message']['content']
                print(f"AI: {ai_response}")
                
                thread = threading.Thread(target=self.speak_text, args=(ai_response,))
                thread.start()
                
        except Exception as e:
            print(f"Error: {e}")
            self.speak_text("Sorry, I had trouble processing that")
    
    def run(self):
        self.animate()

if __name__ == "__main__":
    print("Starting conversational avatar...")
    avatar = ConversationalAvatar()
    avatar.run()
