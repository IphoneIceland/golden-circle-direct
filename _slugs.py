#!/usr/bin/env python3
"""
_slugs.py — a short, permanent name for every block.

  python3 _slugs.py            # print the list
  python3 _slugs.py --write    # writes _blocks/slugs.json

The number in a Craft heading is a POSITION — `1.1` means "first block of tour
1.0" — so reordering the stops means renumbering, and renumbering is what broke
the Threads index twice. A slug is a NAME. It does not move.

  > ### 1.1 🧍 Jóhannes Sveinsson Kjarval
  > ### [kjarval] 🧍 Jóhannes Sveinsson Kjarval

RULES
  * lower case, a-z 0-9 and hyphens, nothing else
  * Icelandic letters transliterated the way the app already does it
    (þ→th, ð→d, æ→ae, ö→o) so a slug can be typed on any keyboard
  * emoji and the leading number are stripped
  * long titles cut at the first — or & , keeping the part that names the thing
  * a collision gets a numeric suffix, and every collision is printed loudly
"""
import json, os, re, sys, unicodedata, collections, subprocess

os.chdir(os.path.dirname(os.path.abspath(__file__)))
WRITE = "--write" in sys.argv

MAP = str.maketrans({"þ": "th", "Þ": "th", "ð": "d", "Ð": "d", "æ": "ae", "Æ": "ae",
                     "ö": "o", "Ö": "o", "ø": "o", "å": "a"})

STOP = {"the", "a", "an", "of", "and", "to", "in", "at", "on", "&"}


def slug(title, keep=3):
    t = title
    t = re.sub(r"^\s*\d+(\.\d+)*\s*", "", t)            # drop a leading 1.1
    t = "".join(c for c in t if not unicodedata.category(c).startswith("So"))
    t = t.split("—")[0].split("–")[0].split(":")[0]      # keep the naming half
    t = t.translate(MAP)
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = re.sub(r"[^A-Za-z0-9]+", " ", t).strip().lower()
    words = [w for w in t.split() if w not in STOP] or t.split()
    return "-".join(words[:keep])


def main():
    book = json.load(open("_blocks/blocks.json", encoding="utf-8"))

    # first pass at 3 words; anything that collides gets more words before it
    # gets a number, because "kjarval-2" tells you nothing and "sog-river" does
    out, used = [], {}
    for e in book:
        s = slug(e["title"])
        if s in used:
            for k in (4, 5, 6):
                longer = slug(e["title"], k)
                if longer not in used:
                    s = longer
                    break
            else:
                n = 2
                while "%s-%d" % (s, n) in used:
                    n += 1
                s = "%s-%d" % (s, n)
        used[s] = e["title"]
        out.append({"slug": s, "title": e["title"], "usedBy": e["usedBy"]})

    clashes = [o for o in out if re.search(r"-\d$", o["slug"])]
    empty = [o for o in out if not o["slug"]]

    w = max(len(o["slug"]) for o in out)
    for o in out:
        print("  %-*s  %s   %s" % (w, o["slug"], o["title"],
                                   "×%d" % len(o["usedBy"]) if len(o["usedBy"]) > 1 else ""))
    print("\n%d slugs, %d unique" % (len(out), len({o["slug"] for o in out})))
    if empty:
        print("EMPTY SLUG on: " + ", ".join(o["title"] for o in empty))
    if clashes:
        print("NEEDED A NUMBER (look at these, they are the ugly ones):")
        for o in clashes:
            print("   %-24s %s" % (o["slug"], o["title"]))

    if WRITE:
        json.dump(out, open("_blocks/slugs.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\nwrote _blocks/slugs.json")


if __name__ == "__main__":
    main()
