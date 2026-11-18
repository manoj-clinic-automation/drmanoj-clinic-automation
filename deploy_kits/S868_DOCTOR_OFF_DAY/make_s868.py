#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s868.py -- kit S868_DOCTOR_OFF_DAY (the parent, S480, 18-Nov-2026). Builds docterz_pickup.py, owner_console.py and
pc_kits.py from the live bytes (the 18-Nov bundle; pc_kits.py as S865 placed it) -- FROM checked by md5, every anchor once.
    python3 make_s868.py <from_dir> <to_dir>"""
import hashlib, os, sys
src, dst = sys.argv[1:3]
FROM = {"docterz_pickup.py": "a26c1467", "owner_console.py": "bbe47872", "pc_kits.py": "9353d510"}
os.makedirs(dst, exist_ok=True)


def rep(t, a, b, w):
    n = t.count(a)
    if n != 1:
        sys.exit("!! anchor %s found %d times" % (w, n))
    return t.replace(a, b)


for n, m in FROM.items():
    if hashlib.md5(open(os.path.join(src, n), "rb").read()).hexdigest()[:8] != m:
        sys.exit("!! %s is not its FROM pin" % n)

# ------------------------------------------------------------------ docterz_pickup.py
t = open(os.path.join(src, "docterz_pickup.py"), encoding="utf-8").read()
t = rep(t, '''THE ALARM: no consultation export''', '''S868 (18-Nov-2026, the owner: on the days he does not sit, the EMPTY consultation report was set aside as "no date in the
file" and his pages called the day missing): a consultation report with no patients in it belongs to the day it was exported
(export_day, as a follow-up log) and, when that day has no OPD slip or is marked 'not sitting' (off_days.py), it is taken as
that day's report -- CURRENT, 0 rows, nothing stored (reception's PC never gets an empty file back) -- and the day is marked
not sitting by the server. An empty report on a day WITH OPD slips is set aside and said. A report WITH patients clears a
not-sitting mark of its day (he sat). The empty reports set aside before S868 ('no date in the file', 0 rows) are no longer
shouted on his page.
THE ALARM: no consultation export''', "docstring")
t = rep(t, '''def take(con, f, raw, dry=False):''', '''def _s868_off(con, day):
    """S868: (is the day one he did not sit, why) -- marked by him or the server (off_days), or no OPD slip that day."""
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE name='clinic_off_day'").fetchone() and \\
                con.execute("SELECT 1 FROM clinic_off_day WHERE day=?", (day,)).fetchone():
            return True, "marked not sitting"
        n = con.execute("SELECT COUNT(*) FROM slip WHERE day=? AND series='opd' AND state='ok'", (day,)).fetchone()[0]
        return (int(n or 0) == 0), ("no OPD slip that day" if not n else "%d OPD slip(s) that day" % int(n))
    except sqlite3.Error:
        return False, "the slips could not be read"


def take(con, f, raw, dry=False):''', "s868_off")
t = rep(t, '''    kind, day, nrows, note = identify(raw)
''', '''    kind, day, nrows, note = identify(raw)
    s868_empty = None                                          # S868: an empty consultation report -- None / 'off' / 'worked'
    if kind == "consultation" and not day and nrows == 0:
        eday = export_day(f, "")
        if eday:
            off, why_off = _s868_off(con, eday)
            day, s868_empty = eday, ("off" if off else "worked")
            note = ("no consultations in it -- Dr Manoj not sitting (%s)" % why_off) if off else \\
                   ("EMPTY, yet %s -- export the consultation report of that day again" % why_off)
''', "take head")
t = rep(t, '''    if kind != "unknown":
        if not day:
            st, note = "quarantined", "no date in the file"
        else:''', '''    if kind != "unknown":
        if not day:
            st, note = "quarantined", "no date in the file"
        elif s868_empty == "worked":
            st = "quarantined"                                 # S868: an empty report never stands for a day he worked
        else:''', "take quarantine")
t = rep(t, '''            elif cur is not None and nrows < cur["rows"]:''', '''            elif s868_empty and cur is not None and cur["rows"] > 0:   # S868 review 5: an empty report after the day's real one
                st, note = "superseded", "an empty report after the day's real export #%d -- nothing to take" % cur["id"]
            elif cur is not None and nrows < cur["rows"]:''', "take empty after real")
t = rep(t, '''        if st in ("current", "quarantined") and not dry:''', '''        if st in ("current", "quarantined") and not dry and s868_empty != "off":   # S868: an empty report is not kept''', "take store")
t = rep(t, '''        con.commit()
        if kind == "clinical" and st == "current":''', '''        con.commit()
        if kind == "consultation" and st == "current":       # S868: the not-sitting mark follows the report (fail-soft)
            try:
                if s868_empty == "off":
                    con.execute("CREATE TABLE IF NOT EXISTS clinic_off_day (day TEXT PRIMARY KEY, how TEXT NOT NULL, by TEXT NOT NULL "
                                "DEFAULT '', at TEXT NOT NULL DEFAULT '', note TEXT NOT NULL DEFAULT '')")
                    con.execute("INSERT OR IGNORE INTO clinic_off_day (day, how, by, at, note) VALUES (?,?,?,?,?)",
                                (day, "auto", "server", now().isoformat(sep=" ")[:19], "an empty consultation report"))
                elif nrows > 0 and con.execute("SELECT 1 FROM sqlite_master WHERE name='clinic_off_day'").fetchone():
                    con.execute("DELETE FROM clinic_off_day WHERE day=?", (day,))
                con.commit()
            except sqlite3.Error:
                pass
        if kind == "clinical" and st == "current":''', "take after")
t = rep(t, '''        for r in con.execute("SELECT kind, business_date, note FROM docterz_export WHERE status='quarantined' AND substr(taken_at,1,10)>=? "''',
        '''        for r in con.execute("SELECT kind, business_date, note FROM docterz_export WHERE status='quarantined' AND substr(taken_at,1,10)>=? "
                             "AND NOT (kind='consultation' AND rows=0 AND note='no date in the file') "            # S868: the old empty ones''', "owner_lines")
open(os.path.join(dst, "docterz_pickup.py"), "w", encoding="utf-8").write(t)

# ------------------------------------------------------------------ owner_console.py
t = open(os.path.join(src, "owner_console.py"), encoding="utf-8").read()
t = rep(t, '''    except Exception as _ex_s851:                                      # noqa: BLE001 -- the console stands without it
        print("patients_page NOT mounted: %s" % _ex_s851, file=sys.stderr)
''', '''    except Exception as _ex_s851:                                      # noqa: BLE001 -- the console stands without it
        print("patients_page NOT mounted: %s" % _ex_s851, file=sys.stderr)
    try:                                                               # S868: the days he is not sitting (the same gate)
        import off_days as _s868_od                                    # noqa: PLC0415 -- beside this file
        _s868_od.init(app, db_getter, require_fn, unit)
    except Exception as _ex_s868:                                      # noqa: BLE001 -- the console stands without it
        print("off_days NOT mounted: %s" % _ex_s868, file=sys.stderr)
''', "mount")
t = rep(t, '''            if r:
                road = "straight from the reception PC" if str(r["drive_id"] or "").startswith("reception:") else "through Drive"''',
        '''            if r and kind == "consultation" and int(r["rows"] or 0) == 0:     # S868: a day he did not sit
                out.append(L("g", "No consultations on %s -- you were not sitting (%s)" % (
                    dmy(cx["lwd"]), "marked" if str(r["drive_id"] or "").startswith("offday:") else "the empty report reached the server %s"
                    % when(r["taken_at"], today))))
            elif r:
                road = "straight from the reception PC" if str(r["drive_id"] or "").startswith("reception:") else "through Drive"''', "exports row")
t = rep(t, '''                             link="Docterz Revenue"))
        return out

    def entries():''', '''                             link="Docterz Revenue"))
        if os.path.exists(os.path.join(FIN, "off_days.py")):         # S868: one line that opens the not-sitting days
            out.append(L("n", "Not sitting today, or on a day ahead? Mark it -- nothing then asks for that day's consultation report",
                         href="/finance/console/off-days", link="Days not sitting"))
        return out

    def entries():''', "exports tail")
open(os.path.join(dst, "owner_console.py"), "w", encoding="utf-8").write(t)

# ------------------------------------------------------------------ pc_kits.py
t = open(os.path.join(src, "pc_kits.py"), encoding="utf-8").read()
t = rep(t, '''_WORD = {"ok": "Working", "warn": "Needs a look", "bad": "Not working", "info": "No report"}''',
        '''_WORD = {"ok": "Working", "warn": "Needs a look", "bad": "Not working", "info": "Off or not heard"}   # S868: was "No report"


def _s868_state(pc_id, state, detail):
    """S868 (the owner, 18-Nov: the reception PC said "No report" though heard 2 minutes ago): the health page gives the
    reception PC an information row; heard within 20 minutes is Working."""
    if pc_id == "reception" and state == "info":
        m = re.search(r"heard (\\d+) minute", detail or "")
        if m and int(m.group(1)) <= 20:
            return "ok"
    return state''', "word")
t = rep(t, '''    extra = ("; the PC reports %d thing%s to look at" % (len(att), "" if len(att) == 1 else "s")) if att else ""''',
        '''    extra = ("; the PC asks a look at: %s" % _s868_att_words(att)) if att else ""   # S868: what, in fixed words (never its text)''', "lab words")
t = rep(t, '''def _lab_open(now):''', '''_S868_ATT = (("the agent is SWITCHED OFF", "its agent is switched off"), ("Google Drive is NOT running", "Google Drive is not running"),
             ("My Drive is not visible", "My Drive is not visible"), ("Chrome is NOT saving", "Chrome does not save into Docterz exports"),
             ("the Claude app is not running", "the Claude app is not running"), ("disk space is low", "its disk is nearly full"),
             ("X-ray file", "X-ray files are waiting in its inbox"), ("the server has not accepted", "its uploads are refused by the server"),
             ("the Labmate folder", "the Labmate folder is missing"), ("Labmate file(s) not found", "Labmate files are missing"),
             ("the Labmate snapshot has failed", "the Labmate copy keeps failing"))


def _s868_att_words(att):
    """S868 (the owner, 18-Nov: what is the one thing?): the lab PC's attention items named in OUR fixed words, matched by their
    known beginnings (lab_agent.py's own list) -- never the PC's text (S865 review 3)."""
    out = []
    for x in att:
        s = str(x or "")
        w = next((ours for start, ours in _S868_ATT if s.startswith(start)), "one other thing (on the PC itself)")
        if w not in out:
            out.append(w)
    return "; ".join(out[:4])


def _lab_open(now):''', "att words")
t = rep(t, '''        state = row["state"] if row else "info"
        said = row["detail"] if row else "its row on the health page could not be read"''',
        '''        state = row["state"] if row else "info"
        said = row["detail"] if row else "its row on the health page could not be read"
        state = _s868_state(pc["id"], state, said)''', "card state")
open(os.path.join(dst, "pc_kits.py"), "w", encoding="utf-8").write(t)
print("make_s868: " + " · ".join("%s %s" % (n, hashlib.md5(open(os.path.join(dst, n), "rb").read()).hexdigest()[:8]) for n in FROM))
