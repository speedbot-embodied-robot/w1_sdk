"""Validate imported example code before VitePress builds the bilingual site."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def imports_for(page, root):
    references = []
    for number, line in enumerate(page.read_text(encoding="utf-8").splitlines(), 1):
        if not line.lstrip().startswith("<<<"):
            continue
        location = f"{page.relative_to(root)}:{number}"
        tokens = line.lstrip()[3:].strip().split("{", 1)[0].split()
        if not tokens:
            raise ValueError(f"{location}: empty source path")
        token = tokens[0]
        filename, _, region = token.partition("#")
        source = (
            root / "docs" / filename[2:]
            if filename.startswith("@/")
            else page.parent / filename
        ).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(f"{location}: missing or external source: {filename}")
        content = source.read_text(encoding="utf-8")
        if region:
            # Support the Python, C++ and XML region forms used by this project.
            name = re.escape(region)
            patterns = [
                (r"// ?#?", ""),
                (r"# ?", ""),
                (r"<!-- ?#?", r" -->"),
            ]
            matches = []
            for prefix, suffix in patterns:
                start = re.search(
                    rf"(?m)^[ \t]*{prefix}region {name}{suffix}[ \t]*$", content
                )
                if start:
                    matches.append((start, prefix, suffix))
            if not matches:
                raise ValueError(f"{location}: missing or malformed region {region}")
            start, prefix, suffix = min(matches, key=lambda item: item[0].start())
            end = re.compile(
                rf"(?m)^[ \t]*{prefix}endregion {name}{suffix}[ \t]*$"
            ).search(content, start.end())
            if not start or not end or end.start() < start.end():
                raise ValueError(f"{location}: missing or malformed region {region}")
            content = content[start.end() : end.start()]
        if not content.strip():
            raise ValueError(f"{location}: empty code import")
        references.append((source.relative_to(root).as_posix(), region))
    return references


def verify(root=ROOT):
    root = root.resolve()
    sources = {}
    for lang in ("zh", "en"):
        sources[lang] = {
            page.relative_to(root / "docs" / lang): imports_for(page, root)
            for page in sorted((root / "docs" / lang).rglob("*.md"))
        }
    for page in sources["zh"].keys() | sources["en"].keys():
        zh = sources["zh"].get(page, [])
        en = sources["en"].get(page, [])
        if zh != en:
            raise ValueError(
                f"{page}: translations import different source files/regions"
            )
    count = sum(len(items) for pages in sources.values() for items in pages.values())
    print(f"Verified {count} code imports and their bilingual source mappings.")


if __name__ == "__main__":
    try:
        verify()
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from error
