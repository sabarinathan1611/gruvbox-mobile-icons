"""Original glyph artwork for Gruvbox Clean. Every glyph is drawn on a 24-unit grid
(content inside 2..22) with a 2-unit round stroke, using only:

  fg(d)      stroke in FG          acc(d)     stroke in ACCENT
  fill_fg(d) solid FG              fill_acc(d) solid ACCENT
  knock(d)   tile-coloured cut-out (separates overlapping shapes, stays flat)
  ring(d)    tile-filled shape with an FG outline (knobs, nodes)

All geometry is emitted as <path> so the SVGs convert 1:1 to Android VectorDrawables.
"""
import math

from palette import ACCENT, BG1, FG

TILE = BG1


# ---------- element helpers ----------

def fg(d):
    return f'<path d="{d}" stroke="{FG}"/>'


def acc(d):
    return f'<path d="{d}" stroke="{ACCENT}"/>'


def fill_fg(d, soft=True):
    s = f' stroke="{FG}" stroke-width="1.2"' if soft else ""
    return f'<path d="{d}" fill="{FG}"{s}/>'


def fill_acc(d, soft=True):
    s = f' stroke="{ACCENT}" stroke-width="1.2"' if soft else ""
    return f'<path d="{d}" fill="{ACCENT}"{s}/>'


def knock(d, width=5):
    return f'<path d="{d}" fill="{TILE}" stroke="{TILE}" stroke-width="{width}"/>'


def ring(d, color=FG):
    return f'<path d="{d}" fill="{TILE}" stroke="{color}"/>'


# ---------- geometry helpers (all return path data) ----------

def f2(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def pt(cx, cy, r, deg):
    """Point on a circle; screen angles (0 = right, 90 = down)."""
    a = math.radians(deg)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def circle(cx, cy, r):
    return (f"M{f2(cx - r)} {f2(cy)} a{f2(r)} {f2(r)} 0 1 0 {f2(2 * r)} 0 "
            f"a{f2(r)} {f2(r)} 0 1 0 {f2(-2 * r)} 0 Z")


def rrect(x, y, w, h, r):
    return (f"M{f2(x + r)} {f2(y)} H{f2(x + w - r)} A{f2(r)} {f2(r)} 0 0 1 {f2(x + w)} {f2(y + r)} "
            f"V{f2(y + h - r)} A{f2(r)} {f2(r)} 0 0 1 {f2(x + w - r)} {f2(y + h)} H{f2(x + r)} "
            f"A{f2(r)} {f2(r)} 0 0 1 {f2(x)} {f2(y + h - r)} V{f2(y + r)} "
            f"A{f2(r)} {f2(r)} 0 0 1 {f2(x + r)} {f2(y)} Z")


def arc(cx, cy, r, a0, a1):
    """Clockwise arc from angle a0 to a1 (degrees, a1 > a0)."""
    x0, y0 = pt(cx, cy, r, a0)
    x1, y1 = pt(cx, cy, r, a1)
    large = 1 if (a1 - a0) % 360 > 180 else 0
    return f"M{f2(x0)} {f2(y0)} A{f2(r)} {f2(r)} 0 {large} 1 {f2(x1)} {f2(y1)}"


def chevron(tx, ty, dx, dy, size=3.0, spread=42):
    """Arrowhead with its tip at (tx, ty) pointing along (dx, dy)."""
    back = math.degrees(math.atan2(-dy, -dx))
    p1 = pt(tx, ty, size, back - spread)
    p2 = pt(tx, ty, size, back + spread)
    return f"M{f2(p1[0])} {f2(p1[1])} L{f2(tx)} {f2(ty)} L{f2(p2[0])} {f2(p2[1])}"


def star(cx, cy, R, points=5, inner=0.45):
    pts = []
    for i in range(points * 2):
        r = R if i % 2 == 0 else R * inner
        pts.append(pt(cx, cy, r, -90 + i * 180 / points))
    return "M" + " L".join(f"{f2(x)} {f2(y)}" for x, y in pts) + " Z"


def gear(cx, cy, r_out, r_in, teeth=8, top=9, base=16):
    pts = []
    for i in range(teeth):
        t = i * 360 / teeth
        pts += [pt(cx, cy, r_in, t - base), pt(cx, cy, r_out, t - top),
                pt(cx, cy, r_out, t + top), pt(cx, cy, r_in, t + base)]
    return "M" + " L".join(f"{f2(x)} {f2(y)}" for x, y in pts) + " Z"


def bubble_round(cx, cy, r, gap0, gap1, tip_deg, tip_r):
    """Circular speech bubble with a tail between angles gap0..gap1."""
    x0, y0 = pt(cx, cy, r, gap1)
    x1, y1 = pt(cx, cy, r, gap0)
    tx, ty = pt(cx, cy, tip_r, tip_deg)
    return (f"M{f2(x0)} {f2(y0)} A{f2(r)} {f2(r)} 0 1 1 {f2(x1)} {f2(y1)} "
            f"L{f2(tx)} {f2(ty)} Z")


def bubble_rect(x, y, w, h, r, tail_x, tail_w, tail_len):
    """Rounded-rect speech bubble with a tail hanging off the bottom edge at tail_x."""
    b = y + h
    return (f"M{f2(x + r)} {f2(y)} H{f2(x + w - r)} A{f2(r)} {f2(r)} 0 0 1 {f2(x + w)} {f2(y + r)} "
            f"V{f2(b - r)} A{f2(r)} {f2(r)} 0 0 1 {f2(x + w - r)} {f2(b)} H{f2(tail_x + tail_w)} "
            f"L{f2(tail_x)} {f2(b + tail_len)} V{f2(b)} H{f2(x + r)} "
            f"A{f2(r)} {f2(r)} 0 0 1 {f2(x)} {f2(b - r)} V{f2(y + r)} "
            f"A{f2(r)} {f2(r)} 0 0 1 {f2(x + r)} {f2(y)} Z")


def ellipse_half(cx, cy, rx, ry, rot, lower=True):
    """Half of a rotated ellipse, from its +x end to its -x end (lower or upper side)."""
    c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
    x0, y0 = cx + rx * c, cy + rx * s
    x1, y1 = cx - rx * c, cy - rx * s
    sweep = 1 if lower else 0
    return f"M{f2(x0)} {f2(y0)} A{f2(rx)} {f2(ry)} {f2(rot)} 0 {sweep} {f2(x1)} {f2(y1)}"


# ---------- shared shapes ----------

ENVELOPE = rrect(3, 5, 18, 14, 2.5)
FOLDER = ("M3 7 A2 2 0 0 1 5 5 H9.5 L11.5 7.5 H19 A2 2 0 0 1 21 9.5 V17.5 "
          "A2 2 0 0 1 19 19.5 H5 A2 2 0 0 1 3 17.5 Z")
PLANE = "M21 3.5 L3 10.5 L10 13.5 L13.5 20.5 Z"
PLANE_WING = "M10 13.5 L13.5 20.5 L21 3.5 Z"
CALENDAR = [fg(rrect(3, 5, 18, 16, 2.5)), fg("M3 10 H21"), fg("M8 3 V7"), fg("M16 3 V7")]
KEYBOARD = [fg(rrect(2.5, 6, 19, 12, 2.5))]
SHIELD = ("M12 2.8 L19.5 5.8 V11.5 C19.5 16 16.3 19.3 12 21 "
          "C7.7 19.3 4.5 16 4.5 11.5 V5.8 Z")


def key_dots(orange=None):
    out = []
    for i, x in enumerate((7, 12, 17)):
        out.append((fill_acc if orange == i else fill_fg)(circle(x, 9.6, 1.1), soft=False))
    for x in (9.5, 14.5):
        out.append(fill_fg(circle(x, 12.4, 1.1), soft=False))
    return out


# ---------- glyphs ----------

GLYPHS: dict[str, list[str]] = {
    # browsers & search
    "fennec": [  # ringed planet
        acc(ellipse_half(12, 12, 10, 3.2, -25, lower=False)),
        ring(circle(12, 12, 6.2)),
        acc(ellipse_half(12, 12, 10, 3.2, -25, lower=True)),
    ],
    "brave": [  # globe with a pointer
        fg(circle(11, 11, 8)), fg("M11 3 C7 6.5 7 15.5 11 19 C15 15.5 15 6.5 11 3"), fg("M3 11 H19"),
        knock("M13.5 13.5 L21 16 L17.6 17.6 L16 21 Z"),
        fill_acc("M13.5 13.5 L21 16 L17.6 17.6 L16 21 Z"),
    ],
    "duckduckgo": [  # private search lens
        fg(circle(10.5, 10.5, 6.5)), acc("M15.3 15.3 L20.5 20.5"),
        fill_acc(circle(10.5, 10.5, 1.6)),
    ],
    "browser": [  # plain globe
        fg(circle(12, 12, 9)), fg("M12 3 C7.5 7 7.5 17 12 21 C16.5 17 16.5 7 12 3"), acc("M3 12 H21"),
    ],
    # app stores
    "aurora": [  # bag with download arrow
        fg("M5 8 H19 L18 20.5 H6 Z"), fg("M9 8 V6.5 A3 3 0 0 1 15 6.5 V8"),
        acc("M12 11 V17"), acc(chevron(12, 17, 0, 1, 3)),
    ],
    "fdroid": [  # package cube
        fill_acc("M12 3 L20 7.5 L12 12 L4 7.5 Z", soft=False),
        fg("M12 3 L20 7.5 V16.5 L12 21 L4 16.5 V7.5 Z"), fg("M4 7.5 L12 12 L20 7.5"), fg("M12 12 V21"),
    ],
    "obtainium": [  # update loop
        fg(arc(12, 12, 8.5, -50, 230)), fg(chevron(*pt(12, 12, 8.5, -50), -0.77, -0.64, 3)),
        acc("M12 8 V15"), acc(chevron(12, 15, 0, 1, 2.8)),
    ],
    "playstore": [  # storefront
        fg("M3 9 L4.5 4 H19.5 L21 9"),
        acc("M3 9 A3 3 0 0 0 9 9 A3 3 0 0 0 15 9 A3 3 0 0 0 21 9"),
        fg("M4.5 12.5 V20 H19.5 V12.5"), fg("M10 20 V15.5 H14 V20"),
    ],
    # messaging
    "whatsapp": [  # round chat bubble
        fg(bubble_round(12, 11, 8.5, 112, 152, 136, 12.2)),
        fill_acc(circle(8.5, 11, 1.1)), fill_acc(circle(12, 11, 1.1)), fill_acc(circle(15.5, 11, 1.1)),
    ],
    "telegram": [  # paper plane
        fill_acc(PLANE_WING, soft=False), fg(PLANE), fg("M21 3.5 L10 13.5"),
    ],
    "forkgram": [  # paper plane, inverted colours
        fill_fg(PLANE_WING, soft=False), acc(PLANE), acc("M21 3.5 L10 13.5"),
    ],
    "signal": [  # two overlapping bubbles
        acc(rrect(9, 3, 12, 9.5, 3)),
        ring(bubble_rect(3, 8.5, 13, 9.5, 3, 5.5, 4, 3)),
        fg("M6.5 12.5 H12.5"),
    ],
    "messages": [  # sms bubble
        fg(bubble_rect(3, 4, 18, 13, 3.5, 7, 4.5, 4)),
        fg("M7.5 9 H16.5"), acc("M7.5 12.5 H13"),
    ],
    # mail
    "protonmail": [  # sealed envelope
        fg(ENVELOPE), fg("M3.5 6.5 L12 13 L20.5 6.5"),
        knock(rrect(15, 15.5, 6, 5, 1.2) + " M16.3 15.5 V14 A1.7 1.7 0 0 1 19.7 14 V15.5"),
        fill_acc(rrect(15, 15.5, 6, 5, 1.2), soft=False),
        acc("M16.3 15.5 V14 A1.7 1.7 0 0 1 19.7 14 V15.5"),
    ],
    "tuta": [  # at-sign
        acc(circle(12, 12, 3.2)),
        fg("M15.2 8.8 V13.6 A2.4 2.4 0 0 0 20 13.6 V12 A8 8 0 1 0 16.6 18.6"),
    ],
    "thunderbird": [  # inbox tray
        fg("M8 7 H5.8 L3 13.5 V18 A2 2 0 0 0 5 20 H19 A2 2 0 0 0 21 18 V13.5 L18.2 7 H16"),
        fg("M3 13.5 H8 L9.5 16 H14.5 L16 13.5 H21"),
        acc("M12 3 V11.5"), acc(chevron(12, 11.5, 0, 1, 3)),
    ],
    "gmail": [  # envelope
        fg(ENVELOPE), acc("M3.5 6.5 L12 13 L20.5 6.5"),
    ],
    # social & video
    "reddit": [  # bubble with upvote
        fg(bubble_rect(3, 4, 18, 13, 3.5, 7, 4.5, 4)),
        acc("M12 14 V8"), acc(chevron(12, 8, 0, -1, 3)),
    ],
    "tiktok": [  # vertical video
        fg(rrect(6.5, 2.5, 11, 19, 2.5)), fg("M11 5.2 H13"),
        fill_acc("M10.5 9 L15 12 L10.5 15 Z"),
    ],
    "newpipe": [  # stream with progress bar
        fg(rrect(3, 3.5, 18, 13, 2.5)), fill_fg("M10.5 7.25 L14.5 10 L10.5 12.75 Z"),
        acc("M3 20.5 H11"), fill_acc(circle(12.5, 20.5, 1.8)), fg("M16 20.5 H21"),
    ],
    "vlc": [  # play button
        fg(circle(12, 12, 9)), fill_acc("M10 8 L16 12 L10 16 Z"),
    ],
    "netflix": [  # tv set
        fg(rrect(3, 7.5, 18, 13, 2.5)), fg("M8 3 L12 7.5 L16 3"),
        fill_acc("M10.5 11 L14.5 14 L10.5 17 Z"),
    ],
    "hotstar": [  # clapperboard
        fg(rrect(3, 10, 18, 10.5, 2)), fg("M8 14.5 H16"),
        acc("M3 10 L20.39 5.34 L19.61 2.44 L2.22 7.1 Z"),
    ],
    "jellyfin": [  # media server
        fg(rrect(4, 3.5, 16, 7.5, 2)), fg(rrect(4, 13, 16, 7.5, 2)),
        fill_acc(circle(8, 7.25, 1.2)), fill_acc(circle(8, 16.75, 1.2)),
        fg("M12 7.25 H16"), fg("M12 16.75 H16"),
    ],
    "letterboxd": [  # film frame with rating star
        fg(rrect(3, 3.5, 18, 17, 2.5)), fg("M7 3.5 V20.5"), fg("M17 3.5 V20.5"),
        fill_acc(star(12, 12.3, 3.4)),
    ],
    "mihon": [  # open book
        fg("M12 7 C10 5.5 7 5 3 5.5 V18.5 C7 18 10 18.5 12 20"),
        acc("M12 7 C14 5.5 17 5 21 5.5 V18.5 C17 18 14 18.5 12 20"),
        fg("M12 7 V20"),
    ],
    # music
    "spotify": [  # headphones
        fg("M4 15 V12.5 A8 8 0 0 1 20 12.5 V15"),
        fill_acc(rrect(3, 14, 4.5, 7, 1.6)), fill_acc(rrect(16.5, 14, 4.5, 7, 1.6)),
    ],
    "simpmusic": [  # music note
        fill_acc(circle(9, 17.5, 2.6)), fg("M12 17.5 V4"), fg("M12 4 C14.5 4.5 18 6 18 9.5"),
    ],
    "spotube": [  # equaliser
        fg("M5 19 V11"), fg("M9.67 19 V5"), acc("M14.33 19 V13"), fg("M19 19 V8"),
    ],
    # games, dev, fitness
    "steam": [  # gamepad
        fg("M7.5 6.5 H16.5 A5 5 0 0 1 21.4 12.5 L20.4 17 A2.6 2.6 0 0 1 15.9 18.2 L14 15.5 "
           "H10 L8.1 18.2 A2.6 2.6 0 0 1 3.6 17 L2.6 12.5 A5 5 0 0 1 7.5 6.5 Z"),
        fg("M7.5 9.5 V13.5"), fg("M5.5 11.5 H9.5"),
        fill_acc(circle(17.2, 9.9, 1.1)), fill_acc(circle(15.2, 12.6, 1.1)),
    ],
    "github": [  # branch graph
        fg("M6 7 V17"), fg("M18 9 C18 14 6 12.5 6 17"),
        ring(circle(6, 5, 2)), ring(circle(6, 19, 2)), ring(circle(18, 7, 2), ACCENT),
    ],
    "strava": [  # route
        fg("M4.5 18.5 C9 18.5 7 11.5 12 11.5 S15.5 5.5 19.5 5.5"),
        fill_acc(circle(4.5, 18.5, 2)), ring(circle(19.5, 5.5, 2)),
    ],
    # money
    "paytm": [  # wallet
        fg("M5.5 6.5 L15.5 3 L17 6.5"), fg(rrect(3, 6.5, 18, 14, 2.5)),
        ring(rrect(14, 11, 7, 5, 1.5), ACCENT), fill_fg(circle(17, 13.5, 0.7)),
    ],
    "gpay": [  # rupee coin
        fg(circle(12, 12, 9)),
        acc("M8.5 7.5 H15.5"), acc("M8.5 10.5 H15.5"),
        acc("M11 7.5 C15 7.5 15 13.5 11 13.5 H8.5 L14 17.5"),
    ],
    "canarabank": [  # bank
        acc("M3 9 L12 3.5 L21 9 Z"),
        fg("M6 12 V17"), fg("M10 12 V17"), fg("M14 12 V17"), fg("M18 12 V17"), fg("M3 20.5 H21"),
    ],
    # shopping, food, services
    "amazon": [  # cart
        fg("M2.5 4 H5 L7.5 15.5 H18 L20.5 7.5 H6"),
        fill_acc(circle(9, 19.5, 1.5)), fill_acc(circle(16.5, 19.5, 1.5)),
    ],
    "swiggy": [  # bowl with steam
        fg("M3 11.5 H21 C21 16.5 17 20.5 12 20.5 C7 20.5 3 16.5 3 11.5 Z"),
        acc("M8.5 3.5 C7.5 5 9.5 6.5 8.5 8.5"), fg("M12 3 C11 4.5 13 6 12 8"),
        acc("M15.5 3.5 C14.5 5 16.5 6.5 15.5 8.5"),
    ],
    "zepto": [  # fast bolt
        fg("M14.5 2.5 L7.5 13 H12.5 L11 21.5 L19 10.5 H13.5 Z"),
        acc("M2.5 9 H6"), acc("M3.5 14.5 H6"),
    ],
    "district": [  # event ticket
        fg(rrect(3, 6, 18, 12, 2.5)),
        knock(circle(3, 12, 2.2), width=0), knock(circle(21, 12, 2.2), width=0),
        fg("M3 9.8 A2.2 2.2 0 0 1 3 14.2"), fg("M21 14.2 A2.2 2.2 0 0 1 21 9.8"),
        fill_acc(circle(15.5, 9, 1), soft=False), fill_acc(circle(15.5, 12, 1), soft=False),
        fill_acc(circle(15.5, 15, 1), soft=False),
        fill_fg(star(9.8, 12.2, 3.2), soft=False),
    ],
    "myjio": [  # sim card
        fg("M6.5 3 H14.5 L19 7.5 V19.5 A1.5 1.5 0 0 1 17.5 21 H6.5 A1.5 1.5 0 0 1 5 19.5 "
           "V4.5 A1.5 1.5 0 0 1 6.5 3 Z"),
        acc(rrect(8.5, 11, 7, 6.5, 1.2)), acc("M12 11 V17.5"),
    ],
    "whereismytrain": [  # train front
        fg(rrect(5, 3, 14, 14, 3)), fg(rrect(7.5, 6, 9, 4, 1)),
        fill_acc(circle(8.8, 13.5, 1.2)), fill_acc(circle(15.2, 13.5, 1.2)),
        fg("M8.5 17 L6.5 21"), fg("M15.5 17 L17.5 21"),
    ],
    # privacy & network
    "protonvpn": [  # shield with check
        fg(SHIELD), acc("M8.5 12 L11 14.5 L15.5 9.5"),
    ],
    "nextdns": [  # network hub
        fg("M12 12.5 L5.5 5.5"), fg("M12 12.5 L18.5 5.5"), fg("M12 12.5 V20"),
        ring(circle(5.5, 5.5, 2)), ring(circle(18.5, 5.5, 2)), ring(circle(12, 20, 2)),
        fill_acc(circle(12, 12.5, 2.4)),
    ],
    "privatedns": [  # toggle
        fg(rrect(2.5, 7, 19, 10, 5)), fill_acc(circle(16.5, 12, 2.6)),
    ],
    "ntfy": [  # bell with badge
        fg("M6 16.5 V11 A6 6 0 0 1 18 11 V16.5 L19.5 18 H4.5 Z"), fg("M10 21 H14"),
        knock(circle(18, 5.5, 2.4), width=3), fill_acc(circle(18, 5.5, 2.2)),
    ],
    "aegis": [  # key
        acc(circle(8, 16, 4.2)), fg("M11 13 L20 4"), fg("M17.5 6.5 L20 9"), fg("M15 9 L17 11"),
    ],
    "msauth": [  # padlock
        fg("M7.5 11 V8 A4.5 4.5 0 0 1 16.5 8 V11"), fg(rrect(4.5, 11, 15, 10, 2.5)),
        fill_acc(circle(12, 15.2, 1.4)), acc("M12 15.5 V18"),
    ],
    "gauth": [  # code timer
        fg(circle(12, 13, 8)), fg("M10 2.5 H14"), fg("M12 2.5 V5"),
        fill_acc("M12 13 V8.5 A4.5 4.5 0 0 1 16.5 13 Z", soft=False),
    ],
    # torrents
    "qbitcontroller": [  # speed gauge
        fg(arc(12, 14, 8.5, 150, 390)), acc("M12 14 L16.5 9"), fill_fg(circle(12, 14, 1.6)),
    ],
    "libretorrent": [  # magnet
        fill_acc("M4 3.5 H8.5 V6 H4 Z"), fill_acc("M15.5 3.5 H20 V6 H15.5 Z"),
        fg("M4 8.6 V12 A8 8 0 0 0 20 12 V8.6 H15.5 V12 A3.5 3.5 0 0 1 8.5 12 V8.6 Z"),
    ],
    # files & photos
    "gallery": [  # landscape photo
        fg(rrect(3, 4.5, 18, 15, 2.5)), fg("M3.5 17 L9 11.5 L13 15.5 L15.5 13 L20.5 18"),
        fill_acc(circle(16, 9, 1.8)),
    ],
    "calendar": CALENDAR + [fill_acc(rrect(13, 13.5, 4.5, 4, 1))],
    "gcalendar": CALENDAR + [acc("M8.5 15 L11 17.5 L15.5 13")],
    "filemanager": [fg(FOLDER), acc("M7.5 12.5 H16.5"), fg("M7.5 15.5 H13")],
    "files": [fg(FOLDER), acc("M3 10.5 H21")],
    "voyager": [fg(FOLDER), acc("M9 16.5 L15 11.5"), acc("M11 11.5 H15 V15.5")],
    "ente": [  # cloud backup
        fg("M7 18.5 A4.5 4.5 0 0 1 6.3 9.6 A6 6 0 0 1 17.7 8.6 A5 5 0 0 1 17 18.5 Z"),
        acc("M12 16.5 V11"), acc(chevron(12, 11, 0, -1, 2.6)),
    ],
    "snapseed": [  # adjustment sliders
        fg("M4 7 H20"), fg("M4 12 H20"), fg("M4 17 H20"),
        ring(circle(9, 7, 2)), fill_acc(circle(15, 12, 2.2)), ring(circle(7.5, 17, 2)),
    ],
    # input & tools
    "leantype": KEYBOARD + key_dots() + [acc("M8.5 15 H15.5")],
    "simplekeyboard": KEYBOARD + key_dots(orange=2) + [fg("M8.5 15 H15.5")],
    "codescanner": [  # scan frame
        fg("M3 8 V5.5 A2.5 2.5 0 0 1 5.5 3 H8"), fg("M16 3 H18.5 A2.5 2.5 0 0 1 21 5.5 V8"),
        fg("M21 16 V18.5 A2.5 2.5 0 0 1 18.5 21 H16"), fg("M8 21 H5.5 A2.5 2.5 0 0 1 3 18.5 V16"),
        acc("M6.5 12 H17.5"),
    ],
    # system
    "phone": [  # handset with signal
        fg("M6.5 3.5 H9.2 L10.8 7.8 L8.8 9.4 C9.8 11.6 12.4 14.2 14.6 15.2 L16.2 13.2 L20.5 14.8 "
           "V17.5 A3 3 0 0 1 17.5 20.5 C10 20 4 14 3.5 6.5 A3 3 0 0 1 6.5 3.5 Z"),
        acc("M14.5 3.5 A6 6 0 0 1 20.5 9.5"), acc("M14.5 7 A2.5 2.5 0 0 1 17 9.5"),
    ],
    "contacts": [  # person
        acc(circle(12, 8.5, 3.8)), fg("M4.5 20.5 A7.5 7.5 0 0 1 19.5 20.5"),
    ],
    "camera": [
        fg("M3 9 A2 2 0 0 1 5 7 H7.5 L9.2 4.5 H14.8 L16.5 7 H19 A2 2 0 0 1 21 9 V18 "
           "A2 2 0 0 1 19 20 H5 A2 2 0 0 1 3 18 Z"),
        acc(circle(12, 13, 3.6)),
    ],
    "settings": [fg(gear(12, 12, 9.2, 6.8)), acc(circle(12, 12, 2.8))],
    "clock": [fg(circle(12, 12, 9)), fg("M12 7 V12"), acc("M12 12 L15.5 14")],
    "calculator": [
        fg(rrect(4.5, 2.5, 15, 19, 2.5)), fg("M8 6.5 H16"),
        *[fill_fg(circle(x, y, 1.05), soft=False) for x, y in
          ((8.5, 11.5), (12, 11.5), (15.5, 11.5), (8.5, 14.75), (12, 14.75), (8.5, 18), (12, 18))],
        acc("M15.5 14.75 V18"),
    ],
    "maps": [
        fg("M12 21 C12 21 5 14.5 5 9.5 A7 7 0 0 1 19 9.5 C19 14.5 12 21 12 21 Z"),
        fill_acc(circle(12, 9.5, 2.3)),
    ],
    # vivo / iQOO system apps and extras
    "weather": [  # sun behind cloud
        *[acc(f"M{f2(pt(8.5, 8.5, 5.4, a)[0])} {f2(pt(8.5, 8.5, 5.4, a)[1])} "
              f"L{f2(pt(8.5, 8.5, 6.6, a)[0])} {f2(pt(8.5, 8.5, 6.6, a)[1])}")
          for a in (135, 180, 225, 270, 315, 0)],
        acc(circle(8.5, 8.5, 3.2)),
        ring("M10 20 A3 3 0 0 1 10 14 A4.5 4.5 0 0 1 18.5 13.5 A3.25 3.25 0 0 1 18 20 Z"),
    ],
    "bountyrush": [  # treasure chest
        fg("M3 10.5 V8.5 A4 4 0 0 1 7 4.5 H17 A4 4 0 0 1 21 8.5 V10.5"),
        fg(rrect(3, 10.5, 18, 9.5, 2)),
        knock(rrect(10.2, 8.5, 3.6, 4.5, 0.8), width=3), fill_acc(rrect(10.2, 8.5, 3.6, 4.5, 0.8)),
    ],
    "themes": [  # paint palette
        fg("M12 3 A9 9 0 1 0 12 21 C13.5 21 14 20 14 19 C14 17.5 13 17 13 15.8 "
           "C13 14.6 14 14 15.5 14 H18 A3 3 0 0 0 21 11 C21 6.5 17 3 12 3 Z"),
        fill_acc(circle(7.5, 11.5, 1.3)), fill_fg(circle(9.5, 7.3, 1.2)), fill_fg(circle(14.5, 7.3, 1.2)),
    ],
    "vappstore": [  # app grid with download slot
        fg(rrect(4, 4, 7, 7, 2)), fg(rrect(13, 4, 7, 7, 2)), fg(rrect(4, 13, 7, 7, 2)),
        acc("M16.5 13 V20"), acc(chevron(16.5, 20, 0, 1, 2.8)),
    ],
    "recorder": [  # microphone
        acc(rrect(9, 3, 6, 11, 3)), fg("M5.5 11 A6.5 6.5 0 0 0 18.5 11"), fg("M12 17.5 V21"),
    ],
    "simpleview": [  # big tiles
        fg(rrect(3, 3, 18, 8, 2.5)), acc(rrect(3, 13, 8, 8, 2.5)), fg(rrect(13, 13, 8, 8, 2.5)),
    ],
    "notes": [  # spiral notepad
        fg(rrect(4.5, 5, 15, 16, 2.5)), fg("M8.5 3 V7"), fg("M12 3 V7"), fg("M15.5 3 V7"),
        fg("M8 11 H16"), fg("M8 14.5 H16"), acc("M8 18 H12.5"),
    ],
    "iqoocloud": [  # cloud with check
        fg("M7 18.5 A4.5 4.5 0 0 1 6.3 9.6 A6 6 0 0 1 17.7 8.6 A5 5 0 0 1 17 18.5 Z"),
        acc("M9 13.8 L11.2 16 L15 12.2"),
    ],
    "compass": [  # needle
        fg(circle(12, 12, 9)),
        fill_acc("M12 5.5 L14.3 12 H9.7 Z"), fill_fg("M9.7 12 L12 18.5 L14.3 12 Z"),
    ],
    "easyshare": [  # two-way transfer
        fg("M4 8.5 H18.5"), fg(chevron(18.5, 8.5, 1, 0, 3.2)),
        acc("M20 15.5 H5.5"), acc(chevron(5.5, 15.5, -1, 0, 3.2)),
    ],
    "gamecenter": [  # joystick
        fg(rrect(4, 15, 16, 6, 2)), fg("M12 15 V9.5"), fill_acc(circle(12, 6.5, 3)),
        fill_fg(circle(16.5, 18, 1), soft=False),
    ],
    "imanager": [  # health score ring
        fg(circle(12, 12, 8.5)), acc(arc(12, 12, 8.5, -90, 180)),
        fg("M8.5 12.2 L11 14.7 L15.5 9.8"),
    ],
    "gold": [  # stacked gold bars with sparkle
        fg("M2.5 20.5 L4 15.5 H10.5 L12 20.5 Z"), fg("M12 20.5 L13.5 15.5 H20 L21.5 20.5 Z"),
        acc("M7.25 13 L8.75 8 H15.25 L16.75 13 Z"),
        fg("M18.5 2.8 V6.8"), fg("M16.5 4.8 H20.5"),
    ],
    "angelone": [  # rising market chart
        fg("M3 3.5 V20.5 H21"), acc("M6.5 15.5 L10.5 11.5 L13.5 14 L19.5 7.5"),
        acc(chevron(19.5, 7.5, 0.68, -0.73, 3)),
    ],
    "cassettecat": [  # cat listening to music
        acc("M2.2 14 A9.8 9.8 0 0 1 21.8 14"),
        ring("M5 9.5 L5.5 3.5 L10 7 H14 L18.5 3.5 L19 9.5 C20 11 20.2 13 20 14.5 "
             "C19.5 18.5 16 21 12 21 C8 21 4.5 18.5 4 14.5 C3.8 13 4 11 5 9.5 Z"),
        fill_acc(rrect(2.2, 11.5, 4, 6.5, 1.5)), fill_acc(rrect(17.8, 11.5, 4, 6.5, 1.5)),
        fg("M8.3 14 A1.6 1.6 0 0 1 11.1 14"), fg("M12.9 14 A1.6 1.6 0 0 1 15.7 14"),
        fill_fg("M11 17 H13 L12 18 Z"),
    ],
    # fallback for unthemed apps
    "fallback": [
        fg(rrect(4, 4, 7, 7, 2)), fg(rrect(13, 4, 7, 7, 2)), fg(rrect(4, 13, 7, 7, 2)),
        acc(rrect(13, 13, 7, 7, 2)),
    ],
}
