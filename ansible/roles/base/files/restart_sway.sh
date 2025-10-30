#!/bin/bash
# Restart Sway service for streaminos user

echo "Restarting Sway service for streaminos user..."

sudo -u streaminos \
  XDG_RUNTIME_DIR=/run/user/1100 \
  systemctl --user restart sway.service

sleep 2

# Check status
sudo -u streaminos \
  XDG_RUNTIME_DIR=/run/user/1100 \
  systemctl --user status sway.service --no-pager

echo ""
echo "Checking outputs..."
sleep 1

/opt/streamin-scripts/list_displays.sh