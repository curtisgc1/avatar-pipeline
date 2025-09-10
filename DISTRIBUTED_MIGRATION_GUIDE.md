# Distributed Godot Avatar System - Migration Guide
# September 9, 2025

## Overview
This guide explains how to migrate from the current single-node avatar-pipeline setup to the distributed Godot-based architecture.

## Current vs Target Architecture

### CURRENT: Single-Node (avatar-pipeline/)
```
~/avatar-pipeline/
├── main_pipeline.py (Python/Pygame)
├── kokoro/ (placeholder TTS)
├── docker-compose.yml (Jetson services)
└── Various test scripts
```

### TARGET: Distributed Godot (brain/ + jetson/)
```
~/brain/ (RTX 4090 + RTX 5080)
├── services/godot-avatar-3d/ (Godot 3D project)
├── services/llm-service/ (AI processing)
├── services/ha-redis-bridge/ (HA integration)
├── compose.yml (Docker orchestration)
└── .env (configuration)

~/jetson/ (Orin Nano satellites)
├── services/godot-avatar-2d/ (Godot 2D project)
├── compose.yml (Docker orchestration)
└── .env (configuration)
```

## Migration Steps

### Phase 1: Brain Server Setup
```bash
# 1. Create brain directory structure
mkdir -p ~/brain/services/godot-avatar-3d
mkdir -p ~/brain/services/llm-service
mkdir -p ~/brain/services/ha-redis-bridge
mkdir -p ~/brain/ha_config
mkdir -p ~/brain/ollama_models
mkdir -p ~/brain/qdrant_storage

# 2. Copy brain configuration
cp ~/avatar-pipeline/docker-compose.yml ~/brain/compose.yml
# Edit compose.yml for brain services

# 3. Configure brain environment
cat > ~/brain/.env << EOF
GPU_5080_ID=0
GPU_4090_ID=1
REDIS_PASSWORD=your_secure_password
HA_URL=http://192.168.1.100:8123
HA_TOKEN=your_ha_token
EOF

# 4. Initialize Godot 3D project
cd ~/brain/services/godot-avatar-3d
godot --init
# Copy avatar assets and scripts
```

### Phase 2: Jetson Satellite Setup
```bash
# 1. Create jetson directory structure
mkdir -p ~/jetson/services/godot-avatar-2d

# 2. Copy jetson configuration
# Create compose.yml for jetson services

# 3. Configure jetson environment
cat > ~/jetson/.env << EOF
BRAIN_IP=192.168.1.100
REDIS_PASSWORD=your_secure_password
SATELLITE_ID=living_room
EOF

# 4. Initialize Godot 2D project
cd ~/jetson/services/godot-avatar-2d
godot --init
# Copy lightweight avatar assets
```

### Phase 3: Service Migration

#### Migrate Audio Processing
- **FROM**: Python/PyAudio + Whisper
- **TO**: Wyoming Whisper (GPU accelerated on Jetson)

#### Migrate AI Processing
- **FROM**: vLLM on Jetson
- **TO**: Ollama on RTX 5080 (better performance)

#### Migrate TTS
- **FROM**: Kokoro placeholder
- **TO**: XTTS on RTX 5080 (high quality)

#### Migrate Display
- **FROM**: Pygame rendering
- **TO**: Godot 3D/2D rendering with lip sync

### Phase 4: Godot Avatar Development

#### 3D Avatar Setup
```bash
cd ~/brain/services/godot-avatar-3d

# Create main scene
# Add avatar character with skeleton
# Implement AvatarDriver.gd script
# Add OpenSeeFace UDP receiver
# Set up viseme mapping
```

#### 2D Avatar Setup
```bash
cd ~/jetson/services/godot-avatar-2d

# Create lightweight scene
# Add sprite-based avatar
# Implement Redis connectivity
# Add lip sync animations
```

### Phase 5: Communication Setup

#### Redis Configuration
```bash
# Install Redis on brain server
sudo apt install redis-server

# Configure Redis with password
sudo nano /etc/redis/redis.conf
# Add: requirepass your_password

# Test connectivity from jetson
redis-cli -h brain_ip -a password ping
```

#### Message Channels
- `avatar:commands`: Satellite → Brain voice commands
- `avatar:responses`: Brain → Satellite AI responses
- `avatar:events`: System status updates
- `satellite:{id}:status`: Individual satellite status

### Phase 6: Testing & Validation

#### Test Checklist
```bash
# Brain services
cd ~/brain && docker compose ps
cd ~/brain/services/godot-avatar-3d && godot --version

# Jetson services
cd ~/jetson && docker compose ps
cd ~/jetson/services/godot-avatar-2d && godot --version

# Communication
redis-cli -h brain_ip -a password ping

# Godot avatars
# Test 3D avatar launch
# Test 2D avatar launch
# Test lip sync pipeline
```

## Key Differences

### Architecture Changes
1. **Distributed**: Brain + multiple satellites vs single node
2. **Rendering**: Godot 3D/2D vs Pygame
3. **AI**: Ollama vs vLLM
4. **TTS**: XTTS vs Kokoro placeholder
5. **Communication**: Redis pub/sub vs direct function calls

### Performance Improvements
1. **GPU Utilization**: Dedicated GPUs for specific tasks
2. **Scalability**: Multiple rooms with independent processing
3. **Rendering**: Hardware-accelerated Godot vs software Pygame
4. **AI**: Optimized Ollama vs general vLLM

### Development Changes
1. **Languages**: GDScript (Godot) + Python vs pure Python
2. **Tools**: Godot editor vs text editors
3. **Deployment**: Docker Compose orchestration vs single scripts
4. **Debugging**: Godot debugger + distributed logs

## Rollback Plan

If migration fails, rollback to original system:
```bash
# Stop distributed services
cd ~/brain && docker compose down
cd ~/jetson && docker compose down

# Restore original avatar-pipeline
cd ~/avatar-pipeline
python3 main_pipeline.py
```

## Success Criteria

### Functional Requirements
- ✅ 3D avatar displays on brain server
- ✅ 2D avatar displays on jetson satellite
- ✅ Voice commands processed from satellite to brain
- ✅ AI responses generated and sent back
- ✅ Lip sync working on both avatars
- ✅ Home Assistant integration functional

### Performance Requirements
- ✅ <500ms latency for voice command processing
- ✅ 60fps avatar animation
- ✅ <100ms Redis communication latency
- ✅ Stable distributed operation

## Support Resources

### Godot Learning
- Official Godot documentation
- Godot avatar tutorials
- GDScript reference

### Distributed Systems
- Redis documentation
- Docker Compose guides
- Network troubleshooting

### Audio/Video
- Rhubarb lip sync documentation
- OpenSeeFace setup guides
- Wyoming protocol documentation

This migration transforms the system from a basic Python prototype to a professional distributed Godot-based avatar platform.
