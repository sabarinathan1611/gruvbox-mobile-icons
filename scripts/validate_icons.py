"""Validate everything a contributor can add: glyph JSON, icon SVG/PNG and wallpapers.

Checks file types, sizes, formats and dimensions, and rejects anything that could carry
active content (scripts, external references, embedded data) inside SVG or JSON.
Exit code 1 on any error. Under GitHub Actions, problems are printed as file annotations.

Usage:  python scripts/validate_icons.py
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

from glyph_store import GLYPH_DIR, MAX_FILE_BYTES, validate

ROOT = Path(__file__).resolve().parent.parent
GITHUB = os.environ.get("GITHUB_ACTIONS") == "true"

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
LIMITS = {  # folder: (allowed suffixes, max bytes per file, required PNG size or None)
    "glyphs": ({".json"}, MAX_FILE_BYTES, None),
    "icons/svg": ({".svg"}, 32 * 1024, None),
    "icons/png": ({".png"}, 64 * 1024, (192, 192)),
    "wallpapers": ({".png"}, 4 * 1024 * 1024, (1080, 2392)),
}
ALWAYS_OK = {"LICENSE", "README.md", ".gitkeep"}
SVG_NS = "{http://www.w3.org/2000/svg}"
SVG_TAGS = {"svg", "g", "path"}
SVG_ATTRS = {"xmlns", "width", "height", "viewBox", "d", "fill", "stroke", "stroke-width",
             "stroke-linecap", "stroke-linejoin", "transform"}
COLOR_RE = re.compile(r"^(#[0-9a-fA-F]{6}|none)$")

problems = {"error": 0, "warning": 0}


def report(level: str, path: Path, msg: str):
    problems[level] += 1
    rel = path.relative_to(ROOT).as_posix()
    if GITHUB:
        print(f"::{level} file={rel}::{msg}")
    else:
        print(f"{level.upper():7} {rel}: {msg}")


def check_svg(path: Path):
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    if re.search(r"<!DOCTYPE|<!ENTITY|<\?xml-stylesheet", text, re.I):
        return report("error", path, "DOCTYPE, ENTITY and stylesheet declarations are not allowed")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return report("error", path, f"not valid XML ({e})")
    if root.tag != SVG_NS + "svg":
        return report("error", path, "root element must be <svg>")
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag not in SVG_TAGS:
            report("error", path, f"element <{tag}> is not allowed (only svg, g, path)")
        for attr, val in el.attrib.items():
            if attr not in SVG_ATTRS:
                report("error", path, f"attribute '{attr}' is not allowed on <{tag}>")
            elif attr in ("fill", "stroke") and not COLOR_RE.match(val):
                report("error", path, f"{attr} must be a #rrggbb colour, got {val!r}")
            elif re.search(r"url\(|javascript:|data:", val, re.I):
                report("error", path, f"'{attr}' contains a URL or embedded data")
        if (el.text or "").strip():
            report("error", path, f"<{tag}> must not contain text")


def check_png(path: Path, size):
    with path.open("rb") as f:
        if f.read(8) != PNG_MAGIC:
            return report("error", path, "not a PNG file (bad signature)")
    try:
        with Image.open(path) as im:
            im.verify()
        with Image.open(path) as im:
            if size and im.size != size:
                report("error", path, f"must be {size[0]}x{size[1]} px, got {im.size[0]}x{im.size[1]}")
            if path.parent.name == "png" and im.mode != "RGBA":
                report("error", path, f"icons must be RGBA, got {im.mode}")
    except Exception as e:  # noqa: BLE001 - any decoder failure means a broken or hostile file
        report("error", path, f"PNG does not decode ({e})")


def check_glyph(path: Path, packages_seen: dict):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return report("error", path, f"not valid UTF-8 JSON ({e})")
    errors, warnings = validate(data, path.name)
    for e in errors:
        report("error", path, e)
    for w in warnings:
        report("warning", path, w)
    packages = data.get("packages") if isinstance(data, dict) else None
    for pkg in packages if isinstance(packages, list) else []:
        if pkg in packages_seen and packages_seen[pkg] != path.stem:
            report("error", path, f"package {pkg} is already mapped by {packages_seen[pkg]}.json")
        packages_seen[pkg] = path.stem


def main():
    packages_seen: dict[str, str] = {}
    for folder, (suffixes, max_bytes, size) in LIMITS.items():
        base = ROOT / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                report("error", path, "symbolic links are not allowed")
                continue
            if path.is_dir():
                report("error", path, "sub-folders are not allowed here")
                continue
            if path.name in ALWAYS_OK:
                continue
            if path.suffix.lower() not in suffixes or path.suffix != path.suffix.lower():
                report("error", path, f"only {', '.join(sorted(suffixes))} files belong in {folder}/")
                continue
            if path.stat().st_size > max_bytes:
                report("error", path, f"file is {path.stat().st_size:,} bytes; limit is {max_bytes:,}")
                continue
            if path.suffix == ".json":
                check_glyph(path, packages_seen)
            elif path.suffix == ".svg":
                check_svg(path)
            else:
                check_png(path, size)

    if not (GLYPH_DIR / "fallback.json").exists():
        report("error", GLYPH_DIR, "glyphs/fallback.json is required")
    total = sum(1 for _ in GLYPH_DIR.glob("*.json"))
    print(f"checked {total} glyphs: {problems['error']} error(s), {problems['warning']} warning(s)")
    sys.exit(1 if problems["error"] else 0)


if __name__ == "__main__":
    main()
