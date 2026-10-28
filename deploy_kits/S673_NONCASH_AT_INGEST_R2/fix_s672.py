"""fix_s672.py -- kit S672_NONCASH_AT_INGEST, the ONE-TIME data step (F-1037; the owner's "yes", 08:57 IST 28-Oct-2026).
27-Oct-2026 was approved before its procedure bill A004474 ("PROSIJER <patient>", Rs 98) was deducted. This adds exactly that one
day_noncash_bill row -- the row day_resync would have made -- with one audit row, and, if Darpan has already handed over 27-Oct,
re-decides his day on the corrected figure. It REFUSES unless the day's only undeducted label bill is A004474 as procedure medicine.
  --db PATH   --lib DIR (the finance folder holding day_resync.py)   --apply (without it: say only)"""
import argparse, hashlib, json, sqlite3, sys

ap = argparse.ArgumentParser()
ap.add_argument("--db", required=True); ap.add_argument("--lib", required=True); ap.add_argument("--apply", action="store_true")
a = ap.parse_args()
sys.path.insert(0, a.lib)
import day_resync as DR      # noqa: E402

DAY, BILL, HEAD = "2026-10-27", "A004474", "procedure_medicine"
WHY = "S672 one-time: the day was approved before this bill was deducted (F-1037); the owner's yes 28-Oct-2026 08:57 IST"
con = sqlite3.connect(a.db, timeout=60); con.row_factory = sqlite3.Row
e = con.execute("SELECT id, business_date, status FROM day_entry WHERE unit='medical' AND business_date=?", (DAY,)).fetchone()
if e is None:
    print("STOP: no pharmacy day %s" % DAY); sys.exit(2)
if con.execute("SELECT 1 FROM day_noncash_bill WHERE unit='medical' AND bill_no=? AND bill_date=?", (BILL, DAY)).fetchone():
    print("ALREADY: %s is deducted on %s -- nothing written" % (BILL, DAY)); sys.exit(0)
hw = DR.words(con, "noncash.home_words", DR.HOME_DEFAULT); pw = DR.words(con, "noncash.proc_words", DR.PROC_DEFAULT)
missing = []
for bill, bdate, head, amt, where in DR.label_bills(con, e, hw, pw):
    if con.execute("SELECT 1 FROM day_noncash_bill WHERE unit='medical' AND bill_no=? AND bill_date=?", (bill, bdate)).fetchone():
        continue
    if amt == 0:
        continue
    missing.append((bill, bdate, head, amt, where))
if len(missing) != 1 or missing[0][0] != BILL or missing[0][2] != HEAD or missing[0][3] <= 0:
    print("STOP: the day's undeducted label bills are not exactly %s as procedure medicine: %s" % (
        BILL, [(m[0], m[2], m[3]) for m in missing])); sys.exit(2)
bill, bdate, head, amt, where = missing[0]
line = "%s %s %s on %s (day %s, found in %s)" % (bill, head, DR.rupees(amt), DAY, e["status"], where)
if not a.apply:
    print("WOULD_ADD: " + line); sys.exit(0)
now = DR.now_iso()
con.execute("INSERT INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, note, entered_by, entered_at, noncash_uid) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (e["id"], "medical", bdate, head, bill, amt, "from Marg's customer text (%s), %s" % (where, WHY), DR.WHO, now,
             "nc" + hashlib.md5(("%s|%s|%s" % ("medical", bill, bdate)).encode()).hexdigest()[:14]))
con.execute("INSERT INTO audit_log (table_name, row_id, action, after_json, by_whom, at) VALUES ('day_entry', ?, 'noncash_sync', ?, ?, ?)",
            (e["id"], json.dumps(dict(date=DAY, added=[dict(bill=bill, head=head, amount_p=amt, source=where)], adjustments=[],
                                      kit="S672 one-time", why=WHY)), DR.WHO, now))
redo = ""
try:
    hr = con.execute("SELECT handed_p FROM darpan_kal_day WHERE unit='medical' AND business_date=?", (DAY,)).fetchone()
except sqlite3.OperationalError:
    hr = None
if hr is not None and hr["handed_p"] is not None:
    import darpan_kal as DK      # noqa: E402,PLC0415  (on the box: the service's venv)
    row = DK._row(con, DAY)
    v = DK._decide(con, DAY, DK.compute_day(con, DAY), row, "system")
    redo = "; Darpan's handover of 27-Oct re-decided on it: %s" % json.dumps(v)
con.commit()
print("ADDED: " + line + redo)
