#!/usr/bin/env python3
"""Swap two adjacent blocks that the road passes in the opposite order.

    _swapblocks.py <tour> <id-a> <id-b> [--apply]

_ordercheck.py finds blocks whose landmark the road reaches BEFORE the block in
front of them. No pin can fix that -- a pin can only move inside the gap between
its neighbours -- so the block fires late for ever. The fix is to put the two
blocks the way round the road actually passes them.

HOW THE SPAN IS FOUND, and why it matters. The first version of this tool sliced
from one `{id:"` to the next, which drags whatever sits between the two blocks
along with the body: a section header (that buried Frooa inside the Olafsvik stop
section on 9.0) or, for the LAST block of a section, the `]},` that closes the
section's blocks array -- which threw the block clean out of its section and left
it as a sibling of the sections themselves. Neither showed up in any text-level
check; both only surfaced when node actually parsed the file.

So a block's span is now found by BRACE MATCHING from its opening `{`, skipping
over string literals and escapes, and only the two object literals trade places.
Every separator, bracket and header stays exactly where it was. After running,
node must parse the file and every section must still have its blocks array --
verify, do not assume.

The two blocks also trade id numbers so ids stay in ascending running order.
A block's TARGET in cues-<tour>.js belongs to its content, not its slot, so swap
those too, then re-run _fixpins.py. Anything citing a block by number now points
at the other subject: run _threadcheck.py and _thrgaps.py afterwards.
"""
import re,io,sys,shutil,datetime

APPLY='--apply' in sys.argv
args=[a for a in sys.argv[1:] if not a.startswith('--')]
if len(args)<3: raise SystemExit("usage: _swapblocks.py <tour> <id-a> <id-b> [--apply]")
TID,A,B=args[0],args[1],args[2]
f='script-%s.js'%TID
s=io.open(f,encoding='utf-8').read()

def span(bid):
    """Start and end of one block's object literal, by brace matching."""
    i=s.find('{id:"%s"'%bid)
    if i<0: raise SystemExit("%s not found in %s"%(bid,f))
    depth=0; j=i; instr=False; esc=False
    while j<len(s):
        c=s[j]
        if instr:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='"': instr=False
        else:
            if c=='"': instr=True
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0: return i,j+1
        j+=1
    raise SystemExit("unbalanced braces from %s"%bid)

ia,ja=span(A); ib,jb=span(B)
if ia>ib: A,B,ia,ja,ib,jb=B,A,ib,jb,ia,ja
between=s[ja:ib]
if '{id:"' in between or re.search(r'\{title:"(?:[^"\\]|\\.)*",\s*kind:"\w+"',between):
    raise SystemExit("%s and %s are not adjacent -- another block or a section "
                     "header sits between them"%(A,B))
if ']' in between or '[' in between:
    raise SystemExit("%s and %s are separated by an array boundary (%r) -- they are "
                     "in different sections, which this tool will not silently "
                     "restructure"%(A,B,between.strip()))
blockA=s[ia:ja]; blockB=s[ib:jb]

def title(b):
    m=re.search(r'title:"((?:[^"\\]|\\.)*)"',b); return m.group(1) if m else '?'
newB=blockB.replace('{id:"%s"'%B,'{id:"%s"'%A,1)
newA=blockA.replace('{id:"%s"'%A,'{id:"%s"'%B,1)
out=s[:ia]+newB+between+newA+s[jb:]

print("%s: %s %-28s  <->  %s %s"%(TID,A,title(blockA)[:28],B,title(blockB)))
print("   after the swap: %s = %s,  %s = %s"%(A,title(blockB)[:34],B,title(blockA)[:34]))
if APPLY:
    stamp=datetime.date.today().isoformat()
    shutil.copy2(f,'%s.bak-%s-swap'%(f,stamp))
    io.open(f,'w',encoding='utf-8').write(out)
    print("   wrote %s"%f)
else:
    print("   (dry run)")
