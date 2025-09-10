FROM nvcr.io/nvidia/l4t-pytorch:r35.4.1-pth2.0-py3

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/Los_Angeles

RUN apt-get update && apt-get install -y \
    git wget ffmpeg libsndfile1 espeak-ng \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    fastapi uvicorn soundfile numpy scipy

COPY server.py /app/server.py
WORKDIR /app

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5002"]
