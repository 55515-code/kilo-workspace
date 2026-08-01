#!/bin/bash
# Export social media derivatives
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "📱 Exporting social media derivatives..."

MASTER="deliverables/the_magicians_empire_master.mp4"
if [ ! -f "$MASTER" ]; then
    echo "❌ Master video not found: $MASTER"
    exit 1
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not available"
    exit 1
fi

mkdir -p deliverables/social

echo "  Creating 1080p web copy..."
ffmpeg -y -i "$MASTER" \
    -c:v libx264 -preset medium -crf 23 \
    -c:a aac -b:a 192k \
    -movflags +faststart \
    deliverables/social/the_magicians_empire_1080p_web.mp4 2>/dev/null
echo "  ✓ 1080p web copy created"

echo "  Creating 720p review copy..."
ffmpeg -y -i "$MASTER" \
    -vf "scale=1280:720" \
    -c:v libx264 -preset fast -crf 28 \
    -c:a aac -b:a 128k \
    deliverables/social/the_magicians_empire_720p_review.mp4 2>/dev/null
echo "  ✓ 720p review copy created"

echo "  Creating vertical excerpts..."

echo "    60-second hook..."
ffmpeg -y -i "$MASTER" \
    -ss 110 -t 60 \
    -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920" \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 192k \
    deliverables/social/hook_60s_vertical.mp4 2>/dev/null
echo "    ✓ 60s vertical created"

echo "    30-second excerpt..."
ffmpeg -y -i "$MASTER" \
    -ss 120 -t 30 \
    -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920" \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 192k \
    deliverables/social/hook_30s_vertical.mp4 2>/dev/null
echo "    ✓ 30s vertical created"

echo "    15-second excerpt..."
ffmpeg -y -i "$MASTER" \
    -ss 125 -t 15 \
    -vf "crop=ih*9/16:ih:(iw-ih*9/16)/2:0,scale=1080:1920" \
    -c:v libx264 -preset fast -crf 23 \
    -c:a aac -b:a 192k \
    deliverables/social/hook_15s_vertical.mp4 2>/dev/null
echo "    ✓ 15s vertical created"

echo ""
echo "✓ Derivatives exported to deliverables/social/"
ls -lh deliverables/social/*.mp4 | awk '{print "  " $9 " (" $5 ")"}'
