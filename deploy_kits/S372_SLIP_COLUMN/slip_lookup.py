#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slip_lookup.py -- kit S372_SLIP_COLUMN (session 279, 23-Sep-2026).

THE OWNER, 23-Sep-2026: "assign that slip number to the daily report which you prepare so that the first column is
the physical slip number. Wherever ... physical slip number is not available, leave it blank for the time being till
the staff get used to this workflow."

One read-only question the day pages ask: which physical slip number goes with this Docterz line? The Chamber Slip
Log (slip_log.py, D557) holds one row per slip: series ('opd' = the reception book, 'xp' = the X-ray & procedure book
in his chamber), the day, the clinic ID. A Docterz line's section decides which book applies: consultations,
revisits and concession cases are OPD slips; X-rays and procedures are X-ray/Proc slips. No match -> blank, never a
guess. Reads the `slip` table only; writes nothing; a missing table (a box without the slip log) means blanks.
"""

SECTION_SERIES = {"consult": "opd", "revisit": "opd", "concession": "opd", "xray": "xp", "proc": "xp"}
_SKIP_STATES = ("void", "cancelled")


def slips_for_day(con, date):
    """{(series, clinic_id): slip_no} for one clinic day, live slips only. Never raises."""
    out = {}
    try:
        rows = con.execute(
            "SELECT series, clinic_id, slip_no, state FROM slip WHERE day=? AND clinic_id IS NOT NULL AND clinic_id<>'' "
            "ORDER BY slip_no", (date,)).fetchall()
    except Exception:                       # noqa: BLE001 -- no slip table on this box: every cell blank
        return out
    for r in rows:
        series, cid, no, state = r[0], str(r[1] or "").strip(), r[2], str(r[3] or "").strip().lower()
        if state in _SKIP_STATES or not cid:
            continue
        out.setdefault((str(series or "").strip().lower(), cid), no)    # the lowest live number for that person that day
    return out


def slip_no(slips, section, clinic_id):
    """The physical slip number for one Docterz line, or '' -- the owner's 'leave it blank'."""
    series = SECTION_SERIES.get(str(section or "").strip().lower())
    cid = str(clinic_id or "").strip()
    if not series or not cid:
        return ""
    no = slips.get((series, cid))
    return str(no) if no is not None else ""
