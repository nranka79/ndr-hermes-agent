#!/usr/bin/env python3
"""
Clean background noise from voice recording and transcribe.
Pipeline: OGA/OGG → WAV → noise reduction (spectral gating) → faster-whisper.

Usage:
    python3 clean-and-transcribe.py /path/to/input.oga [output_dir]
    
    Output: input_cleaned.wav (noise-reduced audio) + prints transcription to stdout.

Requires: whisper-cpu venv with faster-whisper, noisereduce, librosa, soundfile
    /opt/data/whisper-cpu/bin/python3 -m pip install faster-whisper noisereduce librosa soundfile
    /opt/data/whisper-cpu/bin/python3 -m pip install --ignore-installed ctranslate2 onnxruntime
"""

import noisereduce as nr
import librosa
import soundfile as sf
import numpy as np
import subprocess
import tempfile
import os
import sys
from pathlib import Path


def clean_audio(input_path: str, output_path: str | None = None) -> str:
    """
    Apply stationary spectral gating noise reduction to a voice recording.
    Uses first 1.5s of audio as noise profile.
    
    Args:
        input_path: Path to .oga, .ogg, or .wav file.
        output_path: Where to save cleaned WAV. If None, auto-generates.
    
    Returns:
        Path to cleaned WAV file.
    """
    input_path = str(input_path)
    if output_path is None:
        stem = Path(input_path).stem
        output_path = f"{stem}_cleaned.wav"

    print(f"[1/4] Converting {input_path} to WAV...", file=sys.stderr)
    tmp_wav = tempfile.mktemp(suffix=".wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", input_path, "-ar", "16000", "-ac", "1", "-sample_fmt", "s16", tmp_wav],
        check=True, capture_output=True
    )

    print(f"[2/4] Loading audio...", file=sys.stderr)
    audio, sr = librosa.load(tmp_wav, sr=16000, mono=True)
    os.unlink(tmp_wav)
    duration = librosa.get_duration(y=audio, sr=sr)
    rms_before = float(np.sqrt(np.mean(audio**2)))
    print(f"     Duration: {duration:.1f}s, RMS: {rms_before:.4f}", file=sys.stderr)

    print(f"[3/4] Applying spectral gating (noise profile: first 1.5s)...", file=sys.stderr)
    noise_sample = audio[:min(int(1.5 * sr), len(audio) // 4)]
    cleaned = nr.reduce_noise(
        y=audio, sr=sr, y_noise=noise_sample,
        prop_decrease=0.85, stationary=True,
        time_constant_s=2.0, n_std_thresh_stationary=1.5,
        use_tqdm=False
    )

    # Normalize
    max_val = float(np.max(np.abs(cleaned)))
    if max_val > 0:
        cleaned = cleaned / max_val * 0.95

    rms_after = float(np.sqrt(np.mean(cleaned**2)))
    print(f"     RMS after: {rms_after:.4f} ({(1 - rms_after / rms_before) * 100:.0f}% reduction)", file=sys.stderr)

    print(f"[4/4] Saving cleaned audio...", file=sys.stderr)
    sf.write(output_path, cleaned, sr, subtype="PCM_16")
    print(f"     Output: {output_path} ({os.path.getsize(output_path)} bytes)", file=sys.stderr)

    return output_path


def transcribe(audio_path: str, model_name: str = "small") -> str:
    """
    Transcribe cleaned audio using faster-whisper.
    
    Args:
        audio_path: Path to WAV file.
        model_name: Model size (base, small, medium, large-v3).
    
    Returns:
        Full transcription text.
    """
    from faster_whisper import WhisperModel

    print(f"[Transcribe] Loading model '{model_name}'...", file=sys.stderr)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    # Try with VAD first; if no segments, retry without VAD
    print(f"[Transcribe] Transcribing...", file=sys.stderr)
    segments, info = model.transcribe(
        audio_path, beam_size=5, language="en",
        vad_filter=True, vad_parameters=dict(min_silence_duration_ms=500, threshold=0.5)
    )

    text_parts = []
    seg_count = 0
    for seg in segments:
        text_parts.append(seg.text.strip())
        seg_count += 1

    # Retry without VAD if VAD returned nothing
    if seg_count == 0:
        print(f"[Transcribe] VAD returned empty — retrying without VAD filter...", file=sys.stderr)
        segments, info = model.transcribe(audio_path, beam_size=5, language="en", vad_filter=False)
        for seg in segments:
            text_parts.append(seg.text.strip())

    full_text = " ".join(text_parts)
    print(f"[Transcribe] {info.language} (p={info.language_probability:.2f}), {len(full_text.split())} words", file=sys.stderr)

    return full_text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 clean-and-transcribe.py <input.oga> [output_dir]", file=sys.stderr)
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(input_file) or "."

    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    # Clean
    cleaned_path = clean_audio(input_file, os.path.join(output_dir, f"{Path(input_file).stem}_cleaned.wav"))

    # Transcribe
    text = transcribe(cleaned_path)
    print(text)