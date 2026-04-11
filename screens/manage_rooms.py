import tkinter as tk
from tkinter import messagebox, ttk
import customtkinter as ctk
from connect_db import execute_query

MAROON = "#5E1219"
GOLD   = "#EFBF04"
BLACK  = "#000000"
WHITE  = "#FFFFFF"
LIGHT  = "#F5F5F5"

COLS = ("Room ID", "Room Number", "Category", "Capacity", "Status")


class ManageRooms(tk.Frame):
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
        content.grid(row=0, column=0, sticky="nsew", padx=24, pady=16)
        content.columnconfigure(0, weight=1)
        content.rowconfigure(3, weight=1)

        tk.Label(content, text="Manage Rooms",
                 fg=MAROON, bg=WHITE, font=("Poppins", 22, "bold")
                 ).grid(row=0, column=0, sticky="w")

        # Stats bar
        stats_frame = tk.Frame(content, bg=WHITE)
        stats_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        stats_center = tk.Frame(stats_frame, bg=WHITE)
        stats_center.pack(pady=8)
        self._stats_labels = {}
        for key in ["Total Rooms", "Available", "Under Maintenance"]:
            card = ctk.CTkFrame(stats_center, width=150, height=80,
                                fg_color=GOLD,
                                border_color=MAROON, border_width=2,
                                corner_radius=10)
            card.pack(side="left", padx=12)
            card.pack_propagate(False)
            tk.Label(card, text=key, fg=MAROON, bg=GOLD,
                     font=("Poppins", 13, "bold")).pack(pady=(12, 0))
            lbl = tk.Label(card, text="–", fg=MAROON, bg=GOLD,
                           font=("Poppins", 28, "bold"))
            lbl.pack()
            self._stats_labels[key] = lbl

        # Action buttons
        btn_row = tk.Frame(content, bg=WHITE)
        btn_row.grid(row=2, column=0, sticky="w", pady=(14, 8))
        for label, cmd in [
            ("Add Room",          self._add_room),
            ("Edit Room",         self._edit_room),
            ("Under Maintenance", self._maintenance_room),
            ("Search Room",       self._search_room),
            ("Refresh",           self._load_data),
        ]:
            tk.Button(btn_row, text=label,
                      fg=WHITE, bg=MAROON,
                      font=("Poppins", 12, "bold"),
                      relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
                      command=cmd
                      ).pack(side="left", padx=(0, 8))
        tk.Button(btn_row, text="Delete Room",
                  fg=WHITE, bg="#8B0000",
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=14, pady=7, cursor="hand2",
                  command=self._delete_room
                  ).pack(side="left", padx=(0, 8))

        # Treeview
        tree_frame = tk.Frame(content, bg=WHITE)
        tree_frame.grid(row=3, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        tree_border = tk.Frame(tree_frame,
                               highlightbackground=MAROON, highlightthickness=2)
        tree_border.grid(row=0, column=0, sticky="nsew")
        tree_border.columnconfigure(0, weight=1)
        tree_border.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(tree_border, columns=COLS,
                                 show="headings", selectmode="browse",
                                 style="Rooms.Treeview")
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Rooms.Treeview",
                    background="#FFFFFF", foreground="#000000", rowheight=30,
                    fieldbackground="#FFFFFF", bordercolor=MAROON,
                    borderwidth=2, font=("Poppins", 11))
        s.configure("Rooms.Treeview.Heading",
                    background=MAROON, foreground="#FFFFFF",
                    font=("Poppins", 12, "bold"), borderwidth=2, relief="groove")
        s.map("Rooms.Treeview",
              background=[("selected", MAROON)],
              foreground=[("selected", "#FFFFFF")])
        self.tree.tag_configure("evenrow", background="#FFFFFF")
        self.tree.tag_configure("oddrow",  background="#FFF8E7")
        for col in COLS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=130, anchor="center")

        vsb = ttk.Scrollbar(tree_border, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_border, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self._load_data()

    # ------------------------------------------------------------------
    def _load_data(self, search_term=None):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            if search_term:
                rows = execute_query(
                    "SELECT room_id, room_number, room_category, capacity, status FROM Rooms WHERE room_number LIKE %s",
                    (f"%{search_term}%",), fetch=True
                )
            else:
                rows = execute_query(
                    "SELECT room_id, room_number, room_category, capacity, status FROM Rooms ORDER BY room_id",
                    fetch=True
                )
            total = len(rows)
            avail = sum(1 for r in rows if r["status"] == "available")
            maint = sum(1 for r in rows if r["status"] == "maintenance")
            self._stats_labels["Total Rooms"].config(text=str(total))
            self._stats_labels["Available"].config(text=str(avail))
            self._stats_labels["Under Maintenance"].config(text=str(maint))

            for i, row in enumerate(rows):
                tag = "evenrow" if i % 2 == 0 else "oddrow"
                self.tree.insert("", "end", values=(
                    row["room_id"], row["room_number"],
                    row["room_category"], row["capacity"], row["status"]
                ), tags=(tag,))
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    # ------------------------------------------------------------------
    def _add_room(self):
        PREDEFINED = {
            "Projector Room": [
                {"num": "211E", "cap": 20, "floor": 2, "code": "PRJ-211E", "name": "Projector Room 211E"},
                {"num": "211W", "cap": 20, "floor": 2, "code": "PRJ-211W", "name": "Projector Room 211W"},
            ],
            "Group Study Room": [
                {"num": "207", "cap": 5, "floor": 2, "code": "GRP-207", "name": "Group Study Room 207"},
                {"num": "208", "cap": 5, "floor": 2, "code": "GRP-208", "name": "Group Study Room 208"},
                {"num": "307", "cap": 5, "floor": 3, "code": "GRP-307", "name": "Group Study Room 307"},
                {"num": "308", "cap": 5, "floor": 3, "code": "GRP-308", "name": "Group Study Room 308"},
            ],
            "Single Study Room": [
                {"num": "326", "cap": 1, "floor": 3, "code": "SNG-326", "name": "Single Study Room 326"},
                {"num": "327", "cap": 1, "floor": 3, "code": "SNG-327", "name": "Single Study Room 327"},
                {"num": "328", "cap": 1, "floor": 3, "code": "SNG-328", "name": "Single Study Room 328"},
                {"num": "329", "cap": 1, "floor": 3, "code": "SNG-329", "name": "Single Study Room 329"},
                {"num": "330", "cap": 1, "floor": 3, "code": "SNG-330", "name": "Single Study Room 330"},
                {"num": "331", "cap": 1, "floor": 3, "code": "SNG-331", "name": "Single Study Room 331"},
                {"num": "332", "cap": 1, "floor": 3, "code": "SNG-332", "name": "Single Study Room 332"},
                {"num": "333", "cap": 1, "floor": 3, "code": "SNG-333", "name": "Single Study Room 333"},
                {"num": "334", "cap": 1, "floor": 3, "code": "SNG-334", "name": "Single Study Room 334"},
                {"num": "335", "cap": 1, "floor": 3, "code": "SNG-335", "name": "Single Study Room 335"},
                {"num": "336", "cap": 1, "floor": 3, "code": "SNG-336", "name": "Single Study Room 336"},
            ],
        }
        CATEGORY_DB = {
            "Projector Room":    "projector",
            "Group Study Room":  "group_study",
            "Single Study Room": "single_study",
        }
        PREFIX_MAP = {
            "Projector Room":    "PRJ",
            "Group Study Room":  "GRP",
            "Single Study Room": "SNG",
        }

        win = tk.Toplevel(self)
        win.title("Add Room")
        win.geometry("500x600")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()
        self.update_idletasks()
        wx = self.winfo_rootx() + (self.winfo_width()  - 500) // 2
        wy = self.winfo_rooty() + (self.winfo_height() - 600) // 2
        win.geometry(f"500x600+{wx}+{wy}")

        # ── Header ─────────────────────────────────────────────────────
        tk.Label(win, text="Add New Room", fg=MAROON, bg=WHITE,
                 font=("Poppins", 16, "bold")).pack(pady=(18, 6))
        tk.Frame(win, bg="#E0E0E0", height=1).pack(fill="x", padx=24)

        # ── Footer ─────────────────────────────────────────────────────
        footer = tk.Frame(win, bg=WHITE)
        footer.pack(side="bottom", fill="x", pady=(0, 14))
        tk.Frame(footer, bg="#E0E0E0", height=1).pack(fill="x", padx=24, pady=(0, 10))
        btn_row = tk.Frame(footer, bg=WHITE)
        btn_row.pack()

        # ── Scrollable body ─────────────────────────────────────────────
        wrap = tk.Frame(win, bg=WHITE)
        wrap.pack(fill="both", expand=True)
        wrap.columnconfigure(0, weight=1)
        wrap.rowconfigure(0, weight=1)

        canvas = tk.Canvas(wrap, bg=WHITE, highlightthickness=0)
        vsb    = ttk.Scrollbar(wrap, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        form = tk.Frame(canvas, bg=WHITE)
        fid  = canvas.create_window((0, 0), window=form, anchor="nw")
        form.bind("<Configure>",   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(fid, width=e.width))

        def _wh(e): canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _wh)
        form.bind("<MouseWheel>",   _wh)

        def _lbl(text):
            l = tk.Label(form, text=text, fg=BLACK, bg=WHITE,
                         font=("Poppins", 11, "bold"), anchor="w")
            l.pack(fill="x", padx=24, pady=(12, 0))
            l.bind("<MouseWheel>", _wh)

        def _mk_entry(var, readonly=False):
            fg = "#E8E8E8" if readonly else WHITE
            e = ctk.CTkEntry(form, textvariable=var, height=34, corner_radius=6,
                             border_color=MAROON, border_width=1,
                             fg_color=fg, text_color=BLACK, font=("Poppins", 12),
                             state="disabled" if readonly else "normal")
            e.pack(fill="x", padx=24, pady=(2, 0))
            e.bind("<MouseWheel>", _wh)
            return e

        # ── Mode flag ───────────────────────────────────────────────────
        _custom = [False]

        # ── StringVars ──────────────────────────────────────────────────
        cat_var        = tk.StringVar(value="Projector Room")
        rnum_cb_var    = tk.StringVar()
        rnum_entry_var = tk.StringVar()
        name_var       = tk.StringVar()
        code_var       = tk.StringVar()
        cap_var        = tk.StringVar()
        floor_var      = tk.StringVar()
        status_var     = tk.StringVar(value="available")
        desc_var       = tk.StringVar()

        # ── Category ────────────────────────────────────────────────────
        _lbl("Category *")
        cat_combo = ttk.Combobox(form, textvariable=cat_var,
                                 values=list(PREDEFINED.keys()),
                                 state="readonly", font=("Poppins", 12))
        cat_combo.pack(fill="x", padx=24, pady=(2, 0))
        cat_combo.bind("<MouseWheel>", _wh)

        # ── Room Number header row (label + toggle button) ──────────────
        rnum_hdr = tk.Frame(form, bg=WHITE)
        rnum_hdr.pack(fill="x", padx=24, pady=(12, 0))
        rnum_hdr.bind("<MouseWheel>", _wh)
        tk.Label(rnum_hdr, text="Room Number *", fg=BLACK, bg=WHITE,
                 font=("Poppins", 11, "bold"), anchor="w").pack(side="left")
        custom_btn = tk.Button(rnum_hdr, text="Create Custom Room",
                               fg=MAROON, bg=WHITE,
                               font=("Poppins", 10, "bold"),
                               relief="flat", bd=0, cursor="hand2")
        custom_btn.pack(side="right")

        # ── Room number container ────────────────────────────────────────
        rnum_wrap = tk.Frame(form, bg=WHITE)
        rnum_wrap.pack(fill="x", padx=24, pady=(2, 0))
        rnum_wrap.bind("<MouseWheel>", _wh)

        rnum_combo = ttk.Combobox(rnum_wrap, textvariable=rnum_cb_var,
                                  state="readonly", font=("Poppins", 12))
        rnum_combo.pack(fill="x")
        rnum_combo.bind("<MouseWheel>", _wh)

        rnum_entry_w = ctk.CTkEntry(rnum_wrap, textvariable=rnum_entry_var,
                                    height=34, corner_radius=6,
                                    border_color=MAROON, border_width=1,
                                    fg_color=WHITE, text_color=BLACK,
                                    font=("Poppins", 12))
        # not packed initially

        # ── Auto-filled fields ───────────────────────────────────────────
        _lbl("Room Name (auto)")
        name_entry  = _mk_entry(name_var,  readonly=True)

        _lbl("Room Code (auto)")
        code_entry  = _mk_entry(code_var,  readonly=True)

        _lbl("Capacity *")
        cap_entry   = _mk_entry(cap_var,   readonly=True)

        _lbl("Floor Number *")
        floor_entry = _mk_entry(floor_var, readonly=True)

        # ── Status & Description ─────────────────────────────────────────
        _lbl("Status")
        status_combo = ttk.Combobox(form, textvariable=status_var,
                                    values=["available", "inactive", "maintenance"],
                                    state="readonly", font=("Poppins", 12))
        status_combo.pack(fill="x", padx=24, pady=(2, 0))
        status_combo.bind("<MouseWheel>", _wh)

        _lbl("Description (optional)")
        _mk_entry(desc_var, readonly=False)
        tk.Frame(form, bg=WHITE, height=16).pack()

        # ── Helpers ──────────────────────────────────────────────────────
        def _set_readonly(readonly):
            fg    = "#E8E8E8" if readonly else WHITE
            state = "disabled" if readonly else "normal"
            for e in [name_entry, code_entry, cap_entry, floor_entry]:
                e.configure(state=state, fg_color=fg)

        def _update_room_list(*_):
            if _custom[0]:
                return
            cat = cat_var.get()
            all_rooms = PREDEFINED.get(cat, [])
            try:
                existing = execute_query("SELECT room_code FROM Rooms", fetch=True)
                existing_codes = {r["room_code"] for r in (existing or [])}
            except Exception:
                existing_codes = set()
            available = [r["num"] for r in all_rooms if r["code"] not in existing_codes]
            rnum_combo["values"] = available if available else ["(all rooms added)"]
            rnum_cb_var.set("")
            name_var.set(""); code_var.set(""); cap_var.set(""); floor_var.set("")

        DESC_TMPL = {
            "Projector Room":    "Projector-equipped room on floor {floor}, capacity {cap}. Suitable for presentations and collaborative sessions.",
            "Group Study Room":  "Group study room on floor {floor}, capacity {cap}. Designed for collaborative group work.",
            "Single Study Room": "Individual quiet study room on floor {floor}, capacity {cap}. For focused solo study.",
        }

        def _on_room_select(*_):
            if _custom[0]:
                return
            cat  = cat_var.get()
            rnum = rnum_cb_var.get()
            match = next((r for r in PREDEFINED.get(cat, []) if r["num"] == rnum), None)
            if match:
                name_var.set(match["name"])
                code_var.set(match["code"])
                cap_var.set(str(match["cap"]))
                floor_var.set(str(match["floor"]))
                tmpl = DESC_TMPL.get(cat, "")
                desc_var.set(tmpl.format(floor=match["floor"], cap=match["cap"]))

        def _auto_custom(*_):
            if not _custom[0]:
                return
            cat    = cat_var.get()
            prefix = PREFIX_MAP.get(cat, "X")
            rnum   = rnum_entry_var.get().strip()
            code_var.set(f"{prefix}-{rnum}" if rnum else f"{prefix}-")
            name_var.set(f"{cat} {rnum}" if rnum else "")

        cat_var.trace_add("write",        _update_room_list)
        rnum_cb_var.trace_add("write",    _on_room_select)
        rnum_entry_var.trace_add("write", _auto_custom)

        def _toggle_custom():
            if _custom[0]:
                _custom[0] = False
                rnum_entry_w.pack_forget()
                rnum_combo.pack(fill="x")
                custom_btn.config(text="Create Custom Room")
                _set_readonly(True)
                _update_room_list()
            else:
                _custom[0] = True
                rnum_combo.pack_forget()
                rnum_entry_w.pack(fill="x")
                custom_btn.config(text="\u2190 Use Predefined")
                _set_readonly(False)
                rnum_entry_var.set("")
                name_var.set(""); code_var.set(""); cap_var.set(""); floor_var.set("")

        custom_btn.config(command=_toggle_custom)
        _update_room_list()

        # ── Submit ───────────────────────────────────────────────────────
        def _submit():
            rnum  = rnum_entry_var.get().strip() if _custom[0] else rnum_cb_var.get().strip()
            cat   = cat_var.get().strip()
            code  = code_var.get().strip()
            cap   = cap_var.get().strip()
            floor = floor_var.get().strip()
            stat  = status_var.get().strip() or "available"
            desc  = desc_var.get().strip()

            if not rnum or rnum == "(all rooms added)":
                messagebox.showwarning("Add Room", "Please select or enter a room number.", parent=win)
                return
            if not all([cap, floor]):
                messagebox.showwarning("Add Room", "Please fill in all required fields (*).", parent=win)
                return
            try:
                cap_int   = int(cap)
                floor_int = int(floor)
            except ValueError:
                messagebox.showwarning("Add Room", "Capacity and Floor Number must be integers.", parent=win)
                return

            db_cat = cat  # DB CHECK constraint: exact strings required
            name   = name_var.get().strip() or f"{cat} {rnum}"
            if not code:
                code = f"{PREFIX_MAP.get(cat, 'X')}-{rnum}"
            if not desc:
                tmpl = DESC_TMPL.get(cat, "")
                desc = tmpl.format(floor=floor_int, cap=cap_int) if tmpl else ""

            vals = (code, name, db_cat, floor_int, rnum, cap_int, stat, desc or None)
            print("[Add Room] INSERT values:", vals)

            try:
                execute_query(
                    """INSERT INTO Rooms (room_code, room_name, room_category,
                                         floor_number, room_number, capacity, status, description)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    vals
                )
                messagebox.showinfo("Add Room", "Room added successfully.", parent=win)
                win.destroy()
                self._load_data()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        # ── Footer buttons ──────────────────────────────────────────────
        tk.Button(btn_row, text="Cancel",
                  fg="#555555", bg="#E0E0E0",
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Add Room",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=_submit).pack(side="left")

    def _maintenance_room(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Under Maintenance", "Select a room first.")
            return
        vals     = self.tree.item(sel[0])["values"]
        room_id  = vals[0]
        room_num = vals[1]

        win = tk.Toplevel(self)
        win.title("Under Maintenance")
        win.geometry("400x230")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()
        self.update_idletasks()
        wx = self.winfo_rootx() + (self.winfo_width()  - 400) // 2
        wy = self.winfo_rooty() + (self.winfo_height() - 230) // 2
        win.geometry(f"400x230+{wx}+{wy}")

        tk.Label(win, text=f"Move Room {room_num} to maintenance?",
                 fg=MAROON, bg=WHITE, font=("Poppins", 13, "bold"),
                 wraplength=360).pack(pady=(18, 8))
        tk.Label(win, text="Reason:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(anchor="w", padx=30)
        reason_var = tk.StringVar(value="Scheduled Maintenance")
        ttk.Combobox(win, textvariable=reason_var,
                     values=["Scheduled Maintenance", "Equipment Repair",
                             "Deep Cleaning", "Temporary Closure", "Other"],
                     state="readonly", width=32,
                     font=("Poppins", 12)).pack(padx=30, pady=(4, 18))

        def _confirm():
            try:
                execute_query(
                    "UPDATE Rooms SET status = 'maintenance' WHERE room_id = %s",
                    (room_id,)
                )
                win.destroy()
                self._load_data()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        btn_f = tk.Frame(win, bg=WHITE)
        btn_f.pack()
        tk.Button(btn_f, text="Cancel",
                  fg="#555555", bg="#E0E0E0",
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=(0, 10))
        tk.Button(btn_f, text="Confirm",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=16, pady=7, cursor="hand2",
                  command=_confirm).pack(side="left")

    # ------------------------------------------------------------------
    def _edit_room(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Edit Room", "Select a room first.")
            return
        room_id = self.tree.item(sel[0])["values"][0]

        try:
            rows = execute_query(
                """SELECT room_id, room_number, room_category, room_code,
                          floor_number, capacity, status, description
                   FROM Rooms WHERE room_id = %s""",
                (room_id,), fetch=True
            )
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))
            return
        if not rows:
            return
        r = rows[0]

        win = tk.Toplevel(self)
        win.title(f"Edit Room {r['room_number']}")
        win.geometry("480x560")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()
        self.update_idletasks()
        wx = self.winfo_rootx() + (self.winfo_width()  - 480) // 2
        wy = self.winfo_rooty() + (self.winfo_height() - 560) // 2
        win.geometry(f"480x560+{wx}+{wy}")

        # ── Title ───────────────────────────────────────────────────────
        tk.Label(win, text=f"Edit Room {r['room_number']}", fg=MAROON, bg=WHITE,
                 font=("Poppins", 16, "bold")).pack(pady=(18, 4))
        tk.Frame(win, bg="#E0E0E0", height=1).pack(fill="x", padx=24)

        # ── Footer (packed first so it anchors to bottom) ───────────────
        footer = tk.Frame(win, bg=WHITE)
        footer.pack(side="bottom", fill="x", pady=(0, 14))
        tk.Frame(footer, bg="#E0E0E0", height=1).pack(fill="x", padx=24, pady=(0, 10))
        btn_row = tk.Frame(footer, bg=WHITE)
        btn_row.pack()

        # ── Body ────────────────────────────────────────────────────────
        body = tk.Frame(win, bg=WHITE)
        body.pack(fill="both", expand=True, padx=28, pady=(10, 0))

        # Section: Room Information
        tk.Label(body, text="Room Information",
                 fg="#888888", bg=WHITE,
                 font=("Poppins", 11, "italic")).pack(anchor="w", pady=(0, 6))

        RO_BG = "#F0F0F0"
        fields = [
            ("Room Number",  str(r["room_number"]   or "")),
            ("Category",     str(r["room_category"] or "")),
            ("Room Code",    str(r["room_code"]     or "")),
            ("Floor Number", str(r["floor_number"]  or "")),
            ("Capacity",     str(r["capacity"]      or "")),
            ("Description",  str(r["description"]   or "")),
        ]
        for label, value in fields:
            row_f = tk.Frame(body, bg=WHITE)
            row_f.pack(fill="x", pady=(0, 4))
            tk.Label(row_f, text=label, width=14, anchor="w",
                     fg="#555555", bg=WHITE,
                     font=("Poppins", 11, "bold")).pack(side="left")
            var = tk.StringVar(value=value)
            tk.Entry(row_f, textvariable=var, state="disabled",
                     disabledbackground=RO_BG, disabledforeground="#888888",
                     font=("Poppins", 11),
                     relief="flat", bd=1,
                     highlightbackground="#CCCCCC", highlightthickness=1
                     ).pack(side="left", fill="x", expand=True, ipady=4)

        # Divider
        tk.Frame(body, bg="#E0E0E0", height=1).pack(fill="x", pady=(10, 10))

        # Section: Update Status
        tk.Label(body, text="Update Status",
                 fg=MAROON, bg=WHITE,
                 font=("Poppins", 12, "bold")).pack(anchor="w", pady=(0, 6))

        status_var = tk.StringVar(value=str(r["status"] or "available"))
        status_cb = ttk.Combobox(body, textvariable=status_var,
                                 values=["available", "inactive", "maintenance"],
                                 state="readonly", font=("Poppins", 12),
                                 width=24)
        status_cb.pack(anchor="w")

        # ── Save logic ──────────────────────────────────────────────────
        def _save():
            stat = status_var.get().strip()
            try:
                execute_query(
                    "UPDATE Rooms SET status = %s, updated_at = NOW() WHERE room_id = %s",
                    (stat, room_id)
                )
                messagebox.showinfo("Edit Room",
                                    f"Room {r['room_number']} updated to '{stat}'.",
                                    parent=win)
                win.destroy()
                self._load_data()
            except Exception as exc:
                messagebox.showerror("Database Error", str(exc), parent=win)

        tk.Button(btn_row, text="Cancel",
                  fg="#555555", bg="#E0E0E0",
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=win.destroy).pack(side="left", padx=(0, 10))
        tk.Button(btn_row, text="Save Changes",
                  fg=WHITE, bg=MAROON,
                  font=("Poppins", 12, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=_save).pack(side="left")

    # ------------------------------------------------------------------
    def _delete_room(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Delete Room", "Select a room first.")
            return
        vals     = self.tree.item(sel[0])["values"]
        room_id  = vals[0]
        room_num = vals[1]

        if not messagebox.askyesno(
            "Delete Room",
            f"Permanently delete Room {room_num}?\nThis cannot be undone."
        ):
            return
        try:
            result = execute_query(
                "SELECT COUNT(*) AS cnt FROM Reservations "
                "WHERE room_id = %s AND status IN ('reserved', 'checked_in')",
                (room_id,), fetch=True
            )
            active = result[0]["cnt"] if result else 0
            if active > 0:
                messagebox.showerror(
                    "Cannot Delete",
                    f"Room {room_num} has {active} active reservation(s).\n"
                    "Cancel those reservations before deleting."
                )
                return
            execute_query("DELETE FROM Rooms WHERE room_id = %s", (room_id,))
            self._load_data()
        except Exception as exc:
            messagebox.showerror("Database Error", str(exc))

    def _search_room(self):
        win = tk.Toplevel(self)
        win.title("Search Room")
        win.geometry("300x140")
        win.resizable(False, False)
        win.configure(bg=WHITE)
        win.grab_set()

        tk.Label(win, text="Room Number:", fg=BLACK, bg=WHITE,
                 font=("Poppins", 12)).pack(pady=(20, 4))
        var = tk.StringVar()
        ctk.CTkEntry(win, textvariable=var, height=34, corner_radius=6,
                     border_color=MAROON, border_width=1,
                     fg_color=WHITE, text_color=BLACK,
                     font=("Poppins", 12)
                     ).pack(fill="x", padx=30, pady=(0, 10))

        def do_search():
            win.destroy()
            self._load_data(var.get().strip())

        tk.Button(win, text="SEARCH", fg=WHITE, bg=MAROON,
                  font=("Poppins", 13, "bold"),
                  relief="flat", bd=0, padx=20, pady=8, cursor="hand2",
                  command=do_search).pack()
