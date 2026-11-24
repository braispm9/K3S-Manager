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


class K3sManagerApp:

  def __init__(self, root):
    self.root = root
    self.root.title("K3s Manager — Modular Control Center")
    self.root.geometry("520x360")
    self.root.minsize(480, 320)

    self.bg_window = "#0b0f19"
    self.bg_card = "#111827"
    self.accent = "#38bdf8"
    self.text_main = "#f8fafc"
    self.text_muted = "#94a3b8"

    self.root.configure(bg=self.bg_window)
    self.current_working_dir = os.path.expanduser("~")

    # Estilos globales
    style = ttk.Style()
    style.theme_use("clam")
    style.configure(
        ".",
        background=self.bg_card,
        foreground=self.text_main,
        font=("Segoe UI", 10),
    )

    # Ventanas hijas abiertas para evitar duplicados
    self.open_windows = {}

    self.create_main_hub()

  def create_main_hub(self):
    # Contenedor Principal del Hub
    main_frame = tk.Frame(self.root, bg=self.bg_window)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    tk.Label(
        main_frame,
        text="K3s Manager Control Hub",
        bg=self.bg_window,
        fg=self.accent,
        font=("Segoe UI", 14, "bold"),
    ).pack(pady=(0, 15))

    modules_frame = tk.Frame(main_frame, bg=self.bg_window)
    modules_frame.pack(fill=tk.BOTH, expand=True)

    btn_configs = [
        (
            "📦 Pod Management",
            "pods",
            "Manage pods, logs, deployment & selection",
        ),
        (
            "🌐 Network & Ports",
            "net",
            "Network policies, port scanning & tests",
        ),
        ("🛡️ Audit & Security", "audit", "Live connection monitoring & updates"),
        ("📖 User Guide", "help", "Commands and manual reference"),
    ]

    for title, mod_key, desc in btn_configs:
      card = tk.Frame(modules_frame, bg=self.bg_card, bd=1, relief="solid")
      card.pack(fill=tk.X, pady=6)

      info_f = tk.Frame(card, bg=self.bg_card)
      info_f.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=10)

      tk.Label(
          info_f,
          text=title,
          bg=self.bg_card,
          fg=self.text_main,
          font=("Segoe UI", 11, "bold"),
          anchor="w",
      ).pack(fill=tk.X)
      tk.Label(
          info_f,
          text=desc,
          bg=self.bg_card,
          fg=self.text_muted,
          font=("Segoe UI", 9),
          anchor="w",
      ).pack(fill=tk.X)

      tk.Button(
          card,
          text="Open Module",
          command=lambda k=mod_key: self.open_module_window(k),
          bg="#1e293b",
          fg=self.accent,
          activebackground=self.accent,
          activeforeground="#0f172a",
          relief=tk.FLAT,
          font=("Segoe UI", 9, "bold"),
          padx=12,
          pady=8,
      ).pack(side=tk.RIGHT, padx=12, pady=10)

    # Barra inferior de herramientas rápidas
    tool_f = tk.Frame(main_frame, bg=self.bg_window)
    tool_f.pack(fill=tk.X, pady=(10, 0))

    tk.Button(
        tool_f,
        text="💻 External Terminal",
        command=self.open_external_terminal,
        bg="#161e2e",
        fg=self.text_muted,
        relief=tk.FLAT,
        font=("Segoe UI", 9),
    ).pack(side=tk.LEFT)

    if not os.path.exists(SCRIPT_BASH):
      messagebox.showwarning(
          "Warning", f"Script '{SCRIPT_BASH}' not found in current directory!"
      )

  def open_module_window(self, mod_key):
    # Si la ventana ya está abierta, traerla al frente
    if mod_key in self.open_windows and self.open_windows[mod_key].winfo_exists():
      self.open_windows[mod_key].lift()
      return

    win = tk.Toplevel(self.root)
    win.configure(bg=self.bg_window)
    self.open_windows[mod_key] = win

    if mod_key == "pods":
      win.title("K3s Manager — Pod Management")
      win.geometry("900x650")
      self.build_pod_window(win)
    elif mod_key == "net":
      win.title("K3s Manager — Network & Ports")
      win.geometry("750x600")
      self.build_net_window(win)
    elif mod_key == "audit":
      win.title("K3s Manager — Audit & Security")
      win.geometry("700x550")
      self.build_audit_window(win)
    elif mod_key == "help":
      win.title("K3s Manager — User Guide")
      win.geometry("650x500")
      self.build_help_window(win)

  # ==========================================
  # MÓDULO 1: GESTIÓN DE PODS (Con Creación y Logs)
  # ==========================================
  def build_pod_window(self, win):
    container = tk.Frame(win, bg=self.bg_card)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Botones de acción rápida
    btn_f = tk.Frame(container, bg=self.bg_card)
    btn_f.pack(fill=tk.X, padx=10, pady=10)

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
          btn_f,
          text=txt,
          command=cmd,
          bg="#1e293b",
          fg=self.text_main,
          relief=tk.FLAT,
          font=("Segoe UI", 9, "bold"),
          padx=8,
          pady=6,
      ).grid(row=0, column=idx, padx=3, sticky="ew")
      btn_f.columnconfigure(idx, weight=1)

    # Tabla
    table_f = tk.Frame(container, bg=self.bg_card)
    table_f.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    self.tree_pods = ttk.Treeview(
        table_f,
        columns=("ID", "Namespace", "Name"),
        show="headings",
        height=8,
        selectmode="extended",
    )
    for col, w, anchor in [
        ("ID", 60, tk.CENTER),
        ("Namespace", 200, tk.W),
        ("Name", 400, tk.W),
    ]:
      self.tree_pods.heading(col, text=col)
      self.tree_pods.column(col, width=w, anchor=anchor)

    scroll = ttk.Scrollbar(
        table_f, orient=tk.VERTICAL, command=self.tree_pods.yview
    )
    self.tree_pods.configure(yscrollcommand=scroll.set)
    self.tree_pods.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)

    # Controles de IDs y Creación
    ctrl_f = tk.Frame(container, bg=self.bg_card)
    ctrl_f.pack(fill=tk.X, padx=10, pady=10)

    tk.Label(
        ctrl_f, text="IDs / Range:", bg=self.bg_card, fg=self.text_main
    ).grid(row=0, column=0, sticky="w", padx=5)
    self.entry_ids = tk.Entry(
        ctrl_f,
        bg="#0b0f19",
        fg=self.text_main,
        insertbackground="white",
        font=("Segoe UI", 10),
    )
    self.entry_ids.grid(row=0, column=1, padx=5, sticky="ew")

    tk.Button(
        ctrl_f,
        text="Select",
        command=lambda: self.exec_action_ids("add"),
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).grid(row=0, column=2, padx=3)
    tk.Button(
        ctrl_f,
        text="Deselect",
        command=lambda: self.exec_action_ids("remove"),
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).grid(row=0, column=3, padx=3)
    tk.Button(
        ctrl_f,
        text="Get IP",
        command=lambda: self.exec_action_ids("ip"),
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).grid(row=0, column=4, padx=3)

    # Crear Pods
    tk.Label(
        ctrl_f,
        text="Create (Qty/Range):",
        bg=self.bg_card,
        fg=self.text_main,
    ).grid(row=1, column=0, sticky="w", padx=5, pady=8)
    self.entry_create = tk.Entry(
        ctrl_f,
        bg="#0b0f19",
        fg=self.text_main,
        insertbackground="white",
        font=("Segoe UI", 10),
    )
    self.entry_create.grid(row=1, column=1, padx=5, pady=8, sticky="ew")

    tk.Button(
        ctrl_f,
        text="🚀 Create Pods",
        command=self.create_pods_gui,
        bg="#0369a1",
        fg=self.text_main,
        relief=tk.FLAT,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=1, column=2, columnspan=3, sticky="ew", padx=3, pady=8)

    # Consola integrada en la ventana
    self.console_pods = self.create_embedded_console(container)
    self.update_pods_list()

  # ==========================================
  # MÓDULO 2: RED Y PUERTOS
  # ==========================================
  def build_net_window(self, win):
    container = tk.Frame(win, bg=self.bg_card)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tk.Label(
        container,
        text="Pod ID or Range (e.g. 1 or 1-5):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w", padx=10, pady=5)
    self.entry_red_arg = tk.Entry(
        container,
        bg="#0b0f19",
        fg=self.text_main,
        insertbackground="white",
        font=("Segoe UI", 10),
    )
    self.entry_red_arg.pack(fill=tk.X, padx=10, pady=5)

    btn_f = tk.Frame(container, bg=self.bg_card)
    btn_f.pack(fill=tk.X, padx=10, pady=10)

    tk.Button(
        btn_f,
        text="🔍 Scan Ports",
        command=self.gui_check_ports,
        bg="#1e293b",
        fg=self.accent,
        relief=tk.FLAT,
        padx=12,
        pady=6,
    ).pack(side=tk.LEFT, padx=4)
    tk.Button(
        btn_f,
        text="🔒 Isolate / Close",
        command=self.gui_close_port,
        bg="#7f1d1d",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=12,
        pady=6,
    ).pack(side=tk.LEFT, padx=4)
    tk.Button(
        btn_f,
        text="🔓 Restore / Open",
        command=self.gui_open_port,
        bg="#065f46",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=12,
        pady=6,
    ).pack(side=tk.LEFT, padx=4)

    # Tests de conectividad avanzados
    adv_f = tk.LabelFrame(
        container,
        text=" Advanced Tests ",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 9, "bold"),
    )
    adv_f.pack(fill=tk.X, padx=10, pady=10)

    sub_f1 = tk.Frame(adv_f, bg=self.bg_card)
    sub_f1.pack(fill=tk.X, padx=10, pady=6)
    tk.Label(
        sub_f1, text="Test-net range (-a / 1-5):", bg=self.bg_card, fg=self.text_main
    ).pack(side=tk.LEFT)
    self.entry_test_net = tk.Entry(
        sub_f1, bg="#0b0f19", fg=self.text_main, insertbackground="white", width=15
    )
    self.entry_test_net.pack(side=tk.LEFT, padx=10)
    tk.Button(
        sub_f1,
        text="⚡ Run Test Network",
        command=self.gui_test_network,
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).pack(side=tk.LEFT)

    sub_f2 = tk.Frame(adv_f, bg=self.bg_card)
    sub_f2.pack(fill=tk.X, padx=10, pady=6)
    tk.Label(sub_f2, text="Src ID:", bg=self.bg_card, fg=self.text_main).pack(
        side=tk.LEFT
    )
    self.entry_orig = tk.Entry(
        sub_f2, bg="#0b0f19", fg=self.text_main, insertbackground="white", width=6
    )
    self.entry_orig.pack(side=tk.LEFT, padx=5)
    tk.Label(sub_f2, text="Dst ID:", bg=self.bg_card, fg=self.text_main).pack(
        side=tk.LEFT, padx=(10, 0)
    )
    self.entry_dest = tk.Entry(
        sub_f2, bg="#0b0f19", fg=self.text_main, insertbackground="white", width=6
    )
    self.entry_dest.pack(side=tk.LEFT, padx=5)
    tk.Button(
        sub_f2,
        text="⇄ Test Connections",
        command=self.gui_test_connections,
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=10)

    self.console_net = self.create_embedded_console(container)

  # ==========================================
  # MÓDULO 3: AUDITORÍA Y SEGURIDAD
  # ==========================================
  def build_audit_window(self, win):
    container = tk.Frame(win, bg=self.bg_card)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tk.Label(
        container,
        text="Monitor external connections & manage script versions.",
        bg=self.bg_card,
        fg=self.text_muted,
    ).pack(anchor="w", padx=10, pady=5)

    btn_f = tk.Frame(container, bg=self.bg_card)
    btn_f.pack(fill=tk.X, padx=10, pady=10)

    tk.Button(
        btn_f,
        text="📡 Start Connection Monitoring",
        command=self.gui_monitor_connect,
        bg="#1e293b",
        fg=self.accent,
        relief=tk.FLAT,
        padx=12,
        pady=8,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_f,
        text="ℹ️ Check Version",
        command=self.gui_version,
        bg="#1e293b",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=12,
        pady=8,
    ).pack(side=tk.LEFT, padx=5)
    tk.Button(
        btn_f,
        text="⬆️ Update Manager",
        command=self.gui_update_script,
        bg="#0369a1",
        fg=self.text_main,
        relief=tk.FLAT,
        padx=12,
        pady=8,
    ).pack(side=tk.LEFT, padx=5)

    self.console_audit = self.create_embedded_console(container)

  # ==========================================
  # MÓDULO 4: GUÍA DE USUARIO
  # ==========================================
  def build_help_window(self, win):
    container = tk.Frame(win, bg=self.bg_card)
    container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    txt = scrolledtext.ScrolledText(
        container,
        bg="#070a12",
        fg=self.accent,
        font=("Consolas", 10),
        bd=0,
        highlightthickness=0,
    )
    txt.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    txt.insert(
        tk.END,
        """====================================================================
K3S MANAGER USER GUIDE (Release 4.21)
====================================================================

--- POD COMMANDS ---
  • pods [ID|N-M|-A]        : List pods with strict IDs.
  • select <IDs>             : Add pod(s) to active selection.
  • remove <IDs>             : Remove pod(s) from selection.
  • clear-sel                : Clear active pod selection.
  • show                     : Show currently selected pods.

--- INFORMATION & ACTIONS ---
  • ip <ID | Name> [ns]      : Get internal IP of a pod.
  • describe [-l]            : View summary or full details.
  • logs                     : Show logs (requires 1 selected pod).
  • delete                   : Delete selected pods.
  • create <N|N-M> [-i img]  : Create pods individually or by range.

--- NETWORK & SECURITY TESTS ---
  • check-ports [ID | N-M]   : Scan open ports.
  • close-port <ID|N-M>      : Block network traffic (NetworkPolicy).
  • open-port <ID|N-M>       : Restore network traffic.
  • monitor-connect          : Monitor incoming traffic in background.
  • test-network [N | N-M]   : Bulk connectivity test.
  • test-connections [src dst]: Direct traffic test between two pods.
""",
    )
    txt.config(state=tk.DISABLED)

  # ==========================================
  # CONSOLA EMBRICADA AUXILIAR
  # ==========================================
  def create_embedded_console(self, parent):
    consola_frame = tk.Frame(parent, bg=self.bg_card)
    consola_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    consola = scrolledtext.ScrolledText(
        consola_frame,
        wrap=tk.WORD,
        height=10,
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        font=("Consolas", 9),
        bd=0,
        highlightthickness=0,
    )
    consola.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    consola.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(
        consola_frame, orient=tk.VERTICAL, command=consola.yview
    )
    consola.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return consola

  # ==========================================
  # FUNCIONES DE EJECUCIÓN Y COMANDOS BASH
  # ==========================================
  def write_console(self, console_target, text):
    if not console_target or not console_target.winfo_exists():
      return

    def _write():
      try:
        console_target.config(state=tk.NORMAL)
        console_target.insert(tk.END, text + "\n")
        console_target.see(tk.END)
        console_target.config(state=tk.DISABLED)
      except Exception:
        pass

    if threading.current_thread() is threading.main_thread():
      _write()
    else:
      self.root.after(0, _write)

  def run_cmd_realtime(self, cmd, console_target):
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
          self.write_console(console_target, clean_ansi(line.strip()))
      process.wait()
    except Exception as e:
      self.write_console(
          console_target, f"Critical error executing command: {str(e)}"
      )

  def update_pods_list(self):
    def tarea():
      if not hasattr(self, "tree_pods") or not self.tree_pods.winfo_exists():
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
            self.console_pods,
            "[NOTICE] Could not list pods or no K3s connection.",
        )
        return

      idx = 1
      for linea in salida.split("\n"):
        partes = linea.split()
        if len(partes) >= 2 and partes[0] != "kube-system":
          self.tree_pods.insert("", tk.END, values=(idx, partes[0], partes[1]))
          idx += 1
      self.write_console(
          self.console_pods, "[OK] Pod table synchronized successfully."
      )

    threading.Thread(target=tarea, daemon=True).start()

  def show_selection(self):
    if not hasattr(self, "tree_pods"):
      return
    selected_items = self.tree_pods.selection()
    if not selected_items:
      self.write_console(self.console_pods, "[INFO] No pods selected in table.")
    else:
      self.write_console(self.console_pods, "\n--- Selected Pods ---")
      for item in selected_items:
        val = self.tree_pods.item(item, "values")
        self.write_console(
            self.console_pods,
            f" • ID: {val[0]} | NS: {val[1]} | Pod: {val[2]}",
        )

  def clear_selection(self):
    if hasattr(self, "tree_pods"):
      self.tree_pods.selection_remove(self.tree_pods.selection())
      self.write_console(self.console_pods, "[OK] Table selection cleared.")

  def view_logs(self):
    selected = self.tree_pods.selection()
    if len(selected) != 1:
      messagebox.showerror(
          "Error", "Please select exactly 1 pod to view logs."
      )
      return
    val = self.tree_pods.item(selected[0], "values")
    self.write_console(
        self.console_pods, f"\n--- Fetching Logs for: {val[2]} ({val[1]}) ---"
    )
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"kubectl logs {val[2]} -n {val[1]} --tail=50", self.console_pods
        ),
        daemon=True,
    ).start()

  def describe_pod(self):
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror(
          "Error", "Please select at least one pod to describe."
      )
      return

    def tarea():
      for item in selected:
        val = self.tree_pods.item(item, "values")
        self.write_console(
            self.console_pods, f"\n=== DESCRIBE: {val[2]} ({val[1]}) ==="
        )
        self.run_cmd_realtime(
            f"kubectl describe pod {val[2]} -n {val[1]}", self.console_pods
        )

    threading.Thread(target=tarea, daemon=True).start()

  def delete_pods_sel(self):
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "No pods selected for deletion.")
      return
    if messagebox.askyesno(
        "Confirm Deletion",
        f"Are you sure you want to delete {len(selected)} selected pod(s)?",
    ):

      def tarea():
        for item in selected:
          val = self.tree_pods.item(item, "values")
          self.write_console(
              self.console_pods, f"Deleting pod {val[2]} in {val[1]}..."
          )
          self.run_cmd_realtime(
              f"kubectl delete pod {val[2]} -n {val[1]}", self.console_pods
          )
        self.update_pods_list()

      threading.Thread(target=tarea, daemon=True).start()

  def exec_action_ids(self, accion):
    arg = self.entry_ids.get().strip()
    if not arg:
      messagebox.showerror("Error", "Please enter a valid ID or range.")
      return

    def tarea():
      self.write_console(
          self.console_pods,
          f"\nExecuting action '{accion}' with argument '{arg}'...",
      )
      cmd = (
          f"bash {SCRIPT_BASH} {accion} pod {arg}"
          if accion in ["add", "remove"]
          else f"bash {SCRIPT_BASH} ip {arg}"
      )
      self.run_cmd_realtime(cmd, self.console_pods)

    threading.Thread(target=tarea, daemon=True).start()

  def create_pods_gui(self):
    param = self.entry_create.get().strip()
    if not param:
      messagebox.showerror(
          "Error", "Specify a quantity or range (e.g. 3 or 1-5)."
      )
      return

    def tarea():
      self.write_console(self.console_pods, f"\nDeploying pods ({param})...")
      self.run_cmd_realtime(
          f"bash {SCRIPT_BASH} create {param}", self.console_pods
      )
      self.update_pods_list()

    threading.Thread(target=tarea, daemon=True).start()

  def gui_check_ports(self):
    arg = self.entry_red_arg.get().strip()
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} check-ports {arg}", self.console_net
        ),
        daemon=True,
    ).start()

  def gui_close_port(self):
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Specify an ID or range to isolate.")
      return
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} close-port {arg}", self.console_net
        ),
        daemon=True,
    ).start()

  def gui_open_port(self):
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Specify an ID or range to restore.")
      return
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} open-port {arg}", self.console_net
        ),
        daemon=True,
    ).start()

  def gui_test_network(self):
    arg = self.entry_test_net.get().strip()
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} test-network {arg}", self.console_net
        ),
        daemon=True,
    ).start()

  def gui_test_connections(self):
    orig, dest = self.entry_orig.get().strip(), self.entry_dest.get().strip()
    if not orig or not dest:
      messagebox.showerror("Error", "Enter both source and destination IDs.")
      return
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} test-connections {orig} {dest}",
            self.console_net,
        ),
        daemon=True,
    ).start()

  def gui_monitor_connect(self):
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} monitor-connect", self.console_audit
        ),
        daemon=True,
    ).start()

  def gui_version(self):
    threading.Thread(
        target=lambda: self.run_cmd_realtime(
            f"bash {SCRIPT_BASH} version", self.console_audit
        ),
        daemon=True,
    ).start()

  def gui_update_script(self):
    if messagebox.askyesno(
        "Update", "Do you want to check and install updates for K3s Manager?"
    ):
      threading.Thread(
          target=lambda: self.run_cmd_realtime(
              f"bash {SCRIPT_BASH} update", self.console_audit
          ),
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
  app = K3sManagerApp(root)
  root.mainloop()
