import subprocess
import time

def check_memory():
    result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.used', '--format=csv,noheader'], 
                          capture_output=True, text=True)
    print(result.stdout)

print("Baseline:")
check_memory()

print("\nLoading Whisper...")
import whisper
model = whisper.load_model("base")

print("After Whisper:")
check_memory()

print("\nCalling vLLM...")
import requests
response = requests.post("http://localhost:8000/v1/chat/completions",
    json={"model": "Qwen/Qwen2.5-3B-Instruct", 
          "messages": [{"role": "user", "content": "Write a long story"}],
          "max_tokens": 500})

print("During generation:")
check_memory()

print("\nDone")
