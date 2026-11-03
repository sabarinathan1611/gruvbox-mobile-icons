"""Gruvbox dark palette and theme-wide constants. Single source of truth for all scripts."""

BG0_H = "#1d2021"
BG0 = "#282828"
BG1 = "#3c3836"
BG2 = "#504945"
BG3 = "#665c54"
FG = "#ebdbb2"
FG0 = "#fbf1c7"
GRAY = "#928374"
RED = "#fb4934"
GREEN = "#b8bb26"
YELLOW = "#fabd2f"
BLUE = "#83a598"
PURPLE = "#d3869b"
AQUA = "#8ec07c"
ORANGE = "#fe8019"

ACCENT = ORANGE

# Target device: iQOO I2403, 1080x2392 @ 440 dpi
SCREEN_W, SCREEN_H = 1080, 2392
# Punch-hole camera sits at top centre; keep this box free of any detail
CAMERA_CLEAR = (540 - 120, 0, 540 + 120, 200)


def rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
