#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s970.py -- kit S970_SLIP_SETTLES (the parent, S531, 27-Nov-2026). Builds to/ from from/ by anchored replacements on the
installed bytes (register_push.py a4e2549e, day_check.py b8007892). Every anchor must occur exactly once.
    python3 make_s970.py <from_dir> <to_dir>
"""
import hashlib
import os
import sys

FROM_PINS = {"register_push.py": "a4e2549e72954d1ed60599a77d20b6a1", "day_check.py": "b80078927cfb481d24b3a7ae77f2348e"}

RP = [
("""It reads only what day_check.check_day reads; it writes register_push and nothing else.""",
 """It reads only what day_check.check_day reads; it writes register_push -- and, from S970, an answer on his list (below).

S970 (the owner, 27-Nov-2026 12:45 IST: "ONLY SLIP OF THIS DRESSING ALSO SETTLES THE MATCH OF MORNING CASH WITH SLIPS, EVEN IF
DOCTERZ ISNT UPDATED, AS UPDATING BACK DATE DOCTERZ I WANT TO AVOID?" -- and 12:46 "YES" to making it automatic). Before a day is
judged, each row of his back-date list whose WHOLE money the register holds (the day check's backdate row with placed and allp:
a slip Docterz does not carry, every part of its money in the register) is answered "Not entering in Docterz" by itself -- not_in_docterz.mark(...,
'outside') as the login 'auto'. The day then matches with no tap and no back-dated Docterz entry; his list shows the answer with
its Undo. A row anyone has answered or undone before is never answered again (an Undo is final). A slip Docterz carries later
leaves his list by itself, its answer with it (not_in_docterz.rows reads Docterz first), so nothing is counted twice.
Never today's day (the evening list is still the staff's).
REGPUSH_AUTO_OUTSIDE=0 turns this alone off. Writes nid_mark rows only through not_in_docterz.mark()."""),
('VERSION = "S968 1"', 'VERSION = "S970 1"'),
("""DC_MOD = None                                             # the walk may hand in a day_check module
""",
 """DC_MOD = None                                             # the walk may hand in a day_check module
NID_MOD = None                                            # the walk may hand in a not_in_docterz module (S970)
AUTO_WHO = "auto"                                         # S970: the login named on an answer given by itself
"""),
("""def judge(con, day, push=True, at=None, from_save=False):
""",
 """def auto_on():
    return cfg("REGPUSH_AUTO_OUTSIDE", "1").lower() not in ("0", "off", "no", "false")


def _nid():
    if NID_MOD is not None:
        return NID_MOD
    import not_in_docterz as nid                          # noqa: PLC0415
    return nid


def _answered_before(con, slip_id, kind):
    \"\"\"True when the row has ANY answer, live or undone (an Undo is final). Unreadable = True: never answer blind.\"\"\"
    try:
        if con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='nid_mark'").fetchone() is None:
            return False                                  # no answer was ever given on this box
        return con.execute("SELECT 1 FROM nid_mark WHERE slip_id=? AND kind=? LIMIT 1", (slip_id, kind)).fetchone() is not None
    except sqlite3.Error:
        return True


def auto_outside(con, chk, day=None, at=None):
    \"\"\"S970: answer 'Not entering in Docterz' for each back-date row whose WHOLE money the register holds (allp: every part of
    the row placed -- cold review: a part-held row is his). Never today's day (its evening list is still the staff's). Returns how many.\"\"\"
    if not auto_on():
        return 0
    if day and day >= (at or now_ist()).date().isoformat():
        return 0
    rows = [b for b in (chk.get("backdate") or []) if b.get("placed") and b.get("allp") and b.get("slip_id")
            and b.get("kind") in ("opd", "xray", "proc")]
    if not rows:
        return 0
    nid = _nid()
    n = 0
    for b in rows:
        try:
            sid = int(b["slip_id"])
        except (TypeError, ValueError):
            continue
        if _answered_before(con, sid, b["kind"]):
            continue
        try:
            nid.mark(con, AUTO_WHO, sid, b["kind"], "outside")
            n += 1
        except Exception:                                 # noqa: BLE001 -- refused (already answered, Docterz carries it): leave it
            try:
                con.rollback()
            except Exception:                             # noqa: BLE001
                pass
    return n


def judge(con, day, push=True, at=None, from_save=False):
"""),
("""    lines = open_lines(chk)
    keys = sorted(lines)
""",
 """    try:
        if auto_outside(con, chk, day, at):               # S970: rows answered by themselves -- read the day afresh
            chk = dc.check_day(con, day)
    except Exception:                                     # noqa: BLE001 -- the push stands without it
        pass
    lines = open_lines(chk)
    keys = sorted(lines)
"""),
]

DC = [
("""    the row counts as in the register when any part of it is.\"\"\"
    for x in rows:
        if x["slip_id"] == r["slip_id"] and x["kind"] == r["kind"]:
            x["amount"] += r["amount"]
            x["what_en"] = "%s + %s" % (x["what_en"], r["what_en"])
            x["what_hi"] = "%s + %s" % (x["what_hi"], r["what_hi"])
            x["placed"] = x["placed"] or r["placed"]
            x["tender"] = x["tender"] or r["tender"]
            return
    rows.append(r)
""",
 """    the row counts as in the register when any part of it is; 'allp' (S970) only when every part is.\"\"\"
    for x in rows:
        if x["slip_id"] == r["slip_id"] and x["kind"] == r["kind"]:
            x["amount"] += r["amount"]
            x["what_en"] = "%s + %s" % (x["what_en"], r["what_en"])
            x["what_hi"] = "%s + %s" % (x["what_hi"], r["what_hi"])
            x["placed"] = x["placed"] or r["placed"]
            x["allp"] = x.get("allp", x["placed"]) and bool(r["placed"])
            x["tender"] = x["tender"] or r["tender"]
            return
    r["allp"] = bool(r["placed"])
    rows.append(r)
"""),
("""        _sa = _s846_act(_s846, w)
""",
 """        _sa = _s846_act(_s846, w)
        if _sa == "outside" and _s962_mkey(w) not in _nid:   # S970 review: his list no longer carries it (Docterz's clinical
            _sa = None                                    # report knows the visit) -- an old answer hides no staff card
"""),
("""    if wl and wl != "manoj":                              # S962: a staff login's answer is named as theirs, never as his
""",
 """    if wl == "auto" and act == "outside":                 # S970: answered by itself -- the slip is made, the register holds it
        en, hi = "kept outside Docterz automatically (the slip was made)", "Docterz ke bahar, apne aap (parchi bani)"
    elif wl and wl != "manoj":                            # S962: a staff login's answer is named as theirs, never as his
"""),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src, dst):
    os.makedirs(dst, exist_ok=True)
    for name, reps in (("register_push.py", RP), ("day_check.py", DC)):
        b = open(os.path.join(src, name), "rb").read()
        if md5(b) != FROM_PINS[name]:
            raise SystemExit("REFUSED: %s is %s, not the installed %s" % (name, md5(b)[:8], FROM_PINS[name][:8]))
        t = b.decode("utf-8")
        for old, new in reps:
            if t.count(old) != 1:
                raise SystemExit("REFUSED: anchor in %s found %d times: %r" % (name, t.count(old), old[:60]))
            t = t.replace(old, new)
        out = t.encode("utf-8")
        open(os.path.join(dst, name), "wb").write(out)
        print("%s %s -> %s" % (name, FROM_PINS[name][:8], md5(out)[:8]))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
