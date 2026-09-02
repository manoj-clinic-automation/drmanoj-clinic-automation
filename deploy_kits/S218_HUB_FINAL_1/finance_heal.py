#!/usr/bin/env python3
"""
finance_heal.py -- S218: heal-on-landing for stuck records (v1 scope).

THE OWNER'S DIAGNOSIS (01-Sep): feeds land late and out of order, so records
written in the gap STICK after reality has healed. This module re-checks stuck
records against current data and quiets the healed ones -- the record itself is
never lost (every heal is written to heal_log with what healed it and when).

V1 SCOPE -- only what can be re-checked by the ORIGINAL rule (D349):
  1. recon_exception kind='upi_vs_statement', status='open'
     -> finance_upi.reconcile_upi(day) re-runs THE rule; it resolves matches
        itself and leaves true mismatches open.
  2. data_flag code='BANKMATCH_FEED_MISSING'
     -> healed when a upi_statement row for that unit+day now exists.
  3. data_flag code='MARG_DAY_NOT_FILED'
     -> healed when the day is filed AND a non-superseded ingest batch exists.
  data_flag rows have no status column, so a healed flag is COPIED to heal_log
  and then deleted (the same end-state the owner's manual "stale flag - remove"
  produces, but recorded and automatic).
  line_sum_vs_day_total is NOT healed here -- its rule involves patient
  attribution and moves to the returns build. Stated, not hidden.

Runs: */30 cron (8-22h) + the hub's "Recheck now" button. Idempotent.
USAGE: /root/wa/venv/bin/python3 /root/finance/finance_heal.py [--dry-run]
"""
import datetime as dt
import os
import sqlite3
import sys

FIN_DIR = os.environ.get("FIN_DIR", "/root/finance")
DB_PATH = os.environ.get("FINANCE_DB", os.path.join(FIN_DIR, "finance.db"))
sys.path.insert(0, FIN_DIR)


def ensure_log(con):
    con.execute("""CREATE TABLE IF NOT EXISTS heal_log (
        id INTEGER PRIMARY KEY, healed_at TEXT, kind TEXT, unit TEXT,
        business_date TEXT, source_table TEXT, source_id INTEGER,
        detail TEXT, healed_by TEXT)""")


def run(con, dry=False, now=None):
    ensure_log(con)
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    out = dict(rechecked=0, healed=0, still_open=0, items=[])
    import finance_upi                                        # noqa: PLC0415

    # 1 -- upi_vs_statement: re-run the original rule
    rows = con.execute("SELECT id, unit, business_date FROM recon_exception "
                       "WHERE kind='upi_vs_statement' AND status='open'").fetchall()
    for r in rows:
        out["rechecked"] += 1
        if dry:
            continue
        res = finance_upi.reconcile_upi(con, r[1], r[2])
        st = con.execute("SELECT status FROM recon_exception WHERE id=?", (r[0],)).fetchone()
        if st and st[0] != "open":
            out["healed"] += 1
            out["items"].append("upi_vs_statement %s healed (bank now agrees)" % r[2])
            con.execute("INSERT INTO heal_log (healed_at,kind,unit,business_date,"
                        "source_table,source_id,detail,healed_by) VALUES (?,?,?,?,?,?,?,?)",
                        (now, "upi_vs_statement", r[1], r[2], "recon_exception", r[0],
                         "re-run of reconcile_upi found agreement", "finance_heal"))
        else:
            out["still_open"] += 1

    # 1b -- missing_day exceptions: healed the moment the day is filed
    rows = con.execute("SELECT id, unit, business_date FROM recon_exception "
                       "WHERE kind='missing_day' AND status='open'").fetchall()
    for r in rows:
        out["rechecked"] += 1
        e = con.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?",
                        (r[1], r[2])).fetchone()
        if not e:
            out["still_open"] += 1
            continue
        out["healed"] += 1
        out["items"].append("missing_day %s healed (day now filed)" % r[2])
        if not dry:
            con.execute("UPDATE recon_exception SET status='resolved', "
                        "resolution='healed: the day is now filed (finance_heal)', "
                        "closed_by='finance_heal', closed_at=? WHERE id=?", (now, r[0]))
            con.execute("INSERT INTO heal_log (healed_at,kind,unit,business_date,"
                        "source_table,source_id,detail,healed_by) VALUES (?,?,?,?,?,?,?,?)",
                        (now, "missing_day", r[1], r[2], "recon_exception", r[0],
                         "day entry now exists", "finance_heal"))

    # 2 -- BANKMATCH_FEED_MISSING: healed when the statement exists now
    rows = con.execute("SELECT id, unit, business_date, detail FROM data_flag "
                       "WHERE code='BANKMATCH_FEED_MISSING'").fetchall()
    for r in rows:
        out["rechecked"] += 1
        have = con.execute("SELECT 1 FROM upi_statement WHERE unit=? AND statement_date=?",
                           (r[1], r[2])).fetchone()
        if not have:
            out["still_open"] += 1
            continue
        out["healed"] += 1
        out["items"].append("BANKMATCH_FEED_MISSING %s healed (statement arrived)" % r[2])
        if not dry:
            con.execute("INSERT INTO heal_log (healed_at,kind,unit,business_date,"
                        "source_table,source_id,detail,healed_by) VALUES (?,?,?,?,?,?,?,?)",
                        (now, "BANKMATCH_FEED_MISSING", r[1], r[2], "data_flag", r[0],
                         (r[3] or "")[:200] + " | statement now on file", "finance_heal"))
            con.execute("DELETE FROM data_flag WHERE id=?", (r[0],))

    # 3 -- MARG_DAY_NOT_FILED: healed when filed AND a live batch exists
    rows = con.execute("SELECT id, unit, business_date, detail FROM data_flag "
                       "WHERE code='MARG_DAY_NOT_FILED'").fetchall()
    for r in rows:
        out["rechecked"] += 1
        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                        (r[1], r[2])).fetchone()
        b = e and con.execute("SELECT 1 FROM ingest_batch WHERE day_entry_id=? "
                              "AND status!='superseded'", (e[0],)).fetchone()
        if not b:
            out["still_open"] += 1
            continue
        out["healed"] += 1
        out["items"].append("MARG_DAY_NOT_FILED %s healed (day filed + export applied)" % r[2])
        if not dry:
            con.execute("INSERT INTO heal_log (healed_at,kind,unit,business_date,"
                        "source_table,source_id,detail,healed_by) VALUES (?,?,?,?,?,?,?,?)",
                        (now, "MARG_DAY_NOT_FILED", r[1], r[2], "data_flag", r[0],
                         (r[3] or "")[:200] + " | day filed and batch applied", "finance_heal"))
            con.execute("DELETE FROM data_flag WHERE id=?", (r[0],))

    if not dry:
        con.commit()
    return out


def main():
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    out = run(con, dry=dry)
    print("rechecked %d | healed %d | still open %d%s"
          % (out["rechecked"], out["healed"], out["still_open"],
             " (DRY RUN, nothing written)" if dry else ""))
    for i in out["items"]:
        print("  " + i)
    return 0


if __name__ == "__main__":
    sys.exit(main())
