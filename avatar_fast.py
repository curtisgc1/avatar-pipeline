#!/usr/bin/env python3
import speech_recognition as sr
import whisper
import requests
import asyncio
import edge_tts
import tempfile
import os
import threading
import queue
import time

class FastAvatar:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone(device_index=2)  # ReSpeaker
        self.whisper = None  # Load on demand
        self.listening = False
        self.awake = False
        self.command_queue = queue.Queue()
        
        # Adjust for ambient noise
        with self.mic as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
        print("=== Fast Avatar System ===")
        print("Say 'Computer' or 'Hey Avatar' to wake\n")
        
    def listen_continuous(self):
        """Continuous background listening"""
        with self.mic as source:
            while True:
                try:
                    # Listen with timeout for responsiveness
                    audio = self.recognizer.listen(source, timeout=0.5, phrase_time_limit=2)
                    
                    # Quick recognition using Google's API (faster than Whisper)
                    text = self.recognizer.recognize_google(audio).lower()
                    
                    # Check wake words
                    if not self.awake and any(word in text for word in ["computer", "avatar", "jarvis"]):
                        self.awake = True
                        self.command_queue.put("wake")
                    elif self.awake:
                        self.command_queue.put(text)
                        
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    pass
                    
    async def speak(self, text):
        """Fast TTS"""
        communicate = edge_tts.Communicate(text, "en-US-AriaNeural")
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            os.system(f"ffplay -nodisp -autoexit -volume 30 {tmp.name} 2>/dev/null")
            os.unlink(tmp.name)
            
    async def run(self):
        # Start background listener
        listener = threading.Thread(target=self.listen_continuous, daemon=True)
        listener.start()
        
        print("💤 Say 'Computer' to wake...")
        
        while True:
            try:
                # Check for commands
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    
                    if command == "wake":
                        print("⚡ Awake!")
                        await self.speak("Yes?")
                        
                        # Load Whisper if needed for better accuracy
                        if not self.whisper:
                            self.whisper = whisper.load_model("tiny")
                            
                        # Active conversation timeout
                        last_activity = time.time()
                        
                    elif self.awake:
                        print(f"You: {command}")
                        
                        if "goodbye" in command or "sleep" in command:
                            await self.speak("Going to sleep")
                            self.awake = False
                            print("💤 Sleeping...\n")
                            continue
                            
                        # Quick LLM response
                        response = requests.post("http://localhost:8000/v1/chat/completions", 
                            json={
                                "model": "Qwen/Qwen2.5-3B-Instruct",
                                "messages": [
                                    {"role": "system", "content": "Be very brief and conversational."},
                                    {"role": "user", "content": command}
                                ],
                                "max_tokens": 30
                            })
                            
                        reply = response.json()['choices'][0]['message']['content']
                        print(f"Avatar: {reply}\n")
                        await self.speak(reply)
                        
                        last_activity = time.time()
                        
                # Auto-sleep after 30 seconds of inactivity
                if self.awake and 'last_activity' in locals():
                    if time.time() - last_activity > 30:
                        self.awake = False
                        await self.speak("Going back to sleep")
                        print("💤 Auto-sleep...\n")
                        
            except KeyboardInterrupt:
                break
                
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    FastAvatar().run()
