#!/usr/bin/env python3
import numpy as np
import time
import os

# Use pygame which can work without X
os.environ['SDL_VIDEODRIVER'] = 'fbcon'
os.environ['SDL_FBDEV'] = '/dev/fb0'

import pygame

pygame.init()
screen = pygame.display.set_mode((0,0), pygame.FULLSCREEN)
clock = pygame.time.Clock()

# Simple avatar display
running = True
while running:
    screen.fill((10, 10, 20))
    
    # Draw avatar
    pygame.draw.circle(screen, (100, 100, 100), (960, 540), 200)
    
    # Add text
    font = pygame.font.Font(None, 72)
    text = font.render("Avatar Pipeline Active", True, (0, 255, 0))
    screen.blit(text, (600, 400))
    
    pygame.display.flip()
    clock.tick(30)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
