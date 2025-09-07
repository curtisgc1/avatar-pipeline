#!/usr/bin/env python3
"""Minimal plugin wrapper for AvatarPipeline - safe version"""
import os
import sys
from pathlib import Path

# Import the working main_pipeline
try:
    import main_pipeline
except ImportError as e:
    print(f"[Runner] Cannot import main_pipeline: {e}")
    sys.exit(1)

# Simple plugin directory setup
PLUGIN_DIR = Path.home() / ".avatar" / "plugins"
PLUGIN_DIR.mkdir(parents=True, exist_ok=True)

class AvatarWithPlugins(main_pipeline.AvatarPipeline):
    """Minimal plugin extension"""
    
    def __init__(self):
        # Initialize parent class
        super().__init__()
        print("[Runner] AvatarWithPlugins initialized (no plugins loaded yet)")
        self._plugins = []
    
    def maybe_handle_voice_command(self, user_text):
        # First try parent's commands
        if super().maybe_handle_voice_command(user_text):
            return True
        
        # Add simple test command
        if user_text and user_text.strip().lower() == "test runner":
            self.current_text = "AI: Runner is working!"
            if self.enable_tts:
                wav = self.synthesize_speech("Runner is working!")
                if wav: self.play_audio(wav)
            return True
        
        return False

if __name__ == "__main__":
    print("[Runner] Starting minimal AvatarWithPlugins...")
    try:
        app = AvatarWithPlugins()
        app.run()
    except Exception as e:
        print(f"[Runner] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
