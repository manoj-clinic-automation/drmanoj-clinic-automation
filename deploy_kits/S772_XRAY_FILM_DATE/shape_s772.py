#!/usr/bin/env python3
"""shape_s772.py -- the S772 records.py on a SCRATCH copy of a real finance.db, with the check folder listed from the copy's own
parked rows (a stub; no Drive). With --no-film every parked picture counts as read with nothing found (the ID rule only). Prints COUNTS ONLY -- never a name, an ID or a
Drive id. usage: shape_s772.py <dir with records.py> <scratch db> <now 'YYYY-MM-DDTHH:MM:SS'> [--no-film]"""
import collections
import importlib.util
import json
import os
import sqlite3
import sys
import tempfile

app, dbp, now = sys.argv[1], sys.argv[2], sys.argv[3]
assert "scratch" in dbp or dbp.startswith("/tmp"), "scratch only"
stub = tempfile.mkdtemp(prefix="shape772_")
os.environ["RECORDS_DRIVE_STUB"] = stub
os.environ["RECORDS_NOW"] = now
sys.path.insert(0, app)
spec = importlib.util.spec_from_file_location("rec772shape", os.path.join(app, "records.py"))
rec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rec)
con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
rec.ensure(con)
rec.xray_ensure(con)
if len(sys.argv) > 4 and sys.argv[4] == "--no-film":                # a copy with no film reads: every parked picture 'read, nothing found'
    con.execute("CREATE TABLE IF NOT EXISTS xray_filmdate(src_id TEXT PRIMARY KEY, dates TEXT NOT NULL DEFAULT '[]', ids TEXT NOT NULL DEFAULT '[]', "
                "how TEXT NOT NULL DEFAULT '', secs REAL NOT NULL DEFAULT 0, read_at TEXT NOT NULL DEFAULT '')")
    con.execute("INSERT OR IGNORE INTO xray_filmdate(src_id, dates, ids, how) SELECT src_id, '[]', '[]', 'shape' FROM xray_filing WHERE state='check'")
con.commit()
inbox, test, check = (rec.setting(con, k) for k in ("xray_inbox_id", "xray_test_id", "xray_check_id"))
for fid in (inbox, test):
    json.dump([], open(os.path.join(stub, "list_%s.json" % fid), "w"))
park = con.execute("SELECT src_id, orig_name, file_time FROM xray_filing WHERE state='check'").fetchall()
listing = [{"id": r["src_id"], "name": r["orig_name"], "mimeType": "image/jpeg", "md5Checksum": "m" + r["src_id"],
            "modifiedTime": rec._s752_utc(r["file_time"]) or "2026-11-09T13:40:00.000Z"} for r in park]
json.dump(listing, open(os.path.join(stub, "list_%s.json" % check), "w"))


def baaki():
    c = collections.Counter()
    for r in con.execute("SELECT DISTINCT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.series='xp' AND s.state='ok' "
                         "AND i.kind='xray' AND s.clinic_id<>'' AND s.day>='2026-09-01'"):
        if not con.execute("SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=?", (r[1], r[0])).fetchone() \
                and not con.execute("SELECT 1 FROM xray_filing WHERE state='planned' AND action='file' AND clinic_id=? AND day=?", (r[1], r[0])).fetchone():
            c[r[0][:7]] += 1
    return dict(sorted(c.items()))


b0 = baaki()
items, notes = rec.xray_actions(con)
allp = con.execute("SELECT action, verdict FROM xray_filing WHERE state='planned'").fetchall()
kinds = collections.Counter()
for r in allp:
    v = r["verdict"] or ""
    if r["action"] == "dup":
        kinds["to duplicates: " + ("filed to another patient (void)" if "mistyped" in v else "older copy replaced")] += 1
    elif "S772" in v or "printed on the film" in v:
        kinds["filed by S772: " + ("the film's ID" if "ID printed on the film" in v or "the date and the ID" in v else
                                  ("the film's date" if "printed on the film" in v else "the ID's one open day"))] += 1
    elif v.startswith("S752"):
        kinds["filed by S752 (as before)"] += 1
    else:
        kinds["other planned"] += 1
print("parked before: %d" % len(park))
for k, v in sorted(kinds.items()):
    print("  %3d  %s" % (v, k))
held = [r for r in con.execute("SELECT src_id FROM xray_filing WHERE state='check'")]
print("records voided now: %d (the clean-up runs after the mailbox files the corrected copies)" % con.execute("SELECT COUNT(*) FROM record_file WHERE state='void' AND note LIKE 'S772%'").fetchone()[0])
# the next run, as if the mailbox had filed every planned picture: the clean-up it would do
fake = [{"id": r["src_id"], "action": "file", "dest_id": "shapeDEST" + r["src_id"][-10:], "name": r["new_name"]}
        for r in con.execute("SELECT src_id, new_name FROM xray_filing WHERE state='planned' AND action='file'")]
rec.xray_done(con, fake)
done_ids = {x["id"] for x in fake}
json.dump([x for x in listing if x["id"] not in done_ids], open(os.path.join(stub, "list_%s.json" % check), "w"))
items2, _ = rec.xray_actions(con)
d2 = collections.Counter()
for r in con.execute("SELECT verdict FROM xray_filing WHERE state='planned' AND action='dup' AND verdict LIKE 'S772%'"):
    d2["older copy replaced" if "replaced" in r[0] else "filed to another patient (void)"] += 1
print("the next run's clean-up: %s" % dict(d2))
print("records voided after it: %d" % con.execute("SELECT COUNT(*) FROM record_file WHERE state='void' AND note LIKE 'S772%'").fetchone()[0])
print("still parked for a person: %d" % con.execute("SELECT COUNT(*) FROM xray_filing WHERE state='check'").fetchone()[0])
print("mailbox items this run: %d (batch cut %d)" % (len(items), rec.XRAY_BATCH))
print("photo baaki by month before: %s" % b0)
print("photo baaki by month after : %s" % baaki())
print("notes: %s" % notes)
con.rollback()
print("SHAPE DONE")
