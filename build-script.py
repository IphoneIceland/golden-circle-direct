#!/usr/bin/env python3
"""
Generates script-1.0.js from the Craft document. Nothing else goes in.

  python3 build-script.py [--check]

Source: ~/Documents/RitchWiki (or ~/mnt/RitchWiki when linked)/Tour Scripts/1.0 Golden Circle Direct.md

Sections are its top-level "+ #" / "+ ##" headings, blocks its "> ##" / "> ###"
headings, in document order. A block carries only what the document carries:
title, subtitle, the italic line, 🧵 tags, 🎣 hook, bullets, 🎯, 🎤, 🌫️,
fenced blocks, and the 🗣️ list. Nothing is invented, nothing is dropped.
"""
import json, re, os, sys

CRAFT = next(p for p in [os.path.expanduser("~/Documents/RitchWiki"), os.path.expanduser("~/mnt/RitchWiki")] if os.path.isdir(p)) + "/Tour Scripts/1.0 Golden Circle Direct.md"
OUT   = "script-1.0.js"


def _dedent(raw):
    """Craft sometimes exports the whole document shifted right by a uniform
    margin, which silently breaks every ^-anchored pattern here. Strip the
    common indent; relative indentation (say-lists, children) survives."""
    lines = raw.split("\n")
    pads = [len(l) - len(l.lstrip(" ")) for l in lines if l.strip()]
    common = min(pads) if pads else 0
    if not common:
        return raw
    return "\n".join(l[common:] if l.strip() else "" for l in lines)

raw = open(CRAFT, encoding="utf-8").read()
raw = _dedent(raw)
lines = raw.split("\n")

def clean(t):
    t = re.sub(r'\[([^\]]+)\]\(block://[^)]*\)', r'\1', t)   # Craft internal links
    t = re.sub(r'<callout>|</callout>', '', t)
    return t.strip()

SEC   = re.compile(r'^\+ #{1,2}\s+(.*)$')
BLK   = re.compile(r'^\s*> #{2,3}\s+(.*)$')
CUE   = re.compile(r'^\s*> \*(.+?)\*\s*$')
SAYH  = re.compile(r'^\s*\+ #{2,3}\s*🗣️')
ITEM  = re.compile(r'^\s*[-*]\s+(.*)$')
MARK  = re.compile(r'^\s*(🎣|🎯|🎤|🌫️|🧵|📖)\s*(.*)$')

sections, sec, blk = [], None, None
in_say = in_fence = False
fence = []

def close_block():
    global blk
    if blk and sec is not None:
        sec["blocks"].append(blk)
    blk = None

def close_section():
    global sec
    close_block()
    if sec and sec["blocks"]:
        sections.append(sec)
    sec = None

for ln in lines:
    m = SEC.match(ln)
    if m:
        head = clean(m.group(1))
        if head.startswith("🧵"):            # the thread index is not script
            close_section(); sec = None; blk = None
            break
        close_section()
        kind = "stop" if head.startswith("📍") else "drive"
        sec = {"title": re.sub(r'^[📍🚌]\s*', '', head).rstrip("."),
               "kind": kind, "blocks": []}
        in_say = False
        continue
    if sec is None:
        continue

    if ln.strip().startswith("```"):
        if in_fence:
            blk.setdefault("pre", []).append(["", "\n".join(fence)])
            fence, in_fence = [], False
        else:
            in_fence = True
        continue
    if in_fence:
        fence.append(ln.rstrip()); continue

    m = BLK.match(ln)
    if m:
        close_block()
        head = clean(m.group(1))
        head = re.sub(r'^\d+\.\d+\s+', '', head)
        parts = re.split(r'\s+[—–]\s+', head, maxsplit=1)
        blk = {"title": parts[0].strip()}
        if len(parts) > 1: blk["sub"] = parts[1].strip()
        in_say = False
        continue
    if blk is None:
        continue

    m = CUE.match(ln)
    if m:
        blk["cue"] = clean(m.group(1)); continue

    if SAYH.match(ln):
        in_say = True; continue

    m = MARK.match(ln)
    if m:
        in_say = False
        sym, rest = m.group(1), clean(m.group(2))
        if sym == "🧵":
            tags = re.findall(r'#\w[\w-]*', rest)
            if tags: blk["tags"] = tags
        elif sym == "🎣":  blk["hook"] = rest
        elif sym == "🎯":  blk["point"] = rest
        elif sym == "🎤":  blk["mic"] = rest
        elif sym == "🌫️": blk["weather"] = rest
        continue

    m = ITEM.match(ln)
    if m:
        text = clean(m.group(1))
        if not text: continue
        if in_say:
            sm = re.match(r'^\*\*(.+?)\*\*\s*\[(.+?)\]\s*(?:[—–-]\s*(.*))?$', text)
            if sm:
                blk.setdefault("say", []).append(
                    [sm.group(1).strip(), re.sub(r'\*', '', sm.group(2)).strip(),
                     (sm.group(3) or "").strip()])
            else:
                sm2 = re.match(r'^\[(.+?)\]\s*[—–-]\s*(.+)$', text)
                if sm2:
                    blk.setdefault("say", []).append(
                        [sm2.group(2).strip(), re.sub(r'\*','',sm2.group(1)).strip(), ""])
        else:
            blk.setdefault("bullets", []).append(text)
        continue

    t = clean(ln)
    if t and not t.startswith(">") and not t.startswith("*****") and not in_say:
        if "bullets" in blk: blk["bullets"].append(t)

close_section()

# Keep the existing ids where the shape still matches, so cues-1.0.js and the
# map pins stay joined to the right blocks.
flat = [b for s in sections for b in s["blocks"]]
try:
    keep = json.load(open("/tmp/ids.json"))
except Exception:
    keep = []
if len(keep) == len(flat):
    for b, i in zip(flat, keep): b["id"] = i
else:
    for si, s in enumerate(sections):
        for bi, b in enumerate(s["blocks"]):
            b["id"] = "%d.%d" % (si + 1, bi + 1)

def js(v): return json.dumps(v, ensure_ascii=False)
L = ["// 1.0 Golden Circle Direct.",
     "// GENERATED by build-script.py from RitchWiki/Tour Scripts/1.0 Golden Circle Direct.md",
     "// Document only — nothing added. Edit Craft, then re-run the build.",
     "window.__SCRIPT__ = {", "title: %s," % js("Golden Circle Direct"), "sections: ["]
for s in sections:
    L.append("{title:%s, kind:%s, blocks:[" % (js(s["title"]), js(s["kind"])))
    for b in s["blocks"]:
        L.append("{" + ", ".join("%s:%s" % (k, js(b[k])) for k in ("id","title","sub","cue") if k in b) + ",")
        for k in ("hook","point","mic","weather"):
            if k in b: L.append(" %s:%s," % (k, js(b[k])))
        if "bullets" in b:
            L.append(" bullets:[");  [L.append("  %s," % js(x)) for x in b["bullets"]];  L.append(" ],")
        if "pre" in b:
            L.append(" pre:[");      [L.append("  [%s,%s]," % (js(p[0]), js(p[1]))) for p in b["pre"]];  L.append(" ],")
        if "say" in b:
            L.append(" say:[");      [L.append("  [%s,%s,%s]," % (js(x[0]), js(x[1]), js(x[2]))) for x in b["say"]];  L.append(" ],")
        if "tags" in b: L.append(" tags:[%s]," % ",".join(js(t) for t in b["tags"]))
        L.append("},")
    L.append("]},")
L.append("]};")
out = "\n".join(L) + "\n"

n = sum(len(s["blocks"]) for s in sections)
says = sum(len(b.get("say", [])) for s in sections for b in s["blocks"])
buls = sum(len(b.get("bullets", [])) for s in sections for b in s["blocks"])
print("sections %d · blocks %d · bullets %d · pronunciations %d" % (len(sections), n, buls, says))
for s in sections:
    print("  %-36s %-6s %d" % (s["title"][:36], s["kind"], len(s["blocks"])))
missing = [b["id"]+" "+b["title"] for s in sections for b in s["blocks"] if not b.get("bullets")]
if missing: print("blocks with no bullets:", "; ".join(missing))
if "--check" not in sys.argv:
    open(OUT, "w", encoding="utf-8").write(out)
    print("wrote", OUT, len(out), "bytes")
