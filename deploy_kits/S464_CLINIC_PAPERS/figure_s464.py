#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""figure_s464.py -- READ-ONLY on the live system: the new pages, shown the box's REAL papers on a COPY of assets.db.

The installer copies /root/assetapp/assets.db into its scratch folder (sqlite's own backup, read-only on the live
file) and points the edited app at the COPY. This then opens the three new pages as the owner and counts what the
suggestions would say -- so the first time the owner opens the page is not the first time it met his data. It prints
counts only (no supplier, no amount), writes nothing outside the scratch folder, and the copy is removed afterwards.
   usage: figure_s464.py <scratch assetapp folder>      (env ASSETS_DB / ASSETS_UPLOADS point at the scratch copy)
"""
import os
import sqlite3
import sys


def main():
    d = os.path.abspath(sys.argv[1])
    scratch = os.path.realpath(os.environ.get("S464_ROOT", "")) + os.sep
    os.chdir(d)
    sys.path.insert(0, d)
    import asset_register as A
    if not os.path.realpath(A.DB_PATH).startswith(scratch) or not os.path.realpath(A.UPLOAD_DIR).startswith(scratch):
        print("FIGURE_S464 REFUSED: the database or the uploads folder is not the scratch one")
        return 1
    if "d664_papers" not in A.app.view_functions:
        print("FIGURE_S464 RED: clinic_papers did not mount on the box's own database")
        return 1
    import clinic_papers as CP
    con = sqlite3.connect(A.DB_PATH)
    con.row_factory = sqlite3.Row
    own = con.execute("SELECT id FROM users WHERE role='owner' AND active=1 ORDER BY id LIMIT 1").fetchone()
    ep = con.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()
    if not own or not ep:
        print("FIGURE_S464 RED: no active owner login in the copy")
        return 1
    c = A.app.test_client()
    with c.session_transaction() as s:
        s["uid"], s["epoch"] = own["id"], ep["value"]
    bad = []
    r = c.get("/papers")
    if r.status_code != 200 or "Clinic papers to sort" not in r.get_data(as_text=True):
        bad.append("/papers %s" % r.status_code)
    for ym in ("", "?ym=2026-09", "?ym=2026-08"):
        r = c.get("/papers/month" + ym)
        if r.status_code != 200:
            bad.append("/papers/month%s %s" % (ym, r.status_code))
        for g_ in ("procedure", "xray", "others", "unsorted"):
            r2 = c.get("/papers/month?g=%s%s" % (g_, ("&" + ym[1:]) if ym else ""))
            if r2.status_code != 200:
                bad.append("month %s %s %s" % (ym, g_, r2.status_code))
    with A.app.test_request_context("/"):
        db = A.get_db()
        live = CP._live(db)
        rows = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND COALESCE(b.subgroup,'')='' ORDER BY b.id DESC").fetchall()
        tally = {}
        for b in rows:
            p = CP._paper(db, b)
            k = ("no suggestion" if not p["s"] else p["s"].get("label") or
                 ("a note, no tap" if p["s"]["kind"] == "note" else "?")) if not p["reading"] else "still being read"
            tally[k] = tally.get(k, 0) + 1
        lanes = dict(db.execute("SELECT COALESCE(lane,'clinic'), COUNT(*) FROM bills WHERE status<>'rejected' GROUP BY 1").fetchall())
    for b in rows[:8]:
        r = c.get("/papers/%d" % b["id"])
        if r.status_code != 200:
            bad.append("/papers/%d %s" % (b["id"], r.status_code))
    for pth in ("/bills", ) + tuple("/bills/%d" % b["id"] for b in rows[:3]):
        r = c.get(pth)
        if r.status_code != 200:
            bad.append("%s %s" % (pth, r.status_code))
    if bad:
        print("FIGURE_S464 RED: " + "; ".join(bad[:6]))
        return 1
    print("FIGURE_S464 OK: on a copy of the box's own database every new page opens. Clinic papers waiting to be "
          "sorted: %d -- %s. Live papers by lane: %s."
          % (len(rows), ", ".join("%s %d" % (k, v) for k, v in sorted(tally.items(), key=lambda x: -x[1])) or "none",
             ", ".join("%s %d" % (k, lanes[k]) for k in sorted(lanes))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
