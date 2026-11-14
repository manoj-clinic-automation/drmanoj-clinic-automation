#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s835_app.py -- S835_CREDIT_NOTES on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder
with the given sorting_desk.py, clinic_papers.py, claude_reader.py and xray_costs.py (TO -- or the live files for the control), on a
fresh database the app makes itself. Made-up rows only ("Walk Dealer835", dated 2031); a made-up Marg (finance.db) and spine; nothing
leaves the process. The scratch folder is removed at the end.

    python3 -B walk_s835_app.py --live <the app folder> --shared <the shared folder> --files <folder holding the files to test> [--expect-red] [--box]
    --box: run by the installer on the server -- where node is absent, D6 (the page script) stands as checked when the kit was built.
"""
import datetime
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES = opt("--live", "/root/assetapp"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("sorting_desk.py", "clinic_papers.py", "claude_reader.py", "xray_costs.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
GREEN_BOTH = ("A0", "D6", "Z1")                                      # the app loads; its script is valid; an ordinary bill's Save is unchanged

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s835app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(app, f))
        SHARED = opt("--shared")                                     # the live /root/shared (scan_checks_s441 adds page_of, dup_flag ...)
        if SHARED:
            shutil.copytree(SHARED, os.path.join(work, "shared"), ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        fin, spn = os.path.join(work, "finance.db"), os.path.join(work, "spine.db")
        f = sqlite3.connect(fin)
        f.executescript("""
CREATE TABLE purchase_scan_link(bill_id INTEGER, asset_bill_id INTEGER, grade TEXT, matched_on TEXT, linked_at TEXT);
CREATE TABLE purchase_bill(id INTEGER PRIMARY KEY, supplier_norm TEXT, supplier TEXT, bill_no TEXT, bill_date TEXT, month TEXT, amount_p INTEGER, first_seen_day TEXT);
CREATE TABLE purchase_line(id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT, batch TEXT,
  expiry TEXT, tax REAL, qty REAL, free REAL, rate_p INTEGER, discount_pct REAL, amount_p INTEGER, net_rate_p INTEGER, net_amount_p INTEGER,
  loose_qty REAL, purchase_rate_p INTEGER, direction TEXT, source_md5 TEXT, line_type TEXT);
CREATE TABLE purchase_export(md5 TEXT PRIMARY KEY, type TEXT, received_at TEXT, superseded_by TEXT);
INSERT INTO purchase_export VALUES('OLDWALK','ITEMWISE','2031-03-06 10:00','NEWWALK'),('NEWWALK','ITEMWISE','2031-03-07 10:00',NULL);
INSERT INTO purchase_bill VALUES(9001,'WALK DEALER835','WALK DEALER835 BAREILLY','WD803','2031-03-05','2031-03',141000,'2031-03-06');
INSERT INTO purchase_line(supplier_norm,bill_no,bill_date,item,batch,qty,free,rate_p,amount_p,net_amount_p,direction,source_md5,line_type) VALUES
 ('WALK DEALER835','WD803','2031-03-05','WALKITEM OLD','B0',1,0,1000,1000,1000,'PURCHASE','OLDWALK','ITEMWISE'),
 ('WALK DEALER835','WD803','2031-03-05','WALKITEM ONE','B1',2,0,50000,100000,100000,'PURCHASE','NEWWALK','ITEMWISE'),
 ('WALK DEALER835','WD803','2031-03-05','WALKITEM TWO','B2',1,1,41000,41000,41000,'PURCHASE','NEWWALK','ITEMWISE');
""")
        f.commit()
        f.close()
        s = sqlite3.connect(spn)
        s.execute("CREATE TABLE sp_purchase_bill (supplier TEXT, supkey TEXT, bill TEXT, date TEXT, amount_p INTEGER, direction TEXT, source_md5 TEXT)")
        s.commit()
        s.close()
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"),
                   SHARED_LIB_DIR=os.path.join(work, "shared" if opt("--shared") else "noshared"), SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"),
                   SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1", CLINIC_PORTAL_DIR=os.path.join(work, "noportal"),
                   FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=fin, SPINE_DB_FOR_SCANS=spn,
                   READER_WATCH_STATE=os.path.join(work, "rw_state.json"), READER_WATCH_STUB=os.path.join(work, "rw_sent.jsonl"),
                   READER_WATCH_ALL_OFF=os.path.join(work, "_off", "ALL_OFF"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=600)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S835" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S835_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]   # never the kit's own copies (F-1415)
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:500]) if (d and not ok) else ""))


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&#39;", "'").replace("&amp;", "&")


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
ck("A0 the real app loads with its seven parts mounted (%s)" % ", ".join(m for m, x in mods.items() if x is not None), lambda: all(mods.values()))
sd, cp = mods["sorting_desk"], mods["clinic_papers"]
cr = sys.modules.get("claude_reader") or __import__("claude_reader")
ck("A1 the desk carries S835 and its table credit_note exists after the mount",
   lambda: getattr(sd, "CREDIT_NOTES", "") == "S835" and sqlite3.connect(os.environ["ASSETS_DB"]).execute(
       "SELECT 1 FROM sqlite_master WHERE name='credit_note'").fetchone() is not None)
sd.TODAY = datetime.date(2031, 3, 20)
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s835','Walk owner','owner','x',1)")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-01-01')")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s835'").fetchone()[0]
    ss["epoch"] = epoch
N = [0]


def mk(vendor, no, date, amt, lane="clinic", sub=None, status="draft", kind="Consumable", dk=None, created=None, items=()):
    N[0] += 1
    cur = db.execute("INSERT INTO bills(kind, vendor, bill_no, bill_date, total_amount, status, lane, subgroup, doc_kind, created_at, stamp_no, source_stored) "
                     "VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (kind, vendor, no, date, amt, status, lane, sub, dk, created or (date + " 05:00:00"),
                                                         "B-%04d" % (8350 + N[0]), "walk835_%d.pdf" % N[0]))
    for it in items:
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity, rate, amount) VALUES(?,?,?,?,?)", (cur.lastrowid,) + tuple(it))
    db.commit()
    return cur.lastrowid


D = "Walk Dealer835"
H1 = mk(D, "WD-803", "2031-03-05", 1410, lane="pharmacy", status="captured", kind="Pharmacy")
H2 = mk(D, "WD/0789", "2031-03-01", 3260, sub="procedure", status="approved", items=[("WALK GLOVES", 10, 326, 3260)])
H3 = mk(D, "WD/0500", "2030-10-01", 999, sub="procedure", status="approved")                       # older than 90 days
H4 = mk("Another Walk Firm", "AW/1", "2031-03-04", 1410, sub="procedure", status="approved")      # another dealer
H5 = mk(D, "WD-R1", "2031-03-06", 300, sub="procedure", status="captured", dk="receipt")          # a receipt: never offered
H6 = mk(D, "WD/0900", "2031-03-02", 2000, sub="implant_stock", status="approved")
HP = mk(D, "WD/PERS", "2031-03-03", 700, lane="owner_expense", sub="personal", status="captured", kind="Expense")
HL = mk(D, "WD/LAB", "2031-03-04", 640, lane="lab_purchase", status="captured", kind="Lab")                  # NK Pathology's
HE = mk(D, "WD/EQ", "2031-03-08", 9000, sub="clinic_equipment", status="approved", kind="Asset")
HC = mk(D, "WD/CON", "2031-03-09", 5000, sub="construction", status="approved")
P = mk(D, "CN-0045", "2031-03-12", 500, created="2031-03-12 06:00:00")
dbf = sqlite3.connect(os.environ["FINANCE_DB_FOR_SCANS"])
dbf.execute("INSERT INTO purchase_scan_link VALUES(9001, ?, 'verified', 'walk', '2031-03-07')", (H1,))
dbf.commit()
dbf.close()
db.execute("CREATE TABLE IF NOT EXISTS claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT)")
db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
           (P, "2031-03-12 06:01:00", "walk", "credit_note", json.dumps({"doc_kind": "credit_note", "vendor": D, "bill_no": "CN-0045", "bill_date": "2031-03-12",
                                                                         "total_amount": 500, "against_no": "WD/0803",
                                                                         "items": [{"name": "WALKITEM TWO", "qty": 1, "amount": 500}]})))
db.commit()

# ---- R: the reader
cl = cr.clean({"doc_kind": "credit_note", "vendor": "X", "bill_no": "CN-1", "total_amount": 10, "against_no": "INV/7", "items": []}) or {}
cb = cr.clean({"doc_kind": "bill", "vendor": "X", "bill_no": "B-1", "total_amount": 10, "against_no": "INV/7", "items": []}) or {}
ck("R1 the reader asks for a credit note (its kind, the invoice no. it names) and keeps both; a bill's reading is unchanged; the PHARMACY "
   "reader's prompt is untouched",
   lambda: '"credit_note"' in cr.PROMPT and "against_no" in cr.PROMPT and cl.get("doc_kind") == "credit_note" and cl.get("against_no") == "INV/7"
   and cb.get("doc_kind") == "bill" and "against_no" not in cb and '"credit_note"' not in cr.PHARMACY_PROMPT, lambda: (cl, cb))


def paper(i):
    r = own.get("/desk/api/paper/%d" % i)
    return r.status_code, (r.get_json(silent=True) or {})


def save(body):
    r = own.post("/desk/api/save", json=body)
    return r.status_code, (r.get_json(silent=True) or {})


code, j = paper(P)
cn = j.get("cn") or {}
ids = [c["id"] for c in cn.get("cands") or []]
c1 = ([c for c in cn.get("cands") or [] if c["id"] == H1] or [{}])[0]
c2 = ([c for c in cn.get("cands") or [] if c["id"] == H2] or [{}])[0]
ck("D1 a paper the reader calls a credit note: the desk says so with its no. and the invoice it names, and pre-chooses the kind",
   lambda: (j.get("fix") or {}).get("key") == "credit_note" and "CN-0045" in j["fix"]["text"] and "WD/0803" in j["fix"]["text"]
   and j.get("kind") == "credit_note", lambda: (code, j.get("fix"), j.get("kind")))
ck("D2 'Against which bill?': this dealer's bills of 90 days, newest first, any lane (the pharmacy scan too) -- never an older one, another "
   "dealer's, a receipt, or itself; the reader's pick (WD/0803 meets WD-803) pre-chosen",
   lambda: ids[:4] == [H1, H6, H2] or (set(ids) >= {H1, H2, H6} and H3 not in ids and H4 not in ids and H5 not in ids and P not in ids
                                       and ids.index(H1) < ids.index(H2)) and c1.get("pre") and not c2.get("pre"), lambda: (ids, c1.get("pre"), c2.get("pre")))
ck("D3 the pharmacy bill opens with Marg's purchase entry (bill WD803; its two lines from the export in force, never the superseded one) "
   "and 'not entered yet' for the purchase return; the clinic bill with the lines saved on the desk",
   lambda: (c1.get("marg") or {}).get("bill_no") == "WD803" and [l["item"] for l in c1["marg"]["lines"]] == ["WALKITEM ONE", "WALKITEM TWO"]
   and c1.get("ret") == "not entered yet" and c1.get("dest") == "pharmacy" and [l["item"] for l in c2.get("lines") or []] == ["WALK GLOVES"]
   and c2.get("dest") == "procedure", lambda: (c1, c2))
ck("D4 never a bill of an expense file (Dr MK's Personal) or of NK Pathology -- a credit note kept there would count as spend -- not even for the owner",
   lambda: set(r["id"] for r in sd._s835_cands(db, sd._row(db, P), True)) >= {H1, H2} and HP not in [r["id"] for r in sd._s835_cands(db, sd._row(db, P), True)]
   and HL not in [r["id"] for r in sd._s835_cands(db, sd._row(db, P), True)])
html = own.get("/desk").get_data(as_text=True)
ck("D5 the desk carries the credit note box, the bill's credit-note block and the sixth kind chip",
   lambda: "id=cn835" in html and "id=cnon835" in html and '["credit_note", "Credit note"]' in html and "function s835paint" in html)
js = re.findall(r"<script>(.*?)</script>", html, re.S)
jsok, jsmsg = False, "no script"
if js:
    jp = os.path.join(WORK, "desk835.js")
    open(jp, "w", encoding="utf-8").write(js[-1])
    try:
        rr = subprocess.run(["node", "--check", jp], capture_output=True, text=True, timeout=60)
        jsok, jsmsg = rr.returncode == 0, rr.stderr[-400:]
    except FileNotFoundError:                                        # on the box: the script was checked when the kit was built
        jsok, jsmsg = ("--box" in ARGS), "node is not here"
ck("D6 the desk's script, as the page renders it, is valid JavaScript (node --check)", lambda: jsok, lambda: jsmsg)
SENTB = []
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")
db.commit()
pic = os.path.join(WORK, "walk835.jpg")
open(pic, "wb").write(b"\xff\xd8\xff\xe0WALK835" + b"\x00" * 64)
_orig_post = getattr(cr, "_post_before_s783", None)
def _fake(body, key):
    SENTB.append(body)
    return 200, {"stop_reason": "end_turn", "content": [{"type": "text", "text": json.dumps({"doc_kind": "credit_note", "vendor": "W", "bill_no": "CN-9",
                 "total_amount": 9, "against_no": "INV/9", "items": []})}]}, ""
if _orig_post is not None:
    cr._post_before_s783 = _fake
else:
    cr._post = _fake
got = cr.read(pic, None, dbp)
if _orig_post is not None:
    cr._post_before_s783 = _orig_post
sent_text = " ".join(c.get("text", "") for b_ in SENTB for m in b_.get("messages", []) for c in m.get("content", []) if isinstance(c, dict))
ck("R2 the request the reader actually SENDS asks for a credit note and its invoice no., and what comes back is kept (doc_kind, against_no)",
   lambda: "A CREDIT NOTE is money the supplier gives BACK" in sent_text and '"credit_note"' in sent_text and (got or {}).get("doc_kind") == "credit_note"
   and (got or {}).get("against_no") == "INV/9", lambda: (len(SENTB), got))
DUMP = os.environ.get("S835_DUMP")                                   # for the page walk (walk_s835_page.js): the page and its JSON
if DUMP:
    open(os.path.join(DUMP, "desk.html"), "w", encoding="utf-8").write(html)
    json.dump({"P": P, "H1": H1, "H2": H2, "paper_P": j}, open(os.path.join(DUMP, "p.json"), "w", encoding="utf-8"))


def live_links(i):
    try:
        return [dict(r) for r in db.execute("SELECT * FROM credit_note WHERE cn_bill_id=? AND voided_at=''", (i,))]
    except sqlite3.OperationalError:                                 # the control: no such table
        return []


def n_voided(i):
    try:
        return db.execute("SELECT COUNT(*) FROM credit_note WHERE cn_bill_id=? AND voided_at<>''", (i,)).fetchone()[0]
    except sqlite3.OperationalError:
        return -1


def n_links():
    try:
        return db.execute("SELECT COUNT(*) FROM credit_note").fetchone()[0]
    except sqlite3.OperationalError:
        return -1


def row(i):
    return dict(db.execute("SELECT * FROM bills WHERE id=?", (i,)).fetchone())


def sec(ym, key):
    secs, _a, _n = sd.month_data(db, ym, True, datetime.date(2031, 3, 20))
    return [s for s in secs if s["key"] == key][0]


base_proc = sec("2031-03", "procedure")["total"]
code, r1 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "500", "kind": "credit_note", "dest": "",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H2)},
                 "pr_lines": [{"no": 1, "name": "WALK GLOVES", "qty": "5", "unit": "", "brand": "", "place": "proc", "item": "free", "sug": False}],
                 "pr_role": "slip", "pr_order": "", "pr_book": ""})
db.commit()
p1, L1 = row(P), live_links(P)
ck("S1 Saved against the clinic bill: filed with it in Procedure room, NEVER accepted (captured), one live link; the message says its month "
   "is lowered; no Procedure room line came with it",
   lambda: code == 200 and r1.get("ok") and p1["doc_kind"] == "credit_note" and p1["subgroup"] == "procedure" and p1["status"] == "captured"
   and (p1["lane"] or "clinic") == "clinic" and len(L1) == 1 and L1[0]["against_bill_id"] == H2 and "lowered" in r1.get("message", "")
   and not (sd._s634_pr() and sd._s634_pr().has_lines(db, sd._row(db, P))), lambda: (code, r1, p1["doc_kind"], p1["status"], L1))
s = sec("2031-03", "procedure")
mt = sd.month_total(db, "2031-03", True)
mh = txt(own.get("/desk/month?ym=2031-03").get_data(as_text=True))
ck("M1 The month: Procedure room bought ₹3,260 · Credit notes − ₹500 · Spent ₹2,760 -- the section's total, the home card's month total "
   "and the page all read it", lambda: s["bought"] == base_proc and s["credit"] == 500 and s["total"] == base_proc - 500
   and mt == sum(x["total"] for x in sd.month_data(db, "2031-03", True)[0]) and "Credit notes" in mh and "Spent" in mh, lambda: (s.get("bought"), s.get("credit"), s["total"], mt))
ck("M2 never spend anywhere: clinic_papers' live papers and sections leave the credit note out, its accept refuses it",
   lambda: db.execute("SELECT COUNT(*) FROM bills b WHERE b.id=? AND " + cp._live(db), (P,)).fetchone()[0] == 0
   and db.execute("SELECT COUNT(*) FROM bills b WHERE b.id=? AND " + cp._live_sections(db), (P,)).fetchone()[0] == 0
   and not ("credit_note" not in open(cp.__file__, encoding="utf-8").read()))
st2 = sd.paid_state(db, sd._row(db, H2))
code, j2 = paper(H2)
ck("P1 the bill's page: Bill ₹3,260 · Credit note CN-0045 − ₹500 · Still owed ₹2,760; its paid state counts the credit note; a receipt "
   "against it now finds ₹2,760 owing", lambda: st2.get("credit") == 500 and st2["state"] == "part" and (j2.get("cn_on") or {}).get("owed") == "₹2,760"
   and [c["id"] for c in (j2.get("cn_on") or {}).get("credits") or []] == [P] and sd._s560_outstanding(db, sd._row(db, H2)) == 2760
   and st2["word"] == "Credit note −₹500 of ₹3,260",
   lambda: (st2, j2.get("cn_on")))
if DUMP:
    json.dump(j2, open(os.path.join(DUMP, "h2.json"), "w", encoding="utf-8"))
code, r2 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "500", "kind": "credit_note", "dest": "procedure",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H1)}})
db.commit()
p2, L2 = row(P), live_links(P)
sanj = [r[0] for r in db.execute("SELECT id FROM bills WHERE kind='Pharmacy' AND status='captured'")]
code_h1, jh1 = paper(H1)
code_p, jp_ = paper(P)
ck("S2 re-pointed at the pharmacy bill: handed to Sanjeevni (pharmacy lane, kind 'Pharmacy credit note', captured), the old link voided "
   "(kept), one live link; Sanjeevni's own read (kind='Pharmacy' AND status='captured') never takes it; it still opens on the desk, the "
   "pharmacy bill does not -- its refusal names the credit note",
   lambda: code == 200 and p2["lane"] == "pharmacy" and p2["kind"] == "Pharmacy credit note" and p2["status"] == "captured" and len(L2) == 1
   and L2[0]["against_bill_id"] == H1 and len([1 for r_ in db.execute("SELECT * FROM credit_note WHERE cn_bill_id=?", (P,))]) == 2
   and P not in sanj and H1 in sanj and code_p == 200 and code_h1 == 403 and p2["stamp_no"] in (jh1.get("error") or "")
   and "Sanjeevni" in r2.get("message", ""), lambda: (code, r2, p2["lane"], p2["kind"], L2, code_h1, jh1))
ck("S3 the Procedure room month is back to what was bought (the credit note is against a pharmacy bill now)",
   lambda: sec("2031-03", "procedure")["credit"] == 0 and sec("2031-03", "procedure")["total"] == base_proc)
code, r3 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "500", "kind": "credit_note", "dest": "others",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": "acct"}})
db.commit()
p3, L3 = row(P), live_links(P)
code, j3 = paper(H2)
ck("S4 on the dealer's account: kept where he files it (Others, off the pharmacy lane), never accepted; one live link, on account; it "
   "lowers no month; the dealer's statement box lists it",
   lambda: code == 200 and (p3["lane"] or "clinic") == "clinic" and p3["subgroup"] == "others" and p3["status"] == "captured" and p3["kind"] != "Pharmacy credit note"
   and len(L3) == 1 and L3[0]["on_account"] == 1 and L3[0]["against_bill_id"] is None and sec("2031-03", "others")["credit"] == 0
   and [a["id"] for a in (j3.get("cn") or {}).get("acct") or []] == [P], lambda: (r3, p3["lane"], p3["subgroup"], L3))
before = (json.dumps(row(P), sort_keys=True), n_links())
g1 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "500", "kind": "credit_note", "dest": "", "joins": [], "cn": {}})
g2 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "500", "kind": "credit_note", "dest": "", "joins": [], "cn": {"against": str(H3)}})
g3 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "0", "kind": "credit_note", "dest": "", "joins": [], "cn": {"against": str(H2)}})
db.commit()
after = (json.dumps(row(P), sort_keys=True), n_links())
ck("G1 refused, each in one plain line and nothing saved: no bill chosen; an old bill (beyond 90 days); no amount back",
   lambda: g1[0] == 400 and "choose the bill it is against" in g1[1].get("error", "") and g2[0] == 400 and "not one of this dealer" in g2[1].get("error", "")
   and g3[0] == 400 and "amount back" in g3[1].get("error", "") and before == after, lambda: (g1, g2, g3))
Q = mk(D, "CN-0050", "2031-03-14", 300, created="2031-03-14 06:00:00")
code, rq = save({"id": Q, "vendor": D, "bill_no": "CN-0050", "bill_date": "14-03-2031", "total_amount": "300", "kind": "credit_note", "dest": "",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H6)}})
db.commit()
lg = sd.ledger(db, datetime.date(2031, 3, 20)).get(sd._key(D)) or {}
ck("L1 the implant stock ledger: a credit note of ₹300 against a ₹2,000 implant bill -- the dealer owes ₹1,700",
   lambda: code == 200 and abs(lg.get("owed", 0) - 1700) < 0.01 and any(r_["k"] == "Credit note" for r_ in lg.get("rows", [])), lambda: (rq, lg.get("owed")))
code, r4 = save({"id": P, "vendor": D, "bill_no": "CN-0045", "bill_date": "12-03-2031", "total_amount": "500", "kind": "bill", "dest": "procedure",
                 "who": "mk", "flag": "", "joins": []})
db.commit()
p4 = row(P)
ck("S5 the same paper saved as a bill after all: its link voided (kept -- its three links all on record, none live), a bill again on the clinic lane and accepted by the usual rule",
   lambda: code == 200 and p4["doc_kind"] == "bill" and not live_links(P) and n_voided(P) == 3 and p4["status"] == "approved" and p4["kind"] != "Pharmacy credit note",
   lambda: (r4, p4["doc_kind"], p4["status"], live_links(P)))
ck("X1 one sum everywhere: a credit note row counts negative in _s566_total, and xray_costs reads the month's credit notes",
   lambda: sd._s566_total([{"doc_kind": "credit_note", "total_amount": 100}, {"doc_kind": "bill", "total_amount": 250}]) == 150
   and "_s835_cn_rows" in open(mods["xray_costs"].__file__, encoding="utf-8").read())
V = mk(D, "WD/0950", "2031-03-17", 400, created="2031-03-17 06:00:00")
code, rv1 = save({"id": V, "vendor": D, "bill_no": "WD/0950", "bill_date": "17-03-2031", "total_amount": "400", "kind": "bill", "dest": "procedure",
                  "who": "mk", "flag": "", "joins": [], "pr_lines": [{"no": 1, "name": "WALK SWAB", "qty": "4", "unit": "", "brand": "", "place": "proc", "item": "ask", "sug": False}],
                  "pr_role": "slip", "pr_order": "", "pr_book": ""})
db.commit()
prm = sd._s634_pr()
had = bool(prm and prm.has_lines(db, sd._row(db, V)))
code, rv2 = save({"id": V, "vendor": D, "bill_no": "WD/0950", "bill_date": "17-03-2031", "total_amount": "400", "kind": "credit_note", "dest": "",
                  "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H2)}})
db.commit()
ck("C3 a paper with Procedure room lines saved as a credit note: its lines are taken off (a credit note counts nothing in a stock)",
   lambda: had and code == 200 and not prm.has_lines(db, sd._row(db, V)), lambda: (had, rv1, rv2))
E5 = mk(D, "CN-EQ", "2031-03-18", 1000, created="2031-03-18 06:00:00")
code, re5 = save({"id": E5, "vendor": D, "bill_no": "CN-EQ", "bill_date": "18-03-2031", "total_amount": "1000", "kind": "credit_note", "dest": "",
                  "who": "mk", "flag": "", "joins": [], "cn": {"against": str(HE)}})
db.commit()
ck("C5 a credit note against a Clinic equipment bill: filed in Clinic equipment, never made an asset purchase (kind Asset)",
   lambda: code == 200 and row(E5)["subgroup"] == "clinic_equipment" and row(E5)["kind"] != "Asset" and row(E5)["status"] == "captured", lambda: (re5, row(E5)["kind"]))
GA = mk(D, "CN-PE", "2031-03-18", 50, created="2031-03-18 07:00:00")
ga = save({"id": GA, "vendor": D, "bill_no": "CN-PE", "bill_date": "18-03-2031", "total_amount": "50", "kind": "credit_note", "dest": "pe",
           "who": "mk", "flag": "", "joins": [], "cn": {"against": "acct"}})
ck("G2 a credit note on the dealer's account is never kept in an expense file (it would count there): refused in one line",
   lambda: ga[0] == 400 and "never in an expense file" in ga[1].get("error", "") and row(GA)["lane"] in (None, "clinic"), lambda: ga)
T = mk(D, "CN-PH", "2031-03-19", 100, created="2031-03-19 06:00:00")
code, rt = save({"id": T, "vendor": D, "bill_no": "CN-PH", "bill_date": "19-03-2031", "total_amount": "100", "kind": "credit_note", "dest": "",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H1)}})
db.commit()
U = mk(None, None, "2031-03-19", 60, created="2031-03-19 07:00:00")
ju0 = (own.get("/desk/api/paper/%d" % U).get_json(silent=True) or {}).get("cn") or {}
ju1 = (own.get("/desk/api/paper/%d?cn_vendor=%s&cn_day=2031-03-19" % (U, D.replace(" ", "%20"))).get_json(silent=True) or {}).get("cn") or {}
code, ru = save({"id": U, "vendor": D, "bill_no": "CN-U", "bill_date": "19-03-2031", "total_amount": "60", "kind": "credit_note", "dest": "",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H2)}})
db.commit()
ck("D7 no supplier read: the box says to type it; with the supplier typed (not saved yet) the desk offers that dealer's bills, and the "
   "Save against one of them goes through",
   lambda: not ju0.get("cands") and "Type the supplier first" in ju0.get("none", "") and H2 in [c["id"] for c in ju1.get("cands") or []]
   and code == 200 and live_links(U) and live_links(U)[0]["against_bill_id"] == H2, lambda: (ju0.get("none"), [c["id"] for c in ju1.get("cands") or []], ru))
db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_mgr_s835','Walk manager','manager','x',1)")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
db.execute("DELETE FROM settings WHERE key='desk.cn'")
db.commit()
mgr = ar.app.test_client()
with mgr.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_mgr_s835'").fetchone()[0]
    ss["epoch"] = epoch
R = mk(D, "CN-0060", "2031-03-16", 200, created="2031-03-16 06:00:00")
db.execute("INSERT OR REPLACE INTO claude_reading(bill_id, at, model, ok, doc_kind, data) VALUES(?,?,?,1,?,?)",
           (R, "2031-03-16 06:01:00", "walk", "credit_note", json.dumps({"doc_kind": "credit_note", "vendor": D, "bill_no": "CN-0060", "against_no": "WD/0789", "items": []})))
db.commit()
mh0 = mgr.get("/desk").get_data(as_text=True)
jm0 = mgr.get("/desk/api/paper/%d" % R).get_json(silent=True) or {}
sm0 = mgr.post("/desk/api/save", json={"id": R, "vendor": D, "bill_no": "CN-0060", "bill_date": "16-03-2031", "total_amount": "200", "kind": "credit_note",
                                       "dest": "", "joins": [], "cn": {"against": str(H2)}})
sm0j = sm0.get_json(silent=True) or {}
mT = mgr.get("/desk/api/paper/%d" % T)
card = txt(own.get("/desk/month?ym=2031-03").get_data(as_text=True))
ck("W1 installed switched OFF for Shavez: his desk has no Credit note chip, no reader's line, no box, his Save of one is refused in one "
   "line, and a credit note already with Sanjeevni does not open for him; the owner's switch card lists “Credit notes on the desk”",
   lambda: "Credit notes on the desk" in card and '["credit_note", "Credit note"]' not in mh0 and (jm0.get("fix") or {}).get("key") != "credit_note"
   and jm0.get("kind") != "credit_note" and not jm0.get("cn") and sm0.status_code == 403 and "switches them on" in sm0j.get("error", "")
   and row(T)["kind"] == "Pharmacy credit note" and mT.status_code == 403,
   lambda: ("Credit notes on the desk" in card, jm0.get("fix"), jm0.get("kind"), bool(jm0.get("cn")), sm0.status_code, sm0j))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.cn','on')")
db.commit()
mh1 = mgr.get("/desk").get_data(as_text=True)
jm1 = mgr.get("/desk/api/paper/%d" % R).get_json(silent=True) or {}
c1m = [c for c in (jm1.get("cn") or {}).get("cands") or [] if c.get("pre")]
ck("W2 switched on: Shavez gets the chip, the reader's line and the box, the reader's pick (WD/0789) pre-chosen; never the owner's Personal bill",
   lambda: '["credit_note", "Credit note"]' in mh1 and (jm1.get("fix") or {}).get("key") == "credit_note" and jm1.get("kind") == "credit_note"
   and [c["id"] for c in c1m] == [H2] and HP not in [c["id"] for c in (jm1.get("cn") or {}).get("cands") or []], lambda: (jm1.get("fix"), c1m))
code, r7 = save({"id": T, "vendor": D, "bill_no": "CN-PH", "bill_date": "19-03-2031", "total_amount": "100", "kind": "challan", "dest": "pharmacy",
                 "who": "mk", "flag": "", "joins": []})
db.commit()
ck("C7 a credit note with Sanjeevni saved as a CHALLAN after all: kind 'Challan' (a challan never enters Sanjeevni's register), its link voided",
   lambda: code == 200 and row(T)["kind"] == "Challan" and row(T)["lane"] == "pharmacy" and not live_links(T) and n_voided(T) == 1, lambda: (r7, row(T)["kind"]))
T2 = mk(D, "CN-PH2", "2031-03-19", 80, created="2031-03-19 08:00:00")
code, r8a = save({"id": T2, "vendor": D, "bill_no": "CN-PH2", "bill_date": "19-03-2031", "total_amount": "80", "kind": "credit_note", "dest": "",
                  "who": "mk", "flag": "", "joins": [], "cn": {"against": str(H1)}})
db.commit()
was8 = row(T2)["lane"]
code, r8 = save({"id": T2, "vendor": D, "bill_no": "CN-PH2", "bill_date": "19-03-2031", "total_amount": "80", "kind": "credit_note", "dest": "",
                 "who": "mk", "flag": "", "joins": [], "cn": {"against": str(HC)}})
db.commit()
ck("C8 a credit note with Sanjeevni re-pointed at a Construction bill: on the clinic lane in Construction (never the Documents lane), captured",
   lambda: was8 == "pharmacy" and code == 200 and (row(T2)["lane"] or "clinic") == "clinic" and row(T2)["subgroup"] == "construction"
   and row(T2)["status"] == "captured" and row(T2)["kind"] != "Pharmacy credit note", lambda: (was8, r8, row(T2)["lane"], row(T2)["subgroup"]))
Z = mk("Plain Walk Supplier", "PW/1", "2031-03-15", 120)
code, rz = save({"id": Z, "vendor": "Plain Walk Supplier", "bill_no": "PW/1", "bill_date": "15-03-2031", "total_amount": "120", "kind": "bill",
                 "dest": "others", "who": "mk", "flag": "", "joins": []})
db.commit()
ck("Z1 an ordinary bill's Save is unchanged: filed in Others and accepted", lambda: code == 200 and row(Z)["status"] == "approved" and row(Z)["subgroup"] == "others",
   lambda: rz)
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S835 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE (every new check red; the app and an ordinary Save green)" if not bad_
                                                   else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S835 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
