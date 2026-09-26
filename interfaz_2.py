#!/usr/bin/env python3

import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# Archivo de script requerido
# Obtiene la ruta absoluta de la carpeta donde está este script de Python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Une esa ruta con el nombre del script bash
SCRIPT_BASH = os.path.join(BASE_DIR, "k3smanager.sh")


def limpiar_ansi(texto):
  # Función para eliminar los códigos de color de Bash
  ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
  return ansi_escape.sub("", texto)


class RoundedButton(tk.Canvas):
  """Botón personalizado con esquinas redondeadas y efecto smooth."""

  def __init__(
      self,
      parent,
      text,
      command,
      bg_color="#1e293b",
      hover_color="#38bdf8",
      fg_color="#f1f5f9",
      hover_fg="#0f172a",
      radius=12,
      height=36,
      width=140,
      font=("Segoe UI", 9, "bold"),
      bg_canvas="#111827",
  ):
    super().__init__(
        parent,
        height=height,
        width=width,
        bg=bg_canvas,
        highlightthickness=0,
        borderwidth=0,
    )
    self.command = command
    self.bg_color = bg_color
    self.hover_color = hover_color
    self.fg_color = fg_color
    self.hover_fg = hover_fg
    self.radius = radius
    self.text = text
    self.font = font

    self.bind("<Configure>", self.draw)
    self.bind("<Enter>", self.on_enter)
    self.bind("<Leave>", self.on_leave)
    self.bind("<Button-1>", self.on_click)

  def draw(self, event=None):
    self.delete("all")
    w = self.winfo_width()
    h = self.winfo_height()
    if w < 10:
      w = 140
    if h < 10:
      h = 36

    self.create_rounded_rect(2, 2, w - 2, h - 2, self.radius, fill=self.bg_color, outline="")
    self.create_text(w / 2, h / 2, text=self.text, fill=self.fg_color, font=self.font)

  def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
    points = [
        x1 + r, y1, x1 + r, y1,
        x2 - r, y1, x2 - r, y1,
        x2, y1, x2, y1 + r,
        x2, y1 + r, x2, y2 - r,
        x2, y2 - r, x2, y2,
        x2 - r, y2, x2 - r, y2,
        x1 + r, y2, x1 + r, y2,
        x1, y2, x1, y2 - r,
        x1, y2 - r, x1, y1 + r,
        x1, y1 + r, x1, y1
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

  def on_enter(self, event):
    self.delete("all")
    w, h = self.winfo_width(), self.winfo_height()
    self.create_rounded_rect(2, 2, w - 2, h - 2, self.radius, fill=self.hover_color, outline="")
    self.create_text(w / 2, h / 2, text=self.text, fill=self.hover_fg, font=self.font)

  def on_leave(self, event):
    self.draw()

  def on_click(self, event):
    if self.command:
      self.command()


class K3sManagerGUI:

  def __init__(self, root):
    self.root = root
    self.root.title("K3s Manager — Ultra Smooth Enterprise Dashboard")
    self.root.geometry("1120x850")
    self.root.minsize(980, 720)

    self.bg_window = "#0b0f19"
    self.bg_card = "#111827"
    self.accent = "#38bdf8"
    self.text_main = "#f8fafc"
    self.text_muted = "#94a3b8"

    self.root.configure(bg=self.bg_window)

    self.consolas = []  # Lista para almacenar todas las terminales de las pestañas

    self.style = ttk.Style()
    self.style.theme_use("clam")
    self.style.configure(
        ".",
        background=self.bg_window,
        foreground=self.text_main,
        font=("Segoe UI", 10)
    )

    self.style.configure(
        "TEntry",
        fieldbackground="#1e293b",
        foreground=self.text_main,
        insertcolor=self.accent
    )

    self.style.configure("TNotebook", background=self.bg_window, borderwidth=0)
    self.style.configure(
        "TNotebook.Tab",
        font=("Segoe UI", 10, "bold"),
        padding=[18, 10],
        background="#1e293b",
        foreground=self.text_muted,
        borderwidth=0
    )
    self.style.map(
        "TNotebook.Tab",
        background=[("selected", "#111827")],
        foreground=[("selected", self.accent)],
    )

    self.style.configure(
        "TLabelframe",
        background=self.bg_card,
        bordercolor="#1f2937",
        borderwidth=1
    )
    self.style.configure(
        "TLabelframe.Label",
        font=("Segoe UI", 10, "bold"),
        background=self.bg_card,
        foreground=self.accent,
    )

    self.style.configure(
        "Treeview",
        background="#111827",
        foreground=self.text_main,
        fieldbackground="#111827",
        borderwidth=0,
        rowheight=28,
        font=("Segoe UI", 9)
    )
    self.style.configure(
        "Treeview.Heading",
        background="#0b0f19",
        foreground=self.accent,
        font=("Segoe UI", 9, "bold"),
        relief="flat"
    )
    self.style.map(
        "Treeview",
        background=[('selected', '#1f2937')],
        foreground=[('selected', '#38bdf8')]
    )

    self.notebook = ttk.Notebook(root)
    self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)

    self.crear_pestana_pods()
    self.crear_pestana_red()
    self.crear_pestana_auditoria()
    self.crear_pestana_ayuda()

    if not os.path.exists(SCRIPT_BASH):
      self.escribir_consola(f"[ADVERTENCIA] No se encuentra '{SCRIPT_BASH}' en el directorio actual.")
    else:
      self.escribir_consola(f"[OK] Entorno verificado. Script '{SCRIPT_BASH}' detectado correctamente.")

    self.actualizar_lista_pods()

  def escribir_consola(self, texto):
    def _escribir():
      for consola in self.consolas:
        consola.config(state=tk.NORMAL)
        consola.insert(tk.END, texto + "\n")
        consola.see(tk.END)
        consola.config(state=tk.DISABLED)
    if threading.current_thread() is threading.main_thread():
      _escribir()
    else:
      self.root.after(0, _escribir)

  def ejecutar_comando_en_tiempo_real(self, cmd):
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
          linea_limpia = limpiar_ansi(line.strip())
          self.escribir_consola(linea_limpia)
      process.wait()
    except Exception as e:
      self.escribir_consola(f"Error crítico al ejecutar el comando: {str(e)}")

  def crear_consola(self, parent):
    console_frame = ttk.LabelFrame(parent, text=" Terminal de Salida (Logs & Feedback) ", padding=5)
    console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    top_consola_frame = ttk.Frame(console_frame)
    top_consola_frame.pack(fill=tk.BOTH, expand=True)

    consola = scrolledtext.ScrolledText(
        top_consola_frame,
        wrap=tk.WORD,
        height=8,
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        font=("Consolas", 9),
        borderwidth=0
    )
    consola.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    consola.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(top_consola_frame, orient=tk.VERTICAL, command=consola.yview)
    consola.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    btn_frame = ttk.Frame(console_frame)
    btn_frame.pack(fill=tk.X, pady=2)

    def limpiar_esta_consola():
      consola.config(state=tk.NORMAL)
      consola.delete("1.0", tk.END)
      consola.config(state=tk.DISABLED)

    RoundedButton(
        btn_frame,
        text="🧹 Limpiar Consola",
        command=limpiar_esta_consola,
        width=150,
        height=28,
        radius=8,
        bg_color="#1e293b",
        hover_color="#ef4444",
        bg_canvas=self.bg_card
    ).pack(side=tk.RIGHT, padx=2, pady=2)

    self.consolas.append(consola)

  def crear_pestana_pods(self):
    frame = ttk.Frame(self.notebook, padding=10)
    self.notebook.add(frame, text=" 📦 Gestión de Pods ")

    top_frame = ttk.LabelFrame(frame, text=" Acciones Rápidas sobre Pods ", padding=12)
    top_frame.pack(fill=tk.X, padx=5, pady=5)

    btn_config = [
        ("🔄 Actualizar", self.actualizar_lista_pods),
        ("👁️ Ver", self.mostrar_seleccion),
        ("🧹 Limpiar", self.limpiar_seleccion),
        ("📜 Logs (1 Pod)", self.ver_logs),
        ("🔍 Describir", self.describir_pod),
        ("🗑️ Eliminar", self.eliminar_pods_sel),
    ]

    for idx, (text, cmd) in enumerate(btn_config):
      b = RoundedButton(
          top_frame,
          text=text,
          command=cmd,
          bg_color="#1e293b",
          hover_color="#0ea5e9",
          fg_color="#f1f5f9",
          hover_fg="#ffffff",
          radius=12,
          height=36,
          width=140,
          bg_canvas=self.bg_card
      )
      b.grid(row=0, column=idx, padx=4, pady=4, sticky="ew")
      top_frame.columnconfigure(idx, weight=1)

    center_frame = ttk.Frame(frame)
    center_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    columns = ("ID", "Namespace", "Nombre")
    self.tree_pods = ttk.Treeview(center_frame, columns=columns, show="headings", height=10, selectmode="extended")
    self.tree_pods.heading("ID", text="ID Numérico")
    self.tree_pods.heading("Namespace", text="Namespace")
    self.tree_pods.heading("Nombre", text="Nombre del Pod")
    self.tree_pods.column("ID", width=90, anchor=tk.CENTER)
    self.tree_pods.column("Namespace", width=220, anchor=tk.W)
    self.tree_pods.column("Nombre", width=520, anchor=tk.W)

    tree_scroll = ttk.Scrollbar(center_frame, orient=tk.VERTICAL, command=self.tree_pods.yview)
    self.tree_pods.configure(yscrollcommand=tree_scroll.set)

    self.tree_pods.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    action_sub_frame = ttk.LabelFrame(frame, text=" Operaciones por ID y Despliegue ", padding=12)
    action_sub_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(action_sub_frame, text="IDs / Rango (ej: 1,3 o 1-5):").grid(row=0, column=0, sticky=tk.W, padx=5)
    self.entry_ids = ttk.Entry(action_sub_frame, width=18)
    self.entry_ids.grid(row=0, column=1, padx=5)

    RoundedButton(action_sub_frame, text="➕ Añadir", command=lambda: self.ejecutar_accion_ids("add"), bg_color="#1e293b", hover_color="#38bdf8", radius=10, height=32, width=100, bg_canvas=self.bg_card).grid(row=0, column=2, padx=4)
    RoundedButton(action_sub_frame, text="➖ Quitar", command=lambda: self.ejecutar_accion_ids("remove"), bg_color="#1e293b", hover_color="#38bdf8", radius=10, height=32, width=100, bg_canvas=self.bg_card).grid(row=0, column=3, padx=4)
    RoundedButton(action_sub_frame, text="🌐 IP", command=lambda: self.ejecutar_accion_ids("ip"), bg_color="#1e293b", hover_color="#38bdf8", radius=10, height=32, width=100, bg_canvas=self.bg_card).grid(row=0, column=4, padx=4)

    ttk.Label(action_sub_frame, text="Crear Pods (Cant/Rango):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=8)
    self.entry_create = ttk.Entry(action_sub_frame, width=18)
    self.entry_create.grid(row=1, column=1, padx=5, pady=8)

    RoundedButton(action_sub_frame, text="🚀 Crear Pods Prueba", command=self.crear_pods_gui, bg_color="#0369a1", hover_color="#0ea5e9", radius=10, height=32, width=220, bg_canvas=self.bg_card).grid(row=1, column=2, columnspan=3, sticky="w", padx=4, pady=8)

    self.crear_consola(frame)

  def crear_pestana_red(self):
    frame = ttk.Frame(self.notebook, padding=10)
    self.notebook.add(frame, text=" 🌐 Red y Puertos ")

    control_frame = ttk.LabelFrame(frame, text=" Control de Puertos y NetworkPolicies ", padding=15)
    control_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(control_frame, text="ID de Pod o Rango (ej: 1 o 1-5):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
    self.entry_red_arg = ttk.Entry(control_frame, width=25)
    self.entry_red_arg.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

    btn_net_frame = ttk.Frame(control_frame)
    btn_net_frame.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

    RoundedButton(btn_net_frame, text="🔍 Escanear Puertos", command=self.gui_check_ports, width=160, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=5)
    RoundedButton(btn_net_frame, text="🔒 Aislar / Cerrar", command=self.gui_close_port, width=160, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=5)
    RoundedButton(btn_net_frame, text="🔓 Restaurar / Abrir", command=self.gui_open_port, width=160, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=5)

    test_frame = ttk.LabelFrame(
        frame, text=" Pruebas de Conectividad Avanzadas ", padding=15
    )
    test_frame.pack(fill=tk.X, padx=5, pady=10)

    ttk.Label(test_frame, text="Rango test-network (ej: 1-5 o -a):").grid(
        row=0, column=0, sticky=tk.W, padx=5, pady=5
    )
    self.entry_test_net = ttk.Entry(test_frame, width=15)
    self.entry_test_net.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
    RoundedButton(
        test_frame,
        text="⚡ Ejecutar Test",
        command=self.gui_test_network,
        width=150,
        radius=12,
        bg_canvas=self.bg_card,
    ).grid(row=0, column=2, columnspan=2, padx=10, pady=5, sticky=tk.W)

    ttk.Label(test_frame, text="ID Origen:").grid(
        row=1, column=0, sticky=tk.W, padx=5, pady=10
    )
    self.entry_orig = ttk.Entry(test_frame, width=10)
    self.entry_orig.grid(row=1, column=1, sticky=tk.W, padx=5, pady=10)

    ttk.Label(test_frame, text="ID Destino:").grid(
        row=1, column=2, sticky=tk.W, padx=5, pady=10
    )
    self.entry_dest = ttk.Entry(test_frame, width=10)
    self.entry_dest.grid(row=1, column=3, sticky=tk.W, padx=5, pady=10)

    RoundedButton(
        test_frame,
        text="⇄ Probar Tráfico",
        command=self.gui_test_connections,
        width=150,
        radius=12,
        bg_canvas=self.bg_card,
    ).grid(row=1, column=4, padx=10, pady=10)

    self.crear_consola(frame)

  def crear_pestana_auditoria(self):
    frame = ttk.Frame(self.notebook, padding=10)
    self.notebook.add(frame, text=" 🛡️ Auditoría y Sistema ")

    audit_frame = ttk.LabelFrame(frame, text=" Auditoría de Conexiones en Vivo ", padding=15)
    audit_frame.pack(fill=tk.X, padx=5, pady=5)

    ttk.Label(audit_frame, text="Monitoriza accesos externos a los puertos abiertos. Los eventos se registran en logs.").pack(anchor=tk.W, padx=5, pady=5)
    RoundedButton(audit_frame, text="📡 Iniciar Monitorización", command=self.gui_monitor_connect, width=200, radius=12, bg_canvas=self.bg_card).pack(anchor=tk.W, padx=5, pady=10)

    sys_frame = ttk.LabelFrame(frame, text=" Control de Versión y Actualizaciones ", padding=15)
    sys_frame.pack(fill=tk.X, padx=5, pady=10)

    btn_sys_frame = ttk.Frame(sys_frame)
    btn_sys_frame.pack(fill=tk.X, padx=5, pady=5)

    RoundedButton(btn_sys_frame, text="ℹ️ Verificar Versión", command=self.gui_version, width=170, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=5)
    RoundedButton(btn_sys_frame, text="⬆️ Actualizar Manager", command=self.gui_update_script, width=170, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=5)

    self.crear_consola(frame)

  def crear_pestana_ayuda(self):
    frame = ttk.Frame(self.notebook, padding=10)
    self.notebook.add(frame, text=" 📖 Ayuda ")

    help_frame = ttk.LabelFrame(frame, text=" Guía de Uso del Sistema ", padding=5)
    help_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    help_text = scrolledtext.ScrolledText(
        help_frame,
        wrap=tk.WORD,
        font=("Consolas", 9),
        height=12,
        bg="#0b0f19",
        fg="#38bdf8",
        insertbackground="white",
        borderwidth=0
    )
    help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    contenido_ayuda = """====================================================================
GUÍA DE COMANDOS Y ASISTENCIA - K3S MANAGER (Release 3.2)
====================================================================

--- COMANDOS DISPONIBLES PARA PODS ---
  • pods [ID|N-M|namespace|-A] : Listar pods con ID estricto.
  • add pod <IDs...>           : Añadir pod(s) por ID numérico.
  • remove pod <IDs...>        : Quitar pod(s) de la selección.
  • clear-sel                  : Limpiar selección de pods.
  • show                       : Mostrar pods seleccionados.

--- COMANDOS DE INFORMACIÓN Y ACCIÓN ---
  • ip <ID | nombre> [ns]      : Obtener IP interna de un pod.
  • describe [-l]              : Ver información resumida o completa.
  • logs                       : Mostrar logs (requiere 1 solo pod).
  • delete                     : Eliminar pods seleccionados.
  • create <N|N-M> [-i img]    : Crea pods individuales o por rango.

--- PRUEBAS DE RED Y SEGURIDAD ---
  • check-ports [ID | N-M]     : Escanea puertos abiertos.
  • close-port <ID|N-M>        : Bloquea tráfico (NetworkPolicy).
  • open-port <ID|N-M>         : Restablece tráfico de red.
  • monitor-connect            : Monitoriza accesos en background.
  • test-network [N | N-M |-a] : Prueba conectividad masiva.
  • test-connections [orig dst]: Tráfico directo entre dos pods.
"""
    help_text.insert(tk.END, contenido_ayuda)
    help_text.config(state=tk.DISABLED)

    self.crear_consola(frame)

  def actualizar_lista_pods(self):
    def tarea():
      for row in self.tree_pods.get_children():
        self.tree_pods.delete(row)

      cmd = (
          "kubectl get pods --all-namespaces --no-headers -o"
          ' custom-columns="NS:.metadata.namespace,NAME:.metadata.name"'
          " 2>/dev/null | sort -k2 -V"
      )
      try:
        resultado = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="ignore")
        salida = resultado.stdout.strip()
      except Exception:
        salida = ""

      if not salida:
        self.escribir_consola("[AVISO] No se pudieron listar los pods o sin conexión K3s.")
        return

      lineas = salida.split("\n")
      idx = 1
      for linea in lineas:
        partes = linea.split()
        if len(partes) >= 2:
          ns = partes[0]
          if ns != "kube-system":
            name = partes[1]
            self.tree_pods.insert("", tk.END, values=(idx, ns, name))
            idx += 1
      self.escribir_consola("[OK] Tabla de pods sincronizada y actualizada correctamente.")
    threading.Thread(target=tarea, daemon=True).start()

  def mostrar_seleccion(self):
    selected_items = self.tree_pods.selection()
    if not selected_items:
      self.escribir_consola("[INFO] No hay ningún pod seleccionado en la tabla.")
    else:
      self.escribir_consola("\n--- Pods Seleccionados ---")
      for item in selected_items:
        val = self.tree_pods.item(item, "values")
        self.escribir_consola(f" • ID: {val[0]} | NS: {val[1]} | Pod: {val[2]}")

  def limpiar_seleccion(self):
    self.tree_pods.selection_remove(self.tree_pods.selection())
    self.escribir_consola("[OK] Selección de tabla limpiada.")

  def ver_logs(self):
    selected = self.tree_pods.selection()
    if len(selected) != 1:
      messagebox.showerror("Error", "Selecciona exactamente 1 pod de la tabla para ver sus logs.")
      return
    val = self.tree_pods.item(selected[0], "values")
    pod_name, ns = val[2], val[1]
    self.escribir_consola(f"\n--- Descargando Logs de: {pod_name} ({ns}) ---")
    def tarea():
      self.ejecutar_comando_en_tiempo_real(f"kubectl logs {pod_name} -n {ns} --tail=50")
    threading.Thread(target=tarea, daemon=True).start()

  def describir_pod(self):
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "Selecciona al menos un pod de la tabla para describir.")
      return
    def tarea():
      for item in selected:
        val = self.tree_pods.item(item, "values")
        pod_name, ns = val[2], val[1]
        self.escribir_consola(f"\n=== DESCRIPCIÓN: {pod_name} ({ns}) ===")
        self.ejecutar_comando_en_tiempo_real(f"kubectl describe pod {pod_name} -n {ns}")
    threading.Thread(target=tarea, daemon=True).start()

  def eliminar_pods_sel(self):
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "No hay pods seleccionados para eliminar.")
      return
    if messagebox.askyesno("Confirmar Eliminación", f"¿Estás seguro de eliminar los {len(selected)} pod(s) seleccionados?"):
      def tarea():
        for item in selected:
          val = self.tree_pods.item(item, "values")
          pod_name, ns = val[2], val[1]
          self.escribir_consola(f"Eliminando pod {pod_name} en {ns}...")
          self.ejecutar_comando_en_tiempo_real(f"kubectl delete pod {pod_name} -n {ns}")
        self.actualizar_lista_pods()
      threading.Thread(target=tarea, daemon=True).start()

  def ejecutar_accion_ids(self, accion):
    arg = self.entry_ids.get().strip()
    if not arg:
      messagebox.showerror(
          "Error", "Introduce un ID o rango válido en el campo."
      )
      return

    def tarea():
      self.escribir_consola(
          f"\nEjecutando acción '{accion}' con argumento '{arg}'..."
      )
      if accion in ["add", "remove"]:
        cmd = f"bash {SCRIPT_BASH} {accion} pod {arg}"
      elif accion == "ip":
        cmd = f"bash {SCRIPT_BASH} ip {arg}"
      else:
        cmd = f"bash {SCRIPT_BASH} {accion} {arg}"

      self.ejecutar_comando_en_tiempo_real(cmd)

    threading.Thread(target=tarea, daemon=True).start()

  def crear_pods_gui(self):
    param = self.entry_create.get().strip()
    if not param:
      messagebox.showerror(
          "Error", "Indica una cantidad o rango (ej: 3 o 1-5) para crear."
      )
      return

    def tarea():
      self.escribir_consola(f"\nDesplegando pods ({param})...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} create {param}")
      self.actualizar_lista_pods()

    threading.Thread(target=tarea, daemon=True).start()

  def gui_check_ports(self):
    arg = self.entry_red_arg.get().strip()
    def tarea():
      self.escribir_consola(f"\nEscaneando puertos (check-ports {arg})...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} check-ports {arg}")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_close_port(self):
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Especifica un ID o rango para aislar.")
      return
    def tarea():
      self.escribir_consola(f"\nAislando puertos para {arg}...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} close-port {arg}")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_open_port(self):
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Especifica un ID o rango para restaurar.")
      return
    def tarea():
      self.escribir_consola(f"\nRestaurando puertos para {arg}...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} open-port {arg}")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_test_network(self):
    arg = self.entry_test_net.get().strip()
    def tarea():
      self.escribir_consola(f"\nEjecutando test de red masivo ({arg})...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} test-network {arg}")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_test_connections(self):
    orig = self.entry_orig.get().strip()
    dest = self.entry_dest.get().strip()
    if not orig or not dest:
      messagebox.showerror("Error", "Introduce ID origen y destino.")
      return
    def tarea():
      self.escribir_consola(f"\nProbando tráfico entre Pod [{orig}] -> [{dest}]...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} test-connections {orig} {dest}")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_monitor_connect(self):
    def tarea():
      self.escribir_consola("\nIniciando monitor de conexiones TCP...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} monitor-connect")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_version(self):
    def tarea():
      self.escribir_consola("\nVerificando versión del script...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} version")
    threading.Thread(target=tarea, daemon=True).start()

  def gui_update_script(self):
    if messagebox.askyesno("Actualizar", "¿Deseas buscar e instalar actualizaciones para K3s Manager?"):
      def tarea():
        self.escribir_consola("\nBuscando actualizaciones...")
        self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} update")
      threading.Thread(target=tarea, daemon=True).start()


if __name__ == "__main__":
  root = tk.Tk()
  app = K3sManagerGUI(root)
  root.mainloop()
