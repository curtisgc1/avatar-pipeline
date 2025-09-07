import requests
import base64
import subprocess
import json

# Test TTS
response = requests.post("http://localhost:5002/synthesize", 
                        json={"text": "Hello Curtis, testing audio output"})

if response.status_code == 200:
    data = response.json()
    print(f"Got response for text: {data['text']}")
    
    # For now it's just placeholder, but when real audio works:
    # audio_data = base64.b64decode(data['audio'])
    # with open('test_output.wav', 'wb') as f:
    #     f.write(audio_data)
    # subprocess.run(['aplay', 'test_output.wav'])
    
    print("TTS endpoint working (placeholder mode)")
    print("\nNext step: Add real Kokoro model to generate actual audio")
else:
    print(f"Error: {response.status_code}")
