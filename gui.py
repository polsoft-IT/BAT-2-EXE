# -*- coding: utf-8 -*-
"""
BAT2EXE - Modern GUI wrapper for JJSoft BAT2EXE.EXE
Converts .bat / .cmd batch files into standalone .exe executables.

Language: English by default, Polish can be switched at any time.
"""

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
APP_DIR = os.path.dirname(os.path.abspath(__file__))
TOOL_PATH = os.path.join(APP_DIR, "modules", "BAT2EXE.EXE")
MODULES_DIR = os.path.join(APP_DIR, "modules")

# ---------------------------------------------------------------------------
# Translations (EN default, PL switchable at runtime)
# ---------------------------------------------------------------------------
TEXTS = {
    "en": {
        "title": "BAT2EXE — Batch to EXE Converter",
        "input_label": "Batch file (.bat / .cmd)",
        "input_btn": "Browse...",
        "input_hint": "Select a batch file from any location",
        "output_label": "Output location",
        "output_btn": "Browse...",
        "output_hint": "A 'dist' folder will be created in the chosen location",
        "icon_label": "Icon (.ico) — optional",
        "icon_btn": "Browse...",
        "icon_hint": "Custom icon embedded in the compiled .exe",
        "remove_bg": "Remove background",
        "app_label": "Application options",
        "console_label": "Console window",
        "console_show": "Visible (CMD)",
        "console_hide": "Hidden (GUI / no console)",
        "uac_label": "Run as administrator (UAC)",
        "uac_as": "No",
        "uac_high": "If available",
        "uac_admin": "Always",
        "app_hint": "Console visibility and UAC elevation are embedded into the compiled .exe",
        "ok_subsystem": "Console mode applied.",
        "ok_manifest": "UAC manifest applied ({level}).",
        "arch_label": "Architecture",
        "pause_label": "Window after finish",
        "pause_auto": "Auto",
        "pause_always": "Always pause",
        "pause_never": "Close instantly",
        "arch_x86": "32-bit (x86)",
        "arch_x64": "64-bit (x64 wrapper)",
        "bundle_label": "Bundle files / folders into the exe",
        "bundle_add": "Add files",
        "bundle_add_dir": "Add folder",
        "bundle_clear": "Clear",
        "ok_bundle": "Bundled {n} file(s) as resources.",
        "warn_bundle": "Could not bundle resources.",
        "ok_x64": "64-bit wrapper built (32-bit payload embedded).",
        "warn_x64": "Could not build the 64-bit wrapper.",
        "icon_clear": "Clear",
        "err_no_ico": "Selected icon file does not exist.",
        "err_bad_ico": "Only .ico files can be used as icons.",
        "warn_icon": "Warning: could not embed the icon — the .exe was built without it.",
        "icon_done": "Icon embedded successfully.",
        "convert": "Convert",
        "open_dist": "Open dist folder",
        "close": "Close",
        "lang": "Language",
        "log": "Log",
        "ready": "Ready.",
        "working": "Converting, please wait...",
        "done_ok": "Conversion finished successfully!",
        "done_fail": "Conversion failed. Check the log for details.",
        "err_no_input": "Please select a batch file first.",
        "err_no_tool": "Converter tool not found:\n{path}",
        "err_bad_ext": "Only .bat and .cmd files can be converted.",
        "err_no_output": "Please choose an output location.",
        "ask_exit": "Are you sure you want to quit?",
        "success_box": "Success",
        "error_box": "Error",
        "info_box": "Info",
        "about_title": "About BAT2EXE",
        "author_label": "Author",
        "about": "About",
        "menu_lang": "Lang",
        "menu_lang_en": "English",
        "menu_lang_pl": "Polski",
        "menu_settings": "Settings",
        "menu_locations": "Tool locations...",
        "loc_title": "Settings — Tool locations",
        "loc_hint": "Non-standard tool locations (leave empty or reset for defaults)",
        "loc_default": "default",
        "loc_reset": "Reset",
        "loc_browse": "Browse...",
        "loc_close": "Close",
        "loc_upx": "UPX compressor (upx.exe)",
        "loc_7z": "7-Zip archiver (7z.exe)",
        "loc_7zsfx": "7-Zip SFX module (7z.sfx)",
        "loc_7zdll": "7-Zip library (7z.dll)",
        "loc_signtool": "SignTool (SignTools / signtool.exe)",
        "about_title": "O programie BAT2EXE",
        "about_body": (
            "BAT2EXE — modern GUI wrapper\n"
            "for the JJSoft BAT2EXE.EXE converter.\n\n"
            "Turns Windows .bat / .cmd scripts into\n"
            "standalone .exe executables, with an\n"
            "optional custom icon embedded\n"
            "after the build.\n\n"
            "Output always lands in the 'dist'\n"
            "folder of the location you choose."),
        "about_close": "Close",
    },
    "pl": {
        "title": "BAT2EXE — Konwerter BAT na EXE",
        "input_label": "Plik wsadowy (.bat / .cmd)",
        "input_btn": "Wybierz...",
        "input_hint": "Wybierz plik wsadowy z dowolnej lokalizacji",
        "output_label": "Lokalizacja wyjściowa",
        "output_btn": "Wybierz...",
        "output_hint": "W wybranej lokalizacji zostanie utworzony folder 'dist'",
        "icon_label": "Ikona (.ico) — opcjonalna",
        "icon_btn": "Wybierz...",
        "icon_hint": "Własna ikona osadzona w skompilowanym pliku .exe",
        "remove_bg": "Usuń tło",
        "app_label": "Opcje aplikacji",
        "console_label": "Okno konsoli",
        "console_show": "Widoczne (CMD)",
        "console_hide": "Ukryte (GUI / bez konsoli)",
        "uac_label": "Uruchom jako administrator (UAC)",
        "uac_as": "Nie",
        "uac_high": "Jeśli dostępne",
        "uac_admin": "Zawsze",
        "app_hint": "Widoczność konsoli i podniesienie UAC są osadzane w kompilowanym .exe",
        "ok_subsystem": "Tryb konsoli zastosowany.",
        "ok_manifest": "Manifest UAC zastosowany ({level}).",
        "arch_label": "Architektura",
        "pause_label": "Okno po zakończeniu",
        "pause_auto": "Auto",
        "pause_always": "Zawsze pauza",
        "pause_never": "Zamknij od razu",
        "arch_x86": "32-bit (x86)",
        "arch_x64": "64-bit (otoczka x64)",
        "bundle_label": "Dołącz pliki / foldery do exe",
        "bundle_add": "Dodaj pliki",
        "bundle_add_dir": "Dodaj folder",
        "bundle_clear": "Wyczyść",
        "ok_bundle": "Dołączono {n} plik(ów) jako zasoby.",
        "warn_bundle": "Nie udało się dołączyć zasobów.",
        "ok_x64": "Zbudowano otoczkę 64-bit (payload 32-bit osadzony).",
        "warn_x64": "Nie udało się zbudować otoczki 64-bit.",
        "icon_clear": "Wyczyść",
        "err_no_ico": "Wybrany plik ikony nie istnieje.",
        "err_bad_ico": "Jako ikonę można użyć tylko pliku .ico.",
        "warn_icon": "Ostrzeżenie: nie udało się osadzić ikony — plik .exe został zbudowany bez niej.",
        "icon_done": "Ikona została osadzona pomyślnie.",
        "convert": "Konwertuj",
        "open_dist": "Otwórz folder dist",
        "close": "Zamknij",
        "lang": "Język",
        "log": "Dziennik",
        "ready": "Gotowe.",
        "working": "Konwertowanie, proszę czekać...",
        "done_ok": "Konwersja zakończona pomyślnie!",
        "done_fail": "Konwersja nie powiodła się. Sprawdź dziennik.",
        "err_no_input": "Najpierw wybierz plik wsadowy.",
        "err_no_tool": "Nie znaleziono narzędzia konwertera:\n{path}",
        "err_bad_ext": "Konwertować można tylko pliki .bat i .cmd.",
        "err_no_output": "Wybierz lokalizację wyjściową.",
        "ask_exit": "Czy na pewno chcesz zakończyć?",
        "success_box": "Sukces",
        "error_box": "Błąd",
        "info_box": "Informacja",
        "about_title": "O programie BAT2EXE",
        "author_label": "Autor",
        "about": "O programie",
        "menu_lang": "Język",
        "menu_lang_en": "English",
        "menu_lang_pl": "Polski",
        "menu_settings": "Ustawienia",
        "menu_locations": "Lokalizacje narzędzi...",
        "loc_title": "Ustawienia — Lokalizacje narzędzi",
        "loc_hint": "Niestandardowe lokalizacje narzędzi (puste lub Reset = domyślne)",
        "loc_default": "domyślnie",
        "loc_reset": "Reset",
        "loc_browse": "Wybierz...",
        "loc_close": "Zamknij",
        "loc_upx": "Kompresor UPX (upx.exe)",
        "loc_7z": "Archiwizator 7-Zip (7z.exe)",
        "loc_7zsfx": "Moduł SFX 7-Zip (7z.sfx)",
        "loc_7zdll": "Biblioteka 7-Zip (7z.dll)",
        "loc_signtool": "SignTool (SignTools / signtool.exe)",
        "about_body": (
            "BAT2EXE — nowoczesna nakładka graficzna\n"
            "na konwerter JJSoft BAT2EXE.EXE.\n\n"
            "Zamienia skrypty Windows .bat / .cmd na\n"
            "samodzielne pliki .exe, z opcjonalną\n"
            "własną ikoną osadzaną po kompilacji.\n\n"
            "Wynik zawsze trafia do folderu 'dist'\n"
            "we wskazanej lokalizacji."),
        "about_close": "Zamknij",
    },
}

# ---------------------------------------------------------------------------
# Colors / style — dark modern theme
# ---------------------------------------------------------------------------
BG        = "#111716"
BG_CARD   = "#1b2422"
BG_ENTRY  = "#222e2b"
ACCENT    = "#237d6b"
ACCENT_HV = "#2f927e"
GREEN     = "#33794e"
GREEN_HV  = "#3d8e5c"
DANGER    = "#a8433c"
DANGER_HV = "#bc5148"
FG        = "#edf4ef"
FG_DIM    = "#a3b1ab"
BORDER    = "#35443e"


def _round_rect(canvas, x1, y1, x2, y2, radius=10, **kw):
    """Draw a rounded rectangle on a tk.Canvas (helper for the About logo)."""
    points = [
        x1 + radius, y1,  x2 - radius, y1,  x2, y1,  x2, y1 + radius,
        x2, y2 - radius,  x2, y2,  x2 - radius, y2,  x1 + radius, y2,
        x1, y2,  x1, y2 - radius,  x1, y1 + radius,  x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)


def _resolve_pause(pause_mode: str, show_console: bool) -> bool:
    """Decide whether the compiled exe should pause before closing.

    auto:   pause only when a console window will be visible (the classic
            behaviour users expect — they can read the output);
            hidden/GUI mode closes instantly (nothing to read anyway)
    always: pause regardless of console visibility
    never:  never pause, window closes the moment the script ends
    """
    if pause_mode == "always":
        return True
    if pause_mode == "never":
        return False
    return bool(show_console)          # auto


def _write_payload(src_bat: str, dst_bat: str, pause: bool):
    """Copy *src_bat* to *dst_bat*, appending/refreshing the exit behaviour.

    - pause=True  → guarantees the window stays open (adds a final
      'pause' unless the script already ends with one)
    - pause=False → strips trailing pause/exit-less hangs so the window
      closes the instant the script finishes
    Encoding: read as bytes and decode heuristically (batch files are
    commonly cp1250/utf-8/ascii), written back in the same codec.
    """
    raw = open(src_bat, "rb").read()
    for enc in ("utf-8", "cp1250", "cp1252", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("latin-1", errors="replace")
        enc = "latin-1"

    # strip trailing whitespace, remember line ending style
    nl = "\r\n" if "\r\n" in text else "\n"
    body = text.rstrip()
    low = body.lower()

    if pause:
        # already ends with pause? don't double it
        last_cmd = low.splitlines()[-1].strip() if low.splitlines() else ""
        if not last_cmd.endswith("pause"):
            body += nl + "pause"
    else:
        # remove trailing pause lines (and echo prompts right before them)
        lines = body.splitlines()
        while lines and lines[-1].strip().lower() == "pause":
            lines.pop()
            # a preceding echo that only prints "Press any key" is noise now
            if lines and "press" in lines[-1].lower():
                lines.pop()
        body = nl.join(lines)

    with open(dst_bat, "w", encoding=enc, newline="") as fh:
        fh.write(body + nl)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "en"          # default language: English
        self.status_key = "ready"
        self.input_file = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.icon_file = tk.StringVar()
        self.dist_dir = ""
        self._log_queue = queue.Queue()
        self._build_ui()
        self.apply_language()
        self.log(TEXTS["en"]["ready"])
        self._poll_log_id = self.after(100, self._poll_log)

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        self.title("BAT2EXE")
        self.configure(bg=BG)

        try:
            self.call("tk", "scaling", 1.25)
        except tk.TclError:
            pass

        # ---- menu bar (topmost) ----
        self._build_menubar()

        # outer padding frame
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=12, pady=8)
        outer.columnconfigure(0, weight=3)
        outer.columnconfigure(1, weight=2)
        outer.rowconfigure(0, weight=1)

        left_panel = tk.Frame(outer, bg=BG)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(4, weight=1)

        # ---- header ----
        header = tk.Frame(left_panel, bg=BG)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        brand_mark = tk.Frame(header, bg=ACCENT, width=4, height=42)
        brand_mark.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(0, 12))
        brand_mark.grid_propagate(False)

        self.title_lbl = tk.Label(
            header, text="BAT2EXE", bg=BG, fg=FG,
            font=("Segoe UI", 19, "bold"), anchor="w")
        self.title_lbl.grid(row=0, column=1, sticky="w")

        self.subtitle_lbl = tk.Label(
            header, text="", bg=BG, fg=FG_DIM,
            font=("Segoe UI", 10), anchor="w")
        self.subtitle_lbl.grid(row=1, column=1, sticky="w")

        # (_style_combobox kept; language moved to the menu bar)
        self._style_combobox()

        # ---- input / output cards ----
        self.card_in = self._card(left_panel, 1, pady=(6, 0))
        self.lbl_input = self._card_row(self.card_in, 0, "input_label")
        e = tk.Entry(self.card_in, textvariable=self.input_file, bg=BG_ENTRY,
                     fg=FG, insertbackground=FG, relief="flat",
                     font=("Consolas", 10))
        e.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(1, 5))
        self.btn_input = self._button(self.card_in, "input_btn",
                                      self.pick_input, ACCENT, ACCENT_HV)
        self.btn_input.grid(row=1, column=1, sticky="e", padx=(0, 14), pady=(1, 5))
        self.hint_input = self._hint(self.card_in, 2, "input_hint")

        self.card_out = self._card(left_panel, 2, pady=(6, 0))
        self.lbl_output = self._card_row(self.card_out, 0, "output_label")
        e2 = tk.Entry(self.card_out, textvariable=self.output_dir, bg=BG_ENTRY,
                      fg=FG, insertbackground=FG, relief="flat",
                      font=("Consolas", 10))
        e2.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(1, 5))
        self.btn_output = self._button(self.card_out, "output_btn",
                                       self.pick_output, ACCENT, ACCENT_HV)
        self.btn_output.grid(row=1, column=1, sticky="e", padx=(0, 14), pady=(1, 5))
        self.hint_output = self._hint(self.card_out, 2, "output_hint")

        # ---- icon card ----
        self.card_ico = self._card(left_panel, 3, pady=(6, 0))
        self.lbl_icon = self._card_row(self.card_ico, 0, "icon_label")
        e3 = tk.Entry(self.card_ico, textvariable=self.icon_file, bg=BG_ENTRY,
                      fg=FG, insertbackground=FG, relief="flat",
                      font=("Consolas", 10))
        e3.grid(row=1, column=0, sticky="ew", padx=(14, 6), pady=(1, 5))
        self.btn_icon = self._button(self.card_ico, "icon_btn",
                                     self.pick_icon, ACCENT, ACCENT_HV)
        self.btn_icon.grid(row=1, column=1, sticky="e", padx=(0, 6), pady=(1, 5))
        # "remove background" checkbox — user only unchecks if they don't want it
        self.remove_bg = tk.BooleanVar(value=True)   # ON by default
        self.chk_nobg = tk.Checkbutton(
            self.card_ico, variable=self.remove_bg,
            text=TEXTS[self.lang]["remove_bg"],
            bg=BG_CARD, fg=FG_DIM, activebackground=BG_CARD,
            activeforeground=FG, selectcolor=BG_ENTRY,
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 9), cursor="hand2", padx=6)
        self.chk_nobg.grid(row=1, column=2, sticky="e", padx=(0, 14), pady=(1, 5))
        self.hint_icon = self._hint(self.card_ico, 2, "icon_hint")

        # ---- application options card ----
        self.card_app = self._card(left_panel, 4, pady=(6, 0))
        self.lbl_app = self._card_row(self.card_app, 0, "app_label")

        opts = tk.Frame(self.card_app, bg=BG_CARD)
        opts.grid(row=1, column=0, columnspan=3, sticky="ew", padx=14, pady=(1, 5))
        opts.columnconfigure(0, weight=1)
        opts.columnconfigure(1, weight=1)

        # console visibility (radio pair)
        self.show_console = tk.BooleanVar(value=True)   # visible CMD by default
        con_box = tk.Frame(opts, bg=BG_CARD)
        con_box.grid(row=0, column=0, sticky="w")
        tk.Label(con_box, text=TEXTS[self.lang]["console_label"], bg=BG_CARD,
                 fg=FG_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        rb_row = tk.Frame(con_box, bg=BG_CARD)
        rb_row.pack(anchor="w")
        self.rb_con_show = tk.Radiobutton(
            rb_row, text=TEXTS[self.lang]["console_show"], value=True,
            variable=self.show_console, bg=BG_CARD, fg=FG,
            activebackground=BG_CARD, selectcolor=BG_ENTRY,
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 9), cursor="hand2")
        self.rb_con_show.pack(side="left")
        self.rb_con_hide = tk.Radiobutton(
            rb_row, text=TEXTS[self.lang]["console_hide"], value=False,
            variable=self.show_console, bg=BG_CARD, fg=FG,
            activebackground=BG_CARD, selectcolor=BG_ENTRY,
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 9), cursor="hand2")
        self.rb_con_hide.pack(side="left", padx=(12, 0))

        # UAC execution level (radio triple)
        self.uac_level = tk.StringVar(value="asInvoker")
        uac_box = tk.Frame(opts, bg=BG_CARD)
        uac_box.grid(row=0, column=1, sticky="w")
        tk.Label(uac_box, text=TEXTS[self.lang]["uac_label"], bg=BG_CARD,
                 fg=FG_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        uac_row = tk.Frame(uac_box, bg=BG_CARD)
        uac_row.pack(anchor="w")
        self._uac_radios = []
        for i, key in enumerate(("uac_as", "uac_high", "uac_admin")):
            rb = tk.Radiobutton(
                uac_row, text=TEXTS[self.lang][key],
                value=("asInvoker", "highestAvailable", "requireAdministrator")[i],
                variable=self.uac_level, bg=BG_CARD, fg=FG,
                activebackground=BG_CARD, selectcolor=BG_ENTRY,
                relief="flat", bd=0, highlightthickness=0,
                font=("Segoe UI", 9), cursor="hand2")
            rb.pack(side="left", padx=(0, 10 if i < 2 else 0))
            self._uac_radios.append(rb)

        # ---- row 1: architecture + bundled files ----
        # architecture selector
        self.arch = tk.StringVar(value="x86")
        arch_box = tk.Frame(opts, bg=BG_CARD)
        arch_box.grid(row=1, column=0, sticky="w", pady=(4, 0))
        tk.Label(arch_box, text=TEXTS[self.lang]["arch_label"], bg=BG_CARD,
                 fg=FG_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        arch_row = tk.Frame(arch_box, bg=BG_CARD)
        arch_row.pack(anchor="w")
        self._arch_radios = []
        for i, key in enumerate(("arch_x86", "arch_x64")):
            rb = tk.Radiobutton(
                arch_row, text=TEXTS[self.lang][key],
                value=("x86", "x64")[i],
                variable=self.arch, bg=BG_CARD, fg=FG,
                activebackground=BG_CARD, selectcolor=BG_ENTRY,
                relief="flat", bd=0, highlightthickness=0,
                font=("Segoe UI", 9), cursor="hand2")
            rb.pack(side="left", padx=(0, 12 if i == 0 else 0))
            self._arch_radios.append(rb)

        # ---- pause behaviour (only matters when the console is visible) ----
        self.pause_mode = tk.StringVar(value="auto")   # auto / always / never
        pause_box = tk.Frame(arch_box, bg=BG_CARD)
        pause_box.pack(anchor="w", pady=(4, 0))
        tk.Label(pause_box, text=TEXTS[self.lang]["pause_label"], bg=BG_CARD,
                 fg=FG_DIM, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 2))
        pause_row = tk.Frame(pause_box, bg=BG_CARD)
        pause_row.pack(anchor="w")
        self._pause_radios = []
        for i, key in enumerate(("pause_auto", "pause_always", "pause_never")):
            rb = tk.Radiobutton(
                pause_row, text=TEXTS[self.lang][key],
                value=("auto", "always", "never")[i],
                variable=self.pause_mode, bg=BG_CARD, fg=FG,
                activebackground=BG_CARD, selectcolor=BG_ENTRY,
                relief="flat", bd=0, highlightthickness=0,
                font=("Segoe UI", 9), cursor="hand2")
            rb.pack(side="left", padx=(0, 10 if i < 2 else 0))
            self._pause_radios.append(rb)

        # bundled files / folders
        self.bundled = []                     # list of absolute paths
        files_box = tk.Frame(opts, bg=BG_CARD)
        files_box.grid(row=1, column=1, sticky="ew", pady=(4, 0))
        files_box.columnconfigure(0, weight=1)
        tk.Label(files_box, text=TEXTS[self.lang]["bundle_label"], bg=BG_CARD,
                 fg=FG_DIM, font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 2))
        btn_row = tk.Frame(files_box, bg=BG_CARD)
        btn_row.grid(row=1, column=0, sticky="w")
        self.btn_add_files = self._button(
            btn_row, "bundle_add", self._add_bundled, ACCENT, ACCENT_HV)
        self.btn_add_files.pack(side="left")
        self.btn_add_folder = self._button(
            btn_row, "bundle_add_dir", self._add_bundled_folder, ACCENT, ACCENT_HV)
        self.btn_add_folder.pack(side="left", padx=(8, 0))
        self.btn_clear_bundled = self._button(
            btn_row, "bundle_clear", self._clear_bundled, DANGER, DANGER_HV)
        self.btn_clear_bundled.pack(side="left", padx=(8, 0))

        self.bundled_list = tk.Listbox(
            files_box, height=3, bg=BG_ENTRY, fg=FG_DIM, relief="flat",
            font=("Consolas", 8), activestyle="none", bd=0,
            highlightthickness=1, highlightbackground=BORDER)
        self.bundled_list.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        self.hint_app = self._hint(self.card_app, 2, "app_hint")

        # ---- log card ----
        log_card = tk.Frame(outer, bg=BG_CARD, highlightthickness=1,
                            highlightbackground=BORDER)
        log_card.grid(row=0, column=1, sticky="nsew")
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(1, weight=1)

        self.lbl_log = tk.Label(log_card, text="Log", bg=BG_CARD, fg=FG_DIM,
                                font=("Segoe UI", 9, "bold"), anchor="w")
        self.lbl_log.grid(row=0, column=0, sticky="w", padx=14, pady=(5, 2))

        self.log_txt = tk.Text(log_card, bg=BG_ENTRY, fg=FG_DIM, relief="flat",
                               font=("Consolas", 9), width=64, height=3, wrap="word",
                               state="disabled", padx=8, pady=4,
                               selectbackground=ACCENT, selectforeground="white")
        self.log_txt.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 5))

        # scrollbar for log
        sb = tk.Scrollbar(log_card, command=self.log_txt.yview,
                          bg=BG_CARD, troughcolor=BG_ENTRY, width=10)
        sb.grid(row=1, column=1, sticky="ns", padx=(0, 10), pady=(0, 5))
        self.log_txt.configure(yscrollcommand=sb.set)

        # ---- bottom buttons ----
        bottom = tk.Frame(left_panel, bg=BG)
        bottom.grid(row=5, column=0, sticky="ew", pady=(7, 0))
        bottom.columnconfigure(0, weight=1)

        self.btn_convert = tk.Button(
            bottom, text="Convert", command=self.on_convert,
            bg=GREEN, fg="white", activebackground=GREEN_HV, activeforeground="white",
            relief="flat", font=("Segoe UI", 11, "bold"), cursor="hand2",
            padx=22, pady=6, bd=0)
        self.btn_convert.grid(row=0, column=0, sticky="w")
        self._bind_hover(self.btn_convert, GREEN, GREEN_HV)

        btns_right = tk.Frame(bottom, bg=BG)
        btns_right.grid(row=0, column=1, sticky="e")

        self.btn_open = tk.Button(
            btns_right, text="Open dist folder", command=self.open_dist,
            bg=ACCENT, fg="white", activebackground=ACCENT_HV, activeforeground="white",
            relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2",
            padx=16, pady=6, bd=0, state="disabled")
        self.btn_open.pack(side="left", padx=(0, 10))
        self._bind_hover(self.btn_open, ACCENT, ACCENT_HV)

        self.btn_close = tk.Button(
            btns_right, text="Close", command=self.on_close,
            bg=DANGER, fg="white", activebackground=DANGER_HV, activeforeground="white",
            relief="flat", font=("Segoe UI", 10, "bold"), cursor="hand2",
            padx=16, pady=6, bd=0)
        self.btn_close.pack(side="left")
        self._bind_hover(self.btn_close, DANGER, DANGER_HV)

        status_bar = tk.Frame(outer, bg=BG_CARD,
                              highlightthickness=1, highlightbackground=BORDER)
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.status_var = tk.StringVar(value=TEXTS[self.lang][self.status_key])
        self.status_lbl = tk.Label(
            status_bar, textvariable=self.status_var, bg=BG_CARD, fg=FG_DIM,
            font=("Segoe UI", 8), anchor="w", padx=8, pady=3)
        self.status_lbl.pack(fill="x")

        # drag & drop-ish: double-click entry opens file dialog
        for w, fn in ((e, self.pick_input), (e2, self.pick_output),
                      (e3, self.pick_icon)):
            w.bind("<Double-Button-1>", lambda _e, f=fn: f())

    def _build_menubar(self):
        """Native menu bar at the very top of the window."""
        t = TEXTS[self.lang]
        menubar = tk.Menu(self, bg=BG_CARD, fg=FG,
                          activebackground=BG_ENTRY, activeforeground=FG,
                          bd=0, relief="flat")

        # ---- File menu ----
        m_file = tk.Menu(menubar, tearoff=0, bg=BG_CARD, fg=FG,
                         activebackground=BG_ENTRY, activeforeground=FG)
        m_file.add_command(label=t["convert"], command=self.on_convert)
        m_file.add_command(label=t["open_dist"], command=self.open_dist)
        m_file.add_separator()
        m_file.add_command(label=t["close"], command=self.on_close)
        menubar.add_cascade(label={"en": "File", "pl": "Plik"}[self.lang],
                            menu=m_file)

        # ---- Lang menu (radio list of available languages) ----
        m_lang = tk.Menu(menubar, tearoff=0, bg=BG_CARD, fg=FG,
                         activebackground=BG_ENTRY, activeforeground=FG)
        self._lang_var = tk.StringVar(value=self.lang)
        for code, key in (("en", "menu_lang_en"), ("pl", "menu_lang_pl")):
            m_lang.add_radiobutton(label=t[key], value=code,
                                   variable=self._lang_var,
                                   command=lambda c=code: self._on_lang_change(c))
        menubar.add_cascade(label=t["menu_lang"], menu=m_lang)

        # ---- Settings menu ----
        m_set = tk.Menu(menubar, tearoff=0, bg=BG_CARD, fg=FG,
                        activebackground=BG_ENTRY, activeforeground=FG)
        m_set.add_command(label=t["menu_locations"],
                          command=self.show_locations)
        menubar.add_cascade(label=t["menu_settings"], menu=m_set)

        # ---- Help menu ----
        m_help = tk.Menu(menubar, tearoff=0, bg=BG_CARD, fg=FG,
                         activebackground=BG_ENTRY, activeforeground=FG)
        m_help.add_command(label=t["about"], command=self.show_about)
        menubar.add_cascade(label={"en": "Help", "pl": "Pomoc"}[self.lang],
                            menu=m_help)

        self.config(menu=menubar)
        self._menubar = menubar

    def _rebuild_menubar(self):
        """Recreate the menu bar after a language switch."""
        if getattr(self, "_menubar", None):
            self._menubar.destroy()
        self._build_menubar()

    def _style_combobox(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=BG_ENTRY,
                        background=BG_ENTRY, foreground=FG,
                        arrowcolor=FG, bordercolor=BORDER,
                        lightcolor=BG_ENTRY, darkcolor=BG_ENTRY)
        style.map("TCombobox",
                  fieldbackground=[("readonly", BG_ENTRY)],
                  background=[("readonly", BG_ENTRY)],
                  foreground=[("readonly", FG)])
        self.option_add("*TCombobox*Listbox*Background", BG_ENTRY)
        self.option_add("*TCombobox*Listbox*Foreground", FG)
        self.option_add("*TCombobox*Listbox*selectBackground", ACCENT)
        self.option_add("*TCombobox*Listbox*selectForeground", "white")

    def _card(self, parent, row, pady=(0, 0)):
        card = tk.Frame(parent, bg=BG_CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.grid(row=row, column=0, sticky="ew", pady=pady)
        card.columnconfigure(0, weight=1)
        return card

    def _card_row(self, card, row, key):
        lbl = tk.Label(card, text=TEXTS[self.lang][key], bg=BG_CARD, fg=FG_DIM,
                       font=("Segoe UI", 9, "bold"), anchor="w")
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(3, 1))
        return lbl

    def _button(self, parent, key, cmd, bg, hv):
        button = tk.Button(parent, text=TEXTS[self.lang][key], command=cmd,
                           bg=bg, fg="white", activebackground=hv,
                           activeforeground="white", relief="flat", bd=0,
                           font=("Segoe UI", 9, "bold"), cursor="hand2",
                           padx=14, pady=7)
        self._bind_hover(button, bg, hv)
        return button

    @staticmethod
    def _bind_hover(button, bg, hover_bg):
        button.bind("<Enter>", lambda _event: button.configure(bg=hover_bg))
        button.bind("<Leave>", lambda _event: button.configure(bg=bg))

    def _hint(self, card, row, key):
        lbl = tk.Label(card, text=TEXTS[self.lang][key], bg=BG_CARD, fg=FG_DIM,
                       font=("Segoe UI", 8, "italic"), anchor="w")
        lbl.grid(row=row, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 2))
        return lbl

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_reqwidth(), self.winfo_reqheight()
        self.minsize(w, h)
        x = (self.winfo_screenwidth() - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ------------------------------------------------------------ language
    def _on_lang_change(self, code):
        self.lang = code
        self.apply_language()
        self._rebuild_menubar()

    def apply_language(self):
        t = TEXTS[self.lang]
        self.title(t["title"])
        self.title_lbl.config(text="BAT2EXE")
        self.subtitle_lbl.config(
            text={"en": "Convert Windows batch scripts into standalone executables",
                  "pl": "Konwertuj skrypty wsadowe Windows na samodzielne pliki EXE"}[self.lang])
        self.lbl_input.config(text=t["input_label"])
        self.btn_input.config(text=t["input_btn"])
        self.hint_input.config(text=t["input_hint"])
        self.lbl_output.config(text=t["output_label"])
        self.btn_output.config(text=t["output_btn"])
        self.hint_output.config(text=t["output_hint"])
        self.lbl_icon.config(text=t["icon_label"])
        self.btn_icon.config(text=t["icon_btn"])
        self.chk_nobg.config(text=t["remove_bg"])
        self.hint_icon.config(text=t["icon_hint"])
        self.lbl_app.config(text=t["app_label"])
        self.rb_con_show.config(text=t["console_show"])
        self.rb_con_hide.config(text=t["console_hide"])
        for rb, key in zip(self._uac_radios, ("uac_as", "uac_high", "uac_admin")):
            rb.config(text=t[key])
        for rb, key in zip(self._arch_radios, ("arch_x86", "arch_x64")):
            rb.config(text=t[key])
        for rb, key in zip(self._pause_radios,
                           ("pause_auto", "pause_always", "pause_never")):
            rb.config(text=t[key])
        self.btn_add_files.config(text=t["bundle_add"])
        self.btn_add_folder.config(text=t["bundle_add_dir"])
        self.btn_clear_bundled.config(text=t["bundle_clear"])
        self.hint_app.config(text=t["app_hint"])
        self.lbl_log.config(text=t["log"])
        self.btn_convert.config(text=t["convert"])
        self.btn_open.config(text=t["open_dist"])
        self.btn_close.config(text=t["close"])
        self.status_var.set(t[self.status_key])
        self._center()

    # ------------------------------------------------------------ actions
    def log(self, msg):
        self.log_txt.configure(state="normal")
        self.log_txt.insert("end", msg + "\n")
        self.log_txt.see("end")
        self.log_txt.configure(state="disabled")

    def _set_status(self, key):
        self.status_key = key
        self.status_var.set(TEXTS[self.lang][key])

    def pick_input(self):
        path = filedialog.askopenfilename(
            title=TEXTS[self.lang]["input_label"],
            filetypes=[("Batch files", "*.bat *.cmd"), ("All files", "*.*")])
        if path:
            self.input_file.set(path)

    def pick_output(self):
        path = filedialog.askdirectory(title=TEXTS[self.lang]["output_label"])
        if path:
            self.output_dir.set(path)

    def _add_bundled(self):
        paths = filedialog.askopenfilenames(
            title=TEXTS[self.lang]["bundle_label"],
            filetypes=[("All files", "*.*")])
        for p in paths:
            if p not in self.bundled:
                self.bundled.append(p)
        self._refresh_bundled()

    def _add_bundled_folder(self):
        path = filedialog.askdirectory(title=TEXTS[self.lang]["bundle_add_dir"])
        if path and path not in self.bundled:
            self.bundled.append(path)
        self._refresh_bundled()

    def _clear_bundled(self):
        self.bundled.clear()
        self._refresh_bundled()

    def _refresh_bundled(self):
        self.bundled_list.delete(0, "end")
        for p in self.bundled:
            self.bundled_list.insert("end", p)

    def pick_icon(self):
        path = filedialog.askopenfilename(
            title=TEXTS[self.lang]["icon_label"],
            filetypes=[("All supported images",
                        "*.ico *.png *.jpg *.jpeg *.bmp *.gif *.webp *.tif *.tiff"),
                       ("Icon files", "*.ico"),
                       ("PNG images", "*.png"),
                       ("JPEG images", "*.jpg *.jpeg"),
                       ("All files", "*.*")])
        if path:
            self.icon_file.set(path)

    def on_convert(self):
        t = TEXTS[self.lang]
        inp = self.input_file.get().strip()
        out = self.output_dir.get().strip()

        if not os.path.isfile(TOOL_PATH):
            messagebox.showerror(t["error_box"], t["err_no_tool"].format(path=TOOL_PATH))
            return
        if not inp:
            messagebox.showwarning(t["info_box"], t["err_no_input"])
            return
        if not inp.lower().endswith((".bat", ".cmd")):
            messagebox.showwarning(t["info_box"], t["err_bad_ext"])
            return
        if not out:
            messagebox.showwarning(t["info_box"], t["err_no_output"])
            return

        ico = self.icon_file.get().strip()
        if ico and not os.path.isfile(ico):
            messagebox.showwarning(t["info_box"], t["err_no_ico"])
            return
        if ico:
            ext = os.path.splitext(ico)[1].lower()
            if ext not in (".ico", ".png", ".jpg", ".jpeg", ".bmp",
                           ".gif", ".webp", ".tif", ".tiff"):
                messagebox.showwarning(t["info_box"], t["err_bad_ico"])
                return

        dist = os.path.join(out, "dist")
        try:
            os.makedirs(dist, exist_ok=True)   # ALWAYS create dist in chosen location
        except OSError as exc:
            messagebox.showerror(t["error_box"], str(exc))
            return
        self.dist_dir = dist

        self.log("=" * 60)
        self.log(TEXTS[self.lang]["working"])
        self._set_status("working")
        self.btn_convert.config(state="disabled")
        remove_bg = self.remove_bg.get()      # read NOW, not from worker thread
        show_console = self.show_console.get()
        uac_level = self.uac_level.get()
        arch = self.arch.get()
        pause_mode = self.pause_mode.get()
        bundle = list(self.bundled)          # snapshot for the worker
        threading.Thread(target=self._run_convert,
                         args=(inp, dist, ico or None, remove_bg,
                               show_console, uac_level, arch, bundle,
                               pause_mode),
                         daemon=True).start()

    def _run_convert(self, inp, dist, ico=None, remove_bg=True,
                     show_console=True, uac_level="asInvoker",
                     arch="x86", bundle=None, pause_mode="auto"):
        """Run BAT2EXE.EXE in a temp workdir, then move the .exe into dist."""
        import shutil
        import tempfile

        base = os.path.splitext(os.path.basename(inp))[0]
        work = None
        try:
            # BAT2EXE.EXE (JJSoft 2010) is a fragile .NET 2.0/VB tool:
            #  * it crashes when stdout is redirected directly
            #  * it crashes when a log file lives in the same folder
            #    (it tries to DELETE its own working directory -> the open
            #    log file blocks the deletion -> IOException)
            #  * it expects short, plain-ASCII paths without spaces
            #    (hard-codes 'C:\temp\bat2win' internally in some builds)
            # Therefore we run it in a short, ASCII-only temp directory
            # WITHOUT any redirection, then copy the produced .exe to dist.
            root = os.path.join(tempfile.gettempdir(), "bat2exe_work")
            os.makedirs(root, exist_ok=True)
            work = tempfile.mkdtemp(prefix="job", dir=root)
            work_bat = os.path.join(work, "in.bat")

            # ---- auto-pause / no-pause: rewrite the payload before compiling
            want_pause = _resolve_pause(pause_mode, show_console)
            _write_payload(inp, work_bat, want_pause)

            proc = subprocess.run(
                [TOOL_PATH, "in.bat"],
                cwd=work,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW)

            exe_path = os.path.join(work, "in.exe")
            if os.path.isfile(exe_path):
                target = os.path.join(dist, base + ".exe")
                shutil.move(exe_path, target)
                if ico:
                    try:
                        if MODULES_DIR not in sys.path:
                            sys.path.insert(0, MODULES_DIR)
                        import embed_icon
                        if embed_icon.set_icon_auto(target, ico,
                                                    remove_background=remove_bg):
                            self._log_queue.put("[OK] Icon embedded.")
                        else:
                            self._log_queue.put("[WARN] " + TEXTS[self.lang]["warn_icon"])
                    except Exception as icon_exc:          # noqa: BLE001
                        # a broken image must not fail the whole conversion
                        self._log_queue.put(f"[WARN] Icon error: {icon_exc}")
                        self._log_queue.put("[WARN] " + TEXTS[self.lang]["warn_icon"])
                # ---- console visibility + UAC manifest ----
                try:
                    if MODULES_DIR not in sys.path:
                        sys.path.insert(0, MODULES_DIR)
                    import embed_icon
                    res = embed_icon.finalize_exe(
                        target,
                        show_console=show_console,
                        uac_level=uac_level)
                    if res["subsystem"]:
                        self._log_queue.put("[OK] " + TEXTS[self.lang]["ok_subsystem"])
                    if res["manifest"]:
                        self._log_queue.put("[OK] " + TEXTS[self.lang]["ok_manifest"]
                                            .format(level=uac_level))
                except Exception as fin_exc:               # noqa: BLE001
                    self._log_queue.put(f"[WARN] Finalize error: {fin_exc}")
                # ---- bundled files -> RT_RCDATA ----
                if bundle:
                    try:
                        import embed_icon
                        flat = embed_icon.collect_files(bundle)
                        if embed_icon.embed_resources(target, flat):
                            self._log_queue.put(
                                "[OK] " + TEXTS[self.lang]["ok_bundle"]
                                .format(n=len(flat)))
                        else:
                            self._log_queue.put("[WARN] " +
                                                TEXTS[self.lang]["warn_bundle"])
                    except Exception as b_exc:             # noqa: BLE001
                        self._log_queue.put(f"[WARN] Bundle error: {b_exc}")
                # ---- architecture ----
                if arch == "x64":
                    try:
                        import embed_icon
                        x64 = embed_icon.build_for_arch(target, "x64")
                        if x64:
                            shutil.move(x64, target)
                            self._log_queue.put(
                                "[OK] " + TEXTS[self.lang]["ok_x64"])
                        else:
                            self._log_queue.put("[WARN] " +
                                                TEXTS[self.lang]["warn_x64"])
                    except Exception as a_exc:             # noqa: BLE001
                        self._log_queue.put(f"[WARN] Arch error: {a_exc}")
                self._log_queue.put("__FINISH__True")
            else:
                self._log_queue.put(
                    "[WARN] Converter finished but produced no .exe "
                    "(exit code {}).".format(proc.returncode))
                self._log_queue.put("__FINISH__False")
        except Exception as exc:                       # noqa: BLE001
            self._log_queue.put(f"[ERROR] {exc}")
            self._log_queue.put("__FINISH__False")
        finally:
            if work:
                shutil.rmtree(work, ignore_errors=True)

    def _poll_log(self):
        """Consume log messages queued by the worker thread (main thread only)."""
        try:
            while True:
                item = self._log_queue.get_nowait()
                if item.startswith("__FINISH__"):
                    self._finish(item == "__FINISH__True")
                else:
                    self.log(item)
        except queue.Empty:
            pass
        self._poll_log_id = self.after(100, self._poll_log)

    def _log_chunk(self, text):
        for line in (text or "").splitlines():
            self.log(line)

    def _finish(self, ok):
        t = TEXTS[self.lang]
        self.btn_convert.config(state="normal")
        if ok:
            self._set_status("done_ok")
            self.log("[OK] " + t["done_ok"])
            messagebox.showinfo(t["success_box"], t["done_ok"])
            self.btn_open.config(state="normal")
        else:
            self._set_status("done_fail")
            self.log("[FAIL] " + t["done_fail"])
            messagebox.showerror(t["error_box"], t["done_fail"])

    def show_about(self):
        """Modal About popup, styled like the rest of the app."""
        t = TEXTS[self.lang]
        win = tk.Toplevel(self)
        win.title(t["about_title"])
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)

        # accent top bar (visual anchor of the dialog)
        bar = tk.Frame(win, bg=ACCENT, height=4)
        bar.pack(fill="x", side="top")

        frm = tk.Frame(win, bg=BG)
        frm.pack(fill="both", expand=True, padx=26, pady=(20, 20))

        # ---- logo badge + app name row ----
        head = tk.Frame(frm, bg=BG)
        head.pack(fill="x")
        logo = tk.Canvas(head, width=52, height=52, bg=BG,
                         highlightthickness=0)
        logo.grid(row=0, column=0, sticky="w")
        # rounded square with 'B2E' monogram
        _round_rect(logo, 2, 2, 50, 50, radius=12,
                    fill=ACCENT, outline="")
        logo.create_text(26, 26, text="B2E", fill="white",
                         font=("Segoe UI", 11, "bold"))

        name_box = tk.Frame(head, bg=BG)
        name_box.grid(row=0, column=1, sticky="w", padx=(14, 0))
        tk.Label(name_box, text="BAT2EXE", bg=BG, fg=FG,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(name_box, text="Batch  →  EXE   Converter", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 9)).pack(anchor="w")
        head.columnconfigure(1, weight=1)

        # ---- description card ----
        card = tk.Frame(frm, bg=BG_CARD, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="x", pady=(18, 0))
        tk.Label(card, text=t["about_body"], bg=BG_CARD, fg=FG,
                 font=("Segoe UI", 10), justify="left", anchor="w",
                 padx=16, pady=14).pack(fill="x")

        # ---- author and contact links ----
        author_card = tk.Frame(frm, bg=BG_CARD, highlightthickness=1,
                               highlightbackground=BORDER)
        author_card.pack(fill="x", pady=(10, 0))
        tk.Label(author_card, text=t["author_label"], bg=BG_CARD, fg=FG_DIM,
                 font=("Segoe UI", 9, "bold"), anchor="w").pack(
                     fill="x", padx=14, pady=(8, 2))
        tk.Label(author_card, text="Sebastian Januchowski\npolsoft.ITS™",
                 bg=BG_CARD, fg=FG, font=("Segoe UI", 9),
                 justify="left", anchor="w").pack(fill="x", padx=14)

        contact_buttons = tk.Frame(author_card, bg=BG_CARD)
        contact_buttons.pack(fill="x", padx=10, pady=(6, 10))
        tk.Button(
            contact_buttons, text="polsoft.its@mail.com",
            command=lambda: webbrowser.open("mailto:polsoft.its@mail.com"),
            bg=ACCENT, fg="white", activebackground=ACCENT_HV,
            activeforeground="white", relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2",
            padx=10, pady=5).pack(fill="x", pady=(0, 5))
        tk.Button(
            contact_buttons, text="https://github.com/polsoft-it",
            command=lambda: webbrowser.open("https://github.com/polsoft-it"),
            bg=ACCENT, fg="white", activebackground=ACCENT_HV,
            activeforeground="white", relief="flat", bd=0,
            font=("Segoe UI", 9, "bold"), cursor="hand2",
            padx=10, pady=5).pack(fill="x")

        # ---- engine / version footer ----
        foot = tk.Frame(frm, bg=BG)
        foot.pack(fill="x", pady=(14, 0))
        tk.Label(foot, text="Converter engine:  JJSoft BAT2EXE  © 2010",
                 bg=BG, fg=FG_DIM, font=("Segoe UI", 8)).pack(side="left")
        tk.Label(foot, text="v1.0", bg=BG, fg=ACCENT_HV,
                 font=("Segoe UI", 8, "bold")).pack(side="right")

        # ---- close button ----
        tk.Button(frm, text=t["about_close"], command=win.destroy,
                  bg=ACCENT, fg="white", activebackground=ACCENT_HV,
                  activeforeground="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=22, pady=7).pack(anchor="e", pady=(16, 0))

        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        win.geometry(f"+{x}+{y}")
        win.grab_set()
        win.bind("<Escape>", lambda _e: win.destroy())
        win.lift()
        win.focus_force()
        win.focus_set()

    # ------------------------------------------------------------------
    # Settings → tool locations popup
    # ------------------------------------------------------------------
    DEFAULT_TOOL_DIRS = {
        "upx":     os.path.join("modules", "upx.exe"),
        "7z":      os.path.join("modules", "7z.exe"),
        "7zsfx":   os.path.join("modules", "7z.sfx"),
        "7zdll":   os.path.join("modules", "7z.dll"),
        "signtool": os.path.join("modules", "SignTools", "signtool.exe"),
    }

    def show_locations(self):
        """Settings popup: non-standard tool locations, each with Browse
        and a Reset-to-default button."""
        t = TEXTS[self.lang]
        win = tk.Toplevel(self)
        win.title(t["loc_title"])
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)

        if not hasattr(self, "tool_paths"):
            self.tool_paths = {}          # key -> StringVar
        frm = tk.Frame(win, bg=BG)
        frm.pack(fill="both", expand=True, padx=20, pady=(16, 14))

        tk.Label(frm, text=t["loc_hint"], bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 9, "italic"),
                 justify="left", anchor="w").pack(fill="x", pady=(0, 12))

        rows = []
        for i, (key, label_key) in enumerate((
                ("upx", "loc_upx"), ("7z", "loc_7z"),
                ("7zsfx", "loc_7zsfx"), ("7zdll", "loc_7zdll"),
                ("signtool", "loc_signtool"))):
            row = tk.Frame(frm, bg=BG)
            row.pack(fill="x", pady=(0, 10))
            tk.Label(row, text=t[label_key], bg=BG, fg=FG,
                     font=("Segoe UI", 9), anchor="w").pack(fill="x")

            var = self.tool_paths.setdefault(key, tk.StringVar(value=""))
            ent = tk.Entry(row, textvariable=var, bg=BG_ENTRY, fg=FG,
                           insertbackground=FG, relief="flat",
                           font=("Consolas", 9))
            ent.pack(side="left", fill="x", expand=True, pady=(4, 0))

            default_lbl = tk.Label(row, text=t["loc_default"], bg=BG,
                                   fg=FG_DIM, font=("Segoe UI", 8, "italic"))
            default_lbl.pack(side="left", padx=(8, 4), pady=(4, 0))

            def browse(k=key, v=var):
                p = filedialog.askopenfilename(
                    title=TEXTS[self.lang]["loc_browse"],
                    filetypes=[("Executable / module", "*.exe;*.sfx;*.dll"),
                               ("All files", "*.*")])
                if p:
                    v.set(os.path.abspath(p))

            tk.Button(row, text=t["loc_browse"], command=browse,
                      bg=ACCENT, fg="white", activebackground=ACCENT_HV,
                      activeforeground="white", relief="flat", bd=0,
                      font=("Segoe UI", 8, "bold"), cursor="hand2",
                      padx=10, pady=4).pack(side="left", padx=(8, 0), pady=(4, 0))

            def reset(k=key, v=var, lbl=default_lbl):
                v.set("")
                lbl.config(text=TEXTS[self.lang]["loc_default"])

            tk.Button(row, text=t["loc_reset"], command=reset,
                      bg=DANGER, fg="white", activebackground=DANGER_HV,
                      activeforeground="white", relief="flat", bd=0,
                      font=("Segoe UI", 8, "bold"), cursor="hand2",
                      padx=10, pady=4).pack(side="left", padx=(6, 0), pady=(4, 0))
            rows.append((key, var, default_lbl, ent))

            # reflect initial non-default state
            def sync(_e=None, v=var, lbl=default_lbl, k=key):
                if v.get().strip():
                    lbl.config(text=v.get().strip())
            ent.bind("<KeyRelease>", sync)
            var.trace_add("write", lambda *_a, v=var, lbl=default_lbl:
                          lbl.config(text=v.get().strip() or
                                     TEXTS[self.lang]["loc_default"]))

        tk.Button(frm, text=t["loc_close"], command=win.destroy,
                  bg=ACCENT, fg="white", activebackground=ACCENT_HV,
                  activeforeground="white", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), cursor="hand2",
                  padx=22, pady=6).pack(anchor="e", pady=(14, 0))

        win.update_idletasks()
        w, h = win.winfo_width(), win.winfo_height()
        x = self.winfo_rootx() + (self.winfo_width() - w) // 2
        y = self.winfo_rooty() + (self.winfo_height() - h) // 2
        win.geometry(f"+{x}+{y}")
        win.grab_set()
        win.bind("<Escape>", lambda _e: win.destroy())
        win.lift()
        win.focus_force()

    def open_dist(self):
        if self.dist_dir and os.path.isdir(self.dist_dir):
            os.startfile(self.dist_dir)                # noqa: S606 (Windows)

    def on_close(self):
        if messagebox.askokcancel(TEXTS[self.lang]["info_box"],
                                  TEXTS[self.lang]["ask_exit"]):
            self.destroy()


# ---------------------------------------------------------------------------
# Interactive configuration mode (CLI):  python gui.py --configure
# ---------------------------------------------------------------------------
def _ask(prompt: str, default: str = "") -> str:
    shown = f"  {prompt}" + (f" [{default}]" if default else "") + ": "
    val = input(shown).strip()
    return val or default


def _ask_bool(prompt: str, default: bool) -> bool:
    d = "Y/n" if default else "y/N"
    v = input(f"  {prompt} [{d}]: ").strip().lower()
    if not v:
        return default
    return v in ("y", "yes", "t", "tak", "1")


def run_configure():
    """Terminal wizard: asks for every build option, then runs the GUI's
    exact conversion pipeline and prints the result. No window needed."""
    print("=" * 56)
    print(" BAT2EXE — interactive configuration")
    print("=" * 56)

    # 1. input file
    while True:
        inp = _ask("Batch file (.bat/.cmd)")
        if os.path.isfile(inp) and inp.lower().endswith((".bat", ".cmd")):
            break
        print("  ! file not found or wrong extension, try again")

    # 2. output location
    out = _ask("Output location (dist created inside)", os.getcwd())

    # 3. console mode
    show_console = _ask_bool("Show console window (CMD)?", True)

    # 4. pause behaviour
    print("  Pause after finish:")
    print("    1 = auto   (pause only if console is visible)")
    print("    2 = always pause")
    print("    3 = never (close instantly)")
    pv = _ask("  Choice", "1")
    pause_mode = {"1": "auto", "2": "always", "3": "never"}.get(pv, "auto")

    # 5. icon
    ico = ""
    if _ask_bool("Custom icon?", False):
        while True:
            ico = _ask("  Image file (ico/png/jpg/...)")
            if os.path.isfile(ico):
                break
            print("  ! not found, try again")
    remove_bg = _ask_bool("  Remove icon background?", True) if ico else False

    # 6. UAC
    print("  Run as administrator:")
    print("    1 = no   2 = if available   3 = always (UAC prompt)")
    uv = _ask("  Choice", "1")
    uac = {"1": "asInvoker", "2": "highestAvailable",
           "3": "requireAdministrator"}.get(uv, "asInvoker")

    # 7. architecture
    av = _ask("Architecture  1 = x86   2 = x64", "1")
    arch = "x64" if av == "2" else "x86"

    # 8. bundled files
    bundle = []
    if _ask_bool("Bundle extra files/folders into the exe?", False):
        while True:
            p = _ask("  Path (empty = done)")
            if not p:
                break
            if os.path.exists(p):
                bundle.append(p)
            else:
                print("  ! not found")

    print("-" * 56)
    print(" Building...")

    dist = os.path.join(out, "dist")
    os.makedirs(dist, exist_ok=True)
    app = App()
    app.withdraw()                       # headless run of the GUI pipeline
    app._run_convert(os.path.abspath(inp), dist,
                     ico=os.path.abspath(ico) if ico else None,
                     remove_bg=remove_bg, show_console=show_console,
                     uac_level=uac, arch=arch,
                     bundle=[os.path.abspath(b) for b in bundle],
                     pause_mode=pause_mode)
    app.destroy()

    base = os.path.splitext(os.path.basename(inp))[0]
    exe = os.path.join(dist, base + ".exe")
    print("-" * 56)
    if os.path.isfile(exe):
        print(f" [OK] Built: {exe}")
        return 0
    print(" [FAIL] Conversion failed.")
    return 1


if __name__ == "__main__":
    if "--configure" in sys.argv or "-c" in sys.argv:
        sys.exit(run_configure())
    app = App()
    app.mainloop()
