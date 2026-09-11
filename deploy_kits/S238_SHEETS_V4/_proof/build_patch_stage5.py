#!/usr/bin/env python3
"""build_patch_stage5.py -- salary_policy.py v1.10 (2e3fe9fb..., LIVE since 10-Sep 23:20)
-> v1.11 (S238, the owner, 11-Sep-2026): Shivani's cover-duty OT; dates-only staff.
Anchored, exactly-once edits; anything else aborts."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != "2e3fe9fb22cbd5a918115db7c5963e0c":
    sys.exit("source is not the live v1.10")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

rep('''salary_policy.py — v1.10 (S238, the owner's third review)''',
    '''salary_policy.py — v1.11 (S238, the owner, 11-Sep-2026) — OVERTIME IS PAID (ot_pay = 1:
"the incentive for staff not to rush back home"); an optional daily threshold
(ot_threshold_on, default OFF; ot_daily_min 15) ignores punch-out drift; on an extra-duty (cover) day
the cover hours are the extra duty, already credited; overtime counts only AFTER the
cover ends (setting cover_end, 21:00). Staff named in dates_only_staff (Amir Sohail)
leave the attendance grid: Sheet 1 lists only the dates they punched.
v1.10 (S238, the owner's third review)''', "doc")

rep('''    "ot_pay": 0,                # S238: 1 = OT payable enters the net; 0 = shown only (owner to rule)''', '''    "ot_pay": 1,                # S238 (owner 11-Sep-2026): overtime IS paid -- the incentive to stay when the clinic runs late
    "ot_threshold_on": 0,       # S238: 1 = a day's OT below ot_daily_min is ignored (punch-out drift); owner: default OFF
    "ot_daily_min": 15,         # S238: the daily OT threshold in minutes, used only when ot_threshold_on = 1
    "cover_end": "21:00",       # S238: extra-duty (cover) ends; OT on a cover day counts after this
    "dates_only_staff": "Amir Sohail",  # S238: comma-separated; out of the grid, punch dates only''', "defaults")

rep('''        if k == "enforce_from":''', '''        if k == "dates_only_staff":
            clean[k] = ", ".join(x.strip() for x in str(v or "").split(",") if x.strip())
            continue
        if k == "cover_end":
            v = str(v or "").strip()
            if _hhmm(v) is None:
                return False, "cover_end must be a time like 21:00"
            clean[k] = v
            continue
        if k == "enforce_from":''', "save_str")

rep('''def _shift_minutes(info):''', '''def _hhmm(t):
    """'21:00' -> 1260 minutes after midnight; None when it is not a time."""
    try:
        h, m = str(t).strip().split(":")[:2]
        h, m = int(h), int(m)
        return h * 60 + m if 0 <= h < 24 and 0 <= m < 60 else None
    except (ValueError, TypeError):
        return None


def dates_only_names(s):
    return {x.strip().lower() for x in str(s.get("dates_only_staff", "") or "").split(",") if x.strip()}


def _cover_dates(ym):
    """{staff name (lower): set of 'YYYY-MM-DD'} -- the days the register marks EXTRA
    DUTY (cover). Read-only, from the register's own database. Returns (dates, error)."""
    try:
        import sqlite3
        import salary_engine as E
        con = sqlite3.connect(E.DB_PATH)
        out = {}
        for d, nm in con.execute(
                "SELECT r.reg_date, s.name FROM daily_register r JOIN staff s "
                "ON s.staff_id = r.staff_id WHERE r.extra_duty > 0 AND r.reg_date LIKE ?",
                (ym + "-%",)):
            out.setdefault((nm or "").strip().lower(), set()).add(d)
        con.close()
        return out, ""
    except Exception as e:
        return {}, "%s: %s" % (type(e).__name__, e)


def _shift_minutes(info):''', "helpers")

rep('''    holds = hold_state()

    man_adv = manual_advances(ym)''', '''    holds = hold_state()
    cover_dates, cover_err = _cover_dates(ym)

    man_adv = manual_advances(ym)''', "cover_load")

rep('''        ot_min = 0 if exempt else int(a.get("ot_min", 0) or 0)''',
    '''        ot_min = 0 if exempt else int(a.get("ot_min", 0) or 0)
        # S238 v1.11 (the owner): on a COVER day the cover hours are the extra duty,
        # credited separately -- overtime is only what she stayed beyond the cover end.
        # A day's OT below the daily threshold is ignored when the owner switches it on.
        _cov = cover_dates.get(name.strip().lower(), set())
        try:
            _thr = int(float(s.get("ot_daily_min", 15) or 0)) if s.get("ot_threshold_on") else 0
        except (TypeError, ValueError):
            _thr = 0
        if (_cov or _thr) and not exempt:
            _ce = _hhmm(s.get("cover_end", "21:00")) or 1260
            ot_min = 0
            for _d, _c in (a.get("grid") or {}).items():
                if not isinstance(_c, dict) or not _c.get("ot"):
                    continue
                try:
                    _ds = "%s-%02d" % (ym, int(_d))
                except (TypeError, ValueError):
                    continue
                if _ds in _cov:
                    _o = _hhmm(_c.get("out", ""))
                    _day = max(0, _o - _ce) if _o is not None else 0
                else:
                    _day = int(_c.get("ot") or 0)
                if _day > 0 and _day >= _thr:
                    ot_min += _day''', "ot_cover")

rep('''    if not covered:
        notes.append("register grid NOT COVERED for %s — sanctioned leave "''', '''    if cover_err:
        notes.append("extra-duty (cover) days could not be read (%s) — overtime on cover "
                     "days is NOT reduced to the time after %s" % (cover_err, s.get("cover_end")))
    if not covered:
        notes.append("register grid NOT COVERED for %s — sanctioned leave "''', "cover_note")

# ---- Sheet 1: dates-only staff out of the grid; their punch dates instead -------------
rep('''    out.append('<div class="s1grid">')
    for half in halves:''', '''    _donly = dates_only_names(res.get("settings") or {}) if only_uid is None else set()
    _grid_rows = [st for st in rows if st["name"].strip().lower() not in _donly]

    def _punch_days(st):
        ds = []
        for d in sorted(k for k, c in (st.get("grid") or {}).items()
                        if isinstance(c, dict) and c.get("st") == "P"):
            t = "%d" % d
            ds.append("<span class='sunk'>%s</span>" % t
                      if datetime.date(year, mon, d).weekday() == 6 else t)
        return ds

    out.append('<div class="s1grid">')
    for half in halves:''', "grid_rows")
rep('''        out.append("</tr>")
        for st in rows:
            out.append("<tr><td><b>%s</b></td>" % e(st["name"]))''', '''        out.append("</tr>")
        for st in _grid_rows:
            out.append("<tr><td><b>%s</b></td>" % e(st["name"]))''', "grid_loop")
rep('''    out.append('<div class="sub">Cell = arrival time (amber 11–59 min late, red \'''', '''    for st in rows:
        if st["name"].strip().lower() in _donly:
            _pd = _punch_days(st)
            out.append('<div class="sub" style="font-size:13px;margin:4px 0"><b>%s</b> — punched on '
                       '%d day(s): %s</div>' % (e(st["name"]), len(_pd), ", ".join(_pd) or "none"))
    out.append('<div class="sub">Cell = arrival time (amber 11–59 min late, red \'''', "donly_line")
rep('''        absent = st.get("absent", 0)
        lia = st.get("leave_in_absent", 0)
        outst = min(st.get("outst_days", 0), max(0, absent - lia))
        out.append(''', '''        absent = st.get("absent", 0)
        lia = st.get("leave_in_absent", 0)
        outst = min(st.get("outst_days", 0), max(0, absent - lia))
        if st["name"].strip().lower() in _donly:
            _pd = _punch_days(st)
            out.append("<tr><td><b>%s</b></td><td class='n'>%d</td><td class='n'>—</td>"
                       "<td class='n'>—</td><td class='n'>—</td><td class='n'>—</td>"
                       "<td class='dcol'>punched on: %s</td><td class='n'>%d</td><td class='n'>%d</td>%s"
                       "<td class='n'>%d</td>%s%s</tr>"
                       % (e(st["name"]), st["present"], ", ".join(_pd) or "none",
                          st["marks"], st["late_min"],
                          ("<td class='n'>%s</td>" % money(st["late_charge"])) if money_ok else "",
                          st.get("ot_min", 0),
                          ("<td class='n'>%s</td>" % money(st.get("ot_rs", 0))) if money_ok else "",
                          "<td class='rcol'></td>" if print_ else ""))
            continue
        out.append(''', "sum_donly")
rep("""               'without leave (one set of days). OT = minutes beyond shift end on days with a '
               'real out-punch.%s%s</div>'""", """               'without leave (one set of days). OT = minutes beyond shift end on days with a '
               'real out-punch; on an extra-duty (cover) day only the minutes after %s.%s%s%s</div>'""", "s1note_a")
rep("""               % (' Late fine = the whole month\\'s late charge before any hold; OT payable at '""",
    """               % (e(str(res["settings"].get("cover_end", "21:00"))),
                  (' A day under %s min of OT is not counted.' % res["settings"].get("ot_daily_min", 15))
                  if res["settings"].get("ot_threshold_on") else '',
                  ' Late fine = the whole month\\'s late charge before any hold; OT payable at '""", "s1note_b")
# ---- print polish (visual check): no hover wording on paper; Sunday dates underlined ----
rep("""               '&ge;60). Hover for the out-punch. L sanctioned leave · A absent · '""",
    """               '&ge;60).<span class="noprint"> Hover for the out-punch.</span> L sanctioned leave · A absent · '""", "hover")
rep(""" .sunk{color:#4c1d95;font-weight:800;background:#ece6ff;padding:0 2px;border-radius:3px}""",
    """ .sunk{color:#3b0f8a;font-weight:800;text-decoration:underline}""", "sunk")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
