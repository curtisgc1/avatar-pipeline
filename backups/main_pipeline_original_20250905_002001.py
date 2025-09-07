#!/usr/bin/env python3
import os, time, math, wave, re, warnings, subprocess, shutil, json
from pathlib import Path
import pygame, pyaudio, requests

warnings.filterwarnings("ignore", category=UserWarning, module="pkg_resources")

def rms_level(buf):
    if not buf: return 0.0
    import struct
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
        self.llm_model = os.getenv("LLM_MODEL", "qwen2.5:7b")

        # ----- Settings (persisted) -----
        self.settings_path = os.path.expanduser("~/.avatar/settings.json")
        self.settings = {
            "voice_engine": "kokoro",          # kokoro | piper | espeak
            "kokoro_voice": "af_bella",        # default natural female
            "piper_voice":  "amy",             # mapped below
            "volume": 80,                      # 0..150 (PipeWire allows soft over-amp)
            "wake_mode": "hotword",            # hotword | always
            "wake_word": "computer",           # say: "computer, turn on the lights"
        }
        self._load_settings()

        # ----- TTS backends -----
        self.kokoro_url   = os.getenv("KOKORO_URL", "http://localhost:8880/v1")
        self.user_voices_dir = os.path.expanduser("~/.local/share/piper/voices/en_US")
        self.voice_map = {
            "amy":      os.path.join(self.user_voices_dir, "en_US-amy-medium.onnx"),
            "ljspeech": os.path.join(self.user_voices_dir, "en_US-ljspeech-medium.onnx"),
            "kathleen": os.path.join(self.user_voices_dir, "en_US-kathleen-low.onnx"),
        }
        self.espeak_voice = os.getenv("ESPEAK_VOICE", "en+f3")
        try: self.tts_speed = float(os.getenv("TTS_SPEED","1.0"))
        except: self.tts_speed = 1.0
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
                    print("🎙️ Using ReSpeaker input:", info.get("name"))
                    break
            if self.input_device_index is None:
                print("ℹ️ ReSpeaker input not auto-detected; using default input.")
        except Exception as e:
            print("⚠️ Mic scan error:", e)

        # Playback (Pulse/PipeWire default works best)
        self.aplay_candidates = [os.getenv("APLAY_DEVICE")] if os.getenv("APLAY_DEVICE") else []
        self.aplay_candidates += ["default"]

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
        except Exception:
            pass

        # Apply persisted volume immediately
        self._apply_volume(self.settings.get("volume", 80))

    # ----- settings helpers -----
    def _load_settings(self):
        try:
            if Path(self.settings_path).exists():
                self.settings.update(json.loads(Path(self.settings_path).read_text()))
                print("⚙️  Loaded settings:", self.settings)
            else:
                Path(self.settings_path).parent.mkdir(parents=True, exist_ok=True)
                Path(self.settings_path).write_text(json.dumps(self.settings, indent=2))
        except Exception as e:
            print("⚠️ Settings load error:", e)

    def _save_settings(self):
        try:
            Path(self.settings_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.settings_path).write_text(json.dumps(self.settings, indent=2))
            print("💾 Settings saved:", self.settings)
        except Exception as e:
            print("⚠️ Settings save error:", e)

    # ----- volume controls (PipeWire / Pulse) -----
    def _apply_volume(self, percent):
        # Requires wpctl (PipeWire) or pactl (Pulse). Prefer wpctl.
        try:
            pct = max(0, min(int(percent), 150))
            if shutil.which("wpctl"):
                # wpctl accepts 0..1 float for absolute set (e.g., 0.80)
                subprocess.run(["wpctl","set-volume","@DEFAULT_SINK@", f"{pct/100.0:.2f}"], check=False)
            elif shutil.which("pactl"):
                subprocess.run(["pactl","set-sink-volume","@DEFAULT_SINK@", f"{pct}%"], check=False)
        except Exception as e:
            print("🔉 volume set failed:", e)

    def _volume_command(self, text):
        t = text.lower()
        m = re.search(r"(volume|vol)\s*(up|down|set)?\s*([0-9]{1,3})?", t)
        if not m and ("mute" not in t and "unmute" not in t): return False
        if "mute" in t:
            if shutil.which("wpctl"):
                subprocess.run(["wpctl","set-mute","@DEFAULT_SINK@", "1"], check=False)
            elif shutil.which("pactl"):
                subprocess.run(["pactl","set-sink-mute","@DEFAULT_SINK@","1"], check=False)
            self.current_text="AI: Muted."
            return True
        if "unmute" in t:
            if shutil.which("wpctl"):
                subprocess.run(["wpctl","set-mute","@DEFAULT_SINK@", "0"], check=False)
            elif shutil.which("pactl"):
                subprocess.run(["pactl","set-sink-mute","@DEFAULT_SINK@","0"], check=False)
            self.current_text="AI: Unmuted."
            return True
        # up/down/set N
        direction = m.group(2) or "set"
        amt = m.group(3)
        cur = self.settings.get("volume", 80)
        if direction == "up" and amt:
            newv = cur + int(amt)
        elif direction == "down" and amt:
            newv = cur - int(amt)
        elif direction == "set" and amt:
            newv = int(amt)
        else:
            return False
        newv = max(0, min(newv, 150))
        self.settings["volume"] = newv
        self._save_settings()
        self._apply_volume(newv)
        self.current_text = f"AI: Volume {newv}%."
        return True

    # ---------------- UI ----------------
    def render_avatar(self):
        self.screen.fill((20,20,30))
        status = "Idle"
        if self.is_listening: status="🎤 Listening…"
        elif self.is_speaking: status="🗣️ Speaking…"
        self.screen.blit(self.font.render(status, True, (255,255,255)), (10,10))
        if self.avatar_image:
            self.screen.blit(self.avatar_image,(0,0))
        if self.current_text:
            words=self.current_text.split(); lines=[]; cur=""
            for w in words:
                if len(cur+w)<40: cur+=w+" "
                else: lines.append(cur.strip()); cur=w+" "
            if cur: lines.append(cur.strip())
            for i,l in enumerate(lines[-3:]):
                self.screen.blit(self.font.render(l,True,(255,255,255)),(10,50+i*36))
        pygame.display.flip()

    # ---------------- Record with VAD ----------------
    def record_until_silence(self):
        try:
            stream = self.audio.open(format=self.audio_format, channels=1, rate=self.rate,
                                     input=True, input_device_index=self.input_device_index,
                                     frames_per_buffer=self.chunk)
        except Exception as e:
            print("❌ Mic open error:", e); return None
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
                    if (now_ms-last_voice_ms)>self.silence_hang_ms or (now_ms-started_at)>self.max_ms:
                        break
                if not heard and now_ms>15000: stream.stop_stream(); stream.close(); self.is_listening=False; return None
            stream.stop_stream(); stream.close(); self.is_listening=False
            if not frames: return None
            dur_ms=(len(frames)*self.chunk*1000)//self.rate
            if dur_ms<self.min_ms: return None
            fname="recording.wav"
            with wave.open(fname,'wb') as wf:
                wf.setnchannels(1); wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wf.setframerate(self.rate); wf.writeframes(b"".join(frames))
            return fname
        except Exception as e:
            print("❌ Recording error:", e)
            try: stream.stop_stream(); stream.close()
            except: pass
            self.is_listening=False
            return None

    def play_audio(self, f):
        if not f or not Path(f).exists(): return
        last_err=None
        for dev in self.aplay_candidates:
            try:
                cmd=["aplay","-q"]; 
                if dev: cmd+=["-D",dev]
                cmd.append(f)
                subprocess.run(cmd, timeout=20, check=True)
                return
            except Exception as e:
                last_err=e; continue
        print("❌ Playback failed:", last_err)

    # ---------------- STT ----------------
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
            if r.status_code!=200: 
                return ""
            ctype=(r.headers.get("Content-Type") or "").lower()
            text = (r.json().get("text") if "application/json" in ctype else r.text).strip()
            if len(text)<2 or re.fullmatch(r"[Uu]h+|[Mm]m+|[Yy]ou", text): return ""
            return text
        except Exception as e:
            print("❌ STT Exception:", e); return ""

    # ---------------- voice / wake / system commands ----------------
    def _kokoro_voices(self):
        try:
            j=requests.get(self.kokoro_url.rstrip("/")+"/audio/voices", timeout=5).json()
            # next line works with most kokoro servers; fallback to flat list
            voices = j.get("voices") or j
            names=[]
            for v in voices:
                if isinstance(v, dict) and "name" in v: names.append(v["name"])
                elif isinstance(v, str): names.append(v)
            return sorted(set(names))
        except Exception:
            return ["af_bella","af_sky","af_heart"]

    def maybe_handle_voice_command(self, user_text):
        t=user_text.lower().strip()

        # volume
        if self._volume_command(t): return True

        # wake mode
        if re.search(r"\bwake (always|continuous)\b", t):
            self.settings["wake_mode"]="always"; self._save_settings()
            self.current_text="AI: Always listening."
            return True
        if re.search(r"\bwake (hotword|keyword)\b", t):
            self.settings["wake_mode"]="hotword"; self._save_settings()
            self.current_text=f"AI: Say {self.settings['wake_word']} first."
            return True
        m=re.search(r"\bset wake word\s+([a-z0-9\-]+)\b", t)
        if m:
            self.settings["wake_word"]=m.group(1); self._save_settings()
            self.current_text=f"AI: Wake word set to {m.group(1)}."
            return True

        # list voices
        if "list voices" in t or "what voices" in t:
            kok = ", ".join(self._kokoro_voices()[:20])
            pip = ", ".join(self.voice_map.keys())
            msg = f"Kokoro: {kok}. Piper: {pip}."
            self.current_text="AI: " + msg
            if self.enable_tts:
                wav=self.synthesize_speech(msg); 
                if wav: self.play_audio(wav)
            return True

        # switch voices
        if re.search(r"\bvoice\b", t):
            # Kokoro names (bella/sky/heart)
            m = re.search(r"\b(bella|sky|heart)\b", t)
            if m:
                self.settings["voice_engine"]="kokoro"
                self.settings["kokoro_voice"]=f"af_{m.group(1)}"
                self._save_settings()
                self.current_text=f"AI: Switched to {m.group(1)}."
                if self.enable_tts:
                    wav=self.synthesize_speech(self.current_text[4:])
                    if wav: self.play_audio(wav)
                return True
            # Piper names
            m = re.search(r"\b(amy|kathleen|ljspeech)\b", t)
            if m and Path(self.voice_map[m.group(1)]).exists():
                self.settings["voice_engine"]="piper"
                self.settings["piper_voice"]=m.group(1)
                self._save_settings()
                self.current_text=f"AI: Switched to {m.group(1)} (Piper)."
                if self.enable_tts:
                    wav=self.synthesize_speech(self.current_text[4:])
                    if wav: self.play_audio(wav)
                return True

        # remember/save settings on demand
        if "save settings" in t or "remember this voice" in t:
            self._save_settings()
            self.current_text="AI: Settings saved."
            return True

        return False

    # ---------------- LLM ----------------
    def generate_response(self, user_text):
        if not user_text: return ""
        system=("You are a friendly home avatar. Reply ≤8 words. Direct, no echo.")
        prompt=f"System: {system}\nUser: {user_text}\nAssistant:"
        try:
            r=requests.post(self.llm_url, json={"model":self.llm_model,"prompt":prompt,"stream":False,
                                                "options":{"num_ctx":8192,"temperature":0.2}}, timeout=120)
            if r.status_code!=200:
                return "Okay."
            reply=(r.json().get("response") or "").strip()
            reply=re.sub(r"\s+"," ",reply)
            words=reply.split()
            if len(words)>8: reply=" ".join(words[:8]).rstrip(" ,.;:")+"."
            return reply or "Okay."
        except Exception:
            return "Okay."

    # ---------------- TTS: Kokoro → Piper → espeak ----------------
    def synthesize_speech(self, text):
        txt=(text or "").strip()
        if not txt or not self.enable_tts: return None
        out="tts_out.wav"

        # pick engine from settings
        engine=self.settings.get("voice_engine","kokoro")

        # Kokoro first (natural)
        if engine=="kokoro":
            try:
                url=self.kokoro_url.rstrip("/") + "/audio/speech"
                payload={"model":"kokoro","input":txt,"voice": self.settings.get("kokoro_voice","af_bella"),
                         "response_format":"wav","speed": float(self.tts_speed)}
                r=requests.post(url, json=payload, timeout=45)
                if r.status_code==200 and r.content:
                    Path(out).write_bytes(r.content); return out
            except Exception as e:
                print("ℹ️ Kokoro TTS failed:", e)

        # Piper fallback
        try:
            piper_bin=shutil.which("piper")
            pvoice=self.voice_map.get(self.settings.get("piper_voice","amy"))
            if engine in ("piper","kokoro") and piper_bin and pvoice and Path(pvoice).exists():
                subprocess.run([piper_bin,"-m",pvoice,"-f",out], input=txt.encode("utf-8"),
                               timeout=45, check=True)
                if Path(out).exists() and Path(out).stat().st_size>0: return out
        except Exception as e:
            print("ℹ️ Piper failed:", e)

        # espeak fallback
        try:
            speed_wpm=int(self.tts_speed*170)
            subprocess.run(["espeak-ng","-v",self.espeak_voice,"-s",str(speed_wpm),"-w",out,txt],
                           timeout=20, check=True)
            if Path(out).exists() and Path(out).stat().st_size>0: return out
        except Exception as e:
            print("❌ espeak failed:", e)

        return None

    # ---------------- Main loop ----------------
    def run(self):
        print("🎭 Avatar started. Voice cmds: 'voice bella', 'volume up 10', 'wake always', 'list voices', 'save settings'. ESC to quit.")
        running=True
        while running:
            for e in pygame.event.get():
                if e.type==pygame.QUIT: running=False
                elif e.type==pygame.KEYDOWN and e.key==pygame.K_ESCAPE: running=False

            self.render_avatar()

            # 1) capture
            self.is_listening=True
            wav=self.record_until_silence()
            self.is_listening=False
            if not wav: time.sleep(0.05); continue

            # 2) STT
            user=self.transcribe_audio(wav)
            if not user: self.current_text="Didn't catch that."; continue

            # 2a) wake-word gate (STT-based)
            if self.settings.get("wake_mode","hotword")=="hotword":
                ww = self.settings.get("wake_word","computer").lower()
                low = user.lower().strip()
                if low.startswith(ww):
                    user = re.sub(rf"^{re.escape(ww)}[ ,:]*","", low).strip()
                    if not user:
                        self.current_text = f"AI: Listening after '{ww}'."
                        continue
                else:
                    # allow commands to change modes without wake word
                    if self.maybe_handle_voice_command(low): 
                        continue
                    # speak hint just once every so often
                    self.current_text=f"Say '{ww}, …' or 'wake always'."
                    continue

            # 3) system/voice commands
            if self.maybe_handle_voice_command(user):
                continue

            # 4) LLM
            reply=self.generate_response(user)
            self.current_text="AI: "+reply

            # 5) TTS + play
            self.is_speaking=True
            f=self.synthesize_speech(reply)
            if f: self.play_audio(f)
            self.is_speaking=False

            time.sleep(0.05)

        pygame.quit(); self.audio.terminate(); print("👋 Avatar shutdown complete")

if __name__=="__main__":
    AvatarPipeline().run()
