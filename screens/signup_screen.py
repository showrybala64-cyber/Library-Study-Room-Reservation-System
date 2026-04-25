# New account registration screen for students.
# Restricted to @cmich.edu addresses; enforces password complexity before inserting the row.
# On success, passes the registered email back to login so the field is pre-filled.

import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import re
import hashlib
from connect_db import execute_query

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


# SHA-256 must match the hashing used in login and password reset.
def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class SignupScreen(tk.Frame):
    def __init__(self, parent, on_login, **kwargs):
        super().__init__(parent, bg=GOLD, **kwargs)
        self.on_login = on_login
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        logo_path = os.path.join(ASSETS_DIR, "ActionC_maroongold.png")

        # ── Body (gold background) ────────────────────────────────────
        body = tk.Frame(self, bg=GOLD)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        # White card centered (wider for split layout)
        card = tk.Frame(body, bg=WHITE,
                        highlightbackground="#cccccc", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center",
                   relwidth=0.80, relheight=0.88)
        card.columnconfigure(0, weight=2)   # 40% left panel
        card.columnconfigure(1, weight=3)   # 60% right panel
        card.rowconfigure(0, weight=1)

        # ── Left panel — maroon branding (40%) ───────────────────────
        left = tk.Frame(card, bg=MAROON)
        left.grid(row=0, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)

        # CMU Logo
        if os.path.exists(logo_path):
            try:
                left_logo = Image.open(logo_path)
                left_logo.thumbnail((130, 75), Image.LANCZOS)
                self._left_logo = ImageTk.PhotoImage(left_logo)
                tk.Label(left, image=self._left_logo, bg=MAROON, bd=0
                         ).pack(pady=(30, 0))
            except Exception:
                tk.Label(left, text="CMU", fg=GOLD, bg=MAROON,
                         font=("Poppins", 26, "bold")).pack(pady=(30, 0))
        else:
            tk.Label(left, text="CMU", fg=GOLD, bg=MAROON,
                     font=("Poppins", 26, "bold")).pack(pady=(30, 0))

        # Thin gold line under logo
        tk.Frame(left, bg=GOLD, height=3).pack(fill="x", padx=40, pady=(10, 0))

        # Main headline
        tk.Label(left, text="Join University\nLibraries",
                 fg=WHITE, bg=MAROON,
                 font=("Poppins", 22, "bold"),
                 justify="center"
                 ).pack(pady=(22, 6), padx=20)

        # Subtitle
        tk.Label(left, text="Access study rooms,\nresources and more",
                 fg=GOLD, bg=MAROON,
                 font=("Poppins", 12),
                 justify="center"
                 ).pack(padx=20, pady=(0, 26))

        # Bullet points
        for icon, text in [("▶", "Reserve study rooms instantly"),
                            ("▶", "Track your reservations"),
                            ("▶", "Manage your profile")]:
            row_f = tk.Frame(left, bg=MAROON)
            row_f.pack(fill="x", padx=26, pady=5)
            tk.Label(row_f, text=icon, fg=GOLD, bg=MAROON,
                     font=("Arial", 10, "bold")).pack(side="left", padx=(0, 10))
            tk.Label(row_f, text=text, fg=WHITE, bg=MAROON,
                     font=("Poppins", 11)).pack(side="left", anchor="w")

        # Inspiring quote
        tk.Frame(left, bg=GOLD, height=1).pack(fill="x", padx=30, pady=(20, 12))
        tk.Label(left,
                 text='"The more that you read, the more things you will know.\n'
                      'The more that you learn, the more places you\'ll go."',
                 fg=GOLD, bg=MAROON,
                 font=("Poppins", 12, "bold italic"),
                 justify="center",
                 wraplength=185
                 ).pack(padx=14)
        tk.Label(left, text="— Dr. Seuss",
                 fg=GOLD, bg=MAROON,
                 font=("Poppins", 11, "italic"),
                 justify="center"
                 ).pack(pady=(6, 0))

        # Spacer + gold decorative bar at very bottom
        tk.Frame(left, bg=MAROON).pack(expand=True, fill="both")
        tk.Frame(left, bg=GOLD, height=6).pack(fill="x", side="bottom")

        # ── Right panel — scrollable form (60%) ───────────────────────
        right_container = tk.Frame(card, bg=WHITE)
        right_container.grid(row=0, column=1, sticky="nsew")
        right_container.columnconfigure(0, weight=1)
        right_container.rowconfigure(0, weight=1)

        r_canvas = tk.Canvas(right_container, bg=WHITE, highlightthickness=0)
        r_vsb = ttk.Scrollbar(right_container, orient="vertical", command=r_canvas.yview)
        r_canvas.configure(yscrollcommand=r_vsb.set)
        r_canvas.grid(row=0, column=0, sticky="nsew")
        r_vsb.grid(row=0, column=1, sticky="ns")

        right = tk.Frame(r_canvas, bg=WHITE)
        right.columnconfigure(0, weight=1)
        right.columnconfigure(1, weight=1)
        _r_win = r_canvas.create_window((20, 16), window=right, anchor="nw")

        right.bind("<Configure>", lambda e: r_canvas.configure(scrollregion=r_canvas.bbox("all")))
        r_canvas.bind("<Configure>", lambda e: r_canvas.itemconfig(_r_win, width=max(1, e.width - 40)))

        def _r_wheel(e):
            r_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        r_canvas.bind("<MouseWheel>", _r_wheel)
        right.bind("<MouseWheel>", _r_wheel)

        # Title
        tk.Label(right, text="Create an Account",
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 20, "bold")
                 ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 2))
        tk.Label(right, text="Fill in the details below to get started.",
                 fg="#666666", bg=WHITE, font=("Poppins", 11)
                 ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        # ── 2-column field layout ─────────────────────────────────────
        # Col 0: First Name, Last Name, Phone
        # Col 1: Email, Password, Confirm Password
        self.vars = {}

        left_fields  = [("First Name *",  "first_name",   False),
                         ("Last Name *",   "last_name",    False),
                         ("Phone Number",  "phone_number", False)]
        right_fields = [("Email Address *",    "email",            False),
                         ("Password *",         "password",         True),
                         ("Confirm Password *", "confirm_password", True)]

        for r, (lbl, key, is_pw) in enumerate(left_fields):
            self._field(right, r, 0, lbl, key, is_pw)
        for r, (lbl, key, is_pw) in enumerate(right_fields):
            self._field(right, r, 1, lbl, key, is_pw)

        # ── Live password checker (right column, below all fields) ──────
        self._rule_labels = {}
        checker_frame = tk.Frame(right, bg=WHITE)
        checker_frame.grid(row=8, column=1, sticky="nw", padx=(8, 0), pady=(0, 2))
        _RULE_DEFS = [
            ("length",  "At least 8 characters"),
            ("upper",   "At least 1 uppercase letter (A-Z)"),
            ("lower",   "At least 1 lowercase letter (a-z)"),
            ("digit",   "At least 1 number (0-9)"),
            ("special", "At least 1 special character (!@#$%^&*)"),
        ]
        for rkey, rtext in _RULE_DEFS:
            lbl = tk.Label(checker_frame, text=f"[  ] {rtext}",
                           fg="#999999", bg=WHITE, font=("Poppins", 10), anchor="w")
            lbl.pack(anchor="w")
            self._rule_labels[rkey] = lbl

        # Match indicator
        self._match_lbl = tk.Label(right, text="", bg=WHITE, font=("Poppins", 10))
        self._match_lbl.grid(row=9, column=1, sticky="w", padx=(8, 0))

        # Update the checklist on every keystroke so feedback is immediate.
        self.vars["password"].trace_add("write", lambda *_: self._update_pw_checker())
        self.vars["confirm_password"].trace_add("write", lambda *_: self._update_pw_checker())

        # Divider + buttons (pushed down to accommodate checker rows)
        btn_base = 10
        tk.Frame(right, bg="#E0E0E0", height=1
                 ).grid(row=btn_base, column=0, columnspan=2,
                        sticky="ew", pady=(10, 0))

        # SIGN UP button — full width, ~45px tall
        ctk.CTkButton(
            right, text="SIGN UP",
            text_color=WHITE, fg_color=MAROON, hover_color="#8B1A24",
            font=("Poppins", 14, "bold"),
            corner_radius=8, height=46, cursor="hand2",
            command=self._do_signup
        ).grid(row=btn_base + 1, column=0, columnspan=2,
               sticky="ew", pady=(12, 8))

        # Login link centered
        login_lbl = tk.Label(right,
                              text="Already have an account? Login",
                              fg=MAROON, bg=WHITE,
                              font=("Poppins", 12, "underline"),
                              cursor="hand2")
        login_lbl.grid(row=btn_base + 2, column=0, columnspan=2)
        login_lbl.bind("<Button-1>", lambda e: self.on_login())

        # Bind mousewheel to all right panel children for smooth scrolling
        def _bind_wheel(w):
            w.bind("<MouseWheel>", _r_wheel)
            for ch in w.winfo_children():
                _bind_wheel(ch)
        _bind_wheel(right)

    # Renders a labeled entry field; password fields get an eye-toggle icon placed via place().
    def _field(self, parent, row_i, col, label_text, key, is_password):
        grid_row = row_i * 2 + 2
        px = (0, 8) if col == 0 else (8, 0)

        tk.Label(parent, text=label_text,
                 fg=BLACK, bg=WHITE, font=("Poppins", 11, "bold")
                 ).grid(row=grid_row, column=col, sticky="w", padx=px)

        var = tk.StringVar()
        self.vars[key] = var

        if is_password:
            pw_ctk = ctk.CTkEntry(parent, textvariable=var,
                                   show="•", height=42, corner_radius=8,
                                   border_color=MAROON, border_width=2,
                                   fg_color=WHITE, text_color=BLACK,
                                   font=("Poppins", 12))
            pw_ctk.grid(row=grid_row + 1, column=col, sticky="ew",
                        padx=px, pady=(2, 10))

            eye = tk.Label(parent, text=chr(128065), cursor="hand2",
                            bg=WHITE, fg=MAROON, font=("Poppins", 11))

            shown = [False]
            def _toggle(e=pw_ctk, lbl=eye, s=shown):
                s[0] = not s[0]
                e.configure(show="" if s[0] else "•")
                lbl.config(text=chr(128064) if s[0] else chr(128065))

            eye.bind("<Button-1>", lambda event, t=_toggle: t())

            def _place_eye(entry=pw_ctk, label=eye):
                entry.update_idletasks()
                x = entry.winfo_x() + entry.winfo_width() - 30
                y = entry.winfo_y() + (entry.winfo_height() // 2) - 10
                label.place(x=x, y=y)

            parent.after(100, _place_eye)
        else:
            ctk.CTkEntry(parent, textvariable=var,
                          height=42, corner_radius=8,
                          border_color=MAROON, border_width=2,
                          fg_color=WHITE, text_color=BLACK,
                          font=("Poppins", 12)
                          ).grid(row=grid_row + 1, column=col, sticky="ew",
                                 padx=px, pady=(2, 10))

    # Updates the live checklist labels as the user types; green check when a rule is satisfied.
    def _update_pw_checker(self):
        p = self.vars["password"].get()
        _RULE_TEXT = {
            "length":  "At least 8 characters",
            "upper":   "At least 1 uppercase letter (A-Z)",
            "lower":   "At least 1 lowercase letter (a-z)",
            "digit":   "At least 1 number (0-9)",
            "special": "At least 1 special character (!@#$%^&*)",
        }
        checks = {
            "length":  len(p) >= 8,
            "upper":   bool(re.search(r'[A-Z]', p)),
            "lower":   bool(re.search(r'[a-z]', p)),
            "digit":   bool(re.search(r'\d', p)),
            "special": bool(re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/`~\\]', p)),
        }
        for key, ok in checks.items():
            lbl = self._rule_labels[key]
            if ok:
                lbl.config(text=f"[\u2713] {_RULE_TEXT[key]}", fg="#2a8a2a")
            else:
                lbl.config(text=f"[  ] {_RULE_TEXT[key]}", fg="#999999")

        c = self.vars["confirm_password"].get()
        if not c:
            self._match_lbl.config(text="")
        elif p == c:
            self._match_lbl.config(text="\u2713 Passwords match!", fg="#2a8a2a")
        else:
            self._match_lbl.config(text="\u2717 Passwords do not match", fg="#CC0000")

    # Returns a list of unmet rules; empty list means the password is valid.
    @staticmethod
    def _validate_password(password):
        errors = []
        if len(password) < 8:
            errors.append("at least 8 characters")
        if not re.search(r'[A-Z]', password):
            errors.append("at least 1 uppercase letter")
        if not re.search(r'[a-z]', password):
            errors.append("at least 1 lowercase letter")
        if not re.search(r'\d', password):
            errors.append("at least 1 number")
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/`~\\]', password):
            errors.append("at least 1 special character (!@#$%^&* etc.)")
        return errors

    def _do_signup(self):
        v = {k: var.get().strip() for k, var in self.vars.items()}

        if not all([v["first_name"], v["last_name"], v["email"], v["password"]]):
            messagebox.showwarning("Sign Up", "Please fill in all required fields (*).")
            return

        # Restrict registration to university accounts only.
        if not v["email"].lower().endswith("@cmich.edu"):
            messagebox.showerror("Sign Up", "Only @cmich.edu email addresses are allowed to register.")
            return

        if v["password"] != v["confirm_password"]:
            messagebox.showerror("Sign Up", "Passwords do not match.")
            return

        pw_errors = self._validate_password(v["password"])
        if pw_errors:
            messagebox.showerror(
                "Password Requirements Not Met",
                "Your password must contain:\n\n• " + "\n• ".join(pw_errors)
            )
            return

        hashed = _sha256(v["password"])

        try:
            # Check for duplicate before inserting to surface a clear error instead of a DB constraint.
            exists = execute_query(
                "SELECT user_id FROM Users WHERE email = %s",
                (v["email"],), fetch=True
            )
            if exists:
                messagebox.showerror("Sign Up", "An account with this email already exists.")
                return

            execute_query(
                """INSERT INTO Users (first_name, last_name, email, phone_number,
                                     password_hash, role, account_status, penalty_points)
                   VALUES (%s, %s, %s, %s, %s, 'student', 'active', 0)""",
                (v["first_name"], v["last_name"], v["email"],
                 v["phone_number"] or None, hashed)
            )
            messagebox.showinfo("Sign Up", "Account created successfully! Please log in.")
            # Pass email so the login screen can pre-fill it without the user retyping.
            self.on_login(v["email"])
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
