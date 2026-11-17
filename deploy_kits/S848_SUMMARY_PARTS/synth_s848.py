"""synth_s848.py <finance dir> <finance.db COPY> [--real] -- kit S848_SUMMARY_PARTS proof. Read only on the copy.
 T1-T6: the merge rule on made-up papers. E1-E2: s750_dealers on the copy with made-up summary papers of a real dealer's real month
 (parts add up -> agrees; a newer complete paper -> the newest speaks). --real (on the box): the live October of L.K. Drug House agrees.
 Last line: 'SYNTH S848: n PASS, m FAIL'."""
import os, sqlite3, sys
fin, dbp = sys.argv[1], sys.argv[2]
REAL = "--real" in sys.argv
sys.path.insert(0, fin)
os.environ.setdefault("FINANCE_DB", dbp)
import scan_register as SR                                   # noqa: E402
SR._pa()._assets_db = os.environ.get("ASSETS_COPY") or "/nonexistent/assets.db"   # a COPY on the box (--real); never the live file
P = F = 0


def ok(c, what):
    global P, F
    if c:
        P += 1
        print("PASS", what)
    else:
        F += 1
        print("FAIL", what)


def paper(i, lines, read=True, vendor="", day="2026-11-01"):
    fig = sum(l["amount_p"] for l in lines if l["kind"] == "bill") - sum(l["amount_p"] for l in lines if l["kind"] == "credit")
    return dict(id=i, stamp_no="B-%04d" % (i % 10000), vendor=vendor, reading={}, read=read, lines=lines, figure_p=fig if read else None,
                bills_p=fig, credits_p=0, total_bills_p=None, opening_p=None, closing_p=None, day=day, month="2026-10", read_error="")


def b(no, amt, date="2026-10-05", kind="bill"):
    return dict(kind=kind, no=no, date=date, amount_p=amt)


has = hasattr(SR, "_s848_one")
ok(has, "T0 the S848 block is in the page")
if has:
    a, c = paper(296, [b("90058", 95800), b("RT092205", 269800)]), paper(332, [b("96923", 721400), b("98843", 134700)])
    m = SR._s848_one([c, a])
    ok(m["figure_p"] == 95800 + 269800 + 721400 + 134700 and len(m["parts"]) == 2 and m["id"] == 332 and m["stamp_no"] == "B-0296 + B-0332",
       "T1 two papers with different bills add up (figure, parts, the newest's id, both stamps)")
    rev = paper(400, [b("90058", 95800), b("96923", 721400)])
    ok(SR._s848_one([a, rev]) is rev, "T2 a bill on both papers: a revision -- the newest speaks")
    un = paper(401, [b("1", 100)], read=False)
    ok(SR._s848_one([a, un]) is un, "T3 a paper not read: the newest speaks, as before")
    ok(SR._s848_one([a]) is a, "T4 one paper: unchanged")
    cr1, cr2 = paper(410, [b("5", 1000), b("CN1", 500, kind="credit")]), paper(411, [b("6", 2000), b("CN1", 500, kind="credit")])
    ok(SR._s848_one([cr1, cr2]) is cr2, "T5 a credit on both papers: the newest speaks")
    h = SR._s848_parts_html(m, "/finance/purchase")
    ok("2 papers" in h and "B-0296" in h and "/api/s738/scan/296" in h and SR._s848_parts_html(a, "/x") == "", "T6 the opened line names both papers")

con = sqlite3.connect(dbp)
con.row_factory = sqlite3.Row
month = "2026-10"
rows = con.execute("SELECT supplier_norm, supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE COALESCE(month, substr(bill_date,1,7))=? "
                   "AND amount_p>0 ORDER BY supplier_norm, bill_date, bill_no", (month,)).fetchall()
by = {}
for r in rows:
    by.setdefault(r["supplier_norm"], []).append(r)
key = next((k for k in sorted(by) if k and k.startswith("L.K") and len(by[k]) >= 3), None) or next((k for k in sorted(by) if len(by[k]) >= 3), None)
d0 = next((d for d in SR.s750_dealers(con, month, scans={}) if d["key"] == key), None)
ok(key is not None and d0 is not None, "E0 a real dealer of %s with 3+ bills on the copy (%s)" % (month, key))
if d0 is not None:
    bl = [r for r in by[key]]
    eff = {x["bill_no"] for x in d0["bills"] if x["amount_p"] > 0}
    bl = [r for r in bl if r["bill_no"] in eff]
    neg = [x for x in d0["bills"] if x["amount_p"] < 0]
    L = lambda rs_: [b(r["bill_no"], int(r["amount_p"]), r["bill_date"]) for r in rs_]
    credits = [b(x["bill_no"], -x["amount_p"], x["date"], kind="credit") for x in neg]
    A = paper(990001, L(bl[:2]), vendor=bl[0]["supplier"], day="2026-10-15")
    B = paper(990002, L(bl[2:]) + credits, vendor=bl[0]["supplier"], day="2026-11-08")
    B["figure_p"] = B["figure_p"]
    d = next((x for x in SR.s750_dealers(con, month, scans={990001: A, 990002: B}) if x["key"] == key), None)
    ok(d is not None and d["state"] == "agrees" and len((d["summary"] or {}).get("parts") or []) == 2,
       "E1 the dealer's month in two papers (%d + %d bills) agrees with Marg: %s" % (2, len(bl) - 2, d and (d["state"], d["words"])))
    Cn = paper(990003, L(bl) + credits, vendor=bl[0]["supplier"], day="2026-11-09")
    d2 = next((x for x in SR.s750_dealers(con, month, scans={990001: A, 990003: Cn}) if x["key"] == key), None)
    ok(d2 is not None and d2["state"] == "agrees" and not (d2["summary"] or {}).get("parts") and d2["summary"]["id"] == 990003,
       "E2 a newer complete paper over a part: the newest speaks alone (%s)" % (d2 and d2["state"]))
if REAL:
    dr = next((x for x in SR.s750_dealers(con, month) if x["key"].startswith("L.K")), None)
    ok(dr is not None and dr["state"] == "agrees", "R1 the live October of L.K. Drug House agrees: %s" % (repr(dr and (dr["state"], dr["words"], (dr["summary"] or {}).get("stamp_no"))),))
print("SYNTH S848: %d PASS, %d FAIL" % (P, F))
