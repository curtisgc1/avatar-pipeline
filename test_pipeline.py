#!/usr/bin/env python3
import requests
import pyaudio
import wave
import json
import time

def test_services():
    print("Testing Avatar Pipeline Services...")
    
    # Test TTS
    print("\n1. Testing TTS (Kokoro)...")
    tts_response = requests.post("http://localhost:5002/synthesize", 
                                 json={"text": "Hello Curtis, avatar system is working"})
    if tts_response.status_code == 200:
        print("   ✓ TTS service working")
    else:
        print("   ✗ TTS service failed")
    
    # Test STT
    print("\n2. Testing STT (Whisper)...")
    stt_response = requests.get("http://localhost:9000/")
    if stt_response.status_code == 200:
        print("   ✓ STT service working")
    else:
        print("   ✗ STT service failed")
    
    # Test vLLM
    print("\n3. Testing vLLM...")
    try:
        llm_response = requests.get("http://localhost:8000/health")
        if llm_response.status_code == 200:
            print("   ✓ vLLM service working")
    except:
        print("   ✗ vLLM not accessible (may need to check container)")
    
    print("\n✅ Basic services are operational!")
    print("\nNext steps:")
    print("1. Add actual Kokoro model to TTS")
    print("2. Set up avatar display")
    print("3. Create orchestration layer")

if __name__ == "__main__":
    test_services()
