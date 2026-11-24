#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pwd
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import webbrowser

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_BASH = os.path.join(BASE_DIR, "k3smanager.sh")


def clean_ansi(text):
  ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
  return ansi_escape.sub("", text)


class K3sManagerModularGUI:

  def __init__(self, root):
    self.root = root
    self.root.title("K3s Manager — Modular Enterprise Dashboard")
    self.root.geometry("1200x850")
    self.root.minsize(950, 700)

    self.bg_window = "#0b0f19"
    self.bg_card = "#111827"
    self.accent = "#38bdf8"
    self.text_main = "#f8fafc"
    self.text_muted = "#94a3b8"

    self.root.configure(bg=self.bg_window)
    self.current_working_dir = os.path.expanduser("~")

    # Estilos globales
    self.style = ttk.Style()
    self.style.theme_use("clam")
    self.style.configure(
        ".",
        background=self.bg_card,
        foreground=self.text_main,
        font=("Segoe UI", 10),
    )
    self.style.configure(
        "Treeview",
        background="#111827",
        foreground=self.text_main,
        fieldbackground="#111827",
        borderwidth=0,
        rowheight=26,
        font=("Segoe UI", 9),
    )
    self.style.configure(
        "Treeview.Heading",
        background="#0b0f19",
        foreground=self.accent,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
    )

    # Menú superior para añadir/gestionar módulos
    self.create_top_menu()

    # Contenedor principal con PanedWindow vertical/horizontal (Permite redimensionar módulos libremente)
    self.main_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
    self.main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Paneles superiores e inferiores deslizantes
    self.top_frame_container = ttk.Frame(self.main_pane)
    self.bottom_frame_container = ttk.Frame(self.main_pane)

    self.main_pane.add(self.top_frame_container, weight=3)
    self.main_pane.add(self.bottom_frame_container, weight=2)

    # Estado de módulos activos
    self.active_modules = {}

    # Construir interfaz inicial limpia
    self.build_pod_module(self.top_frame_container)
    self.build_console_module(self.bottom_frame_container, "Pods Output")

    self.update_pods_list()

  def create_top_menu(self):
    menubar = tk.Menu(
        self.root, bg="#111827", fg=self.text_main, bd=0, activebackground="#1e293b"
    )

    # Menú Modulos
    module_menu = tk.Menu(
        menubar,
        tearoff=0,
        bg="#111827",
        fg=self.text_main,
        activebackground="#1e293b",
    )
    module_menu.add_command(
        label="📦 Load Pod Management", command=lambda: self.load_module("pods")
    )
    module_menu.add_command(
        label="🌐 Load Network & Ports", command=lambda: self.load_module("net")
    )
    module_menu.add_command(
        label="🛡️ Load Audit & Security", command=lambda: self.load_module("audit")
    )
    module_menu.add_command(
        label="📖 Load User Guide", command=lambda: self.load_module("help")
    )
    menubar.add_cascade(label="Modules", menu=module_menu)

    # Menú Terminal / Utilidades
    tools_menu = tk.Menu(
        menubar,
        tearoff=0,
        bg="#111827",
        fg=self.text_main,
        activebackground="#1e293b",
    )
    tools_menu.add_command(
        label="💻 Open External Terminal",
        command=self.open_external_terminal,
    )
    tools_menu.add_command(
        label="🧹 Clear All Consoles", command=self.clear_consoles
    )
    menubar.add_cascade(label="Tools", menu=tools_menu)

    self.root.config(menu=menubar)

  def load_module(self, module_name):
    # Limpiar contenedor superior para alternar módulos de forma fluida y ordenada
    for widget in self.top_frame_container.winfo_children():
      widget.destroy()

    if module_name == "pods":
      self.build_pod_module(self.top_frame_container)
      self.update_pods_list()
    elif module_name == "net":
      self.build_net_module(self.top_frame_container)
    elif module_name == "audit":
      self.build_audit_module(self.top_frame_container)
    elif module_name == "help":
      self.build_help_module(self.top_frame_container)

  def build_pod_module(self, parent):
    container = tk.LabelFrame(
        parent,
        text=" Pod Management Module ",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 10, "bold"),
        bd=2,
        relief="groove",
    )
    container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    # Botones de acción rápida
    btn_frame = tk.Frame(container, bg=self.bg_card)
    btn_frame.pack(fill=tk.X, padx=10, pady=8)

    actions = [
        ("🔄 Refresh", self.update_pods_list),
        ("👁️ View", self.show_selection),
        ("🧹 Clear", self.clear_selection),
        ("📜 Logs", self.view_logs),
        ("🔍 Describe", self.describe_pod),
        ("🗑️ Delete", self.delete_pods_sel),
    ]

    for idx, (txt, cmd) in enumerate(actions):
      tk.Button(
          btn_frame,
          text=txt,
          command=cmd,
          bg="#1e293b",
          fg=self.text_main,
          activebackground=self.accent,
          relief=tk.FLAT,
          font=("Segoe UI", 9, "bold"),
          padx=10,
          pady=5,
      ).grid(row=0, column=idx, padx=4, sticky="ew")
      btn_frame.columnconfigure(idx, weight=1)

    # Tabla Treeview
    table_frame = tk.Frame(container, bg=self.bg_card)
    table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    self.tree_pods = ttk.Treeview(
        table_frame,
        columns=("ID", "Namespace", "Name"),
        show="headings",
        height=8,
        selectmode="extended",
    )
    for col, w, anchor in [
        ("ID", 70, tk.CENTER),
        ("Namespace", 200, tk.W),
        ("Name", 450, tk.W),
    ]:
      self.tree_pods.heading(col, text=col)
      self.tree_pods.column(col, width=w, anchor=anchor)

    scrollbar = ttk.Scrollbar(
        table_frame, orient=tk.VERTICAL, command=self.tree_pods.yview
    )
    self.tree_pods.configure(yscrollcommand=scrollbar.set)
    self.tree_pods.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Controles inferiores de IDs / Despliegue
    ctrl_frame = tk.Frame(container, bg=self.bg_card)
    ctrl_frame.pack(fill=tk.X, padx=10, pady=8)

    tk.Label(
        ctrl_frame,
        text="IDs / Range:",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9),
    ).grid(row=0, column=0, sticky="w", padx=5)
    self.entry_ids = tk.Entry(
        ctrl_frame,
        bg="#0b0f19",
        fg=self.text_main,
        insertbackground="white",
        font=("Segoe UI", 10),
        relief=tk.FLtr if hasattr(tk, "FLtr") else tk.SOLID,
        bd=1,
    )
    self.entry_ids.grid(row=0, column=1, padx=5, sticky="ew")

    tk.Button(
        ctrl_frame,
        text="Select",
        command=lambda: self.exec_action_ids("add"),
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).grid(row=0, column=2, padx=3)
    tk.Button(
        ctrl_frame,
        text="Deselect",
        command=lambda: self.exec_action_ids("remove"),
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).grid(row=0, column=3, padx=3)
    tk.Button(
        ctrl_frame,
        text="Get IP",
        command=lambda: self.exec_action_ids("ip"),
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).grid(row=0, column=4, padx=3)

  def build_net_module(self, parent):
    container = tk.LabelFrame(
        parent,
        text=" Network & Port Control Module ",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 10, "bold"),
        bd=2,
        relief="groove",
    )
    container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    tk.Label(
        container,
        text="Pod ID or Range (e.g. 1-5):",
        bg=self.bg_card,
        fg=self.text_main,
    ).pack(anchor="w", padx=15, pady=5)
    self.entry_red_arg = tk.Entry(
        container,
        bg="#0b0f19",
        fg=self.text_main,
        insertbackground="white",
        font=("Segoe UI", 10),
        bd=1,
    )
    self.entry_red_arg.pack(fill=tk.X, padx=15, pady=5)

    btn_f = tk.Frame(container, bg=self.bg_card)
    btn_f.pack(fill=tk.X, padx=15, pady=10)

    tk.Button(
        btn_f,
        text="🔍 Scan Ports",
        command=self.gui_check_ports,
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_f,
        text="🔒 Isolate / Close",
        command=self.gui_close_port,
        bg="#7f1d1d",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_f,
        text="🔓 Restore / Open",
        command=self.gui_open_port,
        bg="#065f46",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=10,
        pady=5,
    ).pack(side=tk.LEFT, padx=5)

  def build_audit_module(self, parent):
    container = tk.LabelFrame(
        parent,
        text=" Audit & System Control Module ",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 10, "bold"),
        bd=2,
        relief="groove",
    )
    container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    tk.Button(
        container,
        text="📡 Start Connection Monitoring",
        command=self.gui_monitor_connect,
        bg="#1e293b",
        fg=self.accent,
        relief=tk.FLAT,
        padx=15,
        pady=8,
    ).pack(anchor="w", padx=15, pady=15)
    tk.Button(
        container,
        text="ℹ️ Check Version & Updates",
        command=self.gui_version,
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=15,
        pady=8,
    ).pack(anchor="w", padx=15, pady=5)

  def build_help_module(self, parent):
    container = tk.LabelFrame(
        parent,
        text=" User Guide ",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 10, "bold"),
        bd=2,
        relief="groove",
    )
    container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    txt = scrolledtext.ScrolledText(
        container,
        bg="#070a12",
        fg=self.accent,
        font=("Consolas", 10),
        bd=0,
        highlightthickness=0,
    )
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    txt.insert(
        tk.END,
        """K3S MANAGER MODULAR GUI (Release 4.21)
Use the top 'Modules' menu to load different operational windows into this panel seamlessly without breaking layout constraints.
- Pod Management: Handle cluster pods, logs, and executions.
- Network & Ports: Manage network policies and security filters.
- Audit: Monitor inbound traffic and system versions.""",
    )
    txt.config(state=tk.DISABLED)

  def build_console_module(self, parent, title):
    container = tk.LabelFrame(
        parent,
        text=f" {title} ",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 10, "bold"),
        bd=2,
        relief="groove",
    )
    container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    self.console = scrolledtext.ScrolledText(
        container,
        wrap=tk.WORD,
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        font=("Consolas", 9),
        bd=0,
        highlightthickness=0,
    )
    self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    self.console.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(
        container, orient=tk.VERTICAL, command=self.console.yview
    )
    self.console.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)

  def write_console(self, text):
    if not hasattr(self, "console") or not self.console:
      return

    def _write():
      self.console.config(state=tk.NORMAL)
      self.console.insert(tk.END, text + "\n")
      self.console.see(tk.END)
      self.console.config(state=tk.DISABLED)

    if threading.current_thread() is threading.main_thread():
      _write()
    else:
      self.root.after(0, _write)

  def clear_consoles(self):
    if hasattr(self, "console") and self.console:
      self.console.config(state=tk.NORMAL)
      self.console.delete("1.0", tk.END)
      self.console.config(state=tk.DISABLED)

  def run_cmd_realtime(self, cmd):
    try:
      process = subprocess.Popen(
          cmd,
          shell=True,
          stdout=subprocess.PIPE,
          stderr=subprocess.STDOUT,
          text=True,
          encoding="utf-8",
          errors="ignore",
          bufsize=1,
      )
      while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
          break
        if line:
          self.write_console(clean_ansi(line.strip()))
      process.wait()
    except Exception as e:
      self.write_console(f"Error executing command: {str(e)}")

  def update_pods_list(self):
    def tarea():
      if not hasattr(self, "tree_pods"):
        return
      for row in self.tree_pods.get_children():
        self.tree_pods.delete(row)

      cmd = (
          "kubectl get pods --all-namespaces --no-headers -o"
          ' custom-columns="NS:.metadata.namespace,NAME:.metadata.name"'
          " 2>/dev/null | sort -k2 -V"
      )
      try:
        resultado = subprocess.run(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
        salida = resultado.stdout.strip()
      except Exception:
        salida = ""

      if not salida:
        self.write_console(
            "[NOTICE] Could not list pods or no K3s connection."
        )
        return

      idx = 1
      for linea in salida.split("\n"):
        partes = linea.split()
        if len(partes) >= 2 and partes[0] != "kube-system":
          self.tree_pods.insert("", tk.END, values=(idx, partes[0], partes[1]))
          idx += 1
      self.write_console("[OK] Pod table synchronized successfully.")

    threading.Thread(target=tarea, daemon=True).start()

  def show_selection(self):
    if not hasattr(self, "tree_pods"):
      return
    selected_items = self.tree_pods.selection()
    if not selected_items:
      self.write_console("[INFO] No pods selected.")
    else:
      self.write_console("\n--- Selected Pods ---")
      for item in selected_items:
        val = self.tree_pods.item(item, "values")
        self.write_console(f" • ID: {val[0]} | NS: {val[1]} | Pod: {val[2]}")

  def clear_selection(self):
    if hasattr(self, "tree_pods"):
      self.tree_pods.selection_remove(self.tree_pods.selection())
      self.write_console("[OK] Selection cleared.")

  def view_logs(self):
    if not hasattr(self, "tree_pods"):
      return
    selected = self.tree_pods.selection()
    if len(selected) != 1:
      messagebox.showerror(
          "Error", "Please select exactly 1 pod to view logs."
      )
      return
    val = self.tree_pods.item(selected[0], "values")
    self.write_console(f"\n--- Fetching Logs for: {val[2]} ({val[1]}) ---")
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"kubectl logs {val[2]} -n {val[1]} --tail=50"
        ),
        daemon=True,
    ).start()

  def describe_pod(self):
    if not hasattr(self, "tree_pods"):
      return
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "Select at least one pod.")
      return
    threading.Thread(
        target=lambda: [
            (
                self.write_console(
                    f"\n=== DESCRIBE: {self.tree_pods.item(i, 'values')[2]} ==="
                ),
                self.run_cmd_realtime(
                    f"kubectl describe pod {self.tree_pods.item(i, 'values')[2]}"
                    f" -n {self.tree_pods.item(i, 'values')[1]}"
                ),
            )
            for i in selected
        ],
        daemon=True,
    ).start()

  def delete_pods_sel(self):
    if not hasattr(self, "tree_pods"):
      return
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "No pods selected.")
      return
    if messagebox.askyesno("Confirm", "Delete selected pods?"):
      threading.Thread(
          target=lambda: [
              self.run_cmd_realtime(
                  f"kubectl delete pod {self.tree_pods.item(i, 'values')[2]} -n"
                  f" {self.tree_pods.item(i, 'values')[1]}"
              )
              for i in selected
          ],
          daemon=True,
      ).start()

  def exec_action_ids(self, accion):
    if not hasattr(self, "entry_ids"):
      return
    arg = self.entry_ids.get().strip()
    if not arg:
      messagebox.showerror("Error", "Enter a valid ID.")
      return
    cmd = (
        f"bash {SCRIPT_BASH} {accion} pod {arg}"
        if accion in ["add", "remove"]
        else f"bash {SCRIPT_BASH} ip {arg}"
    )
    threading.Thread(
        target=lambda: self.run_cmd_realtime(cmd), daemon=True
    ).start()

  def gui_check_ports(self):
    arg = self.entry_red_arg.get().strip() if hasattr(self, "entry_red_arg") else ""
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} check-ports {arg}"
        ),
        daemon=True,
    ).start()

  def gui_close_port(self):
    arg = self.entry_red_arg.get().strip() if hasattr(self, "entry_red_arg") else ""
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} close-port {arg}"
        ),
        daemon=True,
    ).start()

  def gui_open_port(self):
    arg = self.entry_red_arg.get().strip() if hasattr(self, "entry_red_arg") else ""
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} open-port {arg}"
        ),
        daemon=True,
    ).start()

  def gui_monitor_connect(self):
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} monitor-connect"
        ),
        daemon=True,
    ).start()

  def gui_version(self):
    threading.Thread(
        target=lambda: self.run_cmd_realtime(f"bash {SCRIPT_BASH} version"),
        daemon=True,
    ).start()

  def get_configured_shell(self):
    shell_path = os.environ.get("SHELL", "")
    if not shell_path:
      try:
        shell_path = pwd.getpwuid(os.getuid()).pw_shell
      except Exception:
        shell_path = "/bin/bash"
    return (
        shutil.which("zsh")
        if "zsh" in os.path.basename(shell_path).lower()
        else shutil.which("bash")
    ) or "/bin/bash"

  def open_external_terminal(self):
    shell_cmd = self.get_configured_shell()
    for bin_name, args in [
        ("x-terminal-emulator", ["x-terminal-emulator", "-e", shell_cmd]),
        ("gnome-terminal", ["gnome-terminal", "--", shell_cmd]),
        ("konsole", ["konsole", "-e", shell_cmd]),
        ("alacritty", ["alacritty", "-e", shell_cmd]),
        ("xterm", ["xterm", "-e", shell_cmd]),
    ]:
      if shutil.which(bin_name):
        subprocess.Popen(
            args,
            cwd=self.current_working_dir,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    messagebox.showerror("Error", "No terminal emulator found.")


if __name__ == "__main__":
  root = tk.Tk()
  app = K3sManagerModularGUI(root)
  root.mainloop()
