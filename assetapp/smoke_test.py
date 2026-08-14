#!/usr/bin/env python3
"""Smoke tests — Asset Register v1.4.2 (grouped Entity->Zone index). Run: python smoke_test.py"""
import os, sys, io, tempfile, shutil

TMP = tempfile.mkdtemp(prefix="assetapp_test_")
os.environ["ASSETS_DB"] = os.path.join(TMP, "test.db")
os.environ["ASSETS_UPLOADS"] = os.path.join(TMP, "uploads")

# A-D21: arm the REAL SSO shim with a stub portal (set BEFORE the app import).
# The stub verify_token speaks "user|role|epoch" tokens so tests can mint any
# role; the app-side mapping code under test is the genuine article.
PORTAL = os.path.join(TMP, "portal")
os.makedirs(PORTAL, exist_ok=True)
open(os.path.join(PORTAL, "clinic_sso.py"), "w").write(
    'COOKIE_NAME = "clinic_sso"\n'
    'def verify_token(tok, secret, current_epoch=None):\n'
    '    if secret != "test-secret":\n'
    '        return None\n'
    '    try:\n'
    '        u, r, e = tok.split("|")\n'
    '    except Exception:\n'
    '        return None\n'
    '    if current_epoch is not None and int(e) != int(current_epoch):\n'
    '        return None\n'
    '    return {"user": u, "role": r}\n')
open(os.path.join(PORTAL, "portal_config.py"), "w").write('CLINIC_SSO_SECRET = "test-secret"\n')
open(os.path.join(PORTAL, "clinic_users.json"), "w").write('{"epoch": 1}\n')
os.environ["CLINIC_PORTAL_DIR"] = PORTAL

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
check("asset index groups under location headers", b"Clinic" in r.data and b"<details" in r.data)
check("asset list shows the Supplier column", b"Supplier" in r.data)

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

print("STEP 13: grouped index (by location, scope, search)")
r = owner.get("/assets")
check("grouped: location summary present", b"<summary" in r.data and b"Clinic" in r.data)
check("list shows the Purchased column", b"Purchased" in r.data)
check("grouped: the asset appears in its group", b"Fuji DR X-Ray" in r.data)
r2 = mgr.get("/assets")
check("manager sees the general (Clinic) group", r2.status_code == 200 and b"Clinic" in r2.data)
check("manager does NOT see Personal (owner-only) location", b"Personal" not in r2.data)
r3 = owner.get("/assets?q=Fuji")
check("search still works inside grouping", b"Fuji DR X-Ray" in r3.data and b"clear" in r3.data)
r4 = owner.get("/assets?q=zzznomatchzzz")
check("empty search shows the no-match line", b"No assets" in r4.data)

print("STEP 14: Wave A - cascading form, contract/period, payment, managed lists, qty")
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
acols = {r[1] for r in db.execute("PRAGMA table_info(assets)")}
for col in ("kind","coverage_start","contract_period","payment_method","pay_account",
            "emi","emi_count","emi_amount","emi_start","emi_end"):
    check(f"assets gained {col}", col in acols)
nb = db.execute("SELECT COUNT(*) FROM pick_lists WHERE kind='bank'").fetchone()[0]
nc = db.execute("SELECT COUNT(*) FROM pick_lists WHERE kind='card'").fetchone()[0]
check("bank/card pick-lists seeded", nb >= 3 and nc >= 2, f"bank={nb} card={nc}")
eid_clinic = db.execute("SELECT id FROM entities WHERE name='Dr Manoj Clinic'").fetchone()[0]
zid_clinic = db.execute("SELECT z.id FROM zones z JOIN entities e ON e.id=z.entity_id WHERE e.name='Dr Manoj Clinic' AND z.name='Reception'").fetchone()[0]
loc_clinic = db.execute("SELECT id FROM locations WHERE name='Clinic'").fetchone()[0]
db.close()
r = owner.get("/assets/new")
check("form has entity/zone/kind cascade", b"name=entity_id" in r.data and b"name=zone_id" in r.data and b"name=kind" in r.data)
check("form has period + payment", b"name=contract_period" in r.data and b"name=payment_method" in r.data)
check("form has month/year + make_copies", b"name=purchase_month" in r.data and b"name=make_copies" in r.data)
r = owner.post("/assets/new", data=dict(
    name="Autoclave WaveA", kind="Asset", entity_id=str(eid_clinic), zone_id=str(zid_clinic),
    category="Medical Equipment", purchase_month="06", purchase_year="2025",
    contract_type="AMC", contract_period="2yr", provider="Fuji Service",
    payment_method="Bank transfer", pay_account="HDFC-test", vendor="Acme Test Vendor",
    price="80000", threshold_days="60"), follow_redirects=False)
check("entity-path create ok", r.status_code == 302)
nid = int(r.headers["Location"].rstrip("/").split("/")[-1])
db = A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory = A.sqlite3.Row
row = db.execute("SELECT * FROM assets WHERE id=?", (nid,)).fetchone()
check("entity_id + zone_id stored", row["entity_id"] == eid_clinic and row["zone_id"] == zid_clinic)
check("location_id derived from entity (Clinic)", row["location_id"] == loc_clinic, str(row["location_id"]))
check("contract_period stored", row["contract_period"] == "2yr")
check("payment stored", row["payment_method"] == "Bank transfer" and row["pay_account"] == "HDFC-test")
ren = db.execute("SELECT due_date FROM expiries WHERE entity='asset' AND entity_id=? AND label='Contract renewal'", (nid,)).fetchone()
check("period computed renewal = purchase+24m (2027-06-01)", ren and ren["due_date"] == "2027-06-01", str(ren and ren["due_date"]))
check("vendor auto-added to managed list", db.execute("SELECT COUNT(*) FROM pick_lists WHERE kind='vendor' AND value='Acme Test Vendor'").fetchone()[0] == 1)
check("bank account auto-added to managed list", db.execute("SELECT COUNT(*) FROM pick_lists WHERE kind='bank' AND value='HDFC-test'").fetchone()[0] == 1)
before = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
db.close()
r = owner.post("/assets/new", data=dict(
    name="Bulk Chair", kind="Asset", entity_id=str(eid_clinic), zone_id=str(zid_clinic),
    category="Furniture", contract_type="None", contract_period="none",
    make_copies="3", threshold_days="60"), follow_redirects=False)
check("bulk create redirects to list", r.status_code == 302 and r.headers["Location"].rstrip("/").endswith("/assets"))
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
after = db.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
check("make_copies=3 created 3 rows", after - before == 3, f"delta={after-before}")
db.close()
r = owner.post("/admin", data={"action":"add_pick","pl_kind":"vendor","value":"Admin Vendor"}, follow_redirects=True)
check("admin add_pick renders new value", b"Admin Vendor" in r.data)
r = mgr.get("/assets/new")
check("manager NEW form shows price+payment (may cost new assets)", b"name=price" in r.data and b"name=payment_method" in r.data)
check("manager form still has entity cascade", b"name=entity_id" in r.data)
r = mgr.get(f"/assets/{aid}/edit")
check("manager edit of hide_price hides price+payment blocks", b"Purchase price" not in r.data and b"Payment (record only)" not in r.data)

print("STEP 15: Wave A.1 - PM count + PM logging with scanned report, EMI defaults")
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
acols = {r[1] for r in db.execute("PRAGMA table_info(assets)")}
scols = {r[1] for r in db.execute("PRAGMA table_info(service_logs)")}
check("assets gained pm_count", "pm_count" in acols)
check("service_logs gained is_pm", "is_pm" in scols)
eid_c = db.execute("SELECT id FROM entities WHERE name='Dr Manoj Clinic'").fetchone()[0]
zid_c = db.execute("SELECT z.id FROM zones z JOIN entities e ON e.id=z.entity_id WHERE e.name='Dr Manoj Clinic' AND z.name='Reception'").fetchone()[0]
db.close()
r = owner.get("/assets/new")
check("form has pm_count + contextual JS", b"name=pm_count" in r.data and b"ctypeChange" in r.data and b"emiRecalc" in r.data)
check("form has vendor picker + add box", b"or type a new vendor" in r.data)
r = owner.post("/assets/new", data=dict(
    name="CT Scanner AMC", kind="Asset", entity_id=str(eid_c), zone_id=str(zid_c),
    category="Medical Equipment", purchase_month="06", purchase_year="2025",
    contract_type="AMC", contract_period="1yr", provider="GE Service", contract_cost="120000",
    pm_count="4", price="600000",
    payment_method="Bank transfer", pay_account="ICICI", emi="on", emi_count="12",
    threshold_days="60"), follow_redirects=False)
check("AMC+PM+EMI create ok", r.status_code == 302)
pid = int(r.headers["Location"].rstrip("/").split("/")[-1])
db = A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory = A.sqlite3.Row
row = db.execute("SELECT * FROM assets WHERE id=?", (pid,)).fetchone()
check("pm_count stored (4)", row["pm_count"] == 4, str(row["pm_count"]))
check("EMI start defaulted to purchase (2025-06-01)", row["emi_start"] == "2025-06-01", str(row["emi_start"]))
db.close()
r = owner.post(f"/assets/{pid}/service", data={
    "log_date":"2026-08-13","work":"1st preventive maintenance","is_pm":"1","done_by":"GE Engineer",
    "report":(io.BytesIO(b"%PDF-1.4 pm-report"), "pm1.pdf")},
    content_type="multipart/form-data", follow_redirects=False)
check("PM service_add ok", r.status_code == 302)
db = A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory = A.sqlite3.Row
check("PM logged (is_pm=1)", db.execute("SELECT COUNT(*) c FROM service_logs WHERE asset_id=? AND is_pm=1",(pid,)).fetchone()["c"] == 1)
check("PM report attached to asset", db.execute("SELECT COUNT(*) c FROM attachments WHERE entity='asset' AND entity_id=?",(pid,)).fetchone()["c"] == 1)
db.close()
r = owner.get(f"/assets/{pid}")
check("asset view shows PM tracker (1 of 4 done)", b"1 of 4 done" in r.data)
check("asset view shows PM badge on log row", b">PM<" in r.data)

print("STEP 16: contextual service log - PM free / repair cost / part-own-warranty")
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
scols = {r[1] for r in db.execute("PRAGMA table_info(service_logs)")}
for col in ("svc_type","part_replaced","part_warranty"):
    check(f"service_logs gained {col}", col in scols)
db.close()
# PM entry: cost is ignored even if posted (covered under AMC), counts as PM
r = owner.post(f"/assets/{pid}/service", data={"log_date":"2026-09-01","work":"2nd PM","svc_type":"Preventive maintenance","cost":"9999"}, follow_redirects=False)
check("PM service_add ok", r.status_code==302)
db=A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory=A.sqlite3.Row
row=db.execute("SELECT * FROM service_logs WHERE asset_id=? AND log_date='2026-09-01'",(pid,)).fetchone()
check("PM forces no cost (AMC-covered)", row["cost"] is None, str(row["cost"]))
check("PM is_pm=1 via svc_type", row["is_pm"]==1)
db.close()
# Repair with a replaced part carrying a 1-year warranty
r = owner.post(f"/assets/{pid}/service", data={"log_date":"2026-10-01","work":"tube failure","svc_type":"Repair","cost":"25000","part_replaced":"X-ray tube","part_warranty_period":"1yr"}, follow_redirects=False)
check("repair service_add ok", r.status_code==302)
db=A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory=A.sqlite3.Row
row=db.execute("SELECT * FROM service_logs WHERE asset_id=? AND log_date='2026-10-01'",(pid,)).fetchone()
check("repair keeps cost", row["cost"]==25000.0, str(row["cost"]))
check("repair not counted as PM", row["is_pm"]==0)
check("replaced part recorded", row["part_replaced"]=="X-ray tube")
check("part warranty computed (2027-10-01)", row["part_warranty"]=="2027-10-01", str(row["part_warranty"]))
pw=db.execute("SELECT due_date FROM expiries WHERE entity='asset' AND entity_id=? AND label='Part warranty: X-ray tube'",(pid,)).fetchone()
check("part warranty reminder created", pw and pw["due_date"]=="2027-10-01", str(pw and pw["due_date"]))
db.close()
r=owner.get(f"/assets/{pid}")
check("service log shows Repair badge", b">Repair<" in r.data)
check("service log shows replaced-part line", b"X-ray tube" in r.data)
check("PM tracker now 2 of 4 done", b"2 of 4 done" in r.data)
check("form defaults to contextual svc type", b"id=svctype" in r.data and b"svcTypeChange" in r.data)

print("STEP 17: Wave B - due badges on grouped index + per-entity renewals view")
soon = (A.today() + A.datetime.timedelta(days=10)).isoformat()
r = owner.post("/assets/new", data=dict(name="SoonRenew", kind="Asset", entity_id=str(eid_c), zone_id=str(zid_c),
    category="Other", contract_type="AMC", contract_period="custom", renewal_date=soon, threshold_days="60"),
    follow_redirects=False)
check("soon-renew asset created", r.status_code==302)
r = owner.get("/assets")
check("grouped index shows a due badge", b"due</span>" in r.data)
check("nav has Renewals link", b"/renewals" in r.data)
r = owner.get("/renewals")
check("renewals route 200", r.status_code==200)
check("renewals groups by entity", b"Dr Manoj Clinic" in r.data)
check("renewals(due-soon) shows the soon asset", b"SoonRenew" in r.data)
r = owner.get("/renewals?all=1")
check("renewals(all) 200 + shows a far-future item", r.status_code==200 and b"CT Scanner AMC" in r.data)
r = mgr.get("/renewals")
check("manager renewals 200 (visibility-gated)", r.status_code==200)
check("manager renewals excludes Personal entity", b"Personal" not in r.data)

print("STEP 18: Wave A.3 - payment(cheque/UPI/unpaid), parts card, report link, contextual label, redesign")
db = A.sqlite3.connect(os.environ["ASSETS_DB"])
acols = {r[1] for r in db.execute("PRAGMA table_info(assets)")}
scols = {r[1] for r in db.execute("PRAGMA table_info(service_logs)")}
for col in ("pay_ref","pay_date"):
    check(f"assets gained {col}", col in acols)
check("service_logs gained report_att_id", "report_att_id" in scols)
db.close()
# --- Cheque: number + date captured and shown, bank auto-added ---
r = owner.post("/assets/new", data=dict(name="Cheque Buy", kind="Asset",
    entity_id=str(eid_c), zone_id=str(zid_c), category="Other",
    contract_type="None", contract_period="none",
    payment_method="Cheque", pay_account="SBI", cheque_no="000123", pay_date="2026-05-05",
    price="5000", threshold_days="60"), follow_redirects=False)
check("cheque asset create ok", r.status_code==302)
cqid = int(r.headers["Location"].rstrip("/").split("/")[-1])
db=A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory=A.sqlite3.Row
row=db.execute("SELECT * FROM assets WHERE id=?",(cqid,)).fetchone()
check("cheque method stored", row["payment_method"]=="Cheque")
check("cheque number -> pay_ref", row["pay_ref"]=="000123", str(row["pay_ref"]))
check("cheque date -> pay_date", row["pay_date"]=="2026-05-05", str(row["pay_date"]))
check("cheque bank auto-added to managed list", db.execute("SELECT COUNT(*) FROM pick_lists WHERE kind='bank' AND value='SBI'").fetchone()[0]==1)
db.close()
r=owner.get(f"/assets/{cqid}")
check("asset view shows cheque no.", b"no. 000123" in r.data)
# --- UPI: ref captured + shown ---
r = owner.post("/assets/new", data=dict(name="UPI Buy", kind="Asset",
    entity_id=str(eid_c), zone_id=str(zid_c), category="Other",
    contract_type="None", contract_period="none",
    payment_method="UPI", upi_ref="UPI-9988", price="2000", threshold_days="60"), follow_redirects=False)
upid = int(r.headers["Location"].rstrip("/").split("/")[-1])
db=A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory=A.sqlite3.Row
check("upi ref -> pay_ref", db.execute("SELECT pay_ref FROM assets WHERE id=?",(upid,)).fetchone()["pay_ref"]=="UPI-9988")
db.close()
r=owner.get(f"/assets/{upid}")
check("asset view shows UPI ref", b"ref UPI-9988" in r.data)
# --- Unpaid: saves as a first-class method ---
r = owner.post("/assets/new", data=dict(name="Unpaid Buy", kind="Asset",
    entity_id=str(eid_c), zone_id=str(zid_c), category="Other",
    contract_type="None", contract_period="none",
    payment_method="Unpaid", price="3000", threshold_days="60"), follow_redirects=False)
unid = int(r.headers["Location"].rstrip("/").split("/")[-1])
db=A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory=A.sqlite3.Row
check("Unpaid method saved", db.execute("SELECT payment_method FROM assets WHERE id=?",(unid,)).fetchone()["payment_method"]=="Unpaid")
db.close()
r=owner.get(f"/assets/{unid}")
check("asset view shows Unpaid", b"Paid via:</b> Unpaid" in r.data)
# --- Parts-replaced card on CT Scanner (X-ray tube from STEP 16) ---
r=owner.get(f"/assets/{pid}")
check("asset view shows Parts replaced card", b"Parts replaced" in r.data)
check("parts card lists X-ray tube", b"X-ray tube" in r.data)
# --- Service with part + report -> report linked on the log + shown in parts card ---
r = owner.post(f"/assets/{pid}/service", data={"log_date":"2026-11-01","work":"board swap",
    "svc_type":"Repair","cost":"5000","part_replaced":"PCB","part_warranty_period":"1yr",
    "report":(io.BytesIO(b"%PDF-1.4 svc-report"), "svc.pdf")},
    content_type="multipart/form-data", follow_redirects=False)
check("repair+report service_add ok", r.status_code==302)
db=A.sqlite3.connect(os.environ["ASSETS_DB"]); db.row_factory=A.sqlite3.Row
row=db.execute("SELECT * FROM service_logs WHERE asset_id=? AND log_date='2026-11-01'",(pid,)).fetchone()
check("service log linked to report attachment", row["report_att_id"] is not None, str(row["report_att_id"]))
db.close()
r=owner.get(f"/assets/{pid}")
check("service log row shows report link", b"report</a>" in r.data)
check("parts card now lists PCB", b"PCB" in r.data)
check("service form has contextual work label", b"id=worklabel" in r.data and b"id=workinput" in r.data)
# --- soothing redesign markers (class names preserved; new green badge class) ---
check("redesign: green badge class defined", b".badge.green" in r.data)
check("redesign: soft background applied", b"#eaeef3" in r.data)

# --- A.4a: back-nav + cost-confirm hook + saved flash ---
r=owner.get(f"/assets/{pid}")
check("A.4a asset_view has back-nav to Assets", "← Assets".encode() in r.data)
check("A.4a service form has cost-confirm hook", b"svcConfirm()" in r.data and b"id=svccost" in r.data)
r = owner.post(f"/assets/{pid}/service", data={"log_date":"2026-11-02","work":"cleaned",
    "svc_type":"Other service"}, content_type="multipart/form-data", follow_redirects=True)
check("A.4a service_add shows saved flash", b"Service entry saved." in r.data)
r=mgr.get(f"/staff/{sid}")
check("A.4a staff_view has back-nav to Staff", "← Staff".encode() in r.data)

# --- palette: live-selectable low-glare background ---
r=owner.get("/admin")
check("palette picker present in Admin", b"Screen background" in r.data and b"#f1ece3" in r.data)
r=owner.post("/admin", data={"action":"set_palette","palette":"sand"}, follow_redirects=True)
check("palette 'sand' applies", b"background:#f1ece3" in r.data)
r=owner.post("/admin", data={"action":"set_palette","palette":"zzz"}, follow_redirects=True)
check("bad palette value ignored (last valid stays)", b"background:#f1ece3" in r.data)
r=owner.post("/admin", data={"action":"set_palette","palette":"cool"}, follow_redirects=True)
check("palette reset to cool default", b"background:#eaeef3" in r.data)

# --- A.4b: image thumbnails on Files (price-gated; pdf excluded) ---
png = b"\x89PNG\r\n\x1a\n" + b"\x00"*16
r = owner.post("/assets/new", data=dict(name="Thumb Test Asset", kind="Asset",
    entity_id=str(eid_c), zone_id=str(zid_c), category="Other",
    contract_type="None", contract_period="none", price="100", threshold_days="60"),
    follow_redirects=False)
tid = int(r.headers["Location"].rstrip("/").split("/")[-1])
owner.post("/files/upload", data={"entity":"asset","entity_id":str(tid),
    "file":(io.BytesIO(png),"photo.png")}, content_type="multipart/form-data")
owner.post("/files/upload", data={"entity":"asset","entity_id":str(tid),
    "file":(io.BytesIO(b"%PDF-1.4 x"),"manual.pdf")}, content_type="multipart/form-data")
r = owner.get(f"/assets/{tid}")
check("A.4b png renders a thumbnail", b'<img src="/files/' in r.data)
check("A.4b exactly one thumbnail (pdf excluded)", r.data.count(b'<img src="/files/')==1)
check("A.4b pdf link present, no thumbnail for it", b"manual.pdf" in r.data)

# --- A.4c: cascading faceted search ---
r=owner.get("/assets")
check("A.4c facet dropdowns present", b"Entity: all" in r.data and b"Zone: all" in r.data
      and b"Category: all" in r.data and b"Kind: all" in r.data and b"Status: all" in r.data)
r=owner.post("/assets/new", data=dict(name="Facet Widget", kind="Asset",
    entity_id=str(eid_c), zone_id=str(zid_c), category="Vehicle",
    contract_type="None", contract_period="none", price="10", threshold_days="60"),
    follow_redirects=False)
check("A.4c test asset created", r.status_code==302)
r=owner.get("/assets")
check("A.4c category appears as a facet option", b"Vehicle" in r.data)
r=owner.get("/assets?f_cat=Vehicle")
check("A.4c category facet isolates the match", b"Facet Widget" in r.data)
r=owner.get("/assets?f_cat=Furniture")
check("A.4c category facet excludes non-matches", b"Facet Widget" not in r.data)
r=owner.get(f"/assets?f_ent={eid_c}")
check("A.4c entity facet returns its assets", b"Facet Widget" in r.data)
r=owner.get("/assets?f_cat=__nope__")
check("A.4c invalid facet is harmless", r.status_code==200 and b"Facet Widget" not in r.data)

# --- Phase D: purchase ledger (bills + bill_items) ---
near = (A.datetime.date.today()+A.datetime.timedelta(days=10)).isoformat()
r = owner.post("/bills/new", data={
    "kind":"Consumable","vendor":"Aastha Medical","bill_no":"D-811",
    "bill_date":"2026-07-06","total_amount":"3969",
    "it_name":["VIDAS TSH","Dell A27 Monitor",""],
    "it_pack":["30 tests","",""],"it_qty":["2","1",""],
    "it_rate":["3780","49405",""],"it_amount":["7560","49405",""],
    "it_batch":["1011672290","",""],"it_expiry":[near,"",""],
    "it_hsn":["382219","85285200",""],
    "it_make":["","Dell",""],"it_model":["","A27",""],"it_serial":["","CD7H484",""]},
    follow_redirects=True)
check("D bill saved with 2 items (blank ignored)", b"Bill saved with 2 line item" in r.data)
check("D bills list shows vendor", b"Aastha Medical" in owner.get("/bills").data)
_db=A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory=A.sqlite3.Row
bid=_db.execute("SELECT id FROM bills WHERE bill_no='D-811'").fetchone()["id"]
nitems=_db.execute("SELECT COUNT(*) c FROM bill_items WHERE bill_id=?", (bid,)).fetchone()["c"]
_db.close()
check("D exactly two line items stored", nitems==2)
r=owner.get(f"/bills/{bid}")
check("D bill detail shows serial + batch", b"CD7H484" in r.data and b"1011672290" in r.data)
r=owner.get("/purchases")
check("D purchases lists both items", b"VIDAS TSH" in r.data and b"Dell A27 Monitor" in r.data)
check("D expiring-soon surfaces near expiry", b"Expiring soon" in r.data and b"1011672290" in r.data)
r=owner.get("/purchases?item=VIDAS TSH")
check("D rate history renders", b"Rate history" in r.data and b"3780" in r.data)
check("D consumption qty shown", b"total quantity" in r.data)
check("D bills open to checker (manager 200; A-D21)", mgr.get("/bills").status_code==200)
check("D purchases owner-only (manager 403)", mgr.get("/purchases").status_code==403)
r=owner.post(f"/bills/{bid}/delete", follow_redirects=True)
check("D bill delete works", b"Bill deleted." in r.data)
_db=A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory=A.sqlite3.Row
gone=_db.execute("SELECT COUNT(*) c FROM bill_items WHERE bill_id=?", (bid,)).fetchone()["c"]
_db.close()
check("D bill items removed on delete", gone==0)

# --- Phase E: Sarvam extract -> pre-filled bill (shared module A-D16) ---
import types as _types, re as _re
check("E sarvam_ocr module importable", A.SARVAM is not None)
check("E not available without key", A.SARVAM.available() is False)
_d,_s = A.SARVAM.extract("/nope.pdf")
check("E extract skips with no key", _s=="skipped" and _d is None)
r=owner.get("/bills/new")
check("E bill form has auto-fill uploader", b"Auto-fill from a scanned bill" in r.data and b"/bills/extract" in r.data)
r=owner.post("/bills/extract", data={"bill":(io.BytesIO(b"%PDF-1.4 x"),"scan1.pdf")},
    content_type="multipart/form-data", follow_redirects=True)
check("E extract graceful-skip + scan attached", b"isn't configured" in r.data and b'name=src_stored value="bill_' in r.data)
_real=A.SARVAM
A.SARVAM=_types.SimpleNamespace(available=lambda: True,
    extract=lambda path,**k: ({"vendor":"Aastha Medical Cares","bill_no":"811",
        "bill_date":"2026-07-06","total_amount":3969,
        "items":[{"item_name":"VIDAS TSH-30400","pack_size":"30 tests","quantity":1,
                  "rate":3780,"batch":"1011672290","expiry":"2026-11-12","hsn":"382219"}]}, "done"))
r=owner.post("/bills/extract", data={"bill":(io.BytesIO(b"%PDF-1.4 y"),"scan2.pdf")},
    content_type="multipart/form-data", follow_redirects=True)
check("E autofill maps header", b"Auto-filled from the scan" in r.data and b'value="Aastha Medical Cares"' in r.data)
check("E autofill maps line item", b'value="VIDAS TSH-30400"' in r.data and b'value="1011672290"' in r.data)
_h,_it = A._map_bill([{"result":{"vendor":"V","items":[{"name":"X","rate":5}]}}])
check("E _map_bill tolerant (list+wrap)", _h["vendor"]=="V" and bool(_it) and _it[0]["name"]=="X")
A.SARVAM=_real
r=owner.post("/bills/extract", data={"bill":(io.BytesIO(b"%PDF-1.4 z"),"scan3.pdf")},
    content_type="multipart/form-data", follow_redirects=True)
_ss=_re.search(rb'name=src_stored value="([^"]+)"', r.data).group(1).decode()
r=owner.post("/bills/new", data={"kind":"Consumable","vendor":"SrcVendor","bill_no":"SRC1",
    "bill_date":"2026-07-06","src_stored":_ss,"src_orig":"scan3.pdf",
    "it_name":["Item A"],"it_pack":[""],"it_qty":["1"],"it_rate":["10"],"it_amount":["10"],
    "it_make":[""],"it_model":[""],"it_serial":[""],"it_batch":[""],"it_expiry":[""],"it_hsn":[""]},
    follow_redirects=True)
check("E bill saved carrying source scan", b"Bill saved with 1 line item" in r.data)
_db=A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory=A.sqlite3.Row
_bid=_db.execute("SELECT id FROM bills WHERE bill_no='SRC1'").fetchone()["id"]; _db.close()
check("E bill_view links the scan", b"scan3.pdf" in owner.get(f"/bills/{_bid}").data)
_rf=owner.get(f"/bills/{_bid}/file")
check("E bill_file serves scan (owner)", _rf.status_code==200 and _rf.data.startswith(b"%PDF"))
check("E bill_file open to checker (manager 200; A-D21)", mgr.get(f"/bills/{_bid}/file").status_code==200)

print("STEP 19: A-D20 date-normalisation + bill->asset bridge + consumable renewals")

# 19a: _norm_date unit checks (day-first, textual, 2-digit year, passthrough, preserve)
check("norm ISO passthrough", A._norm_date("2026-07-06") == "2026-07-06")
check("norm DD.MM.YYYY day-first", A._norm_date("06.07.2026") == "2026-07-06")
check("norm DD-MM-YYYY day-first", A._norm_date("06-07-2026") == "2026-07-06")
check("norm DD/MM/YY 2-digit yr", A._norm_date("06/07/26") == "2026-07-06")
check("norm day>12 disambiguates", A._norm_date("13/07/2026") == "2026-07-13")
check("norm 2nd>12 -> M/D", A._norm_date("07/13/2026") == "2026-07-13")
check("norm textual 12-Nov-26", A._norm_date("12-Nov-26") == "2026-11-12")
check("norm textual 1 Jan 2025", A._norm_date("1 Jan 2025") == "2025-01-01")
check("norm YYYY-MM -> first", A._norm_date("2026-11") == "2026-11-01")
check("norm MMM YYYY -> first", A._norm_date("Nov 2026") == "2026-11-01")
check("norm empty/None -> None", A._norm_date("") is None and A._norm_date(None) is None)
check("norm unparseable preserved", A._norm_date("see note") == "see note")

# 19b: dates normalised ON SAVE (bill_date + item expiry)
r = owner.post("/bills/new", data={"kind":"Consumable","vendor":"NormVendor","bill_no":"NRM1",
    "bill_date":"06.07.2026",
    "it_name":["Gauze"],"it_pack":["10"],"it_qty":["5"],"it_rate":["20"],"it_amount":["100"],
    "it_make":[""],"it_model":[""],"it_serial":[""],"it_batch":["B7"],"it_expiry":["12-Nov-26"],
    "it_hsn":[""]}, follow_redirects=True)
check("A-D20 bill saved (mixed-format dates)", b"Bill saved with 1 line item" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_brow = _db.execute("SELECT id,bill_date FROM bills WHERE bill_no='NRM1'").fetchone()
check("bill_date stored ISO on save", _brow["bill_date"] == "2026-07-06", str(_brow["bill_date"]))
_irow = _db.execute("SELECT expiry FROM bill_items WHERE bill_id=?", (_brow["id"],)).fetchone()
check("item expiry stored ISO on save", _irow["expiry"] == "2026-11-12", str(_irow["expiry"]))
_db.close()

# 19c: startup normalise_dates migration self-heals legacy rows, idempotently
_db = A.sqlite3.connect(os.environ["ASSETS_DB"])
_db.execute("UPDATE bills SET bill_date='31.12.2025' WHERE bill_no='NRM1'")
_db.execute("UPDATE bill_items SET expiry='01/06/27' WHERE bill_id="
            "(SELECT id FROM bills WHERE bill_no='NRM1')")
_db.commit()
_n1 = A.normalise_dates(_db); _db.commit()
check("migration rewrote the legacy rows", _n1 >= 2, f"n={_n1}")
_n2 = A.normalise_dates(_db); _db.commit()
check("migration idempotent (0 on clean pass)", _n2 == 0, f"n={_n2}")
_db.row_factory = A.sqlite3.Row
_chk = _db.execute("SELECT bill_date FROM bills WHERE bill_no='NRM1'").fetchone()["bill_date"]
check("legacy bill_date now ISO", _chk == "2025-12-31", _chk)
_db.close()

# 19d: bill -> asset bridge: prefill, save, two-way link, renewal seed
r = owner.post("/bills/new", data={"kind":"Asset","vendor":"AssetVendor","bill_no":"AST1",
    "bill_date":"2026-07-06",
    "it_name":["Portable Ultrasound"],"it_pack":[""],"it_qty":["1"],"it_rate":["275000"],
    "it_amount":["275000"],"it_make":["Sonosite"],"it_model":["Edge II"],
    "it_serial":["SN-ULTRA-9"],"it_batch":[""],"it_expiry":["2028-07-06"],"it_hsn":[""]},
    follow_redirects=True)
check("bridge asset bill saved", b"Bill saved with 1 line item" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_ab = _db.execute("SELECT id FROM bills WHERE bill_no='AST1'").fetchone()["id"]
_it = _db.execute("SELECT id FROM bill_items WHERE bill_id=?", (_ab,)).fetchone()["id"]
_db.close()
r = owner.get(f"/bills/{_ab}")
check("bill_view offers +asset link", f"bill_item={_it}".encode() in r.data)
r = owner.get(f"/assets/new?bill_item={_it}")
check("bridge prefill name", b'value="Portable Ultrasound"' in r.data)
check("bridge prefill vendor", b'value="AssetVendor"' in r.data)
check("bridge prefill serial", b'value="SN-ULTRA-9"' in r.data)
check("bridge prefill hidden link", f'name=bill_item_id value="{_it}"'.encode() in r.data)
check("bridge blocks manager (403)", mgr.get(f"/assets/new?bill_item={_it}").status_code == 403)
r = owner.post("/assets/new", data=dict(
    name="Portable Ultrasound", location_id="2", category="Medical Equipment",
    status="Active", contract_type="None", vendor="AssetVendor",
    serial_no="SN-ULTRA-9", price="275000", bill_item_id=str(_it), threshold_days="60"),
    follow_redirects=False)
check("bridge asset created", r.status_code == 302)
_newid = int(r.headers["Location"].rstrip("/").split("/")[-1])
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
check("asset.bill_id linked",
      _db.execute("SELECT bill_id FROM assets WHERE id=?", (_newid,)).fetchone()["bill_id"] == _ab)
check("bill_item.asset_id linked",
      _db.execute("SELECT asset_id FROM bill_items WHERE id=?", (_it,)).fetchone()["asset_id"] == _newid)
_seed = _db.execute("SELECT due_date FROM expiries WHERE entity='asset' AND entity_id=? "
                    "AND label='Item expiry'", (_newid,)).fetchone()
check("renewal seeded from item expiry", _seed and _seed["due_date"] == "2028-07-06",
      str(_seed and _seed["due_date"]))
_db.close()
check("bill_view shows linked marker", f"#{_newid}".encode() in owner.get(f"/bills/{_ab}").data)
check("asset_view shows from-bill backlink", f"/bills/{_ab}".encode() in owner.get(f"/assets/{_newid}").data)

# 19e: consumable expiry surfaces in /renewals (owner only)
import datetime as _dt
_soon = (_dt.date.today() + _dt.timedelta(days=20)).isoformat()
_db = A.sqlite3.connect(os.environ["ASSETS_DB"])
_bid2 = _db.execute("INSERT INTO bills(kind,vendor,bill_no,bill_date) "
                    "VALUES('Consumable','ExpVendor','EXP1','2026-07-01')").lastrowid
_db.execute("INSERT INTO bill_items(bill_id,item_name,expiry,batch) VALUES(?,?,?,?)",
            (_bid2, "Lignocaine vials", _soon, "LOT9"))
_db.commit(); _db.close()
r = owner.get("/renewals")
check("renewals shows consumables (owner)",
      b"Consumables expiring" in r.data and b"Lignocaine vials" in r.data)
r = mgr.get("/renewals")
check("renewals hides consumables from manager", b"Consumables expiring" not in r.data)

print("STEP 20: A-D21 reception intake + maker-checker bills + vendor directory")

def sso_client(user, role, epoch=1):
    c = A.app.test_client()
    tok = "%s|%s|%d" % (user, role, epoch)
    try:
        c.set_cookie("clinic_sso", tok)                      # Werkzeug >= 2.3
    except TypeError:
        c.set_cookie("localhost", "clinic_sso", tok)         # older signature
    return c

# fresh authed clients for this step (earlier ones were epoch-invalidated, and
# STEP 12 rotated the manager's password to a generated value -- reset it first)
owner = A.app.test_client(); login(owner, "manoj", "change-me-manoj")
owner.post("/admin", data={"action": "reset_pw", "uid": "3", "new": "step20-pass"},
           follow_redirects=True)
mgr = A.app.test_client(); login(mgr, "manager", "step20-pass")

# --- 20a: SSO role map, positive + FAIL-CLOSED ---
al = sso_client("alisha", "staff")
r = al.get("/intake")
check("SSO staff -> reception reaches intake", r.status_code == 200 and b"stamp number" in r.data)
check("reception dashboard redirects to intake",
      al.get("/").status_code == 302 and "/intake" in al.get("/").headers.get("Location", ""))
for pth in ("/assets", "/bills", "/renewals", "/vendors", "/admin", "/purchases",
            "/staff", "/drafts", "/account", "/bills/new"):
    check("reception 403 on %s" % pth, al.get(pth).status_code == 403)
dr = sso_client("manoj", "doctor")
check("SSO doctor -> owner (sees Admin)", b"Admin" in dr.get("/").data)
mg2 = sso_client("shavez", "manager")
check("SSO manager -> manager (no Admin, has Purchases)",
      b"Admin" not in mg2.get("/").data and b"Purchases" in mg2.get("/").data)
unk = sso_client("eve", "auditor")
check("unknown SSO role fail-closed (login redirect)", unk.get("/assets").status_code == 302)
stale = sso_client("alisha", "staff", epoch=0)
check("stale SSO epoch rejected (login redirect)", stale.get("/intake").status_code == 302)

# --- 20b: intake round-trip + stamp slips + own-only visibility ---
r = al.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 intake1"), "recbill1.pdf"),
                                    "note": "2 boxes"},
            content_type="multipart/form-data", follow_redirects=False)
check("reception submit redirects to slip", r.status_code == 302 and "/intake/slip/" in r.headers["Location"])
_slip1 = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = al.get("/intake/slip/%d" % _slip1)
check("slip shows a stamp number", r.status_code == 200 and b"B-0" in r.data and b"Alisha" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_b1 = _db.execute("SELECT * FROM bills WHERE id=?", (_slip1,)).fetchone()
check("intake bill is a draft", _b1["status"] == "draft")
check("intake bill carries submitter + time", _b1["submitted_by"] == "Alisha" and bool(_b1["submitted_at"]))
check("intake bill carries the scan", bool(_b1["source_stored"]))
_stamp1 = _b1["stamp_no"]
_db.close()
sh = sso_client("shivani", "staff")
r = sh.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 intake2"), "recbill2.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
_slip2 = int(r.headers["Location"].rstrip("/").split("/")[-1])
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_stamp2 = _db.execute("SELECT stamp_no FROM bills WHERE id=?", (_slip2,)).fetchone()["stamp_no"]
_db.close()
check("stamps are distinct + monotonic", _stamp1 != _stamp2 and _stamp2 > _stamp1)
r = al.get("/intake")
check("reception sees ONLY own submissions",
      _stamp1.encode() in r.data and _stamp2.encode() not in r.data)
check("reception cannot open the bill itself", al.get("/bills/%d" % _slip1).status_code == 403)
check("reception cannot view another's slip", al.get("/intake/slip/%d" % _slip2).status_code == 403)

# --- 20c: background Sarvam fill (direct call; fills only what's empty) ---
_fake = {"vendor": "Aastha Medical Cares", "vendor_phone": "9876543210",
         "vendor_email": "sales@aastha.example", "bill_no": "811", "bill_date": "06.07.2026",
         "total_amount": 3969,
         "items": [{"item_name": "VIDAS TSH-30400", "quantity": 1, "rate": 3780,
                    "batch": "1011672290", "expiry": "12-Nov-26"}]}
_realS = A.SARVAM
class _StubS:
    @staticmethod
    def available(): return True
    @staticmethod
    def extract(path, **k): return _fake, "done"
A.SARVAM = _StubS
A._bg_extract(_slip1, "unused-path")
A.SARVAM = _realS
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_b1 = _db.execute("SELECT * FROM bills WHERE id=?", (_slip1,)).fetchone()
check("bg fill: header fields set", _b1["vendor"] == "Aastha Medical Cares" and _b1["bill_no"] == "811")
check("bg fill: date normalised to ISO", _b1["bill_date"] == "2026-07-06")
check("bg fill: vendor contact captured", _b1["vendor_phone"] == "9876543210")
_it1 = _db.execute("SELECT * FROM bill_items WHERE bill_id=?", (_slip1,)).fetchall()
check("bg fill: items inserted, expiry ISO", len(_it1) == 1 and _it1[0]["expiry"] == "2026-11-12")
_db.execute("UPDATE bills SET vendor='HandTyped' WHERE id=?", (_slip1,)); _db.commit(); _db.close()
A.SARVAM = _StubS; A._bg_extract(_slip1, "unused-path"); A.SARVAM = _realS
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
check("bg fill never clobbers checker edits",
      _db.execute("SELECT vendor FROM bills WHERE id=?", (_slip1,)).fetchone()["vendor"] == "HandTyped")
check("bg fill never duplicates items",
      _db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (_slip1,)).fetchone()[0] == 1)
_db.execute("UPDATE bills SET vendor='Aastha Medical Cares' WHERE id=?", (_slip1,))
_db.commit(); _db.close()

# --- 20d: approval lanes (Consumable=manager; Asset=doctor only) + reject ---
r = mgr.get("/bills")
check("manager sees pending badge", b"pending" in r.data and _stamp1.encode() in r.data)
r = mgr.post("/bills/%d/approve" % _slip1, follow_redirects=True)
check("manager approves Consumable draft", b"approved" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_b1 = _db.execute("SELECT * FROM bills WHERE id=?", (_slip1,)).fetchone()
check("approval recorded (by/at)", _b1["status"] == "approved" and _b1["approved_by"] == "Manager")
check("vendor auto-upserted on approve",
      _db.execute("SELECT phone FROM vendors WHERE name='Aastha Medical Cares'").fetchone()["phone"] == "9876543210")
_db.close()
# Asset-kind lane: manager stages, cannot approve; doctor can
r = mgr.post("/bills/new", data={"kind": "Asset", "vendor": "MedEquip Co", "bill_no": "AK1",
    "bill_date": "2026-08-01", "it_name": ["ECG Machine"], "it_pack": [""], "it_qty": ["1"],
    "it_rate": ["55000"], "it_amount": ["55000"], "it_make": [""], "it_model": [""],
    "it_serial": ["ECG-77"], "it_batch": [""], "it_expiry": [""], "it_hsn": [""]},
    follow_redirects=True)
check("manager Asset bill lands as draft", b"sent for doctor approval" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_ak = _db.execute("SELECT id FROM bills WHERE bill_no='AK1'").fetchone()["id"]
_db.close()
check("manager CANNOT approve Asset-kind (403)",
      mgr.post("/bills/%d/approve" % _ak).status_code == 403)
check("manager CANNOT reject Asset-kind (403)",
      mgr.post("/bills/%d/reject" % _ak).status_code == 403)
r = owner.post("/bills/%d/approve" % _ak, follow_redirects=True)
check("doctor approves Asset-kind", b"approved" in r.data)
# reject flow (void, stamp retained, never reused)
r = sh.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 rej"), "rej.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
_rj = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = mgr.post("/bills/%d/reject" % _rj, data={"reason": "duplicate bill"}, follow_redirects=True)
check("manager rejects Consumable draft", b"rejected" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_rjrow = _db.execute("SELECT * FROM bills WHERE id=?", (_rj,)).fetchone()
check("reject is a void (stamp + reason kept)",
      _rjrow["status"] == "rejected" and bool(_rjrow["stamp_no"]) and _rjrow["reject_reason"] == "duplicate bill")
_db.close()
r = owner.post("/bills/new", data={"kind": "Consumable", "vendor": "SeqVendor", "bill_no": "SEQ1",
    "bill_date": "2026-08-02", "it_name": ["x"], "it_pack": [""], "it_qty": ["1"], "it_rate": ["1"],
    "it_amount": ["1"], "it_make": [""], "it_model": [""], "it_serial": [""], "it_batch": [""],
    "it_expiry": [""], "it_hsn": [""]}, follow_redirects=True)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_seq = _db.execute("SELECT stamp_no FROM bills WHERE bill_no='SEQ1'").fetchone()["stamp_no"]
_db.close()
check("stamp never reused after reject", _seq > _rjrow["stamp_no"])

# --- 20e: drafts excluded from analytics + bridge until approved ---
import datetime as _dt2
_soon2 = (_dt2.date.today() + _dt2.timedelta(days=15)).isoformat()
r = mgr.post("/bills/new", data={"kind": "Asset", "vendor": "DraftVend", "bill_no": "DRX1",
    "bill_date": "2026-08-03", "it_name": ["Suction Unit"], "it_pack": [""], "it_qty": ["1"],
    "it_rate": ["9000"], "it_amount": ["9000"], "it_make": [""], "it_model": [""],
    "it_serial": ["SU-5"], "it_batch": [""], "it_expiry": [_soon2], "it_hsn": [""]},
    follow_redirects=True)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_dx = _db.execute("SELECT id FROM bills WHERE bill_no='DRX1'").fetchone()["id"]
_dxit = _db.execute("SELECT id FROM bill_items WHERE bill_id=?", (_dx,)).fetchone()["id"]
_db.close()
check("draft item absent from purchases expiring-soon", b"Suction Unit" not in owner.get("/purchases").data)
check("draft item absent from renewals consumables", b"Suction Unit" not in owner.get("/renewals?all=1").data)
check("draft bill offers no + asset link", b"bill_item=%d" % _dxit not in owner.get("/bills/%d" % _dx).data)
check("bridge prefill refused for draft item (403)",
      owner.get("/assets/new?bill_item=%d" % _dxit).status_code == 403)
owner.post("/bills/%d/approve" % _dx, follow_redirects=True)
check("approved: bridge prefill now opens",
      owner.get("/assets/new?bill_item=%d" % _dxit).status_code == 200)
check("approved: item in renewals consumables", b"Suction Unit" in owner.get("/renewals?all=1").data)

# --- 20f: draft edit + kind-flip changes the lane ---
r = sh.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 flip"), "flip.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
_fl = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = mgr.post("/bills/%d/edit" % _fl, data={"kind": "Asset", "vendor": "FlipVend", "bill_no": "FLP1",
    "bill_date": "2026-08-04", "it_name": ["Autoclave"], "it_pack": [""], "it_qty": ["1"],
    "it_rate": ["30000"], "it_amount": ["30000"], "it_make": [""], "it_model": [""],
    "it_serial": [""], "it_batch": [""], "it_expiry": [""], "it_hsn": [""]},
    follow_redirects=True)
check("manager completes a draft (edit saves)", b"Draft updated" in r.data)
check("kind-flip moved it to the doctor lane (manager approve 403)",
      mgr.post("/bills/%d/approve" % _fl).status_code == 403)
check("approved bills are not editable",
      b"Only draft bills" in mgr.get("/bills/%d/edit" % _slip1, follow_redirects=True).data)

# --- 20g: vendor directory + contacts on the asset page ---
r = mgr.get("/vendors")
check("vendors page lists upserted vendor", r.status_code == 200 and b"Aastha Medical Cares" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_vid = _db.execute("SELECT id FROM vendors WHERE name='Aastha Medical Cares'").fetchone()["id"]
_db.close()
r = mgr.post("/vendors/%d" % _vid, data={"act": "addc", "person_name": "Rakesh Kumar",
    "crole": "engineer", "cphone": "9000000001", "cemail": "rakesh@aastha.example"},
    follow_redirects=True)
check("add engineer contact", b"Rakesh Kumar" in r.data)
r = mgr.post("/vendors/%d" % _vid, data={"act": "addc", "person_name": "S Gupta",
    "crole": "service manager", "cphone": "9000000002"}, follow_redirects=True)
check("add service-manager contact", b"S Gupta" in r.data and b"service manager" in r.data)
r = owner.post("/assets/new", data=dict(name="VIDAS Analyser", location_id="2",
    category="Lab Equipment", status="Active", contract_type="AMC",
    provider="Aastha Medical Cares", vendor="Aastha Medical Cares",
    renewal_date="2027-01-01", threshold_days="60"), follow_redirects=False)
_va = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = owner.get("/assets/%d" % _va)
check("asset page shows service contacts inline",
      b"Service contacts" in r.data and b"Rakesh Kumar" in r.data and b"S Gupta" in r.data)
_db = A.sqlite3.connect(os.environ["ASSETS_DB"]); _db.row_factory = A.sqlite3.Row
_cid = _db.execute("SELECT id FROM vendor_contacts WHERE person_name='Rakesh Kumar'").fetchone()["id"]
_db.close()
mgr.post("/vendors/%d" % _vid, data={"act": "offc", "cid": str(_cid)}, follow_redirects=True)
r = owner.get("/assets/%d" % _va)
check("deactivated contact leaves the asset page",
      b"Rakesh Kumar" not in r.data and b"S Gupta" in r.data)
check("reception still 403 on vendors after all this", al.get("/vendors/%d" % _vid).status_code == 403)

print("STEP 21: A-D22 intake camera input (split camera + photo/PDF; either field works)")
_g = al.get("/intake").data
check("intake shows a camera-capture control",
      b"name=bill_cam" in _g and b"capture=environment" in _g)
check("intake shows a photo/PDF fallback control",
      b"name=bill_file" in _g and b".pdf" in _g)
check("old mixed camera+PDF single input removed",
      b'name=bill accept="image/*,.pdf" capture' not in _g)
check("camera control is a labelled button with filename feedback",
      b"Take a photo of the bill" in _g and b"cam_st" in _g and b"_pick(" in _g)
r = al.post("/intake/submit", data={"bill_cam": (io.BytesIO(b"%PDF-1.4 cam"), "cam.jpg")},
            content_type="multipart/form-data", follow_redirects=False)
check("intake accepts the camera field",
      r.status_code == 302 and "/intake/slip/" in r.headers.get("Location", ""))
r = al.post("/intake/submit", data={"bill_file": (io.BytesIO(b"%PDF-1.4 file"), "saved.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
check("intake accepts the photo/PDF field",
      r.status_code == 302 and "/intake/slip/" in r.headers.get("Location", ""))
r = al.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 legacy"), "legacy.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
check("intake still accepts the legacy 'bill' field",
      r.status_code == 302 and "/intake/slip/" in r.headers.get("Location", ""))
r = al.post("/intake/submit", data={"note": "no file here"},
            content_type="multipart/form-data", follow_redirects=False)
check("intake with no file returns to intake, not a slip",
      r.status_code == 302 and "/intake/slip/" not in r.headers.get("Location", ""))

print("STEP 22: A-D23 OCR status + Re-read button + no-blank-approve guard")
import sqlite3 as _sq
_ADB = os.environ["ASSETS_DB"]
def _bill(bid):
    d = _sq.connect(_ADB); d.row_factory = _sq.Row
    r = d.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone(); d.close(); return r
def _nit(bid):
    d = _sq.connect(_ADB)
    n = d.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (bid,)).fetchone()[0]
    d.close(); return n
_cols = {row[1] for row in _sq.connect(_ADB).execute("PRAGMA table_info(bills)")}
check("bills gained ocr_status column", "ocr_status" in _cols)

# a fresh reception draft; Sarvam is OFF in the harness, so it stays blank + NULL
r = sh.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 ad23a"), "ad23a.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
_bk = int(r.headers["Location"].rstrip("/").split("/")[-1])
_b = _bill(_bk)
check("intake draft blank + ocr_status NULL when Sarvam off",
      (_b["ocr_status"] in (None, "")) and not _b["vendor"] and _nit(_bk) == 0)

# _bg_extract now records a terminal status AND fills a blank bill (recovery path)
_realS = A.SARVAM
class _StubS2:
    @staticmethod
    def available(): return True
    @staticmethod
    def extract(path, **k):
        return ({"vendor": "Shri Ram Enterprise", "bill_no": "SRE/1", "bill_date": "2026-08-10",
                 "total_amount": 1500, "items": [{"item_name": "Gauze", "quantity": 2, "rate": 750}]}, "done")
A.SARVAM = _StubS2
_st = A._bg_extract(_bk, os.path.join(A.UPLOAD_DIR, _b["source_stored"]))
A.SARVAM = _realS
_b = _bill(_bk)
check("re-read fills a blank bill (recovery)", _b["vendor"] == "Shri Ram Enterprise" and _nit(_bk) == 1)
check("re-read records ocr_status='read'", _b["ocr_status"] == "read" and _st == "read")

# a genuinely blank scan -> 'empty'
_realS = A.SARVAM
class _StubEmpty:
    @staticmethod
    def available(): return True
    @staticmethod
    def extract(path, **k): return ({}, "done")
r = sh.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 blankscan"), "blankscan.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
_be = int(r.headers["Location"].rstrip("/").split("/")[-1])
A.SARVAM = _StubEmpty
_st = A._bg_extract(_be, os.path.join(A.UPLOAD_DIR, _bill(_be)["source_stored"]))
A.SARVAM = _realS
check("unreadable scan records ocr_status='empty'", _st == "empty" and _bill(_be)["ocr_status"] == "empty")

# extract error -> 'failed'
_realS = A.SARVAM
class _StubBoom:
    @staticmethod
    def available(): return True
    @staticmethod
    def extract(path, **k): raise RuntimeError("api down")
A.SARVAM = _StubBoom
_st = A._bg_extract(_bk, "unused")
A.SARVAM = _realS
check("extract error records ocr_status='failed'", _st == "failed" and _bill(_bk)["ocr_status"] == "failed")

# reread route guards: no scan, and Sarvam off
r = mgr.post("/bills/new", data={"kind": "Consumable", "vendor": "NoScanVend", "bill_no": "NS1",
    "bill_date": "2026-08-05", "it_name": ["x"], "it_pack": [""], "it_qty": ["1"], "it_rate": ["1"],
    "it_amount": ["1"], "it_make": [""], "it_model": [""], "it_serial": [""], "it_batch": [""],
    "it_expiry": [""], "it_hsn": [""]}, follow_redirects=True)
_d = _sq.connect(_ADB); _d.row_factory = _sq.Row
_ns = _d.execute("SELECT id FROM bills WHERE bill_no='NS1'").fetchone()["id"]; _d.close()
check("reread with no scan is handled gracefully",
      b"No scan" in mgr.post("/bills/%d/reread" % _ns, follow_redirects=True).data)
check("reread with Sarvam off tells the checker to type it in",
      b"configured" in mgr.post("/bills/%d/reread" % _bk, follow_redirects=True).data)

# reread route happy path: Sarvam on (stub), bg stubbed to no-op so 'reading' is observable
_realbg = A._bg_extract
A._bg_extract = lambda *a, **k: None
A.SARVAM = _StubS2
r = mgr.post("/bills/%d/reread" % _bk, follow_redirects=False)
check("reread launches + redirects to the bill",
      r.status_code == 302 and ("/bills/%d" % _bk) in r.headers["Location"])
check("reread marks the bill 'reading'", _bill(_bk)["ocr_status"] == "reading")
r = mgr.get("/bills/%d" % _bk)
check("bill_view shows the reading badge", b"reading the bill" in r.data)
check("bill_view offers Re-read with Sarvam", b"Re-read with Sarvam" in r.data)
A._bg_extract = _realbg
A.SARVAM = _realS

# no-blank-approve guard
r = sh.post("/intake/submit", data={"bill": (io.BytesIO(b"%PDF-1.4 blankappr"), "blankappr.pdf")},
            content_type="multipart/form-data", follow_redirects=False)
_blk = int(r.headers["Location"].rstrip("/").split("/")[-1])
r = mgr.post("/bills/%d/approve" % _blk, follow_redirects=True)
check("blank bill approve blocked without confirm",
      b"no vendor, total, or items" in r.data and _bill(_blk)["status"] == "draft")
r = mgr.post("/bills/%d/approve" % _blk, data={"confirm_blank": "1"}, follow_redirects=True)
check("blank bill approves only with explicit confirm", _bill(_blk)["status"] == "approved")

print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if failed else 0)
