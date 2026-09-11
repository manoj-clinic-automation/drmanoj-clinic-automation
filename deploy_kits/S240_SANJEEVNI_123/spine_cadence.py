#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spine_cadence.py -- S240, Sanjeevni plan item 2 (Rung 4: the item spine refreshes itself)

The item spine (marg_spine.py, S229) has run ONCE, on 07-Sep. Its lists -- "new items needing a
salt", "names to fix", Amir's open tasks -- go stale the moment Marg sends anything new.

This runs the spine on a cadence and says, in a few lines, WHAT CHANGED:
    new names seen · names newly unresolved · names that resolved · new tasks · tasks closed

    python3 spine_cadence.py --db /root/finance/finance.db --if-changed   (cron, every 30 min 09-23)
    python3 spine_cadence.py --db /root/finance/finance.db                (cron, nightly: always runs)
    python3 spine_cadence.py --db ... --dry-run    on a scratch copy; the real db is not written
    python3 spine_cadence.py --selftest

--if-changed skips the run when none of the spine's source tables has moved since the last run
(a fingerprint of row counts and highest row ids), so the cadence costs nothing on a quiet hour.

WRITES
    the spine's own seven tables (marg_spine.build -- idempotent, S229's 54 selftests), and ONE new
    table, marg_spine_drift, one row per run. Nothing else. No screen reads either yet.
    The latest report is also written to /root/finance/spine_drift_latest.txt.
"""
import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SOURCES = ("sale_line_item", "purchase_line", "stock_feed", "stock_rate", "purchase_salt_marg",
           "stock_diff", "stock_count_item", "marg_task")
DRIFT = """
CREATE TABLE IF NOT EXISTS marg_spine_drift (
    id            INTEGER PRIMARY KEY,
    at            TEXT NOT NULL,
    spine_run_id  INTEGER,
    trigger       TEXT NOT NULL,
    fingerprint   TEXT NOT NULL,
    new_names     TEXT NOT NULL,
    new_unresolved TEXT NOT NULL,
    resolved      TEXT NOT NULL,
    new_tasks     TEXT NOT NULL,
    closed_tasks  TEXT NOT NULL,
    counts        TEXT NOT NULL
);
"""
REPORT_PATH = os.environ.get("SPINE_DRIFT_TXT", "/root/finance/spine_drift_latest.txt")


def now_ist():
    return (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")


def _exists(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def fingerprint(con):
    fp = {}
    for t in SOURCES:
        if _exists(con, t):
            n, mx = con.execute("SELECT COUNT(*), MAX(rowid) FROM %s" % t).fetchone()
            extra = ""
            if t == "marg_task":
                extra = con.execute("SELECT COUNT(*) FROM marg_task WHERE status='open'").fetchone()[0]
            fp[t] = [n, mx, extra]
    return json.dumps(fp, sort_keys=True)


def snapshot(con):
    s = {"names": set(), "unres": set(), "tasks": {}}
    if _exists(con, "marg_item_name"):
        s["names"] = {r[0] for r in con.execute("SELECT name FROM marg_item_name")}
    if _exists(con, "marg_name_unresolved"):
        s["unres"] = {r[0] for r in con.execute("SELECT name FROM marg_name_unresolved")}
    if _exists(con, "marg_task"):
        s["tasks"] = {r[0]: (r[1], r[2], r[3]) for r in
                      con.execute("SELECT id, status, kind, COALESCE(a,'') FROM marg_task")}
    return s


def diff(before, after):
    new_tasks = sorted(i for i in after["tasks"] if i not in before["tasks"])
    closed = sorted(i for i, v in after["tasks"].items()
                    if i in before["tasks"] and before["tasks"][i][0] == "open" and v[0] != "open")
    return {"new_names": sorted(after["names"] - before["names"]),
            "new_unresolved": sorted(after["unres"] - before["unres"]),
            "resolved": sorted(before["unres"] - after["unres"]),
            "new_tasks": [[i, after["tasks"][i][1], after["tasks"][i][2]] for i in new_tasks],
            "closed_tasks": [[i, after["tasks"][i][1], after["tasks"][i][2]] for i in closed]}


def last_fingerprint(con):
    if not _exists(con, "marg_spine_drift"):
        return None
    r = con.execute("SELECT fingerprint FROM marg_spine_drift ORDER BY id DESC LIMIT 1").fetchone()
    return r[0] if r else None


def report_text(at, trigger, d, counts):
    def few(xs, n=8):
        xs = [x if isinstance(x, str) else "%s (%s)" % (x[1], x[2] or "-") for x in xs]
        return ", ".join(xs[:n]) + (" and %d more" % (len(xs) - n) if len(xs) > n else "") if xs else "none"
    return "\n".join([
        "ITEM SPINE -- what changed  %s IST  (%s)" % (at.replace("T", " ")[:16], trigger),
        "  items %(items)d · names %(names)d · open tasks %(open_tasks)d · unresolved %(unresolved)d" % counts,
        "  new names seen      : %d  %s" % (len(d["new_names"]), few(d["new_names"])),
        "  newly unresolved    : %d  %s" % (len(d["new_unresolved"]), few(d["new_unresolved"])),
        "  resolved            : %d  %s" % (len(d["resolved"]), few(d["resolved"])),
        "  new tasks           : %d  %s" % (len(d["new_tasks"]), few(d["new_tasks"])),
        "  tasks closed        : %d  %s" % (len(d["closed_tasks"]), few(d["closed_tasks"])),
    ])


def cadence(con, trigger, if_changed=False, out=print, report_path=REPORT_PATH):
    import marg_spine
    con.execute("PRAGMA busy_timeout=30000")
    fp0 = fingerprint(con)
    if if_changed and last_fingerprint(con) == fp0:
        out("spine cadence: sources unchanged since the last run -- skipped")
        return None
    before = snapshot(con)
    marg_spine.build(con, out=lambda *a, **k: None)
    after = snapshot(con)
    d = diff(before, after)
    run = con.execute("SELECT id FROM marg_spine_run ORDER BY id DESC LIMIT 1").fetchone()
    counts = {"items": con.execute("SELECT COUNT(*) FROM marg_item").fetchone()[0],
              "names": len(after["names"]), "unresolved": len(after["unres"]),
              "open_tasks": sum(1 for v in after["tasks"].values() if v[0] == "open")}
    at = now_ist()
    con.executescript(DRIFT)
    con.execute("INSERT INTO marg_spine_drift (at, spine_run_id, trigger, fingerprint, new_names, "
                "new_unresolved, resolved, new_tasks, closed_tasks, counts) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (at, run[0] if run else None, trigger, fingerprint(con),
                 json.dumps(d["new_names"]), json.dumps(d["new_unresolved"]), json.dumps(d["resolved"]),
                 json.dumps(d["new_tasks"]), json.dumps(d["closed_tasks"]), json.dumps(counts)))
    con.commit()
    txt = report_text(at, trigger, d, counts)
    out(txt)
    if report_path:
        try:
            with open(report_path, "w", encoding="utf-8") as fh:
                fh.write(txt + "\n")
        except OSError:
            pass
    return d


def selftest():
    import marg_spine
    fails = []

    def ck(n, c):
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    b = {"names": {"A", "B"}, "unres": {"X"}, "tasks": {1: ("open", "salt", "A"), 2: ("open", "name", "B")}}
    a = {"names": {"A", "B", "C"}, "unres": {"Y"}, "tasks": {1: ("done", "salt", "A"), 2: ("open", "name", "B"),
                                                           3: ("open", "salt", "C")}}
    d = diff(b, a)
    ck("new name found", d["new_names"] == ["C"])
    ck("newly unresolved and resolved", d["new_unresolved"] == ["Y"] and d["resolved"] == ["X"])
    ck("new task and closed task", [t[0] for t in d["new_tasks"]] == [3] and [t[0] for t in d["closed_tasks"]] == [1])
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE sale_line_item (x)")
    f1 = fingerprint(con); con.execute("INSERT INTO sale_line_item VALUES (1)"); f2 = fingerprint(con)
    ck("fingerprint moves when a source moves", f1 != f2)
    ck("marg_spine importable beside it", hasattr(marg_spine, "build"))
    print("spine_cadence selftest: %d checks, %d failures" % (5, len(fails)))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--if-changed", action="store_true")
    ap.add_argument("--trigger", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.db:
        ap.error("--db is required")
    db = a.db
    rp = REPORT_PATH
    if a.dry_run:
        db = os.path.join(tempfile.mkdtemp(), "scratch.db")
        src = sqlite3.connect(a.db); dst = sqlite3.connect(db); src.backup(dst); dst.close(); src.close()
        print("DRY RUN on a copy (the real database is not written)")
        rp = None
    con = sqlite3.connect(db, timeout=30)
    cadence(con, a.trigger or ("changed" if a.if_changed else "nightly"), a.if_changed, report_path=rp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
