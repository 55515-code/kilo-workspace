#!/bin/bash
# Complete music video production pipeline
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

PIPELINE_LOG="pipeline_run_$(date +%Y%m%d_%H%M%S).log"
LOCK_FILE="/tmp/pipeline.lock"
START_TIME=$(date +%s)

cleanup() {
    local exit_code=$?
    rm -f "$LOCK_FILE"
    if [ $exit_code -ne 0 ]; then
        echo ""
        echo "❌ Pipeline failed at step: $CURRENT_STEP"
        echo "   Check log: $PIPELINE_LOG"
        echo "   Cleaning up temporary files..."
        rm -rf renders/proxy/frames/*.tmp 2>/dev/null || true
        rm -rf /tmp/pipeline_* 2>/dev/null || true
    fi
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))
    echo "   Total time: $((elapsed / 60))m $((elapsed % 60))s"
}

trap cleanup EXIT

if [ -f "$LOCK_FILE" ]; then
    echo "❌ Another pipeline instance is running (lock: $LOCK_FILE)"
    exit 1
fi
echo $$ > "$LOCK_FILE"

CURRENT_STEP="initialization"

echo "🎬 The Magician's Empire - Full Production Pipeline"
echo "=================================================="
echo "   Started: $(date)"
echo "   Log: $PIPELINE_LOG"
echo ""

exec > >(tee -a "$PIPELINE_LOG") 2>&1

run_step() {
    local step_num=$1
    local step_name=$2
    local step_cmd=$3
    CURRENT_STEP="$step_name"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Step $step_num: $step_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    local step_start=$(date +%s)
    if eval "$step_cmd"; then
        local step_end=$(date +%s)
        local step_elapsed=$((step_end - step_start))
        echo "  ✓ $step_name complete ($((step_elapsed / 60))m $((step_elapsed % 60))s)"
    else
        echo "  ✗ $step_name FAILED"
        exit 1
    fi
}

run_step 1 "Environment setup" "bash scripts/setup.sh"
run_step 2 "Acquiring source assets" "bash scripts/acquire.sh"
run_step 3 "Analyzing audio" "bash scripts/analyze.sh"
run_step 4 "Generating visual assets" "python3 src/texture_generator.py"
run_step 5 "Rendering animatic" "bash scripts/animatic.sh"
run_step 6 "Rendering final video" "python3 src/video_renderer.py"
run_step 7 "Validating output" "bash scripts/validate.sh"
run_step 8 "Exporting social media derivatives" "bash scripts/export_derivatives.sh"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Production complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "   Master: deliverables/the_magicians_empire_master.mp4"
echo "   Social: deliverables/social/"
echo "   Report: deliverables/validation_report.md"
