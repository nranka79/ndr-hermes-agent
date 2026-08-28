# Common ffmpeg Commands — Quick Reference

## Probe / Inspect

```bash
# Duration
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 <file>

# Stream info (codecs, bitrate, resolution)
ffprobe -v error -show_entries stream=codec_type,codec_name,width,height,bit_rate -of default=noprint_wrappers=1 <file>

# Full format + stream info
ffprobe -v error -show_entries format:stream -of default=noprint_wrappers=1 <file>
```

## Audio Extraction

```bash
# From video → Opus OGG (Telegram voice bubble)
ffmpeg -i <input.mp4> -vn -acodec libopus -b:a 32k <output.ogg> -y

# From video → MP3
ffmpeg -i <input.mp4> -vn -acodec libmp3lame -b:a 128k <output.mp3> -y

# From video → WAV (uncompressed, for further processing)
ffmpeg -i <input.mp4> -vn -acodec pcm_s16le -ar 44100 <output.wav> -y
```

## Audio Clipping / Trimming

```bash
# Keep first N seconds
ffmpeg -i <input> -t 30 -c copy <output>

# Keep from N seconds to end
ffmpeg -i <input> -ss 30 -c copy <output>

# Keep from A to B (seconds)
ffmpeg -i <input> -ss 10 -to 30 -c copy <output>

# Keep from A to B (HH:MM:SS format)
ffmpeg -i <input> -ss 00:01:30 -to 00:02:00 -c copy <output>
```

## Audio Enhancement

### Vocal presence boost (full chain)

The complete filter chain for bringing a voice forward in a vocal recording:

```bash
ffmpeg -i <input> -af "afftdn=nf=-20,highpass=f=120,lowpass=f=8500,equalizer=f=1000:t=q:w=2:g=3,equalizer=f=2500:t=q:w=1:g=5,equalizer=f=4000:t=q:w=1:g=3,compand=attacks=0.05:decays=0.3:points=-80/-80|-30/-20|-15/-5|-5/-2|0/-2|20/-2" <output>
```

### Individual filters

```bash
# Normalize volume (loudness normalization, good for speech)
ffmpeg -i <input> -af loudnorm=I=-16:LRA=11:TP=-1.5 <output>

# Boost volume by factor (e.g. 2x)
ffmpeg -i <input> -af "volume=2.0" <output>

# Reduce background noise (FFT-based)
ffmpeg -i <input> -af "afftdn=nf=-20" <output>

# High-pass filter (remove rumble, good for voice)
ffmpeg -i <input> -af "highpass=f=200" <output>

# Low-pass filter (remove hiss)
ffmpeg -i <input> -af "lowpass=f=8000" <output>

# Compressor (even out loud/quiet parts)
ffmpeg -i <input> -af "compand=attacks=0.05:decays=0.3:points=-80/-80|-30/-20|-15/-5|-5/-2|0/-2|20/-2" <output>

# Equalizer (boost vocal presence at 2.5kHz)
ffmpeg -i <input> -af "equalizer=f=2500:t=q:w=1:g=5" <output>
```

## Spectrogram Generation

```bash
# Full spectrogram image (for vocal analysis)
ffmpeg -i <input> -lavfi "showspectrumpic=s=1800x600:mode=combined:color=rainbow:gain=4:scale=log" -frames:v 1 -update 1 spectrogram.png -y

# Valid color options: channel, intensity, rainbow, moreland
# Increase gain (e.g. gain=8) if the image is too dark
```

## Audio Concatenation

```bash
# Join multiple audio files (same codec)
# First create a file list:
#   file '/path/to/file1.ogg'
#   file '/path/to/file2.ogg'
ffmpeg -f concat -safe 0 -i filelist.txt -c copy <output>
```

## Telegram Delivery

- `.ogg` with Opus codec → sent as **voice bubble**
- `.mp3` → sent as **audio file**
- Use `MEDIA:/absolute/path/to/file` in your response
