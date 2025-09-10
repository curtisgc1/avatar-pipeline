#!/usr/bin/env python3
import whisper
import requests
import subprocess
import asyncio
import edge_tts
import tempfile
import os
import json
import threading

class VoiceControlledAvatar:
    def __init__(self):
        print("Loading models...")
        self.whisper = whisper.load_model("base")
        self.vllm_url = "http://localhost:8000/v1/chat/completions"
        self.voice = "en-US-AriaNeural"
        self.speaking = False
        self.current_process = None
        
        # Settings
        self.config_file = "avatar_config.json"
        self.load_config()
        
        # Voice commands
        self.commands = {
            "stop": self.stop_speaking,
            "quiet": self.stop_speaking,
            "volume up": lambda: self.set_volume(self.volume + 20),
            "volume down": lambda: self.set_volume(self.volume - 20),
            "detailed response": lambda: setattr(self, 'max_tokens', 200),
            "brief response": lambda: setattr(self, 'max_tokens', 50),
            "change voice": self.change_voice,
            "faster": lambda: setattr(self, 'listen_duration', 2),
            "slower": lambda: setattr(self, 'listen_duration', 4),
        }
        
        print(f"Voice-Controlled Avatar Ready!")
        print("Commands: stop, volume up/down, detailed/brief response")
        print(f"Current: Volume {self.volume}%, {self.max_tokens} tokens max\n")
        
    def load_config(self):
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.volume = config.get('volume', 50)
                self.max_tokens = config.get('max_tokens', 50)
                self.listen_duration = config.get('listen_duration', 3)
        except:
            self.volume = 50
            self.max_tokens = 50
            self.listen_duration = 3
            self.save_config()
            
    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump({
                'volume': self.volume,
                'max_tokens': self.max_tokens,
                'listen_duration': self.listen_duration
            }, f)
            
    def stop_speaking(self):
        """Stop current speech"""
        if self.current_process:
            self.current_process.terminate()
            self.speaking = False
            return "Stopped"
        return None
        
    def set_volume(self, new_volume):
        """Set volume"""
        self.volume = max(10, min(100, new_volume))
        self.save_config()
        return f"Volume {self.volume}%"
        
    def change_voice(self):
        """Toggle between voices"""
        voices = ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"]
        current_idx = voices.index(self.voice)
        self.voice = voices[(current_idx + 1) % len(voices)]
        return f"Voice changed to {self.voice.split('-')[2]}"
        
    def detect_speech(self):
        """Record and transcribe"""
        print(f"🎧 Listening for {self.listen_duration}s...")
        
        # If currently speaking, stop to listen for interrupt commands
        if self.speaking:
            self.stop_speaking()
            
        subprocess.run([
            "arecord", "-D", "plughw:2,0", 
            "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", str(self.listen_duration), "-q", "input.wav"
        ])
        
        result = self.whisper.transcribe("input.wav")
        text = result['text'].strip()
        
        return text if text and len(text) > 2 else None
        
    async def speak(self, text, override_volume=None):
        """Speak with ability to be interrupted"""
        self.speaking = True
        
        # Limit length unless detailed mode
        if self.max_tokens <= 50 and len(text) > 150:
            text = text[:150] + "..."
            
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            
            volume = override_volume or self.volume
            self.current_process = subprocess.Popen([
                "ffplay", "-nodisp", "-autoexit", 
                "-volume", str(volume),
                tmp.name
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Start listening for interrupts in background
            interrupt_thread = threading.Thread(target=self.listen_for_interrupt)
            interrupt_thread.daemon = True
            interrupt_thread.start()
            
            self.current_process.wait()
            self.current_process = None
            self.speaking = False
            
            os.unlink(tmp.name)
            
    def listen_for_interrupt(self):
        """Background listener for stop commands during speech"""
        if not self.speaking:
            return
            
        # Quick 1-second listen for "stop"
        subprocess.run([
            "arecord", "-D", "plughw:2,0", 
            "-f", "S16_LE", "-r", "16000", "-c", "1",
            "-d", "1", "-q", "interrupt.wav"
        ])
        
        result = self.whisper.transcribe("interrupt.wav")
        text = result.get('text', '').strip().lower()
        
        if any(stop_word in text for stop_word in ['stop', 'quiet', 'shut']):
            self.stop_speaking()
            
    def process_command(self, text):
        """Check for voice commands"""
        text_lower = text.lower()
        
        # Check for volume with number
        if "volume" in text_lower:
            import re
            numbers = re.findall(r'\d+', text)
            if numbers:
                self.set_volume(int(numbers[0]))
                return f"Volume set to {self.volume}%"
                
        # Check other commands
        for cmd, action in self.commands.items():
            if cmd in text_lower:
                result = action()
                if result:
                    return result
                else:
                    self.save_config()
                    if "detailed" in cmd:
                        return "Detailed responses enabled"
                    elif "brief" in cmd:
                        return "Brief responses enabled"
                    elif "faster" in cmd:
                        return "Faster listening"
                    elif "slower" in cmd:
                        return "Slower listening"
                        
        return None
        
    async def run(self):
        print("=== Full Voice Control Avatar ===")
        print("Say 'stop' anytime to interrupt")
        print("Say 'detailed response' for longer answers\n")
        
        while True:
            text = self.detect_speech()
            
            if text:
                print(f"You: {text}")
                
                # Check for commands
                command_response = self.process_command(text)
                if command_response:
                    print(f"System: {command_response}\n")
                    await self.speak(command_response, override_volume=30)
                    continue
                
                # Check for exit
                if any(word in text.lower() for word in ["goodbye", "exit", "quit"]):
                    await self.speak("Goodbye!")
                    break
                
                # Generate response
                system_prompt = (
                    "You are a concise AI assistant. Give brief, direct answers in 1-2 sentences maximum."
                    if self.max_tokens <= 50 else
                    "You are a helpful AI assistant. Provide clear, informative responses."
                )
                
                response = requests.post(self.vllm_url, json={
                    "model": "Qwen/Qwen2.5-3B-Instruct",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": text}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7
                })
                
                reply = response.json()['choices'][0]['message']['content']
                print(f"Avatar: {reply}\n")
                
                await self.speak(reply)

if __name__ == "__main__":
    avatar = VoiceControlledAvatar()
    asyncio.run(avatar.run())
