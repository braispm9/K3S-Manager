#!/usr/bin/env python3

import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

# Archivo de script requerido
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_BASH = os.path.join(BASE_DIR, "k3smanager.sh")


def limpiar_ansi(texto):
  ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
  return ansi_escape.sub("", texto)


class RoundedButton(tk.Canvas):
  """Botón personalizado con esquinas redondeadas y soporte para bordes activos."""

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
      outline="",
      outline_width=1,
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
    self.outline = outline
    self.outline_width = outline_width

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

    self.create_rounded_rect(
        2, 2, w - 2, h - 2, self.radius,
        fill=self.bg_color,
        outline=self.outline,
        width=self.outline_width
    )
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
    self.create_rounded_rect(
        2, 2, w - 2, h - 2, self.radius,
        fill=self.hover_color,
        outline=self.outline,
        width=self.outline_width
    )
    self.create_text(w / 2, h / 2, text=self.text, fill=self.hover_fg, font=self.font)

  def on_leave(self, event):
    self.draw()

  def on_click(self, event):
    if self.command:
      self.command()


class RoundedEntry(tk.Canvas):
  """Campo de entrada de texto con bordes redondeados forzados y visibles."""

  def __init__(
      self,
      parent,
      width=200,
      height=36,
      radius=10,
      bg_color="#0b0f19",
      fg_color="#f8fafc",
      insert_color="#38bdf8",
      bg_canvas="#111827",
      font=("Segoe UI", 10),
      outline="#38bdf8",
      outline_width=2,
  ):
    super().__init__(
        parent,
        width=width,
        height=height,
        bg=bg_canvas,
        highlightthickness=0,
        borderwidth=0,
    )
    self.radius = radius
    self.bg_color = bg_color
    self.outline = outline
    self.outline_width = outline_width
    self.forced_width = width

    self.bind("<Configure>", self.draw_bg)

    self.entry = tk.Entry(
        self,
        bg=bg_color,
        fg=fg_color,
        insertbackground=insert_color,
        font=font,
        relief=tk.FLAT,
        highlightthickness=0,
    )
    self.entry_window = self.create_window(
        radius + 4, 5, window=self.entry, width=width - (radius * 2) - 8, height=height - 10, anchor="nw"
    )

  def draw_bg(self, event=None):
    self.delete("bg")
    w = self.winfo_width()
    h = self.winfo_height()
    if w < 10:
      w = self.forced_width

    # Dibujar el contorno redondeado del input con su borde brillante
    self.create_rounded_rect(
        1, 1, w - 2, h - 2, self.radius,
        fill=self.bg_color,
        outline=self.outline,
        width=self.outline_width,
        tags="bg"
    )
    self.tag_lower("bg")

    self.coords(self.entry_window, self.radius + 4, 5)
    self.itemconfig(self.entry_window, width=w - (self.radius * 2) - 8, height=h - 10)

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

  def get(self):
    return self.entry.get()

  def delete(self, first, last=tk.END):
    self.entry.delete(first, last)

  def insert(self, index, string):
    self.entry.insert(index, string)


class RoundedLabelFrame(tk.Frame):
  """Contenedor responsivo con bordes redondeados dibujados en Canvas."""

  def __init__(self, parent, text="", radius=16, bg_color="#111827", outline="#1f2937", fg_color="#38bdf8", bg_canvas="#0b0f19", padding=12):
    super().__init__(parent, bg=bg_canvas)
    self.radius = radius
    self.bg_color = bg_color
    self.outline = outline
    self.text = text
    self.fg_color = fg_color
    self.padding = padding

    self.canvas = tk.Canvas(self, bg=bg_canvas, highlightthickness=0, borderwidth=0)
    self.canvas.pack(fill=tk.BOTH, expand=True)

    self.inner_frame = tk.Frame(self.canvas, bg=bg_color)
    self.window_id = self.canvas.create_window(padding, 34, window=self.inner_frame, anchor="nw")

    self.canvas.bind("<Configure>", self.draw)
    self.inner_frame.bind("<Configure>", self.on_inner_resize)

  def on_inner_resize(self, event):
    w = max(event.width, self.winfo_width() - (self.padding * 2))
    h = event.height
    self.canvas.itemconfig(self.window_id, width=w, height=h)

  def draw(self, event=None):
    self.canvas.delete("bg_shape")
    w = self.canvas.winfo_width()
    h = self.canvas.winfo_height()
    if w < 20 or h < 20:
      return

    self.create_rounded_rect(self.canvas, 2, 2, w - 2, h - 2, self.radius, fill=self.bg_color, outline=self.outline, width=1, tags="bg_shape")
    if self.text:
      self.canvas.delete("title_text")
      self.canvas.create_text(16, 18, text=self.text, fill=self.fg_color, font=("Segoe UI", 10, "bold"), anchor="w", tags="title_text")
    self.canvas.tag_lower("bg_shape")

  def create_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
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
    return canvas.create_polygon(points, smooth=True, **kwargs)


class K3sManagerGUI:

  def __init__(self, root):
    self.root = root
    self.root.title("K3s Manager — Ultra Smooth Enterprise Dashboard")
    self.root.geometry("1120x880")
    self.root.minsize(980, 740)

    self.bg_window = "#0b0f19"
    self.bg_card = "#111827"
    self.accent = "#38bdf8"
    self.text_main = "#f8fafc"
    self.text_muted = "#94a3b8"

    self.root.configure(bg=self.bg_window)

    self.consola_pods = None
    self.consola_red = None
    self.consola_auditoria = None

    self.style = ttk.Style()
    self.style.theme_use("clam")
    self.style.configure(
        ".",
        background=self.bg_card,
        foreground=self.text_main,
        font=("Segoe UI", 10)
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

    nav_outer = tk.Frame(root, bg=self.bg_window)
    nav_outer.pack(fill=tk.X, padx=15, pady=(15, 5))

    nav_container = tk.Frame(nav_outer, bg=self.bg_window)
    nav_container.pack(anchor=tk.CENTER)

    self.tabs_frame = tk.Frame(root, bg=self.bg_window)
    self.tabs_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

    self.frames = {}
    for name in ("pods", "red", "auditoria", "ayuda"):
      f = tk.Frame(self.tabs_frame, bg=self.bg_window)
      self.frames[name] = f

    self.tab_buttons = {}
    tabs_data = [
        ("pods", " 📦 Gestión de Pods "),
        ("red", " 🌐 Red y Puertos "),
        ("auditoria", " 🛡️ Auditoría y Sistema "),
        ("ayuda", " 📖 Ayuda "),
    ]

    for key, text in tabs_data:
      btn = RoundedButton(
          nav_container,
          text=text,
          command=lambda k=key: self.mostrar_pestana(k),
          width=180,
          height=38,
          radius=14,
          bg_color="#161e2e",
          hover_color="#1e293b",
          fg_color=self.text_muted,
          hover_fg=self.accent,
          bg_canvas=self.bg_window
      )
      btn.pack(side=tk.LEFT, padx=6)
      self.tab_buttons[key] = btn

    self.crear_pestana_pods()
    self.crear_pestana_red()
    self.crear_pestana_auditoria()
    self.crear_pestana_ayuda()

    self.mostrar_pestana("pods")

    if not os.path.exists(SCRIPT_BASH):
      self.escribir_consola(self.consola_pods, f"[ADVERTENCIA] No se encuentra '{SCRIPT_BASH}' en el directorio actual.")
    else:
      self.escribir_consola(self.consola_pods, f"[OK] Entorno verificado. Script '{SCRIPT_BASH}' detectado correctamente.")

    self.actualizar_lista_pods()

  def mostrar_pestana(self, name):
    for k, frame in self.frames.items():
      frame.pack_forget()
    for k, btn in self.tab_buttons.items():
      if k == name:
        btn.bg_color = "#1e293b"
        btn.fg_color = self.accent
        btn.outline = "#000000"
        btn.outline_width = 2
      else:
        btn.bg_color = "#161e2e"
        btn.fg_color = self.text_muted
        btn.outline = ""
        btn.outline_width = 1
      btn.draw()

    self.frames[name].pack(fill=tk.BOTH, expand=True)

  def escribir_consola(self, consola_target, texto):
    if not consola_target:
      return
    def _escribir():
      consola_target.config(state=tk.NORMAL)
      consola_target.insert(tk.END, texto + "\n")
      consola_target.see(tk.END)
      consola_target.config(state=tk.DISABLED)
    if threading.current_thread() is threading.main_thread():
      _escribir()
    else:
      self.root.after(0, _escribir)

  def ejecutar_comando_en_tiempo_real(self, cmd, consola_target):
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
          self.escribir_consola(consola_target, linea_limpia)
      process.wait()
    except Exception as e:
      self.escribir_consola(consola_target, f"Error crítico al ejecutar el comando: {str(e)}")

  def crear_consola(self, parent):
    console_card = RoundedLabelFrame(parent, text=" Terminal de Salida (Logs & Feedback) ", radius=16, bg_canvas=self.bg_window, padding=12)
    console_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    frame_interno = console_card.inner_frame
    frame_interno.pack(fill=tk.BOTH, expand=True)

    top_consola_frame = tk.Frame(frame_interno, bg=self.bg_card)
    top_consola_frame.pack(fill=tk.BOTH, expand=True)

    consola = scrolledtext.ScrolledText(
        top_consola_frame,
        wrap=tk.WORD,
        height=10,
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        font=("Consolas", 9),
        borderwidth=0,
        highlightthickness=0
    )
    consola.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    consola.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(top_consola_frame, orient=tk.VERTICAL, command=consola.yview)
    consola.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    btn_frame = tk.Frame(frame_interno, bg=self.bg_card)
    btn_frame.pack(fill=tk.X, pady=4)

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

    return consola

  def crear_pestana_pods(self):
    frame = self.frames["pods"]

    top_card = RoundedLabelFrame(frame, text=" Acciones Rápidas sobre Pods ", radius=16, bg_canvas=self.bg_window, padding=12)
    top_card.pack(fill=tk.X, padx=5, pady=5)
    top_inner = top_card.inner_frame
    top_inner.pack(fill=tk.BOTH, expand=True)

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
          top_inner,
          text=text,
          command=cmd,
          bg_color="#1e293b",
          hover_color="#0ea5e9",
          fg_color="#f1f5f9",
          hover_fg="#ffffff",
          radius=12,
          height=36,
          width=135,
          bg_canvas=self.bg_card
      )
      b.grid(row=0, column=idx, padx=4, pady=4, sticky="ew")
      top_inner.columnconfigure(idx, weight=1)

    list_card = RoundedLabelFrame(frame, text=" Listado de Pods Activos ", radius=16, bg_canvas=self.bg_window, padding=12)
    list_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    list_inner = list_card.inner_frame
    list_inner.pack(fill=tk.BOTH, expand=True)

    columns = ("ID", "Namespace", "Nombre")
    self.tree_pods = ttk.Treeview(list_inner, columns=columns, show="headings", height=8, selectmode="extended")
    self.tree_pods.heading("ID", text="ID Numérico")
    self.tree_pods.heading("Namespace", text="Namespace")
    self.tree_pods.heading("Nombre", text="Nombre del Pod")
    self.tree_pods.column("ID", width=90, anchor=tk.CENTER)
    self.tree_pods.column("Namespace", width=220, anchor=tk.W)
    self.tree_pods.column("Nombre", width=520, anchor=tk.W)

    tree_scroll = ttk.Scrollbar(list_inner, orient=tk.VERTICAL, command=self.tree_pods.yview)
    self.tree_pods.configure(yscrollcommand=tree_scroll.set)

    self.tree_pods.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    action_card = RoundedLabelFrame(frame, text=" Operaciones por ID y Despliegue ", radius=16, bg_canvas=self.bg_window, padding=12)
    action_card.pack(fill=tk.X, padx=5, pady=5)
    action_inner = action_card.inner_frame
    action_inner.pack(fill=tk.BOTH, expand=True)

    tk.Label(action_inner, text="IDs / Rango (ej: 1,3 o 1-5):", bg=self.bg_card, fg=self.text_main, font=("Segoe UI", 9)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
    self.entry_ids = RoundedEntry(action_inner, width=160, height=36, radius=10, bg_canvas=self.bg_card)
    self.entry_ids.grid(row=0, column=1, padx=8, pady=6)

    RoundedButton(action_inner, text="➕ Añadir", command=lambda: self.ejecutar_accion_ids("add"), bg_color="#1e293b", hover_color="#38bdf8", radius=10, height=34, width=100, bg_canvas=self.bg_card).grid(row=0, column=2, padx=4)
    RoundedButton(action_inner, text="➖ Quitar", command=lambda: self.ejecutar_accion_ids("remove"), bg_color="#1e293b", hover_color="#38bdf8", radius=10, height=34, width=100, bg_canvas=self.bg_card).grid(row=0, column=3, padx=4)
    RoundedButton(action_inner, text="🌐 IP", command=lambda: self.ejecutar_accion_ids("ip"), bg_color="#1e293b", hover_color="#38bdf8", radius=10, height=34, width=100, bg_canvas=self.bg_card).grid(row=0, column=4, padx=4)

    tk.Label(action_inner, text="Crear Pods (Cant/Rango):", bg=self.bg_card, fg=self.text_main, font=("Segoe UI", 9)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
    self.entry_create = RoundedEntry(action_inner, width=160, height=36, radius=10, bg_canvas=self.bg_card)
    self.entry_create.grid(row=1, column=1, padx=8, pady=6)

    RoundedButton(action_inner, text="🚀 Crear Pods Prueba", command=self.crear_pods_gui, bg_color="#0369a1", hover_color="#0ea5e9", radius=10, height=34, width=220, bg_canvas=self.bg_card).grid(row=1, column=2, columnspan=3, sticky="w", padx=4, pady=6)

    self.consola_pods = self.crear_consola(frame)

  def crear_pestana_red(self):
    frame = self.frames["red"]

    control_card = RoundedLabelFrame(frame, text=" Control de Puertos y NetworkPolicies ", radius=16, bg_canvas=self.bg_window, padding=15)
    control_card.pack(fill=tk.X, padx=5, pady=5)
    control_inner = control_card.inner_frame
    control_inner.pack(fill=tk.BOTH, expand=True)

    grid_red_1 = tk.Frame(control_inner, bg=self.bg_card)
    grid_red_1.pack(fill=tk.X, pady=6)

    tk.Label(grid_red_1, text="ID de Pod o Rango (ej: 1 o 1-5):", bg=self.bg_card, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(5, 12), pady=6)
    self.entry_red_arg = RoundedEntry(grid_red_1, width=220, height=36, radius=10, bg_canvas=self.bg_card)
    self.entry_red_arg.grid(row=0, column=1, sticky=tk.W, padx=5, pady=6)

    btn_net_frame = tk.Frame(control_inner, bg=self.bg_card)
    btn_net_frame.pack(fill=tk.X, pady=(10, 5))

    RoundedButton(btn_net_frame, text="🔍 Escanear Puertos", command=self.gui_check_ports, width=170, height=36, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=(0, 8))
    RoundedButton(btn_net_frame, text="🔒 Aislar / Cerrar", command=self.gui_close_port, width=170, height=36, radius=12, bg_color="#7f1d1d", hover_color="#991b1b", bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=8)
    RoundedButton(btn_net_frame, text="🔓 Restaurar / Abrir", command=self.gui_open_port, width=170, height=36, radius=12, bg_color="#065f46", hover_color="#047857", bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=8)

    test_card = RoundedLabelFrame(frame, text=" Pruebas de Conectividad Avanzadas ", radius=16, bg_canvas=self.bg_window, padding=15)
    test_card.pack(fill=tk.X, padx=5, pady=10)
    test_inner = test_card.inner_frame
    test_inner.pack(fill=tk.BOTH, expand=True)

    grid_test_1 = tk.Frame(test_inner, bg=self.bg_card)
    grid_test_1.pack(fill=tk.X, pady=6)

    tk.Label(grid_test_1, text="Rango test-network (ej: 1-5 o -a):", bg=self.bg_card, fg=self.text_main, font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, padx=(5, 12), pady=6)
    self.entry_test_net = RoundedEntry(grid_test_1, width=180, height=36, radius=10, bg_canvas=self.bg_card)
    self.entry_test_net.grid(row=0, column=1, sticky=tk.W, padx=5, pady=6)
    RoundedButton(grid_test_1, text="⚡ Ejecutar Test", command=self.gui_test_network, width=150, height=36, radius=12, bg_canvas=self.bg_card).grid(row=0, column=2, sticky=tk.W, padx=15, pady=6)

    sep_frame = tk.Frame(test_inner, bg="#1f2937", height=1)
    sep_frame.pack(fill=tk.X, padx=5, pady=12)

    grid_test_2 = tk.Frame(test_inner, bg=self.bg_card)
    grid_test_2.pack(fill=tk.X, pady=6)

    tk.Label(grid_test_2, text="ID Origen:", bg=self.bg_card, fg=self.text_main, font=("Segoe UI", 9)).grid(row=0, column=0, sticky=tk.W, padx=(5, 6), pady=6)
    self.entry_orig = RoundedEntry(grid_test_2, width=90, height=36, radius=10, bg_canvas=self.bg_card)
    self.entry_orig.grid(row=0, column=1, sticky=tk.W, padx=(0, 20), pady=6)

    tk.Label(grid_test_2, text="ID Destino:", bg=self.bg_card, fg=self.text_main, font=("Segoe UI", 9)).grid(row=0, column=2, sticky=tk.W, padx=(0, 6), pady=6)
    self.entry_dest = RoundedEntry(grid_test_2, width=90, height=36, radius=10, bg_canvas=self.bg_card)
    self.entry_dest.grid(row=0, column=3, sticky=tk.W, padx=(0, 15), pady=6)

    RoundedButton(grid_test_2, text="⇄ Probar Tráfico", command=self.gui_test_connections, width=150, height=36, radius=12, bg_canvas=self.bg_card).grid(row=0, column=4, sticky=tk.W, padx=5, pady=6)

    self.consola_red = self.crear_consola(frame)

  def crear_pestana_auditoria(self):
    frame = self.frames["auditoria"]

    audit_card = RoundedLabelFrame(frame, text=" Auditoría de Conexiones en Vivo ", radius=16, bg_canvas=self.bg_window, padding=15)
    audit_card.pack(fill=tk.X, padx=5, pady=5)
    audit_inner = audit_card.inner_frame
    audit_inner.pack(fill=tk.BOTH, expand=True)

    tk.Label(audit_inner, text="Monitoriza accesos externos a los puertos abiertos. Los eventos se registran en logs.", bg=self.bg_card, fg=self.text_muted, font=("Segoe UI", 9)).pack(anchor=tk.W, padx=5, pady=5)
    RoundedButton(audit_inner, text="📡 Iniciar Monitorización", command=self.gui_monitor_connect, width=200, height=36, radius=12, bg_canvas=self.bg_card).pack(anchor=tk.W, padx=5, pady=10)

    sys_card = RoundedLabelFrame(frame, text=" Control de Versión y Actualizaciones ", radius=16, bg_canvas=self.bg_window, padding=15)
    sys_card.pack(fill=tk.X, padx=5, pady=10)
    sys_inner = sys_card.inner_frame
    sys_inner.pack(fill=tk.BOTH, expand=True)

    btn_sys_frame = tk.Frame(sys_inner, bg=self.bg_card)
    btn_sys_frame.pack(fill=tk.X, padx=5, pady=5)

    RoundedButton(btn_sys_frame, text="ℹ️ Verificar Versión", command=self.gui_version, width=170, height=36, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=(0, 10))
    RoundedButton(btn_sys_frame, text="⬆️ Actualizar Manager", command=self.gui_update_script, width=170, height=36, radius=12, bg_canvas=self.bg_card).pack(side=tk.LEFT, padx=10)

    self.consola_auditoria = self.crear_consola(frame)

  def crear_pestana_ayuda(self):
    frame = self.frames["ayuda"]

    help_card = RoundedLabelFrame(frame, text=" Guía de Uso del Sistema ", radius=16, bg_canvas=self.bg_window, padding=10)
    help_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    help_inner = help_card.inner_frame
    help_inner.pack(fill=tk.BOTH, expand=True)

    help_text = scrolledtext.ScrolledText(
        help_inner,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        borderwidth=0,
        highlightthickness=0
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
        self.escribir_consola(self.consola_pods, "[AVISO] No se pudieron listar los pods o sin conexión K3s.")
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
      self.escribir_consola(self.consola_pods, "[OK] Tabla de pods sincronizada y actualizada correctamente.")
    threading.Thread(target=tarea, daemon=True).start()

  def mostrar_seleccion(self):
    selected_items = self.tree_pods.selection()
    if not selected_items:
      self.escribir_consola(self.consola_pods, "[INFO] No hay ningún pod seleccionado en la tabla.")
    else:
      self.escribir_consola(self.consola_pods, "\n--- Pods Seleccionados ---")
      for item in selected_items:
        val = self.tree_pods.item(item, "values")
        self.escribir_consola(self.consola_pods, f" • ID: {val[0]} | NS: {val[1]} | Pod: {val[2]}")

  def limpiar_seleccion(self):
    self.tree_pods.selection_remove(self.tree_pods.selection())
    self.escribir_consola(self.consola_pods, "[OK] Selección de tabla limpiada.")

  def ver_logs(self):
    selected = self.tree_pods.selection()
    if len(selected) != 1:
      messagebox.showerror("Error", "Selecciona exactamente 1 pod de la tabla para ver sus logs.")
      return
    val = self.tree_pods.item(selected[0], "values")
    pod_name, ns = val[2], val[1]
    self.escribir_consola(self.consola_pods, f"\n--- Descargando Logs de: {pod_name} ({ns}) ---")
    def tarea():
      self.ejecutar_comando_en_tiempo_real(f"kubectl logs {pod_name} -n {ns} --tail=50", self.consola_pods)
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
        self.escribir_consola(self.consola_pods, f"\n=== DESCRIPCIÓN: {pod_name} ({ns}) ===")
        self.ejecutar_comando_en_tiempo_real(f"kubectl describe pod {pod_name} -n {ns}", self.consola_pods)
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
          self.escribir_consola(self.consola_pods, f"Eliminando pod {pod_name} en {ns}...")
          self.ejecutar_comando_en_tiempo_real(f"kubectl delete pod {pod_name} -n {ns}", self.consola_pods)
        self.actualizar_lista_pods()
      threading.Thread(target=tarea, daemon=True).start()

  def ejecutar_accion_ids(self, accion):
    arg = self.entry_ids.get().strip()
    if not arg:
      messagebox.showerror("Error", "Introduce un ID o rango válido en el campo.")
      return

    def tarea():
      self.escribir_consola(self.consola_pods, f"\nEjecutando acción '{accion}' con argumento '{arg}'...")
      if accion in ["add", "remove"]:
        cmd = f"bash {SCRIPT_BASH} {accion} pod {arg}"
      elif accion == "ip":
        cmd = f"bash {SCRIPT_BASH} ip {arg}"
      else:
        cmd = f"bash {SCRIPT_BASH} {accion} {arg}"

      self.ejecutar_comando_en_tiempo_real(cmd, self.consola_pods)

    threading.Thread(target=tarea, daemon=True).start()

  def crear_pods_gui(self):
    param = self.entry_create.get().strip()
    if not param:
      messagebox.showerror("Error", "Indica una cantidad o rango (ej: 3 o 1-5) para crear.")
      return

    def tarea():
      self.escribir_consola(self.consola_pods, f"\nDesplegando pods ({param})...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} create {param}", self.consola_pods)
      self.actualizar_lista_pods()

    threading.Thread(target=tarea, daemon=True).start()

  def gui_check_ports(self):
    arg = self.entry_red_arg.get().strip()
    def tarea():
      self.escribir_consola(self.consola_red, f"\nEscaneando puertos (check-ports {arg})...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} check-ports {arg}", self.consola_red)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_close_port(self):
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Especifica un ID o rango para aislar.")
      return
    def tarea():
      self.escribir_consola(self.consola_red, f"\nAislando puertos para {arg}...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} close-port {arg}", self.consola_red)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_open_port(self):
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Especifica un ID o rango para restaurar.")
      return
    def tarea():
      self.escribir_consola(self.consola_red, f"\nRestaurando puertos para {arg}...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} open-port {arg}", self.consola_red)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_test_network(self):
    arg = self.entry_test_net.get().strip()
    def tarea():
      self.escribir_consola(self.consola_red, f"\nEjecutando test de red masivo ({arg})...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} test-network {arg}", self.consola_red)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_test_connections(self):
    orig = self.entry_orig.get().strip()
    dest = self.entry_dest.get().strip()
    if not orig or not dest:
      messagebox.showerror("Error", "Introduce ID origen y destino.")
      return
    def tarea():
      self.escribir_consola(self.consola_red, f"\nProbando tráfico entre Pod [{orig}] -> [{dest}]...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} test-connections {orig} {dest}", self.consola_red)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_monitor_connect(self):
    def tarea():
      self.escribir_consola(self.consola_auditoria, "\nIniciando monitor de conexiones TCP...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} monitor-connect", self.consola_auditoria)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_version(self):
    def tarea():
      self.escribir_consola(self.consola_auditoria, "\nVerificando versión del script...")
      self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} version", self.consola_auditoria)
    threading.Thread(target=tarea, daemon=True).start()

  def gui_update_script(self):
    if messagebox.askyesno("Actualizar", "¿Deseas buscar e instalar actualizaciones para K3s Manager?"):
      def tail():
        self.escribir_consola(self.consola_auditoria, "\nBuscando actualizaciones...")
        self.ejecutar_comando_en_tiempo_real(f"bash {SCRIPT_BASH} update", self.consola_auditoria)
      threading.Thread(target=tail, daemon=True).start()


if __name__ == "__main__":
  root = tk.Tk()
  app = K3sManagerGUI(root)
  root.mainloop()
