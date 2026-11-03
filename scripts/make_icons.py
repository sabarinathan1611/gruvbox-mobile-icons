"""Compose each glyph onto the Gruvbox tile, write icons/svg/*.svg and render icons/png/*.png.

Usage:  .venv/Scripts/python.exe scripts/make_icons.py
Outputs: icons/svg/<name>.svg, icons/png/<name>.png (192x192),
         iconback.svg/png (plain tile for unthemed apps), preview/icons_sheet.png
"""
import io
from pathlib import Path

import resvg_py
from PIL import Image, ImageDraw, ImageFont

from apps import APPS, FALLBACK
from glyphs import GLYPHS, TILE, rrect
from palette import BG0_H, FG, GRAY, rgb

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "icons" / "svg"
PNG_DIR = ROOT / "icons" / "png"
PREVIEW = ROOT / "preview"
SIZE = 192

# Tile: full 24-unit square, ~22% corner radius. Glyph: its own 24-unit grid scaled into the
# central 13 units, so the 2-unit stroke lands at ~8.7 px on a 192 px icon.
TILE_PATH = rrect(0, 0, 24, 24, 5.28)
GLYPH_BOX = 13.0
GLYPH_OFFSET = (24 - GLYPH_BOX) / 2


def svg_for(name: str | None) -> str:
    body = ""
    if name:
        scale = GLYPH_BOX / 24
        elements = "\n    ".join(GLYPHS[name])
        body = (f'\n  <g transform="translate({GLYPH_OFFSET} {GLYPH_OFFSET}) scale({scale:.6f})" '
                f'fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                f'\n    {elements}\n  </g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
            f'viewBox="0 0 24 24">\n  <path d="{TILE_PATH}" fill="{TILE}"/>{body}\n</svg>\n')


def render(svg: str) -> Image.Image:
    png = resvg_py.svg_to_bytes(svg_string=svg, width=SIZE, height=SIZE)
    return Image.open(io.BytesIO(bytes(png))).convert("RGBA")


def preview_sheet(names: list[str], cols=8, cell=132, gap_x=36, label_h=40, pad=56):
    rows = -(-len(names) // cols)
    w = pad * 2 + cols * cell + (cols - 1) * gap_x
    h = pad * 2 + rows * (cell + label_h + 24)
    wp = ROOT / "wallpapers" / "gruvbox_clean_a_glow.png"
    bg = (Image.open(wp).convert("RGB").resize((w, int(w * 2392 / 1080))).crop((0, 0, w, h))
          if wp.exists() else Image.new("RGB", (w, h), rgb(BG0_H)))
    d = ImageDraw.Draw(bg)
    font = ImageFont.load_default(size=18)
    for k, name in enumerate(names):
        r, c = divmod(k, cols)
        x = pad + c * (cell + gap_x)
        y = pad + r * (cell + label_h + 24)
        icon = Image.open(PNG_DIR / f"{name}.png").resize((cell, cell), Image.LANCZOS)
        bg.paste(icon, (x, y), icon)
        label = APPS[name][0] if name in APPS else name
        tw = d.textlength(label, font=font)
        if tw > cell + gap_x - 6:
            label = name
            tw = d.textlength(label, font=font)
        d.text((x + (cell - tw) / 2, y + cell + 10), label,
               fill=rgb(FG if name in APPS else GRAY), font=font)
    return bg


def main():
    missing = [n for n in [*APPS, FALLBACK] if n not in GLYPHS]
    if missing:
        raise SystemExit(f"no glyph for: {', '.join(missing)}")
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    PNG_DIR.mkdir(parents=True, exist_ok=True)

    names = [*APPS, FALLBACK]
    for name in names + ["iconback"]:
        svg = svg_for(None if name == "iconback" else name)
        (SVG_DIR / f"{name}.svg").write_text(svg, encoding="utf-8")
        render(svg).save(PNG_DIR / f"{name}.png", optimize=True)
    print(f"wrote {len(names) + 1} icons to {SVG_DIR} and {PNG_DIR}")

    PREVIEW.mkdir(exist_ok=True)
    preview_sheet(names).save(PREVIEW / "icons_sheet.png", optimize=True)
    print("wrote", PREVIEW / "icons_sheet.png")


if __name__ == "__main__":
    main()
