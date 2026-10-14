"""make_s554.py -- kit S554_PHYSIO_BACKFILL (14-Oct-2026). Builds the two files from the live bytes by exact, counted edits.
    python3 -B make_s554.py <live dir> <out dir>        writes <out>/physio_book.py and <out>/aaj_duties.json.kit
    python3 -B make_s554.py --pins                      prints the FROM pins
THE OWNER, 14-Oct 06:17 IST: "i want him to backfill from 1st october".
ONE floor date for the whole register, held once: the setting physio_book.from (default 2026-10-01 when absent or not a date).
Every rule reads it: the clinic tab's days, a slip's day, a home visit's and a payment's day (and not before the course's start;
a new home course may be started back to the floor), the report's match and its 'before the register', and the duty's SQL.
The duties file is written as aaj_duties.json.kit (the repository's .gitignore drops *.json; the installer places it as
/root/finance/aaj_duties.json). Every anchor must occur exactly once, else the build stops and writes nothing."""
import hashlib
import json
import os
import sys

PINS = {"physio_book.py": "745130164014ec8d6f90cda839f5521b", "aaj_duties.json": "cb8ac36aa60768216b82c918874a65af"}
DID = "bhati.physio_register"
OLD_FLOOR_SQL = "r.business_date >= '2026-10-14'"
NEW_FLOOR_SQL = "r.business_date >= COALESCE((SELECT value FROM setting WHERE key = 'physio_book.from' AND value <> ''), '2026-10-01')"

EDITS = [
    # ---- 1  the version
    ('APP_VERSION = "S552-PHYSIO-BOOK-1.0"\n',
     'APP_VERSION = "S554-PHYSIO-BOOK-1.1"     # S554: one floor date (setting physio_book.from, default 01-Oct-2026) for every rule\n',
     "version"),
    # ---- 2  the 7-day window becomes the floor
    ("BACK_DAYS = 7                    # a slip or a visit: today and the six days before it\n",
     'FROM_KEY = "physio_book.from"    # S554 (14-Oct-2026, the owner: "i want him to backfill from 1st october"): the register\'s ONE\n'
     'FROM_DEFAULT = "2026-10-01"      # floor date -- slips, visits, payments, the report\'s match and the duty all start here\n'
     "PICK_BUTTONS = 7                 # the clinic tab: the newest seven days as buttons, every day from the floor in a list beside them\n",
     "constants"),
    ("""def _days_back():
    t = _today()
    return [(t - dt.timedelta(days=i)).isoformat() for i in range(BACK_DAYS)]


def _day_ok(d):
    return d in _days_back()
""",
     """def floor_day(con):
    \"\"\"S554: the register's floor -- the setting physio_book.from when it is a date, else 01-Oct-2026.\"\"\"
    v = str(_setting(con, FROM_KEY, FROM_DEFAULT) or "").strip()
    return v if _iso_ok(v) else FROM_DEFAULT


def _days_back(con, lo=None):
    \"\"\"Every day from the floor (or a later `lo`, a course's start) up to today, newest first. Today is always there: a floor
    set in the future must never lock the day's own slips out.\"\"\"
    t = _today()
    f = max(floor_day(con), lo if _iso_ok(lo or "") else "")
    n = (t - dt.date.fromisoformat(f)).days + 1
    return [(t - dt.timedelta(days=i)).isoformat() for i in range(max(n, 1))]


def _day_ok(con, d, lo=None):
    return _iso_ok(d or "") and d in _days_back(con, lo)
""",
     "_days_back / _day_ok"),
    # ---- 3  the words
    ('"amount": "Amount sahi likhiye.", "day": "Tareekh aaj ya pichhle 6 din mein se ho.",\n',
     '"amount": "Amount sahi likhiye.", "day": "Tareekh {floor} se aaj tak mein se ho.",\n'
     '       "start": "Tareekh is patient ke shuru hone ki tareekh se pehle ki nahi ho sakti.",\n',
     "ERR day / start"),
    ('    etext = ERR.get(e, "")\n',
     '    etext = ERR.get(e, "").replace("{floor}", _human(floor_day(con)))\n',
     "_head: the floor in the words"),
    # ---- 4  the clinic tab's day picker
    ("""def _day_bar(day):
    out = []
    for d in _days_back():
        out.append("<a class='dayb%s' href='/finance/physio/book?day=%s'>%s</a>" % (" on" if d == day else "", d, _short(d)))
    return "<div class='days'>%s</div>" % "".join(out)
""",
     """def _day_bar(con, day):
    \"\"\"S554: the newest PICK_BUTTONS days as buttons; when the floor is further back, every day from it in a list beside them.\"\"\"
    days = _days_back(con)
    out = []
    for d in days[:PICK_BUTTONS]:
        out.append("<a class='dayb%s' href='/finance/physio/book?day=%s'>%s</a>" % (" on" if d == day else "", d, _short(d)))
    more = ""
    if len(days) > PICK_BUTTONS:
        opts = "".join("<option value='%s'%s>%s</option>" % (d, " selected" if d == day else "", _short(d)) for d in days)
        more = ("<form method='get' action='/finance/physio/book' class='row dayp'><select name='day' class='note'>%s</select>"
                "<button type='submit' class='save'>Yeh din kholo</button></form>" % opts)
    return "<div class='days'>%s</div>%s" % ("".join(out), more)
""",
     "_day_bar"),
    ("""    day = a.get("day") or _today().isoformat()
    if not _day_ok(day):
""",
     """    day = a.get("day") or _today().isoformat()
    if not _day_ok(con, day):
""",
     "_clinic_tab: the day"),
    ("    out = [_day_bar(day)]\n",
     "    out = [_day_bar(con, day)]\n",
     "_clinic_tab: the bar"),
    ("    lo = (_today() - dt.timedelta(days=BACK_DAYS - 1)).isoformat()\n",
     "    lo = floor_day(con)\n",
     "_match_card: the other days from the floor"),
    # ---- 5  the report's floor
    ("""    \"\"\"Days from the register's first clinic entry on, up to today, where reception and Bhati differ.\"\"\"
    floor = first_clinic_day(con)
    if not floor:
        return []
    lo, hi""",
     """    \"\"\"Days from the register's floor (S554: physio_book.from) up to today, where reception and Bhati differ.\"\"\"
    floor = floor_day(con)
    lo, hi""",
     "differ_days"),
    ("""    floor = first_clinic_day(con)
    out = []
    for d in sorted(days):""",
     """    floor = floor_day(con)
    out = []
    for d in sorted(days):""",
     "month_days: the floor"),
    ("before=(not floor or d < floor))",
     "before=(d < floor))",
     "month_days: before the register"),
    ("""    out.append("<div class='card'><h2>Physio register — %s</h2><p>For Bhati the register is <b>%s</b>.</p>\"""",
     """    out.append("<div class='card'><h2>Physio register — %s</h2><p>For Bhati the register is <b>%s</b>. Days are matched from <b>%s</b>.</p>\"""",
     "report: the floor said"),
    ("""                   dt.date.fromisoformat(first).strftime("%B %Y"), "OPEN" if on else "CLOSED (only the doctors see it)",\n""",
     """                   dt.date.fromisoformat(first).strftime("%B %Y"), "OPEN" if on else "CLOSED (only the doctors see it)", _human(floor_day(con)),\n""",
     "report: the floor's value"),
    # ---- 6  home visits and payments
    ("""    rt = "<tr><th class='sec'>Ek visit ₹</th><td><input name='rate' class='amt' inputmode='decimal' value='%s'></td></tr>" % "{:g}".format(rate / 100.0)\n""",
     """    rt = ("<tr><th class='sec'>Ek visit ₹</th><td><input name='rate' class='amt' inputmode='decimal' value='%s'></td></tr>" % "{:g}".format(rate / 100.0)
          + "<tr><th class='sec'>Shuru kab hua</th><td><input type='date' name='started' class='note' value='%s' min='%s' max='%s'></td></tr>" % (
              _today().isoformat(), floor_day(con), _today().isoformat()))\n""",
     "_home_tab: the start date"),
    ("""    out.append("<table class='grid'><tbody><tr><th class='sec'>Haal</th><td>%s</td></tr><tr><th class='sec'>Ek visit</th>""",
     """    out.append("<table class='grid'><tbody><tr><th class='sec'>Haal</th><td>%s</td></tr><tr><th class='sec'>Shuru</th><td>%s</td></tr><tr><th class='sec'>Ek visit</th>""",
     "home_patient: the start shown"),
    ("""               "</tbody></table></div>" % (st, _r(c["rate_p"]),""",
     """               "</tbody></table></div>" % (st, _human(c["started"]), _r(c["rate_p"]),""",
     "home_patient: the start's value"),
    ("""    days = "".join("<option value='%s'>%s</option>" % (d, _short(d)) for d in _days_back())\n""",
     """    days = "".join("<option value='%s'>%s</option>" % (d, _short(d)) for d in _days_back(con, c["started"]))\n""",
     "home_patient: the visit's days"),
    ("""<input type='date' name='day' class='note' value='%s' max='%s'></td></tr></tbody></table>\"""",
     """<input type='date' name='day' class='note' value='%s' min='%s' max='%s'></td></tr></tbody></table>\"""",
     "home_patient: the payment's min"),
    ("""cid, ("{:g}".format(s["due"] / 100.0)) if s["due"] > 0 else "", _today().isoformat(), _today().isoformat()))\n""",
     """cid, ("{:g}".format(s["due"] / 100.0)) if s["due"] > 0 else "", _today().isoformat(), _days_back(con, c["started"])[-1], _today().isoformat()))\n""",
     "home_patient: the payment's min value"),
    ("""    keep = dict(day=day, pick=f.get("pick") or "")
    if not _day_ok(day):
""",
     """    keep = dict(day=day, pick=f.get("pick") or "")
    if not _day_ok(con, day):
""",
     "post_slip: the day"),
    ("""        return _back("/finance/physio/book", tab="home", err="amount", pick=f.get("pick") or "")
""",
     """        return _back("/finance/physio/book", tab="home", err="amount", pick=f.get("pick") or "")
    started = (f.get("started") or "").strip() or _today().isoformat()      # S554: may be back-dated to the floor
    if not _day_ok(con, started):
        return _back("/finance/physio/book", tab="home", err="day", pick=f.get("pick") or "")
""",
     "post_home_new: the start checked"),
    ("""                      (pid, "home", rate, "active", _today().isoformat(), _stamp(), who))
    con.commit()
    _audit_safe(con, "physio_course", cur.lastrowid, "insert", None, dict(patient_id=pid, kind="home", rate_p=rate), who)
""",
     """                      (pid, "home", rate, "active", started, _stamp(), who))
    con.commit()
    _audit_safe(con, "physio_course", cur.lastrowid, "insert", None, dict(patient_id=pid, kind="home", rate_p=rate, started=started), who)
""",
     "post_home_new: the start written"),
    ("""    day = f.get("day") or ""
    if not _day_ok(day):
        return _back(path, err="day")
""",
     """    day = f.get("day") or ""
    if not _day_ok(con, day):
        return _back(path, err="day")
    if not _day_ok(con, day, c["started"]):
        return _back(path, err="start")
""",
     "post_home_visit: the day"),
    ("""    if not _iso_ok(day) or day > _today().isoformat() or day < (_today() - dt.timedelta(days=366)).isoformat():
        return _back(path, err="pday")
""",
     """    if not _iso_ok(day) or day > _today().isoformat():
        return _back(path, err="pday")
    if not _day_ok(con, day):
        return _back(path, err="day")
    if not _day_ok(con, day, c["started"]):
        return _back(path, err="start")
""",
     "post_home_pay: the day"),
]


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

    # ---------------------------------------------------------------------------- physio_book.py
    t = got["physio_book.py"]
    assert "physio_book.from" not in t, "physio_book.py already holds physio_book.from"
    for a, b, what in EDITS:
        t = rep(t, a, b, what)
    for gone in ("BACK_DAYS", "_days_back()", "_day_ok(day)", "first_clinic_day(con)\n    if not floor", "days=366", "not floor or"):
        assert gone not in t, "physio_book.py: %r is still there" % gone
    assert t.count("floor_day(con)") >= 8, "physio_book.py: the floor is not read where it must be"
    compile(t, "physio_book.py", "exec")

    # ---------------------------------------------------------------------------- aaj_duties.json: the duty's floor
    j = got["aaj_duties.json"]
    before = json.loads(j)
    j = rep(j, OLD_FLOOR_SQL, NEW_FLOOR_SQL, "duties: the floor in bhati.physio_register's SQL")
    after = json.loads(j)
    assert "2026-10-14" not in j, "duties: 2026-10-14 is still in the file"
    bx = [x for x in before["extra"] if x["id"] == DID][0]
    ax = [x for x in after["extra"] if x["id"] == DID][0]
    assert dict(bx, sql=None) == dict(ax, sql=None) and ax["sql"] == bx["sql"].replace(OLD_FLOOR_SQL, NEW_FLOOR_SQL), "duties: more than the floor changed"
    assert [x for x in before["extra"] if x["id"] != DID] == [x for x in after["extra"] if x["id"] != DID], "duties: another duty changed"
    assert dict(before, extra=None) == dict(after, extra=None), "duties: something outside 'extra' changed"

    outs = {"physio_book.py": t, "aaj_duties.json.kit": j}
    os.makedirs(out, exist_ok=True)
    for name, text in outs.items():
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))
    print("edits: physio_book.py %d counted, aaj_duties.json 1 counted" % len(EDITS))


if __name__ == "__main__":
    if sys.argv[1:2] == ["--pins"]:
        print(" ".join("%s:%s" % kv for kv in sorted(PINS.items())))
    else:
        build(sys.argv[1], sys.argv[2])
