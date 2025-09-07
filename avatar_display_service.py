#!/usr/bin/env python3
import os
import sys
import time
import subprocess

def setup_display():
    """Setup display on 4090 HDMI without X authorization issues"""
    
    # Option 1: Try starting a new X session on the 4090
    print("Setting up avatar display on 4090 HDMI...")
    
    # Create a simple xinit script
    with open('/tmp/avatar_xinit.sh', 'w') as f:
        f.write('''#!/bin/bash
export DISPLAY=:2
export CUDA_VISIBLE_DEVICES=1
exec python3 /home/curtis/avatar-pipeline/show_avatar.py
''')
    
    os.chmod('/tmp/avatar_xinit.sh', 0o755)
    
    # Start X on display :2 specifically for avatar
    cmd = ['xinit', '/tmp/avatar_xinit.sh', '--', ':2', 'vt7', '-config', '/etc/X11/xorg.conf']
    subprocess.run(cmd)

if __name__ == "__main__":
    setup_display()
