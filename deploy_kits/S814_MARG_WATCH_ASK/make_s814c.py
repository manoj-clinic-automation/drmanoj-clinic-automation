#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s814c.py LIVE_ON OUT -- kit S814 (13-Nov-2026, Sanjeevni session 445): owner_notice.py bf3da532 -> one line to his phone when a staff
answer comes back on the Marg watch -- OFF until he turns it on on the page (ask.notice); only answers after that moment; six a day at most.
One block appended before the command-line guard. Anything else stops the build."""
import hashlib, sys

FROM = "bf3da53250c02ca83bd11a2d0ba8daa3"
GUARD = 'if __name__ == "__main__":                                        # S756 (F-1207): the guard stands LAST, after every section\n'
BLOCK = '''# ---- S814 (13-Nov-2026, Sanjeevni session 445, kit S814_MARG_WATCH_ASK; plan v4 section 8.3) ------------------------------------------------
#  A STAFF ANSWER CAME BACK on the Marg watch (Amir's one tap on his card): one line, "Marg watch: Amir answered -- 'Marg mein theek kar diya'
#  -- 2 rows". OFF until the owner turns it on, on the Marg watch page (ask.notice); then only answers that came after that moment; between
#  owner_notice.hand_from and hand_to; never more than six a day. Tapping opens the Marg watch. Every switch this file already obeys stops it.
KIT_S814 = "S814_MARG_WATCH_ASK"
ASK_A_DAY = 6


def _part_ask(con, now):
    n = now.replace(tzinfo=None)
    m = n.hour * 60 + n.minute
    if m < mins(setting(con, "owner_notice.hand_from"), 480) or m >= mins(setting(con, "owner_notice.hand_to"), 1260):
        return []
    import marg_billwatch as BW                                   # noqa: PLC0415
    rows = BW.ask_messages(con, n)
    if not rows:
        return []
    told = {r[0] for r in con.execute("SELECT key FROM owner_notice WHERE kind='ask'")}
    today = n.strftime("%Y-%m-%d")
    left = ASK_A_DAY - sum(1 for r in con.execute("SELECT made_at FROM owner_notice WHERE kind='ask'") if str(r[0] or "")[:10] == today)
    return [dict(key=r["key"], kind="ask", title=r["title"], body=r["body"]) for r in rows if r["key"] not in told][:max(0, left)]


_collect_before_s814 = collect


def collect(con, now):                                            # noqa: F811 -- S814: + a staff answer, fail-soft like every part
    msgs, errors = _collect_before_s814(con, now)
    try:
        more = _part_ask(con, now)
    except Exception as e:                                        # noqa: BLE001
        more, errors = [], errors + ["ask: %s" % e.__class__.__name__]
    seen = {m["key"] for m in msgs}
    return msgs + [m for m in more if m["key"] not in seen], errors


_payload_before_s814 = _payload


def _payload(key, title, body):                                   # noqa: F811 -- S814: an answer opens the Marg watch
    p = _payload_before_s814(key, title, body)
    if str(key).startswith("ask:"):
        p["url"] = BILLS_URL
    return p
# ---- S814 end -------------------------------------------------------------------------------------------------------------------------------


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
