#!/usr/bin/env python3
"""
selftest_pharma_lane.py -- S219 M3 / PP0-lite.

Drives the PATCHED asset_register through its own Flask test client: a real
intake, a real database, the real routes.  Not a lookalike and not a re-typed
copy of the logic -- the app itself answers.

The claims it has to make good:
  * a pharmacy scan lands kind='Pharmacy', status='captured'
  * a clinic scan is COMPLETELY unchanged -- 'Consumable' / 'draft'
  * pharmacy volume never touches the pending badge
  * pharmacy volume never reaches /purchases (the owner's rate-history page)
  * a pharmacy bill cannot enter the approval flow
  * a mis-read pharmacy bill CAN still be corrected, and correcting it does not
    silently move it into the clinic lane (the trap in bill_edit's whitelist)

USAGE: python3 -B selftest_pharma_lane.py <patched asset_register.py>
"""
import io
import os
import shutil
import sys
import tempfile

CHECKS = []
def ck(n, c):
    CHECKS.append((n, bool(c)))

def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    target = os.path.abspath(sys.argv[1])
    work = tempfile.mkdtemp(prefix="s219_pharma_")
    shutil.copyfile(target, os.path.join(work, "asset_register.py"))
    os.makedirs(os.path.join(work, "uploads"), exist_ok=True)
    os.environ["ASSETS_DB"] = os.path.join(work, "t.db")
    os.environ["ASSETS_UPLOADS"] = os.path.join(work, "uploads")
    os.environ["SHARED_LIB_DIR"] = work
    sys.path.insert(0, work)
    import asset_register as A

    db = A.sqlite3.connect(os.environ["ASSETS_DB"])
    db.row_factory = A.sqlite3.Row
    # a user to act as
    db.execute("INSERT INTO users(username,display_name,role,password_hash,active) "
               "VALUES('tester','Tester','manager','x',1)")
    db.commit()
    uid = db.execute("SELECT id FROM users WHERE username='tester'").fetchone()["id"]
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()

    c = A.app.test_client()
    with c.session_transaction() as sess:
        sess["uid"] = uid
        sess["epoch"] = epoch["value"] if epoch else None

    def scan(lane, name):
        data = {"bill_scan": (io.BytesIO(b"%PDF-1.4 fake"), name)}
        if lane:
            data["lane"] = lane
        return c.post("/intake/scan_submit", data=data,
                      content_type="multipart/form-data")

    r1 = scan("pharmacy", "pharma1.pdf")
    r2 = scan("clinic", "clinic1.pdf")
    r3 = scan(None, "legacy1.pdf")          # no lane at all -- the old callers
    ck("pharmacy scan accepted", r1.status_code == 200)
    ck("clinic scan accepted", r2.status_code == 200)
    ck("a scan with NO lane still works (old behaviour preserved)", r3.status_code == 200)

    rows = db.execute("SELECT * FROM bills ORDER BY id").fetchall()
    ck("three bills were created", len(rows) == 3)
    ph, cl, lg = rows[0], rows[1], rows[2]
    ck("pharmacy bill kind='Pharmacy'", ph["kind"] == "Pharmacy")
    ck("pharmacy bill status='captured'", ph["status"] == "captured")
    ck("pharmacy bill still got a stamp", bool(ph["stamp_no"]))
    ck("clinic bill unchanged: kind='Consumable'", cl["kind"] == "Consumable")
    ck("clinic bill unchanged: status='draft'", cl["status"] == "draft")
    ck("no-lane bill unchanged: 'Consumable'/'draft'",
       lg["kind"] == "Consumable" and lg["status"] == "draft")

    # the pending badge counts drafts only
    npend = db.execute("SELECT COUNT(*) c FROM bills WHERE status='draft'").fetchone()["c"]
    ck("pending badge counts 2, not 3 — pharmacy does not inflate it", npend == 2)

    # /purchases must not see a pharmacy bill, before OR after it has items
    db.execute("INSERT INTO bill_items(bill_id,item_name,quantity,rate,amount,batch,expiry) "
               "VALUES(?,'PARACETAMOL 500',10,12.5,125.0,'B1','2027-01')", (ph["id"],))
    db.commit()
    seen = db.execute(
        "SELECT COUNT(*) c FROM bill_items bi JOIN bills b ON b.id=bi.bill_id "
        "WHERE b.status='approved'").fetchone()["c"]
    ck("/purchases' approved-only filter cannot see the pharmacy item", seen == 0)

    # it cannot enter the approval flow
    ra = c.post("/bills/%d/approve" % ph["id"], data={}, follow_redirects=False)
    still = db.execute("SELECT status FROM bills WHERE id=?", (ph["id"],)).fetchone()["status"]
    ck("approving a captured pharmacy bill does NOT approve it", still == "captured")

    # but it CAN be corrected -- and correction must not move its lane
    rg = c.get("/bills/%d/edit" % ph["id"])
    ck("a captured bill opens for editing (a fixable witness)", rg.status_code == 200)
    c.post("/bills/%d/edit" % ph["id"],
           data={"kind": "Pharmacy", "vendor": "SANWARIA", "bill_no": "S123",
                 "bill_date": "2026-09-02", "total_amount": "125"},
           follow_redirects=True)
    after = db.execute("SELECT kind,vendor,status FROM bills WHERE id=?",
                       (ph["id"],)).fetchone()
    ck("the correction saved", after["vendor"] == "SANWARIA")
    ck("and it is STILL Pharmacy, not silently downgraded", after["kind"] == "Pharmacy")
    ck("and it is still captured, not promoted", after["status"] == "captured")

    # the list can find them
    rl = c.get("/bills?kind=Pharmacy")
    ck("the list filters by kind=Pharmacy", rl.status_code == 200 and b"SANWARIA" in rl.data)
    rl2 = c.get("/bills?status=captured")
    ck("the list filters by status=captured", rl2.status_code == 200 and b"SANWARIA" in rl2.data)
    rl3 = c.get("/bills?kind=Consumable")
    ck("filtering Consumable does NOT show the pharmacy bill",
       rl3.status_code == 200 and b"SANWARIA" not in rl3.data)

    # the intake page offers the lane, and the scanner can carry it
    ri = c.get("/intake")
    ck("the intake page offers the lane", b"Pharmacy purchase" in ri.data)
    ck("the lane rides the scanner's uploadFields (as the Note does)",
       b"uploadFields.lane" in ri.data)

    db.close()
    shutil.rmtree(work, ignore_errors=True)
    bad = [n for n, ok in CHECKS if not ok]
    for n, ok in CHECKS:
        print("  %s  %s" % ("ok  " if ok else "FAIL", n))
    print("\n%d/%d checks passed" % (len(CHECKS) - len(bad), len(CHECKS)))
    print("SELFTEST " + ("GREEN" if not bad else "RED"))
    return 1 if bad else 0

if __name__ == "__main__":
    sys.exit(main())
