import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import hashlib
from connect_db import execute_query

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class LoginScreen(tk.Frame):
    def __init__(self, parent, on_login_success, on_signup, on_forgot, **kwargs):
        super().__init__(parent, bg=GOLD, **kwargs)
        self.on_login_success = on_login_success
        self.on_signup        = on_signup
        self.on_forgot        = on_forgot
        self._fail_count      = 0
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Gold content area ─────────────────────────────────────────
        gold_section = tk.Frame(self, bg=GOLD)
        gold_section.grid(row=0, column=0, sticky="nsew")
        gold_section.columnconfigure(0, weight=1)
        gold_section.rowconfigure(0, weight=1)

        # White card centred
        card = tk.Frame(gold_section, bg=WHITE, bd=0,
                        highlightbackground="#cccccc", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center",
                   relwidth=0.82, relheight=0.85)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=1)
        card.rowconfigure(0, weight=1)

        # ── Left panel – library image + tagline ─────────────────────
        left = tk.Frame(card, bg=MAROON)
        left.grid(row=0, column=0, sticky="nsew")
        left.rowconfigure(0, weight=1)
        left.rowconfigure(1, weight=0)
        left.columnconfigure(0, weight=1)

        img_path = os.path.join(ASSETS_DIR, "reading-sunlit-library.jpg")
        if os.path.exists(img_path):
            try:
                lib_img = Image.open(img_path)
                lib_img = lib_img.resize((600, 480), Image.LANCZOS)
                self._lib_img = ImageTk.PhotoImage(lib_img)
                # Gold border frame (4px)
                gold_border = tk.Frame(left, bg=GOLD, padx=4, pady=4)
                gold_border.grid(row=0, column=0, sticky="nsew",
                                 padx=18, pady=(20, 10))
                gold_border.rowconfigure(0, weight=1)
                gold_border.columnconfigure(0, weight=1)
                # Dark inner shadow frame (2px)
                shadow = tk.Frame(gold_border, bg="#2a2a2a", padx=2, pady=2)
                shadow.grid(row=0, column=0, sticky="nsew")
                shadow.rowconfigure(0, weight=1)
                shadow.columnconfigure(0, weight=1)
                tk.Label(shadow, image=self._lib_img, bg=MAROON, bd=0
                         ).grid(row=0, column=0, sticky="nsew")
            except Exception:
                tk.Frame(left, bg=MAROON).grid(row=0, column=0, sticky="nsew")
        else:
            tk.Frame(left, bg=MAROON).grid(row=0, column=0, sticky="nsew")

        tk.Label(
            left,
            text="Empowering learning through\nknowledge and research.",
            fg=GOLD, bg=MAROON,
            font=("Poppins", 18, "bold"),
            justify="center", pady=14
        ).grid(row=1, column=0)

        # ── Right panel – login form ──────────────────────────────────
        right = tk.Frame(card, bg=WHITE)
        right.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        right.columnconfigure(0, weight=1)

        tk.Label(right, text="Welcome Back",
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 20, "bold")
                 ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        tk.Label(right, text="Sign in to your library account",
                 fg="#555555", bg=WHITE,
                 font=("Poppins", 12)
                 ).grid(row=1, column=0, sticky="w", pady=(0, 20))

        # Email
        tk.Label(right, text="Email",
                 fg=BLACK, bg=WHITE, font=("Poppins", 12, "bold")
                 ).grid(row=2, column=0, sticky="w")
        self.email_var = tk.StringVar()
        email_entry = ctk.CTkEntry(right, textvariable=self.email_var,
                                   height=42, corner_radius=8,
                                   border_color=MAROON, border_width=2,
                                   fg_color=WHITE, text_color=BLACK,
                                   font=("Poppins", 13))
        email_entry.grid(row=3, column=0, sticky="ew", pady=(2, 10))

        # Password with eye icon next to the field
        tk.Label(right, text="Password",
                 fg=BLACK, bg=WHITE, font=("Poppins", 12, "bold")
                 ).grid(row=4, column=0, sticky="w")

        self.pass_var = tk.StringVar()
        self._pw_shown = False
        self.pw_entry = ctk.CTkEntry(right, textvariable=self.pass_var,
                                      show="•", height=42, corner_radius=8,
                                      border_color=MAROON, border_width=2,
                                      fg_color=WHITE, text_color=BLACK,
                                      font=("Poppins", 13))
        self.pw_entry.grid(row=5, column=0, sticky="ew", pady=(2, 8))

        self.eye_lbl = tk.Label(right, text=chr(128065), cursor="hand2",
                                 bg=WHITE, fg=MAROON, font=("Poppins", 11))
        self.eye_lbl.bind("<Button-1>", self._toggle_password)

        def _place_pw_eye():
            self.pw_entry.update_idletasks()
            x = self.pw_entry.winfo_x() + self.pw_entry.winfo_width() - 30
            y = self.pw_entry.winfo_y() + (self.pw_entry.winfo_height() // 2) - 10
            self.eye_lbl.place(x=x, y=y)

        right.after(100, _place_pw_eye)

        # Remember me
        self.remember_var = tk.BooleanVar()
        ctk.CTkCheckBox(right, text="Remember Me",
                        variable=self.remember_var,
                        fg_color=MAROON, hover_color=GOLD,
                        text_color=BLACK, font=("Poppins", 12)
                        ).grid(row=6, column=0, sticky="w", pady=(0, 14))

        # Login button
        ctk.CTkButton(
            right, text="LOGIN",
            text_color=WHITE, fg_color=MAROON, hover_color="#8B1A24",
            font=("Poppins", 14, "bold"),
            corner_radius=8, height=42, cursor="hand2",
            command=self._do_login
        ).grid(row=7, column=0, sticky="ew", pady=(0, 12))

        # Links – centered below LOGIN button
        link_frame = tk.Frame(right, bg=WHITE)
        link_frame.grid(row=8, column=0, sticky="ew")

        signup_lbl = tk.Label(link_frame,
                              text="Don't have an account? Sign up",
                              fg=MAROON, bg=WHITE,
                              font=("Poppins", 12, "underline"),
                              cursor="hand2")
        signup_lbl.pack(anchor="center")
        signup_lbl.bind("<Button-1>", lambda e: self.on_signup())

        forgot_lbl = tk.Label(link_frame,
                              text="Forgot Password?",
                              fg="#CC0000", bg=WHITE,
                              font=("Poppins", 12, "underline", "bold"),
                              cursor="hand2")
        forgot_lbl.pack(anchor="center", pady=(6, 0))
        forgot_lbl.bind("<Button-1>", lambda e: self.on_forgot())

        email_entry.bind("<Return>",     lambda e: self._do_login())
        self.pw_entry.bind("<Return>",   lambda e: self._do_login())

    # ------------------------------------------------------------------
    def _toggle_password(self, event=None):
        self._pw_shown = not self._pw_shown
        self.pw_entry.configure(show="" if self._pw_shown else "•")
        self.eye_lbl.config(text=chr(128064) if self._pw_shown else chr(128065))

    # ------------------------------------------------------------------
    def _show_forgot_popup(self):
        """Smooth 60fps animated lock-unlock popup before navigating to forgot password."""
        popup = tk.Toplevel(self)
        popup.title("")
        popup.geometry("320x240")
        popup.resizable(False, False)
        popup.configure(bg=WHITE)
        popup.overrideredirect(True)
        popup.grab_set()

        # Start 30px above final position for slide-in
        self.update_idletasks()
        final_px = self.winfo_rootx() + (self.winfo_width()  - 320) // 2
        final_py = self.winfo_rooty() + (self.winfo_height() - 240) // 2
        start_py = final_py - 30
        popup.geometry(f"320x240+{final_px}+{start_py}")
        popup.attributes("-alpha", 0.0)

        # Card with maroon border
        outer = tk.Frame(popup, bg=MAROON, padx=2, pady=2)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=WHITE)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Forgot Password",
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 15, "bold")).pack(pady=(18, 2))
        tk.Label(inner, text="Taking you to password reset...",
                 fg="#666666", bg=WHITE,
                 font=("Poppins", 10)).pack()

        canvas = tk.Canvas(inner, width=320, height=120,
                            bg=WHITE, highlightthickness=0)
        canvas.pack(pady=4)

        cx, cy = 160, 80

        def _hex(r, g, b):
            return f"#{r:02X}{g:02X}{b:02X}"

        def _lerp_color(t):
            """Smooth transition: dark-red (#8B0000) → green (#00AA00)."""
            r = int(0x8B * (1 - t))
            g = int(0xAA * t)
            return _hex(r, g, 0)

        def draw_lock(lift=0, shackle_col=MAROON, unlocked=False):
            canvas.delete("all")
            # Lock body
            canvas.create_rectangle(cx - 30, cy - 8, cx + 30, cy + 36,
                                     fill=MAROON, outline="", width=0)
            # Keyhole
            canvas.create_oval(cx - 9, cy + 4, cx + 9, cy + 20,
                               fill=GOLD, outline="")
            canvas.create_rectangle(cx - 4, cy + 13, cx + 4, cy + 27,
                                    fill=GOLD, outline="")
            # Shackle
            if unlocked:
                canvas.create_arc(cx - 4, cy - 62 - lift,
                                   cx + 44, cy - 8 - lift // 2,
                                   start=0, extent=185,
                                   style="arc", outline=shackle_col, width=7)
            else:
                canvas.create_arc(cx - 24, cy - 56 - lift,
                                   cx + 24, cy - 6,
                                   start=0, extent=180,
                                   style="arc", outline=shackle_col, width=7)

        draw_lock()

        frame = [0]
        # Timeline (each tick = 16ms ≈ 60fps):
        # 0–20  : slide in + fade in
        # 20–30 : hold (closed, red shackle)
        # 30–36 : shake left/right
        # 36–62 : shackle lifts + color red→green
        # 62–80 : hold open (green)
        # 80    : close + navigate

        def tick():
            f = frame[0]
            frame[0] += 1

            # Phase 1: slide in + fade in (frames 0–20)
            if f <= 20:
                t = f / 20
                t_ease = 1 - (1 - t) ** 2
                popup.attributes("-alpha", min(t, 1.0))
                py = int(start_py + (final_py - start_py) * t_ease)
                popup.geometry(f"320x240+{final_px}+{py}")
                draw_lock(lift=0, shackle_col="#8B0000", unlocked=False)
                popup.after(16, tick)
                return

            # Phase 2: hold closed (frames 20–30)
            if f <= 30:
                draw_lock(lift=0, shackle_col="#8B0000", unlocked=False)
                popup.after(16, tick)
                return

            # Phase 3: shake (frames 30–36)
            if f <= 36:
                draw_lock(lift=0, shackle_col="#8B0000", unlocked=False)
                shake = 3 if f % 2 == 0 else -3
                canvas.move("all", shake, 0)
                popup.after(16, tick)
                return

            # Phase 4: lift + color transition (frames 36–62)
            if f <= 62:
                progress = (f - 36) / 26
                lift = int(progress * 52)
                col = _lerp_color(progress)
                unlocked = progress > 0.55
                draw_lock(lift=lift, shackle_col=col, unlocked=unlocked)
                popup.after(16, tick)
                return

            # Phase 5: hold open green (frames 62–80)
            if f <= 80:
                draw_lock(lift=52, shackle_col="#00AA00", unlocked=True)
                popup.after(16, tick)
                return

            # Done
            popup.destroy()
            self.on_forgot()

        popup.after(16, tick)

    # ------------------------------------------------------------------
    def _show_lockout_popup(self):
        popup = tk.Toplevel(self)
        popup.title("Having trouble logging in?")
        popup.resizable(False, False)
        popup.configure(bg=WHITE)
        popup.grab_set()

        self.update_idletasks()
        pw, ph = 380, 210
        px = self.winfo_rootx() + (self.winfo_width()  - pw) // 2
        py = self.winfo_rooty() + (self.winfo_height() - ph) // 2
        popup.geometry(f"{pw}x{ph}+{px}+{py}")

        outer = tk.Frame(popup, bg=MAROON, padx=2, pady=2)
        outer.pack(fill="both", expand=True)
        inner = tk.Frame(outer, bg=WHITE)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text="Having trouble logging in?",
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 14, "bold")).pack(pady=(18, 6))
        tk.Label(inner,
                 text="You have entered an incorrect password 3 times.\n"
                      "Would you like to reset your password or try again?",
                 fg="#555555", bg=WHITE,
                 font=("Poppins", 11),
                 justify="center").pack(padx=20)

        btn_row = tk.Frame(inner, bg=WHITE)
        btn_row.pack(pady=(16, 0))

        def go_forgot():
            popup.destroy()
            self.on_forgot()

        def try_again():
            self._fail_count = 0
            popup.destroy()

        tk.Button(btn_row, text="Forgot Password",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                  command=go_forgot).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Try Again",
                  fg=MAROON, bg=GOLD,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=8, cursor="hand2",
                  command=try_again).pack(side="left")

    # ------------------------------------------------------------------
    def _do_login(self):
        identifier = self.email_var.get().strip()
        password   = self.pass_var.get().strip()

        if not identifier or not password:
            messagebox.showwarning("Login", "Please enter your email/ID and password.")
            return

        hashed = _sha256(password)

        try:
            rows = execute_query(
                """SELECT user_id, first_name, last_name, role, account_status
                   FROM Users
                   WHERE (email = %s OR user_id = %s) AND password_hash = %s
                   LIMIT 1""",
                (identifier, identifier, hashed),
                fetch=True
            )
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return

        if not rows:
            self._fail_count += 1
            if self._fail_count % 3 == 0:
                self._show_lockout_popup()
            else:
                messagebox.showerror("Login Failed", "Invalid credentials. Please try again.")
            return

        user = rows[0]
        if user["account_status"] == "suspended":
            messagebox.showerror(
                "Account Suspended",
                "Your account has been suspended due to policy violations.\n"
                "Please contact the library administration."
            )
            return

        self._fail_count = 0
        user_info = {
            "user_id": user["user_id"],
            "name":    f"{user['first_name']} {user['last_name']}",
            "role":    user["role"],
        }
        self.on_login_success(user_info)
