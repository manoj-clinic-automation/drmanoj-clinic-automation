#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scan_quality.py -- kit S618_SCAN_QUALITY (22-Oct-2026), placed as /root/shared/scan_quality.py. Pure: no database, no file, no network.

ONE rule for "this pharmacy scan needs redoing" (brief section 3.2) and ONE table of its words (section 3.4, charter 8). Computed on every
read, never stored. The Scan App and the finance app import it inside their functions, fail-soft (a failing import never takes a screen down).

    verdict(bill, reading, lie, settings) -> None | (code, owner_words)
        bill     a dict of the assets.db bills row (lane, status, page_of, doc_kind, kind)
        reading  claude_reading.data parsed (a dict) when the reading is good (ok=1), else None
        lie      the scan_lie row of the bill's CURRENT file as a dict (whole_bill, totals_visible, legible, blur_kept), else None
        settings {key: value} from assets.db settings (scan.sum_tolerance_rs, scan.sum_tolerance_pct); absent keys take DEFAULTS
    words(code, who, a=None, b=None) -> the words for 'owner' (English), 'shavez' (Roman Hindi) or 'reception' (Roman Hindi)

The codes, in the order they are tried:
    not_bill    the reading's doc_kind is estimate / quotation / other -- or a good reading named no kind, no total and no line
    blurred     the check says the scan cannot be read (legible false), or the phone kept a blurred photo after two refusals (blur_kept)
    cut         the check says a part of the bill that matters is cut off (whole_bill false) or the total line is not in the scan
                (totals_visible false; a challan is exempt from the total)
    no_total    no total was read (a challan is exempt: bills.doc_kind 'challan' or the reading's 'challan')
    not_adding  |the sum of the line amounts - the total| > max(scan.sum_tolerance_rs, scan.sum_tolerance_pct % of the total), or a line
                with no amount (a challan is exempt)
Only lane 'pharmacy', not set aside (status 'rejected'), not a joined page (page_of). No reading (it failed) = the reading's rules are not
asked: the scan is judged by the check alone.
"""

VERSION = "S618.1"
DEFAULTS = {"scan.redo_since": "2026-10-08", "scan.sum_tolerance_rs": "50", "scan.sum_tolerance_pct": "5"}
BILL_KINDS = ("tax_invoice", "bill", "challan")
NOT_BILL_KINDS = ("estimate", "quotation", "other")
CODES = ("not_bill", "blurred", "cut", "no_total", "not_adding")
CHIPS = ("blurred", "cut", "not_bill")                     # the send-back reasons a person picks (no 'tilted': the server turns a page)

# code -> (owner, English; Shavez, Roman Hindi; reception, Roman Hindi -- what to do). THE table: every screen reads it (charter 8).
WORDS = {
    "blurred": ("Blurred — cannot be read", "Photo dhundli hai",
                "Photo dhundli hai — isi bill ki saaf photo lijiye"),
    "cut": ("Part of the bill is cut off", "Bill ka hissa kata hai",
            "Poora bill nahi aaya — poora bill frame mein laakar scan kijiye"),
    "no_total": ("No total on the scan", "Total nahi dikh raha",
                 "Bill ka total photo mein nahi aaya — neeche tak scan kijiye"),
    "not_adding": ("The lines do not add up to the total (%s vs %s)", "Lines ka jod total se nahi milta",
                   "Amount wala hissa photo mein nahi aaya — poora bill scan kijiye"),
    "not_bill": ("Not a bill", "Yeh bill nahi hai", "Yeh bill nahi hai — asli bill dhoondh kar scan kijiye"),
}
CHIP_WORDS = {"blurred": ("blurred", "dhundli"), "cut": ("cut off", "kata hua"), "not_bill": ("not a bill", "bill nahi")}   # (owner, Shavez)
SENT_BY = {"owner": "Doctor sahab ne bheja", "shavez": "Shavez ne bheja", "other": "%s ne bheja"}   # the reception line under each ask
AUDIENCE = {"owner": 0, "shavez": 1, "reception": 2}


def _num(v):
    if v is None or v == "" or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").replace("₹", "").strip())
    except ValueError:
        return None


def setting(settings, key):
    v = (settings or {}).get(key)
    return v if v not in (None, "") else DEFAULTS.get(key)


def rupees(v):
    """₹ in the Indian grouping, whole rupees: 2400 -> '₹2,400'; 125000 -> '₹1,25,000'."""
    n = _num(v)
    if n is None:
        return "₹?"
    neg, n = n < 0, int(round(abs(n)))
    s = str(n)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "₹" + s


def words(code, who="owner", a=None, b=None):
    w = WORDS.get(code)
    if not w:
        return code or ""
    s = w[AUDIENCE.get(who, 0)]
    if code == "not_adding" and who == "owner":
        s = s % (rupees(a), rupees(b))
    return s


def sent_by(kind, login=""):
    """The reception line: who sent the scan back."""
    if kind == "owner":
        return SENT_BY["owner"]
    if str(login or "").lower() == "shavez":
        return SENT_BY["shavez"]
    return SENT_BY["other"] % (str(login or "").split(" ")[0].title() or "Koi")


def _false(v):
    return v is not None and v != "" and int(v) == 0


def _true(v):
    return v is not None and v != "" and int(v) == 1


def sums(reading):
    """(sum of the line amounts, the total, lines with no amount) of a reading."""
    items = [i for i in ((reading or {}).get("items") or []) if isinstance(i, dict)]
    s = sum(_num(i.get("amount")) or 0.0 for i in items)
    return round(s, 2), _num((reading or {}).get("total_amount")), sum(1 for i in items if _num(i.get("amount")) is None), len(items)


def detail(bill, reading, lie, settings=None):
    """verdict() with its numbers: None | dict(code, words, sum, total)."""
    b = bill or {}
    if str(b.get("lane") or "") != "pharmacy" or str(b.get("status") or "") == "rejected" or b.get("page_of"):
        return None
    r = reading if isinstance(reading, dict) else None
    dk = (r or {}).get("doc_kind")
    challan = str(b.get("doc_kind") or "").lower() == "challan" or dk == "challan"
    s, total, noamt, n = sums(r)
    out = lambda code: dict(code=code, words=words(code, "owner", s, total), sum=s, total=total)   # noqa: E731
    if r is not None and (dk in NOT_BILL_KINDS or (not dk and total is None and n == 0)):
        return out("not_bill")
    lie = lie or {}
    if _false(lie.get("legible")) or _true(lie.get("blur_kept")):
        return out("blurred")
    if _false(lie.get("whole_bill")) or (_false(lie.get("totals_visible")) and not challan):
        return out("cut")
    if r is None or challan:
        return None
    if total is None:
        return out("no_total")
    try:
        rs = float(setting(settings, "scan.sum_tolerance_rs"))
        pct = float(setting(settings, "scan.sum_tolerance_pct"))
    except (TypeError, ValueError):
        rs, pct = float(DEFAULTS["scan.sum_tolerance_rs"]), float(DEFAULTS["scan.sum_tolerance_pct"])
    if noamt or abs(s - total) > max(rs, pct / 100.0 * abs(total)):
        return out("not_adding")
    return None


def verdict(bill, reading, lie, settings=None):
    d = detail(bill, reading, lie, settings)
    return (d["code"], d["words"]) if d else None
