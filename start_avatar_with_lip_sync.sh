#!/bin/bash
# Avatar Pipeline with Lip Sync Startup Script

echo "🎭 Starting Avatar Pipeline with Lip Sync..."

# Function to check if a process is running
check_process() {
    pgrep -f "$1" > /dev/null
}

# Function to start a service
start_service() {
    local name=$1
    local command=$2
    local check=$3

    echo "Starting $name..."
    if check_process "$check"; then
        echo "⚠️  $name is already running"
        return 1
    fi

    # Start in background
    eval "$command" &
    local pid=$!

    # Wait a bit for startup
    sleep 2

    if check_process "$check"; then
        echo "✅ $name started successfully (PID: $pid)"
        return 0
    else
        echo "❌ Failed to start $name"
        return 1
    fi
}

# Start Lip Sync Engine
start_service "Lip Sync Engine" "python3 lip_sync_engine.py" "lip_sync_engine"

# Start Avatar Display
start_service "Avatar Display" "python3 -c 'from lip_sync_engine import LipSyncAvatarDisplay; display = LipSyncAvatarDisplay(); display.run()'" "python3.*LipSyncAvatarDisplay"

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 3

# Start Main Pipeline
echo "🚀 Starting Main Pipeline..."
python3 main_pipeline.py

echo "🛑 Shutting down all services..."
# Kill any remaining processes
pkill -f "lip_sync_engine" 2>/dev/null || true
pkill -f "LipSyncAvatarDisplay" 2>/dev/null || true

echo "✅ All services stopped"</content>
<parameter name="filePath">/home/curtis/avatar-pipeline/start_avatar_with_lip_sync.sh
