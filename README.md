# AI Avatar System - Distributed Godot Architecture

## Overview
This is a distributed AI avatar system using Godot 4.x for 3D/2D avatar rendering, with separate brain and satellite nodes for scalable deployment.

## Architecture

### 🧠 Main Brain Server (RTX 4090)
**Location**: `~/brain/`
**Purpose**: Central AI processing and 3D avatar rendering

**Services**:
- **Ollama** (GPU 5080): AI language model inference
- **XTTS Server** (GPU 5080): High-quality text-to-speech
- **Home Assistant**: Smart home integration
- **Redis**: Distributed message bus
- **Qdrant**: Vector database for memory/context
- **Godot 3D Avatar**: Main avatar with lip sync and facial tracking

### 🛰️ Jetson Satellite Nodes (2D Avatars)
**Location**: `~/jetson/`
**Purpose**: Room-based 2D avatar deployment

**Services**:
- **Wyoming OpenWakeWord**: Local wake word detection
- **Wyoming Whisper**: Local speech-to-text (GPU accelerated)
- **Wyoming Piper**: Local text-to-speech
- **Godot 2D Avatar**: Lightweight room avatar

### 🎮 Godot Avatar System

#### 3D Avatar Features:
- Full 3D character with skeletal animation
- Real-time lip sync using Rhubarb/MFA phoneme analysis
- Facial tracking via OpenSeeFace UDP receiver
- Blend shapes and bone-based mouth animation
- Eye tracking and blinking simulation

#### 2D Avatar Features:
- Lightweight sprite-based avatar
- Redis-connected for distributed control
- Unique satellite IDs for room identification
- Optimized for Jetson performance

## Quick Start

### 1. Brain Server Setup
```bash
cd ~/brain
# Configure .env with your GPU IDs and HA credentials
docker compose up -d
```

### 2. Jetson Satellite Setup
```bash
cd ~/jetson
# Configure .env with brain IP and satellite ID
docker compose up -d
```

### 3. Start Godot Avatars
```bash
# 3D Avatar (Brain)
cd ~/brain/services/godot-avatar-3d
godot --fullscreen

# 2D Avatar (Jetson)
cd ~/jetson/services/godot-avatar-2d
godot --fullscreen
```

## Configuration

### Brain Server (.env)
```bash
GPU_5080_ID=0
GPU_4090_ID=1
REDIS_PASSWORD=your_password
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_ha_token
```

### Jetson Satellite (.env)
```bash
BRAIN_IP=192.168.1.100
REDIS_PASSWORD=your_password
SATELLITE_ID=living_room
```

## Godot Development

### Project Structure
```
godot-avatar-3d/
├── project.godot
├── scenes/
│   ├── main.tscn
│   └── avatar.tscn
├── scripts/
│   ├── avatar_driver.gd
│   ├── openseeface_receiver.gd
│   └── viseme_map.gd
└── assets/
    ├── models/
    └── audio/
```

### Key Scripts
- **AvatarDriver.gd**: Main avatar controller with lip sync
- **OpenSeeFaceReceiver.gd**: UDP receiver for facial tracking
- **VisemeMap.gd**: ARPABET to viseme conversion

## Communication

### Redis Channels
- `avatar:commands`: Voice commands from satellites
- `avatar:responses`: AI responses from brain
- `avatar:events`: System status and events
- `satellite:{id}:status`: Individual satellite status

### Message Format
```json
{
  "type": "voice_command",
  "satellite_id": "living_room",
  "text": "turn on the lights",
  "timestamp": 1640995200
}
```

## Development

### Prerequisites
- Docker & Docker Compose
- NVIDIA Container Toolkit
- Godot 4.x
- Python 3.8+
- Visual Studio Code (recommended) - See [VSCODE_SETUP.md](VSCODE_SETUP.md) for setup

### Building Services
```bash
# Build brain services
cd ~/brain && docker compose build

# Build jetson services
cd ~/jetson && docker compose build
```

### Testing
```bash
# Test brain services
cd ~/brain && docker compose ps

# Test jetson services
cd ~/jetson && docker compose ps

# Test Redis connection
redis-cli -h brain_ip ping
```

## Troubleshooting

### Common Issues

**VS Code Sign-In Issues**:
If you can't sign in to VS Code or the authentication page freezes:
```bash
# Run the automated fix script
./fix_vscode_auth.sh

# Or see detailed troubleshooting guide
cat VSCODE_SETUP.md
```

**Godot Display Issues**:
```bash
# Force display output
export DISPLAY=:0
godot --fullscreen --no-window
```

**Redis Connection**:
```bash
# Test connection
redis-cli -h brain_ip -a password ping
```

**GPU Issues**:
```bash
# Check GPU status
nvidia-smi
# Verify container access
docker run --rm --gpus all nvidia/cuda nvidia-smi
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on both brain and satellite nodes
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
