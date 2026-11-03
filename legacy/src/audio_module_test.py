from audio import GameBoyAdvanceAudio
from gba import GameBoyAdvance
import time
import math

cpu = GameBoyAdvance()
audio = GameBoyAdvanceAudio(cpu)

audio.writeEnable(1)
audio.writeSoundControlLo('0x0fff')
audio.writeSoundControlHi('0x03ff')

frequency = 1200  # Frequency of the sound wave in Hz
sample_rate = 16000  # Sample rate in Hz
duration = 5  # Duration of the sound in seconds

samples = int(sample_rate * duration)

for i in range(samples):
    t = float(i) / sample_rate
    value = int(math.sin(2 * math.pi * frequency * t) * 2048 + 2048)  # Generate a sine wave
    audio.writeSoundFIFO(value)

while True:
    audio.updateTimers()
    time.sleep(0.01)