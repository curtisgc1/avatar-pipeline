#!/usr/bin/env python3
import whisper
import subprocess
import requests
import asyncio
import edge_tts
import tempfile
import os

class CleanAvatar:
    def __init__(self):
        print("Loading Whisper model...")
        self.whisper = whisper.load_model("small")  # Better than tiny, faster than base
        
        self.wake_words = ["jarvis", "computer", "avatar"]
        self.voice = "en-US-AriaNeural"
        self.volume = 30
        self.awake = False
        
        print("Ready. Say 'Jarvis' or 'Computer' to wake.\n")
        
    def listen(self, duration=3, prompt=""):
        """Record and transcribe"""
        if prompt:
            print(prompt)
            
        subprocess.run([
            "arecord", "-D", "plughw:2,0", "-f", "S16_LE",
            "-r", "16000", "-c", "1", "-d", str(duration), "-q", "temp.wav"
        ])
        
        result = self.whisper.transcribe("temp.wav", language="en")
        text = result.get('text', '').strip()
        
        # Remove common Whisper artifacts
        junk = ["Thank you.", "Thanks for watching.", "Bye.", "You."]
        if text in junk:
            return ""
            
        return text
        
    async def speak(self, text):
        """Only speak actual responses, not system messages"""
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            subprocess.run(
                ["ffplay", "-nodisp", "-autoexit", "-volume", str(self.volume), tmp.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            os.unlink(tmp.name)
            
    async def handle_conversation(self):
        """Single exchange after wake"""
        # Simple beep to indicate ready (no voice confirmation)
        os.system("aplay /usr/share/sounds/sound-icons/prompt.wav 2>/dev/null")
        
        # Listen for command
        text = self.listen(4)
        
        if text and len(text) > 2:
            print(f"You: {text}")
            
            # Don't speak confirmations for system commands
            if any(word in text.lower() for word in ["stop", "sleep", "goodbye", "bye"]):
                print("[Sleeping]")  # Just print, don't speak
                return False
                
            # Get AI response
            try:
                response = requests.post("http://localhost:8000/v1/chat/completions",
                    json={
                        "model": "Qwen/Qwen2.5-3B-Instruct",
                        "messages": [
                            {"role": "system", "content": "Answer in one short sentence."},
                            {"role": "user", "content": text}
                        ],
                        "max_tokens": 30
                    })
                    
                reply = response.json()['choices'][0]['message']['content']
                
                # Clean up response
                reply = reply.split('.')[0] + '.' if '.' in reply else reply
                
                print(f"Avatar: {reply}\n")
                await self.speak(reply)  # Only speak actual responses
                
                # Listen for follow-up
                return True
                
            except Exception as e:
                print(f"[Error: {e}]")
                return False
        else:
            print("[No input detected]")
            return False
            
    async def run(self):
        consecutive_wakes = 0
        
        while True:
            if not self.awake:
                # Listen for wake word
                text = self.listen(2).lower()
                
                if text and any(word in text for word in self.wake_words):
                    print(f"\n>>> Wake detected: '{text}'")
                    self.awake = True
                    consecutive_wakes = 0
                    
                    # Handle conversation
                    while self.awake and consecutive_wakes < 3:
                        keep_going = await self.handle_conversation()
                        
                        if not keep_going:
                            self.awake = False
                        else:
                            # Brief pause then listen again
                            consecutive_wakes += 1
                            await asyncio.sleep(0.5)
                            
                    self.awake = False
                    print("[Ready for wake word]\n")
                    
            await asyncio.sleep(0.1)

if __name__ == "__main__":
    avatar = CleanAvatar()
    asyncio.run(avatar.run())
