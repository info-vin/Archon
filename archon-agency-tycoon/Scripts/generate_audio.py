import wave
import struct
import math
import os

def write_wav(filename, samples, sample_rate):
    target_dir = "/Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Sound"
    os.makedirs(target_dir, exist_ok=True)
    output_path = os.path.join(target_dir, filename)
    
    buffer = []
    for sample in samples:
        # Prevent clipping and convert to 16-bit PCM integer
        sample = max(-1.0, min(1.0, sample))
        pcm_val = int(sample * 32767)
        buffer.append(struct.pack('<h', pcm_val))
        
    with wave.open(output_path, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b''.join(buffer))
    print(f"🟢 Successfully generated chiptune: {filename} at {output_path}")

def generate_track_1_cyberpunk(sample_rate=22050):
    # Track 1: High Energy Cyberpunk (Am - F - C - G)
    bpm = 120
    beat_dur = 60.0 / bpm
    step_dur = beat_dur / 4
    total_steps = 64
    duration = total_steps * step_dur
    total_samples = int(sample_rate * duration)
    
    notes = {
        'A2': 110.00, 'E3': 164.81, 'F2': 87.31, 'C3': 130.81, 'C2': 65.41, 'G2': 98.00, 'D3': 146.83,
        'A4': 440.00, 'E4': 329.63, 'C5': 523.25, 'E5': 659.25, 'F4': 349.23, 'C4': 261.63, 'G4': 392.00,
        'B4': 493.88, 'D5': 587.33, 'G#4': 415.30, 'B3': 246.94, '-': 0.0
    }
    
    bass_pattern = ['A2']*12 + ['E3']*4 + ['F2']*12 + ['C3']*4 + ['C2']*12 + ['G2']*4 + ['G2']*12 + ['D3']*4
    melody_pattern = [
        'A4', 'E4', 'A4', 'C5', 'E5', 'C5', 'A4', 'E4',
        'A4', 'E4', 'A4', 'C5', 'E5', 'C5', 'A4', 'E4',
        'F4', 'C4', 'F4', 'A4', 'C5', 'A4', 'F4', 'C4',
        'F4', 'C4', 'F4', 'A4', 'C5', 'A4', 'F4', 'C4',
        'C4', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3',
        'C4', 'G3', 'C4', 'E4', 'G4', 'E4', 'C4', 'G3',
        'G4', 'D4', 'G4', 'B4', 'D5', 'B4', 'G4', 'D4',
        'E4', 'B3', 'E4', 'G#4', 'B4', 'G#4', 'E4', 'B3'
    ]
    
    samples = []
    phase_bass = 0.0
    phase_lead = 0.0
    
    for i in range(total_samples):
        t = i / sample_rate
        step = min(int(t / step_dur), total_steps - 1)
        
        bass_note = bass_pattern[step % len(bass_pattern)]
        freq_bass = notes.get(bass_note, 0.0)
        bass_val = 0.0
        if freq_bass > 0:
            phase_bass += 2.0 * math.pi * freq_bass / sample_rate
            bass_val = 0.12 if (phase_bass % (2.0 * math.pi)) < (0.5 * math.pi) else -0.12
            
        lead_note = melody_pattern[step % len(melody_pattern)]
        freq_lead = notes.get(lead_note, 0.0)
        decay = math.exp(-6.0 * (t % step_dur))
        lead_val = 0.0
        if freq_lead > 0:
            phase_lead += 2.0 * math.pi * freq_lead / sample_rate
            mod_phase = (phase_lead % (2.0 * math.pi)) / (2.0 * math.pi)
            lead_val = (4.0 * mod_phase - 1.0) if mod_phase < 0.5 else (3.0 - 4.0 * mod_phase)
            lead_val *= 0.12 * decay
            
        samples.append(bass_val + lead_val)
        
    write_wav("bgm_cyberpunk.wav", samples, sample_rate)

def generate_track_2_neon_city(sample_rate=22050):
    # Track 2: Mellow Neon City (Em - C - D - Bm)
    bpm = 100
    beat_dur = 60.0 / bpm
    step_dur = beat_dur / 2  # 8th notes
    total_steps = 32
    duration = total_steps * step_dur
    total_samples = int(sample_rate * duration)
    
    notes = {
        'E2': 82.41, 'B2': 123.47, 'C2': 65.41, 'G2': 98.00, 'D2': 73.42, 'A2': 110.00, 'B1': 61.74, 'F#2': 92.50,
        'E4': 329.63, 'G4': 392.00, 'B4': 493.88, 'C5': 523.25, 'D5': 587.33, 'F#4': 369.99, 'A4': 440.00, '-': 0.0
    }
    
    bass_pattern = ['E2']*8 + ['C2']*8 + ['D2']*8 + ['B1']*8
    melody_pattern = [
        'E4', 'G4', 'B4', 'G4', 'E4', 'G4', 'B4', '-',
        'C5', 'G4', 'E4', 'G4', 'C5', 'G4', 'E4', '-',
        'D5', 'A4', 'F#4', 'A4', 'D5', 'A4', 'F#4', '-',
        'B4', 'F#4', 'D4', 'F#4', 'B4', 'F#4', 'D4', '-'
    ]
    notes['D4'] = 293.66
    
    samples = []
    phase_bass = 0.0
    phase_lead = 0.0
    
    for i in range(total_samples):
        t = i / sample_rate
        step = min(int(t / step_dur), total_steps - 1)
        
        bass_note = bass_pattern[step % len(bass_pattern)]
        freq_bass = notes.get(bass_note, 0.0)
        bass_val = 0.0
        if freq_bass > 0:
            phase_bass += 2.0 * math.pi * freq_bass / sample_rate
            # Mellow sine-like triangle bass
            mod_p = (phase_bass % (2.0 * math.pi)) / (2.0 * math.pi)
            bass_val = (4.0 * mod_p - 1.0) if mod_p < 0.5 else (3.0 - 4.0 * mod_p)
            bass_val *= 0.15
            
        lead_note = melody_pattern[step % len(melody_pattern)]
        freq_lead = notes.get(lead_note, 0.0)
        decay = math.exp(-3.0 * (t % step_dur)) # Slower decay
        lead_val = 0.0
        if freq_lead > 0:
            phase_lead += 2.0 * math.pi * freq_lead / sample_rate
            # 50% square wave (classic soft pulse)
            lead_val = 0.10 if (phase_lead % (2.0 * math.pi)) < math.pi else -0.10
            lead_val *= decay
            
        samples.append(bass_val + lead_val)
        
    write_wav("bgm_neon_city.wav", samples, sample_rate)

def generate_track_3_hacking(sample_rate=22050):
    # Track 3: Fast Paced Cyber Hacking (Dm - Gm - A# - A)
    bpm = 140
    beat_dur = 60.0 / bpm
    step_dur = beat_dur / 4  # 16th notes
    total_steps = 64
    duration = total_steps * step_dur
    total_samples = int(sample_rate * duration)
    
    notes = {
        'D2': 73.42, 'A2': 110.00, 'G2': 98.00, 'D3': 146.83, 'A#2': 116.54, 'F3': 174.61, 'A2_hi': 220.00,
        'D4': 293.66, 'F4': 349.23, 'A4': 440.00, 'C#5': 554.37, 'E5': 659.25, 'G4': 392.00, 'A#4': 466.16,
        'D5': 587.33, 'F5': 698.46, 'C5': 523.25, '-': 0.0
    }
    
    bass_pattern = ['D2']*16 + ['G2']*16 + ['A#2']*16 + ['A2']*16
    melody_pattern = [
        'D4', 'F4', 'A4', 'D5', 'F5', 'D5', 'A4', 'F4',
        'D4', 'F4', 'A4', 'D5', 'F5', 'D5', 'A4', 'F4',
        'G4', 'A#4', 'D5', 'G5', 'A#5', 'G5', 'D5', 'A#4',
        'G4', 'A#4', 'D5', 'G5', 'A#5', 'G5', 'D5', 'A#4',
        'A#4', 'D5', 'F5', 'A#5', 'D6', 'A#5', 'F5', 'D5',
        'A#4', 'D5', 'F5', 'A#5', 'D6', 'A#5', 'F5', 'D5',
        'A4', 'C#5', 'E5', 'A5', 'C#6', 'A5', 'E5', 'C#5',
        'A4', 'C#5', 'E5', 'A5', 'C#6', 'A5', 'E5', 'C#5'
    ]
    notes['A5'] = 880.00
    notes['A#5'] = 932.33
    notes['D6'] = 1174.66
    notes['C#6'] = 1109.73
    
    samples = []
    phase_bass = 0.0
    phase_lead = 0.0
    
    for i in range(total_samples):
        t = i / sample_rate
        step = min(int(t / step_dur), total_steps - 1)
        
        bass_note = bass_pattern[step % len(bass_pattern)]
        freq_bass = notes.get(bass_note, 0.0)
        bass_val = 0.0
        if freq_bass > 0:
            phase_bass += 2.0 * math.pi * freq_bass / sample_rate
            # 12.5% duty cycle square wave (very sharp buzzy bass)
            bass_val = 0.12 if (phase_bass % (2.0 * math.pi)) < (0.25 * math.pi) else -0.12
            
        lead_note = melody_pattern[step % len(melody_pattern)]
        freq_lead = notes.get(lead_note, 0.0)
        decay = math.exp(-8.0 * (t % step_dur)) # Very fast snappy decay
        lead_val = 0.0
        if freq_lead > 0:
            phase_lead += 2.0 * math.pi * freq_lead / sample_rate
            # Fast pulse wave
            lead_val = 0.10 if (phase_lead % (2.0 * math.pi)) < (0.5 * math.pi) else -0.10
            lead_val *= decay
            
        samples.append(bass_val + lead_val)
        
    write_wav("bgm_hacking.wav", samples, sample_rate)

def generate_sfx_coin(sample_rate=22050):
    duration = 0.25
    total_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / sample_rate
        freq = 523.25 if t < 0.08 else 659.25
        decay = math.exp(-6.0 * t)
        phase += 2.0 * math.pi * freq / sample_rate
        val = 0.15 * decay if (phase % (2.0 * math.pi)) < math.pi else -0.15 * decay
        samples.append(val)
    write_wav("sfx_coin.wav", samples, sample_rate)

def generate_sfx_alarm(sample_rate=22050):
    duration = 1.0
    total_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / sample_rate
        mod = 0.5 + 0.5 * math.sin(2.0 * math.pi * 5.0 * t)
        freq = 500.0 + 400.0 * mod
        phase += 2.0 * math.pi * freq / sample_rate
        val = 0.12 if (phase % (2.0 * math.pi)) < math.pi else -0.12
        samples.append(val)
    write_wav("sfx_alarm.wav", samples, sample_rate)

def generate_sfx_sigh(sample_rate=22050):
    duration = 0.5
    total_samples = int(sample_rate * duration)
    samples = []
    phase = 0.0
    for i in range(total_samples):
        t = i / sample_rate
        freq = 300.0 - 200.0 * (t / duration)
        decay = math.exp(-3.0 * t)
        phase += 2.0 * math.pi * freq / sample_rate
        mod_p = (phase % (2.0 * math.pi)) / (2.0 * math.pi)
        val = (4.0 * mod_p - 1.0) if mod_p < 0.5 else (3.0 - 4.0 * mod_p)
        val *= 0.15 * decay
        samples.append(val)
    write_wav("sfx_sigh.wav", samples, sample_rate)

if __name__ == "__main__":
    generate_track_1_cyberpunk()
    generate_track_2_neon_city()
    generate_track_3_hacking()
    generate_sfx_coin()
    generate_sfx_alarm()
    generate_sfx_sigh()
    # Copy cyberpunk to default bgm.wav as well
    os.system("cp /Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Sound/bgm_cyberpunk.wav /Users/vincenta/GoogleKwok022/Archon/archon-agency-tycoon/Assets/Sound/bgm.wav")
