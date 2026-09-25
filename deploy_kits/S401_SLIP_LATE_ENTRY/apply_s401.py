#!/usr/bin/env python3
"""apply_s401.py -- kit S401_SLIP_LATE_ENTRY. Makes the S401 slip_log.py from the live S398 bytes (d208f57a).
The owner, 25-Sep-2026: a parchi missed on the day has no easy way in afterwards -- that day or the next few
days -- and Bhati and reception must be able to do it as Shavez does. So:
  1. every OPD and X-ray/Proc form carries a 'Din' choice (aaj, kal, ... up to LATE_DAYS back); a slip entered
     late is saved ON ITS OWN DAY, so the night report and the room list see it where it belongs;
  2. a new screen 'Chhooti parchi' lists every number left as chhoota in the last LATE_DAYS days, each with
     'Ab likhein' (opens the right form with the number and the day filled in) and Radd / Kharab;
  3. the Docterz 'Report' link shows for Bhati as it does for Shavez;
  4. taking off one's OWN wrong entry needs no reason on the day it was TYPED (it used to be the slip's day).
Usage: python apply_s401.py <S398 slip_log.py> <out>"""
import hashlib, sys
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == "d208f57a4070b5acc02e3e91c7cb86bd", "the source is not S398 slip_log.py"
s = b.decode("utf-8")


def rep(old, new, n=1):
    global s
    assert s.count(old) == n, ("anchor", old[:70], s.count(old))
    s = s.replace(old, new)


# 1 -- the window and the two helpers
rep('''GAP_LIMIT = 25            # a jump bigger than this is a typing slip until the person confirms it
''', '''GAP_LIMIT = 25            # a jump bigger than this is a typing slip until the person confirms it
LATE_DAYS = 7             # S401: a missed parchi can be written up to this many days after its day
REPORT_USERS = ("shavez", "bhati")    # S401, the owner: Bhati does the slip work as Shavez does
''')
rep('''def _today():
    return _now().date().isoformat()
''', '''def _today():
    return _now().date().isoformat()


def _late_day(v):
    """S401: the day a parchi belongs to -- blank is today; else an ISO date from today back LATE_DAYS days.
    Anything else is None (refused), never silently today."""
    t = _now().date()
    if not (v or "").strip():
        return t.isoformat()
    try:
        d = dt.date.fromisoformat(v.strip()[:10])
    except ValueError:
        return None
    return d.isoformat() if t - dt.timedelta(days=LATE_DAYS) <= d <= t else None


def _day_word(iso):
    t = _now().date()
    try:
        n = (t - dt.date.fromisoformat(iso)).days
    except (TypeError, ValueError):
        return iso or ""
    return "Aaj" if n == 0 else "Kal" if n == 1 else dt.date.fromisoformat(iso).strftime("%d-%b")
''')

# 2 -- log_slip writes the slip on its own day
rep('''def log_slip(con, who, series, slip_no, clinic_id, no_id_name, items, confirm_gap=False):
    """Save one slip. Returns (slip_id, note). Raises SlipError with a staff-readable message."""''',
    '''def log_slip(con, who, series, slip_no, clinic_id, no_id_name, items, confirm_gap=False, day=None):
    """Save one slip. Returns (slip_id, note). Raises SlipError with a staff-readable message.
    S401: `day` is the parchi's own day (default today) -- a late entry lands where it belongs."""''')
rep('''    day, now = _today(), _stamp()
    name_seen, is_new = "", 0
    if clinic_id:
        p = patient(con, clinic_id)
        if p:
            name_seen = p[0]
        if is_new_id(con, clinic_id):''', '''    today, now = _today(), _stamp()
    day = day or today
    name_seen, is_new = "", 0
    if clinic_id:
        p = patient(con, clinic_id)
        if p:
            name_seen = p[0]
        if is_new_id(con, clinic_id, day):''')
rep('''    for g in gap:
        if _live(con, series, g) is None:''', '''    if day != today:                                      # S401: a late parchi never marks numbers as chhoota --
        gap = []                                          # the numbers after it belong to today, not to its day
    for g in gap:
        if _live(con, series, g) is None:''')
rep('''                    (day if cur["day"] == day else cur["day"], clinic_id, no_id_name, is_new, name_seen,''',
    '''                    (day if day != today else cur["day"], clinic_id, no_id_name, is_new, name_seen,   # S401''')

# 3 -- save(): read and check the day; errors come back to the same late form
rep('''    try:
        items = items_from_form(con, f) if series == "xp" else []
        sid, note = log_slip(con, _who(u), series, _int(f.get("slip_no")), cid, nm, items,
                             confirm_gap=f.get("gap_ok") == "1")
    except SlipError as ex:
        return _form_err(str(ex))
    r = con.execute("SELECT slip_no FROM slip WHERE id=?", (sid,)).fetchone()
    msg = "Parchi %d save ho gayi." % r["slip_no"] + ((" " + note) if note else "")
    return redirect("/finance/slips?s=" + series + "&ok=" + _q(msg), code=303)''',
    '''    day = _late_day(f.get("day"))                        # S401
    if day is None:
        return _form_err("Din sahi chunein — aaj se %d din pehle tak." % LATE_DAYS)
    late = day != _today()
    try:
        items = items_from_form(con, f) if series == "xp" else []
        sid, note = log_slip(con, _who(u), series, _int(f.get("slip_no")), cid, nm, items,
                             confirm_gap=f.get("gap_ok") == "1", day=day)
    except SlipError as ex:
        if late:
            return redirect("/finance/slips?s=%s&day=%s&no=%s&err=%s" % (series, day, _q(f.get("slip_no") or ""), _q(str(ex))),
                            code=303)
        return _form_err(str(ex))
    r = con.execute("SELECT slip_no FROM slip WHERE id=?", (sid,)).fetchone()
    msg = "Parchi %d save ho gayi" % r["slip_no"] + ((" — %s ki" % _dmy(day)) if late else "") + "." + ((" " + note) if note else "")
    if late or f.get("back") == "late":
        return redirect("/finance/slips?s=late&ok=" + _q(msg), code=303)
    return redirect("/finance/slips?s=" + series + "&ok=" + _q(msg), code=303)''')

# 4 -- set_state: own same-day correction is judged by the day it was typed; the late screen returns to itself
rep('''        same = s["logged_by"] == who and s["day"] == _today()''',
    '''        same = s["logged_by"] == who and (s["logged_at"] or "")[:10] == _today()     # S401: the day it was typed''')
rep('''    return redirect("/finance/slips?s=list&ok=" + _q("Parchi %d: theek kar diya." % s["slip_no"]), code=303)''',
    '''    back = "late" if request.form.get("back") == "late" else "list"                        # S401
    return redirect("/finance/slips?s=" + back + "&ok=" + _q("Parchi %d: theek kar diya." % s["slip_no"]), code=303)''')

# 5 -- the form head: the number (pre-filled when opened from Chhooti parchi) and the day
rep('''    return nx, ('<div class="row"><label>Parchi no.<input name="slip_no" inputmode="numeric" class="no" '
                'value="%d" required></label><span class="sm">book %d–%d</span></div>'
                % (nx, b["first_no"], b["last_no"]))''',
    '''    want_no = _int(request.args.get("no"))              # S401: opened from 'Chhooti parchi'
    want_day = _late_day(request.args.get("day")) or _today()
    head = ""
    if want_day != _today():
        head = ('<p class="warn">Purani parchi: <b>%s</b> ki. Save karne par usi din mein jayegi.</p>'
                '<input type="hidden" name="back" value="late">' % _dmy(want_day))
    return nx, head + ('<div class="row"><label>Parchi no.<input name="slip_no" inputmode="numeric" class="no" '
                       'value="%d" required></label><span class="sm">book %d–%d</span></div>'
                       % (want_no or nx, b["first_no"], b["last_no"])) + _day_select(want_day)


def _day_select(sel):
    """S401: which day the parchi belongs to -- Aaj by default; up to LATE_DAYS back."""
    t = _now().date()
    o = []
    for i in range(LATE_DAYS + 1):
        d = (t - dt.timedelta(days=i)).isoformat()
        o.append('<option value="%s"%s>%s</option>' % (d, " selected" if d == sel else "",
                                                        _day_word(d) + (" (%s)" % _dmy(d)[:6] if i == 1 else "")))
    return '<div class="row small"><label>Din<select name="day" class="dsel">%s</select></label></div>' % "".join(o)''')

# 6a -- the X-ray form's "pick from OPD" list follows the parchi's day
rep('''                   + head2 + _patient_block(opd, True) +''',
    '''                   + head2 + _patient_block(opd if (_late_day(request.args.get("day")) or today) == today else
                                            [x for x in day_slips(con, _late_day(request.args.get("day"))) if x["series"] == "opd"], True) +''')

# 6 -- the tile: the reminder, the new screen, and its place in the menu
rep('''    missing = [s for s in slips if s["state"] == "missing"]
    user = _who(u).lower()''', '''    missing = [s for s in slips if s["state"] == "missing"]
    late_rows = late_missing(con)                         # S401
    user = _who(u).lower()''')
rep('''    if missing:
        rem.append("Chhoote number: %s — 'Aaj ki list' mein batayein" % ", ".join(str(s["slip_no"]) for s in missing[:8]))''',
    '''    if missing:
        rem.append("Chhoote number: %s — 'Aaj ki list' mein batayein" % ", ".join(str(s["slip_no"]) for s in missing[:8]))
    old_miss = [s for s in late_rows if s["day"] != today]
    if old_miss:                                          # S401
        rem.append("Pichhle dinon ki %d chhooti parchi — 'Chhooti parchi' mein likhein" % len(old_miss))''')
rep('''    secs = {"opd": sec_opd, "xp": sec_xp, "room": sec_room, "list": sec_list, "book": sec_book}''',
    '''    # --- S401: missed parchis of the last LATE_DAYS days, written afterwards on their own day
    lr = ['<p class="sm">Jo parchi us din chhoot gayi, yahan se likhein — woh apne hi din mein jayegi. '
          'Jo number is list mein nahi hai: OPD ya X-ray form mein <b>Din</b> chun kar likhein '
          '(%d din pehle tak).</p>' % LATE_DAYS]
    for s in late_rows:
        lr.append('<div class="lrow miss"><span class="no">%d</span> <b>%s</b> <span class="sm">%s</span>'
                  '<a class="more" href="/finance/slips?s=%s&amp;no=%d&amp;day=%s">Ab likhein</a>'
                  '<form method="post" action="/finance/slips/state/%d" class="vf"><input type="hidden" name="back" value="late">'
                  '<button name="act" value="cancelled">Radd</button><button name="act" value="spoilt">Kharab</button></form></div>'
                  % (s["slip_no"], _esc(SERIES_NAME[s["series"]]), _esc(_day_word(s["day"]) + " · " + _dmy(s["day"])[:6]),
                     s["series"], s["slip_no"], s["day"], s["id"]))
    if len(late_rows) == 0:
        lr.append('<p class="sm">Koi chhooti parchi baaki nahi.</p>')
    y = (_now().date() - dt.timedelta(days=1)).isoformat()
    lr.append('<p><a class="more" href="/finance/slips?s=opd&amp;day=%s">+ Kal ki OPD parchi</a> '
              '<a class="more" href="/finance/slips?s=xp&amp;day=%s">+ Kal ki X-ray/Proc parchi</a></p>' % (y, y))
    sec_late = _sec("late", "Chhooti parchi", "%d baaki" % len(late_rows), "".join(lr))

    secs = {"opd": sec_opd, "xp": sec_xp, "room": sec_room, "list": sec_list, "book": sec_book, "late": sec_late}''')
rep('''_SCREENS = {"opd": "OPD parchi", "xp": "X-ray / Proc parchi", "room": "X-ray room work",
            "list": "Aaj ki list", "book": "Start new book", "all": "Parchi \\u2014 sab"}''',
    '''_SCREENS = {"opd": "OPD parchi", "xp": "X-ray / Proc parchi", "room": "X-ray room work",
            "list": "Aaj ki list", "book": "Start new book", "all": "Parchi \\u2014 sab",
            "late": "Chhooti parchi"}                    # S401''')
rep('''        "list": ('<a class="mi" href="/finance/slips?s=list"><b>Aaj ki list</b><span class="%s">%d parchi%s</span></a>'
                 % ("hot" if miss_n else "", today_n, (" \\u00b7 %d chhoote" % miss_n) if miss_n else "")),
    }''', '''        "list": ('<a class="mi" href="/finance/slips?s=list"><b>Aaj ki list</b><span class="%s">%d parchi%s</span></a>'
                 % ("hot" if miss_n else "", today_n, (" \\u00b7 %d chhoote" % miss_n) if miss_n else "")),
    }
    late_n = len(late_missing(con))                        # S401
    items["late"] = ('<a class="mi" href="/finance/slips?s=late"><b>Chhooti parchi</b><span class="%s">%s</span></a>'
                     % ("hot" if late_n else "", ("%d baaki" % late_n) if late_n else "baad mein likhein"))''')
rep('''        order = ["room", "xp", "opd", "blood", "pend", "list"]
    elif user in ("alisha", "shivani"):
        order = ["opd", "xp", "blood", "pend", "room", "list"]
    else:
        order = ["opd", "xp", "blood", "room", "pend", "list"]''',
    '''        order = ["room", "xp", "opd", "blood", "pend", "list", "late"]
    elif user in ("alisha", "shivani"):
        order = ["opd", "xp", "blood", "pend", "room", "list", "late"]
    else:
        order = ["opd", "xp", "blood", "room", "pend", "list", "late"]''')
rep('''    if "checker" in _roles(u) or user == "shavez":
        out.append('<a class="mi" href="/finance/slips/report">''',
    '''    if "checker" in _roles(u) or user in REPORT_USERS:    # S401: Bhati as Shavez
        out.append('<a class="mi" href="/finance/slips/report">''')
# the Report page itself: a maker in REPORT_USERS may open it
rep('''def room_open(con, before_day=None, days=7):''', '''def late_missing(con):
    """S401: every number left 'chhoota' in the last LATE_DAYS days, oldest first."""
    since = (_now().date() - dt.timedelta(days=LATE_DAYS)).isoformat()
    return [dict(r) for r in con.execute("SELECT * FROM slip WHERE state='missing' AND day>=? ORDER BY day, series, slip_no",
                                         (since,))]


def room_open(con, before_day=None, days=7):''')

open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("S401 slip_log.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
