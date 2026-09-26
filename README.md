<img width="797" height="550" alt="Captura de pantalla 2026-09-19 195338" src="https://github.com/user-attachments/assets/fc5f5f84-3267-40d4-b3a5-ba785241208b" />
<div align="center">
                  
# windowVM

### Gestor de Máquinas Virtuales con interfaz gráfica moderna en Python + QEMU

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-blue?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![QEMU](https://img.shields.io/badge/Backend-QEMU-FF6600?style=for-the-badge)](https://www.qemu.org/)

**Crea, gestiona e inicia máquinas virtuales reales desde una interfaz amigable y colorida.**

[Características](#-características) • [Instalación](#-instalación) • [Uso](#-uso) • [Capturas](#-capturas) • [Roadmap](#-roadmap)

</div>

---

## Descripción

**windowVM** es una aplicación de escritorio desarrollada en **Python con Tkinter** que permite crear y administrar máquinas virtuales utilizando **QEMU** como motor de virtualización. Cuenta con un sistema de logros, persistencia de datos en JSON, un flujo de creación paso a paso y una interfaz gráfica que simula un diseño moderno tipo "CSS" mediante un diccionario de estilos centralizado.

> ⚠️ **Nota:** Este proyecto es educativo y está en desarrollo activo. Es ideal para aprender sobre interfaces gráficas, persistencia de datos y ejecución de subprocesos en Python.

---

## Características

-  **Interfaz gráfica moderna** con paleta de colores personalizable mediante un "pseudo-CSS" (`THEME`).
-  **Ventana redimensionable y maximizable** con elementos responsivos.
-  **Asistente de creación de VMs en 3 pasos**: Nombre + ISO → Hardware → Add-ons.
-  **Persistencia de datos**: Las VMs se guardan automáticamente en `windowvm_data.json`.
-  **Sistema de logros**: Desbloquea logros al crear tu primera VM, cargar una ISO o activar Add-ons.
-  **Especial Add-ons**:
  - Uso optimizado del SSD (caché `writeback`).
  - Carpeta compartida entre host y VM mediante `virtfs`.
-  **Arranque real con QEMU**: Ejecuta tus VMs con la configuración elegida.
-  **Gestión de VMs**: Inicia o elimina máquinas directamente desde la lista principal.
- **Interfaz temática**: Diseños personalizados con Canvas para los íconos y paneles decorativos.
<img width="898" height="592" alt="Captura de pantalla 2026-09-19 141924" src="https://github.com/user-attachments/assets/9afed402-88dd-4622-aab8-055839302a6b" />      

## Requisitos

Antes de ejecutar **windowVM**, asegúrate de tener instalado lo siguiente:

### Obligatorios

| Requisito | Versión | Descripción |
| :--- | :--- | :--- |
| **Python** | 3.10 o superior | Se recomienda Python 3.14. |
| **Tkinter** | Incluido | Viene por defecto con Python. |
| **QEMU** | Última estable | Motor de virtualización. |

### Recomendados

| Requisito | Descripción |
| :--- | :--- |
| **Virtualización por hardware** | Activa Intel VT-x o AMD-V en la BIOS/UEFI. |
| **Windows Hypervisor Platform (WHPX)** | Acelera QEMU en Windows. Habilitar en "Características de Windows" o con `DISM`. |
| **Controladores VirtIO** | Solo necesarios si activas los "Especial Add-ons" (para el SO invitado). |

---

### Descargar ISO

Puedes ir a [Internet Archive](https://archive.org) para descargar las ISO

---

### 2. Verificar QEMU en el PATH
Para que **windowVM** pueda ejecutar las ISOs correctamente, el ejecutable de QEMU debe estar accesible desde cualquier terminal de tu sistema.

* **Windows:** Instala QEMU y añade su ruta (por defecto `C:\Program Files\qemu`) a las *Variables de Entorno del Sistema* (PATH).
* **Linux (Ubuntu/Debian):** Ejecuta `sudo apt install qemu-system-x86 qemu-utils`
* **macOS:** Ejecuta `brew install qemu`

### 3. Ejecutar la aplicación
Una vez cumplidos los requisitos, arranca la interfaz gráfica ejecutando el script principal:

```bash
python windowvm.py
```

---

##  Uso del Probador de ISOs

El flujo de trabajo está optimizado para que pases de tener un archivo descargado a ver el sistema operativo corriendo en segundos:

1. **Crear Instancia:** Haz clic en **"Crear VM nueva +"**.
2. **Asignar e Importar:** Dale un nombre descriptivo a tu máquina y haz clic en **"Cargar ISO..."** para seleccionar tu instalador o entorno de pruebas (soporta `.iso` de Windows, distribuciones Linux, utilidades de rescate, etc.).
3. **Hardware a Medida:** Configura la memoria RAM y procesadores asignados.
4. **Ignorar Discos Vacíos:** Al presionar **"▶ Iniciar"**, el programa inyecta automáticamente el parámetro `-boot d` en QEMU. Esto fuerza al sistema virtual a ignorar el almacenamiento vacío e iniciar de manera prioritaria directo desde tu archivo ISO.

---

##  Aceleración por Hardware Integrada

Para evitar lentitud o congelamientos al emular sistemas modernos, **windowVM** detecta tu sistema operativo anfitrión y activa la aceleración nativa por hardware:

* **Windows:** Invoca de manera nativa la aceleración **WHPX** (Windows Hypervisor Platform).
* **Linux:** Se conecta directamente con el módulo de kernel **KVM**.
* **macOS:** Utiliza el framework nativo **HVF** (Hypervisor.framework).

> **Nota para usuarios de Windows:** Recuerda tener activada la característica opcional **"Plataforma de hipervisor de Windows"** en tu Panel de Control para que QEMU funcione a la velocidad de tu procesador real.


---

# Iconos

<img width="797" height="550" alt="Captura de pantalla 2026-09-19 195338" src="https://github.com/user-attachments/assets/4e7beda3-c6cd-4471-abc8-a94e5fe12a05" />


<div align="center">

### Desarrollado con Python, Tkinter y mucha pasión por los sistemas operativos.
¿Te ha gustado tanto? ¡Déjame una ⭐ en el repositorio! Esta a la derecha de Fork

</div>
