import math, wave, struct

def make_wav(filename, freq, duration, vol=0.2, decay=True, noise=False):
    f = wave.open(filename, 'w')
    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    samples = []
    for i in range(int(44100 * duration)):
        env = (1.0 - i/(44100*duration)) if decay else 1.0
        if noise:
            import random
            val = int(vol * env * 32767 * random.uniform(-1, 1))
        else:
            val = int(vol * env * 32767 * math.sin(2 * math.pi * freq * (i / 44100.0)))
        samples.append(struct.pack('<h', val))
    f.writeframes(b''.join(samples))
    f.close()

make_wav('Assets/Sounds/hover.wav', 600, 0.05, 0.05) # Low volume hover
make_wav('Assets/Sounds/play.wav', 300, 0.2, 0.2) # Play sound
make_wav('Assets/Sounds/error.wav', 150, 0.3, 0.2) # Error sound
make_wav('Assets/Sounds/hit.wav', 0, 0.3, 0.3, True, True) # Noise hit
