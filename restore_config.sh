#!/bin/bash
# Avatar Pipeline Restore Script
# Run this to restore your avatar pipeline configuration

echo "🔄 Restoring Avatar Pipeline Configuration..."
echo "==============================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the avatar-pipeline directory"
    echo "   cd /home/curtis/avatar-pipeline"
    exit 1
fi

echo "📍 Current location: $(pwd)"

# Restore VS Code workspace
echo "🔧 Restoring VS Code workspace..."
code --add /home/curtis/avatar-pipeline

# Check Docker services
echo "🐳 Checking Docker services..."
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker available"
    echo "🚀 To start services: docker-compose up -d"
else
    echo "⚠️  Docker not available - install Docker first"
fi

# Check GPU configuration
echo "🎮 Checking GPU configuration..."
if [ -f ".env" ]; then
    echo "✅ Environment file found"
    echo "   GPU UUIDs configured for RTX 5080 and 4090"
else
    echo "❌ .env file missing"
fi

# Check key files
echo "📁 Checking key files..."
files=("main_pipeline.py" "avatar_interactive.py" "kokoro/server.py" "test_pipeline.py")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file found"
    else
        echo "❌ $file missing"
    fi
done

echo ""
echo "🎯 Quick start commands:"
echo "   docker-compose up -d          # Start services"
echo "   python3 test_pipeline.py      # Test setup"
echo "   python3 avatar_interactive.py # Run interactive avatar"
echo ""
echo "📖 See AVATAR_CONFIG_SUMMARY.md for full configuration details"
echo ""
echo "✅ Restore complete!"
