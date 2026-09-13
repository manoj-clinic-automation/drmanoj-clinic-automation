#!/usr/bin/env python3
"""migrate_stock_expected_s243.py -- kit S243_SNAPSHOT_SOURCE

Moves the COMPUTED rows that push_expected.py wrote into stock_snapshot (before
S243) over to stock_expected, and puts Marg's own figure back where the feed log
still has it. READ-ONLY by default (--dry-run); --apply writes, after backing the
database up to  finance.db.bak_S243_SNAPSHOT_<stamp>  beside it.

WHAT A ROW IS
    computed   source starts with "push_expected"   (push_expected.py; the same
               rule as stock_app._feed_kind, copied here so this script has no
               import of the live app)
    marg       source starts with "push_snapshot"   (push_snapshot.py)
    other      anything else, blank included         -- NEVER touched

WHAT HAPPENS TO A COMPUTED ROW, per (as_on, item)      -- conservative on purpose
    1. it is COPIED into stock_expected (newer loaded_at wins if already there)
    2. then, in stock_snapshot:
       a. the newest Marg push in stock_feed for that as_on carries the item
             -> the row is RESTORED to Marg's qty/source/received_at
                (packing and pack_size are kept: both pushes send the same)
       b. a Marg push exists for that as_on but never carried this item
             -> the row is DELETED (Marg's export for that day did not have it)
       c. no Marg push exists for that as_on at all (an expected-only day)
             -> DELETED, unless a stock_count was measured against that as_on,
                in which case it is KEPT and named here for the owner to decide
                (a pad reader keys packing/pack_size by the count's as_on).

Usage
    python3 migrate_stock_expected_s243.py [--db /root/finance/finance.db] [--dry-run | --apply]
"""
import argparse
import datetime as dt
import io
import os
import shutil
import sqlite3
import sys

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


def feed_kind(source):
    """stock_app._feed_kind, verbatim."""
    s = (source or "").lower()
    if s.startswith("push_expected"):
        return "expected"
    if s.startswith("push_snapshot"):
        return "marg"
    return "other"


def table_exists(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def as_on_key(s):
    t = (s or "").strip().replace("/", "-").split("-")
    if len(t) == 3:
        try:
            a, b, c = (int(x) for x in t)
            if a > 1900:
                return (a, b, c)            # yyyy-mm-dd
            if c > 1900:
                return (c, b, a)            # dd-mm-yyyy
        except ValueError:
            pass
    return (0, 0, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(os.environ.get("FINANCE_DIR", "/root/finance"), "finance.db"))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--dry-run", action="store_true", default=True)
    g.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    apply = bool(a.apply)
    mode = "APPLY" if apply else "DRY RUN (nothing written)"
    print("== S243 stock_expected migration -- %s ==" % mode)
    print("db  %s" % a.db)
    if not os.path.exists(a.db):
        print("!! no such database"); return 2

    if apply:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = a.db + ".bak_S243_SNAPSHOT_" + stamp
        src = sqlite3.connect(a.db)
        dst = sqlite3.connect(bak)
        src.backup(dst)                 # a consistent copy even while the app is up
        dst.close(); src.close()
        print("backup %s (%d bytes)" % (bak, os.path.getsize(bak)))

    con = sqlite3.connect(a.db if apply else "file:%s?mode=ro" % a.db, uri=not apply)
    for t in ("stock_snapshot", "stock_feed"):
        if not table_exists(con, t):
            print("!! table %s is missing -- nothing to do" % t); return 2
    have_expected = table_exists(con, "stock_expected")
    if apply:
        con.executescript(EXPECTED_SCHEMA)
        have_expected = True
    print("stock_expected table: %s" % ("present" if have_expected else "absent (created on --apply)"))

    rows = con.execute("SELECT as_on, item, qty, packing, pack_size, loaded_at, source FROM stock_snapshot").fetchall()
    kinds = {"expected": 0, "marg": 0, "other": 0}
    comp = []
    for r in rows:
        k = feed_kind(r[6])
        kinds[k] += 1
        if k == "expected":
            comp.append(r)
    days_all = sorted({r[0] for r in rows}, key=as_on_key)
    print("stock_snapshot: %d rows over %d days (newest %s) -- marg %d, computed %d, other %d"
          % (len(rows), len(days_all), days_all[-1] if days_all else "-", kinds["marg"], kinds["expected"], kinds["other"]))
    if not comp:
        print("no computed rows in stock_snapshot -- nothing to move")
        newest = days_all[-1] if days_all else None
        print("newest stock_snapshot day after: %s" % newest)
        return 0

    # the newest Marg push per as_on, out of the feed log (the same rule as stock_app._feed_latest)
    marg_latest = {}
    for r in con.execute("SELECT as_on, source, MAX(received_at) FROM stock_feed GROUP BY as_on, source"):
        if feed_kind(r[1]) != "marg":
            continue
        k = str(r[0])
        if k not in marg_latest or str(r[2]) > marg_latest[k]["received_at"]:
            marg_latest[k] = dict(source=str(r[1]), received_at=str(r[2]))
    for k, v in marg_latest.items():
        v["items"] = {str(x[0]): int(x[1]) for x in con.execute(
            "SELECT item, qty FROM stock_feed WHERE as_on=? AND source=? AND received_at=?",
            (k, v["source"], v["received_at"]))}

    counted_days = set()
    if table_exists(con, "stock_count"):
        counted_days = {str(r[0]) for r in con.execute("SELECT DISTINCT marg_as_on FROM stock_count")}

    plan = {"copy": 0, "restore": 0, "delete_not_in_marg": 0, "delete_expected_only": 0, "keep_counted": 0}
    per_day = {}
    actions = []                       # (kind, as_on, item, row, marg_qty_or_None)
    for r in comp:
        as_on, item = str(r[0]), str(r[1])
        d = per_day.setdefault(as_on, dict(n=0, marg_feed=as_on in marg_latest, counted=as_on in counted_days,
                                           restore=0, delete=0, keep=0))
        d["n"] += 1
        plan["copy"] += 1
        m = marg_latest.get(as_on)
        if m is not None:
            if item in m["items"]:
                plan["restore"] += 1; d["restore"] += 1
                actions.append(("restore", as_on, item, r, m))
            else:
                plan["delete_not_in_marg"] += 1; d["delete"] += 1
                actions.append(("delete", as_on, item, r, None))
        elif as_on in counted_days:
            plan["keep_counted"] += 1; d["keep"] += 1
            actions.append(("keep", as_on, item, r, None))
        else:
            plan["delete_expected_only"] += 1; d["delete"] += 1
            actions.append(("delete", as_on, item, r, None))

    print("")
    print("computed rows by day:")
    for as_on in sorted(per_day, key=as_on_key):
        d = per_day[as_on]
        print("  %-12s %4d rows   Marg push in feed: %-3s   count against it: %-3s   -> restore %d, delete %d, keep %d"
              % (as_on, d["n"], "yes" if d["marg_feed"] else "no", "yes" if d["counted"] else "no",
                 d["restore"], d["delete"], d["keep"]))
    print("")
    print("plan: copy %d into stock_expected; in stock_snapshot restore %d to Marg's figure, delete %d "
          "(Marg's export lacked the item), delete %d (expected-only days), KEEP %d (expected-only days a count was measured against)"
          % (plan["copy"], plan["restore"], plan["delete_not_in_marg"], plan["delete_expected_only"], plan["keep_counted"]))
    if plan["keep_counted"]:
        kept = sorted({x[1] for x in actions if x[0] == "keep"}, key=as_on_key)
        print("!! KEPT in stock_snapshot, computed figures a count was measured against: %s" % ", ".join(kept))
        print("   The count(s) against those days were measured against OUR arithmetic, not Marg. Owner's decision.")
    if not apply:
        print("")
        print("dry run -- nothing written. Re-run with --apply to do the above.")
        return 0

    # ---- write ---------------------------------------------------------------
    for kind, as_on, item, r, m in actions:
        con.execute(
            "INSERT INTO stock_expected (as_on,item,qty,packing,pack_size,loaded_at,source) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(as_on,item) DO UPDATE SET qty=excluded.qty, packing=excluded.packing, "
            "pack_size=excluded.pack_size, loaded_at=excluded.loaded_at, source=excluded.source "
            "WHERE excluded.loaded_at > stock_expected.loaded_at",
            (as_on, item, int(r[2] or 0), r[3], int(r[4] or 1), r[5], r[6]))
        if kind == "restore":
            con.execute("UPDATE stock_snapshot SET qty=?, loaded_at=?, source=? WHERE as_on=? AND item=?",
                        (int(m["items"][item]), m["received_at"], m["source"], as_on, item))
        elif kind == "delete":
            con.execute("DELETE FROM stock_snapshot WHERE as_on=? AND item=?", (as_on, item))
    con.commit()

    # ---- read back -----------------------------------------------------------
    left = sum(1 for r in con.execute("SELECT source FROM stock_snapshot") if feed_kind(r[0]) == "expected")
    n_exp = con.execute("SELECT COUNT(*) FROM stock_expected").fetchone()[0]
    days_after = sorted({r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")}, key=as_on_key)
    print("")
    print("done: stock_expected now %d rows; computed rows still in stock_snapshot: %d (expected %d kept)"
          % (n_exp, left, plan["keep_counted"]))
    print("newest stock_snapshot day: %s -> %s" % (days_all[-1] if days_all else "-", days_after[-1] if days_after else "-"))
    if left != plan["keep_counted"]:
        print("!! read-back mismatch -- the backup is beside the db"); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
