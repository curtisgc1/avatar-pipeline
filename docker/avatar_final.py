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
        self.tts_url = "http://localhost:5002/api/tts"
        print("Avatar ready with best models!")
        
    def record(self, duration=3):
        print(f"🎤 Recording {duration}s...")
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(duration),
            "-q", "input.wav"
        ])
        
    def run(self):
        print("\n=== Premium Avatar System ===")
        print("- Whisper large-v3 (4090)")
        print("- XTTS v2 (4090 Docker)")
        print("- vLLM Qwen2.5-3B (5080)\n")
        
        while True:
            input("Press Enter> ")
            self.record(3)
            
            # Transcribe
            result = self.whisper.transcribe("input.wav")
            text = result['text'].strip()
            if not text:
                continue
                
            print(f"You: {text}")
            
            # Generate
            response = requests.post(self.vllm_url, json={
                "model": "Qwen/Qwen2.5-3B-Instruct",
                "messages": [
                    {"role": "user", "content": text}
                ],
                "max_tokens": 100
            })
            
            reply = response.json()['choices'][0]['message']['content']
            print(f"Avatar: {reply}")
            
            # TTS (if Docker XTTS is running)
            try:
                tts_response = requests.post(self.tts_url, 
                    json={"text": reply})
                with open("output.wav", "wb") as f:
                    f.write(tts_response.content)
                subprocess.run(["aplay", "output.wav"], capture_output=True)
            except:
                print("(TTS not available)")

if __name__ == "__main__":
    PremiumAvatar().run()
