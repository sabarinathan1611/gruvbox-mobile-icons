# How to make an icon

Every icon is one small JSON file in [`glyphs/`](../glyphs). You can make it in **Icon Studio**
(no install, runs in your browser) or by hand. CI turns the file into the SVG and PNG icons
and puts it in the APK, so you don't need Python or Android tools to add an icon.

## Option A: Icon Studio (recommended)

1. Open [`editor/index.html`](../editor/index.html) in a browser. Double-clicking the file works;
   no server is needed.
2. Click an icon in the **Library** to edit it, or press **New** to start from scratch.
3. Draw with the tools on the left:

   | Tool | Key | How |
   |---|---|---|
   | Select / move | `V` | click a shape, drag it; drag the round handles to reshape it |
   | Line | `L` | drag |
   | Polyline | `P` | click points; double-click or `Enter` to finish; click the first point to close it |
   | Rounded rectangle | `R` | drag; set the corner radius in the Element panel |
   | Circle | `C` | drag out from the centre |

   Below the tools, pick cream or orange for new shapes, and whether new shapes are filled.
   `X` swaps the selected shape's colour, arrow keys nudge, `Ctrl+D` duplicates, `[` and `]` change
   the layer order, and `Ctrl+Z` undoes. Press `?` for the full list.
4. In the **Element** panel, choose how a shape is drawn: **Stroke** (2-unit line), **Fill**,
   **Ring** (outline filled with the tile colour) or **Cut-out** (a tile-coloured gap that separates
   overlapping shapes). You can also type or paste path data there.
5. Fill in **App mapping**: the app name (the icon name is derived from it), the package name, and
   optionally exact launcher components.
6. When the checks show **Ready to export**, choose **Export → Glyph JSON**.
7. Put the downloaded `<name>.json` in `glyphs/` and push it, or open a pull request.
   See [What happens after you push](#what-happens-after-you-push).

Work is saved in the browser automatically, so closing the tab doesn't lose it.

### Palette

The **Palette** card has presets (Gruvbox, Aqua, Yellow, Blue, Purple, Light) and lets you change
every colour: tile, lines, accent and the preview wallpaper. Click a slot to make it active, then
click a Gruvbox swatch, use the colour picker, or type a hex value.

Custom colours apply to the canvas, the previews and the **SVG / PNG downloads**, so you can make
your own colour variants. The icon pack in this repo always uses the Gruvbox palette, so the
glyph JSON stores roles (`fg` / `accent`), never colours.

## Find the app's package and launcher component

Icons are matched to apps by package name, which you can find in the app's Play Store or F-Droid
URL. Some apps also need an exact **launcher component** (`package/activity`):

```bash
adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER com.example.app
```

With the phone connected, `python scripts/build_mapping.py` records every launcher component on
the phone in `mapping/components.txt`. It is read-only, and it only ever adds rows.

## The glyph format

```json
{
  "name": "vlc",
  "label": "VLC",
  "packages": ["org.videolan.vlc"],
  "components": ["org.videolan.vlc/org.videolan.vlc.StartActivity"],
  "author": "your-github-name",
  "elements": [
    { "type": "stroke", "color": "fg", "d": "M3 12 A9 9 0 1 0 21 12 A9 9 0 1 0 3 12 Z" },
    { "type": "fill", "color": "accent", "d": "M10 8 L16 12 L10 16 Z", "soft": true }
  ]
}
```

| Key | Meaning |
|---|---|
| `name` | drawable name: lowercase letters, digits and `_`; must match the file name |
| `label` | app name shown in the icon picker and search |
| `packages` | every launcher icon of these packages gets this icon |
| `components` | optional exact `package/activity` entries |
| `elements` | shapes drawn in order on a 24 × 24 grid with a 2-unit round stroke |

Element `type`: `stroke`, `fill` (optional `"soft": true` rounds the edges), `ring`, or `knock`
(a cut-out with a `"width"` margin of 0–8). `color` is `fg` (cream) or `accent` (orange).
`d` is ordinary SVG path data (`M L H V C S Q T A Z`). Icon Studio may add a `shape` object to
remember rectangles and circles; it is optional.

## Rules (CI enforces the first four)

- Content stays inside the 24 × 24 grid; aim for the dashed 2..22 square.
- At most 40 shapes, files up to 16 KB, path data only (no scripts, links or embedded images).
- A package can belong to only one icon.
- The name must be unique and must not be a Java keyword.
- One orange accent element, flat colours, and a 2-unit stroke.
- **Never copy a brand logo.** Draw what the app does.

## What happens after you push

1. **Validate**: every glyph, SVG, PNG and wallpaper is checked for format, size, dimensions and
   active content (`scripts/validate_icons.py`).
2. **Security scan**: files in the icon folders must really be JSON, SVG or PNG, the Gradle wrapper
   checksum is verified, and ClamAV scans the whole repository for malware.
3. **Build**: the icons are rendered, the pack is generated and the APK is built (downloadable
   from the workflow run).
4. On `main`, the regenerated icons and previews are committed back automatically.
5. **Release**: when a version tag is pushed, the same checks run, the release **waits for
   approval**, and then a signed APK is published. See [build-apk.md](build-apk.md#releases-cicd).

## Working locally (optional)

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt      # Windows: .venv\Scripts\pip ...
python scripts/validate_icons.py               # the same checks as CI
python scripts/make_icons.py                   # icons/, preview/icons_sheet.png, editor/library.js
python scripts/build_iconpack.py               # Android resources in iconpack/
```
