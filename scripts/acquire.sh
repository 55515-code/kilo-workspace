#!/bin/bash
# Acquire source assets from Proton Drive or local sources
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

AUDIO_PATH="assets/source/audio/master.wav"
ARTWORK_PATH="assets/source/visual/artwork.png"

echo "📥 Acquiring source assets..."

if [ -f "$AUDIO_PATH" ] && [ -f "$ARTWORK_PATH" ]; then
    echo "✓ Assets already present"
    exit 0
fi

mkdir -p assets/source/audio assets/source/visual

if command -v python3 &> /dev/null; then
    echo "Attempting Proton Drive download..."
    if python3 scripts/acquire_proton_direct.py; then
        if [ -f "$AUDIO_PATH" ] && [ -f "$ARTWORK_PATH" ]; then
            echo "✓ Assets downloaded successfully"
        else
            echo "⚠ Download completed but assets not found at expected paths"
        fi
    else
        echo "⚠ Proton Drive download failed"
    fi
else
    echo "⚠ Python3 not available"
fi

if [ ! -f "$AUDIO_PATH" ]; then
    echo ""
    echo "❌ Audio file not found: $AUDIO_PATH"
    echo "Please place source assets manually:"
    echo "  - $AUDIO_PATH"
    echo "  - $ARTWORK_PATH"
    exit 1
fi

if [ ! -f "$ARTWORK_PATH" ]; then
    echo ""
    echo "❌ Artwork file not found: $ARTWORK_PATH"
    echo "Please place source assets manually:"
    echo "  - $AUDIO_PATH"
    echo "  - $ARTWORK_PATH"
    exit 1
fi

echo ""
echo "Verifying assets..."
if command -v ffprobe &> /dev/null; then
    if ffprobe -v error "$AUDIO_PATH" > /dev/null 2>&1; then
        echo "  ✓ Audio file valid"
    else
        echo "  ✗ Audio file invalid"
        exit 1
    fi
    if ffprobe -v error "$ARTWORK_PATH" > /dev/null 2>&1; then
        echo "  ✓ Artwork file valid"
    else
        echo "  ✗ Artwork file invalid"
        exit 1
    fi
else
    echo "  ⚠ ffprobe not available, skipping validation"
fi

echo ""
echo "✓ Assets acquired successfully"
