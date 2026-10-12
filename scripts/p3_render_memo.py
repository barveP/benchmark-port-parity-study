#!/usr/bin/env python3
"""Render a Markdown memo to a self-contained HTML file with the figures embedded (base64), so it can be
sent or opened anywhere. Usage: python -I scripts/p3_render_memo.py <memo.md> <out.html>
Image links in the memo are resolved relative to the memo's folder.
"""
import base64
import os
import re
import sys

import markdown

src, out = sys.argv[1], sys.argv[2]
text = open(src, encoding="utf-8").read()
base = os.path.dirname(os.path.abspath(src))


def embed(m):
    alt, path = m.group(1), m.group(2)
    full = os.path.normpath(os.path.join(base, path))
    if not os.path.exists(full):
        return m.group(0)
    ext = os.path.splitext(full)[1].lstrip(".").lower()
    data = base64.b64encode(open(full, "rb").read()).decode("ascii")
    return f'<img alt="{alt}" src="data:image/{"jpeg" if ext == "jpg" else ext};base64,{data}" style="max-width:100%;">'


text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", embed, text)
body = markdown.markdown(text, extensions=["tables"])
title = re.search(r"^#\s+(.+)$", open(src, encoding="utf-8").read(), re.M)
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>{title.group(1) if title else 'memo'}</title>
<style>body{{font-family:Georgia,serif;max-width:46em;margin:2em auto;padding:0 1em;line-height:1.45;color:#222}}
table{{border-collapse:collapse;font-size:0.9em}}td,th{{border:1px solid #bbb;padding:3px 7px;text-align:left}}
img{{display:block;margin:1em auto}}h1{{font-size:1.5em}}h2{{font-size:1.2em;margin-top:1.6em}}code{{font-size:0.9em}}
figcaption,em.caption{{font-size:0.9em;color:#444}}</style></head><body>{body}</body></html>"""
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {out} ({len(html) // 1024} KB)")
