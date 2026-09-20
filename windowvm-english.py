import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import subprocess
import threading
import shlex

# ==========================================
# "CSS" (Global Styles Dictionary)
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

        # VM list
        self.vms_created = []

        # Temporary variables for creation flow
        self.temp_name = ""
        self.temp_iso = ""
        self.temp_ram = ""
        self.temp_cores = ""
        self.temp_threads = ""
        self.temp_addons = False

        # Load saved data
        self.load_data()

        self.configure_ttk_styles()
        self.create_main_interface()
        self.refresh_vm_list()

    def configure_ttk_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=THEME["colors"]["input_bg"],
                        background=THEME["colors"]["input_bg"], foreground=THEME["colors"]["text_main"])

    # ==========================================
    # PERSISTENCE
    # ==========================================
    def load_data(self):
        if os.path.exists("windowvm_data.json"):
            try:
                with open("windowvm_data.json", "r") as f:
                    data = json.load(f)
                # BUG FIX: if the JSON came from a different version (e.g. the
                # Spanish version, which stores "nombre"/"nucleos"/"hilos"
                # instead of "name"/"cores"/"threads") or has incomplete
                # entries, this used to break rendering of the WHOLE list with
                # a KeyError the next time it was drawn (including any new VM
                # created afterwards). Now each entry is normalized, filling
                # in whatever is missing, and only entries that truly can't be
                # recovered are dropped (without taking down the rest).
                self.vms_created = [v for v in (self._normalize_vm(x) for x in data) if v is not None]
            except Exception as e:
                print(f"Error loading data: {e}")
                self.vms_created = []

    def _normalize_vm(self, vm):
        """Fill in missing keys (from old/incompatible data) so one VM with
        incomplete data doesn't break the rest of the list."""
        if not isinstance(vm, dict):
            print(f"Ignoring invalid VM entry: {vm!r}")
            return None
        name = vm.get("name") or vm.get("nombre")
        if not name:
            print(f"Ignoring VM with no name: {vm!r}")
            return None
        return {
            "name": name,
            "ram": vm.get("ram", "2048"),
            "cores": vm.get("cores", vm.get("nucleos", "2")),
            "threads": vm.get("threads", vm.get("hilos", "4")),
            "iso": vm.get("iso", ""),
            "addons": vm.get("addons", False),
            "disk": vm.get("disk", vm.get("disco", f"vms/{name}.qcow2")),
        }

    def save_data(self):
        try:
            with open("windowvm_data.json", "w") as f:
                json.dump(self.vms_created, f, indent=4)
        except Exception as e:
            messagebox.showerror("Error", f"Could not save data: {e}")

    # ==========================================
    # MAIN INTERFACE
    # ==========================================
    def create_main_interface(self):
        # Right Panel
        self.right_panel = tk.Canvas(self.root, bg=THEME["colors"]["bg_blue_panel"], highlightthickness=0)
        self.right_panel.pack(side="right", fill="both", expand=True)
        self.right_panel.bind("<Configure>", self.draw_right_panel)

        # Left Panel
        self.left_panel = tk.Frame(self.root, bg=THEME["colors"]["bg_main"], width=550)
        self.left_panel.pack(side="left", fill="both", expand=True)
        self.left_panel.pack_propagate(False)

        # Achievements Button
        tk.Button(self.left_panel, text="🏆 Achievements", bg=THEME["colors"]["accent_yellow"], 
                  font=THEME["fonts"]["text_bold"], command=self.show_achievements, 
                  relief="flat", cursor="hand2").place(x=15, y=15)

        # Yellow Circle Icon
        icon_canvas = tk.Canvas(self.left_panel, width=180, height=180, bg=THEME["colors"]["bg_main"], highlightthickness=0)
        icon_canvas.pack(pady=(20, 0))
        icon_canvas.create_oval(5, 5, 175, 175, fill=THEME["colors"]["accent_yellow"], outline="")
        icon_canvas.create_rectangle(45, 50, 135, 110, fill=THEME["colors"]["monitor_screen"], outline="black", width=3)
        icon_canvas.create_polygon(45, 110, 70, 85, 100, 110, fill=THEME["colors"]["monitor_hill"], outline="")
        icon_canvas.create_rectangle(45, 110, 135, 118, fill="black", outline="black")
        icon_canvas.create_line(90, 118, 90, 135, width=3)
        icon_canvas.create_line(70, 135, 110, 135, width=3)

        self.center_frame = tk.Frame(self.left_panel, bg=THEME["colors"]["bg_main"])
        self.center_frame.pack(fill="both", expand=True)

        # Logo
        logo_frame = tk.Frame(self.center_frame, bg=THEME["colors"]["bg_main"])
        logo_frame.pack(pady=(5, 0))
        tk.Label(logo_frame, text="window", font=THEME["fonts"]["logo"], bg=THEME["colors"]["bg_main"], fg="black").pack(side="left")
        tk.Label(logo_frame, text="VM", font=THEME["fonts"]["logo"], bg=THEME["colors"]["bg_main"], fg=THEME["colors"]["accent_orange"]).pack(side="left")

        # Create VM Button
        tk.Button(self.center_frame, text="Create new VM\n+", bg=THEME["colors"]["btn_primary"], fg="white", 
                  font=THEME["fonts"]["text_bold"], width=15, height=2, relief="flat", cursor="hand2", 
                  command=self.open_create_vm_window).pack(pady=THEME["padding"]["medium"])

        # My VMs Title
        tk.Label(self.center_frame, text="── My VMs ──", font=THEME["fonts"]["subtitle"], 
                 bg=THEME["colors"]["bg_main"], fg=THEME["colors"]["text_main"]).pack(pady=(10, 5))
        
        # Scrollable Container
        self.vms_container = tk.Frame(self.center_frame, bg=THEME["colors"]["bg_main"])
        self.vms_container.pack(fill="both", expand=True, padx=20, pady=5)

        self.canvas_vms = tk.Canvas(self.vms_container, bg=THEME["colors"]["bg_main"], highlightthickness=0)
        scrollbar = tk.Scrollbar(self.vms_container, orient="vertical", command=self.canvas_vms.yview)
        self.scrollable_frame = tk.Frame(self.canvas_vms, bg=THEME["colors"]["bg_main"])

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_vms.configure(scrollregion=self.canvas_vms.bbox("all")))
        self.canvas_vms.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_vms.configure(yscrollcommand=scrollbar.set)
        
        # Adjust width dynamically
        self.canvas_vms.bind("<Configure>", lambda e: self.canvas_vms.itemconfig(
            self.canvas_vms.find_all()[0], width=e.width))

        self.canvas_vms.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def draw_right_panel(self, event):
        canvas = event.widget
        W, H = event.width, event.height
        canvas.delete("all")
        canvas.create_rectangle(W*0.15, H*0.35, W*0.45, H*0.65, fill=THEME["colors"]["accent_yellow"], outline="")
        canvas.create_rectangle(W*0.55, H*0.35, W*0.85, H*0.65, fill=THEME["colors"]["accent_red"], outline="")
        canvas.create_rectangle(W*0.35, H*0.1, W*0.65, H*0.9, fill=THEME["colors"]["accent_orange"], outline="")

    # ==========================================
    # VM LIST (RENDERING)
    # ==========================================
    def refresh_vm_list(self):
        # Clear
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.vms_created:
            tk.Label(self.scrollable_frame, text="No VMs :(", font=("Arial", 18, "bold"), 
                     fg=THEME["colors"]["text_muted"], bg=THEME["colors"]["bg_main"]).pack(pady=30)
            tk.Label(self.scrollable_frame, text=":(", font=("Arial", 30, "bold"), 
                     fg="black", bg=THEME["colors"]["bg_main"]).pack()
            return

        for i, vm in enumerate(self.vms_created):
            # BUG FIX: if a single card failed to render (e.g. incomplete
            # data), this used to abort the whole loop and NO further VM
            # would be drawn, including the one that was just created. Now
            # only the problematic card is skipped and the rest continue.
            try:
                card = tk.Frame(self.scrollable_frame, bg=THEME["colors"]["vm_card_bg"], relief="solid", bd=1)
                card.pack(fill="x", pady=4, padx=5)

                # Info
                info_frame = tk.Frame(card, bg=THEME["colors"]["vm_card_bg"])
                info_frame.pack(side="left", padx=10, pady=8, fill="x", expand=True)

                tk.Label(info_frame, text=vm["name"], font=THEME["fonts"]["text_bold"], 
                         bg=THEME["colors"]["vm_card_bg"], anchor="w").pack(anchor="w")
                tk.Label(info_frame, text=f"RAM: {vm['ram']}MB  |  CPU: {vm['cores']}C/{vm['threads']}T  |  Add-ons: {'Yes' if vm['addons'] else 'No'}", 
                         font=THEME["fonts"]["small"], bg=THEME["colors"]["vm_card_bg"], fg="gray").pack(anchor="w")

                # Start Button
                tk.Button(card, text="▶ Start", bg=THEME["colors"]["btn_success"], fg="white", 
                          font=THEME["fonts"]["text_bold"], relief="flat", cursor="hand2",
                          command=lambda v=vm: self.start_vm_real(v)).pack(side="right", padx=10, pady=8)

                # Delete Button
                tk.Button(card, text="🗑", bg=THEME["colors"]["btn_danger"], fg="white", 
                          font=("Arial", 10, "bold"), relief="flat", cursor="hand2", width=3,
                          command=lambda idx=i: self.delete_vm(idx)).pack(side="right", padx=2, pady=8)
            except Exception as e:
                print(f"Could not render VM at position {i} ({vm}): {e}")
                continue

    def delete_vm(self, index):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this VM from the list?"):
            del self.vms_created[index]
            self.save_data()
            self.refresh_vm_list()

    # ==========================================
    # CREATION FLOW (STEP BY STEP, SAVING DATA)
    # ==========================================
    def open_create_vm_window(self):
        self.create_window = tk.Toplevel(self.root)
        self.create_window.title("Create VM")
        self.create_window.geometry("650x450")
        self.create_window.configure(bg=THEME["colors"]["bg_main"])
        self.create_window.resizable(False, False)
        self.create_window.grab_set()

        # Blue Left Panel
        blue_panel = tk.Canvas(self.create_window, width=200, height=450, bg=THEME["colors"]["bg_sidebar_blue"], highlightthickness=0)
        blue_panel.pack(side="left", fill="y")
        blue_panel.create_line(20, 220, 100, 220, fill=THEME["colors"]["accent_orange"], width=12)
        blue_panel.create_line(60, 180, 60, 260, fill=THEME["colors"]["accent_orange"], width=12)
        blue_panel.create_rectangle(100, 170, 190, 240, fill="#bbdefb", outline="black", width=4)
        blue_panel.create_rectangle(105, 175, 185, 230, fill=THEME["colors"]["monitor_screen"], outline="black", width=2)
        blue_panel.create_polygon(105, 230, 135, 200, 165, 230, fill=THEME["colors"]["monitor_hill"], outline="")
        blue_panel.create_arc(125, 185, 155, 215, start=0, extent=180, style=tk.ARC, outline="black", width=2)
        blue_panel.create_oval(130, 190, 135, 195, fill="black")
        blue_panel.create_oval(145, 190, 150, 195, fill="black")
        blue_panel.create_rectangle(135, 240, 155, 255, fill="black")
        blue_panel.create_rectangle(115, 255, 175, 260, fill="black")

        # Form
        form_panel = tk.Frame(self.create_window, bg=THEME["colors"]["bg_main"])
        form_panel.pack(side="left", fill="both", expand=True, padx=30, pady=30)

        tk.Label(form_panel, text="Create VM", font=THEME["fonts"]["title"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", pady=(0, 20))
        tk.Label(form_panel, text="VM Name......", font=THEME["fonts"]["text"], bg=THEME["colors"]["input_bg"], width=25, anchor="w").pack(pady=5)
        self.name_entry = tk.Entry(form_panel, bg="#f5f5f5", relief="solid", bd=1, font=THEME["fonts"]["text"])
        self.name_entry.pack(fill="x", pady=5)

        self.iso_button = tk.Button(form_panel, text="Load ISO..", bg=THEME["colors"]["input_bg"], font=THEME["fonts"]["text"], 
                                    relief="solid", bd=1, cursor="hand2", command=self.load_iso)
        self.iso_button.pack(pady=10, anchor="w")

        tk.Label(form_panel, text="OS....", font=THEME["fonts"]["text"], bg=THEME["colors"]["input_bg"], width=10, anchor="w").pack(pady=5)
        self.os_combo = ttk.Combobox(form_panel, values=["Windows", "Linux", "MacOS", "Other"], font=THEME["fonts"]["text"])
        self.os_combo.pack(fill="x")

        tk.Label(form_panel, text="Type....", font=THEME["fonts"]["text"], bg=THEME["colors"]["input_bg"], width=10, anchor="w").pack(pady=5)
        self.type_combo = ttk.Combobox(form_panel, values=["64-bit", "32-bit", "ARM"], font=THEME["fonts"]["text"])
        self.type_combo.pack(fill="x")

        btn_frame = tk.Frame(form_panel, bg=THEME["colors"]["bg_main"])
        btn_frame.pack(side="bottom", pady=20)
        tk.Button(btn_frame, text="Accept", fg=THEME["colors"]["bg_sidebar_blue"], bg="white", font=THEME["fonts"]["text_bold"], 
                  relief="solid", bd=2, width=10, cursor="hand2", command=self.step1_to_hardware).pack(side="left", padx=10)
        tk.Button(btn_frame, text="Cancel", bg="white", font=THEME["fonts"]["text"], relief="flat", 
                  cursor="hand2", command=self.create_window.destroy).pack(side="left", padx=10)

    def load_iso(self):
        file = filedialog.askopenfilename(title="Select ISO Image", 
                                          filetypes=[("ISO Files", "*.iso"), ("All Files", "*.*")])
        if file:
            self.temp_iso = file
            self.iso_button.config(text="ISO Loaded ✓", fg="green")

    def step1_to_hardware(self):
        """Save name BEFORE destroying the window"""
        self.temp_name = self.name_entry.get().strip()
        if not self.temp_name:
            messagebox.showwarning("Missing name", "Please enter a name for the VM.")
            return
        self.create_window.destroy()
        self.open_hardware_window()

    def open_hardware_window(self):
        self.hardware_window = tk.Toplevel(self.root)
        self.hardware_window.title("VM Hardware")
        self.hardware_window.geometry("400x350")
        self.hardware_window.configure(bg=THEME["colors"]["bg_main"])
        self.hardware_window.grab_set()

        tk.Label(self.hardware_window, text="Hardware Configuration", font=THEME["fonts"]["subtitle"], bg=THEME["colors"]["bg_main"]).pack(pady=20)
        
        tk.Label(self.hardware_window, text="RAM (MB).....", font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", padx=60)
        self.ram_entry = tk.Entry(self.hardware_window, width=30, font=THEME["fonts"]["text"])
        self.ram_entry.insert(0, "2048")
        self.ram_entry.pack(pady=5)

        tk.Label(self.hardware_window, text="Cores.....", font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", padx=60)
        self.cores_entry = tk.Entry(self.hardware_window, width=30, font=THEME["fonts"]["text"])
        self.cores_entry.insert(0, "2")
        self.cores_entry.pack(pady=5)

        tk.Label(self.hardware_window, text="Threads.....", font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"]).pack(anchor="w", padx=60)
        self.threads_entry = tk.Entry(self.hardware_window, width=30, font=THEME["fonts"]["text"])
        self.threads_entry.insert(0, "4")
        self.threads_entry.pack(pady=5)

        tk.Button(self.hardware_window, text="Next", bg=THEME["colors"]["btn_primary"], fg="white", font=THEME["fonts"]["text_bold"], 
                  width=15, relief="flat", cursor="hand2", command=self.step2_to_addons).pack(pady=20)

    def step2_to_addons(self):
        """Save hardware values BEFORE destroying the window"""
        self.temp_ram = self.ram_entry.get().strip() or "2048"
        self.temp_cores = self.cores_entry.get().strip() or "2"
        self.temp_threads = self.threads_entry.get().strip() or "4"
        self.hardware_window.destroy()
        self.open_addons_window()

    def open_addons_window(self):
        self.addons_window = tk.Toplevel(self.root)
        self.addons_window.title("Special Add-ons")
        self.addons_window.geometry("480x280")
        self.addons_window.configure(bg=THEME["colors"]["bg_main"])
        self.addons_window.grab_set()

        tk.Label(self.addons_window, text="✨ Special Add-ons ✨", font=THEME["fonts"]["subtitle"], fg=THEME["colors"]["accent_orange"], bg=THEME["colors"]["bg_main"]).pack(pady=20)
        text = ("Do you want to enable Special Add-ons?\n\n"
                "• Drag and drop files to the VM screen\n"
                "• Direct installation inside the VM\n"
                "• Maximum use of your SSD")
        tk.Label(self.addons_window, text=text, font=THEME["fonts"]["text"], bg=THEME["colors"]["bg_main"], justify="center").pack(pady=10)

        btn_frame = tk.Frame(self.addons_window, bg=THEME["colors"]["bg_main"])
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Enable", bg="#4caf50", fg="white", font=THEME["fonts"]["text_bold"], width=12, relief="flat", 
                  cursor="hand2", command=lambda: self.finalize_creation(True)).pack(side="left", padx=10)
        tk.Button(btn_frame, text="No, thanks", bg="#9e9e9e", fg="white", font=THEME["fonts"]["text"], width=12, relief="flat", 
                  cursor="hand2", command=lambda: self.finalize_creation(False)).pack(side="left", padx=10)

    def finalize_creation(self, addons):
        """Runs after choosing Add-ons. All data is already saved."""
        self.temp_addons = addons
        self.addons_window.destroy()

        # BUG FIX: this whole block could fail silently (e.g. no permission
        # to create the "vms" folder, or any other unexpected error). Being
        # inside a button callback, Tkinter would swallow the exception, only
        # print it to the console, and the VM would end up neither created
        # nor shown, with no clue for the user as to why. Now it's caught and
        # reported with a clear message.
        try:
            # Create folder for VMs
            os.makedirs("vms", exist_ok=True)

            # Create VM record
            vm_info = {
                "name": self.temp_name,
                "ram": self.temp_ram,
                "cores": self.temp_cores,
                "threads": self.temp_threads,
                "iso": self.temp_iso,
                "addons": self.temp_addons,
                "disk": f"vms/{self.temp_name}.qcow2"
            }

            # Add to list and save
            self.vms_created.append(vm_info)
            self.save_data()

            # UPDATE MAIN LIST
            self.refresh_vm_list()
        except Exception as e:
            messagebox.showerror("Error creating VM", f"Could not create the VM:\n{e}")
            return

        # BUG FIX: if there were already enough VMs to fill the visible area,
        # the new card gets added at the bottom of the list but the scroll
        # position stays where it was (at the top), leaving the newly created
        # VM out of view. Force the scroll to the bottom so it's visible right away.
        self.canvas_vms.update_idletasks()
        self.canvas_vms.yview_moveto(1.0)

        # Clear temporary variables
        self.temp_name = ""
        self.temp_iso = ""
        self.temp_ram = ""
        self.temp_cores = ""
        self.temp_threads = ""
        self.temp_addons = False

        messagebox.showinfo("VM Created", f"VM '{vm_info['name']}' created successfully!\n\nIt now appears in 'My VMs'.")

    # ==========================================
    # START VM WITH QEMU (OPTIMIZED FOR SSD)
    # ==========================================
    def start_vm_real(self, vm_info):
        disk_path = vm_info["disk"]
        if not os.path.exists(disk_path):
            try:
                print(f"Creating virtual disk: {disk_path}...")
                subprocess.run(["qemu-img", "create", "-f", "qcow2", disk_path, "20G"], check=True)
            except FileNotFoundError:
                messagebox.showerror("Critical Error", "QEMU is not installed or not in PATH.\n\n"
                                     "Download it from: https://qemu.org")
                return
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Error creating virtual disk: {e}")
                return

        # 🚀 BASE COMMAND WITH WINDOWS HARDWARE ACCELERATION (WHPX)
        # This forces the VM to run at native speed instead of 10% software emulation
        command = [
            "qemu-system-x86_64",
            "-accel", "whpx",                 # Enables Windows Hypervisor Platform
            "-m", str(vm_info["ram"]),
            "-smp", f"cores={vm_info['cores']},threads={vm_info['threads']}",
            "-boot", "d"
        ]

        # 🎛️ SSD OPTIMIZED STORAGE CONFIGURATION (TRIM + VirtIO + Discard)
        if vm_info["addons"]:
            # 1. We create the storage device using the high-performance VirtIO bus
            # 2. 'discard=on' and 'detect-zeroes=unmap' enable real TRIM commands on the host SSD
            # 3. 'cache=none' paired with 'aio=threads' ensures data integrity and speed
            command.extend([
                "-device", "virtio-blk-pci,drive=hd0",
                "-drive", f"file={disk_path},if=none,id=hd0,format=qcow2,cache=none,aio=threads,discard=on,detect-zeroes=unmap"
            ])
            
            # Shared folder setup
            os.makedirs("shared_vm", exist_ok=True)
            command.extend(["-virtfs", f"local,path=./shared_vm,mount_tag=host0,security_model=passthrough"])
            print("🚀 Add-ons and SSD optimization (TRIM/VirtIO) securely enabled.")
        else:
            # Standard fallback boot if Special Add-ons are disabled
            command.extend(["-hda", disk_path])

        if vm_info["iso"]:
            command.extend(["-cdrom", vm_info["iso"]])

        def run_qemu():
            try:
                # 🔒 SECURITY FIX: We remove 'shell=True' and pass the arguments array directly.
                # No longer using shlex.quote or plain string formatting, preventing any shell injection bugs.
                print(f"Running QEMU securely via native subprocess...")
                process = subprocess.Popen(command, shell=False)
                process.wait()
                process.wait()
                print("VM shut down.")
            except Exception as e:
                messagebox.showerror("Startup Error", f"Could not start QEMU:\n{e}")

        threading.Thread(target=run_qemu, daemon=True).start()


    # ==========================================
    # ACHIEVEMENTS
    # ==========================================
    def show_achievements(self):
        achievements_window = tk.Toplevel(self.root)
        achievements_window.title("windowVM Achievements")
        achievements_window.geometry("350x300")
        achievements_window.configure(bg=THEME["colors"]["bg_main"])
        
        tk.Label(achievements_window, text="🏆 Your Achievements", font=THEME["fonts"]["title"], bg=THEME["colors"]["bg_main"]).pack(pady=20)
        
        current_achievements = {
            "Create first VM": len(self.vms_created) > 0,
            "Load an ISO": any(vm["iso"] for vm in self.vms_created),
            "Enable Special Add-ons": any(vm["addons"] for vm in self.vms_created)
        }
        
        for achievement, completed in current_achievements.items():
            status = "✅ Completed" if completed else "❌ Locked"
            color = "green" if completed else "red"
            frame = tk.Frame(achievements_window, bg=THEME["colors"]["bg_main"])
            frame.pack(fill="x", padx=40, pady=5)
            tk.Label(frame, text=achievement, bg=THEME["colors"]["bg_main"], font=THEME["fonts"]["text"]).pack(side="left")
            tk.Label(frame, text=status, bg=THEME["colors"]["bg_main"], fg=color, font=THEME["fonts"]["text_bold"]).pack(side="right")

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowVMApp(root)
    root.mainloop()
