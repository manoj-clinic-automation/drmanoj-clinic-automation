#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figure_s466.py -- READ-ONLY on the live system: the warranty, shown the box's REAL papers on a COPY of assets.db.

The installer copies /root/assetapp/assets.db into its scratch folder (sqlite's own backup, read-only on the live
file) and points the edited app at the COPY. This then, as the owner:
  * opens Renewals & warranties (both views), the list, and the page of each Dr MK expense paper (up to 6);
  * on ONE real Dr MK expense paper, if there is one: saves a warranty ending in 10 days, sees it on Renewals, sees
    that /api/due (what goes out on WhatsApp) answers exactly what it answered before, and removes it again.
It prints counts and paper numbers only (no supplier, no amount) and writes nothing outside the scratch folder.
   usage: figure_s466.py <scratch assetapp folder>     env: S466_ROOT, ASSETS_DB, ASSETS_UPLOADS (all scratch)
"""
import datetime
import os
import sqlite3
import sys


def main():
    d = os.path.abspath(sys.argv[1])
    scratch = os.path.realpath(os.environ.get("S466_ROOT", "")) + os.sep
    os.chdir(d)
    sys.path.insert(0, d)
    import asset_register as A
    if not os.path.realpath(A.DB_PATH).startswith(scratch) or not os.path.realpath(A.UPLOAD_DIR).startswith(scratch):
        print("FIGURE_S466 REFUSED: the database or the uploads folder is not the scratch one")
        return 1
    if "d664_warranty" not in A.app.view_functions:
        print("FIGURE_S466 RED: the warranty did not mount on the box's own database")
        return 1
    con = sqlite3.connect(A.DB_PATH)
    con.row_factory = sqlite3.Row
    own = con.execute("SELECT id FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone()
    ep = con.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()
    tok = con.execute("SELECT value FROM settings WHERE key='api_token'").fetchone()
    if not own or not ep or not tok:
        print("FIGURE_S466 RED: no active owner login, or no api token, in the copy")
        return 1
    c = A.app.test_client()
    with c.session_transaction() as s:
        s["uid"], s["epoch"] = own["id"], ep["value"]
    bad = []
    for pth, must in (("/renewals", "warranties"), ("/renewals?all=1", "warranties"), ("/papers", "Clinic papers to sort"), ("/bills", "")):
        r = c.get(pth)
        if r.status_code != 200 or must not in r.get_data(as_text=True):
            bad.append("%s %s" % (pth, r.status_code))
    due0 = c.get("/api/due?token=" + tok["value"])
    if due0.status_code != 200:
        bad.append("/api/due %s" % due0.status_code)
    exp = con.execute("SELECT id, stamp_no FROM bills WHERE COALESCE(lane,'clinic')='owner_expense' AND status<>'rejected' ORDER BY id DESC").fetchall()
    for b in exp[:6]:
        for pth, must in (("/papers/%d" % b["id"], "Keep the warranty"), ("/bills/%d" % b["id"], "Warranty:")):
            r = c.get(pth)
            if r.status_code != 200 or must not in r.get_data(as_text=True):
                bad.append("%s %s" % (pth, r.status_code))
    already = con.execute("SELECT COUNT(*) FROM d664_warranty").fetchone()[0]
    if bad:
        print("FIGURE_S466 RED: " + "; ".join(bad[:6]))
        return 1
    said = "there is no Dr MK expense paper yet, so no real save was rehearsed"
    free = [b for b in exp if not con.execute("SELECT 1 FROM d664_warranty WHERE bill_id=?", (b["id"],)).fetchone()]
    if free:
        b = free[0]
        till = (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
        r = c.post("/papers/%d/warranty" % b["id"], data={"what": "figure check", "till": till, "remind": "30"})
        row = con.execute("SELECT till, remind_days FROM d664_warranty WHERE bill_id=?", (b["id"],)).fetchone()
        ren = c.get("/renewals").get_data(as_text=True)
        due1 = c.get("/api/due?token=" + tok["value"])
        ok = (r.status_code == 302 and row is not None and row["till"] == till and "figure check" in ren
              and "Dr MK expense" in ren and due1.get_data() == due0.get_data())
        r2 = c.post("/papers/%d/warranty" % b["id"], data={"remove": "1"})
        gone = con.execute("SELECT 1 FROM d664_warranty WHERE bill_id=?", (b["id"],)).fetchone() is None
        if not ok or r2.status_code != 302 or not gone or "figure check" in c.get("/renewals?all=1").get_data(as_text=True):
            print("FIGURE_S466 RED: the real save on %s did not behave (saved %s, on Renewals %s, /api/due unchanged %s, removed %s)"
                  % (b["stamp_no"], row is not None, "figure check" in ren, due1.get_data() == due0.get_data(), gone))
            return 1
        said = ("ONE REAL SAVE REHEARSED on the copy: a warranty on %s showed on Renewals, /api/due answered exactly as before, "
                "and it was removed again" % b["stamp_no"])
    print("FIGURE_S466 OK: on a copy of the box's own database Renewals, the list and every Dr MK expense paper's page open. "
          "Dr MK expense papers: %d (%s). Warranties already noted: %d. %s."
          % (len(exp), ", ".join(b["stamp_no"] or ("#%d" % b["id"]) for b in exp[:10]) or "none", already, said))
    return 0


if __name__ == "__main__":
    sys.exit(main())
