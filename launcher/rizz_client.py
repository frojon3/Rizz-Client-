"""
Rizz Client Launcher (styl macOS)

    pip install -r requirements.txt
    python rizz_client.py

Rizz Core (mod z Keystrokes, Freelook, Zoom, menu pod Prawy Shift) kladziesz w folderze
core/ jako  rizzclient-<wersja MC>.jar  (np. core/rizzclient-1.21.1.jar).
"""
import hashlib
import json
import platform
import shutil
import subprocess
import threading
import uuid as uuidlib
from pathlib import Path

import customtkinter as ctk
import minecraft_launcher_lib as mll
import requests

# ------------------------------------------------------------------ stale
APP = "Rizz Client"
ROOT = Path.home() / ".rizzclient"
INSTANCES = ROOT / "instances"          # osobny folder (mody/zapisy) dla kazdej wersji MC
CONFIG = ROOT / "config.json"
CORE_DIR = Path(__file__).resolve().parent / "core"
API = "https://api.modrinth.com/v2"
HEADERS = {"User-Agent": "RizzClient/2.0 (launcher)"}
DEFAULT_MC = "1.21.1"
FALLBACK_VERSIONS = ["1.21.4", "1.21.1", "1.20.6", "1.20.4", "1.20.1", "1.19.4"]

# mody startowe z Modrinth (slug, fraza zapasowa)
BASE_MODS = [
    ("fabric-api", "Fabric API"),
    ("sodium", "Sodium"),
    ("lithium", "Lithium"),
    ("modmenu", "Mod Menu"),
    ("motionblur", "Motion Blur"),
]
# uzywane tylko gdy nie ma Rizz Core dla danej wersji MC
FALLBACK_MODS = [
    ("freelook", "Freelook"),
    ("keystrokes", "Keystrokes"),
    ("zoomify", "Zoomify"),
]

# FPS Boost: dodatkowe mody wydajnosciowe (Sodium i Lithium sa juz w BASE_MODS)
PERF_MODS = [
    ("ferrite-core", "FerriteCore"),
    ("entityculling", "Entity Culling"),
    ("immediatelyfast", "ImmediatelyFast"),
    ("modernfix", "ModernFix"),
    ("moreculling", "More Culling"),
    ("dynamic-fps", "Dynamic FPS"),
]
# ustawienia options.txt (dla liczb bierzemy mniejsza z wartosci: Twojej i naszej)
FPS_OPTIONS = {
    "renderDistance": "10", "simulationDistance": "8", "entityDistanceScaling": "0.75",
    "graphicsMode": "0", "particles": "2", "maxFps": "260", "enableVsync": "false",
    "entityShadows": "false", "biomeBlendRadius": "1", "mipmapLevels": "2",
}
MIN_KEYS = {"renderDistance", "simulationDistance", "entityDistanceScaling"}
FPS_JVM = ["-XX:+UnlockExperimentalVMOptions", "-XX:+UseG1GC", "-XX:G1NewSizePercent=20",
           "-XX:G1ReservePercent=20", "-XX:MaxGCPauseMillis=50", "-XX:+DisableExplicitGC",
           "-XX:+ParallelRefProcEnabled"]

C_BG, C_SIDE, C_CARD = "#1c1c1e", "#262629", "#2c2c2e"
C_ACCENT, C_ACCENT_H = "#ff375f", "#ff5c7c"
C_TEXT, C_MUTED = "#f5f5f7", "#8e8e93"
FONT = "SF Pro Display" if platform.system() == "Darwin" else "Segoe UI"


# ------------------------------------------------------------------ Modrinth
def api_get(path, **params):
    r = requests.get(API + path, params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def pick_best(versions):
    """Najnowsza stabilna (release); jak brak - najnowsza jaka jest."""
    if not versions:
        return None
    rel = [v for v in versions if v.get("version_type") == "release"]
    return (rel or versions)[0]


def find_version(project, mc):
    """Dobiera wersje moda do wersji MC: dokladna, a w ostatecznosci seria (np. 1.21 dla 1.21.1)."""
    loaders = json.dumps(["fabric"])
    exact = api_get(f"/project/{project}/version", loaders=loaders,
                    game_versions=json.dumps([mc]))
    if exact:
        return pick_best(exact)
    series = ".".join(mc.split(".")[:2])
    if series != mc:
        alt = api_get(f"/project/{project}/version", loaders=loaders,
                      game_versions=json.dumps([series]))
        if alt:
            return pick_best(alt)
    return None


def search_mods(query, mc, limit=25):
    facets = json.dumps([["project_type:mod"], ["categories:fabric"], [f"versions:{mc}"]])
    return api_get("/search", query=query, facets=facets, limit=limit).get("hits", [])


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_file(version, dest):
    files = version["files"]
    f = next((x for x in files if x.get("primary")), files[0])
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / f["filename"]
    if path.exists():
        return path
    with requests.get(f["url"], headers=HEADERS, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(path, "wb") as out:
            for chunk in r.iter_content(1 << 16):
                out.write(chunk)
    return path


def install_project(project, mc, mdir, seen=None):
    """Instaluje mod w wersji pasujacej do MC wraz z wymaganymi zaleznosciami."""
    seen = seen if seen is not None else set()
    ver = find_version(project, mc)
    if not ver:
        raise RuntimeError(f"brak wersji '{project}' dla {mc}")
    seen.add(ver["project_id"])
    names = []
    for dep in ver.get("dependencies", []):
        pid = dep.get("project_id")
        if dep.get("dependency_type") == "required" and pid and pid not in seen:
            try:
                names += install_project(pid, mc, mdir, seen)
            except Exception:
                pass
    names.append(download_file(ver, mdir).name)
    return names


def sync_mods(mc, mdir, log):
    """Sprawdza zainstalowane mody po hashach i podmienia je na wersje pasujace do MC."""
    jars = [p for p in mdir.glob("*.jar") if not p.name.lower().startswith("rizzclient")]
    if not jars:
        return
    hashes = {sha1(p): p for p in jars}
    r = requests.post(f"{API}/version_files/update", headers=HEADERS, timeout=30, json={
        "hashes": list(hashes), "algorithm": "sha1",
        "loaders": ["fabric"], "game_versions": [mc]})
    if r.status_code != 200:
        return
    data = r.json()
    for h, p in hashes.items():
        v = data.get(h)
        if not v:
            log(f"[?] {p.name}: brak wersji pod {mc} na Modrinth (moze nie dzialac)")
            continue
        f = next((x for x in v["files"] if x.get("primary")), v["files"][0])
        if f["hashes"].get("sha1") != h:
            download_file(v, mdir)
            p.unlink(missing_ok=True)
            log(f"[↑] {p.name} -> {f['filename']}")


# ------------------------------------------------------------------ konfiguracja
def load_cfg():
    try:
        return json.loads(CONFIG.read_text())
    except Exception:
        return {"username": "Player", "ram": 4, "mc_version": DEFAULT_MC, "defaults": []}


def save_cfg(cfg):
    ROOT.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(cfg, indent=2))


def instance_dir(mc):
    return INSTANCES / mc


def mods_dir(mc):
    return instance_dir(mc) / "mods"


def core_jar(mc):
    p = CORE_DIR / f"rizzclient-{mc}.jar"
    return p if p.exists() else None


def fetch_core(mc, repo, log):
    """Pobiera rizzclient-<mc>.jar z ostatniego release na GitHubie (budowanego przez Actions)."""
    url = f"https://github.com/{repo}/releases/latest/download/rizzclient-{mc}.jar"
    try:
        r = requests.get(url, headers=HEADERS, stream=True, timeout=60, allow_redirects=True)
        if r.status_code != 200:
            log(f"[!] GitHub: brak rizzclient-{mc}.jar w ostatnim release ({r.status_code})")
            return None
        CORE_DIR.mkdir(parents=True, exist_ok=True)
        path = CORE_DIR / f"rizzclient-{mc}.jar"
        with open(path, "wb") as out:
            for chunk in r.iter_content(1 << 16):
                out.write(chunk)
        log(f"[OK] pobrano Rizz Core {mc} z GitHuba")
        return path
    except requests.RequestException as ex:
        log(f"[!] nie udalo sie pobrac Rizz Core: {ex}")
        return None


def apply_fps_options(idir, log):
    """Wstawia ustawienia pod FPS do options.txt. Zwraca True, jesli zastosowano."""
    f = idir / "options.txt"
    if not f.exists():
        log("[i] options.txt powstanie po pierwszym uruchomieniu - ustawienia FPS wejda przy nastepnym starcie")
        return False
    out, seen = [], set()
    for ln in f.read_text(encoding="utf-8").splitlines():
        k, _, v = ln.partition(":")
        if k in FPS_OPTIONS:
            val = FPS_OPTIONS[k]
            if k in MIN_KEYS:
                try:
                    val = str(min(float(v), float(val))).rstrip("0").rstrip(".") if "." in val else str(min(int(v), int(val)))
                except ValueError:
                    pass
            out.append(f"{k}:{val}")
            seen.add(k)
        else:
            out.append(ln)
    out += [f"{k}:{v}" for k, v in FPS_OPTIONS.items() if k not in seen]
    f.write_text("\n".join(out) + "\n", encoding="utf-8")
    log("[OK] zastosowano ustawienia FPS w options.txt")
    return True


# ------------------------------------------------------------------ GUI
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title(APP)
        self.geometry("1000x660")
        self.minsize(900, 600)
        self.configure(fg_color=C_BG)
        self.cfg = load_cfg()
        self.hits = []
        self.pmax = 1

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar()
        self.content = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        self.pages = {
            "play": self._page_play(),
            "mods": self._page_mods(),
            "store": self._page_store(),
        }
        self.show("play")
        self.refresh_mods()
        self.update_core_label()
        threading.Thread(target=self._load_versions, daemon=True).start()

    def f(self, size=13, bold=False):
        return ctk.CTkFont(family=FONT, size=size, weight="bold" if bold else "normal")

    # ---- pasek boczny
    def _sidebar(self):
        sb = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=C_SIDE)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        dots = ctk.CTkFrame(sb, fg_color="transparent")
        dots.pack(anchor="w", padx=18, pady=(18, 4))
        for color, cmd in (("#ff5f57", self.destroy), ("#febc2e", self.iconify), ("#28c840", None)):
            d = ctk.CTkLabel(dots, text="", width=13, height=13, corner_radius=7, fg_color=color)
            d.pack(side="left", padx=3)
            if cmd:
                d.bind("<Button-1>", lambda _e, c=cmd: c())

        ctk.CTkLabel(sb, text="Rizz Client", font=self.f(24, True), text_color=C_ACCENT
                     ).pack(anchor="w", padx=20, pady=(14, 0))
        ctk.CTkLabel(sb, text="Minecraft • Fabric • Modrinth", font=self.f(11),
                     text_color=C_MUTED).pack(anchor="w", padx=20, pady=(0, 18))

        self.nav = {}
        for key, label in (("play", "▶  Graj"), ("mods", "▣  Moje mody"), ("store", "⌕  Modrinth")):
            b = ctk.CTkButton(sb, text=label, anchor="w", height=36, corner_radius=8,
                              fg_color="transparent", hover_color="#3a3a3d", text_color=C_TEXT,
                              font=self.f(14), command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=12, pady=2)
            self.nav[key] = b

    def show(self, key):
        for k, p in self.pages.items():
            p.grid_forget()
            self.nav[k].configure(fg_color="transparent")
        self.pages[key].grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self.nav[key].configure(fg_color=C_ACCENT)

    def card(self, parent, **kw):
        return ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=14, **kw)

    # ---- strona: Graj
    def _page_play(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(page, text="Graj", font=self.f(28, True)).grid(row=0, column=0, sticky="w")

        card = self.card(page)
        card.grid(row=1, column=0, sticky="ew", pady=14)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Nick", font=self.f(13), text_color=C_MUTED
                     ).grid(row=0, column=0, padx=18, pady=(16, 6), sticky="w")
        self.var_user = ctk.StringVar(value=self.cfg["username"])
        ctk.CTkEntry(card, textvariable=self.var_user, height=34, corner_radius=8,
                     fg_color="#1c1c1e", border_width=0
                     ).grid(row=0, column=1, padx=18, pady=(16, 6), sticky="ew")

        ctk.CTkLabel(card, text="Wersja MC", font=self.f(13), text_color=C_MUTED
                     ).grid(row=1, column=0, padx=18, pady=6, sticky="w")
        self.var_ver = ctk.StringVar(value=self.cfg["mc_version"])
        self.cmb = ctk.CTkComboBox(card, variable=self.var_ver, values=FALLBACK_VERSIONS,
                                   height=34, corner_radius=8, fg_color="#1c1c1e",
                                   border_width=0, button_color=C_ACCENT,
                                   button_hover_color=C_ACCENT_H, command=self.on_version)
        self.cmb.grid(row=1, column=1, padx=18, pady=6, sticky="ew")

        ctk.CTkLabel(card, text="RAM", font=self.f(13), text_color=C_MUTED
                     ).grid(row=2, column=0, padx=18, pady=6, sticky="w")
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.grid(row=2, column=1, padx=18, pady=6, sticky="ew")
        row.grid_columnconfigure(0, weight=1)
        self.var_ram = ctk.IntVar(value=self.cfg["ram"])
        ctk.CTkSlider(row, from_=1, to=16, number_of_steps=15, variable=self.var_ram,
                      button_color=C_ACCENT, button_hover_color=C_ACCENT_H,
                      progress_color=C_ACCENT, command=lambda v: self.ram_lbl.configure(text=f"{int(v)} GB")
                      ).grid(row=0, column=0, sticky="ew")
        self.ram_lbl = ctk.CTkLabel(row, text=f"{self.cfg['ram']} GB", width=50)
        self.ram_lbl.grid(row=0, column=1, padx=(10, 0))

        ctk.CTkLabel(card, text="Rizz Core (GitHub)", font=self.f(13), text_color=C_MUTED
                     ).grid(row=3, column=0, padx=18, pady=6, sticky="w")
        self.var_repo = ctk.StringVar(value=self.cfg.get("core_repo", ""))
        ctk.CTkEntry(card, textvariable=self.var_repo, height=34, corner_radius=8,
                     fg_color="#1c1c1e", border_width=0, placeholder_text="uzytkownik/RizzClient"
                     ).grid(row=3, column=1, padx=18, pady=6, sticky="ew")

        self.var_fps = ctk.BooleanVar(value=self.cfg.get("fps_boost", True))
        ctk.CTkSwitch(card, text="FPS Boost (mody wydajnosciowe + ustawienia + flagi Javy)",
                      variable=self.var_fps, progress_color=C_ACCENT, font=self.f(13)
                      ).grid(row=4, column=0, columnspan=2, padx=18, pady=6, sticky="w")

        self.core_lbl = ctk.CTkLabel(card, text="", font=self.f(12), text_color=C_MUTED)
        self.core_lbl.grid(row=5, column=0, columnspan=2, padx=18, pady=(4, 16), sticky="w")

        lower = ctk.CTkFrame(page, fg_color="transparent")
        lower.grid(row=2, column=0, sticky="nsew")
        lower.grid_columnconfigure(0, weight=1)
        lower.grid_rowconfigure(2, weight=1)

        self.btn_play = ctk.CTkButton(lower, text="GRAJ", height=48, corner_radius=12,
                                      fg_color=C_ACCENT, hover_color=C_ACCENT_H,
                                      font=self.f(17, True), command=self.on_play)
        self.btn_play.grid(row=0, column=0, sticky="ew")
        self.progress = ctk.CTkProgressBar(lower, progress_color=C_ACCENT, fg_color=C_CARD, height=8)
        self.progress.set(0)
        self.progress.grid(row=1, column=0, sticky="ew", pady=(12, 2))
        self.status = ctk.CTkLabel(lower, text="Gotowy.", text_color=C_MUTED, font=self.f(12))
        self.status.grid(row=1, column=0, sticky="e", pady=(30, 0))
        self.log = ctk.CTkTextbox(lower, fg_color=C_CARD, corner_radius=12, font=("Menlo", 11))
        self.log.grid(row=2, column=0, sticky="nsew", pady=(30, 0))
        self.log.configure(state="disabled")
        return page

    def log_line(self, text):
        def _do():
            self.log.configure(state="normal")
            self.log.insert("end", text + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, _do)

    def set_status(self, text):
        self.after(0, lambda: self.status.configure(text=text))

    def update_core_label(self):
        mc = self.var_ver.get()
        if core_jar(mc):
            self.core_lbl.configure(text=f"✓ Rizz Core dostepny dla {mc} (menu: Prawy Shift)",
                                    text_color="#30d158")
        elif self.var_repo.get().strip():
            self.core_lbl.configure(text=f"↓ Rizz Core {mc} zostanie pobrany z GitHuba przy starcie",
                                    text_color="#0a84ff")
        else:
            self.core_lbl.configure(
                text=f"⚠ Brak Rizz Core dla {mc} - wpisz repo GitHub albo uzyje modow z Modrinth",
                text_color="#ffd60a")

    def _load_versions(self):
        try:
            vs = [v for v in mll.fabric.get_stable_minecraft_versions()][:25]
            if vs:
                self.after(0, lambda: self.cmb.configure(values=vs))
        except Exception:
            pass

    def on_version(self, _v=None):
        self.cfg["mc_version"] = self.var_ver.get()
        save_cfg(self.cfg)
        self.refresh_mods()
        self.update_core_label()

    # ---- strona: Moje mody
    def _page_mods(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(page, text="Moje mody", font=self.f(28, True)).grid(row=0, column=0, sticky="w")
        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=12)
        self.btn_sync = ctk.CTkButton(bar, text="Dopasuj i zaktualizuj do wersji MC", corner_radius=8,
                                      fg_color=C_ACCENT, hover_color=C_ACCENT_H, command=self.on_sync)
        self.btn_sync.pack(side="left")
        ctk.CTkButton(bar, text="Otworz folder", corner_radius=8, fg_color=C_CARD,
                      hover_color="#3a3a3d", command=self.open_mods).pack(side="left", padx=8)
        self.mods_frame = ctk.CTkScrollableFrame(page, fg_color=C_CARD, corner_radius=14)
        self.mods_frame.grid(row=2, column=0, sticky="nsew")
        return page

    def refresh_mods(self):
        for w in self.mods_frame.winfo_children():
            w.destroy()
        mdir = mods_dir(self.var_ver.get())
        jars = sorted(mdir.glob("*.jar")) if mdir.exists() else []
        if not jars:
            ctk.CTkLabel(self.mods_frame, text="Brak modow - zainstalujesz je przy pierwszym starcie.",
                         text_color=C_MUTED).pack(pady=20)
        for p in jars:
            row = ctk.CTkFrame(self.mods_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=p.name, anchor="w").pack(side="left", padx=8)
            if not p.name.startswith("rizzclient"):
                ctk.CTkButton(row, text="Usun", width=60, height=26, corner_radius=6,
                              fg_color="#3a3a3d", hover_color="#ff453a",
                              command=lambda q=p: (q.unlink(missing_ok=True), self.refresh_mods())
                              ).pack(side="right", padx=8)

    def open_mods(self):
        d = mods_dir(self.var_ver.get())
        d.mkdir(parents=True, exist_ok=True)
        sysname = platform.system()
        if sysname == "Windows":
            import os
            os.startfile(d)  # noqa
        elif sysname == "Darwin":
            subprocess.Popen(["open", str(d)])
        else:
            subprocess.Popen(["xdg-open", str(d)])

    def on_sync(self):
        mc = self.var_ver.get()
        self.btn_sync.configure(state="disabled")

        def work():
            try:
                sync_mods(mc, mods_dir(mc), self.log_line)
                self.set_status("Mody dopasowane do " + mc)
            except Exception as ex:
                self.log_line(f"Blad synchronizacji: {ex}")
            finally:
                self.after(0, lambda: (self.btn_sync.configure(state="normal"), self.refresh_mods()))
        threading.Thread(target=work, daemon=True).start()

    # ---- strona: Modrinth
    def _page_store(self):
        page = ctk.CTkFrame(self.content, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(page, text="Modrinth", font=self.f(28, True)).grid(row=0, column=0, sticky="w")
        bar = ctk.CTkFrame(page, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", pady=12)
        bar.grid_columnconfigure(0, weight=1)
        self.var_q = ctk.StringVar()
        e = ctk.CTkEntry(bar, textvariable=self.var_q, height=36, corner_radius=10,
                         placeholder_text="Szukaj modow (Fabric, wersja z zakladki Graj)...",
                         fg_color=C_CARD, border_width=0)
        e.grid(row=0, column=0, sticky="ew")
        e.bind("<Return>", lambda _e: self.on_search())
        ctk.CTkButton(bar, text="Szukaj", height=36, corner_radius=10, fg_color=C_ACCENT,
                      hover_color=C_ACCENT_H, command=self.on_search).grid(row=0, column=1, padx=(8, 0))
        self.results = ctk.CTkScrollableFrame(page, fg_color="transparent")
        self.results.grid(row=2, column=0, sticky="nsew")
        return page

    def on_search(self):
        q, mc = self.var_q.get().strip(), self.var_ver.get()

        def work():
            try:
                hits = search_mods(q, mc)
            except Exception as ex:
                self.log_line(f"Blad wyszukiwania: {ex}")
                return
            self.after(0, lambda: self.fill_results(hits, mc))
        threading.Thread(target=work, daemon=True).start()

    def fill_results(self, hits, mc):
        for w in self.results.winfo_children():
            w.destroy()
        for h in hits:
            c = self.card(self.results)
            c.pack(fill="x", pady=5)
            c.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(c, text=h["title"], font=self.f(15, True), anchor="w"
                         ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 0))
            ctk.CTkLabel(c, text=f'{h["author"]}  •  {h["downloads"]:,} pobran', font=self.f(11),
                         text_color=C_MUTED, anchor="w").grid(row=1, column=0, sticky="w", padx=14)
            ctk.CTkLabel(c, text=h["description"], wraplength=520, justify="left", anchor="w",
                         font=self.f(12)).grid(row=2, column=0, sticky="w", padx=14, pady=(2, 10))
            b = ctk.CTkButton(c, text="Zainstaluj", width=96, height=30, corner_radius=8,
                              fg_color=C_ACCENT, hover_color=C_ACCENT_H)
            b.configure(command=lambda hh=h, bb=b: self.install(hh, mc, bb))
            b.grid(row=0, column=1, rowspan=3, padx=14)

    def install(self, hit, mc, btn):
        btn.configure(state="disabled", text="...")

        def work():
            try:
                names = install_project(hit["project_id"], mc, mods_dir(mc))
                self.log_line("Zainstalowano: " + ", ".join(names))
                self.after(0, lambda: btn.configure(text="Gotowe ✓"))
                self.after(0, self.refresh_mods)
            except Exception as ex:
                self.log_line(f"Blad instalacji: {ex}")
                self.after(0, lambda: btn.configure(state="normal", text="Zainstaluj"))
        threading.Thread(target=work, daemon=True).start()

    # ---- start gry
    def jvm_args(self):
        ram = self.cfg["ram"]
        if not self.cfg.get("fps_boost"):
            return [f"-Xmx{ram}G", f"-Xms{min(2, ram)}G"]
        args = [f"-Xmx{ram}G", f"-Xms{ram}G"] + FPS_JVM
        if ram >= 4:
            args.append("-XX:G1HeapRegionSize=32M")
        return args

    def on_play(self):
        self.cfg.update(username=self.var_user.get().strip() or "Player",
                        ram=int(self.var_ram.get()), mc_version=self.var_ver.get(),
                        core_repo=self.var_repo.get().strip(), fps_boost=bool(self.var_fps.get()))
        save_cfg(self.cfg)
        self.btn_play.configure(state="disabled", text="Przygotowywanie...")
        threading.Thread(target=self.launch_flow, daemon=True).start()

    def launch_flow(self):
        try:
            mc = self.cfg["mc_version"]
            idir, mdir = instance_dir(mc), mods_dir(mc)
            mdir.mkdir(parents=True, exist_ok=True)

            # 1) Minecraft + Fabric
            self.set_status(f"Instalowanie Fabric {mc}...")
            cb = {
                "setStatus": lambda t: self.set_status(t),
                "setMax": lambda m: setattr(self, "pmax", max(m, 1)),
                "setProgress": lambda v: self.after(0, lambda: self.progress.set(v / self.pmax)),
            }
            mll.fabric.install_fabric(mc, str(ROOT), callback=cb)
            loader = mll.fabric.get_latest_loader_version()
            version_id = f"fabric-loader-{loader}-{mc}"

            # 2) Rizz Core (zawsze swiezy z folderu core/)
            for old in mdir.glob("rizzclient*.jar"):
                old.unlink(missing_ok=True)
            repo = self.cfg.get("core_repo", "")
            if repo:
                self.set_status("Pobieranie Rizz Core...")
                fetch_core(mc, repo, self.log_line)
            core = core_jar(mc)
            if core:
                shutil.copy2(core, mdir / core.name)
                self.log_line(f"[OK] Rizz Core ({core.name})")
            else:
                self.log_line(f"[!] Brak core/rizzclient-{mc}.jar - tryb Modrinth")

            # 3) mody startowe z Modrinth, dobrane do wersji MC (raz na wersje)
            boost = bool(self.cfg.get("fps_boost"))
            key = mc + ("+core" if core else "") + ("+perf" if boost else "")
            if key not in self.cfg["defaults"]:
                seen = set()
                for slug, query in BASE_MODS + ([] if core else FALLBACK_MODS) + (PERF_MODS if boost else []):
                    self.set_status(f"Mod: {query}...")
                    try:
                        install_project(slug, mc, mdir, seen)
                        self.log_line(f"[OK] {query}")
                    except Exception:
                        try:
                            hits = search_mods(query, mc, limit=1)
                            if hits:
                                install_project(hits[0]["project_id"], mc, mdir, seen)
                                self.log_line(f"[OK] {query} -> {hits[0]['title']}")
                            else:
                                self.log_line(f"[--] {query}: brak wersji pod {mc}")
                        except Exception as ex:
                            self.log_line(f"[!!] {query}: {ex}")
                self.cfg["defaults"].append(key)
                save_cfg(self.cfg)

            # 4) dopasowanie/aktualizacja wszystkich modow do wersji MC
            self.set_status("Dopasowywanie modow do wersji...")
            try:
                sync_mods(mc, mdir, self.log_line)
            except Exception as ex:
                self.log_line(f"Sync pominiety: {ex}")
            self.after(0, self.refresh_mods)

            # 5) Java
            options = {
                "username": self.cfg["username"],
                "uuid": str(uuidlib.uuid3(uuidlib.NAMESPACE_DNS, "OfflinePlayer:" + self.cfg["username"])),
                "token": "",
                "gameDirectory": str(idir),
                "jvmArguments": self.jvm_args(),
                "launcherName": APP,
                "launcherVersion": "2.0",
            }
            try:
                vj = json.loads((ROOT / "versions" / version_id / f"{version_id}.json").read_text())
                base_id = vj.get("inheritsFrom", mc)
                base = json.loads((ROOT / "versions" / base_id / f"{base_id}.json").read_text())
                comp = base.get("javaVersion", {}).get("component")
                if comp:
                    self.set_status("Instalowanie Javy...")
                    mll.runtime.install_jvm_runtime(comp, str(ROOT), callback=cb)
                    exe = mll.runtime.get_executable_path(comp, str(ROOT))
                    if exe:
                        options["executablePath"] = exe
            except Exception as ex:
                self.log_line(f"Uzywam systemowej Javy ({ex})")

            # 5b) ustawienia FPS w options.txt (raz na wersje MC; nie nadpisujemy pozniejszych zmian)
            done = self.cfg.setdefault("fps_opts_done", [])
            if boost and mc not in done and apply_fps_options(idir, self.log_line):
                done.append(mc)
                save_cfg(self.cfg)

            # 6) start
            self.set_status("Gra uruchomiona")
            cmd = mll.command.get_minecraft_command(version_id, str(ROOT), options)
            proc = subprocess.Popen(cmd, cwd=idir, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                self.log_line(line.rstrip())
            proc.wait()
            if boost and mc not in done and apply_fps_options(idir, self.log_line):
                done.append(mc)
                save_cfg(self.cfg)
            self.set_status("Gra zamknieta.")
        except Exception as ex:
            self.log_line(f"BLAD: {ex}")
            self.set_status("Blad - zobacz log.")
        finally:
            self.after(0, lambda: self.btn_play.configure(state="normal", text="GRAJ"))


if __name__ == "__main__":
    App().mainloop()
