"""Generate the Gruvbox Clean wallpapers (1080x2392 PNG) and a contact-sheet preview.

Usage:  .venv/Scripts/python.exe scripts/make_wallpapers.py
Outputs: wallpapers/*.png, preview/wallpapers_contact_sheet.png
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from palette import (AQUA, BG0, BG0_H, BG1, BG2, BG3, BLUE, FG, GRAY, GREEN, ORANGE,
                     PURPLE, RED, SCREEN_H, SCREEN_W, YELLOW, rgb)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "wallpapers"
PREVIEW = ROOT / "preview"
W, H = SCREEN_W, SCREEN_H
SS = 3  # supersampling factor for crisp anti-aliased shapes
rng = np.random.default_rng(7)


# ---------- helpers ----------

def vertical(top: str, bottom: str, start=0.0, end=1.0) -> np.ndarray:
    """Float HxWx3 vertical gradient between two colours over [start, end] of the height."""
    t = np.clip((np.linspace(0, 1, H) - start) / max(end - start, 1e-6), 0, 1)
    t = t * t * (3 - 2 * t)  # smoothstep for a softer transition
    a, b = np.array(rgb(top), float), np.array(rgb(bottom), float)
    col = a[None, :] * (1 - t[:, None]) + b[None, :] * t[:, None]
    return np.repeat(col[:, None, :], W, axis=1)


def glow(img: np.ndarray, color: str, cx, cy, rx, ry, strength) -> np.ndarray:
    """Blend a soft elliptical glow (gaussian falloff) into img."""
    y, x = np.mgrid[0:H, 0:W].astype(float)
    d2 = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
    a = (strength * np.exp(-d2 * 2.2))[..., None]
    return img * (1 - a) + np.array(rgb(color), float) * a


def finish(img: np.ndarray) -> Image.Image:
    """Add +/-0.5 LSB triangular dither to kill gradient banding, then quantise."""
    noise = rng.random(img.shape) - rng.random(img.shape)
    return Image.fromarray(np.clip(img + noise * 0.75, 0, 255).astype(np.uint8), "RGB")


def overlay() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    layer = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer)


def compose(base: Image.Image, layer: Image.Image) -> Image.Image:
    small = layer.resize((W, H), Image.LANCZOS)
    out = base.convert("RGBA")
    out.alpha_composite(small)
    return out.convert("RGB")


def rrect(d, box, r, fill, alpha=255):
    x0, y0, x1, y1 = (v * SS for v in box)
    d.rounded_rectangle((x0, y0, x1, y1), radius=r * SS, fill=(*rgb(fill), alpha))


# ---------- wallpapers ----------

def wp_glow() -> Image.Image:
    """(a) Clean dark gradient with a soft orange glow rising from the bottom edge."""
    img = vertical(BG0_H, BG0, 0.0, 0.85)
    img = glow(img, ORANGE, W / 2, H + 260, W * 0.95, H * 0.36, 0.42)
    img = glow(img, ORANGE, W / 2, H + 60, W * 0.45, H * 0.10, 0.25)
    return finish(img)


def wp_dots() -> Image.Image:
    """(b) Subtle dot grid that fades in from the top; one orange dot as the accent."""
    base = finish(vertical(BG0_H, BG0, 0.2, 1.0))
    layer, d = overlay()
    step, r = 60, 3.2
    cols = W // step
    x_off = (W - (cols - 1) * step) / 2
    accent = (cols - 3, int((H - 330) // step))  # one dot, lower right
    for j in range(int(H // step) + 1):
        y = 40 + j * step
        fade = np.clip((y - 260) / 900, 0, 1)  # top stays clean (camera + status bar)
        if fade <= 0:
            continue
        for i in range(cols):
            x = x_off + i * step
            if (i, j) == accent:
                c, a, rr = ORANGE, 255, r * 2.2
            else:
                c, a, rr = BG3, int(150 * fade), r
            d.ellipse(((x - rr) * SS, (y - rr) * SS, (x + rr) * SS, (y + rr) * SS),
                      fill=(*rgb(c), a))
    return compose(base, layer)


def wp_terminal() -> Image.Image:
    """(c) Terminal-style block in the bottom third: prompt glyph, cursor and palette bars."""
    base = finish(vertical(BG0_H, BG0, 0.3, 1.0))
    layer, d = overlay()
    m = 96                       # side margin
    top = int(H * 0.69)          # block starts inside the bottom third
    # prompt: chevron + block cursor, drawn as shapes (no font)
    cx, cy, s = m + 6, top + 22, 22
    d.line([((cx) * SS, (cy - s) * SS), ((cx + s) * SS, cy * SS), (cx * SS, (cy + s) * SS)],
           fill=(*rgb(ORANGE), 255), width=7 * SS, joint="curve")
    rrect(d, (cx + 52, cy + 12, cx + 52 + 40, cy + 22), 2, FG)
    rrect(d, (cx + 112, cy - 22, cx + 112 + 22, cy + 22), 3, FG, 200)
    # thin rule
    rrect(d, (m, top + 92, W - m, top + 95), 1.5, BG2)
    # palette: accents row, then tones row
    accents = [RED, GREEN, YELLOW, BLUE, PURPLE, AQUA, ORANGE, GRAY]
    tones = [BG0_H, BG0, BG1, BG2, BG3, GRAY, FG]
    gap = 14
    def bar_row(colors, y, h):
        bw = (W - 2 * m - gap * (len(colors) - 1)) / len(colors)
        for k, c in enumerate(colors):
            x = m + k * (bw + gap)
            rrect(d, (x, y, x + bw, y + h), 10, c)
            if c in (BG0_H, BG0):  # keep the darkest swatches visible against the background
                d.rounded_rectangle(((x) * SS, y * SS, (x + bw) * SS, (y + h) * SS),
                                    radius=10 * SS, outline=(*rgb(BG2), 255), width=2 * SS)
    bar_row(accents, top + 140, 120)
    bar_row(tones, top + 140 + 120 + gap * 2, 44)
    return compose(base, layer)


def wp_lock() -> Image.Image:
    """(d) Lock screen: top 35% flat and empty for the clock; quiet horizon arcs below."""
    clean = int(H * 0.35)
    img = vertical(BG0_H, BG0, 0.35, 1.0)
    img = glow(img, ORANGE, W / 2, H + 380, W * 0.9, H * 0.30, 0.30)
    img[:clean] = np.array(rgb(BG0_H), float)   # guarantee a perfectly clean top band
    base = finish(img)
    base.paste(Image.new("RGB", (W, clean), rgb(BG0_H)), (0, 0))  # no dither noise up top
    layer, d = overlay()
    cx, cy = W / 2, H + 520
    rings = [(1500, BG1, 255, 3), (1300, BG1, 255, 3), (1100, BG2, 255, 3), (900, ORANGE, 255, 5)]
    for rad, c, a, wdt in rings:
        d.ellipse(((cx - rad) * SS, (cy - rad) * SS, (cx + rad) * SS, (cy + rad) * SS),
                  outline=(*rgb(c), a), width=wdt * SS)
    out = compose(base, layer)
    out.paste(Image.new("RGB", (W, clean), rgb(BG0_H)), (0, 0))  # rings never reach the top band
    return out


# ---------- contact sheet ----------

def contact_sheet(items: list[tuple[str, Image.Image]]) -> Image.Image:
    tw, th, pad, label_h = 300, int(300 * H / W), 40, 56
    sheet = Image.new("RGB", (pad + len(items) * (tw + pad), th + 2 * pad + label_h), rgb(BG1))
    d = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=22)
    for k, (name, im) in enumerate(items):
        x = pad + k * (tw + pad)
        thumb = im.resize((tw, th), Image.LANCZOS)
        sheet.paste(thumb, (x, pad))
        scale = tw / W
        # camera punch-hole marker (preview only)
        r, ccx, ccy = 18 * scale * 2, x + tw / 2, pad + 60 * scale
        d.ellipse((ccx - r, ccy - r, ccx + r, ccy + r), outline=rgb(GRAY), width=1)
        if name.startswith("d"):
            yl = pad + int(th * 0.35)
            for xx in range(x, x + tw, 10):
                d.line((xx, yl, xx + 5, yl), fill=rgb(GRAY), width=1)
        d.text((x, pad + th + 14), name, fill=rgb(FG), font=font)
    return sheet


def main():
    OUT.mkdir(exist_ok=True)
    PREVIEW.mkdir(exist_ok=True)
    walls = [
        ("a_glow", wp_glow()),
        ("b_dots", wp_dots()),
        ("c_terminal", wp_terminal()),
        ("d_lockscreen", wp_lock()),
    ]
    for name, im in walls:
        assert im.size == (W, H), (name, im.size)
        im.save(OUT / f"gruvbox_clean_{name}.png", optimize=True)
        print("wrote", OUT / f"gruvbox_clean_{name}.png")
    contact_sheet(walls).save(PREVIEW / "wallpapers_contact_sheet.png", optimize=True)
    print("wrote", PREVIEW / "wallpapers_contact_sheet.png")


if __name__ == "__main__":
    main()
