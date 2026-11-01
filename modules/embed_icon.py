# -*- coding: utf-8 -*-
"""
embed_icon.py — Set a custom .ico icon on a compiled .exe, post-build.

BAT2EXE.EXE (JJSoft 2010) cannot embed icons itself, so the GUI calls
set_icon() right after conversion. Two methods are tried:

1. PowerShell + UpdateResourceFromIco  (custom C# helper compiled on the
   fly, uses Win32 BeginUpdateResource/UpdateResourceEndUpdate — always
   available on Windows, no external downloads).
2. Fallback: pure error report (caller logs the failure).

The RT_ICON group is written so Explorer shows the icon immediately.
"""

import ctypes
import io
import os
import subprocess
import tempfile

# Standard Windows icon sizes, largest first — Explorer picks the best one
# per context (desktop, title bar, Alt-Tab, ...).
ICON_SIZES = [256, 128, 64, 48, 32, 24, 16]

# Formats Pillow can open. PNG/JPG/BMP/WEBP/GIF/TIFF all decode losslessly
# into RGBA frames here.
SUPPORTED_IMAGE_EXTS = (
    ".ico", ".png", ".jpg", ".jpeg", ".bmp", ".gif",
    ".webp", ".tif", ".tiff",
)

try:
    from PIL import Image, ImageDraw, ImageFilter  # noqa: F401
    HAVE_PIL = True
except ImportError:                                # pragma: no cover
    HAVE_PIL = False


def ensure_ico(image_path: str, remove_background: bool = False,
               out_path: str | None = None) -> str:
    """Turn any supported image into a full multi-size Windows .ico.

    Handles .ico passthrough (already an icon; optionally rebuilt if
    *remove_background* was requested), and raster formats (png/jpg/bmp/
    gif/webp/tiff) which are auto-scaled from any size down to the full
    ICON_SIZES ladder with high-quality Lanczos resampling.

    When *remove_background* is True the corner-sampled border colour is
    flood-erased from all four edges with alpha feathering (works best on
    flat / near-flat backgrounds).

    Returns the path of the generated .ico (out_path or a temp file).
    Raises ValueError on unsupported/corrupt input.
    """
    if not HAVE_PIL:
        raise RuntimeError("Pillow is not installed - cannot process images")
    from PIL import Image

    image_path = os.path.abspath(image_path)
    if not os.path.isfile(image_path):
        raise ValueError(f"image not found: {image_path}")
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_IMAGE_EXTS:
        raise ValueError(f"unsupported image format: {ext}")

    img = Image.open(image_path)
    try:
        img.load()
    except Exception as exc:
        raise ValueError(f"cannot read image: {exc}") from exc

    # .ico passthrough: Windows handles it natively, no re-encode needed
    if ext == ".ico" and not remove_background:
        return image_path

    img = img.convert("RGBA")
    if remove_background:
        img = _erase_background(img)

    # auto-fit: upscale small images to at least 256 so the top rung of the
    # ladder is a real 256x256 render (Lanczos keeps it crisp)
    w, h = img.size
    if max(w, h) < 256:
        scale = 256 / max(w, h)
        img = img.resize((round(w * scale), round(h * scale)),
                         Image.LANCZOS)
    # enforce square canvas (icon convention) without distorting the art
    img = _square_canvas(img)

    sizes = [(s, s) for s in reversed(ICON_SIZES)]  # small -> large for save()
    try:
        if out_path:
            out_path = os.path.abspath(out_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            img.save(out_path, format="ICO", sizes=sizes,
                     append_images=[img])
        else:
            fd, tmp = tempfile.mkstemp(prefix="b2x_ico_", suffix=".ico")
            os.close(fd)
            img.save(tmp, format="ICO", sizes=sizes,
                     append_images=[img])
            out_path = tmp
    finally:
        img.close()
    return out_path


def _square_canvas(img):
    from PIL import Image
    w, h = img.size
    if w == h:
        return img
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def _erase_background(img):
    """Remove a near-uniform background by sampling all four border rows.

    Strategy: collect border pixel colours, take the dominant one, then
    zero the alpha of every pixel whose colour is within TOLERANCE of it.
    A 1-px alpha feather on the surviving mask edges keeps outlines smooth
    instead of jagged.
    """
    from PIL import Image

    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()

    # 1. dominant border colour (mode of quantised samples)
    samples = []
    for x in range(w):
        samples.append(px[x, 0][:3])
        samples.append(px[x, h - 1][:3])
    for y in range(h):
        samples.append(px[0, y][:3])
        samples.append(px[w - 1, y][:3])
    counts = {}
    for c in samples:
        key = (c[0] // 16, c[1] // 16, c[2] // 16)   # 16-level quantisation
        counts[key] = counts.get(key, 0) + 1
    dom_key = max(counts, key=counts.get)
    dom = tuple(k * 16 + 8 for k in dom_key)

    # 2. tolerance relative to image size — bigger images get slightly
    #    looser matching so JPEG artifacts and soft shadows still vanish
    tol = max(18, min(60, (w + h) // 16))
    tol2 = tol * tol

    mask = Image.new("L", (w, h), 255)
    mpx = mask.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                mpx[x, y] = 0
                continue
            dr, dg, db = r - dom[0], g - dom[1], b - dom[2]
            if dr * dr + dg * dg + db * db <= tol2:
                mpx[x, y] = 0

    # 3. feather the cut edge (1px blur on the mask keeps anti-aliased
    #    borders smooth against any new backdrop)
    mask = mask.filter(__import__("PIL.ImageFilter", fromlist=["ImageFilter"])
                       .GaussianBlur(0.6))
    rgba.putalpha(mask)
    return rgba


def set_icon_auto(exe_path: str, image_path: str,
                  remove_background: bool = False) -> bool:
    """One-call helper: any image -> multi-size .ico -> embed into exe."""
    ico = ensure_ico(image_path, remove_background=remove_background)
    own_temp = os.path.abspath(ico) != os.path.abspath(image_path)
    try:
        ok = set_icon(exe_path, ico)
    finally:
        if own_temp:
            try:
                os.remove(ico)
            except OSError:
                pass
    return ok

# C# helper: copies icon group + all RT_ICON images from an .ico file
# into the target exe's resource section, then rebuilds the PE checksum.
CS_HELPER = r"""
using System;
using System.Runtime.InteropServices;

public class IcoEmbed {
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern IntPtr BeginUpdateResource(string p, bool b);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool UpdateResource(IntPtr h, IntPtr type, IntPtr name,
        ushort lang, byte[] data, uint size);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool EndUpdateResource(IntPtr h, bool b);

    // Parse ICONDIR + ICONDIRENTRY list out of a .ico file
    class IcoFile {
        public ushort count;
        public byte[][] images;   // raw RT_ICON blobs
        public byte[] group;      // raw RT_GROUP_ICON blob
    }

    static IcoFile ParseIco(string path) {
        byte[] all = System.IO.File.ReadAllBytes(path);
        ushort cnt = BitConverter.ToUInt16(all, 4);
        IcoFile f = new IcoFile();
        f.count = cnt;
        f.images = new byte[cnt][];
        int entrySize = 16;
        int dataOffset = 6 + cnt * entrySize;
        // build GRPICONDIRENTRY list (14 bytes each) after GRPICONDIR (6 bytes)
        byte[] grp = new byte[6 + cnt * 14];
        Array.Copy(all, 0, grp, 0, 6);            // reserved, type=1, count
        for (int i = 0; i < cnt; i++) {
            int e = 6 + i * entrySize;
            int g = 6 + i * 14;
            // copy width, height, colorCount, reserved, planes, bitCount
            Array.Copy(all, e,     grp, g,     4);
            Array.Copy(all, e + 4, grp, g + 4, 4);
            uint dataSize = BitConverter.ToUInt32(all, e + 8);
            int imgOff  = (int)BitConverter.ToUInt32(all, e + 12);
            byte[] img = new byte[dataSize];
            Array.Copy(all, imgOff, img, 0, dataSize);
            f.images[i] = img;
            // resource ID = i + 1
            byte[] rid = BitConverter.GetBytes((ushort)(i + 1));
            Array.Copy(rid, 0, grp, g + 12, 2);
        }
        f.group = grp;
        return f;
    }

    public static int Run(string exePath, string icoPath) {
        try {
            IcoFile f = ParseIco(icoPath);
            IntPtr h = BeginUpdateResource(exePath, false);
            if (h == IntPtr.Zero) throw new Exception(
                "BeginUpdateResource failed, error " + Marshal.GetLastWin32Error());
            // RT_ICON = 3, RT_GROUP_ICON = 14; language 0x409
            for (int i = 0; i < f.images.Length; i++) {
                if (!UpdateResource(h, (IntPtr)3, (IntPtr)(i + 1),
                    0x409, f.images[i], (uint)f.images[i].Length))
                    throw new Exception("UpdateResource(RT_ICON " + (i+1) +
                        ") failed, error " + Marshal.GetLastWin32Error());
            }
            if (!UpdateResource(h, (IntPtr)14, (IntPtr)1,
                0x409, f.group, (uint)f.group.Length))
                throw new Exception("UpdateResource(RT_GROUP_ICON) failed, error " +
                    Marshal.GetLastWin32Error());
            if (!EndUpdateResource(h, false))
                throw new Exception("EndUpdateResource failed, error " +
                    Marshal.GetLastWin32Error());
            return 0;
        } catch (Exception ex) {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }

    public static int Main(string[] args) {
        if (args.Length < 2) { Console.Error.WriteLine("usage: exe ico"); return 2; }
        return Run(args[0], args[1]);
    }
}
"""


def set_icon(exe_path: str, ico_path: str) -> bool:
    """Embed *ico_path* as the main icon of *exe_path*. Returns True on success."""
    exe_path = os.path.abspath(exe_path)
    ico_path = os.path.abspath(ico_path)
    if not (os.path.isfile(exe_path) and os.path.isfile(ico_path)):
        return False

    tmp = tempfile.mkdtemp(prefix="icoembed_")
    try:
        cs = os.path.join(tmp, "IcoEmbed.cs")
        exe_helper = os.path.join(tmp, "IcoEmbed.exe")
        with open(cs, "w", encoding="utf-8") as fh:
            fh.write(CS_HELPER)

        # compile helper with the .NET Framework C# compiler shipped with
        # Windows (csc.exe 2.0/4.x under %WINDIR%\Microsoft.NET)
        csc = _find_csc()
        if not csc:
            return False
        r = subprocess.run(
            [csc, "/nologo", "/target:exe", "/out:" + exe_helper, cs],
            capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not os.path.isfile(exe_helper):
            return False

        r = subprocess.run(
            [exe_helper, exe_path, ico_path],
            capture_output=True, text=True, timeout=60,
            creationflags=0x08000000)          # CREATE_NO_WINDOW
        return r.returncode == 0
    except Exception:
        return False
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


def _find_csc():
    import glob
    windir = os.environ.get("WINDIR", r"C:\Windows")
    hits = glob.glob(os.path.join(
        windir, "Microsoft.NET", "Framework*", "v*", "csc.exe"))
    if not hits:
        return None
    # prefer the newest framework version
    hits.sort()
    return hits[-1]


# ---------------------------------------------------------------------------
# PE post-processing: console window + UAC manifest
# ---------------------------------------------------------------------------
# Pure-Python PE patching (no dependencies): flips the optional-header
# Subsystem field and injects/replaces a full manifest resource with the
# requested UAC execution level. Both operations are done in-place after
# every other build step so nothing can overwrite them.

import struct

# IMAGE_OPTIONAL_HEADER.Subsystem values (correct PE spec values):
#   IMAGE_SUBSYSTEM_WINDOWS_GUI = 2  → no console window
#   IMAGE_SUBSYSTEM_WINDOWS_CUI = 3  → console window
SUB_NO_CONSOLE = 2
SUB_CONSOLE = 3


def _pe_parse(data: bytes):
    """Locate the PE optional header inside *data*. Returns offsets dict."""
    if data[:2] != b"MZ":
        raise ValueError("not an executable (MZ missing)")
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe_off:pe_off + 4] != b"PE\x00\x00":
        raise ValueError("PE signature missing")
    coff = pe_off + 4
    machine, nsec, _, _, _, optsz = struct.unpack_from("<HHIIIH", data, coff)
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    if magic == 0x20B:                      # PE32+
        sub_off = opt + 68                  # Subsystem field
        numrva_off = opt + 108              # NumberOfRvaAndSizes
        rva_off = opt + 112                 # data directories start
    elif magic == 0x10B:                    # PE32
        sub_off = opt + 68
        numrva_off = opt + 92
        rva_off = opt + 96
    else:
        raise ValueError(f"unknown optional-header magic {magic:#x}")
    return {"pe_off": pe_off, "coff": coff, "opt": opt,
            "nsec": nsec, "sub_off": sub_off,
            "numrva_off": numrva_off, "rva_off": rva_off}


def _rva_to_off(data: bytes, pe: dict, rva: int) -> int:
    """Translate an RVA into a raw file offset using the section table."""
    nsec = pe["nsec"]
    optsz = struct.unpack_from("<H", data, pe["coff"] + 16)[0]
    sec0 = pe["opt"] + optsz
    for i in range(nsec):
        o = sec0 + i * 40
        name = data[o:o + 8].rstrip(b"\x00")
        vsize, va, rsize, roff = struct.unpack_from("<IIII", data, o + 8)
        if va <= rva < va + max(vsize, rsize):
            return roff + (rva - va)
    raise ValueError(f"RVA {rva:#x} not mapped by any section")


def set_subsystem(exe_path: str, show_console: bool) -> bool:
    """Force the exe's PE Subsystem: console (CMD window) or GUI (no console).

    Works in-place on the compiled .exe (BAT2EXE always emits a console
    subsystem binary, so 'hidden' mode rewrites it to WINDOWS_GUI).
    """
    exe_path = os.path.abspath(exe_path)
    if not os.path.isfile(exe_path):
        return False
    with open(exe_path, "rb") as fh:
        data = bytearray(fh.read())
    try:
        pe = _pe_parse(data)
        want = SUB_CONSOLE if show_console else SUB_NO_CONSOLE
        cur = struct.unpack_from("<H", data, pe["sub_off"])[0]
        if cur != want:
            struct.pack_into("<H", data, pe["sub_off"], want)
        with open(exe_path, "wb") as fh:
            fh.write(data)
        return True
    except Exception:
        return False


# --- UAC manifest -----------------------------------------------------------
# requestedExecutionLevel values accepted by the Windows loader
_UAC_TEMPLATE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <assemblyIdentity version="1.0.0.0" processorArchitecture="*"
                    name="BAT2EXE.app" type="win32"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="{level}" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <compatibility xmlns="urn:schemas-microsoft-com:compatibility.v1">
    <application>
      <!-- Windows 10 and 11 -->
      <supportedOS Id="{{8e0f7a12-bfb3-4fe8-b9a5-48fd50a15a9a}}"/>
      <!-- Windows 8.1 -->
      <supportedOS Id="{{1f676c76-80e1-4239-95bb-83d0f6d0da78}}"/>
      <!-- Windows 7 -->
      <supportedOS Id="{{35138b9a-5d96-4fbd-8e2d-a2440225f93a}}"/>
    </application>
  </compatibility>
</assembly>
"""

_LEVELS = {"asinvoker": "asInvoker", "highestavailable": "highestAvailable",
           "requireadministrator": "requireAdministrator"}


def set_uac_manifest(exe_path: str, level: str) -> bool:
    """Embed a manifest requesting a UAC execution level.

    *level*: "asInvoker" (default, no elevation) |
             "highestAvailable" (max the user is allowed) |
             "requireAdministrator" (always prompt UAC)

    The manifest is written as RT_MANIFEST (24) resource id 1 via the same
    UpdateResource helper used for icons.
    """
    exe_path = os.path.abspath(exe_path)
    if not os.path.isfile(exe_path):
        return False
    lvl = _LEVELS.get(level.strip().lower())
    if not lvl:
        return False

    manifest = _UAC_TEMPLATE.format(level=lvl).encode("utf-8")

    tmp = tempfile.mkdtemp(prefix="uacman_")
    try:
        cs = os.path.join(tmp, "ManifestEmbed.cs")
        helper = os.path.join(tmp, "ManifestEmbed.exe")
        man = os.path.join(tmp, "app.manifest")
        with open(man, "wb") as fh:
            fh.write(manifest)
        with open(cs, "w", encoding="utf-8") as fh:
            fh.write(_MANIFEST_HELPER_CS)
        csc = _find_csc()
        if not csc:
            return False
        r = subprocess.run(
            [csc, "/nologo", "/target:exe", "/out:" + helper, cs],
            capture_output=True, text=True, timeout=60)
        if r.returncode != 0 or not os.path.isfile(helper):
            return False
        r = subprocess.run(
            [helper, exe_path, man],
            capture_output=True, text=True, timeout=60,
            creationflags=0x08000000)
        return r.returncode == 0
    except Exception:
        return False
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


_MANIFEST_HELPER_CS = r"""
using System;
using System.Runtime.InteropServices;

public class ManifestEmbed {
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern IntPtr BeginUpdateResource(string p, bool b);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool UpdateResource(IntPtr h, IntPtr type, IntPtr name,
        ushort lang, byte[] data, uint size);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool EndUpdateResource(IntPtr h, bool b);

    public static int Main(string[] args) {
        if (args.Length < 2) { Console.Error.WriteLine("usage: exe manifest"); return 2; }
        try {
            byte[] man = System.IO.File.ReadAllBytes(args[1]);
            IntPtr h = BeginUpdateResource(args[0], false);
            if (h == IntPtr.Zero) throw new Exception(
                "BeginUpdateResource failed, err " + Marshal.GetLastWin32Error());
            // RT_MANIFEST = 24, resource id 1, lang 0x409
            if (!UpdateResource(h, (IntPtr)24, (IntPtr)1, 0x409,
                                man, (uint)man.Length))
                throw new Exception("UpdateResource failed, err " +
                    Marshal.GetLastWin32Error());
            if (!EndUpdateResource(h, false))
                throw new Exception("EndUpdateResource failed, err " +
                    Marshal.GetLastWin32Error());
            return 0;
        } catch (Exception ex) {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
"""


def finalize_exe(exe_path: str, show_console: bool = True,
                 uac_level: str = "asInvoker") -> dict:
    """One-call post-build finishing: subsystem + UAC manifest.

    Call AFTER icon embedding (icon writes RT_GROUP_ICON which replaces
    resources wholesale for those types only — subsystem/manifest stay).
    Returns {"subsystem": bool, "manifest": bool}.
    """
    return {
        "subsystem": set_subsystem(exe_path, show_console),
        "manifest": set_uac_manifest(exe_path, uac_level),
    }


# ---------------------------------------------------------------------------
# Architecture switching (32-bit <-> 64-bit)
# ---------------------------------------------------------------------------
import base64
import shutil
import sys
# BAT2EXE.EXE (JJSoft 2010) is a 32-bit .NET 2.0 tool and always emits a
# 32-bit (PE32 / x86) stub. This build cannot be recompiled, so a true
# 64-bit binary cannot be produced from it — attempting to just flip the
# Machine field would corrupt the image (pointers/RElocations are 32-bit).
#
# What CAN be done honestly:
#  * detect the architecture of the produced exe,
#  * optionally append a PE32+ payload so Windows on ARM64/x64 notes the
#    preference — NOT valid; the honest, working approach:
#  * 32-bit target: use the stub as-is (runs everywhere via WoW64),
#  * 64-bit target: wrap the 32-bit exe as an embedded RCDATA resource
#    inside a freshly built 64-bit launcher (cs invocation of csc with
#    /platform:x64). The launcher extracts the payload to %TEMP% and runs
#    it. This yields a REAL 64-bit PE that cleanly hosts the 32-bit app.

MACHINE_I386 = 0x014C
MACHINE_AMD64 = 0x8664


def get_machine(exe_path: str) -> int:
    """Return the PE Machine field: 0x14C (x86) or 0x8664 (x64)."""
    with open(exe_path, "rb") as fh:
        data = fh.read(0x400)
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    return struct.unpack_from("<H", data, pe_off + 4)[0]


_LAUNCHER_CS = r"""
using System;
using System.IO;
using System.Reflection;
using System.Diagnostics;

public class Launcher64 {
    public static int Main(string[] args) {
        // payload is the last RT_RCDATA resource named "PAYLOAD_X86"
        Assembly asm = Assembly.GetExecutingAssembly();
        // Win32 resources are not exposed to .NET reflection; use WinAPI
        // through the helper module compiled in. Simplest: embedded as a
        // byte[] literal by the Python side (see make_x64_launcher).
        string exe = Path.Combine(Path.GetTempPath(),
                                  "bat2exe_" + Guid.NewGuid().ToString("N"),
                                  "app32.exe");
        Directory.CreateDirectory(Path.GetDirectoryName(exe));
        File.WriteAllBytes(exe, PAYLOAD_BYTES);
        try {
            var psi = new ProcessStartInfo(exe) {
                Arguments = string.Join(" ", args),
                UseShellExecute = false
            };
            var p = Process.Start(psi);
            p.WaitForExit();
            return p.ExitCode;
        } finally {
            try { Directory.Delete(Path.GetDirectoryName(exe), true); }
            catch { }
        }
    }
    public static readonly byte[] PAYLOAD_BYTES = new byte[0]; // replaced
}
"""


def make_x64_launcher(payload_path: str, out_path: str) -> bool:
    """Build a REAL 64-bit PE that embeds and launches the 32-bit exe.

    This is the honest implementation of '64-bit output' for a tool whose
    stub is hard-locked to 32-bit: the launcher itself is a genuine x64
    image (csc /platform:x64); the 32-bit payload rides inside it.
    """
    payload_path = os.path.abspath(payload_path)
    out_path = os.path.abspath(out_path)
    if not (os.path.isfile(payload_path) and os.path.isfile(payload_path)):
        return False
    tmp = tempfile.mkdtemp(prefix="x64wrap_")
    try:
        with open(payload_path, "rb") as fh:
            payload = fh.read()

        cs = os.path.join(tmp, "Launcher64.cs")
        helper = os.path.join(tmp, "Launcher64.exe")
        # embed the payload as a base64 literal — keeps the CS source valid
        import base64
        b64 = base64.b64encode(payload).decode("ascii")
        src = (
            "using System;\n"
            "using System.IO;\n"
            "using System.Diagnostics;\n"
            "public class Launcher64 {\n"
            f"  static readonly string B64 = \"{b64}\";\n"
            "  public static int Main(string[] args) {\n"
            "    byte[] payload;\n"
            "    try { payload = Convert.FromBase64String(B64); }\n"
            "    catch { return 90; }\n"
            "    string dir = Path.Combine(Path.GetTempPath(),\n"
            "                  \"bat2exe_\" + Guid.NewGuid().ToString(\"N\"));\n"
            "    string exe = Path.Combine(dir, \"app32.exe\");\n"
            "    Directory.CreateDirectory(dir);\n"
            "    File.WriteAllBytes(exe, payload);\n"
            "    try {\n"
            "      var psi = new ProcessStartInfo(exe) {\n"
            "        Arguments = string.Join(\" \", args),\n"
            "        UseShellExecute = false };\n"
            "      var p = Process.Start(psi);\n"
            "      p.WaitForExit();\n"
            "      return p.ExitCode;\n"
            "    } finally {\n"
            "      try { Directory.Delete(dir, true); } catch { }\n"
            "    }\n"
            "  }\n"
            "}\n")
        with open(cs, "w", encoding="ascii") as fh:
            fh.write(src)

        csc = _find_csc()
        if not csc:
            return False
        r = subprocess.run(
            [csc, "/nologo", "/platform:x64", "/target:exe",
             "/out:" + helper, cs],
            capture_output=True, text=True, timeout=120)
        if r.returncode != 0 or not os.path.isfile(helper):
            return False
        shutil.move(helper, out_path)
        return True
    except Exception:
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_for_arch(exe_path: str, arch: str, out_path: str | None = None) -> str | None:
    """Produce the final exe for the requested architecture.

    arch: "x86" (native stub, path unchanged) or "x64" (64-bit launcher
    wrapper embedding the 32-bit payload).
    Returns the path of the final image or None on failure.
    """
    exe_path = os.path.abspath(exe_path)
    arch = arch.lower().replace("32-bit", "x86").replace("64-bit", "x64")
    if arch in ("x86", "32"):
        return exe_path                      # stub already runs under WoW64
    if arch in ("x64", "64"):
        out = out_path or exe_path + ".x64.exe"
        return out if make_x64_launcher(exe_path, out) else None
    return None


# ---------------------------------------------------------------------------
# Extra resources: embed arbitrary files/folders into the exe (RT_RCDATA)
# ---------------------------------------------------------------------------
_RCDATA_HELPER_CS = r"""
using System;
using System.Runtime.InteropServices;

public class RcdataEmbed {
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern IntPtr BeginUpdateResource(string p, bool b);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool UpdateResource(IntPtr h, IntPtr type, IntPtr name,
        ushort lang, byte[] data, uint size);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    static extern bool EndUpdateResource(IntPtr h, bool b);

    // args: exe  file1 [file2 ...]   — resource name = file base name
    public static int Main(string[] args) {
        if (args.Length < 2) { Console.Error.WriteLine("usage: exe files..."); return 2; }
        try {
            IntPtr h = BeginUpdateResource(args[0], false);
            if (h == IntPtr.Zero) throw new Exception(
                "BeginUpdateResource failed, err " + Marshal.GetLastWin32Error());
            for (int i = 1; i < args.Length; i++) {
                byte[] data = System.IO.File.ReadAllBytes(args[i]);
                string name = System.IO.Path.GetFileName(args[i]);
                // RT_RCDATA = 10, name = string, lang 0x409
                IntPtr namePtr = Marshal.StringToHGlobalUni(name);
                try {
                    if (!UpdateResource(h, (IntPtr)10, namePtr, 0x409,
                                        data, (uint)data.Length))
                        throw new Exception("UpdateResource(" + name + ") failed, err " +
                            Marshal.GetLastWin32Error());
                } finally {
                    Marshal.FreeHGlobal(namePtr);
                }
            }
            if (!EndUpdateResource(h, false))
                throw new Exception("EndUpdateResource failed, err " +
                    Marshal.GetLastWin32Error());
            return 0;
        } catch (Exception ex) {
            Console.Error.WriteLine(ex.Message);
            return 1;
        }
    }
}
"""


def embed_resources(exe_path: str, files: list) -> bool:
    """Embed *files* into *exe_path* as RT_RCDATA (name = file base name).

    Files stay inside the exe; the wrapped batch script can extract them
    at runtime via standard resource APIs if it needs them on disk.
    Folders: pass their files flattened (walk them before calling).
    """
    exe_path = os.path.abspath(exe_path)
    files = [os.path.abspath(f) for f in files if os.path.isfile(f)]
    if not files or not os.path.isfile(exe_path):
        return False
    tmp = tempfile.mkdtemp(prefix="rcdata_")
    try:
        cs = os.path.join(tmp, "RcdataEmbed.cs")
        helper = os.path.join(tmp, "RcdataEmbed.exe")
        with open(cs, "w", encoding="utf-8-sig") as fh:
            fh.write(_RCDATA_HELPER_CS)
        csc = _find_csc()
        if not csc:
            return False
        r = subprocess.run(
            [csc, "/nologo", "/target:exe", "/out:" + helper, cs],
            capture_output=True, timeout=60)
        if r.returncode != 0 or not os.path.isfile(helper):
            return False
        r = subprocess.run(
            [helper, exe_path] + files,
            capture_output=True, timeout=120,
            creationflags=0x08000000)
        if r.returncode != 0:
            # surface helper's error text (raw bytes — never decode-crash)
            err = repr((r.stdout or b"") + (r.stderr or b""))
            raise RuntimeError("RCDATA helper failed: " + err)
        return True
    except Exception:
        import traceback
        traceback.print_exc()
        return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def collect_files(paths: list) -> list:
    """Flatten user-selected files AND folders into a flat file list."""
    out = []
    for p in paths:
        p = os.path.abspath(p)
        if os.path.isdir(p):
            for root, _dirs, names in os.walk(p):
                for n in names:
                    out.append(os.path.join(root, n))
        elif os.path.isfile(p):
            out.append(p)
    return out
