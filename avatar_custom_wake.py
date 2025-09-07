#!/usr/bin/env python3
import whisper
import subprocess
import time
import requests
import asyncio
import edge_tts
import tempfile
import os
import json

class CustomWakeAvatar:
    def __init__(self):
        self.wake_whisper = whisper.load_model("tiny")
        self.main_whisper = None
        self.awake = False
        
        # Load custom configuration
        self.config_file = "wake_config.json"
        self.load_config()
        
        print(f"=== Custom Wake Word Avatar ===")
        print(f"Wake words: {', '.join(self.wake_words)}")
        print(f"Volume: {self.volume}%\n")
        
    def load_config(self):
        """Load or create config file"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except:
            config = {
                "wake_words": ["computer", "jarvis", "avatar"],
                "voice": "en-US-AriaNeural",  # Female voice
                "volume": 30,
                "response_timeout": 15,
                "listen_duration": 3,
                "response_length": 20  # Much shorter responses
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
        self.wake_words = config.get("wake_words", ["computer"])
        self.voice = config.get("voice", "en-US-AriaNeural")  # Back to female
        self.volume = config.get("volume", 30)
        self.timeout = config.get("response_timeout", 15)
        self.listen_duration = config.get("listen_duration", 3)
        self.max_tokens = config.get("response_length", 20)  # Very brief
        
    def check_for_wake(self):
        """Check for custom wake words with confidence threshold"""
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", "2", "-q", "wake.wav"
        ])
        
        result = self.wake_whisper.transcribe("wake.wav", language="en")
        text = result.get('text', '').lower().strip()
        
        # Only respond if we clearly heard a wake word
        if len(text) > 0:
            for word in self.wake_words:
                if word.lower() in text:
                    print(f"Heard: '{text}' -> Wake word detected")
                    return True
                    
        return False
        
    def save_config(self):
        """Save configuration"""
        config = {
            "wake_words": self.wake_words,
            "voice": self.voice,
            "volume": self.volume,
            "response_timeout": self.timeout,
            "listen_duration": self.listen_duration,
            "response_length": self.max_tokens
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
            
    async def speak(self, text):
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            os.system(f"ffplay -nodisp -autoexit -volume {self.volume} {tmp.name} 2>/dev/null")
            os.unlink(tmp.name)
            
    async def active_listen(self):
        """Listen and respond - ONLY when appropriate"""
        if not self.main_whisper:
            self.main_whisper = whisper.load_model("base")
            
        # Simple beep instead of "Yes?"
        os.system("aplay /usr/share/sounds/sound-icons/prompt.wav 2>/dev/null")
        
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(int(self.listen_duration)), "-q", "command.wav"
        ])
        
        result = self.main_whisper.transcribe("command.wav")
        text = result.get('text', '').strip()
        
        # Only respond if we got clear speech (not noise)
        if text and len(text) > 3:  # Increased threshold
            print(f"You: {text}")
            
            if "goodbye" in text.lower() or "sleep" in text.lower():
                await self.speak("Sleep mode")
                return False
                
            # VERY brief system prompt
            response = requests.post("http://localhost:8000/v1/chat/completions",
                json={
                    "model": "Qwen/Qwen2.5-3B-Instruct",
                    "messages": [
                        {"role": "system", "content": "Answer in 1-2 short sentences max."},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": self.max_tokens,  # Only 20 tokens
                    "temperature": 0.7
                })
                
            reply = response.json()['choices'][0]['message']['content']
            
            # Truncate if still too long
            if len(reply) > 100:
                reply = reply[:100] + "..."
                
            print(f"Avatar: {reply}\n")
            await self.speak(reply)
            return True
        else:
            # No clear speech detected, go back to sleep
            return False
            
    async def run(self):
        print("💤 Listening for wake word...")
        
        while True:
            if not self.awake:
                if self.check_for_wake():
                    self.awake = True
                    
                    # Single response then back to sleep
                    stay_awake = await self.active_listen()
                    
                    if not stay_awake:
                        self.awake = False
                        print("💤 Sleeping...\n")
                    
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    avatar = CustomWakeAvatar()
    asyncio.run(avatar.run())
