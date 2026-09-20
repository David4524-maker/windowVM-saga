import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import threading
import shlex

# ==========================================
# "CSS" (Diccionario de Estilos Globales)
# ==========================================
THEME = {
    "colors": {
        "bg_main": "#ffffff",
        "bg_blue_panel": "#6a8caf",
        "bg_sidebar_blue": "#03a9f4",
        "btn_primary": "#3f51b5",
        "btn_success": "#4caf50",
        "btn_danger": "#d32f2f",
        "accent_orange": "#ff9800",
        "accent_yellow": "#fbc02d",
        "accent_red": "#d32f2f",
        "text_main": "#333333",
        "text_muted": "#9e9e9e",
        "input_bg": "#e0e0e0",
        "monitor_screen": "#c8e6c9",
        "monitor_hill": "#81c784",
        "vm_card_bg": "#f5f5f5"
    },
    "fonts": {
        "title": ("Arial", 18, "bold"),
        "subtitle": ("Arial", 14, "bold"),
        "text": ("Arial", 11),
        "text_bold": ("Arial", 11, "bold"),
        "logo": ("Arial", 16, "bold"),
        "sad_face": ("Arial", 40, "bold"),
        "small": ("Arial", 9)
    },
    "padding": {"small": 5, "medium": 10, "large": 20}
}

class WindowVMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("windowVM")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)
        self.root.configure(bg=THEME["colors"]["bg_main"])
        self.root.resizable(True, True)

        # Lista de VMs
        self.vms_creadas = []

        # Variables temporales para el flujo de creación
        self.temp_nombre = ""
        self.temp_iso = ""
        self.temp_ram = ""
        self.temp_nucleos = ""
        self.temp_hilos = ""
        self.temp_addons = False

        # Cargar datos guardados
        self.cargar_datos()

        self.configurar_estilos_ttk()
        self.crear_interfaz_principal()
        self.actualizar_lista_vms()

    def configurar_estilos_ttk(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=THEME["colors"]["input_bg"],
                        background=THEME["colors"]["input_bg"], foreground=THEME["colors"]["text_main"])

    # ==========================================
    # PERSISTENCIA
    # ==========================================
    def cargar_datos(self):
        if os.path.exists("windowvm_data.json"):
            try:
                with open("windowvm_data.json", "r") as f:
                    datos = json.load(f)
                # BUG FIX: si el JSON viene de una versión distinta (p.ej. la
                # versión en inglés, que guarda "name"/"cores"/"threads" en vez
                # de "nombre"/"nucleos"/"hilos") o tiene entradas incompletas,
                # antes esto rompía el renderizado de TODA la lista con un
                # KeyError la próxima vez que se dibujaba (incluida cualquier
                # VM nueva que se creara después). Ahora normalizamos cada
                # entrada rellenando lo que falte, y descartamos solo las que
                # de verdad no se puedan recuperar (sin dejar caer el resto).
                self.vms_creadas = [v for v in (self._normalizar_vm(x) for x in datos) if v is not None]
            except Exception as e:
                print(f"Error al cargar datos: {e}")
                self.vms_creadas = []

    def _normalizar_vm(self, vm):
        """Rellena claves faltantes (por datos antiguos/incompatibles) para
        que una VM con datos incompletos no rompa el resto de la lista."""
        if not isinstance(vm, dict):
            print(f"Entrada de VM inválida ignorada: {vm!r}")
            return None
        nombre = vm.get("nombre") or vm.get("name")
        if not nombre:
            print(f"VM sin nombre ignorada: {vm!r}")
            return None
        return {
            "nombre": nombre,
            "ram": vm.get("ram", vm.get("ram", "2048")),
            "nucleos": vm.get("nucleos", vm.get("cores", "2")),
            "hilos": vm.get("hilos", vm.get("threads", "4")),
            "iso": vm.get("iso", ""),
            "addons": vm.get("addons", False),
            "disco": vm.get("disco", vm.get("disk", f"vms/{nombre}.qcow2")),
        }

    def guardar_datos(self):
        try:
            with open("windowvm_data.json", "w") as f:
                json.dump(self.vms_creadas, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los datos: {e}")

    # ==========================================
    # INTERFAZ PRINCIPAL
    # ==========================================
    def crear_interfaz_principal(self):
        # Panel Derecho
        self.panel_derecho = tk.Canvas(self.root, bg=THEME["colors"]["bg_blue_panel"], highlightthickness=0)
        self.panel_derecho.pack(side="right", fill="both", expand=True)
        self.panel_derecho.bind("<Configure>", self.dibujar_panel_derecho)

        # Panel Izquierdo
        self.panel_izquierdo = tk.Frame(self.root, bg=THEME["colors"]["bg_main"], width=550)
        self.panel_izquierdo.pack(side="left", fill="both", expand=True)
        self.panel_izquierdo.pack_propagate(False)

        # Botón de Logros
        tk.Button(self.panel_izquierdo, text="🏆 Logros", bg=THEME["colors"]["accent_yellow"], 
                  font=THEME["fonts"]["text_bold"], command=self.mostrar_logros, 
                  relief="flat", cursor="hand2").place(x=15, y=15)

        # Icono Círculo Amarillo
        canvas_izq = tk.Canvas(self.panel_izquierdo, width=180, height=180, bg=THEME["colors"]["bg_main"], highlightthickness=0)
        canvas_izq.pack(pady=(20, 0))
        canvas_izq.create_oval(5, 5, 175, 175, fill=THEME["colors"]["accent_yellow"], outline="")
        canvas_izq.create_rectangle(45, 50, 135, 110, fill=THEME["colors"]["monitor_screen"], outline="black", width=3)
        canvas_izq.create_polygon(45, 110, 70, 85, 100, 110, fill=THEME["colors"]["monitor_hill"], outline="")
        canvas_izq.create_rectangle(45, 110, 135, 118, fill="black", outline="black")
        canvas_izq.create_line(90, 118, 90, 135, width=3)
        canvas_izq.create_line(70, 135, 110, 135, width=3)

        self.centro_frame = tk.Frame(self.panel_izquierdo, bg=THEME["colors"]["bg_main"])
        self.centro_frame.pack(fill="both", expand=True)

        # Logo
        logo_frame = tk.Frame(self.centro_frame, bg=THEME["colors"]["bg_main"])
        logo_frame.pack(pady=(5, 0))
        tk.Label(logo_frame, text="window", font=THEME["fonts"]["logo"], bg=THEME["colors"]["bg_main"], fg="black").pack(side="left")
        tk.Label(logo_frame, text="VM", font=THEME["fonts"]["logo"], bg=THEME["colors"]["bg_main"], fg=THEME["colors"]["accent_orange"]).pack(side="left")

        # Botón Crear VM
        tk.Button(self.centro_frame, text="Crear VM nueva\n+", bg=THEME["colors"]["btn_primary"], fg="white", 
                  font=THEME["fonts"]["text_bold"], width=15, height=2, relief="flat", cursor="hand2", 
                  command=self.abrir_ventana_crear_vm).pack(pady=THEME["padding"]["medium"])

        # Título Mis VMs
        tk.Label(self.centro_frame, text="── Mis VMs ──", font=THEME["fonts"]["subtitle"], 
                 bg=THEME["colors"]["bg_main"], fg=THEME["colors"]["text_main"]).pack(pady=(10, 5))
        
        # Contenedor con Scroll
        self.vms_container = tk.Frame(self.centro_frame, bg=THEME["colors"]["bg_main"])
        self.vms_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.canvas_vms = tk.Canvas(self.vms_container, bg=THEME["colors"]["bg_main"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.vms_container, orient="vertical", command=self.canvas_vms.yview)
        self.scrollable_frame = tk.Frame(self.canvas_vms, bg=THEME["colors"]["bg_main"])

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_vms.configure(scrollregion=self.canvas_vms.bbox("all")))
        self.canvas_vms.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_vms.configure(yscrollcommand=scrollbar.set)
        
        # Ajustar ancho dinámicamente
        self.canvas_vms.bind("<Configure>", lambda e: self.canvas_vms.itemconfig(
            self.canvas_vms.find_all()[0], width=e.width))

        self.canvas_vms.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def dibujar_panel_derecho(self, event):
        canvas = event.widget
        W, H = event.width, event.height
        canvas.delete("all")
        canvas.create_rectangle(W*0.15, H*0.35, W*0.45, H*0.65, fill=THEME["colors"]["accent_yellow"], outline="")
        canvas.create_rectangle(W*0.55, H*0.35, W*0.85, H*0.65, fill=THEME["colors"]["accent_red"], outline="")
        canvas.create_rectangle(W*0.35, H*0.1, W*0.65, H*0.9, fill=THEME["colors"]["accent_orange"], outline="")

    # ==========================================
    # LISTA DE VMs (RENDERIZADO)
    # ==========================================
    def actualizar_lista_vms(self):
        # Limpiar
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.vms_creadas:
            tk.Label(self.scrollable_frame, text="No hay VMs :(", font=("Arial", 18, "bold"), 
                     fg=THEME["colors"]["text_muted"], bg=THEME["colors"]["bg_main"]).pack(pady=30)
            tk.Label(self.scrollable_frame, text=":(", font=("Arial", 30, "bold"), 
                     fg="black", bg=THEME["colors"]["bg_main"]).pack()
            return

        for i, vm in enumerate(self.vms_creadas):
            # BUG FIX: si una tarjeta individual falla al dibujarse (p.ej. por
            # datos incompletos), antes esto abortaba el bucle entero y NINGUNA
            # VM posterior se dibujaba, incluida la que se acababa de crear.
            # Ahora se salta solo la tarjeta problemática y sigue con el resto.
            try:
                card = tk.Frame(self.scrollable_frame, bg=THEME["colors"]["vm_card_bg"], relief="solid", bd=1)
                card.pack(fill="x", pady=4, padx=5)

                # Información
                info_frame = tk.Frame(card, bg=THEME["colors"]["vm_card_bg"])
                info_frame.pack(side="left", padx=10, pady=8, fill="x", expand=True)

                tk.Label(info_frame, text=vm["nombre"], font=THEME["fonts"]["text_bold"], 
                         bg=THEME["colors"]["vm_card_bg"], anchor="w").pack(anchor="w")
                tk.Label(info_frame, text=f"RAM: {vm['ram']}MB  |  CPU: {vm['nucleos']}C/{vm['hilos']}T  |  Add-ons: {'Sí' if vm['addons'] else 'No'}", 
                         font=THEME["fonts"]["small"], bg=THEME["colors"]["vm_card_bg"], fg="gray").pack(anchor="w")

                # Botón Iniciar
                tk.Button(card, text="▶ Iniciar", bg=THEME["colors"]["btn_success"], fg="white", 
                          font=THEME["fonts"]["text_bold"], relief="flat", cursor="hand2",
                          command=lambda v=vm: self.iniciar_vm_real(v)).pack(side="right", padx=10, pady=8)

                # Botón Eliminar
                tk.Button(card, text="🗑", bg=THEME["colors"]["btn_danger"], fg="white", 
                          font=("Arial", 10, "bold"), relief="flat", cursor="hand2", width=3,
                          command=lambda idx=i: self.eliminar_vm(idx)).pack(side="right", padx=2, pady=8)
            except Exception as e:
                print(f"No se pudo dibujar la VM en la posición {i} ({vm}): {e}")
                continue

    def eliminar_vm(self, index):
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres eliminar esta VM de la lista?"):
            del self.vms_creadas[index]
            self.guardar_datos()
            self.actualizar_lista_vms()

    # ==========================================
    # FLUJO DE CREACIÓN (PASO A PASO, GUARDANDO DATOS)
    # ==========================================
    def abrir_ventana_crear_vm(self):
        self.top_crear = tk.Toplevel(self.root)
        self.top_crear.title("Crear VM")
        self.top_crear.geometry("650x450")
        self.top_crear.configure(bg=THEME["colors"]["bg_main"])
        self.top_crear.resizable(False, False)
        self.top_crear.grab_set()

        # Panel Azul Izquierdo
        panel_azul = tk.Canvas(self.top_crear, width=200, height=450, bg=THEME["colors"]["bg_sidebar_blue"], highlightthickness=0)
        panel_azul.pack(side="left", fill="y")
        panel_azul.create_line(20, 220, 100, 220, fill=THEME["colors"]["accent_orange"], width=12)
        panel_azul.create_line(60, 180, 60, 260, fill=THEME["colors"]["accent_orange"], width=12)
        panel_azul.create_rectangle(100, 170, 190, 240, fill="#bbdefb", outline="black", width=4)
        panel_azul.create_rectangle(105, 175, 185, 230, fill=THEME["colors"]["monitor_screen"], outline="black", width=2)
        panel_azul.create_polygon(105, 230, 135, 200, 165, 230, fill=THEME["colors"]["monitor_hill"], outline="")
        panel_azul.create_arc(125, 185, 155, 215, start=0, extent=180, style=tk.ARC, outline="black", width=2)
        panel_azul.create_oval(130, 190, 135, 195, fill="black")
        panel_azul.create_oval(145, 190, 150, 195, fill="black")
        panel_azul.create_rectangle(135, 240, 155, 255, fill="black")
        panel_azul.create_rectangle(115, 255, 175, 260, fill="black")

        # Formulario
        panel_form = tk.Frame(self.top_crear, bg=THEME["colors"]["bg_main"])
        panel_form.pack(side="left", fill="both", expand=True, padx=30, pady=30)

        tk.Label(panel_form, text="Crear VM", font=THEME["fonts"]["title"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", pady=(0, 20))
        tk.Label(panel_form, text="Nombre de VM......", font=THEME["fonts"]["text"], bg=THEME["colors"]["input_bg"], width=25, anchor="w").pack(pady=5)
        self.entry_nombre = tk.Entry(panel_form, bg="#f5f5f5", relief="solid", bd=1, font=THEME["fonts"]["text"])
        self.entry_nombre.pack(fill="x", pady=5)

        self.btn_iso = tk.Button(panel_form, text="Cargar ISO..", bg=THEME["colors"]["input_bg"], font=THEME["fonts"]["text"], 
                                 relief="solid", bd=1, cursor="hand2", command=self.cargar_iso)
        self.btn_iso.pack(pady=10, anchor="w")

        tk.Label(panel_form, text="SO....", font=THEME["fonts"]["text"], bg=THEME["colors"]["input_bg"], width=10, anchor="w").pack(pady=5)
        self.combo_so = ttk.Combobox(panel_form, values=["Windows", "Linux", "MacOS", "Otro"], font=THEME["fonts"]["text"])
        self.combo_so.pack(fill="x")

        tk.Label(panel_form, text="Tipo....", font=THEME["fonts"]["text"], bg=THEME["colors"]["input_bg"], width=10, anchor="w").pack(pady=5)
        self.combo_tipo = ttk.Combobox(panel_form, values=["64-bit", "32-bit", "ARM"], font=THEME["fonts"]["text"])
        self.combo_tipo.pack(fill="x")

        btn_frame = tk.Frame(panel_form, bg=THEME["colors"]["bg_main"])
        btn_frame.pack(side="bottom", pady=20)
        tk.Button(btn_frame, text="Aceptar", fg=THEME["colors"]["bg_sidebar_blue"], bg="white", font=THEME["fonts"]["text_bold"], 
                  relief="solid", bd=2, width=10, cursor="hand2", command=self.paso1_a_hardware).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancelar", bg="white", font=THEME["fonts"]["text"], relief="flat", 
                  cursor="hand2", command=self.top_crear.destroy).pack(side="left", padx=10)

    def cargar_iso(self):
        archivo = filedialog.askopenfilename(title="Seleccionar Imagen ISO", 
                                             filetypes=[("Archivos ISO", "*.iso"), ("Todos los archivos", "*.*")])
        if archivo:
            self.temp_iso = archivo
            self.btn_iso.config(text="ISO Cargada ✓", fg="green")

    def paso1_a_hardware(self):
        """Guarda el nombre ANTES de destruir la ventana"""
        self.temp_nombre = self.entry_nombre.get().strip()
        if not self.temp_nombre:
            messagebox.showwarning("Falta nombre", "Por favor, ingresa un nombre para la VM.")
            return
        self.top_crear.destroy()
        self.abrir_ventana_hardware()

    def abrir_ventana_hardware(self):
        self.top_hardware = tk.Toplevel(self.root)
        self.top_hardware.title("Hardware de la VM")
        self.top_hardware.geometry("400x350")
        self.top_hardware.configure(bg=THEME["colors"]["bg_main"])
        self.top_hardware.grab_set()

        tk.Label(self.top_hardware, text="Configuración de Hardware", font=THEME["fonts"]["subtitle"], bg=THEME["colors"]["bg_main"]).pack(pady=20)
        
        tk.Label(self.top_hardware, text="MB de RAM.....", font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", padx=60)
        self.entry_ram = tk.Entry(self.top_hardware, width=30, font=THEME["fonts"]["text"])
        self.entry_ram.insert(0, "2048")
        self.entry_ram.pack(pady=5)

        tk.Label(self.top_hardware, text="Nucleos.....", font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", padx=60)
        self.entry_nucleos = tk.Entry(self.top_hardware, width=30, font=THEME["fonts"]["text"])
        self.entry_nucleos.insert(0, "2")
        self.entry_nucleos.pack(pady=5)

        tk.Label(self.top_hardware, text="Hilos.....", font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", padx=60)
        self.entry_hilos = tk.Entry(self.top_hardware, width=30, font=THEME["fonts"]["text"])
        self.entry_hilos.insert(0, "4")
        self.entry_hilos.pack(pady=5)

        tk.Button(self.top_hardware, text="Siguiente", bg=THEME["colors"]["btn_primary"], fg="white", font=THEME["fonts"]["text_bold"], 
                  width=15, relief="flat", cursor="hand2", command=self.paso2_a_addons).pack(pady=20)

    def paso2_a_addons(self):
        """Guarda los valores de hardware ANTES de destruir la ventana"""
        self.temp_ram = self.entry_ram.get().strip() or "2048"
        self.temp_nucleos = self.entry_nucleos.get().strip() or "2"
        self.temp_hilos = self.entry_hilos.get().strip() or "4"
        self.top_hardware.destroy()
        self.abrir_ventana_addons()

    def abrir_ventana_addons(self):
        self.top_addons = tk.Toplevel(self.root)
        self.top_addons.title("Especial Add-ons")
        self.top_addons.geometry("480x280")
        self.top_addons.configure(bg=THEME["colors"]["bg_main"])
        self.top_addons.grab_set()

        tk.Label(self.top_addons, text="✨ Especial Add-ons ✨", font=THEME["fonts"]["subtitle"], fg=THEME["colors"]["accent_orange"], bg=THEME["colors"]["bg_main"]).pack(pady=20)
        texto = ("¿Deseas activar las Especial Add-ons?\n\n"
                 "• Arrastrar y soltar archivos a la pantalla de la VM\n"
                 "• Instalación directa dentro de la VM\n"
                 "• Aprovechamiento máximo de tu SSD")
        tk.Label(self.top_addons, text=texto, font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"], justify="center").pack(pady=10)

        btn_frame = tk.Frame(self.top_addons, bg=THEME["colors"]["bg_main"])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Activar", bg="#4caf50", fg="white", font=THEME["fonts"]["text_bold"], width=12, relief="flat", 
                  cursor="hand2", command=lambda: self.finalizar_creacion(True)).pack(side="left", padx=10)
        tk.Button(btn_frame, text="No, gracias", bg="#9e9e9e", fg="white", font=THEME["fonts"]["text"], width=12, relief="flat", 
                  cursor="hand2", command=lambda: self.finalizar_creacion(False)).pack(side="left", padx=10)

    def finalizar_creacion(self, addons):
        """Se ejecuta al elegir Add-ons. Aquí ya tenemos TODOS los datos guardados."""
        self.temp_addons = addons
        self.top_addons.destroy()

        # BUG FIX: todo este bloque podía fallar en silencio (p.ej. sin
        # permisos para crear la carpeta "vms", o cualquier otro error
        # inesperado). Al estar dentro de un callback de botón, Tkinter
        # tragaba la excepción, la mostraba solo en la consola y la VM
        # quedaba sin crear ni mostrarse, sin que el usuario supiera por qué.
        # Ahora se captura y se avisa con un mensaje claro.
        try:
            # Crear carpeta para las VMs
            os.makedirs("vms", exist_ok=True)

            # Crear el registro de la VM
            vm_info = {
                "nombre": self.temp_nombre,
                "ram": self.temp_ram,
                "nucleos": self.temp_nucleos,
                "hilos": self.temp_hilos,
                "iso": self.temp_iso,
                "addons": self.temp_addons,
                "disco": f"vms/{self.temp_nombre}.qcow2"
            }

            # Añadir a la lista y guardar
            self.vms_creadas.append(vm_info)
            self.guardar_datos()

            # ACTUALIZAR LA LISTA EN LA PANTALLA PRINCIPAL
            self.actualizar_lista_vms()
        except Exception as e:
            messagebox.showerror("Error al crear la VM", f"No se pudo crear la VM:\n{e}")
            return

        # BUG FIX: si ya había VMs llenando el área visible, la tarjeta nueva
        # se añade al final de la lista pero el scroll se queda donde estaba
        # (arriba), dejando la VM recién creada fuera de la vista. Forzamos
        # el scroll hasta el final para que sea visible de inmediato.
        self.canvas_vms.update_idletasks()
        self.canvas_vms.yview_moveto(1.0)

        # Limpiar variables temporales
        self.temp_nombre = ""
        self.temp_iso = ""
        self.temp_ram = ""
        self.temp_nucleos = ""
        self.temp_hilos = ""
        self.temp_addons = False

        messagebox.showinfo("VM Creada", f"¡VM '{vm_info['nombre']}' creada con éxito!\n\nYa aparece en 'Mis VMs'.")

        # ==========================================
    # INICIAR VM CON QEMU (OPTIMIZADO PARA SSD)
    # ==========================================
    def iniciar_vm_real(self, vm_info):
        disco_path = vm_info["disco"]
        if not os.path.exists(disco_path):
            try:
                print(f"Creando disco duro virtual: {disco_path}...")
                subprocess.run(["qemu-img", "create", "-f", "qcow2", disco_path, "20G"], check=True)
            except FileNotFoundError:
                messagebox.showerror("Error Crítico", "QEMU no está instalado o no está en el PATH.\n\n"
                                     "Descárgalo de: https://qemu.org")
                return
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Error al crear el disco duro virtual: {e}")
                return

        # 🚀 COMANDO BASE CON ACELERACIÓN POR HARDWARE DE WINDOWS (WHPX)
        # Esto hace que la VM vaya a velocidad nativa y no al 10%
        comando = [
            "qemu-system-x86_64",
            "-accel", "whpx",                 # Activa Hyper-V de Windows para acelerar la CPU
            "-m", str(vm_info["ram"]),
            "-smp", f"cores={vm_info['nucleos']},threads={vm_info['hilos']}",
            "-boot", "d"
        ]

        # 🎛️ CONFIGURACIÓN DE DISCO OPTIMIZADA PARA SSD (TRIM + VirtIO + Discard)
        if vm_info["addons"]:
            # 1. Creamos el dispositivo de almacenamiento usando el bus VirtIO (ultra rápido)
            # 2. 'discard=on' y 'detect-zeroes=unmap' habilitan el comando TRIM real en el SSD host
            # 3. 'cache=none' o 'cache=writeback' seguro con 'aio=threads'
            comando.extend([
                "-device", "virtio-blk-pci,drive=hd0", # <--- CORREGIDO: cambiado 'virtio-blk-papi' por 'pci'
                "-drive", f"file={disco_path},if=none,id=hd0,format=qcow2,cache=none,aio=threads,discard=on,detect-zeroes=unmap"
            ])
            
            # Carpeta compartida (Opcional, se mantiene de tu código original)
            os.makedirs("compartido_vm", exist_ok=True)
            comando.extend(["-virtfs", f"local,path=./compartido_vm,mount_tag=host0,security_model=passthrough"])
            print("🚀 Add-ons y optimización de SSD (TRIM/VirtIO) activados de forma segura.")
        else:
            # Arranque estándar si no se activan los Add-ons
            comando.extend(["-hda", disco_path])

        if vm_info["iso"]:
            comando.extend(["-cdrom", vm_info["iso"]])

        def run_qemu():
            try:
                # 🔒 SEGURIDAD: Eliminamos 'shell=True' y pasamos la lista de comandos directamente.
                # Ya no usamos shlex.quote ni strings planos, evitando inyecciones de código.
                print(f"Ejecutando QEMU de forma segura de modo nativo...")
                proceso = subprocess.Popen(comando, shell=False)
                proceso.wait()
                print("VM apagada.")
            except Exception as e:
                messagebox.showerror("Error al iniciar", f"No se pudo iniciar QEMU:\n{e}")

        threading.Thread(target=run_qemu, daemon=True).start()


    # ==========================================
    # LOGROS
    # ==========================================
    def mostrar_logros(self):
        top_logros = tk.Toplevel(self.root)
        top_logros.title("Logros de windowVM")
        top_logros.geometry("350x300")
        top_logros.configure(bg=THEME["colors"]["bg_main"])
        
        tk.Label(top_logros, text="🏆 Tus Logros", font=THEME["fonts"]["title"], bg=THEME["colors"]["bg_main"]).pack(pady=20)
        
        logros_actuales = {
            "Crear primera VM": len(self.vms_creadas) > 0,
            "Cargar una ISO": any(vm["iso"] for vm in self.vms_creadas),
            "Activar Especial Add-ons": any(vm["addons"] for vm in self.vms_creadas)
        }
        
        for logro, completado in logros_actuales.items():
            estado = "✅ Completado" if completado else "❌ Bloqueado"
            color = "green" if completado else "red"
            frame = tk.Frame(top_logros, bg=THEME["colors"]["bg_main"])
            frame.pack(fill="x", padx=40, pady=5)
            tk.Label(frame, text=logro, bg=THEME["colors"]["bg_main"], font=THEME["fonts"]["text"]).pack(side="left")
            tk.Label(frame, text=estado, bg=THEME["colors"]["bg_main"], fg=color, font=THEME["fonts"]["text_bold"]).pack(side="right")

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowVMApp(root)
    root.mainloop()
