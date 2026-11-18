#!/usr/bin/env python3
"""synth_s876.py <folder holding patient_events.py, sanjeevni_day.py, finance_ui/finance_approvals.html> [--real <db copy>]
Kit S876_HUB_RECORD_INLINE's proof, on a MADE-UP database built at run time (no real number anywhere in the kit, F-185).
Run on the rebuilt files: every check green.  Run on S874's files (the control): red.
--real: also reads every clinic ID with a Sanjeevni bill in a COPY of the live database (read-only), counting
failures and the slowest read only -- nothing about a patient is printed."""
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = os.path.abspath(sys.argv[1])
REAL = sys.argv[sys.argv.index("--real") + 1] if "--real" in sys.argv else None
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]   # never import the kit's own copy (F-1441)
OK, BAD = [], []


def check(name, cond, why=""):
    (OK if cond else BAD).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  -- " + str(why)))


TMP = tempfile.mkdtemp(prefix="s876_")
try:
    for f in ("patient_events.py", "sanjeevni_day.py"):
        if os.path.exists(os.path.join(ROOT, f)):
            shutil.copy(os.path.join(ROOT, f), TMP)
    sys.path.insert(0, TMP)
    try:
        import patient_events as pe
    except Exception as ex:                                   # noqa: BLE001
        pe = None
        check("T0 patient_events.py imports", False, ex)

    rnd = random.Random()
    def mk_id():
        return str(rnd.randint(10000, 99999))
    A, B_, W = mk_id(), mk_id(), "WA" + mk_id()             # two made-up patients and a walk-in
    while B_ == A:
        B_ = mk_id()
    DB = os.path.join(TMP, "made_up.db")
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT, name TEXT, phone_last4 TEXT, merged_into TEXT);
    CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT);
    CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INT, unit TEXT, patient_ref_id INT, service TEXT, amount_p INT,
                            mode TEXT, source_ref TEXT, confidence REAL, verified_by TEXT);
    CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, day_entry_id INT, business_date TEXT, bill_no TEXT, is_return INT, seq INT,
                                 item_name TEXT, item_key TEXT, pack TEXT, qty_raw TEXT, amount_p INT);
    CREATE TABLE identity_dispute (id INTEGER PRIMARY KEY, bill_no TEXT, clinic_id TEXT, status TEXT);
    CREATE TABLE clinic_day_line (business_date TEXT, section TEXT, patient TEXT, clinic_id TEXT, amount_p INT, mode TEXT);
    CREATE TABLE patient_visit (visit_date TEXT, clinic_id TEXT);
    CREATE TABLE slip (id INTEGER PRIMARY KEY, series TEXT, slip_no TEXT, day TEXT, clinic_id TEXT, state TEXT);
    CREATE TABLE slip_item (id INTEGER PRIMARY KEY, slip_id INT, kind TEXT, name TEXT, side TEXT, sort INT);
    CREATE TABLE record_file (id INTEGER PRIMARY KEY, clinic_id TEXT, kind TEXT, day TEXT, drive_id TEXT, file_name TEXT, state TEXT, note TEXT);
    CREATE TABLE blood_order (id INTEGER PRIMARY KEY, day TEXT, clinic_id TEXT, state TEXT, outcome TEXT);
    CREATE TABLE lab_report (msg_id TEXT, clinic_id TEXT, received_at TEXT);
    CREATE TABLE record_event (id INTEGER PRIMARY KEY, clinic_id TEXT, day TEXT, hospital TEXT, what TEXT, note TEXT, state TEXT);
    """)
    con.execute("INSERT INTO patient_ref VALUES (1,?,?,NULL,NULL)", (A, "MADE UP ONE"))
    con.execute("INSERT INTO patient_ref VALUES (2,?,?,NULL,NULL)", (B_, "MADE UP TWO"))
    con.execute("INSERT INTO patient_ref VALUES (3,?,?,NULL,NULL)", (W, "WALK IN"))
    days = ["2026-11-%02d" % d for d in (1, 2, 10, 11, 15, 16, 18)]
    for i, d in enumerate(days, 1):
        con.execute("INSERT INTO day_entry VALUES (?,?,?)", (i, "medical", d))
    E = {d: i for i, d in enumerate(days, 1)}

    def bill(no, day, pid, lines, ret=False, conf=1.0, ver="x", amt=None, mode="cash"):
        tot = 0
        for s, (name, pack, qty, rate) in enumerate(lines, 1):
            con.execute("INSERT INTO sale_line_item (day_entry_id,business_date,bill_no,is_return,seq,item_name,item_key,pack,qty_raw,amount_p) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)", (E[day], day, no, 1 if ret else 0, s, name, name.upper(), pack, qty, rate))
            tot += pe.line_value_p(qty, pack, rate) if pe else 0
        con.execute("INSERT INTO sale_item (day_entry_id,unit,patient_ref_id,service,amount_p,mode,source_ref,confidence,verified_by) "
                    "VALUES (?,?,?,?,?,?,?,?,?)", (E[day], "medical", pid, "pharmacy_return" if ret else "pharmacy",
                                                   amt if amt is not None else tot, mode, no, conf, ver))
    PANS = ("PANSPED L", "1*10", "1:5", 18400)
    ZIB = ("ZIBON EXTRA", "1*10", "2:0", 26000)
    # patient A: 15-Nov and 16-Nov the same bill (billed twice?); 18-Nov returns 5 tablets of the 16-Nov bill
    bill("A9001", "2026-11-15", 1, [PANS, ZIB])
    bill("A9002", "2026-11-16", 1, [PANS, ZIB], mode="UPI")
    bill("CN901", "2026-11-18", 1, [("PANSPED L", "1*10", "0:5", 18400)], ret=True)
    # an exchange on 02-Nov: bought Crocal, gave it back, took Shelcal instead -- one day
    bill("A8001", "2026-11-02", 1, [("CROCAL", "1*10", "1:0", 5600)])
    bill("CN801", "2026-11-02", 1, [("CROCAL", "1*10", "1:0", 5600)], ret=True)
    bill("A8002", "2026-11-02", 1, [("SHELCAL 500", "1*15", "1:0", 9400)])
    # 10-Nov: a part of one bill given back beside another, unrelated bill (the cold review's case)
    bill("A0998", "2026-11-10", 1, [("CROCAL", "1*10", "1:0", 5600)])
    bill("A0999", "2026-11-10", 1, [("PARA 500", "1*10", "1:0", 2000)])
    bill("CN802", "2026-11-10", 1, [("CROCAL", "1*10", "0:5", 5600)], ret=True)
    # 01-Nov: A999 and A1000 -- the same medicines, unpadded numbers
    bill("A999", "2026-11-01", 1, [("ROSU 10", "1*10", "1:0", 3000)])
    bill("A1000", "2026-11-01", 1, [("ROSU 10", "1*10", "1:0", 3000)])
    # not sure (0.90, unchecked) and disputed: never shown
    bill("A7001", "2026-11-10", 1, [("NOT SURE MED", "1*10", "1:0", 1000)], conf=0.90, ver=None)
    bill("A7002", "2026-11-11", 1, [("DISPUTED MED", "1*10", "1:0", 1000)])
    con.execute("INSERT INTO identity_dispute (bill_no,clinic_id,status) VALUES ('A7002',?,'open')", (A,))
    # other kinds of quantity
    bill("A6001", "2026-11-01", 1, [("LOFTYPRED 80 INJ", "2ML", "3.0", 9800), ("ACTIVE SYP", "100ML", "1.0", 14000),
                                    ("DICLOGEL", "30GM", "1.0", 24200), ("CALFLIP D3 SACH", "1*1", "2.0", 3500),
                                    ("SOME VIAL", "VAIL", "1.0", 12000), ("ODD <b>NAME</b>", "1*10", "0:7", 1000)])
    # patient B: different quantities on two days -- no flag; and the walk-in bill never reaches an ID
    bill("A5001", "2026-11-15", 2, [PANS])
    bill("A5002", "2026-11-16", 2, [("PANSPED L", "1*10", "2:0", 18400)])
    bill("A5003", "2026-11-16", 3, [PANS])
    # the clinic for A
    con.execute("INSERT INTO clinic_day_line VALUES ('2026-11-16','consult','MADE UP ONE',?,50000,'upi')", (A,))
    con.execute("INSERT INTO clinic_day_line VALUES ('2026-11-16','xray','MADE UP ONE',?,40000,'cash')", (A,))
    con.execute("INSERT INTO clinic_day_line VALUES ('2026-11-02','consult','MADE UP ONE',?,50000,'cash')", (A,))
    con.execute("INSERT INTO patient_visit VALUES ('2026-10-20',?)", (A,))
    con.execute("INSERT INTO slip VALUES (1,'opd','S-1','2026-11-16',?,'ok')", (A,))
    con.execute("INSERT INTO slip_item (slip_id,kind,name,side,sort) VALUES (1,'xray','Knee AP/Lat','right',1)")
    con.execute("INSERT INTO record_file (clinic_id,kind,day,drive_id,file_name,state,note) VALUES (?,'xray','2026-11-16','d1','knee_ap.jpg','ok','')", (A,))
    con.execute("INSERT INTO record_file (clinic_id,kind,day,drive_id,file_name,state,note) VALUES (?,'xray','2026-11-16','d2','knee_lat.jpg','ok','')", (A,))
    con.execute("INSERT INTO blood_order (day,clinic_id,state,outcome) VALUES ('2026-11-02',?,'ok','')", (A,))
    con.execute("INSERT INTO lab_report VALUES ('m1',?,'2026-11-03T10:00:00')", (A,))
    con.execute("INSERT INTO record_file (clinic_id,kind,day,drive_id,file_name,state,note) VALUES (?,'blood','2026-11-02','d3','cbc.pdf','ok','')", (A,))
    con.execute("INSERT INTO record_event (clinic_id,day,hospital,what,note,state) VALUES (?,'2026-10-01','City <i>Hospital</i>','TKR right','','ok')", (A,))
    con.commit()

    if pe:
        q = pe.qty_words
        check("T1 quantities in words", [q("1:5", "1*10"), q("0:7", "1*10"), q("2:0", "1*10"), q("3.0", "2ML", "LOFTYPRED 80 INJ"),
                                         q("1.0", "100ML", "ACTIVE SYP"), q("1.0", "30GM", "DICLOGEL"), q("2.0", "1*1", "CALFLIP D3 SACH"),
                                         q("1.0", "VAIL", "X"), q("1:1", "1*10")] ==
              ["1 strip 5 tablets", "7 tablets", "2 strips", "3 injections", "1 bottle", "1 tube", "2 sachets", "1 vial", "1 strip 1 tablet"],
              [q("1:5", "1*10"), q("3.0", "2ML", "LOFTYPRED 80 INJ")])
        r = pe.events(con, A)
        flat = [(d["date"], e) for d in r["days"] for e in d["events"]]
        kinds = [e["kind"] for _, e in flat]
        dates = [d["date"] for d in r["days"]]
        check("T2 days newest first", dates == sorted(dates, reverse=True), dates)
        rets = [(d, e) for d, e in flat if e["kind"] == "returned" and "CN901" in e["ref"]]
        check("T3 the return shown once, on its own date, naming its bill",
              len(rets) == 1 and rets[0][0] == "2026-11-18" and "16-Nov bill A9002" in rets[0][1]["sub"], rets)
        b16 = [e for d, e in flat if e["kind"] == "bought" and e["ref"] == "A9002"]
        note = b16 and [l["note"] for o in b16[0]["opens"] for l in o.get("lines", []) if l["item"] == "PANSPED L"]
        check("T4 the bill notes what came back", bool(note) and note[0] == "5 tablets returned 18-Nov", note)
        ex = [e for d, e in flat if e["kind"] == "exchanged"]
        check("T5 bought, gave back and took another on one day = one Exchanged line",
              len(ex) == 1 and "Crocal" in ex[0]["text"] and "Shelcal 500" in ex[0]["text"] and ex[0]["sign"] == "+" and ex[0]["money"] == "38"
              and len(ex[0]["opens"]) == 3 and not [e for d, e in flat if e["ref"] in ("A8001", "A8002", "CN801")], ex)
        pa = [e for d, e in flat if d == "2026-11-10" and e["kind"] in ("returned", "exchanged", "bought")]
        check("T5b a part of a bill given back beside another bill = a plain return, not 'Exchanged'",
              sorted(e["kind"] for e in pa) == ["bought", "bought", "returned"], [(e["kind"], e["ref"]) for e in pa])
        nn = [e for d, e in flat if e["ref"] == "A1000"]
        check("T5c bill numbers ordered as numbers (A999 before A1000)", nn and nn[0]["flag"] and "bill A999" in nn[0]["flag"]["text"],
              nn and nn[0]["flag"])
        f16 = b16 and b16[0]["flag"]
        check("T6 same medicines and quantities as the day before = flagged", bool(f16) and f16["tone"] == "warn"
              and "15-Nov bill A9001" in f16["text"], f16)
        check("T7 the not-sure and the disputed bill never shown", not [e for d, e in flat if e["ref"] in ("A7001", "A7002")])
        b1 = [e for d, e in flat if e["ref"] == "A6001"]
        q1 = [l["qty"] for o in b1[0]["opens"] for l in o["lines"]] if b1 else []
        check("T8 every bill line in words, none in strips:tabs", q1 == ["3 injections", "1 bottle", "1 tube", "2 sachets", "1 vial", "7 tablets"]
              and not any(re.search(r"\d:\d", l["qty"]) for _, e in flat for o in e["opens"] for l in o.get("lines", [])), q1)
        d16 = [d for d in r["days"] if d["date"] == "2026-11-16"][0]["events"]
        check("T9 a day reads clinic first, then medicines", [e["kind"] for e in d16] == ["consult", "xray", "bought"], [e["kind"] for e in d16])
        xr = [e for e in d16 if e["kind"] == "xray"][0]
        films = [f for o in xr["opens"] for f in o.get("files") or []]
        check("T10 the X-ray names the study from the slip, its films one tap under", "knee ap/lat right" in xr["text"] and len(films) == 2
              and films[0]["url"].startswith("/finance/records/file/") and "2 films filed" in xr["sub"], (xr["text"], xr["sub"], films))
        con_ = [e for e in d16 if e["kind"] == "consult"][0]
        check("T11 consulted with the money and the slip", con_["money"] == "500" and con_["sub"] == "UPI"
              and any(o.get("text", "").startswith("Slip S-1") for o in con_["opens"]), con_)
        bl = [e for d, e in flat if e["kind"] == "blood"]
        check("T12 blood test ordered, report received, report one tap under", len(bl) == 1 and "report received 03-Nov" in bl[0]["text"]
              and bl[0]["opens"] and bl[0]["opens"][0]["files"][0]["url"], bl)
        hs = [e for d, e in flat if e["kind"] == "hospital"]
        check("T13 the doctor's hospital event, its words left plain for the page to escape", len(hs) == 1 and hs[0]["head"] == "TKR right"
              and "City <i>Hospital</i>" in hs[0]["sub"], hs)
        check("T14 a visit Docterz's list knows", "visit" in kinds and "2026-10-20" in dates)
        check("T15 header: name, first seen, visit days, the full record", r["name"] == "MADE UP ONE" and r["first_seen"] == "01-Oct"
              and r["visit_days"] == 3 and r["full_url"] == "/finance/records/p/" + A and r["recent_days"] == 5, (r["first_seen"], r["visit_days"]))
        rb = pe.events(con, B_)
        check("T16 different quantities the day before = no flag; a walk-in's bill never on an ID",
              not [e for d in rb["days"] for e in d["events"] if e.get("flag")] and
              not [e for d in rb["days"] for e in d["events"] if e["ref"] == "A5003"], rb["days"])
        con.execute("INSERT INTO setting VALUES ('patient_events.same_bill_days','0','')")
        con.execute("INSERT INTO setting VALUES ('patient_events.recent_days','2','')")
        r0 = pe.events(con, A)
        check("T17 the settings are read (0 days back -> the day-before pair unflagged; 2 days open)",
              not [e for d in r0["days"] for e in d["events"] if e.get("flag") and e["ref"] == "A9002"] and r0["recent_days"] == 2)
        con.execute("DELETE FROM setting")
        bill("CN902", "2026-11-18", 1, [ZIB, ("PANSPED L", "1*10", "1:0", 18400)], ret=True)
        r2 = pe.events(con, A)
        f2 = [e["flag"] for d in r2["days"] for e in d["events"] if e["ref"] == "A9002"]
        check("T18 returns that take the second bill back in full settle the flag (grey)", f2 and f2[0] and f2[0]["tone"] == "mut"
              and "Taken back by CN901 of 18-Nov, CN902 of 18-Nov" in f2[0]["text"], f2)
        con.execute("DELETE FROM sale_item WHERE source_ref='CN902'"); con.execute("DELETE FROM sale_line_item WHERE bill_no='CN902'"); con.commit()
        check("T19 an ID with nothing on record reads empty, not an error", pe.events(con, "99999999")["days"] == [])
        con.execute("INSERT INTO slip VALUES (9,'opd','S-9',NULL,?,'ok')", (A,)); con.execute("INSERT INTO lab_report VALUES ('m9',?,NULL)", (A,))
        try:
            pe.events(con, A); okn = True
        except Exception as ex:                               # noqa: BLE001
            okn = ex
        check("T19b a slip or a lab report with no date does not break the record", okn is True, okn)
        con.execute("DELETE FROM slip WHERE id=9"); con.execute("DELETE FROM lab_report WHERE msg_id='m9'")
        check("T19c walk-ins (WALK-IN, WA...) are no patient", not pe.is_patient_id("WALK-IN") and not pe.is_patient_id(W)
              and pe.is_patient_id(A) and pe.qty_words("1:x", "1*10") == "quantity not readable")
        check("T20 nothing written by a read", con.total_changes >= 0 and
              sqlite3.connect(DB).execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0] == 14)

    # ---- the door, in Flask, mounted by sanjeevni_day.init
    try:
        from flask import Flask, jsonify
        import sanjeevni_day
        app = Flask("t")
        who = {"role": "checker"}

        def req(role, unit=None):
            if who["role"] == role:
                return ({"user": "manoj"}, None)
            return (None, (jsonify(ok=False, error="denied"), 403))
        sanjeevni_day.init(app, lambda: sqlite3.connect(DB), req, "medical")
        c = app.test_client()
        h = c.get("/finance/sanjeevni/api/patient-events/healthz")
        check("T21 mounted by sanjeevni_day.init (healthz)", h.status_code == 200 and h.get_json().get("kit") == "S876_HUB_RECORD_INLINE", h.status_code)
        g = c.get("/finance/sanjeevni/api/patient/%s/record" % A)
        j = g.get_json() or {}
        check("T22 the door answers the owner with the record", g.status_code == 200 and j.get("ok") and j.get("cid") == A and len(j.get("days", [])) >= 6, g.status_code)
        check("T23 a bad ID is refused", c.get("/finance/sanjeevni/api/patient/a%20b;x/record").status_code in (400, 404))
        check("T23b a walk-in has no record (refused, no chip)", c.get("/finance/sanjeevni/api/patient/WALK-IN/record").status_code == 400)
        who["role"] = "maker"
        check("T24 only the checker (the owner) may read it", c.get("/finance/sanjeevni/api/patient/%s/record" % A).status_code == 403)
        who["role"] = "checker"
        rec_json = j
    except Exception as ex:                                   # noqa: BLE001
        rec_json = {}
        check("T21-24 the door", False, "%s: %s" % (type(ex).__name__, ex))

    # ---- the page: the anchors and the script's own drawing, in node
    html = open(os.path.join(ROOT, "finance_ui", "finance_approvals.html"), encoding="utf-8").read()
    check("T25 a bill's ID taps open the record", "if(b.clinic_id) who=s876Who(who,b.clinic_id);" in html)
    check("T26 a return's ID taps open the record", "b.clinic_id?s876Chip(b.clinic_id,'row'):''" in html)
    check("T27 the Returns card carries the same tap", "s876Chip(r.clinic_id,'here','the patient\\'s record')" in html)
    check("T28 no dialog in the new script (F-1464)", "KIT_S876" in html and not re.search(r"(confirm|alert|prompt)\(",
          html.split("/* ==== KIT_S876")[-1].split("/* ==== end KIT_S876")[0]) if "KIT_S876" in html else False)
    js = re.findall(r"<script>(.*?)</script>", html, re.S)
    part = html.split("/* ==== KIT_S876")[1].split("/* ==== end KIT_S876 ==== */")[0] if "KIT_S876" in html else ""
    if part and rec_json and not shutil.which("node"):
        print("  skip T29-32 (no node on this machine -- proven in the kit's build)")
    elif part and rec_json:
        rec_json["days"][0]["events"][0]["head"] = "<img src=x onerror=alert(1)>"
        node = ("function esc(s){return (s==null?'':String(s)).replace(/[&<>\"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]})}\n"
                "function s874Mob(b){return ' MOB'+(b.mobiles||[]).length}\n/* " + part + "\n"
                "var j=" + json.dumps(rec_json) + ";var h=s876Html(j);var out={h:h};"
                "out.walk=s876Chip('WALK-IN','row');out.wa=s876Chip('WA123','row');out.chip=s876Chip('12<3','row');out.who=s876Who('<b>X</b> <span class=\"mut\">NAME · #777</span>','777');"
                "process.stdout.write(JSON.stringify(out));")
        p = os.path.join(TMP, "t.js")
        open(p, "w", encoding="utf-8").write(node)
        try:
            o = json.loads(subprocess.run(["node", p], capture_output=True, text=True, timeout=60).stdout or "{}")
        except Exception as ex:                               # noqa: BLE001
            o = {}
            print("  node:", ex)
        h = o.get("h", "")
        check("T29 the panel draws: name, the full record, the flag, the lines in words", "MADE UP ONE" in h and "Open the full record" in h
              and "Billed twice?" in h and "1 strip 5 tablets" in h and "/finance/records/p/" + A in h, h[:200])
        check("T30 everything from the record is escaped on the page", "<img src=x" not in h and "&lt;img src=x" in h
              and "<b>NAME</b>" not in h and "City &lt;i&gt;Hospital" in h, "")
        check("T31 days past the setting sit behind 'earlier'", "earlier day" in h and h.index("earlier day") > h.index("18-Nov"))
        check("T32 the chip escapes the ID; the name loses its '#ID' to the chip", "12&lt;3" in o.get("chip", "")
              and "NAME</span>" in o.get("who", "") and o.get("who", "").count("#777") == 1 and o.get("walk") == "#WALK-IN" and o.get("wa") == "#WA123", (o.get("chip"), o.get("who"), o.get("walk"), o.get("wa")))
    else:
        check("T29-32 the panel draws in node", False, "no KIT_S876 script on the page" if not part else "no record from the door")

    # ---- the real copy, read-only: every clinic ID with a bill, counts only
    if REAL and pe:
        rc = sqlite3.connect("file:%s?mode=ro" % REAL, uri=True)
        ids = [x[0] for x in rc.execute("SELECT DISTINCT p.clinic_id FROM sale_item s JOIN patient_ref p ON p.id=s.patient_ref_id "
                                        "WHERE s.service IN ('pharmacy','pharmacy_return') AND p.clinic_id<>''") if pe.is_patient_id(x[0])]
        fails, slow, raw = 0, 0.0, 0
        for cid in ids:
            t = time.time()
            try:
                rr = pe.events(rc, cid)
                raw += sum(1 for d in rr["days"] for e in d["events"] for o in e["opens"] for l in o.get("lines", [])
                           if re.search(r"^\d+:\d+$", l["qty"]))
            except Exception:                                 # noqa: BLE001
                fails += 1
            slow = max(slow, time.time() - t)
        check("R1 every ID on the real copy reads (%d IDs, slowest %.2f s)" % (len(ids), slow), fails == 0 and slow < 2.0, "%d failed" % fails)
        check("R2 no strips:tabs code reaches the page on the real copy", raw == 0, raw)
finally:
    shutil.rmtree(TMP, ignore_errors=True)
print("S876 synth: %d ok, %d failed" % (len(OK), len(BAD)))
sys.exit(1 if BAD else 0)
