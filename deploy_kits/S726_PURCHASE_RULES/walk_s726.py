#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s726.py -- S726_PURCHASE_RULES: the walk, on made-up rows in a scratch finance.db and a scratch assets.db built in a temp folder of
its own (never the live paths: purchase_app is pointed at the scratch assets.db through its own init(assets_db=...)).  No network.

    python3 -B walk_s726.py <dir holding scan_register.py, purchase_app.py, porders.py, purchase_schema.sql>

Run on the TO files: every check green.  Run on the FROM (live) files: the S726 checks go red (the CONTROL) -- a walk that stays green on
the old files proves nothing.  With S726_WALK_SEED_ONLY=<dir> it only writes the seeded finance.db / assets.db there (before any pass) and
stops: the installer's rehearsal runs the proof on them.
"""
import hashlib
import os
import re
import shutil
import sqlite3
import sys
import tempfile

SRC = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
TMP = tempfile.mkdtemp(prefix="walk_s726_")
os.environ["ORDER_TODAY"] = "2026-11-06"
os.environ["SHARED_LIB_DIR"] = os.path.join(TMP, "no_shared")     # never the box's /root/shared
os.environ.pop("ASSETS_DB", None)
os.environ.pop("FINANCE_DB", None)
for n in ("scan_register.py", "purchase_app.py", "porders.py"):
    shutil.copy(os.path.join(SRC, n), os.path.join(TMP, n))
# purchase_app's schema file: beside the files, else S726_SCHEMA_DIR, else the live folder, else beside this walk
_sch = [os.path.join(d, "purchase_schema.sql") for d in (SRC, os.environ.get("S726_SCHEMA_DIR") or SRC, "/root/finance",
                                                         os.path.dirname(os.path.abspath(__file__)))]
_sch = [x for x in _sch if os.path.isfile(x)]
if not _sch:
    print("walk_s726: purchase_schema.sql is not beside %s (nor in S726_SCHEMA_DIR or /root/finance) -- cannot walk" % SRC)
    print("walk_s726: 1 check(s) failed (1 of them S726 checks)")
    sys.exit(1)
shutil.copy(_sch[0], os.path.join(TMP, "purchase_schema.sql"))
sys.path.insert(0, TMP)
FDB = os.path.join(TMP, "finance.db")
ADB = os.path.join(TMP, "assets.db")

import warnings                                                       # noqa: E402
warnings.simplefilter("ignore")
import purchase_app as PA                                             # noqa: E402
import scan_register as SR                                            # noqa: E402
import porders as PO                                                  # noqa: E402

FAILS, S726 = [], []


def ck(name, cond, s726=True):
    print(("  ok   " if cond else "  FAIL ") + ("[S726] " if s726 else "") + name)
    if not cond:
        FAILS.append(name)
        if s726:
            S726.append(name)


# ---------------------------------------------------------------------------------------------------------------- the made-up rows
SUP = {"K": "KEDAR PHARMA DISTRIBUTORS", "A": "AA AGENCIES", "B": "BASS HEALTHCARE", "S": "SHIVAAZ PHARMA", "G": "GUNINA LIFESCIENCES",
       "N": "NANDI DRUG HOUSE", "D": "DEEPAM DRUG HOUSE", "U": "SHRADDHA SURGICALS", "P": "SEPTIMUS TRADERS", "Q": "UNIQUE PHARMA",
       "W": "WINDSOR REMEDIES", "F": "FRESHCO PHARMA", "O": "ORION PHARMA", "R": "ROUNDWELL PHARMA", "V": "VEGA PHARMA",
       "Y": "YASHODA SURGICALS", "H": "HARBOR MEDICALS AGENCIES", "E": "EVEREST LIFESCIENCES", "L": "LOTUS REMEDIES",
       "M": "MERIDIAN SURGICALS", "C": "NOVACARE HEALTH", "T": "TULSI AGENCIES"}
# bill key: (supplier, bill_no, date, rupees)
BILLS = {
    "K1": ("K", "A000213", "2026-10-08", 7400), "K2": ("K", "A000190", "2026-10-02", 7400), "K3": ("K", "A000201", "2026-10-05", 7400),
    "K4": ("K", "A000223", "2026-10-20", 7400),
    "A1": ("A", "415", "2026-09-18", 5000),
    "B1": ("B", "14538", "2026-09-20", 1597),
    "S1": ("S", "3688", "2026-10-10", 7978), "G1": ("G", "81974", "2026-10-11", 12973),
    "N1": ("N", "555", "2026-10-12", 5000), "R1": ("R", "77", "2026-10-13", 1000),
    "D1": ("D", "641", "2026-10-15", 4751),
    "U1": ("U", "10480", "2026-10-03", 3000),
    "P1": ("P", "777", "2026-09-10", 2200), "P2": ("P", "778", "2026-09-12", 2200),
    "Q1": ("Q", "901", "2026-10-22", 3333), "Q2": ("Q", "905", "2026-10-25", 4444),
    "W1": ("W", "300", "2026-10-30", 1234),
    "F1": ("F", "450", "2026-11-04", 2500),
    "O1": ("O", "1201", "2026-10-18", 1000),
    "Z1": ("O", "1300", "2026-11-05", 999),
    "X1": ("O", "1400", "2026-10-19", 2000),
    "V1": ("V", "61", "2026-09-15", 2000), "Y1": ("Y", "62", "2026-09-16", 1500), "E1": ("E", "63", "2026-09-17", 3000),
    "H1": ("H", "70", "2026-09-05", 900), "H2": ("H", "71", "2026-09-20", 900),
    "L0": ("L", "213", "2025-10-08", 500),                                        # a year-old bill with the same number and day
    "M1": ("M", "A000213", "2026-10-09", 800), "M2": ("M", "B/213", "2026-10-09", 650),   # two series of one supplier on one day
    "C1": ("C", "888", "2026-10-14", 3000),
    "T1": ("T", "40", "2026-08-20", 700),                                         # August is final: its link is never changed
}
# scan key: (id, stamp, supplier read, bill no read, date read, total read, created_at UTC)
SCANS = {
    "sK2": (150, "B-0150", "K", "A000190", "2026-10-02", "7400", "2026-10-03 05:00:00"),
    "sK3": (155, "B-0155", "K", "A000201", "2026-10-05", "7400", "2026-10-06 05:00:00"),
    "sK1": (161, "B-0161", "K", "A000213", "2026-10-08", "7400", "2026-10-09 05:00:00"),
    "sK4": (202, "B-0202", "K", "A000223", "2026-10-20", "7400", "2026-10-21 05:00:00"),
    "sA": (224, "B-0224", "A", "487", "2026-10-14", "5000", "2026-10-15 05:00:00"),
    "sB": (247, "B-0247", "B", "A017456", "2026-11-02", "1597", "2026-11-03 05:00:00"),
    "sS": (130, "B-0130", "S", "3688", "2026-10-10", "7979", "2026-10-11 05:00:00"),
    "sG": (131, "B-0131", "G", "81974", "2026-10-11", "12972", "2026-10-12 05:00:00"),
    "sN": (132, "B-0132", "N", "555", "2026-10-12", "5010", "2026-10-13 05:00:00"),
    "sR": (133, "B-0133", "R", "77", "2026-10-13", "1000.50", "2026-10-14 05:00:00"),
    "sD": (134, "B-0134", "D", "641", "2026-10-15", "4762.50", "2026-10-16 05:00:00"),
    "sU": (143, "B-0143", "U", "", "", None, "2026-10-04 05:00:00"),
    "sP": (90, "B-0090", "P", "", "", "2200", "2026-09-11 05:00:00"),
    "sQ1": (180, "B-0180", "Q", "", "", "3333", "2026-10-23 05:00:00"),
    "sQ2": (181, "B-0181", "Q", "", "", "4444", "2026-10-26 05:00:00"),
    "sW": (250, "B-0250", "W", "", "", "1234", "2026-11-02 05:00:00"),
    "sF": (251, "B-0251", "F", "", "2026-11-28", "2500", "2026-11-05 05:00:00"),
    "sO": (190, "B-0190", "O", "1201", "2026-10-18", "1050", "2026-10-19 05:00:00"),
    "sX": (191, "B-0191", None, "1400", "2026-10-19", "2100", "2026-10-20 05:00:00"),
    "sV": (91, "B-0091", "V", "61", "2026-09-15", "2005", "2026-09-16 05:00:00"),
    "sY": (92, "B-0092", "Y", "", "", None, "2026-09-17 05:00:00"),
    "sE": (93, "B-0093", "E", "63", "2026-09-17", "3020", "2026-09-18 05:00:00"),
    "sH2": (94, "B-0094", "H", "71", "2026-09-20", "900", "2026-09-21 05:00:00"),
    "sH1": (95, "B-0095", "H", "", "", "900", "2026-09-06 05:00:00"),
    "sL": (260, "B-0260", "L", "213", "2026-10-08", "520", "2026-10-09 05:00:00"),
    "sM": (261, "B-0261", "M", "A000213", "2026-10-09", "810", "2026-10-10 05:00:00"),
    "sC": (262, "B-0262", "C", "888", "", "3005", "2026-10-15 05:00:00"),
    "sT": (263, "B-0263", "T", "T-99", "2026-10-02", "700", "2026-10-03 05:00:00"),
}
# the live state the old code left: (bill, scan, grade, rule)
LINKS = [("K2", "sK2", "EXACT", "verified"), ("K3", "sK3", "EXACT", "verified"),
         ("K1", "sK4", "AUTO", "auto_link (S454 5)"),                           # B-0202 (A000223) auto-linked to A000213
         ("A1", "sA", "AUTO", "auto_link (S454 5)"),                            # an October paper tied to September's 415
         ("B1", "sB", "AUTO", "auto_link (S454 5)"),                            # a November paper tied to September's 14538
         ("S1", "sS", "EXACT", "verified"), ("G1", "sG", "EXACT", "verified"), ("N1", "sN", "EXACT", "verified"),
         ("R1", "sR", "EXACT", "verified"),
         ("D1", "sD", "EXACT", "paper amount = Marg (reception)"),
         ("U1", "sU", "CONFIRMED", "reception confirmed"),
         ("P1", "sP", "AUTO", "auto_link (S454 5)"),                            # September only, fails the new rule: untouched
         ("Q1", "sQ1", "AUTO", "auto_link (S454 5)"),                           # a correct same-month unique AUTO link: kept
         ("V1", "sV", "EXACT", "verified"),                                     # September: Rs 5 apart -- keeps the noise band
         ("Y1", "sY", "CONFIRMED", "reception confirmed"),                      # September: nothing read -- shown, nobody asked
         ("E1", "sE", "EXACT", "paper amount = Marg (reception)"),              # September: a contradicting answer -- shown, nobody asked
         ("H2", "sH2", "EXACT", "verified"),
         ("T1", "sT", "AUTO", "auto_link (S454 5)")]                            # fails the rule, but August is final: kept
BID = {k: i for i, k in enumerate(sorted(BILLS), 1)}
SID = {k: v[0] for k, v in SCANS.items()}


def seed(fdb, adb):
    a = sqlite3.connect(adb)
    a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, kind TEXT, status TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount TEXT, "
              "created_at TEXT, submitted_at TEXT, stamp_no TEXT, ocr_status TEXT, dup_of INTEGER, bill_month TEXT, lane TEXT)")
    for k, (i, st, sp, no, d, t, c) in SCANS.items():
        a.execute("INSERT INTO bills VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (i, "Pharmacy", "captured", SUP.get(sp, ""), no, d, t, c, None, st, "done", None, None,
                                                                            "pharmacy"))
    a.commit()
    a.close()
    con = sqlite3.connect(fdb)
    con.row_factory = sqlite3.Row
    PA._schema_done = False
    PA._ensure(con)
    PA._ensure_s439(con)
    for ddl in ("CREATE TABLE IF NOT EXISTS s454_scan_answer (asset_bill_id INTEGER NOT NULL, kind TEXT NOT NULL, answer TEXT, value TEXT, by TEXT,"
                " at TEXT NOT NULL, PRIMARY KEY (asset_bill_id, kind))",
                "CREATE TABLE IF NOT EXISTS s454_paper_missing (bill_id INTEGER PRIMARY KEY, by TEXT, at TEXT NOT NULL, accepted_by TEXT, accepted_at TEXT)"):
        con.execute(ddl)
    for k, v in (("purchase.register_from", "2026-10-01"), ("purchase.parked_months", "2026-09"), ("porders.scan_from", "2026-09-01"),
                 ("purchase.total_noise_rs", "10")):
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", (k, v))
    con.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows) VALUES "
                "('e0e0', 'BILLWISE', 'walk.xls', '2026-09-01', '2026-11-30', '20261106-100000', '2026-11-06T10:00:00', 1)")
    for k, (sp, no, d, rsv) in BILLS.items():
        con.execute("INSERT INTO purchase_bill (id, supplier_norm, supplier, bill_no, bill_date, month, amount_p, bw_md5, first_seen_day) "
                    "VALUES (?,?,?,?,?,?,?,?,?)", (BID[k], PA.supplier_key(SUP[sp]), SUP[sp], no, d, d[:7], rsv * 100, "e0e0", d))
    for b, s, g, rule in LINKS:
        con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                    (BID[b], SID[s], g, rule, "2026-10-25T10:00:00"))
        con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (SID[s], BID[b]))
    # Deepam: reception typed the paper as Marg's 4,751 ("scan galat padha"); the scan itself reads 4,762.50
    for k, paper in (("sD", 475100), ("sE", 300000)):
        con.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at, paper_amount, amount_state, confirmed_by, confirmed_at) "
                    "VALUES (?,?,?,?,?,?,?,?)", (SID[k], "linked", "linked", "2026-10-20T10:00:00", paper, "scan_wrong", "reception", "2026-10-20T10:00:00"))
    con.execute("INSERT INTO purchase_month (month, status) VALUES ('2026-08', 'final')")
    con.commit()
    return con


if os.environ.get("S726_WALK_SEED_ONLY"):
    out = os.environ["S726_WALK_SEED_ONLY"]
    os.makedirs(out, exist_ok=True)
    c = seed(os.path.join(out, "finance.db"), os.path.join(out, "assets.db"))
    c.close()
    shutil.rmtree(TMP, ignore_errors=True)
    print("walk_s726: seeded %s (finance.db, assets.db)" % out)
    sys.exit(0)

con = seed(FDB, ADB)
from flask import Flask, jsonify                                       # noqa: E402

app = Flask("walk_s726")
WHO = {"u": dict(user="manoj", role="checker", roles=["checker"])}


def require_stub(*roles):
    u = WHO["u"]
    if u is None or not set(u.get("roles") or []).intersection(roles):
        return None, (jsonify(ok=False, error="not_permitted"), 403)
    return u, None


PA.init(app, lambda: con, require_stub, url_prefix="/finance/purchase", assets_db=ADB)
PO._db = lambda: con
cl = app.test_client()


def link(bk):
    r = con.execute("SELECT asset_bill_id, grade, matched_on FROM purchase_scan_link WHERE bill_id=?", (BID[bk],)).fetchone()
    return (r[0], r[1], r[2] or "") if r else (None, None, "")


def state_of(sk):
    r = con.execute("SELECT why, likely_bill, hint_bill, detail FROM purchase_scan_state WHERE asset_bill_id=?", (SID[sk],)).fetchone()
    return dict(r) if r else {}


def row(reg, bk):
    return next((x for x in reg["rows"] if x["id"] == BID[bk]), None)


print("walk_s726 on %s" % SRC)
# ---------------------------------------------------------------------------------------------------------------- the rules, one by one
cx = SR.Ctx(con)
bills = [dict(b) for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + PA.EFF_BILL)]
acon = PA._assets_con()
scans = {s["id"]: s for s in PA._scans(acon)}
acon.close()
bb = {k: next(b for b in bills if b["id"] == BID[k]) for k in BILLS}
ck("the scratch rows read back (%d bills, %d scans)" % (len(bills), len(scans)), len(bills) == len(BILLS) and len(scans) == len(SCANS), False)
ok_fn = getattr(SR, "autolink_ok", None)
ck("scan_register.autolink_ok exists (the S726 auto-link conditions)", ok_fn is not None)
if ok_fn:
    ck("1 four Kedar bills of Rs 7,400: B-0202 (reads A000223) may not stand on A000213 by amount", not ok_fn(cx, scans[202], bb["K1"], bills)[0])
    ck("1 an October paper (A.A. 487) may not stand on September's 415", not ok_fn(cx, scans[224], bb["A1"], bills)[0])
    ck("1 a November paper (Bass A017456) may not stand on September's 14538", not ok_fn(cx, scans[247], bb["B1"], bills)[0])
    ck("1 a same-month, unique amount, nothing differing: it stands", ok_fn(cx, scans[180], bb["Q1"], bills)[0])
    ck("1 no date read and scanned in the next month: it does not stand", not ok_fn(cx, scans[250], bb["W1"], bills)[0])
    ck("1 another bill of the supplier within Rs 1 (September's 778): it does not stand", not ok_fn(cx, scans[90], bb["P1"], bills)[0])
pick = getattr(SR, "autolink_pick", None)
ck("scan_register.autolink_pick gives the refused candidate", pick is not None and pick(cx, scans[250], bills, {}, "2026-09-01")[:2] == (None, bb["W1"]))
ck("scan_register.autolink_choice: the old name still answers (None for a refused pair, the bill for a good one)",
   SR.autolink_choice(cx, scans[250], bills, {}, "2026-09-01") is None
   and (SR.autolink_choice(cx, scans[181], bills, {}, "2026-09-01") or {}).get("id") == BID["Q2"])
ck("3 Rs 1 or less is equal (the difference kept): 7,979 against 7,978", SR.total(797900, 797800, 1000) == ("equal", 100), False)
def tot(scan_p, ym):
    b = dict(supplier="TEST", bill_no="1", bill_date=ym + "-10", month=ym, amount_p=500000)
    return SR.agree(cx, dict(vendor="TEST", bill_no="", bill_date="", amount_p=scan_p), b)["total"]


ck("3 a counted month: Rs 10 is no longer noise -- it differs", tot(501000, "2026-10") == "differ")
ck("3 a counted month: Rs 1.01 differs", tot(500101, "2026-10") == "differ")
ck("3 a parked month (September) keeps the noise band: Rs 10 is still noise", tot(501000, "2026-09") == "noise")


def differs(a, b, ym):
    try:
        return PO._s440_differs(a, b, ym)
    except TypeError:
        return None


ck("3 the amount question at reception (porders._s440_differs) asks beyond Rs 1 in a counted month: 5,010 against 5,000",
   differs(501000, 500000, "2026-10") is True and differs(500100, 500000, "2026-10") is False)
ck("3 ... and not for September (parked: the old band, no new question)", differs(501000, 500000, "2026-09") is False
   and differs(501100, 500000, "2026-09") is True)
ck("3 purchase.total_noise_rs is still read as before (item_check's meaning unchanged)", SR.noise_p(con) == 1000, False)

# ---------------------------------------------------------------------------------------------------------------- the pass
reg_before = SR.register(con, "2026-10")
ck("the register before the pass: Kedar A000213 has its scan by amount (the wrong pair)", (row(reg_before, "K1") or {}).get("scan") == 202, False)
md0 = hashlib.md5(open(FDB, "rb").read()).hexdigest()
res = PA._rematch(con, "walk")
ck("the pass ran", isinstance(res, dict), False)
ck("2 B-0202's AUTO link to Kedar A000213 is undone and the scans re-pair on their numbers: A000213 <- B-0161, A000223 <- B-0202",
   link("K1")[0] == 161 and link("K4")[0] == 202)
ck("2 ... purchase_bill.scan_bill_id follows (A000213 = B-0161)",
   con.execute("SELECT scan_bill_id FROM purchase_bill WHERE id=?", (BID["K1"],)).fetchone()[0] == 161)
ck("2 A.A. 487's paper is no longer tied to September's 415; scan_bill_id cleared", link("A1")[0] is None
   and con.execute("SELECT scan_bill_id FROM purchase_bill WHERE id=?", (BID["A1"],)).fetchone()[0] is None)
ck("2 Bass A017456's November paper is no longer tied to September's 14538", link("B1")[0] is None)
au = [dict(r) for r in con.execute("SELECT action, ref, detail FROM purchase_audit WHERE action='auto_link_undone'")]
ck("2 three audit rows 'auto_link_undone', kit S726", len(au) == 3 and all('"kit": "S726"' in (x["detail"] or "") for x in au))
ck("2 a September-only AUTO link that fails the new rule is left untouched (Septimus 777 <- B-0090)", link("P1")[:2] == (90, "AUTO"))
ck("2 a correct same-month unique AUTO link is kept (Unique 901 <- B-0180)", link("Q1")[:2] == (180, "AUTO"), False)
ck("1 a new same-month unique scan still pairs by itself (Unique 905 <- B-0181, AUTO)", link("Q2")[:2] == (181, "AUTO"), False)
ck("1 a scan with no date read, scanned in the next month, does not pair by itself (Windsor 300)", link("W1")[0] is None)
sw = state_of("sW")
ck("1 ... it is reception's one-tap 'Yahi bill hai?': its likely bill is Windsor 300", sw.get("why") in PO.S440_ASK and sw.get("likely_bill") == BID["W1"])
sa, sb = state_of("sA"), state_of("sB")
ck("BLOCKER the freed October paper (A.A. 487) is not asked against September's 415: it waits for its own bill",
   sa.get("why") == "no_bill_yet" and not sa.get("likely_bill") and not sa.get("hint_bill"))
ck("BLOCKER the freed November paper (Bass A017456) has no September likely bill either", not sb.get("likely_bill") and not sb.get("hint_bill"))
sf = state_of("sF")
ck("1 a paper dated after Marg's last bill is neither paired by amount nor asked about: it waits for Marg's entry (Freshco)",
   link("F1")[0] is None and not sf.get("likely_bill"))
st = PO.scan_status(con, [SID["sW"], SID["sA"], SID["sF"]])
ck("1 the asset app's read door: 'your answer is wanted' for Windsor, 'wait' for the A.A. and Freshco papers",
   (st.get(str(SID["sW"])) or {}).get("code") == "you" and all((st.get(str(SID[k])) or {}).get("code") == "wait" for k in ("sA", "sF")))
ck("1 an Oct-2025 bill '213' is never paired with an Oct-2026 paper '213' (the full date, year included)", link("L0")[0] is None)
ck("1 two series of one supplier (A000213 and B/213, one day): no pair by number -- a question", link("M1")[0] is None and link("M2")[0] is None
   and state_of("sM").get("likely_bill") == BID["M1"])
sc = state_of("sC")
ck("10 number agrees, no date read, Rs 5 apart: an AMOUNT question (the number agrees), not 'number differs'",
   link("C1")[0] is None and sc.get("why") == "amount_differs" and sc.get("likely_bill") == BID["C1"] and "carries the same number" in (sc.get("detail") or ""))
ck("5 a finalised month's AUTO link is never undone (Tulsi 40 of August <- B-0263)", link("T1")[:2] == (263, "AUTO"))
ck("1 September only: a scan the new rule would refuse keeps the old auto-link (Harbor 70 <- B-0095, AUTO) -- nothing asked",
   link("H1")[:2] == (95, "AUTO") and not state_of("sH1").get("likely_bill"))
st9 = PO.scan_status(con, [SID["sV"]])
ck("3 September: Vega 61 (Rs 5 apart) raises no amount question", (st9.get(str(SID["sV"])) or {}).get("code") == "linked")
ck("1 bill number + date (+ supplier) pair first, whatever the totals: Orion 1201 <- B-0190 (PROBABLE, S726)", link("O1")[0] == 190 and link("O1")[1] == "PROBABLE"
   and "S726" in link("O1")[2])
ck("1 ... but a number and a day with no supplier read, the totals apart, are not paired by themselves (Orion 1400)", link("X1")[0] is None, False)
ck("the pass says how many links it undid", res.get("undone") == 3)
au2 = con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='auto_link_undone'").fetchone()[0]
PA._rematch(con, "walk")
ck("2 a second pass changes nothing more (no new undo, the links the same)", con.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='auto_link_undone'")
   .fetchone()[0] == au2 and link("K1")[0] == 161 and link("A1")[0] is None)

# ---------------------------------------------------------------------------------------------------------------- the register
reg = SR.register(con, "2026-10")
regs = SR.register(con, "2026-09")
rS, rG, rN, rR, rD, rU, rO = (row(reg, k) or {} for k in ("S1", "G1", "N1", "R1", "D1", "U1", "O1"))
ck("3 Shivaaz 3688 (paper 7,979 / Marg 7,978) verifies and SHOWS the rupee",
   rS.get("state") == "verified" and "Paper ₹7,979 · ₹1 rounding — supplier's figure paid" in (rS.get("note") or ""))
ck("3 Gunina 81974 (12,972 / 12,973) verifies and shows the rupee", rG.get("state") == "verified" and "₹1 rounding" in (rG.get("note") or ""))
ck("3 a 50-paise difference is shown with its paise", rR.get("state") == "verified" and "₹0.50 rounding" in (rR.get("note") or ""))
ck("3 Nandi 555 (scan 5,010 / Marg 5,000): Amount differs, reception asked", rN.get("state") == "amount_differs" and rN.get("whose") == "Reception: a question")
ck("4 Deepam 641: the answer 4,751 contradicts the scan's 4,762.50 -> Second look, You & Shavez",
   rD.get("state") == "second_look" and rD.get("whose") == "You & Shavez")
ck("4 ... its note names both figures and Marg's", all(x in (rD.get("note") or "") for x in ("₹4,751", "₹4,762.50", "Marg ₹4,751")))
ck("5 Shraddha 10480 (B-0143, nothing read, paired by hand): Paired, nothing read; Reception: rescan",
   rU.get("state") == "unread_pair" and rU.get("whose") == "Reception: rescan")
ck("4/5 neither is counted as settled", reg["settled"] == sum(1 for x in reg["rows"] if x["state"] in ("verified", "has_scan", "accepted"))
   and rD.get("state") not in ("verified", "has_scan") and rU.get("state") not in ("verified", "has_scan"))
ck("the new states have English labels", SR.STATE_EN.get("second_look") == "Second look" and SR.STATE_EN.get("unread_pair") == "Paired, nothing read")
old_keys = ("month", "cls", "rows", "scans", "counts", "scan_counts", "settled", "total", "open_scans", "done_date", "n_bills")
old_states = ("verified", "has_scan", "amount_differs", "no_scan", "double", "accepted")
ck("register() keeps every existing key and state", all(k in reg for k in old_keys) and all(k in reg["counts"] for k in old_states)
   and all(k in SR.STATES and k in SR.STATE_EN for k in old_states), False)
ck("every row's state is one of STATES and has a label", all(x["state"] in SR.STATES and x["state"] in SR.STATE_EN for x in reg["rows"] + regs["rows"]), False)
try:
    pb = SR.page_body(con, "2026-10", "/finance/purchase", True, ["2026-11", "2026-10", "2026-09"])
    ck("the register page (page_body) still draws", "Purchase bills: October 2026" in pb and 'id="s454bills"' in pb, False)
    ck("... and names the new states", "Second look" in pb and "Paired, nothing read" in pb)
except Exception as e:                                                 # noqa: BLE001
    ck("the register page (page_body) still draws (%s)" % e, False, False)
ck("2 September's register still shows Septimus 777 with its scan", (row(regs, "P1") or {}).get("scan") == 90, False)
rV, rY, rE = (row(regs, k) or {} for k in ("V1", "Y1", "E1"))
ck("3 September: Vega 61 stays Verified (the noise band), its rupees shown", rV.get("state") == "verified" and "₹5 rounding" in (rV.get("note") or ""))
ck("5 September: Yashoda 62 shows 'Paired, nothing read' with whose 'Nobody (September is parked)'",
   rY.get("state") == "unread_pair" and rY.get("whose") == "Nobody (September is parked)")
ck("4 September: Everest 63 shows 'Second look' with whose 'Nobody (September is parked)'",
   rE.get("state") == "second_look" and rE.get("whose") == "Nobody (September is parked)")

# ---------------------------------------------------------------------------------------------------------------- the owner's step view
before = (hashlib.md5(open(FDB, "rb").read()).hexdigest(), con.total_changes)
WHO["u"] = dict(user="manoj", role="checker", roles=["checker"])
r = cl.get("/finance/purchase/page/check?month=2026-10")
h = r.get_data(as_text=True)
ck("6 /finance/purchase/page/check answers the checker (200)", r.status_code == 200)
tot = sum(BILLS[k][3] for k in BILLS if BILLS[k][2][:7] == "2026-10")
n10 = sum(1 for k in BILLS if BILLS[k][2][:7] == "2026-10")
head = "October · %d bills · %s" % (n10, SR.rs(tot * 100))
ck("6 the header reads '%s'" % head, head in h)
ck("6 the strip reads 'NEFT on hold · N open'", bool(re.search(r"NEFT on hold · \d+ open", h)))
labels = ["Scans paired", "With reception", "Differences → Amir", "Rounding (supplier&#x27;s figure paid)", "You &amp; Shavez", "Supplier summaries",
          "Lock &amp; NEFT"]
ck("6 seven rows, in order, each a <details>", h.count("<details") == 7 and all(('data-row="%d"' % i) in h for i in range(1, 8))
   and [h.find(x) for x in labels] == sorted(h.find(x) for x in labels) and min(h.find(x) for x in labels) > 0)
ck("6 row 1 'Scans paired' n / total", bool(re.search(r"Scans paired</span><span class=\"n\">\d+ / %d<" % n10, h)))
ck("6 row 2 With reception carries the nothing-read pair and the unscanned bills", "SHRADDHA SURGICALS 10480" in h and "paired, nothing read: rescan" in h)
ck("6 row 3 Differences → Amir: 'NANDI DRUG HOUSE 555 ₹10'", "NANDI DRUG HOUSE 555 ₹10" in h)
ck("6 row 4 Rounding: Shivaaz and Gunina", "SHIVAAZ PHARMA 3688 · paper ₹7,979 · ₹1" in h and "GUNINA LIFESCIENCES 81974" in h)
ck("6 row 5 You & Shavez: Deepam's second look", "DEEPAM DRUG HOUSE 641 · second look" in h)
ck("6 rows 6 and 7 greyed: 'later' and 'after 1–6'", h.count('class="grey') == 2 and ">later<" in h and ">after 1–6<" in h)
ck("6 a month select", 'id="s726month"' in h and 'value="2026-09"' in h)
ck("6 the S440 bar with BACK", 'id="s440back"' in h)
ck("6 phone-first: no fixed width wider than 390 px", not re.search(r"(?<!max-)width:\s*(39[1-9]|[4-9]\d\d|\d{4,})px", h[h.find('id="s726chk"'):]))
r2 = cl.get("/finance/purchase/page/check")
ck("6 no month: the oldest counted month not fully settled (October)", r2.status_code == 200 and "October · " in r2.get_data(as_text=True))
ck("6 the page wrote nothing (no pass on GET)", (hashlib.md5(open(FDB, "rb").read()).hexdigest(), con.total_changes) == before)
r9 = cl.get("/finance/purchase/page/check?month=2026-09").get_data(as_text=True)
seg = r9[r9.find('data-row="2"'):r9.find('data-row="6"')]
ck("6 September's step view: the parked new states are named as waiting with nobody, in no person's row",
   'id="s726parked"' in r9 and "YASHODA SURGICALS 62" in r9 and "YASHODA" not in seg and "EVEREST" not in seg)
cb = getattr(SR, "check_body", None)
ck("6 'All clear ✓' when nothing is open", cb is not None and "All clear ✓" in cb(con, "2026-12", "/finance/purchase", ["2026-12"],
                                                                         dict(rows=[], scans=[], total=0, settled=0, open_scans=0, cls="counted")))
WHO["u"] = dict(user="shavez", role="maker", roles=["maker"])
r3 = cl.get("/finance/purchase/page/check?month=2026-10")
ck("6 a maker is refused (403)", r3.status_code == 403)
WHO["u"] = None
r4 = cl.get("/finance/purchase/page/check?month=2026-10")
ck("6 no login is refused (403 here; the app's own gate answers 302 first)", r4.status_code in (302, 401, 403))
WHO["u"] = dict(user="manoj", role="checker", roles=["checker"])
ck("6 a malformed month is refused (400)", cl.get("/finance/purchase/page/check?month=2026-1x").status_code == 400)

# ---------------------------------------------------------------------------------------------------------------- the proof's plan
rS9 = (row(SR.register(con, "2026-09"), "A1") or {}), (row(SR.register(con, "2026-09"), "B1") or {})
ck("BLOCKER September's register has no 'Reception: ...' line for 415 or 14538 (Nobody: September is parked)",
   all(x.get("state") == "no_scan" and x.get("whose") == "Nobody (September is parked)" for x in rS9))
try:
    work = PO.scan_work(con)
    ids = {x["bill_id"] for x in work.get("scan") or []} | {x["bill_id"] for x in work.get("confirm") or []}
    ck("BLOCKER reception's own lists (scan_work) carry neither 415 nor 14538", BID["A1"] not in ids and BID["B1"] not in ids)
except Exception as e:                                                 # noqa: BLE001
    ck("BLOCKER reception's own lists (scan_work) could be read (%s)" % str(e)[:80], False)
ck("2 differs(..., None) keeps the old band (never Rs 1 by default)", differs(501000, 500000, None) is False)
import contextlib                                                      # noqa: E402
import io                                                              # noqa: E402
keep_db = PO._db
PO._db = lambda: None
err = io.StringIO()
with contextlib.redirect_stderr(err):
    tolv = PO._s726_tol_p("2026-10") if hasattr(PO, "_s726_tol_p") else None
PO._db = keep_db
ck("3 a fault judging the month falls back to the old band and says so on stderr", tolv == 1000 and "porders S726" in err.getvalue())
plan = getattr(PA, "_s726_undo_plan", None)
pl = plan(con) if plan else None
ck("5 the proof's undo plan (read only) after the pass: only the finalised August link, flagged final, kept",
   pl is not None and [(x["bill"], x.get("final")) for x in pl] == [(BID["T1"], True)])
# 7 -- the S726 context cannot be set up: the pass is the old one entirely (a second scratch pair)
F2, A2 = os.path.join(TMP, "f2.db"), os.path.join(TMP, "a2.db")
con2 = seed(F2, A2)
keep_a, keep_setup = PA._assets_db, getattr(PA, "_s726_setup", None)
PA._assets_db = A2


def _boom(c):
    raise RuntimeError("walk: no S726 context")


PA._s726_setup = _boom
try:
    PA._rematch(con2, "walk")
finally:
    PA._assets_db = keep_a
    if keep_setup is None:
        del PA._s726_setup
    else:
        PA._s726_setup = keep_setup
l2 = {k: (con2.execute("SELECT asset_bill_id, grade FROM purchase_scan_link WHERE bill_id=?", (BID[k],)).fetchone() or (None, None))[:2]
      for k in ("K1", "W1", "O1", "A1")}
ck("7 a setup fault: the old behaviour entirely (no undo, the old auto-link, no number + date pair)",
   l2["K1"] == (202, "AUTO") and l2["A1"] == (224, "AUTO") and l2["W1"][1] == "AUTO" and l2["O1"][0] is None, False)
ck("7 ... and the fault is audited", con2.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s726_setup_error'").fetchone()[0] == 1)
con2.close()
con.close()
shutil.rmtree(TMP, ignore_errors=True)
print("walk_s726: %d check(s) failed (%d of them S726 checks)" % (len(FAILS), len(S726)))
sys.exit(1 if FAILS else 0)
