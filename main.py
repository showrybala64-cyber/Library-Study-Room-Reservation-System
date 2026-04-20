import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import webbrowser
from datetime import datetime
import credentials

# ── Screens ────────────────────────────────────────────────────────────
from screens.login_screen           import LoginScreen
from screens.signup_screen          import SignupScreen
from screens.forgot_password_screen import ForgotPasswordScreen
from screens.student_dashboard      import StudentDashboard
from screens.browse_rooms           import BrowseRooms
from screens.reservations           import Reservations
from screens.violations_student     import ViolationsStudent
from screens.profile_page           import ProfilePage
from screens.manager_dashboard      import ManagerDashboard
from screens.manage_rooms           import ManageRooms
from screens.manage_rules_violations import ManageRulesViolations
from screens.check_violations       import CheckViolations
from screens.reports                import Reports
from connect_db import execute_query

# ── Theme ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

MAROON     = "#5E1219"
GOLD       = "#EFBF04"
BLACK      = "#000000"
WHITE      = "#FFFFFF"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

MAPS_URL = "https://maps.google.com/?q=250+E+Preston+Mt+Pleasant+MI+48859"
ADDRESS  = "250 E Preston\nMt Pleasant, MI 48859"

# ── Nav definitions (label, screen_name) ──────────────────────────────
STUDENT_NAV = [
    ("Dashboard",    "student_dashboard"),
    ("Browse Rooms", "browse_rooms"),
    ("Reservations", "reservations"),
    ("Violations",   "violations_student"),
    ("Profile",      "profile"),
]
ADMIN_NAV = [
    ("Dashboard",                "manager_dashboard"),
    ("Violations",               "check_violations"),
    ("Generate Reports",         "reports"),
    ("Manage Rooms",             "manage_rooms"),
    ("Manage Rules","manage_rules_violations"),
]

# ── Screen routing table ───────────────────────────────────────────────
SCREEN_MAP = {
    "student_dashboard":       (StudentDashboard,       "Dashboard"),
    "browse_rooms":            (BrowseRooms,            "Browse Rooms"),
    "reservations":            (Reservations,           "Reservations"),
    "violations_student":      (ViolationsStudent,      "Violations"),
    "profile":                 (ProfilePage,            "Profile"),
    "manager_dashboard":       (ManagerDashboard,       "Dashboard"),
    "check_violations":        (CheckViolations,        "Violations"),
    "reports":                 (Reports,                "Generate Reports"),
    "manage_rooms":            (ManageRooms,            "Manage Rooms"),
    "manage_rules_violations": (ManageRulesViolations,  "Manage Rules"),
}


# ══════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("CMU University Library – Room Reservation System")
        self.minsize(1100, 750)
        self.state("zoomed")

        self.user_info      = {}
        self._current_frame = None
        self._auth_logo     = None   # keep ImageTk ref alive
        self._app_logo      = None   # keep app header logo ref alive
        self._auth_screen   = None   # keep current auth screen alive
        self._app_container = None   # rebuilt on each login
        self._app_content   = None
        self._app_screen    = None
        self.nav_buttons    = {}

        # StringVars for header user info — created once, updated on login
        self.user_id_var   = tk.StringVar()
        self.user_name_var = tk.StringVar()
        self.user_role_var = tk.StringVar()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._build_auth_container()
        self._show_login()

    # ------------------------------------------------------------------
    # Persistent auth container (built once, never destroyed)
    # ------------------------------------------------------------------
    def _build_auth_container(self):
        container = ctk.CTkFrame(self, fg_color=BLACK, corner_radius=0)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=0)   # header – fixed
        container.rowconfigure(1, weight=1)   # content – expands

        # ── Persistent header ─────────────────────────────────────────
        header = tk.Frame(container, bg=BLACK, height=120)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        logo_block = tk.Frame(header, bg=BLACK, width=200, height=120)
        logo_block.pack(side="left", fill="y")
        logo_block.pack_propagate(False)

        logo_path = os.path.join(ASSETS_DIR, "ActionC_maroongold.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img.thumbnail((190, 110), Image.LANCZOS)
                self._auth_logo = ImageTk.PhotoImage(img)
                tk.Label(logo_block, image=self._auth_logo, bg=BLACK, bd=0
                         ).pack(expand=True)
            except Exception:
                tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                         font=("Poppins", 28, "bold")).pack(expand=True)
        else:
            tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                     font=("Poppins", 28, "bold")).pack(expand=True)

        maroon_block = tk.Frame(header, bg=MAROON)
        maroon_block.pack(side="left", fill="both", expand=True)
        tk.Label(maroon_block, text="UNIVERSITY LIBRARIES",
                 fg=WHITE, bg=MAROON, font=("Poppins", 42, "bold"),
                 anchor="w", padx=20).pack(expand=True, fill="both")

        # ── Swappable content area ────────────────────────────────────
        content = tk.Frame(container, bg=GOLD)
        content.grid(row=1, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(0, weight=1)

        self._auth_container = container
        self._auth_content   = content

    def _clear_auth_content(self):
        for w in self._auth_content.winfo_children():
            w.destroy()

    # ------------------------------------------------------------------
    # Persistent app layout (header + sidebar + content_frame)
    # Built once per login; destroyed on logout.
    # ------------------------------------------------------------------
    def _build_app_layout(self, role: str):
        container = tk.Frame(self, bg=WHITE)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=0)   # header row
        container.rowconfigure(1, weight=1)   # body row

        # ── Persistent header (built inline, no AppHeader component) ──
        header = tk.Frame(container, bg=BLACK, height=120)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        logo_block = tk.Frame(header, bg=BLACK, width=200, height=120)
        logo_block.pack(side="left", fill="y")
        logo_block.pack_propagate(False)

        logo_path = os.path.join(ASSETS_DIR, "ActionC_maroongold.png")
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img.thumbnail((190, 110), Image.LANCZOS)
                self._app_logo = ImageTk.PhotoImage(img)
                tk.Label(logo_block, image=self._app_logo,
                         bg=BLACK, bd=0).pack(expand=True)
            except Exception:
                tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                         font=("Poppins", 28, "bold")).pack(expand=True)
        else:
            tk.Label(logo_block, text="CMU", fg=GOLD, bg=BLACK,
                     font=("Poppins", 28, "bold")).pack(expand=True)

        maroon_frame = tk.Frame(header, bg=MAROON)
        maroon_frame.pack(side="left", fill="both", expand=True)
        maroon_frame.columnconfigure(0, weight=1)
        maroon_frame.rowconfigure(0, weight=0)
        maroon_frame.rowconfigure(1, weight=1)

        info_frame = tk.Frame(maroon_frame, bg=MAROON)
        info_frame.grid(row=0, column=0, sticky="ne", padx=16, pady=(6, 0))
        tk.Label(info_frame, textvariable=self.user_id_var,
                 fg=GOLD, bg=MAROON, font=("Poppins", 13, "bold")
                 ).pack(side="left", padx=(0, 8))
        tk.Label(info_frame, textvariable=self.user_name_var,
                 fg=WHITE, bg=MAROON, font=("Poppins", 13)
                 ).pack(side="left", padx=(0, 8))
        tk.Label(info_frame, textvariable=self.user_role_var,
                 fg=GOLD, bg=MAROON, font=("Poppins", 13, "bold")
                 ).pack(side="left")

        tk.Label(maroon_frame, text="UNIVERSITY LIBRARIES",
                 fg=WHITE, bg=MAROON,
                 font=("Poppins", 42, "bold"),
                 anchor="w", padx=20
                 ).grid(row=1, column=0, sticky="nsew")

        # ── Body: sidebar + content ───────────────────────────────────
        body = tk.Frame(container, bg=WHITE)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Persistent gold sidebar ───────────────────────────────────
        sidebar = tk.Frame(body, bg=GOLD, width=200)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.pack_propagate(False)
        sidebar.grid_propagate(False)
        self.nav_buttons = {}
        self._build_sidebar(sidebar, role)

        # ── Swappable content frame ───────────────────────────────────
        content_frame = tk.Frame(body, bg=WHITE)
        content_frame.grid(row=0, column=1, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        self._app_container = container
        self._app_content   = content_frame

    def _build_sidebar(self, sidebar: tk.Frame, role: str):
        nav_items = STUDENT_NAV if role == "student" else ADMIN_NAV

        BTN_W, BTN_H, GAP = 180, 52, 12
        FONT    = ("Poppins", 14, "bold")
        RADIUS  = 8
        BW      = 3
        D_BDR   = "#3D0A0F"
        LABEL_MAP = {}

        nav_frame = tk.Frame(sidebar, bg=GOLD)
        nav_frame.pack(fill="x", padx=10, pady=(16, 0))

        for label, screen_name in nav_items:
            display = LABEL_MAP.get(label, label)
            btn = ctk.CTkButton(
                nav_frame,
                text=display,
                command=lambda s=screen_name: self._navigate(s),
                width=BTN_W,
                height=55 if "\n" in display else BTN_H,
                corner_radius=RADIUS,
                border_width=BW,
                border_color=D_BDR,
                fg_color=MAROON,
                text_color=WHITE,
                hover_color="#7A1820",
                font=FONT,
                anchor="w",
            )
            btn.pack(pady=(0, GAP))
            self.nav_buttons[label] = btn

        # Spacer pushes logout + address to bottom
        tk.Frame(sidebar, bg=GOLD).pack(fill="both", expand=True)

        # Logout button pinned to bottom
        bottom = tk.Frame(sidebar, bg=GOLD)
        bottom.pack(fill="x", padx=10, pady=(0, 8))
        ctk.CTkButton(
            bottom,
            text="Logout",
            command=lambda: self._navigate("logout"),
            width=BTN_W, height=BTN_H,
            corner_radius=RADIUS, border_width=BW,
            border_color=D_BDR,
            fg_color=MAROON, text_color=WHITE,
            hover_color="#7A1820",
            font=FONT, anchor="w",
        ).pack()

        # Address / directions block
        tk.Label(sidebar,
                 text="For directions to\nCharles V. Park Library\nclick below:",
                 fg=D_BDR, bg=GOLD,
                 font=("Poppins", 12, "bold"), justify="center"
                 ).pack(fill="x", padx=10, pady=(0, 2))

        addr_btn = tk.Button(
            sidebar, text=ADDRESS,
            command=lambda: webbrowser.open(MAPS_URL),
            fg=D_BDR, bg=GOLD,
            font=("Poppins", 13, "bold"),
            relief="flat", bd=0, cursor="hand2",
            wraplength=178, justify="center", pady=6,
        )
        addr_btn.pack(fill="x", padx=10, pady=(0, 10))
        addr_btn.bind("<Enter>", lambda e: addr_btn.config(fg=BLACK))
        addr_btn.bind("<Leave>", lambda e: addr_btn.config(fg=D_BDR))

    def _show_app_screen(self, screen_class, active_nav: str):
        """Clear content_frame and build screen_class inside it."""
        for w in self._app_content.winfo_children():
            w.destroy()
        self._app_screen = screen_class(self._app_content, self.user_info, self._navigate)
        self._app_screen.grid(row=0, column=0, sticky="nsew")
        self._update_active_nav(active_nav)
        self._app_content.update_idletasks()

    def _update_active_nav(self, active: str):
        """Highlight the active sidebar button; restore all others."""
        D_BDR = "#3D0A0F"
        for name, btn in self.nav_buttons.items():
            if name == active:
                btn.configure(fg_color=GOLD, text_color=MAROON,
                               border_color=MAROON, hover_color="#D4A800")
            else:
                btn.configure(fg_color=MAROON, text_color=WHITE,
                               border_color=D_BDR, hover_color="#7A1820")

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def _navigate(self, screen_name: str):
        if screen_name in ("logout", "logout_to_forgot"):
            self.user_info = {}
            if self._app_container is not None:
                try:
                    self._app_container.destroy()
                except Exception:
                    pass
                self._app_container = None
            self._app_content   = None
            self._app_screen    = None
            self.nav_buttons    = {}
            self._current_frame = None   # reset so _swap works cleanly
            if screen_name == "logout_to_forgot":
                self._show_forgot()
            else:
                self._show_login()
            return

        if screen_name in SCREEN_MAP:
            screen_class, active_nav = SCREEN_MAP[screen_name]
            self._show_app_screen(screen_class, active_nav)

    def _swap(self, new_frame):
        """Replace the currently visible top-level frame."""
        if self._current_frame and self._current_frame is not new_frame:
            if self._current_frame is self._auth_container:
                self._current_frame.grid_remove()   # preserve, don't destroy
            else:
                self._current_frame.destroy()
        self._current_frame = new_frame
        new_frame.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    # Auth screens – only content area changes; header stays static
    # ------------------------------------------------------------------
    def _show_login(self):
        self._swap(self._auth_container)
        self._clear_auth_content()
        self._auth_screen = LoginScreen(
            self._auth_content,
            on_login_success=self._on_login_success,
            on_signup=self._show_signup,
            on_forgot=self._show_forgot,
        )
        self._auth_screen.grid(row=0, column=0, sticky="nsew")
        self._auth_content.update_idletasks()

    def _show_signup(self):
        self._swap(self._auth_container)
        self._clear_auth_content()
        self._auth_screen = SignupScreen(self._auth_content, on_login=self._show_login)
        self._auth_screen.grid(row=0, column=0, sticky="nsew")
        self._auth_content.update_idletasks()

    def _show_forgot(self, **kwargs):
        self._swap(self._auth_container)
        self._clear_auth_content()
        self._auth_screen = ForgotPasswordScreen(
            self._auth_content, on_login=self._show_login, **kwargs
        )
        self._auth_screen.grid(row=0, column=0, sticky="nsew")
        self._auth_content.update_idletasks()

    # ------------------------------------------------------------------
    # Login success – build persistent app layout then show dashboard
    # ------------------------------------------------------------------
    def _on_login_success(self, user_info: dict):
        self.user_info = user_info
        # Update StringVars ONCE — labels use textvariable so they refresh instantly
        self.user_id_var.set(f"ID: {user_info.get('user_id', '')}")
        self.user_name_var.set(user_info.get("name", ""))
        self.user_role_var.set(f"[{user_info.get('role', '').capitalize()}]")
        role = user_info.get("role", "student")
        self._build_app_layout(role)
        self._swap(self._app_container)     # hides auth container, shows app
        if role == "admin":
            self._show_app_screen(ManagerDashboard, "Dashboard")
        else:
            self._show_app_screen(StudentDashboard, "Dashboard")
        self._start_noshow_checker()

    # ------------------------------------------------------------------
    # No-show checker – runs immediately after login, then every 5 min
    # ------------------------------------------------------------------
    def _start_noshow_checker(self):
        """Trigger first run immediately; after() keeps it on the main thread."""
        self._check_noshows()

    def _check_noshows(self):
        try:
            rows = execute_query(
                """SELECT r.reservation_id, r.user_id, r.room_id,
                          ru.points_no_show, ru.suspension_threshold_points,
                          ru.suspension_duration_days
                   FROM Reservations r
                   JOIN Rules ru ON ru.is_active = 1
                   LEFT JOIN Check_Ins c ON c.reservation_id = r.reservation_id
                   WHERE r.status = 'reserved'
                     AND r.reservation_date = CURDATE()
                     AND ADDTIME(r.start_time,
                             SEC_TO_TIME(ru.checkin_grace_minutes * 60)) < CURTIME()
                     AND c.checkin_id IS NULL""",
                fetch=True
            )
            for row in rows:
                res_id    = row["reservation_id"]
                user_id   = row["user_id"]
                pts       = row["points_no_show"] or 10
                threshold = row["suspension_threshold_points"] or 30
                susp_days = row["suspension_duration_days"] or 7

                execute_query(
                    "UPDATE Reservations SET status = 'no_show' "
                    "WHERE reservation_id = %s",
                    (res_id,)
                )
                execute_query(
                    """INSERT INTO Violations
                       (user_id, reservation_id, violation_type,
                        points_assessed, status, notes, created_at)
                       VALUES (%s, %s, 'no_show', %s, 'active',
                       'Automatic no-show: student did not check in within grace period',
                       NOW())""",
                    (user_id, res_id, pts)
                )
                execute_query(
                    "UPDATE Users SET penalty_points = penalty_points + %s "
                    "WHERE user_id = %s",
                    (pts, user_id)
                )
                result = execute_query(
                    "SELECT penalty_points FROM Users WHERE user_id = %s",
                    (user_id,), fetch=True
                )
                if result and result[0]["penalty_points"] >= threshold:
                    execute_query(
                        """UPDATE Users SET account_status = 'suspended',
                           suspended_until = DATE_ADD(NOW(), INTERVAL %s DAY)
                           WHERE user_id = %s""",
                        (susp_days, user_id)
                    )
        except Exception as e:
            print(f"[NoShow Checker] Error: {e}")
        finally:
            self.after(300_000, self._check_noshows)


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
