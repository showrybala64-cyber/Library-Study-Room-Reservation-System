import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import os

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


class StudentDashboard(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info  = user_info
        self.navigator  = navigator   # callable(screen_name)
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        content = tk.Frame(self, bg=WHITE)
        content.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)

        tk.Label(content, text="Student Dashboard",
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 24, "bold")
                 ).grid(row=0, column=0, sticky="w")

        name = self.user_info.get("name", "Student")
        tk.Label(content,
                 text=f"Welcome Back, {name}!",
                 fg="#333333", bg=WHITE,
                 font=("Poppins", 16)
                 ).grid(row=1, column=0, sticky="w", pady=(4, 20))

        # Events banner
        banner_path = os.path.join(ASSETS_DIR, "events_banner.png")
        banner_frame = tk.Frame(content, bg="#EEEEEE")
        banner_frame.grid(row=2, column=0, sticky="nsew")

        if os.path.exists(banner_path):
            try:
                banner_img = Image.open(banner_path)
                # Resize to fill frame on render
                self._banner_img_raw = banner_img
                self._banner_label   = tk.Label(banner_frame, bg="#EEEEEE", bd=0)
                self._banner_label.pack(fill="both", expand=True)
                banner_frame.bind("<Configure>", self._resize_banner)
            except Exception:
                tk.Label(banner_frame, text="[Events Banner]",
                         bg=GOLD, fg=MAROON,
                         font=("Poppins", 16, "bold")
                         ).pack(fill="both", expand=True)
        else:
            tk.Label(banner_frame, text="[Events Banner]",
                     bg=GOLD, fg=MAROON,
                     font=("Poppins", 16, "bold")
                     ).pack(fill="both", expand=True)

    def _resize_banner(self, event):
        try:
            w, h = event.width, event.height
            if w < 2 or h < 2:
                return
            img = self._banner_img_raw.resize((w, h), Image.LANCZOS)
            self._banner_tk = ImageTk.PhotoImage(img)
            self._banner_label.config(image=self._banner_tk)
        except Exception:
            pass
