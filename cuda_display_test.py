#!/usr/bin/env python3
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '1'  # Use 4090

print("Testing 4090 display output via CUDA...")

# Simple test to activate the display
import subprocess
result = subprocess.run(['nvidia-smi', '-i', '1', '-q'], capture_output=True, text=True)
if 'RTX 4090' in result.stdout:
    print("4090 is active")
    
    # Try to force display on
    subprocess.run(['sudo', 'nvidia-smi', '-i', '1', '-pm', '1'])
    print("Persistence mode enabled")
    
    # The display should now be active
    print("Check your HDMI monitor - it should show signal")

print("\nIf no display, the 4090 needs its output explicitly enabled")
print("This usually requires either X or Wayland")
