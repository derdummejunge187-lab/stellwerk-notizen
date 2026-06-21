import tkinter as tk
from tkinter import messagebox, ttk
import json, os, shutil, csv, datetime, subprocess, platform, tempfile
import threading, urllib.request, ssl, sys

# ══════════════════════════════════════════════════════════════════════════════
APP_VERSION  = "1.0.0"           # ← hier anpassen bei neuem Release
GITHUB_USER  = "derdummejunge187-lab"
GITHUB_REPO  = "stellwerk-notizen"
VERSION_URL  = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
DOWNLOAD_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/notizen_app.py"
# ══════════════════════════════════════════════════════════════════════════════

LIGHT = {"BG":"#F5F0F0","PANEL":"#FFFFFF","PRIMARY":"#C0392B","PRIMARY_H":"#A93226",
         "DANGER":"#E74C3C","TEXT":"#2C2C2C","SUBTEXT":"#7F7F7F","BORDER":"#E8DEDE",
         "ROW_ODD":"#FDF6F6","ROW_EVEN":"#FFFFFF"}
DARK  = {"BG":"#1E1E2E","PANEL":"#2A2A3E","PRIMARY":"#C0392B","PRIMARY_H":"#A93226",
         "DANGER":"#E74C3C","TEXT":"#E0E0E0","SUBTEXT":"#888899","BORDER":"#3A3A55",
         "ROW_ODD":"#252535","ROW_EVEN":"#2A2A3E"}
C = dict(LIGHT)

FONT_BTN   = ("Segoe UI", 10, "bold")
FONT_LABEL = ("Segoe UI", 9)
FONT_INPUT = ("Segoe UI", 10)
FONT_TABLE = ("Segoe UI", 9)

STW_OPTIONS    = ["BHBF", "NS", "AK", "STB"]
FAHRT_OPTIONS  = ["Zugfahrt", "Rangierfahrt", "Gastfahrt", "Leerfahrt"]
STATUS_OPTIONS = ["Offen", "In Bearbeitung", "Erledigt"]
STATUS_COLORS  = {"Offen":"#E74C3C","In Bearbeitung":"#F39C12","Erledigt":"#27AE60"}
PRIO_OPTIONS   = ["Hoch", "Mittel", "Niedrig"]
PRIO_COLORS    = {"Hoch":"#C0392B","Mittel":"#E67E22","Niedrig":"#27AE60"}

DATA_FILE  = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__)), "notizen_data.json")
TF_FILE    = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__)), "tf_data.json")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__)), "backups")

def load_json(path):
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return []

def save_json(path, data):
    with open(path,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)

def do_backup(path):
    if not os.path.exists(path): return
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"{os.path.basename(path)}.{datetime.date.today().isoformat()}.bak")
    if not os.path.exists(dst): shutil.copy2(path, dst)

def now_str():
    return datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

def make_btn(parent, text, command, bg=None, fg="white", padx=14, pady=6):
    if bg is None: bg = C["PRIMARY"]
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, font=FONT_BTN,
                    relief="flat", cursor="hand2", padx=padx, pady=pady,
                    activebackground=C["PRIMARY_H"], activeforeground="white", bd=0)
    hover = C["PRIMARY_H"] if bg == C["PRIMARY"] else "#BB9999"
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
    btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
    return btn

# ── Auto-Updater ──────────────────────────────────────────────────────────────
def _https_get(url, timeout=8):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": "StellwerkNotizen-Updater/1.0"})
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)

def check_for_update(parent, silent=False):
    def _check():
        try:
            with _https_get(VERSION_URL) as r:
                remote = r.read().decode().strip()
            if remote != APP_VERSION:
                parent.after(0, lambda: _show_update(remote))
            elif not silent:
                parent.after(0, lambda: messagebox.showinfo(
                    "Kein Update", f"Version {APP_VERSION} ist aktuell.", parent=parent))
        except Exception as e:
            if not silent:
                parent.after(0, lambda: messagebox.showwarning(
                    "Update", f"Keine Verbindung zu GitHub.\n{e}", parent=parent))

    def _show_update(remote):
        win = tk.Toplevel(parent)
        win.title("Update verfügbar")
        win.resizable(False, False)
        win.configure(bg=C["BG"])
        win.grab_set()
        win.geometry("380x190")
        hf = tk.Frame(win, bg=C["PRIMARY"]); hf.pack(fill="x")
        tk.Label(hf, text="🔄 Update verfügbar", font=("Segoe UI",12,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(padx=16, pady=12)
        tk.Label(win, text=f"Installiert:  v{APP_VERSION}\nVerfügbar:   v{remote}",
                 font=("Segoe UI",11), bg=C["BG"], fg=C["TEXT"], justify="left").pack(padx=24, pady=16)
        bf = tk.Frame(win, bg=C["BG"]); bf.pack(pady=8)
        make_btn(bf, "Jetzt updaten", lambda: _do_update(win, remote)).pack(side="left", padx=8)
        make_btn(bf, "Später", win.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="left")

    def _do_update(win, remote):
        try:
            base   = os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__))
            target = os.path.join(base, "notizen_app.py")
            with _https_get(DOWNLOAD_URL, timeout=20) as r:
                new_code = r.read()
            if os.path.exists(target):
                shutil.copy2(target, target + f".v{APP_VERSION}.bak")
            with open(target, "wb") as f:
                f.write(new_code)
            win.destroy()
            messagebox.showinfo("Update",
                f"v{remote} heruntergeladen!\nGespeichert: {target}\n\nBitte Programm neu starten.",
                parent=parent)
        except Exception as ex:
            messagebox.showerror("Update fehlgeschlagen", str(ex), parent=parent)

    threading.Thread(target=_check, daemon=True).start()

# ── Popup ─────────────────────────────────────────────────────────────────────
class NotePopup(tk.Toplevel):
    def __init__(self, parent, on_confirm, existing=None, tf_mode=False):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.existing   = existing
        self.tf_mode    = tf_mode
        self.title("Notiz bearbeiten" if existing else "Neue Notiz")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.grab_set()
        w, h = 420, 520
        self.update_idletasks()
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = parent.winfo_rooty()+(parent.winfo_height()-h)//2
        self.geometry(f"{w}x{h}+{px}+{py}")
        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text="Notiz bearbeiten" if self.existing else "Neue Notiz",
                 font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"),
                     bg=C["PRIMARY"], fg="white", cursor="hand2"); x.pack(side="right", padx=8)
        x.bind("<Button-1>", lambda e: self.destroy())

        body = tk.Frame(self, bg=C["BG"]); body.pack(fill="both", expand=True, padx=20, pady=14)

        if not self.tf_mode:
            tk.Label(body, text="Stellwerk", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
            self.stw_var = tk.StringVar(value=(self.existing or {}).get("stw", STW_OPTIONS[0]))
            row = tk.Frame(body, bg=C["BG"]); row.pack(anchor="w", pady=4)
            self._stw_btns = {}
            for s in STW_OPTIONS:
                b = tk.Button(row, text=s, font=("Segoe UI",9,"bold"), bg=C["BORDER"], fg=C["TEXT"],
                              relief="flat", cursor="hand2", padx=12, pady=4, bd=0,
                              command=lambda s=s: self._sel_stw(s))
                b.pack(side="left", padx=3); self._stw_btns[s] = b
            self._sel_stw(self.stw_var.get())
            tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

            tk.Label(body, text="Fahrtart", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
            self.fahrt_var = tk.StringVar(value=(self.existing or {}).get("fahrt", FAHRT_OPTIONS[0]))
            fr = tk.Frame(body, bg=C["BG"]); fr.pack(anchor="w", pady=4)
            self._fahrt_btns = {}
            for s in FAHRT_OPTIONS:
                b = tk.Button(fr, text=s, font=("Segoe UI",8,"bold"), bg=C["BORDER"], fg=C["TEXT"],
                              relief="flat", cursor="hand2", padx=8, pady=3, bd=0,
                              command=lambda s=s: self._sel_fahrt(s))
                b.pack(side="left", padx=2); self._fahrt_btns[s] = b
            self._sel_fahrt(self.fahrt_var.get())
            tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

            tk.Label(body, text="Gleis", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
            self.gleis = tk.Entry(body, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                                  insertbackground=C["TEXT"], highlightthickness=1,
                                  highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
            self.gleis.pack(fill="x", ipady=5, pady=4)
            if self.existing: self.gleis.insert(0, self.existing.get("gleis",""))
            tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

            tk.Label(body, text="Zugnummern (z.B. 1234,5678)", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
            self.zug = tk.Entry(body, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                                insertbackground=C["TEXT"], highlightthickness=1,
                                highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
            self.zug.pack(fill="x", ipady=5, pady=4)
            if self.existing: self.zug.insert(0, self.existing.get("zuege",""))
            tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        ps = tk.Frame(body, bg=C["BG"]); ps.pack(fill="x", pady=2)
        pl = tk.Frame(ps, bg=C["BG"]); pl.pack(side="left", fill="x", expand=True)
        tk.Label(pl, text="Priorität", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.prio_var = tk.StringVar(value=(self.existing or {}).get("prio","Mittel"))
        ttk.Combobox(pl, textvariable=self.prio_var, values=PRIO_OPTIONS,
                     state="readonly", font=FONT_INPUT, width=10).pack(anchor="w", pady=2)
        sl = tk.Frame(ps, bg=C["BG"]); sl.pack(side="left", fill="x", expand=True, padx=10)
        tk.Label(sl, text="Status", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.status_var = tk.StringVar(value=(self.existing or {}).get("status","Offen"))
        ttk.Combobox(sl, textvariable=self.status_var, values=STATUS_OPTIONS,
                     state="readonly", font=FONT_INPUT, width=14).pack(anchor="w", pady=2)
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        tk.Label(body, text="Notiz", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        wrap = tk.Frame(body, bg=C["BORDER"]); wrap.pack(fill="both", expand=True, pady=4)
        self.note = tk.Text(wrap, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                            insertbackground=C["TEXT"], wrap="word", height=5, padx=6, pady=6)
        self.note.pack(fill="both", expand=True, padx=1, pady=1)
        if self.existing: self.note.insert("1.0", self.existing.get("notiz",""))

        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        br = tk.Frame(body, bg=C["BG"]); br.pack(fill="x")
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Bestätigen  ", self._confirm).pack(side="right")

    def _sel_stw(self, s):
        self.stw_var.set(s)
        for k,b in self._stw_btns.items():
            b.configure(bg=C["PRIMARY"] if k==s else C["BORDER"], fg="white" if k==s else C["TEXT"])

    def _sel_fahrt(self, s):
        self.fahrt_var.set(s)
        for k,b in self._fahrt_btns.items():
            b.configure(bg=C["PRIMARY"] if k==s else C["BORDER"], fg="white" if k==s else C["TEXT"])

    def _confirm(self):
        notiz = self.note.get("1.0","end").strip()
        if not notiz:
            messagebox.showwarning("Fehler","Bitte Notiz eingeben.",parent=self); return
        data = {"notiz":notiz,"prio":self.prio_var.get(),"status":self.status_var.get(),
                "ts": self.existing.get("ts",now_str()) if self.existing else now_str(),
                "ts_edit": now_str()}
        if not self.tf_mode:
            zuege = self.zug.get().strip()
            if not zuege:
                messagebox.showwarning("Fehler","Bitte Zugnummer eingeben.",parent=self); return
            data["stw"]   = self.stw_var.get()
            data["zuege"] = zuege
            data["fahrt"] = self.fahrt_var.get()
            data["gleis"] = self.gleis.get().strip()
        if self.existing: data["id"] = self.existing.get("id",0)
        self.on_confirm(data); self.destroy()

# ── Basis-Tab ─────────────────────────────────────────────────────────────────
class BaseTab(tk.Frame):
    def __init__(self, parent, data_path, tf_mode=False):
        super().__init__(parent, bg=C["BG"])
        self.data_path = data_path
        self.tf_mode   = tf_mode
        self.notes     = load_json(data_path)
        self._filter   = None
        self._id_ctr   = max((n.get("id",0) for n in self.notes), default=0)+1
        do_backup(data_path)
        self._build_toolbar()
        self._build_table()
        self._refresh()

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=10)
        make_btn(tb, "+  Hinzufügen", self._open_add, pady=7).pack(side="left")

        if not self.tf_mode:
            tk.Label(tb, text="Filter:", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(side="left", padx=10)
            self._fbtns = {}
            for s in ["Alle"]+STW_OPTIONS:
                b = tk.Button(tb, text=s, font=("Segoe UI",9,"bold"), bg=C["BORDER"], fg=C["TEXT"],
                              relief="flat", cursor="hand2", padx=10, pady=4, bd=0,
                              command=lambda s=s: self._apply_filter(s))
                b.pack(side="left", padx=3); self._fbtns[s] = b
            self._apply_filter("Alle", init=True)

        tk.Label(tb, text="Suche:", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(side="left", padx=10)
        self._sv = tk.StringVar(); self._sv.trace("w", lambda *a: self._refresh())
        tk.Entry(tb, textvariable=self._sv, font=FONT_INPUT, relief="flat",
                 bg=C["PANEL"], fg=C["TEXT"], insertbackground=C["TEXT"],
                 highlightthickness=1, highlightbackground=C["BORDER"],
                 highlightcolor=C["PRIMARY"], width=20).pack(side="left", ipady=4)
        make_btn(tb, "CSV",     self._export_csv, bg="#557755", pady=7).pack(side="right", padx=4)
        make_btn(tb, "Drucken", self._print,       bg="#557799", pady=7).pack(side="right", padx=4)

    def _build_table(self):
        outer = tk.Frame(self, bg=C["BG"]); outer.pack(fill="both", expand=True, padx=16, pady=8)
        cols = ["#","STW","Gleis","Fahrt","Züge","Notiz","Prio","Status","Erstellt",""] if not self.tf_mode \
               else ["#","Notiz","Prio","Status","Erstellt",""]
        widths = {"#":3,"STW":6,"Gleis":6,"Fahrt":10,"Züge":14,"Notiz":0,
                  "Prio":7,"Status":12,"Erstellt":14,"":5}
        hdr = tk.Frame(outer, bg=C["PRIMARY"]); hdr.pack(fill="x")
        for col in cols:
            w = widths.get(col,0); exp = col=="Notiz"
            lbl = tk.Label(hdr, text=col, font=("Segoe UI",9,"bold"),
                           bg=C["PRIMARY"], fg="white", anchor="w", pady=8, padx=8)
            if w: lbl.configure(width=w)
            lbl.pack(side="left", fill="x" if exp else "none", expand=exp)

        sc = tk.Frame(outer, bg=C["BG"]); sc.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(sc, bg=C["BG"], highlightthickness=0)
        sb = tk.Scrollbar(sc, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self.canvas.pack(side="left", fill="both", expand=True)
        self.rf = tk.Frame(self.canvas, bg=C["BG"])
        self._cw = self.canvas.create_window((0,0), window=self.rf, anchor="nw")
        self.rf.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._cw, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    def _refresh(self):
        for w in self.rf.winfo_children(): w.destroy()
        q = self._sv.get().lower() if hasattr(self,"_sv") else ""
        display = [n for n in self.notes
                   if (self._filter is None or n.get("stw")==self._filter) and
                      (not q or q in n.get("zuege","").lower() or q in n.get("notiz","").lower()
                       or q in n.get("gleis","").lower())]
        if not display:
            tk.Label(self.rf, text="Keine Notizen gefunden.", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=40); return
        for i, note in enumerate(display):
            orig = self.notes.index(note)
            rbg  = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
            status = note.get("status","Offen"); prio = note.get("prio","Mittel")
            row = tk.Frame(self.rf, bg=rbg, highlightthickness=1, highlightbackground=C["BORDER"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=str(i+1), font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     width=3, anchor="w").pack(side="left", padx=8, pady=8)
            if not self.tf_mode:
                tk.Label(row, text=note.get("stw",""), font=("Segoe UI",8,"bold"),
                         bg=C["PRIMARY"], fg="white", padx=6, pady=2).pack(side="left", padx=6, pady=8)
                tk.Label(row, text=note.get("gleis",""), font=FONT_TABLE,
                         bg=rbg, fg=C["TEXT"], width=6, anchor="w").pack(side="left", padx=4, pady=8)
                tk.Label(row, text=note.get("fahrt",""), font=FONT_TABLE,
                         bg=rbg, fg=C["TEXT"], width=10, anchor="w").pack(side="left", padx=4, pady=8)
                tk.Label(row, text=note.get("zuege",""), font=FONT_TABLE,
                         bg=rbg, fg=C["TEXT"], width=14, anchor="w").pack(side="left", padx=4, pady=8)
            tk.Label(row, text=note.get("notiz",""), font=FONT_TABLE, bg=rbg, fg=C["TEXT"],
                     anchor="w", wraplength=400, justify="left").pack(side="left", fill="x", expand=True, padx=6, pady=8)
            tk.Label(row, text=prio, font=("Segoe UI",8,"bold"),
                     bg=PRIO_COLORS.get(prio,"#888"), fg="white", padx=6, pady=2).pack(side="left", padx=4, pady=8)
            tk.Label(row, text=status, font=("Segoe UI",8,"bold"),
                     bg=STATUS_COLORS.get(status,"#888"), fg="white", padx=6, pady=2).pack(side="left", padx=4, pady=8)
            tk.Label(row, text=note.get("ts",""), font=("Segoe UI",8),
                     bg=rbg, fg=C["SUBTEXT"], width=14).pack(side="left", padx=4, pady=8)
            e = tk.Label(row, text=" ✎ ", font=("Segoe UI",11), bg=rbg, fg="#4488CC", cursor="hand2")
            e.pack(side="right", padx=4, pady=8)
            e.bind("<Button-1>", lambda ev, idx=orig, n=note: self._edit(idx, n))
            d = tk.Label(row, text=" X ", font=("Segoe UI",11,"bold"), bg=rbg, fg=C["DANGER"], cursor="hand2")
            d.pack(side="right", padx=6, pady=8)
            d.bind("<Button-1>", lambda ev, idx=orig, n=note: self._delete(idx, n))
            d.bind("<Enter>", lambda ev, l=d: l.configure(fg="#A00000"))
            d.bind("<Leave>", lambda ev, l=d: l.configure(fg=C["DANGER"]))

    def _apply_filter(self, stw, init=False):
        self._filter = None if stw=="Alle" else stw
        for s,b in self._fbtns.items():
            b.configure(bg=C["PRIMARY"] if s==stw else C["BORDER"],
                        fg="white" if s==stw else C["TEXT"])
        if not init: self._refresh()

    def _open_add(self):
        NotePopup(self.winfo_toplevel(), self._add, tf_mode=self.tf_mode)

    def _add(self, data):
        data["id"] = self._id_ctr; self._id_ctr += 1
        self.notes.append(data); save_json(self.data_path, self.notes); self._refresh()

    def _edit(self, idx, note):
        def apply(data):
            self.notes[idx] = data; save_json(self.data_path, self.notes); self._refresh()
        NotePopup(self.winfo_toplevel(), apply, existing=note, tf_mode=self.tf_mode)

    def _delete(self, idx, note):
        if messagebox.askyesno("Löschen?", f"Notiz wirklich löschen?\n\n\"{note.get('notiz','')[:60]}\"", parent=self):
            self.notes.pop(idx); save_json(self.data_path, self.notes); self._refresh()

    def _export_csv(self):
        base = os.path.dirname(self.data_path)
        path = os.path.join(base, f"export_{datetime.date.today().isoformat()}.csv")
        cols = (["stw","gleis","fahrt","zuege","notiz","prio","status","ts"] if not self.tf_mode
                else ["notiz","prio","status","ts"])
        with open(path,"w",newline="",encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader(); w.writerows(self.notes)
        messagebox.showinfo("Export", f"CSV gespeichert:\n{path}", parent=self)

    def _print(self):
        lines = []
        for n in self.notes:
            if not self.tf_mode:
                lines.append(f"[{n.get('stw','')}] Gl.{n.get('gleis','')} {n.get('fahrt','')} Zug:{n.get('zuege','')}")
            lines.append(f"  {n.get('notiz','')}  | {n.get('prio','')} | {n.get('status','')} | {n.get('ts','')}")
            lines.append("")
        tmp = tempfile.NamedTemporaryFile(delete=False,suffix=".txt",mode="w",encoding="utf-8")
        tmp.write("\n".join(lines)); tmp.close()
        try:
            if platform.system()=="Windows": os.startfile(tmp.name,"print")
            else: subprocess.call(["lpr",tmp.name])
        except Exception as ex:
            messagebox.showinfo("Drucken",f"Fehler:\n{ex}",parent=self)

# ── Tabs ──────────────────────────────────────────────────────────────────────
class STWTab(BaseTab):
    def __init__(self, parent): super().__init__(parent, DATA_FILE, tf_mode=False)

class TFTab(BaseTab):
    def __init__(self, parent): super().__init__(parent, TF_FILE, tf_mode=True)

# ── Haupt-App ─────────────────────────────────────────────────────────────────
class NotizenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stellwerk Notizen")
        self.geometry("1100x700")
        self.minsize(800,520)
        self.configure(bg=C["BG"])
        self._dark = False
        self._always_top = False
        self._build_header()
        self._build_tabs()

    def _build_header(self):
        self._hdr = tk.Frame(self, bg=C["PRIMARY"]); self._hdr.pack(fill="x")
        tk.Label(self._hdr, text="Stellwerk Notizen", font=("Segoe UI",15,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(side="left", padx=20, pady=14)
        self._top_btn = tk.Button(self._hdr, text="📌 Vorne", font=("Segoe UI",9),
                                   bg=C["PRIMARY_H"], fg="white", relief="flat", cursor="hand2",
                                   padx=10, pady=6, bd=0, command=self._toggle_top)
        self._top_btn.pack(side="right", padx=6, pady=10)
        self._dm_btn = tk.Button(self._hdr, text="🌙 Dunkel", font=("Segoe UI",9),
                                  bg=C["PRIMARY_H"], fg="white", relief="flat", cursor="hand2",
                                  padx=10, pady=6, bd=0, command=self._toggle_dark)
        self._dm_btn.pack(side="right", padx=6, pady=10)
        tk.Button(self._hdr, text="🔄 Update", font=("Segoe UI",9),
                  bg=C["PRIMARY_H"], fg="white", relief="flat", cursor="hand2",
                  padx=10, pady=6, bd=0,
                  command=lambda: check_for_update(self, silent=False)
                  ).pack(side="right", padx=2, pady=10)

    def _build_tabs(self):
        self._tab_bar = tk.Frame(self, bg=C["BG"]); self._tab_bar.pack(fill="x", padx=16, pady=(8,0))
        self._tab_content = tk.Frame(self, bg=C["BG"]); self._tab_content.pack(fill="both", expand=True)
        self._tabs = {}; self._tab_btns = {}
        for name, cls in [("Stellwerksnotizen", STWTab), ("TF Notizen", TFTab)]:
            frame = cls(self._tab_content); self._tabs[name] = frame
            btn = tk.Button(self._tab_bar, text=name, font=("Segoe UI",10,"bold"),
                            bg=C["PRIMARY"], fg="white", relief="flat", cursor="hand2",
                            padx=18, pady=8, bd=0, command=lambda n=name: self._switch(n))
            btn.pack(side="left", padx=4); self._tab_btns[name] = btn
        self._switch("Stellwerksnotizen")

    def _switch(self, name):
        for f in self._tabs.values(): f.pack_forget()
        self._tabs[name].pack(fill="both", expand=True)
        for n,b in self._tab_btns.items():
            b.configure(bg=C["PRIMARY"] if n==name else C["BORDER"],
                        fg="white" if n==name else C["TEXT"])

    def _toggle_dark(self):
        self._dark = not self._dark
        C.update(DARK if self._dark else LIGHT)
        self._dm_btn.configure(text="☀ Hell" if self._dark else "🌙 Dunkel")
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=C["BG"])
        self._build_header(); self._build_tabs()

    def _toggle_top(self):
        self._always_top = not self._always_top
        self.attributes("-topmost", self._always_top)
        self._top_btn.configure(text="📌 Vorne ✓" if self._always_top else "📌 Vorne",
                                bg="#8B0000" if self._always_top else C["PRIMARY_H"])

if __name__ == "__main__":
    app = NotizenApp()
    sb = tk.Frame(app, bg=C["BORDER"], height=22); sb.pack(fill="x", side="bottom")
    tk.Label(sb, text=f"v{APP_VERSION}", font=("Segoe UI",8),
             bg=C["BORDER"], fg=C["SUBTEXT"]).pack(side="right", padx=10)
    app.after(2000, lambda: check_for_update(app, silent=True))
    app.mainloop()
