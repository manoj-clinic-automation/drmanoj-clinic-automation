#!/usr/bin/env python3
"""claude_reread.py -- S550 (D723): Claude reads the scans already in the scan app, once, oldest first.

    python3 claude_reread.py [--db /root/assetapp/assets.db] [--uploads /root/assetapp/uploads] [--limit N] [--gap SECONDS] [--ids 1,2]

- Every paper with a scan that Claude has not yet read well, except: rejected papers, the Other-document lane, and the
  Personal and Resumes sections (a person's papers are never sent in bulk).
- A paper still to be sorted (not approved) whose supplier, amount or items are empty is filled through the app's OWN
  filling step (asset_register._bg_extract with this reading): only what is empty, then the app's own after-checks (the
  month, the double guard, the S441 checks, the way home) -- exactly as a new scan.
- An approved paper and a pharmacy paper: the reading is kept aside and nothing on the paper is written.
- One at a time, a pause between papers; it leaves 50 of the day's calls for the new scans and stops at the day's limit (run
  it again the next day -- it carries on where it stopped). It stops at once when the key is refused or the credit runs out.
- Progress in settings 'read.reread_progress' (the owner's admin card shows it). One copy at a time (a lock file).
Prints no key and no person's name."""
import argparse, datetime as _dt, fcntl, os, sqlite3, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import claude_reader as CR                                           # noqa: E402

RESERVE = 50
KIND_LANE_SQL = ("COALESCE(NULLIF(b.lane,''), CASE b.kind WHEN 'Pharmacy' THEN 'pharmacy' WHEN 'Lab' THEN 'lab_purchase' "
                 "WHEN 'Expense' THEN 'owner_expense' WHEN 'Document' THEN 'other_doc' ELSE 'clinic' END)")


def progress(con, text):
    CR.set_setting(con, "read.reread_progress", "%s (%s)" % (text, _dt.datetime.now().strftime("%d-%b %H:%M")))


def the_app(db, uploads):
    """The scan app's own module, for its filling step. None -> readings are kept, nothing is filled."""
    os.environ["ASSETS_DB"] = db
    os.environ["ASSETS_UPLOADS"] = uploads
    try:
        import asset_register as m                                   # noqa: E402
        return m if hasattr(m, "_bg_extract") else None
    except Exception as e:                                           # noqa: BLE001
        print("the app could not be loaded (%s) -- readings are kept, nothing is filled" % type(e).__name__)
        return None


def row(con, bid):
    return con.execute("SELECT b.id, b.status, b.vendor, b.total_amount, COALESCE(b.subgroup,'') sg, " + KIND_LANE_SQL + " lane, "
                       "(SELECT COUNT(*) FROM bill_items i WHERE i.bill_id=b.id) nit FROM bills b WHERE b.id=?", (bid,)).fetchone()


def to_fill(r):
    return (r is not None and r["status"] not in ("approved", "rejected") and r["lane"] not in ("pharmacy", "other_doc")
            and r["sg"] not in ("personal", "resume") and (not r["vendor"] or r["total_amount"] is None or r["nit"] == 0))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.environ.get("ASSETS_DB") or os.path.join(HERE, "assets.db"))
    ap.add_argument("--uploads", default=os.environ.get("ASSETS_UPLOADS") or os.path.join(HERE, "uploads"))
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--gap", type=float, default=1.0)
    ap.add_argument("--ids", default="", help="only these paper ids, comma-separated")
    a = ap.parse_args(argv)
    lock = open(os.path.join(os.path.dirname(os.path.abspath(a.db)), ".claude_reread.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print("another re-read is already running -- nothing to do"); return 0
    try:
        return _run(a)
    finally:
        try:
            fcntl.flock(lock, fcntl.LOCK_UN); lock.close()
        except OSError:
            pass


def _run(a):
    con = CR._db(a.db)
    CR.ensure(con)
    rows = con.execute(
        "SELECT b.id, b.source_stored FROM bills b LEFT JOIN claude_reading c ON c.bill_id=b.id "
        "WHERE b.source_stored IS NOT NULL AND b.source_stored<>'' AND COALESCE(b.status,'')<>'rejected' "
        "AND " + KIND_LANE_SQL + "<>'other_doc' AND COALESCE(b.subgroup,'') NOT IN ('personal','resume') "
        "AND COALESCE(c.ok,0)=0 ORDER BY b.id").fetchall()
    if a.ids:
        want = {int(x) for x in a.ids.split(",") if x.strip().isdigit()}
        rows = [r for r in rows if r["id"] in want]
    if a.limit:
        rows = rows[:a.limit]
    total = len(rows)
    app = the_app(a.db, a.uploads)
    if app is None:                                                  # nothing is read (and paid for) that could not be filled
        progress(con, "not started \u2014 the app could not be loaded; run it again")
        print("not started: the app could not be loaded")
        con.close()
        return 1
    done = filled = failed = 0
    progress(con, "started: %d papers to read" % total)
    print("%d papers to read" % total)
    why = "finished"
    for r in rows:
        try:
            st = CR.state(con)
            if st != "on":
                why = "stopped: Claude is %s" % st; break
            if CR.calls_today(con) >= CR.cap(con) - RESERVE:
                why = "paused: the day's limit reached -- run again tomorrow"; break
            path = os.path.join(a.uploads, r["source_stored"])
            done += 1
            if not os.path.exists(path):
                failed += 1; continue
            data = CR.read(path, bid=r["id"], db_path=a.db)
            if data is None:
                failed += 1
            elif app is not None and to_fill(row(con, r["id"])):         # looked at again just before writing
                hdr, items = CR.to_bill(data)
                if app._bg_extract(r["id"], path, _reading=(hdr, items)) == "read":
                    filled += 1
                else:                                                # not filled (a busy database): read again next run
                    con.execute("UPDATE claude_reading SET ok=0, error='not filled -- read again next run' WHERE bill_id=?", (r["id"],))
                    con.commit()
                    failed += 1
        except sqlite3.Error as e:                                   # a busy database: this paper waits for the next run
            failed += 1
            print("paper %s: database busy (%s)" % (r["id"], type(e).__name__))
            time.sleep(5)
        except Exception as e:                                       # noqa: BLE001  -- one paper never stops the rest
            failed += 1
            print("paper %s: %s" % (r["id"], type(e).__name__))
        if done % 5 == 0:
            try:
                progress(con, "%d of %d read · %d filled in · %d could not be read" % (done, total, filled, failed))
            except sqlite3.Error:
                pass
        time.sleep(a.gap)
    progress(con, "%s — %d of %d read · %d filled in · %d could not be read" % (why, done, total, filled, failed))
    print("%s: %d of %d read, %d filled in, %d could not be read" % (why, done, total, filled, failed))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
