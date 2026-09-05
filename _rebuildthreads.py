#!/usr/bin/env python3
"""Rebuild a tour's Threads index FROM the blocks' own 🧵 tags.

Inserting four blocks renumbered everything after the insert point, so every row
in the index now cites the wrong block. `build-any.py` only checks that a cited
number EXISTS, so this rot is silent — the index resolves happily to the wrong
stops. (Exactly the 7.0 failure from the gcd181 session.)

Rebuilding from the tags is the only safe move: the tags live on the blocks, so
they cannot drift out of step with the numbering. Existing hand-written
descriptions are carried across by block name, so nothing is lost.

The whole section is written at whatever indentation the document already uses
(5.0 indents its Threads section by four spaces, 6.0 does not).

Usage: python3 _rebuildthreads.py "5.0 South Coast" [--write]
"""
import os, re, sys, shutil

NAME  = sys.argv[1]
WRITE = "--write" in sys.argv
D = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")
p = os.path.join(D, NAME + ".md")
s = open(p, encoding="utf-8").read()

bind = "    " if re.search(r'^    > ### ', s, re.M) else "  "

blocks = []
for m in re.finditer(r'^%s> ### (\d+\.\d+) (.*)$' % re.escape(bind), s, re.M):
    nxt = s.find("\n%s> ### " % bind, m.end())
    body = s[m.end():nxt if nxt > 0 else len(s)]
    tm = re.search(r'^%s🧵 (.*)$' % re.escape(bind), body, re.M)
    blocks.append((m.group(1), m.group(2),
                   re.findall(r'#(\w+)', tm.group(1)) if tm else []))
print("  %d blocks, %d tagged" % (len(blocks), sum(1 for b in blocks if b[2])))

# [ \t]* not \s* — \s matches newlines, so a greedy \s* starting at an earlier
# line-start swallowed the blank lines above the heading into the "indent",
# and every line came out double-spaced.
hm = re.search(r'^([ \t]*)## 🧵 Threads[ \t]*$', s, re.M)
if not hm:
    sys.exit("no Threads section found")
hind = hm.group(1)
old  = s[hm.start():]

DESC, SECT, INTRO = {}, {}, None
for line in old.split("\n"):
    t = line.strip()
    m = re.match(r'^### (\S+)\s+([^#]+?)\s+#(\w+)$', t)
    if m:
        SECT[m.group(3)] = (m.group(1), m.group(2).strip()); continue
    m = re.match(r'^- \d+\.\d+\s+([^—]+?)\s+—\s+(.+)$', t)
    if m:
        DESC[m.group(1).strip()] = m.group(2).strip(); continue
    if t.startswith("Topics that weave"):
        INTRO = t
print("  carried %d descriptions, %d section headers" % (len(DESC), len(SECT)))

order, seen = [], set()
for _, _, tags in blocks:
    for t in tags:
        if t not in seen:
            seen.add(t); order.append(t)

def short(title):
    return re.sub(r'^[^\wÀ-ɏ]+', '', title).split(" — ")[0].strip()

def subtitle(title):
    parts = title.split(" — ", 1)
    return parts[1].strip() if len(parts) > 1 else ""

# Tags that had no header in the old index. Without a real emoji the builder
# skipped the whole section, so 4 of 14 never reached the app.
FALLBACK = {"trade": ("💰", "Trade"), "folklore": ("🧌", "Folklore"),
            "wildlife": ("🦅", "Wildlife"), "seafaring": ("⚓", "Seafaring"),
            "food": ("🍲", "Food & Drink"), "language": ("🔤", "Language & Names"),
            "history": ("🏛️", "History"), "music": ("🎧", "Music"),
            "nature": ("🌿", "Nature"), "sport": ("🥇", "Sport")}

L = [hind + "## 🧵 Threads", ""]
L += [hind + (INTRO or "Topics that weave through the route. If a guest is "
      "interested in one, these are the script blocks to dig into."), ""]
rows = 0
for t in order:
    emoji, label = SECT.get(t) or FALLBACK.get(t, ("🧵", t.title()))
    L += [hind + "### %s %s  #%s" % (emoji, label, t), ""]
    for num, title, tags in blocks:
        if t in tags:
            nm = short(title)
            d = DESC.get(nm) or subtitle(title) or nm
            L.append(hind + "- %s %s — %s" % (num, nm, d))
            rows += 1
    L.append("")
print("  rebuilt %d sections, %d rows" % (len(order), rows))

out = s[:hm.start()] + "\n".join(L).rstrip() + "\n"
if WRITE:
    shutil.copy2(p, p + ".bak-2026-09-05-threads")
    open(p, "w", encoding="utf-8").write(out)
    print("  WROTE %s" % NAME)
else:
    print("\n".join(L[:10]))
    print("  (dry run)")
