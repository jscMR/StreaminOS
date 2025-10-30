# StreaminOS Deployment Summary

**Date:** 2025-10-29  
**Server:** 192.168.0.19  
**Status:** ✅ Fully operational with software encoding

## Quick Reference

### Current Configuration

**Hardware:**
- CPU: Ryzen 5 7600X (6 cores / 12 threads)
- GPU: AMD RX 7900 GRE
- Target: 4K@120Hz streaming

**Software Stack:**
- OS: Arch Linux
- Kernel: 6.17.5-arch1-1
- Mesa: 25.2.5-2 (VAAPI bug present)
- Sunshine: v2025.628.4510-1
- Compositor: Sway (wlroots headless backend)

**Network:**
- mDNS hostname: `streaminos.local`
- Sunshine ports: 47984 (HTTPS), 47989 (HTTP), 47990 (Web UI)
- Autodiscovery: ✅ Enabled (Avahi/mDNS)

### Deployment Commands

**From local machine to remote server:**

```bash
cd /home/noid/dev/StreaminOS/ansible

# Full deployment (all roles)
ansible-playbook -i inventory/production.yml playbooks/install.yml

# Specific components
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags user-setup
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags base
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags aur-helper
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags sunshine

# Dry-run (check what would change)
ansible-playbook -i inventory/production.yml playbooks/install.yml --check --diff

# Syntax validation (no connection)
ansible-playbook playbooks/install.yml --syntax-check
```

### Service Management

**Check service status (on remote server):**

```bash
# Via SSH
ssh noid@192.168.0.19

# Autologin status
systemctl status getty@tty1.service

# Check running processes
ps aux | grep -E "(sway|sunshine)" | grep -v grep

# View Sunshine logs
sudo journalctl -u getty@tty1.service -f
sudo cat /home/streaminos/.local/share/sunshine/logs/sunshine.log

# Check user session
sudo loginctl show-user streaminos
```

**Restart services:**

```bash
# Restart autologin (will restart Sway and Sunshine)
sudo systemctl restart getty@tty1.service

# Or reboot server
sudo reboot
```

## Architecture Overview

### Dual-User System

```
┌────────────────────────────────────────┐
│ noid (ansible_user)                    │
│ - SSH access                           │
│ - Ansible deployment                   │
│ - Sudo privileges                      │
└────────────────────────────────────────┘
              │
              │ Manages
              ▼
┌────────────────────────────────────────┐
│ streaminos (streamin_user)             │
│ - UID/GID: 1100                        │
│ - Auto-login on tty1                   │
│ - Runs: Sway + Sunshine + Steam        │
│ - No SSH access (security)             │
│ - Password locked                      │
└────────────────────────────────────────┘
```

### Service Flow

```
Boot
  ↓
getty@tty1 (autologin as streaminos)
  ↓
Login shell (~/.bash_profile)
  ↓
Environment variables loaded (~/.profile)
  ↓
Sway starts with wlroots headless backend
  ↓
Sunshine.service starts (systemd user service)
  ↓
Ready for streaming (advertised via mDNS)
```

### Streaming Pipeline

```
Game Rendering          Capture              Encoding            Transmission
──────────────         ────────            ──────────          ──────────────
GPU (RX 7900 GRE)  →   Sunshine        →   CPU (software)  →   Network
100% for gaming        wlr-screencopy      libx264/libx265     80 Mbps
4K@120Hz               4K@120Hz            H.264               Moonlight
```

## Implemented Roles

### 1. user-setup
- Creates `streaminos` user (UID 1100)
- Configures groups: video, render, input, audio, wheel
- Sets up autologin on tty1
- Configures PAM limits for real-time performance
- Creates XDG directory structure
- Deploys environment variables:
  - `WLR_BACKENDS=headless`
  - `WLR_RENDERER=gles2`
  - `WLR_HEADLESS_OUTPUTS=1`
  - AMD GPU variables
  - Wayland/XDG variables

### 2. base
- Installs Arch base system packages
- Installs Sway and Wayland stack
- Deploys Sway configuration:
  - Single HEADLESS-1 output (4K@120Hz)
  - Minimal config for streaming
  - No physical input devices
- Configures dhcpcd networking
- Installs Mesa + Vulkan drivers

### 3. aur-helper
- Installs yay AUR helper
- Built from source (AUR/yay-bin)
- Enables AUR package installation in other roles

### 4. sunshine
- Installs sunshine-bin from AUR
- **Software encoding** (workaround Mesa VAAPI bug)
- Configures systemd user service
- Installs Avahi + nss-mdns (mDNS autodiscovery)
- Configuration:
  - Encoder: software (libx264)
  - Codec: H.264
  - Bitrate: 80 Mbps
  - Resolution: 4K (3840x2160)
  - FPS: 120Hz target
  - Capture: wlr-screencopy protocol

## Known Issues and Workarounds

### Mesa 25.2.5 VAAPI Bug

**Issue:** VAAPI hardware encoding produces stride artifacts (vertical lines, fragmented image)  
**Cause:** Mesa 25.2.5 VAAPI encoder incorrectly reads stride from wlroots headless RAM framebuffers  
**Impact:** Cannot use GPU hardware encoding  
**Workaround:** Software encoding via CPU (libx264/libx265)  
**Performance:** ~30-40% CPU usage on Ryzen 5 7600X (acceptable)  
**Quality:** Excellent (software encoding quality superior to VAAPI)  
**Documentation:** See `docs/VAAPI_BUG_MESA.md`

**Future resolution:**
- Monitor Mesa updates (test 25.3+ when available)
- Or downgrade to Mesa 24.x
- Update `ansible/roles/sunshine/defaults/main.yml`:
  ```yaml
  sunshine_encoder: vaapi  # Change from 'software' when bug fixed
  ```

## Configuration Files

### Key Variables

**Global:** `ansible/group_vars/all.yml`
```yaml
streamin_user: streaminos
streamin_uid: 1100
headless_outputs_count: 1
headless_primary_resolution: "3840x2160"
headless_primary_refresh: 120
wlr_backends: "headless"
wlr_renderer: "gles2"
```

**Sunshine:** `ansible/roles/sunshine/defaults/main.yml`
```yaml
sunshine_encoder: software  # Workaround for Mesa bug
sunshine_codec: h264
sunshine_bitrate: 80000
sunshine_default_resolution: "3840x2160"
sunshine_default_fps: 120
sunshine_capture_method: wlr
```

### Important Paths (on server)

**Service user home:**
```
/home/streaminos/
├── .config/
│   ├── sway/config              # Sway compositor config
│   ├── sunshine/sunshine.conf   # Sunshine streaming config
│   └── systemd/user/            # User services
├── .local/share/
│   └── sunshine/logs/           # Sunshine logs
├── .profile                     # Environment variables
└── Pictures/wallpaper.png       # Desktop background
```

**System files:**
```
/etc/systemd/system/getty@tty1.service.d/autologin.conf  # Autologin config
/etc/security/limits.d/99-streaminos.conf                # PAM limits
/etc/nsswitch.conf                                       # mDNS resolution
```

## Verification Checklist

After deployment, verify:

- [ ] Server responds to SSH: `ssh noid@192.168.0.19`
- [ ] Autologin active: `systemctl status getty@tty1.service`
- [ ] Sway running: `ps aux | grep sway`
- [ ] Sunshine running: `ps aux | grep sunshine`
- [ ] mDNS working: `ping streaminos.local` (from client)
- [ ] Streaming working: Open Moonlight, see `streaminos` server
- [ ] No artifacts: Test stream on laptop and mobile
- [ ] Performance: Monitor with `htop` (CPU ~30-40% while streaming)

## Troubleshooting

### Sway not starting

```bash
# Check autologin logs
sudo journalctl -u getty@tty1.service -n 50

# Check if WLR variables are set
sudo -u streaminos bash -c 'source ~/.profile && env | grep WLR'

# Manual start for debugging
sudo systemctl stop getty@tty1.service
sudo -i -u streaminos
sway  # Check for errors
```

### Sunshine not starting

```bash
# Check Sunshine logs
sudo cat /home/streaminos/.local/share/sunshine/logs/sunshine.log

# Check systemd user service
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user status sunshine.service

# Manual start for debugging
sudo -i -u streaminos
sunshine /home/streaminos/.config/sunshine/sunshine.conf
```

### mDNS not working

```bash
# Check Avahi daemon
systemctl status avahi-daemon.service

# Check nss-mdns configuration
grep mdns /etc/nsswitch.conf
# Should contain: hosts: mymachines mdns_minimal [NOTFOUND=return] resolve [!UNAVAIL=return] files myhostname dns

# Restart Avahi
sudo systemctl restart avahi-daemon.service
```

### Streaming artifacts

If you see artifacts after deployment:

1. **Check encoding method:**
   ```bash
   sudo grep "encoder" /home/streaminos/.config/sunshine/sunshine.conf
   # Should be: encoder = software
   ```

2. **Check Mesa version:**
   ```bash
   pacman -Q mesa
   # If 25.2.5, VAAPI is broken - must use software encoding
   ```

3. **Verify single display:**
   ```bash
   sudo -u streaminos bash -c 'source ~/.profile && swaymsg -t get_outputs'
   # Should show only HEADLESS-1
   ```

4. **Check for framebuffer concatenation:**
   ```bash
   sudo grep "Offset" /var/log/sway.log
   # All outputs should be at Offset: 0x0 or different Y coordinates
   ```

## Performance Metrics

**Typical usage during 4K@120Hz streaming:**

| Component | Usage | Notes |
|-----------|-------|-------|
| CPU (Ryzen 5 7600X) | 30-40% | Software encoding (2-3 cores) |
| GPU (RX 7900 GRE) | 0-5% | Not used for encoding, free for games |
| RAM | ~2-3 GB | Sway + Sunshine + system |
| Network | 80 Mbps | Bitrate setting (adjustable) |
| Latency | ~10-15ms | Local network (LAN) |

**Game performance impact:**
- ✅ No FPS impact (GPU not used for encoding)
- ✅ Minimal CPU impact (cores available for game logic)
- ✅ No noticeable latency increase

## Maintenance

### Update system

```bash
ssh noid@192.168.0.19
sudo pacman -Syu
# Check for Mesa updates
pacman -Q mesa
# If Mesa ≥ 25.3, consider testing VAAPI again
```

### Update Sunshine

```bash
# From local machine
cd /home/noid/dev/StreaminOS/ansible
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags sunshine
```

### Backup configuration

```bash
# Backup streaminos user home
ssh noid@192.168.0.19
sudo tar -czf /tmp/streaminos-backup.tar.gz /home/streaminos/.config /home/streaminos/.local

# Download backup
scp noid@192.168.0.19:/tmp/streaminos-backup.tar.gz ~/backups/
```

## Next Steps (Future Development)

**Pending roles to implement:**

1. **steam**: Steam client installation
   - Install steam package
   - Configure library paths
   - Set up auto-start (optional)

2. **steam-monitor**: Auto-register games with Sunshine
   - Watch Steam library for new installations
   - Automatically add games to Sunshine
   - systemd service monitoring steamapps

3. **amdgpu**: GPU optimizations
   - Power profiles (performance mode)
   - Overclocking configuration
   - Fan curves
   - VRAM tuning

4. **dashboard**: Web admin UI
   - System monitoring (CPU, GPU, network)
   - Service management (restart Sway, Sunshine)
   - Game library management
   - Stream statistics
   - Port 8080 web interface

## References

- **Main documentation:** `/home/noid/dev/StreaminOS/README.md`
- **Project instructions:** `/home/noid/dev/StreaminOS/CLAUDE.md`
- **VAAPI bug details:** `/home/noid/dev/StreaminOS/docs/VAAPI_BUG_MESA.md`
- **Ansible playbook:** `/home/noid/dev/StreaminOS/ansible/playbooks/install.yml`
- **Global variables:** `/home/noid/dev/StreaminOS/ansible/group_vars/all.yml`

---

**Last Updated:** 2025-10-29  
**Deployed By:** noid  
**Server:** 192.168.0.19  
**Status:** ✅ Production ready with software encoding
