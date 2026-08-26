#!/usr/bin/env python3
"""
Take a tour from a Craft export to live in the app, in one command.

  python3 add-tour.py 7.0
  python3 add-tour.py 7.0 --check      # say what would happen, change nothing

It does, in order:
  1. finds the Craft export for that tour under ~/Documents/RitchWiki/Tour Scripts
  2. build-any.py   -> script-<id>.js     (content, verbatim from the document)
  3. build-route.py -> route-<id>.js + cues-<id>.js  (geocode + OSRM)
  4. flips ready:true in tours.js
  5. rewrites SHELL_FILES in sw.js from tours.js and bumps VERSION
  6. tells you what is left: the new strings need translating

Every step verifies before moving on, and nothing is flipped to ready until the
three data files exist and parse. A half-built tour in the picker is worse than
no tour in the picker.
"""
import json, os, re, subprocess, sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
CHECK = "--check" in sys.argv
args  = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args:
    sys.exit("usage: python3 add-tour.py <tour id, e.g. 7.0> [--check]")
TID = args[0]

SCRIPTS = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")
TOURS   = open("tours.js", encoding="utf-8").read()

entry = re.search(r'\{id:"%s".*?\}' % re.escape(TID), TOURS, re.S)
if not entry:
    sys.exit("%s is not in tours.js — add it there first (name + sub)." % TID)
name = re.search(r'name:"([^"]+)"', entry.group(0)).group(1)
print("tour %s — %s" % (TID, name))

# ---- 1. the Craft export ------------------------------------------------
cands = [f for f in os.listdir(SCRIPTS)
         if f.endswith(".md") and f.startswith(TID + " ")]
if not cands:
    sys.exit("no Craft export starting '%s ' in %s\n"
             "Export it from Craft first — this script never invents content."
             % (TID, SCRIPTS))
if len(cands) > 1:
    sys.exit("more than one export for %s: %s" % (TID, cands))
doc = cands[0][:-3]
size = os.path.getsize(os.path.join(SCRIPTS, cands[0]))
print("  export: %s (%d bytes)" % (cands[0], size))
if size < 20000:
    sys.exit("that export is only %d bytes — almost certainly a truncated pull. "
             "Re-export before building." % size)

if CHECK:
    print("  --check: would build script/route/cues, flip ready, bump sw.js")
    sys.exit(0)

def run(cmd):
    print("  $ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit((r.stdout or "") + (r.stderr or "") + "\nFAILED: " + " ".join(cmd))
    for line in (r.stdout or "").strip().splitlines():
        print("    " + line)

# ---- 2. content ---------------------------------------------------------
run(["python3", "build-any.py", doc, "script-%s.js" % TID])

# ---- 3. route + cues ----------------------------------------------------
run(["python3", "build-route.py", TID])

# ---- verify all three parse and agree -----------------------------------
probe = '''
global.window={};
require("./route-%s.js"); require("./script-%s.js"); require("./cues-%s.js");
const S=window.__SCRIPT__, R=window.__ROUTE__, C=window.__CUES__;
let b=0; S.sections.forEach(s=>b+=(s.blocks||[]).length);
console.log(JSON.stringify({title:S.title, sections:S.sections.length, blocks:b,
  cues:C.length, km:R.km, geometry:R.geometry.length}));
''' % (TID, TID, TID)
r = subprocess.run(["node", "-e", probe], capture_output=True, text=True)
if r.returncode:
    sys.exit(r.stderr + "\nthe three data files do not load — not flipping ready")
info = json.loads(r.stdout)
print("  built: %(sections)d sections, %(blocks)d blocks, %(cues)d cues, "
      "%(km)s km, %(geometry)d geometry points" % info)
if info["cues"] != info["blocks"]:
    sys.exit("cues (%d) and blocks (%d) disagree — a block would have no pin"
             % (info["cues"], info["blocks"]))

# ---- 4. flip ready ------------------------------------------------------
fixed = entry.group(0).replace("ready:false", "ready:true ")
TOURS = TOURS.replace(entry.group(0), fixed, 1)
open("tours.js", "w", encoding="utf-8").write(TOURS)
print("  tours.js: %s is ready" % TID)

# ---- 5. sw.js: shell list regenerated, never hand-kept -------------------
ready = re.findall(r'\{id:"([^"]+)",\s*ready:true', TOURS)
sw = open("sw.js", encoding="utf-8").read()
lines = []
for i in range(0, len(ready), 3):
    lines.append("  " + ", ".join(
        '"./route-%s.js", "./script-%s.js", "./cues-%s.js"' % (t, t, t)
        for t in ready[i:i+3]) + ",")
block = re.search(r'\n(  "\./route-[^\n]*\n(?:  "\./route-[^\n]*\n)*)', sw)
if not block:
    sys.exit("could not find the tour block in sw.js SHELL_FILES — fix by hand")
sw = sw.replace(block.group(1), "\n".join(lines) + "\n", 1)

ver = re.search(r'const VERSION = "gcd(\d+)-v(\d+)";', sw)
sw = sw.replace(ver.group(0), 'const VERSION = "gcd%d-v1";' % (int(ver.group(1)) + 1), 1)
open("sw.js", "w", encoding="utf-8").write(sw)
print("  sw.js: %d tours cached, VERSION -> gcd%d-v1"
      % (len(ready), int(ver.group(1)) + 1))

print("""
Built and wired. Still to do for %s:
  python3 i18n-strings.py     # re-extract; only genuinely new lines appear
  python3 i18n-chunks.py 3    # translate the new chunks, then
  python3 i18n-build.py       # validate + rebuild the 20 language packs
  python3 build-single.py     # refresh the one-file backup
then commit, push, and refresh the gist.""" % TID)
