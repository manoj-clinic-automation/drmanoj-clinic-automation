#!/usr/bin/env python3
"""make_s727.py -- kit S727 (session 390, the parent, 06-Nov-2026). On S724's file (ffbe8db2).
   python make_s727.py <live staff_register.py> <out> [--expect <md5>]
A LOCKED month's approvals are history: its flow page, its sheet pages and its lock desk never call them stale (the live
read after S724: October -- locked 06-Nov 07:19 and paid -- asked for 'approve again'). Unlocked months are unchanged."""
import hashlib, sys

EDITS = [
('''def _stale_note(st):''',
'''def _month_locked(ym):
    """S727: True when ym's run is locked -- its approvals are then history, never 'stale'."""
    try:
        con = get_db()
        r = con.execute("SELECT status FROM locked_run WHERE ym=?", (ym,)).fetchone()
        con.close()
        return bool(r and r["status"] == "locked")
    except Exception:
        return False


def _stale_note(st):'''),
('''        if _Pf is not None:
            os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
            st = pack_status(ym, _Pf.compute(ym)["staff"])''',
'''        if _Pf is not None and not _month_locked(ym):          # S727: a locked month's approvals are history
            os.environ.setdefault("ATT_REGISTER_DB", DB_PATH)
            st = pack_status(ym, _Pf.compute(ym)["staff"])'''),
('''        st = pack_status(ym, res["staff"])      # S724: only an approval of these very figures counts''',
'''        st = pack_status(ym, None if _month_locked(ym) else res["staff"])      # S724; S727: not for a locked month'''),
('''    st_pack = pack_status(ym, res_staff if res_staff else None)     # S724''',
'''    st_pack = pack_status(ym, res_staff if (res_staff and not (lr and lr["status"] == "locked")) else None)     # S724; S727'''),
]


def main():
    src, out = sys.argv[1], sys.argv[2]
    s = open(src, encoding="utf-8").read()
    for i, (a, b) in enumerate(EDITS, 1):
        n = s.count(a)
        if n != 1:
            print("make_s727: edit %d matches %d times (must be 1) -- nothing written" % (i, n))
            return 2
        s = s.replace(a, b)
    data = s.encode("utf-8")
    if "--expect" in sys.argv and hashlib.md5(data).hexdigest() != sys.argv[sys.argv.index("--expect") + 1]:
        print("make_s727: the result is %s, not the expected one -- nothing written" % hashlib.md5(data).hexdigest())
        return 3
    open(out, "wb").write(data)
    print("make_s727: %d edits applied -> %s (%s)" % (len(EDITS), out, hashlib.md5(data).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
