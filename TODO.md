# StreaminOS TODO

MVP roadmap and planned features.

---

## 🎯 MVP Status

### ✅ Core Features Complete

- [x] User Architecture (dual-user: admin + service)
- [x] Sway Compositor (wlroots headless backend)
- [x] Sunshine (streaming server + mDNS + wlr capture)
- [x] Steam Big Picture
- [x] Wake-on-LAN
- [x] Software encoding (CPU, workaround Mesa VAAPI bug)
- [x] Video streaming (4K@120Hz, H.264, 80 Mbps)

### 🚧 MVP Critical Issues

**Priority: HIGH - Fix Tomorrow**

#### 1. Gamescope Integration (Window Focus)
- [ ] Integrate gamescope as nested compositor within Sway
- [ ] Architecture: `Sway (base) → Gamescope (nested) → Steam Big Picture → Games`
- [ ] Problem: Sway doesn't auto-focus game windows when launched from Steam
- [ ] Solution: Gamescope knows how to manage gaming window focus automatically
- [ ] Implementation: Update steam role to launch via gamescope wrapper

#### 2. Audio Streaming
- [ ] Audio not being captured/streamed by Sunshine
- [ ] Investigate: PulseAudio/PipeWire configuration
- [ ] Configure: Sunshine audio sink settings
- [ ] Test: Audio working in Moonlight client

### 🔄 Post-MVP Enhancements

- [ ] AMD GPU optimizations (RX 7900 GRE tuning)
- [ ] Hardware VAAPI encoding (when Mesa bug fixed)
- [ ] Performance monitoring and tuning

---

## 🔄 Post-MVP Features

### Web Dashboard
- System monitoring (GPU, CPU, network)
- Sunshine configuration management
- Service control

### Performance Monitoring
- GPU utilization/temperature
- Encoding metrics
- Network bandwidth
- Frame rate/latency

### Backup/Recovery
- Config backup/restore
- Steam library metadata export
- Ansible restoration playbook

---

## 📝 Documentation Tasks

- [x] Moonlight client setup guide (STEAM_SETUP.md)
- [x] Codec comparison guide (CODEC_COMPARISON.md)
- [x] VAAPI bug documentation (VAAPI_BUG_MESA.md)
- [ ] Gamescope integration plan (create GAMESCOPE_INTEGRATION_PLAN.md)
- [ ] Audio configuration guide
- [ ] Performance tuning guide
- [ ] Network configuration guide

---

**Version**: 1.5 (Sway Architecture - Stable)
**Next**: 2.0 (Sway + Gamescope Nested)
**Last Updated**: 2025-10-31
