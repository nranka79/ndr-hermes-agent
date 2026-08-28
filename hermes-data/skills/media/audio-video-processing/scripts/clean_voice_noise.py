#!/usr/bin/env python3
"""
Clean consistent background noise (treadmill, fan, AC hum) from voice recordings
using spectral gating (noisereduce). Outputs a cleaned 16kHz mono WAV ready for
transcription.

Usage:
    python3 clean_voice_noise.py <input.oga> [output.wav]

Dependencies: noisereduce, librosa, soundfile (install via uv pip install)
"""

import noisereduce as nr
import librosa
import soundfile as sf
import numpy as np
import sys
import subprocess
import os
import tempfile

INPUT_FILE = sys.argv[1] if len(sys.argv) > 1 else None
OUTPUT_FILE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/cleaned_voice.wav"

if not INPUT_FILE:
    print("Usage: python3 clean_voice_noise.py <input.oga> [output.wav]")
    sys.exit(1)

print(f"🔄 Input:  {INPUT_FILE}")
print(f"🎯 Output: {OUTPUT_FILE}")

# Step 1: Convert OGA/OGG (Opus) → 16k mono WAV
print("📦 Converting OGA → WAV...")
tmp_wav = tempfile.mktemp(suffix=".wav")
subprocess.run([
    "ffmpeg", "-y", "-i", INPUT_FILE,
    "-ar", "16000", "-ac", "1", "-sample_fmt", "s16",
    tmp_wav
], check=True, capture_output=True)

# Step 2: Load audio
print("🔊 Loading audio...")
audio, sr = librosa.load(tmp_wav, sr=16000, mono=True)
duration = librosa.get_duration(y=audio, sr=sr)
print(f"   Duration: {duration:.1f}s, Sample rate: {sr}Hz")

# Step 3: Profile noise from leading silence segment
noise_sample_duration = max(int(1.5 * sr), min(int(0.05 * len(audio)), sr * 3))
noise_sample = audio[:noise_sample_duration]
print(f"   Noise profile: first {noise_sample_duration/sr:.1f}s")

# Step 4: Apply spectral gating (stationary mode for consistent noise)
print("🧹 Applying noise reduction (spectral gating)...")
reduced_audio = nr.reduce_noise(
    y=audio,
    sr=sr,
    y_noise=noise_sample,
    prop_decrease=0.85,
    stationary=True,
    time_constant_s=2.0,
    n_std_thresh_stationary=1.5,
    use_tqdm=True
)

# Step 5: Normalize volume
max_val = np.max(np.abs(reduced_audio))
if max_val > 0:
    reduced_audio = reduced_audio / max_val * 0.95

rms_before = np.sqrt(np.mean(audio**2))
rms_after = np.sqrt(np.mean(reduced_audio**2))
print(f"   RMS before: {rms_before:.4f}")
print(f"   RMS after:  {rms_after:.4f} ({(1-rms_after/rms_before)*100:.0f}% reduction)")

# Step 6: Save cleaned audio
sf.write(OUTPUT_FILE, reduced_audio, sr, subtype='PCM_16')
os.unlink(tmp_wav)

print(f"\n✅ Done! Cleaned: {OUTPUT_FILE} ({os.path.getsize(OUTPUT_FILE)} bytes)")