# 09 - Referencia Rápida de Comandos

## 🎯 Cheatsheet de StreaminOS

Esta es tu referencia rápida para gestionar StreaminOS. Todos los comandos más usados en un solo lugar.

---

## 👤 Gestión de Usuarios

```bash
# Ver información del usuario streaminos
id streaminos
groups streaminos

# Ver todos los procesos de streaminos
pgrep -u streaminos -a
ps aux | grep streaminos

# Ejecutar comando como streaminos
sudo -u streaminos [comando]

# Cambiar a usuario streaminos (shell interactivo)
sudo -i -u streaminos

# Ver sesiones activas
loginctl list-sessions
loginctl show-session [número]

# Terminar sesión de streaminos
sudo loginctl terminate-user streaminos
```

---

## 🔧 Systemd - Servicios

### System Services (root)

```bash
# Listar todos los servicios
systemctl list-units --type=service

# Estado de un servicio
systemctl status [servicio].service

# Iniciar/Parar/Reiniciar
systemctl start [servicio]
systemctl stop [servicio]
systemctl restart [servicio]

# Habilitar/Deshabilitar (auto-start)
systemctl enable [servicio]
systemctl disable [servicio]

# Ver servicios fallidos
systemctl --failed

# Recargar configuración
systemctl daemon-reload
```

### User Services (streaminos)

```bash
# IMPORTANTE: User services necesitan XDG_RUNTIME_DIR

# Atajo para streaminos
alias sctl='sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user'

# Con el alias:
sctl status sway.service
sctl restart sway.service
sctl list-units

# Sin alias (forma completa):
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user status sway.service
```

---

## 📊 Logs con Journalctl

```bash
# Ver todos los logs
journalctl

# Logs de un servicio system
journalctl -u [servicio].service

# Logs de user service
journalctl --user -u [servicio].service
# O para streaminos:
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 journalctl --user -u sway.service

# Últimas N líneas
journalctl -u sway.service -n 50

# Seguir en tiempo real (tail -f)
journalctl -u sway.service -f

# Solo errores
journalctl -u sway.service -p err

# Desde hace X tiempo
journalctl -u sway.service --since "1 hour ago"
journalctl -u sway.service --since "2025-10-28 20:00:00"

# Boot actual
journalctl -b

# Boot anterior
journalctl -b -1

# Listar boots
journalctl --list-boots

# Kernel logs
journalctl -k
dmesg
```

---

## 🖥️ Sway - Compositor

### Estado y Gestión

```bash
# Ver si Sway está corriendo
pgrep -a sway
pgrep -u streaminos sway

# Status del servicio
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user status sway.service

# Logs de Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 journalctl --user -u sway.service -f

# Reiniciar Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user restart sway.service

# Verificar config de Sway
sudo -u streaminos sway -C /home/streaminos/.config/sway/config
```

### Control con swaymsg

```bash
# Atajo
alias swmsg='sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg'

# Ver outputs (monitores)
swmsg -t get_outputs

# Ver ventanas abiertas
swmsg -t get_tree

# Ver workspaces
swmsg -t get_workspaces

# Ejecutar programa
swmsg exec firefox

# Recargar configuración
swmsg reload

# Cerrar Sway
swmsg exit
```

---

## 🎮 GPU y Renderizado

```bash
# Ver GPUs instaladas
lspci | grep VGA
lspci | grep 3D

# Ver dispositivos DRM
ls -la /dev/dri/

# Ver permisos de GPU
ls -l /dev/dri/card*
# Deben estar en grupo 'video'

# Ver módulos de kernel de GPU
lsmod | grep amdgpu
lsmod | grep i915     # Intel
lsmod | grep nouveau  # NVIDIA

# Info de GPU AMD
glxinfo | grep -E "(OpenGL vendor|OpenGL renderer)"
vulkaninfo | head -50

# Logs de GPU en kernel
dmesg | grep -E "(drm|amdgpu|gpu)" | tail -50
```

---

## 📁 Archivos y Configuración

### Ubicaciones Importantes

```bash
# Configuración de streaminos
/home/streaminos/.config/sway/config       # Sway config
/home/streaminos/.config/systemd/user/     # User services
/home/streaminos/.profile                  # Environment vars
/home/streaminos/.bashrc                   # Bash config

# Configuración del sistema
/etc/systemd/system/getty@tty1.service.d/autologin.conf  # Auto-login
/etc/security/limits.d/streaminos.conf                    # PAM limits
/etc/sudoers.d/noid                                       # Sudo config

# Sockets
/run/user/1100/                            # XDG_RUNTIME_DIR
/run/user/1100/wayland-*                   # Wayland sockets
```

### Ver/Editar Configs

```bash
# Ver config de Sway
cat /home/streaminos/.config/sway/config
sudo nano /home/streaminos/.config/sway/config

# Ver service de Sway
cat /home/streaminos/.config/systemd/user/sway.service

# Ver auto-login
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf

# Ver variables de entorno
cat /home/streaminos/.profile
```

---

## 🔍 Diagnóstico Completo

```bash
# Script de diagnóstico rápido
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 bash << 'EOF'
echo "=== Usuario streaminos ==="
id

echo -e "\n=== Sesiones activas ==="
loginctl list-sessions | grep streaminos

echo -e "\n=== Procesos de streaminos ==="
pgrep -u streaminos -a

echo -e "\n=== Sway service status ==="
systemctl --user status sway.service --no-pager -l | head -20

echo -e "\n=== Sockets Wayland ==="
ls -la $XDG_RUNTIME_DIR/wayland-*

echo -e "\n=== GPU devices ==="
ls -la /dev/dri/

echo -e "\n=== Últimos logs de Sway ==="
journalctl --user -u sway.service -n 10 --no-pager
EOF
```

---

## 🚀 Ansible - Deployment

```bash
# Ir al directorio de Ansible
cd /path/to/StreaminOS/ansible

# Verificar sintaxis
ansible-playbook playbooks/install.yml --syntax-check

# Dry-run (sin aplicar cambios)
ansible-playbook -i inventory/production.yml playbooks/install.yml --check

# Aplicar con diff
ansible-playbook -i inventory/production.yml playbooks/install.yml --check --diff

# Aplicar cambios reales
ansible-playbook -i inventory/production.yml playbooks/install.yml

# Aplicar solo un rol
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags user-setup
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags base
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags sway

# Múltiples tags
ansible-playbook -i inventory/production.yml playbooks/install.yml --tags "user-setup,base,sway"

# Verbose (debugging)
ansible-playbook -i inventory/production.yml playbooks/install.yml -vvv

# Probar conexión
ansible -i inventory/production.yml streamin_servers -m ping
```

---

## 📦 Pacman - Gestión de Paquetes

```bash
# Actualizar sistema
sudo pacman -Syu

# Instalar paquete
sudo pacman -S [paquete]

# Buscar paquete
pacman -Ss [búsqueda]

# Info de paquete instalado
pacman -Qi [paquete]

# Listar archivos de paquete
pacman -Ql [paquete]

# Eliminar paquete
sudo pacman -R [paquete]

# Eliminar con dependencias huérfanas
sudo pacman -Rs [paquete]

# Limpiar caché
sudo pacman -Sc

# Ver logs de instalaciones
cat /var/log/pacman.log
```

---

## 🌐 Red y SSH

```bash
# Conectar al servidor
ssh noid@192.168.0.19

# SSH con comando directo
ssh noid@192.168.0.19 "comando"

# Copiar archivos al servidor
scp archivo.txt noid@192.168.0.19:/path/to/dest/

# Copiar desde servidor
scp noid@192.168.0.19:/path/to/file.txt ./

# Copiar directorio recursivo
scp -r directorio/ noid@192.168.0.19:/path/

# Ver IP del servidor
ip addr show

# Probar conectividad
ping 192.168.0.19

# Ver puertos abiertos
ss -tulpn
netstat -tulpn
```

---

## 🔄 Reinicio y Mantenimiento

```bash
# Reiniciar servidor
ssh noid@192.168.0.19 sudo reboot

# Apagar servidor
ssh noid@192.168.0.19 sudo poweroff

# Ver uptime
uptime

# Ver memoria
free -h

# Ver disco
df -h

# Ver procesos top CPU
top
htop

# Ver procesos top memoria
ps aux --sort=-%mem | head -10
```

---

## 🎓 Comandos de Aprendizaje

```bash
# Manuales del sistema
man [comando]
man systemd.service
man sway
man journalctl

# Ayuda de comando
[comando] --help
systemctl --help

# Info de sistema
uname -a
hostnamectl
timedatectl

# Ver variables de entorno
env
printenv

# Ver ruta completa de comando
which sway
which systemctl

# Ver tipo de comando
type systemctl
```

---

## 💾 Aliases Útiles para .bashrc

Añade estos a tu `~/.bashrc` local para facilitar el trabajo:

```bash
# Alias para StreaminOS
alias sshstream='ssh noid@192.168.0.19'
alias ansibleplay='cd ~/dev/StreaminOS/ansible && ansible-playbook -i inventory/production.yml playbooks/install.yml'
alias sctl='sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user'
alias swmsg='sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 WAYLAND_DISPLAY=wayland-1 swaymsg'
alias slogs='sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 journalctl --user -u sway.service'
```

Luego:
```bash
source ~/.bashrc

# Ahora puedes usar:
sshstream
sctl status sway.service
swmsg -t get_outputs
slogs -f
```

---

## 📚 Recursos Rápidos

- **Man pages:** `man [comando]`
- **Arch Wiki:** https://wiki.archlinux.org
- **Sway Wiki:** https://github.com/swaywm/sway/wiki
- **Systemd docs:** https://www.freedesktop.org/software/systemd/man/

---

**Volver al:** [README.md](README.md)
