#!/usr/bin/env python3
import subprocess
import os

print("Enabling 4090 HDMI output...")

# Set to use GPU 1 (4090)
os.environ['CUDA_VISIBLE_DEVICES'] = '1'

# Try using nvidia-ml-py to enable display
try:
    import pynvml
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(1)  # 4090 is index 1
    print(f"4090 found: {pynvml.nvmlDeviceGetName(handle)}")
    pynvml.nvmlShutdown()
except:
    print("pynvml not available")

# Use xrandr to enable output if X is available
try:
    # Create minimal X config just for 4090
    config = """
Section "Device"
    Identifier "4090"
    Driver "nvidia"
    BusID "PCI:161:0:0"
EndSection
"""
    with open('/tmp/4090.conf', 'w') as f:
        f.write(config)
    
    # Start X on display :3 for the 4090
    print("Starting X server on 4090...")
    subprocess.run(['sudo', 'X', ':3', '-config', '/tmp/4090.conf', '-logfile', '/tmp/X3.log'], timeout=3)
except subprocess.TimeoutExpired:
    print("X server started on :3")
except Exception as e:
    print(f"X start failed: {e}")

print("\nTry: DISPLAY=:3 xterm")
print("Or check /tmp/X3.log for errors")
