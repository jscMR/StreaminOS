#!/bin/bash
# Steam launcher wrapper for StreaminOS
# Ensures proper environment for Steam in headless/Wayland setup

# Set environment variables for Steam
export DISPLAY=:0
export WAYLAND_DISPLAY=wayland-1
export XDG_RUNTIME_DIR="/run/user/1100"
export XDG_SESSION_TYPE=wayland
export SDL_VIDEODRIVER=wayland
export QT_QPA_PLATFORM=wayland

# Steam-specific variables
export STEAM_RUNTIME=1
export STEAM_RUNTIME_PREFER_HOST_LIBRARIES=0
export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/1100/bus"

# Disable problematic Steam features in headless
export STEAM_DISABLE_BROWSER_TRACKER=1

# Launch Steam
exec /usr/bin/steam "$@"
