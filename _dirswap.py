#!/usr/bin/env python3
"""Produce the two corrected cue lines in all twenty languages WITHOUT inventing
any translation.

Three cues were corrected against the geometry:
  Gljufrasteinn on 1.0/2.0/3.0  "Look left"  -> "Look right"
  Mavahlid on 9.0               "Look right" -> "Look left"
  Esja on 4.0                   -> reuses 9.0/10.0's existing line, already translated

The first two are new English strings, so their translations would fall back to
English and three cues would REGRESS from translated to not. Rather than machine
translating the sentences myself, this takes the sentence a translator already
wrote and changes only the direction term -- and it does not guess that term
either. It derives each language's own "left" and "right" wording by diffing the
words used across every cue whose English says left against every cue whose
English says right, then applies the single substitution.

Prints every result for eyeballing. Writes nothing without --apply.
"""
import json,glob,io,os,re,sys,collections

APPLY='--apply' in sys.argv
corp=json.load(open('_tr/corpus.json'))
BY_ID={x['id']:x for x in corp}

def is_cue(x): return x.get('ctx','').startswith('cue')
LEFT_IDS={x['id'] for x in corp if is_cue(x) and re.search(r'\bleft\b',x['en'],re.I)
          and not re.search(r'\bright\b',x['en'],re.I)}
RIGHT_IDS={x['id'] for x in corp if is_cue(x) and re.search(r'\bright\b',x['en'],re.I)
           and not re.search(r'\bleft\b',x['en'],re.I)}

TR=collections.defaultdict(dict)
for f in glob.glob('_tr/out/*.jsonl'):
    base=os.path.basename(f)
    if not base.endswith('.jsonl') or '-' not in base: continue
    lang=base.split('-')[0]
    for line in io.open(f,encoding='utf-8',errors='ignore'):
        line=line.strip()
        if not line: continue
        try: o=json.loads(line)
        except Exception: continue
        t=o.get('t') or o.get('text')
        if o.get('id') and t: TR[lang][o['id']]=t

GLJ_OLD='73c0732af0'                                   # "Look left — the white house ..."
MAV=[x['id'] for x in corp if x['en']=="Look right, inland — the farm under the fell."][0]
GLJ_NEW=[x['id'] for x in corp
         if x['en']=="Look right — the white house by the river Kaldakvísl, just off Route 36."][0]
MAV_NEW=[x['id'] for x in corp if x['en']=="Look left, inland — the farm under the fell."][0]

def words(s):
    return set(w for w in re.split(r"[^\w֐-ࣿ一-鿿぀-ヿ]+",s.lower()) if w)

rows=[]
for lang in sorted(TR):
    L=collections.Counter(); R=collections.Counter()
    for i in LEFT_IDS:
        if i in TR[lang]: L.update(words(TR[lang][i]))
    for i in RIGHT_IDS:
        if i in TR[lang]: R.update(words(TR[lang][i]))
    # a direction term is common on one side and absent (or near-absent) on the other
    lterms=sorted([w for w in L if L[w]>=3 and R[w]==0], key=lambda w:-L[w])[:3]
    rterms=sorted([w for w in R if R[w]>=3 and L[w]==0], key=lambda w:-R[w])[:3]
    glj=TR[lang].get(GLJ_OLD); mav=TR[lang].get(MAV)
    # Four languages where the derived term is the right word in the wrong form
    # for THIS sentence, so the substitution is spelled out instead of guessed:
    #   ar  the adverbial يساراً/يميناً cannot follow إلى; the sentence needs اليسار
    #   hi  तरफ़/ओर take बाईं/दाईं, not the bare stem the diff surfaced
    #   ja  the diff found 左手/右手 (the compound); this sentence uses bare 左/右
    #   zh  the diff found 看左边/往右看; this sentence opens 往左看
    HAND={'ar':(None,('إلى اليمين','إلى اليسار')),
          'hi':(('बाईं तरफ़','दाईं तरफ़'),('दाईं ओर','बाईं ओर')),
          'ja':(('左','右'),('右','左')),
          'zh':(('往左看','往右看'),None)}
    def swap(src,frm,to):
        if not src or not frm or not to: return None
        for a in frm:
            m=re.search(re.escape(a),src,re.I)
            if m:
                b=to[0]
                if a[:1].isupper() or src[m.start():m.start()+1].isupper(): b=b[:1].upper()+b[1:]
                return src[:m.start()]+b+src[m.end():]
        return None
    hg,hm=HAND.get(lang,(None,None))
    gnew=(glj.replace(hg[0],hg[1],1) if (hg and glj and hg[0] in glj) else swap(glj,lterms,rterms))
    mnew=(mav.replace(hm[0],hm[1],1) if (hm and mav and hm[0] in mav) else swap(mav,rterms,lterms))
    rows.append((lang,lterms,rterms,glj,gnew,mav,mnew))

print("%-4s %-22s %-22s"%("lang","left terms","right terms"))
for lang,lt,rt,*_ in rows: print("%-4s %-22s %-22s"%(lang,",".join(lt),",".join(rt)))
print("\n=== Gljufrasteinn: 'Look left' -> 'Look right' ===")
for lang,lt,rt,glj,gnew,mav,mnew in rows:
    print("  %-3s %s"%(lang,gnew if gnew else "!! COULD NOT DERIVE (old=%r)"%glj))
print("\n=== Mavahlid on 9.0: 'Look right' -> 'Look left' ===")
for lang,lt,rt,glj,gnew,mav,mnew in rows:
    print("  %-3s %s"%(lang,mnew if mnew else "!! COULD NOT DERIVE (old=%r)"%mav))

bad=[l for l,_,_,_,g,_,m in rows if not g or not m]
print("\nlanguages needing a hand: %s"%(bad or "none"))
if APPLY and not bad:
    for lang,lt,rt,glj,gnew,mav,mnew in rows:
        p='_tr/out/%s-dirfix.jsonl'%lang
        with io.open(p,'w',encoding='utf-8') as fh:
            fh.write(json.dumps({"id":GLJ_NEW,"t":gnew},ensure_ascii=False)+"\n")
            fh.write(json.dumps({"id":MAV_NEW,"t":mnew},ensure_ascii=False)+"\n")
    print("wrote _tr/out/<lang>-dirfix.jsonl for %d languages"%len(rows))
