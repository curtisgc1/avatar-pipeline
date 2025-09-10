#!/usr/bin/env python3
# avatar_test.py — headless avatar pipeline (VAD + faster-whisper + Ollama + espeak-ng)
# Curtis edition: CPU by default; add --gpu when CUDA stack is ready.

import argparse
import os
import sys
import time
import threading
import queue
import wave
import subprocess
import json

import numpy as np
import sounddevice as sd
import requests
from faster_whisper import WhisperModel

# ---------------------
# Config (tweak here)
# ---------------------
LLM_URL = "http://127.0.0.1:11434/api/generate"
LLM_MODEL_NAME = "finalend/llama-3.1-storm:8b"
AVATAR_IMAGE_PATH = os.path.expanduser("~/avatar.png")  # optional (GUI only)

MIC_SAMPLE_RATE = 16000
MIC_CHANNELS = 6                    # 1 channel for STT
MIC_CHUNK_SIZE = 1024

# VAD params
SILENCE_THRESHOLD = 20.0
SILENCE_CHUNKS = 16                 # ~1 sec at 16kHz with CHUNK=1024

# TTS voice (espeak-ng)
ESPEAK_VOICE = "en-us"
ESPEAK_RATE_WPM = 170

# Queues
audio_queue = queue.Queue()
text_queue = queue.Queue()
tts_queue = queue.Queue()
status_queue = queue.Queue()

# ---------------------
# Mic device discovery
# ---------------------

# ---------------------
# Audio Recorder (VAD)
# ---------------------
def audio_recorder():
    devices = sd.query_devices()
    input_device_index = find_input_device_index(p)

    # OPEN MIC VIA PULSEAUDIO DEFAULT SOURCE (no device index)
    stream = p.open(
        dtype="int16",
        channels=MIC_CHANNELS,
        rate=MIC_SAMPLE_RATE,
        input=True,
        frames_per_buffer=MIC_CHUNK_SIZE
        # NOTE: no input_device_index -> PortAudio uses Pulse default source
    )
    

    print("INFO: Audio recorder started.")
    status_queue.put("Status: Listening...")

    while True:
        frames = []
        is_recording = False
        silence_counter = 0

        while True:
            data = stream.read(MIC_CHUNK_SIZE, exception_on_overflow=False)
            audio_data = data.flatten()
            print(f"First 10 samples: {audio_data[:10]}")
            level = float(np.abs(audio_data).mean())
            print(f"Audio level: {level}")

            if not is_recording:
                if level > SILENCE_THRESHOLD:
                    print("INFO: Voice detected! Recording...")
                    status_queue.put("Status: Detected! Recording...")
                    is_recording = True
                    frames = [data]
            else:
                print(f"INFO: Whisper using CPU.")
                frames.append(data)
                if level < SILENCE_THRESHOLD:
                    silence_counter += 1
                else:
                    print(f"INFO: Whisper using CPU.")
                    silence_counter = 0

                if silence_counter > SILENCE_CHUNKS:
                    print("INFO: Silence detected, processing.")
                    status_queue.put("Status: Processing...")
                    audio_queue.put(b"".join(frames))
                    status_queue.put("Status: Listening...")
                    break

# ---------------------
# Speech → Text (Whisper)
# ---------------------
def speech_to_text(whisper_device: str, compute_type: str, model_size: str):
    import subprocess
    while True:
        audio_data = audio_queue.get()
        temp_file = "/tmp/temp_recording.wav"
        try:
            with wave.open(temp_file, 'wb') as wf:
                wf.setnchannels(MIC_CHANNELS)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(MIC_SAMPLE_RATE)
                wf.writeframes(audio_data)
            if whisper_device == "cuda":
                print(f"INFO: Whisper using containerized GPU (RTX 5080).")
                subprocess.run(["docker", "cp", temp_file, "torch-cu128:/workspace/tmp/temp_recording.wav"], check=True)
                result = subprocess.run(
                ["docker", "exec", "torch-cu128", "python", "/workspace/container_stt_simple.py"],
                
                capture_output=True,
                text=True
            )
                transcribed_text = result.stdout.strip()
                if transcribed_text and not transcribed_text.startswith("ERROR"):
                    print(f"Whisper transcribed: {transcribed_text}")
                    text_queue.put(transcribed_text)
            else:
                print(f"INFO: Whisper using CPU.")
                model = WhisperModel(model_size, device=whisper_device, compute_type=compute_type)
                segments, _ = model.transcribe(temp_file)
                transcribed_text = " ".join([seg.text for seg in segments]).strip()
                if transcribed_text:
                    print(f"Whisper transcribed: {transcribed_text}")
                    text_queue.put(transcribed_text)
                print(f"Whisper transcribed: {transcribed_text}")
                text_queue.put(transcribed_text)
        finally:
            try:
                os.remove(temp_file)
            except:
                pass

def llm_processor():
    while True:
        user_text = text_queue.get()
        prompt = f"You are a concise voice assistant. Reply briefly.\nUser: {user_text}\nAssistant:"
        body = {
            "model": LLM_MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
        try:
            r = requests.post(LLM_URL, json=body, timeout=120)
            r.raise_for_status()
            resp = r.json().get("response", "").strip()
            if not resp:
                resp = "I heard you."
        except Exception as e:
            print(f"LLM error: {e}")
            resp = "I ran into an error talking to the language model."

        print(f"LLM says: {resp}")
        print("DEBUG: Adding to TTS queue")
        tts_queue.put(resp)

# ---------------------
# Text → Speech (espeak-ng + paplay)
# ---------------------
def synth_espeak_to_wav(text: str, out_path: str):
    # espeak-ng -v en-us -s 170 -w /tmp/say.wav "hello"
    cmd = [
        "espeak-ng",
        "-v", ESPEAK_VOICE,
        "-s", str(ESPEAK_RATE_WPM),
        "-w", out_path,
        text
    ]
    subprocess.run(cmd, check=True)

def play_wav_with_paplay(wav_path: str):
    # Use PulseAudio default sink (works even if ALSA devices are 'busy')
    subprocess.run(["paplay", wav_path], check=True)


def animate_face_with_sadtalker(wav_path: str, img_path: str, out_dir: str = "/tmp/avatar"):
    import subprocess, os, time
    
    print(f"DEBUG: Animation function called with: {wav_path}, {img_path}")
    os.makedirs(out_dir, exist_ok=True)
    
    # Copy files to container
    subprocess.run(f"docker cp {wav_path} torch-cu128:/workspace/tmp/audio.wav", shell=True, check=True)
    subprocess.run(f"docker cp {img_path} torch-cu128:/workspace/tmp/avatar.png", shell=True, check=True)
    
    # Run SadTalker in container
    cmd = """docker exec -i torch-cu128 bash -lc '
    cd /workspace/SadTalker
    python inference.py       --driven_audio /workspace/tmp/audio.wav       --source_image /workspace/tmp/avatar.png       --result_dir /workspace/tmp/output       --still       --preprocess crop
    '"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout[-500:] if result.stdout else "No output")
    
        # Find and copy the generated video back
    find_cmd = "docker exec torch-cu128 find /workspace/tmp -path '*output*' -name '*.mp4' -type f -mmin -1 | head -1"
    video_path = subprocess.run(find_cmd, shell=True, capture_output=True, text=True).stdout.strip()
    
    if video_path:
        local_video = f"{out_dir}/avatar_output.mp4"
        subprocess.run(f"docker cp torch-cu128:{video_path} {local_video}", shell=True)
        print(f"Video saved to: {local_video}")
        
        # Play the video with audio
        # subprocess.run(f"mpv {local_video} --really-quiet &", shell=True)
        return local_video
    else:
        print("No video generated")
        return None


def text_to_speech():
    while True:
        text = tts_queue.get()
        wav_path = "/tmp/avatar_tts.wav"
        try:
            print(f"DEBUG: Generating TTS for: {text[:50]}...")
            
            # Use espeak with better settings
            subprocess.run(["espeak-ng", "-v", "en+f3", "-s", "175", "-w", wav_path, text], check=True)
            print(f"DEBUG: Audio saved to {wav_path}")
            
            # Verify file exists
            if os.path.exists(wav_path):
                print(f"DEBUG: Audio file size: {os.path.getsize(wav_path)} bytes")
                animate_face_with_sadtalker(wav_path, AVATAR_IMAGE_PATH)
            else:
                print(f"INFO: Whisper using CPU.")
                print("ERROR: Audio file not created!")
            
        except Exception as e:
            print(f"TTS error: {e}")
        finally:
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except:
                pass
def run_gui():
    # Stub to avoid Tk errors; implement later if you want a window.
    print("GUI requested, but no GUI is implemented in this headless build.")
    print("Run without --gui. (Headless is default.)")

# ---------------------
# Main
# ---------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", action="store_true", help="Use GPU for Whisper (requires proper CUDA/CT2 install)")
    parser.add_argument("--model-size", default="base.en", help="Whisper model size, e.g., tiny, base, base.en, small, small.en, medium, large")
    parser.add_argument("--gui", action="store_true", help="(placeholder) try launching a GUI (not implemented here)")
    args = parser.parse_args()

    print("INFO: Make sure 'espeak-ng' is installed (`sudo apt install espeak-ng`)")
    print("INFO: Pipeline starting...")

    # Decide STT backend
    if args.gpu:
        whisper_device = "cuda"
        compute_type = "float16"   # good default for 4090/5080
    else:
        whisper_device = "cpu"
        compute_type = "int8"

    # Threads
    threading.Thread(target=audio_recorder, daemon=True).start()
    threading.Thread(target=speech_to_text, args=(whisper_device, compute_type, args.model_size), daemon=True).start()
    threading.Thread(target=llm_processor, daemon=True).start()
    threading.Thread(target=text_to_speech, daemon=True).start()

    if args.gui:
        run_gui()
    else:
        print("Running headless. Press Ctrl+C to quit.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            os._exit(0)

if __name__ == "__main__":
    import argparse, time, threading, os

    parser = argparse.ArgumentParser()
    parser.add_argument("--gpu", action="store_true", help="Use GPU for Whisper STT")
    parser.add_argument("--llm", default="finalend/llama-3.1-storm:8b",
                        help="Ollama model name (e.g., storm, qwen2.5:7b-instruct)")
    parser.add_argument("--stt", default="base.en",
                        help="Whisper model size (tiny/base.en/small.en/etc)")
    args = parser.parse_args()

    # Override the global model name if --llm is provided
    LLM_MODEL_NAME = args.llm

    print("INFO: Pipeline starting...")

    # Choose Whisper device
    whisper_device = "cuda" if args.gpu else "cpu"
    compute_type   = "float16" if args.gpu else "int8"

    # Start pipeline threads (your speech_to_text must accept device, compute_type, model_size)
    threading.Thread(target=audio_recorder, daemon=True).start()
    threading.Thread(target=speech_to_text, args=(whisper_device, compute_type, args.stt), daemon=True).start()
    threading.Thread(target=llm_processor, daemon=True).start()
    threading.Thread(target=text_to_speech, daemon=True).start()

    print("Running headless. Press Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        os._exit(0)

