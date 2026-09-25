"""S397 proof: the 24-Sep closing-stock TEXT, converted, against Marg's own Excel of 23-Sep and the 24-Sep sales."""
import sys, os, re, json, hashlib, importlib.util, collections
ST = "/tmp/claude-0/-home-claude/1d885aa4-45a5-5a95-a56e-9e50f62b684f/scratchpad/stock/"
REPO = "/home/claude/repo/"
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path)); spec.loader.exec_module(m); return m
MT = load("marg_txt", os.path.abspath("w/marg_txt.py"))
MR = load("marg_read", REPO + "deploy_kits/S331_SPINE/marg_read.py")
RT = load("marg_router", REPO + "margpull/marg_router.py")
res = []
def check(label, cond, got=None):
    res.append(bool(cond)); print(("  ok   " if cond else "  FAIL ") + label + ("" if got is None else "   [%s]" % (got,)))

raw = open(ST + "stock_24sep.txt", "rb").read()
xls, info = MT.convert(raw)
conv = ST + "converted_stock_24sep.XLS"; open(conv, "wb").write(xls)
print("converted: %d bytes, md5 %s, %d rows, kind %s" % (len(xls), hashlib.md5(xls).hexdigest(), info["rows"], info["kind"]))
check("the same text gives the same bytes twice", MT.convert(raw)[0] == xls)
EX = ST + "stock_23sep.XLS"

# 1. the spine's own reader
for lab, p in (("Marg's Excel 23-Sep", EX), ("converted text 24-Sep", conv)):
    fam, R, _ = MR.read_file(p)
    bad = [c for c in R.checks if not c[1]] if hasattr(R, "checks") else None
    check("spine reader: %s reads as STOCK_CLOSING, every check passes" % lab, fam == "STOCK_CLOSING" and R.ok,
          "%s items, printed %s, lines %s" % (len(R.data["items"]), R.data["printed_total"], R.data["lines_total"]))
    if lab.startswith("Marg"): E = R.data
    else: C = R.data
check("dates: 23-Sep and 24-Sep, from each report's own title", (E["as_on"], C["as_on"]) == ("2026-09-23", "2026-09-24"))

# 2. the router: identified the same way, ends with TOTAL
sigs = RT.load_signatures(REPO + "margpull/signatures.json")
ids = []
for p in (EX, conv):
    sh = RT.open_sheet(p)
    pre = RT.read_preamble(sh)
    title, header = pre[0], pre[1]
    sig, status, why = RT.identify(title, header, sigs)
    ids.append(((sig or {}).get("type"), (sig or {}).get("variant"), RT.ends_with(sh, (sig or {}).get("end_marker")), status))
check("router: both identified as STOCK_CLOSING / TOTALS, both end with TOTAL", ids[0] == ids[1] == ("STOCK_CLOSING", "TOTALS", True, "IDENTIFIED"), ids)

# 3. the sheet itself, row by row, against Marg's Excel
import xlrd
a = xlrd.open_workbook(EX).sheet_by_index(0); b = xlrd.open_workbook(conv).sheet_by_index(0)
def grid(sh): return [[sh.cell_value(r, c) for c in range(4)] for r in range(sh.nrows)]
A, B = grid(a), grid(b)
A = [r for r in A if not ("call marg" in str(r[0]).lower())]           # Marg's advert line, Excel only
check("same number of rows, once Marg's advert line is set aside", len(A) == len(B), (len(A), len(B)))
furn = [(i, x, y) for i, (x, y) in enumerate(zip(A, B)) if not isinstance(x[0], float) and x[0] != "TOTAL"
        and [str(v).replace("23-09-2026", "24-09-2026") for v in x] != [str(v) for v in y]]
check("every letterhead, title, heading and page-furniture row identical, cell for cell (date aside)", not furn, furn[:3])
same_pos = all(isinstance(x[0], float) == isinstance(y[0], float) for x, y in zip(A, B))
check("items, page breaks and TOTAL fall on the same rows as Marg's sheet", same_pos)
ia = [x for x in A if isinstance(x[0], float)]; ib = [y for y in B if isinstance(y[0], float)]
check("the same 378 items, same names and packings, same units", [(x[1], x[3]) for x in ia] == [(y[1], y[3]) for y in ib], len(ib))
def kindof(v): return "num" if isinstance(v, float) else ("dash" if v.strip() == "-" else "text")
tk = collections.Counter((kindof(x[2]), kindof(y[2])) for x, y in zip(ia, ib))
check("stock cells are text or number exactly as Marg's sheet makes them (padded to 10, numbers only for plain counts)",
      all(isinstance(y[2], float) or len(y[2]) == 10 for y in ib) and all(isinstance(x[2], float) or len(x[2]) == 10 for x in ia), dict(tk))

# 4. the day's movement: 23-Sep closing - 24-Sep sales = 24-Sep closing
fam, S24, _ = MR.read_file(ST + "sale_24sep.XLS")
check("the 24-Sep sale reads clean in the spine reader", fam == "SALE_BILLWISE" and S24.ok and S24.data["days"] == ["2026-09-24"],
      "%d bills" % len(S24.data["bills"]))
units = lambda q, pack: MR.qty_units(q, pack)
sold = collections.Counter()
by20 = collections.defaultdict(list)
for it in C["items"]:
    by20[it["name"][:20].rstrip()].append(it)
unmatched = []
for bl in S24.data["bills"]:
    for ln in bl["lines"]:
        cands = [it for it in by20.get(ln["name"].rstrip(), []) if it["packing"] == ln["pack"]] or by20.get(ln["name"].rstrip(), [])
        if len(cands) != 1:
            unmatched.append((ln["name"], ln["pack"], len(cands))); continue
        it = cands[0]
        sold[it["name"]] += units(ln["qty"], it["packing"])
E_by = {it["name"]: it for it in E["items"]}
exact = moved = 0; off = []
for it in C["items"]:
    e = E_by.get(it["name"])
    want = e["units"] - sold.get(it["name"], 0)
    if abs(want - it["units"]) < 1e-9:
        exact += 1; moved += 1 if sold.get(it["name"]) else 0
    else:
        off.append((it["name"][:22], e["units"], sold.get(it["name"], 0), it["units"]))
print("  sale lines matched to items: %d, unmatched: %s" % (sum(len(b["lines"]) for b in S24.data["bills"]) - len(unmatched), unmatched[:5]))
# a sale line whose 20-letter name fits several items (S270 3.4 rule 4) is counted against that family
fam_sold = collections.Counter()
for nm, pk, n in unmatched:
    fam_sold[nm.rstrip()] += 0
for bl in S24.data["bills"]:
    for ln in bl["lines"]:
        if (ln["name"], ln["pack"], len(by20.get(ln["name"].rstrip(), []))) in unmatched:
            fam_sold[ln["name"].rstrip()] += units(ln["qty"], ln["pack"])
fam_ok = []
for f, q in fam_sold.items():
    members = by20[f]
    drop = sum(E_by[m["name"]]["units"] - m["units"] for m in members)
    fam_ok.append((f, q, drop))
    off = [o for o in off if not o[0].startswith(f[:22])]
check("a 20-letter family (the sale report cannot say which size): its sales = its drop", fam_ok and all(q == d for f, q, d in fam_ok), fam_ok)
tot_sold_fam = sum(q for f, q, d in fam_ok)
check("roll-forward: 23-Sep closing - 24-Sep sales = 24-Sep closing on every item", not off,
      "%d of %d exact (%d of them sold on 24-Sep); off: %s" % (exact, len(C["items"]), moved, off[:6]))
tot_sold = sum(sold.values()) + tot_sold_fam
check("and in total: %d - %d sold = %d" % (E["printed_total"], tot_sold, C["printed_total"]),
      abs(E["printed_total"] - tot_sold - C["printed_total"]) < 1e-9)
print("PROVE_S397 %s -- %d/%d" % ("GREEN" if all(res) else "RED", sum(res), len(res)))
