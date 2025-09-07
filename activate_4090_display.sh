#!/bin/bash
# Direct framebuffer output to 4090 HDMI

echo "Activating 4090 HDMI display..."

# Option 1: Start new X server on the 4090
sudo X :2 -config /etc/X11/xorg.conf vt8 &
sleep 3

# Option 2: Use nvidia-settings to configure
export DISPLAY=:2
nvidia-settings --load-config-only

echo "Display activated on :2"
echo "Test with: DISPLAY=:2 xterm"
