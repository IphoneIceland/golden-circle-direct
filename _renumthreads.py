#!/usr/bin/env python3
"""Repoint the Threads index rows after stops were renumbered by a reorder.

Swapping two stops swaps their NUMBERS, so every Threads row citing the old
number now points at the other subject. build-any.py only checks a cited number
exists, so this rot is silent -- it has bitten this index twice before.

The remap is applied with ONE regex and a callback, never a loop of successive
substitutions: shifting 5.11->5.12 and 5.12->5.11 in two passes just moves
everything to 5.12 and back. Only the Threads section is touched, and only the
leading stop number of a row, so prose that happens to contain "7.9" is safe.

Run with --apply. Verify with _threadcheck.py afterwards.
"""
import re,io,os,sys,shutil,datetime

APPLY='--apply' in sys.argv
SRC=os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")

# subject -> (old number, new number), taken from the heading order before and
# after the gcd197 reorder.
REMAP={
 '3.0':  {'3.27':'3.28','3.28':'3.27'},
 '5.0':  {'5.11':'5.12','5.12':'5.11','5.20':'5.21','5.21':'5.20'},
 '6.0':  {'6.11':'6.12','6.12':'6.11','6.20':'6.21','6.21':'6.20'},
 '7.0':  {'7.7':'7.9','7.8':'7.7','7.9':'7.8'},
 '9.0':  {'9.22':'9.24','9.23':'9.22','9.24':'9.23'},
 '10.0': {'10.12':'10.13','10.13':'10.14','10.14':'10.12'},
}
DOCS={'3.0':'3.0 Golden Circle Lagoons.md','5.0':'5.0 South Coast.md',
      '6.0':'6.0 South Coast Combo.md','7.0':'7.0 Glacial Lagoon.md',
      '9.0':'9.0 Snæfellsnes North.md','10.0':'10.0 Snæfellsnes South.md'}
stamp=datetime.date.today().isoformat()

def remap_rows(text, table):
    """Rewrite the leading stop number of every '- <n.n> Title — desc' row."""
    def fn(m):
        return m.group(1)+table.get(m.group(2), m.group(2))+m.group(3)
    return re.sub(r'(?m)^([ \t]*[-*]\s+)(\d+\.\d+)(\s)', fn, text)

for tid,table in REMAP.items():
    # ---- the Craft export: only the section under the Threads heading ----
    p=os.path.join(SRC,DOCS[tid])
    if os.path.isfile(p):
        s=io.open(p,encoding='utf-8').read()
        parts=re.split(r'(^\s*\+? ?#{1,2} 🧵 Threads)', s, maxsplit=1, flags=re.M)
        if len(parts)==3:
            new=parts[0]+parts[1]+remap_rows(parts[2],table)
            n=sum(1 for a,b in table.items() if a!=b)
            if new!=s:
                if APPLY:
                    shutil.copy2(p,p+'.bak-%s-threadrenum'%stamp)
                    io.open(p,'w',encoding='utf-8').write(new)
                print("  export  %-30s remapped %d numbers"%(DOCS[tid],n))
            else: print("  export  %-30s no rows cited them"%DOCS[tid])
        else: print("  export  %-30s NO THREADS SECTION"%DOCS[tid])
    else: print("  export  %-30s NOT FOUND"%DOCS[tid])
    # ---- the built script: rows live as ["<n.n> Title","<id>","desc"] ----
    f='script-%s.js'%tid
    s=io.open(f,encoding='utf-8').read()
    def fn(m): return '["'+table.get(m.group(1),m.group(1))+m.group(2)
    new=re.sub(r'\["(\d+\.\d+)( [^"]*")', fn, s)
    if new!=s:
        if APPLY:
            shutil.copy2(f,'%s.bak-%s-threadrenum'%(f,stamp))
            io.open(f,'w',encoding='utf-8').write(new)
        print("  script  %-30s remapped"%f)
    else: print("  script  %-30s unchanged"%f)
if not APPLY: print("\n(dry run — pass --apply)")
