import numpy as np
from gba import GameBoyAdvance
from audio import GameBoyAdvanceAudio
import sounddevice as sd
import time

gba = GameBoyAdvance()
audio = GameBoyAdvanceAudio(gba)

# Set the CPU frequency
audio.cpuFrequency = 16777216  # Typical CPU frequency for GBA (16.777216 MHz)

# Initialize audio module
audio.writeEnable(1)
audio.writeSoundControlLo(0x0fff)
audio.writeSoundControlHi(0x03ff)

# Generate a sine wave
frequency = 8000  # Frequency of the sound wave in Hz
sample_rate = 32768  # Sample rate in Hz (same as GameBoyAdvanceAudio)
duration = 5  # Duration of the sound in seconds
samples = int(sample_rate * duration)

# Create a stream to play the audio
stream = sd.OutputStream(
    samplerate=sample_rate,
    channels=2,
    callback=audio.audioProcess,
    blocksize=audio.bufferSize
)
stream.start()

print("Playing audio for 5 seconds...")

start_time = time.time()

# Generate and play the sine wave
for i in range(samples):
    t = float(i) / sample_rate
    value = int(np.sin(2 * np.pi * frequency * t) * 127 + 128)  # Scale to [-128, 127] range
    audio.writeSoundFIFO(value)
    audio.updateTimers()

    # Wait for the next sample interval
    elapsed_time = time.time() - start_time
    if elapsed_time < i / sample_rate:
        time.sleep((i / sample_rate) - elapsed_time)

print("Audio playback completed.")

# Stop the audio stream
stream.stop()