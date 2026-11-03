# Contributing

Thanks for helping. Icon requests and new icons are both welcome.

## Request an icon

Open an issue titled `Icon request: <App name>` with:

- the app name and a store / F-Droid link
- the **launcher component** (`package/activity`). Get it with:

  ```bash
  adb shell cmd package resolve-activity --brief -a android.intent.action.MAIN -c android.intent.category.LAUNCHER <package>
  ```

  If you can't run adb, the package name alone is fine.

## Add an icon yourself

1. Fork the repo and create a branch, for example `icon/obsidian`.
2. Follow [how-to-make-icons.md](how-to-make-icons.md): add the glyph to `scripts/glyphs.py`
   and the app to `scripts/apps.py`.
3. If you have the phone connected, run `python scripts/build_mapping.py` so the app's
   components are added to `mapping/components.txt`. The script only adds rows, never removes them.
4. Regenerate:

   ```bash
   python scripts/make_icons.py
   python scripts/build_iconpack.py
   ```

5. Commit the code **and** the generated files (`icons/`, `preview/icons_sheet.png`,
   `mapping/components.txt`, `iconpack/app/src/main/`), so the APK builds straight from the repo.
6. Open a pull request. Include a crop of your icon from `preview/icons_sheet.png`.

## Style rules (PRs that break these will be asked to change)

- 24-unit grid, content inside 2..22, 2-unit round stroke.
- Cream `#ebdbb2` lines and **one** orange `#fe8019` accent; flat, with no gradients or shadows.
- **No brand logos or lookalikes.** Draw the app's function, not its logo. This keeps the pack
  original and safe to distribute.
- No stock images, fonts or traced artwork: everything is drawn with the helpers in `glyphs.py`.
- Never hand-edit generated PNG, SVG or XML files; change the scripts and re-run them.

## Never commit

- raw adb dumps (`mapping/raw_query.txt`, `mapping/*.tmp`), which list every app on your phone
- build output, `local.properties`, keystores or passwords

## Other changes

Wallpapers live in `scripts/make_wallpapers.py`, and the palette in `scripts/palette.py`.
For bigger changes (new wallpaper styles, a different accent colour), open an issue first.
