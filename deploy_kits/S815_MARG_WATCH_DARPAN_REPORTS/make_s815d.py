#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s815d.py LIVE OUT -- kit S815 (13-Nov-2026, Sanjeevni session 446): owner_notice.py 8bbfb9ef (S814) -> the five-minute tick first closes
the Marg watch's report asks whose files have come and asks what the cluster rule (D929) asks -- before the pass, fail-soft, whether or not
his phone messages are on (only the ALL_OFF / OWNER_NOTICE_OFF switches stop it). Nothing is told to his phone by this block.
One block appended before the command-line guard; anything else stops the build."""
import hashlib, sys

FROM = "8bbfb9ef8a59e0715eb209da0d155357"
GUARD = 'if __name__ == "__main__":                                        # S756 (F-1207): the guard stands LAST, after every section\n'
BLOCK = '''# ---- S815 (13-Nov-2026, Sanjeevni session 446, kit S815_MARG_WATCH_DARPAN_REPORTS) -------------------------------------------------------------
#  The Marg watch's report asks: closed when their files have come, and the cluster rule's asks made (D929) -- every five minutes, before the
#  pass, its own tables only. Fail-soft: the tick never waits for the Marg watch. Nothing here sends anything.
KIT_S815 = "S815_MARG_WATCH_DARPAN_REPORTS"
_tick_before_s815 = _tick


def _tick(con, now=None):                                         # noqa: F811 -- S815
    try:
        if not _off():
            import marg_billwatch as BW                           # noqa: PLC0415
            BW.rpt_tick(con)
    except Exception:                                             # noqa: BLE001
        try:
            con.rollback()
        except sqlite3.Error:
            pass
    return _tick_before_s815(con, now)
# ---- S815 end -------------------------------------------------------------------------------------------------------------------------------


'''


def main():
    src, out = sys.argv[1:3]
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        raise SystemExit("the live file is not %s -- stopped" % FROM[:8])
    s = raw.decode("utf-8")
    if s.count(GUARD) != 1:
        raise SystemExit("the guard is not found once -- stopped")
    s = s.replace(GUARD, BLOCK + GUARD)
    b = s.encode("utf-8")
    open(out, "wb").write(b)
    print(hashlib.md5(b).hexdigest())


if __name__ == "__main__":
    main()
