import tkinter as tk
import customtkinter as ctk
import webbrowser

GOLD        = "#EFBF04"
MAROON      = "#5E1219"
DARK_BORDER = "#3D0A0F"
HOVER_GOLD  = "#D4A800"
BLACK       = "#000000"
WHITE       = "#FFFFFF"

SIDEBAR_WIDTH  = 200
BTN_WIDTH      = 180
BTN_HEIGHT     = 52
BTN_SPACING    = 12
BTN_FONT       = ("Poppins", 14, "bold")
BTN_BORDER_W   = 3
BTN_RADIUS     = 8

ADDRESS  = "250 E Preston\nMt Pleasant, MI 48859"
MAPS_URL = "https://maps.google.com/?q=250+E+Preston+Mt+Pleasant+MI+48859"


class AppSidebar(ctk.CTkFrame):
    """
    Gold left sidebar — 200px wide, full screen height.
    nav_items : list of (label, command) tuples; last item must be 'Logout'.
    active    : label of currently active screen (highlighted in maroon).
    """

    def __init__(self, parent, nav_items: list, active: str = "", **kwargs):
        super().__init__(parent, fg_color=GOLD, corner_radius=0,
                         width=SIDEBAR_WIDTH, **kwargs)
        self.pack_propagate(False)
        self.grid_propagate(False)
        self._build(nav_items, active)

    # ------------------------------------------------------------------
    def _build(self, nav_items, active):
        # Separate logout from the rest
        logout_item = None
        main_items  = []
        for label, cmd in nav_items:
            if label.strip().lower() == "logout":
                logout_item = (label, cmd)
            else:
                main_items.append((label, cmd))

        # ── Top nav buttons ───────────────────────────────────────────
        nav_frame = tk.Frame(self, bg=GOLD)
        nav_frame.pack(fill="x", padx=10, pady=(16, 0))

        LABEL_MAP = {}
        for label, cmd in main_items:
            is_active = label.strip().lower() == active.strip().lower()
            display = LABEL_MAP.get(label, label)
            long_label = "\n" in display
            ctk.CTkButton(
                nav_frame,
                text=display,
                command=cmd,
                width=BTN_WIDTH,
                height=55 if long_label else BTN_HEIGHT,
                corner_radius=BTN_RADIUS,
                border_width=BTN_BORDER_W,
                border_color=MAROON if is_active else DARK_BORDER,
                fg_color=GOLD if is_active else MAROON,
                text_color=MAROON if is_active else WHITE,
                hover_color=HOVER_GOLD if is_active else "#7A1820",
                font=BTN_FONT,
                anchor="w",
            ).pack(pady=(0, BTN_SPACING))

        # ── Spacer ────────────────────────────────────────────────────
        tk.Frame(self, bg=GOLD).pack(fill="both", expand=True)

        # ── Logout button at bottom ───────────────────────────────────
        if logout_item:
            bottom_frame = tk.Frame(self, bg=GOLD)
            bottom_frame.pack(fill="x", padx=10, pady=(0, 8))
            ctk.CTkButton(
                bottom_frame,
                text=logout_item[0],
                command=logout_item[1],
                width=BTN_WIDTH,
                height=BTN_HEIGHT,
                corner_radius=BTN_RADIUS,
                border_width=BTN_BORDER_W,
                border_color=DARK_BORDER,
                fg_color=MAROON,
                text_color=WHITE,
                hover_color="#7A1820",
                font=BTN_FONT,
                anchor="w",
            ).pack()

        # ── Address at very bottom ────────────────────────────────────
        tk.Label(self,
                 text="For directions to\nCharles V. Park Library\nclick below:",
                 fg=DARK_BORDER, bg=GOLD,
                 font=("Poppins", 12, "bold"),
                 justify="center"
                 ).pack(fill="x", padx=10, pady=(0, 2))

        addr_btn = tk.Button(
            self,
            text=ADDRESS,
            command=lambda: webbrowser.open(MAPS_URL),
            fg=DARK_BORDER, bg=GOLD,
            font=("Poppins", 13, "bold"),
            relief="flat", bd=0,
            cursor="hand2",
            wraplength=178,
            justify="center",
            pady=6,
        )
        addr_btn.pack(fill="x", padx=10, pady=(0, 10))
        addr_btn.bind("<Enter>", lambda e: addr_btn.config(fg=BLACK))
        addr_btn.bind("<Leave>", lambda e: addr_btn.config(fg=DARK_BORDER))
