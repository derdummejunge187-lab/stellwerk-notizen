import tkinter as tk
from tkinter import messagebox, ttk
import json, os, shutil, csv, datetime, subprocess, platform, tempfile
import threading, urllib.request, ssl, sys

# ══════════════════════════════════════════════════════════════════════════════
APP_VERSION  = "1.1.0"
GITHUB_USER  = "derdummejunge187-lab"
GITHUB_REPO  = "stellwerk-notizen"
EXE_NAME     = "StellwerkNotizen.exe"
VERSION_URL  = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
DOWNLOAD_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/notizen_app.py"
EXE_DOWNLOAD_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{EXE_NAME}"
# ══════════════════════════════════════════════════════════════════════════════

CHANGELOG = [
    ("v1.1.1", "2026-06 14:30 Uhr", [
        "Einstellungen-Tab hinzugefuegt (Stellwerke, Dark Mode, Update, Changelog)",
        "Stellwerke fuer Notizen-Auswahl sind jetzt konfigurierbar (bis zu 10)",
        "Hell/Dunkel-Modus wird gespeichert und beim Start wiederhergestellt",
        "Bestaetigen-Button im Notiz-Dialog funktioniert jetzt korrekt",
        "Filterleiste passt sich automatisch an konfigurierte Stellwerke an",
        "Neuer Tab 'Fahrtenliste': Fahrten mit Start/Ziel, Abfahrt/Ankunft und Fahrtart erfassen",
        "Automatische Berechnung von reiner Fahrtzeit und Pausenzeit ab 2 erfassten Fahrten",
        "Fahrten koennen manuell als erledigt markiert werden, inkl. kurzer Dokumentation",
        "Neuer Button 'Aktuelle Fahrt' springt zur naechsten noch offenen Fahrt",
        "Auto-Update laedt bei kompilierten .exe-Versionen die neue .exe direkt von GitHub "
        "und ersetzt die laufende Version automatisch (mit Neustart)",
        "fix: Fehler beim Editieren von Notizen behoben, die zu Datenverlust fuehren konnten",
    ]),
    ("v1.0.0", "2026-06 13 Uhr", [
        "Erste Version der Stellwerk-Notizen App",
        "Stellwerksnotizen und TF-Notizen Tabs",
        "CSV-Export, Drucken, Backup-Funktion",
        "Auto-Updater via GitHub",
        "Hell/Dunkel-Modus",
    ]),
]

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

DEFAULT_STW_OPTIONS = ["BHBF", "NS", "AK", "STB"]
FAHRT_OPTIONS  = ["Zugfahrt", "Rangierfahrt", "Gastfahrt", "Leerfahrt"]
STATUS_OPTIONS = ["Offen", "In Bearbeitung", "Erledigt"]
STATUS_COLORS  = {"Offen":"#E74C3C","In Bearbeitung":"#F39C12","Erledigt":"#27AE60"}
PRIO_OPTIONS   = ["Hoch", "Mittel", "Niedrig"]
PRIO_COLORS    = {"Hoch":"#C0392B","Mittel":"#E67E22","Niedrig":"#27AE60"}

BASE_DIR      = os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__))
DATA_FILE     = os.path.join(BASE_DIR, "notizen_data.json")
TF_FILE       = os.path.join(BASE_DIR, "tf_data.json")
FAHRTEN_FILE  = os.path.join(BASE_DIR, "fahrten_data.json")
BACKUP_DIR    = os.path.join(BASE_DIR, "backups")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"dark_mode": False, "stw_options": list(DEFAULT_STW_OPTIONS)}

def save_settings(s):
    with open(SETTINGS_FILE,"w",encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

SETTINGS = load_settings()
STW_OPTIONS = list(SETTINGS.get("stw_options", DEFAULT_STW_OPTIONS))

if SETTINGS.get("dark_mode", False):
    C.update(DARK)


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path,"r",encoding="utf-8") as f: return json.load(f)
        except:
            pass
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

def parse_hhmm(s):
    try:
        h, m = s.strip().split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return datetime.time(h, m)
    except Exception:
        pass
    return None

def minutes_between(t_start, t_end):
    d1 = datetime.datetime.combine(datetime.date.today(), t_start)
    d2 = datetime.datetime.combine(datetime.date.today(), t_end)
    if d2 <= d1:
        d2 += datetime.timedelta(days=1)
    return int((d2 - d1).total_seconds() // 60)

def fmt_minutes(m):
    h, r = divmod(int(m), 60)
    return f"{h}h {r:02d}min" if h else f"{r}min"

def make_btn(parent, text, command, bg=None, fg="white", padx=14, pady=6):
    if bg is None: bg = C["PRIMARY"]
    btn = tk.Button(parent, text=text, command=command, bg=bg, fg=fg, font=FONT_BTN,
                    relief="flat", cursor="hand2", padx=padx, pady=pady,
                    activebackground=C["PRIMARY_H"], activeforeground="white", bd=0)
    hover = C["PRIMARY_H"] if bg == C["PRIMARY"] else "#BB9999"
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
    btn.bind("<Leave>", lambda e: btn.configure(bg=bg))
    return btn


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
        win.title("Update verfuegbar")
        win.resizable(False, False)
        win.configure(bg=C["BG"])
        win.grab_set()
        win.geometry("380x190")
        hf = tk.Frame(win, bg=C["PRIMARY"]); hf.pack(fill="x")
        tk.Label(hf, text="Update verfuegbar", font=("Segoe UI",12,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(padx=16, pady=12)
        tk.Label(win, text=f"Installiert:  v{APP_VERSION}\nVerfuegbar:   v{remote}",
                 font=("Segoe UI",11), bg=C["BG"], fg=C["TEXT"], justify="left").pack(padx=24, pady=16)
        bf = tk.Frame(win, bg=C["BG"]); bf.pack(pady=8)
        make_btn(bf, "Jetzt updaten", lambda: _do_update(win, remote)).pack(side="left", padx=8)
        make_btn(bf, "Spaeter", win.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="left")

    def _do_update(win, remote):
        is_frozen = getattr(sys, 'frozen', False)
        base = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
        try:
            if is_frozen:
                if platform.system() != "Windows":
                    messagebox.showerror("Update fehlgeschlagen",
                        "Automatisches Ersetzen der .exe wird nur unter Windows unterstuetzt.",
                        parent=parent)
                    return
                current_exe = os.path.abspath(sys.executable)
                new_exe     = os.path.join(base, "_update_new.exe")
                with _https_get(EXE_DOWNLOAD_URL, timeout=60) as r:
                    new_data = r.read()
                with open(new_exe, "wb") as f:
                    f.write(new_data)
                pid = os.getpid()
                bat_path = os.path.join(base, "_apply_update.bat")
                bat_content = (
                    "@echo off\r\n"
                    ":wait\r\n"
                    f"tasklist /FI \"PID eq {pid}\" 2>NUL | findstr \"{pid}\" >NUL\r\n"
                    "if not errorlevel 1 (\r\n"
                    "    timeout /t 1 /nobreak >NUL\r\n"
                    "    goto wait\r\n"
                    ")\r\n"
                    f"move /Y \"{new_exe}\" \"{current_exe}\" >NUL\r\n"
                    f"start \"\" \"{current_exe}\"\r\n"
                    "del \"%~f0\"\r\n"
                )
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                subprocess.Popen(["cmd", "/c", bat_path], cwd=base,
                                  creationflags=subprocess.CREATE_NEW_CONSOLE)
                win.destroy()
                messagebox.showinfo("Update",
                    f"v{remote} wird installiert.\nDie Anwendung schliesst sich jetzt "
                    f"und startet automatisch mit der neuen Version neu.",
                    parent=parent)
                parent.after(300, lambda: os._exit(0))
            else:
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


class NotePopup(tk.Toplevel):
    def __init__(self, parent, on_confirm, existing=None, tf_mode=False):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.existing   = existing
        self.tf_mode    = tf_mode
        self.title("Notiz bearbeiten" if existing else "Neue Notiz")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.withdraw()
        self._build()
        self.update_idletasks()
        w = 420
        h = min(self.winfo_reqheight() + 10, self.winfo_screenheight() - 80)
        h = max(h, 380)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify()
        self.grab_set()

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
            self.stw_var = tk.StringVar(value=(self.existing or {}).get("stw", STW_OPTIONS[0] if STW_OPTIONS else ""))
            row = tk.Frame(body, bg=C["BG"]); row.pack(anchor="w", pady=4)
            self._stw_btns = {}
            for s in STW_OPTIONS:
                b = tk.Button(row, text=s, font=("Segoe UI",9,"bold"), bg=C["BORDER"], fg=C["TEXT"],
                              relief="flat", cursor="hand2", padx=12, pady=4, bd=0,
                              command=lambda s=s: self._sel_stw(s))
                b.pack(side="left", padx=3)
                self._stw_btns[s] = b
            if STW_OPTIONS:
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
                b.pack(side="left", padx=2)
                self._fahrt_btns[s] = b
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
        tk.Label(pl, text="Prioritaet", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
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
        make_btn(br, "  Bestaetigen  ", self._confirm).pack(side="right")

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
        self.on_confirm(data)
        self.destroy()


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
        make_btn(tb, "+  Hinzufuegen", self._open_add, pady=7).pack(side="left")

        if not self.tf_mode:
            tk.Label(tb, text="Filter:", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(side="left", padx=10)
            self._fbtns = {}
            for s in ["Alle"]+STW_OPTIONS:
                b = tk.Button(tb, text=s, font=("Segoe UI",9,"bold"), bg=C["BORDER"], fg=C["TEXT"],
                              relief="flat", cursor="hand2", padx=10, pady=4, bd=0,
                              command=lambda s=s: self._apply_filter(s))
                b.pack(side="left", padx=3)
                self._fbtns[s] = b
            self._apply_filter("Alle", init=True)

        tk.Label(tb, text="Suche:", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(side="left", padx=10)
        self._sv = tk.StringVar(); self._sv.trace("w", lambda *a: self._refresh())
        tk.Entry(tb, textvariable=self._sv, font=FONT_INPUT, relief="flat",
                 bg=C["PANEL"], fg=C["TEXT"], insertbackground=C["TEXT"],
                 highlightthickness=1, highlightbackground=C["BORDER"],
                 highlightcolor=C["PRIMARY"], width=20).pack(side="left", ipady=4)
        make_btn(tb, "CSV",      self._export_csv, bg="#557755", pady=7).pack(side="right", padx=4)
        make_btn(tb, "Drucken",  self._print,      bg="#557799", pady=7).pack(side="right", padx=4)

    def _build_table(self):
        outer = tk.Frame(self, bg=C["BG"]); outer.pack(fill="both", expand=True, padx=16, pady=8)
        cols = ["#","STW","Gleis","Fahrt","Zuege","Notiz","Prio","Status","Erstellt",""] if not self.tf_mode \
               else ["#","Notiz","Prio","Status","Erstellt",""]
        widths = {"#":3,"STW":6,"Gleis":6,"Fahrt":10,"Zuege":14,"Notiz":0,
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
        if messagebox.askyesno("Loeschen?", f"Notiz wirklich loeschen?\n\n\"{note.get('notiz','')[:60]}\"", parent=self):
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


class FahrtPopup(tk.Toplevel):
    def __init__(self, parent, on_confirm, existing=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.existing   = existing
        self.title("Fahrt bearbeiten" if existing else "Neue Fahrt")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.withdraw()
        self._build()
        self.update_idletasks()
        w = 400
        h = min(self.winfo_reqheight() + 10, self.winfo_screenheight() - 80)
        h = max(h, 320)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify()
        self.grab_set()

    def _entry(self, parent, label, value=""):
        tk.Label(parent, text=label, font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        e = tk.Entry(parent, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                     insertbackground=C["TEXT"], highlightthickness=1,
                     highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        e.pack(fill="x", ipady=5, pady=4)
        if value: e.insert(0, value)
        return e

    def _build(self):
        hdr = tk.Frame(self, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text="Fahrt bearbeiten" if self.existing else "Neue Fahrt",
                 font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"),
                     bg=C["PRIMARY"], fg="white", cursor="hand2"); x.pack(side="right", padx=8)
        x.bind("<Button-1>", lambda e: self.destroy())

        body = tk.Frame(self, bg=C["BG"]); body.pack(fill="both", expand=True, padx=20, pady=14)
        ex = self.existing or {}

        self.start_e = self._entry(body, "Startbahnhof", ex.get("start",""))
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        self.ziel_e = self._entry(body, "Endbahnhof", ex.get("ziel",""))
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        zr = tk.Frame(body, bg=C["BG"]); zr.pack(fill="x")
        zl = tk.Frame(zr, bg=C["BG"]); zl.pack(side="left", fill="x", expand=True)
        self.ab_e = self._entry(zl, "Abfahrt (HH:MM)", ex.get("abfahrt",""))
        zr2 = tk.Frame(zr, bg=C["BG"]); zr2.pack(side="left", fill="x", expand=True, padx=(10,0))
        self.an_e = self._entry(zr2, "Ankunft (HH:MM)", ex.get("ankunft",""))
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        tk.Label(body, text="Fahrtart", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.fahrt_var = tk.StringVar(value=ex.get("fahrt", FAHRT_OPTIONS[0]))
        fr = tk.Frame(body, bg=C["BG"]); fr.pack(anchor="w", pady=4)
        self._fahrt_btns = {}
        for s in FAHRT_OPTIONS:
            b = tk.Button(fr, text=s, font=("Segoe UI",8,"bold"), bg=C["BORDER"], fg=C["TEXT"],
                          relief="flat", cursor="hand2", padx=8, pady=3, bd=0,
                          command=lambda s=s: self._sel_fahrt(s))
            b.pack(side="left", padx=2)
            self._fahrt_btns[s] = b
        self._sel_fahrt(self.fahrt_var.get())

        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=10)
        br = tk.Frame(body, bg=C["BG"]); br.pack(fill="x")
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Bestaetigen  ", self._confirm).pack(side="right")

    def _sel_fahrt(self, s):
        self.fahrt_var.set(s)
        for k,b in self._fahrt_btns.items():
            b.configure(bg=C["PRIMARY"] if k==s else C["BORDER"], fg="white" if k==s else C["TEXT"])

    def _confirm(self):
        start = self.start_e.get().strip()
        ziel  = self.ziel_e.get().strip()
        ab    = self.ab_e.get().strip()
        an    = self.an_e.get().strip()
        if not start or not ziel:
            messagebox.showwarning("Fehler","Bitte Start- und Endbahnhof eingeben.",parent=self); return
        if parse_hhmm(ab) is None or parse_hhmm(an) is None:
            messagebox.showwarning("Fehler","Bitte Abfahrt/Ankunft im Format HH:MM eingeben.",parent=self); return
        ex = self.existing or {}
        data = {
            "start": start, "ziel": ziel, "abfahrt": ab, "ankunft": an,
            "fahrt": self.fahrt_var.get(),
            "erledigt": ex.get("erledigt", False),
            "doku": ex.get("doku",""),
            "ts": ex.get("ts", now_str()) if self.existing else now_str(),
            "ts_edit": now_str(),
        }
        if self.existing: data["id"] = ex.get("id",0)
        self.on_confirm(data)
        self.destroy()


class DokuPopup(tk.Toplevel):
    def __init__(self, parent, on_confirm, fahrt):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.title("Fahrt abschliessen")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.withdraw()

        hdr = tk.Frame(self, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text="Fahrt abschliessen", font=("Segoe UI",12,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"),
                     bg=C["PRIMARY"], fg="white", cursor="hand2"); x.pack(side="right", padx=8)
        x.bind("<Button-1>", lambda e: self.destroy())

        body = tk.Frame(self, bg=C["BG"]); body.pack(fill="both", expand=True, padx=20, pady=14)
        tk.Label(body, text=f"{fahrt.get('start','')}  →  {fahrt.get('ziel','')}",
                 font=("Segoe UI",11,"bold"), bg=C["BG"], fg=C["TEXT"]).pack(anchor="w")
        tk.Label(body, text=f"{fahrt.get('abfahrt','')} - {fahrt.get('ankunft','')}  |  {fahrt.get('fahrt','')}",
                 font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", pady=(0,8))

        tk.Label(body, text="Kurze Dokumentation", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        wrap = tk.Frame(body, bg=C["BORDER"]); wrap.pack(fill="both", expand=True, pady=4)
        self.doku = tk.Text(wrap, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                            insertbackground=C["TEXT"], wrap="word", height=5, padx=6, pady=6)
        self.doku.pack(fill="both", expand=True, padx=1, pady=1)

        br = tk.Frame(body, bg=C["BG"]); br.pack(fill="x", pady=(10,0))
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Als erledigt markieren  ", self._confirm).pack(side="right")

        self.update_idletasks()
        w = 400
        h = min(self.winfo_reqheight() + 10, self.winfo_screenheight() - 80)
        h = max(h, 280)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify()
        self.grab_set()

    def _confirm(self):
        text = self.doku.get("1.0","end").strip()
        if not text:
            messagebox.showwarning("Fehler","Bitte kurze Dokumentation eingeben.",parent=self); return
        self.on_confirm(text)
        self.destroy()


class FahrtenTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self.data_path = FAHRTEN_FILE
        self.fahrten   = load_json(FAHRTEN_FILE)
        self._id_ctr   = max((f.get("id",0) for f in self.fahrten), default=0)+1
        self._row_frames = {}
        do_backup(FAHRTEN_FILE)
        self._build_toolbar()
        self._build_summary()
        self._build_list()
        self._refresh()

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=10)
        make_btn(tb, "+  Fahrt hinzufuegen", self._open_add, pady=7).pack(side="left")
        make_btn(tb, "▶  Aktuelle Fahrt", self._jump_current, bg="#557799", pady=7).pack(side="left", padx=8)

    def _build_summary(self):
        self.summary_frame = tk.Frame(self, bg=C["PANEL"], highlightthickness=1, highlightbackground=C["BORDER"])
        self.summary_lbl = tk.Label(self.summary_frame, text="", font=("Segoe UI",10,"bold"),
                                     bg=C["PANEL"], fg=C["TEXT"], anchor="w", padx=12, pady=8)
        self.summary_lbl.pack(fill="x")

    def _build_list(self):
        self.outer = tk.Frame(self, bg=C["BG"]); self.outer.pack(fill="both", expand=True, padx=16, pady=8)
        self.canvas = tk.Canvas(self.outer, bg=C["BG"], highlightthickness=0)
        sb = tk.Scrollbar(self.outer, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self.canvas.pack(side="left", fill="both", expand=True)
        self.rf = tk.Frame(self.canvas, bg=C["BG"])
        self._cw = self.canvas.create_window((0,0), window=self.rf, anchor="nw")
        self.rf.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self._cw, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    def _sorted(self):
        return sorted(self.fahrten, key=lambda f: f.get("abfahrt","99:99"))

    def _current_fahrt(self):
        for f in self._sorted():
            if not f.get("erledigt"):
                return f
        return None

    def _refresh(self):
        for w in self.rf.winfo_children(): w.destroy()
        self._row_frames = {}
        ordered = self._sorted()
        if not ordered:
            tk.Label(self.rf, text="Keine Fahrten erfasst.", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=40)
        else:
            current = self._current_fahrt()
            for i, f in enumerate(ordered):
                if i > 0:
                    t1 = parse_hhmm(ordered[i-1].get("ankunft",""))
                    t2 = parse_hhmm(f.get("abfahrt",""))
                    if t1 and t2:
                        pause = minutes_between(t1, t2)
                        pf = tk.Frame(self.rf, bg=C["BG"]); pf.pack(fill="x")
                        tk.Label(pf, text=f"⏸  Pause: {fmt_minutes(pause)}", font=("Segoe UI",8),
                                 bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", padx=20, pady=2)
                self._build_row(i, f, current is not None and f.get("id")==current.get("id"))
        if len(ordered) >= 2:
            self._update_summary(ordered)
            self.summary_frame.pack(fill="x", padx=16, pady=(0,8), before=self.outer)
        else:
            self.summary_frame.pack_forget()

    def _build_row(self, i, f, is_current):
        rbg = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
        erledigt = f.get("erledigt", False)
        border = C["PRIMARY"] if is_current else C["BORDER"]
        bw = 2 if is_current else 1
        row = tk.Frame(self.rf, bg=rbg, highlightthickness=bw, highlightbackground=border)
        row.pack(fill="x", pady=2)
        self._row_frames[f["id"]] = row

        top = tk.Frame(row, bg=rbg); top.pack(fill="x")
        if is_current:
            tk.Label(top, text="▶", font=("Segoe UI",10,"bold"), bg=rbg, fg=C["PRIMARY"]).pack(side="left", padx=(8,0), pady=8)
        tk.Label(top, text=f"{f.get('start','')}  →  {f.get('ziel','')}", font=("Segoe UI",10,"bold"),
                 bg=rbg, fg=C["TEXT"]).pack(side="left", padx=8, pady=8)
        tk.Label(top, text=f.get("fahrt",""), font=("Segoe UI",8,"bold"),
                 bg=C["PRIMARY"], fg="white", padx=6, pady=2).pack(side="left", padx=6)
        tk.Label(top, text=f"{f.get('abfahrt','')} - {f.get('ankunft','')}", font=FONT_TABLE,
                 bg=rbg, fg=C["TEXT"]).pack(side="left", padx=10)
        t1, t2 = parse_hhmm(f.get("abfahrt","")), parse_hhmm(f.get("ankunft",""))
        if t1 and t2:
            tk.Label(top, text=f"Fahrzeit: {fmt_minutes(minutes_between(t1,t2))}", font=FONT_TABLE,
                     bg=rbg, fg=C["SUBTEXT"]).pack(side="left", padx=10)
        status_txt = "Erledigt" if erledigt else "Offen"
        tk.Label(top, text=status_txt, font=("Segoe UI",8,"bold"),
                 bg=STATUS_COLORS.get(status_txt,"#888"), fg="white", padx=6, pady=2).pack(side="left", padx=6)

        actions = tk.Frame(top, bg=rbg); actions.pack(side="right")
        d = tk.Label(actions, text=" X ", font=("Segoe UI",11,"bold"), bg=rbg, fg=C["DANGER"], cursor="hand2")
        d.pack(side="right", padx=6, pady=8)
        d.bind("<Button-1>", lambda ev, ff=f: self._delete(ff))
        e = tk.Label(actions, text=" ✎ ", font=("Segoe UI",11), bg=rbg, fg="#4488CC", cursor="hand2")
        e.pack(side="right", padx=4, pady=8)
        e.bind("<Button-1>", lambda ev, ff=f: self._edit(ff))
        if not erledigt:
            ok = tk.Label(actions, text=" ✓ Erledigt ", font=("Segoe UI",9,"bold"), bg=rbg, fg="#27AE60", cursor="hand2")
            ok.pack(side="right", padx=4, pady=8)
            ok.bind("<Button-1>", lambda ev, ff=f: self._mark_done(ff))

        if erledigt and f.get("doku"):
            tk.Label(row, text=f"Doku: {f.get('doku')}", font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     anchor="w", wraplength=700, justify="left").pack(fill="x", padx=14, pady=(0,8))

    def _update_summary(self, ordered):
        total_fahr = 0
        total_pause = 0
        for f in ordered:
            t1, t2 = parse_hhmm(f.get("abfahrt","")), parse_hhmm(f.get("ankunft",""))
            if t1 and t2: total_fahr += minutes_between(t1, t2)
        for i in range(1, len(ordered)):
            t1 = parse_hhmm(ordered[i-1].get("ankunft",""))
            t2 = parse_hhmm(ordered[i].get("abfahrt",""))
            if t1 and t2: total_pause += minutes_between(t1, t2)
        self.summary_lbl.configure(
            text=f"{len(ordered)} Fahrten   |   Reine Fahrtzeit: {fmt_minutes(total_fahr)}   |   "
                 f"Pausenzeit: {fmt_minutes(total_pause)}   |   Gesamtzeit: {fmt_minutes(total_fahr+total_pause)}")

    def _open_add(self):
        FahrtPopup(self.winfo_toplevel(), self._add)

    def _add(self, data):
        data["id"] = self._id_ctr; self._id_ctr += 1
        self.fahrten.append(data); save_json(self.data_path, self.fahrten); self._refresh()

    def _edit(self, fahrt):
        def apply(data):
            for i, ff in enumerate(self.fahrten):
                if ff.get("id") == fahrt.get("id"):
                    self.fahrten[i] = data; break
            save_json(self.data_path, self.fahrten); self._refresh()
        FahrtPopup(self.winfo_toplevel(), apply, existing=fahrt)

    def _delete(self, fahrt):
        if messagebox.askyesno("Loeschen?",
                f"Fahrt {fahrt.get('start','')} -> {fahrt.get('ziel','')} wirklich loeschen?", parent=self):
            self.fahrten = [f for f in self.fahrten if f.get("id") != fahrt.get("id")]
            save_json(self.data_path, self.fahrten); self._refresh()

    def _mark_done(self, fahrt):
        def apply(doku_text):
            for ff in self.fahrten:
                if ff.get("id") == fahrt.get("id"):
                    ff["erledigt"] = True
                    ff["doku"] = doku_text
                    ff["ts_erledigt"] = now_str()
                    break
            save_json(self.data_path, self.fahrten); self._refresh()
        DokuPopup(self.winfo_toplevel(), apply, fahrt)

    def _jump_current(self):
        cur = self._current_fahrt()
        if cur is None:
            messagebox.showinfo("Aktuelle Fahrt", "Alle Fahrten sind erledigt.", parent=self)
            return
        row = self._row_frames.get(cur["id"])
        if row is None: return
        self.update_idletasks()
        bbox = self.canvas.bbox("all")
        if not bbox: return
        total_h = max(bbox[3]-bbox[1], 1)
        frac = max(0, (row.winfo_y()-10)/total_h)
        self.canvas.yview_moveto(frac)
        self._flash(row)

    def _flash(self, row):
        row.configure(highlightbackground="#FFD700", highlightthickness=3)
        self.after(900, lambda: row.configure(highlightbackground=C["PRIMARY"], highlightthickness=2))


class SettingsTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["BG"])
        self.app = app
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=C["BG"], highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=C["BG"])
        cw = canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        def section(parent, title):
            f = tk.Frame(parent, bg=C["PANEL"])
            f.pack(fill="x", padx=32, pady=8)
            tk.Label(f, text=f"  {title}", font=("Segoe UI",11,"bold"),
                     bg=C["PRIMARY"], fg="white").pack(fill="x")
            return f

        # ── Stellwerke ────────────────────────────────────────────────────────
        s1 = section(inner, "Stellwerke konfigurieren")
        tk.Label(s1, text="Bis zu 10 Stellwerke fuer die Auswahl beim Hinzufuegen (eines pro Zeile):",
                 font=FONT_LABEL, bg=C["PANEL"], fg=C["SUBTEXT"]).pack(anchor="w", padx=16, pady=(8,4))
        self.stw_text = tk.Text(s1, font=FONT_INPUT, relief="flat", bg=C["BG"], fg=C["TEXT"],
                                insertbackground=C["TEXT"], highlightthickness=1,
                                highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"],
                                height=10, padx=8, pady=6, width=28)
        self.stw_text.pack(padx=16, pady=4, anchor="w")
        self.stw_text.insert("1.0", "\n".join(STW_OPTIONS))
        self._stw_lbl = tk.Label(s1, text="", font=FONT_LABEL, bg=C["PANEL"], fg="#27AE60")
        self._stw_lbl.pack(anchor="w", padx=16)
        bf = tk.Frame(s1, bg=C["PANEL"]); bf.pack(anchor="w", padx=16, pady=(2,14))
        make_btn(bf, "Speichern", self._save_stw, pady=6).pack(side="left")
        make_btn(bf, "Zuruecksetzen", self._reset_stw, bg="#CCBBBB", fg=C["TEXT"], pady=6).pack(side="left", padx=8)

        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", padx=32, pady=2)

        # ── Darstellung ────────────────────────────────────────────────────────
        s2 = section(inner, "Darstellung")
        dm_row = tk.Frame(s2, bg=C["PANEL"]); dm_row.pack(anchor="w", padx=16, pady=10)
        tk.Label(dm_row, text="Dunkles Design:", font=FONT_INPUT, bg=C["PANEL"], fg=C["TEXT"]).pack(side="left")
        self._dm_var = tk.BooleanVar(value=SETTINGS.get("dark_mode", False))
        tk.Checkbutton(dm_row, variable=self._dm_var, command=self._toggle_dark,
                       bg=C["PANEL"], activebackground=C["PANEL"],
                       selectcolor=C["BG"], cursor="hand2").pack(side="left", padx=8)
        self._dm_lbl = tk.Label(dm_row,
                                text="Dunkel" if self._dm_var.get() else "Hell",
                                font=("Segoe UI",9,"bold"), bg=C["PANEL"], fg=C["PRIMARY"])
        self._dm_lbl.pack(side="left")
        tk.Frame(s2, bg=C["PANEL"], height=6).pack()

        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", padx=32, pady=2)

        # ── Update ─────────────────────────────────────────────────────────────
        s3 = section(inner, "Update")
        tk.Label(s3, text=f"Installierte Version: v{APP_VERSION}", font=FONT_INPUT,
                 bg=C["PANEL"], fg=C["TEXT"]).pack(anchor="w", padx=16, pady=(8,4))
        make_btn(s3, "Auf Updates pruefen",
                 lambda: check_for_update(self.app, silent=False), pady=6).pack(anchor="w", padx=16, pady=(0,14))

        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", padx=32, pady=2)

        # ── Changelog ─────────────────────────────────────────────────────────
        s4 = section(inner, "Changelog")
        tk.Frame(s4, bg=C["PANEL"], height=6).pack()
        for version, date, entries in CHANGELOG:
            vf = tk.Frame(s4, bg=C["BG"]); vf.pack(fill="x", padx=16, pady=4)
            hf = tk.Frame(vf, bg=C["PRIMARY"]); hf.pack(fill="x")
            tk.Label(hf, text=f"  {version}", font=("Segoe UI",10,"bold"),
                     bg=C["PRIMARY"], fg="white").pack(side="left", pady=6, padx=4)
            tk.Label(hf, text=date, font=("Segoe UI",9),
                     bg=C["PRIMARY"], fg="#FFCCCC").pack(side="right", pady=6, padx=10)
            for entry in entries:
                ef = tk.Frame(vf, bg=C["BG"]); ef.pack(fill="x")
                tk.Label(ef, text="*", font=FONT_TABLE, bg=C["BG"], fg=C["PRIMARY"]).pack(side="left", padx=(10,2), pady=2)
                tk.Label(ef, text=entry, font=FONT_TABLE, bg=C["BG"], fg=C["TEXT"],
                         anchor="w", justify="left").pack(side="left", pady=2)
        tk.Frame(s4, bg=C["PANEL"], height=14).pack()
        tk.Frame(inner, bg=C["BG"], height=24).pack()

    def _save_stw(self):
        global STW_OPTIONS
        raw = self.stw_text.get("1.0","end").strip().splitlines()
        cleaned = [s.strip() for s in raw if s.strip()][:10]
        if not cleaned:
            messagebox.showwarning("Fehler","Mindestens ein Stellwerk erforderlich.", parent=self); return
        STW_OPTIONS.clear(); STW_OPTIONS.extend(cleaned)
        SETTINGS["stw_options"] = list(STW_OPTIONS)
        save_settings(SETTINGS)
        self.stw_text.delete("1.0","end")
        self.stw_text.insert("1.0", "\n".join(STW_OPTIONS))
        self._stw_lbl.configure(text=f"Gespeichert ({len(STW_OPTIONS)} Stellwerke). Neustart fuer Filter-Update.")
        self.after(5000, lambda: self._stw_lbl.configure(text=""))

    def _reset_stw(self):
        global STW_OPTIONS
        STW_OPTIONS.clear(); STW_OPTIONS.extend(DEFAULT_STW_OPTIONS)
        SETTINGS["stw_options"] = list(STW_OPTIONS)
        save_settings(SETTINGS)
        self.stw_text.delete("1.0","end")
        self.stw_text.insert("1.0", "\n".join(STW_OPTIONS))
        self._stw_lbl.configure(text="Auf Standard zurueckgesetzt.")
        self.after(3000, lambda: self._stw_lbl.configure(text=""))

    def _toggle_dark(self):
        dark = self._dm_var.get()
        SETTINGS["dark_mode"] = dark
        save_settings(SETTINGS)
        self._dm_lbl.configure(text="Dunkel" if dark else "Hell")
        self.app._apply_dark(dark)


class STWTab(BaseTab):
    def __init__(self, parent): super().__init__(parent, DATA_FILE, tf_mode=False)

class TFTab(BaseTab):
    def __init__(self, parent): super().__init__(parent, TF_FILE, tf_mode=True)


class NotizenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Stellwerk Notizen")
        self.geometry("1100x700")
        self.minsize(800,520)
        self.configure(bg=C["BG"])
        self._dark = SETTINGS.get("dark_mode", False)
        self._always_top = False
        self._build_header()
        self._build_tabs()

    def _build_header(self):
        self._hdr = tk.Frame(self, bg=C["PRIMARY"]); self._hdr.pack(fill="x")
        tk.Label(self._hdr, text="Stellwerk Notizen", font=("Segoe UI",15,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(side="left", padx=20, pady=14)
        self._top_btn = tk.Button(self._hdr, text="Vorne", font=("Segoe UI",9),
                                   bg=C["PRIMARY_H"], fg="white", relief="flat", cursor="hand2",
                                   padx=10, pady=6, bd=0, command=self._toggle_top)
        self._top_btn.pack(side="right", padx=6, pady=10)
        dm_text = "Hell" if self._dark else "Dunkel"
        self._dm_btn = tk.Button(self._hdr, text=dm_text, font=("Segoe UI",9),
                                  bg=C["PRIMARY_H"], fg="white", relief="flat", cursor="hand2",
                                  padx=10, pady=6, bd=0, command=self._toggle_dark_header)
        self._dm_btn.pack(side="right", padx=6, pady=10)

    def _build_tabs(self):
        self._tab_bar = tk.Frame(self, bg=C["BG"]); self._tab_bar.pack(fill="x", padx=16, pady=(8,0))
        self._tab_content = tk.Frame(self, bg=C["BG"]); self._tab_content.pack(fill="both", expand=True)
        self._tabs = {}; self._tab_btns = {}
        for name, cls in [("Stellwerksnotizen", STWTab), ("TF Notizen", TFTab),
                           ("Fahrtenliste", FahrtenTab), ("Einstellungen", None)]:
            frame = cls(self._tab_content) if cls else SettingsTab(self._tab_content, self)
            self._tabs[name] = frame
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

    def _apply_dark(self, dark):
        self._dark = dark
        C.update(DARK if dark else LIGHT)
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=C["BG"])
        self._build_header(); self._build_tabs()

    def _toggle_dark_header(self):
        new_dark = not self._dark
        SETTINGS["dark_mode"] = new_dark
        save_settings(SETTINGS)
        self._apply_dark(new_dark)

    def _toggle_top(self):
        self._always_top = not self._always_top
        self.attributes("-topmost", self._always_top)
        self._top_btn.configure(text="Vorne (an)" if self._always_top else "Vorne",
                                bg="#8B0000" if self._always_top else C["PRIMARY_H"])


if __name__ == "__main__":
    app = NotizenApp()
    sb = tk.Frame(app, bg=C["BORDER"], height=22); sb.pack(fill="x", side="bottom")
    tk.Label(sb, text=f"v{APP_VERSION}", font=("Segoe UI",8),
             bg=C["BORDER"], fg=C["SUBTEXT"]).pack(side="right", padx=10)
    app.after(2000, lambda: check_for_update(app, silent=True))
    app.mainloop()