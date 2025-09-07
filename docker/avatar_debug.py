#!/usr/bin/env python3
import whisper
import requests
import subprocess
import time

class PremiumAvatar:
    def __init__(self):
        print("Loading Whisper large-v3...")
        self.whisper = whisper.load_model("large-v3")
        self.vllm_url = "http://localhost:8000/v1/chat/completions"
        print("Avatar ready!")
        
    def record(self, duration=3):
        print(f"🎤 Recording {duration}s...")
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(duration),
            "input.wav"
        ])
        print("Recording complete")
        
    def run(self):
        print("\n=== Avatar System ===\n")
        
        while True:
            input("Press Enter> ")
            
            # Record
            self.record(3)
            
            # Transcribe with feedback
            print("Transcribing...")
            start = time.time()
            result = self.whisper.transcribe("input.wav")
            text = result['text'].strip()
            print(f"Transcription took {time.time()-start:.1f}s")
            
            if not text:
                print("No speech detected")
                continue
                
            print(f"You: {text}")
            
            # Generate response
            print("Generating response...")
            response = requests.post(self.vllm_url, json={
                "model": "Qwen/Qwen2.5-3B-Instruct",
                "messages": [{"role": "user", "content": text}],
                "max_tokens": 100
            })
            
            reply = response.json()['choices'][0]['message']['content']
            print(f"Avatar: {reply}\n")

if __name__ == "__main__":
    PremiumAvatar().run()
