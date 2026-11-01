#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s692.py -- kit S692_SPINE_BILL_DOT (01-Nov-2026, Sanjeevni session 375).

    python3 -B walk_s692.py --new <dir>     the walk on the kit's marg_read.py (<dir>/finance/spine/marg_read.py)   -> 'N of N green'
    python3 -B walk_s692.py --old <dir>     the same checks on the live file (the control)                            -> 'K S692 check(s) red . M green'

Every check stands on the walk's OWN made-up rows (F-998): a made-up supplier, made-up items, round made-up amounts -- no real export,
no real bill, no person.  The kit's rule: a BILL number typed with a stray trailing dot is read as its digits; a batch is not touched.
A control that does not go red on the live file proves nothing -- the checks marked S692 are the ones the live file must fail.
"""
import importlib.util
import sys

A = sys.argv[1:]
MODE, D = A[0], A[1]
spec = importlib.util.spec_from_file_location("marg_read_walk", D.rstrip("/") + "/finance/spine/marg_read.py")
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)

R = []          # (name, ok, s692)


def ck(name, ok, s692=True):
    R.append((name, bool(ok), s692))


# ---------------------------------------------------------------- 1. the number itself
billno = getattr(M, "billno", None)
ck("billno exists", billno is not None)
if billno:
    ck("billno: '3920.' -> '3920'", billno("3920.") == "3920")
    ck("billno: 'SF-123.' -> 'SF-123'", billno("SF-123.") == "SF-123")
    ck("billno: '3463.0' (the grid's float) -> '3463'", billno("3463.0") == "3463", s692=False)
    ck("billno: 'A000575' untouched", billno("A000575") == "A000575", s692=False)
    ck("billno: '003635' untouched (leading zeros kept)", billno("003635") == "003635", s692=False)
    ck("billno: '3920..' untouched (not the shape)", billno("3920..") == "3920..", s692=False)
    ck("billno: '.' untouched", billno(".") == ".", s692=False)
    ck("billno: '12.5' untouched (a real decimal is not a bill)", billno("12.5") == "12.5", s692=False)
ck("textno: a batch 'GT260049.' keeps its dot", M.textno("GT260049.") == "GT260049.", s692=False)
ck("textno: '160.0' -> '160' as before", M.textno("160.0") == "160", s692=False)
ck("READER_VERSION is S692.1", getattr(M, "READER_VERSION", "") == "S692.1")

# ---------------------------------------------------------------- 2. the purchase-line reader on made-up rows
T = "SUPPLIER/ITEM WISE PURCHASE STATEMENT FROM 01-01-2099 TO 31-01-2099"
HDR = ["BILL", "ITEM DESCRIPTION", "PACKING BATCH", "EXP.", "TAX", "QTY.", "FREE", "RATE", "DIS.", "AMOUNT NET RATE", "LOOS PURC. ?", "AMOUNT"]


def item(bill, name, qty, rate):
    amt = qty * rate
    return [bill, name, "1*10 WB%d" % qty, "12/99", "5.0", str(float(qty)), "0.0", str(float(rate)), "0.0",
            "%.2f %.2f" % (amt, rate), "%d %.2f" % (qty * 10, rate), str(float(amt))]


def lines_report(bill2):
    rows = [[T], [""], HDR, ["WALK SUPPLIER NINE"],
            item("9001.0", "WALK ITEM ONE", 10, 100.0),           # 1000
            item(bill2, "WALK ITEM TWO", 5, 200.0),               # 1000
            ["", "", "", "", "", "", "", "TOTAL", "", "2000.00 0.00", "", "2000.0"],
            ["GRAND", "TOTAL", "", "", "", "", "", "", "", "2000.00 0.00", "", "2000.0"]]
    return rows


def failed(R_):
    return [c[0] for c in R_.checks if not c[1]] + ["ANOMALY"] * len(R_.anomalies)


r_clean = M.read_purchase_lines(lines_report("9002.0"))
ck("lines: a clean made-up report reads ok", r_clean.ok, s692=False)
ck("lines: its two bills read 9001 and 9002", [l["bill"] for l in r_clean.data["lines"]] == ["9001", "9002"], s692=False)
r_dot = M.read_purchase_lines(lines_report("9002."))
ck("lines: the dotted bill '9002.' is read, no ANOMALY, the totals re-add", r_dot.ok)
ck("lines: the dotted bill is stored as 9002", len(r_dot.data["lines"]) == 2 and r_dot.data["lines"][1]["bill"] == "9002")
r_bad = M.read_purchase_lines(lines_report("walk-no-bill"))
ck("lines: a row that is no bill at all is still refused (ANOMALY)", not r_bad.ok and r_bad.anomalies, s692=False)
r_bad2 = M.read_purchase_lines(lines_report("9002.."))
ck("lines: '9002..' is still refused", not r_bad2.ok, s692=False)

# ---------------------------------------------------------------- 3. the bill-wise reader on made-up rows
TB = "BILL WISE PURCHASE STATEMENT FROM 01-01-2099 TO 31-01-2099"


def bills_report(bill2):
    return [[TB], [""], ["BILL NO.", "PARTY", "CASH", "CREDIT"], ["05-01-2099"],
            ["9001.0", "WALK SUPPLIER NINE", "", "1000.0"],
            [bill2, "WALK SUPPLIER NINE", "", "1000.0"],
            ["TOTAL", "2000.0", "", ""]]


b_dot = M.read_purchase_billwise(bills_report("9002."))
ck("billwise: the dotted bill reads ok and is stored as 9002", b_dot.ok and [b["bill"] for b in b_dot.data["bills"]] == ["9001", "9002"])
b_clean = M.read_purchase_billwise(bills_report("9002.0"))
ck("billwise: the clean report reads as before", b_clean.ok and [b["bill"] for b in b_clean.data["bills"]] == ["9001", "9002"], s692=False)
ck("both sides of the tie read the same number for the dotted bill",
   [l["bill"] for l in r_dot.data["lines"]][1:] == [b["bill"] for b in b_dot.data["bills"]][1:] == ["9002"])

# ---------------------------------------------------------------- 4. the sale reader untouched (a sale bill is A + digits; a dot is still refused)
ck("sale bill rule untouched: RE_BILL_SALE refuses 'A000575.'", not M.RE_BILL_SALE.match("A000575."), s692=False)

# ---------------------------------------------------------------- the verdict
for n, ok, s in R:
    print("  %s  %s%s" % ("ok " if ok else "RED", n, "  [S692]" if s else ""))
red = [x for x in R if not x[1]]
if MODE == "--new":
    print("%d of %d green" % (len(R) - len(red), len(R)) if not red else "%d RED of %d" % (len(red), len(R)))
    sys.exit(1 if red else 0)
else:
    red692 = [x for x in red if x[2]]
    other = [x for x in red if not x[2]]
    print("%d S692 check(s) red . %d green%s" % (len(red692), len(R) - len(red), " . %d OTHER red" % len(other) if other else ""))
    sys.exit(0)
