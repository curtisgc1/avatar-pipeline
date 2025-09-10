#!/bin/bash
# Test Jetson connection and setup avatar auto-start

echo "Testing Jetson connection..."
if ssh -i ~/.ssh/jetson_key -o ConnectTimeout=10 -o StrictHostKeyChecking=no curtis@192.168.1.31 "echo 'Connection successful!'" 2>/dev/null; then
    echo "✅ Jetson is online!"
    echo "Setting up auto-start service..."

    # Copy files to Jetson
    scp -i ~/.ssh/jetson_key /home/curtis/avatar-pipeline/avatar-pipeline.service curtis@192.168.1.31:~/
    scp -i ~/.ssh/jetson_key /home/curtis/avatar-pipeline/setup_auto_start.sh curtis@192.168.1.31:~/

    # Run setup on Jetson
    ssh -i ~/.ssh/jetson_key curtis@192.168.1.31 "chmod +x ~/setup_auto_start.sh && ~/setup_auto_start.sh"

    echo ""
    echo "🎉 Avatar Pipeline is now set to start automatically!"
    echo "The avatar will be live whenever the Jetson is connected."
else
    echo "❌ Jetson is still offline or booting..."
    echo "Run this script again when the Jetson is ready:"
    echo "  ./test_connection.sh"
fi
