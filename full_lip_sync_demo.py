#!/usr/bin/env python3
"""
Full Lip Sync Demo with Audio for TV Display
Uses HDMI audio output
"""

import cv2
import numpy as np
import time
import subprocess
import threading
import requests
import os

class FullLipSyncDemo:
    def __init__(self):
        self.is_speaking = False
        self.mouth_state = 0.0
        self.audio_device = "hw:1,3"  # HDMI output

    def generate_tts_audio(self, text):
        """Generate TTS audio from brain server"""
        try:
            response = requests.post(
                "http://192.168.1.235:5002/synthesize",
                json={"text": text, "voice": "af_bella", "speed": 1.0},
                timeout=10
            )
            if response.status_code == 200:
                audio_file = f"tts_{hash(text) % 1000}.wav"
                with open(audio_file, "wb") as f:
                    f.write(response.content)
                return audio_file
        except Exception as e:
            print(f"TTS error: {e}")
        return None

    def play_audio_with_animation(self, audio_file, text):
        """Play audio while animating mouth"""
        if not audio_file or not os.path.exists(audio_file):
            print("No audio file to play")
            return

        self.is_speaking = True

        try:
            # Start audio playback with HDMI device
            playback = subprocess.Popen([
                "aplay", "-D", self.audio_device, "-q", audio_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Simple mouth animation based on text timing
            words = text.split()
            duration_per_word = 0.4  # seconds per word
            total_duration = len(words) * duration_per_word

            start_time = time.time()
            while time.time() - start_time < total_duration:
                elapsed = time.time() - start_time
                word_index = int(elapsed / duration_per_word)

                if word_index < len(words):
                    # Alternate mouth states for each word
                    self.mouth_state = 0.8 if (word_index % 2 == 0) else 0.5
                else:
                    self.mouth_state = 0.0

                time.sleep(0.05)  # Update mouth every 50ms

            playback.wait()

        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            self.is_speaking = False
            self.mouth_state = 0.0

            # Clean up audio file
            if audio_file and os.path.exists(audio_file):
                os.remove(audio_file)

    def draw_avatar(self, frame):
        """Draw avatar with animated mouth"""
        h, w = frame.shape[:2]
        cx, cy = w//2, h//2

        # Head
        cv2.circle(frame, (cx, cy-50), 250, (200, 180, 160), -1)
        cv2.circle(frame, (cx, cy-50), 250, (100, 80, 60), 3)

        # Eyes
        eye_y = cy - 100
        cv2.ellipse(frame, (cx-70, eye_y), (35, 30), 0, 0, 360, (255, 255, 255), -1)
        cv2.ellipse(frame, (cx+70, eye_y), (35, 30), 0, 0, 360, (255, 255, 255), -1)
        cv2.circle(frame, (cx-70, eye_y), 15, (50, 50, 200), -1)
        cv2.circle(frame, (cx+70, eye_y), 15, (50, 50, 200), -1)

        # Animated mouth
        mouth_y = cy + 40
        mouth_width = 60
        mouth_height = int(20 + self.mouth_state * 40)  # 20-60 pixels

        if self.is_speaking:
            cv2.ellipse(frame, (cx, mouth_y), (mouth_width, mouth_height), 0, 0, 180, (50, 50, 50), -1)
        else:
            cv2.ellipse(frame, (cx, mouth_y), (mouth_width, 20), 0, 0, 180, (50, 50, 50), 2)

        # Status text
        status = "🗣️ Speaking..." if self.is_speaking else "Idle - Full Lip Sync Demo"
        cv2.putText(frame, status, (100, h-100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 2)

        # Title
        cv2.putText(frame, "AI Avatar with Lip Sync", (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 2.5, (255, 255, 0), 4)

        return frame

    def run_demo(self):
        """Run the full lip sync demo"""
        print("🎭 Starting Full Lip Sync Demo on TV...")
        print(f"🎵 Using audio device: {self.audio_device}")

        # Set up display
        cv2.namedWindow('AI Avatar', cv2.WINDOW_NORMAL)
        cv2.setWindowProperty('AI Avatar', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        # Demo phrases
        phrases = [
            "Hello! I am your AI avatar with lip sync.",
            "Watch my mouth move as I speak to you.",
            "This demonstrates real-time synchronization.",
            "The animation matches the audio perfectly.",
            "Thank you for watching this demonstration!"
        ]

        print("✅ Display and audio configured")
        print("🎬 Starting lip sync sequence...")

        try:
            for i, phrase in enumerate(phrases, 1):
                print(f"\n[Phrase {i}/{len(phrases)}] {phrase}")

                # Generate TTS audio
                audio_file = self.generate_tts_audio(phrase)

                if audio_file:
                    print("🎵 Playing audio with lip sync...")

                    # Start audio and animation in background
                    playback_thread = threading.Thread(
                        target=self.play_audio_with_animation,
                        args=(audio_file, phrase)
                    )
                    playback_thread.start()

                    # Display animation
                    start_time = time.time()
                    phrase_duration = len(phrase.split()) * 0.4 + 1  # Estimate duration

                    while time.time() - start_time < phrase_duration:
                        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                        frame[:] = (30, 30, 50)  # Dark background

                        frame = self.draw_avatar(frame)
                        cv2.imshow('AI Avatar', frame)

                        if cv2.waitKey(30) & 0xFF == ord('q'):
                            break

                    playback_thread.join()

                # Brief pause between phrases
                time.sleep(0.5)

            print("\n✅ Full lip sync demo complete!")
            print("🎉 You should have seen the avatar's mouth move in sync with speech!")

        except KeyboardInterrupt:
            print("\n🛑 Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo error: {e}")
        finally:
            cv2.destroyAllWindows()
            print("🧹 Cleanup complete")

if __name__ == "__main__":
    demo = FullLipSyncDemo()
    demo.run_demo()
