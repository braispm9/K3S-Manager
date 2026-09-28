#!/usr/bin/env python3

import os
import re
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import webbrowser  # <--- Importante para abrir los enlaces de GitHub

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
        x2 - r, y1, x2 -
