"""walk_s677.py -- kit S677_RETURNS_ON_SPINE (Sanjeevni session S362, 28-Oct-2026). Writes nothing outside --scratch.
Loads finance_returns_audit, returns_kinds, finance_returns_escalate, sanjeevni_approvals and spine_read from the root under test and runs
them on a COPY of finance.db and a MADE-UP spine of the walk's own rows (F-998). Every return it judges is its own, dated 2099.
  python walk_s677.py --new <root holding finance/ as built> --db <a COPY of finance.db> --scratch <dir> [--lib <root of unchanged modules>]
  --old <live root>: the control -- every S677 check red, every older check green.
  --box-spine <spine.db>: on the box only -- adds the OLD = NEW proof over every real credit note since --since (default 2026-09-01):
      returns_for_day under the live files vs under the built files, on the same database copy, listed where they differ."""
import argparse, collections, importlib, os, shutil, sqlite3, sys, warnings
warnings.filterwarnings("ignore")
ap = argparse.ArgumentParser()
ap.add_argument("--new"); ap.add_argument("--old"); ap.add_argument("--db"); ap.add_argument("--scratch"); ap.add_argument("--lib")
ap.add_argument("--box-spine"); ap.add_argument("--since", default="2026-09-01"); ap.add_argument("--old-root"); ap.add_argument("--also-since")
a = ap.parse_args()
a.db = os.path.abspath(a.db)
if a.box_spine:
    a.box_spine = os.path.abspath(a.box_spine)
ROOT = os.path.abspath(a.old or a.new)
LIB = os.path.abspath(a.lib or a.old or a.new)
a.scratch = os.path.abspath(a.scratch); os.makedirs(a.scratch, exist_ok=True)
DB = os.path.join(a.scratch, "walk.db")
shutil.copyfile(a.db, DB)
FIN = os.path.join(ROOT, "finance")
if LIB != ROOT:
    FIN = os.path.join(a.scratch, "overlay", "finance"); os.makedirs(os.path.join(FIN, "spine"))
    for e in os.listdir(os.path.join(LIB, "finance")):
        if e == "spine":
            continue
        if not os.path.exists(os.path.join(ROOT, "finance", e)):
            os.symlink(os.path.join(LIB, "finance", e), os.path.join(FIN, e))
    for e in os.listdir(os.path.join(LIB, "finance", "spine")):
        if not os.path.exists(os.path.join(ROOT, "finance", "spine", e)) and not e.endswith(".db"):
            os.symlink(os.path.join(LIB, "finance", "spine", e), os.path.join(FIN, "spine", e))
    for e in os.listdir(os.path.join(ROOT, "finance")):
        if e.endswith(".py"):
            shutil.copyfile(os.path.join(ROOT, "finance", e), os.path.join(FIN, e))
    if os.path.isdir(os.path.join(ROOT, "finance", "spine")):
        for e in os.listdir(os.path.join(ROOT, "finance", "spine")):
            if e.endswith(".py"):
                shutil.copyfile(os.path.join(ROOT, "finance", "spine", e), os.path.join(FIN, "spine", e))
SPINE = os.path.join(a.scratch, "spine_walk.db")
os.environ["SPINE_DB"] = SPINE
sys.path[:0] = [FIN, os.path.join(FIN, "spine")]
os.chdir(a.scratch)
res = []


def check(name, ok, s677=True, note=""):
    res.append((name, bool(ok), s677, str(note)[:400]))


def con_():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


# ---- the made-up spine: the live SCHEMA text from spine_build.py, the walk's own rows -------------------------------------------------
sb = open(os.path.join(FIN, "spine", "spine_build.py"), encoding="utf-8").read()
SCHEMA = sb[sb.index('SCHEMA = """') + len('SCHEMA = """'):]
SCHEMA = SCHEMA[:SCHEMA.index('"""')]
if os.path.exists(SPINE):
    os.remove(SPINE)
s = sqlite3.connect(SPINE)
s.executescript(SCHEMA)
s.executemany("INSERT INTO sp_meta VALUES (?,?)", [("built", "2099-01-20T10:00:00"), ("checkable", "2099-01-19"), ("pending", "")])
for n, pk in (("WALK ZYLORIC", "1*10"), ("WALK PATOPAN DSR", "1*10"), ("WALK NEVER ITEM", "1*10"), ("WALK TWENTYLETTERNAM", "1*10"),
              ("WALK TWOPACK ITEM", "1*10"), ("WALK TWOPACK ITEM", "1*15"), ("WALK SAMEDAY ITEM", "1*10")):
    s.execute("INSERT OR IGNORE INTO sp_item VALUES (?,?,?,?,?,?)", (n[:20], n, pk, "LOOSE", "2099-01-01", "2099-01-19"))
B = [("2099-01-10", "A900001", 0), ("2099-01-10", "A900002", 0), ("2099-01-12", "CN90001", 1), ("2099-01-12", "CN90002", 1),
     ("2099-01-13", "CN90003", 1), ("2099-01-14", "CN90004", 1), ("2099-01-15", "CN90005", 1), ("2099-01-17", "CN90007", 1),
     ("2099-01-11", "A900003", 0), ("2099-01-11", "A900004", 0), ("2099-01-18", "CN90008", 1), ("2099-01-18", "CN90009", 1), ("2099-01-18", "CN90010", 1)]
for d, b, cn in B:
    s.execute("INSERT INTO sp_sale_bill VALUES (?,?,?,?,?,?,?,?,?,?)", (d, b, 100000, 0, 0, 0, 100000, 100000, cn, "walk"))
L = [("2099-01-10", "A900001", 1, "WALK ZYLORIC", "1*10", "0:4", 0.4, 2016, "EE1", "2/29"),
     ("2099-01-10", "A900001", 2, "WALK PATOPAN DSR", "1*10", "0:2", 0.2, 11000, "UC1", "12/28"),
     ("2099-01-10", "A900002", 1, "WALK ZYLORIC", "1*10", "1:0", 1.0, 2016, "EE1", "2/29"),
     ("2099-01-12", "CN90001", 1, "WALK ZYLORIC", "1*10", "0:4", 0.4, 2016, "EE1", "2/29"),          # ok: same qty, same rate
     ("2099-01-12", "CN90002", 1, "WALK ZYLORIC", "1*10", "0:1", 0.1, 2016, "EE1", "2/29"),          # orphan: no sale_item row
     ("2099-01-13", "CN90003", 1, "WALK NEVER ITEM", "1*10", "0:1", 0.1, 5000, "NB1", "6/27"),       # never bought
     ("2099-01-14", "CN90004", 1, "WALK PATOPAN DSR", "1*10", "0:5", 0.5, 11000, "UC1", "12/28"),    # returned more than sold (0:2)
     ("2099-01-15", "CN90005", 1, "WALK ZYLORIC", "1*10", "0:4", 0.4, 2500, "EE1", "2/29"),          # refunded more than paid
     ("2099-01-17", "CN90007", 1, "WALK ZYLORIC", "1*10", "0:2", 0.2, 2016, "EE1", "bad"),           # an expiry the report printed oddly
     ("2099-01-11", "A900003", 1, "WALK SAMEDAY ITEM", "1*10", "1:0", 10.0, 3000, "SD1", "1/30"),    # the same day, two sales, no same-qty: the LARGER on the lower bill
     ("2099-01-11", "A900004", 1, "WALK SAMEDAY ITEM", "1*10", "0:2", 2.0, 3000, "SD1", "1/30"),     # ... the smaller on the higher bill (a plain bill order would take this)
     ("2099-01-11", "A900003", 2, "WALK TWOPACK ITEM", "1*15", "0:3", 3.0, 4500, "TP15", "1/30"),   # the 15-pack at 4500 on the lower bill
     ("2099-01-11", "A900004", 2, "WALK TWOPACK ITEM", "1*10", "0:3", 3.0, 3000, "TP10", "1/30"),   # the 10-pack at 3000 on the higher bill (newest-first takes this without the pack rule)
     ("2099-01-11", "A900004", 3, "WALK TWENTYLETTERNAM", "1*10", "0:1", 1.0, 1000, "TL1", "1/30"),
     ("2099-01-18", "CN90008", 1, "WALK SAMEDAY ITEM", "1*10", "0:4", 4.0, 3000, "SD1", "1/30"),    # 0:4 back: more than 0:2, less than 1:0
     ("2099-01-18", "CN90009", 1, "WALK TWOPACK ITEM", "1*15", "0:3", 3.0, 4500, "TP15", "1/30"),   # the 15-pack back at 4500: ok against ITS pack; 'refunded more than paid' against the 10-pack
     ("2099-01-18", "CN90010", 1, "WALK TWENTYLETTERNAM", "1*10", "0:1", 1.0, 1000, "TL1", "1/30")]
for row in L:
    s.execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", (row[0], row[1], row[2], row[3], row[3][:20], row[4], row[5], row[6], row[7], row[8], row[9]))
s.commit(); s.close()

# ---- the finance side: the walk's own patient, days and bill rows ----------------------------------------------------------------------
c = con_()
c.execute("INSERT INTO patient_ref (clinic_id, name, phone_last4, first_seen) VALUES ('WALK999999','WALK PATIENT','0000','2099-01-01')")
PID = c.execute("SELECT id FROM patient_ref WHERE clinic_id='WALK999999'").fetchone()[0]
DE = {}
for d in ("2099-01-10", "2099-01-11", "2099-01-12", "2099-01-13", "2099-01-14", "2099-01-15", "2099-01-16", "2099-01-17", "2099-01-18"):
    c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES ('medical',?,'submitted','app','walk','2099-01-20T10:00:00')", (d,))
    DE[d] = c.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (d,)).fetchone()[0]
SI = [("2099-01-10", "A900001", "pharmacy", 100000, PID), ("2099-01-12", "CN90001", "pharmacy_return", 100000, PID),
      ("2099-01-13", "CN90003", "pharmacy_return", 100000, PID), ("2099-01-14", "CN90004", "pharmacy_return", 100000, PID),
      ("2099-01-15", "CN90005", "pharmacy_return", 100000, PID), ("2099-01-16", "CN90006", "pharmacy_return", 100000, PID),   # no spine lines
      ("2099-01-17", "CN90007", "pharmacy_return", 100000, PID), ("2099-01-11", "A900003", "pharmacy", 100000, PID),
      ("2099-01-11", "A900004", "pharmacy", 100000, PID), ("2099-01-18", "CN90008", "pharmacy_return", 100000, PID),
      ("2099-01-18", "CN90009", "pharmacy_return", 100000, PID), ("2099-01-18", "CN90010", "pharmacy_return", 100000, PID)]
for d, b, sv, amt, pid in SI:
    c.execute("INSERT INTO sale_item (day_entry_id, unit, patient_ref_id, service, description, amount_p, mode, source, source_ref) "
              "VALUES (?,?,?,?,?,?,?,?,?)", (DE[d], "medical", pid, sv, "walk", amt, "cash", "manual", b))
c.commit()

import finance_returns_audit as fra                                  # noqa: E402
import returns_kinds, finance_returns_escalate, sanjeevni_approvals  # noqa: E402
for m in (fra, returns_kinds, finance_returns_escalate, sanjeevni_approvals):
    assert os.path.dirname(os.path.abspath(m.__file__)) == FIN, "%s not loaded from the root under test" % m.__name__
if LIB != ROOT:
    import spine_read                                                # noqa: E402
    assert os.path.dirname(os.path.abspath(spine_read.__file__)) == os.path.join(FIN, "spine"), "spine_read not from the root under test"

# ---- A: the read door -----------------------------------------------------------------------------------------------------------------
try:
    import spine_read                                                # noqa: E402
    sp = spine_read.Spine(SPINE)
    cns = sp.credit_notes("2099-01-01", "2099-01-31")
    check("A1 credit_notes: the nine credit notes of the month, by date and bill", [x["bill"] for x in cns] == ["CN90001", "CN90002", "CN90003", "CN90004", "CN90005", "CN90007", "CN90008", "CN90009", "CN90010"], note=[x["bill"] for x in cns])
    check("A2 return_days: their days, ascending", sp.return_days("2099-01-01", "2099-01-31") == ["2099-01-12", "2099-01-13", "2099-01-14", "2099-01-15", "2099-01-17", "2099-01-18"])
    ln = sp.sale_lines("A900001", "2099-01-10")
    check("A3 sale_lines by date and bill: two lines in seq order, credit_note 0", [(x["seq"], x["name"], x["credit_note"]) for x in ln] == [(1, "WALK ZYLORIC", 0), (2, "WALK PATOPAN DSR", 0)], note=ln)
    check("A4 sale_lines by bill alone finds it too", [x["seq"] for x in sp.sale_lines("CN90004")] == [1])
    pl = sp.lines_of_bills(["A900001", "A900002", "CN90001"], k20="WALK ZYLORIC", returns=False)
    check("A5 lines_of_bills: the patient's SALE lines of one item, credit notes excluded, newest first", [(x["bill"], x["qty_raw"]) for x in pl] == [("A900002", "1:0"), ("A900001", "0:4")], note=pl)
    check("A6 lines_of_bills: returns=True gives the credit-note lines only", [x["bill"] for x in sp.lines_of_bills(["A900001", "CN90001"], returns=True)] == ["CN90001"])
except Exception as e:                                               # noqa: BLE001
    check("A0 the read door answers", False, note=repr(e))

# ---- B: the engine on the spine --------------------------------------------------------------------------------------------------------
def day(d):
    rows, summ = fra.returns_for_day(c, d, "medical")
    return {r["bill"]: r for r in rows}, summ

try:
    r12, s12 = day("2099-01-12")
    check("B1 12-Jan: CN90001 audited ok -- the same item, the same quantity, the same rate, bought on 10-Jan", r12["CN90001"]["verdict"] == "ok" and r12["CN90001"]["population"] == "audited" and r12["CN90001"]["lines"][0]["detail"].endswith("on 2099-01-10 at the same amount"), note=r12.get("CN90001"))
    check("B2 12-Jan: CN90002 is an orphan (a credit note the spine holds, no bill row, no patient) -- counted, not judged", r12["CN90002"]["population"] == "orphan" and r12["CN90002"]["verdict"] == "no patient attributed" and r12["CN90002"]["amount_p"] > 0, note=r12.get("CN90002"))
    check("B3 12-Jan: summary counts 2, one audited, one orphan", s12["count"] == 2 and s12["audited"] == 1 and s12["orphans"] == 1, note=s12)
    r13, _ = day("2099-01-13")
    check("B4 13-Jan: CN90003 NEVER BOUGHT -- the patient never bought that item", r13["CN90003"]["verdict"] == "NEVER BOUGHT", note=r13.get("CN90003"))
    r14, _ = day("2099-01-14")
    check("B5 14-Jan: CN90004 RETURNED MORE THAN SOLD (0:5 against 0:2)", r14["CN90004"]["verdict"] == "RETURNED MORE THAN SOLD", note=r14.get("CN90004"))
    r15, _ = day("2099-01-15")
    check("B6 15-Jan: CN90005 REFUNDED MORE THAN PAID (rate 2500 against 2016)", r15["CN90005"]["verdict"] == "REFUNDED MORE THAN PAID", note=r15.get("CN90005"))
    r16, s16 = day("2099-01-16")
    check("B7 16-Jan: CN90006 has a bill row but the spine holds no lines -- 'no item detail', money from the bill row", r16["CN90006"]["population"] == "no item detail" and r16["CN90006"]["verdict"] == "not examinable" and r16["CN90006"]["amount_p"] == 100000, note=r16.get("CN90006"))
    r17, _ = day("2099-01-17")
    l17 = r17["CN90007"]["lines"][0]
    check("B8 the row shape is the old one: item_key = norm_item(name), expiry_ym 'YYYY-MM' (2/29 -> 2029-02 on 12-Jan; an odd print -> None), amount_p = the rate per pack, k20 beside",
          l17["expiry_ym"] is None and r12["CN90001"]["lines"][0]["expiry_ym"] == "2029-02" and l17["rate_p"] == 2016 and r12["CN90001"]["lines"][0]["item"] == "WALK ZYLORIC", note=(l17, r12["CN90001"]["lines"][0]))
    lines, src = fra.find_return_lines(c, "CN90001", "2099-01-12")
    check("B9 find_return_lines: by date and bill, item_key in the desk's shape, k20 beside", len(lines) == 1 and lines[0]["item_key"] == "WALK ZYLORIC" and lines[0]["k20"] == "WALK ZYLORIC" and "date and bill" in src, note=(lines, src))
    lines2, src2 = fra.find_return_lines(c, "CN90001", "2099-01-11")
    check("B10 find_return_lines: a wrong date falls back to the bill number and says the spine's date", len(lines2) == 1 and "dated 2099-01-12" in src2, note=src2)
    check("B11 find_return_lines: an unknown bill gives nothing, no guess from digits or amount", fra.find_return_lines(c, "CN99999", "2099-01-12", 100000) == ([], ""))
    rows_r, summ_r = fra.returns_for_range(c, "2099-01-01", "2099-01-31", "medical")
    check("B12 returns_for_range: the seven days, ten returns; nine from their bill rows, the orphan from its lines (0:1 at 2016 a pack = 202)", summ_r["days"] == 7 and summ_r["count"] == 10 and summ_r["value_p"] == 9 * 100000 + 202, note=summ_r)
    check("B13 return_days: the spine's days UNION the bill rows' day (16-Jan has no spine lines)", fra.return_days(c, "medical", "2099-01-01", "2099-01-31") == ["2099-01-12", "2099-01-13", "2099-01-14", "2099-01-15", "2099-01-16", "2099-01-17", "2099-01-18"] and fra.return_days(c, "clinic", "2099-01-01", "2099-01-31") == [], note=fra.return_days(c, "medical", "2099-01-01", "2099-01-31"))
    r18, _ = day("2099-01-18")
    check("B14 two sales on one day, no same-quantity match: the LARGER (1:0) is judged first -- 0:4 back reads 'quantity differs', never 'more than sold'", r18["CN90008"]["verdict"] == "ok" and r18["CN90008"]["lines"][0]["verdict"] == "bought, quantity differs" and "1:0" in r18["CN90008"]["lines"][0]["detail"], note=r18["CN90008"]["lines"])
    check("B15 two packs share the spine's 20-letter key: the return's OWN pack is judged first (the 15-pack at 4500 against the 15-pack sale; against the newer 10-pack at 3000 it would read REFUNDED MORE THAN PAID)", r18["CN90009"]["verdict"] == "ok" and r18["CN90009"]["lines"][0]["verdict"] == "ok", note=r18["CN90009"]["lines"])
    check("B16 a name of exactly 20 letters is kept whole (the sale report prints 20)", r18["CN90010"]["lines"][0]["item"] == "WALK TWENTYLETTERNAM" and r18["CN90010"]["lines"][0]["verdict"] == "ok", note=r18["CN90010"]["lines"])
    keep_sp = fra._spine
    fra._spine = lambda: None
    r13x, _ = day("2099-01-13")
    fra._spine = keep_sp
    class _Boom:
        def __getattr__(self, n):
            raise RuntimeError("walk: the spine vanished mid-read")
    keep2 = fra._spine
    fra._spine = lambda: _Boom()
    r13y, _ = day("2099-01-13")
    fra._spine = keep2
    check("B18 the spine vanishing mid-read (every door raises): a question, never an accusation; the money still counted", r13y["CN90003"]["verdict"] == "not examinable" and r13y["CN90003"]["amount_p"] == 100000, note=(r13y["CN90003"]["verdict"], r13y["CN90003"]["note"][:80]))
    check("B17 the spine unreadable at that moment: a question ('not examinable'), never NEVER BOUGHT; the money still counted", r13x["CN90003"]["verdict"] == "not examinable" and r13x["CN90003"]["amount_p"] == 100000, note=(r13x["CN90003"]["verdict"], r13x["CN90003"]["population"], r13x["CN90003"]["note"][:80]))
except Exception as e:                                               # noqa: BLE001
    check("B0 the engine answers", False, note=repr(e))

# ---- C: the callers ------------------------------------------------------------------------------------------------------------------
try:
    notes = returns_kinds.month_notes(c, "medical", "2099-01")
    check("C1 returns_kinds.month_notes: every return of the month, newest day first", [n["bill"] for n in notes][:3] == ["CN90008", "CN90009", "CN90010"] and len(notes) == 10, note=[n["bill"] for n in notes])
except Exception as e:                                               # noqa: BLE001
    check("C1 returns_kinds.month_notes: every return of the month, newest day first", False, note=repr(e))
try:
    import datetime as _d
    far = (_d.date(2099, 1, 20) - _d.date.today()).days
    n_add = finance_returns_escalate.escalate_day(c, "2099-01-13", "medical") if hasattr(finance_returns_escalate, "escalate_day") else None
    spot = c.execute("SELECT item_key, item_name, batch FROM stock_spot_check WHERE unit='medical' AND bill_no='CN90003'").fetchall()
    check("C2 the escalation writes the return's lines (from the spine) into the spot-check table: key, name, batch", [tuple(r) for r in spot] == [("WALK NEVER ITEM", "WALK NEVER ITEM", "NB1")], note=(n_add, [tuple(r) for r in spot]))
    c.execute("DELETE FROM stock_spot_check WHERE bill_no LIKE 'CN900%'"); c.commit()
    swept = finance_returns_escalate.escalate_recent(c, "medical", 30)
    spot2 = c.execute("SELECT bill_no FROM stock_spot_check WHERE unit='medical' AND bill_no='CN90003'").fetchall()
    check("C3 escalate_recent itself runs on the spine: the sweep reaches the 2099 days (its window ends in the future) and writes CN90003's spot check again", bool(swept) and len(spot2) == 1, note=(swept, spot2))
except Exception as e:                                               # noqa: BLE001
    check("C0 the escalation runs on the spine", False, note=repr(e))
# the approvals page's fallback count: its days from return_days (the function body runs only when returns_kinds is missing; proven on the text)
src_sa = open(os.path.join(FIN, "sanjeevni_approvals.py"), encoding="utf-8").read()
check("C4 sanjeevni_approvals: the Needs-you fallback takes its days from return_days, not from sale_line_item", "return_days(con, _unit, ym" in src_sa and "FROM sale_line_item" not in src_sa)
src_rk = open(os.path.join(FIN, "returns_kinds.py"), encoding="utf-8").read()
src_fe = open(os.path.join(FIN, "finance_returns_escalate.py"), encoding="utf-8").read()
src_fa = open(os.path.join(FIN, "finance_returns_audit.py"), encoding="utf-8").read()
check("C5 no caller under test reads sale_line_item any more; the audit reads sale_item for the patient only", all("sale_line_item" not in t for t in (src_rk, src_fe)) and "FROM sale_line_item" not in src_fa and "FROM sale_item s JOIN day_entry e" in src_fa)

# ---- D: older behaviour unchanged ---------------------------------------------------------------------------------------------------
check("D1 the money is finance_money's: Rs 1,000 credit note reads 1,000 from its bill row", r12["CN90001"]["amount_p"] == 100000 and r12["CN90001"]["money_from"].startswith("the bill row"), s677=False) if "r12" in dir() else check("D1 the money is finance_money's", False, s677=False)
check("D2 a WALK-IN identity is a question, not a verdict (unchanged)", fra._stub_identity(c, None) is None, s677=False)
check("D3 the row carries name, mobile last-4 masked, clinic id (unchanged shape)", "r12" in dir() and r12["CN90001"]["name"] == "WALK PATIENT" and r12["CN90001"]["mobile_last4"] == "0000" and r12["CN90001"]["clinic_id"] == "WALK999999", s677=False)

# ---- E: on the box only -- OLD = NEW over every real credit note since --since -----------------------------------------------------------
if a.box_spine and a.old_root:
    os.environ["SPINE_DB"] = a.box_spine
    c2 = sqlite3.connect(a.db, timeout=30); c2.row_factory = sqlite3.Row          # the untouched copy, read only
    sys.path.insert(0, os.path.join(a.old_root, "finance"))
    spec = importlib.util.spec_from_file_location("fra_old", os.path.join(a.old_root, "finance", "finance_returns_audit.py"))
    fra_old = importlib.util.module_from_spec(spec); spec.loader.exec_module(fra_old)
    def proof(since, label):
        today = (__import__("datetime").date.today() - __import__("datetime").timedelta(days=1)).isoformat()   # yesterday: today's CN may not be in sale_item yet
        days_old = [r[0] for r in c2.execute("SELECT DISTINCT business_date FROM sale_line_item WHERE unit='medical' AND is_return=1 AND business_date BETWEEN ? AND ? "
                                             "UNION SELECT DISTINCT e.business_date FROM sale_item s JOIN day_entry e ON e.id=s.day_entry_id WHERE e.unit='medical' "
                                             "AND s.service LIKE '%!_return' ESCAPE '!' AND e.business_date BETWEEN ? AND ?", (since, today, since, today))]
        days_new = fra.return_days(c2, "medical", since, today)
        diffs, same, n_old, n_new = [], 0, 0, 0
        for d in sorted(set(days_old) | set(days_new)):
            o = {r["bill"]: r for r in fra_old.returns_for_day(c2, d, "medical")[0]}
            n = {r["bill"]: r for r in fra.returns_for_day(c2, d, "medical")[0]}
            n_old += len(o); n_new += len(n)
            for b in sorted(set(o) | set(n)):
                if b not in o or b not in n:
                    diffs.append((d, b, "only in " + ("old" if b in o else "new"), "", "")); continue
                def key(r):
                    return (r["verdict"], r["amount_p"], r["population"], r["n_lines"], r["gross_p"], r["lines_unreadable"],
                            tuple(sorted(tuple(str(v) for v in (l["item"], l["qty_raw"], l["pack"], l["amount_p"], l["expiry_ym"], l["verdict"])) for l in r["lines"])))
                ko, kn = key(o[b]), key(n[b])
                if ko == kn:
                    same += 1
                else:
                    allowed = (ko[2] == "no item detail" and kn[2] == "audited" and ko[1] == kn[1])
                    word = "allowed: the spine holds the lines the old store lacked" if allowed else "NOT ALLOWED"
                    if allowed and kn[0] not in ("ok", "not examinable"):
                        word = "allowed, BUT A NEW VERDICT -- read it: %s" % kn[0]
                    diffs.append((d, b, word, ko[:4], kn[:4]))
        bad = [x for x in diffs if x[2] == "NOT ALLOWED" or x[2].startswith("only in")]
        print("  --  %s OLD = NEW since %s: days old %d / new %d; returns old %d / new %d; identical %d; different %d (allowed %d, NOT allowed %d)"
              % (label, since, len(days_old), len(days_new), n_old, n_new, same, len(diffs), len(diffs) - len(bad), len(bad)))
        for x in diffs[:80]:
            print("      %s %s %s old=%s new=%s" % x)
        return bad
    bad = proof(a.since, "THE GATE:")
    check("E1 old = new on every real credit note since %s -- the only difference allowed: a return the old store could not examine, the spine can, same money" % a.since,
          not bad, note="%d not allowed" % len(bad))
    if a.also_since:
        try:
            proof(a.also_since, "FOR THE RECORD (not a gate):")
        except Exception as e:                                       # noqa: BLE001 -- a record run never stops the gate
            print("  --  FOR THE RECORD (not a gate): the run since %s did not finish: %r" % (a.also_since, e))
c.close()

for n, ok, s_, note in res:
    print(("  ok  " if ok else "  RED ") + n + ("" if ok else ("   | " + note if note else "")))
g = sum(1 for _, ok, _, _ in res if ok)
if a.old:
    red = sum(1 for _, ok, s_, _ in res if not ok and s_); redold = sum(1 for _, ok, s_, _ in res if not ok and not s_)
    print("%d S677 check(s) red · %d older red · %d green" % (red, redold, g))
else:
    print("%d of %d green" % (g, len(res)))
