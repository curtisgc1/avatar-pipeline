#!/usr/bin/env python3
import os
import subprocess
import time

# Simple framebuffer test - write directly to screen
print("Testing display on 4090 HDMI...")

# Try to start a separate X server on the 4090
try:
    # Start X on display :1 using the 4090
    cmd = ["sudo", "X", ":1", "-config", "/etc/X11/xorg.conf", "-sharevts"]
    proc = subprocess.Popen(cmd)
    time.sleep(3)
    
    print("X server started on :1")
    print("Set DISPLAY=:1 to use it")
    
    # Now we can display on :1
    os.environ['DISPLAY'] = ':1'
    
    # Simple test with xterm
    subprocess.run(["xterm", "-display", ":1", "-e", "echo 'Avatar Display Test'"])
    
except Exception as e:
    print(f"Error: {e}")
    print("Try running: sudo X :1 -config /etc/X11/xorg.conf")
