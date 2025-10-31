# Gamescope Integration Plan

**Status**: Planned for implementation
**Priority**: HIGH
**Target Date**: 2025-11-01
**Current Version**: 1.5 (Sway only)
**Target Version**: 2.0 (Sway + Gamescope nested)

---

## Problem Statement

### Current Architecture (v1.5 - Working)

```
Sway (wlroots headless)
  └─ Steam Big Picture
      └─ Games (window launched)
          ❌ Sway doesn't auto-focus game windows
          ❌ Game window stays in background
          ❌ User has to manually focus with Alt+Tab or similar
```

**Issue**: When you launch a game from Steam Big Picture, Sway doesn't automatically focus on the game window. The game runs but stays in the background, requiring manual intervention to bring it to focus.

**Why this happens**: Sway is a tiling window manager designed for desktop use, not specifically optimized for gaming focus management. It doesn't have gaming-specific window rules to auto-focus newly launched game windows.

---

## Proposed Solution: Nested Gamescope

### Target Architecture (v2.0)

```
Sway (wlroots headless, base compositor)
  └─ Gamescope (nested micro-compositor, gaming-aware)
      └─ Steam Big Picture
          └─ Games
              ✅ Gamescope auto-focuses game windows
              ✅ Gaming-optimized window management
              ✅ VRR/FreeSync support built-in
```

**Benefits**:
- ✅ **Auto-focus**: Gamescope automatically focuses game windows when launched
- ✅ **Gaming-optimized**: Designed specifically for Steam and gaming
- ✅ **Performance**: Minimal overhead, designed by Valve for Steam Deck
- ✅ **Window management**: Handles fullscreen, borderless, and windowed games correctly
- ✅ **VRR support**: FreeSync/G-Sync compatible out-of-box

---

## Technical Implementation

### Architecture Layers

**Layer 1: Sway (Base Compositor)**
- Role: Wayland compositor with wlroots headless backend
- Purpose: Create virtual display for Sunshine to capture via wlr-screencopy
- Display: HEADLESS-1 (3840x2160@120Hz)
- Capture: Sunshine captures this layer via wlr protocol

**Layer 2: Gamescope (Nested Compositor)**
- Role: Micro-compositor running inside Sway as Wayland client
- Purpose: Gaming-specific window management and focus handling
- Backend: `--backend wayland` (nested in Sway's Wayland display)
- Display: Inherits resolution from Sunshine environment variables
- Mode: `--expose-wayland` for Steam compatibility

**Layer 3: Steam Big Picture**
- Runs inside gamescope's Wayland session
- Launches games as nested clients
- Gamescope manages focus automatically

**Layer 4: Games**
- Run as children of Steam
- Gamescope handles fullscreen, focus, and window management

---

## Implementation Steps

### 1. Install gamescope package

**File**: `ansible/roles/gamescope/defaults/main.yml`

```yaml
---
# gamescope role - Nested gaming compositor

gamescope_packages:
    - gamescope  # Valve's gaming micro-compositor
    - mesa       # Required for OpenGL/Vulkan
    - vulkan-radeon  # AMD Vulkan driver

gamescope_user: "{{ streamin_user }}"
gamescope_home: "{{ streamin_home }}"

# Default resolution (overridden by Sunshine env vars)
gamescope_default_width: 3840
gamescope_default_height: 2160
gamescope_default_fps: 120

# Gamescope flags for nested mode
gamescope_flags: "-f -e --expose-wayland --force-grab-cursor"
# -f: Fullscreen
# -e: Steam integration mode (better compatibility)
# --expose-wayland: Expose Wayland socket for Steam
# --force-grab-cursor: Proper cursor capture for streaming
```

### 2. Create gamescope launch wrapper

**File**: `ansible/roles/steam/files/launch-gamescope-steam.sh`

```bash
#!/bin/bash
# Gamescope Steam launcher for StreaminOS
# Launches Steam Big Picture within gamescope micro-compositor
# Resolution is passed dynamically from Sunshine via environment variables

# Get resolution from Sunshine environment or use defaults
WIDTH="${SUNSHINE_CLIENT_WIDTH:-3840}"
HEIGHT="${SUNSHINE_CLIENT_HEIGHT:-2160}"
FPS="${SUNSHINE_CLIENT_FPS:-120}"

# Verify we're in a Wayland session (required for nested gamescope)
if [ -z "$WAYLAND_DISPLAY" ]; then
    echo "ERROR: WAYLAND_DISPLAY not set. Gamescope requires Wayland backend."
    exit 1
fi

# Environment variables for optimal gaming
export DXVK_HUD=0
export ENABLE_VKBASALT=0
export SDL_VIDEODRIVER=wayland
export QT_QPA_PLATFORM=wayland

# Launch gamescope with Steam Big Picture
# Gamescope will auto-focus game windows when launched from Steam
exec gamescope \
    --backend wayland \
    -W "$WIDTH" \
    -H "$HEIGHT" \
    -r "$FPS" \
    -f \
    -e \
    --expose-wayland \
    --force-grab-cursor \
    -- steam -bigpicture
```

### 3. Update Sunshine apps.json

**File**: `ansible/roles/steam/templates/apps.json.j2`

Change the command from direct `steam -bigpicture` to the gamescope wrapper:

```json
{
  "apps": [
    {
      "name": "Steam Big Picture",
      "output": "",
      "cmd": "{{ streamin_home }}/.local/bin/launch-gamescope-steam.sh",
      "exclude-global-prep-cmd": "false",
      "elevated": "false",
      "auto-detach": "true",
      "wait-all": "false",
      "exit-timeout": "5"
    }
  ]
}
```

### 4. Verify Sway allows nested compositors

**File**: `ansible/roles/base/templates/sway-config.j2`

Ensure Sway configuration allows clients (gamescope) to create sub-surfaces:

```sway
# XWayland support (for games that need it)
xwayland enable

# Allow nested Wayland compositors
# No special configuration needed - Sway automatically allows Wayland clients
```

### 5. Test the integration

**Steps**:
1. Deploy changes: `ansible-playbook -i inventory/production.yml playbooks/install.yml --tags steam`
2. Restart Sunshine: `systemctl --user restart sunshine.service`
3. Connect via Moonlight
4. Launch "Steam Big Picture" (now running in gamescope)
5. Launch a game from Steam
6. **Verify**: Game window should automatically be in focus (no more Alt+Tab needed)

---

## Troubleshooting

### Gamescope fails to start

**Error**: `Failed to create Wayland display`

**Solution**: Ensure `WAYLAND_DISPLAY` is set in Sunshine service environment:

```ini
# In sunshine.service
Environment=WAYLAND_DISPLAY=wayland-1
```

### Games don't launch

**Error**: `Could not create Vulkan instance`

**Solution**: Ensure Mesa Vulkan drivers are installed:

```bash
pacman -S vulkan-radeon lib32-vulkan-radeon
```

### Resolution doesn't match client

**Symptom**: Black bars or stretched image

**Solution**: Verify Sunshine passes client resolution to wrapper:

```bash
# Check Sunshine environment variables in logs
journalctl --user -u sunshine.service | grep SUNSHINE_CLIENT
```

### Performance issues

**Symptom**: High CPU usage, stuttering

**Considerations**:
- Gamescope adds ~2-5% overhead (minimal)
- Check if RADV ACO compiler is enabled: `echo $RADV_PERFTEST`
- Monitor with: `htop` and `radeontop`

---

## Expected Performance

### CPU Usage (Ryzen 5 7600X)
- Sway: ~1-2%
- Gamescope: ~2-3%
- Sunshine (software encoding): ~30-40%
- **Total overhead**: ~35-45% (leaves 55-65% for games)

### GPU Usage (RX 7900 GRE)
- Sway rendering: Negligible (headless, no actual output)
- Gamescope: ~2-5% (compositing only)
- **Game rendering**: 90-95% (as expected)

### Memory
- Sway: ~50 MB
- Gamescope: ~30-50 MB
- Steam: ~300-500 MB
- **Total added overhead**: ~400-600 MB

### Latency
- No additional input latency expected
- Gamescope is designed for low-latency gaming (Steam Deck uses it)

---

## Alternative Approaches (Rejected)

### Pure Gamescope (No Sway)

**Architecture**: `Gamescope (DRM) → Steam → Games`

**Why rejected**:
- Gamescope's `--backend drm` requires physical monitor (headless server fails)
- Gamescope's `--backend headless` doesn't create DRM output for Sunshine KMS capture
- Would need Wayland capture instead of KMS (more complex, uncertain compatibility)

### Sway with Custom Window Rules

**Architecture**: `Sway + window focus rules → Steam → Games`

**Why rejected**:
- Sway's `for_window` rules can't reliably detect all game windows
- Games have inconsistent window properties (class, title, app_id)
- Maintenance nightmare (different rules for every game engine)
- Gamescope was literally designed to solve this problem

---

## Rollback Plan

If gamescope integration causes issues:

1. Restore previous Steam launcher (direct `steam -bigpicture`)
2. Update apps.json to remove gamescope wrapper
3. Restart Sunshine
4. Continue using current architecture (manual focus)

**Command**:
```bash
cd /home/noid/dev/StreaminOS
git stash  # Save gamescope changes
git checkout 652ad7af48348686ca8cdcbd3ad0fc9a63ff814d  # Revert to working commit
ansible-playbook -i ansible/inventory/production.yml ansible/playbooks/install.yml --tags steam,sunshine
```

---

## Success Criteria

- [x] Gamescope installs without errors
- [ ] Gamescope starts in nested Wayland mode within Sway
- [ ] Steam Big Picture runs inside gamescope
- [ ] Games launch from Steam
- [ ] **Games automatically gain focus** (no manual Alt+Tab)
- [ ] No performance degradation (≤5% overhead)
- [ ] Streaming quality unchanged (still captured by Sunshine wlr)
- [ ] No additional latency

---

## References

- **Gamescope GitHub**: https://github.com/ValveSoftware/gamescope
- **Gamescope Wiki**: https://github.com/ValveSoftware/gamescope/wiki
- **Arch Wiki - Gamescope**: https://wiki.archlinux.org/title/Gamescope
- **Steam Deck Compositor**: Gamescope is the compositor used on Steam Deck
- **Nested Compositor Docs**: https://wayland.freedesktop.org/docs/html/ch05.html

---

**Created**: 2025-10-31
**Status**: Pending implementation
**Estimated Time**: 2-3 hours
**Risk**: Low (easy rollback to working config)
