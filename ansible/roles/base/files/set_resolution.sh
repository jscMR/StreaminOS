#!/bin/bash
# Change resolution of a headless output dynamically

if [ $# -lt 2 ]; then
    echo "Usage: $0 <output> <resolution>[@refresh_rate]"
    echo ""
    echo "Examples:"
    echo "  $0 HEADLESS-1 3840x2160@120Hz"
    echo "  $0 HEADLESS-2 1920x1080@120Hz"
    echo "  $0 HEADLESS-1 2560x1440@144Hz"
    exit 1
fi

OUTPUT="$1"
MODE="$2"

# Find Sway socket
SWAY_SOCK=$(find /run/user/*/sway-ipc.*.sock 2>/dev/null | head -1)

if [ -z "$SWAY_SOCK" ]; then
    echo "ERROR: Cannot find Sway socket"
    exit 1
fi

export SWAYSOCK="$SWAY_SOCK"

echo "Setting $OUTPUT to mode $MODE..."
swaymsg output "$OUTPUT" mode "$MODE"

if [ $? -eq 0 ]; then
    echo "✓ Resolution changed successfully"
    echo ""
    swaymsg -t get_outputs | grep -A 5 "$OUTPUT"
else
    echo "✗ Failed to change resolution"
    exit 1
fi