#!/usr/bin/env python3
"""
Simple Lip Sync Demo
Demonstrates the lip sync system without full avatar display
"""

import time
import threading
from lip_sync_engine import LipSyncEngine

def simple_mouth_animation(viseme_value):
    """Simple text-based mouth animation"""
    mouth_chars = ['○', '◯', '●', '○']  # Different mouth shapes
    index = int(viseme_value * 3)
    mouth = mouth_chars[min(index, 3)]
    print(f'\rAvatar: {mouth}  ', end='', flush=True)

class SimpleLipSyncDemo:
    def __init__(self):
        self.engine = LipSyncEngine()
        self.is_speaking = False

    def on_viseme_update(self, viseme_data):
        """Handle viseme updates"""
        if viseme_data.get('speaking'):
            simple_mouth_animation(viseme_data.get('mouth', 0.0))
        else:
            print('\rAvatar: -  ', end='', flush=True)

    def demo(self):
        """Run the lip sync demo"""
        print("🎭 Lip Sync Demo")
        print("=================")
        print("This demo shows mouth animation synchronized with TTS audio.")
        print("Press Ctrl+C to exit.\n")

        # Start the lip sync engine
        self.engine.start()

        # Test phrases
        test_phrases = [
            "Hello! Welcome to the lip sync demo.",
            "This avatar can move its mouth in real time.",
            "The animation is synchronized with the audio playback.",
            "Thank you for watching this demonstration!"
        ]

        try:
            for phrase in test_phrases:
                print(f"\nSpeaking: {phrase}")
                self.engine.speak_text(phrase)
                time.sleep(1)  # Brief pause between phrases

            print("\n✅ Demo complete! The lip sync system is working.")
            print("💡 To see the full avatar, run: python3 test_lip_sync.py")

            # Keep running to show idle state
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 Stopping demo...")
        finally:
            self.engine.stop()

if __name__ == "__main__":
    demo = SimpleLipSyncDemo()
    demo.demo()
