# Avatar Pipeline Configuration - September 4, 2025
# This file documents the current state of your avatar pipeline setup

## Project Location
/home/curtis/avatar-pipeline

## Hardware Configuration
- RTX 5080 (GPU 0): GPU-588625df-63e3-a721-1b4b-df882b837b3d (for vLLM)
- RTX 4090 (GPU 1): GPU-65f840f0-e3eb-20dd-8701-fd28db808a8c (for TTS/Display)
- ReSpeaker Microphone: hw:2,0
- HDMI Display: Connected to RTX 4090

## Services Configuration
### Docker Services (docker-compose.yml)
- vLLM (Qwen2.5-3B): Port 8000
- Whisper STT: Port 9000
- Kokoro TTS: Port 5002
- Redis (Viseme Bus): Port 6379

### Environment Variables (.env)
GPU_5080_UUID=GPU-588625df-63e3-a721-1b4b-df882b837b3d
GPU_4090_UUID=GPU-65f840f0-e3eb-20dd-8701-fd28db808a8c
SERVER_IP=192.168.1.100
DISPLAY=:0
MODEL_PATH=/home/curtis/avatar-models
AUDIO_DEVICE=plughw:2,0

## VS Code Extensions
- formulahendry.code-runner
- github.copilot
- github.copilot-chat

## Key Files
- main_pipeline.py: Main orchestrator (currently being developed)
- avatar_interactive.py: Interactive avatar with display
- avatar_complete.py: Voice-only avatar
- kokoro/server.py: TTS service
- docker-compose.yml: Service orchestration

## Current Status
✅ GPU configuration complete
✅ Basic services configured
✅ Avatar display working on 4090 HDMI
✅ Audio input/output tested
🔄 Main pipeline integration in progress

## Quick Start Commands
# Start services
docker-compose up -d

# Test pipeline
python3 test_pipeline.py

# Run interactive avatar
python3 avatar_interactive.py

# Run main pipeline (when complete)
python3 main_pipeline.py

## Backup Location
Latest backup: /home/curtis/avatar-pipeline-backup-YYYYMMDD-HHMMSS.tar.gz

## Notes
- Run avatar display from Ubuntu desktop terminal with DISPLAY=:0
- Use dedicated X session (:2) for production
- ReSpeaker is on audio device hw:2,0
- HDMI output goes through RTX 4090
