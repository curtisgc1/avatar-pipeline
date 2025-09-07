#!/usr/bin/env python3
import whisper
import subprocess
import time
import requests
import asyncio
import edge_tts
import tempfile
import os
import threading
import queue

class InteractiveAvatar:
    def __init__(self):
        print("Loading Whisper large-v3 (this takes a moment)...")
        self.whisper = whisper.load_model("large-v3")
        print("Whisper v3 loaded!")
        
        self.wake_words = ["jarvis", "computer", "hey", "curtis", "avatar"]
        self.voice = "en-US-AriaNeural"
        self.volume = 30
        self.awake = False
        self.conversation_history = []
        
        print("\n=== Interactive Avatar with Whisper v3 ===")
        print("Wake words: jarvis, computer, hey curtis\n")
        
    def listen(self, duration=3):
        """Record audio"""
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(duration), "-q", "temp.wav"
        ])
        
        # Use large-v3 for accurate transcription
        result = self.whisper.transcribe("temp.wav", language="en", fp16=False)
        return result.get('text', '').strip()
        
    async def speak(self, text):
        """Quick TTS"""
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            os.system(f"ffplay -nodisp -autoexit -volume {self.volume} {tmp.name} 2>/dev/null &")
            os.unlink(tmp.name)
            
    async def conversation(self):
        """Interactive conversation with context"""
        # Quick beep to indicate ready
        os.system("aplay /usr/share/sounds/sound-icons/prompt.wav 2>/dev/null")
        
        silence_count = 0
        
        while self.awake:
            print("🎤 Listening...")
            text = self.listen(3)
            
            if text and len(text) > 2:
                silence_count = 0
                print(f"You: {text}")
                
                # Check for exit
                if any(word in text.lower() for word in ["goodbye", "bye", "sleep"]):
                    await self.speak("Bye")
                    self.awake = False
                    break
                    
                # Add to conversation history for context
                self.conversation_history.append(f"User: {text}")
                
                # Build context from history
                context = "\n".join(self.conversation_history[-5:])  # Last 5 exchanges
                
                # Get response with context
                response = requests.post("http://localhost:8000/v1/chat/completions",
                    json={
                        "model": "Qwen/Qwen2.5-3B-Instruct",
                        "messages": [
                            {"role": "system", "content": f"Be conversational and brief. Previous context:\n{context}"},
                            {"role": "user", "content": text}
                        ],
                        "max_tokens": 40,
                        "temperature": 0.8
                    })
                    
                reply = response.json()['choices'][0]['message']['content']
                
                # Keep it brief
                if '.' in reply:
                    reply = reply.split('.')[0] + '.'
                    
                print(f"Avatar: {reply}\n")
                self.conversation_history.append(f"Avatar: {reply}")
                
                # Speak while already listening for next input
                await self.speak(reply)
                
            else:
                silence_count += 1
                if silence_count >= 2:  # Faster timeout
                    self.awake = False
                    await self.speak("Sleep mode")
                    break
                    
    async def run(self):
        print("💤 Say 'Hey Curtis' or 'Computer'...")
        
        while True:
            if not self.awake:
                # Listen for wake with v3
                text = self.listen(2).lower()
                
                # Check for wake words
                if any(word in text for word in self.wake_words):
                    print(f"\n⚡ Wake detected: '{text}'")
                    self.awake = True
                    self.conversation_history = []  # Clear history
                    await self.conversation()
                    print("\n💤 Sleeping...")
                    
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    avatar = InteractiveAvatar()
    asyncio.run(avatar.run())
