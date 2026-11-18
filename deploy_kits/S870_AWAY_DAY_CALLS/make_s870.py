#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s870.py -- kit S870_AWAY_DAY_CALLS (the parent, S480, 18-Nov-2026). Builds calls_console.py, portal_followups.py, wa_ladder.py and
docterz_missing_alert.py from the 18-Nov bundle's bytes (FROM checked by md5; every anchor once).    python3 make_s870.py <from_dir> <to_dir>"""
import hashlib, os, sys
src, dst = sys.argv[1:3]
FROM = {"calls_console.py": "efd51956", "portal_followups.py": "ed1121ec", "wa_ladder.py": "c5e6a74c", "docterz_missing_alert.py": "9cc227e1"}
os.makedirs(dst, exist_ok=True)


def rep(t, a, b, w):
    n = t.count(a)
    if n != 1:
        sys.exit("!! anchor %s found %d times" % (w, n))
    return t.replace(a, b)


for n, m in FROM.items():
    if hashlib.md5(open(os.path.join(src, n), "rb").read()).hexdigest()[:8] != m:
        sys.exit("!! %s is not its FROM pin" % n)

AWAY = '''

# S870 (the owner, 18-Nov-2026 12:08-12:11: the days he is not sitting): finance.db's clinic_off_day (kit S868, off_days.py)
# names them. A follow-up due on such a day says "Dr Manoj was away -- offer a new date" and no follow-up WhatsApp
# ("tomorrow", "due", "missed", "dropout") is offered for it: it would invite the patient to, or blame him for, a day the
# doctor was not there. Read-only, never raises: no table / no file = no day away.
def s870_away_days(fin_db=None, lo="0000-00-00", hi="9999-99-99"):
    path = fin_db or os.environ.get("FINANCE_DB") or "/root/finance/finance.db"
    try:
        import sqlite3 as _sq                                   # noqa: PLC0415
        con = _sq.connect("file:%s?mode=ro" % path, uri=True, timeout=3)
        try:
            return {str(r[0]) for r in con.execute("SELECT day FROM clinic_off_day WHERE day BETWEEN ? AND ?", (lo, hi))}
        finally:
            con.close()
    except Exception:                                           # noqa: BLE001
        return set()


S870_AWAY_WORDS = "Dr Manoj was away that day -- offer a new date"
'''

# ------------------------------------------------------------------ calls_console.py
t = open(os.path.join(src, "calls_console.py"), encoding="utf-8").read()
t = rep(t, '''def fu_return_day(dd, id_days, fp_days, presc, lo=None):''', AWAY.lstrip("\n") + '''

def fu_return_day(dd, id_days, fp_days, presc, lo=None):''', "away helper")
t = rep(t, '''            r["cid"] = ((p[5] or "").strip() if p else "")
''', '''            r["cid"] = ((p[5] or "").strip() if p else "")
        _away = s870_away_days(fin_db, min(r["dd"] for r in rows).isoformat(), today.isoformat())   # S870
        for r in rows:
            r["away"] = r["dd"].isoformat() in _away
''', "rows away")
t = rep(t, '''{% if r.section and r.section|lower not in ('follow-up','due today','grace period') %} · {{ r.section }}{% endif %}</span>''',
        '''{% if r.section and r.section|lower not in ('follow-up','due today','grace period') %} · {{ r.section }}{% endif %}{% if r.away %} · <b>Dr Manoj was away that day — offer a new date</b>{% endif %}</span>''', "furow")
t = rep(t, '''  <div class="f2">{% if r.phone %}{{ r.phone_h }}{% else %}no mobile{% endif %} · due {{ r.due_wd }}{% if r.dx %} · {{ r.dx }}{% endif %}</div>''',
        '''  <div class="f2">{% if r.phone %}{{ r.phone_h }}{% else %}no mobile{% endif %} · due {{ r.due_wd }}{% if r.dx %} · {{ r.dx }}{% endif %}</div>
  {% if r.away %}<div class="f2"><b>Dr Manoj was away that day — offer a new date</b></div>{% endif %}''', "furow2")
open(os.path.join(dst, "calls_console.py"), "w", encoding="utf-8").write(t)

# ------------------------------------------------------------------ portal_followups.py
t = open(os.path.join(src, "portal_followups.py"), encoding="utf-8").read()
t = rep(t, '''def _fmt_date(raw, year):''', AWAY.lstrip("\n") + '''

def s870_iso(raw, year, today=None):
    """'16-Nov' (the Call Sheet's own shape) -> its day: a year written in the cell wins; else the year that puts the date
    nearest today's list (review: '28-Dec' on a January sheet is last December's). '' when it does not read."""
    s = str(raw or "").strip()
    m = re.match(r"(\\d{1,2})[-\\s/]([A-Za-z]{3})(?:[-\\s/](\\d{4}))?", s)
    if not m:
        return ""
    base = today or today_ist()
    years = [int(m.group(3))] if m.group(3) else [base.year - 1, base.year, base.year + 1]
    best = None
    for y in years:
        try:
            d = _dt.datetime.strptime("%02d %s %d" % (int(m.group(1)), m.group(2).title(), y), "%d %b %Y").date()
        except ValueError:
            continue
        if best is None or abs((d - base).days) < abs((best - base).days):
            best = d
    return best.isoformat() if best else ""


def _fmt_date(raw, year):''', "fu helpers")
t = rep(t, '''    sections = []; cur = None; in_table = False
    for r in rows:''', '''    sections = []; cur = None; in_table = False
    away = s870_away_days()                                     # S870: the days Dr Manoj was not sitting
    for r in rows:''', "parse away")
t = rep(t, '''            tpl, ok = od_template(od)
            sec_is_fu = "FOLLOW" in (cur["name"] or "").upper()''', '''            tpl, ok = od_template(od)
            is_away = bool(away) and s870_iso(date_raw, year) in away             # S870: never a follow-up message for it
            if is_away:
                tpl, ok = "", False
                status = (status + " · " if status else "") + S870_AWAY_WORDS
            sec_is_fu = "FOLLOW" in (cur["name"] or "").upper()''', "parse row")
t = rep(t, '''                "template": tpl if (ok and sec_is_fu) else "",
                "sendable": sendable})''', '''                "template": tpl if (ok and sec_is_fu) else "",
                "sendable": sendable, "away": is_away})''', "row away")
open(os.path.join(dst, "portal_followups.py"), "w", encoding="utf-8").write(t)
# ------------------------------------------------------------------ wa_ladder.py
t = open(os.path.join(src, "wa_ladder.py"), encoding="utf-8").read()
t = rep(t, '''        fresh = {"last_visit": con.execute("SELECT MAX(visit_date) FROM patient_visit").fetchone()[0] or "",''',
        '''        try:                                                           # S870: the days Dr Manoj was not sitting (S868)
            away = {str(r[0]) for r in con.execute("SELECT day FROM clinic_off_day WHERE day BETWEEN ? AND ?", (off(-15), off(2)))}
        except sqlite3.Error:                                          # no table: no day away
            away = set()
        fresh = {"last_visit": con.execute("SELECT MAX(visit_date) FROM patient_visit").fetchone()[0] or "",''', "wl away read")
t = rep(t, '''        raw[k].append(person(cid, fu, uid))
''', '''        p_ = person(cid, fu, uid)
        p_["iso"] = fu                                                 # S870: the follow-up day, to hold an away day's row
        raw[k].append(p_)
''', "wl iso")
t = rep(t, '''            elif not mob:
                r["hold"] = ("%d different mobiles on record" % r["many"]) if r.get("many") else "no mobile number on record"''',
        '''            elif k in ("tomorrow", "due1", "due5", "overdue", "appt") and r.get("iso") in away:
                r["hold"] = "Dr Manoj was away that day -- offer a new date by a call"            # S870
            elif not mob:
                r["hold"] = ("%d different mobiles on record" % r["many"]) if r.get("many") else "no mobile number on record"''', "wl hold")
t = rep(t, '''            raw["appt"].append({"name": name or "?", "cid": "", "mobile": mob, "last4": mob[-4:], "date": _nice(at), "hold": "", "tick": False, "many": 0})''',
        '''            raw["appt"].append({"name": name or "?", "cid": "", "mobile": mob, "last4": mob[-4:], "date": _nice(at), "hold": "", "tick": False, "many": 0,
                                "iso": (at or "")[:10]})                       # S870 review: a booking on a not-sitting day''', "wl appt iso")
open(os.path.join(dst, "wa_ladder.py"), "w", encoding="utf-8").write(t)
# ------------------------------------------------------------------ docterz_missing_alert.py (S868 review SHOULD 2)
t = open(os.path.join(src, "docterz_missing_alert.py"), encoding="utf-8").read()
t = rep(t, '''        c = con.execute(CONS_SQL, (iso,)).fetchone()
''', '''        c = con.execute(CONS_SQL, (iso,)).fetchone()
        try:                                                           # S870: the row a not-sitting mark writes (S868)
            cm = bool(c) and con.execute("SELECT 1 FROM docterz_export WHERE kind='consultation' AND business_date=? AND "
                                         "status='current' AND drive_id NOT LIKE 'offday:%' LIMIT 1", (iso,)).fetchone() is None
        except sqlite3.Error:
            cm = False
''', "dma read")
t = rep(t, '''        return {"first": first, "cons": bool(c), "fu_row": bool(f), "fu": bool(f) and not short,''',
        '''        return {"first": first, "cons": bool(c), "cons_mark": cm, "fu_row": bool(f), "fu": bool(f) and not short,''', "dma return")
t = rep(t, '''    if st["cons"]:
        signs.append("the consultation report came")''', '''    if st["cons"] and not st.get("cons_mark"):                         # S870: his not-sitting mark is no sign the clinic worked
        signs.append("the consultation report came")''', "dma judge")
open(os.path.join(dst, "docterz_missing_alert.py"), "w", encoding="utf-8").write(t)
print("make_s870: " + " · ".join("%s %s" % (n, hashlib.md5(open(os.path.join(dst, n), "rb").read()).hexdigest()[:8]) for n in FROM))
