#!/bin/bash
# Render final music video
set -e

echo "🎨 Rendering final video..."

if [ ! -f "assets/source/audio.wav" ] || [ ! -f "assets/source/artwork.png" ]; then
    echo "❌ Source assets not found"
    echo "   Run 'make acquire' first"
    exit 1
fi

mkdir -p renders/final

# This is a placeholder - actual implementation would use scene definitions
# For now, create a simple video with the artwork and audio
echo "  Compositing video..."
ffmpeg -y -loop 1 -i assets/source/artwork.png \
    -i assets/source/audio.wav \
    -c:v libx264 -preset medium -crf 18 \
    -c:a aac -b:a 320k \
    -pix_fmt yuv420p \
    -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" \
    -shortest \
    renders/final/music_video.mp4

echo "✓ Render complete"
echo "  Output: renders/final/music_video.mp4"
