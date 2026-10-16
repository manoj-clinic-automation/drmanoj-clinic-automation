#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s570.py -- kit S570_PROOF_MORNING_WINDOW: the builder. Anchored edits on the LIVE bytes of stock_app.py (FROM f58e09db...).

    python3 -B make_s570.py --finance /root/finance --out DIR

Every anchor must occur exactly once in the live file, else STOP (exit 2, nothing written). Writes DIR/stock_app.py and prints its md5;
the installer compares it with PINS.sh's TO pin.

  E1  F-905  _s524_tryable: an export covers a closing when captured after it OR when its own capture, read by the estate's one capture
             rule (_s524_end_day, charter 11), stands for the end of a day at or after the closing's end_day (_s570_covers, new).
  E2  F-906  _s488_why: closing_at of a spine closing = that closing's own capture (its stamp), never a stock_feed push of its printed day.
  E3  F-906  _s488_why (no clean closing in the spine yet): a stock_feed push the capture rule skips (a mid-day capture) is never named;
             each push read by its own capture (not the day's MIN); the purchase side short -> pur_behind.
  E4  F-906  _s488_first_push: the same skip (it is then read by E3's branch only).
"""
import argparse
import hashlib
import os
import sys

FROM = "f58e09dbb273e8b1470aa7220da70015"

E1_OLD = '''def _s524_tryable(c, reach):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): last_sale and last_pur at or past its end_day, and
    both newest exports captured after it. short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach:
        return False, "sale"
    if reach["last_sale"] < d or reach["sale_stamp"] <= c["stamp"]:
        return False, "sale"
    if not reach["last_pur"] or reach["last_pur"] < d or reach["pur_stamp"] <= c["stamp"]:
        return False, "pur"
    return True, ""
'''
E1_NEW = '''def _s570_covers(day, stamp, c, d):
    """S570 (F-905): the newest export of a family (reaching `day`, captured at `stamp`) covers the closing `c` (end_day `d`) when it was
    captured after the closing, OR when its own capture, read by the estate's one capture rule (_s524_end_day, charter 11), stands for the
    end of a day at or after d. The morning order -- the sale report ~05:10, the closing ~05:17, both the end of yesterday -- is covered;
    a same-day capture inside shop hours gives None, and None never covers."""
    if stamp > c["stamp"]:
        return True
    e = _s524_end_day(str(day or ""), _s524_stamp_iso(stamp))
    return e is not None and e >= d


def _s524_tryable(c, reach):
    """(ok, short) -- a closing is tried only when the spine's reach covers it (R1-B2): last_sale and last_pur at or past its end_day, and
    both newest exports cover it (_s570_covers: captured after it, or standing by their own capture for the end of a day at or after its
    end_day -- S570, F-905). short names what is missing: 'sale' | 'pur' | ''."""
    d = c.get("end_day") or ""
    if not d or not reach:
        return False, "sale"
    if reach["last_sale"] < d or not _s570_covers(reach["last_sale"], reach["sale_stamp"], c, d):
        return False, "sale"
    if not reach["last_pur"] or reach["last_pur"] < d or not _s570_covers(reach["last_pur"], reach["pur_stamp"], c, d):
        return False, "pur"
    return True, ""
'''

E2_OLD = '''            out["closing_at"] = _s488_first_push(con, out["closing_day"], last_at, c.get("stamp_iso") or None)
'''
E2_NEW = '''            out["closing_at"] = c.get("stamp_iso") or None   # S570 (F-906): the capture of the closing the proof waits on, never a feed push
'''

E3_OLD = '''            for day, src, at in con.execute("SELECT as_on, source, MIN(received_at) FROM stock_feed WHERE substr(received_at,1,19) > ? "
                                            "GROUP BY as_on, source", (str(last_at or "")[:19],)):
                if _feed_kind(src) != "marg" or _proof_day_key(day) < lk or not at:
                    continue
                if push is None or (_proof_day_key(day), str(at)) < (_proof_day_key(push[0]), push[1]):
                    push = (str(day), str(at))
            if push:
                why = "no_figure"
                out["closing_day"] = push[0]
'''
E3_NEW = '''            for day, src, at in con.execute("SELECT DISTINCT as_on, source, received_at FROM stock_feed WHERE substr(received_at,1,19) > ?",
                                            (str(last_at or "")[:19],)):
                if _feed_kind(src) != "marg" or _proof_day_key(day) < lk or not at or _s570_push_end(day, at) is None:
                    continue                                   # S570 (F-906): a push the capture rule skips (mid-day) is never named
                if push is None or (_proof_day_key(day), str(at)) < (_proof_day_key(push[0]), push[1]):
                    push = (str(day), str(at))
            if push:
                why = "no_figure"
                if sp is not None:                             # S570 (F-906): the words name what the reach is short of
                    _ok, short = _s524_tryable(dict(end_day=_s570_push_end(push[0], push[1]), stamp=_s570_stamp(push[1])), _s524_reach(sp))
                    why = "pur_behind" if short == "pur" else "no_figure"
                out["closing_day"] = push[0]
'''

E4_OLD = '''def _s488_first_push(con, day, last_at, fallback=None):
    """The EARLIEST received_at after last_at among the day's Marg closing-stock pushes (stock_feed rows whose source is marg)."""
    best = None
    for src, at in con.execute("SELECT source, MIN(received_at) FROM stock_feed WHERE as_on=? AND substr(received_at,1,19) > ? GROUP BY source",
                               (day, str(last_at or "")[:19])):
        if _feed_kind(src) == "marg" and at and (best is None or str(at) < best):
            best = str(at)
    return best or fallback
'''
E4_NEW = '''def _s570_push_end(day, at):
    """S570 (F-906): the day whose END a stock_feed push (as_on dd-mm-yyyy, received_at ISO) stands for, by the one capture rule
    (_s524_end_day); None for a mid-day capture -- the spine skips it, and so does every sentence."""
    k = _proof_day_key(day)
    return _s524_end_day("%s-%s-%s" % (k[0:4], k[4:6], k[6:8]), str(at or "")[:19]) if len(k) == 8 else None


def _s570_stamp(at):
    """'YYYY-MM-DDTHH:MM:SS' -> 'YYYYMMDD-HHMMSS' (the shape of an export's stamp); '' when it is not that shape."""
    s = str(at or "")
    return "%s%s%s-%s%s%s" % (s[0:4], s[5:7], s[8:10], s[11:13], s[14:16], s[17:19]) if len(s) >= 19 else ""


def _s488_first_push(con, day, last_at, fallback=None):
    """The EARLIEST received_at after last_at among the day's Marg closing-stock pushes (stock_feed rows whose source is marg) that the
    capture rule places at the end of a day (S570: a mid-day capture is skipped)."""
    best = None
    for src, at in con.execute("SELECT DISTINCT source, received_at FROM stock_feed WHERE as_on=? AND substr(received_at,1,19) > ?",
                               (day, str(last_at or "")[:19])):
        if _feed_kind(src) == "marg" and at and _s570_push_end(day, at) is not None and (best is None or str(at) < best):
            best = str(at)
    return best or fallback
'''

EDITS = [("E1 _s524_tryable (F-905)", E1_OLD, E1_NEW), ("E2 _s488_why closing_at (F-906)", E2_OLD, E2_NEW),
         ("E3 _s488_why feed branch (F-906)", E3_OLD, E3_NEW), ("E4 _s488_first_push (F-906)", E4_OLD, E4_NEW)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = os.path.join(a.finance, "stock_app.py")
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, FROM))
        return 2
    t = raw.decode("utf-8")
    for name, old, new in EDITS:
        n = t.count(old)
        if n != 1:
            print("STOP: anchor %s occurs %d times (must be exactly 1) -- nothing built" % (name, n))
            return 2
        t = t.replace(old, new, 1)
        print("edit %s: anchored once, applied" % name)
    out = t.encode("utf-8")
    os.makedirs(a.out, exist_ok=True)
    dst = os.path.join(a.out, "stock_app.py")
    with open(dst, "wb") as fh:
        fh.write(out)
    print("built %s md5 %s (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM))
    return 0


if __name__ == "__main__":
    sys.exit(main())
