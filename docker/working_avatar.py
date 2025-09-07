import whisper
import requests
import pygame
from gtts import gTTS
import os
import tempfile

class AvatarSystem:
    def __init__(self):
        print("Initializing Avatar System...")
        self.whisper = whisper.load_model("base")
        self.vllm_url = "http://localhost:8000/v1/chat/completions"
        pygame.mixer.init()
        
    def record_audio(self, duration=3):
        """Record audio from ReSpeaker"""
        print(f"Recording for {duration} seconds...")
        os.system(f"arecord -D plughw:2,0 -f S16_LE -r 16000 -c 1 -d {duration} input.wav 2>/dev/null")
        return "input.wav"
        
    def transcribe(self, audio_file):
        """Convert speech to text"""
        print("Transcribing...")
        result = self.whisper.transcribe(audio_file)
        return result['text'].strip()
        
    def generate_response(self, user_text):
        """Generate AI response"""
        print("Thinking...")
        response = requests.post(self.vllm_url, json={
            "model": "Qwen/Qwen2.5-3B-Instruct",
            "messages": [
                {"role": "system", "content": "You are a friendly AI avatar. Keep responses concise and natural."},
                {"role": "user", "content": user_text}
            ],
            "max_tokens": 100,
            "temperature": 0.7
        })
        return response.json()['choices'][0]['message']['content']
        
    def speak(self, text):
        """Convert text to speech and play"""
        print("Speaking...")
        tts = gTTS(text=text, lang='en', slow=False)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tts.save(tmp_file.name)
            pygame.mixer.music.load(tmp_file.name)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            os.unlink(tmp_file.name)
            
    def chat_loop(self):
        """Main conversation loop"""
        print("\n=== Avatar System Ready ===")
        print("Press Enter to speak, or type 'quit' to exit\n")
        
        while True:
            input("Press Enter to start recording...")
            
            # Record and process
            audio_file = self.record_audio(3)
            user_text = self.transcribe(audio_file)
            
            if not user_text or len(user_text) < 2:
                print("No speech detected, try again.")
                continue
                
            print(f"\nYou: {user_text}")
            
            if "quit" in user_text.lower() or "exit" in user_text.lower():
                self.speak("Goodbye!")
                break
                
            # Generate and speak response
            response = self.generate_response(user_text)
            print(f"Avatar: {response}\n")
            self.speak(response)

if __name__ == "__main__":
    avatar = AvatarSystem()
    avatar.chat_loop()
