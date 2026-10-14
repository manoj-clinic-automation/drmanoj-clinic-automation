"""make_s553.py -- kit S553_BHATI_SLIP_DUTY (14-Oct-2026). Builds the two files from the live bytes by exact, counted edits.
    python3 -B make_s553.py <live dir> <out dir>        writes <out>/aaj_seed.py and <out>/aaj_duties.json.kit
    python3 -B make_s553.py --pins                      prints the FROM pins
The duties file is written as aaj_duties.json.kit (the repository's .gitignore drops *.json; the installer places it as
/root/finance/aaj_duties.json). Every anchor must occur exactly once, else the build stops and writes nothing."""
import hashlib
import json
import os
import sys

PINS = {"aaj_duties.json": "2d6d30ebe73ff721d5591743c86eebb1", "aaj_seed.py": "156ded1ee17b852b4a30e94be453ca61"}

# The duty (aaj_duties.json, 'extra'). Due when a day D with 2026-10-14 <= D < today has reception's physio money > 0 and
# Bhati's live clinic slips of D do not equal reception's cash and UPI, mode by mode. n = such days, since = the oldest.
SQL = ("SELECT COUNT(*) AS n, MIN(r.business_date) AS since FROM clinic_physio_day r WHERE r.business_date >= '2026-10-14' "
       "AND r.business_date < date('now','localtime') AND COALESCE(r.cash_p,0) + COALESCE(r.upi_p,0) > 0 AND "
       "(COALESCE(r.cash_p,0) <> (SELECT COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id = s.course_id "
       "WHERE c.kind = 'clinic' AND s.day = r.business_date AND s.voided_at = '' AND s.mode = 'cash') OR "
       "COALESCE(r.upi_p,0) <> (SELECT COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id = s.course_id "
       "WHERE c.kind = 'clinic' AND s.day = r.business_date AND s.voided_at = '' AND s.mode = 'upi'))")
DUTY = {
    "id": "bhati.physio_register",
    "person": "bhati",
    "kind": "sql",
    "group": "open",
    "allowed_days": 1,
    "hi": "Physio slips register mein likhiye -- {since} ki slips reception ke hisaab se nahin mil rahi",
    "how_hi": ("Button us din ka Physio register kholta hai. Us din ki har slip Cash / UPI ke saath likhiye; galat entry "
               "'Galat entry hatao' se hataiye. Aapka Cash aur UPI reception ke likhe se milte hi yeh line apne aap hat jaayegi."),
    "en": "Bhati: physiotherapy slips of {since} not entered in his register, or not agreeing with reception",
    "tile": "Physiotherapy",
    "door": "/finance/physio/book",
    "sql": SQL,
    "ok_hi": "Physio slips: register reception ke hisaab se mil raha hai",
}
# The panel line (aaj_seed.PEOPLE['bhati']). Its 'hi' is what Bhati reads, shown as written (aaj_kaam.py does not fill
# {since} into a panel line), so the day is not in it: the button opens that day.
LINE_HI = "Physio slips register mein likhiye — reception ke hisaab se nahin mil rahi"
LINE_EN = "Bhati: physiotherapy slips of a day not entered in his register, or not agreeing with reception. Opens that day."
DOOR = "/finance/physio/book?day={since}"


def rep(s, a, b, what):
    n = s.count(a)
    assert n == 1, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    got = {}
    for name, pin in PINS.items():
        b = open(os.path.join(live, name), "rb").read()
        assert hashlib.md5(b).hexdigest() == pin, "%s: FROM pin differs (%s) -- STOP" % (name, hashlib.md5(b).hexdigest())
        got[name] = b.decode("utf-8")

    # ---------------------------------------------------------------------------- aaj_duties.json: one 'extra' duty
    j = got["aaj_duties.json"]
    assert '"id": "bhati.physio_register"' not in j, "aaj_duties.json already holds bhati.physio_register"
    block = "\n".join("  " + ln for ln in json.dumps(DUTY, indent=1, ensure_ascii=False).splitlines())
    j = rep(j, '''   "en": "Bhati: petty cash in hand agrees with the book",
   "tile": "Petty book",
   "door": "/finance/petty"
  },
''', '''   "en": "Bhati: petty cash in hand agrees with the book",
   "tile": "Petty book",
   "door": "/finance/petty"
  },
%s,
''' % block, "duties: after bhati.petty_cash_match")
    d = json.loads(j)
    ids = [x.get("id") for x in d["extra"]]
    assert ids.count("bhati.physio_register") == 1 and len(ids) == len(set(ids)), "duties: ids not unique"
    assert [x for x in d["extra"] if x["id"] == "bhati.physio_register"][0] == DUTY, "duties: the new duty did not read back"

    # ---------------------------------------------------------------------------- aaj_seed.py: the door, and Bhati's line
    t = got["aaj_seed.py"]
    assert "bhati.physio_register" not in t, "aaj_seed.py already names bhati.physio_register"
    t = rep(t, ''' 'shavez.match_check': {'door': '/finance/clinic/match/{since}'}}
''', ''' 'shavez.match_check': {'door': '/finance/clinic/match/{since}'},
 'bhati.physio_register': {'door': '%s'}}   # S553: his register's clinic tab on the day
''' % DOOR, "seed: ENGINE door")
    t = rep(t, '''            {'id': 'bhati.petty_cash_match',
             'hi': 'Haath ka petty cash book se milaiye',
             'en': 'Petty cash in hand agrees with the book.',
             'when': 'day',
             'on': True,
             'opens': 'Petty book'}]},
''', '''            {'id': 'bhati.petty_cash_match',
             'hi': 'Haath ka petty cash book se milaiye',
             'en': 'Petty cash in hand agrees with the book.',
             'when': 'day',
             'on': True,
             'opens': 'Petty book'},
            {'id': 'bhati.physio_register',                       # S553 (14-Oct-2026): the owner's word, 05:43 IST
             'hi': '%s',
             'en': '%s',
             'when': 'day',
             'on': True,
             'opens': 'Physiotherapy'}]},
''' % (LINE_HI, LINE_EN), "seed: Bhati's line")
    compile(t, "aaj_seed.py", "exec")

    outs = {"aaj_duties.json.kit": j, "aaj_seed.py": t}
    os.makedirs(out, exist_ok=True)
    for name, text in outs.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--pins"]:
        print(" ".join("%s:%s" % kv for kv in sorted(PINS.items())))
    else:
        build(sys.argv[1], sys.argv[2])
