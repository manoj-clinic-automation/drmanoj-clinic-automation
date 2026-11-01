#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s697.py -- S697_MONTH_CONSOLE_R2: the walk on MADE-UP databases (never a patient; never the live files).

Carries S696's 53 checks (three rewritten by design: bought narrowed to the room groups, the unsorted bills under Other papers,
VERSION S697 1.5) and adds one or more per S697 change: the IPD line from S682's own column (c), "due since" (d), Other papers and the
pharmacy scans (e), the month chips and no second link (b), the Sanjeevni section's pages with figures and the one Marg-reports
line (h), TARGET_DOOR's expiry and ?old=1 doors, the fig field, the page's tinted lines and bars (a, i), the film log's no-count day
and the month named (g).

usage: python3 walk_s697.py <finance dir with month_read.py and the estate's modules> [--control]
  --control  runs the same checks against a finance dir WITHOUT S697 (the live files): the S697 checks must go RED.

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
    -- S697: S682's implant bills (voided_at, as its CREATE line), the review queue, the stock check, Darpan's corrections, the scan links
    CREATE TABLE surg_implant_bill(id INTEGER PRIMARY KEY, implant_id INT, case_id INT, vendor_id INT, bill_no TEXT, bill_day TEXT, amount_p INT, bill_to TEXT, note TEXT, by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT '');
    CREATE TABLE recon_exception(id INTEGER PRIMARY KEY, unit TEXT, kind TEXT, status TEXT);
    CREATE TABLE stock_diff(id INTEGER PRIMARY KEY, item TEXT, status TEXT);
    CREATE TABLE upi_match(id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, status TEXT, bill_no TEXT, txn_amount_p INT, rrn TEXT, resolution TEXT, resolved TEXT);
    CREATE TABLE darpan_correction(id INTEGER PRIMARY KEY, match_id INT, ticked_by TEXT, ticked_at TEXT, note TEXT);
    CREATE TABLE purchase_scan_link(id INTEGER PRIMARY KEY, bill_id INT, asset_bill_id INT, grade TEXT);
    """)
    c.execute("INSERT INTO surg_implant_bill (implant_id, case_id, vendor_id, bill_no, bill_day, amount_p, bill_to) VALUES (1, 1, 1, 'B1', ?, 1200000, 'patient')", (pm + "-20",))
    c.execute("INSERT INTO surg_implant_bill (implant_id, case_id, vendor_id, bill_no, bill_day, amount_p, bill_to, voided_at) VALUES (1, 1, 1, 'B2', ?, 1200000, 'patient', '2026-10-21T10:00:00')", (pm + "-20",))
    c.execute("INSERT INTO recon_exception (unit, kind, status) VALUES ('medical', 'return_flagged', 'open')")
    c.execute("INSERT INTO recon_exception (unit, kind, status) VALUES ('medical', 'upi_vs_statement', 'open')")
    c.execute("INSERT INTO recon_exception (unit, kind, status) VALUES ('medical', 'upi_vs_statement', 'resolved')")
    c.execute("INSERT INTO stock_diff (item, status) VALUES ('ZZ-MADE-UP', 'open')")
    c.execute("INSERT INTO stock_diff (item, status) VALUES ('ZZ-MADE-UP-2', 'closed')")
    c.execute("INSERT INTO upi_match (unit, business_date, status, bill_no, txn_amount_p) VALUES ('medical', ?, 'cash', 'X1', 50000)", (ym + "-01",))
    c.execute("INSERT INTO upi_match (unit, business_date, status, bill_no, txn_amount_p) VALUES ('medical', ?, 'cash', 'X2', 50000)", (ym + "-01",))
    c.execute("INSERT INTO upi_match (unit, business_date, status, bill_no, txn_amount_p) VALUES ('medical', ?, 'cash', 'X0', 50000)", (pm + "-01",))   # last month: not this month's count
    c.execute("INSERT INTO darpan_correction (match_id, ticked_by, ticked_at) VALUES (2, 'darpan', ?)", (ym + "-02T09:00:00",))
    c.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade) VALUES (501, 21, 'A')")
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
    CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, subgroup TEXT, status TEXT, dup_of INT, created_at TEXT, lane TEXT, bill_month TEXT);
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
    a.execute("INSERT INTO bills VALUES (5, 'Consumable', 'Jugnu', 'J5', '2026-08-02', 9000, 'xray_8x10', '', NULL, '2026-08-02 10:00:00', 'clinic', NULL)")
    a.execute("INSERT INTO bills VALUES (7, 'Consumable', 'Jugnu', 'J7', ?, 21600, 'xray_8x10', '', NULL, '2026-10-12 10:00:00', 'clinic', NULL)", (pm + "-12",))
    a.execute("INSERT INTO bills VALUES (8, 'Consumable', 'Jugnu', 'J8', ?, 13900, 'xray_11x14', '', NULL, '2026-10-27 10:00:00', 'clinic', NULL)", (pm + "-27",))
    a.execute("INSERT INTO bills VALUES (9, 'Consumable', 'Plaster Co', 'P9', ?, 4000, 'procedure', '', NULL, '2026-10-20 10:00:00', 'clinic', NULL)", (pm + "-20",))
    a.execute("INSERT INTO bills VALUES (10, 'Consumable', 'Someone', 'S10', ?, 700, '', '', NULL, '2026-10-21 10:00:00', 'clinic', NULL)", (pm + "-21",))      # not sorted
    a.execute("INSERT INTO bills VALUES (11, 'Consumable', 'Dup', 'D11', ?, 999, 'procedure', '', 9, '2026-10-22 10:00:00', 'clinic', NULL)", (pm + "-22",))  # a second scan: skipped
    a.execute("INSERT INTO bills VALUES (12, 'Consumable', 'Paper Co', 'P12', ?, 1500, 'stationery', '', NULL, '2026-10-23 10:00:00', 'clinic', NULL)", (pm + "-23",))
    a.execute("INSERT INTO bills VALUES (13, 'Consumable', 'Mason', 'M13', ?, 25000, 'construction', '', NULL, '2026-10-24 10:00:00', 'clinic', NULL)", (pm + "-24",))   # a section: Other papers
    a.execute("INSERT INTO bills VALUES (14, 'Lab', 'Reagent Co', 'R14', ?, 8000, '', '', NULL, '2026-10-25 10:00:00', 'lab_purchase', NULL)", (pm + "-25",))        # NK's lane
    a.execute("INSERT INTO bills VALUES (15, 'Expense', 'Shop', 'E15', ?, 3000, '', '', NULL, '2026-10-26 10:00:00', 'owner_expense', NULL)", (pm + "-26",))
    a.execute("INSERT INTO bills VALUES (21, 'Pharmacy', 'Kedar', 'K21', ?, 9999, '', 'captured', NULL, '2026-10-05 10:00:00', 'pharmacy', NULL)", (pm + "-05",))   # paired (link 21)
    a.execute("INSERT INTO bills VALUES (22, 'Pharmacy', 'Kedar', 'K22', ?, 8888, '', 'captured', NULL, '2026-10-06 10:00:00', NULL, NULL)", (pm + "-06",))          # lane by kind; waiting
    a.execute("INSERT INTO bills VALUES (23, 'Pharmacy', 'Kedar', 'K23', ?, 7777, '', 'rejected', NULL, '2026-10-07 10:00:00', 'pharmacy', NULL)", (pm + "-07",))   # rejected: never counted
    a.execute("INSERT INTO bills VALUES (24, 'Consumable', 'Late', 'L24', '2026-09-28', 600, 'others', '', NULL, '2026-10-02 10:00:00', 'clinic', ?)", (pm,))      # bill_month wins over the bill date
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
    tmp = tempfile.mkdtemp(prefix="walk_s697_")
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
        try:                                                           # S697 (d): the month jobs' own tables and one home-medicines item, no count saved
            import month_jobs as MJ0                                   # noqa: PLC0415 -- the estate's module in fin_dir
            MJ0.ensure(con)
            con.execute("INSERT INTO mj_home_item (name, unit, need, active, added_at, added_by) VALUES ('ZZ made-up tablet', 'strip', 2, 1, '2026-10-01T10:00:00', 'walk')")
            con.commit()
        except Exception as e:                                         # noqa: BLE001
            ok("S697: the month jobs' tables made on the made-up database", False, "%s: %s" % (type(e).__name__, e))
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
            ok("ipd: 1 case on record -> green line", at(g["ipd"]["rows"], 1).get("dot") == "g" and "· 1 ·" in at(g["ipd"]["rows"], 1).get("text", ""), str(at(g["ipd"]["rows"], 1)))
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
            # S697 (e): bought = films + the three room groups only; the sections, the other lanes, the unsorted and the pharmacy scans under Other papers
            ok("S697 bought: procedure room 4,000, the second scan skipped; stationery 1,500; Others 600 by its bill_month", b.get("Procedure room", {}).get("v") == "₹4,000" and b.get("Stationery & packaging", {}).get("v") == "₹1,500" and b.get("Others", {}).get("v") == "₹600", str(b.keys()))
            ok("S697 bought: no section, no other lane, no unsorted, no pharmacy line in bought", not any(k in b for k in ("Construction work", "Bills not yet laned", "Clinic bills not yet sorted into a group", "Pharmacy bills scanned", "NK Pathology purchases")), str(b.keys()))
            ok("S697 bought: total = 21,600 + 13,900 + 4,000 + 1,500 + 600", E["bought"]["total_p"] == 4160000, str(E["bought"]["total_p"]))
            ok("S697 bought: the room group links open the Scan App's month page for that group", b.get("Procedure room", {}).get("href") == "/scanapp/papers/month?ym=%s&g=procedure" % pm)
            o = {z["k"]: z for z in E.get("others", {"rows": []})["rows"]}
            ok("S697 others: construction 25,000 as a section line with its month link", o.get("Construction work", {}).get("v") == "₹25,000" and o.get("Construction work", {}).get("href") == "/scanapp/papers/month?ym=%s&g=construction" % pm, str(o.keys()))
            ok("S697 others: NK Pathology's lane 8,000 and the personal-expense lane 3,000", o.get("NK Pathology purchases", {}).get("v") == "₹8,000" and o.get("Personal expenses", {}).get("v") == "₹3,000")
            ok("S697 others: 1 clinic bill not sorted -> amber 'group not settled', link to g=unsorted", o.get("Clinic bills not yet sorted into a group", {}).get("cls") == "w" and o.get("Clinic bills not yet sorted into a group", {}).get("href", "").endswith("g=unsorted"))
            ph = o.get("Pharmacy bills scanned", {})
            ok("S697 others: pharmacy 2 scanned (the rejected one never), 1 paired with Marg, 1 waiting; rupees never shown as a sum", ph.get("sub") == "2 scanned · 1 paired with Marg · 1 waiting" and ph.get("v") == "rupees in Marg" and ph.get("cls") == "w", str(ph))
            ok("S697 others: the chip counts papers (1+1+1+1+2 = 6), never adds rupees", E.get("others", {}).get("n_bills") == 6, str(E.get("others", {}).get("n_bills")))
            ok("S697 others: no 'Other papers' lines in the running month but the pharmacy line (none scanned)", {z["k"] for z in Rn.get("others", {"rows": [{"k": "?"}]})["rows"]} <= {"Other papers", "Pharmacy bills scanned"}, str([z["k"] for z in Rn.get("others", {"rows": []})["rows"]]))
            # S697 (c): the IPD line from S682's own table -- 2 bills, 1 voided -> 1
            ok("S697 ipd: implant bills counted by voided_at -> '1 bill', never 'not read'", "1 bill" in at(g["ipd"]["rows"], 1).get("text", "") and "not read" not in at(g["ipd"]["rows"], 1).get("text", ""), str(at(g["ipd"]["rows"], 1)))
            # S697 (d): the home-medicines count due and not made -> 'due since 25 Oct' on the ended month
            hm = next((x for x in g["darpan"]["rows"] if "Home medicines" in x["text"]), None)
            ok("S697 darpan: home medicines due and not counted -> 'due since 25 Oct'", hm is not None and "due since 25 Oct" in hm["text"] and "opens" not in hm["text"], str(hm))
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
            # S697 mutants
            con.execute("UPDATE surg_implant_bill SET voided_at='2026-10-22T10:00:00' WHERE bill_no='B1'")
            m9 = MR.read(con, env, now)["months"][0]["groups"][6]
            mut("M9 the other implant bill voided -> '0 bills'", "0 bills" in at(m9["rows"], 1).get("text", ""), str(at(m9["rows"], 1)))
            con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade) VALUES (502, 22, 'B')")
            m10 = {z["k"]: z for z in MR.read(con, env, now)["months"][0].get("others", {"rows": []})["rows"]}.get("Pharmacy bills scanned", {})
            mut("M10 the second scan linked -> 2 paired, 0 waiting, the line calm", m10.get("sub") == "2 scanned · 2 paired with Marg · 0 waiting" and m10.get("cls") == "", str(m10))
            con.execute("INSERT INTO mj_home_count (month, saved_at, saved_by) VALUES ('2026-11', '2026-10-28T10:00:00', 'darpan')")
            m11 = next((x for x in MR.read(con, env, now)["months"][0]["groups"][2]["rows"] if "Home medicines" in x["text"]), None)
            mut("M11 the count saved -> 'counted for November', green", m11 is not None and m11["dot"] == "g" and "counted" in m11["text"], str(m11))
            a2 = sqlite3.connect(adb); a2.execute("UPDATE bills SET subgroup='procedure' WHERE id=10"); a2.commit(); a2.close()
            m12 = MR.read(con, env, now)["months"][0]
            mut("M12 the unsorted bill sorted -> no amber unsorted line; procedure room 4,700", not any(z["k"].startswith("Clinic bills not yet sorted") for z in m12.get("others", {"rows": []})["rows"]) and {z["k"]: z for z in m12["bought"]["rows"]}.get("Procedure room", {}).get("v") == "₹4,700")
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
            ok("VERSION S697 1.5", s.get("version") == "S697 1.5", str(s.get("version")))
            # S697 (b): the month chips on the bar, no second link to the page
            mo = s["sections"].get("month", {})
            ok("S697 month: two chips October · November, each the page on that month", [c["t"] for c in mo.get("chips", [])] == ["October", "November"] and at(mo.get("chips", []), 0).get("href") == "/finance/console/month#2026-10" and at(mo.get("chips", []), 1).get("state") == "running", str(mo.get("chips")))
            ok("S697 month: no second link to the page (the 'on one page' line gone)", not any("on one page" in (l.get("text") or "") for l in mo.get("lines", [])))
            ok("S697 month: the ended month's line first, the running month's line second, then October's groups", len(mo.get("lines", [])) >= 3 and mo["lines"][0]["href"].endswith("#2026-10") and mo["lines"][1]["href"].endswith("#2026-11") and mo["lines"][2].get("sub") is True, str([l["href"] for l in mo["lines"][:3]]))
            # S697 (h): the Sanjeevni section's pages with their figures, then ONE Marg-reports line
            sj = s["sections"].get("sanj", {})
            sl = {(l.get("link") or ""): l for l in sj.get("lines", [])}
            ok("S697 sanj: the purchase-orders line opens ?old=1 and carries a figure", sl.get("purchase orders", {}).get("href") == "/finance/porders?old=1" and "fig" in sl.get("purchase orders", {}), str(sl.get("purchase orders")))
            ok("S697 sanj: review queue 2 exceptions open (the resolved one not counted; every day locked by M3), amber", sl.get("review queue", {}).get("fig") == "2" and sl.get("review queue", {}).get("dot") == "w", str(sl.get("review queue")))
            ok("S697 sanj: stock check 1 difference open, amber", sl.get("stock check", {}).get("fig") == "1" and sl.get("stock check", {}).get("dot") == "w", str(sl.get("stock check")))
            ok("S697 sanj: corrections 1 not ticked this month (the ticked one and last month's not counted), amber", sl.get("corrections", {}).get("fig") == "1" and sl.get("corrections", {}).get("dot") == "w", str(sl.get("corrections")))
            ok("S697 sanj: the expiry watch line is there (a reading or said not read), grey at 0", (sl.get("expiry watch", {}).get("href") == "/finance/sanjeevni/expiry") or any("expiry watch could not be read" in (l.get("text") or "") for l in sj.get("lines", [])), str(sl.get("expiry watch")))
            rp = sl.get("Aaj ki reports")
            ok("S697 sanj: ONE Marg-reports line with its details table, STOCK_EXPIRY never listed", rp is not None and rp.get("table") and not any("expiry" in (r[0] or "").lower() and "stock" in (r[0] or "").lower() for r in rp["table"]["rows"]) and sum(1 for l in sj.get("lines", []) if (l.get("link") or "") == "Aaj ki reports") == 1, str(rp)[:300])
            ok("S697 sanj: the order -- the Needs-you lines first, then purchase orders, review, expiry, stock, corrections, reports", [l.get("link") for l in sj.get("lines", []) if l.get("link") in ("purchase orders", "review queue", "expiry watch", "stock check", "corrections", "Aaj ki reports")] == ["purchase orders", "review queue", "expiry watch", "stock check", "corrections", "Aaj ki reports"], str([l.get("link") for l in sj.get("lines", [])]))
            ok("S697 sanj: the chip says what needs him (open lines and/or reports due)", bool(sj.get("chip")) and (("report" in sj["chip"]) or ("open" in sj["chip"]) or sj["chip"] == "clear"), str(sj.get("chip")))
            ok("S697 sanj: every staff screen left out (his word)", not any((l.get("href") or "") in ("/finance/darpan/kal", "/finance/salecheck", "/finance/returns/desk", "/finance/amir") for l in sj.get("lines", []) if (l.get("link") or "") in ("purchase orders", "review queue", "expiry watch", "stock check", "corrections", "Aaj ki reports")))
            ok("S697: every line still has a dot word the page tints by", all((l.get("dot") in ("g", "w", "b", "n")) for sec in s["sections"].values() for l in sec.get("lines", [])))
        if okb:                                                        # S697 builder-level mutants: a changed table changes the section's figure
            c2 = sqlite3.connect(fdb); c2.execute("UPDATE stock_diff SET status='closed'"); c2.execute("INSERT INTO darpan_correction (match_id, ticked_by, ticked_at) VALUES (1, 'darpan', '2026-11-02T09:30:00')"); c2.execute("UPDATE recon_exception SET status='resolved'"); c2.execute("UPDATE day_entry SET status='approved' WHERE status='submitted'"); c2.commit(); c2.close()
            pr2 = subprocess.run([sys.executable, "-B", oc, "--build", "--db", fdb, "--out", snap, "--lock", snap + ".lock"], cwd=fin_dir, env=envb, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=170)
            s2 = json.load(open(snap, encoding="utf-8")) if pr2.returncode == 0 else {"sections": {}}
            sl2 = {(l.get("link") or ""): l for l in s2["sections"].get("sanj", {}).get("lines", [])}
            mut("M13 the difference closed, the correction ticked, the review resolved -> stock 0, corrections 0, review 0, all green",
                sl2.get("stock check", {}).get("fig") == "0" and sl2.get("stock check", {}).get("dot") == "g" and sl2.get("corrections", {}).get("fig") == "0" and sl2.get("corrections", {}).get("dot") == "g"
                and sl2.get("review queue", {}).get("fig") == "0" and sl2.get("review queue", {}).get("dot") == "g", str([sl2.get(k) for k in ("stock check", "corrections", "review queue")]))
        page = os.path.join(fin_dir, "month_page.html")
        ok("month_page.html beside the console, fetches /finance/console/api/month", os.path.exists(page) and "/finance/console/api/month" in open(page, encoding="utf-8").read())
        src = open(oc, encoding="utf-8").read()
        ok("the two routes are in owner_console.py", "/finance/console/month" in src and "/finance/console/api/month" in src and "def sec_month" in src)
        import re                                                      # noqa: PLC0415
        ok("the names the new routes use exist in owner_console.py", all(re.search(r"^    def %s\(" % n, src, re.M) for n in ("_state", "_gate")) and
           re.search(r"^def _label\(", src, re.M) and "MAX_AGE" in src and "jsonify" in src and "failed=s.get" in src)
        # S697: the doors, the fig field, the page's look, the film log
        ok("S697 TARGET_DOOR: expiry -> the expiry page, porders -> the owner's ?old=1 page", '"expiry": "/finance/sanjeevni/expiry"' in src and '"porders": "/finance/porders?old=1"' in src)
        ok("S697 L() carries fig", "fig=None" in src and '("fig", str(fig)' in src)
        html = open(os.path.join(fin_dir, "owner_console.html"), encoding="utf-8").read()
        ok("S697 page: the line is tinted by its dot word (amber, rose), the figure bold at the end, the dot not drawn", ".line.w{background:var(--warn-soft)" in html and ".line.b{background:var(--bad-soft)" in html and "el('b','fig'" in html and ".dot{display:none}" in html)
        ok("S697 page: the bars as the month page's -- uppercase label, the pill tinted, accent bar and summary when open", "text-transform:uppercase" in html and ".cnt.w{color:var(--warn-ink);background:var(--warn-soft)}" in html and "details.sec[open]>summary{background:var(--accent)" in html and "details.sec[open]{box-shadow:inset 3px 0 0 var(--accent)" in html)
        ok("S697 page: the month chips drawn on the bar, a tap on a chip never toggles the bar", "x.chips" in html and "mchip" in html and "ev.stopPropagation()" in html)
        ok("S697 page: a fill still re-tints its line", "the tint follows the fill" in html)
        mp = open(page, encoding="utf-8").read() if os.path.exists(page) else ""
        ok("S697 month page: the section Other papers of the month under Bought, its chip counts papers", "othersHTML" in mp and "Other papers of the month" in mp and "boughtHTML(m)+othersHTML(m)+suppliesHTML(m)" in mp)
        xf = open(os.path.join(fin_dir, "xray_film.py"), encoding="utf-8").read()
        ok("S697 film log: a no-count day shows that day's slip films; 'Mornings not counted' names the month", "S697 (F-1080c)" in xf and "sf = slip_films(con, _d(r[\"day\"]), _d(r[\"day\"]))" in xf and '"Mornings not counted in %s:" % mname(ym, lang)' in xf)
        ok("S697 film log: xray_film.py compiles", subprocess.run([sys.executable, "-B", "-m", "py_compile", os.path.join(fin_dir, "xray_film.py")], env=dict(os.environ, PYTHONPYCACHEPREFIX=tmp), stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode == 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    n_ok = sum(1 for _n, c, _w in CHECKS if c)
    n_m = sum(1 for _n, c in MUT if c)
    print("\nWALK S697: %d of %d green · mutants caught %d of %d · %s" % (n_ok, len(CHECKS), n_m, len(MUT), "CONTROL run (reds expected on the live console)" if control else ""))
    if control:
        reds = len(CHECKS) - n_ok
        print("CONTROL: %d red" % reds)
        return 0 if reds >= 20 else 1
    return 0 if (n_ok == len(CHECKS) and n_m == len(MUT)) else 1


def at(rows, i):
    """The i-th row or {} -- the control run on the live files must never crash on a shorter list (F-1079 shows as one row)."""
    return rows[i] if i < len(rows) else {}


def sm_groups_yours(E):
    return sum(1 for g in E["groups"] if g["yours"])


if __name__ == "__main__":
    sys.exit(main())
