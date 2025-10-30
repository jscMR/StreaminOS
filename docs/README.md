# StreaminOS - Documentación Completa

Esta documentación te guiará a través de **todos los conceptos de Linux** que hacen funcionar StreaminOS, desde lo más básico hasta lo más avanzado.

## 📚 Índice de Documentación

### Fundamentos de Linux
1. **[Usuarios y Permisos](01-users-and-permissions.md)** 
   - Por qué usamos dos usuarios (noid y streaminos)
   - Grupos de Linux y para qué sirven
   - Permisos y seguridad
   - El principio de mínimo privilegio

2. **[Systemd - El Gestor del Sistema](02-systemd.md)**
   - Qué es systemd y por qué lo usamos
   - Servicios del sistema vs servicios de usuario
   - Cómo Sway arranca automáticamente
   - Logs y troubleshooting con journalctl

3. **[Wayland y Sway](03-wayland-sway.md)**
   - Diferencia entre X11 y Wayland
   - Por qué Sway es perfecto para streaming
   - Compositors de Wayland
   - Variables de entorno críticas (XDG_RUNTIME_DIR, etc.)

### Arquitectura de StreaminOS
4. **[Arquitectura de Usuarios](04-user-architecture.md)**
   - Diseño dual-user en profundidad
   - Auto-login en tty1
   - getty y agetty explicados
   - PAM y autenticación

5. **[GPU y Renderizado](05-gpu-rendering.md)**
   - DRM (Direct Rendering Manager)
   - /dev/dri/ y dispositivos de GPU
   - AMD vs NVIDIA en Linux
   - Hardware rendering vs software rendering

### Automatización con Ansible
6. **[Ansible Básico](06-ansible-basics.md)**
   - Conceptos: playbooks, roles, tasks
   - Inventarios y variables
   - Idempotencia
   - Tags y ejecución selectiva

7. **[Roles de StreaminOS](07-streaminos-roles.md)**
   - user-setup: creación del usuario de servicio
   - base: sistema base y Sway
   - Roles futuros (sunshine, steam, evdi)

### Troubleshooting y Debugging
8. **[Guía de Troubleshooting](08-troubleshooting.md)**
   - Cómo leer logs con journalctl
   - Debugging de servicios systemd
   - Problemas comunes y soluciones
   - Herramientas de diagnóstico

### Referencia Rápida
9. **[Comandos Útiles](09-quick-reference.md)**
   - Cheatsheet de comandos frecuentes
   - systemctl, journalctl, loginctl
   - Verificar estado del sistema

---

## 🎯 Cómo Usar Esta Documentación

**Si eres nuevo en Linux:** Empieza por los "Fundamentos de Linux" en orden.

**Si tienes experiencia:** Salta directo a "Arquitectura de StreaminOS".

**Si algo falla:** Ve a "Troubleshooting y Debugging".

Cada documento incluye:
- ✅ **Conceptos teóricos** explicados desde cero
- ✅ **Ejemplos prácticos** con comandos reales
- ✅ **Diagramas** para visualizar cómo funciona
- ✅ **Enlaces** a documentación oficial para profundizar

---

## 🚀 Lo Que Has Construido Hasta Ahora

Con StreaminOS has creado:

1. **Un sistema Linux profesional** con separación de usuarios
2. **Automatización completa** con Ansible reproducible
3. **Compositor Wayland funcionando** en modo headless
4. **Arquitectura preparada** para streaming de juegos con Sunshine
5. **Gestión moderna** con systemd user services

Todo esto **siguiendo las mejores prácticas de la industria**.

---

## 📖 Filosofía de Esta Documentación

No solo te explico **QUÉ** hace StreaminOS, sino:
- **POR QUÉ** está diseñado así
- **CÓMO** funciona internamente
- **CUÁNDO** usar cada approach
- **DÓNDE** buscar cuando algo falla

**Objetivo:** Que entiendas Linux a un nivel profundo, no solo copiar y pegar comandos.

---

Empieza por [01-users-and-permissions.md](01-users-and-permissions.md) →
