"""make_s876.py <finance dir holding the FROM files> <out dir> -- kit S876_HUB_RECORD_INLINE (D1007, Session 483).
   finance_ui/finance_approvals.html  four anchored patches on S874's page (254c0bbf): a bill's clinic ID in the day panel
       becomes a tap; a sale return's clinic ID the same; the Returns card's detail gets "the patient's record" with the
       same tap; the S876 script (the panel: events newest first, the paper one tap under each, "Open the full record").
   sanjeevni_day.py                   one anchored patch on S874's db30da9f: init mounts patient_events.py (as hub_cash).
   patient_events.py                  NEW -- copied as is.
Every anchor must occur exactly once at its FROM pin; nothing is written when one does not."""
import hashlib
import os
import shutil
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"finance_ui/finance_approvals.html": "254c0bbf47b18a539437a11dec831b0a",
        "sanjeevni_day.py": "db30da9f33ee8319b3c8c15f1d39fb12"}

HTML = [
    # 1 -- the day panel, a bill: the ID inside the name becomes the tap
    ("        who+=s874Mob(b);                                                                   /* S874: the full mobile + Call */\n",
     "        if(b.clinic_id) who=s876Who(who,b.clinic_id);                                     /* S876: the ID opens the record */\n"
     "        who+=s874Mob(b);                                                                   /* S874: the full mobile + Call */\n"),
    # 2 -- the day panel, a sale return
    ("b.clinic_id?('#'+esc(b.clinic_id)):''].filter(Boolean).join(' · ')+s874Mob(b);   /* S874 */",
     "b.clinic_id?s876Chip(b.clinic_id,'row'):''].filter(Boolean).join(' · ')+s874Mob(b);   /* S874 · S876 */"),
    # 3 -- the Returns card: the patient's record, under what the patient bought
    ("  h+=rhBought(r);\n",
     "  h+=rhBought(r);\n"
     "  if(r.clinic_id&&typeof s876Is===\"function\"&&s876Is(r.clinic_id)) h+='<div style=\"margin:4px 0\">'+s876Chip(r.clinic_id,'here','the patient\\'s record')+'</div>';   /* S876 */\n"),
    # 4 -- the script
    ("/* ==== end KIT_S869 ==== */\n",
     "/* ==== end KIT_S869 ==== */\n" + open(os.path.join(HERE, "s876_part.js"), encoding="utf-8").read()),
]
DAY = [
    ("        print(\"hub_cash not mounted: %s\" % ex)\n    return bp\n",
     "        print(\"hub_cash not mounted: %s\" % ex)\n"
     "    try:                                                     # S876: the patient's record inline (patient_events.py)\n"
     "        import patient_events\n"
     "        patient_events.init(app, db_getter, require_fn, unit)\n"
     "    except Exception as ex:                                  # noqa: BLE001 -- the Hub then says the record could not be opened\n"
     "        print(\"patient_events not mounted: %s\" % ex)\n"
     "    return bp\n"),
]


def patch(text, pairs, name):
    for a, b in pairs:
        n = text.count(a)
        assert n == 1, "%s: an anchor occurs %d times: %r" % (name, n, a[:70])
        text = text.replace(a, b)
    return text


def main():
    outs = {}
    for f, pin in FROM.items():
        b = open(os.path.join(SRC, f), "rb").read()
        assert hashlib.md5(b).hexdigest() == pin, "%s is not at its FROM pin (%s)" % (f, hashlib.md5(b).hexdigest())
        t = b.decode("utf-8")
        outs[f] = patch(t, HTML if f.endswith(".html") else DAY, f)
    for f, t in outs.items():
        p = os.path.join(OUT, f)
        os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
        open(p, "wb").write(t.encode("utf-8"))
        print(f, hashlib.md5(t.encode("utf-8")).hexdigest())
    shutil.copyfile(os.path.join(HERE, "patient_events.py"), os.path.join(OUT, "patient_events.py"))
    print("patient_events.py", hashlib.md5(open(os.path.join(OUT, "patient_events.py"), "rb").read()).hexdigest())


if __name__ == "__main__":
    main()
