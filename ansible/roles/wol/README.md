# Wake-on-LAN (WoL) Role

This role configures persistent Wake-on-LAN for StreaminOS, allowing you to power on your server remotely using magic packets.

## Features

- ✅ Persistent WoL configuration using systemd.link
- ✅ Immediate activation (no reboot required)
- ✅ Auto-detection of network interface and MAC address
- ✅ Hardware support verification
- ✅ Installs client tools for sending magic packets

## Requirements

### BIOS/UEFI Configuration (MANDATORY)

WoL **requires** specific BIOS/UEFI settings to work. Without these, the server will not wake up:

1. **Enable Wake-on-LAN**
   - Look for settings named:
     - "Wake on LAN"
     - "PCI Power Up"
     - "PME Event Wake Up"
     - "Resume by PCI/PCI-E Device"
   - Enable this setting

2. **Disable ErP Mode** (if present)
   - ErP mode cuts power to PCIe devices, preventing WoL
   - Disable "ErP Ready" or "ErP Support"
   - Alternative names: "Energy Related Products Mode"

3. **Check Power State Support**
   - Some motherboards only support WoL from S3 (sleep), not S5 (powered off)
   - Verify your board supports "Wake from S5" if you want to wake from powered-off state

### Hardware Requirements

- Ethernet network card (WiFi does not reliably support WoL)
- Network card must support magic packet (most modern cards do)
- Power supply must remain connected to maintain standby power

## Installation

### Deploy WoL role

```bash
cd ansible
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags wol
```

### Variables

Configure in `roles/wol/defaults/main.yml` or override in your inventory:

```yaml
wol_enable: true                    # Enable/disable WoL
wol_interface: "eno1"               # Network interface name
wol_install_client_tools: true     # Install 'wol' command
wol_verify_support: true           # Check hardware support
```

## Usage

### Get your server's MAC address

The role automatically detects and displays the MAC address during deployment. You can also check it manually:

```bash
ip link show eno1 | grep "link/ether"
# Example output: link/ether 10:7c:61:b6:9a:27
```

### Verify WoL is enabled

```bash
sudo ethtool eno1 | grep Wake-on
# Expected output: Wake-on: g
# g = magic packet support enabled
```

### Send magic packets to wake the server

#### From Linux/macOS

Install wol package:
```bash
# Arch/Manjaro
sudo pacman -S wol

# Ubuntu/Debian
sudo apt install wakeonlan

# macOS
brew install wakeonlan
```

Wake the server from local network:
```bash
wol 10:7c:61:b6:9a:27
```

Wake from internet (requires router port forwarding):
```bash
# Forward UDP port 9 to 255.255.255.255 in your router
wol -p 9 -i YOUR_PUBLIC_IP 10:7c:61:b6:9a:27
```

#### From Windows

Use [WakeMeOnLan](https://www.nirsoft.net/utils/wake_on_lan.html):
1. Download and run WakeMeOnLan
2. Click "Add New Computer"
3. Enter MAC address: `10:7c:61:b6:9a:27`
4. Enter IP: `192.168.0.19` (or leave blank for broadcast)
5. Click "Wake Up Selected Computers"

#### From Android

Apps like "Wake On Lan" (by Mike Webb):
1. Install from Play Store
2. Add device with MAC address
3. Tap to send magic packet

#### From iOS

Apps like "Mocha WOL":
1. Install from App Store
2. Add device with MAC address
3. Tap to wake

## Testing

### Test WoL functionality

1. **Power off the server** (not reboot, actual shutdown):
   ```bash
   sudo poweroff
   ```

2. **Send magic packet from another computer**:
   ```bash
   wol 10:7c:61:b6:9a:27
   ```

3. **Server should power on automatically**
   - Typically takes 2-5 seconds
   - You'll hear fans spin up and see LEDs light up

### Test from sleep (S3)

Some systems support waking from sleep more reliably:
```bash
# Put server to sleep
sudo systemctl suspend

# Wake with magic packet
wol 10:7c:61:b6:9a:27
```

## Troubleshooting

### WoL not working after configuration

1. **Check BIOS settings first** - This is the #1 cause of WoL failures
   - Verify "Wake on LAN" is enabled
   - Verify "ErP Mode" is disabled
   - Save and exit BIOS

2. **Verify hardware support**:
   ```bash
   sudo ethtool eno1 | grep "Supports Wake-on"
   # Should show 'g' in the list (e.g., "pumbg")
   ```

3. **Check current WoL status**:
   ```bash
   sudo ethtool eno1 | grep "Wake-on:"
   # Should show "Wake-on: g"
   # If showing "d", run: sudo ethtool -s eno1 wol g
   ```

4. **Verify systemd.link file exists**:
   ```bash
   cat /etc/systemd/network/50-wired.link
   # Should contain: WakeOnLan=magic
   ```

5. **Check network connectivity**:
   - Magic packets use UDP broadcast
   - Ensure no firewall blocks UDP port 9
   - Ensure router/switch allows broadcast packets

6. **Test from same subnet first**:
   - WoL works best on local network
   - Test locally before attempting internet wake

### WoL stops working after reboot

This usually means systemd.link is not being applied:

```bash
# Verify file exists
ls -la /etc/systemd/network/50-wired.link

# Check if systemd-networkd is running
systemctl status systemd-networkd

# Manually enable WoL for testing
sudo ethtool -s eno1 wol g
```

### Specific network card issues

**Realtek RTL8168/8111**:
- May require r8168 driver with s5wol parameter
- Add to `/etc/modprobe.d/r8168.conf`:
  ```
  options r8168 s5wol=1
  ```

**Intel cards**:
- Usually work out of the box
- Verify e1000e driver is loaded: `lsmod | grep e1000e`

### Router configuration for internet wake

1. **Port forwarding**:
   - Forward UDP port 9 to broadcast address (e.g., 192.168.0.255)
   - Or forward to server's last known IP (less reliable)

2. **Dynamic DNS** (recommended):
   - Use DynDNS, No-IP, or similar
   - Allows waking server without remembering public IP

3. **Security considerations**:
   - Magic packets are unencrypted and unauthenticated
   - Anyone with your MAC address can wake your server
   - Consider using VPN for secure remote wake

## Architecture

### How it works

1. **systemd.link** (`/etc/systemd/network/50-wired.link`):
   - Configures WoL at boot time
   - Matches interface by original name (eno1)
   - Sets `WakeOnLan=magic` parameter

2. **Immediate activation** (tasks/main.yml):
   - Runs `ethtool -s eno1 wol g` during deployment
   - Enables WoL without requiring reboot

3. **Persistence**:
   - systemd.link ensures WoL survives reboots
   - Applied automatically when interface comes up

### Compatibility

- **Network manager**: Works with dhcpcd, NetworkManager, systemd-networkd
- **systemd.link**: Available in systemd >= 197 (all modern distros)
- **Kernel**: Requires driver support (most Ethernet drivers support WoL)

## Integration with StreaminOS

Wake-on-LAN is particularly useful for StreaminOS:

1. **Power off server when not gaming** to save electricity
2. **Wake remotely** when you want to stream games
3. **Moonlight clients** can wake server before connecting (configure in Moonlight settings)
4. **Automated wake** via scripts or home automation

### Moonlight integration

Moonlight can automatically wake your server:

1. Open Moonlight settings
2. Find your StreaminOS server
3. Enable "Send WoL packet before connecting"
4. Add MAC address: `10:7c:61:b6:9a:27`

Now when you select your server, Moonlight will:
1. Send magic packet
2. Wait for server to boot (~30 seconds)
3. Connect automatically when ready

## Files Created

```
/etc/systemd/network/50-wired.link   # Persistent WoL configuration
```

## Dependencies

- `ethtool` - Network driver configuration utility
- `wol` - CLI tool for sending magic packets (optional)

## See Also

- [Arch Wiki - Wake-on-LAN](https://wiki.archlinux.org/title/Wake-on-LAN)
- [systemd.link man page](https://www.freedesktop.org/software/systemd/man/systemd.link.html)
- [ethtool man page](https://man7.org/linux/man-pages/man8/ethtool.8.html)
