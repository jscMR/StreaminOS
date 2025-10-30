# StreaminOS Design Philosophy

## Core Concept: "Steam Deck at Home"

StreaminOS is designed around a single, focused vision: **providing a Steam Deck-like experience for home game streaming**. The system prioritizes simplicity, stability, and performance over feature complexity.

## Design Principles

### 1. Single-Purpose Interface

**Decision**: Only Steam Big Picture mode is exposed through Moonlight/Sunshine.

**Rationale**:
- Steam Big Picture provides a complete, controller-friendly gaming interface
- All game library management happens within Big Picture
- Users can browse, purchase, install, and launch games from one place
- Eliminates redundant interfaces and decision fatigue

**What This Means**:
- No separate desktop application in Moonlight
- No individual game shortcuts in Moonlight
- No automatic game detection and app generation
- Manual app curation via Sunshine web UI if truly needed (rare)

### 2. Simplicity Over Automation

**Decision**: Manual app management via Sunshine web UI instead of automatic game detection.

**Rationale**:
- Automatic game detection (steam-monitor) adds ~400 lines of code and system overhead
- inotify monitoring, VDF parsing, and cover image fetching consume resources
- Most users play a limited set of games and don't need 100+ apps in Moonlight
- Steam Big Picture already provides excellent game browsing and launching
- Manual curation is acceptable for the rare case of wanting individual game shortcuts

**What We Removed**:
- `steam-monitor` role and service (~400 lines)
- Python dependencies (vdf, inotify-simple)
- Filesystem monitoring overhead
- Cover image downloading and management
- Game state tracking and synchronization

**Benefits**:
- Reduced system complexity
- Lower resource usage
- Fewer potential failure points
- Easier to maintain and debug
- Cleaner user experience

### 3. Gamescope Over Traditional Compositor

**Decision**: Use Gamescope as the sole compositor instead of Sway/wlroots.

**Problem Solved**:
When using Sway, games launched from Steam Big Picture would stay "behind" the Big Picture interface - the window manager didn't understand the relationship between Steam and its games, causing focus issues.

**Rationale**:
- **Purpose-built**: Gamescope is Valve's micro-compositor designed specifically for gaming
- **Focus management**: Automatically handles Steam ↔ Game window transitions
- **No desktop needed**: StreaminOS is headless - nobody uses local display
- **Simpler stack**: One compositor instead of two (Sway + nested gamescope)
- **Better performance**: Gamescope optimized for game frame pacing and latency
- **Console OS architecture**: Aligns with "console at home" philosophy

**Architecture**:
```
Sunshine → Gamescope (DRM backend) → Steam Big Picture → Games
```

**What We Removed**:
- Sway compositor and configuration
- wlroots headless backend setup  
- wlr-randr resolution scripts
- Systemd Sway service
- Auto-login on tty1

**How Gamescope Works**:
- Launched **on-demand** by Sunshine (not persistent)
- Receives resolution dynamically via environment variables
- Uses DRM backend for direct hardware access
- Creates isolated Wayland sandbox for Steam
- Sunshine captures via KMS (Kernel Mode Setting)

**Benefits**:
- ✅ Fixes game window focus automatically
- ✅ Lower resource usage (one compositor vs two)
- ✅ No persistent compositor consuming resources when idle
- ✅ Upscaling support (FSR, NIS) available for future
- ✅ True "console OS" - no desktop environment bloat

**Trade-offs Considered**:
- ⚠️ Less flexibility than Sway (but we don't need it)
- ⚠️ Gamescope designed for AMD GPUs (perfect for RX 7900 GRE)
- ⚠️ No manual window management (we don't want it anyway)

### 4. SSH for Administration, Not Desktop

**Decision**: No desktop/terminal app in Moonlight for system management.

**Rationale**:
- StreaminOS is a headless server with SSH access
- Any administrative tasks can be performed via SSH
- A streaming desktop adds no value over SSH
- Reduces confusion about the system's purpose

**Administrative Access**:
```bash
# All management via SSH as admin user
ssh noid@streaminos.local

# Service user operations
sudo -u streaminos systemctl --user status sunshine.service
```

### 5. Essential Features Only

**What We Keep**:

1. **Dynamic Resolution Detection** (via Gamescope)
   - Gamescope receives client resolution from Sunshine environment variables
   - Automatically matches client display capabilities
   - No external scripts needed - handled by compositor

2. **Wake-on-LAN**
   - Core feature for on-demand server power-up
   - Enables true "console-like" experience
   - No overhead when not in use

3. **Auto-detach for Clean Sessions**
   - `auto_detach: true` for Steam Big Picture
   - Ensures processes close cleanly when streaming ends
   - Prevents resource leaks and hung processes

**What We Don't Need**:
- Multiple app configurations (Desktop, Steam, Big Picture, games)
- Automatic game detection and synchronization
- Cover image management
- Complex state tracking
- Persistent compositor service

## User Experience Flow

### Typical Usage

1. **Power on server** (Wake-on-LAN from Moonlight)
2. **Connect** via Moonlight (auto-discover `streaminos.local`)
3. **Launch** "Steam Big Picture" (only app in list)
4. **Browse** game library with controller
5. **Play** game
6. **Exit** Big Picture when done (auto-detach cleans up)

### Edge Cases

**Need an additional app?**
- Use Sunshine web UI at `http://streaminos.local:47990`
- Manually add the app with command and settings
- Acceptable for rare use cases

**Need to manage system?**
- SSH into server as admin user
- Use standard Linux tools and Ansible for changes

## Technical Benefits

### Performance
- Lower CPU usage (no background monitoring)
- Lower memory footprint (no Python processes, no state tracking)
- Fewer disk I/O operations (no cover downloads, no VDF parsing)

### Stability
- Fewer moving parts means fewer failure points
- No race conditions from filesystem monitoring
- No timeout issues from Sunshine reloads during streaming
- Simpler troubleshooting

### Maintainability
- ~400 fewer lines of code to maintain
- No Python dependencies to manage
- Fewer Ansible roles to keep in sync
- Clearer system architecture

## Comparison: Before vs After

### Before (Automated Approach)

```
Moonlight Apps:
├── Desktop (terminal)
├── Steam (client)
├── Steam Big Picture
├── Hades II
├── Baldur's Gate 3
├── [100+ detected games]
└── [Auto-updates on game install/uninstall]

Background Services:
├── steam-monitor.service (watching ~/.local/share/Steam)
├── Python process parsing VDF files
├── inotify monitoring filesystem events
└── Periodic Sunshine reloads

Maintenance:
├── Python package updates
├── VDF parsing compatibility
├── Cover image source stability
└── State synchronization logic
```

### After (Minimalist Approach)

```
Moonlight Apps:
└── Steam Big Picture

Background Services:
├── sunshine.service
└── [essential system services only]

Maintenance:
├── Ansible role updates
└── Steam/Sunshine updates

Manual Additions (rare):
└── Sunshine web UI (http://streaminos.local:47990)
```

## Future Considerations

### When Automation Makes Sense

Automatic game detection would be reconsidered if:
- Moonlight/Sunshine add native profile support (multi-user)
- User base grows significantly and manual curation becomes a pain point
- A lightweight, robust game detection method emerges
- Performance overhead becomes negligible on modern hardware

### Current Verdict

For the current use case (single-user home streaming server), the **minimalist approach is superior**:
- Simpler system architecture
- Lower resource usage
- Easier to understand and maintain
- Steam Big Picture already provides excellent UX
- Manual curation is acceptable for edge cases

## Conclusion

StreaminOS embraces the **"Steam Deck at home"** philosophy by:
1. Providing a single, focused interface (Big Picture)
2. Eliminating unnecessary automation overhead
3. Keeping the system simple and maintainable
4. Trusting Steam's built-in game management
5. Using SSH for system administration

This approach delivers a **robust, performant, and low-maintenance** game streaming experience that focuses on what matters: **playing games**.

## Architecture Evolution

### Version 1.0: Sway + wlroots (Initial Implementation)

The initial architecture used Sway as a traditional Wayland compositor:
- **Compositor**: Sway with wlroots headless backend
- **Capture**: wlr capture method in Sunshine
- **Resolution**: wlr-randr scripts for dynamic adjustment
- **Auto-start**: Sway service on tty1 auto-login

**Problem Discovered**: Games launched from Steam Big Picture stayed "behind" the interface. Sway's window management couldn't understand the Steam ↔ Game relationship, causing focus issues.

### Version 2.0: Gamescope Pure (Console OS)

Current architecture using Gamescope as the sole compositor:
- **Compositor**: Gamescope (on-demand, DRM backend)
- **Capture**: KMS (Kernel Mode Setting) in Sunshine
- **Resolution**: Gamescope command-line flags (dynamic)
- **Auto-start**: None - launched by Sunshine when client connects

**Key Changes**:
```
REMOVED:
- ansible/roles/base/ (entire Sway role)
- Sway systemd service
- wlroots configuration
- wlr-randr scripts
- Auto-login on tty1
- ~500 lines of code

ADDED:
- ansible/roles/gamescope/
- Gamescope launcher script
- KMS capture configuration
- On-demand compositor architecture
- ~200 lines of code
```

**Migration Path**:
```bash
# 1. Clean existing Sway installation
ansible-playbook -i inventory/production.yml playbooks/migrate-to-gamescope.yml

# 2. Deploy new architecture
ansible-playbook -i inventory/production.yml playbooks/install.yml
```

**Results**:
- ✅ Game window focus works automatically
- ✅ 60% less code to maintain
- ✅ Lower idle resource usage (no persistent compositor)
- ✅ True console OS architecture
- ✅ Aligns perfectly with "Steam Deck at home" philosophy

---

**Last Updated**: October 2025  
**Version**: 2.0 (Console OS - Gamescope Architecture)
