"""Lightweight, dependency-free static-site check run in CI on every PR."""
import sys
import pathlib
from html.parser import HTMLParser

SKIP = ("http://", "https://", "//", "#", "mailto:", "tel:", "data:", "javascript:")


class RefCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ("src", "href") and v:
                self.refs.append((k, v, self.getpos()[0]))

    handle_startendtag = handle_starttag


root = pathlib.Path(".")
html_files = [p for p in root.rglob("*.html") if ".git" not in p.parts]
errors = []
for f in html_files:
    try:
        text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        errors.append(f"{f}: not valid UTF-8: {e}")
        continue
    c = RefCollector()
    try:
        c.feed(text)
        c.close()
    except Exception as e:
        errors.append(f"{f}: HTML parse error: {e}")
        continue
    for k, v, line in c.refs:
        val = v.strip()
        if not val or val.lower().startswith(SKIP):
            continue
        target = f.parent / val.split("?")[0].split("#")[0]
        if not target.exists():
            errors.append(f'{f}:{line}: {k}="{v}" -> missing local file')

if errors:
    print("Site validation FAILED:")
    for e in errors:
        print("  -", e)
    sys.exit(1)
print(f"Site validation passed: {len(html_files)} HTML file(s) checked.")
