#!/usr/bin/env python3
import pyaudio
import wave

print('Testing audio recording...')
p = pyaudio.PyAudio()

# Find ReSpeaker device
respeaker_device = None
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    name = info.get('name', '')
    if 'ArrayUAC10' in str(name):
        respeaker_device = i
        print(f'Found ReSpeaker at device {i}: {name}')
        break

if respeaker_device is None:
    print('ReSpeaker not found, trying default')
    try:
        default_info = p.get_default_input_device_info()
        respeaker_device = int(default_info['index'])
        print(f'Using default device {respeaker_device}')
    except Exception as e:
        print(f'No default input device: {e}')
        p.terminate()
        exit(1)

print(f'Using device {respeaker_device}')

# Try to open stream
try:
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=16000,
                    input=True,
                    input_device_index=int(respeaker_device),
                    frames_per_buffer=1024)

    print('Audio stream opened successfully!')
    print('Recording for 2 seconds...')

    frames = []
    for i in range(0, int(16000 / 1024 * 2)):
        data = stream.read(1024)
        frames.append(data)

    print('Recording complete!')

    # Save to file
    wf = wave.open('test_recording.wav', 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(16000)
    wf.writeframes(b''.join(frames))
    wf.close()

    print('Saved to test_recording.wav')

    stream.stop_stream()
    stream.close()

except Exception as e:
    print(f'Audio test failed: {e}')
    import traceback
    traceback.print_exc()

p.terminate()
print('Audio test complete')
