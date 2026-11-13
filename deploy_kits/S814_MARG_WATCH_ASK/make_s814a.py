#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s814a.py LIVE_AMIR OUT -- kit S814 (13-Nov-2026, Sanjeevni session 445): amir_day.py 49e1eba1 -> one new kind on his one-time jobs
card: 'ask' -- the owner's question from the Marg watch, answered with one tap (an optional short line). After he answers, the line leaves his
card; no take-back (the owner's rule of 11-Oct). Every patch is an exact anchor that occurs once; anything else stops the build."""
import hashlib, sys

FROM = "49e1eba1ac3190ee2afc03b192df13c0"


def one(s, a, b):
    if s.count(a) != 1:
        raise SystemExit("anchor not found once (%d): %r" % (s.count(a), a[:80]))
    return s.replace(a, b)


def main():
    src, out = sys.argv[1:3]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    s = one(s, 'S494_KINDS = {"category": 0, "vendor_bill": 1, "tap": 2}\n',
            'S494_KINDS = {"ask": -1, "category": 0, "vendor_bill": 1, "tap": 2}      # S814: "ask" -- the owner\'s question from the Marg watch, first on the card\n'
            'S814_ANS = {"fixed": "Marg mein theek kar diya", "right": "Sahi hai, galti nahi", "supplier": "Supplier ne bill badla", "unknown": "Pata nahi",\n'
            '            "returned": "Grahak ne maal wapas kiya", "mistake": "Bill galti se bana tha"}\n')
    s = one(s, 'def _s494_tap(cx, who, val):\n',
            'def _s494_tap(cx, who, val, note=""):\n')
    s = one(s, '''        if val == "cat":
            hit = [(r[0], r[1], "done") for r in cx.execute("SELECT id, key FROM amir_job WHERE kind='category' AND " + S494_OPEN).fetchall()]
        else:''', '''        ma = re.match(r"^ask:(\\d{1,9}):([a-z]{3,10})$", val)       # S814: his answer to the owner's question -- one tap, a short line
        if ma:
            r = cx.execute("SELECT id, key, sub_hi FROM amir_job WHERE id=? AND kind='ask' AND " + S494_OPEN, (int(ma.group(1)),)).fetchone()
            code = ma.group(2)
            if not r or code not in S814_ANS or code not in str(r[2] or "").split(","):
                return 0
            line = re.sub(r"[\\s|]+", " ", str(note or "")).strip()[:300]
            what = code + (("|" + line) if line else "")
            if cx.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what=?, done_at=?, done_how='answered' WHERE id=? AND done_at IS NULL",
                          (now, who, what, now, r[0])).rowcount != 1:   # S446 review S5: a double tap answers once
                cx.rollback()
                return 0
            _audit(cx, who, "job", r[1], {"answered": code, "line": line or None})
            cx.commit()
            return 1
        if val == "cat":
            hit = [(r[0], r[1], "done") for r in cx.execute("SELECT id, key FROM amir_job WHERE kind='category' AND " + S494_OPEN).fetchall()]
        else:''')
    s = one(s, '''    out = ["<div class=line id=s494jobs><span class=sub><b>Ek baar ke kaam</b></span></div>"]
''', '''    out = ["<div class=line id=s494jobs><span class=sub><b>Ek baar ke kaam</b></span></div>"]
    for j in jobs:                                             # S814: the owner's question, first -- the answers are one tap each
        if j["kind"] != "ask":
            continue
        codes = [c for c in str(j.get("sub_hi") or "").split(",") if c in S814_ANS]
        q = "<br>".join(_esc(x) for x in str(j.get("text_hi") or j["subject"]).split("\\n"))
        btns = "".join("<button class='btn plain' name=ans value='%s' style='display:block;width:100%%;text-align:left;margin:0 0 6px'>%s</button>"
                       % (c, _esc(S814_ANS[c])) for c in codes)
        out.append("<div class=line style='border-left:4px solid var(--bad);padding-left:8px'><span class=big><b>Doctor sahab ka sawaal</b></span><br>"
                   "<span>%s</span><form method=post style='margin-top:8px'><button type=submit disabled hidden aria-hidden=true></button>"
                   "<input type=hidden name=job value='ask:%d'>"
                   "<input name=note maxlength=300 placeholder='Kuch likhna ho to pehle yahan likhiye (zaroori nahi)' "
                   "style='width:100%%;padding:8px;margin:0 0 8px;border:1px solid #d0d5dd;border-radius:8px'>%s</form></div>" % (q, j["id"], btns))
''')
    s = one(s, '''        if f.get("job"):                                       # S494: a one-time job tapped on his card -- FIRST, for every step
            _s494_tap(cx, user, f.get("job"))''', '''        if f.get("job"):                                       # S494: a one-time job tapped on his card -- FIRST, for every step
            jv = str(f.get("job") or "")
            if jv.startswith("ask:") and f.get("ans"):         # S814: the answer button names the answer
                jv = "%s:%s" % (jv, f.get("ans"))
            _s494_tap(cx, user, jv, f.get("note") or "")''')
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
