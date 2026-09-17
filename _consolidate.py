#!/usr/bin/env python3
"""
_consolidate.py — one block per subject, instead of the same block typed out
four times under four different numbers.

  python3 _consolidate.py            # analyse only, writes nothing but reports
  python3 _consolidate.py --write    # writes _blocks/library.json + conflicts.md

WHAT THIS IS FOR
Geysir is written out four times as 1.x, 2.x, 3.x and 4.x. The facts are the
same; the copies have drifted in wording. Correct a date and you have to do it
four times, and if you miss one the tours disagree on the mic.

WHAT IT DOES NOT TOUCH
Nothing shipped. `script-<id>.js` keeps its shape and its ids, because
`cues-<id>.js` is keyed on those ids and a pin is genuinely per-tour — the same
mountain is on your left going out and your right coming home. This builds the
SOURCE the scripts get stamped from. One place to edit, ten files out.

Translations are safe: i18n keys on a hash of the English text, so identical
lines already share one translation. Consolidating can only reduce the corpus.

HOW A FIELD IS CLASSIFIED across the copies of one subject
  identical   every copy agrees                      -> take it
  reordered   same lines, different order             -> take the commonest order
  superset    one copy contains all the others' lines -> take the fullest
  conflict    genuinely different words               -> RITCHIE'S CALL, listed
"""
import json, os, re, subprocess, sys, collections, hashlib

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WRITE = "--write" in sys.argv
OUT = "_blocks"

TOURS = [m for m in re.findall(r'\{id:"([^"]+)".*?ready:\s*(true|false)',
         open("tours.js", encoding="utf-8").read(), re.S)]
READY = [t for t, r in TOURS if r == "true"]

# Fields that carry Ritchie's words. `weather` is in here too — it is prose.
PROSE = ["cue", "hook", "point", "mic", "weather", "sub"]
LISTS = ["bullets", "say", "tags"]

NODE = r'''
const out={};
for(const id of %s){
  global.window={};
  require("./script-"+id+".js");
  const S=global.window.__SCRIPT__;
  out[id]={title:S.title, sections:S.sections.map(s=>({
    title:s.title, kind:s.kind,
    blocks:s.blocks.map(b=>b)
  }))};
}
process.stdout.write(JSON.stringify(out));
'''

def load():
    js = NODE % json.dumps(READY)
    raw = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True)
    return json.loads(raw.stdout)


def norm(s):
    """Whitespace-insensitive compare. Never used to CHANGE text, only to match."""
    return re.sub(r"\s+", " ", s).strip() if isinstance(s, str) else s


def classify(values, field=None):
    """values: list of (tour, value). Returns (verdict, chosen, detail)."""
    present = [(t, v) for t, v in values if v not in (None, "", [])]

    # `say` is [name, pronunciation, blurb] triples. Two tours giving the same
    # name a differently-worded blurb is ONE pronunciation, not two — union it
    # naively and Geysir ends up listed four times. Key on the name, keep the
    # fullest blurb, and only call it a conflict if the PRONUNCIATION disagrees.
    if field == "say" and present and isinstance(present[0][1], list):
        if len({json.dumps(v, ensure_ascii=False) for _, v in present}) == 1:
            return "identical", present[0][1], ""
        by_name, order, prons = {}, [], collections.defaultdict(set)
        for t, v in present:
            for row in v:
                if not isinstance(row, list) or not row:
                    return "conflict", None, "unexpected shape"
                nm = row[0]
                if nm not in by_name:
                    by_name[nm] = list(row); order.append(nm)
                elif len(json.dumps(row, ensure_ascii=False)) > \
                     len(json.dumps(by_name[nm], ensure_ascii=False)):
                    by_name[nm] = list(row)
                if len(row) > 1:
                    prons[nm].add(norm(row[1]))
        clash = [n for n, p in prons.items() if len(p) > 1]
        if clash:
            return "conflict", None, "pronunciation disagrees: " + ", ".join(clash)
        return ("say-merged", [by_name[n] for n in order],
                "%d names, fullest blurb kept for each" % len(order))

    if not present:
        return "absent", None, ""
    seen = {}
    for t, v in present:
        seen.setdefault(json.dumps(v, ensure_ascii=False, sort_keys=True), []).append(t)
    if len(seen) == 1:
        return "identical", present[0][1], ""

    first = present[0][1]
    if isinstance(first, list):
        # same lines, different order?
        sets = [frozenset(json.dumps(x, ensure_ascii=False) for x in v) for _, v in present]
        if len(set(sets)) == 1:
            order = collections.Counter(
                json.dumps(v, ensure_ascii=False) for _, v in present).most_common(1)[0][0]
            return "reordered", json.loads(order), "%d orderings" % len(seen)
        # one copy that contains every other copy's lines?
        big = max(present, key=lambda p: len(sets[present.index(p)]))
        bigset = frozenset(json.dumps(x, ensure_ascii=False) for x in big[1])
        if all(s <= bigset for s in sets):
            return "superset", big[1], "fullest is %s (%d lines)" % (big[0], len(big[1]))

        # Partial overlap: every copy shares most lines, but each carries one or
        # two the others don't. Nothing is contradicted, so nothing has to be
        # thrown away — the union keeps every line anyone ever wrote, in the
        # fullest copy's order, with the strays appended in tour order.
        union, seen_lines = list(big[1]), {json.dumps(x, ensure_ascii=False) for x in big[1]}
        added = []
        for t, v in present:
            for x in v:
                k = json.dumps(x, ensure_ascii=False)
                if k not in seen_lines:
                    seen_lines.add(k); union.append(x); added.append(t)
        return ("union", union,
                "%d lines: %s had %d, +%d only on %s"
                % (len(union), big[0], len(big[1]), len(added),
                   "/".join(sorted(set(added)))))

    # prose: identical once whitespace is normalised?
    if len({norm(v) for _, v in present}) == 1:
        return "identical", present[0][1], "whitespace only"
    return "conflict", None, "%d wordings" % len(seen)


def main():
    lib_src = load()

    # every instance of every subject, in tour order
    subjects = collections.OrderedDict()
    for tid in READY:
        for si, sec in enumerate(lib_src[tid]["sections"]):
            for bi, b in enumerate(sec["blocks"]):
                key = b["title"].strip()
                subjects.setdefault(key, []).append(
                    {"tour": tid, "sec": sec["title"], "kind": sec["kind"], "b": b})

    fields = PROSE + LISTS
    library, conflicts = {}, []
    stats = collections.Counter()

    for title, insts in subjects.items():
        stats["subjects"] += 1
        stats["instances"] += len(insts)
        if len(insts) == 1:
            stats["single"] += 1
        canon, per_tour, verdicts = {}, {}, {}
        for f in fields:
            verdict, chosen, detail = classify([(i["tour"], i["b"].get(f)) for i in insts], f)
            verdicts[f] = verdict
            if verdict in ("identical", "reordered", "superset", "union", "say-merged"):
                if chosen is not None:
                    canon[f] = chosen
            elif verdict == "conflict":
                # cue is legitimately per-tour: the road runs both ways past the
                # same hill, so left and right are both correct. Keep them all.
                if f == "cue":
                    for i in insts:
                        if i["b"].get(f):
                            per_tour.setdefault(i["tour"], {})[f] = i["b"][f]
                    stats["cue-overrides"] += 1
                else:
                    conflicts.append({
                        "title": title, "field": f, "copies": len(insts),
                        "detail": detail,
                        "versions": [{"tour": i["tour"], "value": i["b"].get(f)} for i in insts],
                    })
                    stats["conflicts"] += 1
            if len(insts) > 1 and verdict in ("reordered", "superset", "union", "say-merged", "conflict"):
                stats["drift:" + verdict] += 1

        library[title] = {
            "copies": [i["tour"] for i in insts],
            "sections": sorted({i["sec"] for i in insts}),
            "canonical": canon,
            "perTour": per_tour,
            "verdicts": verdicts,
        }

    # ── what it would save ────────────────────────────────────────────────
    strings_now = sum(
        len([1 for f in PROSE if i["b"].get(f)]) +
        sum(len(i["b"].get(f) or []) for f in ("bullets",))
        for insts in subjects.values() for i in insts)
    uniq_now = len({json.dumps(i["b"].get(f), ensure_ascii=False)
                    for insts in subjects.values() for i in insts
                    for f in PROSE if i["b"].get(f)})

    print("SUBJECTS  %d distinct, written out %d times"
          % (stats["subjects"], stats["instances"]))
    print("          %d appear on only one tour" % stats["single"])
    print("          %d redundant copies"
          % (stats["instances"] - stats["subjects"]))
    print()
    print("DRIFT, on the %d shared subjects:" % (stats["subjects"] - stats["single"]))
    print("  same lines, different order   %3d fields" % stats["drift:reordered"])
    print("  one copy is the fullest       %3d fields" % stats["drift:superset"])
    print("  overlapping, merged by union  %3d fields" % stats["drift:union"])
    print("  pronunciations merged by name %3d fields" % stats["drift:say-merged"])
    print("  genuinely different wording   %3d fields" % stats["drift:conflict"])
    print()
    print("AUTO-RESOLVED       %d fields" % (stats["drift:reordered"] + stats["drift:superset"]
                                             + stats["drift:union"] + stats["drift:say-merged"]))
    print("KEPT AS PER-TOUR    %d cue lines (road runs both ways)" % stats["cue-overrides"])
    print("NEEDS RITCHIE       %d fields, listed in %s/conflicts.md" % (stats["conflicts"], OUT))
    print()
    print("TRANSLATION: %d prose strings on disk, %d distinct — "
          "every needless reword costs 20 translations." % (strings_now, uniq_now))

    if not WRITE:
        print("\n(dry run — nothing written. re-run with --write)")
        return

    os.makedirs(OUT, exist_ok=True)
    with open(OUT + "/library.json", "w", encoding="utf-8") as fh:
        json.dump(library, fh, ensure_ascii=False, indent=1)

    with open(OUT + "/conflicts.md", "w", encoding="utf-8") as fh:
        fh.write("# Same block, different words — your call\n\n")
        fh.write("Each of these is one subject written out more than once, where the "
                 "copies say the same thing in different words. Neither is wrong, so "
                 "picking one is a voice decision, not a mechanical one. Pick a tour's "
                 "version per row and I'll make it canonical everywhere.\n\n")
        fh.write("Cue lines are NOT in here — the road runs past the same hill in both "
                 "directions, so left on one tour and right on another are both true. "
                 "Those stay per-tour on purpose.\n\n---\n\n")
        by_title = collections.defaultdict(list)
        for c in conflicts:
            by_title[c["title"]].append(c)
        for title, cs in by_title.items():
            fh.write("## %s  · %d copies\n\n" % (title, cs[0]["copies"]))
            for c in cs:
                fh.write("**`%s`** — %s\n\n" % (c["field"], c["detail"]))
                for v in c["versions"]:
                    val = v["value"]
                    if isinstance(val, list):
                        val = "\n".join("  - " + json.dumps(x, ensure_ascii=False)
                                        if not isinstance(x, str) else "  - " + x for x in val)
                        fh.write("- **%s**\n%s\n\n" % (v["tour"], val))
                    else:
                        fh.write("- **%s** — %s\n" % (v["tour"], val))
                fh.write("\n")
            fh.write("---\n\n")
    print("wrote %s/library.json (%d subjects) and %s/conflicts.md"
          % (OUT, len(library), OUT))


if __name__ == "__main__":
    main()
