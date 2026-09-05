#!/usr/bin/env python3
"""Schema survey across every ready tour: what is missing, everywhere.

Ritchie: "fix everything please including back office.. everything should match."
This is the list of what "everything" actually is.
"""
import json, os, re, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
tours = re.findall(r'\{id:"([^"]+)"[^}]*?ready:\s*true',
                   open(os.path.join(HERE, "tours.js"), encoding="utf-8").read())

print("%-6s %6s %7s %6s %5s %6s %7s %8s %7s" %
      ("tour", "blocks", "declared", "hooks", "wx", "cues", "sight", "threads", "live"))
print("-" * 74)
rows = []
for t in tours:
    sc = open(os.path.join(HERE, "script-%s.js" % t), encoding="utf-8").read()
    n = len(re.findall(r'\{id:"%s\.\d+\.\d+",' % re.escape(t), sc))
    music = len(re.findall(r'title:"[^"]*Music Leg', sc))
    wx = sc.count('weather:"')
    hk = sc.count('hook:"')
    cu = open(os.path.join(HERE, "cues-%s.js" % t), encoding="utf-8").read()
    C = json.loads(cu[cu.index("["):cu.rindex("]") + 1])
    sight = sum(1 for c in C if c.get("target"))
    thr = len(re.findall(r'\{title:"[^"]+", tag:"#\w+"', sc))
    decl = re.search(r'\{id:"%s".*?blocks:(\d+)\}' % re.escape(t), 
                     open(os.path.join(HERE, "tours.js"), encoding="utf-8").read(), re.S)
    decl = decl.group(1) if decl else "?"
    live = subprocess.run(["curl", "-s", "-H", "Cache-Control: no-cache",
                           "https://www.iguideiceland.is/app/script-%s.js" % t],
                          capture_output=True, text=True).stdout.strip()
    same = "ok" if live == sc.strip() else "DIFFERS"
    flag = ""
    if str(n) != str(decl): flag += " COUNT"
    if wx < n - music:      flag += " WX-%d" % (n - music - wx)
    if hk < n:              flag += " HOOK-%d" % (n - hk)
    if sight < len(C) - music: flag += " SIGHT-%d" % (len(C) - music - sight)
    print("%-6s %6d %7s %6d %5d %6d %7d %8d %7s%s"
          % (t, n, decl, hk, wx, len(C), sight, thr, same, flag))
    rows.append((t, n, music, wx, hk, len(C), sight, same, flag))

print("\nTOURS NEEDING WORK:")
for t, n, music, wx, hk, nc, sight, same, flag in rows:
    if flag or same != "ok":
        print("  %-5s%s%s" % (t, flag, "" if same == "ok" else " LIVE-DIFFERS"))
