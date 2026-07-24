#!/usr/bin/env python3
"""Smoke tests — Asset Register v1.0.0. Run: python smoke_test.py"""
import os, sys, io, tempfile, shutil

TMP = tempfile.mkdtemp(prefix="assetapp_test_")
os.environ["ASSETS_DB"] = os.path.join(TMP, "test.db")
os.environ["ASSETS_UPLOADS"] = os.path.join(TMP, "uploads")

import app as A
A.init_db()

passed = failed = 0
def check(name, cond, detail=""):
    global passed, failed
    if cond: passed += 1; print(f"  PASS  {name}")
    else: failed += 1; print(f"  FAIL  {name}  {detail}")

def login(c, user, pw):
    return c.post("/login", data={"username": user, "password": pw}, follow_redirects=False)

owner = A.app.test_client()
mgr   = A.app.test_client()

print("STEP 1: seed & login")
r = login(mgr, "manager", "wrong-password")
check("wrong password rejected", b"Invalid credentials" in r.data or r.status_code == 200)
r = login(mgr, "manager", "change-me-manager")
check("manager login ok", r.status_code == 302)
r = login(owner, "manoj", "change-me-manoj")
check("owner login ok", r.status_code == 302)

print("STEP 2: owner creates asset in owner-only location; manager cannot see it")
r = owner.post("/assets/new", data=dict(
    name="Home Inverter", location_id="5", category="Electrical (Battery/Inverter/Stabilizer)",
    status="Active", contract_type="Warranty only", price="16500",
    warranty_till="2030-01-01", threshold_days="60"), follow_redirects=False)
check("owner create in owner_only loc", r.status_code == 302)
hid = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = mgr.get("/assets")
check("manager list excludes owner-only asset", b"Home Inverter" not in r.data)
check("manager direct URL blocked (403)", mgr.get(f"/assets/{hid}").status_code == 403)
check("owner sees it", b"Home Inverter" in owner.get(f"/assets/{hid}").data)

print("STEP 3: manager creates asset in general location")
r = mgr.post("/assets/new", data=dict(
    name="Fuji DR X-Ray", location_id="2", category="Medical Equipment",
    status="Active", contract_type="AMC", provider="Fuji Service", price="1500000",
    contract_cost="45000", renewal_date="2026-08-15", threshold_days="60"),
    follow_redirects=False)
check("manager create in general loc", r.status_code == 302)
aid = int(r.headers["Location"].rstrip("/").split("/")[-1])
check("owner sees manager-created asset", b"Fuji DR X-Ray" in owner.get(f"/assets/{aid}").data)
r = mgr.post("/assets/new", data=dict(name="Sneaky", location_id="5", category="Other",
                                      status="Active", contract_type="None"))
check("manager cannot create in owner-only loc (403)", r.status_code == 403)

print("STEP 4: hide_price - price invisible to manager, visible to owner")
db = A.sqlite3.connect(os.environ["ASSETS_DB"]); db.execute(
    "UPDATE assets SET hide_price=1 WHERE id=?", (aid,)); db.commit(); db.close()
r = mgr.get(f"/assets/{aid}")
check("manager view lacks price", b"1500000" not in r.data and "₹15".encode() not in r.data)
check("manager view still shows asset", b"Fuji DR X-Ray" in r.data)
check("owner view shows price", "₹1500000".encode() in owner.get(f"/assets/{aid}").data)

print("STEP 5: manager edit of hide_price asset preserves stored price")
r = mgr.post(f"/assets/{aid}/edit", data=dict(
    name="Fuji DR X-Ray System", location_id="2", category="Medical Equipment",
    status="Active", contract_type="AMC", provider="Fuji Service",
    renewal_date="2026-08-15", threshold_days="60"), follow_redirects=False)
check("manager edit accepted", r.status_code == 302)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
row = db.execute("SELECT price, contract_cost, name FROM assets WHERE id=?", (aid,)).fetchone(); db.close()
check("price preserved after manager edit", row[0] == 1500000.0, f"got {row[0]}")
check("contract_cost preserved", row[1] == 45000.0, f"got {row[1]}")
check("name change applied", row[2] == "Fuji DR X-Ray System")

print("STEP 6: sensitive file gating")
r = mgr.post("/files/upload", data={"entity": "asset", "entity_id": str(aid),
    "file": (io.BytesIO(b"%PDF-1.4 fake invoice"), "invoice.pdf")},
    content_type="multipart/form-data", follow_redirects=False)
check("upload on hide_price asset accepted", r.status_code == 302)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
fid, sens = db.execute("SELECT id,sensitive FROM attachments WHERE entity='asset' AND entity_id=?",
                       (aid,)).fetchone(); db.close()
check("file auto-marked sensitive (hide_price asset)", sens == 1)
check("manager download blocked (403)", mgr.get(f"/files/{fid}").status_code == 403)
r = owner.get(f"/files/{fid}")
check("owner download ok", r.status_code == 200 and b"fake invoice" in r.data)

print("STEP 7: dashboard + WhatsApp API")
r = mgr.get("/")
check("manager dashboard shows amber renewal", b"Fuji DR X-Ray" in r.data and b"amber" in r.data)
check("manager dashboard excludes owner-only warranty", b"Home Inverter" not in r.data)
check("owner dashboard shows both due states correctly",
      b"Fuji DR X-Ray" in owner.get("/").data)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
tok = db.execute("SELECT value FROM settings WHERE key='api_token'").fetchone()[0]; db.close()
anon = A.app.test_client()
check("API wrong token 403", anon.get("/api/due?token=nope").status_code == 403)
r = anon.get(f"/api/due?token={tok}")
j = r.get_json()
check("API returns due item", r.status_code == 200 and any(x["item"].startswith("Fuji") for x in j), str(j))

print("STEP 8: deletion rights, staff module, epoch")
check("manager delete blocked (403)", mgr.post(f"/assets/{hid}/delete").status_code == 403)
r = mgr.post("/staff/new", data=dict(name="Test Peon", role_title="Housekeeping",
    status="Active", doc_label="Contract renewal", doc_due="2026-08-01",
    threshold_days="60"), follow_redirects=False)
check("manager can create staff record", r.status_code == 302)
sid = int(r.headers["Location"].rstrip("/").split("/")[-1])
check("staff expiry on manager dashboard", b"Test Peon" in mgr.get("/").data)
r = owner.post(f"/assets/{hid}/delete", follow_redirects=False)
check("owner delete works", r.status_code == 302)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
check("asset + expiries fully removed",
      db.execute("SELECT COUNT(*) FROM assets WHERE id=?", (hid,)).fetchone()[0] == 0 and
      db.execute("SELECT COUNT(*) FROM expiries WHERE entity='asset' AND entity_id=?", (hid,)).fetchone()[0] == 0)
db.close()
r = owner.post("/account", data={"action": "epoch"}, follow_redirects=False)
check("epoch bump redirects to login", r.status_code == 302)
check("manager session invalidated", mgr.get("/assets").status_code == 302)
check("owner session invalidated", owner.get("/assets").status_code == 302)

print("STEP 9: built-in scanner")
# re-login (epoch was bumped in step 8)
login(owner, "manoj", "change-me-manoj")
login(mgr, "manager", "change-me-manager")
r = owner.get(f"/scan/asset/{aid}")
check("scan page renders for asset", r.status_code == 200 and b"Drag the four corners" in r.data)
check("pages render as real HTML, not escaped text", b'<div class=card' in r.data and b"&lt;div" not in r.data)
check("scan page carries jsPDF + warp code", b"jspdf" in r.data and b"Heckbert" in r.data)
r = mgr.get(f"/scan/staff/{sid}")
check("scan page renders for staff (manager)", r.status_code == 200)
check("scan on unknown entity 404", owner.get("/scan/vehicle/1").status_code == 404)
# hide_price asset: scan page should default sensitive flag
r = owner.get(f"/scan/asset/{aid}")
check("hide_price asset scan defaults sensitive", b"append('sensitive','1')" in r.data)
r = mgr.post("/files/upload", data={"entity": "asset", "entity_id": str(aid),
    "file": (io.BytesIO(b"%PDF-1.4 scanpdf"), "scan_2026-07-24.pdf")},
    content_type="multipart/form-data")
check("scanner-style pdf upload accepted", r.status_code == 302)

print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if failed else 0)
