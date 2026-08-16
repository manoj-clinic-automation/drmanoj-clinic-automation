"""docterz_report.py — one reader for BOTH Docterz daily exports.

Session 181. Parallels marg_report.py in spirit: read what the vendor emits,
refuse what cannot be trusted, and emit normalised rows plus a day summary
that has already been checked against the file's own footer.

THE TWO VARIANTS (both real, both observed 2026-08):
  consultation_report_YYYYMMDD.csv  — 39 cols. Money: per-stream amounts,
      Total row, receipt trail in "Payment Collected By".
      Split format:  1100 (Cash: 600, Online Payment: 500)   [Capitalised]
  clinical_data_report_YYYYMMDD.csv — 55 cols. Clinical: Diagnosis,
      Follow Up, Tests, Procedures, Drugs Prescribed, Instructions.
      Stream amount columns PRESENT BUT ALL ZERO (vendor-side; not correctable).
      Split format:  1100 (split: cash: 1100)                [lowercase, prefix]

BOTH end with the authoritative footer:
  Date,Cash,Credit Card,Debit Card,Net Banking,Online Payment,Patient APP,Wallet,Total,Refund

RULES CARRIED IN CODE (each traces to a measured fault):
  * ALL SEVEN tender tokens are recognised, case-insensitively, with or
    without the "split:" prefix. An unrecognised token is a REFUSAL, never a
    silent drop — dropped Wallet/Debit-Card legs cost Rs 500-600/day (S181).
  * The footer is read and ASSERTED against the sum of parsed rows. Any
    disagreement is a shout, not a warning counter.
  * A row's parsed legs must sum to its collected amount.
  * The Total row (Sr No blank/non-numeric) is dropped by rule, not position.
  * Dates are PARSED day-first (both DD-MM-YYYY and DD/MM/YYYY, with or
    without AM/PM); never sliced (F-78).
  * "Mode Of Payment" values may carry a trailing space, and empty may be a
    lone space — normalised before comparison.
  * Radiology is dead at source; X-ray money arrives in "Laboratory Amount"
    (Docterz-side, owner-confirmed not correctable). The consumer decides the
    mapping; this reader reports what the file says.
  * Phones leave this module MASKED to last-4 unless the caller explicitly
    asks for the raw store form (F-86: the destination's constraints are part
    of the spec; the tracker's own ledgers carry the full number, chat and
    logs never do).

Stdlib only. Python 3.8+.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
import sys

# ---------------------------------------------------------------- vocabulary

# canonical tender keys, in footer column order
TENDERS = ("cash", "credit_card", "debit_card", "net_banking",
           "online", "patient_app", "wallet")

_TOKEN_MAP = {
    "cash": "cash",
    "credit card": "credit_card",
    "debit card": "debit_card",
    "net banking": "net_banking",
    "online payment": "online",
    "patient app": "patient_app",
    "wallet": "wallet",
}

_FOOTER_HEADER = ["Date", "Cash", "Credit Card", "Debit Card", "Net Banking",
                  "Online Payment", "Patient APP", "Wallet", "Total", "Refund"]

# mode label -> canonical single-tender key (when no parenthetical detail)
_MODE_MAP = {
    "cash": "cash",
    "credit card": "credit_card",
    "debit card": "debit_card",
    "net banking": "net_banking",
    "online payment": "online",
    "patient app": "patient_app",
    "wallet": "wallet",
}

_SPLIT_LEG = re.compile(r"([A-Za-z][A-Za-z ]*?)\s*:\s*(\d+)")

_STREAMS = ("Consultation Amount", "Procedure Amount", "Drugs Amount",
            "Vaccination Amount", "Package Amount", "Laboratory Amount",
            "Radiology Amount")


class DocterzRefused(Exception):
    """The file cannot be trusted; the reason says exactly why."""


# ---------------------------------------------------------------- helpers

def mask_phone(p: str) -> str:
    d = re.sub(r"\D", "", p or "")
    return ("…" + d[-4:]) if len(d) >= 4 else ""


def _norm(s: str) -> str:
    return (s or "").strip()


def parse_date(s: str):
    """Day-first date, optional time, '-' or '/' separators. None if blank."""
    s = _norm(s)
    if not s:
        return None
    m = re.match(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", s)
    if not m:
        raise DocterzRefused(f"unparseable date: {s!r}")
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 2000 or y > 2100:
        raise DocterzRefused(f"implausible year in date: {s!r}")
    return dt.date(y, mo, d)


def parse_follow_up(s: str, visit: "dt.date"):
    """'19-08-2026' | '1 weeks' | '1 days' | '2 month(s)' -> date, or None."""
    s = _norm(s)
    if not s:
        return None
    m = re.match(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})$", s)
    if m:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.match(r"(\d+)\s*(day|week|month)s?$", s, re.I)
    if m and visit:
        n, unit = int(m.group(1)), m.group(2).lower()
        days = n * {"day": 1, "week": 7, "month": 30}[unit]
        return visit + dt.timedelta(days=days)
    return None  # free text we do not understand; carried verbatim upstream


def parse_collected(raw: str, mode_label: str, bill: int):
    """-> (collected_total, legs dict, notes list).

    Handles: plain number · '1100 (Cash: 600, Online Payment: 500)' ·
    '1100 (split: cash: 1100)' · blank.
    REFUSES an unrecognised tender token instead of dropping the leg.
    """
    notes = []
    legs = {k: 0 for k in TENDERS}
    raw = _norm(raw)
    if not raw:
        return 0, legs, notes

    m = re.match(r"^(\d+)\s*(?:\((.*)\))?\s*$", raw)
    if not m:
        raise DocterzRefused(f"unparseable Amount collected: {raw!r}")
    total = int(m.group(1))
    detail = m.group(2)

    if detail:
        body = re.sub(r"^\s*split\s*:\s*", "", detail, flags=re.I)
        pos, consumed = 0, 0
        for leg in _SPLIT_LEG.finditer(body):
            token = leg.group(1).strip().lower()
            if token == "split":       # nested prefix guard
                continue
            key = _TOKEN_MAP.get(token)
            if key is None:
                raise DocterzRefused(
                    f"UNRECOGNISED tender token {leg.group(1)!r} in {raw!r} — "
                    "refusing rather than dropping the leg (S181 rule)")
            legs[key] += int(leg.group(2))
            consumed += int(leg.group(2))
            pos = leg.end()
        if consumed != total:
            notes.append(f"legs sum {consumed} != collected {total} in {raw!r}")
    else:
        label = _norm(mode_label).lower()
        if label in ("", "-",):
            if total:
                notes.append(f"collected {total} with no payment mode")
        else:
            key = _MODE_MAP.get(label)
            if key is None and label == "split payment":
                # a split with no detail: unattributable — shout, don't guess
                notes.append(f"'Split Payment' with no leg detail on {total}")
            elif key is None:
                raise DocterzRefused(f"unknown Mode Of Payment {mode_label!r}")
            else:
                legs[key] = total
    return total, legs, notes


# ---------------------------------------------------------------- core

def read_export(path_or_text, *, mask=True):
    """Parse one Docterz export (either variant).

    Returns dict:
      variant       'consultation' | 'clinical'
      rows          list of per-visit dicts (see below)
      day_legs      {tender: rupees} summed over rows
      footer        {tender: rupees, 'total':, 'refund':} from the file
      footer_ok     True if day_legs matches footer exactly
      mismatches    list of strings (footer/tender disagreements)
      anomalies     list of row-level notes
      total_row     the file's own Total figures (consultation variant)
      date          the business date from the footer

    Refuses (raises DocterzRefused) on: unknown tender token, missing footer,
    unparseable dates, or an unrecognisable header set.
    """
    if isinstance(path_or_text, str) and "\n" not in path_or_text:
        text = open(path_or_text, encoding="utf-8-sig").read()
    else:
        text = path_or_text
    rows_raw = list(csv.reader(io.StringIO(text)))
    if not rows_raw:
        raise DocterzRefused("empty file")

    hdr = [_norm(h) for h in rows_raw[0]]
    idx = {h: i for i, h in enumerate(hdr)}
    for req in ("Sr No", "Clinic Specific Id", "Consultation Date",
                "Bill Amount", "Amount collected", "Mode Of Payment"):
        if req not in idx:
            raise DocterzRefused(f"header missing {req!r} — not a Docterz "
                                 f"export I recognise ({len(hdr)} cols)")
    variant = "clinical" if "Diagnosis" in idx else "consultation"

    def cell(row, name):
        i = idx.get(name)
        return _norm(row[i]) if i is not None and i < len(row) else ""

    visits, anomalies = [], []
    for row in rows_raw[1:]:
        if not row or not _norm(row[0]).isdigit():
            continue  # banner, Total row, blank — dropped by RULE, not position
        bill = int(float(cell(row, "Bill Amount") or 0))
        collected, legs, notes = parse_collected(
            cell(row, "Amount collected"), cell(row, "Mode Of Payment"), bill)
        visit_date = parse_date(cell(row, "Consultation Date"))
        v = {
            "clinic_id": cell(row, "Clinic Specific Id"),
            "patient_uid": cell(row, "Patient UID"),
            "name": cell(row, "Patient Name"),
            "phone": mask_phone(cell(row, "Mobile")) if mask
                     else re.sub(r"\D", "", cell(row, "Mobile")),
            "date": visit_date,
            "purpose": cell(row, "Purpose Of Visit"),
            "schedule": cell(row, "Schedule"),
            "invoice": cell(row, "Invoice No."),
            "bill": bill,
            "collected": collected,
            "pending": int(float(cell(row, "Bill Amount Pending") or 0)),
            "legs": legs,
            "mode": _norm(cell(row, "Mode Of Payment")),
            "streams": {s: int(float(cell(row, s) or 0)) for s in _STREAMS
                        if s in idx},
        }
        if variant == "consultation":
            stream_sum = sum(v["streams"].values())
            if stream_sum != bill:
                anomalies.append(f"row {v['invoice'] or v['clinic_id']}: "
                                 f"streams {stream_sum} != bill {bill}")
        else:
            v["clinical"] = {
                "diagnosis": cell(row, "Diagnosis"),
                "follow_up_raw": cell(row, "Follow Up"),
                "follow_up_date": parse_follow_up(cell(row, "Follow Up"),
                                                  visit_date),
                "tests": cell(row, "Tests"),
                "procedures": cell(row, "Procedures"),
                "drugs": cell(row, "Drugs Prescribed"),
                "instructions": cell(row, "Instructions"),
            }
        for n in notes:
            anomalies.append(f"row {v['invoice'] or v['clinic_id']}: {n}")
        visits.append(v)

    # ---- footer -----------------------------------------------------------
    footer = None
    date = None
    for i, row in enumerate(rows_raw):
        cells = [_norm(c) for c in row]
        if cells[:2] == ["Date", "Cash"] and "Total" in cells:
            if cells[:len(_FOOTER_HEADER)] != _FOOTER_HEADER:
                raise DocterzRefused(f"footer header shape changed: {cells!r}")
            vals = [_norm(c) for c in rows_raw[i + 1]]
            date = parse_date(vals[0].split("-", 3)[-1].strip()
                              if " - " in vals[0] else vals[0])
            nums = [int(float(x or 0)) for x in vals[1:len(_FOOTER_HEADER)]]
            footer = dict(zip(TENDERS, nums[:7]))
            footer["total"], footer["refund"] = nums[7], nums[8]
            break
    if footer is None:
        raise DocterzRefused("footer tender block missing — cannot certify "
                             "the day; a file without it is not accepted")

    day_legs = {k: sum(v["legs"][k] for v in visits) for k in TENDERS}
    mismatches = []
    for k in TENDERS:
        if day_legs[k] != footer[k]:
            mismatches.append(f"{k}: rows {day_legs[k]} != footer {footer[k]}")
    if sum(day_legs.values()) != footer["total"] - footer["refund"]:
        mismatches.append(f"total: rows {sum(day_legs.values())} != "
                          f"footer {footer['total']} - refund {footer['refund']}")

    return {
        "variant": variant, "rows": visits, "day_legs": day_legs,
        "footer": footer, "footer_ok": not mismatches,
        "mismatches": mismatches, "anomalies": anomalies, "date": date,
    }


# ---------------------------------------------------------------- selftest

def _fixture_consultation():
    """Synthetic — every quirk observed in the real 13-Aug file, NO real data."""
    hdr = ("Sr No,Patient Name,Patient UID,Mobile,Gender,DOB,Age,Address,"
           "Consultation Date,Doctor,Clinic Specific Id,Prescription,"
           "Purpose Of Visit,Bill Amount,Amount collected,Bill Amount Pending,"
           "Advance Collected,Adjust Advance,Consultation Amount,"
           "Consultation Discount,Procedure Amount,Procedure Discount,"
           "Drugs Amount,Drugs Discount,Vaccination Amount,"
           "Vaccination Discount,Package Amount,Package Discount,"
           "Laboratory Amount,Laboratory Discount,Radiology Amount,"
           "Radiology Discount,Cashback,Points,Mode Of Payment,"
           "Payment Collected By,Invoice No.,Schedule,Notes")
    rows = [
        hdr,
        "Test Clinic,,,,,,,,",
        # plain cash; trailing space in mode
        '1,Test A,AAAAA00001,9000000001,female,01/01/1980,46 years,,'
        '13-08-2026 08:45 PM,Doc,1001,Done,Consultation,600,600,0,0,0,600,0,'
        '0,0,0,0,0,0,0,0,0,0,0,0,,,Cash ,"trail",2001,Evening,',
        # split with Capitalised tokens incl. Wallet (the dropped-leg case)
        '2,Test B,BBBBB00002,9000000002,male,01/01/1990,36 years,,'
        '13-08-2026 07:30 PM,Doc,1002,Done,Consultation,1100,'
        '"1100 (Wallet: 500, Online Payment: 600)",0,0,0,600,0,0,0,0,0,0,0,'
        '0,0,500,0,0,0,,,Split Payment ,"trail",2002,Evening,',
        # debit card as whole-visit mode; xray money in Laboratory col
        '3,Test C,CCCCC00003,9000000003,male,01/01/1996,30 years,,'
        '13-08-2026 10:35 AM,Doc,1003,Done,Consultation,600,600,0,0,0,600,0,'
        '0,0,0,0,0,0,0,0,0,0,0,0,,,Debit Card ,"trail",2003,Morning,',
        # unpaid: blank-space mode, dash trail
        '4,Test D,DDDDD00004,9000000004,male,01/01/1988,38 years,,'
        '13-08-2026 07:35 PM,Doc,1004,Pending,Consultation,0,0,0,0,0,0,0,0,0,'
        '0,0,0,0,0,0,0,0,0,0,,, ,-,,Evening,',
        ',Total,,,,,,,,,,,,2300,2300,0,0,0,1800,0,0,0,0,0,0,0,0,0,500,0,0,0,,,,,,,',
        "", "Mode of Payment Collection Details",
        "Date,Cash,Credit Card,Debit Card,Net Banking,Online Payment,"
        "Patient APP,Wallet,Total,Refund",
        "13-08-2026 - 13-08-2026,600,0,600,0,600,0,500,2300,0",
    ]
    return "\n".join(rows)


def _fixture_clinical():
    hdr = ("Sr No,Patient Name,Patient UID,Mobile,Gender,DOB,Age,Address,"
           "Consultation Date,Doctor,Clinic Specific Id,Prescription,"
           "Purpose Of Visit,Bill Amount,Amount collected,Bill Amount Pending,"
           "Consultation Amount,Consultation Discount,Procedure Amount,"
           "Procedure Discount,Drugs Amount,Drugs Discount,Vaccination Amount,"
           "Vaccination Discount,Package Amount,Package Discount,"
           "Laboratory Amount,Laboratory Discount,Radiology Amount,"
           "Radiology Discount,Cashback,Points,Mode Of Payment,"
           "Payment Collected By,Invoice No.,Schedule,Notes,Complaints,"
           "Findings,Diagnosis,Drugs Prescribed,Dosage,Tests,Procedures,"
           "Instructions,Handouts,Vitals,Lab Trends,Clinical Note,"
           "Prescription Note,Follow Up,Ref By,Ref To,Vaccine Given,"
           "Vaccine Schedule")
    rows = [
        hdr,
        "Test Clinic,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,",
        # lowercase split: prefix, cash-only
        '1,Test E,EEEEE00005,9000000005,male,12/08/2006,20 years,,'
        '12-08-2026 07:55 PM,Doc,1005,Done,Consultation,1100,'
        '"1100 (split: cash: 1100)",0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,,,Cash,'
        'Reception,3001,Evening,,,,DX ONE,Tab X,Tab X 1 for 2 days,,,ADVICE,'
        ',,,,,14-08-2026,,,,',
        # split with Debit Card leg (the 12-Aug Rs600 case), relative follow-up
        '2,Test F,FFFFF00006,9000000006,male,12/08/1991,35 years,,'
        '12-08-2026 02:25 PM,Doc,1006,Done,Consultation,1100,'
        '"1100 (split: cash: 500, Debit Card: 600)",0,0,0,0,0,0,0,0,0,0,0,0,'
        '0,0,0,,,Split Payment,Reception,3002,Morning,,,,DX TWO,Tab Y,'
        'Tab Y 1 for 7 days,,,ADVICE,,,,,,1 weeks,,,,',
        # unpaid follow-up: '-' mode, empty collected
        '3,Test G,GGGGG00007,9000000007,female,22/07/1978,48 years,,'
        '12-08-2026 06:30 PM,Doc,1007,Pending,Consultation,0,,0,0,0,0,0,0,0,'
        '0,0,0,0,0,0,0,0,,,-,-,,Evening,,,,,,,,,,,,,,,,,,,',
        "Total,,,,,,3 appointments,,,,,,,,,,,,,,,,,,,,,,,,,,",
        "", "Mode of Payment Collection Details",
        "Date,Cash,Credit Card,Debit Card,Net Banking,Online Payment,"
        "Patient APP,Wallet,Total,Refund",
        "12-08-2026 - 12-08-2026,1600,0,600,0,0,0,0,2200,0",
    ]
    return "\n".join(rows)


def selftest():
    ok = fail = 0

    def check(name, cond):
        nonlocal ok, fail
        ok, fail = (ok + 1, fail) if cond else (ok, fail + 1)
        if not cond:
            print(f"  FAIL: {name}")

    r = read_export(_fixture_consultation())
    check("variant consultation", r["variant"] == "consultation")
    check("4 visits parsed", len(r["rows"]) == 4)
    check("wallet leg kept", r["day_legs"]["wallet"] == 500)
    check("online leg kept", r["day_legs"]["online"] == 600)
    check("debit card whole-visit", r["day_legs"]["debit_card"] == 600)
    check("footer matches rows", r["footer_ok"])
    check("date parsed", str(r["date"]) == "2026-08-13")
    check("xray-in-laboratory visible",
          r["rows"][1]["streams"]["Laboratory Amount"] == 500)
    check("unpaid row zero legs", sum(r["rows"][3]["legs"].values()) == 0)
    check("no anomalies", not r["anomalies"])

    r2 = read_export(_fixture_clinical())
    check("variant clinical", r2["variant"] == "clinical")
    check("split: prefix handled", r2["rows"][0]["legs"]["cash"] == 1100)
    check("debit leg inside split kept", r2["rows"][1]["legs"]["debit_card"] == 600)
    check("cash leg beside it kept", r2["rows"][1]["legs"]["cash"] == 500)
    check("clinical diagnosis carried",
          r2["rows"][0]["clinical"]["diagnosis"] == "DX ONE")
    check("follow-up date parsed",
          str(r2["rows"][0]["clinical"]["follow_up_date"]) == "2026-08-14")
    check("relative follow-up parsed",
          str(r2["rows"][1]["clinical"]["follow_up_date"]) == "2026-08-19")
    check("clinical footer matches", r2["footer_ok"])
    check("phone masked", r2["rows"][0]["phone"] == "…0005")

    # refusal on an unknown tender token
    bad = _fixture_consultation().replace("Wallet: 500", "Gift Card: 500")
    try:
        read_export(bad)
        check("unknown token refused", False)
    except DocterzRefused:
        check("unknown token refused", True)

    # refusal when the footer is missing
    nofoot = "\n".join(_fixture_consultation().splitlines()[:-3])
    try:
        read_export(nofoot)
        check("missing footer refused", False)
    except DocterzRefused:
        check("missing footer refused", True)

    # a doctored footer must be caught, loudly, not warned about
    doctored = _fixture_consultation().replace(
        "600,0,600,0,600,0,500,2300,0", "1100,0,600,0,600,0,0,2300,0")
    r3 = read_export(doctored)
    check("doctored footer detected", not r3["footer_ok"]
          and any("cash" in m for m in r3["mismatches"]))

    print(f"SELFTEST {ok}/{ok + fail} passed")
    return fail == 0


# ---------------------------------------------------------------- cli

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) < 2:
        print("usage: python docterz_report.py <export.csv> | --selftest")
        sys.exit(2)
    res = read_export(sys.argv[1])          # masked by default
    print(f"variant   : {res['variant']}")
    print(f"date      : {res['date']}")
    print(f"visits    : {len(res['rows'])}")
    print(f"day legs  : " + "  ".join(f"{k}={v}" for k, v in
                                      res["day_legs"].items() if v))
    print(f"footer OK : {res['footer_ok']}")
    for m in res["mismatches"]:
        print(f"  MISMATCH: {m}")
    for a in res["anomalies"]:
        print(f"  anomaly : {a}")
