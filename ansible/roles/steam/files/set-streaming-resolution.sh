#!/bin/bash
# Sunshine Dynamic Resolution Script for StreaminOS
# Changes wlroots headless display resolution based on Moonlight client request
#
# Usage: set-streaming-resolution.sh <width> <height> <fps>
# Called automatically by Sunshine prep-cmd with environment variables

set -e

WIDTH="${1:-1920}"
HEIGHT="${2:-1080}"
FPS="${3:-60}"

DEFAULT_WIDTH="1920"
DEFAULT_HEIGHT="1080"
DEFAULT_FPS="60"

LOG_TAG="[StreaminOS-Resolution]"

# Logging function
log() {
    echo "$LOG_TAG $1" >&2
}

# Validate inputs
if ! [[ "$WIDTH" =~ ^[0-9]+$ ]] || ! [[ "$HEIGHT" =~ ^[0-9]+$ ]] || ! [[ "$FPS" =~ ^[0-9]+$ ]]; then
    log "ERROR: Invalid resolution parameters: ${WIDTH}x${HEIGHT}@${FPS}"
    log "Using default: ${DEFAULT_WIDTH}x${DEFAULT_HEIGHT}@${DEFAULT_FPS}"
    WIDTH=$DEFAULT_WIDTH
    HEIGHT=$DEFAULT_HEIGHT
    FPS=$DEFAULT_FPS
fi

log "Requested resolution: ${WIDTH}x${HEIGHT}@${FPS}Hz"

# Set environment for wlr-randr
export XDG_RUNTIME_DIR="/run/user/1100"
export WAYLAND_DISPLAY="wayland-1"

# Check if wlr-randr is available
if ! command -v wlr-randr &> /dev/null; then
    log "ERROR: wlr-randr not found in PATH"
    exit 1
fi

# Get available modes
AVAILABLE_MODES=$(wlr-randr 2>/dev/null || echo "")

if [ -z "$AVAILABLE_MODES" ]; then
    log "ERROR: Cannot communicate with Wayland display"
    exit 1
fi

# Check if requested resolution is available
REQUESTED_MODE="${WIDTH}x${HEIGHT} px, ${FPS}"
if echo "$AVAILABLE_MODES" | grep -q "$REQUESTED_MODE"; then
    log "Resolution ${WIDTH}x${HEIGHT}@${FPS}Hz is available - applying..."
    wlr-randr --output Virtual-1 --mode "${WIDTH}x${HEIGHT}@${FPS}"

    if [ $? -eq 0 ]; then
        log "SUCCESS: Resolution changed to ${WIDTH}x${HEIGHT}@${FPS}Hz"
    else
        log "ERROR: Failed to apply resolution"
        exit 1
    fi
else
    log "WARNING: Resolution ${WIDTH}x${HEIGHT}@${FPS}Hz not available"

    # Try without exact FPS match (find closest)
    CLOSEST_MODE=$(echo "$AVAILABLE_MODES" | grep "${WIDTH}x${HEIGHT}" | head -n 1)

    if [ -n "$CLOSEST_MODE" ]; then
        # Extract FPS from closest mode
        CLOSEST_FPS=$(echo "$CLOSEST_MODE" | grep -oP '\d+\.\d+(?= Hz)' | cut -d. -f1)
        log "Using closest available: ${WIDTH}x${HEIGHT}@${CLOSEST_FPS}Hz"
        wlr-randr --output Virtual-1 --mode "${WIDTH}x${HEIGHT}@${CLOSEST_FPS}"

        if [ $? -eq 0 ]; then
            log "SUCCESS: Applied closest resolution ${WIDTH}x${HEIGHT}@${CLOSEST_FPS}Hz"
        else
            log "ERROR: Failed to apply closest resolution"
            exit 1
        fi
    else
        log "WARNING: No ${WIDTH}x${HEIGHT} mode available at all"
        log "Falling back to default: ${DEFAULT_WIDTH}x${DEFAULT_HEIGHT}@${DEFAULT_FPS}Hz"
        wlr-randr --output Virtual-1 --mode "${DEFAULT_WIDTH}x${DEFAULT_HEIGHT}@${DEFAULT_FPS}"

        if [ $? -eq 0 ]; then
            log "SUCCESS: Fallback to default resolution"
        else
            log "ERROR: Even fallback failed!"
            exit 1
        fi
    fi
fi

log "Resolution change complete"
exit 0
