#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data_s454p1c.py -- kit S454_BILL_REGISTER, part 1C: the two data steps of S454 17 (run by the installer on finance.db after its backup;
run by the walk on scratch copies). Prints counts and ids only -- never a number, a body or the key.

  17.9   message id 1 (A.A. Pharmaceuticals, the August NEFT) was marked sent at 15:00:27 IST on 03-Oct by a test run of the macro although it
         did not go: put back to waiting (queued, attempts 0, sent_at / sent_by / last_try_at / handed_at cleared), audited with the reason --
         ONLY if it still reads sent at that time by reception-phone. Message id 2 (sent by hand afterwards) is true and is left.
  17.10  order.phone_alive_min = 720 (the phone asks only while awake and unlocked), audited.
  The payment messages as found (waiting, sent, failed), before and after -- nothing else is changed (17.6: nothing is held).

    data_s454p1c.py --db /root/finance/finance.db --finance /root/finance
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys

MSG1_SENT_AT = "2026-10-03T15:00:27"
REASON = ("S454 17.9: marked sent at 15:00:27 IST on 03-Oct by a test run of the reception phone's macro (WhatsApp had not opened); "
          "it did not go -- put back to waiting")


def _audit(con, who, action, ref, detail):
    try:
        import purchase_app as pa                             # noqa: PLC0415
        pa._audit(con, who, action, ref, detail)
    except Exception:                                         # noqa: BLE001
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (dt.datetime.now().replace(microsecond=0).isoformat(), who, action, str(ref), json.dumps(detail)))


def pay_counts(con):
    out = dict(waiting=0, sent=0, failed=0, skipped=0)
    for st, n in con.execute("SELECT status, COUNT(*) FROM supplier_msg WHERE kind IN ('neft','cheque') GROUP BY status"):
        out[{"queued": "waiting"}.get(st, st)] = n
    return out


def reset_msg1(con, who):
    r = con.execute("SELECT id, kind, status, sent_by, sent_at FROM supplier_msg WHERE id=1").fetchone()
    if not r:
        return dict(reset=False, found="no message 1")
    found = dict(kind=r[1], status=r[2], sent_by=r[3], sent_at=r[4])
    if not (r[1] == "neft" and r[2] == "sent" and r[3] == "reception-phone" and str(r[4] or "") == MSG1_SENT_AT):
        return dict(reset=False, found=found)
    con.execute("UPDATE supplier_msg SET status='queued', attempts=0, sent_at=NULL, sent_by=NULL, last_try_at=NULL, handed_at=NULL "
                "WHERE id=1 AND status='sent' AND sent_by='reception-phone' AND sent_at=?", (MSG1_SENT_AT,))
    _audit(con, who, "s454_msg_reset", "1", dict(kit="S454 P1C", reason=REASON, was=found))
    con.commit()
    return dict(reset=True, found=found)


def set_alive(con, who):
    r = con.execute("SELECT value FROM setting WHERE key='order.phone_alive_min'").fetchone()
    before = r[0] if r else None
    if str(before) == "720":
        return dict(before=before, after="720", changed=False)
    con.execute("INSERT INTO setting (key, value, note) VALUES ('order.phone_alive_min', '720', ?) ON CONFLICT(key) DO UPDATE SET value='720'",
                ("S454: the reception phone silent this long -- the WhatsApp button is disabled (17.10: it asks only while awake and unlocked)",))
    _audit(con, who, "s454_setting", "order.phone_alive_min", dict(before=before, after="720", why="S454 17.10: the phone asks only while awake and unlocked"))
    con.commit()
    return dict(before=before, after="720", changed=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--finance", required=True)
    a = ap.parse_args()
    sys.path.insert(0, a.finance)
    con = sqlite3.connect(a.db, timeout=60)
    print("payment messages as found: %s" % json.dumps(pay_counts(con)))
    r = reset_msg1(con, "S454 install")
    print("17.9  message 1: %s" % json.dumps(r))
    s = set_alive(con, "S454 install")
    print("17.10 order.phone_alive_min: %s" % json.dumps(s))
    print("payment messages after: %s" % json.dumps(pay_counts(con)))
    print("S454 P1C data done")


if __name__ == "__main__":
    main()
