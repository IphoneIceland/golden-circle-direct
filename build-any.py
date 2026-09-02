#!/usr/bin/env python3
"""
Craft document -> script JS, for either export shape.

  python3 build-any.py "5.0 South Coast" script-5.0.js

Handles both formats the Craft exports have used:
  NEW  sections "+ # 🚌 …", hooks in <callout>, say as "**Name** [PRON] — gloss"
  OLD  sections "## 🚌 …",  hooks as "🎣 …",     say as "[PRON] — Name (gloss)"
Only what the document holds goes in. Nothing invented.
"""
import json, re, os, sys

name, out = sys.argv[1], sys.argv[2]
src = next(p for p in [os.path.expanduser("~/Documents/RitchWiki"), os.path.expanduser("~/mnt/RitchWiki")] if os.path.isdir(p)) + "/Tour Scripts/%s.md" % name

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

raw = open(src, encoding="utf-8").read()
raw = _dedent(raw)

# The 🧵 Threads index is NOT script — it never goes on the mic — but it IS part of
# the document, so it ships. Split it off here and parse it separately at the bottom.
# (Until 31.08.26 this line threw it away, which is how four Threads indexes rotted
#  five stop numbers out of date without a single check failing. Craft, the Mac and
#  the app mirror each other; a section that exists in two of the three does not.)
_parts = re.split(r'^\s*\+? ?#{1,2} 🧵 Threads', raw, maxsplit=1, flags=re.M)
raw, threads_raw = _parts[0], (_parts[1] if len(_parts) > 1 else "")

NEW = bool(re.search(r'^\+ #{1,2}\s', raw, re.M))
# Craft freely mixes "## " and "+ ## " headings inside ONE export, so the
# section pattern accepts both, always. Non-route headings (the doc title,
# safety card) are filtered below by their emoji, not by their markup.
SEC = re.compile(r'^\+? ?#{1,2}\s+(.*)$')
BLK = re.compile(r'^\s*> #{2,3}\s+(.*)$')
CUE = re.compile(r'^\s*> \*(.+?)\*\s*$')
SAYH= re.compile(r'^\s*(?:\+ #{2,3}\s*)?🗣️')
ITEM= re.compile(r'^\s*[-*]\s+(.*)$')
MARK= re.compile(r'^\s*(🎣|🎯|🎤|🌫️|🧵|📖)\s*(.*)$')

def clean(t):
    t = re.sub(r'\[([^\]]+)\]\(block://[^)]*\)', r'\1', t)
    t = re.sub(r'</?callout>', '', t)
    return t.strip()

sections, sec, blk = [], None, None
in_say = in_fence = False; fence=[]

def close_block():
    global blk
    if blk and sec is not None: sec["blocks"].append(blk)
    blk = None
def close_section():
    global sec
    close_block()
    if sec and sec["blocks"]: sections.append(sec)
    sec = None

for ln in raw.split("\n"):
    m = SEC.match(ln)
    if m:
        head = clean(m.group(1))
        close_section()
        if not (head.startswith("📍") or head.startswith("🚌")):
            sec = None; continue    # doc title, safety card, threads index: not script
        kind = "stop" if head.startswith("📍") else "drive"
        sec = {"title": re.sub(r'^[📍🚌]\s*','',head).rstrip("."), "kind": kind, "blocks": []}
        in_say=False; continue
    if sec is None: continue

    if ln.strip().startswith("```"):
        if in_fence and blk: blk.setdefault("pre",[]).append(["", "\n".join(fence)]); fence=[]; in_fence=False
        else: in_fence=True
        continue
    if in_fence: fence.append(ln.rstrip()); continue

    m = BLK.match(ln)
    if m:
        close_block()
        full = clean(m.group(1))
        no   = re.match(r'^(\d+\.\d+)\s+', full)
        head = re.sub(r'^\d+\.\d+\s+','', full)
        parts = re.split(r'\s+[—–]\s+', head, maxsplit=1)
        blk = {"title": parts[0].strip()}
        if no: blk["no"] = no.group(1)      # the stop number the Threads index cites
        if len(parts)>1: blk["sub"]=parts[1].strip()
        in_say=False; continue
    if blk is None: continue

    m = CUE.match(ln)
    if m: blk["cue"]=clean(m.group(1)); continue
    if SAYH.match(ln): in_say=True; continue

    # The 🎣 hook is written as "<callout>🎣 …</callout>", so the marker is not
    # at the start of the raw line and MARK never fired on it. Every hook in every
    # tour was silently dropped from 1970-something until 02.09.26 — it failed the
    # bullets fallback too (the callout precedes the bullets, so "bullets" was not
    # yet in blk) and was discarded outright. Strip the callout wrapper first.
    m = MARK.match(re.sub(r'</?callout>', '', ln))
    if m:
        in_say=False
        sym, rest = m.group(1), clean(m.group(2))
        if sym=="🧵":
            tg=re.findall(r'#\w[\w-]*', rest)
            if tg: blk["tags"]=tg
        elif sym=="🎣": blk["hook"]=rest
        elif sym=="🎯": blk["point"]=rest
        elif sym=="🎤": blk["mic"]=rest
        elif sym=="🌫️": blk["weather"]=rest
        continue

    m = ITEM.match(ln)
    if m:
        text=clean(m.group(1))
        if not text: continue
        if in_say:
            a=re.match(r'^\*\*(.+?)\*\*\s*\[(.+?)\]\s*(?:[—–-]\s*(.*))?$', text)
            b=re.match(r'^\[(.+?)\]\s*[—–-]\s*(.+)$', text)
            if a:
                nm, pr, gl = a.group(1), a.group(2), (a.group(3) or "")
            elif b:
                pr, tail = b.group(1), b.group(2)
                g=re.match(r'^(.*?)\s*\((.+)\)\s*$', tail)
                nm, gl = (g.group(1), g.group(2)) if g else (tail, "")
            else: continue
            blk.setdefault("say",[]).append([re.sub(r'\*','',nm).strip(),
                                             re.sub(r'\*','',pr).strip(),
                                             re.sub(r'\*','',gl).strip()])
        else:
            blk.setdefault("bullets",[]).append(text)
        continue

    t=clean(ln)
    if t and not t.startswith(">") and not t.startswith("*****") and not in_say and "bullets" in blk:
        blk["bullets"].append(t)

close_section()
for si,s in enumerate(sections):
    for bi,b in enumerate(s["blocks"]):
        b["id"] = "%s.%d.%d" % (name.split()[0], si+1, bi+1)

# ---- 🧵 Threads index ------------------------------------------------------
# Cross-reference list at the foot of every script: "if a guest asks about X,
# these are the blocks to open". Entries look like
#     - 1.5 Kjalarnesþing — the prototype, founded by Þorsteinn Ingólfsson
# and a compound entry may cite two stops:
#     - 1.7 Mosfellsdalur / 1.9 Gljúfrasteinn — Halldór Laxness (Nobel 1955)
# Each stop number is resolved to the block id so the app can jump straight there.
BY_NO = {b["no"]: b["id"] for s in sections for b in s["blocks"] if "no" in b}
THR_H = re.compile(r'^\s*#{3}\s+(.*)$')                    # ### ⚖️ Parliament  #law
THR_I = re.compile(r'^\s*[-*]\s+((?:\d+\.\d+[^—–]*?)(?:/\s*\d+\.\d+[^—–]*?)*)\s+[—–]\s+(.*)$')
THR_L = re.compile(r'^\s*([📖📜✍️🎬🎵🪶⚖️🌋].*)$')          # a sub-label like "📖 Books"

threads, thr, sub, thr_intro = [], None, None, ""
def _thr_close():
    global thr, sub
    if thr:
        if sub and sub["items"]: thr["subs"].append(sub)
        if thr["subs"]: threads.append(thr)
    thr, sub = None, None

for ln in threads_raw.split("\n"):
    t = clean(ln)
    if not t or t.startswith("*****"): continue
    m = THR_H.match(ln)
    if m:
        _thr_close()
        head = clean(m.group(1))
        tag  = re.search(r'(#\w[\w-]*)\s*$', head)
        thr  = {"title": re.sub(r'\s*#\w[\w-]*\s*$', '', head).strip(),
                "tag": tag.group(1) if tag else "", "subs": []}
        sub  = {"label": "", "items": []}
        continue
    if thr is None:
        # the one line of prose between the heading and the first group
        if not thr_intro and not t.startswith("-"): thr_intro = t
        continue
    m = THR_I.match(ln)
    if m:
        label, desc = clean(m.group(1)).strip(), clean(m.group(2)).strip()
        first = re.match(r'^(\d+\.\d+)', label)
        threads_id = BY_NO.get(first.group(1), "") if first else ""
        sub["items"].append([label, threads_id, desc])
        continue
    if THR_L.match(ln) and not t.startswith("-"):
        if sub and sub["items"]: thr["subs"].append(sub)
        sub = {"label": t, "items": []}
_thr_close()

# A number in the index that no block answers to is a broken cross-reference —
# the exact rot this section is meant to prevent. Fail loudly rather than ship it.
_dead = [it[0] for th in threads for sb in th["subs"] for it in sb["items"] if not it[1]]
if _dead:
    sys.stderr.write("⚠️  %s: Threads index cites stops that do not exist: %s\n"
                     % (name, ", ".join(_dead)))

def js(v): return json.dumps(v, ensure_ascii=False)
L=["// %s — generated by build-any.py from the Craft document. Do not hand-edit." % name,
   "window.__SCRIPT__ = {", "title: %s," % js(re.sub(r'^[\d.]+\s*','',name)), "sections: ["]
for s in sections:
    L.append("{title:%s, kind:%s, blocks:[" % (js(s["title"]), js(s["kind"])))
    for b in s["blocks"]:
        L.append("{"+", ".join("%s:%s"%(k,js(b[k])) for k in ("id","title","sub","cue") if k in b)+",")
        for k in ("hook","point","mic","weather"):
            if k in b: L.append(" %s:%s,"%(k,js(b[k])))
        for k,fmt in (("bullets",lambda x:"  %s,"%js(x)),):
            if k in b:
                L.append(" %s:["%k); [L.append(fmt(x)) for x in b[k]]; L.append(" ],")
        if "pre" in b:
            L.append(" pre:["); [L.append("  [%s,%s],"%(js(p[0]),js(p[1]))) for p in b["pre"]]; L.append(" ],")
        if "say" in b:
            L.append(" say:["); [L.append("  [%s,%s,%s],"%(js(x[0]),js(x[1]),js(x[2]))) for x in b["say"]]; L.append(" ],")
        if "tags" in b: L.append(" tags:[%s],"%",".join(js(t) for t in b["tags"]))
        L.append("},")
    L.append("]},")
L.append("],")
if threads:
    L.append("threadsIntro: %s," % js(thr_intro))
    L.append("threads: [")
    for th in threads:
        L.append("{title:%s, tag:%s, subs:[" % (js(th["title"]), js(th["tag"])))
        for sb in th["subs"]:
            L.append(" {label:%s, items:[" % js(sb["label"]))
            for it in sb["items"]:
                L.append("  [%s,%s,%s]," % (js(it[0]), js(it[1]), js(it[2])))
            L.append(" ]},")
        L.append("]},")
    L.append("],")
L.append("};")
open(out,"w",encoding="utf-8").write("\n".join(L)+"\n")
n=sum(len(s["blocks"]) for s in sections)
print("%-22s format=%s  sections %d  blocks %d  bullets %d  pronunciations %d  threads %d/%d  -> %s"
      % (name, "NEW" if NEW else "OLD", len(sections), n,
         sum(len(b.get("bullets",[])) for s in sections for b in s["blocks"]),
         sum(len(b.get("say",[])) for s in sections for b in s["blocks"]),
         len(threads), sum(len(sb["items"]) for th in threads for sb in th["subs"]), out))
for s in sections: print("   %-34s %-6s %d" % (s["title"][:34], s["kind"], len(s["blocks"])))
