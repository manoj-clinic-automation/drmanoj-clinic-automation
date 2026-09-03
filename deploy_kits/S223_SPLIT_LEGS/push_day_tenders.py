#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
push_day_tenders.py -- S223: recover the split-payment legs, on the clinic PC.

THE OWNER: "give breakup details of any split payment also"

WHY THIS EXISTS AT ALL. The Day Revenue sheet records a bill's payment MODE but not its legs.
"Split Payment" is all it can say. The legs live one step upstream, in the raw Docterz export:

    1100 (Wallet: 600, Online Payment: 500)

and the live tracker's `split_payment()` looks for exactly two words -- cash, and online -- where
Docterz emits seven. Measured over the 79 raw exports this PC has retained: **26 bills whose
tender the old reader could not see in full, Rs 18,100 in total -- Debit Card 9,400, Wallet 7,100,
Patient APP 1,600.** No revenue was ever lost by this: the day's GRAND TOTAL comes from Bill
Amount, not from tender. What was lost was the SPLIT -- which of that money was cash and which was
not -- and that is the figure the bank has to agree with.

WHAT THIS DOES. Reads the retained exports, parses every tender token, and writes ONE file:

    <tracker>/outputs/Day_Tenders.csv

WHY THAT FOLDER AND NO OTHER. `outputs/` is already the folder Google Drive syncs -- it is where
`Staff_Action_Today_*.xlsx` comes from, and the VPS already reads that folder. So this needs NO new
push, NO new endpoint, NO new credential and NO change to the tracker itself. The file simply
appears beside the workbooks and the reader on the box picks it up.

WHAT IT WRITES, AND WHAT IT REFUSES TO WRITE. business date, clinic ID, invoice number, tender,
amount. **No patient name. No mobile number.** Neither is read out of the row at all. The clinic ID
is the join key and is already in every Day Revenue sheet in that same Drive folder.

READ-ONLY on everything except its own output file. It does not touch the tracker's code, its
database, its ledgers, or any file Docterz or the tracker owns.

    python push_day_tenders.py                 (from the tracker folder)
    python push_day_tenders.py --dry-run       parse and report, write nothing
"""
import argparse
import csv
import glob
import os
import re
import sys
import tempfile

CANON = {"cash": "Cash", "credit card": "Credit Card", "debit card": "Debit Card",
         "net banking": "Net Banking", "online payment": "Online Payment",
         "patient app": "Patient APP", "wallet": "Wallet"}
_PAIR = re.compile(r"([A-Za-z][A-Za-z .]*?)\s*:\s*([\d,]+(?:\.\d+)?)")
_LEAD = re.compile(r"\s*([\d,]+(?:\.\d+)?)")
_GATEWAY = re.compile(r"\s+(?:pay|order|txn|ref)[_-][A-Za-z0-9]{6,}\s*$", re.I)
OUT_NAME = "Day_Tenders.csv"
COLS = ["business_date", "clinic_id", "invoice_no", "tender", "amount_p", "source_file"]


class UnknownTender(ValueError):
    pass


def _num(x):
    if x is None:
        return 0.0
    s = str(x).replace(",", "").replace("₹", "").strip()
    if s in ("", "nan", "None", "#VALUE!", "-"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def _norm(k):
    return " ".join(str(k or "").strip().casefold().split())


def parse_tenders(amount_collected, mode_of_payment=""):
    """Every 'Name: amount' pair inside the bracket -- all seven tokens, case-insensitive,
    trailing spaces tolerated. An unrecognised token RAISES rather than being walked past."""
    raw = "" if amount_collected is None else str(amount_collected)
    out = {}
    pairs = _PAIR.findall(raw)
    if pairs:
        unknown = []
        for k, v in pairs:
            key = _norm(k)
            if key in CANON:
                out[CANON[key]] = out.get(CANON[key], 0.0) + _num(v)
            else:
                unknown.append(k.strip())
        if unknown:
            raise UnknownTender("unrecognised tender token(s) %r in %r" % (unknown, raw))
        return out
    m = _LEAD.match(raw)
    total = _num(m.group(1)) if m else 0.0
    if total == 0.0:
        return {}
    mode = _norm(_GATEWAY.sub("", str(mode_of_payment or "")))
    return {CANON.get(mode, mode_of_payment.strip() or "Unknown"): total}


def read_export(path):
    """Rows STOP at the 'Total' row, so no footer line is ever mistaken for a bill (F-93)."""
    rows = list(csv.reader(open(path, encoding="utf-8-sig")))
    if not rows:
        return [], None
    header, stop = rows[0], len(rows)
    for i, r in enumerate(rows[1:], start=1):
        c = [x.strip() for x in r]
        if len(c) > 2 and _norm(c[1]) == "total" and not c[2]:
            stop = i
            break
    body = []
    for r in rows[1:stop]:
        if not any(x.strip() for x in r):
            continue
        if len(r) >= 3 and not r[2].strip() and not r[0].strip().isdigit():
            continue                      # the clinic-name banner row
        body.append(dict(zip(header, r)))
    return body, header


def _iso(v):
    m = re.match(r"^(\d{2})-(\d{2})-(\d{4})", str(v or "").strip())
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--uploads", default=os.path.join(here, "uploads"))
    ap.add_argument("--outputs", default=os.path.join(here, "outputs"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if not os.path.isdir(a.uploads):
        sys.exit("REFUSING: %s is not a folder. Run this from the tracker folder, or pass "
                 "--uploads." % a.uploads)
    if not os.path.isdir(a.outputs):
        sys.exit("REFUSING: %s is not a folder. That folder is the one Drive syncs; without it "
                 "this file would go nowhere." % a.outputs)
    files = sorted(glob.glob(os.path.join(a.uploads, "consultation_report_*.csv")))
    print("retained exports: %d" % len(files))
    rows, bills, days, loud, money = [], 0, set(), [], 0.0
    for p in files:
        try:
            body, _ = read_export(p)
        except Exception as e:                                   # noqa: BLE001
            print("  unreadable, skipped: %s (%s)" % (os.path.basename(p), e))
            continue
        for r in body:
            try:
                t = parse_tenders(r.get("Amount collected"), r.get("Mode Of Payment") or "")
            except UnknownTender as e:
                loud.append("%s: %s" % (os.path.basename(p), e))
                continue
            nz = {k: v for k, v in t.items() if v}
            if len(nz) < 2:
                continue                                          # one tender: nothing to break up
            d = _iso(r.get("Consultation Date"))
            cid = str(r.get("Clinic Specific Id") or "").strip()
            if cid.endswith(".0"):
                cid = cid[:-2]
            inv = str(r.get("Invoice No.") or "").strip()
            if not d:
                continue
            bills += 1
            days.add(d)
            for tender, amt in sorted(nz.items()):
                money += amt
                rows.append([d, cid, inv, tender, int(round(amt * 100)),
                             os.path.basename(p)])
    print("split bills: %d, across %d days, Rs %d in %d legs"
          % (bills, len(days), int(money), len(rows)))
    if loud:
        print("LOUD -- unrecognised tender tokens, NOT guessed at:")
        for m in loud[:10]:
            print("   %s" % m)
    if a.dry_run:
        print("DRY RUN -- nothing written")
        return 0
    out = os.path.join(a.outputs, OUT_NAME)
    fd, tmp = tempfile.mkstemp(dir=a.outputs, suffix=".tmp")
    with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(COLS)
        w.writerows(sorted(rows))
    if os.path.exists(out):
        os.remove(out)
    os.rename(tmp, out)
    print("wrote %s  (%d rows)" % (out, len(rows)))
    print("Drive syncs that folder, so the VPS will see it within a few minutes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
