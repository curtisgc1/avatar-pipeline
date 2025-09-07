#!/usr/bin/env python3
import whisper
import requests
import subprocess
import asyncio
import edge_tts
import tempfile
import os

class VoiceAvatar:
    def __init__(self, whisper_model="small"):
        print(f"Loading Whisper {whisper_model}...")
        self.whisper = whisper.load_model(whisper_model)
        self.vllm_url = "http://localhost:8000/v1/chat/completions"
        self.voice = "en-US-AriaNeural"  # or en-US-GuyNeural for male
        print("Voice Avatar ready!")
        
    def record(self, duration=3):
        print(f"🎤 Recording {duration}s...")
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(duration),
            "input.wav"
        ], capture_output=True)
        
    async def speak(self, text):
        """Fast TTS with edge-tts"""
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            subprocess.run(["ffplay", "-nodisp", "-autoexit", tmp.name], 
                         capture_output=True)
            os.unlink(tmp.name)
            
    async def run(self):
        print("\n=== Voice Avatar System ===")
        print(f"- Whisper on 4090")
        print(f"- vLLM on 5080")
        print(f"- Edge-TTS voice output\n")
        
        while True:
            input("Press Enter to speak> ")
            
            # Record
            self.record(3)
            
            # Transcribe
            print("Processing...")
            result = self.whisper.transcribe("input.wav")
            text = result['text'].strip()
            
            if not text:
                print("No speech detected")
                continue
                
            print(f"You: {text}")
            
            # Generate
            response = requests.post(self.vllm_url, json={
                "model": "Qwen/Qwen2.5-3B-Instruct",
                "messages": [
                    {"role": "system", "content": "Be conversational and friendly."},
                    {"role": "user", "content": text}
                ],
                "max_tokens": 100,
                "temperature": 0.7
            })
            
            reply = response.json()['choices'][0]['message']['content']
            print(f"Avatar: {reply}")
            
            # Speak
            await self.speak(reply)

if __name__ == "__main__":
    # Use "small" for 3x faster, or "base" for 10x faster
    avatar = VoiceAvatar(whisper_model="small")  
    asyncio.run(avatar.run())
