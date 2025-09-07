def animate_face_with_sadtalker(wav_path: str, img_path: str, out_dir: str = "/tmp/avatar"):
    import subprocess, os, shutil, time
    
    print(f"DEBUG: Animation function called with: {wav_path}, {img_path}")
    os.makedirs(out_dir, exist_ok=True)
    
    # Copy files to container
    subprocess.run(f"docker cp {wav_path} torch-cu128:/workspace/tmp/audio.wav", shell=True, check=True)
    subprocess.run(f"docker cp {img_path} torch-cu128:/workspace/tmp/avatar.png", shell=True, check=True)
    
    # Run SadTalker in container
    cmd = """docker exec -i torch-cu128 bash -lc '
    cd /workspace/SadTalker
    python inference.py \
      --driven_audio /workspace/tmp/audio.wav \
      --source_image /workspace/tmp/avatar.png \
      --result_dir /workspace/tmp/output \
      --still \
      --preprocess crop
    '"""
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    
    # Find and copy the generated video back
    timestamp = time.strftime("%Y_%m_%d_%H.%M.%S")
    docker_video = f"/workspace/tmp/output/{timestamp}.mp4"
    local_video = f"{out_dir}/avatar_{timestamp}.mp4"
    
    # Try to find the actual video file
    find_cmd = "docker exec torch-cu128 find /workspace/tmp -name '*.mp4' -type f | head -1"
    video_path = subprocess.run(find_cmd, shell=True, capture_output=True, text=True).stdout.strip()
    
    if video_path:
        subprocess.run(f"docker cp torch-cu128:{video_path} {local_video}", shell=True)
        print(f"Video saved to: {local_video}")
        
        # Play the video
        subprocess.run(f"vlc {local_video} --play-and-exit --intf dummy 2>/dev/null &", shell=True)
        return local_video
    else:
        print("No video generated")
        return None
