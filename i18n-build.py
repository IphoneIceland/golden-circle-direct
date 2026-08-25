#!/usr/bin/env python3
"""
Validate the translated chunks and build one script file per language.

  python3 i18n-build.py           # validate + write i18n/tours/<lang>.js
  python3 i18n-build.py --check   # validate only, write nothing

Several translation agents shared a scratch directory and reported the input
being swapped underneath them mid-run. They caught it and re-read from source,
but trust is not a verification strategy: every id in every output is checked
against the chunk it claims to come from, in order, before anything is written.
"""
import json, os, re, sys, hashlib

os.chdir(os.path.dirname(os.path.abspath(__file__)))
CHECK = "--check" in sys.argv
LANGS = ["de","fr","es","it","nl","pt","pl","da","sv","no",
         "fi","is","zh","ja","ko","ru","ar","hi","tr","he"]
CHUNKS = [1, 2, 3]

corpus = json.load(open("_tr/corpus.json", encoding="utf-8"))
EN = {e["id"]: e["en"] for e in corpus}
expect = {}
for n in CHUNKS:
    expect[n] = [e["id"] for e in
                 json.load(open("_tr/chunks/chunk-%d.json" % n, encoding="utf-8"))]

ICELANDIC = "ÞþÐðÆæÖöÁáÍíÓóÚúÝýÉé"
NUM = re.compile(r"\d")

ok_all, report = True, []
built = {}

for lang in LANGS:
    tr, problems = {}, []
    for n in CHUNKS:
        path = "_tr/out/%s-%d.jsonl" % (lang, n)
        if not os.path.isfile(path):
            problems.append("chunk %d missing" % n); ok_all = False; continue
        rows = []
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as ex:
                problems.append("chunk %d line %d is not JSON: %s" % (n, i, ex))
        got = [r.get("id") for r in rows]
        want = expect[n]
        if got != want:
            missing = [i for i in want if i not in set(got)]
            extra = [i for i in got if i not in set(want)]
            problems.append("chunk %d id mismatch: %d lines vs %d expected, "
                            "%d missing, %d not from this chunk"
                            % (n, len(got), len(want), len(missing), len(extra)))
        for r in rows:
            t = (r.get("t") or "").strip()
            if not t:
                problems.append("chunk %d: %s is empty" % (n, r.get("id")))
            if r.get("id") in EN:
                tr[r["id"]] = r["t"]

    missing = [i for i in EN if i not in tr]
    if missing:
        problems.append("%d strings never translated" % len(missing))

    # Markup parity: a dropped ** turns half a paragraph bold on the phone.
    bad_bold = [i for i in tr if EN[i].count("**") != tr[i].count("**")]
    # A line that had numbers and now has none has lost a fact, not a comma.
    lost_nums = [i for i in tr
                 if NUM.search(EN[i]) and not NUM.search(tr[i])]
    # Untranslated leftovers: identical to the English AND long enough to matter.
    identical = [i for i in tr
                 if tr[i] == EN[i] and len(EN[i].split()) > 6]

    if problems:
        ok_all = False
    report.append({"lang": lang, "strings": len(tr), "problems": problems,
                   "bold": len(bad_bold), "lost_numbers": len(lost_nums),
                   "identical_to_english": len(identical)})
    built[lang] = tr

for r in report:
    flag = "FAIL" if r["problems"] else "ok  "
    print("%s %-3s %3d/%d strings | bold %d | numbers lost %d | untranslated %d"
          % (flag, r["lang"], r["strings"], len(EN), r["bold"],
             r["lost_numbers"], r["identical_to_english"]))
    for p in r["problems"]:
        print("       %s" % p)

if CHECK:
    sys.exit(0 if ok_all else 1)
if not ok_all:
    sys.exit("refusing to build — fix the failures above first")

def h32(s):
    """FNV-1a 32-bit over UTF-8 — the browser computes this with Math.imul."""
    x = 0x811c9dc5
    for byte in s.encode("utf-8"):
        x ^= byte
        x = (x * 0x01000193) & 0xFFFFFFFF
    return "%08x" % x

# 864 strings in a 32-bit space collide with probability ~1 in 11,000. Cheap to
# check, and a silent collision would put one block's words on another's line.
keys = {}
for i, en in EN.items():
    k = h32(en)
    if k in keys and keys[k] != en:
        sys.exit("hash collision between two different strings — widen the hash")
    keys[k] = en

os.makedirs("i18n/tours", exist_ok=True)
for lang, tr in built.items():
    tr = {h32(EN[i]): t for i, t in tr.items()}
    body = json.dumps(tr, ensure_ascii=False, separators=(",", ":"))
    js = ("window.__TR__ = window.__TR__ || {};\n"
          "window.__TR__.%s = %s;\n" % (lang, body))
    open("i18n/tours/%s.js" % lang, "w", encoding="utf-8").write(js)
    print("wrote i18n/tours/%s.js  %d strings  %d KB"
          % (lang, len(tr), round(len(js.encode()) / 1024)))
