#!/usr/bin/env python3
import pvporcupine
import pvrecorder
import whisper
import requests
import subprocess
import asyncio
import edge_tts
import tempfile
import os
import json
import struct
import time

class WakeWordAvatar:
    def __init__(self):
        # Initialize wake word detection
        # Using built-in wake words (you can create custom ones)
        self.wake_words = ["jarvis", "computer", "alexa", "hey google"]
        
        print("Initializing wake word detection...")
        
        # You need a Picovoice access key (free from their website)
        # For testing, you can use the demo key
        try:
            self.porcupine = pvporcupine.create(
                access_key="YOUR_ACCESS_KEY_HERE",  # Get from https://console.picovoice.ai/
                keywords=["jarvis", "computer"]  # Built-in wake words
            )
            self.recorder = pvrecorder.PvRecorder(
                device_index=-1, 
                frame_length=self.porcupine.frame_length
            )
        except:
            print("Using alternative wake word detection...")
            self.porcupine = None
            
        self.whisper = None  # Load on demand
        self.vllm_url = "http://localhost:8000/v1/chat/completions"
        self.voice = "en-US-AriaNeural"
        
        # Settings
        self.config_file = "avatar_config.json"
        self.load_config()
        
        print("\n=== Avatar Wake Word System ===")
        print("Say 'Computer' or 'Jarvis' to wake me up")
        print("Then I'll listen and respond\n")
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.volume = config.get('volume', 50)
        except:
            self.volume = 50
            
    def load_models(self):
        """Load heavy models only when needed"""
        if self.whisper is None:
            print("Loading Whisper model...")
            self.whisper = whisper.load_model("base")
            print("Ready for conversation!")
            
    def listen_for_wake_word(self):
        """Listen for wake word using simple method"""
        print("💤 Waiting for wake word...")
        
        while True:
            # Record short clip
            subprocess.run([
                "arecord", "-D", "plughw:2,0", 
                "-f", "S16_LE", "-r", "16000", "-c", "1",
                "-d", "2", "-q", "wake_check.wav"
            ])
            
            # Quick transcribe if models loaded
            if self.whisper:
                result = self.whisper.transcribe("wake_check.wav")
                text = result.get('text', '').lower()
                
                # Check for wake words
                if any(word in text for word in ["computer", "jarvis", "avatar", "hey"]):
                    return True
            
            time.sleep(0.1)
            
    def detect_speech(self, duration=4):
        """Record speech after wake"""
        print("🎤 Yes? Listening...")
        
        subprocess.run([
            "arecord", "-D", "plughw:2,0", 
            "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", str(duration), "-q", "input.wav"
        ])
        
        result = self.whisper.transcribe("input.wav")
        text = result['text'].strip()
        
        return text if text and len(text) > 2 else None
        
    async def speak(self, text):
        """Generate and play speech"""
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", 
                "-volume", str(self.volume),
                tmp.name
            ], capture_output=True)
            os.unlink(tmp.name)
            
    async def conversation_loop(self):
        """Active conversation after wake"""
        await self.speak("Yes, I'm listening")
        
        timeout = 0
        while timeout < 3:  # 3 rounds of silence before sleeping
            text = self.detect_speech()
            
            if text:
                print(f"You: {text}")
                timeout = 0  # Reset timeout
                
                # Check for sleep command
                if any(word in text.lower() for word in ["goodbye", "sleep", "stop"]):
                    await self.speak("Going back to sleep")
                    return
                    
                # Generate response
                response = requests.post(self.vllm_url, json={
                    "model": "Qwen/Qwen2.5-3B-Instruct",
                    "messages": [
                        {"role": "system", "content": "Be helpful and concise."},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": 50
                })
                
                reply = response.json()['choices'][0]['message']['content']
                print(f"Avatar: {reply}\n")
                
                await self.speak(reply)
            else:
                timeout += 1
                
        await self.speak("Going back to sleep")
        
    async def run(self):
        """Main loop with wake word detection"""
        
        while True:
            # Wait for wake word
            if self.listen_for_wake_word():
                # Load models if not loaded
                self.load_models()
                
                # Sound to indicate wake
                subprocess.run(["aplay", "-q", "/usr/share/sounds/sound-icons/guitar-12.wav"], 
                             capture_output=True)
                
                # Start conversation
                await self.conversation_loop()
                
                print("\n💤 Back to sleep. Say 'Computer' to wake me.\n")

if __name__ == "__main__":
    avatar = WakeWordAvatar()
    asyncio.run(avatar.run())
