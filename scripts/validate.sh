#!/bin/bash
# Validate rendered output
set -e

echo "✓ Validating output..."

VIDEO="renders/final/music_video.mp4"

if [ ! -f "$VIDEO" ]; then
    echo "❌ Video not found: $VIDEO"
    echo "   Run 'make render' first"
    exit 1
fi

# Check video properties
echo "  Checking video properties..."
ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height,codec_name,duration \
    -of csv=p=0 "$VIDEO"

# Check audio
echo "  Checking audio stream..."
ffprobe -v error -select_streams a:0 \
    -show_entries stream=codec_name,sample_rate,channels \
    -of csv=p=0 "$VIDEO"

# File size
SIZE=$(du -h "$VIDEO" | cut -f1)
echo "  File size: $SIZE"

echo "✓ Validation complete"
