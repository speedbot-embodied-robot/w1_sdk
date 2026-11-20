"""Check a built W1 VitePress site using only the Python standard library."""

import os
import re
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit


DOCS = Path(__file__).resolve().parents[1] / "docs"
DIST = DOCS / ".vitepress" / "dist"
LANGUAGES = ("zh", "en")


class Page(HTMLParser):
    """Collect public URLs, named destinations and sidebar links from one page."""

    def __init__(self, path):
        super().__init__()
        self.ids = set()
        self.links = []
        self.sidebar_depth = 0
        self.redirect = None
        self.feed(path.read_text(encoding="utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "nav" and (self.sidebar_depth or attrs.get("id") == "VPSidebarNav"):
            self.sidebar_depth += 1
        for key in ("href", "src", "poster"):
            if attrs.get(key):
                self.links.append((tag, attrs[key], bool(self.sidebar_depth)))
        if tag == "meta" and attrs.get("http-equiv", "").lower() == "refresh":
            match = re.fullmatch(r"0\s*;\s*url\s*=\s*(.+)", attrs.get("content", ""), re.I)
            if match:
                self.redirect = match[1]

    def handle_endtag(self, tag):
        if tag == "nav" and self.sidebar_depth:
            self.sidebar_depth -= 1


def check_site():
    prefix = os.getenv("DOCS_BASE", "/").strip("/")
    base = f"/{prefix}/" if prefix else "/"
    platform = os.getenv("DOCS_PLATFORM") or (
        "github" if os.getenv("GITHUB_ACTIONS") == "true" else "local"
    )
    default = os.getenv("DOCS_DEFAULT_LANG") or ("en" if platform == "github" else "zh")
    pages = {p.relative_to(DIST).as_posix(): Page(p) for p in DIST.rglob("*.html")}
    if "index.html" not in pages:
        raise SystemExit("Missing built index.html. Run npm run docs:build first.")
    errors = set()
    if pages["index.html"].redirect != f"{base}{default}/":
        errors.add(f"index.html should redirect to {base}{default}/")
    routes = {lang: set() for lang in LANGUAGES}
    for lang in LANGUAGES:
        sources = {
            p.relative_to(DOCS).with_suffix(".html").as_posix()
            for p in (DOCS / lang).rglob("*.md")
        }
        emitted = {name for name in pages if name.startswith(f"{lang}/")}
        for name in sources ^ emitted:
            errors.add(f"{name}: Markdown source and build output differ")
        routes[lang] = {name.split("/", 1)[1] for name in emitted}
        if "index.html" not in routes[lang]:
            errors.add(f"{lang}/index.html: missing language homepage")
        if not list((DIST / "assets").rglob(f"@localSearchIndex{lang}.*.js")):
            errors.add(f"{lang}: missing local search index")
    for route in routes["en"] ^ routes["zh"]:
        errors.add(f"{route}: missing translation")

    navigation = defaultdict(set)
    sidebar_pages = set()
    for name, page in pages.items():
        for tag, href, in_sidebar in page.links:
            url = urlsplit(urljoin(base + name, href))
            if url.scheme or url.netloc:
                continue
            path = unquote(url.path)
            if not path.startswith(base):
                errors.add(f"{name}: {href} points outside site base {base}")
                continue
            target = path[len(base):]
            if path.endswith("/"):
                target += "index.html"
            if not (DIST / target).is_file():
                errors.add(f"{name}: missing target {href}")
                continue
            if target not in pages:
                continue
            if url.fragment and unquote(url.fragment) not in pages[target].ids:
                errors.add(f"{name}: missing anchor {href}")
            if tag == "a":
                navigation[name].add(target)
                if in_sidebar and name.split("/")[0] == target.split("/")[0]:
                    sidebar_pages.add(target)

    for lang in LANGUAGES:
        home = f"{lang}/index.html"
        if home not in navigation["index.html"]:
            errors.add(f"index.html: missing {lang} language link")
        other = "zh" if lang == "en" else "en"
        seen = set()
        pending = [home]
        while pending:
            name = pending.pop()
            if name not in seen:
                seen.add(name)
                pending.extend(t for t in navigation[name] if t.startswith(f"{lang}/"))
        for route in routes[lang]:
            name = f"{lang}/{route}"
            if name not in seen or (name != home and name not in sidebar_pages):
                errors.add(f"{name}: unreachable from home or missing from sidebar")
            if f"{other}/{route}" not in navigation[name]:
                errors.add(f"{name}: missing link to corresponding {other} page")
    if errors:
        raise SystemExit("\n".join(sorted(errors)))
    print(f"Verified {len(pages)} HTML pages under {base} (default {default}).")


if __name__ == "__main__":
    check_site()
