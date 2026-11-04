"""Build the GitHub Pages site into _site/.

    /          Icon Studio (copied from editor/)
    /docs/     documentation rendered from README.md and docs/*.md

Usage:    python scripts/build_site.py
Preview:  python -m http.server 8000 --directory _site   then open http://localhost:8000/
The Pages workflow (.github/workflows/pages.yml) runs this on every push to main.
"""
import html
import json
import re
import shutil
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

from glyph_store import load_all
from make_icons import write_editor_library

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "_site"
TEMPLATES = ROOT / "site"
REPO = "sabarinathan1611/gruvbox-mobile-icons"
GITHUB = f"https://github.com/{REPO}"
RELEASES = f"{GITHUB}/releases/latest"
BRANCH = "main"

# (source file, URL slug under /docs/, sidebar title); a None source builds the licence page
PAGES = [
    ("README.md", "", "Introduction"),
    ("docs/how-to-make-icons.md", "making-icons", "Making icons"),
    ("docs/build-apk.md", "building", "Building and releasing"),
    ("docs/CONTRIBUTING.md", "contributing", "Contributing"),
    (None, "license", "License"),
]
SLUG_BY_SOURCE = {src: slug for src, slug, _ in PAGES if src}
ASSET_DIRS = ("preview/", "icons/", "wallpapers/")
STUDIO_FILES = ("index.html", "styles.css", "app.js", "library.js")
FAVICON = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><rect width="24" height="24" '
           'rx="5.3" fill="#3c3836"/><path d="M7 12h10M12 7v10" stroke="#fe8019" stroke-width="2.4" '
           'stroke-linecap="round"/></svg>')

ATTR_RE = re.compile(r'\b(href|src)="([^"]*)"')
HEADING_RE = re.compile(r'<h([1-3]) id="([^"]+)">(.*?)</h\1>', re.S)
TAG_RE = re.compile(r"<[^>]+>")


def page_url(slug: str) -> str:
    """Site-relative URL of a docs page."""
    return f"docs/{slug}/" if slug else "docs/"


# ---------- markdown ----------

def new_markdown() -> markdown.Markdown:
    return markdown.Markdown(
        extensions=["tables", "fenced_code", "codehilite", "toc", "sane_lists", "attr_list"],
        extension_configs={
            "codehilite": {"css_class": "highlight", "guess_lang": False},
            "toc": {"permalink": "#", "permalink_title": "Link to this section"},
        },
    )


def text_of(fragment: str) -> str:
    text = html.unescape(TAG_RE.sub(" ", fragment))
    return re.sub(r"\s+", " ", text).strip()


def license_page() -> tuple[str, dict[str, str]]:
    """Markdown for the licence page, plus raw HTML blocks to splice in after rendering."""
    blocks = {}
    for key, path in (("CODE", "LICENSE"), ("ART", "LICENSE-ARTWORK")):
        body = html.escape((ROOT / path).read_text(encoding="utf-8"))
        blocks[f"<p>{key}_LICENSE_TEXT</p>"] = (
            f'<details><summary>Full text of {path}</summary>'
            f'<div class="highlight"><pre><code>{body}</code></pre></div></details>')
    md = """# License

Gruvbox Clean uses two licences: one for the code and one for the artwork.

| Part | Licence |
|---|---|
| **Code**: `scripts/`, `editor/`, `site/`, `iconpack/` (Gradle, Java, XML) | Apache License 2.0 |
| **Artwork**: icons, glyph designs in `glyphs/`, wallpapers, previews | CC BY-NC-SA 4.0 |

You're welcome to use, share and remix the icons and wallpapers **for non-commercial use**, with
credit ("Gruvbox Clean by sabarinathan1611") and under the same licence. Selling the icons or
wallpapers, or including them in a paid product, is not allowed without permission.
Contributions are accepted under the terms in
[Contributing](docs/CONTRIBUTING.md#licence-of-contributions).

The colour palette is [Gruvbox](https://github.com/morhetz/gruvbox) by Pavel Pertsev (MIT licence).

## Apache License 2.0 (code)

CODE_LICENSE_TEXT

## CC BY-NC-SA 4.0 (artwork)

ART_LICENSE_TEXT
"""
    return md, blocks


# ---------- links ----------

def rewrite_links(page_html: str, source: str | None, to_root: str) -> str:
    """Turn repo-relative links into site pages, copied assets or GitHub URLs."""
    src_dir = (ROOT / source).parent if source else ROOT

    def fix(m):
        attr, url = m.group(1), html.unescape(m.group(2))
        if not url or re.match(r"^([a-z][a-z0-9+.-]*:|#|//)", url, re.I):
            return m.group(0)
        path, _, frag = url.partition("#")
        frag = f"#{frag}" if frag else ""
        target = (src_dir / path).resolve()
        try:
            rel = target.relative_to(ROOT).as_posix()
        except ValueError:
            return m.group(0)
        if rel in SLUG_BY_SOURCE:
            new = f"{to_root}{page_url(SLUG_BY_SOURCE[rel])}{frag}"
        elif rel in ("LICENSE", "LICENSE-ARTWORK"):
            new = f"{to_root}{page_url('license')}"
        elif rel in ("editor", "editor/index.html"):
            new = to_root
        elif rel.startswith(ASSET_DIRS) and target.is_file() and target.suffix in (".png", ".svg"):
            dest = OUT / "assets" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, dest)
            new = f"{to_root}assets/{rel}"
        else:
            kind = "tree" if target.is_dir() else "blob"
            new = f"{GITHUB}/{kind}/{BRANCH}/{rel}{frag}"
        return f'{attr}="{html.escape(new, quote=True)}"'

    return ATTR_RE.sub(fix, page_html)


# ---------- page parts ----------

def toc_html(tokens: list[dict]) -> str:
    """'On this page' list of the h2 headings with their h3s nested."""
    def items(level_tokens):
        out = []
        for t in level_tokens:
            if t["level"] in (2, 3):
                kids = items(t["children"]) if t["level"] == 2 else ""
                out.append(f'<li><a href="#{t["id"]}">{html.escape(text_of(t["name"]))}</a>{kids}</li>')
            else:
                out.extend(items(t["children"]))
        return f"<ul>{''.join(out)}</ul>" if out else ""

    body = items(tokens)
    return f"<h2>On this page</h2>{body}" if body else ""


def nav_html(current: str, to_root: str) -> str:
    links = []
    for _, slug, title in PAGES:
        on = ' class="on" aria-current="page"' if slug == current else ""
        links.append(f'<li><a href="{to_root}{page_url(slug)}"{on}>{html.escape(title)}</a></li>')
    return (f'<p class="group">Documentation</p><ul>{"".join(links)}</ul>'
            f'<div class="cta"><a class="primary" href="{to_root}">Open Icon Studio</a>'
            f'<a href="{RELEASES}">Download the APK</a></div>')


def pager_html(i: int, to_root: str) -> str:
    def link(j, cls, label):
        _, slug, title = PAGES[j]
        return f'<a class="{cls}" href="{to_root}{page_url(slug)}"><small>{label}</small>{html.escape(title)}</a>'
    out = link(i - 1, "prev", "Previous") if i > 0 else ""
    out += link(i + 1, "next", "Next") if i < len(PAGES) - 1 else ""
    return out


def sections(page_html: str, page_title: str, url: str) -> list[dict]:
    """Split a page at its h1-h3 headings into search-index entries."""
    marks = list(HEADING_RE.finditer(page_html))
    entries = []
    for k, m in enumerate(marks):
        end = marks[k + 1].start() if k + 1 < len(marks) else len(page_html)
        heading = text_of(m.group(3)).rstrip("#").strip()
        text = text_of(page_html[m.end():end])[:600]
        anchor = "" if m.group(1) == "1" else f"#{m.group(2)}"
        entries.append({"page": page_title, "heading": heading, "url": f"{url}{anchor}", "text": text})
    return entries


# ---------- build ----------

def build_docs(template: str) -> list[dict]:
    index = []
    for i, (source, slug, title) in enumerate(PAGES):
        md = new_markdown()
        if source:
            text, blocks = (ROOT / source).read_text(encoding="utf-8"), {}
        else:
            text, blocks = license_page()
        body = md.convert(text)
        for placeholder, block in blocks.items():
            body = body.replace(placeholder, block)
        to_root = "../../" if slug else "../"
        body = rewrite_links(body, source, to_root)

        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        page_title = text_of(h1.group(1)).rstrip("#").strip() if h1 else title
        para = re.search(r"<p>(.*?)</p>", body, re.S)
        description = text_of(para.group(1))[:160] if para else page_title
        url = page_url(slug)
        edit = f"{GITHUB}/edit/{BRANCH}/{source}" if source else f"{GITHUB}/blob/{BRANCH}/LICENSE-ARTWORK"

        page = template
        for key, value in {
            "{{title}}": html.escape(page_title), "{{description}}": html.escape(description, quote=True),
            "{{root}}": to_root, "{{github}}": GITHUB, "{{releases}}": RELEASES,
            "{{nav}}": nav_html(slug, to_root), "{{toc}}": toc_html(md.toc_tokens),
            "{{content}}": body, "{{pager}}": pager_html(i, to_root), "{{edit}}": edit,
        }.items():
            page = page.replace(key, value)
        dest = OUT / url / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(page, encoding="utf-8", newline="\n")
        index += sections(body, title, url)
        print(f"  {url} <- {source or 'LICENSE files'}")
    return index


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    # Icon Studio at the site root, with an up-to-date icon library
    write_editor_library(load_all())
    for name in STUDIO_FILES:
        shutil.copy2(ROOT / "editor" / name, OUT / name)
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")

    # Documentation
    assets = OUT / "docs" / "assets"
    assets.mkdir(parents=True)
    dark = HtmlFormatter(style="gruvbox-dark").get_style_defs(".highlight")
    light = HtmlFormatter(style="gruvbox-light").get_style_defs(".highlight")
    css = (TEMPLATES / "docs.css").read_text(encoding="utf-8")
    (assets / "docs.css").write_text(
        f"{css}\n/* Pygments: gruvbox-dark, gruvbox-light */\n{dark}\n"
        f"@media (prefers-color-scheme: light) {{\n{light}\n}}\n", encoding="utf-8", newline="\n")
    shutil.copy2(TEMPLATES / "docs.js", assets / "docs.js")
    index = build_docs((TEMPLATES / "docs.html").read_text(encoding="utf-8"))
    (assets / "search-index.js").write_text(
        f"window.DOCS_INDEX = {json.dumps(index, ensure_ascii=False, separators=(',', ':'))};\n",
        encoding="utf-8", newline="\n")

    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"built {OUT}: Icon Studio + {len(PAGES)} doc pages, {len(index)} search entries, {files} files")


if __name__ == "__main__":
    main()
