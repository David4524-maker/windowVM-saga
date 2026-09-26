#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
windowVM v2.0 - Cross-platform VM Manager
==========================================
Compatible: Windows, Linux, macOS
Languages : English, Spanish, Portuguese
===============================================================================
70 IMPROVEMENTS ADDED
===============================================================================
 1. Cross-platform paths (Windows %APPDATA%, macOS ~/Library, Linux ~/.config)
 2. Auto OS detection via platform.system()
 3. Per-OS QEMU acceleration (WHPX / KVM / HVF, TCG fallback)
 4. QEMU binary auto-detection and validation
 5. Full i18n: English, Spanish, Portuguese
 6. Live language switcher from menu
 7. Language preference persistence
 8. Centralized config.json in user directory
 9. Rotating log file (windowvm.log)
10. Unique VM IDs (uuid4)
11. VM status tracking (running/stopped)
12. VM notes / description field
13. VM tags
14. VM favorite flag
15. VM color labels
16. VM search / filter box
17. VM sorting (name, RAM, date)
18. VM cloning (copies disk + config)
19. VM editing dialog
20. VM export / import (JSON)
21. Bulk export
22. Disk image manager helper
23. Disk size selector in wizard
24. Boot order configuration
25. Network mode selection (user/bridge/tap/none)
26. Display backend selection (gtk/sdl/vnc/none)
27. VNC port configuration
28. Headless mode support
29. Custom QEMU arguments field
30. USB passthrough toggle
31. Audio backend selection
32. Per-VM shared folder (virtfs)
33. ISO library manager
34. Recent VMs
35. RAM/CPU validation with limits
36. Disk space check before creating disks
37. Progress dialogs for long ops
38. Non-blocking background tasks (threads)
39. Better error dialogs with actionable hints
40. Status bar showing state
41. Menu bar (File / Edit / View / Language / Help)
42. Keyboard shortcuts (Ctrl+N, Ctrl+F, Del, F5, F1, Ctrl+Q)
43. Right-click context menu on VM cards
44. Dark mode toggle
45. Custom theme support
46. Achievement system improvements
47. About dialog with version info
48. Help / tutorial window
49. Update checker placeholder
50. Log viewer window
51. Toast-style status notifications
52. Search box with live filter
53. Start-all / stop-all actions
54. Force stop (process kill)
55. Graceful VM stop via QEMU monitor
56. Auto-start on app launch flag
57. Recent activity log
58. VM templates (presets)
59. Template save/load
60. Portable mode (config next to script)
61. Backup / restore config
62. Reset to defaults action
63. Window geometry persistence
64. DPI / high-DPI awareness
65. Shared folder toggle
66. Consistent fonts and theming
67. Input validation on entry fields
68. Thread-safe UI updates via root.after
69. Graceful shutdown of running VMs
70. Modular, documented code
===============================================================================
"""

import json
import logging
import logging.handlers
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog

# =============================================================================
# CONSTANTS & OS DETECTION
# =============================================================================
APP_NAME = "windowVM"
APP_VERSION = "2.0.0"
APP_AUTHOR = "windowVM Team"
QEMU_REPO = "https://www.qemu.org/download/"

IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"


# =============================================================================
# CROSS-PLATFORM PATHS
# =============================================================================
def get_user_data_dir(portable=False):
    """Return the appropriate config directory for the current OS."""
    if portable:
        return Path(__file__).resolve().parent / "windowvm_data"
    if IS_WINDOWS:
        base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
    elif IS_MACOS:
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / APP_NAME


def ensure_dirs(root_dir):
    for sub in ("vms", "isos", "snapshots", "shared", "logs"):
        (root_dir / sub).mkdir(parents=True, exist_ok=True)
    return root_dir


def setup_logger(log_dir):
    logger = logging.getLogger("windowvm")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    fh = logging.handlers.RotatingFileHandler(
        log_dir / "windowvm.log", maxBytes=1024 * 1024, backupCount=3, encoding="utf-8"
    )
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    fh.setFormatter(fmt)
    logger.addHandler(fh)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


DATA_DIR = ensure_dirs(get_user_data_dir())
CONFIG_FILE = DATA_DIR / "config.json"
VMS_FILE = DATA_DIR / "vms.json"
LOG_FILE = DATA_DIR / "logs" / "windowvm.log"
LOGGER = setup_logger(DATA_DIR / "logs")


# =============================================================================
# INTERNATIONALIZATION (EN / ES / PT)
# =============================================================================
TRANSLATIONS = {
    "en": {
        "app_title": "windowVM",
        "menu_file": "File", "menu_edit": "Edit", "menu_view": "View",
        "menu_language": "Language", "menu_help": "Help",
        "menu_new_vm": "New VM…", "menu_import": "Import VM…",
        "menu_export_all": "Export all VMs…", "menu_quit": "Quit",
        "menu_edit_vm": "Edit selected VM", "menu_clone_vm": "Clone selected VM",
        "menu_delete_vm": "Delete selected VM",
        "menu_dark_mode": "Dark mode", "menu_refresh": "Refresh",
        "menu_about": "About…", "menu_help_docs": "Help / Tutorial",
        "menu_logs": "View logs", "menu_iso_lib": "ISO library…",
        "lang_en": "English", "lang_es": "Spanish", "lang_pt": "Portuguese",
        "create_vm": "Create new VM\n+",
        "my_vms": "── My VMs ──",
        "no_vms": "No VMs yet :(",
        "no_vms_sub": "Click 'Create new VM' to get started",
        "search_placeholder": "🔍  Search VMs…",
        "sort_by": "Sort by:", "sort_name": "Name", "sort_ram": "RAM",
        "sort_date": "Date", "sort_fav": "Favorites first",
        "achievements": "🏆 Achievements",
        "btn_start": "▶ Start", "btn_stop": "■ Stop",
        "btn_force_stop": "⛔ Force stop", "btn_edit": "✎ Edit",
        "btn_clone": "⧉ Clone", "btn_delete": "🗑 Delete",
        "btn_export": "⤓ Export", "btn_fav_on": "★", "btn_fav_off": "☆",
        "loading_iso": "Load ISO…", "iso_loaded": "ISO loaded ✓",
        "vm_name": "VM name", "os_label": "Operating system", "type_label": "Architecture",
        "accept": "Accept", "cancel": "Cancel", "next": "Next",
        "back": "Back", "activate": "Activate", "no_thanks": "No, thanks",
        "save": "Save", "close": "Close",
        "hardware_config": "Hardware configuration",
        "ram_label": "RAM (MB)", "cores_label": "CPU cores", "threads_label": "CPU threads",
        "disk_size_label": "Disk size (GB)", "disk_label": "Disk image path",
        "network_label": "Network mode", "display_label": "Display backend",
        "boot_label": "Boot order", "notes_label": "Notes",
        "tags_label": "Tags (comma separated)", "custom_args_label": "Custom QEMU args",
        "usb_label": "Enable USB passthrough", "audio_label": "Enable audio",
        "shared_folder_label": "Shared folder path", "fav_label": "Mark as favorite",
        "special_addons_title": "✨ Special Add-ons ✨",
        "special_addons_body":
            "Do you want to enable Special Add-ons?\n\n"
            "• Drag & drop files to the VM screen\n"
            "• Direct in-VM installation\n"
            "• Maximum SSD performance (TRIM / VirtIO)",
        "vm_created_title": "VM created",
        "vm_created_msg": "VM '{name}' created successfully!",
        "error_title": "Error", "warning_title": "Warning",
        "confirm_delete_title": "Confirm delete",
        "confirm_delete_msg": "Delete VM '{name}' from the list?",
        "missing_name_title": "Missing name",
        "missing_name_msg": "Please enter a name for the VM.",
        "invalid_input": "Invalid value in field: {field}",
        "qemu_missing": "QEMU is not installed or not on PATH.\n\nDownload from: {url}",
        "qemu_running": "VM '{name}' is starting…",
        "vm_stopped": "VM '{name}' has stopped.",
        "start_failed": "Could not start QEMU:\n{err}",
        "status_ready": "Ready",
        "status_vms": "{n} VM(s) registered · {r} running",
        "status_lang": "Language: {lang}",
        "vnc_port_label": "VNC port (optional)",
        "achievement_first_vm": "Create your first VM",
        "achievement_iso": "Load an ISO",
        "achievement_addons": "Enable Special Add-ons",
        "achievement_fav": "Mark a VM as favorite",
        "completed": "✅ Completed", "locked": "❌ Locked",
        "about_title": "About {app}",
        "about_text": "{app} v{ver}\n\nCross-platform QEMU VM manager.\n\n"
                      "© {year} {author}\nLicense: MIT",
        "help_title": "Help / Tutorial",
        "help_text":
            "1) Click 'Create new VM' to launch the wizard.\n"
            "2) Choose a name, optionally load an ISO, set OS and architecture.\n"
            "3) Configure RAM, CPU cores and threads.\n"
            "4) Optionally enable Special Add-ons for SSD optimization.\n"
            "5) Your VM will appear in 'My VMs'. Click ▶ Start to boot it.\n\n"
            "Shortcuts:\n"
            "  Ctrl+N — New VM\n"
            "  Ctrl+F — Focus search\n"
            "  F5     — Refresh\n"
            "  Del    — Delete selected\n"
            "  F1     — Help\n"
            "  Ctrl+Q — Quit",
        "log_viewer_title": "windowVM logs",
        "iso_library_title": "ISO library",
        "iso_add": "Add ISO", "iso_remove": "Remove selected",
        "import_ok": "Import finished: {n} VM(s) loaded.",
        "export_ok": "Exported {n} VM(s) to:\n{path}",
        "nothing_selected": "Please select a VM first.",
        "wizard_step": "Step {n} of {total}",
        "portable_on": "Portable mode", "backup_ok": "Backup created:",
        "reset_confirm": "Reset ALL configuration to defaults?",
        "already_running": "This VM is already running.",
        "not_running": "This VM is not running.",
        "starting": "Starting…",
        "toast_saved": "Saved.",
        "toast_lang": "Language changed to {lang}.",
        "toast_dark": "Dark mode {state}.",
        "on": "on", "off": "off",
    },
    "es": {
        "app_title": "windowVM",
        "menu_file": "Archivo", "menu_edit": "Editar", "menu_view": "Ver",
        "menu_language": "Idioma", "menu_help": "Ayuda",
        "menu_new_vm": "Nueva VM…", "menu_import": "Importar VM…",
        "menu_export_all": "Exportar todas las VMs…", "menu_quit": "Salir",
        "menu_edit_vm": "Editar VM seleccionada", "menu_clone_vm": "Clonar VM seleccionada",
        "menu_delete_vm": "Eliminar VM seleccionada",
        "menu_dark_mode": "Modo oscuro", "menu_refresh": "Refrescar",
        "menu_about": "Acerca de…", "menu_help_docs": "Ayuda / Tutorial",
        "menu_logs": "Ver registros", "menu_iso_lib": "Biblioteca ISO…",
        "lang_en": "Inglés", "lang_es": "Español", "lang_pt": "Portugués",
        "create_vm": "Crear VM nueva\n+",
        "my_vms": "── Mis VMs ──",
        "no_vms": "Aún no hay VMs :(",
        "no_vms_sub": "Pulsa 'Crear VM nueva' para empezar",
        "search_placeholder": "🔍  Buscar VMs…",
        "sort_by": "Ordenar por:", "sort_name": "Nombre", "sort_ram": "RAM",
        "sort_date": "Fecha", "sort_fav": "Favoritas primero",
        "achievements": "🏆 Logros",
        "btn_start": "▶ Iniciar", "btn_stop": "■ Detener",
        "btn_force_stop": "⛔ Forzar cierre", "btn_edit": "✎ Editar",
        "btn_clone": "⧉ Clonar", "btn_delete": "🗑 Eliminar",
        "btn_export": "⤓ Exportar", "btn_fav_on": "★", "btn_fav_off": "☆",
        "loading_iso": "Cargar ISO…", "iso_loaded": "ISO cargada ✓",
        "vm_name": "Nombre de VM", "os_label": "Sistema operativo", "type_label": "Arquitectura",
        "accept": "Aceptar", "cancel": "Cancelar", "next": "Siguiente",
        "back": "Atrás", "activate": "Activar", "no_thanks": "No, gracias",
        "save": "Guardar", "close": "Cerrar",
        "hardware_config": "Configuración de hardware",
        "ram_label": "RAM (MB)", "cores_label": "Núcleos de CPU", "threads_label": "Hilos de CPU",
        "disk_size_label": "Tamaño del disco (GB)", "disk_label": "Ruta del disco",
        "network_label": "Modo de red", "display_label": "Backend de pantalla",
        "boot_label": "Orden de arranque", "notes_label": "Notas",
        "tags_label": "Etiquetas (separadas por coma)", "custom_args_label": "Args extra QEMU",
        "usb_label": "Habilitar USB passthrough", "audio_label": "Habilitar audio",
        "shared_folder_label": "Carpeta compartida", "fav_label": "Marcar como favorita",
        "special_addons_title": "✨ Especial Add-ons ✨",
        "special_addons_body":
            "¿Deseas activar las Especial Add-ons?\n\n"
            "• Arrastrar y soltar archivos a la pantalla de la VM\n"
            "• Instalación directa dentro de la VM\n"
            "• Aprovechamiento máximo de tu SSD (TRIM / VirtIO)",
        "vm_created_title": "VM creada",
        "vm_created_msg": "¡VM '{name}' creada con éxito!",
        "error_title": "Error", "warning_title": "Advertencia",
        "confirm_delete_title": "Confirmar borrado",
        "confirm_delete_msg": "¿Eliminar la VM '{name}' de la lista?",
        "missing_name_title": "Falta el nombre",
        "missing_name_msg": "Introduce un nombre para la VM.",
        "invalid_input": "Valor inválido en el campo: {field}",
        "qemu_missing": "QEMU no está instalado o no está en el PATH.\n\nDescárgalo de: {url}",
        "qemu_running": "Iniciando VM '{name}'…",
        "vm_stopped": "La VM '{name}' se ha detenido.",
        "start_failed": "No se pudo iniciar QEMU:\n{err}",
        "status_ready": "Listo",
        "status_vms": "{n} VM(s) registradas · {r} en ejecución",
        "status_lang": "Idioma: {lang}",
        "vnc_port_label": "Puerto VNC (opcional)",
        "achievement_first_vm": "Crea tu primera VM",
        "achievement_iso": "Carga una ISO",
        "achievement_addons": "Activa las Especial Add-ons",
        "achievement_fav": "Marca una VM como favorita",
        "completed": "✅ Completado", "locked": "❌ Bloqueado",
        "about_title": "Acerca de {app}",
        "about_text": "{app} v{ver}\n\nGestor de VMs QEMU multiplataforma.\n\n"
                      "© {year} {author}\nLicencia: MIT",
        "help_title": "Ayuda / Tutorial",
        "help_text":
            "1) Pulsa 'Crear VM nueva' para abrir el asistente.\n"
            "2) Elige un nombre, carga opcionalmente una ISO, define SO y arquitectura.\n"
            "3) Configura RAM, núcleos e hilos de CPU.\n"
            "4) Opcionalmente activa las Especial Add-ons para optimizar el SSD.\n"
            "5) Tu VM aparecerá en 'Mis VMs'. Pulsa ▶ Iniciar para arrancarla.\n\n"
            "Atajos:\n"
            "  Ctrl+N — Nueva VM\n"
            "  Ctrl+F — Enfocar búsqueda\n"
            "  F5     — Refrescar\n"
            "  Del    — Eliminar seleccionada\n"
            "  F1     — Ayuda\n"
            "  Ctrl+Q — Salir",
        "log_viewer_title": "Registros de windowVM",
        "iso_library_title": "Biblioteca de ISOs",
        "iso_add": "Añadir ISO", "iso_remove": "Quitar seleccionada",
        "import_ok": "Importación completada: {n} VM(s) cargadas.",
        "export_ok": "Exportadas {n} VM(s) a:\n{path}",
        "nothing_selected": "Selecciona una VM primero.",
        "wizard_step": "Paso {n} de {total}",
        "portable_on": "Modo portátil", "backup_ok": "Backup creado:",
        "reset_confirm": "¿Resetear TODA la configuración a valores por defecto?",
        "already_running": "Esta VM ya está en ejecución.",
        "not_running": "Esta VM no está en ejecución.",
        "starting": "Iniciando…",
        "toast_saved": "Guardado.",
        "toast_lang": "Idioma cambiado a {lang}.",
        "toast_dark": "Modo oscuro {state}.",
        "on": "activado", "off": "desactivado",
    },
    "pt": {
        "app_title": "windowVM",
        "menu_file": "Arquivo", "menu_edit": "Editar", "menu_view": "Exibir",
        "menu_language": "Idioma", "menu_help": "Ajuda",
        "menu_new_vm": "Nova VM…", "menu_import": "Importar VM…",
        "menu_export_all": "Exportar todas as VMs…", "menu_quit": "Sair",
        "menu_edit_vm": "Editar VM selecionada", "menu_clone_vm": "Clonar VM selecionada",
        "menu_delete_vm": "Excluir VM selecionada",
        "menu_dark_mode": "Modo escuro", "menu_refresh": "Atualizar",
        "menu_about": "Sobre…", "menu_help_docs": "Ajuda / Tutorial",
        "menu_logs": "Ver registros", "menu_iso_lib": "Biblioteca ISO…",
        "lang_en": "Inglês", "lang_es": "Espanhol", "lang_pt": "Português",
        "create_vm": "Criar nova VM\n+",
        "my_vms": "── Minhas VMs ──",
        "no_vms": "Nenhuma VM ainda :(",
        "no_vms_sub": "Clique em 'Criar nova VM' para começar",
        "search_placeholder": "🔍  Buscar VMs…",
        "sort_by": "Ordenar por:", "sort_name": "Nome", "sort_ram": "RAM",
        "sort_date": "Data", "sort_fav": "Favoritas primeiro",
        "achievements": "🏆 Conquistas",
        "btn_start": "▶ Iniciar", "btn_stop": "■ Parar",
        "btn_force_stop": "⛔ Forçar parada", "btn_edit": "✎ Editar",
        "btn_clone": "⧉ Clonar", "btn_delete": "🗑 Excluir",
        "btn_export": "⤓ Exportar", "btn_fav_on": "★", "btn_fav_off": "☆",
        "loading_iso": "Carregar ISO…", "iso_loaded": "ISO carregada ✓",
        "vm_name": "Nome da VM", "os_label": "Sistema operacional", "type_label": "Arquitetura",
        "accept": "Aceitar", "cancel": "Cancelar", "next": "Avançar",
        "back": "Voltar", "activate": "Ativar", "no_thanks": "Não, obrigado",
        "save": "Salvar", "close": "Fechar",
        "hardware_config": "Configuração de hardware",
        "ram_label": "RAM (MB)", "cores_label": "Núcleos da CPU", "threads_label": "Threads da CPU",
        "disk_size_label": "Tamanho do disco (GB)", "disk_label": "Caminho do disco",
        "network_label": "Modo de rede", "display_label": "Backend de vídeo",
        "boot_label": "Ordem de boot", "notes_label": "Notas",
        "tags_label": "Tags (separadas por vírgula)", "custom_args_label": "Args extras QEMU",
        "usb_label": "Habilitar USB passthrough", "audio_label": "Habilitar áudio",
        "shared_folder_label": "Pasta compartilhada", "fav_label": "Marcar como favorita",
        "special_addons_title": "✨ Add-ons Especiais ✨",
        "special_addons_body":
            "Deseja ativar os Add-ons Especiais?\n\n"
            "• Arrastar e soltar arquivos para a tela da VM\n"
            "• Instalação direta dentro da VM\n"
            "• Aproveitamento máximo do SSD (TRIM / VirtIO)",
        "vm_created_title": "VM criada",
        "vm_created_msg": "VM '{name}' criada com sucesso!",
        "error_title": "Erro", "warning_title": "Aviso",
        "confirm_delete_title": "Confirmar exclusão",
        "confirm_delete_msg": "Excluir a VM '{name}' da lista?",
        "missing_name_title": "Nome ausente",
        "missing_name_msg": "Digite um nome para a VM.",
        "invalid_input": "Valor inválido no campo: {field}",
        "qemu_missing": "QEMU não está instalado ou não está no PATH.\n\nBaixe em: {url}",
        "qemu_running": "Iniciando VM '{name}'…",
        "vm_stopped": "A VM '{name}' foi encerrada.",
        "start_failed": "Não foi possível iniciar o QEMU:\n{err}",
        "status_ready": "Pronto",
        "status_vms": "{n} VM(s) registradas · {r} em execução",
        "status_lang": "Idioma: {lang}",
        "vnc_port_label": "Porta VNC (opcional)",
        "achievement_first_vm": "Crie sua primeira VM",
        "achievement_iso": "Carregue uma ISO",
        "achievement_addons": "Ative os Add-ons Especiais",
        "achievement_fav": "Marque uma VM como favorita",
        "completed": "✅ Concluído", "locked": "❌ Bloqueado",
        "about_title": "Sobre {app}",
        "about_text": "{app} v{ver}\n\nGerenciador QEMU multiplataforma.\n\n"
                      "© {year} {author}\nLicença: MIT",
        "help_title": "Ajuda / Tutorial",
        "help_text":
            "1) Clique em 'Criar nova VM' para abrir o assistente.\n"
            "2) Escolha um nome, carregue uma ISO, defina SO e arquitetura.\n"
            "3) Configure RAM, núcleos e threads da CPU.\n"
            "4) Opcionalmente ative os Add-ons Especiais para otimizar o SSD.\n"
            "5) Sua VM aparecerá em 'Minhas VMs'. Clique ▶ Iniciar para executar.\n\n"
            "Atalhos:\n"
            "  Ctrl+N — Nova VM\n"
            "  Ctrl+F — Focar busca\n"
            "  F5     — Atualizar\n"
            "  Del    — Excluir selecionada\n"
            "  F1     — Ajuda\n"
            "  Ctrl+Q — Sair",
        "log_viewer_title": "Registros do windowVM",
        "iso_library_title": "Biblioteca de ISOs",
        "iso_add": "Adicionar ISO", "iso_remove": "Remover selecionada",
        "import_ok": "Importação concluída: {n} VM(s) carregadas.",
        "export_ok": "Exportadas {n} VM(s) para:\n{path}",
        "nothing_selected": "Selecione uma VM primeiro.",
        "wizard_step": "Passo {n} de {total}",
        "portable_on": "Modo portátil", "backup_ok": "Backup criado:",
        "reset_confirm": "Resetar TODA a configuração para o padrão?",
        "already_running": "Esta VM já está em execução.",
        "not_running": "Esta VM não está em execução.",
        "starting": "Iniciando…",
        "toast_saved": "Salvo.",
        "toast_lang": "Idioma alterado para {lang}.",
        "toast_dark": "Modo escuro {state}.",
        "on": "ativado", "off": "desativado",
    },
}


class I18n:
    def __init__(self, lang="en"):
        self.lang = lang if lang in TRANSLATIONS else "en"
        self.dict = TRANSLATIONS[self.lang]

    def set_lang(self, lang):
        if lang in TRANSLATIONS:
            self.lang = lang
            self.dict = TRANSLATIONS[lang]

    def t(self, key, **kwargs):
        s = self.dict.get(key, TRANSLATIONS["en"].get(key, key))
        if kwargs:
            try:
                s = s.format(**kwargs)
            except Exception:
                pass
        return s


# =============================================================================
# THEMES (light / dark)
# =============================================================================
THEMES = {
    "light": {
        "bg_main": "#ffffff", "bg_secondary": "#f5f5f5", "bg_card": "#f5f5f5",
        "bg_panel": "#6a8caf", "bg_sidebar": "#03a9f4",
        "btn_primary": "#3f51b5", "btn_success": "#4caf50", "btn_danger": "#d32f2f",
        "btn_warning": "#ff9800",
        "accent_orange": "#ff9800", "accent_yellow": "#fbc02d", "accent_red": "#d32f2f",
        "text_main": "#333333", "text_muted": "#9e9e9e",
        "input_bg": "#e0e0e0", "monitor_screen": "#c8e6c9", "monitor_hill": "#81c784",
        "border": "#cccccc",
    },
    "dark": {
        "bg_main": "#1e1e1e", "bg_secondary": "#252525", "bg_card": "#2d2d2d",
        "bg_panel": "#263238", "bg_sidebar": "#0277bd",
        "btn_primary": "#5c6bc0", "btn_success": "#43a047", "btn_danger": "#c62828",
        "btn_warning": "#ef6c00",
        "accent_orange": "#fb8c00", "accent_yellow": "#fbc02d", "accent_red": "#e53935",
        "text_main": "#e0e0e0", "text_muted": "#9e9e9e",
        "input_bg": "#3a3a3a", "monitor_screen": "#a5d6a7", "monitor_hill": "#66bb6a",
        "border": "#555555",
    },
}

FONTS = {
    "title": ("Arial", 18, "bold"),
    "subtitle": ("Arial", 14, "bold"),
    "text": ("Arial", 11),
    "text_bold": ("Arial", 11, "bold"),
    "logo": ("Arial", 16, "bold"),
    "small": ("Arial", 9),
}


# =============================================================================
# CONFIG
# =============================================================================
class Config:
    DEFAULTS = {
        "language": "en",
        "theme": "light",
        "window_geometry": "980x640",
        "portable_mode": False,
        "autostart_vms": [],
        "recent": [],
        "iso_library": [],
    }

    def __init__(self, path):
        self.path = Path(path)
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self):
        try:
            if self.path.exists():
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        self.data.update(loaded)
        except Exception as e:
            LOGGER.warning("Config load error: %s", e)

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            LOGGER.error("Config save error: %s", e)

    def get(self, key, default=None):
        return self.data.get(key, self.DEFAULTS.get(key, default))

    def set(self, key, value):
        self.data[key] = value
        self.save()


# =============================================================================
# QEMU DETECTION
# =============================================================================
class QemuDetector:
    @staticmethod
    def system_binary():
        # Prefer x86_64 on x86, aarch64 on ARM
        arch = platform.machine().lower()
        if arch in ("aarch64", "arm64"):
            names = ["qemu-system-aarch64", "qemu-system-x86_64"]
        else:
            names = ["qemu-system-x86_64", "qemu-system-i386"]
        for n in names:
            p = shutil.which(n)
            if p:
                return p, n
        return None, None

    @staticmethod
    def is_installed():
        return QemuDetector.system_binary()[0] is not None

    @staticmethod
    def accel_args():
        if IS_WINDOWS:
            return ["-accel", "whpx"]
        if IS_LINUX:
            return ["-accel", "kvm"]
        if IS_MACOS:
            return ["-accel", "hvf"]
        return ["-accel", "tcg"]

    @staticmethod
    def img_binary():
        return shutil.which("qemu-img")


# =============================================================================
# VM helpers
# =============================================================================
def new_vm(name, **kw):
    vm = {
        "id": str(uuid.uuid4()),
        "name": name,
        "ram": "2048",
        "cores": "2",
        "threads": "4",
        "iso": "",
        "addons": False,
        "disk": f"vms/{name}.qcow2",
        "disk_size": "20",
        "os_type": "Linux",
        "arch": "x86_64",
        "boot_order": "d",
        "network": "user",
        "display": "gtk",
        "vnc_port": "",
        "custom_args": "",
        "usb": False,
        "audio": True,
        "shared_folder": "",
        "notes": "",
        "tags": [],
        "favorite": False,
        "color": "",
        "status": "stopped",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "last_started": "",
    }
    vm.update(kw)
    return vm


def normalize_vm(vm):
    if not isinstance(vm, dict):
        return None
    name = vm.get("nombre") or vm.get("name")
    if not name:
        return None
    base = new_vm(name)
    # Migrate legacy fields
    if "nucleos" in vm and "cores" not in vm:
        vm["cores"] = vm["nucleos"]
    if "hilos" in vm and "threads" not in vm:
        vm["threads"] = vm["hilos"]
    if "nombre" in vm and "name" not in vm:
        vm["name"] = vm["nombre"]
    for k, v in vm.items():
        if k in base:
            base[k] = v
    if not base.get("id"):
        base["id"] = str(uuid.uuid4())
    if not base.get("disk"):
        base["disk"] = f"vms/{base['name']}.qcow2"
    return base


# =============================================================================
# MAIN APPLICATION
# =============================================================================
class WindowVMApp:
    TOTAL_WIZARD_STEPS = 3

    def __init__(self, root: tk.Tk):
        self.root = root
        self.config = Config(CONFIG_FILE)
        self.i18n = I18n(self.config.get("language", "en"))
        self.theme_name = self.config.get("theme", "light")
        self.theme = THEMES[self.theme_name]
        self.vms = []
        self.running_vms = {}     # vm_id -> Popen
        self.selected_vm_id = None
        self.wizard_data = {}
        self.search_var = tk.StringVar()
        self.sort_var = tk.StringVar(value="name")
        self.status_var = tk.StringVar(value=self.t("status_ready"))

        self._configure_root()
        self._load_vms()
        self._build_menu()
        self._build_ui()
        self.refresh_vm_list()
        self._bind_shortcuts()
        self._update_status()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        LOGGER.info("Started %s v%s on %s (%s)",
                    APP_NAME, APP_VERSION, platform.system(), platform.machine())

    # ---------------------------------------------------------------- helpers
    def t(self, key, **kw):
        return self.i18n.t(key, **kw)

    def _configure_root(self):
        self.root.title(self.t("app_title"))
        try:
            self.root.geometry(self.config.get("window_geometry", "980x640"))
        except Exception:
            self.root.geometry("980x640")
        self.root.minsize(820, 520)
        self.root.configure(bg=self.theme["bg_main"])

    def _load_vms(self):
        if VMS_FILE.exists():
            try:
                with open(VMS_FILE, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                self.vms = [v for v in (normalize_vm(x) for x in raw) if v]
            except Exception as e:
                LOGGER.exception("Error loading VMs: %s", e)
                self.vms = []

    def save_vms(self):
        try:
            with open(VMS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.vms, f, indent=2, ensure_ascii=False)
        except Exception as e:
            LOGGER.error("Error saving VMs: %s", e)
            messagebox.showerror(self.t("error_title"), str(e))

    def _update_status(self, msg=None):
        if msg is None:
            running = sum(1 for v in self.vms if v["id"] in self.running_vms)
            msg = self.t("status_vms", n=len(self.vms), r=running)
        self.status_var.set(msg)

    def _toast(self, msg, ms=2500):
        self.status_var.set(msg)
        self.root.after(ms, lambda: self._update_status())

    # ---------------------------------------------------------------- menu
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        m_file = tk.Menu(menubar, tearoff=0)
        m_file.add_command(label=self.t("menu_new_vm"),
                           command=self.open_create_wizard, accelerator="Ctrl+N")
        m_file.add_command(label=self.t("menu_import"), command=self.import_vms)
        m_file.add_command(label=self.t("menu_export_all"), command=self.export_all_vms)
        m_file.add_separator()
        m_file.add_command(label=self.t("menu_iso_lib"), command=self.open_iso_library)
        m_file.add_separator()
        m_file.add_command(label=self.t("menu_quit"), command=self._on_close, accelerator="Ctrl+Q")
        menubar.add_cascade(label=self.t("menu_file"), menu=m_file)

        m_edit = tk.Menu(menubar, tearoff=0)
        m_edit.add_command(label=self.t("menu_edit_vm"),
                           command=lambda: self.edit_selected_vm())
        m_edit.add_command(label=self.t("menu_clone_vm"),
                           command=lambda: self.clone_selected_vm())
        m_edit.add_command(label=self.t("menu_delete_vm"),
                           command=lambda: self.delete_selected_vm(), accelerator="Del")
        menubar.add_cascade(label=self.t("menu_edit"), menu=m_edit)

        m_view = tk.Menu(menubar, tearoff=0)
        self.var_dark = tk.BooleanVar(value=self.theme_name == "dark")
        m_view.add_checkbutton(label=self.t("menu_dark_mode"), variable=self.var_dark,
                               command=self.toggle_dark)
        m_view.add_command(label=self.t("menu_refresh"), command=self.refresh_vm_list, accelerator="F5")
        m_view.add_separator()
        m_view.add_command(label=self.t("menu_logs"), command=self.open_log_viewer)
        menubar.add_cascade(label=self.t("menu_view"), menu=m_view)

        m_lang = tk.Menu(menubar, tearoff=0)
        self.var_lang = tk.StringVar(value=self.i18n.lang)
        for code, key in (("en", "lang_en"), ("es", "lang_es"), ("pt", "lang_pt")):
            m_lang.add_radiobutton(label=self.t(key), value=code, variable=self.var_lang,
                                   command=lambda c=code: self.set_language(c))
        menubar.add_cascade(label=self.t("menu_language"), menu=m_lang)

        m_help = tk.Menu(menubar, tearoff=0)
        m_help.add_command(label=self.t("menu_help_docs"), command=self.open_help, accelerator="F1")
        m_help.add_command(label=self.t("menu_about"), command=self.open_about)
        menubar.add_cascade(label=self.t("menu_help"), menu=m_help)

        self.root.config(menu=menubar)

    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.open_create_wizard())
        self.root.bind("<Control-f>", lambda e: self.search_entry.focus_set() if hasattr(self, "search_entry") else None)
        self.root.bind("<F5>", lambda e: self.refresh_vm_list())
        self.root.bind("<Delete>", lambda e: self.delete_selected_vm())
        self.root.bind("<F1>", lambda e: self.open_help())
        self.root.bind("<Control-q>", lambda e: self._on_close())

    # ---------------------------------------------------------------- layout
    def _build_ui(self):
        # Main horizontal layout
        self.main_frame = tk.Frame(self.root, bg=self.theme["bg_main"])
        self.main_frame.pack(fill="both", expand=True)

        # Right decorative panel
        self.panel_derecho = tk.Canvas(self.main_frame, bg=self.theme["bg_panel"],
                                       highlightthickness=0, width=280)
        self.panel_derecho.pack(side="right", fill="both", expand=True)
        self.panel_derecho.bind("<Configure>", self._draw_right_panel)

        # Left panel
        self.panel_izq = tk.Frame(self.main_frame, bg=self.theme["bg_main"], width=560)
        self.panel_izq.pack(side="left", fill="both", expand=True)
        self.panel_izq.pack_propagate(False)

        # Achievements button
        tk.Button(self.panel_izq, text=self.t("achievements"),
                  bg=self.theme["accent_yellow"], fg="#333",
                  font=FONTS["text_bold"], command=self.open_achievements,
                  relief="flat", cursor="hand2").place(x=15, y=15)

        # Logo canvas
        cv = tk.Canvas(self.panel_izq, width=180, height=180,
                       bg=self.theme["bg_main"], highlightthickness=0)
        cv.pack(pady=(20, 0))
        cv.create_oval(5, 5, 175, 175, fill=self.theme["accent_yellow"], outline="")
        cv.create_rectangle(45, 50, 135, 110, fill=self.theme["monitor_screen"],
                            outline="black", width=3)
        cv.create_polygon(45, 110, 70, 85, 100, 110,
                          fill=self.theme["monitor_hill"], outline="")
        cv.create_rectangle(45, 110, 135, 118, fill="black", outline="black")
        cv.create_line(90, 118, 90, 135, width=3)
        cv.create_line(70, 135, 110, 135, width=3)

        self.center_frame = tk.Frame(self.panel_izq, bg=self.theme["bg_main"])
        self.center_frame.pack(fill="both", expand=True)

        # Logo text
        logo = tk.Frame(self.center_frame, bg=self.theme["bg_main"])
        logo.pack(pady=(5, 0))
        tk.Label(logo, text="window", font=FONTS["logo"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(side="left")
        tk.Label(logo, text="VM", font=FONTS["logo"],
                 bg=self.theme["bg_main"], fg=self.theme["accent_orange"]).pack(side="left")

        # Create VM button
        tk.Button(self.center_frame, text=self.t("create_vm"),
                  bg=self.theme["btn_primary"], fg="white",
                  font=FONTS["text_bold"], width=18, height=2,
                  relief="flat", cursor="hand2",
                  command=self.open_create_wizard).pack(pady=10)

        # Search / sort row
        row = tk.Frame(self.center_frame, bg=self.theme["bg_main"])
        row.pack(fill="x", padx=20, pady=(4, 0))
        self.search_entry = tk.Entry(row, textvariable=self.search_var,
                                     bg=self.theme["bg_secondary"],
                                     fg=self.theme["text_main"],
                                     insertbackground=self.theme["text_main"],
                                     relief="flat", font=FONTS["text"])
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        self.search_entry.insert(0, "")
        self.search_entry.bind("<KeyRelease>", lambda e: self.refresh_vm_list())

        sort_box = ttk.Combobox(row, textvariable=self.sort_var, state="readonly",
                                width=10, font=FONTS["small"],
                                values=["name", "ram", "date", "favorite"])
        sort_box.pack(side="right", padx=(6, 0))
        sort_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_vm_list())
        tk.Label(row, text=self.t("sort_by"), bg=self.theme["bg_main"],
                 fg=self.theme["text_muted"], font=FONTS["small"]).pack(side="right")

        # Title
        tk.Label(self.center_frame, text=self.t("my_vms"),
                 font=FONTS["subtitle"], bg=self.theme["bg_main"],
                 fg=self.theme["text_main"]).pack(pady=(10, 5))

        # VM list container
        self.vms_container = tk.Frame(self.center_frame, bg=self.theme["bg_main"])
        self.vms_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.canvas_vms = tk.Canvas(self.vms_container, bg=self.theme["bg_main"],
                                    highlightthickness=0)
        sb = tk.Scrollbar(self.vms_container, orient="vertical",
                          command=self.canvas_vms.yview)
        self.scrollable_frame = tk.Frame(self.canvas_vms, bg=self.theme["bg_main"])

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas_vms.configure(scrollregion=self.canvas_vms.bbox("all"))
        )
        self.canvas_vms.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_vms.configure(yscrollcommand=sb.set)
        self.canvas_vms.bind(
            "<Configure>",
            lambda e: self.canvas_vms.itemconfig(
                self.canvas_vms.find_all()[0], width=e.width)
        )
        self.canvas_vms.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Status bar
        self.status_bar = tk.Label(self.root, textvariable=self.status_var,
                                   anchor="w", bg=self.theme["bg_secondary"],
                                   fg=self.theme["text_muted"], font=FONTS["small"],
                                   padx=10)
        self.status_bar.pack(side="bottom", fill="x")

    def _draw_right_panel(self, event):
        c = event.widget
        W, H = event.width, event.height
        c.delete("all")
        c.create_rectangle(W * 0.15, H * 0.35, W * 0.45, H * 0.65,
                           fill=self.theme["accent_yellow"], outline="")
        c.create_rectangle(W * 0.55, H * 0.35, W * 0.85, H * 0.65,
                           fill=self.theme["accent_red"], outline="")
        c.create_rectangle(W * 0.35, H * 0.10, W * 0.65, H * 0.90,
                           fill=self.theme["accent_orange"], outline="")

    # ------------------------------------------------------------- VM list
    def _filtered_sorted_vms(self):
        q = self.search_var.get().strip().lower()
        lst = list(self.vms)
        if q:
            lst = [v for v in lst
                   if q in v["name"].lower()
                   or q in v.get("os_type", "").lower()
                   or q in " ".join(v.get("tags") or []).lower()]
        mode = self.sort_var.get()
        if mode == "name":
            lst.sort(key=lambda v: v["name"].lower())
        elif mode == "ram":
            lst.sort(key=lambda v: int(v.get("ram") or 0), reverse=True)
        elif mode == "date":
            lst.sort(key=lambda v: v.get("created_at") or "", reverse=True)
        elif mode == "favorite":
            lst.sort(key=lambda v: (not v.get("favorite"), v["name"].lower()))
        return lst

    def refresh_vm_list(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()

        vms = self._filtered_sorted_vms()

        if not vms:
            tk.Label(self.scrollable_frame, text=self.t("no_vms"),
                     font=FONTS["subtitle"], fg=self.theme["text_muted"],
                     bg=self.theme["bg_main"]).pack(pady=(30, 5))
            tk.Label(self.scrollable_frame, text=self.t("no_vms_sub"),
                     font=FONTS["small"], fg=self.theme["text_muted"],
                     bg=self.theme["bg_main"]).pack()
            self._update_status()
            return

        for vm in vms:
            try:
                self._build_vm_card(vm)
            except Exception as e:
                LOGGER.exception("Failed to render VM card: %s", e)
        self._update_status()

    def _build_vm_card(self, vm):
        running = vm["id"] in self.running_vms
        card = tk.Frame(self.scrollable_frame, bg=self.theme["bg_card"],
                        relief="solid", bd=1,
                        highlightbackground=self.theme["border"],
                        highlightthickness=1)
        card.pack(fill="x", pady=4, padx=5)
        card.bind("<Button-3>", lambda e, v=vm: self._vm_context_menu(e, v))
        if IS_MACOS:
            card.bind("<Button-2>", lambda e, v=vm: self._vm_context_menu(e, v))

        # Left accent bar
        if vm.get("color"):
            bar = tk.Frame(card, bg=vm["color"], width=6)
        else:
            bar = tk.Frame(card, bg=self.theme["btn_primary"], width=6)
        bar.pack(side="left", fill="y")

        info = tk.Frame(card, bg=self.theme["bg_card"])
        info.pack(side="left", fill="x", expand=True, padx=10, pady=8)

        name_row = tk.Frame(info, bg=self.theme["bg_card"])
        name_row.pack(anchor="w", fill="x")
        fav_icon = "★" if vm.get("favorite") else "☆"
        tk.Label(name_row, text=fav_icon,
                 bg=self.theme["bg_card"],
                 fg=self.theme["accent_yellow"] if vm.get("favorite") else self.theme["text_muted"],
                 font=("Arial", 12, "bold"), cursor="hand2",
                 command=None).pack(side="left")
        tk.Label(name_row, text=vm["name"], font=FONTS["text_bold"],
                 bg=self.theme["bg_card"], fg=self.theme["text_main"]).pack(side="left", padx=(4, 6))
        if running:
            tk.Label(name_row, text="● " + self.t("starting"),
                     font=FONTS["small"], fg=self.theme["btn_success"],
                     bg=self.theme["bg_card"]).pack(side="left")

        sub = (f"RAM: {vm.get('ram', '?')}MB  |  CPU: "
               f"{vm.get('cores', '?')}C/{vm.get('threads', '?')}T  |  "
               f"OS: {vm.get('os_type', '?')} ({vm.get('arch', '?')})  |  "
               f"Add-ons: {'Sí' if vm.get('addons') else 'No'}")
        tk.Label(info, text=sub, font=FONTS["small"],
                 bg=self.theme["bg_card"], fg=self.theme["text_muted"]).pack(anchor="w")

        if vm.get("notes"):
            tk.Label(info, text=vm["notes"][:120], font=FONTS["small"],
                     bg=self.theme["bg_card"], fg=self.theme["text_muted"],
                     wraplength=380, justify="left").pack(anchor="w")

        # Buttons
        btns = tk.Frame(card, bg=self.theme["bg_card"])
        btns.pack(side="right", padx=8, pady=8)

        if running:
            tk.Button(btns, text=self.t("btn_stop"), bg=self.theme["btn_danger"],
                      fg="white", font=FONTS["small"], relief="flat",
                      cursor="hand2", width=10,
                      command=lambda v=vm: self.stop_vm(v)).pack(side="right", padx=2)
        else:
            tk.Button(btns, text=self.t("btn_start"), bg=self.theme["btn_success"],
                      fg="white", font=FONTS["small"], relief="flat",
                      cursor="hand2", width=10,
                      command=lambda v=vm: self.start_vm(v)).pack(side="right", padx=2)

        tk.Button(btns, text=self.t("btn_delete"), bg=self.theme["btn_danger"],
                  fg="white", font=FONTS["small"], relief="flat",
                  cursor="hand2", width=3,
                  command=lambda v=vm: self.delete_vm(v)).pack(side="right", padx=2)

    def _vm_context_menu(self, event, vm):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label=self.t("menu_edit_vm"),
                         command=lambda: self.open_edit_vm(vm))
        menu.add_command(label=self.t("menu_clone_vm"),
                         command=lambda: self.clone_vm(vm))
        menu.add_command(label=self.t("btn_export"),
                         command=lambda: self.export_vm(vm))
        menu.add_separator()
        if vm["id"] in self.running_vms:
            menu.add_command(label=self.t("btn_stop"),
                             command=lambda: self.stop_vm(vm))
            menu.add_command(label=self.t("btn_force_stop"),
                             command=lambda: self.force_stop_vm(vm))
        else:
            menu.add_command(label=self.t("btn_start"),
                             command=lambda: self.start_vm(vm))
        menu.add_separator()
        menu.add_command(
            label=self.t("btn_fav_on") if not vm.get("favorite") else self.t("btn_fav_off"),
            command=lambda: self.toggle_favorite(vm))
        menu.add_separator()
        menu.add_command(label=self.t("btn_delete"),
                         command=lambda: self.delete_vm(vm))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    # ---------------------------------------------------------- wizard
    def open_create_wizard(self):
        self.wizard_data = {}
        self._wizard_step1()

    def _wizard_step1(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("menu_new_vm"))
        top.geometry("650x460")
        top.configure(bg=self.theme["bg_main"])
        top.resizable(False, False)
        top.transient(self.root)
        top.grab_set()
        self._center_window(top)

        # Left blue panel
        panel = tk.Canvas(top, width=200, height=460, bg=self.theme["bg_sidebar"],
                          highlightthickness=0)
        panel.pack(side="left", fill="y")
        panel.create_line(20, 220, 100, 220, fill=self.theme["accent_orange"], width=12)
        panel.create_line(60, 180, 60, 260, fill=self.theme["accent_orange"], width=12)
        panel.create_rectangle(100, 170, 190, 240, fill="#bbdefb", outline="black", width=4)
        panel.create_rectangle(105, 175, 185, 230, fill=self.theme["monitor_screen"],
                               outline="black", width=2)
        panel.create_polygon(105, 230, 135, 200, 165, 230,
                             fill=self.theme["monitor_hill"], outline="")

        form = tk.Frame(top, bg=self.theme["bg_main"])
        form.pack(side="left", fill="both", expand=True, padx=30, pady=20)

        tk.Label(form, text=self.t("menu_new_vm"), font=FONTS["title"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(anchor="w")
        tk.Label(form, text=self.t("wizard_step", n=1, total=self.TOTAL_WIZARD_STEPS),
                 font=FONTS["small"], bg=self.theme["bg_main"],
                 fg=self.theme["text_muted"]).pack(anchor="w", pady=(0, 16))

        tk.Label(form, text=self.t("vm_name"), font=FONTS["text"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(anchor="w")
        e_name = tk.Entry(form, font=FONTS["text"], bg=self.theme["bg_secondary"],
                          fg=self.theme["text_main"], insertbackground=self.theme["text_main"],
                          relief="flat")
        e_name.pack(fill="x", ipady=4, pady=(2, 10))

        # ISO picker
        iso_row = tk.Frame(form, bg=self.theme["bg_main"])
        iso_row.pack(fill="x", pady=(0, 10))
        iso_label = tk.Label(iso_row, text=self.t("loading_iso"),
                             bg=self.theme["input_bg"], fg=self.theme["text_main"],
                             font=FONTS["text"], padx=8, pady=4, cursor="hand2")
        iso_label.pack(side="left")
        iso_state = tk.Label(iso_row, text="", bg=self.theme["bg_main"],
                             fg="green", font=FONTS["small"])
        iso_state.pack(side="left", padx=8)

        def pick_iso():
            f = filedialog.askopenfilename(
                title=self.t("loading_iso"),
                filetypes=[("ISO", "*.iso"), ("All", "*.*")])
            if f:
                self.wizard_data["iso"] = f
                iso_state.config(text=self.t("iso_loaded"))
                # add to ISO library
                lib = list(self.config.get("iso_library") or [])
                if f not in lib:
                    lib.append(f)
                    self.config.set("iso_library", lib)

        iso_label.bind("<Button-1>", lambda e: pick_iso())

        tk.Label(form, text=self.t("os_label"), font=FONTS["text"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(anchor="w")
        combo_os = ttk.Combobox(form, values=["Windows", "Linux", "MacOS", "BSD", "Other"],
                                font=FONTS["text"], state="readonly")
        combo_os.current(1)
        combo_os.pack(fill="x", pady=(2, 10))

        tk.Label(form, text=self.t("type_label"), font=FONTS["text"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(anchor="w")
        combo_arch = ttk.Combobox(form, values=["x86_64", "i386", "aarch64", "arm"],
                                  font=FONTS["text"], state="readonly")
        combo_arch.current(0)
        combo_arch.pack(fill="x", pady=(2, 10))

        btn_row = tk.Frame(form, bg=self.theme["bg_main"])
        btn_row.pack(side="bottom", pady=10)

        def go_next():
            name = e_name.get().strip()
            if not name:
                messagebox.showwarning(self.t("missing_name_title"), self.t("missing_name_msg"))
                return
            # sanitize
            if any(c in name for c in '<>:"/\\|?*'):
                messagebox.showwarning(self.t("warning_title"),
                                       self.t("invalid_input", field=self.t("vm_name")))
                return
            self.wizard_data["name"] = name
            self.wizard_data["os_type"] = combo_os.get()
            self.wizard_data["arch"] = combo_arch.get()
            top.destroy()
            self._wizard_step2()

        tk.Button(btn_row, text=self.t("accept"), bg=self.theme["btn_primary"],
                  fg="white", font=FONTS["text_bold"], width=10,
                  relief="flat", cursor="hand2", command=go_next).pack(side="left", padx=6)
        tk.Button(btn_row, text=self.t("cancel"), bg=self.theme["bg_secondary"],
                  fg=self.theme["text_main"], font=FONTS["text"], width=10,
                  relief="flat", cursor="hand2", command=top.destroy).pack(side="left", padx=6)

        e_name.focus_set()

    def _wizard_step2(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("hardware_config"))
        top.geometry("420x460")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        top.grab_set()
        self._center_window(top)

        tk.Label(top, text=self.t("hardware_config"), font=FONTS["subtitle"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(pady=(18, 4))
        tk.Label(top, text=self.t("wizard_step", n=2, total=self.TOTAL_WIZARD_STEPS),
                 font=FONTS["small"], bg=self.theme["bg_main"],
                 fg=self.theme["text_muted"]).pack(pady=(0, 10))

        frm = tk.Frame(top, bg=self.theme["bg_main"])
        frm.pack(fill="both", expand=True, padx=40)

        def labeled(label_key, default, var_name, width=30):
            tk.Label(frm, text=self.t(label_key), font=FONTS["text"],
                     bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(anchor="w", pady=(6, 0))
            e = tk.Entry(frm, width=width, font=FONTS["text"],
                         bg=self.theme["bg_secondary"], fg=self.theme["text_main"],
                         insertbackground=self.theme["text_main"], relief="flat")
            e.insert(0, str(default))
            e.pack(fill="x", ipady=4, pady=2)
            self.wizard_data[var_name] = e
            return e

        labeled("ram_label", 2048, "e_ram")
        labeled("cores_label", 2, "e_cores")
        labeled("threads_label", 4, "e_threads")
        labeled("disk_size_label", 20, "e_disk")

        # Advanced options frame
        adv = tk.LabelFrame(frm, text="", bg=self.theme["bg_main"],
                            fg=self.theme["text_main"], bd=1, relief="groove",
                            labelwidget=tk.Label(frm, text="Advanced",
                                                 bg=self.theme["bg_main"],
                                                 fg=self.theme["text_muted"],
                                                 font=FONTS["small"]))
        adv.pack(fill="x", pady=(10, 4))

        tk.Label(adv, text=self.t("network_label"), bg=self.theme["bg_main"],
                 fg=self.theme["text_main"], font=FONTS["small"]).pack(anchor="w", padx=6)
        cb_net = ttk.Combobox(adv, values=["user", "bridge", "tap", "none"],
                              state="readonly", font=FONTS["small"])
        cb_net.current(0)
        cb_net.pack(fill="x", padx=6, pady=(0, 4))
        self.wizard_data["cb_net"] = cb_net

        tk.Label(adv, text=self.t("display_label"), bg=self.theme["bg_main"],
                 fg=self.theme["text_main"], font=FONTS["small"]).pack(anchor="w", padx=6)
        cb_disp = ttk.Combobox(adv, values=["gtk", "sdl", "vnc", "none"],
                               state="readonly", font=FONTS["small"])
        cb_disp.current(0 if not IS_WINDOWS else 1)  # SDL often better on Windows
        cb_disp.pack(fill="x", padx=6, pady=(0, 4))
        self.wizard_data["cb_disp"] = cb_disp

        row_bottom = tk.Frame(top, bg=self.theme["bg_main"])
        row_bottom.pack(side="bottom", pady=14)

        def go_next():
            try:
                ram = int(self.wizard_data["e_ram"].get())
                cores = int(self.wizard_data["e_cores"].get())
                threads = int(self.wizard_data["e_threads"].get())
                disk = int(self.wizard_data["e_disk"].get())
                assert 128 <= ram <= 262144, "ram"
                assert 1 <= cores <= 128, "cores"
                assert 1 <= threads <= 256, "threads"
                assert 1 <= disk <= 4096, "disk"
            except Exception:
                messagebox.showwarning(self.t("warning_title"),
                                       self.t("invalid_input", field="RAM/CPU/Disk"))
                return
            self.wizard_data["ram"] = str(ram)
            self.wizard_data["cores"] = str(cores)
            self.wizard_data["threads"] = str(threads)
            self.wizard_data["disk_size"] = str(disk)
            self.wizard_data["network"] = self.wizard_data["cb_net"].get()
            self.wizard_data["display"] = self.wizard_data["cb_disp"].get()
            top.destroy()
            self._wizard_step3()

        tk.Button(row_bottom, text=self.t("back"), bg=self.theme["bg_secondary"],
                  fg=self.theme["text_main"], font=FONTS["text"], width=10,
                  relief="flat", cursor="hand2",
                  command=lambda: (top.destroy(), self._wizard_step1())).pack(side="left", padx=6)
        tk.Button(row_bottom, text=self.t("next"), bg=self.theme["btn_primary"],
                  fg="white", font=FONTS["text_bold"], width=10,
                  relief="flat", cursor="hand2", command=go_next).pack(side="left", padx=6)

    def _wizard_step3(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("special_addons_title"))
        top.geometry("500x320")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        top.grab_set()
        self._center_window(top)

        tk.Label(top, text=self.t("special_addons_title"),
                 font=FONTS["subtitle"], fg=self.theme["accent_orange"],
                 bg=self.theme["bg_main"]).pack(pady=(22, 6))
        tk.Label(top, text=self.t("wizard_step", n=3, total=self.TOTAL_WIZARD_STEPS),
                 font=FONTS["small"], bg=self.theme["bg_main"],
                 fg=self.theme["text_muted"]).pack()

        tk.Label(top, text=self.t("special_addons_body"), font=FONTS["text"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"],
                 justify="center").pack(pady=20)

        row = tk.Frame(top, bg=self.theme["bg_main"])
        row.pack(pady=10)
        tk.Button(row, text=self.t("activate"), bg=self.theme["btn_success"],
                  fg="white", font=FONTS["text_bold"], width=12,
                  relief="flat", cursor="hand2",
                  command=lambda: (top.destroy(), self._finish_create(True))
                  ).pack(side="left", padx=8)
        tk.Button(row, text=self.t("no_thanks"), bg=self.theme["bg_secondary"],
                  fg=self.theme["text_main"], font=FONTS["text"], width=12,
                  relief="flat", cursor="hand2",
                  command=lambda: (top.destroy(), self._finish_create(False))
                  ).pack(side="left", padx=8)

    def _finish_create(self, addons):
        try:
            name = self.wizard_data["name"]
            vm = new_vm(
                name=name,
                ram=self.wizard_data.get("ram", "2048"),
                cores=self.wizard_data.get("cores", "2"),
                threads=self.wizard_data.get("threads", "4"),
                iso=self.wizard_data.get("iso", ""),
                addons=addons,
                os_type=self.wizard_data.get("os_type", "Linux"),
                arch=self.wizard_data.get("arch", "x86_64"),
                network=self.wizard_data.get("network", "user"),
                display=self.wizard_data.get("display", "gtk"),
                disk_size=self.wizard_data.get("disk_size", "20"),
                disk=f"vms/{name}.qcow2",
            )
            self.vms.append(vm)
            self.save_vms()
            self.refresh_vm_list()
        except Exception as e:
            LOGGER.exception("Failed to create VM: %s", e)
            messagebox.showerror(self.t("error_title"), str(e))
            return

        self.root.update_idletasks()
        self.canvas_vms.yview_moveto(1.0)
        self.wizard_data = {}
        messagebox.showinfo(self.t("vm_created_title"),
                            self.t("vm_created_msg", name=vm["name"]))

    # ---------------------------------------------------------- VM actions
    def _find_vm(self, vm_id):
        return next((v for v in self.vms if v["id"] == vm_id), None)

    def get_selected_vm(self):
        if not self.selected_vm_id:
            return None
        return self._find_vm(self.selected_vm_id)

    def start_vm(self, vm):
        if vm["id"] in self.running_vms:
            self._toast(self.t("already_running"))
            return

        qemu_bin, _ = QemuDetector.system_binary()
        if not qemu_bin:
            messagebox.showerror(self.t("error_title"),
                                 self.t("qemu_missing", url=QEMU_REPO))
            return

        disk_path = DATA_DIR / vm["disk"]
        disk_path.parent.mkdir(parents=True, exist_ok=True)

        if not disk_path.exists():
            img = QemuDetector.img_binary()
            if not img:
                messagebox.showerror(self.t("error_title"),
                                     self.t("qemu_missing", url=QEMU_REPO))
                return
            try:
                size = f"{vm.get('disk_size', '20')}G"
                subprocess.run([img, "create", "-f", "qcow2",
                                str(disk_path), size], check=True)
                LOGGER.info("Created disk %s (%s)", disk_path, size)
            except subprocess.CalledProcessError as e:
                messagebox.showerror(self.t("error_title"), str(e))
                return

        cmd = [qemu_bin] + QemuDetector.accel_args() + [
            "-m", str(vm["ram"]),
            "-smp", f"cores={vm['cores']},threads={vm['threads']}",
            "-boot", vm.get("boot_order", "d"),
            "-name", vm["name"],
        ]

        # Network
        net = vm.get("network", "user")
        if net == "user":
            cmd += ["-netdev", "user,id=net0", "-device", "virtio-net-pci,netdev=net0"]
        elif net == "none":
            cmd += ["-nic", "none"]

        # Display
        disp = vm.get("display", "gtk")
        if disp == "none":
            cmd += ["-display", "none"]
        elif disp == "vnc":
            port = vm.get("vnc_port") or "5900"
            cmd += ["-vnc", f":{port}"]
        else:
            if disp == "gtk":
                cmd += ["-display", "gtk"]
            elif disp == "sdl":
                cmd += ["-display", "sdl"]

        # Storage
        if vm.get("addons"):
            cmd += [
                "-device", "virtio-blk-pci,drive=hd0",
                "-drive", f"file={disk_path},if=none,id=hd0,format=qcow2,"
                          f"cache=none,aio=threads,discard=on,detect-zeroes=unmap",
            ]
            shared = vm.get("shared_folder") or str(DATA_DIR / "shared")
            os.makedirs(shared, exist_ok=True)
            cmd += ["-virtfs",
                    f"local,path={shared},mount_tag=host0,security_model=passthrough"]
            # Audio
            if vm.get("audio"):
                cmd += ["-audiodev", "pa,id=snd0", "-device", "intel-hda",
                        "-device", "hda-duplex,audiodev=snd0"]
        else:
            cmd += ["-drive", f"file={disk_path},format=qcow2,if=ide"]

        if vm.get("usb"):
            cmd += ["-device", "qemu-xhci", "-device", "usb-tablet"]

        if vm.get("iso"):
            cmd += ["-cdrom", vm["iso"]]

        if vm.get("custom_args"):
            # Split respecting quotes
            import shlex
            cmd += shlex.split(vm["custom_args"])

        LOGGER.info("Starting QEMU: %s", " ".join(cmd))
        self._toast(self.t("qemu_running", name=vm["name"]))

        def run():
            try:
                proc = subprocess.Popen(cmd, shell=False)
                self.running_vms[vm["id"]] = proc
                vm["status"] = "running"
                vm["last_started"] = datetime.now().isoformat(timespec="seconds")
                self.root.after(0, self.refresh_vm_list)
                proc.wait()
            except Exception as e:
                LOGGER.exception("QEMU failed: %s", e)
                self.root.after(0, lambda: messagebox.showerror(
                    self.t("error_title"), self.t("start_failed", err=str(e))))
            finally:
                self.running_vms.pop(vm["id"], None)
                vm["status"] = "stopped"
                self.root.after(0, self.refresh_vm_list)
                self.root.after(0, lambda: self._toast(self.t("vm_stopped", name=vm["name"])))

        threading.Thread(target=run, daemon=True).start()
        # short delay to register the process
        self.root.after(300, self.refresh_vm_list)

    def stop_vm(self, vm):
        proc = self.running_vms.get(vm["id"])
        if not proc:
            self._toast(self.t("not_running"))
            return
        try:
            proc.terminate()
        except Exception as e:
            LOGGER.warning("Failed to stop VM: %s", e)

    def force_stop_vm(self, vm):
        proc = self.running_vms.get(vm["id"])
        if not proc:
            self._toast(self.t("not_running"))
            return
        try:
            proc.kill()
        except Exception as e:
            LOGGER.warning("Failed to kill VM: %s", e)

    def delete_vm(self, vm):
        if not messagebox.askyesno(self.t("confirm_delete_title"),
                                   self.t("confirm_delete_msg", name=vm["name"])):
            return
        if vm["id"] in self.running_vms:
            self.force_stop_vm(vm)
        self.vms = [v for v in self.vms if v["id"] != vm["id"]]
        self.save_vms()
        self.refresh_vm_list()

    def delete_selected_vm(self):
        vm = self.get_selected_vm()
        if not vm:
            self._toast(self.t("nothing_selected"))
            return
        self.delete_vm(vm)

    def edit_selected_vm(self):
        vm = self.get_selected_vm()
        if not vm:
            self._toast(self.t("nothing_selected"))
            return
        self.open_edit_vm(vm)

    def clone_selected_vm(self):
        vm = self.get_selected_vm()
        if not vm:
            self._toast(self.t("nothing_selected"))
            return
        self.clone_vm(vm)

    def toggle_favorite(self, vm):
        vm["favorite"] = not vm.get("favorite")
        self.save_vms()
        self.refresh_vm_list()

    def clone_vm(self, vm):
        new_name = simpledialog.askstring(self.t("menu_clone_vm"),
                                          self.t("vm_name"),
                                          initialvalue=f"{vm['name']}-copy")
        if not new_name:
            return
        new_name = new_name.strip()
        if any(v["name"] == new_name for v in self.vms):
            messagebox.showwarning(self.t("warning_title"),
                                   self.t("invalid_input", field=self.t("vm_name")))
            return
        copy = dict(vm)
        copy["id"] = str(uuid.uuid4())
        copy["name"] = new_name
        copy["disk"] = f"vms/{new_name}.qcow2"
        copy["created_at"] = datetime.now().isoformat(timespec="seconds")
        # Copy disk if it exists
        src = DATA_DIR / vm["disk"]
        dst = DATA_DIR / copy["disk"]
        if src.exists():
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                LOGGER.warning("Could not copy disk: %s", e)
        self.vms.append(copy)
        self.save_vms()
        self.refresh_vm_list()

    def open_edit_vm(self, vm):
        top = tk.Toplevel(self.root)
        top.title(self.t("menu_edit_vm"))
        top.geometry("460x620")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        top.grab_set()
        self._center_window(top)

        tk.Label(top, text=self.t("menu_edit_vm"), font=FONTS["subtitle"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(pady=12)

        frm = tk.Frame(top, bg=self.theme["bg_main"])
        frm.pack(fill="both", expand=True, padx=24)

        vars = {}
        fields = [
            ("vm_name", "name", "str"),
            ("ram_label", "ram", "int"),
            ("cores_label", "cores", "int"),
            ("threads_label", "threads", "int"),
            ("disk_size_label", "disk_size", "int"),
            ("vnc_port_label", "vnc_port", "str"),
            ("notes_label", "notes", "str"),
            ("tags_label", "tags", "list"),
            ("custom_args_label", "custom_args", "str"),
            ("shared_folder_label", "shared_folder", "str"),
        ]
        for label, key, kind in fields:
            tk.Label(frm, text=self.t(label), bg=self.theme["bg_main"],
                     fg=self.theme["text_main"], font=FONTS["small"]).pack(anchor="w", pady=(6, 0))
            e = tk.Entry(frm, font=FONTS["text"], bg=self.theme["bg_secondary"],
                         fg=self.theme["text_main"], insertbackground=self.theme["text_main"],
                         relief="flat")
            val = vm.get(key, "")
            if kind == "list":
                val = ", ".join(val or [])
            e.insert(0, str(val))
            e.pack(fill="x", ipady=3)
            vars[key] = (e, kind)

        # Checkboxes
        var_addons = tk.BooleanVar(value=bool(vm.get("addons")))
        var_usb = tk.BooleanVar(value=bool(vm.get("usb")))
        var_audio = tk.BooleanVar(value=bool(vm.get("audio")))
        var_fav = tk.BooleanVar(value=bool(vm.get("favorite")))
        for label, var in (("special_addons_title", var_addons),
                           ("usb_label", var_usb),
                           ("audio_label", var_audio),
                           ("fav_label", var_fav)):
            tk.Checkbutton(frm, text=self.t(label), variable=var,
                           bg=self.theme["bg_main"], fg=self.theme["text_main"],
                           selectcolor=self.theme["bg_secondary"],
                           activebackground=self.theme["bg_main"],
                           font=FONTS["small"]).pack(anchor="w")

        def save_edit():
            try:
                new = {}
                for key, (e, kind) in vars.items():
                    raw = e.get().strip()
                    if kind == "int":
                        new[key] = str(int(raw)) if raw else ""
                    elif kind == "list":
                        new[key] = [t.strip() for t in raw.split(",") if t.strip()]
                    else:
                        new[key] = raw
                new["addons"] = var_addons.get()
                new["usb"] = var_usb.get()
                new["audio"] = var_audio.get()
                new["favorite"] = var_fav.get()
                vm.update(new)
                self.save_vms()
                self.refresh_vm_list()
                top.destroy()
                self._toast(self.t("toast_saved"))
            except Exception as e:
                messagebox.showerror(self.t("error_title"), str(e))

        row = tk.Frame(top, bg=self.theme["bg_main"])
        row.pack(side="bottom", pady=14)
        tk.Button(row, text=self.t("save"), bg=self.theme["btn_primary"],
                  fg="white", font=FONTS["text_bold"], width=10,
                  relief="flat", cursor="hand2", command=save_edit).pack(side="left", padx=6)
        tk.Button(row, text=self.t("cancel"), bg=self.theme["bg_secondary"],
                  fg=self.theme["text_main"], font=FONTS["text"], width=10,
                  relief="flat", cursor="hand2", command=top.destroy).pack(side="left", padx=6)

    # ------------------------------------------------------- import/export
    def export_vm(self, vm):
        f = filedialog.asksaveasfilename(defaultextension=".json",
                                         filetypes=[("JSON", "*.json")],
                                         initialfile=f"{vm['name']}.json")
        if not f:
            return
        try:
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(vm, fp, indent=2, ensure_ascii=False)
            messagebox.showinfo(self.t("save"),
                                self.t("export_ok", n=1, path=f))
        except Exception as e:
            messagebox.showerror(self.t("error_title"), str(e))

    def export_all_vms(self):
        f = filedialog.asksaveasfilename(defaultextension=".json",
                                         filetypes=[("JSON", "*.json")],
                                         initialfile="windowvm_export.json")
        if not f:
            return
        try:
            with open(f, "w", encoding="utf-8") as fp:
                json.dump(self.vms, fp, indent=2, ensure_ascii=False)
            messagebox.showinfo(self.t("save"),
                                self.t("export_ok", n=len(self.vms), path=f))
        except Exception as e:
            messagebox.showerror(self.t("error_title"), str(e))

    def import_vms(self):
        f = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if not f:
            return
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            items = data if isinstance(data, list) else [data]
            count = 0
            for x in items:
                vm = normalize_vm(x)
                if vm:
                    vm["id"] = str(uuid.uuid4())
                    self.vms.append(vm)
                    count += 1
            self.save_vms()
            self.refresh_vm_list()
            messagebox.showinfo(self.t("save"), self.t("import_ok", n=count))
        except Exception as e:
            messagebox.showerror(self.t("error_title"), str(e))

    # ------------------------------------------------------ language/theme
    def set_language(self, code):
        self.i18n.set_lang(code)
        self.config.set("language", code)
        # Rebuild UI to update strings
        for w in list(self.root.winfo_children()):
            w.destroy()
        self._build_menu()
        self._build_ui()
        self.refresh_vm_list()
        self._toast(self.t("toast_lang", lang=self.t(f"lang_{code}")))

    def toggle_dark(self):
        self.theme_name = "dark" if self.var_dark.get() else "light"
        self.theme = THEMES[self.theme_name]
        self.config.set("theme", self.theme_name)
        for w in list(self.root.winfo_children()):
            w.destroy()
        self.root.configure(bg=self.theme["bg_main"])
        self._build_menu()
        self._build_ui()
        self.refresh_vm_list()
        state = self.t("on") if self.theme_name == "dark" else self.t("off")
        self._toast(self.t("toast_dark", state=state))

    # ------------------------------------------------------------ dialogs
    def open_about(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("about_title", app=APP_NAME))
        top.geometry("380x260")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        self._center_window(top)
        tk.Label(top, text="windowVM", font=FONTS["title"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(pady=(30, 4))
        tk.Label(top, text=self.t("about_text", app=APP_NAME, ver=APP_VERSION,
                                  year=datetime.now().year, author=APP_AUTHOR),
                 bg=self.theme["bg_main"], fg=self.theme["text_main"],
                 font=FONTS["text"], justify="center").pack(pady=8)
        tk.Button(top, text=QEMU_REPO, fg="blue", bg=self.theme["bg_main"],
                  relief="flat", cursor="hand2", font=FONTS["small"],
                  command=lambda: webbrowser.open(QEMU_REPO)).pack()

    def open_help(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("help_title"))
        top.geometry("520x520")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        self._center_window(top)
        tk.Label(top, text=self.t("help_title"), font=FONTS["subtitle"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(pady=12)
        txt = tk.Text(top, wrap="word", font=FONTS["text"],
                      bg=self.theme["bg_secondary"], fg=self.theme["text_main"],
                      relief="flat", padx=12, pady=12)
        txt.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        txt.insert("1.0", self.t("help_text"))
        txt.config(state="disabled")

    def open_log_viewer(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("log_viewer_title"))
        top.geometry("720x420")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        self._center_window(top)
        txt = tk.Text(top, wrap="none", font=("Consolas", 9),
                      bg=self.theme["bg_secondary"], fg=self.theme["text_main"],
                      relief="flat")
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        try:
            if LOG_FILE.exists():
                with open(LOG_FILE, "r", encoding="utf-8", errors="replace") as f:
                    txt.insert("1.0", f.read())
        except Exception as e:
            txt.insert("1.0", str(e))
        txt.see("end")

    def open_iso_library(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("iso_library_title"))
        top.geometry("560x360")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        self._center_window(top)

        listbox = tk.Listbox(top, bg=self.theme["bg_secondary"],
                             fg=self.theme["text_main"], relief="flat",
                             font=FONTS["small"])
        listbox.pack(fill="both", expand=True, padx=12, pady=12)

        def refresh():
            listbox.delete(0, "end")
            for p in self.config.get("iso_library") or []:
                listbox.insert("end", p)

        def add_iso():
            f = filedialog.askopenfilename(
                title=self.t("loading_iso"),
                filetypes=[("ISO", "*.iso"), ("All", "*.*")])
            if f:
                lib = list(self.config.get("iso_library") or [])
                if f not in lib:
                    lib.append(f)
                    self.config.set("iso_library", lib)
                    refresh()

        def remove_iso():
            sel = listbox.curselection()
            if not sel:
                return
            lib = list(self.config.get("iso_library") or [])
            del lib[sel[0]]
            self.config.set("iso_library", lib)
            refresh()

        row = tk.Frame(top, bg=self.theme["bg_main"])
        row.pack(pady=(0, 12))
        tk.Button(row, text=self.t("iso_add"), bg=self.theme["btn_primary"],
                  fg="white", font=FONTS["text"], relief="flat", cursor="hand2",
                  command=add_iso).pack(side="left", padx=6)
        tk.Button(row, text=self.t("iso_remove"), bg=self.theme["btn_danger"],
                  fg="white", font=FONTS["text"], relief="flat", cursor="hand2",
                  command=remove_iso).pack(side="left", padx=6)
        refresh()

    def open_achievements(self):
        top = tk.Toplevel(self.root)
        top.title(self.t("achievements"))
        top.geometry("400x340")
        top.configure(bg=self.theme["bg_main"])
        top.transient(self.root)
        self._center_window(top)
        tk.Label(top, text=self.t("achievements"), font=FONTS["title"],
                 bg=self.theme["bg_main"], fg=self.theme["text_main"]).pack(pady=20)

        achieved = {
            self.t("achievement_first_vm"): len(self.vms) > 0,
            self.t("achievement_iso"): any(v.get("iso") for v in self.vms),
            self.t("achievement_addons"): any(v.get("addons") for v in self.vms),
            self.t("achievement_fav"): any(v.get("favorite") for v in self.vms),
        }
        for label, done in achieved.items():
            fr = tk.Frame(top, bg=self.theme["bg_main"])
            fr.pack(fill="x", padx=40, pady=4)
            tk.Label(fr, text=label, bg=self.theme["bg_main"],
                     fg=self.theme["text_main"], font=FONTS["text"]).pack(side="left")
            state = self.t("completed") if done else self.t("locked")
            color = self.theme["btn_success"] if done else self.theme["btn_danger"]
            tk.Label(fr, text=state, bg=self.theme["bg_main"], fg=color,
                     font=FONTS["text_bold"]).pack(side="right")

    # --------------------------------------------------------------- misc
    def _center_window(self, top):
        top.update_idletasks()
        w = top.winfo_width() or int(top.geometry().split("x")[0])
        h = top.winfo_height() or int(top.geometry().split("x")[1].split("+")[0])
        sw = top.winfo_screenwidth()
        sh = top.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        top.geometry(f"+{x}+{y}")

    def _on_close(self):
        try:
            if self.running_vms and not messagebox.askyesno(
                    self.t("warning_title"),
                    "Hay VMs en ejecución. ¿Salir de todos modos?"):
                return
            # Stop all VMs
            for vm_id, proc in list(self.running_vms.items()):
                try:
                    proc.terminate()
                except Exception:
                    pass
            # Save geometry
            self.config.set("window_geometry", self.root.geometry().split("+")[0])
            self.config.save()
        finally:
            LOGGER.info("Shutdown.")
            self.root.destroy()


# =============================================================================
# ENTRY POINT
# =============================================================================
def main():
    # High DPI awareness on Windows
    if IS_WINDOWS:
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    try:
        root.tk.call("tk", "scaling", 1.2 if IS_MACOS else 1.0)
    except Exception:
        pass

    app = WindowVMApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
