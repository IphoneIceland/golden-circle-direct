#!/usr/bin/env python3
"""Mirror a block swap into the Craft EXPORT markdown.

    _swapmd.py "<export.md>" <heading-a> <heading-b> [--apply]

The app was reordered at gcd197; the exports still hold the old order, so a
rebuild would silently undo it. A stop in the export is a numbered H3 heading
("### 9.4 Kjalarnes — ...") followed by everything up to the next heading of the
SAME OR HIGHER level. This swaps two adjacent stops and swaps their numbers, so
the numbering stays ascending and every Threads row still points at the right
subject.

Headings are matched on the number, so pass the numbers ("7.7" "7.8"), not titles.
"""
import re,io,sys,shutil,datetime,os

APPLY='--apply' in sys.argv
args=[a for a in sys.argv[1:] if not a.startswith('--')]
if len(args)<3: raise SystemExit(__doc__)
PATH,A,B=args[0],args[1],args[2]
s=io.open(PATH,encoding='utf-8').read()

HEAD=re.compile(r'(?m)^([ \t]*)(>? ?)(#{1,3})\s+(\d+\.\d+)\s+(.*)$')
hits=[(m.group(4),m.start(),len(m.group(3)),m.group(0)) for m in HEAD.finditer(s)]
if not hits: raise SystemExit("no numbered headings found in %s"%PATH)

def block(num):
    for i,(n,pos,lvl,line) in enumerate(hits):
        if n==num:
            end=len(s)
            for n2,pos2,lvl2,_ in hits[i+1:]:
                if lvl2<=lvl: end=pos2; break
            return pos,end,lvl,line
    raise SystemExit("stop %s not found in %s"%(num,PATH))

ia,ja,la,lina=block(A); ib,jb,lb,linb=block(B)
if ia>ib: A,B,ia,ja,la,lina,ib,jb,lb,linb=B,A,ib,jb,lb,linb,ia,ja,la,lina
if ja!=ib: raise SystemExit("%s and %s are not adjacent in %s"%(A,B,PATH))
if la!=lb: raise SystemExit("%s and %s are at different heading levels"%(A,B))

blkA=s[ia:ja]; blkB=s[ib:jb]
# trade the numbers so the document still reads 1,2,3...
def renum(blk,frm,to):
    return re.sub(r'^(\s*>? ?#{1,3}\s+)%s(\s)'%re.escape(frm), lambda m:m.group(1)+to+m.group(2), blk, count=1)
newB=renum(blkB,B,A); newA=renum(blkA,A,B)
out=s[:ia]+newB+newA+s[jb:]

print("%s"%os.path.basename(PATH))
print("   %s  %s" % (A, lina.strip()[:70]))
print("   %s  %s" % (B, linb.strip()[:70]))
print("   -> %s takes %r, %s takes %r"%(A,linb.strip()[:34],B,lina.strip()[:34]))
if APPLY:
    stamp=datetime.date.today().isoformat()
    shutil.copy2(PATH,PATH+'.bak-%s-reorder'%stamp)
    io.open(PATH,'w',encoding='utf-8').write(out)
    print("   written")
else:
    print("   (dry run)")
