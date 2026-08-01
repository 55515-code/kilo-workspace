#!/bin/bash
# Analyze audio structure (beats, tempo, segments)
set -e

echo "🎵 Analyzing audio structure..."

if [ ! -f "assets/source/audio.wav" ]; then
    echo "❌ Audio file not found: assets/source/audio.wav"
    echo "   Run 'make acquire' first"
    exit 1
fi

mkdir -p analysis

# Extract audio info
echo "  Extracting audio metadata..."
ffprobe -v quiet -print_format json -show_format -show_streams assets/source/audio.wav > analysis/audio_info.json

# Beat detection (placeholder - would use librosa)
echo "  Detecting beats and tempo..."
python3 -c "
import json
import sys
try:
    import librosa
    import numpy as np
    
    y, sr = librosa.load('assets/source/audio.wav', sr=None)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    
    result = {
        'tempo': float(tempo),
        'beat_frames': beats.tolist()[:50],  # First 50 beats
        'duration': float(len(y) / sr),
        'sample_rate': int(sr)
    }
    
    with open('analysis/beat_info.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f'  ✓ Tempo: {tempo:.1f} BPM')
    print(f'  ✓ Duration: {result[\"duration\"]:.1f}s')
    print(f'  ✓ Beats detected: {len(beats)}')
except ImportError:
    print('  ⚠ librosa not available, skipping beat analysis')
    sys.exit(0)
"

echo "✓ Analysis complete"
echo "  Output: analysis/"
