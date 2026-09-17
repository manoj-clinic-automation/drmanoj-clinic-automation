#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update_legs_s309.py -- S309 (F-517): the Docterz freshness leg, tightened.

THE FAULT (F-517, S265): the leg "clinic day revenue ingest" still carries the 200-hour window and the
note "docterz_ingest.py is run by hand today ... Tighten to 26 h the day it gets a timer." It has had a
timer since S238 and, since S291 (17-Sep), runs every ten minutes all day. At 200 h the leg stays silent
through eight days of no data at all.

THE WINDOW, MEASURED, NOT ASSUMED. F-517 proposed 26 h. The leg watches the DATA (the newest taken_at in
clinic_day_revenue), not the job, and the data only lands when Docterz has a new day sheet. The 17-Sep
database shows real quiet spells of 24.0 h and 28.7 h in the week before, and 69.9 h across 12-13 Sep,
before the PC's auto-pickup settled. A 26 h window would therefore cry wolf on a quiet Sunday or a
morning after the PC was off. This kit sets 50 h -- the file's own documented window for "a job that may
legitimately be quiet over a closed Sunday" -- and says so in the note. Tightening further is a later
decision, once a month of the every-ten-minute schedule has been seen.

WHAT IT TOUCHES: exactly two strings inside one leg object of the legs file -- the window and the note.
Every other byte of the file is kept as it is (this is a TEXT edit, verified against a parsed compare;
the file is hand-formatted with one-space indent and is not re-serialised). A backup is written beside
the file first. Nothing else on the box is touched and no service is restarted: the collector reads this
file on each run.

Usage:
  update_legs_s309.py --check [--file PATH]     read-only: what the leg says now
  update_legs_s309.py --apply [--file PATH]     make the change (idempotent; ALREADY when done)
"""
import hashlib
import json
import os
import re
import sys

LEG_NAME = "clinic day revenue ingest"
OLD_H, NEW_H = 200, 50
NEW_NOTE = ("watches the data it lands, not a log: the newest row in clinic_day_revenue. "
            "docterz_ingest.py has run on a timer since S238 and every ten minutes all day since S291 "
            "(17-Sep-2026), so the 200 h window of its hand-run days is gone (F-517). 50 h: a day sheet "
            "may legitimately not arrive over a closed Sunday, or on a morning after the clinic PC was "
            "off overnight -- measured quiet spells of 24.0 h and 28.7 h in the week to 17-Sep. Tighten "
            "to 26 h once a month of the ten-minute schedule has been seen.")
DEFAULT_FILE = "/root/finance/freshness_legs.json"
CONF = "/root/finance/freshness.conf"


def resolve_file(arg):
    """The path the live collector reads: --file, else LEGS_FILE from freshness.conf, else the default.
    The conf may hold secrets; only this one key is read and nothing from it is printed."""
    if arg:
        return arg
    try:
        with open(CONF, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LEGS_FILE") and "=" in line:
                    v = line.split("=", 1)[1].strip()
                    if v:
                        return v
    except OSError:
        pass
    return DEFAULT_FILE


def md5_text(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def leg_span(text):
    """(start, end) of the one leg object that carries LEG_NAME, or (None, None)."""
    key = '"name": "%s"' % LEG_NAME
    i = text.find(key)
    if i < 0:
        return None, None
    start = text.rfind("{", 0, i)
    end = text.find("}", i)
    if start < 0 or end < 0:
        return None, None
    return start, end + 1


def current(text):
    """(window, note) as the file says now, or (None, None)."""
    s, e = leg_span(text)
    if s is None:
        return None, None
    try:
        leg = json.loads(text[s:e])
    except ValueError:
        return None, None
    return leg.get("max_age_h"), leg.get("note")


def rewrite(text):
    """The new text, or an error string. Two replacements inside the leg object, nothing else."""
    s, e = leg_span(text)
    if s is None:
        return None, "the leg %r is not in this file" % LEG_NAME
    block = text[s:e]
    nb, n1 = re.subn(r'("max_age_h"\s*:\s*)%d\b' % OLD_H, lambda m: m.group(1) + str(NEW_H), block)
    if n1 != 1:
        return None, "the %d h window is not in the leg exactly once (found %d)" % (OLD_H, n1)
    nb, n2 = re.subn(r'("note"\s*:\s*)"(?:[^"\\]|\\.)*"',
                     lambda m: m.group(1) + json.dumps(NEW_NOTE, ensure_ascii=False), nb)
    if n2 != 1:
        return None, "the note is not in the leg exactly once (found %d)" % n2
    new = text[:s] + nb + text[e:]
    # the parsed compare: only this leg's window and note may have moved
    try:
        a, b = json.loads(text), json.loads(new)
    except ValueError as ex:
        return None, "the edit did not stay valid JSON: %s" % ex
    if len(a.get("legs", [])) != len(b.get("legs", [])) or a.get("_about") != b.get("_about") \
            or a.get("_windows") != b.get("_windows"):
        return None, "the file's shape changed -- refusing"
    for la, lb in zip(a["legs"], b["legs"]):
        if la["name"] == LEG_NAME:
            if lb["max_age_h"] != NEW_H or lb["note"] != NEW_NOTE:
                return None, "the leg did not take the new window or note"
            la = dict(la); lb = dict(lb)
            la.pop("max_age_h"); la.pop("note"); lb.pop("max_age_h"); lb.pop("note")
            if la != lb:
                return None, "something else in the leg changed -- refusing"
        elif la != lb:
            return None, "another leg changed -- refusing"
    return new, ""


def data_age_h(text, path):
    """Hours since the newest row the leg watches, read-only, or (None, why). The leg names its own
    database, table and column, so nothing here is hard-coded but the clock."""
    import datetime
    import sqlite3
    s_, e_ = leg_span(text)
    if s_ is None:
        return None, "leg not found"
    try:
        leg = json.loads(text[s_:e_])
    except ValueError as ex:
        return None, str(ex)
    if leg.get("kind") != "sqlite_max":
        return None, "not a sqlite_max leg"
    db, tbl, col = leg.get("target"), leg.get("table"), leg.get("column")
    if not (db and tbl and col) or not os.path.isfile(db):
        return None, "database not readable here"
    try:
        con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        row = con.execute("SELECT MAX(%s) FROM %s" % (col, tbl)).fetchone()
        con.close()
    except sqlite3.Error as ex:
        return None, str(ex)
    if not row or not row[0]:
        return None, "no rows"
    try:
        t = datetime.datetime.fromisoformat(str(row[0]).replace("T", " ")[:19])
    except ValueError:
        return None, "unreadable timestamp"
    return (datetime.datetime.now() - t).total_seconds() / 3600.0, ""


def main(argv):
    mode = "--check" if "--check" in argv else ("--apply" if "--apply" in argv else "")
    path = None
    if "--file" in argv:
        path = argv[argv.index("--file") + 1]
    path = resolve_file(path)
    if not mode:
        print(__doc__)
        return 2
    if not os.path.isfile(path):
        print("FAIL: no legs file at", path)
        return 1
    with open(path, encoding="utf-8") as f:
        text = f.read()
    win, note = current(text)
    print("legs file : %s (md5 %s)" % (path, md5_text(text)))
    print("leg       : %s" % LEG_NAME)
    print("window now: %s h" % win)
    print("note now  : %s" % ((note or "")[:90] + ("..." if note and len(note) > 90 else "")))
    age, why = data_age_h(text, path)
    if age is None:
        print("data age  : not read here (%s)" % why)
    else:
        print("data age  : %.1f h since the newest row the leg watches" % age)
        if age > NEW_H:
            print("NOTE: at %d h this leg would go red the moment the collector next runs." % NEW_H)
    if win == NEW_H and note == NEW_NOTE:
        print("RESULT ALREADY -- this leg already carries the S309 window and note.")
        return 0
    if mode == "--check":
        print("RESULT PENDING -- --apply would set %d h and rewrite the note." % NEW_H)
        return 0
    if age is not None and age > NEW_H and "--even-if-red" not in argv:
        print("FAIL: the data is already %.1f h old, older than the %d h window. Nothing changed --"
              " the window is not the problem to fix first. Re-run with --even-if-red to set it anyway."
              % (age, NEW_H))
        return 1
    new, err = rewrite(text)
    if err:
        print("FAIL:", err)
        return 1
    bak = "%s.bak_S309_%s" % (path, md5_text(text)[:8])
    with open(bak, "w", encoding="utf-8") as f:
        f.write(text)
    tmp = path + ".s309.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new)
    os.replace(tmp, path)
    with open(path, encoding="utf-8") as f:
        back = f.read()
    if back != new:
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        print("FAIL: the read-back did not match; the old file has been put back")
        return 1
    w2, n2 = current(back)
    print("backup    : %s" % bak)
    print("window now: %s h  (was %s)" % (w2, win))
    print("new md5   : %s" % md5_text(back))
    print("RESULT APPLIED" if (w2 == NEW_H and n2 == NEW_NOTE) else "FAIL: read-back does not carry the change")
    return 0 if (w2 == NEW_H and n2 == NEW_NOTE) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
