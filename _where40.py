#!/usr/bin/env python3
"""Reverse-geocode named points along route 4.0 so road/river claims are checked
against the map rather than assumed."""
import json,io,math,subprocess,sys,time
def hav(a,b,c,d):
    R=6371000.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))
_t=io.open('route-4.0.js',encoding='utf-8').read()
rt=json.loads(_t[_t.index('{'):_t.rindex('}')+1])
g=rt["geometry"] if isinstance(rt,dict) else rt
cum=[0.0]
for i in range(1,len(g)): cum.append(cum[-1]+hav(g[i-1][0],g[i-1][1],g[i][0],g[i][1]))
total=cum[-1]
def at(pct):
    want=total*pct/100
    for i,c in enumerate(cum):
        if c>=want: return i
    return len(g)-1
for pct in [float(x) for x in sys.argv[1:]]:
    i=at(pct); lat,lon=g[i]
    out=subprocess.run(['curl','-s','-A','iguide-audit/1.0 (richardjsuffling@gmail.com)',
        'https://nominatim.openstreetmap.org/reverse?lat=%f&lon=%f&format=json&zoom=16'%(lat,lon)],
        capture_output=True,text=True).stdout
    try: nm=json.loads(out).get('display_name')
    except Exception: nm='(no result)'
    print("%6.2f%%  %.5f,%.5f  %s"%(pct,lat,lon,nm))
    time.sleep(1.2)
