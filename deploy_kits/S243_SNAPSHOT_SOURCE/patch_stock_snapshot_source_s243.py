#!/usr/bin/env python3
"""patch_stock_snapshot_source_s243.py -- kit S243_SNAPSHOT_SOURCE

THE DEFECT (found at S243 by code reading, /root/finance/stock_app.py 0b965da4)
    POST /finance/stock/api/snapshot receives two different feeds:
      push_snapshot.py  source "push_snapshot"                   = Marg's real closing stock
      push_expected.py  source "push_expected base=.. pur_to=.." = OUR computed figure,
                                                                  as_on = the last SALE date
    Both upserted stock_snapshot keyed (as_on, item) with no source in the key, and
    reconcile() reads stock_snapshot by (as_on, item) without looking at source. When both
    land for the same as_on the later one silently became "Marg's figure" -- for the count
    page, for reconcile(), for every pad reader. stock_feed (append-only) already told the
    two apart; stock_snapshot did not.

THE FIX (smallest safe shape; every URL and every reader unchanged)
    1. a new table stock_expected -- same columns as stock_snapshot plus the source it
       already carries -- created idempotently from inside stock_app (EXPECTED_SCHEMA).
    2. /api/snapshot routes by _feed_kind(source): the computed feed ("expected") writes
       stock_expected; Marg ("marg") and any unrecognised sender ("other") write
       stock_snapshot exactly as before. stock_feed still receives every push, unchanged.
    3. reconcile() is not run for the computed feed -- a difference closes only when
       MARG's export agrees with the count, never when our own arithmetic does.
    reconcile() itself is untouched. Every reader of the computed figure goes through
    stock_feed (see README / EVIDENCE) and is untouched.

Usage:  python3 patch_stock_snapshot_source_s243.py [BASE_stock_app.py] [OUT_stock_app.py]
        default BASE = ../S240_STOCK_GATE_R2/stock_app.py (the 0b965da4 pin), OUT = ./stock_app.py
"""
import hashlib
import io
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(HERE), "S240_STOCK_GATE_R2", "stock_app.py")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "stock_app.py")
FROM_PIN = "0b965da40816079a60c49a20946832b3"


def md5(b):
    return hashlib.md5(b).hexdigest()


raw = io.open(BASE, "rb").read()
print("base  %s  %s" % (md5(raw), BASE))
if md5(raw) != FROM_PIN:
    raise SystemExit("REFUSED: the base is not the %s pin this patch was written for" % FROM_PIN[:8])
src = raw.decode("utf-8")
assert "\r\n" not in src, "the base has CRLF endings; refusing"

# ---- 1. the new table, beside FEED_SCHEMA ----------------------------------
old1 = '''CREATE INDEX IF NOT EXISTS idx_feed_item ON stock_feed(item, as_on);
CREATE INDEX IF NOT EXISTS idx_feed_ason ON stock_feed(as_on);
"""


'''
new1 = '''CREATE INDEX IF NOT EXISTS idx_feed_item ON stock_feed(item, as_on);
CREATE INDEX IF NOT EXISTS idx_feed_ason ON stock_feed(as_on);
"""


# ---- S243 SNAPSHOT SOURCE: the computed feed gets its own table ------------
# stock_snapshot is keyed (as_on, item) and last-write-wins, and until S243 BOTH
# senders wrote it: Marg's closing-stock export (push_snapshot) and our own
# computed figure (push_expected, as_on = the last sale date). Whichever landed
# later became "Marg's figure" for the count page, for reconcile() and for every
# pad reader -- silently. stock_feed kept both apart; stock_snapshot did not.
#
# From S243 the computed feed lands HERE, same shape, and stock_snapshot holds
# Marg's figures only. Nothing reads this table yet: every screen that shows the
# computed figure (drift, now, readiness, three-way) already reads stock_feed.
# It exists so the computed push keeps a keyed, latest-wins home of its own and
# so the day this fault is looked for again, the row says where it went.
EXPECTED_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_expected (
  as_on     TEXT NOT NULL,
  item      TEXT NOT NULL,
  qty       INTEGER NOT NULL,
  packing   TEXT,
  pack_size INTEGER NOT NULL DEFAULT 1,
  loaded_at TEXT NOT NULL,
  source    TEXT,
  PRIMARY KEY (as_on, item)
);
CREATE INDEX IF NOT EXISTS idx_expected_item ON stock_expected(item, as_on);
"""


def _expected_ensure(con):
    con.executescript(EXPECTED_SCHEMA)
# ---- end S243 SNAPSHOT SOURCE table ------------------------------------------


'''
assert src.count(old1) == 1, "anchor 1 (FEED_SCHEMA tail) not found exactly once"
src = src.replace(old1, new1)

# ---- 2. the door routes by sender ------------------------------------------
old2 = '''    con = _db()
    ensure_schema(con)
    n = 0
    for it in items:
        name = (it.get("item") or "").strip()
        if not name:
            continue
        con.execute(
            "INSERT INTO stock_snapshot (as_on,item,qty,packing,pack_size,loaded_at,source) "
            "VALUES (?,?,?,?,?,?,?) ON CONFLICT(as_on,item) DO UPDATE SET "
            "qty=excluded.qty, packing=excluded.packing, pack_size=excluded.pack_size, "
            "loaded_at=excluded.loaded_at, source=excluded.source",
            (as_on, name, int(it.get("qty") or 0), it.get("packing"),
             int(it.get("pack_size") or 1), now_iso(), b.get("source")))
'''
new2 = '''    con = _db()
    ensure_schema(con)
    # S243 SNAPSHOT SOURCE -- which sender is this? The computed feed
    # (push_expected) goes to stock_expected; Marg's export (push_snapshot) and
    # any sender the server does not recognise go to stock_snapshot, as before.
    # The two are told apart by the same rule stock_feed has used since S221.
    _kind = _feed_kind(b.get("source"))
    _table = "stock_expected" if _kind == "expected" else "stock_snapshot"
    if _kind == "expected":
        _expected_ensure(con)
    n = 0
    for it in items:
        name = (it.get("item") or "").strip()
        if not name:
            continue
        con.execute(
            "INSERT INTO " + _table + " (as_on,item,qty,packing,pack_size,loaded_at,source) "
            "VALUES (?,?,?,?,?,?,?) ON CONFLICT(as_on,item) DO UPDATE SET "
            "qty=excluded.qty, packing=excluded.packing, pack_size=excluded.pack_size, "
            "loaded_at=excluded.loaded_at, source=excluded.source",
            (as_on, name, int(it.get("qty") or 0), it.get("packing"),
             int(it.get("pack_size") or 1), now_iso(), b.get("source")))
'''
assert src.count(old2) == 1, "anchor 2 (the stock_snapshot upsert) not found exactly once"
src = src.replace(old2, new2)

# ---- 3. reconcile only against Marg ----------------------------------------
old3 = '''    closed = reconcile(con, as_on)
    return jsonify(ok=True, as_on=as_on, items=n, reconciled=closed,
                   revalued=revalued)
'''
new3 = '''    # S243: a difference closes when MARG's export agrees with the count -- never
    # when our own computed figure does. The computed feed skips reconcile().
    closed = reconcile(con, as_on) if _kind != "expected" else 0
    return jsonify(ok=True, as_on=as_on, items=n, reconciled=closed,
                   revalued=revalued, stored_in=_table)
'''
assert src.count(old3) == 1, "anchor 3 (the reconcile call) not found exactly once"
src = src.replace(old3, new3)

# ---- 4. the S221 comment that described the fault now says where it went ---
old4 = '''    # S221 TWO PRICES -- keep EVERY pushed figure, append-only, with its source.
    # stock_snapshot is keyed (as_on,item) and last-write-wins, so Marg's export
    # and the computed expected figure overwrite each other whenever they share
    # an as_on. This log is what makes them comparable instead of destructive.
'''
new4 = '''    # S221 TWO PRICES -- keep EVERY pushed figure, append-only, with its source.
    # stock_snapshot is keyed (as_on,item) and last-write-wins, so until S243
    # Marg's export and the computed expected figure overwrote each other
    # whenever they shared an as_on (S243 SNAPSHOT SOURCE: the computed feed now
    # lands in stock_expected). This log is what makes them comparable.
'''
assert src.count(old4) == 1, "anchor 4 (the S221 comment) not found exactly once"
src = src.replace(old4, new4)

out = src.encode("utf-8")
io.open(OUT, "wb").write(out)
print("wrote %s  %s" % (md5(out), OUT))
print("old md5 %s" % md5(raw))
print("new md5 %s" % md5(out))
