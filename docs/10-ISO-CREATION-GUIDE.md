# 10 - Creación de una ISO Personalizada (Respin)

## 🎯 Objetivo

Esta guía explica cómo transformar el proyecto Ansible de StreaminOS en una **imagen ISO instalable y personalizada**, similar a distribuciones como Nobara. Esto permite tener un sistema pre-configurado desde el momento de la instalación.

La herramienta clave para este proceso es **Archiso**, la utilidad oficial de Arch Linux para este propósito.

---

## 🏗️ Flujo de Trabajo: De Ansible a ISO

El concepto fundamental es ejecutar los playbooks de Ansible *durante* el proceso de construcción de la ISO, para que el sistema final ya contenga toda la configuración.

**Flujo Anterior:**
1. Instalar Arch Linux base.
2. Clonar el repositorio de StreaminOS.
3. Ejecutar `ansible-playbook`.

**Nuevo Flujo (Archiso):**
1. Definir un perfil de `archiso`.
2. Integrar el proyecto Ansible en el proceso de construcción.
3. Construir la imagen `.iso`.
4. Arrancar desde la ISO e instalar un sistema ya configurado.

---

## 📋 Plan de Acción Detallado

### Paso 1: Instalar Archiso y Preparar el Entorno

Primero, necesitas la herramienta `archiso` en tu sistema de desarrollo.

```bash
# 1. Instalar archiso
sudo pacman -S archiso

# 2. Copiar el perfil base 'releng' a un nuevo directorio
cp -r /usr/share/archiso/configs/releng/ ~/streaminos-iso-build
cd ~/streaminos-iso-build
```
El directorio `~/streaminos-iso-build` será ahora la base para tu respin.

### Paso 2: Integrar el Proyecto Ansible

El directorio `airootfs` dentro de tu perfil de build (`~/streaminos-iso-build/airootfs/`) es el sistema de archivos raíz (`/`) de la ISO final. Todo lo que pongas ahí, estará en el sistema "Live".

1.  **Instalar Ansible en la ISO:** El entorno Live necesita Ansible para ejecutar los playbooks. Edita el archivo `~/streaminos-iso-build/packages.x86_64` y añade `ansible-core` a la lista de paquetes.

2.  **Copiar tu Proyecto:** Copia tu proyecto `StreaminOS` completo a una ubicación dentro del `airootfs`.
    ```bash
    sudo cp -r /home/noid/dev/StreaminOS ~/streaminos-iso-build/airootfs/opt/StreaminOS
    ```

3.  **Ejecutar Ansible Durante el Build:** `archiso` ejecuta el script `airootfs/root/customize_airootfs.sh` dentro de un chroot al construir la imagen. Este es el lugar perfecto para lanzar Ansible.

    Edita `~/streaminos-iso-build/airootfs/root/customize_airootfs.sh` y añade al final:

    ```bash
    #!/bin/bash
    
    # ... (contenido existente del script) ...
    
    # --- PERSONALIZACIÓN CON ANSIBLE ---
    echo "==> Ejecutando Playbook de Ansible para StreaminOS"
    
    # Crear un inventario específico para el entorno de construcción local
    echo "[local]" > /opt/StreaminOS/inventory/iso
    echo "localhost ansible_connection=local" >> /opt/StreaminOS/inventory/iso
    
    # Ejecutar el playbook principal
    # Usamos --extra-vars para poder adaptar tasks si es necesario
    ansible-playbook -i /opt/StreaminOS/inventory/iso /opt/StreaminOS/playbooks/install.yml --extra-vars "is_chroot=true"
    
    # (Opcional pero recomendado) Limpiar los scripts de Ansible para no dejarlos en la ISO final
    rm -rf /opt/StreaminOS
    
    echo "==> Finalizada la personalización con Ansible"
    # --- FIN DE LA PERSONALIZACIÓN ---
    ```

### Paso 3: Configurar un Instalador (Opcional)

Para una experiencia tipo Nobara, necesitarás un instalador.
- **Simple:** El script `archinstall` que viene por defecto en la ISO de Arch.
- **Avanzado:** Integrar un instalador gráfico como `Calamares`. Esto es más complejo pero ofrece una experiencia de usuario final mucho más pulida.

### Paso 4: Construir y Probar la ISO

Una vez configurado el perfil, puedes construir la imagen.

```bash
# Desde el directorio ~/streaminos-iso-build
sudo ./build.sh -v
```

El archivo `.iso` final se encontrará en `~/streaminos-iso-build/out/`.

**¡Importante!** Siempre prueba la ISO generada en una máquina virtual (QEMU, VirtualBox) antes de instalarla en hardware real.

---

## 💡 Consideraciones Adicionales

- **Idempotencia:** Asegúrate de que tus roles de Ansible sean verdaderamente idempotentes. Se ejecutarán en un entorno `chroot` limpio cada vez, lo cual ayuda.
- **Tags de Ansible:** La variable `--extra-vars "is_chroot=true"` es muy poderosa. Puedes usarla en tus tasks para condicionar acciones que no deberían ejecutarse en un `chroot` (ej: `when: not is_chroot | default(false)`).
- **Limpieza:** Decide qué herramientas de construcción (como `ansible-core` mismo) quieres mantener en el sistema final. Puedes desinstalarlas al final del script `customize_airootfs.sh` para crear una imagen final más limpia.
