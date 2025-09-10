# AI Avatar System Architecture - Distributed Godot Implementation
# September 9, 2025

## System Architecture

The AI Avatar System consists of a distributed architecture with Godot 4.x avatars running on separate brain and satellite nodes:

### 🧠 Main Brain Server (RTX 4090)
**Location**: `~/brain/`
**Hardware**: RTX 4090 (GPU 1) + RTX 5080 (GPU 0)
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
**Hardware**: Jetson Orin Nano with GPU acceleration
**Purpose**: Room-based 2D avatar deployment

**Services**:
- **Wyoming OpenWakeWord**: Local wake word detection
- **Wyoming Whisper**: Local speech-to-text (GPU accelerated)
- **Wyoming Piper**: Local text-to-speech
- **Godot 2D Avatar**: Lightweight room avatar

## Godot Avatar System

### 3D Avatar Features:
- Full 3D character with skeletal animation
- Real-time lip sync using Rhubarb/MFA phoneme analysis
- Facial tracking via OpenSeeFace UDP receiver
- Blend shapes and bone-based mouth animation
- Eye tracking and blinking simulation

### 2D Avatar Features:
- Lightweight sprite-based avatar
- Redis-connected for distributed control
- Unique satellite IDs for room identification
- Optimized for Jetson performance

## Communication Architecture

### Redis Pub/Sub Channels
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

## Service Orchestration

### Brain Services (docker-compose.yml)
```yaml
services:
  redis:
    image: redis:7.2-alpine
    ports: ["6379:6379"]

  ollama:
    image: ollama/ollama:0.3.12
    environment:
      - NVIDIA_VISIBLE_DEVICES=0  # RTX 5080
    ports: ["11434:11434"]

  xtts-server:
    image: alekst7/haxtts-service:v1.0
    environment:
      - NVIDIA_VISIBLE_DEVICES=0  # RTX 5080
    ports: ["9898:9898"]

  home-assistant:
    image: ghcr.io/home-assistant/home-assistant:2025.9
    network_mode: host

  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports: ["6333:6333"]

  llm-service:
    build: ./services/llm-service
    depends_on: [redis, ollama, qdrant]

  ha-redis-bridge:
    build: ./services/ha-redis-bridge
    depends_on: [redis, home-assistant]
```

### Jetson Services (docker-compose.yml)
```yaml
services:
  wyoming-openwakeword:
    image: rhasspy/wyoming-openwakeword:1.0.0
    ports: ["10400:10400"]

  wyoming-whisper:
    image: rhasspy/wyoming-whisper:1.0.0
    ports: ["10300:10300"]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  wyoming-piper:
    image: rhasspy/wyoming-piper:1.0.0
    ports: ["10200:10200"]

  avatar-lite:
    build: ./services/godot-avatar-2d
    environment:
      - DISPLAY=${DISPLAY}
      - REDIS_URL=redis://:${REDIS_PASSWORD}@${BRAIN_IP}:6379
      - SATELLITE_ID=${SATELLITE_ID}
    volumes: ["/tmp/.X11-unix:/tmp/.X11-unix"]
```

## Godot Implementation Details

### 3D Avatar Scripts
- **AvatarDriver.gd**: Main avatar controller with lip sync
- **OpenSeeFaceReceiver.gd**: UDP receiver for facial tracking
- **VisemeMap.gd**: ARPABET to viseme conversion

### Lip Sync Pipeline
1. **Audio Input**: Capture voice from satellite
2. **Phoneme Analysis**: Rhubarb/MFA generates viseme timings
3. **Viseme Mapping**: Convert phonemes to mouth shapes
4. **Animation**: Drive blend shapes or bone animations
5. **Facial Tracking**: OpenSeeFace provides head/eye data

### 2D Avatar Implementation
- Lightweight Godot project optimized for Jetson
- Sprite-based animations with lip sync
- Redis connectivity for distributed control
- Unique room identification

## Configuration Files

### Brain Configuration (.env)
```bash
GPU_5080_ID=0
GPU_4090_ID=1
REDIS_PASSWORD=your_password
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_ha_token
```

### Jetson Configuration (.env)
```bash
BRAIN_IP=192.168.1.100
REDIS_PASSWORD=your_password
SATELLITE_ID=living_room
```

## Deployment Architecture

### Hardware Setup
- **Brain Server**: RTX 4090 + RTX 5080, Ubuntu 22.04
- **Jetson Satellites**: Orin Nano, Ubuntu 22.04
- **Network**: Ethernet connectivity between all nodes
- **Displays**: HDMI monitors for avatar rendering

### Software Stack
- **OS**: Ubuntu 22.04 across all nodes
- **Container**: Docker with NVIDIA runtime
- **Game Engine**: Godot 4.x for avatars
- **Communication**: Redis for distributed messaging
- **AI**: Ollama for LLM inference

## Data Flow

### Voice Command Flow
1. **Satellite Detection**: Wake word detected locally
2. **Audio Capture**: Record voice command
3. **Local STT**: Convert speech to text (Wyoming Whisper)
4. **Redis Publish**: Send command to brain
5. **Brain Processing**: LLM generates response
6. **TTS Generation**: Convert response to speech
7. **Avatar Animation**: Trigger lip sync and display
8. **Audio Playback**: Play response through satellite speakers

### Home Assistant Integration
1. **Command Recognition**: Parse HA commands from voice
2. **HA API Call**: Send commands to Home Assistant
3. **Response Processing**: Handle HA responses
4. **Avatar Feedback**: Display status through avatar

## Development Workflow

### Godot Development
```bash
# 3D Avatar Development
cd ~/brain/services/godot-avatar-3d
godot project.godot

# 2D Avatar Development
cd ~/jetson/services/godot-avatar-2d
godot project.godot
```

### Service Development
```bash
# Build custom services
cd ~/brain/services/llm-service
docker build -t avatar-llm-service .

# Deploy updates
cd ~/brain && docker compose up -d --build
```

## Troubleshooting Guide

### Godot Issues
```bash
# Check Godot installation
godot --version

# Run with debug output
godot --verbose project.godot

# Force display output
export DISPLAY=:0
godot --fullscreen project.godot
```

### Redis Connection Issues
```bash
# Test connection
redis-cli -h brain_ip -a password ping

# Check Redis logs
docker logs redis

# Verify network connectivity
telnet brain_ip 6379
```

### GPU Issues
```bash
# Check GPU status
nvidia-smi

# Test container GPU access
docker run --rm --gpus all nvidia/cuda nvidia-smi

# Verify GPU IDs
nvidia-smi -L
```

## Current Status & Roadmap

### ✅ Implemented
- Distributed brain/satellite architecture
- Godot 3D avatar with lip sync
- Godot 2D avatar for satellites
- Redis-based communication
- Home Assistant integration
- Docker service orchestration

### 🔄 In Development
- Complete lip sync pipeline
- Facial tracking integration
- Multi-room coordination
- Advanced avatar animations

### 📋 Next Priorities
1. Deploy and test full distributed system
2. Implement complete lip sync pipeline
3. Add facial tracking to 3D avatar
4. Develop multi-room avatar coordination
5. Create centralized management interface

This architecture provides a scalable, distributed AI avatar system with professional-grade 3D/2D rendering capabilities using Godot 4.x.

## System Architecture

The Avatar Pipeline consists of two main processing pipelines that work together to create an interactive AI avatar system:

### 1. AUDIO PIPELINE
**Purpose**: Voice input processing and response generation
**Flow**: ReSpeaker Mic → STT → LLM → TTS → Audio Output

**Components**:
- **Input**: ReSpeaker 4 Mic Array (hw:2,0)
- **STT Service**: Whisper ASR (Port 9000)
- **LLM Service**: vLLM with Qwen2.5-3B (Port 8000)
- **TTS Service**: Kokoro TTS (Port 5002)
- **Output**: System audio (PulseAudio/ALSA)

### 2. DISPLAY PIPELINE
**Purpose**: Visual avatar rendering and user interface
**Flow**: Text Input → Avatar Animation → HDMI Display

**Components**:
- **Input**: Text from Audio Pipeline or direct commands
- **Rendering**: Pygame/OpenCV for avatar graphics
- **Display**: HDMI output to monitor (Jetson GPU)
- **UI**: Real-time status display and controls

## Bridge Component

The Bridge serves as the communication layer between all system components:

### Features:
- **Redis Pub/Sub**: Message passing between services
- **WebSocket Server**: Real-time communication (Port 8765)
- **API Gateway**: RESTful interface for external systems
- **Service Discovery**: Automatic endpoint detection
- **Load Balancing**: Distribute requests across services

### Communication Channels:
- `avatar_commands`: Commands from main pipeline
- `avatar_responses`: Responses from services
- `avatar_events`: System events and status updates

## Home Assistant Integration

Voice-controlled smart home automation:

### Features:
- **Voice Commands**: Control lights, climate, switches
- **Device Discovery**: Automatic detection of HA entities
- **Status Queries**: Ask about device states
- **Scene Control**: Activate predefined scenes
- **Security**: Token-based authentication

### Supported Commands:
- "Turn on/off the lights"
- "Set temperature to 72 degrees"
- "What's the living room temperature?"
- "Activate goodnight scene"

## Plugin System

Extensible command processing:

### Built-in Plugins:
- **Home Assistant**: Smart home control
- **System Control**: Volume, display, settings
- **Memory**: Conversation history and recall
- **Wake Words**: Hotword detection and management

### Plugin Interface:
```python
def handle_command(pipeline, user_text):
    # Process command
    # Return True if handled, False to continue
    return True

commands = {
    "trigger_word": handle_command
}
```

## Service Orchestration

### Docker Compose Services:
```yaml
services:
  # Audio Pipeline
  whisper-stt:     # STT processing
  vllm-avatars:    # LLM inference
  kokoro-tts:      # Text-to-speech

  # Communication
  viseme-bus:      # Redis message bus
  avatar-bridge:   # Communication bridge

  # Display Pipeline
  avatar-display:  # Visual rendering
```

### Environment Configuration:
- **GPU**: Jetson Orin (single GPU for all services)
- **Audio**: ReSpeaker 4 Mic Array
- **Network**: 192.168.1.31 (Jetson IP)
- **Display**: HDMI output

## Data Flow

### Normal Operation:
1. **Audio Input**: ReSpeaker captures voice
2. **STT Processing**: Converts speech to text
3. **Command Processing**: Check for system commands
4. **LLM Processing**: Generate AI response
5. **TTS Processing**: Convert response to speech
6. **Audio Output**: Play response through speakers
7. **Display Update**: Update avatar visuals

### Home Assistant Integration:
1. **Voice Command**: "Turn on the lights"
2. **Plugin Detection**: Home Assistant plugin triggered
3. **HA API Call**: Send command to Home Assistant
4. **Response**: Confirm action taken
5. **TTS Response**: "Lights have been turned on"

### Bridge Communication:
- **Internal**: Redis pub/sub for service communication
- **External**: WebSocket for client applications
- **API**: REST endpoints for external integrations

## Configuration Files

### Core Configuration:
- `docker-compose.yml`: Service definitions
- `.env`: Environment variables and GPU UUIDs
- `avatar_config.json`: Avatar settings and preferences

### Audio Configuration:
- `.asoundrc`: ALSA audio device settings
- PulseAudio configuration for multi-channel audio

### Plugin Configuration:
- `~/.avatar/plugins/`: Plugin directory
- `~/.avatar/settings.json`: User preferences
- `~/.avatar/memory.json`: Conversation history

## Deployment Architecture

### Hardware Setup:
- **Jetson Orin Nano**: Main processing unit
- **ReSpeaker 4 Mic**: Audio input device
- **HDMI Monitor**: Avatar display output
- **Network**: Ethernet connection for services

### Software Stack:
- **OS**: Ubuntu 22.04 (JetPack)
- **Container**: Docker with NVIDIA runtime
- **Audio**: ALSA/PulseAudio with PyAudio
- **Display**: Pygame with OpenGL acceleration
- **Communication**: Redis for pub/sub, WebSocket for real-time

## Current Status & Next Steps

### ✅ Completed:
- Basic service configuration (STT, LLM, TTS)
- Jetson GPU setup and UUID configuration
- Audio device detection (ReSpeaker)
- Docker compose for service orchestration
- Plugin system foundation

### 🔄 In Progress:
- ALSA audio configuration fixes
- Docker permission resolution
- Real Kokoro TTS model integration

### 📋 Next Steps:
1. **Fix Audio Issues**: Resolve ALSA/PyAudio configuration
2. **Deploy Services**: Get Docker containers running
3. **Test Pipelines**: Verify audio and display pipelines
4. **Bridge Integration**: Implement full bridge component
5. **Home Assistant**: Complete smart home integration
6. **Orchestrator**: Build main pipeline coordinator

## Troubleshooting Guide

### Audio Issues:
- Check ALSA configuration: `cat ~/.asoundrc`
- Test audio devices: `arecord -l && aplay -l`
- Verify ReSpeaker: `arecord -D hw:2,0 -f cd test.wav`

### Docker Issues:
- Permission denied: Use `sudo` or add user to docker group
- GPU access: Check NVIDIA runtime: `docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi`

### Service Issues:
- Check service status: `docker ps`
- View logs: `docker logs <container_name>`
- Test endpoints: `curl http://localhost:9000`

## Development Notes

### Code Organization:
- `main_pipeline.py`: Main orchestrator
- `avatar_bridge.py`: Communication bridge
- `home_assistant_plugin.py`: Smart home integration
- `test_*.py`: Testing and validation scripts

### Key Integration Points:
- Plugin system for extensibility
- Redis for decoupled communication
- WebSocket for real-time features
- REST APIs for service integration

This architecture provides a robust, extensible AI avatar system with clear separation of concerns and multiple integration points for future enhancements.
