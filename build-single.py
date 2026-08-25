#!/usr/bin/env python3
"""
Inline the app into ONE self-contained file: golden-circle-direct.html.

  python3 build-single.py

index.html plus every local stylesheet, script and Leaflet image, folded into
a single page with no external requests. That file is what goes in the backup
gist. Verified byte-identical against the committed build before first use.

Run it after build-script.py, and bump VERSION in sw.js before shipping.
"""
import re, os, base64, mimetypes

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SRC = "index.html"
OUT = "golden-circle-direct.html"


def rd(p):
    return open(p, encoding="utf-8").read()


def datauri(rel, base="vendor"):
    p = os.path.join(base, rel)
    if not os.path.isfile(p):
        return None            # e.g. Leaflet's url(#default#VML) — leave it be
    mt = mimetypes.guess_type(p)[0] or "application/octet-stream"
    return "data:%s;base64,%s" % (mt, base64.b64encode(open(p, "rb").read()).decode())


def one_url(m):
    d = datauri(m.group(1))
    return m.group(0) if d is None else "url(%s)" % d


def repl_css(m):
    css = re.sub(r'url\((?!data:)([^)\'"]+)\)', one_url, rd(m.group(1)))
    return "<style>\n" + css + "\n</style>"


def repl_js(m):
    return "<script>\n" + rd(m.group(1)) + "\n</script>"


out = re.sub(r'<link rel="stylesheet" href="([^"]+)">', repl_css, rd(SRC))
out = re.sub(r'<script src="([^"]+)"></script>', repl_js, out)

# The picker fetches route-/script-/cues-<id>.js on demand. A single file has no
# siblings to fetch, so every tour's data rides along in a #bundle tag and
# loadScript() reads that instead of the network. Without this the one-file
# build is a working welcome screen bolted to three dead buttons.
import json
tours = re.findall(r'id:"([^"]+)"', rd("tours.js"))
assert tours, "no tours found in tours.js"
bundle = {}
for tid in tours:
    for kind in ("route", "script", "cues"):
        name = "%s-%s.js" % (kind, tid)
        if not os.path.isfile(name):
            raise SystemExit("missing %s — cannot build a complete single file" % name)
        bundle[name] = rd(name)
blob = json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
tag = '<script id="bundle" type="application/json">' + blob + '</script>\n'
assert "</body>" in out
out = out.replace("</body>", tag + "</body>", 1)

open(OUT, "w", encoding="utf-8").write(out)
print("wrote %s (%d bytes, %d tours bundled: %s)" % (OUT, len(out), len(tours), ", ".join(tours)))
