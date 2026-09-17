#!/usr/bin/env python3
"""
_onecopy.py — one block, one entry.

  python3 _onecopy.py            # report only
  python3 _onecopy.py --write    # writes _blocks/blocks.json + dropped.md

Every script block currently exists once per tour that uses it. "Three Names to
Keep in Your Pocket" is six blocks — 1.1, 2.1, 3.1, 4.1, 9.1, 10.1 — and they
are the same block. This keeps ONE of each and records which tours used it.

THE RULE, one line: the fullest version wins.
Fullest = most characters across hook, point, mic, bullets, say. Where a copy
carries a line the winner doesn't, the line is kept rather than lost.

THE ONE EXCEPTION: `cue` stays per-tour. The road passes the same hill in both
directions, so "look left" on 9.0 and "look right" on 10.0 are both correct.

Nothing here touches script-*.js. This writes the list.
"""
import json, os, re, sys, collections, subprocess, unicodedata

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WRITE = "--write" in sys.argv
OUT = "_blocks"
READY = [t for t, r in re.findall(r'\{id:"([^"]+)".*?ready:\s*(true|false)',
         open("tours.js", encoding="utf-8").read(), re.S) if r == "true"]

NODE = r'''
const out={};
for(const id of %s){ global.window={}; require("./script-"+id+".js");
  const S=global.window.__SCRIPT__;
  out[id]=S.sections.map(s=>({title:s.title,kind:s.kind,blocks:s.blocks}));
}
process.stdout.write(JSON.stringify(out));
'''

def size(b):
    n = 0
    for f in ("hook", "point", "mic", "weather", "sub"):
        n += len(b.get(f) or "")
    for f in ("bullets", "say"):
        n += len(json.dumps(b.get(f) or [], ensure_ascii=False))
    return n


def main():
    src = json.loads(subprocess.run(["node", "-e", NODE % json.dumps(READY)],
                                    capture_output=True, text=True, check=True).stdout)

    # 🎧 Music Leg appears TWICE inside every tour and the two are different
    # music. Keying on title alone collapses them — that is the bug that made
    # the map dot run backwards (HANDOVER, 5 Sep). Key on title + which
    # occurrence it is within its own tour, exactly like the cue builder does.
    # Tour 7.0 writes its block titles WITHOUT the leading emoji that every
    # other tour uses — "Hveragerði" against "🌋 Hveragerði" — so matching on
    # the raw title left 29 duplicates standing. Match on the words.
    def subject_of(title):
        t = re.sub(r"^\s*\d+(\.\d+)*\s*", "", title)
        t = "".join(ch for ch in t
                    if not unicodedata.category(ch).startswith("So")
                    and ch not in "️‍")
        return re.sub(r"\s+", " ", t).strip().lower()

    subjects = collections.OrderedDict()
    for tid in READY:
        nth = collections.Counter()
        for sec in src[tid]:
            for b in sec["blocks"]:
                s = subject_of(b["title"])
                nth[s] += 1
                key = s if nth[s] == 1 else "%s #%d" % (s, nth[s])
                subjects.setdefault(key, []).append(
                    {"tour": tid, "sec": sec["title"], "kind": sec["kind"], "b": b})

    blocks, dropped = [], []
    for title, insts in subjects.items():
        win = max(insts, key=lambda i: size(i["b"]))
        b = json.loads(json.dumps(win["b"]))          # deep copy, never mutate source

        # keep any line a loser had that the winner didn't
        rescued = []
        for f in ("bullets",):
            have = {json.dumps(x, ensure_ascii=False) for x in (b.get(f) or [])}
            for i in insts:
                for x in (i["b"].get(f) or []):
                    k = json.dumps(x, ensure_ascii=False)
                    if k not in have:
                        have.add(k); b.setdefault(f, []).append(x)
                        rescued.append("%s: %s" % (i["tour"], (x if isinstance(x, str) else k)[:90]))
        # say: one row per name, fullest blurb
        if any(i["b"].get("say") for i in insts):
            by, order = {}, []
            for i in insts:
                for row in (i["b"].get("say") or []):
                    nm = row[0]
                    if nm not in by:
                        by[nm] = list(row); order.append(nm)
                    elif len(json.dumps(row, ensure_ascii=False)) > len(json.dumps(by[nm], ensure_ascii=False)):
                        by[nm] = list(row)
            b["say"] = [by[n] for n in order]

        # The cue is the only field that is legitimately different per tour —
        # the road passes the same hill in both directions. Keep the winning
        # tour's wording as the default so an exported block is never cue-less,
        # and carry the alternatives alongside it so the right one can be
        # chosen when the block is placed on a tour that drives the other way.
        cues = {i["tour"]: i["b"]["cue"] for i in insts if i["b"].get("cue")}
        same_cue = len(set(cues.values())) <= 1
        if cues:
            b["cue"] = cues.get(win["tour"]) or next(iter(cues.values()))
        else:
            b.pop("cue", None)

        # what the losing copies said that the winner now overrides
        for f in ("hook", "point", "mic", "weather", "sub"):
            others = {i["tour"]: i["b"].get(f) for i in insts
                      if i["b"].get(f) and i["b"].get(f) != b.get(f)}
            if others:
                dropped.append({"title": win["b"]["title"], "field": f, "kept_from": win["tour"],
                                "kept": b.get(f), "dropped": others})

        blocks.append({
            "title": win["b"]["title"],
            "subject": title,
            "usedBy": [i["tour"] for i in insts],
            "section": win["sec"], "kind": win["kind"], "from": win["tour"],
            "block": b,
            "cuePerTour": None if same_cue else cues,
            "rescued": rescued,
        })

    dup = [b for b in blocks if len(b["usedBy"]) > 1]
    print("BLOCKS   %d entries, from %d copies"
          % (len(blocks), sum(len(b["usedBy"]) for b in blocks)))
    print("         %d used by more than one tour" % len(dup))
    print("         %d deleted duplicates"
          % (sum(len(b["usedBy"]) for b in blocks) - len(blocks)))
    print()
    print("KEPT PER-TOUR   %d blocks whose look-here line differs by direction"
          % len([b for b in blocks if b["cuePerTour"]]))
    print("RESCUED LINES   %d bullets that only existed on one tour"
          % sum(len(b["rescued"]) for b in blocks))
    print("OVERRIDDEN      %d wordings on %d blocks — listed in %s/dropped.md"
          % (len(dropped), len({d['title'] for d in dropped}), OUT))
    print()
    top = sorted(dup, key=lambda b: -len(b["usedBy"]))[:8]
    print("most-copied blocks:")
    for b in top:
        print("  %-2d× %s" % (len(b["usedBy"]), b["title"]))

    if not WRITE:
        print("\n(dry run — nothing written. re-run with --write)")
        return

    os.makedirs(OUT, exist_ok=True)
    json.dump(blocks, open(OUT + "/blocks.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    with open(OUT + "/dropped.md", "w", encoding="utf-8") as fh:
        fh.write("# What the duplicates said, that the kept copy doesn't\n\n")
        fh.write("One block per subject now. Where the copies were worded differently, "
                 "the fullest one was kept. This is everything the other copies said, "
                 "so nothing disappears without you seeing it. Nothing here is lost from "
                 "disk — the old scripts are untouched.\n\n---\n\n")
        for t in dict.fromkeys(d["title"] for d in dropped):
            fh.write("## %s\n\n" % t)
            for d in [x for x in dropped if x["title"] == t]:
                fh.write("**%s** — keeping %s:\n\n> %s\n\n" % (d["field"], d["kept_from"], d["kept"]))
                for tour, val in d["dropped"].items():
                    fh.write("- ~~%s~~ — %s\n" % (tour, val))
                fh.write("\n")
            fh.write("---\n\n")
    print("\nwrote %s/blocks.json (%d blocks) and %s/dropped.md" % (OUT, len(blocks), OUT))


if __name__ == "__main__":
    main()
