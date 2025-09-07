#!/usr/bin/env python3
import os
import subprocess

# Set GPU for display
os.environ['CUDA_VISIBLE_DEVICES'] = '1'  # 4090 is GPU 1

print("Starting avatar display on 4090 HDMI...")

# Use NVIDIA settings to force output
subprocess.run(['nvidia-settings', '--assign', 'CurrentMetaMode=nvidia-auto-select'])

# Simple display test using framebuffer
try:
    # Create a window directly with SDL (simpler than X)
    import pygame
    pygame.init()
    
    # Try fullscreen on primary display
    screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
    pygame.display.set_caption("Avatar Display - RTX 4090")
    
    # Dark background with text
    screen.fill((20, 20, 30))
    font = pygame.font.Font(None, 72)
    text = font.render("Avatar Display Test", True, (0, 255, 0))
    screen.blit(text, (600, 500))
    pygame.display.flip()
    
    # Keep displaying for 10 seconds
    pygame.time.wait(10000)
    pygame.quit()
    print("Display test complete!")
    
except Exception as e:
    print(f"Pygame not available: {e}")
    print("Install with: pip install pygame")
