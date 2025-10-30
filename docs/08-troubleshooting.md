# 08 - Guía de Troubleshooting

## 🎯 Objetivo

Esta guía te enseña a **diagnosticar y resolver problemas** en StreaminOS usando herramientas profesionales de Linux.

---

## 🔧 Herramientas Esenciales

### 1. journalctl - Ver Logs

```bash
# Logs del sistema completo
journalctl

# Logs de un servicio
journalctl -u sway.service

# User service
journalctl --user -u sway.service

# Últimas 50 líneas
journalctl -u sway.service -n 50

# Seguir en tiempo real
journalctl -u sway.service -f

# Solo errores
journalctl -u sway.service -p err

# Desde hace X tiempo
journalctl -u sway.service --since "1 hour ago"
journalctl -u sway.service --since "2025-10-28 20:00:00"
```

### 2. systemctl - Estado de Servicios

```bash
# Estado de un servicio
systemctl status sshd.service

# User service
systemctl --user status sway.service

# Listar todos
systemctl list-units --type=service

# Ver por qué falló
systemctl status sway.service --no-pager -l

# Ver dependencias
systemctl list-dependencies sway.service
```

### 3. pgrep/ps - Ver Procesos

```bash
# Buscar procesos por nombre
pgrep -a sway

# Procesos de un usuario
pgrep -u streaminos -a

# Árbol de procesos
ps auxf

# Proceso específico con detalles
ps aux | grep sway
```

### 4. loginctl - Gestión de Sesiones

```bash
# Ver sesiones activas
loginctl list-sessions

# Detalles de una sesión
loginctl show-session 2

# Sesiones de un usuario
loginctl list-sessions | grep streaminos

# Propiedades de sesión
loginctl session-status 2
```

---

## 🐛 Problemas Comunes y Soluciones

### Problema 1: Sway no arranca

**Síntomas:**
```bash
pgrep sway
# (sin output)

systemctl --user status sway.service
# ● sway.service - Sway Wayland Compositor
#      Active: failed
```

**Diagnóstico:**
```bash
# Ver los logs
journalctl --user -u sway.service -n 50

# Errores comunes y soluciones:
```

#### Error: "XDG_RUNTIME_DIR is not set"

```bash
# Ver el service file
cat ~/.config/systemd/user/sway.service

# Debe tener:
Environment=XDG_RUNTIME_DIR=/run/user/1100
```

**Solución:**
```bash
# Editar service
nano ~/.config/systemd/user/sway.service

# Agregar en [Service]:
Environment=XDG_RUNTIME_DIR=/run/user/%U

# Recargar y reiniciar
systemctl --user daemon-reload
systemctl --user restart sway.service
```

#### Error: "Failed to initialize EGL"

```bash
journalctl --user -u sway.service | grep EGL
# [ERROR] Failed to initialize EGL context
```

**Causa:** GPU no accesible o falta de drivers

**Solución:**
```bash
# Verificar que streaminos está en grupo video
groups streaminos | grep video

# Verificar dispositivos DRM
ls -la /dev/dri/
# Deben existir card0, card1, renderD128

# Verificar permisos
ls -l /dev/dri/card0
# crw-rw----+ 1 root video ...
#             ^^^^ grupo video

# Si falta grupo, agregarlo
sudo usermod -aG video streaminos

# Reiniciar sesión
sudo loginctl terminate-user streaminos
```

---

### Problema 2: Auto-login no funciona

**Síntomas:**
```bash
# streaminos no aparece en sesiones
loginctl list-sessions
# Solo aparece noid
```

**Diagnóstico:**
```bash
# Ver configuración de getty
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf

# Ver logs de getty
journalctl -u getty@tty1.service -n 30
```

**Solución:**

Si `autologin.conf` no existe:
```bash
# Recrear con Ansible
cd /path/to/StreaminOS/ansible
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags autologin
```

Si existe pero no funciona:
```bash
# Verificar sintaxis
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf
# Debe ser:
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin streaminos --noclear %I $TERM

# Recargar y reiniciar
sudo systemctl daemon-reload
sudo systemctl restart getty@tty1.service

# Verificar en 5 segundos
sleep 5 && loginctl list-sessions
```

---

### Problema 3: Sway arranca pero crashea

**Síntomas:**
```bash
systemctl --user status sway.service
# Active: activating (auto-restart)
# Se reinicia constantemente
```

**Diagnóstico:**
```bash
# Ver todos los crashes
journalctl --user -u sway.service | grep -C 5 "Failed\|Stopped"

# Ver última ejecución
journalctl --user -u sway.service -n 100 --no-pager
```

**Errores comunes:**

#### Config inválido
```bash
# Testear config manualmente
sudo -u streaminos sway -C /home/streaminos/.config/sway/config

# Si hay error, muestra la línea:
# Error on line 15: Unknown command 'foo'
```

**Solución:**
```bash
# Editar config
sudo nano /home/streaminos/.config/sway/config

# O regenerar con Ansible
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags base,sway
```

#### Falta `swaybg`
```bash
journalctl --user -u sway.service | grep swaybg
# failed to execute 'swaybg': No such file or directory
```

**Solución:**
```bash
# Instalar swaybg
sudo pacman -S swaybg

# Reiniciar Sway
systemctl --user restart sway.service
```

---

### Problema 4: No puedo conectar con swaymsg

**Síntomas:**
```bash
swaymsg -t get_outputs
# Unable to retrieve socket path
```

**Diagnóstico:**
```bash
# Verificar socket
ls -la /run/user/1100/wayland-*

# Si no existe, Sway no está corriendo
pgrep -u streaminos sway
```

**Solución:**
```bash
# Asegurarse que las variables estén configuradas
export XDG_RUNTIME_DIR=/run/user/1100
export WAYLAND_DISPLAY=wayland-1

# Ahora probar
swaymsg -t get_outputs

# Si sigue sin funcionar, ejecutar como streaminos
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg -t get_outputs
```

---

### Problema 5: GPU no detectada

**Síntomas:**
```bash
lspci | grep VGA
# (sin output)

ls /dev/dri/
# ls: cannot access '/dev/dri/': No such file or directory
```

**Diagnóstico:**
```bash
# Ver si el kernel detecta la GPU
lspci -v | grep -A 10 VGA

# Ver módulos del kernel cargados
lsmod | grep -E "(amdgpu|i915|nouveau)"

# Ver logs del kernel
dmesg | grep -E "(drm|gpu|amdgpu)" | tail -50
```

**Solución para AMD:**
```bash
# Instalar drivers
sudo pacman -S mesa vulkan-radeon

# Cargar módulo
sudo modprobe amdgpu

# Hacer permanente
echo "amdgpu" | sudo tee /etc/modules-load.d/amdgpu.conf

# Reiniciar
sudo reboot
```

---

## 🔎 Diagnóstico Paso a Paso

### Cuando algo no funciona

**1. ¿Está el servicio corriendo?**
```bash
systemctl --user status sway.service
```

**2. ¿Qué dicen los logs?**
```bash
journalctl --user -u sway.service -n 50
```

**3. ¿Existen los procesos?**
```bash
pgrep -u streaminos -a
```

**4. ¿Están las variables de entorno?**
```bash
cat /proc/$(pgrep sway)/environ | tr '\0' '\n'
```

**5. ¿Hay permisos correctos?**
```bash
groups streaminos
ls -la /dev/dri/
```

**6. ¿Funciona manualmente?**
```bash
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 sway
# (probar iniciar manualmente)
```

---

## 📊 Comandos de Diagnóstico Rápido

```bash
# Estado general del sistema
systemctl status

# Servicios fallidos
systemctl --failed

# User services fallidos
systemctl --user --failed

# Ver todo streaminos
ps aux | grep streaminos
loginctl list-sessions | grep streaminos
pgrep -u streaminos -a

# GPU y DRM
ls -la /dev/dri/
lspci | grep VGA
groups streaminos | grep video

# Sockets de Wayland
ls -la /run/user/1100/wayland-*

# Verificación completa de Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 bash -c '
  echo "=== Usuario ==="
  id
  echo "=== Sway corriendo ==="
  pgrep -a sway
  echo "=== Socket Wayland ==="
  ls -la $XDG_RUNTIME_DIR/wayland-*
  echo "=== Service status ==="
  systemctl --user status sway.service --no-pager
'
```

---

## 🆘 Cuando Todo Falla

### Reset Completo

```bash
# 1. Parar todo
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user stop sway.service

# 2. Limpiar procesos colgados
pkill -u streaminos -9

# 3. Terminar sesión
sudo loginctl terminate-user streaminos

# 4. Limpiar sockets
sudo rm -rf /run/user/1100/wayland-*

# 5. Reiniciar getty (auto-login)
sudo systemctl restart getty@tty1.service

# 6. Verificar
sleep 5 && pgrep -u streaminos -a
```

### Reinstalar User Service

```bash
cd /path/to/StreaminOS/ansible

# Recrear todo el usuario
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags user-setup

# Reiniciar sistema
ssh noid@192.168.0.19 sudo reboot
```

---

## 📚 Logs Importantes

### Dónde buscar

```bash
# System logs
/var/log/pacman.log          # Instalaciones de paquetes
/var/log/Xorg.0.log          # Xorg (si se usa)

# Systemd journal
journalctl -b                # Boot actual
journalctl -b -1             # Boot anterior
journalctl --list-boots      # Lista de boots

# User services
journalctl --user            # Todos los user logs

# Kernel
dmesg                        # Mensajes del kernel
journalctl -k                # Kernel logs vía systemd
```

### Exportar Logs para Soporte

```bash
# Exportar últimos 1000 logs de Sway
journalctl --user -u sway.service -n 1000 > sway-logs.txt

# Exportar boot actual completo
journalctl -b > boot-log.txt

# Información del sistema
cat > system-info.txt << EOF
=== Sistema ===
$(uname -a)

=== GPU ===
$(lspci | grep VGA)

=== DRM ===
$(ls -la /dev/dri/)

=== Usuario streaminos ===
$(id streaminos)

=== Sesiones ===
$(loginctl list-sessions)

=== Procesos ===
$(pgrep -u streaminos -a)
EOF
```

---

## 💡 Tips Profesionales

### Habilitar Debug Logging

Para Sway:
```bash
# Editar service
nano ~/.config/systemd/user/sway.service

# Cambiar ExecStart a:
ExecStart=/usr/bin/sway -d 2>&1 | tee /tmp/sway-debug.log

# Recargar
systemctl --user daemon-reload
systemctl --user restart sway.service

# Ver debug
tail -f /tmp/sway-debug.log
```

### Monitorear en Tiempo Real

```bash
# Terminal 1: Ver logs
journalctl --user -u sway.service -f

# Terminal 2: Ver procesos
watch -n 1 'pgrep -u streaminos -a'

# Terminal 3: Ver sesiones
watch -n 1 'loginctl list-sessions'
```

---

## 📖 Siguiente Paso

Si después de todo esto sigues teniendo problemas:

1. Busca en los logs el error exacto
2. Google: "sway [error exacto]"
3. [Sway GitHub Issues](https://github.com/swaywm/sway/issues)
4. [Arch Wiki - Sway](https://wiki.archlinux.org/title/Sway)
5. [r/swaywm](https://reddit.com/r/swaywm)

**Recuerda:** El 90% de los problemas se resuelven mirando los logs con `journalctl`.

---

**Volver al:** [README.md](README.md)
