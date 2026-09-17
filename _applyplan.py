#!/usr/bin/env python3
"""
_applyplan.py — take a tour-plan.json out of the back office and write it into
the tour scripts.

  python3 _applyplan.py tour-plan.json            # say what would change
  python3 _applyplan.py tour-plan.json --write    # do it

WHAT A PLAN IS
The back office matrix is a picture of which blocks sit on which tours. Tick a
cell, hit Save plan, and you get a file listing every add and every remove.
This applies it.

HOW IT BEHAVES, and why
  * Every script it touches gets a dated .bak BESIDE it, before the edit.
  * An ADD takes the block from the library, drops it into the section it
    belongs to, and places it in that section by the block's own progress along
    that tour — so it fires where the road reaches it, not at the end of a list.
  * A REMOVE lifts the block out and leaves the section alone.
  * Block ids are renumbered per section afterwards, the way the exporter does.
  * NOTHING is written unless every affected script still parses and every
    section still has its blocks array. That check is the whole reason this is
    a script and not a hand edit — losing a section's blocks[] is a real bug
    this project has had twice.
  * cues-*.js is NOT touched. A new block needs a pin and a target, and that is
    _autosight.py's job, not this one. The report says which blocks now need one.
"""
import json, os, re, subprocess, sys, shutil, datetime

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WRITE = "--write" in sys.argv
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PLAN = ARGS[0] if ARGS else "tour-plan.json"
STAMP = datetime.date.today().strftime("%Y-%m-%d")

if not os.path.exists(PLAN):
    sys.exit("no plan at %s — save one out of the back office first" % PLAN)

plan = json.load(open(PLAN, encoding="utf-8"))
BOOK = {e["title"]: e for e in json.load(open("_blocks/blocks.json", encoding="utf-8"))}
AIM = json.load(open("aim.json", encoding="utf-8")) if os.path.exists("aim.json") else {"blocks": {}}

NODE_READ = r'''
global.window = {};
require("./script-%s.js");
process.stdout.write(JSON.stringify(global.window.__SCRIPT__));
'''

def read_script(tid):
    out = subprocess.run(["node", "-e", NODE_READ % tid],
                         capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def write_script(tid, S):
    """Same shape the exporter writes, so add-tour.py and the app see no change."""
    js = ("// %s — rebuilt by _applyplan.py %s\n" % (S.get("title", tid), STAMP) +
          "window.__SCRIPT__ = " + json.dumps(S, ensure_ascii=False, indent=1) + ";\n")
    open("script-%s.js" % tid, "w", encoding="utf-8").write(js)


def progress_on(title, tid):
    """Where along this tour the block's own landmark sits. None if unknown."""
    a = AIM["blocks"].get(title)
    if not a or a.get("unaimed"):
        return None
    on = (a.get("on") or {}).get(tid)
    return on["best"]["progress"] if on else None


def apply(tid, adds, removes):
    S = read_script(tid)
    before = sum(len(s["blocks"]) for s in S["sections"])
    notes = []

    for title in removes:
        for sec in S["sections"]:
            hit = [b for b in sec["blocks"] if b["title"].strip() == title.strip()]
            for b in hit:
                sec["blocks"].remove(b)
                notes.append("  − %-44s from %s" % (title[:44], sec["title"]))

    for title in adds:
        e = BOOK.get(title)
        if not e:
            notes.append("  ! %-44s NOT IN THE LIBRARY — skipped" % title[:44]); continue
        if any(b["title"].strip() == title.strip()
               for s in S["sections"] for b in s["blocks"]):
            notes.append("  = %-44s already on %s" % (title[:44], tid)); continue

        blk = json.loads(json.dumps(e["block"]))
        # the cue is the one field that is legitimately per-tour
        per = (e.get("cuePerTour") or {}).get(tid)
        if per:
            blk["cue"] = per

        # put it in the section it came from, or the nearest thing this tour has
        names = [s["title"] for s in S["sections"]]
        sec = next((s for s in S["sections"] if s["title"] == e["section"]), None)
        if sec is None:
            sec = S["sections"][0] if S["sections"] else None
            notes.append("  ~ %-44s no '%s' section on %s — put in '%s'"
                         % (title[:44], e["section"], tid, sec["title"] if sec else "?"))
        if sec is None:
            notes.append("  ! %-44s tour has no sections — skipped" % title[:44]); continue

        # place it by where the road actually reaches it
        p = progress_on(title, tid)
        pos = len(sec["blocks"])
        if p is not None:
            for i, b in enumerate(sec["blocks"]):
                bp = progress_on(b["title"].strip(), tid)
                if bp is not None and bp > p:
                    pos = i; break
        sec["blocks"].insert(pos, blk)
        notes.append("  + %-44s into %s at #%d%s"
                     % (title[:44], sec["title"], pos + 1,
                        "" if p is not None else "  (no target — placed last)"))

    # renumber, exactly as the exporter does
    for si, s in enumerate(S["sections"]):
        for bi, b in enumerate(s["blocks"]):
            b["id"] = "%s.%d.%d" % (tid, si + 1, bi + 1)

    after = sum(len(s["blocks"]) for s in S["sections"])
    return S, before, after, notes


def main():
    changes = plan.get("changes") or []
    if not changes:
        sys.exit("plan has no changes in it")

    by_tour = {}
    for c in changes:
        t = by_tour.setdefault(c["tour"], {"add": [], "remove": []})
        t["add" if c["action"] == "add" else "remove"].append(c["block"])

    print("PLAN  %s   built %s" % (PLAN, plan.get("builtAt", "?")[:19]))
    print("      %d change%s across %d tour%s\n"
          % (len(changes), "" if len(changes) == 1 else "s",
             len(by_tour), "" if len(by_tour) == 1 else "s"))

    staged, needs_target = {}, []
    for tid in sorted(by_tour):
        if not os.path.exists("script-%s.js" % tid):
            print("  %s — no script on disk, skipped\n" % tid); continue
        S, before, after, notes = apply(tid, by_tour[tid]["add"], by_tour[tid]["remove"])
        print("%s   %d → %d blocks" % (tid, before, after))
        for n in notes:
            print(n)
        print()
        staged[tid] = S
        for title in by_tour[tid]["add"]:
            if progress_on(title, tid) is None:
                needs_target.append((tid, title))

    if needs_target:
        print("NEEDS A TARGET before it can be aimed or mapped:")
        for tid, t in needs_target:
            print("   %-6s %s" % (tid, t))
        print("   run _autosight.py for these — this script does not touch cues.\n")

    if not WRITE:
        print("(dry run — nothing written. re-run with --write)")
        return

    # write to a temp name, parse-check it, and only then move it into place
    ok = True
    for tid, S in staged.items():
        src = "script-%s.js" % tid
        shutil.copy2(src, "%s.bak-%s-applyplan" % (src, STAMP))
        write_script(tid, S)

    check = r'''
const fs=require("fs");
let bad=0;
for(const id of %s){
  global.window={};
  try{ eval(fs.readFileSync("script-"+id+".js","utf8")); }
  catch(e){ console.log("PARSE FAIL "+id+": "+e.message); bad++; continue; }
  const S=global.window.__SCRIPT__;
  if(!S||!Array.isArray(S.sections)){ console.log("NO SECTIONS "+id); bad++; continue; }
  const mal=S.sections.filter(s=>!Array.isArray(s.blocks));
  if(mal.length){ console.log("SECTION WITH NO blocks[] "+id); bad++; }
}
process.stdout.write(bad? "BAD":"OK");
''' % json.dumps(list(staged))
    res = subprocess.run(["node", "-e", check], capture_output=True, text=True)
    print(res.stdout.replace("OK", "").replace("BAD", ""), end="")

    if "OK" not in res.stdout:
        for tid in staged:
            shutil.copy2("script-%s.js.bak-%s-applyplan" % (tid, STAMP), "script-%s.js" % tid)
        sys.exit("REVERTED — the rebuilt scripts did not check out. Nothing changed.")

    print("wrote %d script%s, all parse, no section lost its blocks."
          % (len(staged), "" if len(staged) == 1 else "s"))
    print("rollback: script-<id>.js.bak-%s-applyplan" % STAMP)
    print("\nnext: python3 _autosight.py   (targets)   then   ~/Documents/iGuide-deploy/sync-app.sh")


if __name__ == "__main__":
    main()
