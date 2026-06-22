import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import json, os, shutil, csv, datetime, subprocess, platform, tempfile
import threading, urllib.request, ssl, sys, re, hashlib, time, queue

# ══════════════════════════════════════════════════════════════════════════════
APP_VERSION  = "1.2.1"
GITHUB_USER  = "derdummejunge187-lab"
GITHUB_REPO  = "stellwerk-notizen"
EXE_NAME     = "StellwerkNotizen.exe"
VERSION_URL  = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/version.txt"
DOWNLOAD_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/notizen_app.py"
EXE_DOWNLOAD_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/main/{EXE_NAME}"
# ══════════════════════════════════════════════════════════════════════════════

CHANGELOG = [
    ("v1.2.1", "22.06.2026 18:00 Uhr", [
        "Neuer Tab 'Trainings': Trainingstermine mit Anmeldung",
        "Trainings: Host + bis zu 3 Helfer + Platzanzahl pro Termin",
        "Trainings: Azubi-Raenge (Azubi KS, Azubi TF, Azubi FDl) koennen sich anmelden",
        "Trainings: Keine Doppelanmeldungen, Platzbegrenzung",
        "Trainings: Cloud-Sync via GitHub Gist (gleicher Mechanismus wie Personal)",
        "Neuer Rang: Azubi KS, Azubi TF, Azubi FDl hinzugefuegt",
        "Netzplan: 'Suedbahn' durch 'DVN' ersetzt",
        "Personal-Tab: Fehler beim 'Mitarbeiter hinzufuegen' behoben",
        "News-Tab entfernt (Webhook-Funktionalitaet eingestellt)",
        "Anthropic/KI-Screenshot-Import entfernt (API-Key nicht mehr benoetigt)",
        "API-Keys und Gist-URL jetzt fest im Skript verankert",
        "Schichtplan: Google-Sheets-Ladefehler behoben",
    ]),
    ("v1.2.0", "22.06.2026 12:00 Uhr", [
        "Neuer Tab 'Netzplan': zeigt das Streckennetz als interaktive Karte",
        "Neuer Tab 'Personal': Login mit BN/PW, 'Angemeldet bleiben'-Option",
        "Personal: Mitarbeiterliste mit Rollen HR, TF, FDL, KS",
        "Personal: Lizenzen fuer FDL (AK, NS, STB, BHBF) und TF (Streckenkunde + Fahrzeuge)",
        "Personal: Zusatzlizenzen PV, Ausbilder, Shift-Host fuer alle Raenge",
        "Personal: Cloud-Sync via GitHub Gist (alle sehen immer denselben Stand)",
        "Personal: Edit-Lock - immer nur 1 Person kann gleichzeitig bearbeiten",
        "Personal: Manueller Aktualisieren-Button fuer neuesten Stand",
    ]),
    ("v1.1.0", "21.06.2026 14:30 Uhr", [
        "Einstellungen-Tab hinzugefuegt (Stellwerke, Dark Mode, Update, Changelog)",
        "Stellwerke fuer Notizen-Auswahl sind jetzt konfigurierbar (bis zu 10)",
        "Hell/Dunkel-Modus wird gespeichert und beim Start wiederhergestellt",
        "Bestaetigen-Button im Notiz-Dialog funktioniert jetzt korrekt",
        "Filterleiste passt sich automatisch an konfigurierte Stellwerke an",
        "Neuer Tab 'Fahrtenliste'",
        "Neuer Tab 'Schichtplan'",
    ]),
    ("v1.0.0", "21.06.2026 13:00 Uhr", [
        "Erste Version der Stellwerk-Notizen App",
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

RANK_OPTIONS     = ["HR", "TF", "FDL", "KS", "Azubi KS", "Azubi TF", "Azubi FDl"]
RANK_COLORS      = {"HR":"#8B0000","TF":"#1A5276","FDL":"#145A32","KS":"#7D3C98",
                     "Azubi KS":"#A569BD","Azubi TF":"#3498DB","Azubi FDl":"#1ABC9C"}
AZUBI_RANKS      = {"Azubi KS", "Azubi TF", "Azubi FDl"}
FDL_LIZENZEN     = ["AK", "NS", "STB", "BHBF"]
TF_STRECKENKUNDE = ["BG-AK", "AK-MSB", "BHBF-SHBF"]
TF_FAHRZEUGE     = ["BR 429", "BR 648", "BR 628"]
ZUSATZ_LIZENZEN  = ["PV", "Ausbilder", "Shift-Host"]

# App-Accounts: BN -> sha256(Passwort)
# Neue Accounts hier eintragen:
PERSONAL_ACCOUNTS = {
    "jggaming26":  hashlib.sha256("Jlg161218MGB!".encode()).hexdigest(),
    "user1":  hashlib.sha256("passwort1".encode()).hexdigest(),
    # "BN456": hashlib.sha256("meinPW".encode()).hexdigest(),
}

BASE_DIR      = os.path.dirname(os.path.abspath(sys.executable if getattr(sys,'frozen',False) else __file__))
DATA_FILE     = os.path.join(BASE_DIR, "notizen_data.json")
TF_FILE       = os.path.join(BASE_DIR, "tf_data.json")
FAHRTEN_FILE  = os.path.join(BASE_DIR, "fahrten_data.json")
SCHICHTPLAN_CACHE_FILE = os.path.join(BASE_DIR, "schichtplan_cache.json")
TRAININGS_FILE = os.path.join(BASE_DIR, "trainings_data.json")
TRAININGS_GIST_FILENAME = "trainings_data.json"
TRAININGS_GIST_FILENAME = "trainings_data.json"
BACKUP_DIR    = os.path.join(BASE_DIR, "backups")
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")
PERSONAL_SESSION_FILE = os.path.join(BASE_DIR, "personal_session.json")
SCHICHTPLAN_POLL_SECONDS = 150
# ── Fester Google-Sheets-Freigabelink fuer den Schichtplan ──────────────────
# Hier einmal den Link eintragen – fertig. Kein Eingabefeld noetig.
SCHICHTPLAN_GSHEET_URL = "https://docs.google.com/spreadsheets/d/1N5i4KX7HjGr0vgDKKEQVy0jtKcd7b4klClYFh6Rsfoo/edit?usp=sharing"
# ────────────────────────────────────────────────────────────────────────────


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

_APP_INSTANCE = None
_EVENT_QUEUE = queue.Queue()

def show_toast(root, title, message, duration_ms=7000):
    if root is None:
        return
    try:
        toast = tk.Toplevel(root)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)
        toast.configure(bg=C["PRIMARY"])
        w, h = 330, 100
        sw, sh = toast.winfo_screenwidth(), toast.winfo_screenheight()
        toast.geometry(f"{w}x{h}+{sw-w-24}+{sh-h-60}")
        tk.Label(toast, text=title, font=("Segoe UI",10,"bold"), bg=C["PRIMARY"], fg="white",
                 anchor="w", justify="left", wraplength=300).pack(fill="x", padx=14, pady=(12,4))
        tk.Label(toast, text=message, font=("Segoe UI",9), bg=C["PRIMARY"], fg="#FFE5E5",
                 anchor="w", justify="left", wraplength=300).pack(fill="x", padx=14)
        close = tk.Label(toast, text="✕", font=("Segoe UI",9,"bold"), bg=C["PRIMARY"], fg="white", cursor="hand2")
        close.place(x=w-26, y=8)
        close.bind("<Button-1>", lambda e: toast.destroy())
        toast.after(duration_ms, lambda: toast.destroy() if toast.winfo_exists() else None)
    except Exception:
        pass


# ── Fest verankerte Gist-Konfiguration (hier eintragen, kein Eingabefeld mehr) ──
GIST_URL   = ""  # ← HIER die Gist-URL eintragen, z.B. "https://gist.github.com/username/abc123"
GIST_TOKEN = ""  # ← HIER den GitHub Token eintragen (mit gist-Berechtigung)

# ── Aktuell eingeloggter Benutzer (wird vom PersonalTab gesetzt) ─────────
_CURRENT_USER = {"bn": None, "roblox": None, "rank": None}

# ── Gist-Sync fuer Personal & Trainings ───────────────────────────────────────
def _gist_api(method, url, token, data=None):
    ctx = ssl.create_default_context()
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method,
        headers={"Authorization": f"token {token}",
                 "Accept": "application/vnd.github.v3+json",
                 "Content-Type": "application/json",
                 "User-Agent": "StellwerkNotizen/1.2"})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return json.loads(r.read().decode("utf-8"))

def personal_sync_load():
    """Laedt Personal-Daten vom Gist. Gibt (mitarbeiter_list, lock_info) zurueck."""
    url = GIST_URL.strip()
    token = GIST_TOKEN.strip()
    if not url or not token:
        return None, None
    try:
        m = re.search(r"gist\.github\.com/[^/]+/([a-f0-9]+)", url)
        if not m:
            return None, None
        gist_id = m.group(1)
        data = _gist_api("GET", f"https://api.github.com/gists/{gist_id}", token)
        files = data.get("files", {})
        main_f = files.get("personal_data.json", {})
        raw = main_f.get("content", "")
        if not raw:
            return [], {}
        parsed = json.loads(raw)
        mitarbeiter = parsed.get("mitarbeiter", [])
        lock = parsed.get("lock", {})
        return mitarbeiter, lock
    except Exception:
        return None, None

def personal_sync_save(mitarbeiter, lock):
    """Speichert Personal-Daten zum Gist."""
    url = GIST_URL.strip()
    token = GIST_TOKEN.strip()
    if not url or not token:
        return False, "Kein Gist-URL/Token konfiguriert"
    try:
        m = re.search(r"gist\.github\.com/[^/]+/([a-f0-9]+)", url)
        if not m:
            return False, "Ungueltige Gist-URL"
        gist_id = m.group(1)
        payload = {"files": {"personal_data.json": {
            "content": json.dumps({"mitarbeiter": mitarbeiter, "lock": lock},
                                   ensure_ascii=False, indent=2)
        }}}
        _gist_api("PATCH", f"https://api.github.com/gists/{gist_id}", token, payload)
        return True, ""
    except Exception as e:
        return False, str(e)

def gist_sync_data(filename, content):
    """Universelle Gist-Sync: speichert JSON-Daten in einer separaten Datei im selben Gist."""
    url = GIST_URL.strip()
    token = GIST_TOKEN.strip()
    if not url or not token:
        return False, "Kein Gist konfiguriert"
    try:
        m = re.search(r"gist\.github\.com/[^/]+/([a-f0-9]+)", url)
        if not m:
            return False, "Ungueltige Gist-URL"
        gist_id = m.group(1)
        payload = {"files": {filename: {"content": content}}}
        _gist_api("PATCH", f"https://api.github.com/gists/{gist_id}", token, payload)
        return True, ""
    except Exception as e:
        return False, str(e)

def gist_load_data(filename):
    """Universelle Gist-Sync: laedt JSON-Daten aus einer separaten Datei im Gist."""
    url = GIST_URL.strip()
    token = GIST_TOKEN.strip()
    if not url or not token:
        return None
    try:
        m = re.search(r"gist\.github\.com/[^/]+/([a-f0-9]+)", url)
        if not m:
            return None
        gist_id = m.group(1)
        data = _gist_api("GET", f"https://api.github.com/gists/{gist_id}", token)
        files = data.get("files", {})
        f = files.get(filename, {})
        raw = f.get("content", "")
        if not raw:
            return None
        return json.loads(raw)
    except Exception:
        return None


# ── Session (Angemeldet bleiben) ──────────────────────────────────────────────
def load_session():
    if os.path.exists(PERSONAL_SESSION_FILE):
        try:
            with open(PERSONAL_SESSION_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_session(bn):
    with open(PERSONAL_SESSION_FILE,"w",encoding="utf-8") as f:
        json.dump({"bn": bn, "ts": now_str()}, f)

def clear_session():
    if os.path.exists(PERSONAL_SESSION_FILE):
        os.remove(PERSONAL_SESSION_FILE)


# ── Schichtplan helpers (unverändert) ─────────────────────────────────────────
def gsheet_csv_url(share_url):
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", share_url or "")
    if not m:
        return None
    doc_id = m.group(1)
    gid_m = re.search(r"[?&#]gid=(\d+)", share_url)
    gid = gid_m.group(1) if gid_m else "0"
    return f"https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&gid={gid}"

def load_schichtplan_cache():
    if os.path.exists(SCHICHTPLAN_CACHE_FILE):
        try:
            with open(SCHICHTPLAN_CACHE_FILE,"r",encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"hash":"", "hash_initialized": False, "rows": [], "last_check":"", "last_change":""}

def save_schichtplan_cache(data):
    with open(SCHICHTPLAN_CACHE_FILE,"w",encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def fetch_schichtplan_once():
    url = SCHICHTPLAN_GSHEET_URL.strip()
    if not url or "DEINE_SHEET_ID" in url:
        raise ValueError("Bitte SCHICHTPLAN_GSHEET_URL im Skript eintragen.")
    csv_url = gsheet_csv_url(url)
    if not csv_url:
        raise ValueError("Der hinterlegte Google-Sheets-Link konnte nicht gelesen werden. Stelle sicher, dass die Tabelle oeffentlich ('Jeder mit Link – Betrachter') freigegeben ist.")
    with _https_get(csv_url, timeout=20) as r:
        raw = r.read().decode("utf-8-sig", errors="replace")
    new_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    cache = load_schichtplan_cache()
    changed = cache.get("hash_initialized", False) and new_hash != cache.get("hash", "")
    rows = list(csv.reader(raw.splitlines()))
    cache["rows"] = rows
    cache["hash"] = new_hash
    cache["hash_initialized"] = True
    cache["last_check"] = now_str()
    if changed:
        cache["last_change"] = now_str()
    save_schichtplan_cache(cache)
    return rows, changed, cache

def _schichtplan_poll_loop():
    while True:
        try:
            if SCHICHTPLAN_GSHEET_URL.strip() and "DEINE_SHEET_ID" not in SCHICHTPLAN_GSHEET_URL:
                rows, changed, cache = fetch_schichtplan_once()
                _EVENT_QUEUE.put(("schichtplan", changed))
        except Exception:
            pass
        time.sleep(SCHICHTPLAN_POLL_SECONDS)

def _on_schichtplan_update(changed):
    if _APP_INSTANCE is None:
        return
    tab = _APP_INSTANCE._tabs.get("Schichtplan")
    if tab is not None and hasattr(tab, "refresh_from_cache"):
        tab.refresh_from_cache()
    if changed:
        show_toast(_APP_INSTANCE, "Schichtplan aktualisiert",
                   "Der Schichtplan wurde geaendert - bitte pruefen.")

_BG_THREADS_STARTED = False

def start_background_services():
    global _BG_THREADS_STARTED
    if _BG_THREADS_STARTED:
        return
    _BG_THREADS_STARTED = True
    threading.Thread(target=_schichtplan_poll_loop, daemon=True).start()

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
                    "@echo off\r\n:wait\r\n"
                    f"tasklist /FI \"PID eq {pid}\" 2>NUL | findstr \"{pid}\" >NUL\r\n"
                    "if not errorlevel 1 (\r\n    timeout /t 1 /nobreak >NUL\r\n    goto wait\r\n)\r\n"
                    f"move /Y \"{new_exe}\" \"{current_exe}\" >NUL\r\n"
                    f"start \"\" \"{current_exe}\"\r\ndel \"%~f0\"\r\n"
                )
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                subprocess.Popen(["cmd", "/c", bat_path], cwd=base,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
                win.destroy()
                messagebox.showinfo("Update",
                    f"v{remote} wird installiert. Die Anwendung schliesst sich jetzt.", parent=parent)
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


# ════════════════════════════════════════════════════════════════════════
# NotePopup, BaseTab, FahrtPopup, DokuPopup
# FahrtenTab, SchichtplanTab, SettingsTab
# ════════════════════════════════════════════════════════════════════════

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
            tk.Label(body, text="Zugnummern", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
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
        w, h = 400, max(min(self.winfo_reqheight()+10, self.winfo_screenheight()-80), 320)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify(); self.grab_set()

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
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white", cursor="hand2")
        x.pack(side="right", padx=8); x.bind("<Button-1>", lambda e: self.destroy())
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
            b.pack(side="left", padx=2); self._fahrt_btns[s] = b
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
        start = self.start_e.get().strip(); ziel = self.ziel_e.get().strip()
        ab = self.ab_e.get().strip(); an = self.an_e.get().strip()
        if not start or not ziel:
            messagebox.showwarning("Fehler","Bitte Start- und Endbahnhof eingeben.",parent=self); return
        if parse_hhmm(ab) is None or parse_hhmm(an) is None:
            messagebox.showwarning("Fehler","Bitte Abfahrt/Ankunft im Format HH:MM eingeben.",parent=self); return
        ex = self.existing or {}
        data = {"start":start,"ziel":ziel,"abfahrt":ab,"ankunft":an,"fahrt":self.fahrt_var.get(),
                "erledigt":ex.get("erledigt",False),"doku":ex.get("doku",""),
                "ts":ex.get("ts",now_str()) if self.existing else now_str(),"ts_edit":now_str()}
        if self.existing: data["id"] = ex.get("id",0)
        self.on_confirm(data); self.destroy()


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
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white", cursor="hand2")
        x.pack(side="right", padx=8); x.bind("<Button-1>", lambda e: self.destroy())
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
        w, h = 400, max(min(self.winfo_reqheight()+10, self.winfo_screenheight()-80), 280)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify(); self.grab_set()

    def _confirm(self):
        text = self.doku.get("1.0","end").strip()
        if not text:
            messagebox.showwarning("Fehler","Bitte kurze Dokumentation eingeben.",parent=self); return
        self.on_confirm(text); self.destroy()


class FahrtenTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self.data_path = FAHRTEN_FILE
        self.fahrten   = load_json(FAHRTEN_FILE)
        self._id_ctr   = max((f.get("id",0) for f in self.fahrten), default=0)+1
        self._row_frames = {}
        do_backup(FAHRTEN_FILE)
        self._build_toolbar(); self._build_summary(); self._build_list(); self._refresh()

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

    def _chrono_sorted(self):
        return sorted(self.fahrten, key=lambda f: f.get("abfahrt","99:99"))

    def _display_sorted(self):
        return sorted(self.fahrten, key=lambda f: (bool(f.get("erledigt",False)), f.get("abfahrt","99:99")))

    def _current_fahrt(self):
        for f in self._chrono_sorted():
            if not f.get("erledigt"):
                return f
        return None

    def _refresh(self):
        for w in self.rf.winfo_children(): w.destroy()
        self._row_frames = {}
        ordered = self._display_sorted()
        if not ordered:
            tk.Label(self.rf, text="Keine Fahrten erfasst.", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=40)
        else:
            current = self._current_fahrt()
            for i, f in enumerate(ordered):
                if i > 0 and bool(ordered[i-1].get("erledigt",False)) == bool(f.get("erledigt",False)):
                    t1 = parse_hhmm(ordered[i-1].get("ankunft",""))
                    t2 = parse_hhmm(f.get("abfahrt",""))
                    if t1 and t2:
                        pause = minutes_between(t1,t2)
                        pf = tk.Frame(self.rf, bg=C["BG"]); pf.pack(fill="x")
                        tk.Label(pf, text=f"⏸  Pause: {fmt_minutes(pause)}", font=("Segoe UI",8),
                                 bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", padx=20, pady=2)
                if i > 0 and not ordered[i-1].get("erledigt",False) and f.get("erledigt",False):
                    sep = tk.Frame(self.rf, bg=C["BG"]); sep.pack(fill="x", pady=(8,4))
                    tk.Frame(sep, bg=C["BORDER"], height=1).pack(fill="x", side="top")
                    tk.Label(sep, text="Erledigte Fahrten", font=("Segoe UI",8,"bold"),
                             bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", pady=(4,0))
                self._build_row(i, f, current is not None and f.get("id")==current.get("id"))
        chrono = self._chrono_sorted()
        if len(chrono) >= 2:
            self._update_summary(chrono)
            self.summary_frame.pack(fill="x", padx=16, pady=(0,8), before=self.outer)
        else:
            self.summary_frame.pack_forget()

    def _build_row(self, i, f, is_current):
        rbg = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
        erledigt = f.get("erledigt",False)
        border = C["PRIMARY"] if is_current else C["BORDER"]
        bw = 2 if is_current else 1
        row = tk.Frame(self.rf, bg=rbg, highlightthickness=bw, highlightbackground=border)
        row.pack(fill="x", pady=2); self._row_frames[f["id"]] = row
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
        total_fahr = sum(minutes_between(t1,t2) for f in ordered
                         for t1,t2 in [(parse_hhmm(f.get("abfahrt","")), parse_hhmm(f.get("ankunft","")))]
                         if t1 and t2)
        total_pause = sum(minutes_between(t1,t2)
                          for i in range(1,len(ordered))
                          for t1,t2 in [(parse_hhmm(ordered[i-1].get("ankunft","")), parse_hhmm(ordered[i].get("abfahrt","")))]
                          if t1 and t2)
        self.summary_lbl.configure(
            text=f"{len(ordered)} Fahrten   |   Reine Fahrtzeit: {fmt_minutes(total_fahr)}   |   "
                 f"Pausenzeit: {fmt_minutes(total_pause)}   |   Gesamtzeit: {fmt_minutes(total_fahr+total_pause)}")

    def _open_add(self): FahrtPopup(self.winfo_toplevel(), self._add)
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
                f"Fahrt {fahrt.get('start','')} -> {fahrt.get('ziel','')} loeschen?", parent=self):
            self.fahrten = [f for f in self.fahrten if f.get("id") != fahrt.get("id")]
            save_json(self.data_path, self.fahrten); self._refresh()
    def _mark_done(self, fahrt):
        def apply(doku_text):
            for ff in self.fahrten:
                if ff.get("id") == fahrt.get("id"):
                    ff["erledigt"] = True; ff["doku"] = doku_text; ff["ts_erledigt"] = now_str(); break
            save_json(self.data_path, self.fahrten); self._refresh()
        DokuPopup(self.winfo_toplevel(), apply, fahrt)
    def _jump_current(self):
        cur = self._current_fahrt()
        if cur is None:
            messagebox.showinfo("Aktuelle Fahrt","Alle Fahrten sind erledigt.", parent=self); return
        row = self._row_frames.get(cur["id"])
        if row is None: return
        self.update_idletasks()
        bbox = self.canvas.bbox("all")
        if not bbox: return
        total_h = max(bbox[3]-bbox[1], 1)
        self.canvas.yview_moveto(max(0, (row.winfo_y()-10)/total_h))
        self._flash(row)
    def _flash(self, row):
        row.configure(highlightbackground="#FFD700", highlightthickness=3)
        self.after(900, lambda: row.configure(highlightbackground=C["PRIMARY"], highlightthickness=2))
class SchichtplanTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self._build_toolbar(); self._build_table(); self.refresh_from_cache()

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=10)
        make_btn(tb, "🔄  Jetzt aktualisieren", self._manual_refresh, pady=7).pack(side="left")
        self.status_lbl = tk.Label(tb, text="", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"])
        self.status_lbl.pack(side="left", padx=16)

    def _build_table(self):
        outer = tk.Frame(self, bg=C["BG"]); outer.pack(fill="both", expand=True, padx=16, pady=(0,16))
        outer.grid_rowconfigure(0, weight=1); outer.grid_columnconfigure(0, weight=1)
        style = ttk.Style()
        try: style.theme_use("clam")
        except Exception: pass
        style.configure("Schicht.Treeview", background=C["PANEL"], fieldbackground=C["PANEL"],
                        foreground=C["TEXT"], rowheight=28, font=("Segoe UI",10), borderwidth=0)
        style.configure("Schicht.Treeview.Heading", background=C["PRIMARY"], foreground="white",
                        font=("Segoe UI",10,"bold"), relief="flat")
        style.map("Schicht.Treeview", background=[("selected", C["PRIMARY_H"])])
        vsb = tk.Scrollbar(outer, orient="vertical"); hsb = tk.Scrollbar(outer, orient="horizontal")
        self.tree = ttk.Treeview(outer, style="Schicht.Treeview", show="headings",
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        vsb.configure(command=self.tree.yview); hsb.configure(command=self.tree.xview)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns"); hsb.grid(row=1, column=0, sticky="ew")

    def _manual_refresh(self):
        self.status_lbl.configure(text="Aktualisiere ...")
        threading.Thread(target=self._fetch_now, daemon=True).start()

    def _fetch_now(self):
        try:
            rows, changed, cache = fetch_schichtplan_once()
            self.after(0, lambda: self._populate(rows, cache))
            if changed:
                self.after(0, lambda: show_toast(self.winfo_toplevel(),
                            "Schichtplan aktualisiert", "Der Schichtplan wurde geaendert."))
        except Exception as ex:
            msg = str(ex)
            hint = ""
            if "403" in msg or "404" in msg:
                hint = "\n\nHinweis: Sheet muss auf \'Jeder mit Link – Betrachter\' freigegeben sein."
            elif "Kein Google-Sheets-Link" in msg:
                hint = "\n\nBitte Link unter Einstellungen → Schichtplan eintragen."
            full = msg + hint
            self.after(0, lambda m=full: messagebox.showerror(
                "Schichtplan Fehler", f"Konnte nicht geladen werden:\n{m}", parent=self))
            self.after(0, lambda: self.status_lbl.configure(text="Fehler – siehe Fehlermeldung"))

    def refresh_from_cache(self):
        cache = load_schichtplan_cache(); self._populate(cache.get("rows",[]), cache)

    def _populate(self, rows, cache):
        self.tree.delete(*self.tree.get_children())
        if not rows:
            self.tree["columns"] = ()
            self.status_lbl.configure(text="Noch keine Daten - bitte Google-Sheets-Link in Einstellungen hinterlegen.")
            return
        header = rows[0]; n = len(header)
        cols = [f"c{i}" for i in range(n)]
        self.tree["columns"] = cols
        for i, name in enumerate(header):
            self.tree.heading(cols[i], text=name or f"Spalte {i+1}")
            self.tree.column(cols[i], width=220, minwidth=160, stretch=False, anchor="w")
        for row in rows[1:]:
            if len(row) < n: row = row + [""]*(n-len(row))
            else: row = row[:n]
            self.tree.insert("", "end", values=row)
        self.status_lbl.configure(
            text=f"Letzte Pruefung: {cache.get('last_check') or '-'}   |   Letzte Aenderung: {cache.get('last_change') or 'noch keine'}")


# ════════════════════════════════════════════════════════════════════════
# NETZPLAN TAB
# ════════════════════════════════════════════════════════════════════════
class NetzplanTab(tk.Frame):
    """Netzplan – 1:1 Nachbau des DVN-Streckennetzes."""
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self._build()

    def _build(self):
        tb = tk.Frame(self, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=8)
        tk.Label(tb, text="Netzplan – DVN", font=("Segoe UI",13,"bold"),
                 bg=C["BG"], fg=C["TEXT"]).pack(side="left")
        outer = tk.Frame(self, bg=C["PANEL"], highlightthickness=1,
                         highlightbackground=C["BORDER"])
        outer.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self.canvas = tk.Canvas(outer, bg="white", highlightthickness=0)
        sb_v = tk.Scrollbar(outer, orient="vertical", command=self.canvas.yview)
        sb_h = tk.Scrollbar(outer, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=sb_v.set, xscrollcommand=sb_h.set)
        sb_v.pack(side="right", fill="y"); sb_h.pack(side="bottom", fill="x")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda e: self._draw())
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    def _draw(self):
        c = self.canvas
        c.delete("all")
        W = c.winfo_width(); H = c.winfo_height()
        if W < 10 or H < 10:
            self.after(100, self._draw); return

        # Wir zeichnen auf einem fixen 1100x820 Referenz-Raster
        # und skalieren auf die tatsächliche Canvas-Größe
        RW, RH = 1100, 820
        s = min(W / RW, H / RH, 1.2)
        ox = (W - RW*s) / 2
        oy = max((H - RH*s) / 2, 10)

        def p(x, y):
            return ox + x*s, oy + y*s

        COL_RB4  = "#E8000D"
        COL_RB14 = "#F07800"
        COL_RB16 = "#009EE3"
        COL_TXT  = "#1A1A2E"
        LW = max(int(8*s), 4)

        # Stationen (x,y auf 1100x820, abgelesen vom Bild)
        ST = {
            "Markt Schlossberg":  (148, 415),
            "Luisental":          (268, 330),
            "Weidenheim":         (378, 315),
            "Altenkirchen":       (498, 300),
            "Niedersöllern":      (378, 450),
            "Mühlstetten":        (355, 560),
            "Kleinhagen":         (435, 670),
            "Bergenau Süd":       (515, 670),
            "Bergenau Hbf":       (665, 555),
            "Nordtal (Werra)":    (762, 670),
            "Waldstadt":          (848, 670),
            "Hungen Bahnhof":     (912, 565),
            "Kemsfelde":          (912, 470),
            "Großweiler (Werra)": (912, 385),
            "Kleinbittersdorf":   (912, 295),
            "Staburg Stadt":      (845, 210),
            "Staburg Hbf":        (1025, 175),
        }

        # Routen als Polylinien – wir geben Wegpunkte an
        # damit die Linien rechtwinklig (metro-style) verlaufen
        # RB4: Bergenau Hbf → (rechtwinklig runter→links) → Bergenau Süd → Kleinhagen
        #      → Mühlstetten → Niedersöllern → (hoch→rechts) → Altenkirchen
        rb4_pts = [
            ST["Bergenau Hbf"],
            (ST["Bergenau Hbf"][0], ST["Kleinhagen"][1]),   # senkrecht runter
            ST["Bergenau Süd"],
            ST["Kleinhagen"],
            ST["Mühlstetten"],
            ST["Niedersöllern"],
            (ST["Niedersöllern"][0], ST["Altenkirchen"][1]), # senkrecht hoch
            ST["Altenkirchen"],
        ]
        # RB14: Markt Schlossberg → Luisental → Weidenheim → Altenkirchen
        rb14_pts = [
            ST["Markt Schlossberg"],
            ST["Luisental"],
            ST["Weidenheim"],
            (ST["Weidenheim"][0], ST["Altenkirchen"][1]),
            ST["Altenkirchen"],
        ]
        # RB16: Bergenau Hbf → (senkrecht runter) → Waldstadt → Nordtal → 
        #        (senkrecht hoch rechts) → Hungen Bhf → Kemsfelde → Großweiler →
        #        Kleinbittersdorf → Staburg Stadt → Staburg Hbf
        rb16_pts = [
            ST["Bergenau Hbf"],
            (ST["Bergenau Hbf"][0], ST["Waldstadt"][1]),    # runter
            ST["Waldstadt"],
            ST["Nordtal (Werra)"],
            (ST["Hungen Bahnhof"][0], ST["Waldstadt"][1]),  # rechts
            ST["Hungen Bahnhof"],
            ST["Kemsfelde"],
            ST["Großweiler (Werra)"],
            ST["Kleinbittersdorf"],
            (ST["Kleinbittersdorf"][0], ST["Staburg Stadt"][1]),  # runter zur Staburg Stadt Höhe
            ST["Staburg Stadt"],
            (ST["Staburg Stadt"][0], ST["Staburg Hbf"][1]), # hoch zu Staburg Hbf
            ST["Staburg Hbf"],
        ]

        def draw_poly(pts, color, lw, dy=0):
            coords = []
            for (x,y) in pts:
                px, py = p(x, y+dy)
                coords.extend([px, py])
            if len(coords) >= 4:
                c.create_line(*coords, fill=color, width=lw,
                               capstyle="round", joinstyle="round", smooth=False)

        # Zeichenreihenfolge: RB16 zuerst (hinterste Ebene)
        draw_poly(rb16_pts, COL_RB16, LW)
        # RB4 und RB14 überlappen an Altenkirchen-Bereich
        # kleiner Versatz damit beide sichtbar
        draw_poly(rb4_pts,  COL_RB4,  LW, dy=0)
        draw_poly(rb14_pts, COL_RB14, LW, dy=-LW//2-1)

        # ── Stationspunkte ──
        major = {"Altenkirchen","Bergenau Hbf","Markt Schlossberg",
                 "Staburg Hbf","Staburg Stadt"}
        rb4_set  = set(["Bergenau Hbf","Bergenau Süd","Kleinhagen","Mühlstetten","Niedersöllern","Altenkirchen"])
        rb14_set = set(["Markt Schlossberg","Luisental","Weidenheim","Altenkirchen"])
        rb16_set = set(["Bergenau Hbf","Waldstadt","Nordtal (Werra)","Hungen Bahnhof",
                         "Kemsfelde","Großweiler (Werra)","Kleinbittersdorf","Staburg Stadt","Staburg Hbf"])

        for name, (rx, ry) in ST.items():
            cx, cy = p(rx, ry)
            r = max(int((11 if name in major else 7)*s), 4)
            c.create_oval(cx-r, cy-r, cx+r, cy+r,
                           fill="white", outline=COL_TXT, width=max(int(2*s),1))

            # Label-Seite
            label_right = {"Altenkirchen","Staburg Hbf","Staburg Stadt",
                           "Bergenau Hbf","Hungen Bahnhof","Kemsfelde",
                           "Großweiler (Werra)","Kleinbittersdorf","Waldstadt",
                           "Nordtal (Werra)","Bergenau Süd"}
            label_left  = {"Markt Schlossberg","Niedersöllern","Mühlstetten","Kleinhagen"}
            label_up    = {"Luisental","Weidenheim"}

            fs = max(int(10*s), 7)
            fw = "bold" if name in major else "normal"

            if name in label_right:
                lx2, ly2, anc = cx + r + 6, cy, "w"
            elif name in label_left:
                lx2, ly2, anc = cx - r - 6, cy, "e"
            elif name in label_up:
                lx2, ly2, anc = cx, cy - r - 6, "s"
            else:
                lx2, ly2, anc = cx, cy + r + 8, "n"

            c.create_text(lx2, ly2, text=name,
                           font=("Segoe UI", fs, fw), fill=COL_TXT, anchor=anc)

            # Linien-Badges an Haupt-Stationen
            if name in major:
                badge_items = []
                if name in rb4_set:  badge_items.append(("RB4",  COL_RB4))
                if name in rb14_set: badge_items.append(("RB14", COL_RB14))
                if name in rb16_set: badge_items.append(("RB16", COL_RB16))
                bw = max(int(28*s),18); bh = max(int(14*s),10)
                bx_start = cx - (len(badge_items)-1)*(bw+3)//2
                for bi, (btext, bcol) in enumerate(badge_items):
                    bx = bx_start + bi*(bw+3)
                    c.create_rectangle(bx-bw//2, cy+r+4, bx+bw//2, cy+r+4+bh,
                                        fill=bcol, outline="", width=0)
                    c.create_text(bx, cy+r+4+bh//2, text=btext,
                                   font=("Segoe UI", max(int(7*s),6), "bold"),
                                   fill="white", anchor="center")

        # ── Legende ──
        lx0, ly0 = p(20, 145)
        legend = [("RB4",  COL_RB4,  "Bergenau Hbf – Altenkirchen"),
                  ("RB14", COL_RB14, "Markt Schlossberg – Altenkirchen"),
                  ("RB16", COL_RB16, "Bergenau Hbf – Staburg Stadt / Staburg Hbf")]
        gap = max(int(26*s), 18)
        for i, (lbl, col, desc) in enumerate(legend):
            iy = ly0 + i * gap
            bw2 = max(int(34*s),22); bh2 = max(int(17*s),12)
            c.create_rectangle(lx0, iy-bh2//2, lx0+bw2, iy+bh2//2,
                                 fill=col, outline="")
            c.create_text(lx0+bw2//2, iy, text=lbl,
                           font=("Segoe UI", max(int(8*s),6), "bold"),
                           fill="white", anchor="center")
            c.create_text(lx0+bw2+8, iy, text=desc,
                           font=("Segoe UI", max(int(9*s),7)),
                           fill=COL_TXT, anchor="w")

        # ── Titel ──
        c.create_text(p(20, 40)[0], p(20,40)[1],
                      text="≡  DVN", font=("Segoe UI", max(int(15*s),10), "bold"),
                      fill=COL_RB4, anchor="w")
        c.create_text(p(20, 105)[0], p(20,105)[1],
                      text="AGENDA DER V1.1",
                      font=("Segoe UI", max(int(14*s),9), "bold"),
                      fill=COL_TXT, anchor="w")

        c.configure(scrollregion=c.bbox("all"))


# ════════════════════════════════════════════════════════════════════════
# PERSONAL TAB – Login + Mitarbeiterliste
# ════════════════════════════════════════════════════════════════════════
class PersonalUserPopup(tk.Toplevel):
    """Mitarbeiter anlegen oder bearbeiten."""
    def __init__(self, parent, on_confirm, existing=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.existing   = existing
        self.title("Mitarbeiter bearbeiten" if existing else "Mitarbeiter hinzufuegen")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.withdraw()
        self._build()
        self.update_idletasks()
        w = 480
        h = min(self.winfo_reqheight()+20, self.winfo_screenheight()-80)
        h = max(h, 500)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify()
        self.grab_set()

    def _chk_row(self, parent, text, var):
        f = tk.Frame(parent, bg=C["PANEL"]); f.pack(fill="x", pady=1)
        tk.Checkbutton(f, variable=var, bg=C["PANEL"], activebackground=C["PANEL"],
                       selectcolor=C["BG"], cursor="hand2").pack(side="left")
        tk.Label(f, text=text, font=FONT_INPUT, bg=C["PANEL"], fg=C["TEXT"]).pack(side="left", padx=4)
        return f

    def _build(self):
        # Scrollbar wrapper
        canvas = tk.Canvas(self, bg=C["BG"], highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); canvas.pack(fill="both", expand=True)
        body = tk.Frame(canvas, bg=C["BG"])
        cw = canvas.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))

        hdr = tk.Frame(body, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text="Mitarbeiter bearbeiten" if self.existing else "Mitarbeiter hinzufuegen",
                 font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white", cursor="hand2")
        x.pack(side="right", padx=8); x.bind("<Button-1>", lambda e: self.destroy())

        inner = tk.Frame(body, bg=C["BG"]); inner.pack(fill="both", expand=True, padx=20, pady=14)
        ex = self.existing or {}

        # Benutzername (BN) - Verknuepfung zum Login
        tk.Label(inner, text="BN (Benutzername)", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.bn_e = tk.Entry(inner, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                              insertbackground=C["TEXT"], highlightthickness=1,
                              highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        self.bn_e.pack(fill="x", ipady=5, pady=4)
        self.bn_e.insert(0, ex.get("bn",""))
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        # Roblox Username
        tk.Label(inner, text="Roblox-Username", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.roblox_e = tk.Entry(inner, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                                  insertbackground=C["TEXT"], highlightthickness=1,
                                  highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        self.roblox_e.pack(fill="x", ipady=5, pady=4)
        self.roblox_e.insert(0, ex.get("roblox",""))
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        # Rang
        tk.Label(inner, text="Rang", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.rank_var = tk.StringVar(value=ex.get("rank", RANK_OPTIONS[0]))
        rf = tk.Frame(inner, bg=C["BG"]); rf.pack(anchor="w", pady=4)
        self._rank_btns = {}
        for r in RANK_OPTIONS:
            col = RANK_COLORS.get(r, C["PRIMARY"])
            b = tk.Button(rf, text=r, font=("Segoe UI",9,"bold"),
                          bg=C["BORDER"], fg=C["TEXT"],
                          relief="flat", cursor="hand2", padx=14, pady=5, bd=0,
                          command=lambda r=r: self._sel_rank(r))
            b.pack(side="left", padx=3); self._rank_btns[r] = b
        self._sel_rank(self.rank_var.get())
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        # Lizenzen (dynamisch je nach Rang – wir zeigen alle, Popup updated bei Rang-Wahl)
        self._lic_frame = tk.Frame(inner, bg=C["BG"]); self._lic_frame.pack(fill="x")
        self._fdl_vars  = {k: tk.BooleanVar(value=k in ex.get("fdl_lizenzen",[])) for k in FDL_LIZENZEN}
        self._tf_sk_vars = {k: tk.BooleanVar(value=k in ex.get("tf_streckenkunde",[])) for k in TF_STRECKENKUNDE}
        self._tf_fz_vars = {k: tk.BooleanVar(value=k in ex.get("tf_fahrzeuge",[])) for k in TF_FAHRZEUGE}
        self._build_lizenzen(self.rank_var.get())

        # Zusatzlizenzen
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        tk.Label(inner, text="Zusatzlizenzen", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        zf = tk.Frame(inner, bg=C["PANEL"], highlightthickness=1, highlightbackground=C["BORDER"])
        zf.pack(fill="x", pady=4)
        self._zusatz_vars = {k: tk.BooleanVar(value=k in ex.get("zusatz_lizenzen",[])) for k in ZUSATZ_LIZENZEN}
        for k, var in self._zusatz_vars.items():
            self._chk_row(zf, k, var)

        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", pady=8)
        br = tk.Frame(inner, bg=C["BG"]); br.pack(fill="x", pady=(0,10))
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Speichern  ", self._confirm).pack(side="right")

    def _build_lizenzen(self, rank):
        for w in self._lic_frame.winfo_children(): w.destroy()
        if rank == "FDL":
            tk.Label(self._lic_frame, text="FDL-Lizenzen", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
            lf = tk.Frame(self._lic_frame, bg=C["PANEL"], highlightthickness=1,
                          highlightbackground=C["BORDER"]); lf.pack(fill="x", pady=4)
            for k, var in self._fdl_vars.items():
                self._chk_row(lf, k, var)
        elif rank == "TF":
            tk.Label(self._lic_frame, text="Streckenkunde", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
            sf = tk.Frame(self._lic_frame, bg=C["PANEL"], highlightthickness=1,
                          highlightbackground=C["BORDER"]); sf.pack(fill="x", pady=4)
            for k, var in self._tf_sk_vars.items():
                self._chk_row(sf, k, var)
            tk.Label(self._lic_frame, text="Fahrzeuglizenzen", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", pady=(8,0))
            ff = tk.Frame(self._lic_frame, bg=C["PANEL"], highlightthickness=1,
                          highlightbackground=C["BORDER"]); ff.pack(fill="x", pady=4)
            for k, var in self._tf_fz_vars.items():
                self._chk_row(ff, k, var)
        else:
            tk.Label(self._lic_frame, text=f"Keine Rang-spezifischen Lizenzen fuer {rank}.",
                     font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", pady=4)

    def _sel_rank(self, r):
        self.rank_var.set(r)
        col = RANK_COLORS.get(r, C["PRIMARY"])
        for k, b in self._rank_btns.items():
            active = k == r
            b.configure(bg=RANK_COLORS.get(k,C["PRIMARY"]) if active else C["BORDER"],
                        fg="white" if active else C["TEXT"])
        self._build_lizenzen(r)

    def _confirm(self):
        bn = self.bn_e.get().strip()
        roblox = self.roblox_e.get().strip()
        if not roblox:
            messagebox.showwarning("Fehler","Bitte Roblox-Username eingeben.",parent=self); return
        rank = self.rank_var.get()
        data = {
            "id": self.existing.get("id", int(time.time()*1000)) if self.existing else int(time.time()*1000),
            "bn": bn,
            "roblox": roblox,
            "rank": rank,
            "fdl_lizenzen": [k for k,v in self._fdl_vars.items() if v.get()],
            "tf_streckenkunde": [k for k,v in self._tf_sk_vars.items() if v.get()],
            "tf_fahrzeuge": [k for k,v in self._tf_fz_vars.items() if v.get()],
            "zusatz_lizenzen": [k for k,v in self._zusatz_vars.items() if v.get()],
            "ts": self.existing.get("ts", now_str()) if self.existing else now_str(),
            "ts_edit": now_str(),
        }
        self.on_confirm(data)
        self.destroy()


class PersonalTab(tk.Frame):
    """Personal-Tab mit Login, Mitarbeiterliste und Cloud-Sync via GitHub Gist."""
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self._current_bn = None
        self._mitarbeiter = []
        self._lock = {}
        self._remember_var = tk.BooleanVar(value=True)
        self._build_login()
        # Prüfe gespeicherte Session
        sess = load_session()
        if sess.get("bn") and sess["bn"] in PERSONAL_ACCOUNTS:
            self._do_login(sess["bn"], from_session=True)

    # ─── Login-Screen ────────────────────────────────────────────────────────
    def _build_login(self):
        self._login_frame = tk.Frame(self, bg=C["BG"]); self._login_frame.pack(expand=True)
        # Logo-Bereich
        hf = tk.Frame(self._login_frame, bg=C["PRIMARY"]); hf.pack(fill="x", pady=(0,30))
        tk.Label(hf, text="🔐  Personal – Anmeldung", font=("Segoe UI",14,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(pady=18)
        # Card
        card = tk.Frame(self._login_frame, bg=C["PANEL"], highlightthickness=1,
                        highlightbackground=C["BORDER"])
        card.pack(padx=60, pady=0, ipadx=20, ipady=20)
        tk.Label(card, text="Benutzername (BN)", font=FONT_LABEL, bg=C["PANEL"], fg=C["SUBTEXT"]).pack(anchor="w", padx=20, pady=(14,2))
        self._bn_e = tk.Entry(card, font=FONT_INPUT, relief="flat", bg=C["BG"], fg=C["TEXT"],
                              insertbackground=C["TEXT"], highlightthickness=1,
                              highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"], width=28)
        self._bn_e.pack(padx=20, ipady=5, pady=(0,8))
        tk.Label(card, text="Passwort", font=FONT_LABEL, bg=C["PANEL"], fg=C["SUBTEXT"]).pack(anchor="w", padx=20, pady=(4,2))
        self._pw_e = tk.Entry(card, font=FONT_INPUT, relief="flat", bg=C["BG"], fg=C["TEXT"],
                              show="*", insertbackground=C["TEXT"], highlightthickness=1,
                              highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"], width=28)
        self._pw_e.pack(padx=20, ipady=5, pady=(0,10))
        self._pw_e.bind("<Return>", lambda e: self._try_login())
        rem_row = tk.Frame(card, bg=C["PANEL"]); rem_row.pack(anchor="w", padx=20)
        tk.Checkbutton(rem_row, variable=self._remember_var, bg=C["PANEL"],
                       activebackground=C["PANEL"], selectcolor=C["BG"], cursor="hand2").pack(side="left")
        tk.Label(rem_row, text="Angemeldet bleiben", font=FONT_LABEL, bg=C["PANEL"], fg=C["TEXT"]).pack(side="left", padx=4)
        self._login_lbl = tk.Label(card, text="", font=FONT_LABEL, bg=C["PANEL"], fg=C["DANGER"])
        self._login_lbl.pack(pady=(4,2))
        make_btn(card, "  Anmelden  ", self._try_login).pack(pady=(8,20))

    def _try_login(self):
        bn = self._bn_e.get().strip()
        pw = self._pw_e.get()
        if not bn or not pw:
            self._login_lbl.configure(text="Bitte BN und Passwort eingeben."); return
        pw_hash = hashlib.sha256(pw.encode()).hexdigest()
        if PERSONAL_ACCOUNTS.get(bn) != pw_hash:
            self._login_lbl.configure(text="Ungueltige Zugangsdaten."); return
        if self._remember_var.get():
            save_session(bn)
        self._do_login(bn)

    def _do_login(self, bn, from_session=False):
        self._current_bn = bn
        global _CURRENT_USER
        _CURRENT_USER["bn"] = bn
        _CURRENT_USER["roblox"] = bn
        _CURRENT_USER["rank"] = ""
        if hasattr(self, "_login_frame") and self._login_frame.winfo_exists():
            self._login_frame.destroy()
        self._build_main()
        self._load_data()

    # ─── Haupt-Screen (nach Login) ────────────────────────────────────────────
    def _build_main(self):
        self._main_frame = tk.Frame(self, bg=C["BG"]); self._main_frame.pack(fill="both", expand=True)
        # Toolbar
        tb = tk.Frame(self._main_frame, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=10)
        make_btn(tb, "+  Mitarbeiter hinzufuegen", self._open_add, pady=7).pack(side="left")
        make_btn(tb, "🔄  Aktualisieren", self._reload, bg="#557799", pady=7).pack(side="left", padx=8)
        # Abmelden
        make_btn(tb, f"Abmelden ({self._current_bn})", self._logout,
                 bg="#CCBBBB", fg=C["TEXT"], pady=7).pack(side="right")
        self._sync_lbl = tk.Label(tb, text="", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"])
        self._sync_lbl.pack(side="right", padx=12)
        # Tabelle Header
        hdr = tk.Frame(self._main_frame, bg=C["PRIMARY"]); hdr.pack(fill="x", padx=16)
        for txt, w, exp in [("#",3,False),("Roblox-Name",18,False),("Rang",6,False),
                             ("Lizenzen / Streckenkunde",0,True),("Zusatz",14,False),
                             ("Erstellt",12,False),("",7,False)]:
            l = tk.Label(hdr, text=txt, font=("Segoe UI",9,"bold"),
                         bg=C["PRIMARY"], fg="white", anchor="w", pady=8, padx=8)
            if w: l.configure(width=w)
            l.pack(side="left", fill="x" if exp else "none", expand=exp)
        # Liste
        outer = tk.Frame(self._main_frame, bg=C["BG"]); outer.pack(fill="both", expand=True, padx=16, pady=(0,16))
        self._pcanvas = tk.Canvas(outer, bg=C["BG"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=self._pcanvas.yview)
        self._pcanvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self._pcanvas.pack(side="left", fill="both", expand=True)
        self._prf = tk.Frame(self._pcanvas, bg=C["BG"])
        self._pcw = self._pcanvas.create_window((0,0), window=self._prf, anchor="nw")
        self._prf.bind("<Configure>", lambda e: self._pcanvas.configure(scrollregion=self._pcanvas.bbox("all")))
        self._pcanvas.bind("<Configure>", lambda e: self._pcanvas.itemconfig(self._pcw, width=e.width))
        self._pcanvas.bind_all("<MouseWheel>", lambda e: self._pcanvas.yview_scroll(int(-1*(e.delta/120)),"units"))

    def _logout(self):
        clear_session()
        self._current_bn = None
        global _CURRENT_USER
        _CURRENT_USER["bn"] = None; _CURRENT_USER["roblox"] = None; _CURRENT_USER["rank"] = None
        if hasattr(self, "_main_frame") and self._main_frame.winfo_exists():
            self._main_frame.destroy()
        self._build_login()

    # ─── Daten laden / speichern / sync ──────────────────────────────────────
    def _load_data(self):
        self._sync_lbl.configure(text="Lade Daten ...")
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        m, lock = personal_sync_load()
        if m is None:
            # Kein Gist konfiguriert – lokale Daten nutzen
            self.after(0, lambda: self._on_data_loaded([], {}))
        else:
            self.after(0, lambda: self._on_data_loaded(m, lock or {}))

    def _on_data_loaded(self, mitarbeiter, lock):
        self._mitarbeiter = mitarbeiter
        self._lock = lock
        global _CURRENT_USER
        if _CURRENT_USER["bn"]:
            for m in self._mitarbeiter:
                if m.get("bn", "").lower() == _CURRENT_USER["bn"].lower():
                    _CURRENT_USER["roblox"] = m.get("roblox", _CURRENT_USER["bn"])
                    _CURRENT_USER["rank"] = m.get("rank", "")
                    break
        self._sync_lbl.configure(text=f"Stand: {now_str()}")
        self._refresh_list()

    def _reload(self):
        self._load_data()

    def _save_and_sync(self, release_lock=True):
        if release_lock:
            self._lock.pop(str(self._editing_id), None) if hasattr(self,"_editing_id") else None
        ok, err = personal_sync_save(self._mitarbeiter, self._lock)
        if not ok:
            # Kein Gist – lokal ist ausreichend
            pass
        self._sync_lbl.configure(text=f"Gespeichert: {now_str()}")

    # ─── Edit-Lock ────────────────────────────────────────────────────────────
    def _try_acquire_lock(self, user_id):
        user_id = str(user_id)
        lock_info = self._lock.get(user_id)
        if lock_info and lock_info.get("bn") != self._current_bn:
            # Lock von jemand anderem – prüfe Alter (> 5 Min => stale)
            try:
                lock_ts = datetime.datetime.strptime(lock_info["ts"], "%d.%m.%Y %H:%M")
                age = (datetime.datetime.now() - lock_ts).total_seconds()
                if age < 300:
                    return False, lock_info.get("bn","?")
            except Exception:
                pass
        self._lock[user_id] = {"bn": self._current_bn, "ts": now_str()}
        return True, None

    def _release_lock(self, user_id):
        self._lock.pop(str(user_id), None)

    # ─── Liste anzeigen ──────────────────────────────────────────────────────
    def _refresh_list(self):
        for w in self._prf.winfo_children(): w.destroy()
        if not self._mitarbeiter:
            tk.Label(self._prf, text="Noch keine Mitarbeiter eingetragen.",
                     font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=40); return
        sorted_ma = sorted(self._mitarbeiter, key=lambda m: (RANK_OPTIONS.index(m.get("rank","HR")) if m.get("rank") in RANK_OPTIONS else 99, m.get("roblox","").lower()))
        for i, ma in enumerate(sorted_ma):
            rbg = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
            row = tk.Frame(self._prf, bg=rbg, highlightthickness=1, highlightbackground=C["BORDER"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=str(i+1), font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     width=3, anchor="w").pack(side="left", padx=8, pady=8)
            tk.Label(row, text=ma.get("roblox",""), font=("Segoe UI",10,"bold"),
                     bg=rbg, fg=C["TEXT"], width=18, anchor="w").pack(side="left", padx=4, pady=8)
            rank = ma.get("rank","")
            tk.Label(row, text=rank, font=("Segoe UI",8,"bold"),
                     bg=RANK_COLORS.get(rank,"#888"), fg="white",
                     padx=6, pady=2).pack(side="left", padx=6, pady=8)
            # Lizenzen
            lic_parts = []
            if ma.get("fdl_lizenzen"): lic_parts.append("FDL: " + ", ".join(ma["fdl_lizenzen"]))
            if ma.get("tf_streckenkunde"): lic_parts.append("SK: " + ", ".join(ma["tf_streckenkunde"]))
            if ma.get("tf_fahrzeuge"): lic_parts.append("FZ: " + ", ".join(ma["tf_fahrzeuge"]))
            lic_txt = "   ".join(lic_parts) if lic_parts else "–"
            tk.Label(row, text=lic_txt, font=FONT_TABLE, bg=rbg, fg=C["TEXT"],
                     anchor="w").pack(side="left", fill="x", expand=True, padx=4, pady=8)
            # Zusatz
            zusatz = ", ".join(ma.get("zusatz_lizenzen",[])) or "–"
            tk.Label(row, text=zusatz, font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     width=14, anchor="w").pack(side="left", padx=4, pady=8)
            tk.Label(row, text=ma.get("ts",""), font=("Segoe UI",8),
                     bg=rbg, fg=C["SUBTEXT"], width=12).pack(side="left", padx=4, pady=8)
            # Buttons
            d = tk.Label(row, text=" X ", font=("Segoe UI",11,"bold"), bg=rbg, fg=C["DANGER"], cursor="hand2")
            d.pack(side="right", padx=6, pady=8)
            d.bind("<Button-1>", lambda ev, m=ma: self._delete(m))
            e = tk.Label(row, text=" ✎ ", font=("Segoe UI",11), bg=rbg, fg="#4488CC", cursor="hand2")
            e.pack(side="right", padx=4, pady=8)
            e.bind("<Button-1>", lambda ev, m=ma: self._edit(m))

    # ─── CRUD ─────────────────────────────────────────────────────────────────
    def _open_add(self):
        try:
            PersonalUserPopup(self.winfo_toplevel(), self._add)
        except Exception as e:
            messagebox.showerror("Fehler", f"Popup konnte nicht geoeffnet werden:\n{e}", parent=self)

    def _add(self, data):
        self._mitarbeiter.append(data)
        global _CURRENT_USER
        if _CURRENT_USER["bn"] and _CURRENT_USER["bn"].lower() == data.get("bn", "").lower():
            _CURRENT_USER["roblox"] = data.get("roblox", _CURRENT_USER["bn"])
            _CURRENT_USER["rank"] = data.get("rank", "")
        threading.Thread(target=lambda: personal_sync_save(self._mitarbeiter, self._lock), daemon=True).start()
        self._sync_lbl.configure(text=f"Gespeichert: {now_str()}")
        self._refresh_list()

    def _edit(self, ma):
        uid = str(ma.get("id",""))
        ok, locked_by = self._try_acquire_lock(uid)
        if not ok:
            messagebox.showwarning("Gesperrt",
                f"Wird gerade von '{locked_by}' bearbeitet.\nBitte kurz warten.", parent=self)
            return
        threading.Thread(target=lambda: personal_sync_save(self._mitarbeiter, self._lock), daemon=True).start()
        def on_confirm(data):
            self._release_lock(uid)
            for i, m in enumerate(self._mitarbeiter):
                if str(m.get("id","")) == uid:
                    self._mitarbeiter[i] = data; break
            global _CURRENT_USER
            if _CURRENT_USER["bn"] and _CURRENT_USER["bn"].lower() == data.get("bn", "").lower():
                _CURRENT_USER["roblox"] = data.get("roblox", _CURRENT_USER["bn"])
                _CURRENT_USER["rank"] = data.get("rank", "")
            threading.Thread(target=lambda: personal_sync_save(self._mitarbeiter, self._lock), daemon=True).start()
            self._sync_lbl.configure(text=f"Gespeichert: {now_str()}")
            self._refresh_list()
        def on_cancel():
            self._release_lock(uid)
            threading.Thread(target=lambda: personal_sync_save(self._mitarbeiter, self._lock), daemon=True).start()
        popup = PersonalUserPopup(self.winfo_toplevel(), on_confirm, existing=ma)
        popup.protocol("WM_DELETE_WINDOW", lambda: (on_cancel(), popup.destroy()))

    def _delete(self, ma):
        if messagebox.askyesno("Loeschen?",
                f"Mitarbeiter '{ma.get('roblox','')}' wirklich loeschen?", parent=self):
            self._mitarbeiter = [m for m in self._mitarbeiter if str(m.get("id","")) != str(ma.get("id",""))]
            threading.Thread(target=lambda: personal_sync_save(self._mitarbeiter, self._lock), daemon=True).start()
            self._sync_lbl.configure(text=f"Geloescht: {now_str()}")
            self._refresh_list()


# ════════════════════════════════════════════════════════════════════════
# TRAININGS TAB
# ════════════════════════════════════════════════════════════════════════

class TrainingPopup(tk.Toplevel):
    """Training anlegen oder bearbeiten."""
    def __init__(self, parent, on_confirm, existing=None, mitarbeiter_list=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.existing   = existing
        self.mitarbeiter_list = mitarbeiter_list or []
        self.title("Training bearbeiten" if existing else "Neues Training")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.withdraw()
        self._build()
        self.update_idletasks()
        w, h = 480, 520
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify(); self.grab_set()

    def _build(self):
        hdr = tk.Frame(self, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text="Training bearbeiten" if self.existing else "Neues Training",
                 font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"),
                     bg=C["PRIMARY"], fg="white", cursor="hand2")
        x.pack(side="right", padx=8); x.bind("<Button-1>", lambda e: self.destroy())
        body = tk.Frame(self, bg=C["BG"]); body.pack(fill="both", expand=True, padx=20, pady=14)
        ex = self.existing or {}
        # Titel
        tk.Label(body, text="Titel", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.titel_e = tk.Entry(body, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                                insertbackground=C["TEXT"], highlightthickness=1,
                                highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        self.titel_e.pack(fill="x", ipady=5, pady=4)
        self.titel_e.insert(0, ex.get("titel",""))
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        # Datum/Zeit
        dr = tk.Frame(body, bg=C["BG"]); dr.pack(fill="x")
        dl = tk.Frame(dr, bg=C["BG"]); dl.pack(side="left", fill="x", expand=True)
        tk.Label(dl, text="Datum (TT.MM.JJJJ)", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.datum_e = tk.Entry(dl, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                                insertbackground=C["TEXT"], highlightthickness=1,
                                highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        self.datum_e.pack(fill="x", ipady=5, pady=4)
        self.datum_e.insert(0, ex.get("datum",""))
        dr2 = tk.Frame(dr, bg=C["BG"]); dr2.pack(side="left", fill="x", expand=True, padx=(10,0))
        tk.Label(dr2, text="Zeit (HH:MM)", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.zeit_e = tk.Entry(dr2, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                               insertbackground=C["TEXT"], highlightthickness=1,
                               highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        self.zeit_e.pack(fill="x", ipady=5, pady=4)
        self.zeit_e.insert(0, ex.get("zeit",""))
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        # Host + Helper (Auswahl aus Mitarbeiterliste)
        namen = [m.get("roblox","?") for m in self.mitarbeiter_list] if self.mitarbeiter_list else []
        if not namen:
            namen = [""]
        tk.Label(body, text="Host (Ausbilder/Leiter)", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.host_var = tk.StringVar(value=ex.get("host",""))
        ttk.Combobox(body, textvariable=self.host_var, values=namen,
                     state="normal", font=FONT_INPUT).pack(fill="x", pady=4)
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        tk.Label(body, text="Helfer (bis zu 3)", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.helper_vars = []
        for i in range(3):
            var = tk.StringVar(value=ex.get("helpers",["","",""])[i] if i < len(ex.get("helpers",[])) else "")
            self.helper_vars.append(var)
            ttk.Combobox(body, textvariable=var, values=namen,
                         state="normal", font=FONT_INPUT, width=40).pack(fill="x", pady=2)
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)
        # Platzanzahl
        tk.Label(body, text="Maximale Teilnehmerzahl", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        self.max_e = tk.Entry(body, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                              insertbackground=C["TEXT"], highlightthickness=1,
                              highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"], width=8)
        self.max_e.pack(anchor="w", ipady=5, pady=4)
        self.max_e.insert(0, str(ex.get("max_participants",10)))
        br = tk.Frame(body, bg=C["BG"]); br.pack(fill="x", pady=(14,0))
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Speichern  ", self._confirm).pack(side="right")

    def _confirm(self):
        titel = self.titel_e.get().strip()
        datum = self.datum_e.get().strip()
        zeit  = self.zeit_e.get().strip()
        host  = self.host_var.get().strip()
        helpers = [v.get().strip() for v in self.helper_vars if v.get().strip()]
        try:
            max_p = int(self.max_e.get().strip())
        except ValueError:
            messagebox.showwarning("Fehler","Bitte gueltige Zahl fuer Teilnehmer eingeben.",parent=self); return
        if not titel or not datum or not zeit or not host:
            messagebox.showwarning("Fehler","Bitte Titel, Datum, Zeit und Host eingeben.",parent=self); return
        # Helper duerfen nicht gleich dem Host sein
        for h in helpers:
            if h == host:
                messagebox.showwarning("Fehler","Ein Helfer kann nicht der Host sein.",parent=self); return
        ex = self.existing or {}
        data = {
            "id": ex.get("id", int(time.time()*1000)) if self.existing else int(time.time()*1000),
            "titel": titel, "datum": datum, "zeit": zeit,
            "host": host, "helpers": helpers,
            "max_participants": max_p,
            "participants": ex.get("participants", []),
            "ts": ex.get("ts", now_str()) if self.existing else now_str(),
            "ts_edit": now_str(),
        }
        self.on_confirm(data); self.destroy()


class TrainingsTab(tk.Frame):
    """Trainings-Termine mit Anmeldung fuer Azubis."""
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self._trainings = []
        self._mitarbeiter = []
        self._load_local()
        self._build_toolbar()
        self._build_list()
        self._refresh()
        # Im Hintergrund vom Gist laden (falls verfuegbar)
        threading.Thread(target=self._sync_load, daemon=True).start()

    def _load_local(self):
        try:
            self._trainings = load_json(TRAININGS_FILE)
        except Exception:
            self._trainings = []

    def _save_local(self):
        save_json(TRAININGS_FILE, self._trainings)

    def _sync_load(self):
        try:
            data = gist_load_data(TRAININGS_GIST_FILENAME)
            if data is not None and isinstance(data, list):
                self._trainings = data
                self._save_local()
                self.after(0, self._refresh)
        except Exception:
            pass
        # Auch Mitarbeiter laden fuer die Dropdowns
        try:
            m, _ = personal_sync_load()
            if m is not None:
                self._mitarbeiter = m
        except Exception:
            pass

    def _sync_save(self):
        threading.Thread(target=lambda: gist_sync_data(
            TRAININGS_GIST_FILENAME,
            json.dumps(self._trainings, ensure_ascii=False, indent=2)
        ), daemon=True).start()

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=10)
        make_btn(tb, "+  Training erstellen", self._open_add, pady=7).pack(side="left")
        make_btn(tb, "🔄  Sync", self._manual_sync, bg="#557799", pady=7).pack(side="left", padx=8)
        # Aktueller User-Status
        global _CURRENT_USER
        status = f"Angemeldet als: {_CURRENT_USER['bn'] or 'nicht eingeloggt'}"
        if _CURRENT_USER["rank"] in AZUBI_RANKS:
            status += f"  |  Rang: {_CURRENT_USER['rank']}  |  Kann sich anmelden"
        elif _CURRENT_USER["bn"]:
            status += f"  |  Rang: {_CURRENT_USER['rank'] or '?'}"
        self._status_lbl = tk.Label(tb, text=status, font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"])
        self._status_lbl.pack(side="right", padx=8)
        self._sync_lbl = tk.Label(tb, text="", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"])
        self._sync_lbl.pack(side="right")

    def _manual_sync(self):
        self._sync_lbl.configure(text="Sync ...")
        threading.Thread(target=self._sync_load, daemon=True).start()

    def _build_list(self):
        outer = tk.Frame(self, bg=C["BG"]); outer.pack(fill="both", expand=True, padx=16, pady=(0,16))
        # Header
        hdr = tk.Frame(outer, bg=C["PRIMARY"]); hdr.pack(fill="x")
        for txt, w, exp in [("#",3,False),("Titel",18,False),("Datum",12,False),("Zeit",8,False),
                             ("Host",14,False),("Helfer",18,False),("Plaetze",10,False),("",14,False)]:
            l = tk.Label(hdr, text=txt, font=("Segoe UI",9,"bold"),
                         bg=C["PRIMARY"], fg="white", anchor="w", pady=8, padx=6)
            if w: l.configure(width=w)
            l.pack(side="left", fill="x" if exp else "none", expand=exp)
        # Liste
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
        global _CURRENT_USER
        if not self._trainings:
            tk.Label(self.rf, text="Keine Trainings angelegt.", font=FONT_LABEL,
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=40); return
        sorted_t = sorted(self._trainings, key=lambda t: t.get("datum","") + t.get("zeit",""), reverse=True)
        is_azubi = _CURRENT_USER["rank"] in AZUBI_RANKS
        current_user_bn = _CURRENT_USER["bn"]
        for i, tr in enumerate(sorted_t):
            rbg = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
            row = tk.Frame(self.rf, bg=rbg, highlightthickness=1, highlightbackground=C["BORDER"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=str(i+1), font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     width=3, anchor="w").pack(side="left", padx=6, pady=8)
            tk.Label(row, text=tr.get("titel",""), font=("Segoe UI",10,"bold"),
                     bg=rbg, fg=C["TEXT"], width=18, anchor="w").pack(side="left", padx=4, pady=8)
            tk.Label(row, text=tr.get("datum",""), font=FONT_TABLE, bg=rbg, fg=C["TEXT"],
                     width=12, anchor="w").pack(side="left", padx=4, pady=8)
            tk.Label(row, text=tr.get("zeit",""), font=FONT_TABLE, bg=rbg, fg=C["TEXT"],
                     width=8, anchor="w").pack(side="left", padx=4, pady=8)
            tk.Label(row, text=tr.get("host",""), font=FONT_TABLE, bg=rbg, fg=C["TEXT"],
                     width=14, anchor="w").pack(side="left", padx=4, pady=8)
            helpers = ", ".join(tr.get("helpers",[])) or "–"
            tk.Label(row, text=helpers, font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     width=18, anchor="w").pack(side="left", padx=4, pady=8)
            # Plaetze
            max_p = tr.get("max_participants",0)
            cur_p = len(tr.get("participants",[]))
            full = cur_p >= max_p
            platz_txt = f"{cur_p}/{max_p}"
            platz_col = "#E74C3C" if full else "#27AE60"
            tk.Label(row, text=platz_txt, font=("Segoe UI",9,"bold"),
                     bg=rbg, fg=platz_col, width=10, anchor="w").pack(side="left", padx=4, pady=8)
            # Anmelden/Abmelden Button
            is_signed_up = current_user_bn and current_user_bn in tr.get("participants",[])
            if is_azubi and current_user_bn:
                if is_signed_up:
                    b = tk.Button(row, text="Abmelden", font=("Segoe UI",8,"bold"),
                                  bg="#CCBBBB", fg=C["TEXT"], relief="flat", cursor="hand2",
                                  padx=8, pady=2, bd=0,
                                  command=lambda t=tr: self._anmelden(t, current_user_bn))
                    b.pack(side="left", padx=4)
                elif full:
                    tk.Label(row, text="Voll", font=("Segoe UI",8,"bold"),
                             bg=rbg, fg="#E74C3C", padx=8).pack(side="left")
                else:
                    b = tk.Button(row, text="Anmelden", font=("Segoe UI",8,"bold"),
                                  bg="#27AE60", fg="white", relief="flat", cursor="hand2",
                                  padx=8, pady=2, bd=0,
                                  command=lambda t=tr: self._anmelden(t, current_user_bn))
                    b.pack(side="left", padx=4)
            elif is_signed_up:
                tk.Label(row, text="Angemeldet", font=("Segoe UI",8,"bold"),
                         bg=rbg, fg="#27AE60", padx=8).pack(side="left")
            # Bearbeiten/Loeschen (nur eingeloggt)
            if current_user_bn:
                d = tk.Label(row, text=" X ", font=("Segoe UI",11,"bold"), bg=rbg, fg=C["DANGER"], cursor="hand2")
                d.pack(side="right", padx=4, pady=8)
                d.bind("<Button-1>", lambda ev, t=tr: self._delete(t))
                e_lbl = tk.Label(row, text=" ✎ ", font=("Segoe UI",11), bg=rbg, fg="#4488CC", cursor="hand2")
                e_lbl.pack(side="right", padx=4, pady=8)
                e_lbl.bind("<Button-1>", lambda ev, t=tr: self._edit(t))

    def _anmelden(self, training, bn):
        idx = None
        for i, t in enumerate(self._trainings):
            if t.get("id") == training.get("id"):
                idx = i; break
        if idx is None: return
        tr = self._trainings[idx]
        parts = tr.get("participants",[])
        if bn in parts:
            parts.remove(bn)
        else:
            if len(parts) >= tr.get("max_participants",0):
                messagebox.showwarning("Voll","Alle Plaetze sind belegt.", parent=self); return
            parts.append(bn)
        tr["participants"] = parts
        self._save_local()
        self._sync_save()
        self._refresh()

    def _open_add(self):
        if not _CURRENT_USER["bn"]:
            messagebox.showwarning("Hinweis","Bitte zuerst im Personal-Tab anmelden.", parent=self); return
        if not self._mitarbeiter:
            threading.Thread(target=self._sync_load, daemon=True).start()
        TrainingPopup(self.winfo_toplevel(), self._add, mitarbeiter_list=self._mitarbeiter)

    def _add(self, data):
        self._trainings.append(data)
        self._save_local()
        self._sync_save()
        self._refresh()

    def _edit(self, training):
        if not _CURRENT_USER["bn"]:
            messagebox.showwarning("Hinweis","Bitte zuerst anmelden.", parent=self); return
        def apply(data):
            for i, t in enumerate(self._trainings):
                if t.get("id") == training.get("id"):
                    self._trainings[i] = data; break
            self._save_local()
            self._sync_save()
            self._refresh()
        TrainingPopup(self.winfo_toplevel(), apply, existing=training,
                      mitarbeiter_list=self._mitarbeiter)

    def _delete(self, training):
        if not _CURRENT_USER["bn"]:
            return
        if messagebox.askyesno("Loeschen?",
                f"Training '{training.get('titel','')}' wirklich loeschen?", parent=self):
            self._trainings = [t for t in self._trainings if t.get("id") != training.get("id")]
            self._save_local()
            self._sync_save()
            self._refresh()


# ════════════════════════════════════════════════════════════════════════
# SETTINGS TAB
# ════════════════════════════════════════════════════════════════════════
class SettingsTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=C["BG"])
        self.app = app
        self._build()

    def _build(self):
        canvas = tk.Canvas(self, bg=C["BG"], highlightthickness=0)
        vsb = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=C["BG"])
        cw = canvas.create_window((0,0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        def section(parent, title):
            f = tk.Frame(parent, bg=C["PANEL"]); f.pack(fill="x", padx=32, pady=8)
            tk.Label(f, text=f"  {title}", font=("Segoe UI",11,"bold"),
                     bg=C["PRIMARY"], fg="white").pack(fill="x")
            return f

        # ── Stellwerke ────────────────────────────────────────────────────────
        s1 = section(inner, "Stellwerke konfigurieren")
        tk.Label(s1, text="Bis zu 10 Stellwerke (eines pro Zeile):",
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
        self._dm_var = tk.BooleanVar(value=SETTINGS.get("dark_mode",False))
        tk.Checkbutton(dm_row, variable=self._dm_var, command=self._toggle_dark,
                       bg=C["PANEL"], activebackground=C["PANEL"],
                       selectcolor=C["BG"], cursor="hand2").pack(side="left", padx=8)
        self._dm_lbl = tk.Label(dm_row, text="Dunkel" if self._dm_var.get() else "Hell",
                                font=("Segoe UI",9,"bold"), bg=C["PANEL"], fg=C["PRIMARY"])
        self._dm_lbl.pack(side="left")
        tk.Frame(s2, bg=C["PANEL"], height=6).pack()
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", padx=32, pady=2)

        # ── Schichtplan ──────────────────────────────────────────────────────
        s2c = section(inner, "Schichtplan")
        short = SCHICHTPLAN_GSHEET_URL[:70] + ("..." if len(SCHICHTPLAN_GSHEET_URL) > 70 else "")
        status = "✔  Link ist gesetzt" if "DEINE_SHEET_ID" not in SCHICHTPLAN_GSHEET_URL else "⚠  Noch nicht konfiguriert"
        col_s = "#27AE60" if "DEINE_SHEET_ID" not in SCHICHTPLAN_GSHEET_URL else "#E74C3C"
        tk.Label(s2c,
                 text="Der Google-Sheets-Link ist fest im Skript hinterlegt\n"
                      "(Konstante SCHICHTPLAN_GSHEET_URL).\n"
                      "Aenderungen direkt dort vornehmen.",
                 font=FONT_LABEL, bg=C["PANEL"], fg=C["SUBTEXT"], justify="left").pack(anchor="w", padx=16, pady=(8,4))
        tk.Label(s2c, text=status, font=("Segoe UI",9,"bold"),
                 bg=C["PANEL"], fg=col_s).pack(anchor="w", padx=16)
        tk.Label(s2c, text=short, font=("Segoe UI",8),
                 bg=C["PANEL"], fg=C["SUBTEXT"]).pack(anchor="w", padx=16, pady=(2,14))
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", padx=32, pady=2)

        # ── Cloud-Sync (GitHub Gist) ──────────────────────────────────────────
        s_gist = section(inner, "Cloud-Sync (GitHub Gist)")
        gist_status = "✔  Konfiguriert" if GIST_URL and GIST_TOKEN else "⚠  Bitte in der Skript-Datei eintragen"
        gist_col = "#27AE60" if GIST_URL and GIST_TOKEN else "#E74C3C"
        tk.Label(s_gist,
                 text="Gist-URL und Token werden fest im Skript definiert\n"
                      "(Konstanten GIST_URL und GIST_TOKEN, ca. Zeile 175).\n"
                      "Personal-, Trainings- und Termin-Daten werden ueber diesen Gist synchronisiert.",
                 font=FONT_LABEL, bg=C["PANEL"], fg=C["SUBTEXT"], justify="left").pack(anchor="w", padx=16, pady=(8,6))
        tk.Label(s_gist, text=gist_status, font=("Segoe UI",9,"bold"),
                 bg=C["PANEL"], fg=gist_col).pack(anchor="w", padx=16)
        tk.Label(s_gist, text=f"Gist-URL: {GIST_URL[:60] + '...' if len(GIST_URL) > 60 else GIST_URL or '(leer)'}",
                 font=("Segoe UI",8), bg=C["PANEL"], fg=C["SUBTEXT"]).pack(anchor="w", padx=16, pady=(2,14))
        tk.Frame(inner, bg=C["BORDER"], height=1).pack(fill="x", padx=32, pady=2)

        # ── Personal Accounts ─────────────────────────────────────────────────
        s_acc = section(inner, "Personal-Accounts (im Skript)")
        tk.Label(s_acc,
                 text="Accounts werden direkt im Skript definiert (PERSONAL_ACCOUNTS-Dictionary).\n"
                      "Format: 'BN': hashlib.sha256('passwort'.encode()).hexdigest()\n"
                      "Aktuell konfigurierte Accounts: " + ", ".join(PERSONAL_ACCOUNTS.keys()),
                 font=FONT_LABEL, bg=C["PANEL"], fg=C["SUBTEXT"], justify="left").pack(anchor="w", padx=16, pady=(8,14))
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
            hf2 = tk.Frame(vf, bg=C["PRIMARY"]); hf2.pack(fill="x")
            tk.Label(hf2, text=f"  {version}", font=("Segoe UI",10,"bold"),
                     bg=C["PRIMARY"], fg="white").pack(side="left", pady=6, padx=4)
            tk.Label(hf2, text=date, font=("Segoe UI",9),
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
        SETTINGS["stw_options"] = list(STW_OPTIONS); save_settings(SETTINGS)
        self.stw_text.delete("1.0","end"); self.stw_text.insert("1.0", "\n".join(STW_OPTIONS))
        self._stw_lbl.configure(text=f"Gespeichert ({len(STW_OPTIONS)} Stellwerke). Neustart fuer Filter-Update.")
        self.after(5000, lambda: self._stw_lbl.configure(text=""))

    def _reset_stw(self):
        global STW_OPTIONS
        STW_OPTIONS.clear(); STW_OPTIONS.extend(DEFAULT_STW_OPTIONS)
        SETTINGS["stw_options"] = list(STW_OPTIONS); save_settings(SETTINGS)
        self.stw_text.delete("1.0","end"); self.stw_text.insert("1.0", "\n".join(STW_OPTIONS))
        self._stw_lbl.configure(text="Auf Standard zurueckgesetzt.")
        self.after(3000, lambda: self._stw_lbl.configure(text=""))

    def _toggle_dark(self):
        dark = self._dm_var.get(); SETTINGS["dark_mode"] = dark; save_settings(SETTINGS)
        self._dm_lbl.configure(text="Dunkel" if dark else "Hell"); self.app._apply_dark(dark)


class STWTab(BaseTab):
    def __init__(self, parent): super().__init__(parent, DATA_FILE, tf_mode=False)

class TFTab(BaseTab):
    def __init__(self, parent): super().__init__(parent, TF_FILE, tf_mode=True)


class NotizenApp(tk.Tk):
    def __init__(self):
        super().__init__()
        global _APP_INSTANCE
        _APP_INSTANCE = self
        self.title("Stellwerk Notizen")
        self.geometry("1200x720")
        self.minsize(900,540)
        self.configure(bg=C["BG"])
        self._dark = SETTINGS.get("dark_mode",False)
        self._always_top = False
        self._build_header()
        self._build_tabs()
        start_background_services()
        self._poll_event_queue()

    def _poll_event_queue(self):
        try:
            while True:
                kind, payload = _EVENT_QUEUE.get_nowait()
                if kind == "schichtplan": _on_schichtplan_update(payload)
        except queue.Empty:
            pass
        self.after(250, self._poll_event_queue)

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
        for name, cls in [
            ("Stellwerksnotizen", STWTab),
            ("TF Notizen", TFTab),
            ("Fahrtenliste", FahrtenTab),
            ("Netzplan", NetzplanTab),
            ("Schichtplan", SchichtplanTab),
            ("Personal", PersonalTab),
            ("Trainings", TrainingsTab),
            ("Termine / Inactivity", TermineTab),
            ("Einstellungen", None),
        ]:
            frame = cls(self._tab_content) if cls else SettingsTab(self._tab_content, self)
            self._tabs[name] = frame
            btn = tk.Button(self._tab_bar, text=name, font=("Segoe UI",9,"bold"),
                            bg=C["PRIMARY"], fg="white", relief="flat", cursor="hand2",
                            padx=14, pady=8, bd=0, command=lambda n=name: self._switch(n))
            btn.pack(side="left", padx=3); self._tab_btns[name] = btn
        self._switch("Stellwerksnotizen")

    def _switch(self, name):
        for f in self._tabs.values(): f.pack_forget()
        self._tabs[name].pack(fill="both", expand=True)
        for n,b in self._tab_btns.items():
            b.configure(bg=C["PRIMARY"] if n==name else C["BORDER"],
                        fg="white" if n==name else C["TEXT"])

    def _apply_dark(self, dark):
        self._dark = dark; C.update(DARK if dark else LIGHT)
        for w in self.winfo_children(): w.destroy()
        self.configure(bg=C["BG"]); self._build_header(); self._build_tabs()

    def _toggle_dark_header(self):
        new_dark = not self._dark; SETTINGS["dark_mode"] = new_dark; save_settings(SETTINGS)
        self._apply_dark(new_dark)

    def _toggle_top(self):
        self._always_top = not self._always_top
        self.attributes("-topmost", self._always_top)
        self._top_btn.configure(text="Vorne (an)" if self._always_top else "Vorne",
                                bg="#8B0000" if self._always_top else C["PRIMARY_H"])


# ════════════════════════════════════════════════════════════════════════
# TERMINE / INACTIVITY TAB
# ════════════════════════════════════════════════════════════════════════

TERMINE_FILE = os.path.join(BASE_DIR, "termine_data.json")

ANWESENHEIT_OPTIONS = [
    ("Anwesend",             "#27AE60"),
    ("Fehlt ohne Abmeldung", "#C0392B"),
    ("Nimmt nicht teil",     "#7F7F7F"),
    ("Entschuldigt Abgemeldet", "#F39C12"),
]


class TerminPopup(tk.Toplevel):
    """Termin anlegen oder bearbeiten."""
    def __init__(self, parent, on_confirm, existing=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self.existing   = existing
        self.title("Termin bearbeiten" if existing else "Neuer Termin")
        self.resizable(False, False)
        self.configure(bg=C["BG"])
        self.withdraw()
        self._build()
        self.update_idletasks()
        w, h = 440, max(min(self.winfo_reqheight()+20, self.winfo_screenheight()-80), 360)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify()
        self.grab_set()

    def _entry(self, parent, label, value="", placeholder=""):
        tk.Label(parent, text=label, font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        e = tk.Entry(parent, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                     insertbackground=C["TEXT"], highlightthickness=1,
                     highlightbackground=C["BORDER"], highlightcolor=C["PRIMARY"])
        e.pack(fill="x", ipady=5, pady=4)
        if value:
            e.insert(0, value)
        elif placeholder:
            e.insert(0, placeholder)
            e.configure(fg=C["SUBTEXT"])
            def on_focus_in(event, entry=e, ph=placeholder):
                if entry.get() == ph:
                    entry.delete(0, "end")
                    entry.configure(fg=C["TEXT"])
            def on_focus_out(event, entry=e, ph=placeholder):
                if not entry.get():
                    entry.insert(0, ph)
                    entry.configure(fg=C["SUBTEXT"])
            e.bind("<FocusIn>", on_focus_in)
            e.bind("<FocusOut>", on_focus_out)
        return e

    def _build(self):
        hdr = tk.Frame(self, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text="Termin bearbeiten" if self.existing else "Neuer Termin",
                 font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"),
                     bg=C["PRIMARY"], fg="white", cursor="hand2")
        x.pack(side="right", padx=8)
        x.bind("<Button-1>", lambda e: self.destroy())

        body = tk.Frame(self, bg=C["BG"]); body.pack(fill="both", expand=True, padx=20, pady=14)
        ex = self.existing or {}

        self.titel_e = self._entry(body, "Titel / Schicht", ex.get("titel",""))
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        tk.Label(body, text="Beschreibung", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w")
        wrap = tk.Frame(body, bg=C["BORDER"]); wrap.pack(fill="x", pady=4)
        self.desc_t = tk.Text(wrap, font=FONT_INPUT, relief="flat", bg=C["PANEL"], fg=C["TEXT"],
                              insertbackground=C["TEXT"], wrap="word", height=3, padx=6, pady=6)
        self.desc_t.pack(fill="x", padx=1, pady=1)
        if ex.get("beschreibung"):
            self.desc_t.insert("1.0", ex["beschreibung"])
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=6)

        # Von / Bis in einer Zeile
        drow = tk.Frame(body, bg=C["BG"]); drow.pack(fill="x")
        dl = tk.Frame(drow, bg=C["BG"]); dl.pack(side="left", fill="x", expand=True)
        self.von_e = self._entry(dl, "Von (TT.MM.YYYY HH:MM)", ex.get("von",""), "01.01.2025 18:00")
        dr = tk.Frame(drow, bg=C["BG"]); dr.pack(side="left", fill="x", expand=True, padx=(10,0))
        self.bis_e = self._entry(dr, "Bis (TT.MM.YYYY HH:MM)", ex.get("bis",""), "01.01.2025 20:00")
        tk.Frame(body, bg=C["BORDER"], height=1).pack(fill="x", pady=10)

        br = tk.Frame(body, bg=C["BG"]); br.pack(fill="x")
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Speichern  ", self._confirm).pack(side="right")

    def _confirm(self):
        titel = self.titel_e.get().strip()
        von   = self.von_e.get().strip()
        bis   = self.bis_e.get().strip()
        # Platzhalter abfangen
        if von in ("01.01.2025 18:00",): von = ""
        if bis in ("01.01.2025 20:00",): bis = ""
        if not titel:
            messagebox.showwarning("Fehler","Bitte Titel eingeben.", parent=self); return
        if not von or not bis:
            messagebox.showwarning("Fehler","Bitte Von und Bis eingeben.", parent=self); return
        ex = self.existing or {}
        data = {
            "id":    ex.get("id", int(time.time()*1000)) if self.existing else int(time.time()*1000),
            "titel": titel,
            "beschreibung": self.desc_t.get("1.0","end").strip(),
            "von":   von,
            "bis":   bis,
            "ts":    ex.get("ts", now_str()) if self.existing else now_str(),
            "ts_edit": now_str(),
            "anwesenheit": ex.get("anwesenheit", {}),
        }
        self.on_confirm(data)
        self.destroy()


class AnwesenheitPopup(tk.Toplevel):
    """Zeigt alle Personal-User und erlaubt Anwesenheits-Erfassung für einen Termin."""
    def __init__(self, parent, termin, mitarbeiter, on_save):
        super().__init__(parent)
        self.termin      = termin
        self.mitarbeiter = mitarbeiter
        self.on_save     = on_save
        self.title(f"Anwesenheit – {termin.get('titel','')}")
        self.resizable(True, True)
        self.configure(bg=C["BG"])
        self.withdraw()
        self._vars = {}   # user_id -> StringVar
        self._build()
        self.update_idletasks()
        w = 720
        h = min(80 + 60*max(len(mitarbeiter),1) + 80, self.winfo_screenheight()-80)
        h = max(h, 360)
        px = parent.winfo_rootx()+(parent.winfo_width()-w)//2
        py = max(10, parent.winfo_rooty()+(parent.winfo_height()-h)//2)
        self.geometry(f"{w}x{h}+{px}+{py}")
        self.deiconify()
        self.grab_set()

    def _build(self):
        hdr = tk.Frame(self, bg=C["PRIMARY"]); hdr.pack(fill="x")
        tk.Label(hdr, text=f"Anwesenheit: {self.termin.get('titel','')}",
                 font=("Segoe UI",12,"bold"), bg=C["PRIMARY"], fg="white").pack(side="left", padx=16, pady=12)
        tk.Label(hdr, text=f"{self.termin.get('von','')} – {self.termin.get('bis','')}",
                 font=("Segoe UI",9), bg=C["PRIMARY"], fg="#FFE5E5").pack(side="left", padx=8)
        x = tk.Label(hdr, text="  X  ", font=("Segoe UI",12,"bold"),
                     bg=C["PRIMARY"], fg="white", cursor="hand2")
        x.pack(side="right", padx=8)
        x.bind("<Button-1>", lambda e: self.destroy())

        # Legende / Spaltenheader
        col_hdr = tk.Frame(self, bg=C["BG"]); col_hdr.pack(fill="x", padx=16, pady=(8,2))
        tk.Label(col_hdr, text="Mitarbeiter", font=("Segoe UI",9,"bold"),
                 bg=C["BG"], fg=C["TEXT"], width=22, anchor="w").pack(side="left")
        tk.Label(col_hdr, text="Rang", font=("Segoe UI",9,"bold"),
                 bg=C["BG"], fg=C["TEXT"], width=6, anchor="w").pack(side="left")
        for lbl, col in ANWESENHEIT_OPTIONS:
            tk.Label(col_hdr, text=lbl, font=("Segoe UI",8,"bold"),
                     bg=col, fg="white", padx=6, pady=3,
                     width=max(len(lbl)//2+2, 10), anchor="center").pack(side="left", padx=3)

        # Scrollbare Liste
        outer = tk.Frame(self, bg=C["BG"]); outer.pack(fill="both", expand=True, padx=16, pady=(0,8))
        canvas = tk.Canvas(outer, bg=C["BG"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); canvas.pack(side="left", fill="both", expand=True)
        rf = tk.Frame(canvas, bg=C["BG"])
        cw = canvas.create_window((0,0), window=rf, anchor="nw")
        rf.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        if not self.mitarbeiter:
            tk.Label(rf, text="Keine Mitarbeiter angelegt (Personal-Tab).",
                     font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=30)
        else:
            existing_aw = self.termin.get("anwesenheit", {})
            sorted_ma = sorted(self.mitarbeiter,
                               key=lambda m: (RANK_OPTIONS.index(m.get("rank","HR"))
                                              if m.get("rank") in RANK_OPTIONS else 99,
                                              m.get("roblox","").lower()))
            for i, ma in enumerate(sorted_ma):
                uid  = str(ma.get("id",""))
                rbg  = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
                row  = tk.Frame(rf, bg=rbg, highlightthickness=1, highlightbackground=C["BORDER"])
                row.pack(fill="x", pady=1)

                # Name + Rang
                tk.Label(row, text=ma.get("roblox",""), font=("Segoe UI",9,"bold"),
                         bg=rbg, fg=C["TEXT"], width=22, anchor="w").pack(side="left", padx=8, pady=8)
                rank = ma.get("rank","")
                tk.Label(row, text=rank, font=("Segoe UI",8,"bold"),
                         bg=RANK_COLORS.get(rank,"#888"), fg="white",
                         padx=4, pady=2, width=5, anchor="center").pack(side="left", padx=4)

                # Radio-Buttons für die 4 Zustände
                var = tk.StringVar(value=existing_aw.get(uid, ""))
                self._vars[uid] = var
                for lbl, col in ANWESENHEIT_OPTIONS:
                    rb = tk.Radiobutton(
                        row, variable=var, value=lbl,
                        bg=rbg, activebackground=rbg,
                        selectcolor=col,
                        cursor="hand2", relief="flat", bd=0,
                        indicatoron=True
                    )
                    # Farbiges Label daneben
                    inner_f = tk.Frame(row, bg=rbg); inner_f.pack(side="left", padx=6, pady=6)
                    rb2 = tk.Radiobutton(inner_f, variable=var, value=lbl, text="",
                                         bg=rbg, activebackground=rbg, selectcolor=col,
                                         cursor="hand2", relief="flat", bd=0)
                    rb2.pack(side="left")
                    # Klickbares Farb-Label als Schnell-Button
                    btn_f = tk.Frame(inner_f,
                                     bg=col if var.get()==lbl else C["BORDER"],
                                     highlightthickness=1, highlightbackground=C["BORDER"],
                                     cursor="hand2")
                    btn_f.pack(side="left")
                    btn_lbl = tk.Label(btn_f, text="✔" if var.get()==lbl else " ",
                                       font=("Segoe UI",9,"bold"), bg=btn_f["bg"],
                                       fg="white", padx=8, pady=3, cursor="hand2")
                    btn_lbl.pack()

                    def make_click(v=var, val=lbl, bf=btn_f, bl=btn_lbl, uid=uid):
                        def click(e=None):
                            v.set(val)
                            # Alle Buttons dieser Zeile neu rendern via refresh
                            self._refresh_row_btns(uid)
                        return click

                    btn_f.bind("<Button-1>", make_click())
                    btn_lbl.bind("<Button-1>", make_click())
                    rb2.configure(command=make_click())

        # Speichern-Button
        br = tk.Frame(self, bg=C["BG"]); br.pack(fill="x", padx=16, pady=(4,14))
        make_btn(br, "Abbrechen", self.destroy, bg="#CCBBBB", fg=C["TEXT"]).pack(side="right", padx=6)
        make_btn(br, "  Anwesenheit speichern  ", self._save).pack(side="right")
        # Schnell-Buttons: Alle auf einen Status setzen
        tk.Label(br, text="Alle setzen:", font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(side="left")
        for lbl, col in ANWESENHEIT_OPTIONS:
            b = tk.Button(br, text=lbl[:8], font=("Segoe UI",8,"bold"),
                          bg=col, fg="white", relief="flat", cursor="hand2",
                          padx=6, pady=3, bd=0,
                          command=lambda l=lbl: self._set_all(l))
            b.pack(side="left", padx=3)

        # Wir speichern Referenz auf rf für Neuzeichnen
        self._rf = rf
        self._canvas = canvas
        self._sorted_ma = sorted_ma if self.mitarbeiter else []

    def _refresh_row_btns(self, uid):
        """Einfacher Refresh: Farben der Buttons in der Zeile aktualisieren – 
           ohne vollständigen Rebuild. Wir nutzen variable-Tracing über einen 
           lightweight Ansatz: Widgets werden nach Name gesucht."""
        pass  # Visueller Feedback durch selectcolor des Radiobuttons reicht aus

    def _set_all(self, status):
        for var in self._vars.values():
            var.set(status)

    def _save(self):
        aw = {uid: var.get() for uid, var in self._vars.items() if var.get()}
        self.on_save(aw)
        self.destroy()


class TermineTab(tk.Frame):
    """Termine / Inactivity – Schichten mit Anwesenheitsverfolgung."""
    def __init__(self, parent):
        super().__init__(parent, bg=C["BG"])
        self._termine = load_json(TERMINE_FILE)
        do_backup(TERMINE_FILE)
        self._mitarbeiter = []   # wird aus Personal-Sync geladen
        self._build_toolbar()
        self._build_list()
        self._refresh()
        # Mitarbeiter im Hintergrund laden
        threading.Thread(target=self._load_mitarbeiter, daemon=True).start()

    def _load_mitarbeiter(self):
        m, _ = personal_sync_load()
        if m is not None:
            self._mitarbeiter = m

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=C["BG"]); tb.pack(fill="x", padx=16, pady=10)
        make_btn(tb, "+  Termin hinzufügen", self._open_add, pady=7).pack(side="left")
        tk.Label(tb, text="Klicke auf einen Termin, um die Anwesenheit zu erfassen.",
                 font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(side="left", padx=16)
        make_btn(tb, "🔄  Personal sync", self._reload_ma, bg="#557799", pady=7).pack(side="right")

    def _reload_ma(self):
        threading.Thread(target=self._load_mitarbeiter, daemon=True).start()
        show_toast(self.winfo_toplevel(), "Personal", "Mitarbeiterliste wird aktualisiert...")

    def _build_list(self):
        # Zwei-Spalten-Layout: Links Terminliste, rechts Detail/Zusammenfassung
        main = tk.Frame(self, bg=C["BG"]); main.pack(fill="both", expand=True, padx=16, pady=(0,16))

        # Linke Seite: Terminliste
        left = tk.Frame(main, bg=C["BG"]); left.pack(side="left", fill="both", expand=True)
        hdr = tk.Frame(left, bg=C["PRIMARY"]); hdr.pack(fill="x")
        for txt, w, exp in [("#",3,False),("Titel / Schicht",20,True),
                             ("Von",14,False),("Bis",14,False),("",6,False)]:
            l = tk.Label(hdr, text=txt, font=("Segoe UI",9,"bold"),
                         bg=C["PRIMARY"], fg="white", anchor="w", pady=8, padx=8)
            if w: l.configure(width=w)
            l.pack(side="left", fill="x" if exp else "none", expand=exp)

        outer = tk.Frame(left, bg=C["BG"]); outer.pack(fill="both", expand=True)
        self._canvas = tk.Canvas(outer, bg=C["BG"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self._canvas.pack(side="left", fill="both", expand=True)
        self._rf = tk.Frame(self._canvas, bg=C["BG"])
        self._cw = self._canvas.create_window((0,0), window=self._rf, anchor="nw")
        self._rf.bind("<Configure>", lambda e: self._canvas.configure(scrollregion=self._canvas.bbox("all")))
        self._canvas.bind("<Configure>", lambda e: self._canvas.itemconfig(self._cw, width=e.width))
        self._canvas.bind_all("<MouseWheel>", lambda e: self._canvas.yview_scroll(int(-1*(e.delta/120)),"units"))

        # Rechte Seite: Anwesenheits-Zusammenfassung des ausgewählten Termins
        sep = tk.Frame(main, bg=C["BORDER"], width=1); sep.pack(side="left", fill="y", padx=8)
        right = tk.Frame(main, bg=C["BG"], width=280); right.pack(side="left", fill="y")
        right.pack_propagate(False)
        tk.Label(right, text="Zusammenfassung", font=("Segoe UI",10,"bold"),
                 bg=C["PRIMARY"], fg="white").pack(fill="x", pady=(0,4), padx=0, ipady=8)
        self._detail_frame = tk.Frame(right, bg=C["BG"]); self._detail_frame.pack(fill="both", expand=True)
        self._show_detail(None)

    def _refresh(self):
        for w in self._rf.winfo_children(): w.destroy()
        if not self._termine:
            tk.Label(self._rf, text="Noch keine Termine angelegt.",
                     font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(pady=40); return
        sorted_t = sorted(self._termine, key=lambda t: t.get("von",""), reverse=True)
        for i, t in enumerate(sorted_t):
            rbg = C["ROW_ODD"] if i%2==0 else C["ROW_EVEN"]
            row = tk.Frame(self._rf, bg=rbg, highlightthickness=1,
                           highlightbackground=C["BORDER"], cursor="hand2")
            row.pack(fill="x", pady=2)
            row.bind("<Button-1>", lambda e, tt=t: self._open_anwesenheit(tt))

            tk.Label(row, text=str(i+1), font=FONT_TABLE, bg=rbg, fg=C["SUBTEXT"],
                     width=3, anchor="w").pack(side="left", padx=8, pady=10)
            tk.Label(row, text=t.get("titel",""), font=("Segoe UI",10,"bold"),
                     bg=rbg, fg=C["TEXT"], anchor="w").pack(side="left", fill="x", expand=True, padx=4, pady=10)

            # Anwesenheits-Pille
            aw = t.get("anwesenheit", {})
            if aw:
                counts = {}
                for v in aw.values():
                    counts[v] = counts.get(v,0)+1
                pill_f = tk.Frame(row, bg=rbg); pill_f.pack(side="left", padx=6)
                for lbl, col in ANWESENHEIT_OPTIONS:
                    n = counts.get(lbl,0)
                    if n > 0:
                        tk.Label(pill_f, text=f"{n}", font=("Segoe UI",8,"bold"),
                                 bg=col, fg="white", padx=5, pady=1).pack(side="left", padx=1)

            tk.Label(row, text=t.get("von",""), font=FONT_TABLE,
                     bg=rbg, fg=C["TEXT"], width=14).pack(side="left", padx=4, pady=10)
            tk.Label(row, text=t.get("bis",""), font=FONT_TABLE,
                     bg=rbg, fg=C["TEXT"], width=14).pack(side="left", padx=4, pady=10)

            d = tk.Label(row, text=" X ", font=("Segoe UI",11,"bold"),
                         bg=rbg, fg=C["DANGER"], cursor="hand2")
            d.pack(side="right", padx=6, pady=8)
            d.bind("<Button-1>", lambda ev, tt=t: self._delete(tt))
            e_lbl = tk.Label(row, text=" ✎ ", font=("Segoe UI",11),
                             bg=rbg, fg="#4488CC", cursor="hand2")
            e_lbl.pack(side="right", padx=4, pady=8)
            e_lbl.bind("<Button-1>", lambda ev, tt=t: self._edit(tt))

    def _show_detail(self, termin):
        for w in self._detail_frame.winfo_children(): w.destroy()
        if termin is None:
            tk.Label(self._detail_frame,
                     text="Termin auswählen\num Anwesenheit\nzu sehen.",
                     font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"],
                     justify="center").pack(expand=True)
            return
        aw = termin.get("anwesenheit", {})
        tk.Label(self._detail_frame, text=termin.get("titel",""),
                 font=("Segoe UI",10,"bold"), bg=C["BG"], fg=C["TEXT"],
                 wraplength=240, justify="left").pack(anchor="w", padx=10, pady=(10,2))
        tk.Label(self._detail_frame,
                 text=f"{termin.get('von','')}  –  {termin.get('bis','')}",
                 font=FONT_LABEL, bg=C["BG"], fg=C["SUBTEXT"]).pack(anchor="w", padx=10)
        desc = termin.get("beschreibung","")
        if desc:
            tk.Label(self._detail_frame, text=desc, font=FONT_LABEL,
                     bg=C["BG"], fg=C["TEXT"], wraplength=240, justify="left").pack(anchor="w", padx=10, pady=(4,0))
        tk.Frame(self._detail_frame, bg=C["BORDER"], height=1).pack(fill="x", padx=10, pady=8)

        # Statistik
        total_ma = len(self._mitarbeiter)
        counts = {}
        for v in aw.values():
            counts[v] = counts.get(v,0)+1
        for lbl, col in ANWESENHEIT_OPTIONS:
            n = counts.get(lbl,0)
            row = tk.Frame(self._detail_frame, bg=C["BG"]); row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text="", bg=col, width=3).pack(side="left", padx=(0,6), ipady=8)
            tk.Label(row, text=lbl, font=FONT_TABLE, bg=C["BG"], fg=C["TEXT"],
                     anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(row, text=str(n), font=("Segoe UI",9,"bold"),
                     bg=C["BG"], fg=C["TEXT"]).pack(side="right")

        not_set = total_ma - sum(counts.values())
        if not_set > 0:
            row = tk.Frame(self._detail_frame, bg=C["BG"]); row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text="", bg=C["BORDER"], width=3).pack(side="left", padx=(0,6), ipady=8)
            tk.Label(row, text="Nicht eingetragen", font=FONT_TABLE, bg=C["BG"],
                     fg=C["SUBTEXT"], anchor="w").pack(side="left", fill="x", expand=True)
            tk.Label(row, text=str(not_set), font=("Segoe UI",9,"bold"),
                     bg=C["BG"], fg=C["SUBTEXT"]).pack(side="right")

        tk.Frame(self._detail_frame, bg=C["BORDER"], height=1).pack(fill="x", padx=10, pady=8)
        # Namentliche Liste
        ma_by_id = {str(m.get("id","")): m for m in self._mitarbeiter}
        for lbl, col in ANWESENHEIT_OPTIONS:
            names = [ma_by_id[uid].get("roblox","?")
                     for uid, v in aw.items() if v == lbl and uid in ma_by_id]
            if names:
                tk.Label(self._detail_frame, text=lbl, font=("Segoe UI",8,"bold"),
                         bg=col, fg="white", anchor="w").pack(fill="x", padx=10, pady=(4,1))
                for n in names:
                    tk.Label(self._detail_frame, text=f"  • {n}", font=FONT_TABLE,
                             bg=C["BG"], fg=C["TEXT"], anchor="w").pack(anchor="w", padx=10)

        make_btn(self._detail_frame, "📋  Anwesenheit bearbeiten",
                 lambda t=termin: self._open_anwesenheit(t), pady=5).pack(fill="x", padx=10, pady=12)

    def _open_anwesenheit(self, termin):
        self._show_detail(termin)
        if not self._mitarbeiter:
            # Nochmal versuchen zu laden
            threading.Thread(target=self._load_mitarbeiter, daemon=True).start()
            messagebox.showinfo("Hinweis",
                "Mitarbeiterliste wird geladen. Bitte kurz warten und erneut öffnen.",
                parent=self)
            return
        def on_save(aw):
            for t in self._termine:
                if str(t.get("id","")) == str(termin.get("id","")):
                    t["anwesenheit"] = aw; break
            save_json(TERMINE_FILE, self._termine)
            self._refresh()
            self._show_detail(termin)
        AnwesenheitPopup(self.winfo_toplevel(), termin, self._mitarbeiter, on_save)

    def _open_add(self):
        TerminPopup(self.winfo_toplevel(), self._add)

    def _add(self, data):
        self._termine.append(data)
        save_json(TERMINE_FILE, self._termine)
        self._refresh()

    def _edit(self, termin):
        def apply(data):
            for i, t in enumerate(self._termine):
                if str(t.get("id","")) == str(termin.get("id","")):
                    self._termine[i] = data; break
            save_json(TERMINE_FILE, self._termine)
            self._refresh()
        TerminPopup(self.winfo_toplevel(), apply, existing=termin)

    def _delete(self, termin):
        if messagebox.askyesno("Löschen?",
                f"Termin '{termin.get('titel','')}' wirklich löschen?", parent=self):
            self._termine = [t for t in self._termine
                             if str(t.get("id","")) != str(termin.get("id",""))]
            save_json(TERMINE_FILE, self._termine)
            self._refresh()
            self._show_detail(None)


if __name__ == "__main__":
    app = NotizenApp()
    sb = tk.Frame(app, bg=C["BORDER"], height=22); sb.pack(fill="x", side="bottom")
    tk.Label(sb, text=f"v{APP_VERSION}", font=("Segoe UI",8),
             bg=C["BORDER"], fg=C["SUBTEXT"]).pack(side="right", padx=10)
    app.after(2000, lambda: check_for_update(app, silent=True))
    app.mainloop()