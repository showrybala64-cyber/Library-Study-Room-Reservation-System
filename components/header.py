# Persistent header widget shown on every screen after login.
# Displays the CMU logo, the app title, and the current user's ID/name/role.
# Logout lives in the sidebar, not here, to keep the header read-only.

import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import os

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

HEADER_HEIGHT = 120
LOGO_WIDTH    = 200


class AppHeader(ctk.CTkFrame):
    # Two-zone layout: black logo block on the left, maroon title bar on the right.
    # user_info dict must contain user_id, name, and role keys.

    def __init__(self, parent, user_info: dict, on_logout=None, **kwargs):
        super().__init__(parent, fg_color=BLACK, corner_radius=0,
                         height=HEADER_HEIGHT, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.user_info = user_info
        self._build()

    def _build(self):
        # Fixed-width black block keeps the logo from stretching when the window resizes.
        logo_block = tk.Frame(self, bg=BLACK, width=LOGO_WIDTH,
                              height=HEADER_HEIGHT)
        logo_block.pack(side="left", fill="y")
        logo_block.pack_propagate(False)

        logo_path = os.path.join(ASSETS_DIR, "ActionC_maroongold.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img.thumbnail((LOGO_WIDTH - 10, HEADER_HEIGHT - 10), Image.LANCZOS)
                self._logo_img = ImageTk.PhotoImage(img)
                tk.Label(logo_block, image=self._logo_img,
                         bg=BLACK, bd=0).pack(expand=True)
            except Exception:
                # Fall back to text if the image file is corrupt or unreadable.
                tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                         font=("Poppins", 28, "bold")).pack(expand=True)
        else:
            tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                     font=("Poppins", 28, "bold")).pack(expand=True)

        maroon_frame = tk.Frame(self, bg=MAROON)
        maroon_frame.pack(side="left", fill="both", expand=True)
        maroon_frame.columnconfigure(0, weight=1)
        maroon_frame.rowconfigure(0, weight=0)
        maroon_frame.rowconfigure(1, weight=1)

        uid  = self.user_info.get("user_id", "")
        name = self.user_info.get("name", "")
        role = self.user_info.get("role", "").capitalize()

        # User identity sits top-right so it is visible but does not compete with the title.
        info_frame = tk.Frame(maroon_frame, bg=MAROON)
        info_frame.grid(row=0, column=0, sticky="ne", padx=16, pady=(6, 0))

        tk.Label(info_frame, text=f"ID: {uid}",
                 fg=GOLD, bg=MAROON, font=("Poppins", 13, "bold")
                 ).pack(side="left", padx=(0, 8))
        tk.Label(info_frame, text=name,
                 fg=WHITE, bg=MAROON, font=("Poppins", 13)
                 ).pack(side="left", padx=(0, 8))
        tk.Label(info_frame, text=f"[{role}]",
                 fg=GOLD, bg=MAROON, font=("Poppins", 13, "bold")
                 ).pack(side="left")

        tk.Label(maroon_frame,
                 text="UNIVERSITY LIBRARIES",
                 fg=WHITE, bg=MAROON,
                 font=("Poppins", 42, "bold"),
                 anchor="w", padx=20
                 ).grid(row=1, column=0, sticky="nsew")
