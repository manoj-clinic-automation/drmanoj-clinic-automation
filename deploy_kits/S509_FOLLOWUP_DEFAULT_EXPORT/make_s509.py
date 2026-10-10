"""make_s509.py -- S509_FOLLOWUP_DEFAULT_EXPORT. Builds docterz_pickup.py and aaj_seed.py from the live bytes (S507's) by exact edits.
    python3 make_s509.py <live dir> <out dir>"""
import hashlib
import os
import sys

PINS = {"docterz_pickup.py": "b54ce6af3bb597cfc7942f6231962cf2", "aaj_seed.py": "bb6bf911e87622ef410814a7952990ac"}
OLD_HINT = "Follow-up log mein agle kaam ke din (Sunday chhodkar) tak ki date honi chahiye -- Docterz ka default ek mahine wala export sabse sahi hai."
NEW_HINT = "Follow-up log: Docterz jo date apne aap dikhata hai (aaj se ek mahina) wahi rehne dijiye aur export kijiye -- date badalne ki zaroorat nahin."


def rep(s, a, b, what, count=1):
    n = s.count(a)
    assert n == count, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    got = {}
    for name, pin in PINS.items():
        b = open(os.path.join(live, name), "rb").read()
        assert hashlib.md5(b).hexdigest() == pin, "%s: FROM pin differs" % name
        got[name] = b.decode("utf-8")
    s = got["docterz_pickup.py"]
    s = rep(s, '''THE ALARM: no consultation export for the last working day''', '''S509 (the owner, 10-Oct-2026 22:38): "we simply open the follow-up logs in Docterz and it shows the default from date as the
current date until one month and we export it as such ... no date fields need to be altered". So a follow-up log's day is
no longer its earliest due date minus one (that rule needed the start date moved to tomorrow by hand): it is the day it was
EXPORTED (IST), and an export made before 13:00 belongs to the previous working day (the morning catch-up of a missed evening).
The earliest-due rule stays only for a file with no export time. Docterz's default (today .. one month) reaches the next call
day by itself; the tracker on the owner's PC already anchors a log to the consultation day (03-Oct proved it).
THE ALARM: no consultation export for the last working day''', "docstring")
    s = rep(s, '''def take(con, f, raw, dry=False):''', '''def export_day(f, fallback):
    """S509: the business day of a follow-up log -- the IST day of its export time; before 13:00, the previous working day
    (Sunday skipped). `fallback` (the earliest-due rule) when the file carries no time."""
    t = str((f or {}).get("modifiedTime") or "")
    try:
        u = dt.datetime.strptime(t[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return fallback
    ist = u + dt.timedelta(hours=5, minutes=30)
    d = ist.date()
    if ist.hour < 13:
        d -= dt.timedelta(days=1)
    while d.weekday() == 6:
        d -= dt.timedelta(days=1)
    return d.isoformat()


def take(con, f, raw, dry=False):''', "export_day")
    s = rep(s, '''    kind, day, nrows, note = identify(raw)
    st, stored = kind if kind == "unknown" else "current", ""''', '''    kind, day, nrows, note = identify(raw)
    if kind == "followup" and day:
        day = export_day(f, day)                               # S509: the day it was exported, not its earliest due date minus one
    st, stored = kind if kind == "unknown" else "current", ""''', "take day")
    t = got["aaj_seed.py"]
    t = rep(t, OLD_HINT, NEW_HINT, "seed hints", count=2)
    os.makedirs(out, exist_ok=True)
    for name, text in (("docterz_pickup.py", s), ("aaj_seed.py", t)):
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
