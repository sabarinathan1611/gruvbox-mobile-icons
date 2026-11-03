"""Read the phone's real launcher components (read-only adb) and write mapping/components.txt.

Sources:
  1. `cmd package query-activities` for MAIN/LAUNCHER (everything launchable for the owner user)
  2. `dumpsys package <pkg>` for every package in apps.py, to also catch apps that live in
     another user profile and alternate launcher aliases (e.g. Fossify colour variants)

Usage:  .venv/Scripts/python.exe scripts/build_mapping.py [serial]
"""
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from apps import APPS, owner_of

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "mapping" / "components.txt"
# Optional device serial; without one, adb uses the only connected device
SERIAL = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("ANDROID_SERIAL")

COMPONENT_RE = re.compile(r"^\s*(?:[0-9a-f]+\s+)?([\w.]+/[\w.$]+)(?:\s+filter\s+[0-9a-f]+)?\s*$")


def adb(*args: str) -> str:
    target = ["-s", SERIAL] if SERIAL else []
    res = subprocess.run(["adb", *target, "shell", *args], capture_output=True, text=True,
                         encoding="utf-8", errors="replace")
    return res.stdout


def full(component: str) -> str:
    """Expand 'pkg/.Act' to 'pkg/pkg.Act'."""
    pkg, act = component.split("/", 1)
    return f"{pkg}/{pkg}{act}" if act.startswith(".") else component


def launcher_query() -> set[str]:
    out = adb("cmd", "package", "query-activities", "--brief",
              "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER")
    return {full(m.group(1)) for line in out.splitlines() if (m := COMPONENT_RE.match(line))}


def launcher_from_dumpsys(pkg: str) -> set[str]:
    """Components in the package's resolver table that have both MAIN and LAUNCHER."""
    text = adb("dumpsys", "package", pkg)
    table = text.split("Activity Resolver Table:", 1)[-1].split("Receiver Resolver Table:", 1)[0]
    found, current, actions, cats = set(), None, set(), set()

    def flush():
        if current and "android.intent.action.MAIN" in actions \
                and "android.intent.category.LAUNCHER" in cats:
            found.add(full(current))

    for line in table.splitlines():
        m = re.match(r"^\s+[0-9a-f]+\s+([\w.]+/[\w.$]+)\s+filter\s+[0-9a-f]+", line)
        if m:
            flush()
            current, actions, cats = m.group(1), set(), set()
        elif current and (a := re.search(r'Action: "([^"]+)"', line)):
            actions.add(a.group(1))
        elif current and (c := re.search(r'Category: "([^"]+)"', line)):
            cats.add(c.group(1))
    flush()
    return {c for c in found if c.startswith(pkg + "/")}


def read_existing() -> dict[str, str]:
    if not OUT.exists():
        return {}
    rows = {}
    for line in OUT.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            parts = line.split()
            rows[parts[0]] = parts[-1]
    return rows


def main():
    # Merge, never replace: components found on earlier runs or other phones stay mapped
    components = read_existing()
    for c in launcher_query():
        components[c] = "launcher"
    packages = sorted({t.split("/", 1)[0] for _, targets in APPS.values() for t in targets})
    for pkg in packages:
        for c in launcher_from_dumpsys(pkg):
            components.setdefault(c, "manifest")
    if not components:
        sys.exit("no components found - is the phone connected and authorised?")

    rows = sorted(components.items())
    w = max(len(c) for c, _ in rows)
    lines = [
        f"# Launcher components found on the connected phone, generated {date.today()}",
        "# by scripts/build_mapping.py. Columns: component, drawable ('-' = fallback), source",
        "# source: launcher = launchable for owner user; manifest = other profile or alias",
    ]
    for c, src in rows:
        lines.append(f"{c:<{w}}  {owner_of(c) or '-':<16}  {src}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    themed = sum(1 for c, _ in rows if owner_of(c))
    print(f"wrote {OUT}: {len(rows)} components, {themed} themed")
    missing = [d for d, (_, t) in APPS.items() if not any(owner_of(c) == d for c, _ in rows)]
    if missing:
        print("drawables with no component on this phone:", ", ".join(missing))


if __name__ == "__main__":
    main()
