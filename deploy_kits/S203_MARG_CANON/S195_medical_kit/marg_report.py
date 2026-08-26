#!/usr/bin/python3
"""
marg_report.py — read a Marg ERP 9+ "BILL WISE SALES STATEMENT" .XLS export
and turn it into clean, checked rows the clinic-finance module can ingest.

WHY THIS EXISTS
    finance_ingest.py already registers  ADAPTERS["marg_export"] = adapter_csv,
    and adapter_csv wants a delimited file with a header row. A raw Marg export
    is not that: it is a printed report converted to a grid, complete with
    repeated page headers, repeated column headers, per-day sections, drug-detail
    lines under each bill, "C/F :" carry-forward rows and page footers.

    So this module sits UPSTREAM. It reads the .xls, throws the furniture away,
    checks the file's own arithmetic, and writes a plain CSV that adapter_csv can
    read with nothing but a column map. finance_ingest.py is NOT modified. (D313:
    the line source is an adapter selected by a column map, not by code.)

WHAT IT REFUSES, AND WHY
    A file that cannot be trusted is refused with a reason, never half-parsed:
      · wrong report variant  — the 3-column "Summary-1" layout has no CASH
        column, so cash/UPI cannot be derived from it at all;
      · truncated export      — no GRAND TOTAL row means the export stopped
        early. Observed for real on 15-08-2026: a month-to-date run with item
        detail ran past 44 pages and stopped on the 6th of fifteen days;
      · arithmetic mismatch   — a day whose bill rows do not sum to its own
        DAY TOTAL row.
    Silence is the failure mode this project keeps paying for. This module
    shouts instead.

MONEY
    Integer paise throughout (D313). Values are read as text and converted, never
    trusted as floats: in a real export the positive amounts arrive as numeric
    cells while the negative credit notes arrive as TEXT with leading spaces
    (' -1150.00'). A reader that trusts the cell type drops every refund.

    cash    = the CASH column
    noncash = NET AMT. - CASH          (UPI and/or credit)
    The .CASH/.UPI "D.R." field is NOT used to split payment. It was measured
    wrong: on 14-08-2026 it labelled 23 of 23 bills .CASH on a fortnight where
    36.9% of net was non-cash. It is carried through as a label only.

PATIENT IDENTITY
    Marg writes the description as   "<phone> <NAME> <clinic id>"  — the clinic
    ID is LAST. finance_ingest.split_clinic_id() expects it FIRST, so it returns
    None for every real Marg line and every bill would land on WALK-IN. This
    module therefore extracts clinic_id itself and emits it as its own column,
    so split_clinic_id() is never asked to guess.

DEPENDENCY
    xlrd (pure python, reads legacy BIFF .xls).  pip install xlrd
"""

import argparse
import csv
import json
import os
import re
import sys

# --------------------------------------------------------------------------- #
# layout constants — derived from real exports, not from memory (D172)
# --------------------------------------------------------------------------- #

HEADER_9 = ["BILL NO.", "DESCRIPTION", "D.R.", "GROSS AMT.", "DISCOUNT",
            "TAX", "DR/CR", "NET AMT.", "CASH"]
HEADER_3 = ["BILL NO.", "DESCRIPTION", "BILL VALUE"]

COL = {"bill": 0, "desc": 1, "mode": 2, "gross": 3, "disc": 4,
       "tax": 5, "drcr": 6, "net": 7, "cash": 8}

# The clinic's own patient ID, as the pharmacy counter types it at the end of
# the description. Four digits on 111 of 113 real bills — an observed
# convention, not a guarantee, so it is used to SCORE an ID, never to reject one.
CLINIC_ID_DIGITS = 4

RE_DATE = re.compile(r"^(\d{2})-(\d{2})-(\d{4})$")
RE_BILL = re.compile(r"^(?:A|CN)\d+$")
RE_ITEM = re.compile(r"^\s*\d+\s+")
RE_BILLS_FOOTER = re.compile(r"Bills:\s*(\d+)")
RE_TITLE = re.compile(r"BILL WISE SALES STATEMENT\s+(?:AS ON\s+(?P<on>\d{2}-\d{2}-\d{4})"
                      r"|FROM\s+(?P<from>\d{2}-\d{2}-\d{4})(?:\s+TO\s+(?P<to>\d{2}-\d{2}-\d{4}))?)")

FURNITURE_PREFIXES = ("SANJEEVNI", "35G/15B", "Phone :", "Digital Purchase",
                      "BILL WISE SALES STATEMENT", "Total No. of")


class MargReportError(Exception):
    """The file cannot be trusted. The message says exactly why."""


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def paise(v):
    """Text -> integer paise. Handles ' -1150.00', '1351.3', '', None.

    Deliberately reads str(v): in a real export the negatives are TEXT cells and
    the positives are numeric cells, so cell type cannot be trusted."""
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    if not s:
        return None
    neg = s.startswith("-")
    if neg:
        s = s[1:].strip()
    if not re.fullmatch(r"\d+(\.\d{1,3})?", s):
        return None
    whole, _, frac = s.partition(".")
    frac = (frac + "00")[:2]
    val = int(whole) * 100 + int(frac)
    return -val if neg else val


def iso(ddmmyyyy):
    m = RE_DATE.match((ddmmyyyy or "").strip())
    if not m:
        return None
    d, mo, y = m.groups()
    return "%s-%s-%s" % (y, mo, d)


def split_description(text):
    """Marg writes '<phone> <NAME> <clinic id>'. Any part may be absent.

    Returns (phone, name, clinic_id, confidence). Never invents an id.
      '9519825641 MANOSHA 6503'  -> ('9519825641', 'MANOSHA', '6503', 0.99)
      '7088144921 UTKARSH GUPTA' -> ('7088144921', 'UTKARSH GUPTA', None, 0.80)
      'SUDHA DEVI'               -> (None, 'SUDHA DEVI', None, 0.50)
      'ABL        BEENA AGARWAL' -> (None, 'BEENA AGARWAL', None, 0.50)   'ABL' = account code
    """
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    if not s:
        return None, None, None, 0.0

    phone = None
    m = re.match(r"^(\d{10})\s+(.*)$", s)
    if m:
        phone, s = m.group(1), m.group(2).strip()
    else:
        # a short all-caps account code such as 'ABL' in place of a phone
        m = re.match(r"^([A-Z]{2,4})\s+(.+)$", s)
        if m and " " in m.group(2):
            s = m.group(2).strip()

    clinic_id = None
    m = re.match(r"^(.*?)\s+(\d{2,8})$", s)
    if m and not m.group(1).strip().isdigit():
        s, clinic_id = m.group(1).strip(), m.group(2)

    name = s or None

    # Observed on 113 real IDs across six days: 111 were exactly four digits,
    # one was "77" and one "523". So four digits is the counter's convention.
    # A shorter one is either mis-keyed or a number wrongly taken off the end of
    # a name — it is NOT discarded (that would lose a real patient) and NOT
    # trusted either. It is returned with a confidence below finance's default
    # ingest.min_confidence of 0.70, so it lands in the review queue for a human
    # instead of being attributed to a patient it may not belong to.
    odd_id = bool(clinic_id) and len(clinic_id) != CLINIC_ID_DIGITS

    if clinic_id and phone:
        conf = 0.60 if odd_id else 0.99
    elif clinic_id:
        conf = 0.55 if odd_id else 0.95
    elif phone:
        conf = 0.80
    else:
        conf = 0.50
    return phone, name, clinic_id, conf


def mask_phone(p):
    return None if not p else "*" * (len(p) - 4) + p[-4:]


def last4(p):
    """The ONLY form of a phone number that leaves this module.

    finance's own patient_ref stores phone_last4 and nothing more, and the
    standing rule is that patient numbers are masked to the last four. The full
    number is read from the report to help identify the patient and is then
    dropped — it is never written to a CSV, a database or a log."""
    s = re.sub(r"\D", "", str(p or ""))
    return s[-4:] if len(s) >= 4 else None


# --------------------------------------------------------------------------- #
# item (drug) lines — the Button B detail
# --------------------------------------------------------------------------- #

RE_AMT_EXP = re.compile(r"^\s*(?P<amt>[\d,]+\.\d{1,2})(?:\s+(?P<exp>\d{1,2}/\d{2}))?\s*$")
RE_QTY_PAIR = re.compile(r"^\s*(?P<strips>\d+):(?P<loose>\d+)\s*$")


def expiry_ym(token):
    """'3/29' -> '2029-03'. Two-digit years are this century; Marg prints no others."""
    if not token:
        return None
    m = re.match(r"^\s*(\d{1,2})/(\d{2})\s*$", token)
    if not m:
        return None
    mo, yr = int(m.group(1)), int(m.group(2))
    if not 1 <= mo <= 12:
        return None
    return "20%02d-%02d" % (yr, mo)


def parse_item_line(line, qty, amount_expiry, batch):
    """One drug line under a bill.

        '1  43 FOLITRAX 15 MG TAB   1*5' · '0:2' · ' 283.47  3/29' · 'AT-220426'

    The second number varies for the same drug across days (GEN D3 NANO was 0 on
    01-Aug and 4 on 14-Aug), so it is NOT an item code. It is most likely stock
    in hand — but that is an inference, so it is carried raw as `col2` and named
    nothing it has not been proven to be (D188)."""
    toks = re.sub(r"\s+", " ", str(line or "")).strip().split(" ")
    seq = col2 = name = pack = None
    if len(toks) >= 4 and toks[0].isdigit() and toks[1].isdigit():
        seq, col2 = int(toks[0]), toks[1]
        pack = toks[-1]
        name = " ".join(toks[2:-1]).strip() or None
    elif toks:
        name = " ".join(toks).strip() or None

    amount_p = expiry = None
    m = RE_AMT_EXP.match(str(amount_expiry or ""))
    if m:
        amount_p = paise(m.group("amt"))
        expiry = expiry_ym(m.group("exp"))

    q = str(qty or "").strip()
    strips = loose = None
    mq = RE_QTY_PAIR.match(q)
    if mq:
        strips, loose = int(mq.group("strips")), int(mq.group("loose"))

    return {
        "seq": seq,
        "col2": col2,
        "item_name": name,
        "pack": pack,
        "qty_raw": q or None,
        "qty_strips": strips,
        "qty_loose": loose,
        "amount_p": amount_p,
        "expiry_ym": expiry,
        "batch": (str(batch or "").strip() or None),
    }


# --------------------------------------------------------------------------- #
# the reader
# --------------------------------------------------------------------------- #

def _open_sheet(path):
    try:
        import xlrd
    except ImportError:
        raise MargReportError(
            "xlrd is not installed on this machine; it is needed to read Marg's "
            "legacy .xls export.  Install with:  pip install xlrd")
    try:
        book = xlrd.open_workbook(path)
    except Exception as ex:                                    # noqa: BLE001
        raise MargReportError("not a readable .xls file (%s)" % ex)
    return book.sheet_by_index(0)


def _cell(sh, r, c):
    return str(sh.cell_value(r, c)).strip() if c < sh.ncols else ""


def _find_header(sh):
    for r in range(min(sh.nrows, 40)):
        if _cell(sh, r, 0) == "BILL NO.":
            return r, [_cell(sh, r, c) for c in range(sh.ncols)]
    raise MargReportError("no 'BILL NO.' header row found — this does not look "
                          "like a Bill Wise Sales Statement export")


def read_report(path, keep_items=False):
    """Parse a Marg export. Raises MargReportError if it cannot be trusted."""
    sh = _open_sheet(path)
    hdr_row, header = _find_header(sh)

    if header[:3] == HEADER_3 and header[3:] == [""] * (len(header) - 3):
        raise MargReportError(
            "this is the 3-column 'Summary-1' report (BILL NO. | DESCRIPTION | "
            "BILL VALUE). It has no CASH column, so cash and UPI cannot be "
            "separated from it. Regenerate with Report Type = Detail.")
    if header[:9] != HEADER_9:
        raise MargReportError(
            "unexpected column layout: %r. Expected: %r. A file is not identified "
            "by its name (D188) — refusing rather than guessing column positions."
            % (header[:9], HEADER_9))

    title = ""
    for r in range(hdr_row):
        t = _cell(sh, r, 0)
        if "BILL WISE SALES STATEMENT" in t:
            title = re.sub(r"\s+", " ", t).strip()
            break
    tm = RE_TITLE.search(title)
    if not tm:
        raise MargReportError("could not read the report period from the title: %r" % title)
    if tm.group("on"):
        span = (iso(tm.group("on")), iso(tm.group("on")))
        variant = "single-day"
    else:
        span = (iso(tm.group("from")), iso(tm.group("to")) if tm.group("to") else None)
        variant = "range"

    days, order = {}, []
    cur = None
    grand = None
    footer_bills = None
    items_seen = 0
    last_bill_key = None

    for r in range(hdr_row + 1, sh.nrows):
        c0, c1, c2 = _cell(sh, r, 0), _cell(sh, r, 1), _cell(sh, r, 2)

        if RE_DATE.match(c0):
            cur = iso(c0)
            if cur not in days:
                days[cur] = {"date": cur, "bills": [], "items": [], "declared": None}
                order.append(cur)
            continue

        if "GRAND TOTAL" in c2:
            grand = {k: paise(_cell(sh, r, COL[k]))
                     for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
            m = RE_BILLS_FOOTER.search(c1) or RE_BILLS_FOOTER.search(c0)
            if m:
                footer_bills = int(m.group(1))
            continue

        if "DAY TOTAL" in c2:
            if cur:
                days[cur]["declared"] = {k: paise(_cell(sh, r, COL[k]))
                                         for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
            continue

        if c2 == "C/F :" or c0.startswith(FURNITURE_PREFIXES) or c0 == "BILL NO." or not (c0 or c1):
            continue

        if RE_BILL.match(c0):
            if cur is None:
                raise MargReportError("bill %s appears before any date section" % c0)
            phone, name, cid, conf = split_description(c1)
            row = {
                "bill_date": cur,
                "bill_no": c0,
                "clinic_id": cid,
                "patient_name": name,
                "phone": phone,
                "mode": c2.replace("#", "").strip().lstrip(".").lower() or None,
                "gross_p": paise(_cell(sh, r, COL["gross"])) or 0,
                "disc_p": paise(_cell(sh, r, COL["disc"])) or 0,
                "tax_p": paise(_cell(sh, r, COL["tax"])) or 0,
                "drcr_p": paise(_cell(sh, r, COL["drcr"])) or 0,
                "net_p": paise(_cell(sh, r, COL["net"])),
                "cash_p": paise(_cell(sh, r, COL["cash"])),
                "confidence": conf,
                "is_credit_note": c0.startswith("CN"),
            }
            if row["net_p"] is None or row["cash_p"] is None:
                raise MargReportError("bill %s on %s has an unreadable NET or CASH value"
                                      % (c0, cur))
            row["noncash_p"] = row["net_p"] - row["cash_p"]
            days[cur]["bills"].append(row)
            last_bill_key = (cur, c0)
            continue

        # a drug-detail line: BILL NO. blank, description starts with a line number
        if not c0 and RE_ITEM.match(c1):
            items_seen += 1
            if keep_items and last_bill_key:
                raw_line = re.sub(r"\s+", " ", c1)
                raw_amt = _cell(sh, r, COL["gross"]) or None
                raw_batch = _cell(sh, r, COL["disc"]) or None
                days[last_bill_key[0]]["items"].append({
                    "bill_date": last_bill_key[0],
                    "bill_no": last_bill_key[1],
                    "line": raw_line,
                    "qty": c2 or None,
                    "amount_expiry": raw_amt,
                    "batch": raw_batch,
                    "parsed": parse_item_line(raw_line, c2, raw_amt, raw_batch),
                })
            continue
        # anything else is page furniture; ignored deliberately

    # ---------------------------------------------------------------- checks
    errors, warnings = [], []

    if grand is None:
        errors.append(
            "TRUNCATED EXPORT — no GRAND TOTAL row. The export stopped before the "
            "end of the report; %d day(s) were read but the file is incomplete. "
            "Re-run the export, or shorten the date range / switch item detail off."
            % len(order))

    for d in order:
        rec = days[d]
        dec = rec["declared"]
        computed = {k: sum(b[k + "_p"] for b in rec["bills"])
                    for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
        rec["computed"] = computed
        if dec is None:
            errors.append("day %s has no DAY TOTAL row — that day is incomplete" % d)
            continue
        for k in ("gross", "net", "cash"):
            if dec.get(k) is not None and dec[k] != computed[k]:
                errors.append("day %s: %s bill rows sum to %.2f but the DAY TOTAL row says %.2f"
                              % (d, k.upper(), computed[k] / 100.0, dec[k] / 100.0))

    if grand is not None:
        tot = {k: sum(days[d]["computed"][k] for d in order)
               for k in ("gross", "disc", "tax", "drcr", "net", "cash")}
        for k in ("gross", "net", "cash"):
            if grand.get(k) is not None and grand[k] != tot[k]:
                errors.append("GRAND TOTAL %s says %.2f but the days sum to %.2f"
                              % (k.upper(), grand[k] / 100.0, tot[k] / 100.0))
        n = sum(len(days[d]["bills"]) for d in order)
        if footer_bills is not None and footer_bills != n:
            errors.append("footer says %d bills, %d bill rows were read" % (footer_bills, n))

    nbills = sum(len(days[d]["bills"]) for d in order)

    cn = [b for d in order for b in days[d]["bills"] if b["is_credit_note"]]
    if cn:
        warnings.append("%d credit note(s) totalling %.2f — kept, and carried through "
                        "signed (needs finance_ingest at S180 U1 or later)"
                        % (len(cn), sum(b["net_p"] for b in cn) / 100.0))

    no_id = [b for d in order for b in days[d]["bills"] if not b["clinic_id"]]
    if no_id:
        warnings.append("%d of %d bills carry no clinic ID and will attribute to WALK-IN"
                        % (len(no_id), nbills))

    odd = [b for d in order for b in days[d]["bills"]
           if b["clinic_id"] and len(b["clinic_id"]) != CLINIC_ID_DIGITS]
    if odd:
        warnings.append("%d bill(s) carry a clinic ID that is not %d digits (%s) — scored "
                        "low so they go to review rather than to a possibly wrong patient"
                        % (len(odd), CLINIC_ID_DIGITS,
                           ", ".join(sorted({b["clinic_id"] for b in odd})[:6])))

    return {
        "path": os.path.basename(path),
        "title": title,
        "variant": variant,
        "period": span,
        "days": [days[d] for d in order],
        "grand": grand,
        "footer_bills": footer_bills,
        "item_lines_seen": items_seen,
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
    }


# --------------------------------------------------------------------------- #
# outputs
# --------------------------------------------------------------------------- #

LINE_COLUMNS = ["bill_date", "bill_no", "clinic_id", "patient_name", "phone_last4",
                "description", "amount", "mode"]

ITEM_COLUMNS = ["bill_date", "bill_no", "is_return", "seq", "item_name", "pack",
                "qty_raw", "qty_strips", "qty_loose", "amount", "expiry_ym", "batch", "col2"]


def write_lines_csv(report, fh, business_date=None):
    """Bill-level rows for finance_ingest.adapter_csv.

    amount = NET AMT. in rupees, SIGNED — a credit note stays negative here, and
    finance_ingest turns it into a magnitude plus a '_return' service on the way
    in (S180 U1). Phone is written as the last four digits only."""
    w = csv.DictWriter(fh, fieldnames=LINE_COLUMNS, lineterminator="\n")
    w.writeheader()
    n = 0
    for day in report["days"]:
        if business_date and day["date"] != business_date:
            continue
        for b in day["bills"]:
            w.writerow({
                "bill_date": b["bill_date"],
                "bill_no": b["bill_no"],
                "clinic_id": b["clinic_id"] or "",
                "patient_name": b["patient_name"] or "",
                "phone_last4": last4(b["phone"]) or "",
                "description": "",
                "amount": "%.2f" % (b["net_p"] / 100.0),
                "mode": b["mode"] or "",
            })
            n += 1
    return n


def write_items_csv(report, fh, business_date=None):
    """Drug-level rows from a Button B export. Carries no patient identity at
    all — the bill number is the only link back, and that link lives in the
    bill-level file."""
    w = csv.DictWriter(fh, fieldnames=ITEM_COLUMNS, lineterminator="\n")
    w.writeheader()
    returns = {b["bill_no"] for day in report["days"] for b in day["bills"]
               if b["is_credit_note"]}
    n = 0
    for day in report["days"]:
        if business_date and day["date"] != business_date:
            continue
        for it in day["items"]:
            p = it["parsed"]
            w.writerow({
                "bill_date": it["bill_date"],
                "bill_no": it["bill_no"],
                "is_return": 1 if it["bill_no"] in returns else 0,
                "seq": p["seq"] if p["seq"] is not None else "",
                "item_name": p["item_name"] or "",
                "pack": p["pack"] or "",
                "qty_raw": p["qty_raw"] or "",
                "qty_strips": p["qty_strips"] if p["qty_strips"] is not None else "",
                "qty_loose": p["qty_loose"] if p["qty_loose"] is not None else "",
                "amount": ("%.2f" % (p["amount_p"] / 100.0)) if p["amount_p"] is not None else "",
                "expiry_ym": p["expiry_ym"] or "",
                "batch": p["batch"] or "",
                "col2": p["col2"] or "",
            })
            n += 1
    return n


def day_totals(report):
    out = []
    for day in report["days"]:
        c = day["computed"]
        out.append({
            "business_date": day["date"],
            "bills": len(day["bills"]),
            "gross_p": c["gross"], "discount_p": c["disc"], "tax_p": c["tax"],
            "drcr_p": c["drcr"], "net_p": c["net"], "cash_p": c["cash"],
            "noncash_p": c["net"] - c["cash"],
        })
    return out


# --------------------------------------------------------------------------- #
# selftest
# --------------------------------------------------------------------------- #

def selftest(sample_dir="."):
    """Runs against the real exports collected on 15-08-2026."""
    checks, failures = 0, []

    def ck(label, cond):
        nonlocal checks
        checks += 1
        if not cond:
            failures.append(label)

    # -- paise ------------------------------------------------------------
    ck("paise plain", paise("1351.3") == 135130)
    ck("paise negative text", paise(" -1150.00") == -115000)
    ck("paise leading spaces", paise("   -77.00") == -7700)
    ck("paise zero", paise("0.0") == 0)
    ck("paise blank", paise("") is None)
    ck("paise junk", paise(" 283.47  3/29") is None)
    ck("paise no float error", paise("1044.53") == 104453)

    # -- description ------------------------------------------------------
    ck("desc phone+name+id", split_description("9519825641 MANOSHA 6503")[:3]
       == ("9519825641", "MANOSHA", "6503"))
    ck("desc phone+name", split_description("7088144921 UTKARSH GUPTA")[:3]
       == ("7088144921", "UTKARSH GUPTA", None))
    ck("desc name only", split_description("          SUDHA DEVI")[:3]
       == (None, "SUDHA DEVI", None))
    ck("desc account code", split_description("ABL        BEENA AGARWAL")[:3]
       == (None, "BEENA AGARWAL", None))
    ck("desc id kept as text", split_description("9760674568 DIPTI BHATNAGAR 7372")[2] == "7372")
    ck("desc empty", split_description("")[3] == 0.0)
    ck("4-digit id is trusted", split_description("9519825641 MANOSHA 6503")[3] >= 0.95)
    ck("odd-length id is kept", split_description("9760674568 PANKAJ 77")[2] == "77")
    ck("odd-length id is NOT trusted",
       split_description("9760674568 PANKAJ 77")[3] < 0.70)
    ck("odd-length id without phone also untrusted",
       split_description("ARUNA 523")[3] < 0.70)

    # -- iso --------------------------------------------------------------
    ck("iso", iso("01-08-2026") == "2026-08-01")
    ck("iso bad", iso("nonsense") is None)

    # -- masking (the only form a phone leaves this module in) -------------
    ck("last4", last4("9519825641") == "5641")
    ck("last4 of nothing", last4("") is None)
    ck("last4 refuses a short number", last4("123") is None)
    ck("lines CSV carries no full phone", "phone" not in LINE_COLUMNS)

    # -- item lines --------------------------------------------------------
    p = parse_item_line("1  43 FOLITRAX 15 MG TAB   1*5", "0:2", " 283.47  3/29", "AT-220426")
    ck("item name", p["item_name"] == "FOLITRAX 15 MG TAB")
    ck("item pack", p["pack"] == "1*5")
    ck("item amount", p["amount_p"] == 28347)
    ck("item expiry", p["expiry_ym"] == "2029-03")
    ck("item batch", p["batch"] == "AT-220426")
    ck("item qty pair", (p["qty_strips"], p["qty_loose"]) == (0, 2))
    ck("item col2 kept raw", p["col2"] == "43")

    p2 = parse_item_line("5   8 BRUTAFLAM GEL   30GM", "1.0", "  74.90 11/30", "2512BE0")
    ck("non-strip pack", p2["pack"] == "30GM")
    ck("multiword name", p2["item_name"] == "BRUTAFLAM GEL")
    ck("expiry 2030", p2["expiry_ym"] == "2030-11")
    ck("qty not a pair", p2["qty_strips"] is None and p2["qty_raw"] == "1.0")

    p3 = parse_item_line("1   5 LACTOVAX SYP   200ML.", "1.0", " 262.50  4/27", "YL256A")
    ck("syrup pack", p3["pack"] == "200ML.")
    ck("expiry month padded", p3["expiry_ym"] == "2027-04")

    ck("expiry rejects month 13", expiry_ym("13/29") is None)
    ck("expiry rejects junk", expiry_ym("AT-220426") is None)

    # -- real files -------------------------------------------------------
    def s(n):
        return os.path.join(sample_dir, n)

    if os.path.exists(s("REPORT_1.XLS")):
        try:
            read_report(s("REPORT_1.XLS"))
            failures.append("3-column report should have been refused")
        except MargReportError as ex:
            ck("refuses 3-column Summary-1", "no CASH column" in str(ex))
        checks += 1

    if os.path.exists(s("REPORT_1_optC.XLS")):
        r = read_report(s("REPORT_1_optC.XLS"))
        ck("optC parses", r["ok"] is True)
        ck("optC single day", r["variant"] == "single-day")
        ck("optC 5 bills", len(r["days"][0]["bills"]) == 5)
        ck("optC net", r["days"][0]["computed"]["net"] == 302600)
        ck("optC cash", r["days"][0]["computed"]["cash"] == 302600)
        ck("optC grand present", r["grand"] is not None)

    if os.path.exists(s("REPORT_1_optE.XLS")):
        r = read_report(s("REPORT_1_optE.XLS"), keep_items=True)
        ck("optE parses", r["ok"] is True)
        ck("optE 37 bills", len(r["days"][0]["bills"]) == 37)
        ck("optE net", r["days"][0]["computed"]["net"] == 2811900)
        ck("optE cash", r["days"][0]["computed"]["cash"] == 1641100)
        items = r["days"][0]["items"]
        ck("optE item lines kept", len(items) == 166)
        named = [i for i in items if i["parsed"]["item_name"]]
        ck("every item line yields a name", len(named) == len(items))
        wexp = [i for i in items if i["parsed"]["expiry_ym"]]
        ck("most item lines carry an expiry", len(wexp) >= int(0.9 * len(items)))
        wamt = [i for i in items if i["parsed"]["amount_p"] is not None]
        ck("most item lines carry an amount", len(wamt) >= int(0.9 * len(items)))

    if os.path.exists(s("REPORT_1_optD.XLS")):
        r = read_report(s("REPORT_1_optD.XLS"))
        ck("optD detects truncation", r["ok"] is False)
        ck("optD says TRUNCATED", any("TRUNCATED" in e for e in r["errors"]))
        ck("optD range variant", r["variant"] == "range")
        ck("optD period start", r["period"][0] == "2026-08-01")
        complete = [d for d in r["days"] if d["declared"]]
        ck("optD 5 complete days", len(complete) == 5)
        ck("optD day1 net", complete[0]["computed"]["net"] == 2811900)
        ck("optD day1 cash", complete[0]["computed"]["cash"] == 1641100)
        ck("optD noncash > 0", complete[0]["computed"]["net"] > complete[0]["computed"]["cash"])
        ck("optD every complete day balances",
           all(not any(d["date"] in e for e in r["errors"]) for d in complete))
        ck("optD clinic ids found",
           sum(1 for d in r["days"] for b in d["bills"] if b["clinic_id"]) > 0)

    print("selftest: %d/%d passed" % (checks - len(failures), checks))
    for f in failures:
        print("  FAIL:", f)
    return not failures


# --------------------------------------------------------------------------- #

def main(argv=None):
    ap = argparse.ArgumentParser(description="Read a Marg BILL WISE SALES STATEMENT .xls")
    ap.add_argument("xls", nargs="?", help="path to REPORT_1.XLS")
    ap.add_argument("--csv", help="write bill-level rows here for adapter_csv")
    ap.add_argument("--items-csv", dest="items_csv",
                    help="write drug-level rows here (implies --items)")
    ap.add_argument("--date", help="only this business date (YYYY-MM-DD)")
    ap.add_argument("--items", action="store_true", help="also collect drug-detail lines")
    ap.add_argument("--json", action="store_true", help="print the day totals as JSON")
    ap.add_argument("--selftest", metavar="DIR", nargs="?", const=".",
                    help="run the built-in checks against the sample exports")
    a = ap.parse_args(argv)

    if a.selftest is not None:
        return 0 if selftest(a.selftest) else 1
    if not a.xls:
        ap.error("give an .xls path, or --selftest")

    try:
        rep = read_report(a.xls, keep_items=a.items or bool(a.items_csv))
    except MargReportError as ex:
        print("REFUSED: %s" % ex, file=sys.stderr)
        return 2

    print("%s  [%s]" % (rep["title"], rep["variant"]))
    print("%-12s %6s %14s %14s %14s" % ("DATE", "BILLS", "NET", "CASH", "NON-CASH"))
    for t in day_totals(rep):
        print("%-12s %6d %14.2f %14.2f %14.2f"
              % (t["business_date"], t["bills"], t["net_p"] / 100.0,
                 t["cash_p"] / 100.0, t["noncash_p"] / 100.0))
    if rep["item_lines_seen"]:
        print("(%d drug-detail lines skipped)" % rep["item_lines_seen"])
    for w in rep["warnings"]:
        print("WARNING: %s" % w)
    for e in rep["errors"]:
        print("ERROR:   %s" % e, file=sys.stderr)

    if a.json:
        print(json.dumps(day_totals(rep), indent=2))

    if a.csv or a.items_csv:
        if not rep["ok"]:
            print("not writing any CSV — the file did not pass its own checks", file=sys.stderr)
            return 3
        if a.csv:
            with open(a.csv, "w", encoding="utf-8", newline="") as fh:
                n = write_lines_csv(rep, fh, a.date)
            print("wrote %d bill rows to %s" % (n, a.csv))
        if a.items_csv:
            if not rep["item_lines_seen"]:
                print("no drug-detail lines in this file — it is a Button A "
                      "(accounts) export, not Button B", file=sys.stderr)
                return 4
            with open(a.items_csv, "w", encoding="utf-8", newline="") as fh:
                n = write_items_csv(rep, fh, a.date)
            print("wrote %d item rows to %s" % (n, a.items_csv))

    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
