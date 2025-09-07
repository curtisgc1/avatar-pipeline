import os, re, glob, importlib.util, traceback
from pathlib import Path

# import your running app
import main_pipeline as app

SKILLS = []  # list of (compiled_regex, handler)

def load_skills():
    global SKILLS
    SKILLS = []
    skills_dir = os.path.expanduser("~/.avatar/skills")
    Path(skills_dir).mkdir(parents=True, exist_ok=True)
    for path in sorted(glob.glob(os.path.join(skills_dir, "*.py"))):
        try:
            mod_name = "_skill_" + os.path.basename(path)[:-3]
            spec = importlib.util.spec_from_file_location(mod_name, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register"):
                for pattern, handler in (mod.register() or []):
                    SKILLS.append((re.compile(pattern, re.I), handler))
        except Exception:
            print("skill load error for", path)
            traceback.print_exc()

def patched_maybe_handle(self, user_text):
    t = (user_text or "").strip()
    # 1) skills first
    for rx, fn in SKILLS:
        m = rx.search(t)
        if m:
            try:
                handled = fn(self, t, m)
                if handled: return True
            except Exception:
                traceback.print_exc()
    # 2) fall back to the app's original handler
    return app.AvatarPipeline._orig_mhvc(self, user_text)

# Monkey-patch
if not hasattr(app.AvatarPipeline, "_orig_mhvc"):
    app.AvatarPipeline._orig_mhvc = app.AvatarPipeline.maybe_handle_voice_command
app.AvatarPipeline.maybe_handle_voice_command = patched_maybe_handle

# Add a built-in management skill so you can say "reload skills"
def _reload_skill(self, t, m):
    load_skills()
    self.current_text = "AI: Skills reloaded."
    if getattr(self, "enable_tts", True):
        wav = self.synthesize_speech("Skills reloaded.")
        if wav: self.play_audio(wav)
    return True

def _list_skills(self, t, m):
    names = [Path(rx.pattern).pattern for rx,_ in SKILLS]
    msg = f"{len(SKILLS)} skills loaded."
    self.current_text = "AI: " + msg
    if getattr(self, "enable_tts", True):
        wav = self.synthesize_speech(msg)
        if wav: self.play_audio(wav)
    return True

def management_register():
    return [
        (r"^reload skills$", _reload_skill),
        (r"^list skills$", _list_skills),
    ]

# Preload skills and management hooks
load_skills()
for pattern, fn in management_register():
    SKILLS.append((re.compile(pattern, re.I), fn))

def run():
    app.AvatarPipeline().run()

if __name__ == "__main__":
    run()
