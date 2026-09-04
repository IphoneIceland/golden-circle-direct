#!/usr/bin/env python3
"""9.0 has no Threads index at all. Build one from 10.0's — same stops, reversed
route, so the descriptions carry over verbatim and only the numbers change."""
import re, io, unicodedata

SRC = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts/"
P9, P10 = SRC + "9.0 Snæfellsnes North.md", SRC + "10.0 Snæfellsnes South.md"

def key(t):
    t = re.sub(r'[\*_`]', '', t)
    t = "".join(c for c in t if not unicodedata.category(c).startswith("S"))
    t = re.split(r'\s+[—–]\s+', t, 1)[0]
    return re.sub(r'\s+', ' ', t).strip().lower()

def heads(path):
    raw = io.open(path, encoding="utf-8").read()
    body = re.split(r'^\s*\+? ?#{1,2} 🧵 Threads', raw, maxsplit=1, flags=re.M)[0]
    return {m.group(1): m.group(2).strip()
            for m in re.finditer(r'(?m)^\s*> ### (\d+\.\d+)\s+(.*)$', body)}

h9, h10 = heads(P9), heads(P10)
by_key9 = {key(v): k for k, v in h9.items()}
map10to9 = {}
for no, ti in h10.items():
    k = key(ti)
    if k in by_key9:
        map10to9[no] = by_key9[k]
missing = [n for n in h10 if n not in map10to9]
print("unmapped 10.0 stops:", missing or "none")

# read 10.0's index
raw10 = io.open(P10, encoding="utf-8").read()
thr10 = re.split(r'^\s*\+? ?#{1,2} 🧵 Threads', raw10, maxsplit=1, flags=re.M)[1]
sections, cur = [], None
for ln in thr10.split("\n"):
    m = re.match(r'^\s*(### .*?)\s*$', ln)
    if m:
        cur = [m.group(1), []]; sections.append(cur); continue
    m = re.match(r'^\s*-\s+(\d+\.\d+)\s+(.*)$', ln)
    if m and cur:
        cur[1].append((m.group(1), m.group(2)))

# 9.0-only stops that need their own lines
EXTRA = {
 "#geology":  [("9.15", "Fossá — a waterfall on porous lava, and nobody wrote its name down"),
               ("9.16", "Selvallavatn — a lake fed by a river with no outlet on the surface")],
 "#wildlife": [],
 "#history":  [("9.15", "Fossá — the one waterfall in a country of named water that never got a name"),
               ("9.16", "Selvallavatn — the whirlpool a farm boy noticed and nobody followed up")],
 "#language": [("9.15", "Fossá — 'river falls', which is Icelandic for 'we did not bother'")],
}
NEWSEC = {"#history": "### 🕰️ History  #history",
          "#language": "### 🔤 Language & Names  #language"}

out = ["*******", "", "## 🧵 Threads", "",
       "Topics that weave through the route. If a guest is interested in one, these are the script blocks to dig into.", ""]

def num(n):
    return tuple(int(x) for x in n.split("."))

done = set()
for head, items in sections:
    tag = re.search(r'(#\w+)\s*$', head)
    tag = tag.group(1) if tag else ""
    done.add(tag)
    lines = []
    for no, desc in items:
        n9 = map10to9.get(no)
        if not n9:
            print("  dropped (no 9.0 stop):", no, desc[:50]); continue
        lines.append((n9, "%s %s" % (n9, re.sub(r'^10\.\d+\s*', '', desc))))
    for n9, d in EXTRA.get(tag, []):
        lines.append((n9, "%s %s" % (n9, d)))
    if not lines:
        continue
    lines.sort(key=lambda x: num(x[0]))
    out += [head, ""] + ["- " + d for _, d in lines] + [""]

for tag, head in NEWSEC.items():
    if tag in done:
        continue
    lines = sorted(EXTRA[tag], key=lambda x: num(x[0]))
    out += [head, ""] + ["- %s %s" % (n, d) for n, d in lines] + [""]

t9 = io.open(P9, encoding="utf-8").read()
assert "🧵 Threads" not in t9
t9 = t9.replace("\U0001f9f5 #geology #saga", "\U0001f9f5 #geology #literature")
t9 = t9.replace("\U0001f9f5 #geology #nature #history", "\U0001f9f5 #geology #wildlife #history")
t9 = t9.replace("\U0001f9f5 #nature #geology", "\U0001f9f5 #wildlife #geology")
t9 = t9.rstrip("\n") + "\n\n" + "\n".join(out).rstrip() + "\n"
io.open(P9, "w", encoding="utf-8").write(t9)
print("9.0 threads index written:", len([l for l in out if l.startswith("- ")]), "entries")
