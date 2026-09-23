#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""slip_lookup.py -- kit S372_SLIP_COLUMN (session 279, 23-Sep-2026); S379_PARCHI_TIDY the same day: the day statement
runs in slip-number order and names every skipped number (slip_order, book_check).

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


# ---------------------------------------------------------------- S379: the register's order, and what was skipped
# THE OWNER, 23-Sep-2026: "the slips numbering in the ... day statement should come in an incremental order and not
# randomly. That is how the physical register is designed. If any number is skipped, mention it there."
BOOK_LABEL = {"opd": "OPD", "xp": "X-ray & Proc"}
_REASON = {"cancelled": "cancelled", "spoilt": "spoilt", "missing": "no reason given yet"}
CARRY_MAX = 50              # a jump from the day before larger than this is a new book, not a gap


def slip_order(rows, slips, section):
    """Rows with a physical slip first, in slip-number order; rows with none after them, in the order given."""
    have, none = [], []
    for i, l in enumerate(rows):
        s = slip_no(slips, section, l["clinic_id"])
        (have if s else none).append((int(s) if s else 0, i, l))
    have.sort(key=lambda x: (x[0], x[1]))
    return [l for _, _, l in have] + [l for _, _, l in none]


def book_check(con, date):
    """One entry per book used that day: its first and last number, how many were written, and every number in
    between -- and back to the day before's last number -- that is not a written slip, with its reason.
    Reads the slip table only. Never raises; no table, no entries."""
    out = []
    try:
        for series in ("opd", "xp"):
            day = con.execute("SELECT slip_no, state FROM slip WHERE series=? AND day=? AND state<>'void'",
                              (series, date)).fetchall()
            if not day:
                continue
            nos = [int(r[0]) for r in day]
            first, last = min(nos), max(nos)
            written = sum(1 for r in day if str(r[1]) == "ok")
            start = first
            p = con.execute("SELECT MAX(slip_no) FROM slip WHERE series=? AND day<? AND state<>'void' AND slip_no<?",
                            (series, date, first)).fetchone()
            if p and p[0] is not None and 0 < first - int(p[0]) - 1 <= CARRY_MAX:
                start = int(p[0]) + 1
            seen = {}
            for no, st in con.execute("SELECT slip_no, state FROM slip WHERE series=? AND state<>'void' "
                                      "AND slip_no BETWEEN ? AND ?", (series, start, last)):
                if seen.get(int(no)) != "ok":
                    seen[int(no)] = str(st)
            skipped = []
            for n in range(start, last + 1):
                st = seen.get(n)
                if st == "ok":
                    continue
                skipped.append((n, _REASON.get(st, "not written")))
            out.append({"series": series, "label": BOOK_LABEL[series], "first": first, "last": last,
                        "written": written, "skipped": skipped})
    except Exception:                       # noqa: BLE001 -- a box without the slip log: nothing to say
        return []
    return out
