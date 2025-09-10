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

class FluidAvatar:
    def __init__(self):
        self.wake_whisper = whisper.load_model("small")  # Better accuracy for wake
        self.main_whisper = None
        self.awake = False
        self.silence_count = 0
        
        # Config
        self.wake_words = ["jarvis", "computer", "hey curtis", "curtis"]
        self.voice = "en-US-AriaNeural"
        self.volume = 30
        self.max_tokens = 30  # Short but complete
        
        print("=== Fluid Conversation Avatar ===")
        print(f"Wake words: {', '.join(self.wake_words)}\n")
        
    def check_for_wake(self):
        """Better wake detection"""
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", "2", "-q", "wake.wav"
        ])
        
        result = self.wake_whisper.transcribe("wake.wav", language="en")
        text = result.get('text', '').lower().strip()
        
        # Check for wake words
        for word in self.wake_words:
            if word in text:
                print(f"Wake: '{text}'")
                return True
                    
        return False
        
    async def speak(self, text):
        """Speak response"""
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            os.system(f"ffplay -nodisp -autoexit -volume {self.volume} {tmp.name} 2>/dev/null")
            os.unlink(tmp.name)
            
    async def conversation_loop(self):
        """Maintain fluid conversation"""
        if not self.main_whisper:
            print("Loading conversation model...")
            self.main_whisper = whisper.load_model("base")
            
        # Sound to indicate ready
        os.system("aplay /usr/share/sounds/sound-icons/prompt.wav 2>/dev/null")
        
        self.silence_count = 0
        
        while self.awake:
            # Record
            subprocess.run([
                "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
                "-r", "16000", "-c", "1", "-d", "3", "-q", "input.wav"
            ])
            
            result = self.main_whisper.transcribe("input.wav")
            text = result.get('text', '').strip()
            
            # Check if we got speech
            if text and len(text) > 2:
                self.silence_count = 0  # Reset silence counter
                print(f"You: {text}")
                
                # Check for sleep command
                if any(word in text.lower() for word in ["goodbye", "sleep", "stop"]):
                    await self.speak("Sleep mode")
                    self.awake = False
                    break
                    
                # Generate response
                response = requests.post("http://localhost:8000/v1/chat/completions",
                    json={
                        "model": "Qwen/Qwen2.5-3B-Instruct",
                        "messages": [
                            {"role": "system", "content": "Give brief, natural responses. Maximum 2 sentences."},
                            {"role": "user", "content": text}
                        ],
                        "max_tokens": self.max_tokens,
                        "temperature": 0.7
                    })
                    
                reply = response.json()['choices'][0]['message']['content']
                
                # Clean up response
                sentences = reply.split('.')
                if len(sentences) > 2:
                    reply = '.'.join(sentences[:2]) + '.'
                    
                print(f"Avatar: {reply}\n")
                await self.speak(reply)
                
                print("🎤 Listening...")
                
            else:
                # No speech detected
                self.silence_count += 1
                
                # After 3 rounds of silence, sleep
                if self.silence_count >= 3:
                    await self.speak("Going to sleep")
                    self.awake = False
                    break
                else:
                    print("...")  # Still listening
                    
    async def run(self):
        print("💤 Say wake word to start...")
        
        while True:
            if not self.awake:
                if self.check_for_wake():
                    print("⚡ Awake! Starting conversation...\n")
                    self.awake = True
                    await self.conversation_loop()
                    print("\n💤 Sleeping...\n")
                    
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    avatar = FluidAvatar()
    asyncio.run(avatar.run())
