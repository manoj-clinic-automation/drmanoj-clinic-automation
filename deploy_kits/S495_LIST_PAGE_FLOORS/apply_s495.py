#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s495.py -- S495_LIST_PAGE_FLOORS: the edits, on the real bytes.

   usage: apply_s495.py <folder holding clinic_register.py records.py slip_log.py petty_book.py>   (edited IN PLACE)
          apply_s495.py --pins                                                                     (print FROM -> TO)

Each file must be at its FROM md5 (the live bytes of the 07-Oct-2026 bundle); each anchor must be found exactly as many
times as written here; each result must be the TO md5 this kit was built to. Anything else: nothing is written, exit 1.
The edits put ONE guarded call at each place a page lists dated work for a staff login (see aaj_floor.py):

  clinic_register.py  the counter sheet: register_index and register_list -- the list of days            (2 places, 1 helper)
  records.py          Check karein: checks_page -- the open items                                        (1 place,  1 helper)
  slip_log.py         Report baaki: pending_page -- blood pending / arrived / reports with no order, X-ray pending
                                                                                                         (1 place,  1 helper)
  petty_book.py       the petty book as its keeper sees it: the physiotherapy tick card's 14 days        (1 place)

NOT touched in any of them: a money figure, a count the owner reads (check_line, pending_counts), a write path, a day or an
item opened by its own address.
"""
import hashlib
import os
import sys

PINS = {
    "clinic_register.py": ("eaaea278498b8511ca9a79adf9c20eba", "38d0cb4f0615c9aefcf16d3dee5dfea0"),
    "records.py": ("6492135c9438093a257cf96ef91a9b32", "5b325c6f4c42893ed11d4ace19020bf8"),
    "slip_log.py": ("caef39f69833d5a1d25dd91be834fb97", "87f07d57f61a5c0e031d6ff0f01585d0"),
    "petty_book.py": ("698c988efbb161806ccf9ad5a11efe5a", "d426265eeb9ce95c0f4d6550dfb908cf"),
}

EDITS = {
    "clinic_register.py": [
        (1, '''    t = dt.date.today().isoformat()
    return days if t in days else [t] + list(days)


# ---------------------------------------------------------------- pages
''', '''    t = dt.date.today().isoformat()
    return days if t in days else [t] + list(days)


def _floor_days(con, u, days):
    """S495: a STAFF login is shown no day before the lists' floor (aaj_floor.py: 01-Oct-2026, and only while the lists
    are started). The doctors' list is whole. Display only: no figure is worked from this list, and a day opened by its own
    address is as before. Without the helper, or if it fails, the list is what it has always been."""
    try:
        import aaj_floor                                         # noqa: PLC0415
        f = aaj_floor.floor_for(con, _require, u)
        return [d for d in days if str(d) >= f] if f else days
    except Exception:                                            # noqa: BLE001
        return days


# ---------------------------------------------------------------- pages
'''),
        (2, '''    days = _with_today(days)
''', '''    days = _floor_days(con, u, _with_today(days))
'''),
    ],
    "records.py": [
        (1, '''

@bp.route(CP)
def checks_page():
''', '''

def _floor_items(con, u, items):
    """S495: a STAFF login is shown no item dated before the lists' floor (aaj_floor.py: 01-Oct-2026, and only while the
    lists are started). A doctor's page, the doctors' line (check_line) and an answer by its key are whole. An X-ray file
    with no day of its own is dated by the day it was first seen (xray_filing.planned_at) -- the list's own rule
    (aaj_seed.FLOOR), so the line and the page agree. Without the helper, or if ANYTHING here fails (the read below is
    made directly, not through _rows, so that a failed read is an error and not an empty answer), the page is what it has
    always been."""
    try:
        import aaj_floor                                         # noqa: PLC0415
        f = aaj_floor.floor_for(con, _require, u)
        if not f:
            return items
        seen = {}
        for r in con.execute("SELECT src_id, day, planned_at FROM xray_filing WHERE state='check'").fetchall():
            seen["xf:" + str(r[0])] = r[1] or str(r[2] or "")[:10]
        return [i for i in items if str((seen.get(i["key"]) if i.get("kind") == "xray_file" else i.get("day")) or "") >= f]
    except Exception:                                            # noqa: BLE001
        return items


@bp.route(CP)
def checks_page():
'''),
        (1, '''    con = _db()
    ensure(con)
    items = check_items(con)
    ok = request.args.get("ok", "")
''', '''    con = _db()
    ensure(con)
    items = _floor_items(con, u, check_items(con))
    ok = request.args.get("ok", "")
'''),
    ],
    "slip_log.py": [
        (1, '''

@bp.route("/finance/slips/pending")
def pending_page():
''', '''

def _floor_pend(con, u, *lists):
    """S495: a STAFF login is shown nothing dated before the lists' floor (aaj_floor.py: 01-Oct-2026, and only while the
    lists are started) -- the tests waiting, the reports that came, the reports with no order, the X-ray photos waiting.
    A doctor's page, the doctors' counts (pending_counts) and an action by its key are whole. Without the helper, or if it
    fails, the page is what it has always been."""
    try:
        import aaj_floor                                         # noqa: PLC0415
        f = aaj_floor.floor_for(con, _require, u)
        return tuple(aaj_floor.keep(x, f) for x in lists) if f else lists
    except Exception:                                            # noqa: BLE001
        return lists


@bp.route("/finance/slips/pending")
def pending_page():
'''),
        (1, '''    xs = xray_pending(con) if len(tabs) > 1 else []
''', '''    xs = xray_pending(con) if len(tabs) > 1 else []
    b, g, orph, xs = _floor_pend(con, u, b, g, orph, xs)
'''),
    ],
    "petty_book.py": [
        (1, '''    since = (today - dt.timedelta(days=14)).isoformat()
    rows = _physio_rows(con, since)
''', '''    since = (today - dt.timedelta(days=14)).isoformat()
    try:                                         # S495: no physiotherapy day before the lists' floor on the keeper's card
        import aaj_floor                         # noqa: PLC0415 -- (aaj_floor.py: 01-Oct-2026, only while the lists are started)
        since = max(since, aaj_floor.floor_for(con, _require, u) or since)
    except Exception:                            # noqa: BLE001 -- the card is what it has always been
        pass
    rows = _physio_rows(con, since)
'''),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def edit(name, text):
    for n, a, b in EDITS[name]:
        if text.count(a) != n:
            raise SystemExit("apply_s495: %s: an anchor is there %d time(s), not %d -- nothing written:\n%s" % (name, text.count(a), n, a[:160]))
        if b in text:
            raise SystemExit("apply_s495: %s: the new text is already there -- nothing written" % name)
        text = text.replace(a, b)
    return text


def main():
    if len(sys.argv) == 2 and sys.argv[1] == "--pins":
        for k, (f, t) in PINS.items():
            print("%s  %s -> %s" % (k, f, t))
        return 0
    check_to = "--no-to" not in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        raise SystemExit(__doc__)
    d = args[0]
    out = {}
    for name, (frm, to) in PINS.items():
        raw = open(os.path.join(d, name), "rb").read()
        if md5(raw) != frm:
            raise SystemExit("apply_s495: %s is %s, not %s -- another kit changed it after this one was built; nothing written" % (name, md5(raw), frm))
        new = edit(name, raw.decode("utf-8")).encode("utf-8")
        if check_to and md5(new) != to:
            raise SystemExit("apply_s495: %s edits to %s, not the %s this kit was built to -- nothing written" % (name, md5(new), to))
        compile(new.decode("utf-8"), name, "exec")
        out[name] = new
    for name, new in out.items():
        with open(os.path.join(d, name), "wb") as fh:
            fh.write(new)
        print("%s  %s -> %s" % (name, PINS[name][0], md5(new)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
