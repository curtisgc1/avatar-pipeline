#!/usr/bin/env python3
import whisper
import numpy as np
import subprocess
import json
import asyncio
import requests
import edge_tts
import tempfile
import os
from datetime import datetime
import hashlib
import wave

class VoiceIdentifiedAvatar:
    def __init__(self):
        self.whisper_tiny = whisper.load_model("tiny")  # For wake word
        self.whisper = None  # Load on demand
        self.profiles_file = "voice_profiles.json"
        self.load_profiles()
        
        print("=== Voice-Identified Avatar System ===")
        print("New users: Say 'Computer, this is [YourName]' to register")
        print("Existing users: Just say 'Computer'\n")
        
    def load_profiles(self):
        try:
            with open(self.profiles_file, 'r') as f:
                self.profiles = json.load(f)
        except:
            self.profiles = {}
            self.setup_curtis_profile()
            
    def setup_curtis_profile(self):
        """Your personalized profile"""
        self.profiles["curtis"] = {
            "name": "Curtis",
            "voice_signature": None,
            "preferences": {
                "voice": "en-US-GuyNeural",
                "volume": 30,  # Lower as requested
                "response_length": "brief",
                "wake_word": "jarvis"
            },
            "context": {
                "setup": "RTX 5080 for avatars, RTX 4090 for Ollama, 1TB RAM",
                "current_project": "Avatar pipeline with lip sync",
                "interests": ["AI", "real-time avatars", "voice systems"],
                "notes": []
            },
            "memory": {
                "conversations": [],
                "facts": [
                    "Prefers best models over speed",
                    "Has ReSpeaker 4-mic array",
                    "Monitor connected to 5080 HDMI",
                    "Running dual EPYC 7742s"
                ]
            }
        }
        self.save_profiles()
        
    def save_profiles(self):
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)
            
    def extract_voice_features(self, audio_file):
        """Extract voice features for identification"""
        with wave.open(audio_file, 'rb') as wav:
            frames = wav.readframes(-1)
            audio_data = np.frombuffer(frames, dtype=np.int16)
            
        # Simple voice signature (you can make this more sophisticated)
        features = {
            "mean_frequency": float(np.mean(np.abs(np.fft.fft(audio_data)[:1000]))),
            "std_frequency": float(np.std(np.abs(np.fft.fft(audio_data)[:1000]))),
            "energy": float(np.mean(audio_data ** 2))
        }
        return features
        
    def identify_user(self, audio_file):
        """Identify user by voice"""
        current_features = self.extract_voice_features(audio_file)
        
        best_match = None
        min_distance = float('inf')
        
        for user, profile in self.profiles.items():
            if profile.get('voice_signature'):
                # Calculate distance between voice signatures
                sig = profile['voice_signature']
                distance = sum([
                    abs(current_features[k] - sig[k]) / sig[k]
                    for k in current_features.keys()
                ])
                
                if distance < min_distance and distance < 0.3:  # Threshold
                    min_distance = distance
                    best_match = user
                    
        return best_match
        
    def register_new_user(self, name, audio_file):
        """Register new user with voice signature"""
        voice_sig = self.extract_voice_features(audio_file)
        
        self.profiles[name.lower()] = {
            "name": name,
            "voice_signature": voice_sig,
            "preferences": {
                "voice": "en-US-AriaNeural",
                "volume": 50,
                "response_length": "normal"
            },
            "context": {
                "registered": datetime.now().isoformat(),
                "notes": []
            },
            "memory": {
                "conversations": [],
                "facts": []
            }
        }
        
        self.save_profiles()
        return name.lower()
        
    async def personalized_response(self, user, text):
        """Generate response with user context"""
        profile = self.profiles[user]
        
        # Build context
        system_prompt = f"""You are talking to {profile['name']}. 
        Important context: {json.dumps(profile['context'], indent=2)}
        Known facts: {json.dumps(profile['memory']['facts'], indent=2)}
        Response style: {profile['preferences']['response_length']}
        Be conversational and remember their details."""
        
        # Add conversation memory
        if profile['memory']['conversations']:
            recent = profile['memory']['conversations'][-3:]
            system_prompt += f"\nRecent exchanges: {json.dumps(recent, indent=2)}"
            
        # Generate response
        response = requests.post("http://localhost:8000/v1/chat/completions", json={
            "model": "Qwen/Qwen2.5-3B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            "max_tokens": 50 if profile['preferences']['response_length'] == 'brief' else 150
        })
        
        reply = response.json()['choices'][0]['message']['content']
        
        # Store in memory
        profile['memory']['conversations'].append({
            "time": datetime.now().isoformat(),
            "user": text,
            "avatar": reply
        })
        
        # Keep only last 20 exchanges
        if len(profile['memory']['conversations']) > 20:
            profile['memory']['conversations'] = profile['memory']['conversations'][-20:]
            
        self.save_profiles()
        return reply
        
    async def speak(self, text, user="default"):
        """Speak with user's preferred settings"""
        if user in self.profiles:
            voice = self.profiles[user]['preferences']['voice']
            volume = self.profiles[user]['preferences']['volume']
        else:
            voice = "en-US-AriaNeural"
            volume = 50
            
        communicate = edge_tts.Communicate(text, voice)
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
            await communicate.save(tmp.name)
            subprocess.run([
                "ffplay", "-nodisp", "-autoexit", 
                "-volume", str(volume),
                tmp.name
            ], capture_output=True)
            os.unlink(tmp.name)
            
    async def run(self):
        print("💤 Listening for wake word...\n")
        
        while True:
            # Record for wake word
            subprocess.run([
                "arecord", "-D", "plughw:2,0", 
                "-f", "S16_LE", "-r", "16000", "-c", "1",
                "-d", "3", "-q", "wake.wav"
            ])
            
            # Check for wake word
            result = self.whisper_tiny.transcribe("wake.wav")
            text = result.get('text', '').lower()
            
            wake_words = ["computer", "jarvis", "avatar"]
            if any(word in text for word in wake_words):
                # Try to identify user
                user = self.identify_user("wake.wav")
                
                # Check if registering new user
                if "this is" in text:
                    words = text.split("this is")
                    if len(words) > 1:
                        name = words[1].strip().split()[0]
                        user = self.register_new_user(name, "wake.wav")
                        await self.speak(f"Voice registered for {name}. Nice to meet you!", user)
                        
                if user:
                    print(f"⚡ Identified: {self.profiles[user]['name']}")
                    
                    # Load main whisper if needed
                    if not self.whisper:
                        self.whisper = whisper.load_model("base")
                        
                    # Personalized greeting
                    await self.speak(f"Hello {self.profiles[user]['name']}", user)
                    
                    # Conversation loop
                    for _ in range(5):
                        subprocess.run([
                            "arecord", "-D", "plughw:2,0", 
                            "-f", "S16_LE", "-r", "16000", "-c", "1",
                            "-d", "4", "-q", "input.wav"
                        ])
                        
                        result = self.whisper.transcribe("input.wav")
                        user_text = result['text'].strip()
                        
                        if user_text and len(user_text) > 2:
                            print(f"{self.profiles[user]['name']}: {user_text}")
                            
                            if "goodbye" in user_text.lower():
                                await self.speak("Goodbye!", user)
                                break
                                
                            reply = await self.personalized_response(user, user_text)
                            print(f"Avatar: {reply}\n")
                            await self.speak(reply, user)
                            
                    print("💤 Back to sleep...\n")
                else:
                    await self.speak("I don't recognize you. Say 'Computer, this is YourName' to register")

if __name__ == "__main__":
    avatar = VoiceIdentifiedAvatar()
    asyncio.run(avatar.run())
