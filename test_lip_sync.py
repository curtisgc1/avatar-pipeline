#!/usr/bin/env python3
"""
Test script for Lip Sync System
"""

import time
import threading
from lip_sync_engine import LipSyncEngine, LipSyncAvatarDisplay

def test_lip_sync():
    """Test the lip sync system"""
    print("🎭 Testing Lip Sync System...")

    # Create instances
    engine = LipSyncEngine()
    display = LipSyncAvatarDisplay()

    # Start services
    engine.start()

    # Start display in background thread
    display_thread = threading.Thread(target=display.run, daemon=True)
    display_thread.start()

    # Wait for services to start
    time.sleep(3)

    # Test phrases
    test_phrases = [
        "Hello! This is a test of the lip sync system.",
        "The avatar should move its mouth as I speak.",
        "This demonstrates real-time synchronization between audio and visual animation.",
        "Thank you for testing the lip sync feature!"
    ]

    print("🎤 Starting test sequence...")
    for i, phrase in enumerate(test_phrases, 1):
        print(f"Test {i}: {phrase}")
        engine.speak_text(phrase)
        time.sleep(2)  # Wait between phrases

    print("✅ Test sequence complete")
    print("Press Ctrl+C to exit")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping test...")
        engine.stop()

if __name__ == "__main__":
    test_lip_sync()
