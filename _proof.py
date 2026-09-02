#!/usr/bin/env python3
"""Proof sheet: route, pins and every sightline, drawn so a human can spot a
pin in the sea or an arrow pointing at nothing. Numbers pass; eyes decide."""
import json, re, io, math, os
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.expanduser("~/Documents/RitchWiki/_proof_tmp")

def cues(t):
    s = t[t.index('['):t.rindex(']')+1]
    try: return json.loads(s)
    except Exception:
        return json.loads(re.sub(r'([{,])\s*([A-Za-z_]\w*)\s*:', r'\1"\2":', s))

def route(t):
    o = json.loads(t[t.index('{'):t.rindex('}')+1])
    return o["geometry"] if isinstance(o, dict) else o

for tid in ["1.0", "4.0", "7.0", "9.0"]:
    C = cues(io.open(f"cues-{tid}.js", encoding="utf-8").read())
    R = route(io.open(f"route-{tid}.js", encoding="utf-8").read())
    lats = [p[0] for p in R] + [c["target"]["lat"] for c in C if c.get("target")]
    lons = [p[1] for p in R] + [c["target"]["lon"] for c in C if c.get("target")]
    la0, la1 = min(lats), max(lats); lo0, lo1 = min(lons), max(lons)
    W, H, PAD = 1500, 1100, 60
    import math as _m
    kx = _m.cos(_m.radians((la0+la1)/2))          # longitude shrinks at 64N
    sx = (W-2*PAD)/max((lo1-lo0)*kx, 1e-9); sy = (H-2*PAD)/max(la1-la0, 1e-9)
    s = min(sx, sy)
    def px(la, lo):
        return (PAD + (lo-lo0)*kx*s, H - PAD - (la-la0)*s)

    im = Image.new("RGB", (W, H), (16, 17, 21)); d = ImageDraw.Draw(im)
    d.line([px(p[0], p[1]) for p in R], fill=(58, 130, 230), width=3)
    for c in C:
        if not c.get("target"): continue
        a = px(c["pin"]["lat"], c["pin"]["lon"])
        b = px(c["target"]["lat"], c["target"]["lon"])
        d.line([a, b], fill=(212, 169, 74), width=2)
        d.ellipse([b[0]-5, b[1]-5, b[0]+5, b[1]+5], outline=(240, 210, 130), width=2)
    for c in C:
        a = px(c["pin"]["lat"], c["pin"]["lon"])
        col = (235, 80, 80) if c.get("target") else (120, 125, 140)
        d.ellipse([a[0]-5, a[1]-5, a[0]+5, a[1]+5], fill=col, outline=(255,255,255))
    try: f = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 30)
    except Exception: f = None
    n = sum(1 for c in C if c.get("target"))
    d.text((20, 16), f"{tid} — {len(C)} pins, {n} sightlines", fill=(245,240,230), font=f)
    im.save(f"{OUT}/proof-{tid}.png")
    print(f"  wrote proof-{tid}.png  ({len(C)} pins, {n} sightlines)")
