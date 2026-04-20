import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from PIL import Image, ImageTk
import os
import re
import hashlib
from connect_db import execute_query

MAROON  = "#5E1219"
GOLD    = "#EFBF04"
BLACK   = "#000000"
WHITE   = "#FFFFFF"
CREAM   = "#FFF8E7"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class ForgotPasswordScreen(tk.Frame):
    def __init__(self, parent, on_login, prefill_email: str = "", temp_mode: bool = False, **kwargs):
        super().__init__(parent, bg=GOLD, **kwargs)
        self.on_login      = on_login
        self._prefill_email = prefill_email
        self._temp_mode    = temp_mode
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # ── Body ──────────────────────────────────────────────────────
        body = tk.Frame(self, bg=GOLD)
        body.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.rowconfigure(0, weight=1)

        # ── Cream card (placed, responsive) ───────────────────────────
        card = tk.Frame(body, bg=CREAM,
                        highlightbackground="#cccccc", highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center",
                   relwidth=0.42, relheight=0.84)
        card.columnconfigure(0, weight=1)
        card.columnconfigure(1, weight=0)   # scrollbar column
        card.rowconfigure(0, weight=0)      # static title
        card.rowconfigure(1, weight=1)      # scrollable content

        # ── Static title area (always visible) ───────────────────────
        title_area = tk.Frame(card, bg=CREAM)
        title_area.grid(row=0, column=0, columnspan=2, sticky="ew")

        tk.Label(title_area, text="Reset Password",
                 fg=MAROON, bg=CREAM,
                 font=("Poppins", 20, "bold")
                 ).pack(pady=(22, 2))
        tk.Label(title_area, text="Enter your email and new password below.",
                 fg="#555555", bg=CREAM, font=("Poppins", 12)
                 ).pack()
        tk.Frame(title_area, bg="#D8D0C8", height=1
                 ).pack(fill="x", padx=24, pady=(10, 0))

        # ── Scrollable canvas + scrollbar ─────────────────────────────
        canvas = tk.Canvas(card, bg=CREAM, highlightthickness=0)
        vsb    = ttk.Scrollbar(card, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 0), pady=(4, 0))
        vsb.grid(row=1, column=1, sticky="ns", pady=(4, 0))

        # ── Form frame inside canvas ──────────────────────────────────
        form = tk.Frame(canvas, bg=CREAM)
        form.columnconfigure(0, weight=1)
        form_id = canvas.create_window((0, 0), window=form, anchor="nw")

        def _sync_scroll(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_width(e):
            canvas.itemconfig(form_id, width=e.width)

        form.bind("<Configure>", _sync_scroll)
        canvas.bind("<Configure>", _sync_width)

        # Mousewheel scrolling
        def _on_wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

        canvas.bind("<MouseWheel>", _on_wheel)
        form.bind("<MouseWheel>", _on_wheel)

        # ── Build fields in scrollable form ───────────────────────────
        self.vars = {}

        def _add_label(row, text):
            lbl = tk.Label(form, text=text,
                           fg=BLACK, bg=CREAM, font=("Poppins", 12, "bold"))
            lbl.grid(row=row, column=0, sticky="w", padx=30, pady=(14, 0))
            lbl.bind("<MouseWheel>", _on_wheel)

        def _add_entry(row, var, state="normal"):
            entry = ctk.CTkEntry(form, textvariable=var,
                                  height=42, corner_radius=8,
                                  border_color=MAROON, border_width=2,
                                  fg_color=WHITE, text_color=BLACK,
                                  font=("Poppins", 13), state=state)
            entry.grid(row=row, column=0, sticky="ew", padx=30, pady=(2, 0))
            entry.bind("<MouseWheel>", _on_wheel)

        # Temp-mode banner (row -1, packed before grid rows)
        if self._temp_mode:
            banner = tk.Frame(form, bg="#FFF3CD", relief="flat", bd=0)
            banner.grid(row=0, column=0, sticky="ew", padx=30, pady=(14, 0))
            banner.bind("<MouseWheel>", _on_wheel)
            tk.Label(
                banner,
                text="\u26a0  Please enter 'mypass' as your current password "
                     "and set a new password below.",
                fg="#7D5A00", bg="#FFF3CD",
                font=("Poppins", 11), wraplength=330, justify="left",
                padx=10, pady=8
            ).pack(fill="x")
            email_row_offset = 1
        else:
            email_row_offset = 0

        # Email (rows offset, offset+1)
        email_var = tk.StringVar(value=self._prefill_email)
        self.vars["email"] = email_var
        email_state = "readonly" if (self._temp_mode and self._prefill_email) else "normal"
        _add_label(email_row_offset,     "Email Address *")
        _add_entry(email_row_offset + 1, email_var, state=email_state)

        # r is the last row used; all subsequent fields shift with email_row_offset
        r = email_row_offset + 1

        # Old / Temporary password
        old_var = tk.StringVar()
        self.vars["old_pass"] = old_var
        _add_label(r + 1, "Current / Temporary Password *")
        self._pw_field(form, r + 2, old_var, _on_wheel)

        # New password
        new_var = tk.StringVar()
        self.vars["new_pass"] = new_var
        _add_label(r + 3, "New Password *")
        self._pw_field(form, r + 4, new_var, _on_wheel)

        # ── Live password checker ──────────────────────────────────
        self._fp_rule_labels = {}
        checker_frame = tk.Frame(form, bg=CREAM)
        checker_frame.grid(row=r + 5, column=0, sticky="w", padx=30, pady=(4, 0))
        checker_frame.bind("<MouseWheel>", _on_wheel)
        _RULE_DEFS = [
            ("length",  "At least 8 characters"),
            ("upper",   "At least 1 uppercase letter (A-Z)"),
            ("lower",   "At least 1 lowercase letter (a-z)"),
            ("digit",   "At least 1 number (0-9)"),
            ("special", "At least 1 special character (!@#$%^&*)"),
        ]
        for rkey, rtext in _RULE_DEFS:
            rl = tk.Label(checker_frame, text=f"[  ] {rtext}",
                          fg="#999999", bg=CREAM, font=("Poppins", 10), anchor="w")
            rl.pack(anchor="w")
            rl.bind("<MouseWheel>", _on_wheel)
            self._fp_rule_labels[rkey] = rl

        # Confirm password
        confirm_var = tk.StringVar()
        self.vars["confirm"] = confirm_var
        _add_label(r + 6, "Confirm New Password *")
        self._pw_field(form, r + 7, confirm_var, _on_wheel)

        # Match indicator
        self._fp_match_lbl = tk.Label(form, text="", bg=CREAM, font=("Poppins", 10))
        self._fp_match_lbl.grid(row=r + 8, column=0, sticky="w", padx=30)
        self._fp_match_lbl.bind("<MouseWheel>", _on_wheel)

        # Bind traces
        new_var.trace_add("write", lambda *_: self._update_fp_checker())
        confirm_var.trace_add("write", lambda *_: self._update_fp_checker())

        # Divider
        div = tk.Frame(form, bg="#D8D0C8", height=1)
        div.grid(row=r + 9, column=0, sticky="ew", padx=30, pady=(16, 0))
        div.bind("<MouseWheel>", _on_wheel)

        # SUBMIT button
        sub_btn = ctk.CTkButton(
            form, text="SUBMIT",
            text_color=WHITE, fg_color=MAROON, hover_color="#8B1A24",
            font=("Poppins", 14, "bold"),
            corner_radius=8, height=46, cursor="hand2",
            command=self._do_reset
        )
        sub_btn.grid(row=r + 10, column=0, sticky="ew", padx=30, pady=(14, 6))
        sub_btn.bind("<MouseWheel>", _on_wheel)

        # Back to Login link
        back_lbl = tk.Label(form,
                             text="← Back to Login",
                             fg=MAROON, bg=CREAM,
                             font=("Poppins", 12, "underline"),
                             cursor="hand2")
        back_lbl.grid(row=r + 11, column=0, pady=(0, 24))
        back_lbl.bind("<Button-1>", lambda e: self.on_login())
        back_lbl.bind("<MouseWheel>", _on_wheel)

    # ------------------------------------------------------------------
    def _update_fp_checker(self):
        p = self.vars["new_pass"].get()
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
            lbl = self._fp_rule_labels[key]
            if ok:
                lbl.config(text=f"[\u2713] {_RULE_TEXT[key]}", fg="#2a8a2a")
            else:
                lbl.config(text=f"[  ] {_RULE_TEXT[key]}", fg="#999999")

        c = self.vars["confirm"].get()
        if not c:
            self._fp_match_lbl.config(text="")
        elif p == c:
            self._fp_match_lbl.config(text="\u2713 Passwords match!", fg="#2a8a2a")
        else:
            self._fp_match_lbl.config(text="\u2717 Passwords do not match", fg="#CC0000")

    # ------------------------------------------------------------------
    def _pw_field(self, parent, grid_row, var, wheel_cb=None):
        """Password CTkEntry with place()-overlaid eye toggle."""
        pw_ctk = ctk.CTkEntry(parent, textvariable=var,
                               show="•", height=42, corner_radius=8,
                               border_color=MAROON, border_width=2,
                               fg_color=WHITE, text_color=BLACK,
                               font=("Poppins", 13))
        pw_ctk.grid(row=grid_row, column=0, sticky="ew", padx=30, pady=(2, 0))

        eye = tk.Label(parent, text=chr(128065), cursor="hand2",
                        bg=WHITE, fg=MAROON, font=("Poppins", 11))

        shown = [False]
        def _toggle(e=pw_ctk, lbl=eye, s=shown):
            s[0] = not s[0]
            e.configure(show="" if s[0] else "•")
            lbl.config(text=chr(128064) if s[0] else chr(128065))

        eye.bind("<Button-1>", lambda event, t=_toggle: t())

        if wheel_cb:
            pw_ctk.bind("<MouseWheel>", wheel_cb)
            eye.bind("<MouseWheel>", wheel_cb)

        def _place_eye(entry=pw_ctk, label=eye):
            entry.update_idletasks()
            x = entry.winfo_x() + entry.winfo_width() - 30
            y = entry.winfo_y() + (entry.winfo_height() // 2) - 10
            label.place(x=x, y=y)

        parent.after(100, _place_eye)

    # ------------------------------------------------------------------
    def _do_reset(self):
        v = {k: var.get().strip() for k, var in self.vars.items()}

        if not all([v["email"], v["old_pass"], v["new_pass"], v["confirm"]]):
            messagebox.showwarning("Reset", "Please fill in all required fields.")
            return

        if not v["email"].lower().endswith("@cmich.edu"):
            messagebox.showerror("Reset", "Only @cmich.edu email addresses are allowed.")
            return

        if v["new_pass"] != v["confirm"]:
            messagebox.showerror("Reset", "New passwords do not match.")
            return

        p = v["new_pass"]
        pw_errors = []
        if len(p) < 8:
            pw_errors.append("at least 8 characters")
        if not re.search(r'[A-Z]', p):
            pw_errors.append("at least 1 uppercase letter")
        if not re.search(r'[a-z]', p):
            pw_errors.append("at least 1 lowercase letter")
        if not re.search(r'\d', p):
            pw_errors.append("at least 1 number")
        if not re.search(r'[!@#$%^&*()\-_=+\[\]{}|;:\'",.<>?/`~\\]', p):
            pw_errors.append("at least 1 special character (!@#$%^&* etc.)")
        if pw_errors:
            messagebox.showerror(
                "Password Requirements Not Met",
                "Your new password must contain:\n\n• " + "\n• ".join(pw_errors)
            )
            return

        hashed_old = _sha256(v["old_pass"])
        hashed_new = _sha256(v["new_pass"])

        try:
            rows = execute_query(
                "SELECT user_id FROM Users WHERE email = %s AND password_hash = %s",
                (v["email"], hashed_old), fetch=True
            )
            if not rows:
                messagebox.showerror("Reset", "Incorrect current/temporary password.")
                return

            execute_query(
                "UPDATE Users SET password_hash = %s, password_reset_required = 0 "
                "WHERE email = %s",
                (hashed_new, v["email"])
            )
            messagebox.showinfo(
                "Reset",
                "Password updated successfully. Please login with your new password."
            )
            self.on_login()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
