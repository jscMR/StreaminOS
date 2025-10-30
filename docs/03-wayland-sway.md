# 03 - Wayland y Sway: El Compositor Moderno

## 🎯 Lo Que Vas a Aprender

- Diferencia entre X11 y Wayland
- Qué es un compositor y por qué lo necesitas
- Por qué Sway es perfecto para streaming headless
- Variables de entorno críticas para Wayland
- Cómo funcionan los displays en Linux

---

## 🖥️ La Evolución: X11 → Wayland

### X11 (X Window System) - El Antiguo

**X11** existe desde 1984 y ha servido bien, pero tiene problemas:

```
┌──────────────────────────────────────┐
│         Aplicación (Firefox)         │
└──────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│         X Server (Xorg)              │
│  • Gestiona ventanas                 │
│  • Maneja input (teclado/ratón)     │
│  • Dibuja gráficos                   │
└──────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│    Window Manager (i3, openbox)     │
│  • Decoraciones de ventanas          │
│  • Gestión de layouts                │
└──────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│         Compositor (compton)         │
│  • Efectos visuales                  │
│  • Transparencia, sombras            │
└──────────────────────────────────────┘
                 ↓
              [GPU/Monitor]
```

**Problemas de X11:**
- ❌ Arquitectura cliente-servidor obsoleta
- ❌ Demasiados componentes separados
- ❌ Seguridad: aplicaciones pueden espiar otras ventanas
- ❌ Input lag por múltiples capas
- ❌ Screen tearing
- ❌ No diseñado para GPUs modernas

### Wayland - El Moderno

**Wayland** simplifica todo combinando componentes:

```
┌──────────────────────────────────────┐
│         Aplicación (Firefox)         │
└──────────────────────────────────────┘
                 ↓
┌──────────────────────────────────────┐
│      Compositor Wayland (Sway)       │
│  • TODO en uno:                      │
│    - Window manager                  │
│    - Compositor                      │
│    - Display server                  │
└──────────────────────────────────────┘
                 ↓
              [GPU/Monitor]
```

**Ventajas de Wayland:**
- ✅ Arquitectura simple y moderna
- ✅ Mejor seguridad (aislamiento entre apps)
- ✅ Menor latencia (menos capas)
- ✅ No screen tearing
- ✅ Diseñado para GPUs modernas con DRM/KMS
- ✅ Perfecto para streaming (acceso directo a buffers)

---

## 🎨 ¿Qué es un Compositor?

Un **compositor** es el programa que:

1. **Gestiona ventanas**: Tamaño, posición, foco
2. **Renderiza**: Dibuja las ventanas en pantalla
3. **Maneja input**: Teclado, ratón, touchpad
4. **Controla outputs**: Monitores, resoluciones, rotación

En Wayland, el compositor **ES** el display server. Todo en uno.

### Compositors Populares

| Compositor | Tipo | Uso |
|------------|------|-----|
| **Sway** | Tiling (i3-like) | Streaming, headless, teclado |
| **Hyprland** | Tiling dinámico | Desktop con efectos |
| **GNOME** | Stacking | Desktop tradicional |
| **KDE Plasma** | Stacking | Desktop completo |
| **Wayfire** | Stacking | Desktop ligero |

---

## 🚀 Por Qué Sway para StreaminOS

### Sway = i3 en Wayland

**Sway** es un clon de **i3wm** (window manager tiling popular) pero para Wayland.

```bash
# Ver versión de Sway
sway --version
# sway version 1.11
```

### Ventajas de Sway para Streaming

1. **Headless-friendly**: Funciona sin monitor físico
2. **Lightweight**: Mínimo consumo de recursos
3. **Sin efectos innecesarios**: CPU/GPU disponible para juegos
4. **Tiling**: Organización automática de ventanas (útil para gestión remota)
5. **IPC robusto**: Control programático con `swaymsg`
6. **Wayland puro**: Acceso directo a buffers de GPU para Sunshine

### Configuración Mínima en StreaminOS

```bash
# Ver config de Sway
cat /home/streaminos/.config/sway/config
```

```
# StreaminOS Sway Config
# Minimalist configuration for streaming server

# Mod key (Mod4 = Super/Windows key)
set $mod Mod4

# Terminal
set $term foot

# Basic keybindings
bindsym $mod+Return exec $term
bindsym $mod+Shift+q kill
bindsym $mod+Shift+c reload
bindsym $mod+Shift+e exit

# Outputs (for virtual displays)
output * bg #000000 solid_color

# No gaps, no borders (headless server)
default_border none
default_floating_border none
gaps inner 0
gaps outer 0
```

**¿Por qué tan minimalista?**
- No necesitamos wallpapers (no hay monitor físico)
- No necesitamos gaps/borders (solo streaming)
- No necesitamos status bar (gestionamos por SSH)

---

## 🎮 Sway en Modo Headless

### ¿Qué Significa Headless?

**Headless** = Sin monitor físico conectado.

En StreaminOS:
- El servidor está en el rack/armario
- No tiene monitor, teclado ni ratón físicos
- Gestionamos todo por SSH
- Sunshine captura el output de Sway y lo streammea

### Cómo Funciona Sin Monitor

```
┌─────────────────────────────────────────┐
│              Sway                       │
│  • Cree que hay un "monitor" virtual   │
│  • Renderiza a ese display             │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│         GPU (AMD RX 7900)               │
│  • Crea framebuffers en memoria        │
│  • NO envía señal a HDMI/DP            │
└─────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│            Sunshine                     │
│  • Lee framebuffers de GPU             │
│  • Codifica con NVENC/VAAPI            │
│  • Streamea por red a Moonlight        │
└─────────────────────────────────────────┘
                 ↓
        [Cliente Moonlight]
     (Tu PC, móvil, TV, etc.)
```

### Verificar Outputs de Sway

```bash
# Ver qué outputs tiene Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg -t get_outputs

# Salida típica en headless (con GPU física):
# Output DVI-D-1 'Unknown Unknown (Unknown)'
#   Current mode: 1920x1080 @ 60.000 Hz
#   Position: 0,0
#   ...
```

---

## 🌐 Variables de Entorno Críticas

Wayland usa varias variables de entorno. Si faltan, nada funciona.

### XDG_RUNTIME_DIR

**La más importante**. Directorio temporal del usuario.

```bash
echo $XDG_RUNTIME_DIR
# /run/user/1100
```

**Contiene:**
- Sockets de Wayland (`wayland-0`, `wayland-1`)
- Sockets de PulseAudio
- Otros sockets IPC

```bash
ls -la /run/user/1100/
# srw-rw-r-- 1 streaminos streaminos 0 Oct 28 20:20 wayland-1
# ^^^^ socket de Wayland
```

**Problema común:**
```bash
# Sin XDG_RUNTIME_DIR
sway
# XDG_RUNTIME_DIR is not set in the environment. Aborting.
```

**Solución:**
```bash
export XDG_RUNTIME_DIR="/run/user/$(id -u)"
```

### WAYLAND_DISPLAY

Indica qué socket de Wayland usar.

```bash
echo $WAYLAND_DISPLAY
# wayland-1
```

Múltiples compositors pueden correr simultáneamente:
- `wayland-0` = Primera sesión
- `wayland-1` = Segunda sesión
- etc.

```bash
# Conectar a un compositor específico
WAYLAND_DISPLAY=wayland-1 firefox
```

### Otras Variables Importantes

```bash
# Habilitar Wayland en apps
export MOZ_ENABLE_WAYLAND=1        # Firefox
export QT_QPA_PLATFORM=wayland     # Qt apps
export GDK_BACKEND=wayland         # GTK apps
export SDL_VIDEODRIVER=wayland     # SDL (juegos)

# AMD GPU optimizations
export RADV_PERFTEST=aco           # ACO shader compiler (más rápido)
export mesa_glthread=true          # Multi-thread GL

# Gaming
export PROTON_ENABLE_NVAPI=1       # NVIDIA API en Proton
export DXVK_ASYNC=1                # Async shader compilation
export WINE_FULLSCREEN_FSR=1       # FidelityFX Super Resolution
```

Ver en StreaminOS:
```bash
cat /home/streaminos/.profile
```

---

## 📡 IPC: Controlando Sway

Sway expone un **IPC socket** para control remoto.

### Comandos con swaymsg

```bash
# Ver todos los outputs
swaymsg -t get_outputs

# Ver todas las ventanas
swaymsg -t get_tree

# Ver workspaces
swaymsg -t get_workspaces

# Ejecutar un comando
swaymsg exec firefox

# Mover una ventana
swaymsg move container to workspace 2

# Cambiar layout
swaymsg layout tabbed

# Recargar configuración
swaymsg reload
```

### Ejemplo: Script para Gestionar Juegos

```bash
#!/bin/bash
# Lanzar juego en workspace dedicado

swaymsg workspace 1
swaymsg exec steam steam://rungameid/730  # CS2
swaymsg fullscreen enable
```

---

## 🔍 Troubleshooting Sway

### Sway no arranca

```bash
# Ver logs
journalctl --user -u sway.service

# Errores comunes:
# "XDG_RUNTIME_DIR is not set"
→ Asegúrate que está en .bashrc o el service

# "Failed to initialize EGL"
→ Problemas con GPU, ver siguiente sección

# "No outputs found"
→ GPU sin output disponible, necesitas DRM
```

### Verificar que Sway está corriendo

```bash
# Ver proceso
pgrep -u streaminos -a | grep sway

# Ver socket
ls -la /run/user/1100/wayland-*

# Conectar al socket
WAYLAND_DISPLAY=wayland-1 XDG_RUNTIME_DIR=/run/user/1100 swaymsg -t get_version
```

### Testear Wayland apps

```bash
# Lanzar una app de prueba
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 weston-terminal
```

---

## 🎓 Ejercicios Prácticos

```bash
# 1. Ver si Sway está corriendo
pgrep -u streaminos sway

# 2. Ver outputs disponibles
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg -t get_outputs | head -20

# 3. Ver workspaces
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg -t get_workspaces

# 4. Ver logs de Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 journalctl --user -u sway.service -n 50

# 5. Ver variables de entorno de Sway
cat /proc/$(pgrep sway)/environ | tr '\0' '\n' | grep -E "(XDG|WAYLAND|DISPLAY)"

# 6. Recargar configuración de Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg reload
```

---

## 🔮 El Futuro: Wayland se Come a X11

**Estado actual (2025):**
- GNOME: 100% Wayland por defecto
- KDE Plasma: 99% Wayland (casi completo)
- Fedora: Wayland por defecto desde 2016
- Ubuntu: Wayland por defecto desde 22.04
- Arch: Puedes usar lo que quieras

**X11 está siendo deprecado** por todos los proyectos principales. StreaminOS está adelante de la curva usando solo Wayland.

---

## 📚 Profundizar Más

- `man sway` - Sway manual
- `man sway.5` - Sway configuration
- `man swaymsg` - Sway IPC
- [Sway Wiki](https://github.com/swaywm/sway/wiki)
- [Wayland Architecture](https://wayland.freedesktop.org/architecture.html)
- [Wayland Book](https://wayland-book.com/)

---

**Siguiente:** [04-user-architecture.md](04-user-architecture.md) - Arquitectura profunda de usuarios →
