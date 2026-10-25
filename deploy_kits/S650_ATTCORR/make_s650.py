#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s650.py -- builds kit S650_ATTCORR's four changed files from the LIVE bytes (D786, session 354, 25-Oct-2026).

  python3 make_s650.py <dir holding the four live files> <out dir>

Each base file must be the pinned live file (md5 below) or nothing is written. Every edit is an exact piece that must
occur exactly once; the counted edits are printed.
  staff_register.py  1 edit : the hook that installs att_correction.py, just before the __main__ block
  aaj_duties.json    1 edit : three 'fetch' lines appended to 'extra' (reception.attcorr_print, reception.attcorr_enter,
                              shavez.attcorr_check) -- shipped as aaj_duties.json.kit (.gitignore drops *.json)
  aaj_seed.py        2 edits: reception's two lines at the top of her list; Shavez's line after his day check
  owner_console.py   1 edit : the console's Attendance section reads the corrections' state (read-only)
"""
import hashlib
import os
import sys

BASE = {
    "staff_register.py": "0a098cfa315628e3db270602a831edd9",
    "aaj_duties.json": "1c49af3585c63beeeceef8803f112fca",
    "aaj_seed.py": "98f633640ada6e809ce60fa1f0b826a7",
    "owner_console.py": "a6315bfdcc0f4811bf546f89dd96002f",
}

SEP = "# " + "-" * 75
SR_OLD = SEP + "\n# CLI\n" + SEP + '\nif __name__ == "__main__":\n'
HOOK = '''# S650 (D786, session 354, 25-Oct-2026): the month-end attendance correction flow lives in att_correction.py beside
# this file -- its pages under /register/attcorr and the salary lock's wait for the owner's Approve & save. A fault
# there must never take the register down: the register then runs exactly as before, without those pages.
try:
    import att_correction as _attcorr
    _attcorr.install(app, sys.modules[__name__])
except Exception as _attcorr_err:                        # noqa: BLE001
    print("att_correction not installed: %s: %s" % (type(_attcorr_err).__name__, _attcorr_err), file=sys.stderr)


'''

DUTIES_OLD = '''   "fetch": {"url": "/finance/clinic/check/api/mine", "field": "open", "text_field": "text"}
  }
 ]
}'''
DUTIES_NEW = '''   "fetch": {"url": "/finance/clinic/check/api/mine", "field": "open", "text_field": "text"}
  },
  {
   "id": "reception.attcorr_print",
   "person": "alisha",
   "kind": "fetch",
   "group": "open",
   "hi": "Attendance correction sheet print kijiye",
   "en": "Reception: from the 1st, print the month's attendance correction sheet for the staff to tick and sign (S650, D786; read on the page from the register's own door)",
   "tile": "Staff Register",
   "door": "/register/attcorr/sheet",
   "fetch": {"url": "/register/attcorr/api/line", "field": "print_open", "text_field": "print_text"}
  },
  {
   "id": "reception.attcorr_enter",
   "person": "alisha",
   "kind": "fetch",
   "group": "open",
   "hi": "Sign wali sheet se tick bhariye aur Save kijiye",
   "en": "Reception: enter the signed sheet's ticks on screen and Save (S650, D786; read on the page from the register's own door)",
   "tile": "Staff Register",
   "door": "/register/attcorr/enter",
   "fetch": {"url": "/register/attcorr/api/line", "field": "enter_open", "text_field": "enter_text"}
  },
  {
   "id": "shavez.attcorr_check",
   "person": "shavez",
   "kind": "fetch",
   "group": "open",
   "hi": "Attendance correction check kijiye",
   "en": "Shavez: after reception saves, check the month's attendance corrections against the signed sheet and Save (S650, D786; read on the page from the register's own door)",
   "tile": "Staff Register",
   "door": "/register/attcorr/check",
   "fetch": {"url": "/register/attcorr/api/line", "field": "check_open", "text_field": "check_text"}
  }
 ]
}'''

SEED_REC_OLD = "  'lines': [{'id': 'rec.docterz_morning',"
SEED_REC_NEW = """  'lines': [{'id': 'reception.attcorr_print',                  # S650 (D786, 25-Oct-2026): from the 1st, until she saves
             'hi': 'Attendance correction sheet print kijiye',
             'en': "From the 1st: prints the month's attendance correction sheet; each staff member ticks and signs.",
             'when': 'first',
             'on': True,
             'opens': 'Staff Register'},
            {'id': 'reception.attcorr_enter',
             'hi': 'Sign wali sheet se tick bhariye aur Save kijiye',
             'en': "Enters the signed sheet's ticks on screen and saves.",
             'when': 'first',
             'on': True,
             'opens': 'Staff Register'},
            {'id': 'rec.docterz_morning',"""

SEED_SHZ_OLD = """             'opens': 'Day check'}]},
 {'key': 'amir',"""
SEED_SHZ_NEW = """             'opens': 'Day check'},
            {'id': 'shavez.attcorr_check',                     # S650 (D786, 25-Oct-2026): after reception saves
             'hi': 'Attendance correction check kijiye',
             'en': "After reception saves: checks the month's attendance corrections against the signed sheet.",
             'when': 'first',
             'on': True,
             'opens': 'Staff Register'}]},
 {'key': 'amir',"""

CONSOLE_OLD = '''    piece(lines, "The salary month's lock", lock)
'''
CONSOLE_NEW = '''    piece(lines, "The salary month's lock", lock)

    def attcorr():                     # S650 (D786, 25-Oct-2026): the month-end attendance corrections, read-only
        first = dt.date.fromisoformat(today[:8] + "01")
        pm = (first - dt.timedelta(days=1)).isoformat()[:7]
        rc = sqlite3.connect("file:%s?mode=ro" % REGISTER_DB, uri=True, timeout=5)
        try:
            if not rc.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='attcorr_month'").fetchone():
                return None
            m = rc.execute("SELECT entered_by, entered_ts, checked_by, checked_ts, approved_by, approved_ts "
                           "FROM attcorr_month WHERE ym=?", (pm,)).fetchone()
            pend = rc.execute("SELECT COUNT(*) FROM attcorr_day WHERE ym=? AND COALESCE(mark,'') <> "
                              "COALESCE(applied_mark,'')", (pm,)).fetchone()[0]
        finally:
            rc.close()
        if not m or not m[1]:
            return None                # nothing before reception saves (the mock-up)
        mon = dt.date(int(pm[:4]), int(pm[5:7]), 1).strftime("%B")
        href = "/register/attcorr?ym=%s" % pm
        if m[5] and not pend:
            return L("g", "Attendance correction: %s approved by %s %s" % (mon, m[4], when(m[5], today)),
                     href=href, link="the month")
        who = (("checked by %s %s" % (m[2], when(m[3], today))) if m[3]
               else ("entered by %s %s; Shavez has not checked yet" % (m[0], when(m[1], today))))
        return L("w", "Attendance correction: %s ready \\u2014 approve & save" % mon, who=who, href=href, link="approve")

    piece(lines, "Attendance correction", attcorr)
'''

EDITS = {
    "staff_register.py": [(SR_OLD, HOOK + SR_OLD)],
    "aaj_duties.json": [(DUTIES_OLD, DUTIES_NEW)],
    "aaj_seed.py": [(SEED_REC_OLD, SEED_REC_NEW), (SEED_SHZ_OLD, SEED_SHZ_NEW)],
    "owner_console.py": [(CONSOLE_OLD, CONSOLE_NEW)],
}
OUTNAME = {"aaj_duties.json": "aaj_duties.json.kit"}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for name, edits in EDITS.items():
        raw = open(os.path.join(src, name), "rb").read()
        if md5(raw) != BASE[name]:
            sys.exit("STOP: %s is %s, not the pinned live %s -- nothing written" % (name, md5(raw)[:8], BASE[name][:8]))
        txt = raw.decode("utf-8")
        for i, (old, new) in enumerate(edits, 1):
            n = txt.count(old)
            if n != 1:
                sys.exit("STOP: %s edit %d: the piece occurs %d times, not once -- nothing written" % (name, i, n))
            txt = txt.replace(old, new, 1)
        b = txt.encode("utf-8")
        dest = os.path.join(out, OUTNAME.get(name, name))
        with open(dest, "wb") as f:
            f.write(b)
        print("%-18s %s -> %s  %d counted edit(s)" % (name, BASE[name][:8], md5(b), len(edits)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
