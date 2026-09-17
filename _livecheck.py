"""Confirms the live site actually serves what we think it does.

Fetches with curl, not urllib: this Mac's Python has no CA bundle configured
and every https call fails CERTIFICATE_VERIFY_FAILED. curl uses the system
store and works.
"""
import subprocess

def get(path):
    url = "https://www.iguideiceland.is" + path
    code = subprocess.run(["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", url],
                          capture_output=True, text=True, timeout=180).stdout.strip()
    body = subprocess.run(["curl", "-s", url],
                          capture_output=True, text=True, timeout=180).stdout
    return code, body

cm, m = get("/map")
ci, i = get("/iceland")
cn, n = get("/norse")

checks = [
    ("/map returns 200",           cm == "200"),
    ("/map: three-door gate",      'id="gate"' in m and m.count('class="lock"') == 3),
    ("/map: vegvisir ground",      'id="gateMark"' in m),
    ("/map: command menu",         'id="tabbar"' in m),
    ("/map: Maps exit",            'data-nav="home"' in m),
    ("/map: Website exit",         'data-nav="website"' in m),
    ("/map: layer -> /iceland",    "/iceland.html" in m),
    ("/map: canonical is /map",    'iguideiceland.is/map"' in m),
    ("/map: no laptop paths",      "file:///" not in m),
    ("/iceland returns 200",       ci == "200"),
    ("/iceland: the island map",   'id="tabbar"' in i and "mapinfo" in i),
    ("/iceland: both exits",       "vgHome" in i and "vgSite" in i),
    ("/norse still 200",           cn == "200"),
    ("/norse untouched (old UI)",  'id="gate"' not in n and 'id="bar"' in n),
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
