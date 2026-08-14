#!/usr/bin/env python3
"""inspect_assets.py -- READ-ONLY look at the tail of the assets table + the
dependents of rows 45..60, so the stray owner test rows can be identified by
eye before any delete. Prints only; changes nothing.

Run on the VPS:  cd /root/assetapp && python3 inspect_assets.py
"""
import sqlite3

db = sqlite3.connect("file:assets.db?mode=ro", uri=True)   # read-only handle
db.row_factory = sqlite3.Row

print("total assets:", db.execute("SELECT COUNT(*) FROM assets").fetchone()[0])

print("\n-- last 15 rows --")
q = ("SELECT a.id, a.name, l.name loc, a.status, a.created_at, "
     "u.username creator, a.bill_id "
     "FROM assets a "
     "JOIN locations l ON l.id = a.location_id "
     "LEFT JOIN users u ON u.id = a.created_by "
     "ORDER BY a.id DESC LIMIT 15")
for r in db.execute(q):
    print(" #%-3d %-30s loc=%-16s %-9s %s by=%-8s bill=%s" % (
        r["id"], (r["name"] or "")[:30], (r["loc"] or "")[:16],
        r["status"], (r["created_at"] or "")[:16],
        str(r["creator"]), r["bill_id"]))

print("\n-- dependents, ids 45..60 --")
for aid in range(45, 61):
    if not db.execute("SELECT 1 FROM assets WHERE id=?", (aid,)).fetchone():
        continue
    def c(sql, p):
        return db.execute(sql, p).fetchone()[0]
    exp = c("SELECT COUNT(*) FROM expiries WHERE entity='asset' AND entity_id=?", (aid,))
    att = c("SELECT COUNT(*) FROM attachments WHERE entity='asset' AND entity_id=?", (aid,))
    svc = c("SELECT COUNT(*) FROM service_logs WHERE asset_id=?", (aid,))
    bil = c("SELECT COUNT(*) FROM bill_items WHERE asset_id=?", (aid,))
    print(" #%-3d expiries=%d attach=%d service=%d bill_links=%d" % (
        aid, exp, att, svc, bil))

print("\n(read-only -- nothing was changed)")
