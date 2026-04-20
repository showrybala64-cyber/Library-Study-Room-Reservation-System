import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from components.date_picker import make_date_entry
from connect_db import execute_query

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
LIGHT  = "#F5F5F5"


class ProfilePage(tk.Frame):
    def __init__(self, parent, user_info: dict, navigator, **kwargs):
        super().__init__(parent, bg=WHITE, **kwargs)
        self.user_info = user_info
        self.navigator = navigator
        self._build()

    # ------------------------------------------------------------------
    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        content = tk.Frame(self, bg=WHITE)
        content.grid(row=0, column=0, sticky="nsew", padx=30, pady=20)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)

        tk.Label(content, text="My Profile",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))

        # Load user data
        try:
            rows = execute_query(
                """SELECT user_id, first_name, last_name, email, phone_number,
                          date_of_birth, role, account_status,
                          penalty_points, created_at
                   FROM Users WHERE user_id = %s""",
                (self.user_info["user_id"],), fetch=True
            )
            if not rows:
                tk.Label(content, text="User data not found.",
                         fg="red", bg=WHITE).grid(row=1, column=0)
                return
            u = rows[0]
        except Exception as exc:
            tk.Label(content, text=f"DB Error: {exc}",
                     fg="red", bg=WHITE).grid(row=1, column=0)
            return

        # ── Personal Info (left) ──────────────────────────────────────
        pi_frame = tk.LabelFrame(content, text="Personal Information",
                                 bg=WHITE, fg=MAROON,
                                 font=("Poppins", 13, "bold"),
                                 padx=16, pady=12)
        pi_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))
        pi_frame.columnconfigure(1, weight=1)

        self.vars = {}
        personal_fields = [
            ("First Name",    "first_name",    str(u["first_name"] or ""),     False),
            ("Last Name",     "last_name",     str(u["last_name"] or ""),      False),
            ("Email",         "email",         str(u["email"] or ""),          False),
            ("Date of Birth", "dob",           str(u["date_of_birth"] or ""),  True),
            ("Phone Number",  "phone_number",  str(u["phone_number"] or ""),   True),
        ]
        for idx, (label, key, value, editable) in enumerate(personal_fields):
            tk.Label(pi_frame, text=label + ":",
                     fg=BLACK, bg=WHITE, font=("Poppins", 12, "bold")
                     ).grid(row=idx, column=0, sticky="w", pady=5)
            if key == "dob":
                self.dob_entry = make_date_entry(
                    pi_frame, default_date=value if value else None,
                    entry_width=200)
                self.dob_entry.grid(row=idx, column=1, sticky="ew",
                                    padx=(10, 0), pady=5)
            else:
                var = tk.StringVar(value=value)
                self.vars[key] = var
                state = "normal" if editable else "readonly"
                border = MAROON if editable else "#AAAAAA"
                entry = ctk.CTkEntry(pi_frame, textvariable=var,
                                     height=34, corner_radius=6,
                                     border_color=border, border_width=1,
                                     fg_color=WHITE if editable else LIGHT,
                                     text_color=BLACK,
                                     state=state, font=("Poppins", 12))
                entry.grid(row=idx, column=1, sticky="ew", padx=(10, 0), pady=5)

        # ── Account Info (right) ──────────────────────────────────────
        ai_frame = tk.LabelFrame(content, text="Account Information",
                                 bg=WHITE, fg=MAROON,
                                 font=("Poppins", 13, "bold"),
                                 padx=16, pady=12)
        ai_frame.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=(0, 12))
        ai_frame.columnconfigure(1, weight=1)

        account_fields = [
            ("User ID",        str(u["user_id"])),
            ("Role",           str(u["role"] or "").capitalize()),
            ("Account Status", str(u["account_status"] or "")),
            ("Penalty Points", str(u["penalty_points"] or 0)),
            ("Member Since",   str(u["created_at"])[:10] if u["created_at"] else ""),
        ]
        for idx, (label, value) in enumerate(account_fields):
            tk.Label(ai_frame, text=label + ":",
                     fg=BLACK, bg=WHITE, font=("Poppins", 12, "bold")
                     ).grid(row=idx, column=0, sticky="w", pady=5)
            ro_var = tk.StringVar(value=value)
            ctk.CTkEntry(ai_frame, textvariable=ro_var,
                         height=34, corner_radius=6,
                         border_color="#AAAAAA", border_width=1,
                         fg_color=LIGHT, text_color=BLACK,
                         state="readonly", font=("Poppins", 12)
                         ).grid(row=idx, column=1, sticky="ew", padx=(10, 0), pady=5)

        # Buttons
        btn_frame = tk.Frame(content, bg=WHITE)
        btn_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Button(btn_frame, text="Update Profile",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 13, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._update_profile
                  ).pack(side="left", padx=(0, 10))

        tk.Button(btn_frame, text="Change Password",
                  fg=MAROON, bg=GOLD,
                  font=("Poppins", 13, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=self._change_password
                  ).pack(side="left")

    # ------------------------------------------------------------------
    def _update_profile(self):
        dob          = self.dob_entry.get().strip()
        phone_number = self.vars["phone_number"].get().strip()
        try:
            execute_query(
                "UPDATE Users SET date_of_birth = %s, phone_number = %s WHERE user_id = %s",
                (dob or None, phone_number or None, self.user_info["user_id"])
            )
            messagebox.showinfo("Profile", "Profile updated successfully.")
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _change_password(self):
        popup = tk.Toplevel(self)
        popup.title("Change Password")
        popup.resizable(False, False)
        popup.configure(bg=WHITE)
        popup.grab_set()
        popup.update_idletasks()

        pw, ph = 420, 240
        px = self.winfo_rootx() + (self.winfo_width()  - pw) // 2
        py = self.winfo_rooty() + (self.winfo_height() - ph) // 2
        popup.geometry(f"{pw}x{ph}+{px}+{py}")

        tk.Label(popup, text="\U0001F512", bg=WHITE,
                 font=("Segoe UI Emoji", 24)).pack(pady=(20, 4))

        tk.Label(popup,
                 text="To change your password, you will be redirected to the\n"
                      "Forgot Password screen. Do you want to continue?",
                 fg="#333333", bg=WHITE, font=("Poppins", 13),
                 justify="center", wraplength=380).pack(padx=20)

        btn_row = tk.Frame(popup, bg=WHITE)
        btn_row.pack(pady=(15, 15))

        def go_forgot():
            popup.destroy()
            # Logout clears the session and returns to the login screen,
            # from which the user can access Forgot Password directly.
            self.navigator("logout_to_forgot")

        tk.Button(btn_row, text="Go to Forgot Password",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, width=18, pady=8, cursor="hand2",
                  command=go_forgot).pack(side="left", padx=(0, 10))

        tk.Button(btn_row, text="Cancel",
                  fg=BLACK, bg="#CCCCCC",
                  font=("Poppins", 12),
                  relief="flat", bd=0, width=10, pady=8, cursor="hand2",
                  command=popup.destroy).pack(side="left")
