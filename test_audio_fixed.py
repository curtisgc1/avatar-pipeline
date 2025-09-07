import requests
import base64
import subprocess

# Get audio from TTS
response = requests.post("http://localhost:5002/synthesize", 
                        json={"text": "Testing audio output"})

if response.status_code == 200:
    data = response.json()
    print(f"Got audio for: {data['text']}")
    print(f"Format: {data.get('format', 'unknown')}")
    
    # Decode the audio
    audio_bytes = base64.b64decode(data['audio'])
    
    # Save as WAV file
    with open('test_tone.wav', 'wb') as f:
        f.write(audio_bytes)
    
    # Play the audio (should hear a 440Hz tone)
    print("Playing test tone (440Hz beep)...")
    subprocess.run(['aplay', 'test_tone.wav'])
    
    print("\nAudio pipeline working!")
    print("Next: Add real TTS model for speech synthesis")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
