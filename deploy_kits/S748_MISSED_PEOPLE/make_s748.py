#!/usr/bin/env python3
"""make_s748.py -- S748_MISSED_PEOPLE (the parent, S400, 07-Nov-2026): the owner's 'yes' (10:02 IST) and 'yes' (10:06 IST) --
NET MISSED leads each staff card: the patients who rang on that person's duty and were never reached after (no connected call
either way), counted as patients ('Net missed: 3 patients · 16 missed calls from 9 patients, 6 reached later'); the line is
rose whenever it is above zero; the staff's own card leads with it too ('Jinse baat nahin hui: 3 log').
Counted edits on the LIVE bytes (S747's TO, read whole at S400): each anchor found exactly once.
usage: make_s748.py <calls_console.py> <aaj_kaam.html> <out_dir> [--expect]"""
import hashlib
import os
import sys

FROM_MD5 = {"calls_console.py": "df484c7d4fa37b2c0e29d18eb476ea0a", "aaj_kaam.html": "dc684e46126fcaa54bb0f88813172ef4"}
HERE = os.path.dirname(os.path.abspath(__file__))


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.exit("STOP: anchor %s found %d times (must be 1)" % (label, n))
    return text.replace(old, new, 1)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 3:
        sys.exit(__doc__)
    src = {"calls_console.py": a[0], "aaj_kaam.html": a[1]}
    raw = {}
    for k, p in src.items():
        raw[k] = open(p, "rb").read()
        if md5(raw[k]) != FROM_MD5[k]:
            sys.exit("STOP: %s is %s, not the FROM %s" % (k, md5(raw[k])[:8], FROM_MD5[k][:8]))
    t = raw["calls_console.py"].decode("utf-8")
    t = edit(t, 'KIT = "S747_CALLS_REVIEW_CARDS"\nVERSION = "S747 1.0"\n', 'KIT = "S748_MISSED_PEOPLE"\nVERSION = "S748 1.0"\n', "E1 kit")
    t = edit(t, "when either cannot be found they are not registered and the staff page simply shows no card.\n",
             "when either cannot be found they are not registered and the staff page simply shows no card.\n"
             "S748_MISSED_PEOPLE (S400, 07-Nov-2026, the owner's 'yes' 10:02 and 10:06 IST): NET MISSED leads each card -- the patients\n"
             "who rang on that person's duty and were never reached after, either way ('Net missed: 3 patients . 16 missed calls from 9\n"
             "patients, 6 reached later'); a call the owner marked reviewed still counts here (it is a fact, not a verdict); a dispute he\n"
             "accepted does not. The card is rose whenever net missed is above zero. Calls stay counted as calls everywhere else.\n",
             "E2 doc")
    t = edit(t, '        nl, nb, mm = len(c["not_logged"]), len(c["not_back"]), len(c["mismatch"])\n',
             '        c["missed_people"] = len({(p.get("phone") or it["ref"]) for p, it in c["missed_items"]})       # S748\n'
             '        c["not_back_people"] = len({(p.get("phone") or it["ref"]) for p, it in c["not_back"]})\n'
             '        c["net_missed"] = len({(p.get("phone") or it["ref"]) for p, it in c["not_back"]} |\n'
             '                              {(p.get("phone") or it["ref"]) for p, it, k in c["reviewed"] if k == "not_back"})\n'
             '        nl, nb, mm = len(c["not_logged"]), len(c["not_back"]), len(c["mismatch"])\n', "E3 people")
    t = edit(t, '"wa_ans": c["wa_ans"], "not_logged": len(c["not_logged"]), "mismatch": len(c["mismatch"]),\n'
                '                     "agreed": c["agreed"]},',
             '"wa_ans": c["wa_ans"], "not_logged": len(c["not_logged"]), "mismatch": len(c["mismatch"]),\n'
             '                     "agreed": c["agreed"], "missed_people": c.get("missed_people", 0), "net_missed": c.get("net_missed", 0)},', "E4 json")
    t = edit(t, '<span class="figs">{% if c.missed_known %}{{ c.answered }}/{{ c.rung }} answered · {% if c.missed %}<b class="b">{{ c.missed }} missed</b>'
                '{% else %}0 missed{% endif %}{% else %}{{ c.answered }} answered · missed on duty not known{% endif %}',
             '<span class="figs">{% if c.missed_known %}{% if c.net_missed %}<b class="b">Net missed: {{ c.net_missed }} patient'
             '{{ \'s\' if c.net_missed != 1 else \'\' }}</b>{% else %}<b class="g">Net missed: 0</b>{% endif %}{% if c.missed %} · {{ c.missed }} '
             'missed call{{ \'s\' if c.missed != 1 else \'\' }} from {{ c.missed_people }} patient{{ \'s\' if c.missed_people != 1 else \'\' }}, '
             '{{ c.missed_people - c.net_missed }} reached later{% endif %} · {{ c.answered }}/{{ c.rung }} answered'
             '{% else %}{{ c.answered }} answered · missed on duty not known{% endif %}', "E5 summary")
    t = edit(t, 'Missed on duty, not called back · {{ nb }}</div>',
             'Missed on duty, not called back · {{ nb }}{% if c.not_back_people != nb %} ({{ c.not_back_people }} '
             'patient{{ \'s\' if c.not_back_people != 1 else \'\' }}){% endif %}</div>', "E6 subhead")
    t = edit(t, 'c["tone"] = "rose" if (nl or nb) else', 'c["tone"] = "rose" if (nl or nb or c["net_missed"]) else', "E7 tone")
    h = raw["aaj_kaam.html"].decode("utf-8")
    h = edit(h, "else { words.push(f.answered+'/'+f.rung+' uthaye');",
             "else { if(f.missed_known&&f.net_missed!==undefined)words.push('Jinse baat nahin hui: '+f.net_missed+' log'); words.push(f.answered+'/'+f.rung+' uthaye');",
             "H0 lead")
    h = edit(h, "fig('Phone uthaye (bajne wale mein se)', f.answered+'/'+f.rung);",
             "if(f.missed_known&&f.net_missed!==undefined)fig('Jinse baat nahin hui (call chhoota, phir kabhi nahin mile)', f.net_missed+' log', f.net_missed?'bad':'ok', 'missed');\n"
             "      fig('Phone uthaye (bajne wale mein se)', f.answered+'/'+f.rung);", "H3 net row")
    h = edit(h, "if(f.missed_known)words.push(f.missed+' chhoote');",
             "if(f.missed_known)words.push(f.missed+' chhoote'+((f.missed_people&&f.missed_people!==f.missed)?(' ('+f.missed_people+' logon se)'):''));",
             "H1 summary")
    h = edit(h, "fig('Duty par chhoote call', String(f.missed), f.missed?'bad':'', 'missed');",
             "fig('Duty par chhoote call', String(f.missed)+((f.missed_people&&f.missed_people!==f.missed)?(' ('+f.missed_people+' logon se)'):''), f.missed?'bad':'', 'missed');",
             "H2 figure")
    res = {"calls_console.py": t.encode("utf-8"), "aaj_kaam.html": h.encode("utf-8")}
    want = {}
    if "--expect" in sys.argv:
        for line in open(os.path.join(HERE, "TO_MD5.txt"), encoding="utf-8"):
            if line.strip():
                h5, name = line.split()
                want[name] = h5
    os.makedirs(a[2], exist_ok=True)
    for k, b in res.items():
        if want and want.get(k) != md5(b):
            sys.exit("STOP: the made %s is %s, not the TO %s" % (k, md5(b)[:8], (want.get(k) or "?")[:8]))
        open(os.path.join(a[2], k), "wb").write(b)
        print("made %s %s -> %s" % (k, FROM_MD5[k][:8], md5(b)[:8]))


if __name__ == "__main__":
    main()
