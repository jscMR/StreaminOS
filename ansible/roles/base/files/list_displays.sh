#!/bin/bash
# List all Sway outputs (physical and virtual)

echo "===================================="
echo "Sway Outputs Status"
echo "===================================="

# Check if Sway is running
if ! pgrep -x sway > /dev/null; then
    echo "ERROR: Sway is not running"
    exit 1
fi

# Find Sway socket
SWAY_SOCK=$(find /run/user/*/sway-ipc.*.sock 2>/dev/null | head -1)

if [ -z "$SWAY_SOCK" ]; then
    echo "ERROR: Cannot find Sway socket"
    exit 1
fi

# Get outputs
export SWAYSOCK="$SWAY_SOCK"
swaymsg -t get_outputs -p

echo ""
echo "WLR Backend Configuration:"
ps aux | grep sway | grep -o 'WLR_BACKENDS=[^ ]*' || echo "  Not set in process args"

echo ""
echo "Environment Variables:"
echo "  WLR_BACKENDS: ${WLR_BACKENDS:-not set}"
echo "  WLR_HEADLESS_OUTPUTS: ${WLR_HEADLESS_OUTPUTS:-not set}"