# Gruvbox Clean: icon pack and wallpapers for Android

A flat, minimal [Gruvbox](https://github.com/morhetz/gruvbox) dark theme for Android:
**84 original icons**, four wallpapers and a lock-screen wallpaper. It works with Nova Launcher,
Lawnchair and any launcher that supports ADW / Nova icon packs.

I use it daily with **Nova Launcher** on an iQOO (vivo OriginOS, Android 16).

**[Open Icon Studio online](https://sabarinathan1611.github.io/gruvbox-mobile-icons/)** ·
**[Documentation](https://sabarinathan1611.github.io/gruvbox-mobile-icons/docs/)** ·
**[Download the APK](https://github.com/sabarinathan1611/gruvbox-mobile-icons/releases/latest)**

![Icon preview](preview/icons_sheet.png)

![Wallpapers](preview/wallpapers_contact_sheet.png)

## Download

Get the latest APK from **[Releases](https://github.com/sabarinathan1611/gruvbox-mobile-icons/releases/latest)**,
install it, then apply it from your launcher. The wallpapers are attached to each release and
are also in [`wallpapers/`](wallpapers).

## Make or edit icons: Icon Studio

Use it **[online](https://sabarinathan1611.github.io/gruvbox-mobile-icons/)**, or open
[`editor/index.html`](editor/index.html) from a clone in any browser. There's nothing to install, and it works offline.

- **Create icons**: draw lines, polylines, rounded rectangles and circles on the 24-unit grid, with
  snapping, node editing, layers, undo and live launcher-size previews.
- **Edit any icon in the pack**: pick it from the searchable library and change it.
- **Full palette control**: Gruvbox presets, or change the tile, line, accent and wallpaper colours.
- **Download** as SVG or PNG (192 / 512 px) in your colours, or as **Glyph JSON** for the pack.

To add an icon to the pack, put the exported `<name>.json` in [`glyphs/`](glyphs) and push or open a
pull request. CI validates the file, scans it for malware, renders the icons and builds the APK.
A release goes out after approval ([details](docs/how-to-make-icons.md#what-happens-after-you-push)).

[![CI](https://github.com/sabarinathan1611/gruvbox-mobile-icons/actions/workflows/ci.yml/badge.svg)](https://github.com/sabarinathan1611/gruvbox-mobile-icons/actions/workflows/ci.yml)

## Apply in Nova Launcher

1. Open **Nova Settings → Look & feel → Icon style → Icon theme** and choose **Gruvbox Clean**.
2. Change a single icon: long-press the app → **Edit** → tap the icon → **Gruvbox Clean**, then
   use the search box at the top to find an icon.
3. Apps without a custom icon keep their own logo, shrunk onto a matching Gruvbox tile.

**Lawnchair**: Home settings → General → Icon pack → Gruvbox Clean (turn off *Themed icons*).

## Nova Launcher colour setup (hex)

Set these in Nova Settings to match the icons. Menu names move a little between Nova versions;
look for the same item nearby.

| Nova setting | Where | Hex |
|---|---|---|
| Dock background | Dock → Dock background → Color | `#282828` (about 20% transparency) |
| App drawer background | App drawer → Background → Color | `#1d2021` (0–10% transparency) |
| App drawer / home icon labels | App drawer (or Home screen) → Icon layout → Label → Color | `#ebdbb2` |
| Folder background | Folders → Background → Color | `#3c3836` |
| Folder icon background | Folders → Folder icon → Background color | `#3c3836` |
| Search bar | Home screen → Search bar style → Bar color | `#3c3836` |
| Search bar logo / icons | Home screen → Search bar style → Logo / icon color | `#fe8019` |
| Accent / scroll highlight | Look & feel → Accent color (if shown) | `#fe8019` |
| Notification dots | Notification badges → Dots → Color | `#fe8019` |
| Night mode | Look & feel → Night mode | Always on |

Wallpapers: home screen `gruvbox_clean_a_glow` / `b_dots` / `c_terminal`,
lock screen `gruvbox_clean_d_lockscreen` (top 35% left empty for the clock).

## Palette

| Role | Name | Hex |
|---|---|---|
| Background (darkest) | bg0_h | `#1d2021` |
| Background | bg0 | `#282828` |
| Icon tile, surfaces | bg1 | `#3c3836` |
| Borders, inactive | bg2 / bg3 | `#504945` / `#665c54` |
| Text, icon lines | fg | `#ebdbb2` |
| Bright text | fg0 | `#fbf1c7` |
| Muted text | gray | `#928374` |
| **Accent** | orange | `#fe8019` |
| Other Gruvbox colours | red / green / yellow / blue / purple / aqua | `#fb4934` `#b8bb26` `#fabd2f` `#83a598` `#d3869b` `#8ec07c` |

## Icon style

- Rounded-square tile in `#3c3836` with a 22% corner radius.
- A glyph on a 24-unit grid with a 2-unit round stroke, drawn in `#ebdbb2` with one orange `#fe8019` accent.
- Flat shapes only: no gradients or shadows.
- Icons show what an app *does* (a cart, a paper plane, a gamepad); they never copy brand logos.
- Each icon is a small JSON file in [`glyphs/`](glyphs); [`scripts/`](scripts) renders them to [`icons/svg/`](icons/svg) and [`icons/png/`](icons/png).

## Docs

- [How to make an icon](docs/how-to-make-icons.md)
- [How to build the APK](docs/build-apk.md)
- [Contributing](docs/CONTRIBUTING.md): request or add an icon for your app

## Project layout

```
glyphs/         one JSON file per icon: the source of truth
editor/         Icon Studio (HTML, CSS, JS)
scripts/        palette, validator and the generators (Python)
.github/        CI (validate, malware scan, build) and approval-gated releases
icons/svg|png   rendered icons, plus fallback and iconback
wallpapers/     1080x2392 PNG wallpapers
mapping/        components.txt: launcher components mapped to icons
preview/        preview sheets
iconpack/       Android project (package com.sabari.gruvboxclean)
docs/           guides
```

## Licence

Copyright © 2026 sabarinathan1611.

| Part | Licence |
|---|---|
| **Code**: `scripts/`, `iconpack/` (Gradle, Java, XML) | [Apache License 2.0](LICENSE) |
| **Artwork**: icons, wallpapers, previews, and the glyph designs in `glyphs/` | [CC BY-NC-SA 4.0](LICENSE-ARTWORK) |

You're welcome to use, share and remix the icons and wallpapers **for non-commercial use**,
with credit ("Gruvbox Clean by sabarinathan1611") and under the same licence.
Selling the icons or wallpapers, or including them in a paid product, is not allowed without
permission. Contributions are accepted under the terms in [CONTRIBUTING](docs/CONTRIBUTING.md#licence-of-contributions).

## Credits

Colour palette: [Gruvbox](https://github.com/morhetz/gruvbox) by Pavel Pertsev (MIT licence).
All icons and wallpapers are original work made for this project.
