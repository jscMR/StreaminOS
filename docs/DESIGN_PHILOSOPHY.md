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

### 3. SSH for Administration, Not Desktop

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

### 4. Essential Features Only

**What We Keep**:

1. **Dynamic Resolution Detection** (`global_prep_cmd`)
   - Essential for matching client display capabilities
   - Improves streaming quality and performance
   - Automatic, transparent, no user intervention needed

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

---

**Last Updated**: October 2025  
**Version**: 1.0 (Minimalist Architecture)
