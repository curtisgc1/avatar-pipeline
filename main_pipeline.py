#!/usr/bin/env python3
import os, time, math, wave, re, warnings, subprocess, shutil, json, struct, threading
from pathlib import Path
import pygame, pyaudio, requests

# Plugin system
import importlib.util
from pathlib import Path

def load_plugins():
    """Load voice command plugins from ~/.avatar/plugins/"""
    plugins = {}
    plugin_dir = Path.home() / ".avatar" / "plugins"
    plugin_dir.mkdir(parents=True, exist_ok=True)
    
    for plugin_file in plugin_dir.glob("*.py"):
        try:
            spec = importlib.util.spec_from_file_location(f"plugin_{plugin_file.stem}", plugin_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'commands'):
                plugins.update(module.commands)
                print(f"Loaded plugin: {plugin_file.stem}")
        except Exception as e:
            print(f"Plugin load error {plugin_file}: {e}")
    return plugins


warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

def rms_level(buf):
    if not buf: return 0.0
    n = len(buf)//2
    if n<=0: return 0.0
    shorts = struct.unpack("<"+"h"*n, buf)
    mean_sq = sum(s*s for s in shorts)/float(n)
    return (mean_sq**0.5)/32768.0

class AvatarPipeline:
    def __init__(self):
        # ----- Services -----
        self.stt_url   = os.getenv("STT_URL", "http://localhost:9000")
        self.stt_path  = os.getenv("STT_ASR_PATH", "/asr")
        self.llm_url   = os.getenv("LLM_URL", "http://localhost:11434").rstrip("/") + "/api/generate"
        self.llm_model = os.getenv("LLM_MODEL", "dolphin-llama3:latest")

        # ----- Settings / Memory -----
        self.settings_path = os.path.expanduser("~/.avatar/settings.json")
        self.mem_path      = os.path.expanduser("~/.avatar/memory.json")
        self.settings = {
            "voice_engine": "kokoro", "kokoro_voice": "af_bella", "piper_voice": "amy",
            "volume": 80, "tts_speed": 1.0,
            "wake_mode": "hotword",           # current runtime mode
            "boot_wake_mode": "always",       # << default at reboot (always = no wake word)
            "wake_word": "computer",
            "hotword_engine": "porcupine",
            "hotword_sensitivity": 0.75, "hotword_window_s": 10,
            "chime_on_wake": False
        }
        self._load_settings()
        # Apply the boot default every start
        self.settings["wake_mode"] = self.settings.get("boot_wake_mode","always")
        self.memory = self._mem_load()
        self.awaiting_clear_confirm = False

        # ----- TTS backends -----
        self.kokoro_url   = os.getenv("KOKORO_URL", "http://localhost:8880/v1")
        self.user_voices_dir = os.path.expanduser("~/.local/share/piper/voices/en_US")
        self.voice_map = {
            "amy":      os.path.join(self.user_voices_dir, "en_US-amy-medium.onnx"),
            "ljspeech": os.path.join(self.user_voices_dir, "en_US-ljspeech-medium.onnx"),
            "kathleen": os.path.join(self.user_voices_dir, "en_US-kathleen-low.onnx"),
        }
        self.espeak_voice = os.getenv("ESPEAK_VOICE", "en+f3")
        self.enable_tts = os.getenv("ENABLE_TTS","1") == "1"

        # ----- Audio I/O -----
        self.audio = pyaudio.PyAudio()
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024
        self.input_device_index = None
        try:
            for i in range(self.audio.get_device_count()):
                info = self.audio.get_device_info_by_index(i)
                if "respeaker" in (info.get("name") or "").lower() and info.get("maxInputChannels",0)>0:
                    self.input_device_index = i
                    print("🎙️ Using ReSpeaker input:", info.get("name")); break
        except Exception as e: print("⚠️ Mic scan error:", e)
        # Load voice command plugins
        self.plugins = load_plugins()

        # Playback (prefer Pulse first)
        self.aplay_candidates = [os.getenv("APLAY_DEVICE")] if os.getenv("APLAY_DEVICE") else []
        self.aplay_candidates += ["pulse", "default"]
        self._play_proc = None  # for 'stop speaking'

        # ----- VAD -----
        self.start_thresh     = float(os.getenv("VAD_START", "0.012"))
        self.stop_thresh      = float(os.getenv("VAD_STOP",  "0.009"))
        self.min_ms           = int(os.getenv("VAD_MIN_MS", "300"))
        self.max_ms           = int(os.getenv("VAD_MAX_MS", "8000"))
        self.silence_hang_ms  = int(os.getenv("VAD_HANG_MS","1000"))

        # ----- UI -----
        self.screen_width, self.screen_height = 1280, 720
        self.current_text = "Starting…"
        self.is_listening = False
        self.is_speaking  = False

        pygame.init(); pygame.font.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height), pygame.FULLSCREEN)
        pygame.display.set_caption("AI Avatar")
        self.font = pygame.font.SysFont(None, 32)
        self.avatar_image = None
        try:
            self.avatar_image = pygame.image.load("avatar.png")
            self.avatar_image = pygame.transform.scale(self.avatar_image,(self.screen_width,self.screen_height))
        except Exception: pass

        # Apply persisted volume/speed
        self._apply_volume(self.settings.get("volume", 80))
        self.tts_speed = float(self.settings.get("tts_speed", 1.0))

        # ----- Porcupine hotword (model-based) -----
        self.hw = None; self.hw_stream = None; self.hw_thread = None
        self.last_wake_ts = 0.0

        # Sleep mode: when True, only Porcupine listens; VAD/STT paused
        self.sleeping = (self.settings["wake_mode"] == "hotword" and self.settings.get("hotword_engine")=="porcupine" and False)
        # above starts False; we’ll flip when user says "sleep now"
        self.exit_requested = False

        self._init_hotword_engine()    # attempt init; harmless if not available

    # ===== settings & memory =====
    def _load_settings(self):
        try:
            p=Path(self.settings_path)
            if p.exists(): self.settings.update(json.loads(p.read_text()))
            else:
                p.parent.mkdir(parents=True, exist_ok=True); p.write_text(json.dumps(self.settings, indent=2))
        except Exception as e: print("⚠️ Settings load error:", e)
    def _save_settings(self):
        try:
            p=Path(self.settings_path); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self.settings, indent=2))
        except Exception as e: print("⚠️ Settings save error:", e)
    def _mem_load(self):
        try:
            p=Path(self.mem_path)
            if p.exists(): return json.loads(p.read_text())
        except Exception as e: print("⚠️ Memory load error:", e)
        return []
    def _mem_save(self):
        try:
            p=Path(self.mem_path); p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(self.memory, indent=2))
        except Exception as e: print("⚠️ Memory save error:", e)

    # ===== volume/speed =====
    def _apply_volume(self, percent):
        try:
            pct=max(0,min(int(percent),150))
            if shutil.which("wpctl"): subprocess.run(["wpctl","set-volume","@DEFAULT_SINK@", f"{pct/100.0:.2f}"], check=False)
            elif shutil.which("pactl"): subprocess.run(["pactl","set-sink-volume","@DEFAULT_SINK@", f"{pct}%"], check=False)
        except Exception as e: print("🔉 volume set failed:", e)
    def _volume_command(self, text):
        t=text.lower()
        m=re.search(r"(volume|vol)\s*(up|down|set)?\s*([0-9]{1,3})?", t)
        if not m and ("mute" not in t and "unmute" not in t): return False
        if "mute" in t:
            if shutil.which("wpctl"): subprocess.run(["wpctl","set-mute","@DEFAULT_SINK@", "1"], check=False)
            elif shutil.which("pactl"): subprocess.run(["pactl","set-sink-mute","@DEFAULT_SINK@","1"], check=False)
            self.current_text="AI: Muted."; return True
        if "unmute" in t:
            if shutil.which("wpctl"): subprocess.run(["wpctl","set-mute","@DEFAULT_SINK@", "0"], check=False)
            elif shutil.which("pactl"): subprocess.run(["pactl","set-sink-mute","@DEFAULT_SINK@","0"], check=False)
            self.current_text="AI: Unmuted."; return True
        direction=m.group(2) or "set"; amt=m.group(3); cur=self.settings.get("volume",80)
        if direction=="up" and amt: newv=cur+int(amt)
        elif direction=="down" and amt: newv=cur-int(amt)
        elif direction=="set" and amt: newv=int(amt)
        else: return False
        newv=max(0,min(newv,150)); self.settings["volume"]=newv; self._save_settings(); self._apply_volume(newv)
        self.current_text=f"AI: Volume {newv}%."; return True
    def _speed_command(self, text):
        t=text.lower()
        if "speed up" in t or "faster" in t: self.tts_speed=min(self.tts_speed+0.1,1.5)
        elif "speed down" in t or "slower" in t: self.tts_speed=max(self.tts_speed-0.1,0.5)
        else:
            m=re.search(r"\b(speed|rate)\s*([0-9.]+)\b", t)
            if not m: return False
            self.tts_speed=max(0.5,min(float(m.group(2)),1.5))
        self.settings["tts_speed"]=self.tts_speed; self._save_settings()
        self.current_text=f"AI: Speed {self.tts_speed:.2f}."; return True

    # ===== hotword mic suspend/resume to avoid double-open =====
    def _suspend_hotword(self):
        try:
            if self.hw_stream:
                self.hw_stream.stop_stream(); self.hw_stream.close(); self.hw_stream=None
            if self.hw_thread and self.hw_thread.is_alive():
                tmp=self.hw; self.hw=None
                self.hw_thread.join(timeout=1.0)
                self.hw=tmp; self.hw_thread=None
        except Exception as e: print("ℹ️ suspend hotword:", e)
    def _resume_hotword(self):
        try:
            if self.settings.get("hotword_engine","stt")!="porcupine" or self.hw is None: return
            import pvporcupine
            self.hw_stream = self.audio.open(format=self.audio_format, channels=1,
                                             rate=self.hw.sample_rate, input=True,
                                             input_device_index=self.input_device_index,
                                             frames_per_buffer=self.hw.frame_length)
            self.hw_thread = threading.Thread(target=self._hotword_loop, daemon=True)
            self.hw_thread.start()
        except Exception as e: print("ℹ️ resume hotword failed:", e)

    # ===== Porcupine init/loop =====
    def _init_hotword_engine(self):
        try:
            import pvporcupine
        except Exception:
            print("ℹ️ Porcupine not installed; using STT wake word only."); return
        if self.settings.get("hotword_engine","stt")!="porcupine":
            print("ℹ️ Hotword engine set to STT."); return
        access_key=os.getenv("PV_ACCESS_KEY") or self.settings.get("pv_access_key","")
        if not access_key: print("ℹ️ PV_ACCESS_KEY not set; using STT wake word."); return
        name=self.settings.get("wake_word","porcupine").lower()
        builtin={"computer":"computer","jarvis":"jarvis","porcupine":"porcupine",
                 "bumblebee":"bumblebee","alexa":"alexa","hey google":"hey google","ok google":"ok google"}.get(name,"porcupine")
        try:
            import pvporcupine
            sens=float(self.settings.get("hotword_sensitivity",0.60))
            self.hw = pvporcupine.create(access_key=access_key, keywords=[builtin], sensitivities=[sens])
            self._resume_hotword()
            print(f"✅ Porcupine hotword active for '{builtin}' @ {sens:.2f}")
        except Exception as e:
            print("ℹ️ Porcupine init failed; falling back to STT gate:", e); self.hw=None
    def _hotword_loop(self):
        try:
            while self.hw is not None and self.hw_stream is not None:
                pcm = self.hw_stream.read(self.hw.frame_length, exception_on_overflow=False)
                pcm = struct.unpack_from("h"*self.hw.frame_length, pcm)
                r = self.hw.process(pcm)
                if r >= 0:
                    self.last_wake_ts = time.time()
                    if self.settings.get("chime_on_wake", False): self._play_chime()
                    self.sleeping = False
                    self.current_text = "AI: Wake word detected."
        except Exception: pass
        finally:
            try:
                if self.hw_stream: self.hw_stream.stop_stream(); self.hw_stream.close()
            except: pass
            self.hw_stream=None

    # ===== UI =====
    def render_avatar(self):
        self.screen.fill((20,20,30))
        status = "😴 Sleeping" if self.sleeping else ("🎤 Listening…" if self.is_listening else ("🗣️ Speaking…" if self.is_speaking else "Idle"))
        self.screen.blit(self.font.render(status, True, (255,255,255)), (10,10))
        if self.avatar_image: self.screen.blit(self.avatar_image,(0,0))
        if self.current_text:
            words=self.current_text.split(); lines=[]; cur=""
            for w in words:
                if len(cur+w)<40: cur+=w+" "
                else: lines.append(cur.strip()); cur=w+" "
            if cur: lines.append(cur.strip())
            for i,l in enumerate(lines[-3:]): self.screen.blit(self.font.render(l,True,(255,255,255)),(10,50+i*36))
        pygame.display.flip()

    # ===== Record with VAD (suspends hotword) =====
    def record_until_silence(self):
        self._suspend_hotword()
        try:
            stream = self.audio.open(format=self.audio_format, channels=1, rate=self.rate,
                                     input=True, input_device_index=self.input_device_index,
                                     frames_per_buffer=self.chunk)
        except Exception as e:
            print("❌ Mic open error:", e); self._resume_hotword(); return None
        frames=[]; heard=False; started_at=None; last_voice_ms=0; t0=time.time()
        try:
            while True:
                data = stream.read(self.chunk, exception_on_overflow=False)
                level=rms_level(data); now_ms=int((time.time()-t0)*1000)
                self.is_listening=True
                if now_ms%200<50: self.render_avatar()
                if not heard and level>=self.start_thresh:
                    heard=True; started_at=now_ms; last_voice_ms=now_ms; frames.append(data)
                elif heard:
                    frames.append(data)
                    if level>=self.stop_thresh: last_voice_ms=now_ms
                    if (now_ms-last_voice_ms)>self.silence_hang_ms or (now_ms-started_at)>self.max_ms: break
                if not heard and now_ms>15000: 
                    stream.stop_stream(); stream.close(); self.is_listening=False; self._resume_hotword(); return None
            stream.stop_stream(); stream.close(); self.is_listening=False
            if not frames: self._resume_hotword(); return None
            dur_ms=(len(frames)*self.chunk*1000)//self.rate
            if dur_ms<self.min_ms: self._resume_hotword(); return None
            fname="recording.wav"
            with wave.open(fname,'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate); wf.writeframes(b"".join(frames))
            return fname
        except Exception as e:
            print("❌ Recording error:", e); 
            try: stream.stop_stream(); stream.close()
            except: pass
            self.is_listening=False
            return None
        finally:
            self._resume_hotword()

    # ===== playback =====
    def _stop_playback(self):
        if self._play_proc and self._play_proc.poll() is None:
            try: self._play_proc.terminate()
            except Exception: pass
        self._play_proc=None
    def play_audio(self, f):
        if not f or not Path(f).exists(): return
        self._stop_playback()
        last_err=None
        for dev in self.aplay_candidates:
            try:
                cmd=["aplay","-q"]; 
                if dev: cmd+=["-D",dev]
                cmd.append(f)
                self._play_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception as e:
                last_err=e; continue
        print("❌ Playback failed:", last_err)

    # ===== STT =====
    def transcribe_audio(self, f):
        url=self.stt_url.rstrip("/")+self.stt_path
        try:
            with open(f,'rb') as fd:
                r=requests.post(url, files={"audio_file":("rec.wav",fd,"audio/wav")}, timeout=60)
            if r.status_code in (400,404,415,422):
                for key in ("file","audio","audio_data"):
                    with open(f,'rb') as fd:
                        r=requests.post(url, files={key:("rec.wav",fd,"audio/wav")}, timeout=60)
                    if r.status_code==200: break
            if r.status_code!=200: return ""
            ctype=(r.headers.get("Content-Type") or "").lower()
            text = (r.json().get("text") if "application/json" in ctype else r.text).strip()
            if len(text)<2 or re.fullmatch(r"[Uu]h+|[Mm]m+|[Yy]ou", text): return ""
            return text
        except Exception as e: print("❌ STT Exception:", e); return ""

    # ===== voices / wake / memory / system =====
    def _kokoro_voices(self):
        try:
            j=requests.get(self.kokoro_url.rstrip("/")+"/audio/voices", timeout=5).json()
            voices = j.get("voices") or j
            names=[]
            for v in voices:
                if isinstance(v, dict) and "name" in v: names.append(v["name"])
                elif isinstance(v, str): names.append(v)
            return sorted(set(names))
        except Exception:
            return ["af_bella","af_sky","af_heart"]

    def maybe_handle_voice_command(self, user_text):
        if user_text: print(f"[VOICE] Heard: {user_text}")
        t=user_text.lower().strip()

        # stop speaking
        if re.search(r"\b(stop speaking|silence|be quiet|cancel speech)\b", t):
            self._stop_playback(); self.current_text="AI: Stopped."; return True

        # EXIT app completely (requires relaunch later)
        if re.search(r"\b(exit|quit|stop app|shutdown avatar)\b", t):
            self.exit_requested = True
            self.current_text = "AI: Exiting."
            return True

        # sleep/wake cycle (keeps hotword only)
        if re.search(r"\b(sleep now|go to sleep|sleep|goodnight|good night)\b", t):
            self.sleeping = True
            print("[SLEEP MODE] Entering sleep - only porcupine wake word will work")
            if self.enable_tts:
                wav = self.synthesize_speech("Going to sleep. Say porcupine to wake me.")
                if wav: self.play_audio(wav)
            self.settings["wake_mode"] = "hotword"
            self._save_settings()
            self.current_text = "AI: Sleeping. Say the wake word."
            return True
        if re.search(r"\b(wake up|i'm back|i am back)\b", t):
            self.sleeping = False
            self.current_text = "AI: I'm here."
            return True

        # defaults for next reboot
        if re.search(r"\bwake always by default\b", t):
            self.settings["boot_wake_mode"]="always"; self._save_settings()
            self.current_text="AI: Will start with no wake word."; return True
        if re.search(r"\bwake hotword by default\b", t):
            self.settings["boot_wake_mode"]="hotword"; self._save_settings()
            self.current_text="AI: Will start with wake word."; return True

        # volume / speed
        if self._volume_command(t) or self._speed_command(t): return True

        # wake engine & options
        if "use porcupine" in t:
            self.settings["hotword_engine"]="porcupine"; self._save_settings(); self._init_hotword_engine()
            self.current_text="AI: Using Porcupine."; return True
        if "use stt wake word" in t:
            self.settings["hotword_engine"]="stt"; self._save_settings(); self.hw=None
            self.current_text="AI: Using STT wake word."; return True
        m=re.search(r"\bset wake word\s+([a-z0-9 ]+)\b", t)
        if m:
            self.settings["wake_word"]=m.group(1).strip(); self._save_settings(); self._init_hotword_engine()
            self.current_text=f"AI: Wake word set to {m.group(1)}."; return True
        m=re.search(r"\bhotword sensitivity\s*([0-9.]+)\b", t)
        if m:
            s=max(0.0,min(float(m.group(1)),1.0)); self.settings["hotword_sensitivity"]=s; self._save_settings(); self._init_hotword_engine()
            self.current_text=f"AI: Sensitivity {s:.2f}."; return True

        # voices
        if "list voices" in t:
            kok=", ".join(self._kokoro_voices()[:30]); pip=", ".join(self.voice_map.keys())
            msg=f"Kokoro: {kok}. Piper: {pip}."
            self.current_text="AI: "+msg
            if self.enable_tts:
                f=self.synthesize_speech(msg); 
                if f: self.play_audio(f)
            return True
        if re.search(r"\bdefault voice\s+(bella|sky|heart)\b", t):
            v=re.search(r"\b(bella|sky|heart)\b", t).group(1)
            self.settings["voice_engine"]="kokoro"; self.settings["kokoro_voice"]=f"af_{v}"
            self._save_settings(); self.current_text=f"AI: Default voice {v}."; return True
        if re.search(r"\bdefault voice\s+(amy|kathleen|ljspeech)\b", t):
            v=re.search(r"\b(amy|kathleen|ljspeech)\b", t).group(1)
            if Path(self.voice_map[v]).exists():
                self.settings["voice_engine"]="piper"; self.settings["piper_voice"]=v
                self._save_settings(); self.current_text=f"AI: Default voice {v} (Piper)."; return True
        if "voice " in t:
            m=re.search(r"\b(bella|sky|heart)\b", t)
            if m:
                self.settings["voice_engine"]="kokoro"; self.settings["kokoro_voice"]=f"af_{m.group(1)}"
                self._save_settings(); self.current_text=f"AI: Switched to {m.group(1)}."
                if self.enable_tts:
                    f=self.synthesize_speech(self.current_text[4:]); 
                    if f: self.play_audio(f)
                return True
            m=re.search(r"\b(amy|kathleen|ljspeech)\b", t)
            if m and Path(self.voice_map[m.group(1)]).exists():
                self.settings["voice_engine"]="piper"; self.settings["piper_voice"]=m.group(1)
                self._save_settings(); self.current_text=f"AI: Switched to {m.group(1)} (Piper)."
                if self.enable_tts:
                    f=self.synthesize_speech(self.current_text[4:]); 
                    if f: self.play_audio(f)
                return True

        # memory
        m=re.search(r"\bremember that\s+(.+)", t)
        if m: self.memory.append({"ts":time.time(),"text":m.group(1).strip(),"tags":[]}); self._mem_save(); self.current_text="AI: Noted."; return True
        m=re.search(r"\bremember my\s+(.+?)\s+is\s+(.+)", t)
        if m: self.memory.append({"ts":time.time(),"text":f"my {m.group(1)} is {m.group(2)}","tags":[]}); self._mem_save(); self.current_text="AI: Remembered."; return True
        m=re.search(r"\bwhat do you remember about\s+(.+)", t)
        if m:
            q=m.group(1); hits=[e["text"] for e in self.memory if q.lower() in e.get("text","").lower()][:5]
            msg="; ".join(hits) if hits else "Nothing yet."
            self.current_text="AI: "+msg; 
            if self.enable_tts:
                f=self.synthesize_speech(msg); 
                if f: self.play_audio(f)
            return True
        if re.fullmatch(r"(what do you remember|what do you remember\?)", t):
            hits=[e["text"] for e in self.memory][-5:]; msg="; ".join(hits) if hits else "Nothing yet."
            self.current_text="AI: "+msg; 
            if self.enable_tts:
                f=self.synthesize_speech(msg); 
                if f: self.play_audio(f)
            return True
        m=re.search(r"\bforget\s+(.+)", t)
        if m and "forget memory" != "forget "+m.group(1):
            q=m.group(1).lower(); before=len(self.memory)
            self.memory=[e for e in self.memory if q not in e.get("text","").lower()]
            self._mem_save(); self.current_text=f"AI: Removed {before-len(self.memory)} item(s)."; return True

        if "clear memory" in t:
            self.memory=[]; self._mem_save(); self.current_text="AI: Memory cleared."; return True

        # Check plugins
        for trigger, handler in self.plugins.items():
            if trigger in t:
                try:
                    return handler(self, user_text)
                except Exception as e:
                    print(f"Plugin error: {e}")
                    continue

        if "save settings" in t or "remember this voice" in t:
            self._save_settings(); self.current_text="AI: Settings saved."; return True
        return False

    # ===== LLM =====
    def generate_response(self, user_text):
        if not user_text: return ""
        # light memory injection
        mem_hits=[e["text"] for e in self.memory if any(w in e.get("text","").lower() for w in user_text.lower().split())][:3]
        mem_block = ("\nMemory:\n" + "\n".join(f"- {m}" for m in mem_hits) + "\n") if mem_hits else ""

        # Enhanced system prompt for Home Assistant integration
        system=("You are a friendly home avatar with access to smart home controls. " +
               "You can control lights, climate, switches, and other smart devices. " +
               "For device control, respond with EXACTLY these command formats in brackets: " +
               "'[TURN_ON_LIGHT living_room]', '[TURN_OFF_LIGHT kitchen]', " +
               "'[SET_TEMPERATURE 72]', '[TURN_ON_SWITCH fan]', '[TURN_OFF_SWITCH fan]'. " +
               "For general conversation, reply naturally ≤8 words. " +
               "Direct, no echo." + mem_block)

        prompt=f"System: {system}\nUser: {user_text}\nAssistant:"
        try:
            r=requests.post(self.llm_url, json={"model":self.llm_model,"prompt":prompt,"stream":False,
                                                "options":{"num_ctx":8192,"temperature":0.2}}, timeout=120)
            if r.status_code!=200: return "Okay."
            reply=(r.json().get("response") or "").strip()

            # Check for Home Assistant commands in the response
            ha_command = self._extract_ha_command(reply)
            if ha_command:
                result = self._execute_ha_command(ha_command)
                return result

            # Normal response processing
            reply=re.sub(r"\s+"," ",reply); words=reply.split()
            if len(words)>8: reply=" ".join(words[:8]).rstrip(" ,.;:")+"."
            return reply or "Okay."
        except Exception: return "Okay."

    def _extract_ha_command(self, text):
        """Extract Home Assistant commands from LLM response"""
        import re
        # Look for commands in square brackets with more flexible pattern
        match = re.search(r'\[([A-Z_]+(?:\s+[A-Za-z0-9_]+)*)\]', text)
        if match:
            return match.group(1).strip()
        return None

    def _execute_ha_command(self, command):
        """Execute Home Assistant command and return response"""
        try:
            # Import HA integration
            from home_assistant_plugin import HomeAssistantIntegration
            ha = HomeAssistantIntegration()

            if not ha.hass_token:
                return "Home Assistant not configured"

            parts = command.split()
            action = parts[0]

            # Handle different command formats
            if action in ["TURN_ON_LIGHT", "TURNING_ON_LIGHT", "TURN_ON_LIGHTS"]:
                entity_id = f"light.{parts[1]}" if len(parts) > 1 else None
                return ha.control_light("on", entity_id)

            elif action in ["TURN_OFF_LIGHT", "TURNING_OFF_LIGHT", "TURN_OFF_LIGHTS"]:
                entity_id = f"light.{parts[1]}" if len(parts) > 1 else None
                return ha.control_light("off", entity_id)

            elif action in ["SET_TEMPERATURE", "TASK_SET_TEMPERATURE"]:
                if len(parts) > 1:
                    temp = parts[1] if parts[1].isdigit() else "72"
                    return ha.control_climate(f"set temperature to {temp}")
                return "Temperature not specified"

            elif action in ["TURN_ON_SWITCH", "TURNING_ON_SWITCH"]:
                entity_id = f"switch.{parts[1]}" if len(parts) > 1 else None
                return ha.control_switch("on", entity_id)

            elif action in ["TURN_OFF_SWITCH", "TURNING_OFF_SWITCH"]:
                entity_id = f"switch.{parts[1]}" if len(parts) > 1 else None
                return ha.control_switch("off", entity_id)

            else:
                return f"Unknown command: {command}"

        except Exception as e:
            return f"Command execution failed: {str(e)}"

    # ===== TTS =====
    def _play_chime(self):
        for cmd in (["canberra-gtk-play","-i","bell-terminal"], ["paplay","/usr/share/sounds/freedesktop/stereo/bell.oga"]):
            try: subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); break
            except Exception: continue
    def _stop_playback(self):
        if self._play_proc and self._play_proc.poll() is None:
            try: self._play_proc.terminate()
            except Exception: pass
        self._play_proc=None
    def play_audio(self, f):
        if not f or not Path(f).exists(): return
        self._stop_playback()
        last_err=None
        for dev in self.aplay_candidates:
            try:
                cmd=["aplay","-q"]; 
                if dev: cmd+=["-D",dev]
                cmd.append(f)
                self._play_proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return
            except Exception as e:
                last_err=e; continue
        print("❌ Playback failed:", last_err)
    def synthesize_speech(self, text):
        txt=(text or "").strip()
        if not txt or not self.enable_tts: return None
        out="tts_out.wav"; engine=self.settings.get("voice_engine","kokoro")
        if engine=="kokoro":
            try:
                url=self.kokoro_url.rstrip("/") + "/audio/speech"
                payload={"model":"kokoro","input":txt,"voice": self.settings.get("kokoro_voice","af_bella"),
                         "response_format":"wav","speed": float(self.tts_speed)}
                r=requests.post(url, json=payload, timeout=45)
                if r.status_code==200 and r.content:
                    Path(out).write_bytes(r.content); return out
            except Exception: pass
        try:
            pbin=shutil.which("piper"); pvoice=self.voice_map.get(self.settings.get("piper_voice","amy"))
            if engine in ("piper","kokoro") and pbin and pvoice and Path(pvoice).exists():
                subprocess.run([pbin,"-m",pvoice,"-f",out], input=txt.encode("utf-8"), timeout=45, check=True)
                if Path(out).exists() and Path(out).stat().st_size>0: return out
        except Exception: pass
        try:
            swpm=int(self.tts_speed*170)
            subprocess.run(["espeak-ng","-v",self.espeak_voice,"-s",str(swpm),"-w",out,txt], timeout=20, check=True)
            if Path(out).exists() and Path(out).stat().st_size>0: return out
        except Exception: pass
        return None

    # ===== Main loop =====
    def run(self):
        print("🎭 Avatar ready. Say 'sleep now' to pause; say the wake word to resume; say 'exit' to quit.")
        running=True
        while running:
            for e in pygame.event.get():
                if e.type==pygame.QUIT: running=False
                elif e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: running=False

            self.render_avatar()

            # exit requested by voice?
            if self.exit_requested:
                break

            # Sleep mode: only hotword wakes us (no recording)
            if self.sleeping:
                time.sleep(0.1)
                continue

            # If wake_mode=hotword+porcupine, require a recent detection
            if self.settings.get("wake_mode")=="hotword" and self.settings.get("hotword_engine")=="porcupine" and self.hw is not None:
                window=int(self.settings.get("hotword_window_s",10))
                if time.time()-getattr(self,'last_wake_ts',0) > window:
                    # still accept system commands spoken (via STT) to change mode, so record a short sample:
                    # (lightweight: 1s grab just to catch "wake always by default", etc.)
                    self.is_listening=True
                    wav=self.record_until_silence()
                    self.is_listening=False
                    if not wav: time.sleep(0.05); continue
                    user=self.transcribe_audio(wav)
                    if user and self.maybe_handle_voice_command(user): continue
                    self.current_text="Say the wake word."; time.sleep(0.05); continue

            # normal conversation path
            self.is_listening=True
            wav=self.record_until_silence()
            self.is_listening=False
            if not wav: time.sleep(0.05); continue

            user=self.transcribe_audio(wav)
            if not user: self.current_text="Didn't catch that."; continue
            if self.maybe_handle_voice_command(user): continue

            reply=self.generate_response(user); self.current_text="AI: "+reply
            self.is_speaking=True
            f=self.synthesize_speech(reply)
            if f: self.play_audio(f)
            self.is_speaking=False
            time.sleep(0.05)

        pygame.quit(); self.audio.terminate(); print("👋 Avatar shutdown complete")

if __name__=="__main__":
    AvatarPipeline().run()
