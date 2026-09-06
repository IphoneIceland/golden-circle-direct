#!/usr/bin/env python3
"""Which pass is the checker actually standing on?

_clockcheck.py resolves a pin to a route index with a nearest-point search. On an
out-and-back tour the same stretch of road is driven twice, so the nearest point
can belong to the OTHER pass -- and the direction of travel there is reversed,
which flips left and right. This prints both resolutions side by side so the
disagreement can be settled with evidence instead of preference.
"""
import json,re,io,math,sys
def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))
def brg(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c);dl=math.radians(d-b)
    y=math.sin(dl)*math.cos(p2)
    x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360
def clock_of(d):
    h=round(d/30)%12
    return 12 if h==0 else h

TID=sys.argv[1]; WANT=set(sys.argv[2:])
_t=io.open('route-%s.js'%TID,encoding='utf-8').read()
o=json.loads(_t[_t.index('{'):_t.rindex('}')+1])
g=o["geometry"] if isinstance(o,dict) else o
N=len(g); cum=[0.0]
for i in range(1,N): cum.append(cum[-1]+hav(g[i-1][0],g[i-1][1],g[i][0],g[i][1]))
total=cum[-1]
c=io.open('cues-%s.js'%TID,encoding='utf-8').read()
s=c[c.index('['):c.rindex(']')+1]
try: cu=json.loads(s)
except Exception: cu=json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:',r'\1"\2":',s))

def trav(pi):
    j=min(pi+3,N-1); i0=max(pi-1,0)
    return brg(g[i0][0],g[i0][1],g[j][0],g[j][1])
def by_progress(pct):
    want=total*pct/100
    for i,cc in enumerate(cum):
        if cc>=want: return i
    return N-1

for x in cu:
    if WANT and x['id'] not in WANT: continue
    T=x.get('target')
    if not T: continue
    p=x['pin']
    pn=min(range(N), key=lambda i: hav(p['lat'],p['lon'],g[i][0],g[i][1]))
    pp=by_progress(x['progress'])
    b=brg(p['lat'],p['lon'],T['lat'],T['lon'])
    print("%-10s %-24s  progress %6.2f%%" % (x['id'],T['name'][:24],x['progress']))
    print("      nearest-point  -> index %5d (%.2f%% of route)  heading %5.1f  => %2d o'clock"
          % (pn, cum[pn]/total*100, trav(pn), clock_of((b-trav(pn))%360)))
    print("      by progress    -> index %5d (%.2f%% of route)  heading %5.1f  => %2d o'clock"
          % (pp, cum[pp]/total*100, trav(pp), clock_of((b-trav(pp))%360)))
    print("      SAME PASS" if abs(pn-pp)<25 else "      *** DIFFERENT PASS — the two resolutions are %d route points apart"%abs(pn-pp))
