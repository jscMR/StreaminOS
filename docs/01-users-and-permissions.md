# 01 - Usuarios y Permisos en Linux

## 🎯 Lo Que Vas a Aprender

Después de leer esto entenderás:
- Por qué Linux usa múltiples usuarios
- Cómo funcionan los grupos
- Por qué StreaminOS usa dos usuarios separados
- Qué son los UIDs y GIDs
- El principio de "mínimo privilegio"

---

## 👤 Conceptos Fundamentales: Usuarios

### ¿Qué es un usuario en Linux?

En Linux, **todo proceso ejecuta como un usuario**. No hay programas "sin usuario". Esto es fundamental para la seguridad.

```bash
# Ver tu usuario actual
whoami

# Ver todos los procesos y sus usuarios
ps aux | head -10
```

**Cada usuario tiene:**
- **Username**: El nombre (ej: `noid`, `streaminos`, `root`)
- **UID** (User ID): Un número único (ej: 1000, 1100, 0)
- **Home directory**: Carpeta personal (ej: `/home/noid`)
- **Shell**: Programa que ejecuta comandos (ej: `/bin/bash`)
- **Grupos**: Uno o más grupos de permisos

### Los Tres Tipos de Usuarios

1. **root (UID 0)**: El superusuario, puede hacer TODO
2. **Usuarios del sistema (UID 1-999)**: Para servicios (nginx, mysql, etc.)
3. **Usuarios normales (UID 1000+)**: Personas reales

```bash
# Ver información de un usuario
id noid
# Salida: uid=1000(noid) gid=1000(noid) groups=1000(noid),998(wheel)

id streaminos
# Salida: uid=1100(streaminos) gid=1100(streaminos) groups=1100(streaminos),984(video),988(render),...
```

---

## 👥 Grupos: Compartir Permisos

### ¿Para qué sirven los grupos?

Los grupos permiten dar permisos a **múltiples usuarios** sin modificar archivos uno por uno.

**Ejemplo real en StreaminOS:**

El usuario `streaminos` necesita acceso a la GPU. En lugar de darle permisos individuales, lo agregamos al grupo `video`:

```bash
# Ver todos los grupos de un usuario
groups streaminos
# Salida: streaminos wheel audio input render video

# Ver qué usuarios están en el grupo 'video'
getent group video
# Salida: video:x:984:streaminos
```

### Grupos Importantes en StreaminOS

| Grupo | UID | Propósito |
|-------|-----|-----------|
| `video` | 984 | Acceso a `/dev/dri/*` (GPU) |
| `render` | 988 | Hardware rendering (aceleración) |
| `input` | 993 | Teclado, ratón, gamepads |
| `audio` | 996 | Dispositivos de audio |
| `wheel` | 998 | Puede usar `sudo` (en algunas distros) |

```bash
# Ver dispositivos de GPU
ls -l /dev/dri/
# crw-rw----+ 1 root video  226, 0 Oct 28 20:15 card0
#               ^^^^^ ^^^^^ 
#              owner group
```

El archivo `card0` pertenece al grupo `video`. Solo usuarios en ese grupo pueden acceder.

---

## 🏗️ La Arquitectura Dual de StreaminOS

### ¿Por Qué Dos Usuarios?

StreaminOS usa **dos usuarios separados** por seguridad y claridad:

```
┌─────────────────────────────────────┐
│ noid (UID 1000)                     │
│ Rol: Administrador                   │
│                                      │
│ ✓ SSH desde tu máquina local        │
│ ✓ Ejecuta Ansible                   │
│ ✓ Tiene sudo completo                │
│ ✓ Gestiona el servidor               │
│                                      │
│ Archivos en: /home/noid              │
└─────────────────────────────────────┘
            │
            │ Despliega y configura
            ▼
┌─────────────────────────────────────┐
│ streaminos (UID 1100)               │
│ Rol: Servicios de Streaming         │
│                                      │
│ ✓ Ejecuta Sway (compositor)         │
│ ✓ Ejecutará Sunshine (streaming)    │
│ ✓ Ejecutará Steam (juegos)          │
│ ✗ NO tiene acceso SSH                │
│ ✗ NO tiene sudo                      │
│                                      │
│ Archivos en: /home/streaminos        │
└─────────────────────────────────────┘
```

### Ventajas de Esta Arquitectura

1. **Seguridad**: Si Sunshine se compromete, el atacante NO tiene sudo
2. **Aislamiento**: Tus archivos personales en `/home/noid` están separados
3. **Claridad**: Saber quién hace qué es obvio
4. **Backup**: Solo necesitas respaldar `/home/streaminos` para los servicios
5. **Troubleshooting**: Los logs de servicios están bajo un solo usuario

### El Principio de Mínimo Privilegio

**Regla de oro:** Cada proceso debe tener SOLO los permisos que necesita, nada más.

- `streaminos` NO necesita:
  - ❌ SSH (no es un humano que se loguea)
  - ❌ sudo (no gestiona el sistema)
  - ❌ Acceso a `/home/noid`

- `streaminos` SÍ necesita:
  - ✅ GPU (grupo `video` y `render`)
  - ✅ Input devices (grupo `input`)
  - ✅ Audio (grupo `audio`)
  - ✅ Su home directory con sus configs

---

## 🔐 UIDs Fijos: ¿Por Qué 1100?

```yaml
# En group_vars/all.yml
streamin_uid: 1100
streamin_gid: 1100
```

**Razón:** Si reinstalamos StreaminOS, queremos que los archivos sigan perteneciendo al mismo usuario.

### Sin UID Fijo (PROBLEMA):
```bash
# Primera instalación
streaminos -> UID 1000

# Reinstalación (ya hay un usuario con UID 1000)
streaminos -> UID 1001  ← ¡DIFERENTE!

# Los archivos antiguos siguen siendo UID 1000
# streaminos (UID 1001) no puede accederlos
```

### Con UID Fijo (SOLUCIÓN):
```bash
# Primera instalación
streaminos -> UID 1100

# Reinstalación
streaminos -> UID 1100  ← SIEMPRE EL MISMO

# Los archivos con UID 1100 siguen siendo accesibles
```

---

## 🔍 Comandos de Diagnóstico

```bash
# Ver información completa de un usuario
id streaminos

# Ver qué usuario ejecuta un proceso
ps aux | grep sway
# streaminos  2327  0.5  0.5 /usr/bin/sway

# Ver propietario de un archivo
ls -l /home/streaminos/.config/sway/config
# -rw-r--r-- 1 streaminos streaminos 532 Oct 28 20:02 config
#              ^^^^^^^^^^^ ^^^^^^^^^^
#              owner       group

# Ver todos los procesos de un usuario
pgrep -u streaminos -a

# Cambiar a otro usuario (requiere sudo)
sudo -u streaminos bash

# Ver grupos de todos los usuarios
cat /etc/group | grep streaminos
```

---

## 💡 Preguntas Frecuentes

### ¿Por qué no usar solo root para todo?

**Malo:**
```bash
# Todo como root = desastre de seguridad
sudo sway  # Si Sway se explota, el atacante es root
```

**Bueno:**
```bash
# Sway como usuario normal
# Si se explota, el atacante solo es streaminos (sin sudo)
```

### ¿Por qué streaminos tiene el grupo 'wheel'?

En StreaminOS, `wheel` **NO le da sudo** (hemos deshabilitado eso). Solo lo agregamos para compatibilidad con ciertas herramientas que lo esperan.

Verificar:
```bash
sudo cat /etc/sudoers.d/streaminos
# (archivo no existe = sin sudo)
```

### ¿Puedo cambiar el nombre 'streaminos'?

Sí, pero tendrías que modificar:
- `group_vars/all.yml` → `streamin_user: tu_nombre`
- Volver a ejecutar Ansible

---

## 🎓 Ejercicios Prácticos

Conecta a tu servidor y ejecuta:

```bash
# 1. Ver qué usuarios existen
cat /etc/passwd | grep -E "(noid|streaminos)"

# 2. Ver el UID y grupos
id noid
id streaminos

# 3. Ver quién puede acceder a la GPU
ls -l /dev/dri/card0

# 4. Ver procesos de streaminos
ps aux | grep streaminos

# 5. Intentar acceder a archivos de noid como streaminos
sudo -u streaminos cat /home/noid/.bashrc
# (debería fallar con Permission denied)
```

---

## 📚 Profundizar Más

- `man useradd` - Crear usuarios
- `man usermod` - Modificar usuarios
- `man groups` - Ver grupos
- [Linux Users and Groups - Arch Wiki](https://wiki.archlinux.org/title/Users_and_groups)

---

**Siguiente:** [02-systemd.md](02-systemd.md) - Cómo systemd gestiona servicios →
