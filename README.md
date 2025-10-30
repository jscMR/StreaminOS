# StreaminOS

> Arch-based Linux mini distribution optimized for home game streaming with Sunshine

StreaminOS is a project to create a self-hosted game streaming server, similar to Amazon Luna but running on your own hardware at home. It uses Sunshine for streaming, on-demand virtual displays, and automatic Steam game management.

## Features

- 🎮 **Game streaming** with Sunshine
- 🖥️ **On-demand virtual displays** with evdi
- 🎯 **Auto-detection** of Steam games and automatic registration in Sunshine
- ⚡ **Optimized for AMD GPU** (RX 7900 GRE)
- 🌊 **Wayland compositor** with Sway for maximum performance
- 📊 **Web dashboard** for administration
- 🔧 **Fully reproducible** with Ansible

## Recommended Hardware

- **CPU**: Ryzen 5 7600X or higher
- **GPU**: AMD RX 7900 GRE (configurable for other AMD GPUs)
- **RAM**: 32GB recommended
- **Network**: Gigabit Ethernet or higher

## Prerequisites

1. **Base Arch Linux installation**
   ```bash
   # Minimum required packages
   pacstrap /mnt base base-devel git dhcpcd
   ```

2. **User with sudo privileges**
   ```bash
   # Create user and add to wheel group
   useradd -m -G wheel your_user
   passwd your_user

   # Enable sudo for wheel group
   visudo  # Uncomment: %wheel ALL=(ALL:ALL) ALL
   ```

3. **Git installed**
   ```bash
   pacman -S git
   ```

## Working with Existing Installations

StreaminOS is designed to work with **existing Arch Linux installations**. You don't need a fresh install!

### What happens to your existing setup?

✅ **Packages**:
- Already installed packages are left untouched
- Only missing packages are installed
- No conflicts or breakage

✅ **Users**:
- Your existing user and SSH setup remain unchanged
- No user creation or sudo modifications

⚠️ **Sway Configuration**:
- **Will be overwritten** with StreaminOS optimized config
- Original config is automatically backed up with timestamp
- Find backups at `~/.config/sway/config.<timestamp>`

### Preview changes before applying

```bash
# See exactly what would change (without applying)
ansible-playbook -i inventory/production.yml playbooks/install.yml --check --diff
```

### Requirements for existing installations

- Arch Linux (verified at runtime)
- User with sudo privileges (no password prompt for sudo recommended)
- SSH access configured
- Python 3 installed (`pacman -S python`)

## Quick Installation

### Option A: Remote Installation (Recommended)

Deploy from your local development machine to a remote bare metal server:

#### 1. Clone the repository (on your local machine)

```bash
git clone https://github.com/your-user/StreaminOS.git
cd StreaminOS
```

#### 2. Install Ansible (on your local machine)

```bash
# For Arch Linux
sudo pacman -S ansible

# For Ubuntu/Debian
sudo apt install ansible

# For macOS
brew install ansible
```

#### 3. Configure remote server inventory

```bash
cd ansible/inventory

# Edit production.yml with your server details
vim production.yml
```

Update the following values:
- `ansible_host`: Your server's IP address
- `ansible_user`: Your SSH username on the server

#### 4. Test connectivity

```bash
ansible -i inventory/production.yml streamin_servers -m ping
```

#### 5. Run installation

```bash
# From ansible/ directory
ansible-playbook -i inventory/production.yml playbooks/install.yml

# With sudo password prompt (if needed)
ansible-playbook -i inventory/production.yml playbooks/install.yml --ask-become-pass
```

### Option B: Local Installation

Install directly on the target machine:

#### 1. Clone the repository

```bash
git clone https://github.com/your-user/StreaminOS.git
cd StreaminOS
```

#### 2. Install Ansible

```bash
sudo pacman -S ansible
```

#### 3. Use the localhost example inventory

```bash
cd ansible
cp inventory/hosts.yml.example inventory/hosts.yml
```

#### 4. Run installation

```bash
ansible-playbook playbooks/install.yml
```

## Component Installation

You can install specific components using tags:

```bash
# For remote installation (from local machine)
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags base      # Base system and Sway only
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags sunshine  # Sunshine (streaming)
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags steam     # Steam and game management
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags evdi      # Virtual displays
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags amdgpu    # GPU optimizations
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags dashboard # Web dashboard

# For local installation (on the server itself)
ansible-playbook playbooks/install.yml --tags base      # Base system and Sway only
ansible-playbook playbooks/install.yml --tags sunshine  # Sunshine (streaming)
# ... etc
```

## Project Structure

```
StreaminOS/
├── ansible/
│   ├── playbooks/          # Installation playbooks
│   ├── roles/              # Modular roles
│   ├── inventory/          # Host inventory
│   └── group_vars/         # Configuration variables
├── services/               # Services and daemons
├── dashboard/              # Web admin UI
└── docs/                   # Additional documentation
```

## Components

### Base System
- Minimal Arch Linux
- Sway (Wayland compositor)
- Optimized configurations for headless server

### Sunshine
- Game streaming server
- Low-latency optimized configuration
- Virtual display integration

### Virtual Display (EVDI)
- **Solves headless streaming artifacts**: Creates "real" DRM displays for proper framebuffer capture
- On-demand virtual displays (4K@120Hz capable)
- Multiple simultaneous streams at different resolutions
- Management scripts for display creation/removal
- Essential for high-quality headless game streaming
- No overhead when not streaming

### Steam Monitor
- Automatic monitoring of new installations
- Automatic registration in Sunshine
- Support for remote installation from mobile

### Web Dashboard
- Administration interface
- System status monitoring
- Game management and configuration
- Real-time GPU statistics

## Usage

### Start Sway

```bash
# From TTY
sway
```

### Manage Services

```bash
# Check service status
systemctl status streamin-steam-monitor
systemctl status streamin-virtual-display
systemctl status streamin-dashboard

# View logs
journalctl -u streamin-steam-monitor -f
```

### Access Dashboard

```bash
# Dashboard will be available at:
http://localhost:8080
```

## Configuration

Configuration variables are in `ansible/group_vars/all.yml`:

```yaml
# Sunshine port
sunshine_port: 47989

# Virtual display resolution
virtual_display_resolution: "1920x1080"

# Dashboard port
dashboard_port: 8080
```

## Development

### Remote Development Workflow

The recommended workflow is to develop locally and deploy to your remote server:

```bash
# 1. Edit roles/playbooks locally in your preferred editor

# 2. Check syntax (runs locally, no connection needed)
ansible-playbook playbooks/install.yml --syntax-check

# 3. Dry-run mode (connects to server but doesn't apply changes)
ansible-playbook -i inventory/production.yml playbooks/install.yml --check

# 4. Apply changes to remote server
ansible-playbook -i inventory/production.yml playbooks/install.yml

# 5. Run with verbose output for debugging
ansible-playbook -i inventory/production.yml playbooks/install.yml -vvv
```

### SSH Setup for Remote Development

Ensure you have SSH access configured:

```bash
# Test SSH connection
ssh user@your-server-ip

# Set up SSH key (if not already done)
ssh-copy-id user@your-server-ip

# Test Ansible connectivity
ansible -i inventory/production.yml streamin_servers -m ping
```

### Local Testing (Optional)

For testing on the server itself:

```bash
# Check syntax
ansible-playbook playbooks/install.yml --syntax-check

# Dry-run mode
ansible-playbook playbooks/install.yml --check

# Run with verbose output
ansible-playbook playbooks/install.yml -vvv
```

### Adding a New Role

1. Create role structure:
   ```bash
   mkdir -p ansible/roles/my-role/{tasks,handlers,defaults,meta}
   ```

2. Implement tasks in `tasks/main.yml`
3. Add to playbook in `playbooks/install.yml`
4. Update documentation

## Roadmap

- [x] Base system with Sway
- [x] User architecture (dual-user system)
- [x] AUR helper (yay) installation
- [x] Sunshine installation with mDNS autodiscovery
- [x] EVDI virtual displays for headless 4K@120Hz streaming
- [ ] Steam integration
- [ ] Game monitoring service
- [ ] AMD GPU optimizations
- [ ] Web administration dashboard
- [ ] Custom ISO generation
- [ ] Support for other GPUs (NVIDIA, Intel)

## Contributing

Contributions are welcome. Please:

1. Fork the project
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## 📚 Documentation

**Comprehensive learning resources available in `/docs`:**

StreaminOS includes extensive educational documentation to help you understand Linux deeply, not just copy commands:

- **[Documentation Index](docs/README.md)** - Start here!
- **[01 - Users and Permissions](docs/01-users-and-permissions.md)** - Dual-user architecture explained
- **[02 - Systemd](docs/02-systemd.md)** - Service management and auto-start
- **[03 - Wayland and Sway](docs/03-wayland-sway.md)** - Modern compositors for streaming
- **[08 - Troubleshooting](docs/08-troubleshooting.md)** - Debug like a pro
- **[09 - Quick Reference](docs/09-quick-reference.md)** - Command cheatsheet

Each document includes:
- ✅ Theory explained from scratch
- ✅ Practical examples with real commands
- ✅ Visual diagrams
- ✅ Troubleshooting tips
- ✅ Exercises to practice

**Goal:** Understand Linux at a professional level, not just run commands blindly.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-user/StreaminOS/issues)
- **Documentation**: See comprehensive docs in `/docs` folder
- **CLAUDE.md**: Development guide for Claude Code

## Acknowledgments

- [Sunshine](https://github.com/LizardByte/Sunshine) - Game streaming server
- [Moonlight](https://moonlight-stream.org/) - Streaming client
- [evdi](https://github.com/DisplayLink/evdi) - Virtual displays
- [Sway](https://swaywm.org/) - Wayland compositor
