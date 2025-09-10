#!/usr/bin/env python3
"""
Lip Sync System for Avatar Pipeline
Provides real-time mouth animation synchronized with TTS audio
"""

import numpy as np
import wave
import audioop
import threading
import time
import json
import socket
import subprocess
import os
from pathlib import Path
import requests
import struct

class LipSyncEngine:
    def __init__(self, brain_server="192.168.1.235", jetson_client="192.168.1.31"):
        self.brain_server = brain_server
        self.jetson_client = jetson_client
        self.tts_url = f"http://{brain_server}:5002"
        self.is_speaking = False
        self.current_audio_data = None
        self.viseme_queue = []
        self.socket_thread = None
        self.running = False

        # Viseme mapping (simplified phoneme-to-mouth-shape)
        self.viseme_map = {
            'A': 0.9,  # Wide open (ah, father)
            'E': 0.7,  # Mid open (eh, bed)
            'I': 0.3,  # Narrow (ee, machine)
            'O': 0.8,  # Round (oh, go)
            'U': 0.6,  # Rounded narrow (oo, too)
            'M': 0.2,  # Closed (mmm)
            'B': 0.4,  # Bilabial (buh)
            'P': 0.4,  # Bilabial (puh)
            'F': 0.5,  # Fricative (fuh)
            'V': 0.5,  # Fricative (vuh)
            'S': 0.1,  # Sibilant (sss)
            'Z': 0.1,  # Sibilant (zzz)
            'T': 0.3,  # Alveolar (tuh)
            'D': 0.3,  # Alveolar (duh)
            'K': 0.2,  # Velar (kuh)
            'G': 0.2,  # Velar (guh)
            'L': 0.4,  # Lateral (luh)
            'R': 0.6,  # Retroflex (ruh)
            'W': 0.7,  # Rounded (wuh)
            'Y': 0.3,  # Palatal (yuh)
            'TH': 0.4, # Dental (thuh)
            'SH': 0.2, # Palatal fricative (shuh)
            'CH': 0.3, # Affricate (chuh)
            'J': 0.3,  # Affricate (juh)
            'default': 0.1  # Closed mouth
        }

    def start(self):
        """Start the lip sync engine"""
        self.running = True
        self.socket_thread = threading.Thread(target=self._socket_listener, daemon=True)
        self.socket_thread.start()
        print("🎭 Lip Sync Engine started")

    def stop(self):
        """Stop the lip sync engine"""
        self.running = False
        self.is_speaking = False
        if self.socket_thread:
            self.socket_thread.join()
        print("🎭 Lip Sync Engine stopped")

    def _socket_listener(self):
        """Listen for TTS commands from main pipeline"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('localhost', 5556))  # Different port from avatar display
        sock.settimeout(0.1)

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                msg = json.loads(data.decode())

                if msg.get('action') == 'speak':
                    text = msg.get('text', '')
                    threading.Thread(target=self._process_tts_request, args=(text,), daemon=True).start()

            except socket.timeout:
                continue
            except Exception as e:
                print(f"Socket error: {e}")
                continue

    def _process_tts_request(self, text):
        """Process TTS request with lip sync"""
        try:
            # Generate TTS audio
            audio_file = self._generate_tts_audio(text)
            if not audio_file:
                return

            # Extract visemes from audio
            visemes = self._extract_visemes_from_audio(audio_file, text)

            # Start synchronized playback and animation
            self._play_with_lip_sync(audio_file, visemes)

        except Exception as e:
            print(f"TTS processing error: {e}")

    def _generate_tts_audio(self, text):
        """Generate TTS audio from brain server"""
        try:
            response = requests.post(
                f"{self.tts_url}/synthesize",
                json={
                    "text": text,
                    "voice": "af_bella",
                    "speed": 1.0
                },
                timeout=30
            )

            if response.status_code == 200:
                # The response should contain audio data
                audio_file = "temp_lip_sync.wav"
                with open(audio_file, 'wb') as f:
                    f.write(response.content)
                return audio_file

        except Exception as e:
            print(f"TTS generation error: {e}")

        return None

    def _extract_visemes_from_audio(self, audio_file, text=""):
        """Extract viseme timing from audio file"""
        visemes = []

        try:
            with wave.open(audio_file, 'rb') as wf:
                sample_rate = wf.getframerate()
                n_frames = wf.getnframes()
                audio_data = wf.readframes(n_frames)

                # Convert to numpy array
                if wf.getsampwidth() == 2:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                else:
                    audio_array = np.frombuffer(audio_data, dtype=np.int8)

                # Simple energy-based viseme detection
                frame_size = int(sample_rate * 0.02)  # 20ms frames
                step_size = int(sample_rate * 0.01)   # 10ms step

                for i in range(0, len(audio_array) - frame_size, step_size):
                    frame = audio_array[i:i + frame_size]

                    # Calculate RMS energy
                    rms = np.sqrt(np.mean(frame.astype(np.float64) ** 2))

                    # Normalize to 0-1 range
                    energy = min(rms / 10000.0, 1.0)

                    # Map energy to viseme (higher energy = more open mouth)
                    viseme_value = energy

                    # Add timing information
                    timestamp = i / sample_rate
                    visemes.append({
                        'time': timestamp,
                        'viseme': viseme_value,
                        'duration': step_size / sample_rate
                    })

        except Exception as e:
            print(f"Viseme extraction error: {e}")
            # Fallback: simple text-based viseme generation
            visemes = self._generate_text_based_visemes(text)

        return visemes

    def _generate_text_based_visemes(self, text):
        """Generate basic visemes from text (fallback method)"""
        visemes = []
        words = text.split()
        duration_per_word = 0.3  # seconds
        current_time = 0

        for word in words:
            # Simple vowel/consonant detection
            for char in word.lower():
                if char in 'aeiou':
                    viseme = 0.7  # Open for vowels
                elif char in 'mpb':
                    viseme = 0.2  # Closed for bilabials
                elif char in 'fv':
                    viseme = 0.4  # Mid for fricatives
                else:
                    viseme = 0.3  # Default mid

                visemes.append({
                    'time': current_time,
                    'viseme': viseme,
                    'duration': 0.1
                })
                current_time += 0.1

            current_time += 0.1  # Pause between words

        return visemes

    def _play_with_lip_sync(self, audio_file, visemes):
        """Play audio while sending lip sync data to avatar"""
        self.is_speaking = True

        try:
            # Start audio playback
            playback_process = subprocess.Popen(
                ['aplay', '-q', audio_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Send lip sync data to avatar display
            start_time = time.time()

            for viseme in visemes:
                # Wait for the right timing
                while time.time() - start_time < viseme['time']:
                    time.sleep(0.01)

                # Send viseme data to avatar
                self._send_viseme_to_avatar(viseme['viseme'])

                # Hold the viseme for its duration
                time.sleep(viseme['duration'])

            # Wait for audio to finish
            playback_process.wait()

        except Exception as e:
            print(f"Lip sync playback error: {e}")

        finally:
            self.is_speaking = False
            self._send_viseme_to_avatar(0.0)  # Close mouth

            # Clean up
            if os.path.exists(audio_file):
                os.remove(audio_file)

    def _send_viseme_to_avatar(self, viseme_value):
        """Send viseme data to avatar display"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            message = json.dumps({
                'speaking': self.is_speaking,
                'mouth': viseme_value,
                'timestamp': time.time()
            })
            sock.sendto(message.encode(), ('localhost', 5555))  # Avatar display port
            sock.close()
        except Exception as e:
            print(f"Avatar communication error: {e}")

    def speak_text(self, text):
        """Public method to speak text with lip sync"""
        threading.Thread(target=self._process_tts_request, args=(text,), daemon=True).start()

# Enhanced Avatar Display with better lip sync
class LipSyncAvatarDisplay:
    def __init__(self):
        self.is_speaking = False
        self.mouth_state = 0.0
        self.last_update = time.time()

        # Socket for receiving lip sync data
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('localhost', 5555))
        self.sock.settimeout(0.1)

        # OpenCV window setup
        try:
            import cv2
            self.cv2 = cv2
            self.cv2.namedWindow('Avatar', self.cv2.WINDOW_NORMAL)
            self.cv2.setWindowProperty('Avatar', self.cv2.WND_PROP_FULLSCREEN, self.cv2.WINDOW_FULLSCREEN)
            self.display_available = True
        except:
            print("OpenCV not available, using text-only mode")
            self.display_available = False

    def listen_for_lip_sync(self):
        """Listen for lip sync data"""
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = json.loads(data.decode())

                self.is_speaking = msg.get('speaking', False)
                self.mouth_state = msg.get('mouth', 0.0)
                self.last_update = time.time()

            except socket.timeout:
                # Check if we should close mouth (no updates for 0.5s)
                if time.time() - self.last_update > 0.5:
                    self.is_speaking = False
                    self.mouth_state = 0.0
                continue
            except:
                continue

    def draw_avatar(self, frame):
        """Draw avatar with lip sync"""
        if not self.display_available:
            return frame

        h, w = frame.shape[:2]
        cx, cy = w//2, h//2

        # Head
        self.cv2.circle(frame, (cx, cy-50), 150, (200, 180, 160), -1)
        self.cv2.circle(frame, (cx, cy-50), 150, (100, 80, 60), 3)

        # Eyes
        eye_y = cy - 80
        self.cv2.ellipse(frame, (cx-50, eye_y), (25, 20), 0, 0, 360, (255, 255, 255), -1)
        self.cv2.ellipse(frame, (cx+50, eye_y), (25, 20), 0, 0, 360, (255, 255, 255), -1)
        self.cv2.circle(frame, (cx-50, eye_y), 10, (50, 50, 200), -1)
        self.cv2.circle(frame, (cx+50, eye_y), 10, (50, 50, 200), -1)

        # Lip sync mouth
        mouth_y = cy + 20
        mouth_width = 40
        mouth_height = int(10 + self.mouth_state * 40)  # 10-50 pixels based on viseme

        if self.is_speaking:
            # Animated mouth based on viseme
            self.cv2.ellipse(frame, (cx, mouth_y), (mouth_width, mouth_height), 0, 0, 180, (50, 50, 50), -1)
        else:
            # Closed mouth
            self.cv2.ellipse(frame, (cx, mouth_y), (mouth_width, 10), 0, 0, 180, (50, 50, 50), 2)

        # Status text
        status = "🗣️ Speaking..." if self.is_speaking else "Idle"
        self.cv2.putText(frame, status, (50, h-50),
                        self.cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        return frame

    def run(self):
        """Main display loop"""
        if not self.display_available:
            print("Display not available")
            return

        # Start lip sync listener
        listener = threading.Thread(target=self.listen_for_lip_sync, daemon=True)
        listener.start()

        print("🎭 Lip Sync Avatar Display Running (Press 'q' to quit)")

        while True:
            frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            frame[:] = (30, 30, 40)  # Dark background

            frame = self.draw_avatar(frame)

            self.cv2.imshow('Avatar', frame)

            if self.cv2.waitKey(30) & 0xFF == ord('q'):
                break

        self.cv2.destroyAllWindows()

if __name__ == "__main__":
    # Test the lip sync system
    engine = LipSyncEngine()
    display = LipSyncAvatarDisplay()

    # Start both components
    engine.start()

    # Start display in separate thread
    display_thread = threading.Thread(target=display.run, daemon=True)
    display_thread.start()

    # Test with some text
    time.sleep(2)  # Let display start
    engine.speak_text("Hello! This is a test of the lip sync system.")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.stop()
        print("Lip sync test complete")
