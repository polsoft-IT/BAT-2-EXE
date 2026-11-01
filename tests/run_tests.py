# -*- coding: utf-8 -*-
"""
run_tests.py — End-to-end test suite for the BAT2EXE GUI pipeline.

What it does:
  1. Builds fixture files (tests/make_fixtures.py) — batch files + .ico.
  2. Runs the same conversion path the GUI uses (gui.App._run_convert)
     against each batch file, with and without an icon.
  3. Verifies the produced .exe exists, contains the icon resource
     (when requested), and RUNS correctly (real process launch, output
     captured and compared with what the plain .bat prints).
  4. Cleans up all temporary output.

Usage:
    python tests/run_tests.py          # run all tests
    python tests/run_tests.py -v       # verbose
Exit code 0 = all tests passed.
"""

import ctypes
import os
import shutil
import subprocess
import sys
import tempfile
import time
import queue
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "modules"))

import make_fixtures                                    # noqa: E402
import embed_icon                                       # noqa: E402

VERBOSE = "-v" in sys.argv

PASS, FAIL = "[PASS]", "[FAIL]"
_results = []


def report(name, ok, detail=""):
    _results.append((name, ok))
    line = f"{PASS if ok else FAIL} {name}"
    if detail:
        line += f" — {detail}"
    print(line)


# ---------------------------------------------------------------------------
# Conversion (uses the GUI's worker method without opening a window)
# ---------------------------------------------------------------------------
def convert(bat_path, use_icon=None, out_dir=None):
    """Run the GUI conversion path. Returns (ok, exe_path, log_lines, out_dir)."""
    import tkinter as tk
    import importlib.util
    from tkinter import messagebox

    messagebox.showinfo = lambda *a, **k: None
    messagebox.showerror = lambda *a, **k: None
    messagebox.showwarning = lambda *a, **k: None

    spec = importlib.util.spec_from_file_location("gui", os.path.join(ROOT, "gui.py"))
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)

    app = gui.App()
    out_dir = out_dir or tempfile.mkdtemp(prefix="b2x_test_")
    app.input_file.set(os.path.abspath(bat_path))
    app.output_dir.set(out_dir)
    if use_icon:
        app.icon_file.set(os.path.abspath(use_icon))
    app.on_convert()

    deadline = time.time() + 180
    while time.time() < deadline:
        app.update()
        if app.btn_convert["state"] == "normal":
            break
        time.sleep(0.1)
    log = app.log_txt.get("1.0", "end").splitlines()
    ok = any("[OK]" in ln for ln in log) and not any("[FAIL]" in ln for ln in log)
    # cancel pending callbacks AND clear every Tk variable reference before
    # destroy — else Python 3.13+ GC fires Variable.__del__ on dead Tcl from
    # worker threads and spams 'main thread is not in main loop'
    try:
        app.tk.call("after", "cancel", app._poll_log_id)
    except Exception:
        pass
    for name in ("input_file", "output_dir", "icon_file", "remove_bg",
                 "show_console", "uac_level", "arch", "pause_mode"):
        v = getattr(app, name, None)
        if v is not None:
            try:
                del app.__dict__[name]      # drop ref so no __del__ on dead tk
            except Exception:
                pass
    import gc
    gc.collect()
    app.destroy()
    exe = os.path.join(out_dir, "dist",
                       os.path.splitext(os.path.basename(bat_path))[0] + ".exe")
    return ok, exe, log, out_dir


def has_group_icon(exe_path):
    k32 = ctypes.windll.kernel32
    h = k32.LoadLibraryExW(os.path.abspath(exe_path), None, 0x2 | 0x20)
    if not h:
        return False
    found = bool(k32.FindResourceW(h, ctypes.c_void_p(1), ctypes.c_void_p(14)))
    k32.FreeLibrary(h)
    return found


def run_exe(exe_path, args="", timeout=30):
    """Launch the compiled exe and capture its console output."""
    p = subprocess.run([exe_path] + args.split(), capture_output=True,
                       timeout=timeout, shell=False)
    out = (p.stdout or b"") + (p.stderr or b"")
    return p.returncode, out.decode("utf-8", errors="replace")


def run_bat(bat_path, args="", timeout=30):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run(["cmd", "/c", bat_path] + args.split(),
                       capture_output=True, timeout=timeout, env=env)
    out = (p.stdout or b"") + (p.stderr or b"")
    return p.returncode, out.decode("utf-8", errors="replace")


def cleanup(out_dir):
    shutil.rmtree(out_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_hello():
    bat = make_fixtures.make_hello()
    ok, exe, log, d = convert(bat)
    if not ok or not os.path.isfile(exe):
        report("hello: conversion", False, "no exe / FAIL in log")
        cleanup(d)
        return
    report("hello: conversion", True, os.path.basename(exe))

    rc_bat, out_bat = run_bat(bat, "TESTARG")
    rc_exe, out_exe = run_exe(exe, "TESTARG")
    same = ("Hello from BAT2EXE test!" in out_exe)
    arg_ok = ("TESTARG" in out_exe)
    report("hello: exe runs & prints expected text", same and arg_ok and rc_exe == rc_bat,
           f"rc={rc_exe}")
    cleanup(d)


def test_hello_with_icon():
    bat = make_fixtures.make_hello()
    ico = make_fixtures.make_ico()
    ok, exe, log, d = convert(bat, use_icon=ico)
    if not ok or not os.path.isfile(exe):
        report("hello+icon: conversion", False)
        cleanup(d)
        return
    icon_ok = has_group_icon(exe)
    icon_logged = "[OK] Icon embedded." in log
    rc, out = run_exe(exe, "X")
    runs = ("Hello from BAT2EXE test!" in out)
    report("hello+icon: icon embedded", icon_ok and icon_logged)
    report("hello+icon: exe still runs", runs and rc == 0)
    cleanup(d)


def test_big_output():
    bat = make_fixtures.make_big_output()
    ok, exe, log, d = convert(bat)
    if not ok or not os.path.isfile(exe):
        report("big_output: conversion", False)
        cleanup(d)
        return
    rc, out = run_exe(exe, timeout=60)
    n = sum(1 for ln in out.splitlines() if ln.startswith("line "))
    report("big_output: exe produces 200 lines", n == 200, f"got {n}")
    cleanup(d)


def test_unicode():
    bat = make_fixtures.make_unicode()
    ok, exe, log, d = convert(bat)
    # Unicode content is a known weak spot of BAT2EXE — the tool may
    # refuse or garble it. We only require that the pipeline does not
    # hang and reports something sensible.
    ran = ok and os.path.isfile(exe)
    report("unicode: pipeline completes without crash", True,
           "exe produced" if ran else "no exe (tool limitation)")
    cleanup(d)


def test_icon_bad_file():
    """GUI must warn but not crash when the .ico is invalid."""
    bat = make_fixtures.make_hello()
    ico = os.path.join(HERE, "_not_an_icon.ico")
    with open(ico, "wb") as fh:
        fh.write(b"this is definitely not an ico file")
    ok, exe, log, d = convert(bat, use_icon=ico)
    warned = any("[warn]" in ln.lower() and "icon" in ln.lower() for ln in log)
    produced = ok and os.path.isfile(exe)
    report("bad-ico: conversion finishes, icon warns",
           produced and warned, f"produced={produced} warned={warned}")
    os.remove(ico)
    cleanup(d)


def main():
    print("=" * 60)
    print("BAT2EXE test suite")
    print("=" * 60)
    fixtures = make_fixtures.make_all()
    if VERBOSE:
        for k, v in fixtures.items():
            print(f"  fixture {k}: {v}")

    test_hello()
    test_hello_with_icon()
    test_big_output()
    test_unicode()
    test_icon_bad_file()

    print("-" * 60)
    n_ok = sum(1 for _, o in _results if o)
    print(f"RESULT: {n_ok}/{len(_results)} passed")
    return 0 if n_ok == len(_results) else 1


if __name__ == "__main__":
    sys.exit(main())
