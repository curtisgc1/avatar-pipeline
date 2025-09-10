#!/bin/bash
# Avatar Pipeline Auto-Start Setup Script
# This script sets up the avatar pipeline to start automatically on boot

echo "Setting up Avatar Pipeline auto-start service..."

# Copy service file to systemd
sudo cp /home/curtis/avatar-pipeline/avatar-pipeline.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable avatar-pipeline.service

# Start the service now
sudo systemctl start avatar-pipeline.service

# Check status
echo "Service status:"
sudo systemctl status avatar-pipeline.service --no-pager -l

echo ""
echo "Avatar Pipeline is now set to start automatically on boot!"
echo "To check status: sudo systemctl status avatar-pipeline.service"
echo "To restart: sudo systemctl restart avatar-pipeline.service"
echo "To stop: sudo systemctl stop avatar-pipeline.service"
echo "To view logs: journalctl -u avatar-pipeline.service -f"
