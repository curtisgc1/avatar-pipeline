import requests
import base64
import subprocess
import numpy as np

# Get audio from TTS
response = requests.post("http://localhost:5002/synthesize", 
                        json={"text": "Testing audio output"})

if response.status_code == 200:
    data = response.json()
    print(f"Got audio for: {data['text']}")
    print(f"Duration: {data.get('duration', 'unknown')} seconds")
    
    # Decode the audio
    audio_bytes = base64.b64decode(data['audio'])
    
    # Save to WAV file
    with open('test_tone.raw', 'wb') as f:
        f.write(audio_bytes)
    
    # Play the audio (440Hz tone)
    print("Playing test tone (should hear a beep)...")
    subprocess.run(['aplay', '-f', 'S16_LE', '-r', '24000', '-c', '1', 'test_tone.raw'])
    
    print("Did you hear the tone?")
else:
    print(f"Error: {response.status_code}")
