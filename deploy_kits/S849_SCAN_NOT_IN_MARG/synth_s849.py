"""synth_s849.py <finance dir under test> <finance.db COPY> [--real <assets.db COPY>] -- kit S849_SCAN_NOT_IN_MARG proof. Works on COPIES only.
 A made-up assets.db (four scans shaped as the real ones: B-0150 / B-0154 Deepam, B-0122 / B-0134 Shivaaz) beside a copy of finance.db:
 the asks, the Needs-you line, Amir's card, every answer, the undo, the OFF switch, the scan permission. --real: the live copies -- B-0150 is
 asked and its best match is Marg bill A000678. Last line: 'SYNTH S849: n PASS, m FAIL'."""
import json, os, shutil, sqlite3, sys, tempfile
FIN, DBC = sys.argv[1], sys.argv[2]
REAL = sys.argv[sys.argv.index("--real") + 1] if "--real" in sys.argv else None
tmp = tempfile.mkdtemp(prefix="s849synth_")
code = os.path.join(tmp, "finance")
shutil.copytree(FIN, code, ignore=shutil.ignore_patterns("*.db", "__pycache__", "_off"))
_me = os.path.dirname(os.path.abspath(__file__))           # F-1415: never the kit's own copy beside this script
sys.path[:] = [x for x in sys.path if os.path.abspath(x or os.getcwd()) != _me]
sys.path.insert(0, code)
P = F = 0


def ok(c, what):
    global P, F
    if c:
        P += 1
        print("PASS", what)
    else:
        F += 1
        print("FAIL", what)


def made_up_assets(path):
    c = sqlite3.connect(path)
    cols = ("id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, notes TEXT, source_stored TEXT, source_orig TEXT, "
            "created_by INTEGER, created_at TEXT, stamp_no TEXT, status TEXT, submitted_by TEXT, submitted_at TEXT, approved_by TEXT, approved_at TEXT, "
            "reject_reason TEXT, ocr_status TEXT, lane TEXT, fp TEXT, fpc TEXT, dup_of INTEGER, dup_flag TEXT, dup_cand INTEGER, dup_why TEXT, late_for TEXT, "
            "bill_month TEXT, doc_kind TEXT, challan_state TEXT, challan_of INTEGER, pe_who TEXT, rescan_of INTEGER, page_of INTEGER, subgroup TEXT")
    c.execute("CREATE TABLE bills(%s)" % cols)
    c.execute("CREATE TABLE bill_items(id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, pack_size TEXT, quantity REAL, rate REAL, amount REAL, make TEXT, "
              "model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT, asset_id INTEGER)")
    c.execute("CREATE TABLE claude_reading(bill_id INTEGER, ok INTEGER, doc_kind TEXT, data TEXT, error TEXT)")

    def bill(i, v, no, d, tot, created):
        c.execute("INSERT INTO bills(id,kind,vendor,bill_no,bill_date,total_amount,created_at,stamp_no,status,submitted_by,submitted_at,lane,bill_month,ocr_status) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (i, "Pharmacy", v, no, d, tot, created, "B-%04d" % i, "captured", "Reception", created, "pharmacy", "2026-10", "done"))

    def item(b, n, q, r, a, bt, e):
        c.execute("INSERT INTO bill_items(bill_id,item_name,pack_size,quantity,rate,amount,batch,expiry) VALUES (?,?,?,?,?,?,?,?)", (b, n, "10*10", q, r, a, bt, e))
    bill(150, "DEEPAM PHARMA", "A0006678", "2026-04-12", 615.32, "2026-10-12 19:28:00")
    item(150, "ROSIKA FORTE TAB", 5010, 213.36, 10668, "MT667", "1/28")
    item(150, "THIO Q-AP TAB", 102, 228.66, 2286, "AT25595", "11/27")
    bill(154, "DEEPAM PHARMA", "A000678", "2026-10-12", 12922, "2026-10-12 19:37:00")
    item(154, "ROSIKA FORTE TAB", 30, 213.36, 10668, "M1667", "1/28")
    bill(122, "SHIVAAZ FORMULATIONS", "3499", "2026-10-03", 4747, "2026-10-04 18:00:00")
    bill(134, "SHIVAAZ FORMULATIONS", "3499", "2026-10-03", 4747, "2026-10-04 18:10:00")
    c.commit()
    c.close()


def fresh():
    db = os.path.join(tmp, "f%d.db" % (P + F))
    shutil.copy(DBC, db)
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


try:
    import purchase_app as pa                                 # noqa: E402
    import scan_ask as sa                                     # noqa: E402
    import provisional_s781 as PV                             # noqa: E402
    import scan_register as SR                                # noqa: E402
    have = True
except Exception as e:                                        # noqa: BLE001
    print("import:", e)
    have = False
ok(have, "T0 the finance code under test holds scan_ask.py and imports")
if have and REAL:
    pa._assets_db = REAL
    con = fresh()
    v = sa.view(con)
    c = next((x for x in v["asked"] + v["parked"] if x["stamp"] == "B-0150"), None)
    best = c and next((y for y in c["cands"] if y["best"]), None)
    ok(v["ok"] and c is not None and best is not None and best["bill"]["bill_no"] == "A000678",
       "R1 the live copies: B-0150 (Deepam) is asked and its best match is Marg bill A000678 (%s)" % repr(best and best["bill"]["bill_no"]))
    ok(sa.page_html(con).count("class=case") >= 1, "R2 the doctor's page draws on the live copies")
    ids, blocks = sa.amir_view(con)
    ok(150 in ids and len(blocks) >= 1, "R3 Amir's card carries the question on the live copies (%d)" % len(blocks))
    con.close()
if have:
    A = os.path.join(tmp, "assets.db")
    made_up_assets(A)
    pa._assets_db = A
    con = fresh()
    v = sa.view(con)
    by = {x["stamp"]: x for x in v["asked"]}
    b150 = by.get("B-0150")
    best = b150 and next((y for y in b150["cands"] if y["best"]), None)
    ok(b150 is not None and best is not None and best["bill"]["bill_no"] == "A000678" and best["agree"] == 2 and best["scan"] == 154,
       "T1 B-0150 asked; best match Marg bill A000678, 2 of 2 lines agree, its own scan B-0154")
    q = next((m for a, m, mk in best["cmp"] if a and a["name"].startswith("ROSIKA")), None) if best else None
    mk = next((mk for a, m, mk in best["cmp"] if a and a["name"].startswith("ROSIKA")), {}) if best else {}
    ok(mk.get("batch") is True and mk.get("rate") is True and mk.get("qty") is False, "T2 ROSIKA: batch and rate ticked, the qty read 5010 marked against Marg's 50 + 10")
    ok("B-0122" in by and next((y for y in by["B-0122"]["cands"] if y["best"]), {}).get("bill", {}).get("bill_no") == "3499", "T3 B-0122 asked; best Marg bill 3499 (number and total)")
    nl = sa.needs_lines(con)
    ok(len(nl) == 1 and nl[0]["target"] == "scans" and nl[0]["href"] == sa.PAGE and "2:" in nl[0]["text"], "T4 one Needs-you line, Bills & papers, opens the page")
    h = sa.page_html(con)
    ok(h.count("class=case") == 2 and h.count("data-src='/finance/purchase/api/s738/scan/150'") == 1 and "data-src='/finance/purchase/api/s738/scan/154'" in h
       and "Yes — same bill as A000678 (scanned twice)" in h, "T5 the page: two cases, the scan and the candidate's own scan inline, the buttons")
    ids, blocks = sa.amir_view(con)
    ok(ids == {150, 122} and len(blocks) == 2 and "sna:150:same:" in blocks[1] + blocks[0] and "Yeh kharid ka bill nahi hai" in blocks[0],
       "T6 Amir's card: both questions in Hindi, one-tap answers")
    ok(sa.amir_may_see(con, 154) and sa.amir_may_see(con, 150) and not sa.amir_may_see(con, 1), "T7 Amir may open the asked scan and the candidate's scan, nothing else")
    ok(SR.s738_scan_ok(con, 154, False, "amir") and not SR.s738_scan_ok(con, 1, False, "amir"), "T8 the scan door lets Amir open them (s738_scan_ok)")
    ok(sa.answer(con, "amir", 150, "same", 999999)[0] is False, "T9 'same' with a bill not among the candidates is refused")
    bid = int(best["bill"]["id"])
    r = sa.answer(con, "manoj", 150, "same", bid, owner=True)
    st = con.execute("SELECT why, dup_ok FROM purchase_scan_state WHERE asset_bill_id=150").fetchone()
    ok(r[0] and st and st["dup_ok"] == 154 and st["why"] == "dup", "T10 'same' on a bill that has its scan: kept as its second scan (dup_ok 154, why dup)")
    ok(sa.answer(con, "amir", 150, "notbill")[0] is False, "T11 a second answer to the same scan is refused (the first closes it)")
    ok(all(x["stamp"] != "B-0150" for x in PV.provisional(con, "2026-10")), "T12 B-0150 leaves the Purchase bills page's waiting list")
    r = sa.answer(con, "amir", 122, "notbill")
    ok(r[0] and all(x["stamp"] != "B-0122" for x in PV.provisional(con, "2026-10")) and all(x["id"] != 122 for x in pa.scans_for_amir(con)["list"]),
       "T13 'not a purchase bill' (Amir): leaves the waiting list and his enter list")
    ok(sa.needs_lines(con) == [] and sa.amir_view(con) == (set(), []), "T14 nothing left: no Needs-you line, nothing on his card")
    aid = con.execute("SELECT id FROM s849_answer WHERE scan=122").fetchone()[0]
    ok(sa.undo(con, "manoj", aid)[0] and any(x["stamp"] == "B-0122" for x in sa.view(con)["asked"]), "T15 the doctor's Undo asks it again")
    ok(sa.amir_tap(con, "amir", "sna:122:enter:0") == 1 and [x["stamp"] for x in sa.view(con, for_amir=True)["enter"]] == ["B-0122"],
       "T16 Amir's tap 'enter': the question becomes his do-line 'Marg mein chadhaiye'")
    ok(sa.amir_tap(con, "amir", "sna:1:same:1") == 0 and sa.amir_tap(con, "amir", "junk") == 0, "T17 a tap for a scan not asked, or junk, records nothing")
    off = os.path.join(code, "_off")
    os.makedirs(off, exist_ok=True)
    open(os.path.join(off, "S849_OFF"), "w").close()
    ok(sa.view(con)["asked"] == [] and sa.needs_lines(con) == [] and sa.aside_ids(con) == set(), "T18 OFF: nothing asked, nothing set aside")
    os.remove(os.path.join(off, "S849_OFF"))
    ok(sa.set_days(con, "manoj", 30) and sa.days(con) == 30 and not sa.set_days(con, "manoj", 0), "T19 the days are his setting (1-60)")
    con.close()
    src = {n: open(os.path.join(code, n), encoding="utf-8").read() for n in ("amir_day.py", "sanjeevni_approvals.py")}
    ok("scan_ask.amir_tap(cx, user, jv)" in src["amir_day.py"] and "_state_before_s849 = state" in src["amir_day.py"]
       and "scan_ask.init(app, db_getter, require_fn)" in src["sanjeevni_approvals.py"] and "_needs_you_before_s849 = _needs_you_before_s761" in src["sanjeevni_approvals.py"],
       "T20 the seams: Amir's tap and card, the Hub's mount and Needs-you")
print("SYNTH S849: %d PASS, %d FAIL" % (P, F))
