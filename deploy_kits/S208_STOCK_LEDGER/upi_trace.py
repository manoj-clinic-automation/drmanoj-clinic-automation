#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""upi_trace.py — the bank is the truth. Which bills were really UPI, and who
                  rang them as cash.

THE OWNER'S RULING, AND IT IS FINAL
    Darpan does not ring every UPI sale as UPI. So the payment mode typed into
    Marg is a claim, not a fact. **The bank statement is the sole source of
    truth** for UPI, card, and anything else that settles -- they are all in
    the bank's list.

    So this does not start from Marg and look for a difference. It starts from
    the BANK, and asks of each settled transaction: which sale bill is this?
    The amount answers it -- a bank transaction lands on a bill's total, or on
    the non-cash part of one, exactly or within a rupee.

WHAT COMES OUT, AND WHAT EACH PART IS FOR
    1  BANK -> BILL, and Darpan agreed        nothing to do
    2  BANK -> BILL, but rung as CASH         *** the feedback list. These bills
                                              were paid into the bank and rung
                                              as cash. The drawer is expected to
                                              hold money that was never in it.
    3  BANK, no bill found                    a look: part payment, a split, or
                                              a bill on another day
    4  BILL says non-cash, no bank line       the reverse gap
    5  BILLS WITH NO PATIENT IDENTITY         no clinic ID, no name, no mobile.
                                              **Counted as sale in full** -- the
                                              money is not in doubt -- and
                                              flagged, because the name is.

    That fifth list IS the sale variance. It is not missing money. It is
    missing identity, and the two have been read as one thing for months.

    python3 upi_trace.py --date 27-08-2026 --bank <statement.xlsx|.csv>
    python3 upi_trace.py --date 27-08-2026            (bills only, no bank file)

Writes a page you can sit in front of with Darpan, and a CSV. Reads only --
nothing is sent anywhere, nothing on the server is touched.
"""
import argparse
import csv
import datetime as dt
import glob
import html
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
for _sub in ("S206_SANJEEVNI_MARG_PURCHASE", os.path.join("S205_LIVE_TOOLS", "manojz")):
    _p = os.path.join(KITS, _sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import xlsx_sheet                      # noqa: E402
import marg_report as MR               # noqa: E402
MR._open_sheet = xlsx_sheet.open_sheet_any

DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
DEF_OUT = r"D:\Downloads\margsync\_analysis"
TOLERANCE_P = 100          # one rupee. Rounding, never a real difference.


def R(p):
    """paise -> rupees, as people write them."""
    return "%.2f" % (int(p or 0) / 100.0)


def dkey(s):
    s = str(s or "").strip()
    for f in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%b-%y", "%d-%b-%Y"):
        try:
            return dt.datetime.strptime(s.upper() if "%b" in f else s, f).date()
        except ValueError:
            pass
    return None


def paise(v):
    if v is None:
        return None
    try:
        return int(round(float(str(v).replace(",", "").replace("INR", "").strip()) * 100))
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ Marg
def bills_for(archive, date):
    """Every bill Marg issued on this day, with its own cash / non-cash split."""
    out, files = [], []
    pats = [os.path.join(archive, "SALE_BILLWISE", "*", "*.XLS"),
            os.path.join(archive, "SALE_BILLWISE", "*", "*.xlsx")]
    seen = set()
    for p in sorted(sum([glob.glob(x) for x in pats], [])):
        try:
            rep = MR.read_report(p, keep_items=False)
        except Exception:                                      # noqa: BLE001
            continue
        if not rep.get("ok"):
            continue
        for d in rep.get("days") or []:
            if dkey(d.get("date")) != date:
                continue
            files.append(os.path.basename(p))
            for b in d.get("bills") or []:
                if b.get("bill_no") in seen:
                    continue
                seen.add(b.get("bill_no"))
                out.append(b)
    out.sort(key=lambda b: str(b.get("bill_no") or ""))
    return out, files


# ------------------------------------------------------------------ bank
def bank_rows(path, date):
    """Settled transactions for the day, from the merchant statement.

    Accepts the ICICI MPR workbook, or a CSV with the same column names --
    because a file you can open in Notepad is a file you can check, and the
    matcher must be testable without waiting for a statement to arrive.
    """
    if not path:
        return [], "no bank file given"
    if not os.path.exists(path):
        return [], "bank file not found: %s" % path
    rows = []
    if path.lower().endswith(".csv"):
        with io.open(path, "r", encoding="utf-8-sig", newline="") as fh:
            rd = list(csv.reader(fh))
        table = [[c for c in r] for r in rd]
    else:
        sh = xlsx_sheet.open_sheet_any(path)
        table = []
        for i in range(sh.nrows):
            table.append([_txt(c) for c in sh.row(i)])
    if not table:
        return [], "the bank file is empty"

    hdr_i, hdr = None, None
    for i, r in enumerate(table[:30]):
        low = [str(c).strip().lower() for c in r]
        if any("transaction amount" == c or c == "amount" for c in low):
            hdr_i, hdr = i, low
            break
    if hdr is None:
        return [], "could not find a 'Transaction Amount' column in the bank file"

    def col(*names):
        for n in names:
            if n in hdr:
                return hdr.index(n)
        return None

    c_amt = col("transaction amount", "amount")
    c_d1 = col("txn dt", "transaction date", "date")
    c_rrn = col("rrn", "reference number", "reference no")
    c_mode = col("mode of payment", "mode", "payment mode")
    c_time = col("transaction date", "time", "txn time")

    for r in table[hdr_i + 1:]:
        joined = " ".join(str(c) for c in r)
        if "Grand Total" in joined or "Subtotal" in joined:
            continue
        amt = paise(r[c_amt]) if c_amt is not None and c_amt < len(r) else None
        d = dkey(str(r[c_d1]).split(" ")[0]) if c_d1 is not None and c_d1 < len(r) else None
        if amt is None or d is None or d != date:
            continue
        rows.append({"amount_p": amt,
                     "rrn": str(r[c_rrn]).strip() if c_rrn is not None and c_rrn < len(r) else "",
                     "mode": (str(r[c_mode]).strip() if c_mode is not None
                              and c_mode < len(r) else "") or "UPI",
                     "time": str(r[c_time]).strip() if c_time is not None
                             and c_time < len(r) else ""})
    rows.sort(key=lambda x: -x["amount_p"])
    return rows, None


def _txt(cell):
    s = str(cell)
    if ":" in s and s.split(":", 1)[0] in ("text", "number", "empty", "date",
                                           "bool", "error", "blank"):
        s = s.split(":", 1)[1]
    return s.strip().strip("'")


# --------------------------------------------------------------- matching
def match(bank, bills):
    """Bank first. Each settled transaction looks for the bill it paid.

    A bank line can land on either of two amounts on a bill:
      * the bill's NON-CASH part, when Darpan already marked some of it
      * the bill's WHOLE net, when he rang the entire bill as cash
    The second case is the one worth finding, so it is never ruled out.

    One to one, exact before near, and a bill is used once. Anything unmatched
    stays unmatched -- a forced match would invent a fact.
    """
    used = set()
    cand = []
    for i, b in enumerate(bills):
        if b.get("is_credit_note"):
            continue
        nc = int(b.get("noncash_p") or 0)
        net = int(b.get("net_p") or 0)
        if nc > 0:
            cand.append((nc, i, "non-cash part"))
        if net > 0 and net != nc:
            cand.append((net, i, "whole bill"))

    matched, unmatched_bank = [], []
    for t in bank:
        best = None
        for amt, i, which in cand:
            if i in used:
                continue
            d = abs(amt - t["amount_p"])
            if d > TOLERANCE_P:
                continue
            rank = (d, 0 if which == "non-cash part" else 1)
            if best is None or rank < best[0]:
                best = (rank, amt, i, which, d)
        if best is None:
            unmatched_bank.append(t)
            continue
        _, amt, i, which, d = best
        used.add(i)
        b = bills[i]
        booked_noncash = int(b.get("noncash_p") or 0) > 0
        matched.append({"txn": t, "bill": b, "on": which, "off_by_p": d,
                        "agreed": booked_noncash})
    unmatched_bills = [b for i, b in enumerate(bills)
                       if i not in used and int(b.get("noncash_p") or 0) > 0
                       and not b.get("is_credit_note")]
    return matched, unmatched_bank, unmatched_bills


def unidentified(bills):
    """No clinic ID, no usable name, no mobile. The money is not in doubt."""
    out = []
    for b in bills:
        cid = str(b.get("clinic_id") or "").strip()
        nm = re.sub(r"[^A-Z]", "", str(b.get("patient_name") or "").upper())
        ph = re.sub(r"\D", "", str(b.get("phone") or ""))
        if not cid and not ph and nm in ("", "CASH", "CUSTOMER", "SELF"):
            out.append(b)
    return out


# ----------------------------------------------------------------- output
def render(date, bills, bank, bank_err, matched, ub, ubill, unid, files):
    tot_net = sum(int(b.get("net_p") or 0) for b in bills if not b.get("is_credit_note"))
    tot_cash = sum(int(b.get("cash_p") or 0) for b in bills if not b.get("is_credit_note"))
    tot_nc = sum(int(b.get("noncash_p") or 0) for b in bills if not b.get("is_credit_note"))
    bank_tot = sum(t["amount_p"] for t in bank)
    cns = [b for b in bills if b.get("is_credit_note")]
    cn_p = sum(int(b.get("net_p") or 0) for b in cns)
    wrong = [m for m in matched if not m["agreed"]]
    wrong_p = sum(m["txn"]["amount_p"] for m in wrong)

    E = html.escape
    o = []
    A = o.append
    A("<!doctype html><meta charset='utf-8'>")
    A("<title>UPI trace %s</title>" % date.strftime("%d-%m-%Y"))
    A("<style>body{font:15px/1.5 system-ui,sans-serif;margin:0;padding:18px;"
      "background:#faf9f7;color:#1b1b1b;max-width:960px}"
      "h1{font-size:20px;margin:0 0 4px}h2{font-size:16px;margin:26px 0 8px}"
      ".sub{color:#666;font-size:13px;margin-bottom:18px}"
      "table{border-collapse:collapse;width:100%;font-size:14px;margin:6px 0}"
      "th,td{padding:6px 8px;border-bottom:1px solid #e3e0da;text-align:left}"
      "th{background:#f0ede8;font-weight:600}td.n{text-align:right;"
      "font-variant-numeric:tabular-nums}"
      ".big{background:#fff;border:1px solid #e3e0da;border-radius:8px;"
      "padding:12px 14px;margin:10px 0}"
      ".red{border-left:4px solid #b3261e}.amber{border-left:4px solid #a8730a}"
      ".green{border-left:4px solid #2e6b34}.grey{border-left:4px solid #999}"
      ".k{color:#666;font-size:13px}.v{font-size:22px;font-variant-numeric:tabular-nums}"
      ".row{display:flex;gap:22px;flex-wrap:wrap}</style>")
    A("<h1>UPI trace — %s</h1>" % date.strftime("%d %B %Y"))
    A("<div class='sub'>The bank is the truth. Every settled transaction is "
      "matched to the bill it paid.<br>Source: %s</div>"
      % E(", ".join(files) or "no Marg sale report found"))

    A("<div class='row'>")
    for k, v in (("bills", str(len([b for b in bills if not b.get('is_credit_note')]))),
                 ("net sale", R(tot_net)), ("rung as cash", R(tot_cash)),
                 ("rung as non-cash", R(tot_nc)),
                 ("bank settled", R(bank_tot) if bank else "—")):
        A("<div class='big'><div class='k'>%s</div><div class='v'>%s</div></div>" % (k, v))
    A("</div>")
    A("<div class='big grey'>Sale bills only: <b>%s</b> = cash %s + non-cash %s. "
      "Marg's day total is <b>%s</b> — this plus <b>%d credit note(s)</b> "
      "at %s. A credit note is goods coming BACK, carried as a negative, so it "
      "is never matched against the bank.</div>"
      % (R(tot_net), R(tot_cash), R(tot_nc), R(tot_net + cn_p), len(cns), R(cn_p)))

    if bank_err:
        A("<div class='big amber'><b>No bank file read.</b> %s<br>"
          "Everything below the bank line needs one. Drop the day's merchant "
          "statement in and run again.</div>" % E(bank_err))

    A("<h2>1 · Rung as CASH, but the money went to the bank</h2>")
    if wrong:
        A("<div class='big red'><b>%d bill(s), %s.</b> These were paid into the "
          "bank and entered as cash. The drawer is expected to hold money that "
          "was never in it — that is the shortfall, and this is the list to go "
          "through with Darpan.</div>" % (len(wrong), R(wrong_p)))
        A("<table><tr><th>bill</th><th>patient</th><th class='n'>bill total</th>"
          "<th class='n'>bank</th><th>matched on</th><th>ref</th></tr>")
        for m in sorted(wrong, key=lambda m: -m["txn"]["amount_p"]):
            b = m["bill"]
            A("<tr><td>%s</td><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
              "<td>%s%s</td><td>%s</td></tr>"
              % (E(str(b.get("bill_no"))), E(str(b.get("patient_name") or "")),
                 R(b.get("net_p")), R(m["txn"]["amount_p"]), m["on"],
                 "" if m["off_by_p"] == 0 else " (off by %s)" % R(m["off_by_p"]),
                 E(m["txn"].get("rrn", ""))))
        A("</table>")
    elif bank:
        A("<div class='big green'>Nothing. Every bank transaction matched a bill "
          "that was already entered as non-cash.</div>")

    A("<h2>2 · Bank transactions with no bill</h2>")
    if ub:
        A("<div class='big amber'>%d transaction(s), %s. A part payment, two "
          "bills paid together, or a bill from another day.</div>"
          % (len(ub), R(sum(t["amount_p"] for t in ub))))
        A("<table><tr><th class='n'>amount</th><th>mode</th><th>ref</th>"
          "<th>time</th></tr>")
        for t in ub:
            A("<tr><td class='n'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
              % (R(t["amount_p"]), E(t.get("mode", "")), E(t.get("rrn", "")),
                 E(t.get("time", ""))))
        A("</table>")
    elif bank:
        A("<div class='big green'>None. Every settled transaction found its bill.</div>")

    A("<h2>3 · Entered as non-cash, but nothing settled</h2>")
    if ubill:
        A("<div class='big amber'>%d bill(s), %s. Entered as non-cash with no "
          "bank line to show for it.</div>"
          % (len(ubill), R(sum(int(b.get("noncash_p") or 0) for b in ubill))))
        A("<table><tr><th>bill</th><th>patient</th><th class='n'>non-cash</th></tr>")
        for b in ubill:
            A("<tr><td>%s</td><td>%s</td><td class='n'>%s</td></tr>"
              % (E(str(b.get("bill_no"))), E(str(b.get("patient_name") or "")),
                 R(b.get("noncash_p"))))
        A("</table>")
    elif bank:
        A("<div class='big green'>None.</div>")

    A("<h2>4 · Bills with no patient identity</h2>")
    A("<div class='big grey'><b>%d bill(s), %s — counted as sale in full.</b> "
      "No clinic ID, no name, no mobile. <b>The money is not in doubt; the name "
      "is.</b> This is the sale variance, and it has never been missing money.</div>"
      % (len(unid), R(sum(int(b.get("net_p") or 0) for b in unid))))
    if unid:
        A("<table><tr><th>bill</th><th class='n'>net</th><th class='n'>cash</th>"
          "<th class='n'>non-cash</th></tr>")
        for b in unid:
            A("<tr><td>%s</td><td class='n'>%s</td><td class='n'>%s</td>"
              "<td class='n'>%s</td></tr>"
              % (E(str(b.get("bill_no"))), R(b.get("net_p")), R(b.get("cash_p")),
                 R(b.get("noncash_p"))))
        A("</table>")

    A("<h2>5 · Matched and agreed</h2>")
    ok = [m for m in matched if m["agreed"]]
    A("<div class='big green'>%d transaction(s), %s. Nothing to do.</div>"
      % (len(ok), R(sum(m["txn"]["amount_p"] for m in ok))))
    return "\n".join(o)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--date", required=True, help="dd-mm-yyyy")
    ap.add_argument("--bank", default=None, help="the day's merchant statement")
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--out", default=DEF_OUT)
    a = ap.parse_args(argv)

    date = dkey(a.date)
    if date is None:
        print("--date must be dd-mm-yyyy")
        return 2
    bills, files = bills_for(a.archive, date)
    if not bills:
        print("no Marg sale report for %s in %s" % (a.date, a.archive))
        return 2
    bank, err = bank_rows(a.bank, date)
    matched, ub, ubill = match(bank, bills)
    unid = unidentified(bills)

    live = [b for b in bills if not b.get("is_credit_note")]
    wrong = [m for m in matched if not m["agreed"]]
    cns = [b for b in bills if b.get("is_credit_note")]
    cn_p = sum(int(b.get("net_p") or 0) for b in cns)
    print("%s : %d sale bill(s), net %s, cash %s, non-cash %s"
          % (a.date, len(live),
             R(sum(int(b.get("net_p") or 0) for b in live)),
             R(sum(int(b.get("cash_p") or 0) for b in live)),
             R(sum(int(b.get("noncash_p") or 0) for b in live))))
    print("          plus %d credit note(s) %s -> Marg day total %s"
          % (len(cns), R(cn_p),
             R(sum(int(b.get("net_p") or 0) for b in live) + cn_p)))
    if err:
        print("bank: %s" % err)
    else:
        print("bank : %d settled transaction(s), %s"
              % (len(bank), R(sum(t["amount_p"] for t in bank))))
        print("  rung as CASH but settled in the bank : %d bill(s), %s"
              % (len(wrong), R(sum(m["txn"]["amount_p"] for m in wrong))))
        print("  bank line with no bill               : %d" % len(ub))
        print("  non-cash bill with no bank line      : %d" % len(ubill))
    print("  bills with no patient identity       : %d, %s  (counted in full)"
          % (len(unid), R(sum(int(b.get("net_p") or 0) for b in unid))))

    os.makedirs(a.out, exist_ok=True)
    stem = "UPI_TRACE_%s" % date.strftime("%Y-%m-%d")
    hp = os.path.join(a.out, stem + ".html")
    with io.open(hp, "w", encoding="utf-8") as fh:
        fh.write(render(date, bills, bank, err, matched, ub, ubill, unid, files))
    cp = os.path.join(a.out, stem + ".csv")
    with io.open(cp, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["bucket", "bill", "patient", "net", "cash", "noncash",
                    "bank_amount", "matched_on", "ref"])
        for m in wrong:
            b = m["bill"]
            w.writerow(["RUNG AS CASH, SETTLED IN BANK", b.get("bill_no"),
                        b.get("patient_name"), R(b.get("net_p")), R(b.get("cash_p")),
                        R(b.get("noncash_p")), R(m["txn"]["amount_p"]), m["on"],
                        m["txn"].get("rrn", "")])
        for t in ub:
            w.writerow(["BANK LINE, NO BILL", "", "", "", "", "",
                        R(t["amount_p"]), "", t.get("rrn", "")])
        for b in ubill:
            w.writerow(["NON-CASH BILL, NO BANK LINE", b.get("bill_no"),
                        b.get("patient_name"), R(b.get("net_p")), R(b.get("cash_p")),
                        R(b.get("noncash_p")), "", "", ""])
        for b in unid:
            w.writerow(["NO PATIENT IDENTITY", b.get("bill_no"),
                        b.get("patient_name"), R(b.get("net_p")), R(b.get("cash_p")),
                        R(b.get("noncash_p")), "", "", ""])
    print("\nwritten:\n  %s\n  %s" % (hp, cp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
