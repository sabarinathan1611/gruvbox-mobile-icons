"""App catalogue built from glyphs/*.json: drawable name -> (label, [packages and components]).

To theme a new app, add a glyph file in glyphs/ (Icon Studio exports one) and re-run the scripts.
"""
from glyph_store import load_all

# Shown for any app without a custom icon (also offered in the icon picker)
FALLBACK = "fallback"

APPS: dict[str, tuple[str, list[str]]] = {
    name: (g["label"], [*g.get("packages", []), *g.get("components", [])])
    for name, g in load_all().items() if name != FALLBACK
}


def owner_of(component: str) -> str | None:
    """Return the drawable for a full 'pkg/pkg.Activity' component, or None.

    An entry can name a whole package or one exact component (needed when one package,
    like com.android.contacts, exposes two launcher icons).
    """
    pkg = component.split("/", 1)[0]
    for drawable, (_, targets) in APPS.items():
        if component in targets:
            return drawable
    for drawable, (_, targets) in APPS.items():
        if pkg in targets:
            return drawable
    return None
