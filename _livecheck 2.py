"""Confirms the live site actually serves what we think it does."""
import urllib.request

def get(p):
    r = urllib.request.urlopen("https://www.iguideiceland.is" + p, timeout=90)
    return r.status, r.read().decode("utf-8", "replace")

sm, m = get("/map")
si, i = get("/iceland")
sn, n = get("/norse")

checks = [
    ("/map returns 200",            sm == 200),
    ("/map: three-door gate",       'id="gate"' in m and m.count('class="lock"') == 3),
    ("/map: vegvisir ground",       'id="gateMark"' in m),
    ("/map: command menu",          'id="tabbar"' in m),
    ("/map: Maps exit",             'data-nav="home"' in m),
    ("/map: Website exit",          'data-nav="website"' in m),
    ("/map: layer -> /iceland",     "/iceland.html" in m),
    ("/map: canonical is /map",     'iguideiceland.is/map"' in m),
    ("/map: no laptop paths",       "file:///" not in m),
    ("/iceland returns 200",        si == 200),
    ("/iceland: the island map",    'id="tabbar"' in i and "mapinfo" in i),
    ("/iceland: both exits",        "vgHome" in i and "vgSite" in i),
    ("/norse still 200",            sn == 200),
    ("/norse untouched (old UI)",   'id="gate"' not in n and 'id="bar"' in n),
]
for name, ok in checks:
    print(("  OK   " if ok else "  MISS ") + name)
bad = [name for name, ok in checks if not ok]
print()
print("  /map     %d bytes" % len(m))
print("  /iceland %d bytes" % len(i))
print("  /norse   %d bytes" % len(n))
print()
print("LIVE AND CORRECT" if not bad else "PROBLEMS: " + ", ".join(bad))
