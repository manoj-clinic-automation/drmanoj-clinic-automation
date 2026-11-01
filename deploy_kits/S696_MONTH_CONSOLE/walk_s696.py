#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s696.py -- S696_MONTH_CONSOLE: the walk on MADE-UP databases (never a patient; never the live files).

usage: python3 walk_s696.py <finance dir with month_read.py and the estate's modules> [--control]
  --control  runs the same checks against a finance dir WITHOUT S696 (the live owner_console.py): the S696 checks must go RED.

What it proves: every reading rule of month_read.py on rows it made itself -- the dots, the actions, the subtotals and the
grand total, the X-ray expenses, the film rate, the bought and supplies lines, the fail-soft path, section_lines -- and that a
changed input changes the reading (mutants M1-M8). The console's own builder is run on the made-up database at the end.
Exit 0 only when every check is green.
"""
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

CHECKS = []
MUT = []


def ok(name, cond, why=""):
    CHECKS.append((name, bool(cond), why))
    print("  %s  %s%s" % ("green" if cond else "RED  ", name, (" -- " + why) if (why and not cond) else ""))


def mut(name, caught, why=""):
    MUT.append((name, bool(caught)))
    print("  %s  mutant %s%s" % ("caught" if caught else "MISSED", name, (" -- " + why) if (why and not caught) else ""))


def mk_finance(path, today):
    """A made-up finance.db: the tables month_read reads directly, plus the film log's and the month jobs' own tables."""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    c = con.cursor()
    ym = today.strftime("%Y-%m")
    pm = (today.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
    c.executescript("""
    CREATE TABLE clinic_day_revenue(business_date TEXT PRIMARY KEY, cons_count INT, cons_amount_p INT, xray_count INT, xray_amount_p INT,
        proc_count INT, proc_amount_p INT, total_count INT, total_amount_p INT);
    CREATE TABLE clinic_day_line(business_date TEXT, section TEXT, sn INT, patient TEXT, clinic_id TEXT, amount_p INT, mode TEXT, shift TEXT, gateway_ref TEXT);
    CREATE TABLE clinic_physio_day(business_date TEXT PRIMARY KEY, cash_p INT, upi_p INT);
    CREATE TABLE physio_course(id INTEGER PRIMARY KEY, patient_id INT, kind TEXT, rate_p INT, status TEXT);
    CREATE TABLE physio_session(id INTEGER PRIMARY KEY, course_id INT, day TEXT, slip_no TEXT, amount_p INT, mode TEXT, voided_at TEXT);
    CREATE TABLE physio_payment(id INTEGER PRIMARY KEY, course_id INT, day TEXT, amount_p INT, mode TEXT, voided_at TEXT);
    CREATE TABLE day_entry(id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, status TEXT);
    CREATE TABLE purchase_month(month TEXT PRIMARY KEY, status TEXT, finalised_by TEXT, finalised_at TEXT, billwise_total_p INT, itemwise_total_p INT, note TEXT);
    CREATE TABLE purchase_neft_event(id INTEGER PRIMARY KEY, month TEXT, kind TEXT);
    CREATE TABLE purchase_pay_check(id INTEGER PRIMARY KEY, month TEXT, at TEXT, who TEXT, ok INT, detail TEXT);
    CREATE TABLE petty_payee(code TEXT PRIMARY KEY, name TEXT, what_hi TEXT, what_en TEXT, head TEXT, default_p INT, sort INT, active INT);
    CREATE TABLE petty_entry(id INTEGER PRIMARY KEY, entry_date TEXT, kind TEXT, party TEXT, other_name TEXT, amount_p INT, void_at TEXT);
    CREATE TABLE surg_case(id INTEGER PRIMARY KEY, uid TEXT);
    CREATE TABLE pack_send(id INTEGER PRIMARY KEY, month TEXT, sent_at TEXT, sent_by TEXT);
    CREATE TABLE mj_paper(id INTEGER PRIMARY KEY, vehicle_id INT, paper TEXT, expiry TEXT);
    CREATE TABLE xf_purchase(id INTEGER PRIMARY KEY, src TEXT UNIQUE, size TEXT, bill_day TEXT, boxes REAL, vendor TEXT, seen_at TEXT, gone_at TEXT NOT NULL DEFAULT '', held INT NOT NULL DEFAULT 0);
    """)
    # the clinic's month that ended: 3 days
    for d, cons, xr, pr in ((pm + "-03", 60000, 40000, 15000), (pm + "-04", 50000, 30000, 0), (pm + "-05", 70000, 50000, 20000)):
        c.execute("INSERT INTO clinic_day_revenue VALUES (?,?,?,?,?,?,?,?,?)", (d, 1, cons, 1, xr, 1, pr, 3, cons + xr + pr + 1000))   # +10 other
        c.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", (d, "consult", 1, "", "", cons - 10000, "Cash", "", ""))
        c.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", (d, "consult", 2, "", "", 10000, "Online Payment", "", ""))
        c.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", (d, "xray", 3, "", "", xr, "Split Payment", "", ""))
        if pr:
            c.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", (d, "proc", 4, "", "", pr, "Debit Card", "", ""))
        c.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", (d, "revisit", 5, "", "", 0, "", "", ""))
    # the running month: one day
    c.execute("INSERT INTO clinic_day_revenue VALUES (?,?,?,?,?,?,?,?,?)", (ym + "-02", 1, 30000, 0, 0, 0, 0, 1, 30000))
    c.execute("INSERT INTO clinic_day_line VALUES (?,?,?,?,?,?,?,?,?)", (ym + "-02", "consult", 1, "", "", 30000, "Cash", "", ""))
    # physio
    c.execute("INSERT INTO clinic_physio_day VALUES (?,?,?)", (pm + "-03", 50000, 20000))
    c.execute("INSERT INTO clinic_physio_day VALUES (?,?,?)", (pm + "-04", 30000, 0))
    c.execute("INSERT INTO physio_course VALUES (1, 1, 'home', 50000, 'open')")
    c.execute("INSERT INTO physio_course VALUES (2, 2, 'clinic', 50000, 'open')")
    c.execute("INSERT INTO physio_session VALUES (1, 1, ?, '', 50000, 'cash', NULL)", (pm + "-10",))
    c.execute("INSERT INTO physio_session VALUES (2, 1, ?, '', 50000, 'cash', NULL)", (pm + "-11",))
    c.execute("INSERT INTO physio_session VALUES (3, 1, ?, '', 50000, 'cash', '2026-01-01')", (pm + "-12",))   # voided: not counted
    c.execute("INSERT INTO physio_session VALUES (4, 2, ?, '7', 50000, 'cash', NULL)", (pm + "-12",))      # a clinic course: not a home visit
    c.execute("INSERT INTO physio_payment VALUES (1, 1, ?, 70000, 'cash', NULL)", (pm + "-11",))
    # Sanjeevni days: 4 approved of 5 (one submitted) in the ended month
    for i, st in enumerate(("approved", "approved", "approved", "approved", "submitted")):
        c.execute("INSERT INTO day_entry (unit, business_date, status) VALUES ('medical', ?, ?)", (pm + "-%02d" % (i + 1), st))
    c.execute("INSERT INTO purchase_month VALUES (?, 'final', 'manoj', ?, 0, 0, NULL)", (pm, pm + "-28T10:00:00"))
    c.execute("INSERT INTO purchase_pay_check (month, at, who, ok, detail) VALUES (?, ?, 'shavez', 1, '')", (pm, ym + "-01T09:00:00"))
    # petty: two monthly payees, one paid
    c.execute("INSERT INTO petty_payee VALUES ('rahul','Rahul','','', 'monthly', 500000, 1, 1)")
    c.execute("INSERT INTO petty_payee VALUES ('guard','Guard','','', 'monthly', 300000, 2, 1)")
    c.execute("INSERT INTO petty_payee VALUES ('mason','Mason','','', 'construction', 100000, 3, 1)")
    c.execute("INSERT INTO petty_entry (entry_date, kind, party, amount_p) VALUES (?, 'pay', 'rahul', 500000)", (pm + "-28",))
    c.execute("INSERT INTO surg_case VALUES (1, 'u1')")
    # vehicle papers: one due in 20 days
    c.execute("INSERT INTO mj_paper (vehicle_id, paper, expiry) VALUES (1, 'insurance', ?)", ((today + dt.timedelta(days=20)).isoformat(),))
    c.execute("INSERT INTO mj_paper (vehicle_id, paper, expiry) VALUES (1, 'rc', ?)", ((today + dt.timedelta(days=400)).isoformat(),))
    # film bills: two boxes of 8x10 last month (bill 7), one of 11x14 (bill 8); an older 8x10 (bill 5)
    c.execute("INSERT INTO xf_purchase (src, size, bill_day, boxes, vendor) VALUES ('bill:7:2026-10-12 10:00:00:8x10', '8x10', ?, 2, 'Jugnu')", (pm + "-12",))
    c.execute("INSERT INTO xf_purchase (src, size, bill_day, boxes, vendor) VALUES ('bill:8:2026-10-27 10:00:00:11x14', '11x14', ?, 1, 'Jugnu')", (pm + "-27",))
    c.execute("INSERT INTO xf_purchase (src, size, bill_day, boxes, vendor) VALUES ('bill:5:2026-08-02 10:00:00:8x10', '8x10', '2026-08-02', 1, 'Jugnu')")
    con.commit()
    return con


def mk_register(path, pm, approved=True, locked=False, checked=True):
    if os.path.exists(path):
        os.unlink(path)
    rc = sqlite3.connect(path)
    rc.executescript("""
    CREATE TABLE attcorr_month(ym TEXT PRIMARY KEY, entered_by TEXT, entered_ts TEXT, checked_by TEXT, checked_ts TEXT, approved_by TEXT, approved_ts TEXT);
    CREATE TABLE attcorr_day(ym TEXT, mark TEXT, applied_mark TEXT);
    CREATE TABLE locked_run(ym TEXT PRIMARY KEY, status TEXT, locked_by TEXT, locked_ts TEXT);""")
    rc.execute("INSERT INTO attcorr_month VALUES (?, 'shivani', ?, ?, ?, ?, ?)",
               (pm, pm + "-30T10:12:00", "shavez" if checked else None, (pm + "-30T12:40:00") if checked else None,
                "manoj" if approved else None, (pm + "-30T13:00:00") if approved else None))
    if locked:
        rc.execute("INSERT INTO locked_run VALUES (?, 'locked', 'manoj', ?)", (pm, pm + "-30T14:00:00"))
    rc.commit()
    rc.close()


def mk_assets(path, pm, ym, today):
    a = sqlite3.connect(path)
    a.executescript("""
    CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, subgroup TEXT, status TEXT, dup_of INT, created_at TEXT);
    CREATE TABLE expiries(id INTEGER PRIMARY KEY, entity TEXT, entity_id INT, label TEXT, due_date TEXT, threshold_days INT, resolved INT DEFAULT 0);
    CREATE TABLE assets(id INTEGER PRIMARY KEY, name TEXT, purchase_date TEXT, created_at TEXT);
    CREATE TABLE asset_cover(id INTEGER PRIMARY KEY, asset_id INT, kind TEXT, provider TEXT, from_day TEXT, till_day TEXT, cost REAL, voided_at TEXT DEFAULT '');
    CREATE TABLE service_logs(id INTEGER PRIMARY KEY, asset_id INT, log_date TEXT, work TEXT, cost REAL, next_due TEXT);
    CREATE TABLE xray_mark(id INTEGER PRIMARY KEY, kind TEXT, ref_id INT, removed_at TEXT DEFAULT '', removed_by TEXT DEFAULT '');
    CREATE TABLE battery_place(id INTEGER PRIMARY KEY, name TEXT, life_months INT);
    CREATE TABLE battery_fit(id INTEGER PRIMARY KEY, place_id INT, fitted_on TEXT, price REAL, bill_id INT, voided_at TEXT DEFAULT '');
    CREATE TABLE stationery_line(id INTEGER PRIMARY KEY, day TEXT, side TEXT, amount REAL, voided_at TEXT DEFAULT '');
    CREATE TABLE stationery_stmt(id INTEGER PRIMARY KEY, ym TEXT, made_at TEXT, voided_at TEXT DEFAULT '');
    """)
    a.execute("INSERT INTO bills VALUES (5, 'Consumable', 'Jugnu', 'J5', '2026-08-02', 9000, 'xray_8x10', '', NULL, '2026-08-02 10:00:00')")
    a.execute("INSERT INTO bills VALUES (7, 'Consumable', 'Jugnu', 'J7', ?, 21600, 'xray_8x10', '', NULL, '2026-10-12 10:00:00')", (pm + "-12",))
    a.execute("INSERT INTO bills VALUES (8, 'Consumable', 'Jugnu', 'J8', ?, 13900, 'xray_11x14', '', NULL, '2026-10-27 10:00:00')", (pm + "-27",))
    a.execute("INSERT INTO bills VALUES (9, 'Consumable', 'Plaster Co', 'P9', ?, 4000, 'clinic_consumables', '', NULL, '2026-10-20 10:00:00')", (pm + "-20",))
    a.execute("INSERT INTO bills VALUES (10, 'Consumable', 'Someone', 'S10', ?, 700, '', '', NULL, '2026-10-21 10:00:00')", (pm + "-21",))      # not laned
    a.execute("INSERT INTO bills VALUES (11, 'Consumable', 'Dup', 'D11', ?, 999, 'clinic_consumables', '', 9, '2026-10-22 10:00:00')", (pm + "-22",))  # a second scan: skipped
    a.execute("INSERT INTO expiries (entity, entity_id, label, due_date, threshold_days, resolved) VALUES ('asset', 1, 'licence', ?, 30, 0)", ((_first(ym) + dt.timedelta(days=10)).isoformat(),))
    a.execute("INSERT INTO expiries (entity, entity_id, label, due_date, threshold_days, resolved) VALUES ('asset', 1, 'old', ?, 30, 1)", ((_first(ym) + dt.timedelta(days=5)).isoformat(),))   # resolved: not counted
    a.execute("INSERT INTO assets VALUES (1, 'Digital X-ray', '2024-01-01', '2024-01-01')")
    a.execute("INSERT INTO assets VALUES (2, 'Scooter', ?, ?)", (pm + "-15", pm + "-15"))
    a.execute("INSERT INTO asset_cover (asset_id, kind, provider, from_day, till_day, cost) VALUES (1, 'amc', 'Fuji', ?, ?, 36000)", (pm[:4] + "-01-01", pm[:4] + "-12-31"))
    a.execute("INSERT INTO asset_cover (asset_id, kind, provider, from_day, till_day, cost) VALUES (1, 'warranty', 'Fuji', ?, ?, 99999)", (pm[:4] + "-01-01", pm[:4] + "-12-31"))  # not spread
    a.execute("INSERT INTO service_logs (asset_id, log_date, work, cost, next_due) VALUES (1, ?, 'tube check', 1500, ?)", (pm + "-09", (today + dt.timedelta(days=40)).isoformat()))
    a.execute("INSERT INTO xray_mark (kind, ref_id) VALUES ('machine', 1)")
    a.execute("INSERT INTO xray_mark (kind, ref_id) VALUES ('battery_place', 1)")
    a.execute("INSERT INTO battery_place VALUES (1, 'X-ray UPS', 12)")
    a.execute("INSERT INTO battery_place VALUES (2, 'Reception UPS', 12)")
    a.execute("INSERT INTO battery_fit (place_id, fitted_on, price, bill_id) VALUES (1, ?, 3200, NULL)", (pm + "-19",))
    a.execute("INSERT INTO battery_fit (place_id, fitted_on, price, bill_id) VALUES (2, ?, 2800, 4)", (pm + "-20",))
    a.execute("INSERT INTO stationery_line (day, side, amount) VALUES (?, 'clinic', 6350)", (pm + "-05",))
    a.execute("INSERT INTO stationery_line (day, side, amount) VALUES (?, 'nk', 1900)", (pm + "-05",))
    a.execute("INSERT INTO stationery_line (day, side, amount) VALUES (?, 'clinic', 50)", (pm + "-06",))
    a.commit()
    a.close()


def _first(ym):
    return dt.date(int(ym[:4]), int(ym[5:7]), 1)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    fin_dir = os.path.abspath(sys.argv[1])
    control = "--control" in sys.argv
    today = dt.date(2026, 11, 2)                                       # a made-up day: the 2nd of the running month
    now = dt.datetime(2026, 11, 2, 9, 30)
    ym, pm = "2026-11", "2026-10"
    tmp = tempfile.mkdtemp(prefix="walk_s696_")
    try:
        fdb, rdb, adb = os.path.join(tmp, "fin.db"), os.path.join(tmp, "register.db"), os.path.join(tmp, "assets.db")
        con = mk_finance(fdb, today)
        mk_register(rdb, pm, approved=False, locked=False, checked=True)
        mk_assets(adb, pm, ym, today)
        os.environ["FINANCE_DB"] = fdb
        # the module under test is the one IN fin_dir -- never the kit's own copy beside this script (sys.path[0])
        sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != os.path.dirname(os.path.abspath(__file__))]
        sys.path.insert(0, fin_dir)
        MR = None
        mr_path = os.path.join(fin_dir, "month_read.py")
        if os.path.exists(mr_path):
            import importlib.util                                      # noqa: PLC0415
            spec = importlib.util.spec_from_file_location("month_read", mr_path)
            MR = importlib.util.module_from_spec(spec)
            sys.modules["month_read"] = MR
            spec.loader.exec_module(MR)
            ok("month_read.py beside the console", True)
        else:
            ok("month_read.py beside the console", False, "no month_read.py in " + fin_dir)
        if MR is not None:
            env = dict(register=rdb, assets=adb)
            r = MR.read(con, env, now)
            ok("two months, ended then running", [m["state"] for m in r["months"]] == ["ended", "running"] and r["months"][0]["ym"] == pm)
            E, Rn = r["months"][0], r["months"][1]
            g = {x["key"]: x for x in E["groups"]}
            # 1 attendance
            a = g["att"]
            ok("att: entered green, checked green, approve amber with the action, lock grey",
               [x["dot"] for x in a["rows"]] == ["g", "g", "w", "n"] and a["act"] == "Approve & save" and a["act_href"].endswith(pm), str([x["dot"] for x in a["rows"]]))
            ok("att: the running month is all grey", all(x["dot"] == "n" for x in Rn["groups"][0]["rows"]))
            # 2 sanjeevni
            s = g["sanj"]
            ok("sanj: 4 of 5 days -> amber Approve", s["rows"][0]["dot"] == "w" and s["rows"][0]["act"] == "Approve", s["rows"][0]["text"])
            ok("sanj: purchases final -> green", s["rows"][1]["dot"] == "g", s["rows"][1]["text"])
            ok("sanj: pay sheet verified, no NEFT -> grey 'verified'", s["rows"][2]["dot"] == "n" and "verified" in s["rows"][2]["text"], s["rows"][2]["text"])
            ok("sanj: month not locked -> amber Check it", s["rows"][3]["dot"] == "w" and s["rows"][3]["act"] == "Check it")
            # 3 darpan (the month_jobs module is the estate's: on the made-up database it is 'not read' -- fail-soft -- or read)
            d = g["darpan"]
            ok("darpan: a reading or a said 'not read', never missing", d["n"] >= 1)
            papers = [x for x in d["rows"] if "paper" in x["text"].lower()]
            ok("darpan: one paper due within 45 days -> amber", bool(papers) and papers[0]["dot"] == "w" and "1 vehicle paper" in papers[0]["text"], str([x["text"] for x in d["rows"]]))
            # 5 petty + renewals
            p = g["petty"]
            ok("petty: Guard unpaid -> amber, Rahul not named", p["rows"][0]["dot"] == "w" and "Guard" in p["rows"][0]["text"] and "Rahul" not in p["rows"][0]["text"], p["rows"][0]["text"])
            ok("renewals: 1 due in the running month, the resolved one not counted", "1 renewal due" in Rn["groups"][4]["rows"][1]["text"], Rn["groups"][4]["rows"][1]["text"])
            # 6 pack: packs.py is the estate's; on a made-up database without its tables the piece is 'not read' or read -- fail-soft
            ok("pack: a line exists", g["pack"]["n"] >= 1)
            # 7 ipd
            ok("ipd: 1 case on record -> green line", g["ipd"]["rows"][1]["dot"] == "g" and "· 1 ·" in g["ipd"]["rows"][1]["text"], g["ipd"]["rows"][1]["text"])
            # revenue
            rv = E["revenue"]
            heads = {h["key"]: h for h in rv["heads"]}
            cl = heads["clinic"]
            rows = {x["label"]: x for x in cl["rows"]}
            ok("clinic: consultation 1,800 = cash 1,500 + UPI 300", rows["Consultation"]["total"] == 180000 and rows["Consultation"]["cash"] == 150000 and rows["Consultation"]["upi"] == 30000)
            ok("clinic: X-ray 1,200 all 'two ways'", rows["X-ray"]["two"] == 120000 and rows["X-ray"]["total"] == 120000)
            ok("clinic: procedures 350 card", rows["Procedures"]["card"] == 35000)
            ok("clinic: Other = total - three heads = 30", rows.get("Other", {}).get("total") == 3000)
            ok("clinic subtotal 3,380", cl["sub"]["total"] == 338000, str(cl["sub"]))
            ph = heads["physio"]
            ok("physio: in-clinic 1,000 (cash 800, UPI 200)", ph["sub"]["total"] == 100000 and ph["sub"]["cash"] == 80000)
            ok("physio: home visits 2, charged 1,000, received 700, kept apart", ph["home"] == dict(visits=2, charged=100000, received=70000) and ph["sub"]["total"] == 100000)
            sj = heads.get("sanj") or heads.get("unread") or {}
            ok("sanjeevni: the estate's month_rows read, or said not read", sj.get("sub") is not None or sj.get("why"), str(list(heads)))
            ok("grand total = clinic + sanjeevni + physio", rv["total"]["total"] == sum(h["sub"]["total"] for h in rv["heads"] if h.get("sub")))
            ok("cash share computed", rv["cash_pct"] is not None and 0 <= rv["cash_pct"] <= 100)
            # x-ray expenses
            x = E["xray"]
            f = {z["size"]: z for z in x["films"]}
            ok("film rate 8x10 = 10,800 / 150 = 72.00 from the last box", f["8×10"]["rate_p"] == 7200 and f["8×10"]["box_p"] == 1080000, str(f["8×10"]))
            ok("film rate 11x14 = 13,900 / 150 = 92.67", f["11×14"]["rate_p"] == 9267, str(f["11×14"]))
            fx = {z["label"]: z["amount_p"] for z in x["fixed"]}
            ok("AMC 36,000 over 12 months = 3,000; warranty not spread", any(k.endswith("AMC") and v == 300000 for k, v in fx.items()) and not any("Insurance" in k for k in fx))
            ok("service 1,500 on its day", any("service" in k and v == 150000 for k, v in fx.items()), str(fx))
            ok("battery 3,200 over 12 = 267 on the marked place only", any("battery" in k and v == 26667 for k, v in fx.items()) and sum(1 for k in fx if "battery" in k) == 1, str(fx))
            ok("expenses = films + fixed; margin = revenue - expenses", x["expense_p"] == sum(z["amount_p"] or 0 for z in x["films"]) + sum(fx.values()) and x["margin_p"] == x["revenue_p"] - x["expense_p"])
            # bought
            b = {z["k"]: z for z in E["bought"]["rows"]}
            ok("bought: 8x10 2 boxes = 21,600", b["X-ray films · 8×10"]["v"] == "₹21,600", str(b.get("X-ray films · 8×10")))
            ok("bought: 11x14 1 box = 13,900", b["X-ray films · 11×14"]["v"] == "₹13,900")
            ok("bought: clinic consumables 4,000, the second scan skipped", b.get("Clinic consumables", {}).get("v") == "₹4,000", str(b.keys()))
            ok("bought: 1 bill not laned -> 'lane not settled'", b.get("Bills not yet laned", {}).get("st") == "lane not settled")
            # supplies
            sp = {z["k"]: z for z in E["supplies"]["rows"]}
            st = sp["Stationery · the challans"]
            ok("supplies: 2 clinic lines 6,400 and 1 NK line 1,900; statement not made", "clinic 2 lines ₹6,400" in st["sub"] and "NK Pathology 1 line ₹1,900" in st["sub"] and st["cls"] == "w", st["sub"] + " | " + st["st"])
            bt = sp["Batteries fitted or replaced"]
            ok("supplies: 2 batteries, 6,000, 1 bill awaited", bt["sub"] == "2 this month" and bt["v"] == "₹6,000" and bt["st"] == "1 bill awaited", str(bt))
            ok("supplies: machines 1 serviced, 1 added", sp["Machines"]["sub"] == "1 serviced · 1 added this month", sp["Machines"]["sub"])
            # summary and section lines
            sm = E["summary"]
            ok("summary counts add up", sm["done"] + sm["yours"] + sm["waiting"] <= sm["n"] and sm["yours"] >= 4)
            ok("pack due the 10th of the next month", sm["pack_due"] == "2026-11-10")
            sl = MR.section_lines(r)
            ok("section lines: the ended month first, amber, the page's address with the month", sl[0]["dot"] == "w" and sl[0]["href"].endswith("#2026-10"), str(sl[0]))
            ok("section lines: one line per group that needs him", sum(1 for l in sl if l.get("sub")) == sm_groups_yours(E))
            ok("running month: revenue so far 300 (one day)", Rn["summary"]["revenue_p"] == 30000, str(Rn["summary"]["revenue_p"]))
            # no name, no clinic ID anywhere in the reading (the rows carry none; this is the guard)
            blob = json.dumps(r, ensure_ascii=False)
            ok("no patient field in the reading", "patient" not in blob.lower() and "clinic_id" not in blob)
            # fail-soft: no register, no assets
            r2 = MR.read(con, dict(register="/nonexistent", assets="/nonexistent"), now)
            ok("fail-soft: the staff register absent -> 'not read' line, the page still whole", r2["months"][0]["groups"][0]["rows"][0]["text"].endswith("not read") and len(r2["months"][0]["groups"]) == 7)
            ok("fail-soft: the Scan App absent -> films 'no bill ... read yet', fixed costs said", r2["months"][0]["xray"]["films"][0]["rate_p"] is None and r2["months"][0]["xray"].get("fixed_unread"))
            # ---- mutants: a changed input must change the reading
            mk_register(rdb, pm, approved=True, locked=False)
            m1 = MR.read(con, env, now)["months"][0]["groups"][0]
            mut("M1 approved -> the lock becomes the amber action", m1["act"] == "Lock" and m1["rows"][2]["dot"] == "g")
            mk_register(rdb, pm, approved=True, locked=True)
            m2 = MR.read(con, env, now)["months"][0]["groups"][0]
            mut("M2 locked -> all four green, no action", all(x["dot"] == "g" for x in m2["rows"]) and m2["act"] is None)
            con.execute("UPDATE day_entry SET status='locked'")
            m3 = MR.read(con, env, now)["months"][0]["groups"][1]
            mut("M3 every day locked -> the month line green", m3["rows"][3]["dot"] == "g" and m3["rows"][0]["dot"] == "g")
            con.execute("INSERT INTO purchase_neft_event (month, kind) VALUES (?, 'ok')", (pm,))
            m4 = MR.read(con, env, now)["months"][0]["groups"][1]
            mut("M4 NEFT event -> vendor payments green", m4["rows"][2]["dot"] == "g")
            con.execute("INSERT INTO petty_entry (entry_date, kind, party, amount_p) VALUES (?, 'pay', 'guard', 300000)", (pm + "-29",))
            m5 = MR.read(con, env, now)["months"][0]["groups"][4]
            mut("M5 Guard paid -> petty green with both names", m5["rows"][0]["dot"] == "g" and "Guard" in m5["rows"][0]["text"] and "Rahul" in m5["rows"][0]["text"])
            con.execute("INSERT INTO pack_send (month, sent_at, sent_by) VALUES (?, ?, 'manoj')", (pm, ym + "-05T10:00:00"))
            m6 = MR.read(con, env, now)["months"][0]
            mut("M6 pack sent -> summary says so", m6["summary"]["pack_sent"] is True)
            con.execute("UPDATE xf_purchase SET held=1 WHERE src LIKE 'bill:7:%'")
            m7 = MR.read(con, env, now)["months"][0]["xray"]
            mut("M7 the last 8x10 bill HELD -> the rate falls back to the older box (9,000/150 = 60)", {z["size"]: z for z in m7["films"]}["8×10"]["rate_p"] == 6000)
            con.execute("UPDATE clinic_day_line SET mode='Wallet' WHERE section='consult' AND mode='Online Payment'")
            m8 = MR.read(con, env, now)["months"][0]["revenue"]
            mut("M8 Wallet counts as UPI (his ruling: Razorpay to the bank)", {x["label"]: x for x in [h for h in m8["heads"] if h["key"] == "clinic"][0]["rows"]}["Consultation"]["upi"] == 30000)
        # ---- the console's own builder on the made-up database, with the S696 section
        oc = os.path.join(fin_dir, "owner_console.py")
        snap = os.path.join(tmp, "snap.dat")
        envb = dict(os.environ, CONSOLE_REGISTER_DB=rdb, CONSOLE_ASSETS_DB=adb, DUTY_MAP_JSON="/nonexistent", CONSOLE_FRESHNESS="/nonexistent",
                    CONSOLE_BEAT="/nonexistent", TMPDIR=os.environ.get("WALK_TMPDIR", tmp), PYTHONPATH=os.environ.get("PYTHONPATH", ""))
        con.commit()
        con.close()
        pr = subprocess.run([sys.executable, "-B", oc, "--build", "--db", fdb, "--out", snap, "--lock", snap + ".lock"], cwd=fin_dir, env=envb,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=170)
        okb = pr.returncode == 0 and os.path.exists(snap)
        ok("the console builder runs whole on the made-up database", okb, pr.stdout.decode("utf-8", "replace")[-300:])
        if okb:
            s = json.load(open(snap, encoding="utf-8"))
            ok("the snapshot carries the section 'month' second in ORDER", s["order"][:2] == ["needs", "month"], str(s["order"]))
            ok("the section 'The month' is read, not failed", "month" not in s["failed"] and s["sections"].get("month", {}).get("ok") is True)
            ok("the snapshot carries the whole month reading for the page", bool(s.get("month")) and len(s["month"]["months"]) == 2)
            ok("VERSION S696 1.4", s.get("version") == "S696 1.4", str(s.get("version")))
        page = os.path.join(fin_dir, "month_page.html")
        ok("month_page.html beside the console, fetches /finance/console/api/month", os.path.exists(page) and "/finance/console/api/month" in open(page, encoding="utf-8").read())
        src = open(oc, encoding="utf-8").read()
        ok("the two routes are in owner_console.py", "/finance/console/month" in src and "/finance/console/api/month" in src and "def sec_month" in src)
        import re                                                      # noqa: PLC0415
        ok("the names the new routes use exist in owner_console.py", all(re.search(r"^    def %s\(" % n, src, re.M) for n in ("_state", "_gate")) and
           re.search(r"^def _label\(", src, re.M) and "MAX_AGE" in src and "jsonify" in src and "failed=s.get" in src)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_ok = sum(1 for _n, c, _w in CHECKS if c)
    n_m = sum(1 for _n, c in MUT if c)
    print("\nWALK S696: %d of %d green · mutants caught %d of %d · %s" % (n_ok, len(CHECKS), n_m, len(MUT), "CONTROL run (reds expected on the live console)" if control else ""))
    if control:
        reds = len(CHECKS) - n_ok
        print("CONTROL: %d red" % reds)
        return 0 if reds >= 3 else 1
    return 0 if (n_ok == len(CHECKS) and n_m == len(MUT)) else 1


def sm_groups_yours(E):
    return sum(1 for g in E["groups"] if g["yours"])


if __name__ == "__main__":
    sys.exit(main())
