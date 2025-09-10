#!/usr/bin/env python3
"""
Simple Lip Sync Demo for TV Display
"""

import cv2
import numpy as np
import time
import subprocess
import threading

class SimpleLipSyncDemo:
    def __init__(self):
        self.is_speaking = False
        self.mouth_state = 0.0

    def generate_tts_audio(self, text):
        """Generate TTS audio from brain server"""
        try:
            import requests
            response = requests.post(
                "http://192.168.1.235:5002/synthesize",
                json={"text": text, "voice": "af_bella", "speed": 1.0},
                timeout=10
            )
            if response.status_code == 200:
                with open("demo_audio.wav", "wb") as f:
                    f.write(response.content)
                return "demo_audio.wav"
        except Exception as e:
            print(f"TTS error: {e}")
        return None

    def play_audio_with_animation(self, audio_file, text):
        """Play audio while animating mouth"""
        if not audio_file:
            return

        # Start audio playback
        playback = subprocess.Popen(["aplay", "-q", audio_file])

        # Simple mouth animation based on text timing
        words = text.split()
        duration_per_word = 0.3
        total_duration = len(words) * duration_per_word

        start_time = time.time()
        while time.time() - start_time < total_duration:
            elapsed = time.time() - start_time
            word_index = int(elapsed / duration_per_word)

            if word_index < len(words):
                # Alternate mouth states for each word
                self.mouth_state = 0.7 if (word_index % 2 == 0) else 0.3
            else:
                self.mouth_state = 0.0

            time.sleep(0.1)

        playback.wait()
        self.mouth_state = 0.0

    def draw_avatar(self, frame):
        """Draw avatar with animated mouth"""
        h, w = frame.shape[:2]
        cx, cy = w//2, h//2

        # Head
        cv2.circle(frame, (cx, cy-50), 200, (200, 180, 160), -1)
        cv2.circle(frame, (cx, cy-50), 200, (100, 80, 60), 3)

        # Eyes
        eye_y = cy - 100
        cv2.ellipse(frame, (cx-60, eye_y), (30, 25), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, (cx+60, eye_y), (30, 25), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (cx-60, eye_y), 12, (50, 50, 200), -1)
        cv2.circle(frame, (cx+60, eye_y), 12, (50, 50, 200), -1)

        # Animated mouth
        mouth_y = cy + 30
        mouth_width = 50
        mouth_height = int(15 + self.mouth_state * 35)  # 15-50 pixels

        if self.is_speaking:
            cv2.ellipse(frame, (cx, mouth_y), (mouth_width, mouth_height), 0, 0, 180, (50, 50, 50), -1)
        else:
            cv2.ellipse(frame, (cx, mouth_y), (mouth_width, 15), 0, 0, 180, (50, 50, 50), 2)

        # Status text
        status = "🗣️ Speaking..." if self.is_speaking else "Idle - Lip Sync Demo"
        cv2.putText(frame, status, (50, h-100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

        return frame

    def run_demo(self):
        """Run the lip sync demo"""
        print("🎭 Starting Lip Sync Demo on TV...")

        # Set up display
        cv2.namedWindow('Lip Sync Avatar', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('Lip Sync Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Demo phrases
        phrases = [
            "Hello! Welcome to the lip sync demo.",
            "This avatar can move its mouth in real time.",
            "The animation is synchronized with the audio playback.",
            "Thank you for watching this demonstration!"
        ]

        try:
            for phrase in phrases:
                print(f"\nSpeaking: {phrase}")

                # Generate TTS audio
                self.is_speaking = True
                audio_file = self.generate_tts_audio(phrase)

                if audio_file:
                    # Play audio with animation in background
                    animation_thread = threading.Thread(
                        target=self.play_audio_with_animation,
                        args=(audio_file, phrase)
                    )
                    animation_thread.start()

                    # Display animation
                    start_time = time.time()
                    while time.time() - start_time < 4:  # Show for 4 seconds
                        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                        frame[:] = (30, 30, 40)  # Dark background

                        frame = self.draw_avatar(frame)
                        cv2.imshow('Lip Sync Avatar', frame)

                        if cv2.waitKey(30) & 0xFF == ord('q'):
                            break

                    animation_thread.join()
                    self.is_speaking = False

                # Brief pause between phrases
                time.sleep(1)

            print("\n✅ Demo complete!")

        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted")
        finally:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    demo = SimpleLipSyncDemo()
    demo.run_demo()
