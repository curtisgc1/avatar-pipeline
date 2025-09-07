# Avatar Pipeline Project

## Overview
This project implements an AI avatar system using various components for speech recognition, language processing, text-to-speech, and display. It leverages GPUs (RTX 5080 for LLM, RTX 4090 for TTS) and onboard graphics for display management.

## Components
- **STT (Speech-to-Text)**: Whisper ASR via Docker (port 9000)
- **LLM**: vLLM with Qwen2.5-3B model (port 8000)
- **TTS**: Kokoro TTS (port 5002)
- **Display**: Pygame/OpenCV for avatar rendering
- **Audio**: PyAudio for input/output
- **Wake Word**: Porcupine or STT-based
- **Memory**: Persistent conversation memory

## Installation Steps
1. **Install Ubuntu 22.04** with onboard ASPEED graphics as primary, PCIe as secondary.
2. **Install NVIDIA Drivers**:
   ```
   sudo apt update
   sudo apt install nvidia-driver-580
   ```
3. **Install Docker**:
   ```
   sudo apt install docker.io docker-compose
   sudo systemctl enable docker
   ```
4. **Install Python Dependencies**:
   ```
   pip install -r requirements.txt
   ```
5. **Configure GPU UUIDs** in `.env`:
   - GPU_5080_UUID: [your RTX 5080 UUID]
   - GPU_4090_UUID: [your RTX 4090 UUID]
6. **Blacklist NVIDIA for Display** (to use onboard VGA):
   - Create `/etc/modprobe.d/blacklist-nvidia.conf` with:
     ```
     blacklist nvidia
     blacklist nvidia_drm
     blacklist nvidia_modeset
     ```
   - `sudo update-initramfs -u`
7. **Start Services**:
   ```
   cd /home/curtis/avatar-pipeline
   docker-compose up -d
   ```
8. **Run Avatar**:
   - For VGA GUI: `python3 main_pipeline.py`
   - For HDMI Avatar: `sudo xinit python3 test_avatar_on_monitor.py -- :1 vt8`

## How It Works
1. **Audio Input**: Records from ReSpeaker mic using VAD.
2. **STT**: Sends audio to Whisper for transcription.
3. **LLM**: Processes text with Qwen2.5-3B for response.
4. **TTS**: Generates speech with Kokoro.
5. **Display**: Renders avatar on screen with Pygame.
6. **Wake Word**: Listens for "computer" or custom word.
7. **Commands**: Supports volume, voice, memory, sleep/wake.

## Configuration
- Edit `avatar_config.json` for settings.
- Use `wake_config.json` for wake words.
- GPU binding via `.env`.

## Troubleshooting
- VGA not working: Check BIOS for onboard primary.
- HDMI blank: Ensure NVIDIA loaded for 4090.
- Services down: `docker ps` to check.

## Files
- `main_pipeline.py`: Main script
- `docker-compose.yml`: Services
- `requirements.txt`: Python deps
- `test_avatar_on_monitor.py`: Display test

For issues, check logs in `ai-avatar.log`.
