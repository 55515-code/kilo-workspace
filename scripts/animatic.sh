#!/bin/bash
# Generate animatic (rough cut with placeholder visuals)
set -e

echo "🎬 Generating animatic..."

if [ ! -f "assets/source/audio.wav" ]; then
    echo "❌ Audio file not found: assets/source/audio.wav"
    echo "   Run 'make acquire' first"
    exit 1
fi

if [ ! -f "analysis/beat_info.json" ]; then
    echo "⚠ Beat analysis not found, running analyze first..."
    bash scripts/analyze.sh
fi

mkdir -p renders/animatic

# Create placeholder video with audio
echo "  Creating placeholder video..."
ffmpeg -y -f lavfi -i "color=c=black:s=1920x1080:d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 assets/source/audio.wav)" \
    -i assets/source/audio.wav \
    -c:v libx264 -preset ultrafast -crf 28 \
    -c:a aac -b:a 192k \
    -shortest \
    renders/animatic/rough_cut.mp4

echo "✓ Animatic complete"
echo "  Output: renders/animatic/rough_cut.mp4"
