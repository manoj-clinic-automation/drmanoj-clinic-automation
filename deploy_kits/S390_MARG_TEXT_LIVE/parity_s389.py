#!/usr/bin/env python3
"""parity_s389.py -- the proof for kit S389: the SAME day, exported by Marg as Excel and as text, read by the
clinic's own readers, must give the same bills and the same medicine lines.

  python3 parity_s389.py --text report.txt --xls MARG.XLS --finance DIR --ingest DIR
Prints counts, dates and rupees only -- never a name or a number from a description.
"""
import argparse, os, sys, tempfile, importlib.util, json
ap = argparse.ArgumentParser()
ap.add_argument("--text", required=True); ap.add_argument("--xls", required=True)
ap.add_argument("--finance", required=True); ap.add_argument("--ingest", required=True)
ap.add_argument("--conv", default=os.path.dirname(os.path.abspath(__file__)))
a = ap.parse_args()
n, fails = 0, []
def check(label, cond, got=None):
    global n
    n += 1
    print(("  ok   " if cond else "  FAIL ") + label + ("" if got is None else "   [%s]" % (got,)))
    if not cond: fails.append(label)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path)); spec.loader.exec_module(m); return m

MT = load("marg_txt", os.path.join(a.conv, "marg_txt.py"))
xls, info = MT.convert(open(a.text, "rb").read())
tmp = os.path.join(tempfile.mkdtemp(), "converted.XLS"); open(tmp, "wb").write(xls)

FR = load("marg_report_fin", os.path.join(a.finance, "marg_report.py"))
A = FR.read_report(a.xls, keep_items=True); B = FR.read_report(tmp, keep_items=True)
check("finance reader: Marg's Excel reads clean", A["ok"], A["errors"][:2])
check("finance reader: the converted text reads clean", B["ok"], B["errors"][:2])
check("same report period and title", A["period"] == B["period"] and A["title"] == B["title"], (A["period"], B["period"]))
check("same GRAND TOTAL, to the paisa", A["grand"] == B["grand"], (A["grand"], B["grand"]))
check("same number of bills in the footer", A["footer_bills"] == B["footer_bills"], (A["footer_bills"], B["footer_bills"]))
da, db = A["days"], B["days"]
check("same days", [d["date"] for d in da] == [d["date"] for d in db])
diff_b, diff_i = [], []
for x, y in zip(da, db):
    if x["declared"] != y["declared"]:
        diff_b.append(("declared", x["date"]))
    for bx, by in zip(x["bills"], y["bills"]):
        for k in bx:
            if bx[k] != by.get(k):
                diff_b.append((bx["bill_no"], k))
    if len(x["bills"]) != len(y["bills"]):
        diff_b.append(("count", len(x["bills"]), len(y["bills"])))
    if len(x["items"]) != len(y["items"]):
        diff_i.append(("count", len(x["items"]), len(y["items"])))
    for ix, iy in zip(x["items"], y["items"]):
        for k in ("bill_no", "bill_date", "parsed"):
            if ix[k] != iy[k]:
                diff_i.append((ix["bill_no"], k, json.dumps(ix[k], default=str)[:90], json.dumps(iy[k], default=str)[:90]))
check("every bill identical in every field the server keeps (money, mode, ID, credit note)", not diff_b, diff_b[:4])
check("every medicine line identical as the server parses it", not diff_i, diff_i[:3])

# the router's verdict and the item lines the one door stores
sys.path.insert(0, a.ingest)
R = load("marg_router", os.path.join(a.ingest, "marg_router.py"))
MI = load("marg_ingest", os.path.join(a.ingest, "marg_ingest.py"))
try:
    MI._readers()
except Exception:
    pass
sigs = json.load(open(os.path.join(a.ingest, "signatures.json")))["signatures"]
sh = R.open_sheet(tmp); title, header, hrow, c0 = R.read_preamble(sh)
ident = R.identify(title, header, sigs) if hasattr(R, "identify") else None
check("the router identifies it as Marg's Excel is identified", ident is not None and "SALE_BILLWISE" in str(ident), str(ident)[:80])
la, lb = MI.sale_lines(a.xls), MI.sale_lines(tmp)
check("the one door's item lines are identical", la == lb, (len(la), len(lb), next(((i, x, y) for i, (x, y) in enumerate(zip(la, lb)) if x != y), None)))
print(("PARITY_S389 GREEN -- %d/%d" % (n, n)) if not fails else ("PARITY_S389 RED -- %d of %d failed" % (len(fails), n)))
sys.exit(1 if fails else 0)
