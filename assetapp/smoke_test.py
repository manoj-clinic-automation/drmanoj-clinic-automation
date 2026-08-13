#!/usr/bin/env python3
"""Smoke tests — Asset Register v1.4.2 (grouped Entity->Zone index). Run: python smoke_test.py"""
import os, sys, io, tempfile, shutil

TMP = tempfile.mkdtemp(prefix="assetapp_test_")
os.environ["ASSETS_DB"] = os.path.join(TMP, "test.db")
os.environ["ASSETS_UPLOADS"] = os.path.join(TMP, "uploads")

import asset_register as A
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

print("STEP 9: scanner shell renders + carries config (not the old inline JS)")
login(owner, "manoj", "change-me-manoj")
login(mgr, "manager", "change-me-manager")
r = owner.get(f"/scan/asset/{aid}")
check("scan page renders for asset", r.status_code == 200)
check("mounts the widget div", b"id=scanroot" in r.data)
check("loads the shared widget script (cache-busted)", b"/scan/widget.js?v=" in r.data)
check("carries jsPDF cdn", b"jspdf" in r.data)
check("injects SCANNER_CONFIG", b"SCANNER_CONFIG" in r.data)
check("config points at the upload route", b"/files/upload" in r.data and b"uploadUrl" in r.data)
check("config carries a nameBase default", b"nameBase" in r.data)
check("shell HTML is real, not escaped", b"<div id=scanroot>" in r.data and b"&lt;div" not in r.data)
check("hide_price asset -> config marks sensitive", b'"sensitive"' in r.data)
r = mgr.get(f"/scan/staff/{sid}")
check("scan page renders for staff (manager)", r.status_code == 200)
check("non-sensitive staff scan has no sensitive flag", b'"sensitive"' not in r.data)
check("scan on unknown entity 404", owner.get("/scan/vehicle/1").status_code == 404)
r = owner.get("/scan/draft/0")
check("draft scan renders", r.status_code == 200 and b"scanroot" in r.data)

print("STEP 10: shared widget served from disk + still accepts uploads")
r = anon.get("/scan/widget.js")
check("widget.js served (public, 200)", r.status_code == 200)
check("widget.js content-type is javascript", "javascript" in r.headers.get("Content-Type", ""))
check("widget.js keeps warp + live-camera logic", b"Heckbert" in r.data and b"getUserMedia" in r.data)
check("widget.js has the 1A features", b"composeIdCard" in r.data and b"Add whole image" in r.data
      and b"batch" in r.data.lower())
r = mgr.post("/files/upload", data={"entity": "asset", "entity_id": str(aid),
    "file": (io.BytesIO(b"%PDF-1.4 scanpdf"), "Fuji_2026-08-13.pdf")},
    content_type="multipart/form-data")
check("scanner-style pdf upload still accepted", r.status_code == 302)

print("STEP 11: Phase A taxonomy backbone + backfill (dry-run / apply / idempotent)")
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
ents = [r[0] for r in db.execute("SELECT name FROM entities ORDER BY sort")]
check("3 entities seeded", ents == ["Dr Manoj Clinic", "NK Pathology", "Personal"], str(ents))
check("zones seeded (>=20)", db.execute("SELECT COUNT(*) FROM zones").fetchone()[0] >= 20)
acols = {r[1] for r in db.execute("PRAGMA table_info(assets)")}
check("assets gained entity_id + zone_id", "entity_id" in acols and "zone_id" in acols)
db.close()
A.migrate_taxonomy(apply=False)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
check("dry-run leaves rows unclassified", db.execute("SELECT COUNT(*) FROM assets WHERE entity_id IS NULL").fetchone()[0] > 0)
db.close()
A.migrate_taxonomy(apply=True)
db = A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory = A.sqlite3.Row
check("apply classifies every asset", db.execute("SELECT COUNT(*) FROM assets WHERE entity_id IS NULL").fetchone()[0] == 0)
row = db.execute("SELECT en.name e FROM assets a JOIN entities en ON en.id=a.entity_id WHERE a.id=?", (aid,)).fetchone()
check("Clinic asset -> Dr Manoj Clinic", row and row["e"] == "Dr Manoj Clinic", str(row and row["e"]))
db.close()
n, unmapped = A.migrate_taxonomy(apply=True)
check("re-apply is a no-op (idempotent)", n == 0 and not unmapped)
r = owner.get("/assets")
check("asset index groups under entity headers", b"Dr Manoj Clinic" in r.data and b"<details" in r.data)
check("asset index shows a zone group", b"Unassigned" in r.data)

print("STEP 12: admin — password set-and-reveal, generate, token masked + rotate")
r = owner.post("/admin", data={"action":"reset_pw","uid":"3","new":"temppass123"}, follow_redirects=True)
check("typed password revealed once", b"temppass123" in r.data and b"shown once" in r.data)
r = owner.post("/admin", data={"action":"reset_pw","uid":"3","gen":"1"}, follow_redirects=True)
check("generated password revealed", b"is now:" in r.data)
r = owner.get("/admin")
check("token not printed bare (masked in <details>)", b"<details>" in r.data and b"Show API token" in r.data)
check("rotate-token control present", b"rotate_token" in r.data)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
tok_before = db.execute("SELECT value FROM settings WHERE key='api_token'").fetchone()[0]; db.close()
owner.post("/admin", data={"action":"rotate_token"}, follow_redirects=True)
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
tok_after = db.execute("SELECT value FROM settings WHERE key='api_token'").fetchone()[0]; db.close()
check("rotate actually changes the token", tok_before != tok_after)
r = mgr.get("/admin")
check("manager still blocked from admin (403/redirect)", r.status_code in (302,403))

print("STEP 13: Phase C grouped index (entity->zone, scope, search)")
r = owner.get("/assets")
check("grouped: entity summary present", b"<summary" in r.data and b"Dr Manoj Clinic" in r.data)
check("grouped: zone nested under entity", b"Unassigned" in r.data)
check("grouped: the asset appears in its group", b"Fuji DR X-Ray" in r.data)
r2 = mgr.get("/assets")
check("manager sees the general (Clinic) group", r2.status_code == 200 and b"Dr Manoj Clinic" in r2.data)
check("manager does NOT see Personal (owner-only) group", b"Personal" not in r2.data)
r3 = owner.get("/assets?q=Fuji")
check("search still works inside grouping", b"Fuji DR X-Ray" in r3.data and b"clear" in r3.data)
r4 = owner.get("/assets?q=zzznomatchzzz")
check("empty search shows the no-match line", b"No assets" in r4.data)

print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if failed else 0)
