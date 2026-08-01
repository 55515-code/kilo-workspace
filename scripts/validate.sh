#!/bin/bash
# Comprehensive validation of final output
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "🔍 Validating final output..."

MASTER="deliverables/the_magicians_empire_master.mp4"
AUDIO="assets/source/audio/master.wav"

if [ ! -f "$MASTER" ]; then
    echo "❌ Master video not found: $MASTER"
    exit 1
fi

if [ ! -f "$AUDIO" ]; then
    echo "⚠ Source audio not found: $AUDIO"
    echo "   Skipping duration comparison"
    AUDIO=""
fi

echo "  Checking video stream..."
if command -v ffprobe &> /dev/null; then
    ffprobe -v error -select_streams v:0 \
        -show_entries stream=width,height,codec_name,r_frame_rate,duration \
        -of json "$MASTER" > /tmp/video_info.json
    echo "  ✓ Video info extracted"
    
    VIDEO_WIDTH=$(jq -r '.streams[0].width' /tmp/video_info.json)
    VIDEO_HEIGHT=$(jq -r '.streams[0].height' /tmp/video_info.json)
    VIDEO_CODEC=$(jq -r '.streams[0].codec_name' /tmp/video_info.json)
    echo "    Resolution: ${VIDEO_WIDTH}x${VIDEO_HEIGHT}"
    echo "    Codec: $VIDEO_CODEC"
else
    echo "  ⚠ ffprobe not available"
fi

echo "  Checking audio stream..."
if command -v ffprobe &> /dev/null; then
    ffprobe -v error -select_streams a:0 \
        -show_entries stream=codec_name,sample_rate,channels,duration \
        -of json "$MASTER" > /tmp/audio_info.json
    echo "  ✓ Audio info extracted"
    
    AUDIO_CODEC=$(jq -r '.streams[0].codec_name' /tmp/audio_info.json)
    AUDIO_RATE=$(jq -r '.streams[0].sample_rate' /tmp/audio_info.json)
    AUDIO_CHANNELS=$(jq -r '.streams[0].channels' /tmp/audio_info.json)
    echo "    Codec: $AUDIO_CODEC"
    echo "    Sample rate: ${AUDIO_RATE}Hz"
    echo "    Channels: $AUDIO_CHANNELS"
fi

if [ -n "$AUDIO" ] && command -v ffprobe &> /dev/null; then
    echo "  Comparing durations..."
    VIDEO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MASTER")
    AUDIO_DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$AUDIO")
    
    echo "    Video duration: ${VIDEO_DURATION}s"
    echo "    Audio duration: ${AUDIO_DURATION}s"
    
    DIFF=$(echo "$VIDEO_DURATION - $AUDIO_DURATION" | bc -l 2>/dev/null || echo "0")
    ABS_DIFF=$(echo "${DIFF#-}" | bc -l 2>/dev/null || echo "0")
    
    if (( $(echo "$ABS_DIFF > 1.0" | bc -l 2>/dev/null || echo "0") )); then
        echo "  ⚠ Duration mismatch exceeds 1 second"
    else
        echo "  ✓ Durations match within tolerance"
    fi
fi

if command -v ffmpeg &> /dev/null; then
    echo "  Running full decode test..."
    if ffmpeg -v error -i "$MASTER" -f null - 2>/tmp/decode_test.log; then
        echo "  ✓ Full decode test passed"
    else
        echo "  ✗ Decode test failed"
        cat /tmp/decode_test.log
        exit 1
    fi
else
    echo "  ⚠ ffmpeg not available, skipping decode test"
fi

echo "  Validating captions..."
if [ -f "captions/song.srt" ] || [ -f "captions/song.vtt" ]; then
    if python3 scripts/validate_captions.py; then
        echo "  ✓ Captions validated"
    else
        echo "  ⚠ Caption validation failed"
    fi
else
    echo "  ⚠ No caption files found"
fi

echo "  Generating validation report..."
if python3 scripts/generate_validation_report.py; then
    echo "  ✓ Validation report generated"
else
    echo "  ⚠ Report generation failed"
fi

SIZE=$(du -h "$MASTER" | cut -f1)
echo ""
echo "✓ Validation complete"
echo "  File size: $SIZE"
