#!/usr/bin/env python3
"""
Inline the app into ONE self-contained file: iguide-iceland.html.

  python3 build-single.py

index.html plus every local stylesheet, script and Leaflet image, folded into
a single page with no external requests. That file is what goes in the backup
gist. Verified byte-identical against the committed build before first use.

Run it after build-script.py, and bump VERSION in sw.js before shipping.
"""
import re, os, base64, mimetypes

os.chdir(os.path.dirname(os.path.abspath(__file__)))
SRC = "index.html"
OUT = "iguide-iceland.html"


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

# The theme lives in the INLINE <style> — @font-face pointing at fonts/*.woff2 —
# and the logo is a plain <img>. Neither is a linked stylesheet or a script src,
# so the passes above walked straight past them and the one-file build came out
# in fallback serif with a broken logo. Fold them in too.
def local_datauri(path):
    if not os.path.isfile(path):
        raise SystemExit("missing %s — cannot build a complete single file" % path)
    mt = mimetypes.guess_type(path)[0] or "application/octet-stream"
    if path.endswith(".woff2"):
        mt = "font/woff2"
    if path.endswith(".svg"):
        mt = "image/svg+xml"
    return "data:%s;base64,%s" % (mt, base64.b64encode(open(path, "rb").read()).decode())

def inline_font(m):
    return "url(%s)" % local_datauri(m.group(1))
out, nfonts = re.subn(r"url\('(fonts/[^']+)'\)", inline_font, out)

def inline_img(m):
    return '%s"%s"%s' % (m.group(1), local_datauri(m.group(2)), m.group(3))
out, nimgs = re.subn(r'(<img[^>]*\ssrc=)"(images/[^"]+)"([^>]*>)', inline_img, out)
assert nfonts == 2, "expected 2 @font-face urls, rewrote %d" % nfonts
assert nimgs >= 1, "expected at least one local <img>, rewrote %d" % nimgs

# The picker fetches route-/script-/cues-<id>.js on demand. A single file has no
# siblings to fetch, so every tour's data rides along in a #bundle tag and
# loadScript() reads that instead of the network. Without this the one-file
# build is a working welcome screen bolted to three dead buttons.
import json
tours = re.findall(r'\{id:"([^"]+)"', rd("tours.js"))
assert tours, "no tours found in tours.js"
# tours.js lists tours that are not built yet (ready:false). Those have no data
# to bundle and must not stop the build — but a tour the picker WILL open and
# whose files are missing is a real hole, so that still fails loudly.
ready = re.findall(r'\{id:"([^"]+)",\s*ready:true', rd("tours.js"))
bundle = {}
for tid in tours:
    files = ["%s-%s.js" % (k, tid) for k in ("route", "script", "cues")]
    missing = [f for f in files if not os.path.isfile(f)]
    if missing:
        if tid in ready:
            raise SystemExit("tour %s is ready:true but %s missing — "
                             "the picker would open a dead tour" % (tid, ", ".join(missing)))
        print("  skipping %s — not built yet" % tid)
        continue
    for f in files:
        bundle[f] = rd(f)
# The tour translations load on demand too, so they have the same problem.
for name in sorted(os.listdir("i18n/tours")):
    if name.endswith(".js"):
        bundle["i18n/tours/" + name] = rd("i18n/tours/" + name)
blob = json.dumps(bundle, ensure_ascii=False).replace("<", "\\u003c")
tag = '<script id="bundle" type="application/json">' + blob + '</script>\n'
assert "</body>" in out
out = out.replace("</body>", tag + "</body>", 1)

open(OUT, "w", encoding="utf-8").write(out)
built = sorted({k.split("-",1)[1][:-3] for k in bundle if k.startswith("route-")})
print("wrote %s (%d bytes, %d tours bundled, %d fonts, %d images: %s)"
      % (OUT, len(out), len(built), nfonts, nimgs, ", ".join(built)))
