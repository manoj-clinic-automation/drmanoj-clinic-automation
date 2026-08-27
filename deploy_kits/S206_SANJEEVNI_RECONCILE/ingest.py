#!/usr/bin/python3
"""
ingest.py -- every movement of every item, 01-Apr-2026 to 26-Aug-2026, one shape.

THE THREE FAULTS THIS FILE EXISTS TO NOT REPEAT
 1 - WHOLE-UNIT SALES READ AS ZERO. A strip line writes qty '0:1'. A tube,
     vial, syringe or spray writes '1.0'. A reader that only understands
     'packs:loose' returns nothing for the second kind -- 2,807 lines, 16.3%
     of the year, silently zero. Those items then read as dead stock.
 2 - CREDIT NOTES COUNTED AS SALES. Sale bills run A00001-A03215; credit
     notes run CN00001-. A credit note is goods coming BACK. Subtracting it
     makes the error TWICE the quantity -- the exact signature seen on every
     fast mover: TYRO BR out by +704 against 352 CN units.
 3 - PACK SIZE TAKEN FROM WHICHEVER SOURCE WAS HANDY. '2:3' is 23 units at
     1*10 and 33 at 1*15. The pack size comes from packmap, which reports
     disagreement instead of picking a winner.
"""

import os
import re
import sys
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import packmap as PM

KIT = os.path.expanduser("~/mnt/dr-manoj-git/drmanoj-clinic-automation/deploy_kits")
sys.path.insert(0, os.path.join(KIT, "S206_SANJEEVNI_MARG_PURCHASE"))
sys.path.insert(0, os.path.join(KIT, "S205_LIVE_TOOLS", "manojz"))

import marg_report as MR
import marg_stock as MS
import marg_purchase as MP
import purchase_returns as PR
import xlsx_sheet

MR._open_sheet = xlsx_sheet.open_sheet_any     # runtime only; live file untouched

CN_RE = re.compile(r"^\s*CN", re.I)
DL = os.path.expanduser("~/mnt/Downloads")


def is_credit_note(bill):
    return bool(CN_RE.match(str(bill or "")))


# ------------------------------- sale --------------------------------
def sale_files():
    pats = ["margsync/MargArchive/SALE_BILLWISE/*/*.XLS",
            "MARG REPORTS CLAUDE/*.XLS", "MARG REPORTS CLAUDE/*.xlsx",
            "MARG REPORTS CLAUDE/SENT/*.XLS", "MARG REPORTS CLAUDE/New folder/*.XLS"]
    out = []
    for p in pats:
        out += sorted(glob.glob(os.path.join(DL, p)))
    return out


def read_sale():
    """Deduplicated sale item lines. Returns (lines, files, packobs)."""
    seen, lines, files, packobs = set(), [], [], []
    for p in sale_files():
        try:
            rep = MR.read_report(p, keep_items=True)
        except Exception as e:
            files.append((os.path.basename(p), 0, "SKIPPED: %s" % e))
            continue
        if not rep.get("ok"):
            files.append((os.path.basename(p), 0, "NOT OK"))
            continue
        n = 0
        for d in rep["days"]:
            for it in d.get("items") or []:
                ps = it.get("parsed") or {}
                key = (it["bill_date"], it["bill_no"], ps.get("seq"))
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                lines.append({"date": it["bill_date"], "bill": it["bill_no"],
                              "item": ps.get("item_name"), "pack": ps.get("pack"),
                              "strips": ps.get("qty_strips"), "loose": ps.get("qty_loose"),
                              "qty_raw": it.get("qty"), "amount_p": ps.get("amount_p"),
                              "expiry": ps.get("expiry_ym"), "batch": ps.get("batch")})
                if ps.get("item_name"):
                    packobs.append((ps["item_name"], ps.get("pack"), "sale"))
        files.append((os.path.basename(p), n, str(rep.get("title", "ok"))))
    return lines, files, packobs


def sale_units(ln, size):
    """
    Base units on one sale line. Returns (units, branch).
    The branch is named so a mis-read can be COUNTED, not guessed at.
    """
    st, lo = ln.get("strips"), ln.get("loose")
    if st is not None or lo is not None:
        return (PM.units(st or 0, lo or 0, size), "packs:loose")
    raw = str(ln.get("qty_raw") or "").strip()
    if not raw or raw == "-":
        return (0.0, "blank")
    try:
        return (float(raw), "whole")
    except ValueError:
        return (None, "unreadable")


# ------------------------------- stock -------------------------------
def stock_candidates():
    out = sorted(glob.glob(os.path.join(DL, "margsync/MargArchive/STOCK_CLOSING/*/*")))
    out += sorted(glob.glob(os.path.join(DL, "*.XLS")))
    out += sorted(glob.glob(os.path.join(DL, "margsync/MargArchive/_REFUSED/*")))
    return [p for p in out if p.lower().endswith((".xls", ".xlsx"))]


def find_stock(as_on, store):
    """Every export matching this date AND store. The STORE comes from the
    title row, never the filename (D188: a filename is not provenance)."""
    hits = []
    for p in stock_candidates():
        try:
            rep = MS.read_closing(p)
        except Exception:
            continue
        if rep["as_on"] == as_on and rep["store"] == store:
            hits.append(rep)
    return hits


# ------------------------------ purchase -----------------------------
def purchase_files():
    d = os.path.join(DL, "margsync/MargArchive/PURCHASE_ITEMWISE")
    return sorted(glob.glob(os.path.join(d, "*", "*.XLS"))) + \
           sorted(glob.glob(os.path.join(d, "*", "*.xlsx")))


def read_purchase():
    """Returns (rows, reports, packobs). Return rows carry is_return=True."""
    rows, reps, packobs = [], [], []
    for p in purchase_files():
        try:
            rep = MP.read_purchase(p)
        except Exception as e:
            reps.append((os.path.basename(p), 0, "SKIPPED: %s" % e))
            continue
        PR.apply(rep)
        for r in rep["rows"]:
            r["_period"] = rep.get("period")
            rows.append(r)
            if r.get("item"):
                packobs.append((r["item"], r.get("packing"), "purchase"))
        reps.append((os.path.basename(p), len(rep["rows"]), str(rep.get("period", "ok"))))
    return rows, reps, packobs
