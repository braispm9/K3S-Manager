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
import sys
import json

# Comprobar si se ha pasado el argumento JSON por la línea de comandos de forma segura[cite: 3]
if len(sys.argv) > 1:
  json_string = sys.argv[1]
  try:
    data = json.loads(json_string)
    if not isinstance(data, (dict, list)):
      data = {}
  except (json.JSONDecodeError, TypeError):
    data = {}
else:
  data = {}
  print("[i] Abriendo K3s Manager GUI sin datos externos (modo independiente).")

# Archivo de script requerido[cite: 3]
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_BASH = os.path.join(BASE_DIR, "k3smanager.sh")


def limpiar_ansi(texto):
  ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
  return ansi_escape.sub("", texto)


class RoundedButton(tk.Canvas):
  """Botón personalizado con esquinas redondeadas y soporte para bordes activos[cite: 3]."""

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
        2,
        2,
        w - 2,
        h - 2,
        self.radius,
        fill=self.bg_color,
        outline=self.outline,
        width=self.outline_width,
    )
    self.create_text(
        w / 2, h / 2, text=self.text, fill=self.fg_color, font=self.font
    )

  def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

  def on_enter(self, event):
    self.delete("all")
    w, h = self.winfo_width(), self.winfo_height()
    self.create_rounded_rect(
        2,
        2,
        w - 2,
        h - 2,
        self.radius,
        fill=self.hover_color,
        outline=self.outline,
        width=self.outline_width,
    )
    self.create_text(
        w / 2, h / 2, text=self.text, fill=self.hover_fg, font=self.font
    )

  def on_leave(self, event):
    self.draw()

  def on_click(self, event):
    if self.command:
      self.command()


class RoundedEntry(tk.Canvas):
  """Campo de entrada de texto con bordes redondeados forzados y visibles[cite: 3]."""

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
        radius + 4,
        5,
        window=self.entry,
        width=width - (radius * 2) - 8,
        height=height - 10,
        anchor="nw",
    )

  def draw_bg(self, event=None):
    self.delete("bg")
    w = self.winfo_width()
    h = self.winfo_height()
    if w < 10:
      w = self.forced_width

    self.create_rounded_rect(
        1,
        1,
        w - 2,
        h - 2,
        self.radius,
        fill=self.bg_color,
        outline=self.outline,
        width=self.outline_width,
        tags="bg",
    )
    self.tag_lower("bg")

    self.coords(self.entry_window, self.radius + 4, 5)
    self.itemconfig(
        self.entry_window, width=w - (self.radius * 2) - 8, height=h - 10
    )

  def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

  def get(self):
    return self.entry.get()

  def delete(self, first, last=tk.END):
    self.entry.delete(first, last)

  def insert(self, index, string):
    self.entry.insert(index, string)


class RoundedLabelFrame(tk.Frame):
  """Contenedor responsivo con bordes redondeados dibujados en Canvas[cite: 3]."""

  def __init__(
      self,
      parent,
      text="",
      radius=16,
      bg_color="#111827",
      outline="#1f2937",
      fg_color="#38bdf8",
      bg_canvas="#0b0f19",
      padding=12,
  ):
    super().__init__(parent, bg=bg_canvas)
    self.radius = radius
    self.bg_color = bg_color
    self.outline = outline
    self.text = text
    self.fg_color = fg_color
    self.padding = padding

    self.canvas = tk.Canvas(
        self, bg=bg_canvas, highlightthickness=0, borderwidth=0
    )
    self.canvas.pack(fill=tk.BOTH, expand=True)

    self.inner_frame = tk.Frame(self.canvas, bg=bg_color)
    self.window_id = self.canvas.create_window(
        padding, 34, window=self.inner_frame, anchor="nw"
    )

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

    self.create_rounded_rect(
        self.canvas,
        2,
        2,
        w - 2,
        h - 2,
        self.radius,
        fill=self.bg_color,
        outline=self.outline,
        width=1,
        tags="bg_shape",
    )
    if self.text:
      self.canvas.delete("title_text")
      self.canvas.create_text(
          16,
          18,
          text=self.text,
          fill=self.fg_color,
          font=("Segoe UI", 10, "bold"),
          anchor="w",
          tags="title_text",
      )
    self.canvas.tag_lower("bg_shape")

  def create_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
    r = min(r, (x2 - x1) / 2, (y2 - y1) / 2)
    points = [
        x1 + r,
        y1,
        x2 - r,
        y1,
        x2,
        y1,
        x2,
        y1 + r,
        x2,
        y2 - r,
        x2,
        y2,
        x2 - r,
        y2,
        x1 + r,
        y2,
        x1,
        y2,
        x1,
        y2 - r,
        x1,
        y1 + r,
        x1,
        y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class K3sManagerModularGUI:

  def __init__(self, root):
    self.root = root
    self.root.title("K3s Manager — Modular Side Menu Dashboard")
    self.root.geometry("1280850")
    self.root.minsize(1000, 700)

    self.bg_window = "#0b0f19"
    self.bg_card = "#111827"
    self.accent = "#38bdf8"
    self.text_main = "#f8fafc"
    self.text_muted = "#94a3b8"

    self.root.configure(bg=self.bg_window)
    self.current_working_dir = os.path.expanduser("~")
    self.comandos_completado = data if isinstance(data, (list, dict)) else {}

    # Estilos globales ttk[cite: 3]
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
        rowheight=28,
        font=("Segoe UI", 9),
    )
    self.style.configure(
        "Treeview.Heading",
        background="#0b0f19",
        foreground=self.accent,
        font=("Segoe UI", 9, "bold"),
        relief="flat",
    )
    self.style.map(
        "Treeview",
        background=[("selected", "#1f2937")],
        foreground=[("selected", "#38bdf8")],
    )

    # Variables de referencias a consolas y elementos clave
    self.consola_pods = None
    self.consola_red = None
    self.consola_auditoria = None

    # Estructura principal: Menú lateral (Sidebar) + Área de trabajo modular
    self.create_layout()

    if not os.path.exists(SCRIPT_BASH):
      print(f"[ADVERTENCIA] No se encuentra '{SCRIPT_BASH}' en el directorio.")
    else:
      print(
          f"[OK] Entorno verificado. Script '{SCRIPT_BASH}' detectado"
          " correctamente."
      )

  def create_layout(self):
    # 1. Menú Lateral (Sidebar)
    sidebar = tk.Frame(self.root, bg=self.bg_card, width=240)
    sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=0, pady=0)
    sidebar.pack_propagate(False)

    tk.Label(
        sidebar,
        text="K3S MANAGER",
        bg=self.bg_card,
        fg=self.accent,
        font=("Segoe UI", 12, "bold"),
    ).pack(pady=(20, 15))

    tk.Label(
        sidebar,
        text="Módulos Dinámicos",
        bg=self.bg_card,
        fg=self.text_muted,
        font=("Segoe UI", 9),
    ).pack(anchor="w", padx=20, pady=(0, 5))

    # Botones del menú lateral para añadir módulos a voluntad
    modules_to_add = [
        ("📦 Gestión Pods", "pods"),
        ("🌐 Red y Puertos", "red"),
        ("🛡️ Auditoría", "auditoria"),
        ("📖 Ayuda & Info", "ayuda"),
    ]

    for text, key in modules_to_add:
      RoundedButton(
          sidebar,
          text=text,
          command=lambda k=key: self.add_module(k),
          width=200,
          height=38,
          radius=12,
          bg_color="#161e2e",
          hover_color="#1e293b",
          fg_color=self.text_main,
          hover_fg=self.accent,
          bg_canvas=self.bg_card,
      ).pack(pady=6, padx=20)

    tk.Label(
        sidebar,
        text="Utilidades",
        bg=self.bg_card,
        fg=self.text_muted,
        font=("Segoe UI", 9),
    ).pack(anchor="w", padx=20, pady=(15, 5))

    RoundedButton(
        sidebar,
        text="💻 Terminal Ext.",
        command=self.abrir_terminal_externa,
        width=200,
        height=38,
        radius=12,
        bg_color="#161e2e",
        hover_color="#1e293b",
        fg_color=self.text_muted,
        hover_fg=self.accent,
        bg_canvas=self.bg_card,
    ).pack(pady=6, padx=20)

    RoundedButton(
        sidebar,
        text="🧹 Limpiar Todo",
        command=self.clear_workspace,
        width=200,
        height=38,
        radius=12,
        bg_color="#7f1d1d",
        hover_color="#991b1b",
        fg_color=self.text_main,
        hover_fg="#ffffff",
        bg_canvas=self.bg_card,
    ).pack(pady=6, padx=20)

    # 2. Área de Trabajo Principal con PanedWindow (Permite redimensionar paneles libremente)
    self.workspace_pane = ttk.PanedWindow(self.root, orient=tk.VERTICAL)
    self.workspace_pane.pack(
        side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10
    )

    # Contenedores iniciales por defecto (Pods + Red)
    self.pane_top = ttk.Frame(self.workspace_pane)
    self.pane_bottom = ttk.Frame(self.workspace_pane)
    self.workspace_pane.add(self.pane_top, weight=3)
    self.workspace_pane.add(self.pane_bottom, weight=2)

    # Cargar módulos iniciales
    self.crear_modulo_pods(self.pane_top)
    self.crear_modulo_red(self.pane_bottom)

  def clear_workspace(self):
    for widget in self.pane_top.winfo_children():
      widget.destroy()
    for widget in self.pane_bottom.winfo_children():
      widget.destroy()
    messagebox.showinfo(
        "Workspace",
        "Espacio limpiado. Usa el menú lateral para añadir módulos.",
    )

  def add_module(self, key):
    # Añadir o alternar módulos en el panel superior o inferior según disponibilidad
    target_pane = self.pane_top if len(self.pane_top.winfo_children()) == 0 else self.pane_bottom
    for widget in target_pane.winfo_children():
      widget.destroy()

    if key == "pods":
      self.crear_modulo_pods(target_pane)
    elif key == "red":
      self.crear_modulo_red(target_pane)
    elif key == "auditoria":
      self.crear_modulo_auditoria(target_pane)
    elif key == "ayuda":
      self.crear_modulo_ayuda(target_pane)

  # ==========================================
  # CONSTRUCTOR DE CONSOLAS Y MÓDULOS
  # ==========================================
  def crear_consola(self, parent):
    console_card = RoundedLabelFrame(
        parent,
        text=" Terminal de Salida (Logs & Feedback)[cite: 3] ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=10,
    )
    console_card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    frame_interno = console_card.inner_frame
    frame_interno.pack(fill=tk.BOTH, expand=True)

    top_consola_frame = tk.Frame(frame_interno, bg=self.bg_card)
    top_consola_frame.pack(fill=tk.BOTH, expand=True)

    consola = scrolledtext.ScrolledText(
        top_consola_frame,
        wrap=tk.WORD,
        height=8,
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        font=("Consolas", 9),
        borderwidth=0,
        highlightthickness=0,
    )
    consola.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    consola.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(
        top_consola_frame, orient=tk.VERTICAL, command=consola.yview
    )
    consola.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    return consola

  def crear_modulo_pods(self, parent):
    frame = tk.Frame(parent, bg=self.bg_window)
    frame.pack(fill=tk.BOTH, expand=True)

    top_card = RoundedLabelFrame(
        frame, text=" Acciones Rápidas sobre Pods[cite: 3] ", radius=14, padding=10
    )
    top_card.pack(fill=tk.X, padx=2, pady=2)
    top_inner = top_card.inner_frame
    top_inner.pack(fill=tk.BOTH, expand=True)

    btn_config = [
        ("🔄 Actualizar", self.actualizar_lista_pods),
        ("👁️ Ver", self.mostrar_seleccion),
        ("🧹 Limpiar", self.limpiar_seleccion),
        ("📜 Logs", self.ver_logs),
        ("🔍 Describir", self.describir_pod),
        ("🗑️ Eliminar", self.eliminar_pods_sel),
    ]

    for idx, (text, cmd) in enumerate(btn_config):
      RoundedButton(
          top_inner,
          text=text,
          command=cmd,
          bg_color="#1e293b",
          hover_color="#0ea5e9",
          fg_color="#f1f5f9",
          hover_fg="#ffffff",
          radius=10,
          height=32,
          width=110,
          bg_canvas=self.bg_card,
      ).grid(row=0, column=idx, padx=3, pady=2, sticky="ew")
      top_inner.columnconfigure(idx, weight=1)

    list_card = RoundedLabelFrame(
        frame, text=" Listado de Pods Activos[cite: 3] ", radius=14, padding=10
    )
    list_card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    list_inner = list_card.inner_frame
    list_inner.pack(fill=tk.BOTH, expand=True)

    columns = ("ID", "Namespace", "Nombre")
    self.tree_pods = ttk.Treeview(
        list_inner,
        columns=columns,
        show="headings",
        height=6,
        selectmode="extended",
    )
    for col, w in [("ID", 70), ("Namespace", 180), ("Nombre", 350)]:
      self.tree_pods.heading(col, text=col)
      self.tree_pods.column(col, width=w, anchor=tk.W if col != "ID" else tk.CENTER)

    tree_scroll = ttk.Scrollbar(
        list_inner, orient=tk.VERTICAL, command=self.tree_pods.yview
    )
    self.tree_pods.configure(yscrollcommand=tree_scroll.set)
    self.tree_pods.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    action_card = RoundedLabelFrame(
        frame, text=" Operaciones ID & Despliegue[cite: 3] ", radius=14, padding=10
    )
    action_card.pack(fill=tk.X, padx=2, pady=2)
    action_inner = action_card.inner_frame
    action_inner.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        action_inner,
        text="IDs (ej: 1,3 o 1-5):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9),
    ).grid(row=0, column=0, sticky=tk.W, padx=4, pady=4)
    self.entry_ids = RoundedEntry(
        action_inner, width=140, height=32, radius=8, bg_canvas=self.bg_card
    )
    self.entry_ids.grid(row=0, column=1, padx=4, pady=4)

    RoundedButton(
        action_inner,
        text="➕ Añadir",
        command=lambda: self.ejecutar_accion_ids("add"),
        width=90,
        height=30,
        radius=8,
        bg_canvas=self.bg_card,
    ).grid(row=0, column=2, padx=2)
    RoundedButton(
        action_inner,
        text="➖ Quitar",
        command=lambda: self.ejecutar_accion_ids("remove"),
        width=90,
        height=30,
        radius=8,
        bg_canvas=self.bg_card,
    ).grid(row=0, column=3, padx=2)
    RoundedButton(
        action_inner,
        text="🌐 IP",
        command=lambda: self.ejecutar_accion_ids("ip"),
        width=90,
        height=30,
        radius=8,
        bg_canvas=self.bg_card,
    ).grid(row=0, column=4, padx=2)

    tk.Label(
        action_inner,
        text="Crear Pods (N/Rango):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9),
    ).grid(row=1, column=0, sticky=tk.W, padx=4, pady=4)
    self.entry_create = RoundedEntry(
        action_inner, width=140, height=32, radius=8, bg_canvas=self.bg_card
    )
    self.entry_create.grid(row=1, column=1, padx=4, pady=4)

    RoundedButton(
        action_inner,
        text="🚀 Crear Pods Prueba",
        command=self.crear_pods_gui,
        bg_color="#0369a1",
        hover_color="#0ea5e9",
        width=190,
        height=30,
        radius=8,
        bg_canvas=self.bg_card,
    ).grid(row=1, column=2, columnspan=3, sticky="w", padx=2, pady=4)

    self.consola_pods = self.crear_consola(frame)
    self.actualizar_lista_pods()

  def crear_modulo_red(self, parent):
    frame = tk.Frame(parent, bg=self.bg_window)
    frame.pack(fill=tk.BOTH, expand=True)

    control_card = RoundedLabelFrame(
        frame, text=" Control de Puertos & Red[cite: 3] ", radius=14, padding=12
    )
    control_card.pack(fill=tk.X, padx=2, pady=2)
    control_inner = control_card.inner_frame
    control_inner.pack(fill=tk.BOTH, expand=True)

    tk.Label(
        control_inner,
        text="ID de Pod o Rango (ej: 1-5):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9, "bold"),
    ).pack(anchor=tk.W, padx=5, pady=2)
    self.entry_red_arg = RoundedEntry(
        control_inner, width=200, height=34, radius=8, bg_canvas=self.bg_card
    )
    self.entry_red_arg.pack(anchor=tk.W, padx=5, pady=4)

    btn_net_frame = tk.Frame(control_inner, bg=self.bg_card)
    btn_net_frame.pack(fill=tk.X, pady=6)

    RoundedButton(
        btn_net_frame,
        text="🔍 Escanear",
        command=self.gui_check_ports,
        width=150,
        height=32,
        radius=8,
        bg_canvas=self.bg_card,
    ).pack(side=tk.LEFT, padx=4)
    RoundedButton(
        btn_net_frame,
        text="🔒 Aislar / Cerrar",
        command=self.gui_close_port,
        width=150,
        height=32,
        radius=8,
        bg_color="#7f1d1d",
        hover_color="#991b1b",
        bg_canvas=self.bg_card,
    ).pack(side=tk.LEFT, padx=4)
    RoundedButton(
        btn_net_frame,
        text="🔓 Restaurar / Abrir",
        command=self.gui_open_port,
        width=150,
        height=32,
        radius=8,
        bg_color="#065f46",
        hover_color="#047857",
        bg_canvas=self.bg_card,
    ).pack(side=tk.LEFT, padx=4)

    self.consola_red = self.crear_consola(frame)

  def crear_modulo_auditoria(self, parent):
    frame = tk.Frame(parent, bg=self.bg_window)
    frame.pack(fill=tk.BOTH, expand=True)

    audit_card = RoundedLabelFrame(
        frame, text=" Auditoría y Sistema[cite: 3] ", radius=14, padding=12
    )
    audit_card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    audit_inner = audit_card.inner_frame
    audit_inner.pack(fill=tk.BOTH, expand=True)

    RoundedButton(
        audit_inner,
        text="📡 Iniciar Monitorización TCP",
        command=self.gui_monitor_connect,
        width=220,
        height=34,
        radius=10,
        bg_canvas=self.bg_card,
    ).pack(anchor=tk.W, padx=5, pady=6)
    RoundedButton(
        audit_inner,
        text="ℹ️ Verificar Versión del Script",
        command=self.gui_version,
        width=220,
        height=34,
        radius=10,
        bg_canvas=self.bg_card,
    ).pack(anchor=tk.W, padx=5, pady=6)
    RoundedButton(
        audit_inner,
        text="⬆️ Actualizar K3s Manager",
        command=self.gui_update_script,
        width=220,
        height=34,
        radius=10,
        bg_color="#0369a1",
        hover_color="#0ea5e9",
        bg_canvas=self.bg_card,
    ).pack(anchor=tk.W, padx=5, pady=6)

    self.consola_auditoria = self.crear_consola(frame)

  def crear_modulo_ayuda(self, parent):
    frame = tk.Frame(parent, bg=self.bg_window)
    frame.pack(fill=tk.BOTH, expand=True)

    help_card = RoundedLabelFrame(
        frame, text=" Guía de Comandos ", radius=14, padding=10
    )
    help_card.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
    help_inner = help_card.inner_frame
    help_inner.pack(fill=tk.BOTH, expand=True)

    help_text = scrolledtext.ScrolledText(
        help_inner,
        wrap=tk.WORD,
        font=("Consolas", 9),
        bg="#070a12",
        fg="#38bdf8",
        borderwidth=0,
        highlightthickness=0,
    )
    help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    help_text.insert(
        tk.END,
        """====================================================================
K3S MANAGER - GUÍA RÁPIDA DE COMANDOS
====================================================================
• pods [ID|N-M|-A]        : Listar pods con ID estricto.
• select <IDs>             : Añadir pod(s) a selección activa.
• remove <IDs>             : Quitar pod(s) de selección.
• ip <ID | Nombre>         : Obtener IP interna de un pod.
• check-ports [ID | N-M]   : Escanear puertos abiertos.
• close-port <ID|N-M>      : Aislar pod con NetworkPolicy.
• open-port <ID|N-M>       : Restaurar red del pod.
• monitor-connect          : Monitorizar accesos TCP externos.
• update                   : Actualizar script bash desde GitHub.
""",
    )
    help_text.config(state=tk.DISABLED)

  # ==========================================
  # FUNCIONES DE CONTROL, LOGS Y BASH (IDÉNTICAS AL ORIGINAL)[cite: 3]
  # ==========================================
  def obtener_shell_configurada(self):
    shell_path = os.environ.get("SHELL", "")
    if not shell_path:
      try:
        shell_path = pwd.getpwuid(os.getuid()).pw_shell
      except Exception:
        shell_path = "/bin/bash"
    shell_name = os.path.basename(shell_path).lower()
    if "zsh" in shell_name and shutil.which("zsh"):
      return shutil.which("zsh") or "/bin/zsh"
    return shutil.which("bash") or "/bin/bash"

  def abrir_terminal_externa(self):
    shell_cmd = self.obtener_shell_configurada()
    terminales = [
        ("x-terminal-emulator", ["x-terminal-emulator", "-e", shell_cmd]),
        ("gnome-terminal", ["gnome-terminal", "--", shell_cmd]),
        ("konsole", ["konsole", "-e", shell_cmd]),
        ("alacritty", ["alacritty", "-e", shell_cmd]),
        ("xterm", ["xterm", "-e", shell_cmd]),
    ]
    for bin_name, cmd_args in terminales:
      if shutil.which(bin_name):
        subprocess.Popen(
            cmd_args,
            cwd=self.current_working_dir,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    messagebox.showerror("Error", "No se encontró terminal externa disponible.")

  def escribir_consola(self, consola_target, texto):
    if not consola_target or not consola_target.winfo_exists():
      return

    def _escribir():
      try:
        consola_target.config(state=tk.NORMAL)
        consola_target.insert(tk.END, texto + "\n")
        consola_target.see(tk.END)
        consola_target.config(state=tk.DISABLED)
      except Exception:
        pass

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
          self.escribir_consola(consola_target, limpiar_ansi(line.strip()))
      process.wait()
    except Exception as e:
      self.escribir_consola(
          consola_target, f"Error crítico al ejecutar el comando: {str(e)}"
      )

  def actualizar_lista_pods(self):
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
        if self.consola_pods:
          self.escribir_consola(
              self.consola_pods,
              "[AVISO] No se pudieron listar los pods o sin conexión K3s.",
          )
        return

      idx = 1
      for linea in salida.split("\n"):
        partes = linea.split()
        if len(partes) >= 2 and partes[0] != "kube-system":
          self.tree_pods.insert("", tk.END, values=(idx, partes[0], partes[1]))
          idx += 1
      if self.consola_pods:
        self.escribir_consola(
            self.consola_pods,
            "[OK] Tabla de pods sincronizada y actualizada correctamente.",
        )

    threading.Thread(target=tarea, daemon=True).start()

  def mostrar_seleccion(self):
    if not hasattr(self, "tree_pods") or not self.consola_pods:
      return
    selected_items = self.tree_pods.selection()
    if not selected_items:
      self.escribir_consola(
          self.consola_pods, "[INFO] No hay ningún pod seleccionado en la tabla."
      )
    else:
      self.escribir_consola(self.consola_pods, "\n--- Pods Seleccionados ---")
      for item in selected_items:
        val = self.tree_pods.item(item, "values")
        self.escribir_consola(
            self.consola_pods,
            f" • ID: {val[0]} | NS: {val[1]} | Pod: {val[2]}",
        )

  def limpiar_seleccion(self):
    if hasattr(self, "tree_pods") and self.consola_pods:
      self.tree_pods.selection_remove(self.tree_pods.selection())
      self.escribir_consola(self.consola_pods, "[OK] Selección de tabla limpiada.")

  def ver_logs(self):
    if not hasattr(self, "tree_pods") or not self.consola_pods:
      return
    selected = self.tree_pods.selection()
    if len(selected) != 1:
      messagebox.showerror(
          "Error", "Selecciona exactamente 1 pod de la tabla para ver sus logs."
      )
      return
    val = self.tree_pods.item(selected[0], "values")
    self.escribir_consola(
        self.consola_pods, f"\n--- Descargando Logs de: {val[2]} ({val[1]}) ---"
    )
    threading.Thread(
        target=lambda: self.ejecutar_comando_en_tiempo_real(
            f"kubectl logs {val[2]} -n {val[1]} --tail=50", self.consola_pods
        ),
        daemon=True,
    ).start()

  def describir_pod(self):
    if not hasattr(self, "tree_pods") or not self.consola_pods:
      return
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "Selecciona al menos un pod para describir.")
      return

    def tarea():
      for item in selected:
        val = self.tree_pods.item(item, "values")
        self.escribir_consola(
            self.consola_pods, f"\n=== DESCRIPCIÓN: {val[2]} ({val[1]}) ==="
        )
        self.ejecutar_comando_en_tiempo_real(
            f"kubectl describe pod {val[2]} -n {val[1]}", self.consola_pods
        )

    threading.Thread(target=tarea, daemon=True).start()

  def eliminar_pods_sel(self):
    if not hasattr(self, "tree_pods") or not self.consola_pods:
      return
    selected = self.tree_pods.selection()
    if not selected:
      messagebox.showerror("Error", "No hay pods seleccionados para eliminar.")
      return
    if messagebox.askyesno(
        "Confirmar Eliminación",
        f"¿Estás seguro de eliminar los {len(selected)} pod(s) seleccionados?",
    ):

      def tarea():
        for item in selected:
          val = self.tree_pods.item(item, "values")
          self.escribir_consola(
              self.consola_pods, f"Eliminando pod {val[2]} en {val[1]}..."
          )
          self.ejecutar_comando_en_tiempo_real(
              f"kubectl delete pod {val[2]} -n {val[1]}", self.consola_pods
          )
        self.actualizar_lista_pods()

      threading.Thread(target=tarea, daemon=True).start()

  def ejecutar_accion_ids(self, accion):
    if not hasattr(self, "entry_ids") or not self.consola_pods:
      return
    arg = self.entry_ids.get().strip()
    if not arg:
      messagebox.showerror("Error", "Introduce un ID o rango válido en el campo.")
      return

    def tarea():
      self.escribir_consola(
          self.consola_pods,
          f"\nEjecutando acción '{accion}' con argumento '{arg}'...",
      )
      cmd = (
          f"bash {SCRIPT_BASH} {accion} pod {arg}"
          if accion in ["add", "remove"]
          else f"bash {SCRIPT_BASH} ip {arg}"
      )
      self.ejecutar_comando_en_tiempo_real(cmd, self.consola_pods)

    threading.Thread(target=tarea, daemon=True).start()

  def crear_pods_gui(self):
    if not hasattr(self, "entry_create") or not self.consola_pods:
      return
    param = self.entry_create.get().strip()
    if not param:
      messagebox.showerror(
          "Error", "Indica una cantidad o rango (ej: 3 o 1-5) para crear."
      )
      return

    def tarea():
      self.escribir_consola(
          self.consola_pods, f"\nDesplegando pods ({param})..."
      )
      self.ejecutar_comando_en_tiempo_real(
          f"bash {SCRIPT_BASH} create {param}", self.consola_pods
      )
      self.actualizar_lista_pods()

    threading.Thread(target=tarea, daemon=True).start()

  def gui_check_ports(self):
    if not hasattr(self, "entry_red_arg") or not self.consola_red:
      return
    arg = self.entry_red_arg.get().strip()
    threading.Thread(
        target=lambda: self.ejecutar_comando_en_tiempo_real(
            f"bash {SCRIPT_BASH} check-ports {arg}", self.consola_red
        ),
        daemon=True,
    ).start()

  def gui_close_port(self):
    if not hasattr(self, "entry_red_arg") or not self.consola_red:
      return
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Especifica un ID o rango para aislar.")
      return
    threading.Thread(
        target=lambda: self.ejecutar_comando_en_tiempo_real(
            f"bash {SCRIPT_BASH} close-port {arg}", self.consola_red
        ),
        daemon=True,
    ).start()

  def gui_open_port(self):
    if not hasattr(self, "entry_red_arg") or not self.consola_red:
      return
    arg = self.entry_red_arg.get().strip()
    if not arg:
      messagebox.showerror("Error", "Especifica un ID o rango para restaurar.")
      return
    threading.Thread(
        target=lambda: self.ejecutar_comando_en_tiempo_real(
            f"bash {SCRIPT_BASH} open-port {arg}", self.consola_red
        ),
        daemon=True,
    ).start()

  def gui_monitor_connect(self):
    if not self.consola_auditoria:
      return
    threading.Thread(
        target=lambda: self.ejecutar_comando_en_tiempo_real(
            f"bash {SCRIPT_BASH} monitor-connect", self.consola_auditoria
        ),
        daemon=True,
    ).start()

  def gui_version(self):
    if not self.consola_auditoria:
      return
    threading.Thread(
        target=lambda: self.ejecutar_comando_en_tiempo_real(
            f"bash {SCRIPT_BASH} version", self.consola_auditoria
        ),
        daemon=True,
    ).start()

  def gui_update_script(self):
    if not self.consola_auditoria:
      return
    if messagebox.askyesno(
        "Actualizar", "¿Deseas buscar e instalar actualizaciones para K3s Manager?"
    ):
      threading.Thread(
          target=lambda: self.ejecutar_comando_en_tiempo_real(
              f"bash {SCRIPT_BASH} update", self.consola_auditoria
          ),
          daemon=True,
      ).start()


if __name__ == "__main__":
  root = tk.Tk()
  app = K3sManagerModularGUI(root)
  root.mainloop()
