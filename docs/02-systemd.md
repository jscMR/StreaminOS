# 02 - Systemd: El Gestor del Sistema

## 🎯 Lo Que Vas a Aprender

- Qué es systemd y por qué reemplazó a SysVinit
- Diferencia entre servicios del sistema y servicios de usuario
- Cómo Sway arranca automáticamente en StreaminOS
- Logs con journalctl
- Units, targets y dependencies

---

## 🚀 ¿Qué es Systemd?

**Systemd** es el **init system** de Linux moderno. Es el primer proceso que arranca (PID 1) y gestiona TODO el sistema.

```bash
# Ver el proceso 1
ps aux | grep "PID\|systemd" | head -2
# USER  PID  %CPU %MEM    VSZ   RSS TTY  STAT START   TIME COMMAND
# root    1   0.0  0.0  22536 13036 ?    Ss   20:05   0:00 /sbin/init
```

### ¿Qué Hace Systemd?

1. **Arranca servicios** (nginx, sshd, etc.)
2. **Gestiona el orden** de arranque (dependencias)
3. **Monitorea procesos** y los reinicia si fallan
4. **Captura logs** centralizados con journald
5. **Gestiona usuarios** con logind
6. **Controla targets** (multi-user, graphical, etc.)

---

## 📦 Units: La Unidad Básica

En systemd, **todo es un unit**:

| Tipo | Extensión | Propósito | Ejemplo |
|------|-----------|-----------|---------|
| **Service** | `.service` | Demonios y procesos | `sshd.service`, `sway.service` |
| **Target** | `.target` | Grupos de units | `multi-user.target`, `graphical.target` |
| **Socket** | `.socket` | Activación por socket | `sshd.socket` |
| **Timer** | `.timer` | Tareas programadas (cron) | `backup.timer` |
| **Mount** | `.mount` | Puntos de montaje | `home.mount` |

```bash
# Listar todos los units
systemctl list-units

# Listar solo servicios
systemctl list-units --type=service

# Ver un unit específico
systemctl status sshd.service
```

---

## �� System vs User Services

**Diferencia CRÍTICA en StreaminOS:**

### System Services (root)
- Gestionados por el systemd del sistema (PID 1)
- Se ejecutan como `root` por defecto
- Ubicación: `/etc/systemd/system/` o `/usr/lib/systemd/system/`
- Arrancan al boot del sistema

```bash
# Listar system services
systemctl list-units --type=service

# Ejemplo: SSH daemon
systemctl status sshd.service
```

### User Services (usuario normal)
- Gestionados por el systemd del USUARIO
- Se ejecutan como ese usuario (sin root)
- Ubicación: `~/.config/systemd/user/`
- Arrancan cuando el usuario hace login

```bash
# Listar user services de streaminos
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user list-units

# Ejemplo: Sway en StreaminOS
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user status sway.service
```

### ¿Por Qué Usar User Services?

**StreaminOS usa user services para Sway** por estas razones:

1. **Seguridad**: Sway NO corre como root
2. **Aislamiento**: El crash de Sway no afecta al sistema
3. **User context**: Sway tiene acceso automático a los archivos del usuario
4. **XDG_RUNTIME_DIR**: Automáticamente configurado

---

## 🎬 Anatomía de un Service: sway.service

Veamos el servicio que creamos para Sway:

```ini
# Ubicación: /home/streaminos/.config/systemd/user/sway.service

[Unit]
Description=Sway Wayland Compositor
Documentation=man:sway(5)
BindsTo=graphical-session.target
Wants=graphical-session-pre.target
After=graphical-session-pre.target

[Service]
Type=simple
ExecStart=/usr/bin/sway
Restart=on-failure
RestartSec=5

# Variables de entorno
Environment=XDG_CONFIG_HOME=/home/streaminos/.config
Environment=XDG_DATA_HOME=/home/streaminos/.local/share
Environment=MOZ_ENABLE_WAYLAND=1
Environment=RADV_PERFTEST=aco

[Install]
WantedBy=graphical-session.target
```

### Desglose Línea por Línea

#### Sección [Unit]

```ini
Description=Sway Wayland Compositor
```
- Descripción human-readable

```ini
BindsTo=graphical-session.target
```
- Si `graphical-session.target` se detiene, Sway también
- **BindsTo** = dependencia fuerte

```ini
Wants=graphical-session-pre.target
After=graphical-session-pre.target
```
- Espera a que `graphical-session-pre.target` esté listo
- **Wants** = dependencia suave (no falla si no existe)
- **After** = orden de arranque

#### Sección [Service]

```ini
Type=simple
```
- El proceso principal NO hace fork (permanece en primer plano)

```ini
ExecStart=/usr/bin/sway
```
- Comando que ejecuta el servicio

```ini
Restart=on-failure
RestartSec=5
```
- Si Sway crashea, reiniciarlo automáticamente
- Esperar 5 segundos antes de reiniciar

```ini
Environment=XDG_CONFIG_HOME=/home/streaminos/.config
```
- Variables de entorno para el proceso

#### Sección [Install]

```ini
WantedBy=graphical-session.target
```
- Al ejecutar `systemctl --user enable sway.service`, se crea un symlink en `graphical-session.target.wants/`
- Cuando `graphical-session.target` arranca, Sway arranca también

---

## 🔄 Ciclo de Vida de un Servicio

```
┌─────────────┐
│   inactive  │  (no cargado en memoria)
└─────────────┘
       │
       │ systemctl start
       ▼
┌─────────────┐
│   active    │  (running)
│   (running) │
└─────────────┘
       │
       │ crash o stop
       ▼
┌─────────────┐
│   failed    │  (salió con error)
└─────────────┘
       │
       │ restart (si Restart=on-failure)
       ▼
┌─────────────┐
│   active    │
└─────────────┘
```

### Comandos de Gestión

```bash
# Iniciar un servicio
systemctl --user start sway.service

# Detener
systemctl --user stop sway.service

# Reiniciar
systemctl --user restart sway.service

# Ver estado
systemctl --user status sway.service

# Habilitar (arrancar al login)
systemctl --user enable sway.service

# Deshabilitar
systemctl --user disable sway.service

# Ver logs
journalctl --user -u sway.service

# Ver logs en tiempo real
journalctl --user -u sway.service -f
```

---

## 🎯 Targets: Puntos de Sincronización

Los **targets** son grupos de units que representan un estado del sistema.

```bash
# Ver targets activos
systemctl list-units --type=target

# Targets comunes
multi-user.target      # Sistema multi-usuario (sin GUI)
graphical.target       # Con interfaz gráfica (X11/Wayland)
rescue.target          # Modo de rescate (single-user)
```

### Targets de Usuario

```bash
# Para user services
default.target                  # Target por defecto
graphical-session.target        # Sesión gráfica de usuario
graphical-session-pre.target    # Antes de la sesión gráfica
```

**En StreaminOS:**
- Cuando `streaminos` hace login → `graphical-session.target` arranca
- `sway.service` está en `graphical-session.target.wants/`
- Resultado: Sway arranca automáticamente

---

## 📊 Journalctl: Ver Logs

Systemd captura **todos los logs** en un journal binario centralizado.

### Comandos Esenciales

```bash
# Ver todos los logs
journalctl

# Logs de un servicio específico
journalctl -u sshd.service

# User service logs
journalctl --user -u sway.service

# Últimas 50 líneas
journalctl -u sway.service -n 50

# Seguir en tiempo real (como tail -f)
journalctl -u sway.service -f

# Logs desde hace 1 hora
journalctl -u sway.service --since "1 hour ago"

# Logs entre fechas
journalctl -u sway.service --since "2025-10-28 20:00:00" --until "2025-10-28 20:30:00"

# Solo errores
journalctl -u sway.service -p err

# Con más detalles
journalctl -u sway.service -o verbose
```

### Niveles de Prioridad

| Nivel | Número | Uso |
|-------|--------|-----|
| emerg | 0 | Sistema inutilizable |
| alert | 1 | Acción inmediata requerida |
| crit | 2 | Condiciones críticas |
| err | 3 | Errores |
| warning | 4 | Advertencias |
| notice | 5 | Normal pero significativo |
| info | 6 | Informativo |
| debug | 7 | Debug |

```bash
# Solo errores y críticos
journalctl -u sway.service -p err
```

---

## 🔍 Troubleshooting con Systemd

### Mi servicio no arranca

```bash
# 1. Ver el estado
systemctl --user status sway.service

# 2. Ver los últimos logs
journalctl --user -u sway.service -n 50

# 3. Ver si hay errores de sintaxis en el unit file
systemd-analyze verify ~/.config/systemd/user/sway.service

# 4. Recargar configuración después de editar
systemctl --user daemon-reload

# 5. Ver dependencias
systemctl --user list-dependencies sway.service
```

### Mi servicio se reinicia constantemente

```bash
# Ver cuántas veces ha reiniciado
systemctl --user status sway.service
# Mira la línea "Tasks" y "Restarts"

# Ver los crashes
journalctl --user -u sway.service | grep -i "failed\|error\|crash"

# Desactivar el auto-restart temporalmente
# Editar el service y comentar:
# Restart=on-failure
```

### Variables de entorno no se cargan

```bash
# Para user services, SIEMPRE necesitas XDG_RUNTIME_DIR
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user status sway.service

# Ver variables de entorno de un proceso
cat /proc/$(pgrep sway)/environ | tr '\0' '\n'
```

---

## 💡 Auto-start al Login: getty + systemd

**Flujo completo en StreaminOS:**

```
1. Sistema arranca
   ↓
2. systemd (PID 1) arranca
   ↓
3. getty@tty1.service arranca
   (configurado con --autologin streaminos)
   ↓
4. streaminos hace login automáticamente
   ↓
5. systemd --user (del usuario streaminos) arranca
   ↓
6. graphical-session.target se activa
   ↓
7. sway.service arranca (porque está en graphical-session.target.wants/)
   ↓
8. ¡Sway corriendo! 🎉
```

Ver el auto-login:
```bash
# Ver configuración de getty
cat /etc/systemd/system/getty@tty1.service.d/autologin.conf

# Ver sesiones activas
loginctl list-sessions

# Ver detalles de la sesión de streaminos
loginctl show-session 2
```

---

## 🎓 Ejercicios Prácticos

```bash
# 1. Ver todos los servicios del sistema
systemctl list-units --type=service --all

# 2. Ver servicios de usuario de streaminos
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user list-units

# 3. Ver el estado de Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user status sway.service

# 4. Ver logs de Sway en tiempo real
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 journalctl --user -u sway.service -f

# 5. Reiniciar Sway
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user restart sway.service

# 6. Ver dependencias
sudo -u streaminos XDG_RUNTIME_DIR=/run/user/1100 systemctl --user list-dependencies sway.service
```

---

## 📚 Profundizar Más

- `man systemd.unit` - Sintaxis de unit files
- `man systemd.service` - Service units en detalle
- `man systemctl` - Comandos de gestión
- `man journalctl` - Ver logs
- [Systemd - Arch Wiki](https://wiki.archlinux.org/title/Systemd)
- [Understanding Systemd Units](https://www.freedesktop.org/software/systemd/man/systemd.unit.html)

---

**Siguiente:** [03-wayland-sway.md](03-wayland-sway.md) - Compositors y Wayland →
