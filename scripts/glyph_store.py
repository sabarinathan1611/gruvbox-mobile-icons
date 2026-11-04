"""Glyph files (glyphs/<name>.json): loading, validation and SVG rendering.

One JSON file per icon is the single source of truth. Icon Studio (editor/) writes the same
format, and CI validates every file with validate() before anything is built.

  {
    "name": "vlc",                        # drawable name, must match the file name
    "label": "VLC",                       # shown in the icon picker and search
    "packages": ["org.videolan.vlc"],     # every launcher icon of these packages
    "components": ["pkg/pkg.Activity"],   # optional exact launcher components
    "author": "you",
    "elements": [                         # drawn in order on a 24x24 grid, 2-unit stroke
      {"type": "stroke", "color": "fg", "d": "M3 12 H21"},
      {"type": "fill", "color": "accent", "d": "...", "soft": true},
      {"type": "ring", "color": "fg", "d": "..."},   # tile-filled, outlined
      {"type": "knock", "d": "...", "width": 5}       # tile-coloured cut-out
    ]
  }
"""
import json
import re
from pathlib import Path

from palette import ACCENT, AQUA, BG1, BLUE, FG, GRAY, GREEN, PURPLE, RED, YELLOW

ROOT = Path(__file__).resolve().parent.parent
GLYPH_DIR = ROOT / "glyphs"

DEFAULT_PALETTE = {"tile": BG1, "fg": FG, "accent": ACCENT, "red": RED, "green": GREEN, "yellow": YELLOW,
                   "blue": BLUE, "purple": PURPLE, "aqua": AQUA, "gray": GRAY}
SIZE = 192
TILE_RADIUS = 5.28          # 22% of the 24-unit tile
GLYPH_BOX = 13.0            # glyph grid is scaled into the central 13 units of the tile

MAX_FILE_BYTES = 16 * 1024
MAX_ELEMENTS = 40
MAX_PATH_CHARS = 2000
TYPES = {"stroke", "fill", "ring", "knock"}
COLORS = {"fg", "accent", "red", "green", "yellow", "blue", "purple", "aqua", "gray"}
STROKE_WIDTH = (0.5, 4.0)   # allowed line width for stroke and ring elements; 2 is the default
TOP_KEYS = {"name", "label", "packages", "components", "author", "elements"}
ELEMENT_KEYS = {"type", "color", "d", "soft", "width", "shape"}
RESERVED = {"iconback", "ic_launcher"}
JAVA_KEYWORDS = set("""abstract assert boolean break byte case catch char class const continue
default do double else enum extends final finally float for goto if implements import instanceof
int interface long native new package private protected public return short static strictfp super
switch synchronized this throw throws transient try void volatile while true false null""".split())

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{1,40}$")
PACKAGE_RE = re.compile(r"^[A-Za-z][\w]*(\.[A-Za-z][\w]*)+$")
COMPONENT_RE = re.compile(r"^[A-Za-z][\w]*(\.[A-Za-z][\w]*)+/[A-Za-z_$][\w.$]*$")
PATH_CHARS_RE = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9eE.,\s+-]+$")
TOKEN_RE = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
ARGS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}


# ---------- loading ----------

def load_all() -> dict[str, dict]:
    """All glyph files, keyed by name, in file-name order."""
    return {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(GLYPH_DIR.glob("*.json"))}


# ---------- path parsing (used for bounds checks) ----------

def path_points(d: str) -> list[tuple[float, float]]:
    """Absolute endpoints and control points of an SVG path. Raises ValueError if malformed."""
    tokens = TOKEN_RE.findall(d)
    if not tokens or tokens[0] not in "Mm":
        raise ValueError("path must start with M")
    pts, i, cmd = [], 0, None
    x = y = sx = sy = 0.0
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd, i = t, i + 1
            if cmd in "Zz":
                x, y = sx, sy
                continue
        elif cmd is None or cmd in "Zz":
            raise ValueError(f"number without a command near '{t}'")
        n = ARGS[cmd.upper()]
        if i + n > len(tokens) or any(tok.isalpha() for tok in tokens[i:i + n]):
            raise ValueError(f"'{cmd}' needs {n} numbers")
        a = [float(v) for v in tokens[i:i + n]]
        i += n
        rel = cmd.islower()
        up = cmd.upper()
        if up == "H":
            x = a[0] + (x if rel else 0)
        elif up == "V":
            y = a[0] + (y if rel else 0)
        elif up == "A":
            if a[0] < 0 or a[1] < 0 or a[3] not in (0, 1) or a[4] not in (0, 1):
                raise ValueError("bad arc parameters")
            x, y = a[5] + (x if rel else 0), a[6] + (y if rel else 0)
        else:
            ox, oy = x, y
            for k in range(0, n, 2):
                pts.append((a[k] + (ox if rel else 0), a[k + 1] + (oy if rel else 0)))
            x, y = pts[-1]
        pts.append((x, y))
        if up == "M":
            sx, sy = x, y
            cmd = "l" if rel else "L"   # extra pairs after M are line-tos
    return pts


# ---------- validation ----------

def validate(data, filename: str | None = None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for one glyph file's parsed JSON."""
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ["top level must be a JSON object"], warnings
    for k in data.keys() - TOP_KEYS:
        errors.append(f"unknown key '{k}'")

    name = data.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        errors.append("name must be 2-41 chars: lowercase letters, digits, '_', starting with a letter")
    elif name in JAVA_KEYWORDS or name in RESERVED:
        errors.append(f"name '{name}' is reserved")
    elif filename and Path(filename).stem != name:
        errors.append(f"name '{name}' must match the file name ({Path(filename).name})")

    label = data.get("label")
    if not isinstance(label, str) or not 1 <= len(label) <= 40 or re.search(r"[<>&\x00-\x1f]", label):
        errors.append("label must be 1-40 characters without < > & or control characters")
    author = data.get("author", "")
    if not isinstance(author, str) or len(author) > 60 or re.search(r"[<>\x00-\x1f]", author):
        errors.append("author must be a short plain string")

    for key, rx in (("packages", PACKAGE_RE), ("components", COMPONENT_RE)):
        val = data.get(key, [])
        if not isinstance(val, list) or len(val) > 20:
            errors.append(f"{key} must be a list (max 20)")
            continue
        for v in val:
            if not isinstance(v, str) or not rx.match(v):
                errors.append(f"invalid {key[:-1]}: {v!r}")
    if name != "fallback" and not data.get("packages") and not data.get("components"):
        warnings.append("no packages or components: the icon won't be applied to any app")

    els = data.get("elements")
    if not isinstance(els, list) or not 1 <= len(els) <= MAX_ELEMENTS:
        errors.append(f"elements must be a list of 1-{MAX_ELEMENTS} items")
        return errors, warnings
    has_accent = False
    for n, el in enumerate(els, 1):
        where = f"element {n}"
        if not isinstance(el, dict):
            errors.append(f"{where}: must be an object")
            continue
        for k in el.keys() - ELEMENT_KEYS:
            errors.append(f"{where}: unknown key '{k}'")
        typ = el.get("type")
        if typ not in TYPES:
            errors.append(f"{where}: type must be one of {sorted(TYPES)}")
        if typ in ("stroke", "fill", "ring"):
            if el.get("color") not in COLORS:
                errors.append(f"{where}: color must be one of {', '.join(sorted(COLORS))}")
            has_accent |= el.get("color") not in (None, "fg")
        if "soft" in el and not isinstance(el["soft"], bool):
            errors.append(f"{where}: soft must be true or false")
        w = el.get("width")
        is_num = isinstance(w, (int, float)) and not isinstance(w, bool)
        if typ == "knock" and w is not None and not (is_num and 0 <= w <= 8):
            errors.append(f"{where}: knock width must be a number 0-8")
        elif typ in ("stroke", "ring") and w is not None and not (is_num and STROKE_WIDTH[0] <= w <= STROKE_WIDTH[1]):
            errors.append(f"{where}: line width must be a number {STROKE_WIDTH[0]:g}-{STROKE_WIDTH[1]:g}")
        elif typ == "fill" and w is not None:
            errors.append(f"{where}: fill shapes have no width")
        if "shape" in el and not isinstance(el["shape"], dict):
            errors.append(f"{where}: shape must be an object")
        d = el.get("d")
        if not isinstance(d, str) or not d.strip() or len(d) > MAX_PATH_CHARS:
            errors.append(f"{where}: d must be a path string up to {MAX_PATH_CHARS} characters")
            continue
        if not PATH_CHARS_RE.match(d):
            errors.append(f"{where}: d may only contain SVG path commands and numbers")
            continue
        try:
            pts = path_points(d)
        except ValueError as e:
            errors.append(f"{where}: bad path ({e})")
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        if min(xs) < -0.5 or min(ys) < -0.5 or max(xs) > 24.5 or max(ys) > 24.5:
            errors.append(f"{where}: points must stay inside the 24x24 grid")
        elif min(xs) < 1 or min(ys) < 1 or max(xs) > 23 or max(ys) > 23:
            warnings.append(f"{where}: reaches the grid edge; keep content inside 2..22")
    if not has_accent and name != "fallback":
        warnings.append("no coloured element (the style uses at least one accent colour)")
    return errors, warnings


# ---------- rendering ----------

def _num(v: float) -> str:
    return f"{v:g}"


def element_svg(el: dict, pal: dict) -> str:
    d = el["d"]
    typ = el["type"]
    col = pal.get(el.get("color", "fg"), pal["fg"])
    w = el.get("width")
    width = f' stroke-width="{_num(w)}"' if typ in ("stroke", "ring") and w is not None and w != 2 else ""
    if typ == "stroke":
        return f'<path d="{d}" stroke="{col}"{width}/>'
    if typ == "fill":
        soft = f' stroke="{col}" stroke-width="1.2"' if el.get("soft") else ""
        return f'<path d="{d}" fill="{col}"{soft}/>'
    if typ == "ring":
        return f'<path d="{d}" fill="{pal["tile"]}" stroke="{col}"{width}/>'
    tile = pal["tile"]
    return f'<path d="{d}" fill="{tile}" stroke="{tile}" stroke-width="{_num(el.get("width", 5))}"/>'


def tile_path() -> str:
    r, w = TILE_RADIUS, 24
    return (f"M{r} 0 H{w - r} A{r} {r} 0 0 1 {w} {r} V{w - r} A{r} {r} 0 0 1 {w - r} {w} H{r} "
            f"A{r} {r} 0 0 1 0 {w - r} V{r} A{r} {r} 0 0 1 {r} 0 Z")


def svg_for(glyph: dict | None, pal: dict | None = None, size: int = SIZE) -> str:
    """Full icon SVG: tile plus glyph. glyph=None gives the plain tile (iconback)."""
    pal = pal or DEFAULT_PALETTE
    body = ""
    if glyph:
        off, scale = (24 - GLYPH_BOX) / 2, GLYPH_BOX / 24
        elements = "\n    ".join(element_svg(e, pal) for e in glyph["elements"])
        body = (f'\n  <g transform="translate({off} {off}) scale({scale:.6f})" '
                f'fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                f'\n    {elements}\n  </g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
            f'viewBox="0 0 24 24">\n  <path d="{tile_path()}" fill="{pal["tile"]}"/>{body}\n</svg>\n')
