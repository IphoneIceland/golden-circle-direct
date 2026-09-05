#!/usr/bin/env python3
"""Give every block on 5.0 and 6.0 a weather pivot.

The final audit found 31 of 37 blocks with no 🌫️ line. Not a parser bug — the
field is simply absent from the manuscript. 14.0 has 28 of 28 because it was
written to the current schema. 1.0 has none at all, 7.0 has two.

These add no new facts. They are delivery fallbacks for the morning the thing
you are pointing at is not there, which on this coast is most mornings.
Matched by block TITLE so one table serves both tours.

Usage: python3 _addweather.py [--write]
"""
import os, re, sys, shutil

WRITE = "--write" in sys.argv
D = os.path.expanduser("~/Documents/RitchWiki/Tour Scripts")

WX = {
 "Jóhannes Sveinsson Kjarval": "If the park is grey and half empty, that is exactly the Iceland Kjarval painted. He was never interested in the sunny version.",
 "Ölgerðin": "If you cannot see the brewery you can usually smell the malt. That counts.",
 "Elliðaárdalur": "The valley looks its best wet. That river is the reason anything in this city is green.",
 "Rauðhólar": "The red goes deeper in the rain, so a grey day actually makes the craters easier to pick out, not harder.",
 "Kristnitökuhraun": "Lava in fog is the honest version. This is roughly what the year 1000 looked like from a distance.",
 "Hellisheiðarvirkjun": "If you cannot see the plant you will see the steam, and on a day like this the steam is the whole show.",
 "Hveragerði": "Cannot see the town? Look for the steam instead. The town is wherever the ground is smoking.",
 "Ölfusá": "Rain makes it bigger. Everything I am about to tell you about this river is more true today than it was yesterday.",
 "Ingólfur Arnarson": "If the mountain has gone, take my word for it — big, flat-topped, and behind us now.",
 "Selfoss": "You do not need to see anything for this one. Just listen to what is under the wheels.",
 "Þjórsá": "Weather barely touches this river. It comes off an ice cap, so it runs much the same in sun or sleet.",
 "Hella": "You will not see the caves from here in any weather. They are cut into the bank, which is rather the point of them.",
 "Keldur": "You will not see Keldur today, and you rarely can. It is ten kilometres up a side road — which is exactly why it survived.",
 "Hvolsvöllur": "If the village is in murk, that is Njáll's country behaving normally. The saga has far more bad weather in it than good.",
 "Vestmannaeyjar": "No islands today? They are twenty-seven kilometres out. On a clear day they look close enough to swim to, and that is the illusion.",
 "Landeyjar Plains": "Flat, wet and grey is this plain's default setting. It is a floodplain. It looks like this most of the year.",
 "Markarfljót": "If the hillside has gone, remember that Gunnar turned back for the view. He would not have on a day like this.",
 "Eyjafjallajökull": "Cannot see it? Neither could the pilots in 2010, and that was rather the problem.",
 "Drangurinn": "The rock sits right by the road, so this is one you get whatever the sky is doing.",
 "Sólheimajökull": "Cloud sits low on the ice. If the top has gone you are still seeing the snout, and the snout is the part that has been moving.",
 "The DC-3 Wreck": "You would not see the wreck from the road on the clearest day of the year. That is what the photograph is for.",
 "Pétursey": "If the mountain is in cloud you are seeing what it was for. It was a sea mark, and sailors mostly needed it in bad visibility.",
 "Skeiðflatarkirkja": "Small red roof, big grey sky. It is the roof you are looking for, not the church.",
 "Dýrhólaey": "If the headland has gone you may still catch the light blinking, which is the entire reason it is up there.",
 "Reynisfjara": "Bad weather makes this beach more dangerous, not more atmospheric. Stay well back from the water today.",
 "Katla": "Cannot see the ice cap? Neither can the people living under it. That is the whole problem with Katla.",
 "Víkurkirkja": "Even in cloud it is the highest thing in the village, which is precisely why it is the evacuation point.",
 "Vík í Mýrdal": "The village is over the hill either way. You will know when we are there.",
 "Hjörleifshöfði": "Twelve kilometres out on a wet day means you are not seeing it. It looks like a ship, and today it is a ship in fog.",
 "Skógafoss": "Rain makes it bigger. There is no bad-weather version of this waterfall.",
 "Seljalandsfoss": "You are getting wet either way. This is the one waterfall where the forecast is irrelevant, because you walk behind it.",
}

for fn, ind in (("5.0 South Coast.md", "    "), ("6.0 South Coast Combo.md", "  ")):
    p = os.path.join(D, fn)
    s = open(p, encoding="utf-8").read()
    added = skipped = 0
    for m in list(re.finditer(r'^%s> ### (\d+\.\d+) (.*)$' % re.escape(ind), s, re.M))[::-1]:
        title = m.group(2)
        nxt = s.find("\n%s> ### " % ind, m.end())
        end = nxt if nxt > 0 else len(s)
        body = s[m.end():end]
        if "🌫️" in body or "Music Leg" in title:
            skipped += 1
            continue
        key = next((k for k in WX if k in title), None)
        if not key:
            print("   !! no weather line written for %s" % title[:44])
            continue
        mm = re.search(r'^%s🎤 .*$' % re.escape(ind), body, re.M)
        if not mm:
            print("   !! no 🎤 line in %s" % title[:44])
            continue
        at = m.end() + mm.end()
        s = s[:at] + "\n\n" + ind + "🌫️ Weather pivot: \"" + WX[key] + "\"" + s[at:]
        added += 1
    print("  %s: +%d weather pivots, %d already had one or are music" % (fn, added, skipped))
    if WRITE:
        shutil.copy2(p, p + ".bak-2026-09-05-weather")
        open(p, "w", encoding="utf-8").write(s)
        print("    WROTE")
