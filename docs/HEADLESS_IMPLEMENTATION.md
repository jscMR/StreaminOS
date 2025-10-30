# Implementación de Virtual Displays con wlroots Headless Backend

**Fecha de creación:** 2025-10-29
**Autor:** StreaminOS Team
**Objetivo:** Reemplazar EVDI con la solución nativa wlroots headless para virtual displays

---

## 📋 Resumen Ejecutivo

### Problema Actual
- **EVDI/DisplayLink** no funciona con Sway (drivers propietarios rechazados)
- Sway muestra: `!!! Proprietary DisplayLink drivers are in use !!!`
- Artefactos de streaming por falta de displays virtuales funcionales

### Solución Correcta
- **wlroots headless backend**: Solución nativa para virtual displays
- Mismo concepto que Windows Apollo (IddSampleDriver)
- GPU rendering completo con AMD RX 7900 GRE
- Sin drivers propietarios, sin hardware adicional

### Resultado Esperado
- Virtual displays 4K@120Hz funcionales
- Streaming sin artefactos
- 100% open source y estable

---

## 🎯 Arquitectura

### Antes (EVDI - INCORRECTO)
```
GPU AMD → EVDI (DisplayLink drivers) → DRM devices
                    ↓
                Sway rechaza
                    ↓
                  FALLA
```

### Después (wlroots headless - CORRECTO)
```
GPU AMD → wlroots DRM backend (rendering)
              ↓
        wlroots headless backend (virtual outputs)
              ↓
        HEADLESS-1 (4K@120Hz)
        HEADLESS-2 (1080p@60Hz)
              ↓
        Sunshine captura via WLR protocol
              ↓
        VAAPI encoding (GPU)
              ↓
        Stream perfecto
```

---

## 📦 Fase 1: Limpieza de EVDI

### 1.1. Desinstalar del Servidor

```bash
# Conectar al servidor
ssh noid@192.168.0.19

# Descargar módulo kernel
sudo modprobe -r evdi

# Desinstalar paquetes
yay -Rns evdi-dkms displaylink

# Eliminar archivos de configuración
sudo rm -rf /opt/evdi-scripts/
sudo rm -f /etc/modules-load.d/evdi.conf
sudo rm -f /etc/udev/rules.d/99-evdi.rules

# Recargar udev
sudo udevadm control --reload-rules && sudo udevadm trigger

# Verificar que no queden DRM devices de EVDI
ls /dev/dri/
# Solo deberías ver card0, card1, renderD128, renderD129 (AMD)
```

### 1.2. Eliminar Role EVDI de Ansible

```bash
# En tu máquina local
cd /home/noid/dev/StreaminOS/ansible

# Eliminar role completo
rm -rf roles/evdi/

# Verificar eliminación
ls -la roles/
```

### 1.3. Actualizar Playbook

**Archivo:** `ansible/playbooks/install.yml`

**Buscar y ELIMINAR estas líneas:**
```yaml
# EVDI virtual displays (essential for headless 4K@120Hz streaming)
- role: evdi
  tags:
    - evdi
    - display
    - virtual-display
```

**Resultado:** El role evdi ya no se ejecutará.

---

## 📝 Fase 2: Implementar wlroots Headless Backend

### 2.1. Actualizar Variables Globales

**Archivo:** `ansible/group_vars/all.yml`

**Buscar sección:**
```yaml
# ============================================================================
# Virtual Display (EVDI)
# ============================================================================
evdi_displays_max: 4
virtual_display_resolution: "3840x2160"  # 4K resolution
virtual_display_refresh_rate: 120  # 120Hz refresh rate
```

**Reemplazar por:**
```yaml
# ============================================================================
# Virtual Displays (wlroots Headless Backend)
# ============================================================================
# Native wlroots solution (no EVDI needed)
# Creates virtual outputs for headless game streaming

# Number of headless outputs to create
headless_outputs_count: 2

# Primary display (for 4K streaming)
headless_primary_resolution: "3840x2160"
headless_primary_refresh: 120

# Secondary display (for lower quality streams)
headless_secondary_resolution: "1920x1080"
headless_secondary_refresh: 60

# WLR backend configuration
wlr_backends: "headless"  # Options: "drm,headless" or "headless"
```

---

### 2.2. Actualizar Role user-setup

**Archivo:** `ansible/roles/user-setup/templates/environment.j2`

**Agregar al final del archivo:**

```bash
# ============================================================================
# wlroots Headless Backend Configuration
# ============================================================================
# Enable headless backend for virtual displays (Sunshine streaming)

# Backend selection:
# - "headless": Pure virtual displays (no physical monitor needed)
# - "drm,headless": Physical + virtual displays (if monitor connected)
export WLR_BACKENDS={{ wlr_backends }}

# Number of headless outputs to pre-create
export WLR_HEADLESS_OUTPUTS={{ headless_outputs_count }}

# Renderer (auto-detect GPU, fallback to software if needed)
# export WLR_RENDERER=auto

# For debugging wlroots issues (optional)
# export WLR_DEBUG=1
```

---

### 2.3. Actualizar Sway Configuration

**Archivo:** `ansible/roles/base/templates/sway-config.j2`

**Buscar sección:**
```
# Output configuration
# Physical outputs (if any)
output * {
    bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill
}

# EVDI virtual outputs configuration
# These will be created dynamically by Sunshine/scripts
# Sway will auto-detect them, but we can set defaults here

# Default for any Virtual-* outputs (EVDI creates these)
output "Virtual-*" {
    mode {{ virtual_display_resolution | default('3840x2160') }}@{{ virtual_display_refresh_rate | default(120) }}Hz
    position 0 0
    bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill
}

# Headless mode fallback
output HEADLESS-1 {
    mode 1920x1080@60Hz
    position 0 0
    bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill
}
```

**Reemplazar por:**
```
# ============================================================================
# Output Configuration - Headless Virtual Displays
# ============================================================================

# Physical outputs (if any monitor is connected)
output * bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill

# Headless virtual display 1 (Primary - 4K@120Hz)
# Used for high-quality game streaming via Sunshine
output HEADLESS-1 {
    mode {{ headless_primary_resolution }}@{{ headless_primary_refresh }}Hz
    position 0 0
    bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill
}

# Headless virtual display 2 (Secondary - 1080p@60Hz)
# Used for lower bitrate streams or secondary clients
output HEADLESS-2 {
    mode {{ headless_secondary_resolution }}@{{ headless_secondary_refresh }}Hz
    position {{ headless_primary_resolution.split('x')[0] }} 0
    bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill
}

# Additional headless displays can be configured here
# output HEADLESS-3 {
#     mode 2560x1440@120Hz
#     position 0 2160
#     bg /home/{{ streamin_user }}/Pictures/wallpaper.png fill
# }
```

---

### 2.4. Crear Scripts de Gestión

#### Script 1: list_displays.sh

**Archivo:** `ansible/roles/base/files/list_displays.sh`

```bash
#!/bin/bash
# List all Sway outputs (physical and virtual)

echo "===================================="
echo "Sway Outputs Status"
echo "===================================="

# Check if Sway is running
if ! pgrep -x sway > /dev/null; then
    echo "ERROR: Sway is not running"
    exit 1
fi

# Find Sway socket
SWAY_SOCK=$(find /run/user/*/sway-ipc.*.sock 2>/dev/null | head -1)

if [ -z "$SWAY_SOCK" ]; then
    echo "ERROR: Cannot find Sway socket"
    exit 1
fi

# Get outputs
export SWAYSOCK="$SWAY_SOCK"
swaymsg -t get_outputs -p

echo ""
echo "WLR Backend Configuration:"
ps aux | grep sway | grep -o 'WLR_BACKENDS=[^ ]*' || echo "  Not set in process args"

echo ""
echo "Environment Variables:"
echo "  WLR_BACKENDS: ${WLR_BACKENDS:-not set}"
echo "  WLR_HEADLESS_OUTPUTS: ${WLR_HEADLESS_OUTPUTS:-not set}"
```

#### Script 2: set_resolution.sh

**Archivo:** `ansible/roles/base/files/set_resolution.sh`

```bash
#!/bin/bash
# Change resolution of a headless output dynamically

if [ $# -lt 2 ]; then
    echo "Usage: $0 <output> <resolution>[@refresh_rate]"
    echo ""
    echo "Examples:"
    echo "  $0 HEADLESS-1 3840x2160@120Hz"
    echo "  $0 HEADLESS-2 1920x1080@60Hz"
    echo "  $0 HEADLESS-1 2560x1440@144Hz"
    exit 1
fi

OUTPUT="$1"
MODE="$2"

# Find Sway socket
SWAY_SOCK=$(find /run/user/*/sway-ipc.*.sock 2>/dev/null | head -1)

if [ -z "$SWAY_SOCK" ]; then
    echo "ERROR: Cannot find Sway socket"
    exit 1
fi

export SWAYSOCK="$SWAY_SOCK"

echo "Setting $OUTPUT to mode $MODE..."
swaymsg output "$OUTPUT" mode "$MODE"

if [ $? -eq 0 ]; then
    echo "✓ Resolution changed successfully"
    echo ""
    swaymsg -t get_outputs | grep -A 5 "$OUTPUT"
else
    echo "✗ Failed to change resolution"
    exit 1
fi
```

#### Script 3: restart_sway.sh

**Archivo:** `ansible/roles/base/files/restart_sway.sh`

```bash
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
```

---

### 2.5. Actualizar Tasks del Role base

**Archivo:** `ansible/roles/base/tasks/main.yml`

**Agregar al final (antes de los tasks de verificación):**

```yaml
- name: Create StreaminOS scripts directory
  file:
    path: /opt/streamin-scripts
    state: directory
    owner: root
    group: root
    mode: '0755'
  tags: base

- name: Install display management scripts
  copy:
    src: "{{ item }}"
    dest: /opt/streamin-scripts/{{ item }}
    owner: root
    group: root
    mode: '0755'
  loop:
    - list_displays.sh
    - set_resolution.sh
    - restart_sway.sh
  tags: base
```

---

## 🔧 Fase 3: Actualizar Sunshine

**Archivo:** `ansible/roles/sunshine/defaults/main.yml`

**No necesita cambios** - Sunshine ya está configurado correctamente:
```yaml
sunshine_capture_method: wlr  # ✓ Compatible con headless outputs
```

**Archivo:** `ansible/roles/sunshine/templates/sunshine.conf.j2`

**Verificar que tenga:**
```ini
# Capture method for Wayland
capture = wlr

# Wayland display
wayland_display = wayland-1
```

✓ Ya está correcto, no requiere cambios.

---

## 📚 Fase 4: Actualizar Documentación

### 4.1. CLAUDE.md

**Buscar:**
```markdown
5. **`evdi`**: Virtual display driver for headless streaming
   - Tags: `evdi`, `display`, `virtual-display`
   - Installs evdi-dkms kernel module from AUR
   - Installs DisplayLink userspace tools
   - Creates management scripts for display creation/removal
   - Configures udev rules for device permissions
   - Supports up to 4 simultaneous virtual displays
   - Default: 4K@120Hz resolution
   - Solves artifacts caused by headless setup
```

**Reemplazar por:**
```markdown
5. **Headless Virtual Displays**: wlroots native virtual outputs
   - Built into Sway/wlroots (no external packages)
   - Creates virtual displays via WLR_BACKENDS environment variable
   - Full GPU rendering with AMD VAAPI
   - Default: 2 outputs (4K@120Hz + 1080p@60Hz)
   - Management scripts for resolution control
   - Solves headless streaming artifacts completely
   - Production-ready, same approach as Windows Apollo
```

### 4.2. README.md

**Buscar:**
```markdown
### Virtual Display (EVDI)
- **Solves headless streaming artifacts**: Creates "real" DRM displays for proper framebuffer capture
- On-demand virtual displays (4K@120Hz capable)
- Multiple simultaneous streams at different resolutions
- Management scripts for display creation/removal
- Essential for high-quality headless game streaming
- No overhead when not streaming
```

**Reemplazar por:**
```markdown
### Virtual Displays (wlroots Headless)
- **Native wlroots solution**: No external drivers or kernel modules
- Solves headless streaming artifacts completely
- GPU-accelerated rendering (AMD RX 7900 GRE)
- Multiple virtual outputs (4K@120Hz + 1080p@60Hz)
- Dynamic resolution switching via scripts
- Zero overhead when not streaming
- Same architecture as Windows Apollo
```

---

## 🚀 Fase 5: Despliegue

### 5.1. Validar Sintaxis Ansible

```bash
cd /home/noid/dev/StreaminOS/ansible
ansible-playbook playbooks/install.yml --syntax-check
```

### 5.2. Desplegar Cambios al Servidor

```bash
# Deploy base role (Sway config + scripts)
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags base

# Deploy user-setup (environment variables)
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags user-setup

# Deploy sunshine (verificar que sigue funcionando)
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags sunshine
```

### 5.3. Reiniciar Servidor

```bash
ssh noid@192.168.0.19 "sudo reboot"
```

Esperar 1-2 minutos.

---

## ✅ Fase 6: Verificación

### 6.1. Verificar Variables de Entorno

```bash
ssh noid@192.168.0.19 "sudo -u streaminos bash -c 'source ~/.profile && env | grep WLR'"
```

**Esperado:**
```
WLR_BACKENDS=headless
WLR_HEADLESS_OUTPUTS=2
```

### 6.2. Verificar Sway está Corriendo

```bash
ssh noid@192.168.0.19 "ps aux | grep sway | grep streaminos"
```

**Esperado:**
```
streaminos  [PID]  ... /usr/bin/sway
```

### 6.3. Listar Outputs Headless

```bash
ssh noid@192.168.0.19 "sudo /opt/streamin-scripts/list_displays.sh"
```

**Esperado:**
```
Output HEADLESS-1 'Unknown Unknown' (focused)
  Current mode: 3840x2160 @ 120.000 Hz
  Position: 0,0
  ...

Output HEADLESS-2 'Unknown Unknown'
  Current mode: 1920x1080 @ 60.000 Hz
  Position: 3840,0
  ...
```

### 6.4. Verificar Rendering GPU

```bash
ssh noid@192.168.0.19 "sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 \
  WAYLAND_DISPLAY=wayland-1 swaymsg -t get_outputs | grep -A 10 HEADLESS-1"
```

Buscar líneas como:
```
Make: Unknown
Model: Unknown
Serial: Unknown
Scale: 1.000000
Transform: normal
Current mode: 3840x2160 @ 120.000 Hz
```

### 6.5. Verificar Sunshine Detecta Outputs

```bash
ssh noid@192.168.0.19 "sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 \
  journalctl --user -u sunshine.service -n 50 | grep -i 'output\|display'"
```

Buscar líneas como:
```
Info: Found display [HEADLESS-1]
Info: Resolution: 3840x2160
```

### 6.6. Test de Streaming

1. Abrir Moonlight en tu laptop
2. Conectar a "streaminos"
3. Seleccionar "Desktop"
4. **Verificar:**
   - ✅ Sin artefactos
   - ✅ Imagen nítida
   - ✅ 4K@120Hz (si tu cliente lo soporta)
   - ✅ Smooth performance

---

## 🐛 Troubleshooting

### Problema 1: Sway no arranca

**Síntomas:**
```bash
systemctl --user status sway.service
# Status: failed
```

**Logs:**
```bash
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 \
  journalctl --user -u sway.service -n 50
```

**Soluciones:**

1. **Falta WLR_BACKENDS:**
```bash
# Verificar
source /home/streaminos/.profile
echo $WLR_BACKENDS  # Debe mostrar "headless"
```

2. **Conflicto con displays físicos:**
```bash
# Cambiar a backend híbrido
export WLR_BACKENDS=drm,headless
```

3. **Mesa/GPU issues:**
```bash
# Permitir software rendering (temporal)
export WLR_RENDERER_ALLOW_SOFTWARE=1
```

---

### Problema 2: No aparecen outputs HEADLESS

**Verificar:**
```bash
# Contar outputs
swaymsg -t get_outputs | grep -c "Output HEADLESS"
```

**Si es 0:**

1. **Verificar WLR_HEADLESS_OUTPUTS:**
```bash
echo $WLR_HEADLESS_OUTPUTS  # Debe ser 2
```

2. **Reiniciar Sway:**
```bash
sudo /opt/streamin-scripts/restart_sway.sh
```

3. **Logs de wlroots:**
```bash
journalctl --user -u sway.service | grep -i headless
```

---

### Problema 3: Sunshine no captura headless

**Verificar configuración:**
```bash
cat /home/streaminos/.config/sunshine/sunshine.conf | grep -E '(capture|wayland)'
```

**Debe tener:**
```
capture = wlr
wayland_display = wayland-1
```

**Reiniciar Sunshine:**
```bash
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 \
  systemctl --user restart sunshine.service
```

---

### Problema 4: Artefactos persisten

**Si todavía hay artefactos:**

1. **Verificar resolución actual:**
```bash
/opt/streamin-scripts/list_displays.sh
```

2. **Cambiar a resolución conocida buena:**
```bash
/opt/streamin-scripts/set_resolution.sh HEADLESS-1 1920x1080@60Hz
```

3. **Verificar bitrate en Sunshine:**
```bash
grep bitrate /home/streaminos/.config/sunshine/sunshine.conf
# Debe ser >= 50000 (50 Mbps)
```

4. **Verificar VAAPI funciona:**
```bash
vainfo --display drm --device /dev/dri/renderD128
```

---

### Problema 5: GPU no se usa (software rendering)

**Síntomas:**
- Alto uso de CPU
- Bajo FPS
- Logs muestran "software rendering"

**Solución:**
```bash
# Verificar que AMD drivers están cargados
lsmod | grep amdgpu

# Verificar DRM devices
ls -la /dev/dri/

# Force GPU rendering
export WLR_RENDERER=gles2
export WLR_DRM_DEVICES=/dev/dri/card0:/dev/dri/card1
```

---

## 📊 Comparación Antes/Después

| Aspecto | EVDI (Antes) | wlroots Headless (Después) |
|---------|--------------|----------------------------|
| **Drivers** | Propietarios (DisplayLink) | Nativos (wlroots) |
| **Sway** | ❌ Rechazado | ✅ Soportado |
| **GPU Rendering** | ❌ Falla | ✅ Completo |
| **Instalación** | Kernel module + AUR | Variables de entorno |
| **Mantenimiento** | Alto (updates) | Bajo (estable) |
| **Artefactos** | ❌ Sí | ✅ No |
| **Performance** | N/A (no funciona) | ✅ Nativa |
| **Documentación** | Escasa | Abundante |
| **Estabilidad** | ⭐ | ⭐⭐⭐⭐⭐ |

---

## 🎯 Checklist Final

Antes de considerar completa la implementación, verificar:

- [ ] EVDI completamente desinstalado del servidor
- [ ] Role evdi eliminado de Ansible
- [ ] Variables WLR configuradas en environment.j2
- [ ] Sway config actualizado con outputs HEADLESS
- [ ] Scripts de gestión instalados en /opt/streamin-scripts/
- [ ] Documentación actualizada (CLAUDE.md, README.md)
- [ ] Cambios desplegados al servidor
- [ ] Servidor reiniciado
- [ ] Sway arranca correctamente
- [ ] HEADLESS-1 y HEADLESS-2 visibles
- [ ] Sunshine detecta outputs headless
- [ ] Streaming funciona sin artefactos
- [ ] GPU rendering activo (verificar con radeontop)
- [ ] Documentación de troubleshooting probada

---

## 📖 Referencias

- **wlroots documentation**: https://gitlab.freedesktop.org/wlroots/wlroots
- **Sway documentation**: https://github.com/swaywm/sway/wiki
- **Sunshine documentation**: https://docs.lizardbyte.dev/projects/sunshine/
- **wlroots headless backend**: https://github.com/swaywm/wlroots/blob/master/include/wlr/backend/headless.h
- **Similar projects**: wayvnc, gamescope, wf-recorder

---

## ✨ Resultado Final Esperado

```
$ /opt/streamin-scripts/list_displays.sh

====================================
Sway Outputs Status
====================================

Output HEADLESS-1 'Unknown Unknown' (focused)
  Current mode: 3840x2160 @ 120.000 Hz
  Position: 0,0
  Transform: normal
  Scale factor: 1.000000
  Active workspace: 1

Output HEADLESS-2 'Unknown Unknown'
  Current mode: 1920x1080 @ 60.000 Hz
  Position: 3840,0
  Transform: normal
  Scale factor: 1.000000

WLR Backend Configuration:
  WLR_BACKENDS=headless

Environment Variables:
  WLR_BACKENDS: headless
  WLR_HEADLESS_OUTPUTS: 2
```

**¡Streaming 4K@120Hz sin artefactos! ✨**

---

**Documento creado:** 2025-10-29
**Próxima revisión:** Después de implementación exitosa
**Estado:** Listo para ejecutar
