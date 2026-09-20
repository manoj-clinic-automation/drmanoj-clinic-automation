#!/usr/bin/env python3
"""make_s353.py -- builds the S353 records.py from the S351 file (4c2f38b9): one anchored edit in
_day_studies(), checked to occur exactly once. The kit ships the RESULT as a full file (D202).

THE OWNER'S RULING (20-Sep-2026): "Usually the AP and lateral are done on a single film ... The knee studies is
a unique x-ray where both knee AP standing is taken and both knee lateral view is taken. So that is two films.
Record that as an exception."
"""
import hashlib
import sys

SRC, DST = sys.argv[1], sys.argv[2]
s = open(SRC, encoding="utf-8").read()
assert hashlib.md5(s.encode("utf-8")).hexdigest() == "4c2f38b9eabca883944b32e987600963", "not the S351 file"

OLD = '''def _day_studies(con, day, cid):
    """What the chamber recorded for this patient that day: the slip's X-rays in slip order, else
    Docterz's X-ray lines (study not named there)."""
    st = []
    for s in _rows(con, "SELECT id, slip_no, logged_at FROM slip WHERE day=? AND clinic_id=? AND series='xp' AND state='ok' "
                        "ORDER BY id", (day, cid)):
        for it in _rows(con, "SELECT name, side FROM slip_item WHERE slip_id=? AND kind='xray' ORDER BY sort, id", (s["id"],)):
            st.append({"study": (it["name"] or "X-ray") + (" " + it["side"] if it["side"] else ""),
                       "slip": s["slip_no"], "logged_at": s["logged_at"]})
    if st:
        return st, "slip"
'''
NEW = '''# S353 -- FILMS PER STUDY, the owner's ruling (20-Sep-2026): "usually the AP and lateral are done on a single
# film" -- so a two-view study is ONE film, one photo. The one exception he named: Knee studies (K/S), where both
# knees AP standing go on one film and both knees lateral on a second -- TWO films, two photos. A study's films
# are what the day list counts, so a K/S patient with two pictures reads MATCHED, not "numbered".
TWO_FILM_STUDIES = (("knee studies", ("AP standing", "Lateral")),
                    ("k/s", ("AP standing", "Lateral")))


def study_films(name):
    """The films one study is taken on, in the order they are shot: ['name'] for almost every study,
    ['name -- AP standing', 'name -- Lateral'] for Knee studies (K/S)."""
    low = (name or "").lower()
    for key, films in TWO_FILM_STUDIES:
        if key in low:
            return ["%s \\u2014 %s" % (name, f) for f in films]
    return [name]


def _day_studies(con, day, cid):
    """What the chamber recorded for this patient that day: the slip's X-rays in slip order, else
    Docterz's X-ray lines (study not named there). S353: each study expanded to its films."""
    st = []
    for s in _rows(con, "SELECT id, slip_no, logged_at FROM slip WHERE day=? AND clinic_id=? AND series='xp' AND state='ok' "
                        "ORDER BY id", (day, cid)):
        for it in _rows(con, "SELECT name, side FROM slip_item WHERE slip_id=? AND kind='xray' ORDER BY sort, id", (s["id"],)):
            for film in study_films(it["name"] or "X-ray"):
                st.append({"study": film + (" " + it["side"] if it["side"] else ""),
                           "slip": s["slip_no"], "logged_at": s["logged_at"]})
    if st:
        return st, "slip"
'''
assert s.count(OLD) == 1, "anchor"
s = s.replace(OLD, NEW)
open(DST, "w", encoding="utf-8", newline="\n").write(s)
print("written", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
