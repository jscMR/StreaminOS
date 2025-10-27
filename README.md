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

## Quick Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-user/StreaminOS.git
cd StreaminOS
```

### 2. Install Ansible

```bash
sudo pacman -S ansible
```

### 3. Run installation

```bash
cd ansible
ansible-playbook playbooks/install.yml
```

## Component Installation

You can install specific components using tags:

```bash
# Base system and Sway only
ansible-playbook playbooks/install.yml --tags base

# Sunshine (streaming)
ansible-playbook playbooks/install.yml --tags sunshine

# Steam and game management
ansible-playbook playbooks/install.yml --tags steam

# Virtual displays
ansible-playbook playbooks/install.yml --tags evdi

# GPU optimizations
ansible-playbook playbooks/install.yml --tags amdgpu

# Web dashboard
ansible-playbook playbooks/install.yml --tags dashboard
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

### Virtual Display (evdi)
- On-demand virtual displays
- Automatic management from Moonlight clients
- No overhead when not in use

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

### Local Testing

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
- [ ] Sunshine installation
- [ ] evdi and virtual display configuration
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

## Support

- **Issues**: [GitHub Issues](https://github.com/your-user/StreaminOS/issues)
- **Documentation**: See `docs/` folder
- **CLAUDE.md**: Development guide for Claude Code

## Acknowledgments

- [Sunshine](https://github.com/LizardByte/Sunshine) - Game streaming server
- [Moonlight](https://moonlight-stream.org/) - Streaming client
- [evdi](https://github.com/DisplayLink/evdi) - Virtual displays
- [Sway](https://swaywm.org/) - Wayland compositor
