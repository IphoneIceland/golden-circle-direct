#!/usr/bin/env python3
"""
Craft -> app converter for the 1.0 Golden Circle Direct script.

Craft is the manuscript. This regenerates script-1.0.js from it so the two
can never drift again.

  python3 build-script.py [--check]

Content (sub, hook, bullets, point, mic, say, tags) comes from Craft, matched
on block TITLE. Route facts (id, emoji, cue, target, weather, flag) stay as
they are in the app, because those describe where the coach is, not what is
said. Blocks in the app that Craft has never heard of are left untouched and
reported at the end.

The parser reads the CURRENT Craft export shape:

    > ### 1.2 🏢 Title — Subtitle
    > *cue*
    <callout>🎣 hook</callout>
    - bullet
    🎯 point
    🎤 mic
    🌫️ Weather pivot (…): "…"
    + ### 🗣️ How to say it:
      - **Name** [**PRON**] — gloss
    🧵 #tag #tag

and stays tolerant of the older one (📖 marker, `* ` bullets, 🧵 second,
`* [**PRON**] — Name (gloss)` pronunciations).
"""
import json, re, subprocess, sys, os

CRAFT = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts/1.0 Golden Circle Direct.md")
APP   = "script-1.0.js"

# Blocks the app deliberately keeps hand-structured: Craft holds them as
# markdown tables and code blocks, and the app's heads/pre version reads
# better on a phone. Wording still comes from Craft for everything else.
HAND_STRUCTURED = {"The Norse Expansion (793–1066 CE)"}

MARKERS = "🎣📖🎯🎤🗣🌫🧵"

# A block heading: "> ### 1.2 🏢 Title — Subtitle", any heading depth,
# any leading indentation. The 🗣️ sub-heading has no "> " so never matches.
HEAD_RE    = re.compile(r'^[ \t]*>[ \t]*#{1,6}[ \t]+(.*)$')
# The trailing Threads index, "+ ## 🧵 Threads" — not a block.
THREADS_RE = re.compile(r'^[ \t]*\+?[ \t]*#{1,6}[ \t]*🧵[ \t]*Threads\b')
LINK_RE    = re.compile(r'\[([^\]]+)\]\([^)]*\)')
NUM_RE     = re.compile(r'^(\d+\.\d+[a-z]?)[ \t]+(.*)$')
EMOJI_RE   = re.compile(
    r'^(?:[\U0001F000-\U0001FAFF←-⯿︀-️‍⃣]+[ \t]*)+')


def is_marker(s):
    return bool(s) and s[0] in MARKERS


def clean(s):
    return re.sub(r'[ \t]+', ' ', s).strip()


def parse_head(raw):
    """'1.2 🏢 Title — Subtitle' -> ('1.2', 'Title', 'Subtitle')"""
    head = LINK_RE.sub(r'\1', raw).strip()
    m = NUM_RE.match(head)
    cid = ""
    if m:
        cid, head = m.group(1), m.group(2).strip()
    head = EMOJI_RE.sub('', head).strip()
    parts = re.split(r'[ \t]+[—–][ \t]+', head, maxsplit=1)
    return cid, parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")


def grab(marker, lines):
    """Text following a 🎣/🎯/🎤/🌫️ marker, up to the next marker or break."""
    out, on = [], False
    for raw in lines:
        s = raw.strip()
        if on:
            if not s:
                break
            if is_marker(s) or s.startswith(("- ", "* ", "+ ", ">", "#", "```")):
                break
            out.append(s)
            continue
        if s.startswith(marker):
            on = True
            out.append(s[len(marker):].strip())
    return clean(" ".join(out))


def weather_text(line):
    """🌫️ Weather pivot (…): "the line" -> just the spoken line."""
    if not line:
        return ""
    m = re.search(r'["“](.+)["”][ \t]*$', line)
    return clean(m.group(1) if m else re.sub(r'^Weather pivot[^:]*:[ \t]*', '', line))


def parse_say(lines):
    """- **Name** [**PRON**] — gloss   (new)
       * [**PRON**] — Name (gloss)     (old)"""
    say = []
    for raw in lines:
        s = raw.strip()
        if not s.startswith(("- ", "* ")):
            continue
        s = s[2:].strip()
        # new order: name first, then pronunciation, then gloss
        m = re.match(r'\*\*(.+?)\*\*[ \t]*\[([^\]]+)\]'
                     r'(?:[ \t]*/[ \t]*\[([^\]]+)\])?[ \t]*[—–-][ \t]*(.*)$', s)
        if m:
            name = re.sub(r'\*', '', m.group(1)).strip()
            pron = re.sub(r'\*', '', m.group(2)).strip()
            if m.group(3):
                pron += " / " + re.sub(r'\*', '', m.group(3)).strip()
            gloss = re.sub(r'\*', '', m.group(4)).strip()
            say.append([name, pron, gloss])
            continue
        # old order: pronunciation first, then name, gloss in brackets
        m = re.match(r'\[([^\]]+)\][ \t]*[—–-][ \t]*(.+)$', s)
        if m:
            pron = re.sub(r'\*', '', m.group(1)).strip()
            tail = re.sub(r'\*', '', m.group(2)).strip()
            g = re.match(r'^(.*?)[ \t]*\((.+)\)[ \t]*$', tail)
            name, gloss = (g.group(1).strip(), g.group(2).strip()) if g else (tail, "")
            say.append([name, pron, gloss])
    return say


def parse_bullets(lines):
    """Top-level - / * list items, ignoring fenced code."""
    out, fence = [], False
    for raw in lines:
        s = raw.strip()
        if s.startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        if s.startswith(("- ", "* ")):
            out.append(clean(s[2:]))
    return out


def parse_craft(path):
    md = open(path, encoding="utf-8").read()
    # <callout>…</callout> is Craft chrome, not words to say.
    md = md.replace("<callout>", "").replace("</callout>", "")

    lines = md.split("\n")
    heads = []                       # (line index, heading text)
    stop = len(lines)
    for i, l in enumerate(lines):
        if THREADS_RE.match(l):
            stop = i
            break
        m = HEAD_RE.match(l)
        if m:
            heads.append((i, m.group(1)))
    heads = [h for h in heads if h[0] < stop]

    out = {}
    for n, (i, raw) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else stop
        cid, title, sub = parse_head(raw)
        if not title:
            continue
        body = lines[i + 1:end]

        # The 🗣️ list, and everything before it.
        cut = len(body)
        for j, l in enumerate(body):
            if "🗣" in l:
                cut = j
                break
        main, sayb = body[:cut], body[cut + 1:]

        bullets = parse_bullets(main)
        if not bullets:                       # old format: the 📖 story block
            story = grab("📖", main)
            if story:
                bullets = [clean(p) for p in re.split(r'\n[ \t]*\n', story) if p.strip()]

        out[title] = dict(
            craft_id = cid,
            sub      = sub,
            hook     = grab("🎣", main),
            bullets  = bullets,
            point    = grab("🎯", main),
            mic      = grab("🎤", main),
            weather  = weather_text(grab("🌫", body)),
            say      = parse_say(sayb),
            # 🧵 tags sit last in the current export, second in the old one.
            tags     = re.findall(r'#\w[\w-]*',
                                  "\n".join(l for l in body if l.strip().startswith("🧵"))),
        )
    return out


def read_app(path):
    js = '''
      global.window={};
      eval(require("fs").readFileSync(%s,"utf8"));
      console.log(JSON.stringify(window.__SCRIPT__));
    ''' % json.dumps(path)
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True,
                                     text=True, check=True).stdout)

def js_str(s):
    return json.dumps(s, ensure_ascii=False)

def emit(script):
    L = []
    L.append("// 1.0 Golden Circle Direct — on-mic script.")
    L.append("// GENERATED by build-script.py from RitchWiki/Tour Scripts/1.0 Golden Circle Direct.md")
    L.append("// Do not hand-edit. Edit Craft, then re-run the build.")
    L.append("window.__SCRIPT__ = {")
    L.append("title: %s," % js_str(script["title"]))
    L.append("intro: [")
    for i in script.get("intro", []):
        L.append("  %s," % js_str(i))
    L.append("],")
    L.append("sections: [")
    for sec in script["sections"]:
        L.append("{title:%s, kind:%s, blocks:[" % (js_str(sec["title"]), js_str(sec["kind"])))
        for b in sec["blocks"]:
            f = ['id:%s' % js_str(b["id"])]
            if b.get("emoji"): f.append("emoji:%s" % js_str(b["emoji"]))
            f.append("title:%s" % js_str(b["title"]))
            if b.get("sub"):  f.append("sub:%s" % js_str(b["sub"]))
            if b.get("cue"):  f.append("cue:%s" % js_str(b["cue"]))
            L.append("{" + ", ".join(f) + ",")
            if b.get("target"):
                t = b["target"]
                L.append(" target:{lat:%r, lon:%r, name:%s}," % (t["lat"], t["lon"], js_str(t["name"])))
            if b.get("hook"): L.append(" hook:%s," % js_str(b["hook"]))
            if b.get("bullets"):
                L.append(" bullets:[")
                for x in b["bullets"]: L.append("  %s," % js_str(x))
                L.append(" ],")
            if b.get("heads"):
                L.append(" heads:[")
                for h in b["heads"]:
                    L.append("  [%s,[%s]]," % (js_str(h[0]), ",".join(js_str(x) for x in h[1])))
                L.append(" ],")
            if b.get("pre"):
                L.append(" pre:[")
                for pr in b["pre"]:
                    L.append("  [%s,%s]," % (js_str(pr[0]), js_str(pr[1])))
                L.append(" ],")
            if b.get("point"):   L.append(" point:%s," % js_str(b["point"]))
            if b.get("mic"):     L.append(" mic:%s," % js_str(b["mic"]))
            if b.get("weather"): L.append(" weather:%s," % js_str(b["weather"]))
            if b.get("flag"):    L.append(" flag:%s," % js_str(b["flag"]))
            if b.get("say"):
                L.append(" say:[")
                for s in b["say"]:
                    L.append("  [%s,%s,%s]," % (js_str(s[0]), js_str(s[1]), js_str(s[2] if len(s) > 2 else "")))
                L.append(" ],")
            if b.get("tags"):    L.append(" tags:[%s]," % ",".join(js_str(t) for t in b["tags"]))
            L.append("},")
        L.append("]},")
    L.append("]};")
    return "\n".join(L) + "\n"

def main():
    craft = parse_craft(CRAFT)
    script = read_app(APP)
    changed, untouched = [], []
    seen = set()
    for sec in script["sections"]:
        for b in sec["blocks"]:
            c = craft.get(b["title"])
            if not c:
                untouched.append("%s %s" % (b["id"], b["title"]))
                continue
            seen.add(b["title"])
            before = json.dumps([b.get("bullets"), b.get("say"), b.get("hook"),
                                 b.get("point"), b.get("mic"), b.get("sub")], ensure_ascii=False)
            if c["sub"]:     b["sub"] = c["sub"]
            if c["hook"]:    b["hook"] = c["hook"]
            if c["bullets"] and b["title"] not in HAND_STRUCTURED:
                b["bullets"] = c["bullets"]
                b.pop("heads", None)
            if c["point"]:   b["point"] = c["point"]
            if c["mic"]:     b["mic"] = c["mic"]
            # Weather is a route fact: the app's own wins if it has one.
            if c["weather"] and not b.get("weather"):
                b["weather"] = c["weather"]
            if c["say"]:
                # Craft wins on wording, but never throw away a gloss the app
                # already had and Craft never wrote.
                old_gloss = {x[0].lower(): (x[2] if len(x) > 2 else "")
                             for x in (b.get("say") or [])}
                b["say"] = [[n, pr, g or old_gloss.get(n.lower(), "")]
                            for n, pr, g in c["say"]]
            if c["tags"]:    b["tags"] = c["tags"]
            after = json.dumps([b.get("bullets"), b.get("say"), b.get("hook"),
                                b.get("point"), b.get("mic"), b.get("sub")], ensure_ascii=False)
            if before != after:
                changed.append("%s %s" % (b["id"], b["title"]))
    missing = [t for t in craft if t not in seen]
    print("blocks parsed from Craft    : %d" % len(craft))
    print("blocks refreshed from Craft : %d" % len(changed))
    print("app-only blocks left alone  : %d  %s" % (len(untouched), "; ".join(untouched)))
    print("in Craft but not in the app : %d  %s" % (len(missing), "; ".join(missing)))
    if "--check" in sys.argv:
        return
    out = emit(script)
    open(APP, "w", encoding="utf-8").write(out)
    print("wrote %s (%d bytes)" % (APP, len(out)))

main()
