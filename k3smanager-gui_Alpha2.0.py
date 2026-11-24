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


class RoundedButton(tk.Canvas):

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
    w, h = self.winfo_width(), self.winfo_height()
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
    w, h = self.winfo_width(), self.winfo_height()
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
    w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
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


class K3sManagerGUI:

  def __init__(self, root):
    self.root = root
    self.root.title("K3s Manager — Enterprise Dashboard")
    self.root.geometry("1120x880")
    self.root.minsize(980, 740)

    self.bg_window = "#0b0f19"
    self.bg_card = "#111827"
    self.accent = "#38bdf8"
    self.text_main = "#f8fafc"
    self.text_muted = "#94a3b8"

    self.root.configure(bg=self.bg_window)

    self.console_pods = None
    self.console_net = None
    self.console_audit = None
    self.current_working_dir = os.path.expanduser("~")

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

    nav_outer = tk.Frame(root, bg=self.bg_window)
    nav_outer.pack(fill=tk.X, padx=15, pady=(15, 5))
    nav_container = tk.Frame(nav_outer, bg=self.bg_window)
    nav_container.pack(anchor=tk.CENTER)

    self.tabs_frame = tk.Frame(root, bg=self.bg_window)
    self.tabs_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

    self.frames = {
        name: tk.Frame(self.tabs_frame, bg=self.bg_window)
        for name in ("pods", "net", "audit", "help")
    }

    self.tab_buttons = {}
    tabs_data = [
        ("pods", " 📦 Pod Management "),
        ("net", " 🌐 Network & Ports "),
        ("audit", " 🛡️ Audit & System "),
        ("help", " 📖 Help & Info "),
    ]

    for key, text in tabs_data:
      btn = RoundedButton(
          nav_container,
          text=text,
          command=lambda k=key: self.show_tab(k),
          width=175,
          height=38,
          radius=14,
          bg_color="#161e2e",
          hover_color="#1e293b",
          fg_color=self.text_muted,
          hover_fg=self.accent,
          bg_canvas=self.bg_window,
      )
      btn.pack(side=tk.LEFT, padx=4)
      self.tab_buttons[key] = btn

    btn_term = RoundedButton(
        nav_container,
        text=" 💻 External TERM ",
        command=self.open_external_terminal,
        width=175,
        height=38,
        radius=14,
        bg_color="#161e2e",
        hover_color="#1e293b",
        fg_color=self.text_muted,
        hover_fg=self.accent,
        bg_canvas=self.bg_window,
    )
    btn_term.pack(side=tk.LEFT, padx=4)

    self.create_tab_pods()
    self.create_tab_net()
    self.create_tab_audit()
    self.create_tab_help()

    self.show_tab("pods")

    if not os.path.exists(SCRIPT_BASH):
      self.write_console(
          self.console_pods,
          f"[WARNING] Script '{SCRIPT_BASH}' not found in current directory.",
      )
    else:
      self.write_console(
          self.console_pods,
          f"[OK] Environment verified. Script '{SCRIPT_BASH}' loaded"
          " successfully.",
      )

    self.update_pods_list()

  def get_configured_shell(self):
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

  def open_external_terminal(self):
    shell_cmd = self.get_configured_shell()
    terminals = [
        ("x-terminal-emulator", ["x-terminal-emulator", "-e", shell_cmd]),
        ("gnome-terminal", ["gnome-terminal", "--", shell_cmd]),
        ("konsole", ["konsole", "-e", shell_cmd]),
        ("xfce4-terminal", ["xfce4-terminal", "-e", shell_cmd]),
        ("alacritty", ["alacritty", "-e", shell_cmd]),
        ("kitty", ["kitty", shell_cmd]),
        ("tilix", ["tilix", "-e", shell_cmd]),
        ("xterm", ["xterm", "-e", shell_cmd]),
    ]
    for bin_name, cmd_args in terminals:
      if shutil.which(bin_name):
        subprocess.Popen(
            cmd_args,
            cwd=self.current_working_dir,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    messagebox.showerror(
        "Error", "No graphical terminal emulator found on this system."
    )

  def show_tab(self, name):
    for k, frame in self.frames.items():
      frame.pack_forget()
    for k, btn in self.tab_buttons.items():
      if k == name:
        btn.bg_color, btn.fg_color, btn.outline, btn.outline_width = (
            "#1e293b",
            self.accent,
            "#000000",
            2,
        )
      else:
        btn.bg_color, btn.fg_color, btn.outline, btn.outline_width = (
            "#161e2e",
            self.text_muted,
            "",
            1,
        )
      btn.draw()
    self.frames[name].pack(fill=tk.BOTH, expand=True)

  def write_console(self, console_target, text):
    if not console_target:
      return

    def _write():
      console_target.config(state=tk.NORMAL)
      console_target.insert(tk.END, text + "\n")
      console_target.see(tk.END)
      console_target.config(state=tk.DISABLED)

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

  def create_console(self, parent):
    console_card = RoundedLabelFrame(
        parent,
        text=" Output Terminal (Logs & Feedback) ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=12,
    )
    console_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    frame_interno = console_card.inner_frame

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
        highlightthickness=0,
    )
    consola.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    consola.config(state=tk.DISABLED)

    scrollbar = ttk.Scrollbar(
        top_consola_frame, orient=tk.VERTICAL, command=consola.yview
    )
    consola.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    btn_frame = tk.Frame(frame_interno, bg=self.bg_card)
    btn_frame.pack(fill=tk.X, pady=4)

    RoundedButton(
        btn_frame,
        text="🧹 Clear Console",
        command=lambda: (
            consola.config(state=tk.NORMAL),
            consola.delete("1.0", tk.END),
            consola.config(state=tk.DISABLED),
        ),
        width=150,
        height=28,
        radius=8,
        bg_color="#1e293b",
        hover_color="#ef4444",
        bg_canvas=self.bg_card,
    ).pack(side=tk.RIGHT, padx=2, pady=2)

    return consola

  def create_tab_pods(self):
    frame = self.frames["pods"]

    top_card = RoundedLabelFrame(
        frame,
        text=" Quick Pod Actions ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=12,
    )
    top_card.pack(fill=tk.X, padx=5, pady=5)
    top_inner = top_card.inner_frame

    btn_config = [
        ("🔄 Refresh", self.update_pods_list),
        ("👁️ View", self.show_selection),
        ("🧹 Clear Sel", self.clear_selection),
        ("📜 Logs", self.view_logs),
        ("🔍 Describe", self.describe_pod),
        ("🗑️ Delete", self.delete_pods_sel),
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
          bg_canvas=self.bg_card,
      )
      b.grid(row=0, column=idx, padx=4, pady=4, sticky="ew")
      top_inner.columnconfigure(idx, weight=1)

    list_card = RoundedLabelFrame(
        frame,
        text=" Active Pods List ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=12,
    )
    list_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    list_inner = list_card.inner_frame

    self.tree_pods = ttk.Treeview(
        list_inner,
        columns=("ID", "Namespace", "Name"),
        show="headings",
        height=8,
        selectmode="extended",
    )
    for col, width, anchor in [
        ("ID", 90, tk.CENTER),
        ("Namespace", 220, tk.W),
        ("Name", 520, tk.W),
    ]:
      self.tree_pods.heading(col, text=col)
      self.tree_pods.column(col, width=width, anchor=anchor)

    tree_scroll = ttk.Scrollbar(
        list_inner, orient=tk.VERTICAL, command=self.tree_pods.yview
    )
    self.tree_pods.configure(yscrollcommand=tree_scroll.set)
    self.tree_pods.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    action_card = RoundedLabelFrame(
        frame,
        text=" ID Operations & Deployment ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=12,
    )
    action_card.pack(fill=tk.X, padx=5, pady=5)
    action_inner = action_card.inner_frame

    tk.Label(
        action_inner,
        text="IDs / Range (e.g. 1,3 or 1-5):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9),
    ).grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
    self.entry_ids = RoundedEntry(
        action_inner, width=160, height=36, radius=10, bg_canvas=self.bg_card
    )
    self.entry_ids.grid(row=0, column=1, padx=8, pady=6)

    for idx, (txt, act) in enumerate(
        [("➕ Select", "add"), ("➖ Deselect", "remove"), ("🌐 IP", "ip")]
    ):
      RoundedButton(
          action_inner,
          text=txt,
          command=lambda a=act: self.exec_action_ids(a),
          bg_color="#1e293b",
          hover_color="#38bdf8",
          radius=10,
          height=34,
          width=100,
          bg_canvas=self.bg_card,
      ).grid(row=0, column=idx + 2, padx=4)

    tk.Label(
        action_inner,
        text="Create Pods (Qty/Range):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9),
    ).grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
    self.entry_create = RoundedEntry(
        action_inner, width=160, height=36, radius=10, bg_canvas=self.bg_card
    )
    self.entry_create.grid(row=1, column=1, padx=8, pady=6)

    RoundedButton(
        action_inner,
        text="🚀 Create Test Pods",
        command=self.create_pods_gui,
        bg_color="#0369a1",
        hover_color="#0ea5e9",
        radius=10,
        height=34,
        width=220,
        bg_canvas=self.bg_card,
    ).grid(row=1, column=2, columnspan=3, sticky="w", padx=4, pady=6)

    self.console_pods = self.create_console(frame)

  def create_tab_net(self):
    frame = self.frames["net"]

    control_card = RoundedLabelFrame(
        frame,
        text=" Port Control & NetworkPolicies ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=15,
    )
    control_card.pack(fill=tk.X, padx=5, pady=5)
    control_inner = control_card.inner_frame

    grid_red_1 = tk.Frame(control_inner, bg=self.bg_card)
    grid_red_1.pack(fill=tk.X, pady=6)

    tk.Label(
        grid_red_1,
        text="Pod ID or Range (e.g. 1 or 1-5):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=0, column=0, sticky=tk.W, padx=(5, 12), pady=6)
    self.entry_red_arg = RoundedEntry(
        grid_red_1, width=220, height=36, radius=10, bg_canvas=self.bg_card
    )
    self.entry_red_arg.grid(row=0, column=1, sticky=tk.W, padx=5, pady=6)

    btn_net_frame = tk.Frame(control_inner, bg=self.bg_card)
    btn_net_frame.pack(fill=tk.X, pady=(10, 5))

    for txt, cmd, bg, hov in [
        ("🔍 Scan Ports", self.gui_check_ports, "#1e293b", "#38bdf8"),
        ("🔒 Isolate / Close", self.gui_close_port, "#7f1d1d", "#991b1b"),
        ("🔓 Restore / Open", self.gui_open_port, "#065f46", "#047857"),
    ]:
      RoundedButton(
          btn_net_frame,
          text=txt,
          command=cmd,
          width=170,
          height=36,
          radius=12,
          bg_color=bg,
          hover_color=hov,
          bg_canvas=self.bg_card,
      ).pack(side=tk.LEFT, padx=8)

    test_card = RoundedLabelFrame(
        frame,
        text=" Advanced Connectivity Tests ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=15,
    )
    test_card.pack(fill=tk.X, padx=5, pady=10)
    test_inner = test_card.inner_frame

    grid_test_1 = tk.Frame(test_inner, bg=self.bg_card)
    grid_test_1.pack(fill=tk.X, pady=6)

    tk.Label(
        grid_test_1,
        text="Test-network range (e.g. 1-5 or -a):",
        bg=self.bg_card,
        fg=self.text_main,
        font=("Segoe UI", 9, "bold"),
    ).grid(row=0, column=0, sticky=tk.W, padx=(5, 12), pady=6)
    self.entry_test_net = RoundedEntry(
        grid_test_1, width=180, height=36, radius=10, bg_canvas=self.bg_card
    )
    self.entry_test_net.grid(row=0, column=1, sticky=tk.W, padx=5, pady=6)
    RoundedButton(
        grid_test_1,
        text="⚡ Run Test",
        command=self.gui_test_network,
        width=150,
        height=36,
        radius=12,
        bg_canvas=self.bg_card,
    ).grid(row=0, column=2, sticky=tk.W, padx=15, pady=6)

    tk.Frame(test_inner, bg="#1f2937", height=1).pack(
        fill=tk.X, padx=5, pady=12
    )

    grid_test_2 = tk.Frame(test_inner, bg=self.bg_card)
    grid_test_2.pack(fill=tk.X, pady=6)

    for idx, (lbl, attr, w) in enumerate(
        [("Source ID:", "entry_orig", 90), ("Target ID:", "entry_dest", 90)]
    ):
      tk.Label(
          grid_test_2,
          text=lbl,
          bg=self.bg_card,
          fg=self.text_main,
          font=("Segoe UI", 9),
      ).grid(row=0, column=idx * 2, sticky=tk.W, padx=(5, 6), pady=6)
      setattr(
          self,
          attr,
          RoundedEntry(
              grid_test_2,
              width=w,
              height=36,
              radius=10,
              bg_canvas=self.bg_card,
          ),
      )
      getattr(self, attr).grid(
          row=0, column=idx * 2 + 1, sticky=tk.W, padx=(0, 20), pady=6
      )

    RoundedButton(
        grid_test_2,
        text="⇄ Test Traffic",
        command=self.gui_test_connections,
        width=150,
        height=36,
        radius=12,
        bg_canvas=self.bg_card,
    ).grid(row=0, column=4, sticky=tk.W, padx=5, pady=6)

    self.console_net = self.create_console(frame)

  def create_tab_audit(self):
    frame = self.frames["audit"]

    audit_card = RoundedLabelFrame(
        frame,
        text=" Live Connection Audit ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=15,
    )
    audit_card.pack(fill=tk.X, padx=5, pady=5)
    audit_inner = audit_card.inner_frame

    tk.Label(
        audit_inner,
        text=(
            "Monitor external accesses to open ports. Events are saved in"
            " logs."
        ),
        bg=self.bg_card,
        fg=self.text_muted,
        font=("Segoe UI", 9),
    ).pack(anchor=tk.W, padx=5, pady=5)
    RoundedButton(
        audit_inner,
        text="📡 Start Monitoring",
        command=self.gui_monitor_connect,
        width=200,
        height=36,
        radius=12,
        bg_canvas=self.bg_card,
    ).pack(anchor=tk.W, padx=5, pady=10)

    sys_card = RoundedLabelFrame(
        frame,
        text=" Version Control & Updates ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=15,
    )
    sys_card.pack(fill=tk.X, padx=5, pady=10)
    sys_inner = sys_card.inner_frame

    btn_sys_frame = tk.Frame(sys_inner, bg=self.bg_card)
    btn_sys_frame.pack(fill=tk.X, padx=5, pady=5)

    for txt, cmd in [
        ("ℹ️ Check Version", self.gui_version),
        ("⬆️ Update Manager", self.gui_update_script),
    ]:
      RoundedButton(
          btn_sys_frame,
          text=txt,
          command=cmd,
          width=170,
          height=36,
          radius=12,
          bg_canvas=self.bg_card,
      ).pack(side=tk.LEFT, padx=10)

    self.console_audit = self.create_console(frame)

  def create_tab_help(self):
    frame = self.frames["help"]

    help_card = RoundedLabelFrame(
        frame,
        text=" System User Guide ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=10,
    )
    help_card.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    help_inner = help_card.inner_frame

    help_text = scrolledtext.ScrolledText(
        help_inner,
        wrap=tk.WORD,
        font=("Consolas", 10),
        bg="#070a12",
        fg="#38bdf8",
        insertbackground="white",
        borderwidth=0,
        highlightthickness=0,
    )
    help_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    help_text.insert(
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
    help_text.config(state=tk.DISABLED)

    creator_card = RoundedLabelFrame(
        frame,
        text=" Creators & Maintainers ",
        radius=16,
        bg_canvas=self.bg_window,
        padding=12,
    )
    creator_card.pack(fill=tk.X, padx=5, pady=(0, 5))
    creator_inner = creator_card.inner_frame

    tk.Label(
        creator_inner,
        text="K3s Manager has been developed and optimized by:",
        bg=self.bg_card,
        fg=self.text_muted,
        font=("Segoe UI", 9),
    ).pack(anchor=tk.W, padx=5, pady=(0, 8))

    btns_creators_frame = tk.Frame(creator_inner, bg=self.bg_card)
    btns_creators_frame.pack(fill=tk.X, padx=5, pady=2)

    for user in ["braispm9", "pwnddev"]:
      RoundedButton(
          btns_creators_frame,
          text=f"GitHub: {user}",
          command=lambda u=user: webbrowser.open(f"https://github.com/{u}"),
          width=200,
          height=36,
          radius=12,
          bg_color="#1e293b",
          hover_color="#38bdf8",
          bg_canvas=self.bg_card,
      ).pack(side=tk.LEFT, padx=10)

  def update_pods_list(self):
    def tarea():
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


if __name__ == "__main__":
  root = tk.Tk()
  app = K3sManagerGUI(root)
  root.mainloop()
