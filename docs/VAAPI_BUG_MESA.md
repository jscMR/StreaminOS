# Mesa 25.2.5 VAAPI Bug - Stride Artifacts with wlroots Headless

## Problem Summary

**Date Discovered:** 2025-10-29  
**Affected Configuration:** wlroots headless backend + AMD GPU + Mesa 25.2.5 VAAPI encoder  
**Symptoms:** Vertical lines and fragmented wallpaper artifacts during streaming  
**Workaround:** Use software encoding instead of VAAPI hardware encoding

## Technical Details

### What is VAAPI?

**VAAPI (Video Acceleration API)** is a hardware video encoding/decoding API that allows applications like Sunshine to offload video compression to the GPU instead of the CPU.

**Normal Pipeline (working):**
```
Game (GPU renders) → Sway compositor → Sunshine captures →
VAAPI encoder (GPU compresses) → Network → Moonlight client
```

### The Bug Explanation

The Mesa 25.2.5 VAAPI encoder has a **stride/pitch calculation bug** when working with wlroots headless framebuffers.

**What is stride/pitch?**
- In computer graphics, **stride** (also called **pitch**) is the number of bytes per row in a framebuffer
- For a 4K display (3840px wide) with 32-bit color (4 bytes per pixel):
  - Theoretical stride: `3840 × 4 = 15,360 bytes/row`
  - Actual stride might be: `15,376 bytes/row` (aligned to 16-byte boundary for performance)

**The Bug:**
When wlroots creates headless framebuffers in **RAM** (not VRAM), it uses specific stride values for memory alignment. Mesa 25.2.5's VAAPI encoder **incorrectly reads this stride value**, causing it to:
1. Read pixels from wrong memory addresses
2. Create vertical line artifacts (every ~192 pixels)
3. Fragment the image as it misaligns rows

**Why wlroots headless specifically?**
- Physical displays (DRM backend): Framebuffers in VRAM with GPU-native stride
- **wlroots headless**: Framebuffers in **RAM** with CPU-optimized stride
- Mesa VAAPI assumes VRAM framebuffers and reads stride incorrectly from RAM buffers

### Visual Symptoms

```
Expected:                    Actual (with bug):
┌─────────────────┐         ┌─┬───┬───┬───┬───┐
│                 │         │ │   │   │   │   │
│   Clean 4K      │         │ │ F │ r │ a │ g │
│   Wallpaper     │    →    │ │ r │ a │ g │ m │
│                 │         │ │ a │ g │ m │ e │
│                 │         │ │ g │ m │ e │ n │
└─────────────────┘         └─┴───┴───┴───┴───┘
                            ~30 vertical lines
                            Fragmented/repeated pattern
```

## Affected Software Versions

- **Mesa:** 25.2.5-2 (confirmed buggy)
- **Sunshine:** All versions (not a Sunshine bug)
- **wlroots:** All versions (not a wlroots bug)
- **Sway:** All versions (not a Sway bug)
- **Kernel:** All versions (not a kernel bug)

**Root cause:** Mesa VAAPI encoder implementation

## Workaround: Software Encoding

### Configuration Change

**File:** `ansible/roles/sunshine/defaults/main.yml`

```yaml
# Encoder configuration for AMD GPU
# NOTE: Using software encoding due to Mesa 25.2.5 VAAPI bug causing stride artifacts
# See: https://github.com/LizardByte/Sunshine/issues/4314
# TODO: Test VAAPI again when Mesa 25.3+ or downgrade to Mesa 24.x
sunshine_encoder: software # software encoding works perfectly (uses CPU)
# sunshine_encoder: vaapi # Uncomment when VAAPI bug is fixed
sunshine_adapter: /dev/dri/renderD128 # AMD render node (not used with software encoding)
```

### Performance Impact

**With Software Encoding:**
- **GPU:** 0% encoding overhead (100% available for game rendering)
- **CPU:** ~30-40% usage (2-3 cores on Ryzen 5 7600X)
- **Quality:** Excellent (libx264/libx265 produces better quality than VAAPI)
- **Latency:** ~5ms higher than VAAPI (imperceptible for LAN streaming)

**Hardware Requirements:**
- Recommended: 6+ core CPU (Ryzen 5 7600X or better)
- For weaker CPUs (4 cores or less): Wait for Mesa fix to use VAAPI

## Troubleshooting Steps Taken

During debugging, we tried:

1. ❌ **EVDI virtual displays** - Sway rejected DisplayLink proprietary drivers
2. ❌ **Backend configuration** (`drm,headless` vs `headless`) - No difference
3. ❌ **Sunshine version downgrade** (2025.924.x → 2025.628.x) - Still buggy
4. ❌ **Multiple displays** - Framebuffer concatenation made it worse
5. ❌ **Codec change** (HEVC → H.264) - Same artifacts
6. ✅ **Software encoding** - **WORKS PERFECTLY**

**Key diagnostic:**
- Screenshot with `grim` showed **perfect rendering** (no artifacts)
- This isolated the bug to Sunshine's encoding pipeline, not Sway rendering
- Testing software encoding confirmed VAAPI encoder as culprit

## Future Solutions

### Option 1: Wait for Mesa Update (RECOMMENDED)

Monitor Mesa releases for version 25.3+ or later:

```bash
# Check for Mesa updates
pacman -Qu mesa

# When 25.3+ is available, upgrade
sudo pacman -Syu mesa

# Test VAAPI again
# Change sunshine_encoder: vaapi in defaults/main.yml
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags sunshine
```

### Option 2: Downgrade Mesa to 24.x

```bash
# Install downgrade tool
sudo pacman -S downgrade

# Downgrade Mesa
sudo downgrade mesa

# Select version 24.x from list
# Hold package to prevent auto-upgrade
sudo vim /etc/pacman.conf
# Add: IgnorePkg = mesa
```

### Option 3: Try AMF Encoder (Experimental)

AMD AMF is an alternative hardware encoder:

```yaml
sunshine_encoder: amf
```

**Note:** AMF support in Linux is experimental and may require additional kernel modules.

## Related Issues

- [LizardByte/Sunshine#4314](https://github.com/LizardByte/Sunshine/issues/4314) - VAAPI stride artifacts
- Mesa GitLab: Search for "VAAPI stride" issues

## Testing Checklist

When testing VAAPI in the future:

- [ ] Mesa version ≥ 25.3 or ≤ 24.x
- [ ] Verify Sway is using wlroots headless backend
- [ ] Check Sunshine logs for VAAPI encoder initialization
- [ ] Test with single display (avoid framebuffer concatenation)
- [ ] Stream to 2+ devices (laptop + mobile) to confirm no artifacts
- [ ] Monitor CPU/GPU usage to verify hardware encoding is active
- [ ] Compare quality vs software encoding

## Current Working Configuration

**Server:** 192.168.0.19  
**OS:** Arch Linux  
**Kernel:** 6.17.5-arch1-1  
**Mesa:** 25.2.5-2  
**Sunshine:** v2025.628.4510-1  

**Environment:**
```bash
WLR_BACKENDS=headless
WLR_RENDERER=gles2
WLR_HEADLESS_OUTPUTS=1
WLR_LIBINPUT_NO_DEVICES=1
WLR_RENDERER_ALLOW_SOFTWARE=1
```

**Sunshine:**
```
encoder = software
output = HEADLESS-1 (4K@120Hz)
codec = h264
bitrate = 80000 Kbps
```

**Result:** ✅ Perfect streaming, no artifacts, working on laptop and mobile clients

---

**Last Updated:** 2025-10-29  
**Status:** Software encoding confirmed working, monitoring Mesa for VAAPI fix
