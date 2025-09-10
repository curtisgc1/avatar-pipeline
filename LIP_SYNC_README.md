# Avatar Pipeline with Lip Sync

This project implements a complete AI avatar system with real-time lip synchronization between text-to-speech audio and 2D avatar mouth animation.

## Features

- 🎭 **Real-time Lip Sync**: Synchronized mouth animation with TTS audio
- 🗣️ **Multi-TTS Support**: Kokoro, Piper, and eSpeak TTS engines
- 👁️ **2D Avatar Display**: OpenCV-based avatar with animated features
- 🔊 **Audio Pipeline**: STT → LLM → TTS with brain server integration
- 🌐 **Distributed Architecture**: Jetson client + Brain server communication
- 🎯 **Voice Commands**: Wake word detection and voice control

## Components

### 1. Lip Sync Engine (`lip_sync_engine.py`)
- Generates TTS audio from brain server
- Extracts visemes (mouth shapes) from audio
- Sends real-time animation data to avatar display
- Supports energy-based and text-based viseme generation

### 2. Enhanced Avatar Display
- Receives lip sync data via UDP socket
- Renders 2D avatar with animated mouth
- Fullscreen OpenCV display
- Real-time mouth shape updates

### 3. Main Pipeline (`main_pipeline.py`)
- Integrated with lip sync system
- Voice command processing
- Memory and settings management
- Home Assistant integration

## Setup

### Prerequisites
```bash
# Install Python dependencies
pip install numpy opencv-python requests pygame pyaudio

# Ensure brain services are running on 192.168.1.235
# - Redis (port 6379)
# - STT service (port 9000)
# - LLM service (port 8000)
# - TTS service (port 5002)
```

### Quick Start

1. **Test Lip Sync Independently**:
```bash
python3 test_lip_sync.py
```

2. **Start Full System**:
```bash
./start_avatar_with_lip_sync.sh
```

3. **Manual Startup**:
```bash
# Terminal 1: Start Lip Sync Engine
python3 lip_sync_engine.py

# Terminal 2: Start Avatar Display
python3 -c "from lip_sync_engine import LipSyncAvatarDisplay; LipSyncAvatarDisplay().run()"

# Terminal 3: Start Main Pipeline
python3 main_pipeline.py
```

## How It Works

### Lip Sync Process
1. **Text Input**: Main pipeline sends text to lip sync engine
2. **TTS Generation**: Engine requests audio from brain server TTS service
3. **Viseme Extraction**: Audio is analyzed to extract mouth shapes over time
4. **Real-time Animation**: Viseme data is sent to avatar display via UDP
5. **Synchronized Playback**: Audio plays while avatar mouth animates

### Viseme System
- **Energy-based**: Analyzes audio amplitude for mouth openness
- **Text-based**: Fallback using vowel/consonant patterns
- **Real-time**: 20ms frame analysis for smooth animation
- **Adaptive**: Mouth shapes range from closed (0.0) to wide open (1.0)

### Communication
- **Main Pipeline ↔ Lip Sync Engine**: UDP socket (port 5556)
- **Lip Sync Engine ↔ Avatar Display**: UDP socket (port 5555)
- **Brain Services**: HTTP REST APIs

## Configuration

### Network Settings
```python
# In lip_sync_engine.py
brain_server = "192.168.1.235"  # Brain server IP
jetson_client = "192.168.1.31"   # Jetson client IP
```

### TTS Settings
- **Kokoro**: High-quality neural TTS
- **Piper**: Local TTS with multiple voices
- **eSpeak**: Fallback system TTS

### Display Settings
- **Resolution**: 1920x1080 fullscreen
- **Frame Rate**: 30 FPS
- **Mouth Animation**: Smooth interpolation between visemes

## Voice Commands

The system supports various voice commands:
- **"Sleep now"**: Enter sleep mode
- **"Wake up"**: Exit sleep mode
- **"List voices"**: Show available TTS voices
- **"Voice [name]"**: Switch TTS voice
- **"Remember [text]"**: Store in memory
- **"What do you remember"**: Recall memories

## Troubleshooting

### Common Issues

1. **No Audio Playback**:
   - Check `aplay -l` for available devices
   - Verify PulseAudio or ALSA configuration

2. **Display Not Showing**:
   - Set `export DISPLAY=:0` for X11
   - Check OpenCV installation

3. **Lip Sync Not Working**:
   - Verify brain server TTS service is running
   - Check UDP socket connections (ports 5555, 5556)
   - Ensure firewall allows local UDP traffic

4. **Poor Lip Sync Quality**:
   - Audio analysis may need tuning for specific voices
   - Try different TTS engines for better results

### Debug Mode
```bash
# Enable verbose logging
export PYTHONPATH=/home/curtis/avatar-pipeline
python3 -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Main Pipeline │────│  Lip Sync Engine │────│ Avatar Display  │
│   (Jetson)      │    │    (Jetson)      │    │   (Jetson)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         └────────────────────────┴────────────────────────┘
                          ┌─────────────────┐
                          │  Brain Server   │
                          │ (192.168.1.235) │
                          │ - Redis         │
                          │ - STT Service   │
                          │ - LLM Service   │
                          │ - TTS Service   │
                          └─────────────────┘
```

## Future Enhancements

- **3D Avatar**: Upgrade to 3D model with blend shapes
- **Emotion Detection**: Facial expressions based on content
- **Gesture Animation**: Body language synchronized with speech
- **Multi-language**: Support for different languages
- **Custom Voices**: User-trained voice models

## Files

- `lip_sync_engine.py`: Core lip sync implementation
- `main_pipeline.py`: Main avatar pipeline with lip sync integration
- `avatar_display.py`: Basic avatar display (replaced by lip sync version)
- `start_avatar_with_lip_sync.sh`: Startup script
- `test_lip_sync.py`: Standalone test script
- `requirements.txt`: Python dependencies

## License

This project is part of the Avatar Pipeline system for AI-powered interactive avatars.
