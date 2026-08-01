#!/bin/bash
# Generate low-resolution animatic for review
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🎬 Generating animatic..."

AUDIO="assets/source/audio/master.wav"
if [ ! -f "$AUDIO" ]; then
    echo "❌ Audio not found: $AUDIO"
    echo "   Run 'bash scripts/acquire.sh' first"
    exit 1
fi

if [ ! -f "analysis/section_map.json" ]; then
    echo "❌ Section map not found: analysis/section_map.json"
    echo "   Run 'bash scripts/analyze.sh' first"
    exit 1
fi

mkdir -p renders/proxy/frames review/keyframes

echo "  Rendering animatic frames..."
if ! python3 scripts/render_animatic.py; then
    echo "❌ Frame rendering failed"
    exit 1
fi

FRAME_COUNT=$(ls -1 renders/proxy/frames/frame_*.png 2>/dev/null | wc -l)
if [ "$FRAME_COUNT" -eq 0 ]; then
    echo "❌ No frames generated"
    exit 1
fi
echo "  ✓ Generated $FRAME_COUNT frames"

echo "  Assembling animatic video..."
if command -v ffmpeg &> /dev/null; then
    ffmpeg -y -framerate 24 -i renders/proxy/frames/frame_%06d.png \
        -i "$AUDIO" \
        -c:v libx264 -preset fast -crf 28 \
        -c:a aac -b:a 192k \
        -pix_fmt yuv420p \
        -shortest \
        renders/proxy/the_magicians_empire_animatic.mp4 2>/dev/null
    
    if [ -f "renders/proxy/the_magicians_empire_animatic.mp4" ]; then
        echo "  ✓ Animatic video created"
    else
        echo "  ⚠ Video assembly failed"
    fi
else
    echo "  ⚠ ffmpeg not available, skipping video assembly"
fi

echo "  Generating contact sheet..."
if python3 scripts/generate_contact_sheet.py; then
    echo "  ✓ Contact sheet created"
else
    echo "  ⚠ Contact sheet generation failed"
fi

echo ""
echo "✓ Animatic complete: renders/proxy/the_magicians_empire_animatic.mp4"
