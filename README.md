<div align="center">
                  
# windowVM

### Gestor de Máquinas Virtuales con interfaz gráfica moderna en Python + QEMU

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-blue?style=for-the-badge)](https://docs.python.org/3/library/tkinter.html)
[![QEMU](https://img.shields.io/badge/Backend-QEMU-FF6600?style=for-the-badge)](https://www.qemu.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

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

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/David4524-maker/windowVM.git
cd windowVM
