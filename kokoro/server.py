from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import io
import numpy as np
import wave

app = FastAPI()

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0

@app.post("/synthesize")
async def synthesize(request: TTSRequest):
    try:
        # Generate a simple sine wave as placeholder audio
        sample_rate = 24000
        duration = 1  # seconds
        t = np.linspace(0, duration, int(sample_rate * duration))
        frequency = 440  # Hz (A4 note)
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)  # mono
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            wav.writeframes(audio_int16.tobytes())
        
        # Get the WAV data and encode to base64
        buffer.seek(0)
        wav_data = buffer.read()
        audio_b64 = base64.b64encode(wav_data).decode('utf-8')
        
        return {
            "audio": audio_b64,
            "sample_rate": sample_rate,
            "text": request.text,
            "format": "wav"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/")
async def root():
    return {"message": "TTS Server"}
