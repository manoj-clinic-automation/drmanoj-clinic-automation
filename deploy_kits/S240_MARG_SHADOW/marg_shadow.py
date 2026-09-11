#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_shadow.py -- S240 (D467) Phase 1b. The server works the figures out ITSELF, and compares.

WHY. Before any job moves off the owner's PC, the server must reach the SAME answers from its own
store, day after day. This runs the PC's own computation -- push_expected.py 4b3b700c, vendored here
unchanged with the modules it imports -- over what marg_ingest.py collected, and sets the result
against what the PC pushed to stock_feed. Nothing is sent, nothing is applied, no screen changes.

WHAT IS SUBSTITUTED, AND ONLY THIS: the sale lines. The PC reads them from the sale export files;
the server keeps no such file (they carry patient mobiles), so they are read from mi_sale_line --
the same lines, parsed by the same reader at the moment the export arrived. Of two exports covering
one day, the one captured LATER wins, which is the PC's own rule (F-322).

Everything else -- baseline stock, purchases, the late-keyed-bill rule (D465), the clipped-name rule
(D466) -- runs on the server's own archive with the same code.

    /root/wa/venv/bin/python3 -B /root/marg_ingest/marg_shadow.py [--baseline dd-mm-yyyy] [--quiet]

SWITCH-OFF: /root/marg_ingest/OFF (shared with marg_ingest.py), or remove the cron line.
"""
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)   # google-auth's Python 3.9 end-of-life
                                                            # notice, twice per run, in every log
import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib")
sys.path.insert(0, LIB)

DB_DEFAULT = os.environ.get("MARG_INGEST_DB", "/root/finance/finance.db")
ARCHIVE = os.path.join(HERE, "archive")
CONF = os.path.join(HERE, "shadow.json")
OFF_FLAG = os.path.join(HERE, "OFF")
HEARTBEAT = os.path.join(HERE, "shadow_last.json")
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
DEFAULT_BASELINE = "03-09-2026"          # what PUSH_STOCK_DAILY.bat pins on the PC
MAX_DIFF_ROWS = 500
STAMP_RE = re.compile(r"__(\d{8}-\d{6})__")

SCHEMA = """
CREATE TABLE IF NOT EXISTS sh_run (
  id         INTEGER PRIMARY KEY,
  started    TEXT NOT NULL,
  finished   TEXT,
  baseline   TEXT NOT NULL DEFAULT '',
  as_on      TEXT NOT NULL DEFAULT '',
  items      INTEGER NOT NULL DEFAULT 0,
  pc_source  TEXT NOT NULL DEFAULT '',
  pc_at      TEXT NOT NULL DEFAULT '',
  same       INTEGER NOT NULL DEFAULT 0,
  differ     INTEGER NOT NULL DEFAULT 0,
  gap_units  REAL NOT NULL DEFAULT 0,
  only_here  INTEGER NOT NULL DEFAULT 0,
  only_pc    INTEGER NOT NULL DEFAULT 0,
  verdict    TEXT NOT NULL DEFAULT '',
  cutoff     TEXT NOT NULL DEFAULT '',
  note       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS sh_diff (
  run_id     INTEGER NOT NULL,
  item       TEXT NOT NULL,
  server_qty REAL,
  pc_qty     REAL,
  diff       REAL
);
CREATE INDEX IF NOT EXISTS ix_sh_diff ON sh_diff(run_id);
CREATE TABLE IF NOT EXISTS sh_feed (
  run_id     INTEGER NOT NULL,
  kind       TEXT NOT NULL,
  period     TEXT NOT NULL DEFAULT '',
  server_n   INTEGER, pc_n INTEGER,
  server_p   INTEGER, pc_p INTEGER,
  note       TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_sh_feed ON sh_feed(run_id);
"""


def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0)


def conf():
    try:
        return json.load(open(CONF))
    except (OSError, ValueError):
        return {}


def sale_lines_from_db(con, after, upto=None, cutoff=""):
    """The PC's sales_after(), served from mi_sale_line. Of two exports covering one day, the one
    captured later wins; within a file a line is (date, bill, seq)."""
    rows = con.execute(
        "SELECT l.bill_date, l.bill_no, l.seq, l.item_name, l.pack, l.qty_strips, l.qty_loose, "
        "l.qty_raw, f.stamp FROM mi_sale_line l JOIN mi_file f ON f.md5 = l.md5 "
        "ORDER BY f.stamp, l.rowid").fetchall()
    best, days = {}, set()
    for bd, bn, seq, item, pack, st, lo, raw, stamp in rows:
        if cutoff and (stamp or "") > cutoff:
            continue                                    # not yet captured at the moment compared
        d = None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y"):
            try:
                d = dt.datetime.strptime(str(bd), fmt).date()
                break
            except ValueError:
                continue
        if d is None or d <= after or (upto and d > upto):
            continue
        best[(d, bn, seq)] = {"date": d, "bill": bn, "item": item, "pack": pack,
                              "strips": st, "loose": lo, "qty_raw": raw}
        days.add(d)
    return list(best.values()), sorted(days), []


def as_the_pc_saw_it(archive, cutoff, tmp):
    """A view of the server's archive holding only what had been captured by `cutoff` -- so the two
    figures are compared over the same evidence, never over a later export the PC had not yet seen.
    Symlinks only: nothing is copied and nothing in the archive is touched."""
    n = 0
    for p in glob.glob(os.path.join(archive, "*", "*", "*")):
        if not p.lower().endswith((".xls", ".xlsx")):
            continue
        m = STAMP_RE.search(os.path.basename(p))
        if m and m.group(1) > cutoff:
            continue
        rel = os.path.relpath(p, archive)
        dest = os.path.join(tmp, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            os.symlink(os.path.abspath(p), dest)
        except OSError:
            shutil.copy2(p, dest)
        n += 1
    return n


def pc_expected(con, as_on):
    """The newest figure the PC pushed for this date: {item: qty}, its source line and time."""
    row = con.execute(
        "SELECT source, MAX(received_at) FROM stock_feed WHERE as_on=? AND source LIKE 'push_expected%' "
        "GROUP BY source ORDER BY 2 DESC LIMIT 1", (as_on,)).fetchone()
    if not row:
        return {}, "", ""
    src, at = row[0], row[1]
    out = {}
    for item, qty in con.execute(
            "SELECT item, qty FROM stock_feed WHERE as_on=? AND source=? AND received_at=?",
            (as_on, src, at)):
        out[str(item)] = float(qty or 0)
    return out, src, at


def feed_counts(con, run_id, rep, out):  # noqa: C901
    """Two cheap counts beside the stock figure: purchase bills the server can date, and sale bills
    it holds, against what the PC has put in the server's own tables."""
    import contextlib
    import io
    rows = []
    try:
        import push_expected as PE
        with contextlib.redirect_stdout(io.StringIO()):
            dates, _f, _c = PE.bill_dates(ARCHIVE)
        by_month = {}
        for (_sup, _bill), d in dates.items():
            by_month[d.strftime("%Y-%m")] = by_month.get(d.strftime("%Y-%m"), 0) + 1
        for month, n in sorted(by_month.items())[-3:]:
            pc = con.execute("SELECT COUNT(*) FROM purchase_bill WHERE month=?", (month,)).fetchone()
            rows.append(("purchase bills", month, n, (pc or [0])[0], None, None,
                         "a count, not a verdict: the PC sends only what it has been asked to"))
    except Exception as e:                                        # noqa: BLE001
        rows.append(("purchase bills", "", None, None, None, None, str(e)[:120]))
    try:
        con.execute("SELECT 1 FROM sale_bill LIMIT 1")
        for d, n in con.execute("SELECT bill_date, COUNT(DISTINCT bill_no) FROM mi_sale_line "
                                "GROUP BY bill_date ORDER BY bill_date DESC LIMIT 5"):
            iso = str(d)
            pc = con.execute("SELECT COUNT(*) FROM sale_bill WHERE bill_date=?", (iso,)).fetchone()
            rows.append(("sale bills", iso, n, (pc or [0])[0], None, None, ""))
    except sqlite3.Error:
        rows.append(("sale bills", "", None, None, None, None,
                     "the sale_bill table is not on this box yet"))
    for r in rows:
        con.execute("INSERT INTO sh_feed (run_id, kind, period, server_n, pc_n, server_p, pc_p, note) "
                    "VALUES (?,?,?,?,?,?,?,?)", (run_id,) + r)
        out("  %-14s %-10s server %-6s pc %-6s %s"
            % (r[0], r[1], r[2] if r[2] is not None else "-", r[3] if r[3] is not None else "-", r[6]))


def run(db=DB_DEFAULT, baseline=None, archive=ARCHIVE, out=print, upto=None):
    import push_expected as PE
    t0 = now_ist()
    base = baseline or conf().get("baseline") or DEFAULT_BASELINE
    con = sqlite3.connect(db, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    con.executescript(SCHEMA)
    have = {r[1] for r in con.execute("PRAGMA table_info(sh_run)")}
    for col, decl in (("cutoff", "TEXT NOT NULL DEFAULT ''"),):
        if col not in have:                             # an older table from a first install
            con.execute("ALTER TABLE sh_run ADD COLUMN %s %s" % (col, decl))
    run_id = con.execute("INSERT INTO sh_run (started, baseline) VALUES (?,?)",
                         (t0.isoformat(), base)).lastrowid
    con.commit()
    def _compute(arch, cutoff=""):
        PE.sales_after = lambda _a, after, upto=None: sale_lines_from_db(con, after, upto, cutoff)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):           # the PC script's own chatter, captured
            r = PE.compute(arch, base, PE.dkey(upto) if upto else None)
        return r, buf.getvalue().splitlines()

    import contextlib
    import io
    rep, chatter = _compute(archive)
    if rep.get("error"):
        con.execute("UPDATE sh_run SET finished=?, verdict='refused', note=? WHERE id=?",
                    (now_ist().isoformat(), rep["error"][:300], run_id))
        con.commit()
        out("shadow REFUSED: %s" % rep["error"])
        return 1
    as_on = PE.ddmmyyyy(rep["as_on"])
    out("shadow %s  baseline %s  expected as on %s: %d items"
        % (t0.strftime("%d-%m-%Y %H:%M"), base, as_on, len(rep["items"])))

    theirs, src, at = pc_expected(con, as_on)
    cutoff = ""
    same = differ = only_here = only_pc = 0
    gap = 0.0
    diffs = []
    if theirs:
        # Compare over the SAME evidence: only what had been captured by the moment the PC pushed.
        cutoff = (at or "").replace("-", "").replace(":", "").replace("T", "-")[:15]
        tmp = tempfile.mkdtemp(prefix="sh_", dir=os.path.join(HERE, "work")
                               if os.path.isdir(os.path.join(HERE, "work")) else None)
        try:
            kept = as_the_pc_saw_it(archive, cutoff, tmp)
            rep2, chatter = _compute(tmp, cutoff)
            if rep2.get("error"):
                out("  like-for-like run refused: %s" % rep2["error"][:160])
                rep2 = None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if rep2 and PE.ddmmyyyy(rep2["as_on"]) == as_on:
            mine = {it["item"]: float(it["qty"]) for it in rep2["items"]}
            for item, q in mine.items():
                if item not in theirs:
                    continue
                d = q - theirs[item]
                if abs(d) < 0.001:
                    same += 1
                else:
                    differ += 1
                    gap += abs(d)
                    diffs.append((item, q, theirs[item], d))
            only_here = len([i for i in mine if i not in theirs])
            only_pc = len([i for i in theirs if i not in mine])
            out("  against the PC's own figure (%s, pushed %s), over the %d file(s) it had by then:"
                % (src, (at or "")[:16].replace("T", " "), kept))
            out("    same %d · differ %d (%.0f units) · only here %d · only on the PC %d"
                % (same, differ, gap, only_here, only_pc))
        elif rep2:
            out("  the like-for-like run lands on %s, not %s -- not compared"
                % (PE.ddmmyyyy(rep2["as_on"]), as_on))
            theirs = {}
    else:
        out("  the PC has pushed no computed figure for %s yet -- nothing to compare" % as_on)
    verdict = ("no pc figure" if not theirs else
               "same" if (differ == 0 and only_here == 0 and only_pc == 0) else "differs")
    diffs.sort(key=lambda t: -abs(t[3]))
    for item, q, p, d in diffs[:8]:
        out("      %-30s server %8.0f   PC %8.0f   %+.0f" % (item[:30], q, p, d))
    con.executemany("INSERT INTO sh_diff (run_id, item, server_qty, pc_qty, diff) VALUES (?,?,?,?,?)",
                    [(run_id,) + d for d in diffs[:MAX_DIFF_ROWS]])
    con.execute("UPDATE sh_run SET finished=?, as_on=?, items=?, pc_source=?, pc_at=?, same=?, "
                "differ=?, gap_units=?, only_here=?, only_pc=?, verdict=?, cutoff=? WHERE id=?",
                (now_ist().isoformat(), as_on, len(rep["items"]), src, at, same, differ, gap,
                 only_here, only_pc, verdict, cutoff, run_id))
    for line in chatter:
        t = line.strip()
        if t.startswith(("!!", "keying", "CLIPPED", "LATE-KEYED")):
            out("  [compute] " + t[:150])
    feed_counts(con, run_id, rep, out)
    con.commit()
    try:
        with open(HEARTBEAT, "w") as fh:
            json.dump(dict(finished=now_ist().isoformat(), baseline=base, as_on=as_on,
                           items=len(rep["items"]), same=same, differ=differ, verdict=verdict), fh)
    except OSError:
        pass
    con.close()
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--baseline", default=None)
    ap.add_argument("--archive", default=ARCHIVE)
    ap.add_argument("--upto", default=None, help="compute only to this date, dd-mm-yyyy (checks only)")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args(argv)
    if os.path.exists(OFF_FLAG):
        return 0
    lines = []
    rc = run(a.db, a.baseline, a.archive, out=(lines.append if a.quiet else print), upto=a.upto)
    if a.quiet and rc:
        print("\n".join(lines))
    return rc


if __name__ == "__main__":
    sys.exit(main())
