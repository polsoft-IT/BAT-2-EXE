# -*- coding: utf-8 -*-
"""
make_fixtures.py — Generate test fixture files for the BAT2EXE test suite.

Creates (in this folder, if missing):
  - hello.bat        : simple ASCII batch file (safe end-to-end case)
  - unicode.bat      : batch file with non-ASCII characters (edge case)
  - big_output.bat   : batch file producing many lines of output
  - purple.ico       : valid single-image 32x32 32-bit .ico (purple circle)
"""

import math
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))


def make_hello():
    path = os.path.join(HERE, "hello.bat")
    if os.path.exists(path):
        return path
    with open(path, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write("@echo off\r\n"
                 "echo Hello from BAT2EXE test!\r\n"
                 "echo Argument received: %1\r\n"
                 "exit /b 0\r\n")
    return path


def make_unicode():
    path = os.path.join(HERE, "unicode.bat")
    if os.path.exists(path):
        return path
    with open(path, "w", encoding="cp1250", newline="\r\n") as fh:
        fh.write("@echo off\r\n"
                 "echo Zażółć gęślą jaźń\r\n"
                 "exit /b 0\r\n")
    return path


def make_big_output(lines=200):
    path = os.path.join(HERE, "big_output.bat")
    if os.path.exists(path):
        return path
    with open(path, "w", encoding="ascii", newline="\r\n") as fh:
        fh.write("@echo off\r\n")
        for i in range(lines):
            fh.write(f"echo line {i:04d}\r\n")
        fh.write("exit /b 0\r\n")
    return path


def make_ico(name="purple.ico", w=32, h=32, rgb=(200, 92, 124)):
    path = os.path.join(HERE, name)
    if os.path.exists(path):
        return path
    # BITMAPINFOHEADER, bottom-up, double height (XOR + AND mask)
    bmp = struct.pack("<IiiHHIIiiII", 40, w, h * 2, 1, 32, 0,
                      w * h * 4, 0, 0, 0, 0)
    px = bytearray()
    r, g, b = rgb
    for y in range(h):
        for x in range(w):
            d = math.hypot(x - (w / 2 - 0.5), y - (h / 2 - 0.5))
            # BGRA: filled circle, semi-transparent edge, transparent corners
            if d < w / 2 - 2:
                px += bytes((b, g, r, 255))
            elif d < w / 2:
                px += bytes((b, g, r, 128))
            else:
                px += bytes((0, 0, 0, 0))
    img = bmp + bytes(px) + bytes(((w + 31) // 32 * 4) * h)
    ico = struct.pack("<HHH", 0, 1, 1)
    ico += struct.pack("<BBBBHHII", w, h, 0, 0, 1, 32, len(img), 22)
    ico += img
    with open(path, "wb") as fh:
        fh.write(ico)
    return path


def make_all():
    return {
        "hello": make_hello(),
        "unicode": make_unicode(),
        "big_output": make_big_output(),
        "ico": make_ico(),
    }


if __name__ == "__main__":
    for kind, p in make_all().items():
        print(f"{kind:12s} -> {p}")
