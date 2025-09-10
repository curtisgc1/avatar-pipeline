# Avatar Pipeline Configuration - September 9, 2025
# This file documents the current state of your avatar pipeline setup

## Project Location
/home/curtis/avatar-pipeline

## Hardware Configuration
- **Jetson Orin Nano**: GPU-0b1bceb1-f932-552d-a009-72255ffb72bf (for vLLM, TTS, Display)
- **ReSpeaker 4 Mic Array**: hw:2,0 (USB Audio Device)
- **HDMI Display**: Connected to Jetson Orin
- **Network**: 192.168.1.31 (Jetson IP)

## Services Configuration
### Docker Services (docker-compose.yml)
- vLLM (Qwen2.5-3B): Port 8000 - Jetson GPU
- Whisper STT: Port 9000 - CPU optimized
- Kokoro TTS: Port 5002 - Jetson GPU
- Redis (Viseme Bus): Port 6379 - Communication bus

### Environment Variables (.env)
GPU_5080_UUID=0b1bceb1-f932-552d-a009-72255ffb72bf
GPU_4090_UUID=0b1bceb1-f932-552d-a009-72255ffb72bf
SERVER_IP=192.168.1.31
DISPLAY=:0
MODEL_PATH=/home/curtis/avatar-models
AUDIO_DEVICE=hw:2,0

## VS Code Extensions
- formulahendry.code-runner
- github.copilot
- github.copilot-chat

## Key Files
- main_pipeline.py: Main orchestrator (currently being developed)
- avatar_interactive.py: Interactive avatar with display
- avatar_complete.py: Voice-only avatar
- kokoro/server.py: TTS service (placeholder)
- docker-compose.yml: Service orchestration

## Current Status
✅ Jetson Orin configured with passwordless SSH
✅ Docker and NVIDIA Container Runtime installed
✅ GPU UUID configured for Jetson
✅ Audio devices detected (ReSpeaker on card 2)
✅ Services configured for Jetson compatibility
🔄 ALSA audio configuration needs fixing
🔄 Main pipeline integration in progress

## Quick Start Commands
# Start services (from Jetson)
docker compose up -d

# Test pipeline
python3 test_pipeline.py

# Run interactive avatar
python3 avatar_interactive.py

# Run main pipeline (when complete)
python3 main_pipeline.py

## Backup Location
Latest backup: /home/curtis/avatar-pipeline-backup-YYYYMMDD-HHMMSS.tar.gz

## Notes
- Run avatar display from Jetson desktop with DISPLAY=:0
- ReSpeaker is on audio device hw:2,0
- All services use Jetson Orin GPU
- Audio configuration needs ALSA fixes
