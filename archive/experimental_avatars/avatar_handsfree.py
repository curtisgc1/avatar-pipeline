#!/usr/bin/env python3
import whisper
import requests
import subprocess
import asyncio
import edge_tts
import tempfile
import os
import webrtcvad
import json

class HandsFreeAvatar:
    def __init__(self):
        print("Loading models...")
        self.whisper = whisper.load_model("base")
        self.vllm_url = "http://localhost:8000/v1/chat/completions"
        self.voice = "en-US-AriaNeural"
        
        # Voice Activity Detection
        self.vad = webrtcvad.Vad(2)
        
        # Load/save volume setting
        self.config_file = "avatar_config.json"
        self.load_config()
        
        print(f"Hands-free Avatar ready! (Volume: {self.volume}%)")
        print("Say 'volume up/down' or 'volume 50' to adjust\n")
        
    def load_config(self):
        """Load saved settings"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.volume = config.get('volume', 50)
        except:
            self.volume = 50  # Default 50%
            self.save_config()
            
    def save_config(self):
        """Save settings"""
        with open(self.config_file, 'w') as f:
            json.dump({'volume': self.volume}, f)
        
    def detect_speech(self, timeout=10):
        """Listen for speech using ReSpeaker"""
        print("🎧 Listening...")
        
        subprocess.run([
            "arecord", "-D", "plughw:2,0", 
            "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", "4", "-q", "input.wav"
        ])
        
        result = self.whisper.transcribe("input.wav")
        text = result['text'].strip()
        
        return text if text and len(text) > 2 else None
        
    async def speak(self, text):
        """Generate and play speech with volume control"""
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            
            # Play with volume control
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", 
                "-volume", str(self.volume),
                tmp.name
            ], capture_output=True)
            
            os.unlink(tmp.name)
            
    def handle_volume(self, text):
        """Handle volume commands"""
        text_lower = text.lower()
        
        if "volume up" in text_lower:
            self.volume = min(100, self.volume + 20)
            self.save_config()
            return f"Volume set to {self.volume} percent"
            
        elif "volume down" in text_lower:
            self.volume = max(10, self.volume - 20)
            self.save_config()
            return f"Volume set to {self.volume} percent"
            
        elif "volume" in text_lower:
            # Try to extract number
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                self.volume = max(10, min(100, int(numbers[0])))
                self.save_config()
                return f"Volume set to {self.volume} percent"
                
        return None
            
    async def run(self):
        print("=== Hands-Free Avatar ===")
        print(f"Current volume: {self.volume}%")
        print("Just start speaking!\n")
        
        while True:
            text = self.detect_speech()
            
            if text:
                print(f"You: {text}")
                
                # Check for volume commands
                volume_response = self.handle_volume(text)
                if volume_response:
                    print(f"Avatar: {volume_response}\n")
                    await self.speak(volume_response)
                    continue
                
                # Check for exit
                if "goodbye" in text.lower() or "exit" in text.lower():
                    await self.speak("Goodbye!")
                    break
                
                # Generate response
                response = requests.post(self.vllm_url, json={
                    "model": "Qwen/Qwen2.5-3B-Instruct",
                    "messages": [
                        {"role": "system", "content": "Be helpful and conversational."},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 100
                })
                
                reply = response.json()['choices'][0]['message']['content']
                print(f"Avatar: {reply}\n")
                
                await self.speak(reply)

if __name__ == "__main__":
    avatar = HandsFreeAvatar()
    asyncio.run(avatar.run())
