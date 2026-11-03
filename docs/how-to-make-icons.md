# How to make an icon

Every icon is drawn in code (`scripts/glyphs.py`), placed on the shared tile and rendered to SVG
and PNG by a script. Don't edit the PNGs or SVGs by hand: change the code and re-run it.

## 0. One-time setup

Python 3.11+ is required.

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r requirements.txt
# macOS / Linux
.venv/bin/pip install -r requirements.txt
```

The examples below use `python`; replace it with `.venv\Scripts\python.exe` (Windows) or
`.venv/bin/python` (macOS / Linux).

## 1. Find the app's launcher component

An icon pack matches apps by **launcher component** (`package/activity`), not just the package name.

**With the phone connected over adb (recommended).** Enable USB debugging, then run:

```bash
python scripts/build_mapping.py
```

This only reads from the phone. It adds every launcher component it finds to
`mapping/components.txt` (it never removes rows, so mappings from other phones stay).
A `-` in the second column means the app has no custom icon yet.

**Single app by hand:**

```bash
adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.example.app
```

## 2. Draw the glyph

Open `scripts/glyphs.py` and add an entry to the `GLYPHS` dict:

```python
"obsidian": [  # notes vault
    fg(rrect(5, 3, 14, 18, 2.5)),               # page outline
    fg("M8.5 8 H15.5"), fg("M8.5 11.5 H15.5"),  # text lines
    acc("M8.5 15 H12.5"),                       # the one orange accent
],
```

### Drawing rules

- **Grid:** 24 × 24 units. Keep all content inside **2..22**. The tile and padding are added for you.
- **Stroke:** 2 units with round caps and joins (the default). Don't change the width.
- **Colours:** cream `#ebdbb2` for the main shape, plus **one** orange `#fe8019` accent element.
- **Flat:** no gradients, shadows or opacity.
- **Original:** draw what the app *does* (cart, plane, gamepad); never trace or imitate a brand logo.
- **Paths only:** every helper emits `<path>`, so icons convert cleanly to Android vectors.

### Helpers

| Helper | Draws |
|---|---|
| `fg(d)` / `acc(d)` | stroke in cream / orange |
| `fill_fg(d)` / `fill_acc(d)` | solid cream / orange shape (`soft=False` for sharp edges) |
| `ring(d, color)` | shape filled with the tile colour and outlined, for knobs and nodes that sit on lines |
| `knock(d, width)` | tile-coloured cut-out, to separate overlapping shapes |
| `circle(cx, cy, r)` | circle path |
| `rrect(x, y, w, h, r)` | rounded rectangle path |
| `arc(cx, cy, r, a0, a1)` | clockwise arc; angles in degrees, 0 = right, 90 = down |
| `chevron(x, y, dx, dy, size)` | arrowhead with its tip at (x, y) pointing along (dx, dy) |
| `star(cx, cy, R)`, `gear(...)` | star and gear outlines |
| `bubble_rect(...)`, `bubble_round(...)` | speech bubbles with tails |

`d` is ordinary SVG path data (`M L H V C A Z`). Elements are drawn in list order, so
put `knock`/`ring` shapes after anything they should cover.

## 3. Map the icon to the app

Add a line to `APPS` in `scripts/apps.py`:

```python
"obsidian": ("Obsidian", ["md.obsidian"]),
```

- The key is the drawable name: lowercase letters, digits and `_`, and not a Java keyword.
- Listing the package maps **every** launcher component of that package, including alternate-icon aliases.
- When one package has several launcher icons with different jobs, list the exact component
  instead: `"com.android.contacts/com.android.dialer.TwelveKeyDialer"`.

## 4. Render and check

```bash
python scripts/make_icons.py
```

This writes `icons/svg/<name>.svg`, `icons/png/<name>.png` (192 × 192) and refreshes
`preview/icons_sheet.png`, where every icon is shown at real launcher size (132 px) on the wallpaper.
Check yours there. If it looks busy at that size, remove detail.

## 5. Put it in the APK

```bash
python scripts/build_iconpack.py
```

Then build and install as described in [build-apk.md](build-apk.md).

## Checklist

- [ ] Content stays inside 2..22 and uses the 2-unit stroke
- [ ] Exactly one orange accent element
- [ ] Reads clearly at launcher size in `preview/icons_sheet.png`
- [ ] Doesn't look like the app's brand logo
- [ ] Added to `GLYPHS` and `APPS`, and the scripts were re-run
