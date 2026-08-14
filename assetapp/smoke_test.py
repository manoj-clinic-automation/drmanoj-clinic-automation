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
check("D bills owner-only (manager 403)", mgr.get("/bills").status_code==403)
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
check("E bill_file owner-only", mgr.get(f"/bills/{_bid}/file").status_code==403)

print(f"\n{'='*40}\nRESULT: {passed} passed, {failed} failed")
shutil.rmtree(TMP, ignore_errors=True)
sys.exit(1 if failed else 0)
