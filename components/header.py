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
    """
    Top header bar — 120px tall.
    Left  : Black logo box, 200px wide.
    Right : Maroon bar, fills remaining width.
              - 'UNIVERSITY LIBRARIES' 42px bold centered.
              - User ID / Name / Role labels at top-right (13px).
    No logout button — logout is handled by the sidebar.
    """

    def __init__(self, parent, user_info: dict, on_logout=None, **kwargs):
        super().__init__(parent, fg_color=BLACK, corner_radius=0,
                         height=HEADER_HEIGHT, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self.user_info = user_info
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        # ── Black logo block (200 px wide) ────────────────────────────
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
                tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                         font=("Poppins", 28, "bold")).pack(expand=True)
        else:
            tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                     font=("Poppins", 28, "bold")).pack(expand=True)

        # ── Maroon bar (fills remaining width) ────────────────────────
        maroon_frame = tk.Frame(self, bg=MAROON)
        maroon_frame.pack(side="left", fill="both", expand=True)
        maroon_frame.columnconfigure(0, weight=1)
        maroon_frame.rowconfigure(0, weight=0)   # user info row
        maroon_frame.rowconfigure(1, weight=1)   # title row

        # User info — top-right (row 0)
        uid  = self.user_info.get("user_id", "")
        name = self.user_info.get("name", "")
        role = self.user_info.get("role", "").capitalize()

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

        # Title — vertically centred (row 1)
        tk.Label(maroon_frame,
                 text="UNIVERSITY LIBRARIES",
                 fg=WHITE, bg=MAROON,
                 font=("Poppins", 42, "bold"),
                 anchor="w", padx=20
                 ).grid(row=1, column=0, sticky="nsew")
