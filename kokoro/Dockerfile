FROM pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles

RUN apt-get update && apt-get install -y \
    git wget ffmpeg libsndfile1 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi uvicorn soundfile numpy scipy \
    kokoro>=0.9.4

COPY server.py /app/server.py
WORKDIR /app

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5002"]
