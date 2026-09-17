#!/bin/bash
# _finalsweep.sh — rebuild every manuscript, run every checker, and compare every
# deployed script against the live site. Written 17 Sep 2026 at the end of the
# merge job so the whole thing can be re-proved in one command.
cd ~/Documents/golden-circle-direct || exit 1

echo "==================== BUILD ===================="
python3 - <<'PYEOF'
import glob, os, subprocess, re
BASE = "/Users/ritchiej/Documents/RitchWiki/Tour Scripts"
for p in sorted(glob.glob(BASE + "/*.md")):
    name = os.path.basename(p)[:-3]
    if name.startswith("_"):
        continue
    num = name.split(" ")[0]
    out = subprocess.run(["python3", "build-any.py", name, "script-%s.js" % num],
                         capture_output=True, text=True,
                         cwd="/Users/ritchiej/Documents/golden-circle-direct")
    line = [l for l in (out.stdout + out.stderr).split("\n") if "format=" in l]
    print(("%-42s " % name) + (line[0].split(" ", 1)[1] if line else "NO BUILD LINE"))
PYEOF

echo
echo "==================== CHECKS ===================="
printf "mergecheck : "; python3 _mergecheck.py  2>&1 | tail -1
printf "photocheck : "; python3 _photocheck.py  2>&1 | grep -E "^problems" | tail -1
printf "threadcheck: "; python3 _threadcheck.py 2>&1 | tail -1
printf "leakcheck  : "; python3 _leakcheck.py   2>&1 | tail -1
printf "blocklib   : "; python3 ~/Documents/iGuide-deploy/_blocklib.py 2>&1 | tail -1

echo
echo "==================== LIVE vs LOCAL ===================="
LIVE=$(curl -s "https://iguideiceland.is/app/sw.js?cb=$RANDOM$RANDOM" | grep -m1 "const VERSION")
LOCAL=$(grep -m1 "const VERSION" ~/Documents/iGuide-Iceland-Site/app/sw.js)
echo "sw.js local: $LOCAL"
echo "sw.js live : $LIVE"
BAD=0
for f in ~/Documents/iGuide-Iceland-Site/app/script-*.js; do
  n=$(basename "$f")
  L=$(shasum -a256 "$f" | cut -d" " -f1)
  R=$(curl -s "https://iguideiceland.is/app/$n?cb=$RANDOM$RANDOM" | shasum -a256 | cut -d" " -f1)
  if [ "$L" = "$R" ]; then
    echo "  OK        $n  ${L:0:16}"
  else
    echo "  MISMATCH  $n  local=${L:0:16} live=${R:0:16}"
    BAD=$((BAD+1))
  fi
done
echo
echo "hash mismatches: $BAD"
