#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aaj_floor.py -- S495_LIST_PAGE_FLOORS (parent; session 298, 07-Oct-2026). The lists' floor, for the PAGES the lists open.

The owner, 06-Oct-2026: the staff's lists start from 1 October, and staff must not see September "on the list or on the
page a line opens". S493 laid the floor under the lists. This is the same floor for four pages of the parent's that a line
opens: the counter sheet's day list (clinic_register.py), Check karein (records.py), Report baaki (slip_log.py) and the
physiotherapy tick card of the petty book (petty_book.py). Each calls floor_for() at ONE place and drops what is older.

floor_for(con, require, u) -> 'YYYY-MM-DD', or None. None means: show the page as it has always been. It is None
  * for the owner (checker of unit 'packs' -- the console's own gate, the lists' own) and for ANY DOCTOR (the signed-in
    login's own role, as the page's own gate handed it over in `u`): the doctors' view of every page is whole;
  * while the lists are not started (setting aaj.staff_on empty): the pages change on the day the lists do, not before,
    and stopping the lists puts the pages back;
  * whenever anything here cannot be told (no setting table, an error, a login that cannot be read): a page never fails,
    and never hides work, because its floor could not be worked out.
The day is the setting aaj.from when it is a date, else aaj_seed.FLOOR_DEFAULT, else 01-Oct-2026 -- aaj_kaam.staff_floor's rule.

Reads two setting rows. Writes nothing. No door of its own.
"""
import datetime as dt

VERSION = "S495 1.0"
DEFAULT = "2026-10-01"


def _default():
    try:
        import aaj_seed                                                # noqa: PLC0415 -- S493's; this file stands without it
        return dt.date.fromisoformat(str(aaj_seed.FLOOR_DEFAULT)[:10]).isoformat()
    except Exception:                                                  # noqa: BLE001
        return DEFAULT


def started(con):
    """Are the lists started? (setting aaj.staff_on = '<since>|<by>'; empty or absent = not started)"""
    r = con.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
    v = str((r[0] if r else "") or "")
    if "|" not in v:
        return False
    try:
        dt.datetime.fromisoformat(v.split("|", 1)[0])
    except ValueError:
        return False
    return True


def day(con):
    """The floor itself, whoever asks."""
    r = con.execute("SELECT value FROM setting WHERE key='aaj.from'").fetchone()
    v = (r[0] if r else None) or None
    if v:
        try:
            return dt.date.fromisoformat(str(v)[:10]).isoformat()
        except ValueError:
            pass
    return _default()


def floor_for(con, require, u=None):
    """The day before which a page shows THIS login nothing -- or None: show the page as it has always been.
    `u` is the login as the page's own gate returned it ({'user', 'role', 'roles'}): a doctor is never floored."""
    try:
        if str((u or {}).get("role") or "").strip().lower() == "doctor":
            return None
        owner, _err = require("checker", unit="packs")
        if owner:
            return None
        if not started(con):
            return None
        return day(con)
    except Exception:                                                  # noqa: BLE001 -- a page never fails for its floor
        return None


def keep(rows, floor, key="day"):
    """rows (dicts, or anything with [key]) dated on or after the floor; all of them when there is no floor."""
    if not floor:
        return rows
    out = []
    for r in rows:
        try:
            d = r[key]
        except Exception:                                              # noqa: BLE001
            d = None
        if str(d or "") >= floor:
            out.append(r)
    return out
