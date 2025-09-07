#!/usr/bin/env python3
import whisper
import subprocess
import requests
import asyncio
import edge_tts
import tempfile
import os
import time

class FixedAvatar:
    def __init__(self):
        print("Loading Whisper base model...")
        self.whisper = whisper.load_model("base")  # Faster, less hallucination
        
        self.wake_words = ["jarvis", "computer", "curtis"]
        self.voice = "en-US-AriaNeural"
        self.volume = 30
        self.awake = False
        
        print("\n=== Fixed Avatar System ===")
        print("Wake words: jarvis, computer, curtis\n")
        
    def listen(self, duration=3):
        """Record and transcribe with confidence check"""
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(duration), "-q", "temp.wav"
        ])
        
        # Transcribe with higher confidence threshold
        result = self.whisper.transcribe(
            "temp.wav", 
            language="en",
            fp16=False,
            no_speech_threshold=0.6,  # Higher threshold to avoid phantoms
            logprob_threshold=-1.0
        )
        
        text = result.get('text', '').strip()
        
        # Filter out common hallucinations
        hallucinations = ["thanks for watching", "subscribe", "bye", "you", "."]
        if text.lower() in hallucinations or len(text) < 3:
            return ""
            
        # Check confidence
        if result.get('no_speech_prob', 0) > 0.6:
            return ""  # Likely just noise
            
        return text
        
    async def speak(self, text):
        """Fixed audio output"""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            
            # Save to file
            audio_file = "response.mp3"
            await communicate.save(audio_file)
            
            # Play with explicit wait
            process = subprocess.Popen(
                ["ffplay", "-nodisp", "-autoexit", "-volume", str(self.volume), audio_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            process.wait()  # Wait for audio to finish
            
            # Clean up
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
        except Exception as e:
            print(f"Audio error: {e}")
            # Fallback to espeak
            subprocess.run(["espeak", text], capture_output=True)
            
    async def conversation(self):
        """Conversation loop with better filtering"""
        await self.speak("Ready")
        
        silence_count = 0
        
        while self.awake:
            text = self.listen(3)
            
            if text:  # Only process real speech
                silence_count = 0
                print(f"You: {text}")
                
                if "goodbye" in text.lower() or "sleep" in text.lower():
                    await self.speak("Goodbye")
                    self.awake = False
                    break
                    
                # Get response
                try:
                    response = requests.post("http://localhost:8000/v1/chat/completions",
                        json={
                            "model": "Qwen/Qwen2.5-3B-Instruct",
                            "messages": [
                                {"role": "system", "content": "Give very brief responses, max 15 words."},
                                {"role": "user", "content": text}
                            ],
                            "max_tokens": 25,
                            "temperature": 0.7
                        }, timeout=5)
                        
                    reply = response.json()['choices'][0]['message']['content']
                    
                    # Keep it very brief
                    if len(reply) > 50:
                        reply = reply[:50]
                        
                    print(f"Avatar: {reply}\n")
                    await self.speak(reply)
                    
                except Exception as e:
                    print(f"LLM error: {e}")
                    await self.speak("Error processing")
                    
            else:
                silence_count += 1
                if silence_count >= 3:
                    self.awake = False
                    await self.speak("Sleep mode")
                    break
                    
    async def run(self):
        print("💤 Say 'Computer' or 'Jarvis'...")
        
        while True:
            if not self.awake:
                text = self.listen(2).lower()
                
                # Only wake on clear wake word
                if text and any(word in text for word in self.wake_words):
                    print(f"\n⚡ Wake: '{text}'")
                    self.awake = True
                    await self.conversation()
                    print("\n💤 Sleeping...")
                    
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    # Test audio first
    print("Testing audio output...")
    subprocess.run(["espeak", "Audio test"], capture_output=True)
    
    avatar = FixedAvatar()
    asyncio.run(avatar.run())
