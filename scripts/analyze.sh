#!/bin/bash
# Comprehensive audio analysis
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

AUDIO="assets/source/audio/master.wav"

if [ ! -f "$AUDIO" ]; then
    echo "❌ Audio file not found: $AUDIO"
    echo "   Run 'bash scripts/acquire.sh' first"
    exit 1
fi

mkdir -p analysis

echo "🎵 Analyzing audio..."

echo "  Extracting metadata..."
if command -v ffprobe &> /dev/null; then
    ffprobe -v quiet -print_format json -show_format -show_streams "$AUDIO" > analysis/audio_info.json
    echo "  ✓ Metadata saved to analysis/audio_info.json"
else
    echo "  ⚠ ffprobe not available, skipping metadata extraction"
fi

echo "  Running detailed audio analysis..."
if python3 scripts/analyze_audio_detailed.py; then
    echo "  ✓ Detailed analysis complete"
else
    echo "  ⚠ Detailed analysis failed, falling back to basic analysis"
    python3 -c "
import json
import sys
try:
    import librosa
    import numpy as np
    
    y, sr = librosa.load('$AUDIO', sr=None)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    
    result = {
        'tempo': float(tempo),
        'beat_frames': beats.tolist()[:50],
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
fi

echo ""
echo "✓ Analysis complete"
echo "  Output: analysis/"
