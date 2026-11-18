#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  scan_register.py  ·  v1.0  ·  kit S454_BILL_REGISTER (part 2)  ·  Session 283 (Sanjeevni)  ·  D650 / D662 / D663 / D665 / F-690 / F-691
#
#  A SCAN IS PAIRED WITH ITS MARG BILL ON WHAT A SCAN READS WELL -- ONE SET OF RULES, IN ONE PLACE (S454 section 5), used by the matcher
#  (purchase_app._rematch: it pairs by itself only what is VERIFIED, and the auto-link), the questions (porders.scan_work: "the amount
#  differs" beyond the noise), the month's register (the Scan links page) and the Sarvam counter. Two pages cannot disagree about a bill.
#
#  How a field agrees (agree()):
#    supplier  -- purchase_app._vendor_match / supplier_key as they are, plus: punctuation and brackets dropped, "&" = "AND", the standalone
#                 words PVT, LTD, P, CO and M/S dropped (never a letter inside a name), a trailing BAREILLY dropped; then the learnt
#                 spellings (purchase_scan_alias, the owner's S263 links) and reception's choice. The shop's own name, or a heading such as
#                 "WHOLE SALE CHEMIST & DRUGGIST", is never a supplier: "not read".
#    bill no.  -- Marg's number, leading zeros dropped, equals ONE WHOLE RUN of digits in the scan's reading. A run that is the financial
#                 year, and a reading shaped like a drug-licence number, is never the bill number.
#    date      -- the day and the month agree (a year other than Marg's is a misreading and is ignored).
#    total     -- within Rs 1 is equal, and a non-zero rupee is SHOWN ("Paper Rs 7,979 · Rs 1 rounding -- supplier's figure paid"); more
#                 differs (S726, F-1140: for a COUNTED month the Rs 1-10 noise band no longer passes a total -- every such rupee is corrected
#                 in Marg by Amir; a parked or hidden month keeps purchase.total_noise_rs, so September raises nothing new -- band_p()).
#                 A paper amount reception typed stands in for the scan's reading.
#  The states of a Marg bill that has a scan -- each in exactly one:
#    Amount differs  -- paired, the total differs by more than the noise (one question; then the paper's amount decides)
#    Verified        -- the total agrees, the bill number agrees, and at least one of supplier and date agrees (the matcher's own rule)
#    Has its scan    -- paired, the total agrees or was not read, and not Verified (reception's "Haan", or the auto-link). Nobody is asked.
#  The auto-link: a scan whose supplier agrees and whose amount is within Rs 1 of EXACTLY ONE unscanned bill of that supplier (dated from
#  porders.scan_from, within 60 days of the scan, not refused for it) is paired with no card (audit auto_link) -- S726 (F-1141, D839) only
#  when ALSO: the paper's date (no date read: the scan day) is in the bill's calendar month; NO other bill of that supplier (scanned or
#  not, any state) within the 60 days carries an amount within Rs 1; and neither the read bill number nor the read date differs.
#  Otherwise the pair is reception's one-tap "is this the same bill?" (purchase_app's _why: the bill becomes the scan's likely bill).
#  S726 also adds two states of a paired bill, neither settled: Second look (F-1142: an answer -- a paper amount typed -- contradicts
#  what the scan itself read by more than Rs 1; You & Shavez) and Paired, nothing read (F-1143: the scan read neither a total nor a
#  bill number; reception rescans). In a parked month both are shown with whose line "Nobody (<month> is parked)": nobody is asked.
#  The owner's step view (D840) is check_body(), served at /finance/purchase/page/check.
#  The Sarvam counter (F-690) counts misses by the same reading: supplier and bill number as above; the date as read (a wrong year IS a
#  miss here, and only here); the total beyond Rs 1. Batch and expiry are not judged from a scan.
#
#  The month's register (register()): one row per Marg purchase bill of the month in exactly one state -- Verified · Has its scan ·
#  Amount differs · No scan · Entered twice in Marg (wins over every other) · Accepted without paper (the owner's tap, counted months) --
#  then the month's scans with no Marg bill, each in one state; the head line; "Last 7 days" (is the new flow ready?); the Sarvam
#  figures. A parked month is headed as parked: no accept tap, no day counts, no alert.
#  READ ONLY of the asset app's database. Nothing here prints a phone number, an account number or a key.
# =============================================================================
import datetime as dt
import json
import os
import re
import sqlite3

VERSION = "1.0"
KIT = "S454_BILL_REGISTER"
NOISE_DEFAULT = 10
HINT_DAYS = 60
STOPWORDS = ("PVT", "LTD", "P", "CO", "MS")
HEADING_RE = re.compile(r"\bWHOLE\s*SALE\b|\bWHOLESALE\b|\bCHEMISTS?\s*(?:&|AND)\s*DRUGGISTS?\b|^\s*(?:TAX\s+)?INVOICE\s*$|^\s*(?:GST|CASH|CREDIT)\s+(?:TAX\s+)?INVOICE",
                        re.I)
LICENCE_RE = re.compile(r"\bD\.?\s?L\.?\s*(?:NO|NUMBER)?\b|\bLIC(?:ENCE|ENSE)?\b|\bFORM\b|\b2[01]\s*-?\s*B\b|"
                        r"^\s*\d{1,4}\s*/\s*(?:19|20)\d\d\s*/\s*[A-Z]{2,}\s*$|\bUP\s*-?\s*\d{2}\s*[A-Z]{0,3}\s*-?\s*\d{4,}", re.I)
FY_RE = re.compile(r"(?<!\d)20\d\d\s*[-/]\s*(?:20)?\d\d(?!\d)")
MONTHS3 = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")
STATES = ("verified", "has_scan", "amount_differs", "no_scan", "double", "accepted", "second_look", "unread_pair")    # S726 adds the last two
STATE_EN = {"verified": "Verified", "has_scan": "Has its scan", "amount_differs": "Amount differs", "no_scan": "No scan",
            "double": "Entered twice in Marg", "accepted": "Accepted without paper", "second_look": "Second look",
            "unread_pair": "Paired, nothing read"}
KIT_S726 = "S726_PURCHASE_RULES"
SCAN_STATES = ("probably", "vendor", "to_name", "unread", "waiting", "second")
SCAN_EN = {"probably": "Probably a bill already in Marg, read differently", "vendor": "Supplier not known",
           "to_name": "To be named by reception (no number, no amount)", "unread": "Unread pharmacy paper (reception said it is a pharmacy bill)",
           "waiting": "Waiting for Marg's entry", "second": "Second scan of a bill, set aside"}
SCAN_WHOSE = {"probably": "Reception: one question each", "vendor": "Reception: one question each", "to_name": "Reception: one question each",
              "unread": "Reception: one question when its Marg bill comes", "waiting": "Nobody", "second": "Nobody"}


# ------------------------------------------------------------------ small things
def _pa():
    import purchase_app                                       # noqa: PLC0415 -- beside this file
    return purchase_app


def today():
    v = os.environ.get("ORDER_TODAY", "")
    try:
        return dt.date.fromisoformat(v) if v else dt.date.today()
    except ValueError:
        return dt.date.today()


def setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and r[0] is not None and str(r[0]).strip() != "":
            return str(r[0]).strip()
    except sqlite3.Error:
        pass
    return default


def int_setting(con, key, default):
    try:
        return int(float(setting(con, key, str(default))))
    except (TypeError, ValueError):
        return default


def noise_p(con):
    return 100 * max(0, int_setting(con, "purchase.total_noise_rs", NOISE_DEFAULT))


def rs(p):
    if p is None:
        return "—"
    v = str(int(round(abs(int(p)) / 100.0)))
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return ("−" if int(p) < 0 else "") + "₹" + v


def rs2(p):
    """S726: like rs(), with the paise shown when there are any ('₹4,762.50')."""
    if p is None:
        return "—"
    p = int(p)
    a = abs(p)
    v = rs(a - a % 100) + ((".%02d" % (a % 100)) if a % 100 else "")
    return ("−" + v) if p < 0 else v


def _date(s):
    try:
        return dt.date.fromisoformat(str(s or "")[:10])
    except ValueError:
        return None


def ddmon(iso):
    d = _date(iso)
    return "%02d-%s" % (d.day, MONTHS3[d.month - 1]) if d else ""


def month_name(ym):
    try:
        return "%s %s" % (MONTHS[int(ym[5:7]) - 1], ym[:4])
    except (ValueError, IndexError):
        return ym


def esc(s):
    import html                                               # noqa: PLC0415
    return html.escape("" if s is None else str(s), quote=True)


def _amount_p(v):
    try:
        return None if v in (None, "") else int(round(float(v) * 100))
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------ the rules (S454 section 5)
def sup_norm(s):
    """Upper case; punctuation and brackets dropped; '&' = AND; standalone PVT, LTD, P, CO, M/S and P.L. dropped; a trailing BAREILLY dropped."""
    t = str(s or "").upper()
    t = re.sub(r"\bM\s*/\s*S\b\.?", " ", t)
    t = re.sub(r"(?<![A-Z0-9.])P\s*\.\s*L\b\.?", " ", t)       # S454 P3B (18.3): a standalone "P.L." is dropped like PVT and LTD
    t = t.replace("&", " AND ")
    t = re.sub(r"[^A-Z0-9 ]+", " ", t)
    words = [w for w in t.split() if w not in STOPWORDS]
    while len(words) > 1 and words[-1] in ("BAREILLY", "BLY"):
        words.pop()
    return " ".join(words)


def vendor_not_read(s):
    """The scan's supplier field holds nothing usable: empty, the shop's own name, or a heading."""
    t = str(s or "").strip()
    if not t or not re.search(r"[A-Za-z]", t):
        return True
    if HEADING_RE.search(t):
        return True
    try:
        pa = _pa()
        return bool(pa._is_buyer_s439(pa._vendor_tokens_s439(t)))
    except Exception:                                         # noqa: BLE001
        return bool(re.search(r"SANJ[EI]+V", t.upper()))


class Ctx(object):
    """What the rules need beyond the two rows: the learnt spellings, the owner's links, reception's choices and paper amounts, the noise."""

    def __init__(self, con):
        pa = _pa()
        self.noise = noise_p(con)
        v726 = setting(con, "purchase.register_from", "2026-10-01")          # S726: the first counted month (as month_class reads it)
        self.first = v726[:7] if re.match(r"^\d{4}-\d\d", v726) else "2026-10"
        self.learned = {}
        try:
            self.learned = {r[0]: r[1] for r in con.execute("SELECT ocr_norm, supplier_norm FROM purchase_scan_alias")}
        except sqlite3.Error:
            pass
        self.alias = {}
        try:
            for a, b in con.execute("SELECT bill_norm, register_norm FROM purchase_vendor_alias"):
                ka, kb = pa.supplier_key(a), pa.supplier_key(b)
                if ka and kb:
                    self.alias.setdefault(kb, set()).add(ka)
                    self.alias.setdefault(ka, set()).add(kb)
        except sqlite3.Error:
            pass
        self.chosen, self.paper, self.amount_state, self.likely, self.why, self.no = {}, {}, {}, {}, {}, {}
        try:
            for r in con.execute("SELECT asset_bill_id, chosen_vendor, paper_amount, amount_state, likely_bill, why, hint_no FROM purchase_scan_state"):
                sid = int(r[0])
                if r[1] not in (None, "", "-"):
                    self.chosen[sid] = r[1]
                if r[2] is not None:
                    self.paper[sid] = int(r[2])
                if r[3]:
                    self.amount_state[sid] = r[3]
                if r[4]:
                    self.likely[sid] = int(r[4])
                self.why[sid] = r[5] or ""
                self.no[sid] = {int(x) for x in str(r[6] or "").split(",") if x.strip().isdigit()}
        except sqlite3.Error:
            pass
        try:                                                  # a parked month's answer is kept on the register (S454 4.6)
            for sid, v in con.execute("SELECT asset_bill_id, value FROM s454_scan_answer WHERE kind='amount' AND answer='paper'"):
                if int(sid) not in self.paper and str(v or "").lstrip("-").isdigit():
                    self.paper[int(sid)] = int(v)
            for sid, v in con.execute("SELECT asset_bill_id, value FROM s454_scan_answer WHERE kind='vendor' AND answer='chosen'"):
                if v not in (None, "", "-") and int(sid) not in self.chosen:
                    self.chosen[int(sid)] = v
        except sqlite3.Error:
            pass


def supplier(cx, scan_vendor, bill_supplier, chosen=None):
    """'agree' | 'differ' | 'not_read'."""
    pa = _pa()
    bk = pa.supplier_key(bill_supplier)
    if chosen:
        return "agree" if (chosen == bk or sup_norm(chosen) == sup_norm(bill_supplier)) else "differ"
    if vendor_not_read(scan_vendor):
        return "not_read"
    sk = pa.supplier_key(scan_vendor)
    if pa._vendor_match(scan_vendor, bill_supplier):
        return "agree"
    if sup_norm(scan_vendor) and sup_norm(scan_vendor) == sup_norm(bill_supplier):
        return "agree"
    for k in (sk, sup_norm(scan_vendor)):
        lk = cx.learned.get(k)
        if lk and (lk == bk or sup_norm(lk) == sup_norm(bill_supplier)):
            return "agree"
    if sk in cx.alias.get(bk, set()):
        return "agree"
    return "differ"


def _runs(text):
    t = FY_RE.sub(" ", str(text or ""))
    return [r for r in (x.lstrip("0") for x in re.findall(r"\d+", t)) if r]


def billno(scan_no, marg_no):
    """'agree' | 'differ' | 'not_read'."""
    s = str(scan_no or "").strip()
    if not s or not re.search(r"\d", s):
        return "not_read"
    if LICENCE_RE.search(s):
        return "differ"
    m = [r for r in (x.lstrip("0") for x in re.findall(r"\d+", str(marg_no or ""))) if r]
    if not m:
        return "differ"
    return "agree" if m[-1] in _runs(s) else "differ"


def billno_compat(scan_no, marg_no):
    """S726: the scan's reading against Marg's number for the S726 tests only (billno() itself is unchanged; other code reads it) ->
    'agree' | 'close' | 'differ' | 'not_read'. All the digits of each, letters and separators dropped, leading zeros stripped:
    'agree' when equal, or when the shorter (4 digits or more) ends the longer (Marg truncates: 90058 <- RT-490058, 1692 <- A011692), or
    when the digit runs, each without its zeros, join to the same (YS0706202627 <- YS/0706/2026-27, the year kept here);
    'close' when the shorter (3 digits or more) and the same-length end of the longer differ in exactly ONE digit (an OCR misread:
    11086 <- A011986, 77627 <- GPPL/24-77527); else 'differ'. A licence-shaped reading is 'differ', as in billno()."""
    st = str(scan_no or "")
    if not re.search(r"\d", st):
        return "not_read"
    if billno(scan_no, marg_no) == "agree":
        return "agree"                                             # never stricter than billno() (1692 <- 1692/26-27)
    if LICENCE_RE.search(st):
        return "differ"
    sd = re.sub(r"\D", "", st).lstrip("0")
    md = re.sub(r"\D", "", str(marg_no or "")).lstrip("0")
    if not sd or not md:
        return "differ"
    sr = "".join(x.lstrip("0") for x in re.findall(r"\d+", st))
    mr = "".join(x.lstrip("0") for x in re.findall(r"\d+", str(marg_no or "")))
    if sd == md or (sr and sr == mr) or sr == md or sd == mr:
        return "agree"
    short, long_ = sorted((sd, md), key=len)
    if len(short) >= 4 and long_.endswith(short):
        return "agree"
    if len(short) >= 3 and sum(1 for x, y in zip(short, long_[-len(short):]) if x != y) == 1:
        return "close"
    return "differ"


def date_md(scan_date, marg_date):
    sd, md = _date(scan_date), _date(marg_date)
    if sd is None:
        return "not_read"
    if md is None:
        return "differ"
    return "agree" if (sd.month, sd.day) == (md.month, md.day) else "differ"


def total(scan_p, marg_p, noise):
    """(class, difference in paise): equal (within Rs 1) | noise (within the noise setting) | differ | not_read."""
    if scan_p is None or int(scan_p) == 0:
        return "not_read", None
    d = int(scan_p) - int(marg_p or 0)
    if abs(d) <= 100:
        return "equal", d
    if abs(d) <= noise:
        return "noise", d
    return "differ", d


def scan_amount(cx, s):
    """The scan's total as the rules read it: reception's paper amount, else what the scan read."""
    sid = int(s["id"])
    if sid in cx.paper:
        return cx.paper[sid]
    return s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))


def agree(cx, s, b):
    """One scan against one Marg bill -> dict(supplier, billno, date, total, diff, paper)."""
    sid = int(s["id"]) if s.get("id") is not None else None
    tp = scan_amount(cx, s) if sid is not None else (s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount")))
    tc, diff = total(tp, b["amount_p"], band_p(cx, b))              # S726 (F-1140): Rs 1 in a counted month
    return dict(supplier=supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)), billno=billno(s.get("bill_no"), b["bill_no"]),
                date=date_md(s.get("bill_date"), b["bill_date"]), total=tc, diff=diff, scan_p=tp, paper=(sid in cx.paper))


def band_p(cx, b):
    """S726 (F-1140): the total's band for this bill -- Rs 1 when its month is counted (every rupee beyond is corrected in Marg); a parked or
    hidden month (September) keeps purchase.total_noise_rs, as it was cleared."""
    ym = str(b.get("month") or str(b.get("bill_date") or "")[:7])
    return 100 if (not ym or ym >= getattr(cx, "first", "2026-10")) else cx.noise


def verified(a):
    return a["total"] in ("equal", "noise") and a["billno"] == "agree" and (a["supplier"] == "agree" or a["date"] == "agree")


def pair_state(a):
    if a["total"] == "differ":
        return "amount_differs"
    return "verified" if verified(a) else "has_scan"


def s726_state(cx, s, a, present=True):
    """S726: a paired bill's state -- pair_state(a), unless the scan read neither a total nor a bill number (unread_pair, F-1143) or an
    answer (a paper amount typed) contradicts what the scan itself read by more than Rs 1 (second_look, F-1142). `present`: the scan's
    own row was read (a scan missing from the asset app's list is never judged unread)."""
    st = pair_state(a)
    if not present:
        return st
    raw = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
    read_total = raw not in (None, 0)
    if not read_total and a["billno"] == "not_read":
        return "unread_pair"
    sid = int(s["id"]) if s.get("id") is not None else None
    if sid is not None and sid in cx.paper and read_total and abs(int(cx.paper[sid]) - int(raw)) > 100:
        return "second_look"
    return st


def sarvam_flags(cx, s, b):
    """The Sarvam counter (F-690): supplier and bill number by the rules; the date as read (a wrong year is a miss here); the total beyond Rs 1."""
    sd = _date(s.get("bill_date"))
    raw_total = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
    return dict(supplier_ok=int(supplier(cx, s.get("vendor"), b["supplier"]) == "agree"),        # what the scan READ: reception's choice is not a reading
                billno_ok=int(billno(s.get("bill_no"), b["bill_no"]) == "agree"),
                date_ok=int(bool(sd) and sd.isoformat() == str(b["bill_date"])[:10]),
                total_ok=int(raw_total is not None and abs(int(raw_total) - int(b["amount_p"] or 0)) <= 100))


# ------------------------------------------------------------------ the auto-link (used by purchase_app._rematch)
def scan_month(s, bill_month=None):
    """S726: the month a scan belongs to -- the asset app's bill_month, else its paper date (when within 120 days of its scan day: a
    misread year is not a month), else its scan day (IST). '' when nothing is known."""
    bm = str(bill_month or s.get("bill_month") or "")
    if re.match(r"^\d{4}-\d\d$", bm):
        return bm
    day = _date(_scan_day(s))
    pd = _date(s.get("bill_date"))
    if pd and (day is None or abs((pd - day).days) <= 120):
        return pd.isoformat()[:7]
    return day.isoformat()[:7] if day else ""


def autolink_ok(cx, s, b, bills, undo=False, before=None):
    """S726 (F-1141, D839): may this amount-only pair stand by itself? -> (True, '') or (False, the reason in plain English).
    The paper's date (no date read: the scan day) is in the bill's calendar month; no OTHER bill of that supplier (scanned or not, any
    state) within HINT_DAYS of the scan carries an amount within Rs 1 of the scan's; the read bill number and the read date do not differ.
    The number: 'differ' (billno_compat) always contradicts; 'close' (one digit off) does not take an existing link apart (undo=True) but
    is not enough for a NEW pair (reception is asked). before (the undo only): only bills dated on or before it count as 'another bill'.
    A number that AGREES, with the amount within Rs 1 and the supplier agreeing, is the same bill: OK, the date and same-amount tests skipped."""
    a = agree(cx, s, b)
    bcmp = billno_compat(s.get("bill_no"), b["bill_no"])
    sp0 = scan_amount(cx, s)
    if (bcmp == "agree" and sp0 not in (None, 0) and abs(int(sp0) - int(b["amount_p"] or 0)) <= 100
            and supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(int(s["id"]))) == "agree"):
        return True, ""                                            # the number, the amount and the supplier agree: the same bill -- a misread
        #                                                            date or an older bill of the same amount never takes it apart
    if bcmp == "differ" or (bcmp == "close" and not undo):      # S726: Marg's number written another way is not a contradiction
        return False, "the scan's bill number reads %s%s" % (str(s.get("bill_no") or "").strip()[:30] or "otherwise",
                                                             " (one digit off: a question, not a pair by itself)" if bcmp == "close" else "")
    if a["date"] == "differ":
        return False, "the scan's date reads %s" % (ddmon(s.get("bill_date")) or "otherwise")
    bd = _date(b.get("bill_date"))
    if a["date"] != "agree":
        day = _date(_scan_day(s))
        if bd is None or day is None or (day.year, day.month) != (bd.year, bd.month):
            return False, "no date read and it was scanned in another month (%s)" % (ddmon(day.isoformat()) if day else "unknown")
    sp = scan_amount(cx, s)
    if sp is None or int(sp) == 0:
        return False, "no amount read"
    sid = int(s["id"])
    days = [d for d in (_date(s.get("bill_date")), _date(str(s.get("created_at") or "")[:10])) if d]
    pa = _pa()
    bk = pa.supplier_key(b["supplier"])
    for x in bills:
        if x["id"] == b["id"] or abs(int(sp) - int(x["amount_p"] or 0)) > 100:
            continue
        xd = _date(x.get("bill_date"))
        if not xd or not days or min(abs((d - xd).days) for d in days) > HINT_DAYS:
            continue
        if before is not None and xd > before:
            continue                                               # the undo: a newer same-amount bill never takes a correct pair apart
        if pa.supplier_key(x["supplier"]) != bk and supplier(cx, s.get("vendor"), x["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        return False, "another bill of this supplier carries this amount (%s of %s)" % (x["bill_no"], ddmon(x.get("bill_date")))
    return True, ""


def autolink_choice(cx, s, bills, taken, scan_from, refused=()):
    """The one unscanned bill this scan pairs with by itself, or None (S726: autolink_pick's first part -- the S726 conditions applied)."""
    return autolink_pick(cx, s, bills, taken, scan_from, refused)[0]


def autolink_pick(cx, s, bills, taken, scan_from, refused=()):
    """(bill, None, '') -- the one unscanned bill this scan pairs with by itself: its supplier agrees, its amount is within Rs 1 of EXACTLY
    ONE unscanned bill of that supplier dated from scan_from and within HINT_DAYS of the scan (paper date or scan day), not refused for it,
    AND autolink_ok (S726). (None, candidate, why) when S726 refuses that one candidate -- it becomes reception's question. (None, None, '')."""
    sp = scan_amount(cx, s)
    if sp is None or int(sp) == 0:
        return None, None, ""
    sid = int(s["id"])
    days = [d for d in (_date(s.get("bill_date")), _date(str(s.get("created_at") or "")[:10])) if d]
    out = []
    for b in bills:
        if b["id"] in taken or b["id"] in refused or b["id"] in cx.no.get(sid, set()):
            continue
        if str(b.get("bill_date") or "") < scan_from:
            continue
        bd = _date(b.get("bill_date"))
        if not bd or not days or min(abs((d - bd).days) for d in days) > HINT_DAYS:
            continue
        if abs(int(sp) - int(b["amount_p"] or 0)) > 100:
            continue
        if supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        out.append(b)
    if len(out) != 1:
        return None, None, ""
    ok, why = autolink_ok(cx, s, out[0], bills)
    return (out[0], None, "") if ok else (None, out[0], why)


# ------------------------------------------------------------------ data
def asset_scans(con=None):
    """{id: scan} -- the captured pharmacy scans (assets.db, READ ONLY); None when unreachable."""
    pa = _pa()
    acon = pa._assets_con()
    if acon is None:
        return None
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "total_amount", "submitted_at", "created_at", "ocr_status", "dup_of",
                           "bill_month", "lane", "status", "kind") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND status='captured' ORDER BY id" % ", ".join(sel))]
    finally:
        acon.close()
    out = {}
    for r in rows:
        r["amount_p"] = _amount_p(r.get("total_amount"))
        r["day"] = _scan_day(r)
        bm = str(r.get("bill_month") or "")
        r["month"] = bm if re.match(r"^\d{4}-\d\d$", bm) else (str(r.get("bill_date") or "")[:7] if _date(r.get("bill_date")) else str(r["day"] or "")[:7])
        out[int(r["id"])] = r
    return out


def s824_set_aside(con=None):
    """S824 (F-1378): {id: scan} -- the pharmacy scans the scan app SET ASIDE as a second scan of another bill (status 'rejected', dup_of
    set, not a page of a bill; assets.db, READ ONLY), in asset_scans' shape. Read ONLY by _s740_revised: a dealer's revised bill set aside
    by a "same paper" answer is still the dealer's revised bill. {} when unreachable or the columns are not there."""
    pa = _pa()
    acon = pa._assets_con()
    if acon is None:
        return {}
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        if not {"dup_of", "status", "kind"} <= cols:
            return {}
        sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "total_amount", "submitted_at", "created_at", "ocr_status", "dup_of",
                           "bill_month", "lane", "status", "kind") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Pharmacy' AND status='rejected' AND dup_of IS NOT NULL%s ORDER BY id"
                                              % (", ".join(sel), " AND page_of IS NULL" if "page_of" in cols else ""))]
    except sqlite3.Error:
        return {}
    finally:
        acon.close()
    out = {}
    for r in rows:
        r["amount_p"] = _amount_p(r.get("total_amount"))
        r["day"] = _scan_day(r)
        out[int(r["id"])] = r
    return out


def _scan_day(r):
    """The scan's day in IST: submitted_at (IST) else created_at (UTC) + 5:30."""
    s = str(r.get("submitted_at") or "").replace("T", " ")
    try:
        return dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M").date().isoformat()
    except ValueError:
        pass
    c = str(r.get("created_at") or "").replace("T", " ")
    try:
        return (dt.datetime.strptime(c[:19], "%Y-%m-%d %H:%M:%S") + dt.timedelta(hours=5, minutes=30)).date().isoformat()
    except ValueError:
        return ""


def _scan_moment(r):
    s = str(r.get("submitted_at") or "").replace("T", " ")
    try:
        return dt.datetime.strptime(s[:16], "%Y-%m-%d %H:%M")
    except ValueError:
        pass
    c = str(r.get("created_at") or "").replace("T", " ")
    try:
        return dt.datetime.strptime(c[:19], "%Y-%m-%d %H:%M:%S") + dt.timedelta(hours=5, minutes=30)
    except ValueError:
        return None


def links(con):
    try:
        return {int(r[0]): dict(scan=int(r[1]), grade=r[2], rule=r[3] or "", at=r[4]) for r in
                con.execute("SELECT bill_id, asset_bill_id, grade, matched_on, linked_at FROM purchase_scan_link")}
    except sqlite3.Error:
        return {}


def s726_quiet_bills(con):
    """S726: the bills of a month not counted (September) whose AUTO link S726 undid and that have no scan now -> {bill id}. Nobody is
    asked about them: September is parked and was cleared by the owner (the undo only freed a counted month's paper)."""
    try:
        ids = {int(r[0]) for r in con.execute("SELECT DISTINCT ref FROM purchase_audit WHERE action='auto_link_undone'") if str(r[0] or "").isdigit()}
        if not ids:
            return set()
        linked = {int(r[0]) for r in con.execute("SELECT bill_id FROM purchase_scan_link")}
        out = set()
        for bid in ids - linked:
            r = con.execute("SELECT month, bill_date FROM purchase_bill WHERE id=?", (bid,)).fetchone()
            ym = (r[0] or str(r[1] or "")[:7]) if r else ""
            if r and re.match(r"^\d{4}-\d\d$", ym) and month_class(con, ym) != "counted":
                out.add(bid)
        return out
    except sqlite3.Error:
        return set()


def month_class(con, ym):
    """counted | parked | hidden -- the same reading as the reception screen (purchase.register_from, purchase.parked_months)."""
    v = setting(con, "purchase.register_from", "2026-10-01")
    first = v[:7] if re.match(r"^\d{4}-\d\d", v) else "2026-10"
    if not ym or ym >= first:
        return "counted"
    parked = [m.strip() for m in setting(con, "purchase.parked_months", "2026-09").split(",") if m.strip()]
    return "parked" if ym in parked else "hidden"


def _doubles(bills):
    """S440's reading of a double entry in Marg: the same supplier, date and amount under one number typed in two cases ->
    {member id: [the group's ids]}."""
    g = {}
    for b in bills:
        g.setdefault((b["supplier_norm"], str(b["bill_no"] or "").strip().lower(), b["bill_date"], b["amount_p"]), []).append(b["id"])
    out = {}
    for ids in g.values():
        if len(ids) > 1:
            for i in ids:
                out[i] = sorted(ids)
    return out


def entered_at(con, b):
    """When Marg's entry of this bill first reached the server: the earliest live-or-old export that carried a line of it, else the export
    its bill row came from."""
    try:
        r = con.execute("SELECT MIN(e.received_at) FROM purchase_line l JOIN purchase_export e ON e.md5=l.source_md5 WHERE l.supplier_norm=? "
                        "AND l.bill_no=? AND l.bill_date=?", (b["supplier_norm"], b["bill_no"], b["bill_date"])).fetchone()
        if r and r[0]:
            return str(r[0])[:19]
        r = con.execute("SELECT MIN(received_at) FROM purchase_export WHERE md5 IN (?,?)", (b.get("bw_md5"), b.get("sw_md5"))).fetchone()
        return str(r[0])[:19] if r and r[0] else ""
    except sqlite3.Error:
        return ""


# ------------------------------------------------------------------ the register
def register(con, month):
    """The month's register (the docstring at the top). Returns dict(month, cls, rows, scans, counts, scan_counts, settled, total, ...)."""
    pa = _pa()
    cx = Ctx(con)
    cls = month_class(con, month)
    allb = [dict(r) for r in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL + " ORDER BY b.bill_date, b.id")]
    bills = [b for b in allb if str(b.get("month") or str(b["bill_date"])[:7]) == month]
    lk = links(con)
    scans = asset_scans(con) or {}
    dbl = _doubles(bills)
    missing = {}
    try:
        missing = {int(r[0]): dict(by=r[1], at=r[2], accepted_by=r[3], accepted_at=r[4]) for r in
                   con.execute("SELECT bill_id, by, at, accepted_by, accepted_at FROM s454_paper_missing")}
    except sqlite3.Error:
        pass
    hint = {}
    for sid, b_id in cx.likely.items():
        if cx.why.get(sid) in ("number_differs", "amount_differs", "no_digits") and sid not in {v["scan"] for v in lk.values()}:
            hint.setdefault(b_id, sid)
    t = today()
    quiet726 = s726_quiet_bills(con) if cls != "counted" else set()
    rows, seen_double = [], set()
    for b in bills:
        if b["id"] in seen_double:
            continue
        row = dict(id=b["id"], date=b["bill_date"], supplier=pa.supplier_key(b["supplier"]), bill_no=str(b["bill_no"] or ""), amount_p=int(b["amount_p"] or 0),
                   scan=None, stamp="", note="", whose="Nobody", state=None)
        l = lk.get(b["id"])
        if b["id"] in dbl:
            grp = dbl[b["id"]]
            seen_double.update(grp)
            members = [x for x in bills if x["id"] in grp]
            row["bill_no"] = " and ".join(str(x["bill_no"]) for x in members)
            sc = next((lk[x]["scan"] for x in grp if x in lk), None)
            row.update(state="double", scan=sc, stamp=(scans.get(sc) or {}).get("stamp_no") or "", whose="Amir: a Marg correction",
                       note="The same bill entered %d times in Marg; one entry is to be removed." % len(members))
        elif l:
            s = scans.get(l["scan"]) or dict(id=l["scan"], vendor=None, bill_no=None, bill_date=None, amount_p=None)
            a = agree(cx, s, b)
            st = s726_state(cx, s, a, l["scan"] in scans)           # S726: second look (F-1142) / paired, nothing read (F-1143)
            row.update(scan=l["scan"], stamp=s.get("stamp_no") or ("#%d" % l["scan"]), state=st, agree=a)
            row["note"], row["whose"] = _note(cx, st, a, b, s, l)
            if cls != "counted" and st in ("second_look", "unread_pair"):        # S726: a parked month raises nothing to a person
                row["whose"] = "Nobody (%s is parked)" % MONTHS[int(month[5:7]) - 1]
        else:
            m = missing.get(b["id"])
            if m and m.get("accepted_at") and cls == "counted":
                row.update(state="accepted", note="Accepted without paper by %s on %s." % (m.get("accepted_by") or "?", ddmon(m["accepted_at"])),
                           whose="Nobody")
            else:
                bits, whose = [], "Reception: to scan"
                if b["id"] in hint:
                    hs = scans.get(hint[b["id"]]) or {}
                    bits.append("Scan %s is probably this bill; its number was read as “%s”." % (hs.get("stamp_no") or "#%d" % hint[b["id"]],
                                                                                                 hs.get("bill_no") or "nothing"))
                    whose = "Reception: a question"
                if m:
                    bits.append("Paper not found (reception, %s)." % ddmon(m["at"]))
                    whose = "You: accept or ask" if cls == "counted" else "Nobody"
                if cls == "counted":
                    bd = _date(b["bill_date"])
                    if bd:
                        bits.append("%d day%s waited." % ((t - bd).days, "" if (t - bd).days == 1 else "s"))
                elif cls == "parked" and whose.startswith("Reception: to scan"):
                    whose = "Reception (optional)"
                row.update(state="no_scan", note=" ".join(bits), whose=whose, missing=bool(m))
                if b["id"] in quiet726:                            # S726: its amount-only pair was undone to free a counted paper
                    row.update(note="Its amount-only pair with a later month's paper was undone (S726).",
                               whose="Nobody (%s is parked)" % MONTHS[int(month[5:7]) - 1])
        rows.append(row)
    counts = {k: sum(1 for r in rows if r["state"] == k) for k in STATES}
    # the scans of this month with no Marg bill
    linked_scans = {v["scan"] for v in lk.values()}
    answers = {}
    try:
        for sid, kind, ans in con.execute("SELECT asset_bill_id, kind, answer FROM s454_scan_answer"):
            answers.setdefault(int(sid), {})[kind] = ans
    except sqlite3.Error:
        pass
    open_scans = []
    for sid, s in sorted(scans.items()):
        if sid in linked_scans or s.get("dup_of") or str(s.get("lane") or "pharmacy") != "pharmacy" or s.get("month") != month:
            continue
        why = cx.why.get(sid, "")
        unread = _unread(s)
        if why == "dup":
            stt = "second"
        elif unread and (answers.get(sid) or {}).get("pharmacy") == "yes":
            stt = "unread"
        elif unread:
            stt = "to_name"
        elif why in ("number_differs", "amount_differs", "no_digits") and cx.likely.get(sid):
            stt = "probably"
        elif why == "vendor_unknown" and sid not in cx.chosen:
            stt = "vendor"
        else:
            stt = "waiting"
        open_scans.append(dict(id=sid, stamp=s.get("stamp_no") or "#%d" % sid, state=stt, vendor=s.get("vendor") or "", bill_no=s.get("bill_no") or "",
                               amount_p=s.get("amount_p"), day=s.get("day")))
    scan_counts = {k: sum(1 for x in open_scans if x["state"] == k) for k in SCAN_STATES}
    settled = counts["verified"] + counts["has_scan"] + counts["accepted"]
    total_rows = len(rows)
    open_n = sum(v for k, v in scan_counts.items() if k != "second")
    done_date = ""
    if total_rows and settled == total_rows and not open_n:
        done_date = max([str((lk.get(r["id"]) or {}).get("at") or "")[:10] for r in rows] + [""])
    return dict(month=month, cls=cls, rows=rows, scans=open_scans, counts=counts, scan_counts=scan_counts, settled=settled, total=total_rows,
                open_scans=open_n, done_date=done_date, n_bills=len(bills))


def _unread(s):
    no_no = not str(s.get("bill_no") or "").strip()
    no_amt = s.get("amount_p") in (None, 0)
    head = re.search(r"\b(ESTIMATE|CHALLAN|QUOTATION)\b", "%s %s" % (s.get("vendor") or "", s.get("bill_no") or ""), re.I)
    return bool((no_no and no_amt) or head)


def _note(cx, st, a, b, s, l):
    """(the row's note, whose line now) for a paired bill."""
    bits = []
    how = l.get("grade") or ""
    if st == "unread_pair":                                    # S726 (F-1143): nothing read is never settled
        return ("%s; the scan read neither a total nor a bill number, so nothing on it confirms this bill. Rescan the paper."
                % ("Paired by reception" if how == "CONFIRMED" else "Paired"), "Reception: rescan")
    if st == "second_look":                                    # S726 (F-1142): the answer and the scan disagree
        raw = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
        return ("The amount given for the paper is %s; the scan itself reads %s; Marg %s. The two readings of one paper disagree by more "
                "than ₹1 — a second look." % (rs2(a["scan_p"]), rs2(raw), rs2(b["amount_p"])), "You & Shavez")
    if st == "amount_differs":
        sp = a["scan_p"]
        if a["paper"]:
            astate = cx.amount_state.get(int(s["id"]), "")
            more = sp - int(b["amount_p"] or 0)
            bits.append("The paper reads %s, %s %s." % (rs(sp), rs(abs(more)), "more" if more > 0 else "less"))
            whose = {"marg_wrong": "Amir: a Marg correction", "owner": "You"}.get(astate, "Nobody")
        else:
            bits.append("The scan reads %s; Marg %s — waiting for reception." % (rs(sp), rs(b["amount_p"])))
            whose = "Reception: a question"
        return " ".join(bits), whose
    if a["total"] in ("equal", "noise") and a.get("diff"):     # S726 (F-1140): a rounding rupee is shown, never silent
        bits.append("Paper %s · %s rounding — supplier's figure paid." % (rs2(a["scan_p"]), rs2(abs(a["diff"]))))
    if st == "verified":
        if a["supplier"] == "not_read":
            bits.append("Supplier not read on the scan.")
        elif a["supplier"] == "differ":
            bits.append("The scan's supplier reads “%s”; Marg's stands." % (s.get("vendor") or ""))
        if a["date"] == "differ":
            bits.append("The scan reads the date as %s; Marg's date stands." % (ddmon(s.get("bill_date")) or "—"))
        elif a["date"] == "not_read":
            bits.append("Date not read on the scan.")
        return " ".join(bits), "Nobody"
    # has its scan
    agreed = [k for k in ("supplier", "date", "total") if (a[k] == "agree" or (k == "total" and a[k] in ("equal", "noise")))]
    misread = [k for k in ("billno", "supplier", "date") if a[k] in ("differ", "not_read")]
    lab = {"supplier": "supplier", "date": "date", "total": "total", "billno": "bill number"}
    if how == "CONFIRMED":
        lead = "Paired by reception"
        if "nothing was read" in (l.get("rule") or ""):
            lead = "Paired by reception; nothing was read on the paper"
    elif how == "AUTO":
        lead = "Paired by itself: the only unscanned bill of this supplier with this amount"
    elif "S726" in (l.get("rule") or ""):
        lead = "Paired on bill number and date"
    else:
        lead = "Paired on %s" % (", ".join(lab[k] for k in agreed) or "what was read")
    tail = ("; the scan's %s %s misread." % (" and ".join(lab[k] for k in misread), "was" if len(misread) == 1 else "were")) if misread else "."
    if a["total"] == "not_read":
        tail = tail.rstrip(".") + "; no total read." if misread else "; no total read."
    bits.insert(0, lead + tail)
    return " ".join(bits), "Nobody"


# ------------------------------------------------------------------ is the new flow ready? (S454 7.2)
def readiness(con, days=7):
    """(N bills entered in Marg in the last `days` days, n had their scan before the entry, m paired with no tap)."""
    pa = _pa()
    since = (dt.datetime.now() - dt.timedelta(days=days)).isoformat()[:19]
    lk = links(con)
    scans = asset_scans(con) or {}
    n = had = notap = 0
    for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL + " AND b.bill_date>=?", ((dt.date.today() - dt.timedelta(days=days + 45)).isoformat(),)):
        b = dict(b)
        ent = entered_at(con, b)
        if not ent or ent < since:
            continue
        n += 1
        l = lk.get(b["id"])
        if not l:
            continue
        sm = _scan_moment(scans.get(l["scan"]) or {})
        if sm and sm.isoformat()[:19] <= ent:
            had += 1
        if l["grade"] != "CONFIRMED":
            notap += 1
    return n, had, notap


# ------------------------------------------------------------------ the Sarvam counter (F-690)
def sarvam(con, month):
    """The month's linked bills read by the counter's rule: dict(n, supplier, billno, date, total = how many READ RIGHT; misses; items)."""
    pa = _pa()
    cx = Ctx(con)
    lk = links(con)
    scans = asset_scans(con) or {}
    out = dict(n=0, supplier=0, billno=0, date=0, total=0, items_read=0, items_right=0, agreed=0)
    for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL + " AND COALESCE(b.month, substr(b.bill_date,1,7))=?", (month,)):
        b = dict(b)
        l = lk.get(b["id"])
        if not l or l["scan"] not in scans:
            continue
        f = sarvam_flags(cx, dict(scans[l["scan"]]), b)
        out["n"] += 1
        for k in ("supplier", "billno", "date", "total"):
            out[k] += f[k + "_ok"]
        out["agreed"] += int(all(f.values()))
    try:
        for read, detail in con.execute("SELECT items_read, detail FROM purchase_sarvam_check WHERE month=?", (month,)):
            items = (json.loads(detail or "{}") or {}).get("items") or []
            out["items_read"] += int(read or 0)
            out["items_right"] += sum(1 for x in items if not [k for k in (x.get("bad") or []) if k not in ("batch", "expiry")])
    except (sqlite3.Error, ValueError):
        pass
    out["misses"] = dict(supplier=out["n"] - out["supplier"], billno=out["n"] - out["billno"], date=out["n"] - out["date"], total=out["n"] - out["total"])
    return out


def sarvam_text(month, s):
    m = s["misses"]
    return ("%s: %d linked bill%s · read right in full %d · supplier misread %d · bill no. misread %d · date misread %d · total misread %d · "
            "item lines %d of %d read right (batch and expiry are not judged from a scan)"
            % (month_name(month), s["n"], "" if s["n"] == 1 else "s", s["agreed"], m["supplier"], m["billno"], m["date"], m["total"],
               s["items_right"], s["items_read"]))


# ------------------------------------------------------------------ the page (English; phone width, no sideways scroll)
CSS = """
#s454reg .hd{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0}
#s454reg .chipn{border:1px solid #d6d2cc;border-radius:16px;padding:3px 10px;font-size:14px;background:#fff}
#s454reg .bl{border-top:1px solid #eee;padding:8px 0;display:flex;flex-direction:column;gap:2px}
#s454reg .bl .a{font-weight:600}
#s454reg .bl .b{font-size:14px;color:#555}
#s454reg .st{font-weight:700}
#s454reg .st.verified,#s454reg .st.has_scan,#s454reg .st.accepted{color:#1f4d25}
#s454reg .st.amount_differs,#s454reg .st.double{color:#8a5300}
#s454reg .st.no_scan{color:#8c1d18}
#s454reg .st.second_look,#s454reg .st.unread_pair{color:#8c1d18}
#s454reg table{width:100%;border-collapse:collapse;font-size:14px}#s454reg td{border-top:1px solid #eee;padding:5px 4px;vertical-align:top}
#s454reg .park{background:#f3f0ea;border-left:5px solid #8a7a5c;padding:8px 12px}
#s454reg select{min-height:36px}
"""


def page_body(con, month, prefix, owner, months):
    r = register(con, month)
    c, sc = r["counts"], r["scan_counts"]
    parked = r["cls"] != "counted"
    h = ['<div id="s454reg"><style>%s</style>' % CSS]
    h.append('<h1>Purchase bills: %s</h1>' % esc(month_name(month)))
    h.append('<div class="muted">Every bill Amir entered in Marg, with its paper. A bill is <b>Verified</b> when its scan\'s bill number and total agree '
             'with Marg, and its supplier or its date.</div>')
    if parked:
        h.append('<div class="park">%s is parked: nothing here raises an alert and nobody is asked. The count starts with %s.</div>'
                 % (esc(MONTHS[int(month[5:7]) - 1]), esc(month_name(setting(con, "purchase.register_from", "2026-10-01")[:7]).split(" ")[0])))
    opts = "".join('<option value="%s"%s>%s</option>' % (m, " selected" if m == month else "", esc(month_name(m))) for m in months)
    h.append('<div style="margin:6px 0">Month <select onchange="location.href=\'%s/page/scans?month=\'+this.value">%s</select></div>' % (prefix, opts))
    chips = [("%d bills in Marg" % r["total"])] + ["%d %s" % (c[k], STATE_EN[k].lower()) for k in STATES if c[k]]
    h.append('<div class="hd" id="s454heads">%s</div>' % "".join('<span class="chipn">%s</span>' % esc(x) for x in chips))
    if r["done_date"]:
        h.append('<div id="s454settled"><b>%d of %d ✓</b> %s</div>' % (r["total"], r["total"], esc(ddmon(r["done_date"]))))
    else:
        h.append('<div id="s454settled"><b>%d of %d settled</b> (%d verified, %d %s their scan%s). %d bill%s to go, and %d scan%s %s no Marg bill.</div>'
                 % (r["settled"], r["total"], c["verified"], c["has_scan"], "has" if c["has_scan"] == 1 else "have",
                    (", %d accepted without paper" % c["accepted"]) if c["accepted"] else "", r["total"] - r["settled"],
                    "" if r["total"] - r["settled"] == 1 else "s", r["open_scans"], "" if r["open_scans"] == 1 else "s",
                    "has" if r["open_scans"] == 1 else "have"))
    n, had, notap = readiness(con)
    h.append('<div class="card" id="s454ready"><h2 style="margin:0;font-size:16px">Is the new flow ready? The last 7 days</h2>'
             '<div>Last 7 days: %d bill%s entered in Marg · %d had their scan before the entry · %d paired with no tap.</div>'
             '<div class="muted">When these stay high, Amir\'s soft start can move to its next stage (purchase.entry_mode).</div></div>'
             % (n, "" if n == 1 else "s", had, notap))
    order = {"no_scan": 0, "unread_pair": 0, "amount_differs": 1, "second_look": 1, "double": 2, "has_scan": 3, "accepted": 4, "verified": 5}
    rows = sorted(r["rows"], key=lambda x: (order.get(x["state"], 9), x["date"], x["id"]))
    items = []
    for x in rows:
        tap = ""
        if owner and not parked and x["state"] in ("no_scan", "accepted") and (x.get("missing") or x["state"] == "accepted"):
            tap = (' <button class="sm" onclick="s454np(%d,%d)">%s</button>' % (x["id"], 0 if x["state"] == "accepted" else 1,
                                                                             "Undo" if x["state"] == "accepted" else "Accept without paper"))
        items.append('<div class="bl" data-bill="%d" data-state="%s"><div class="a">%s · %s · %s · %s</div><div><span class="st %s">%s</span>%s%s</div>'
                     '<div class="b">%s%s</div></div>'
                     % (x["id"], x["state"], esc(ddmon(x["date"])), esc(x["supplier"]), esc(x["bill_no"]), esc(rs(x["amount_p"])), x["state"],
                        esc(STATE_EN[x["state"]]), (" · scan " + esc(x["stamp"])) if x["stamp"] else "", tap, esc(x["note"]),
                        (" <i>Whose line now: %s</i>" % esc(x["whose"])) if x["whose"] else ""))
    first, rest = items[:12], items[12:]
    h.append('<div class="card" id="s454bills"><h2 style="margin:0;font-size:16px">The bills, open ones first</h2>%s%s</div>'
             % ("".join(first), ('<details><summary>Show all %d</summary>%s</details>' % (len(items), "".join(rest))) if rest else ""))
    srows = "".join('<tr><td>%s</td><td>%d</td><td>%s</td></tr>' % (esc(SCAN_EN[k]), sc[k], esc(SCAN_WHOSE[k])) for k in SCAN_STATES)
    detail = "".join('<div class="bl"><div class="a">%s · %s</div><div class="b">%s · %s · %s</div></div>'
                     % (esc(x["stamp"]), esc(SCAN_EN[x["state"]]), esc(x["vendor"] or "no supplier read"), esc(x["bill_no"] or "no number"),
                        esc(rs(x["amount_p"]) if x["amount_p"] else "no amount")) for x in r["scans"])
    h.append('<div class="card" id="s454scans"><h2 style="margin:0;font-size:16px">Scans with no Marg bill: %d</h2><table><tr><td><b>What it is</b></td>'
             '<td><b>Scans</b></td><td><b>Whose line now</b></td></tr>%s</table>%s</div>'
             % (len(r["scans"]), srows, ('<details><summary>each scan</summary>%s</details>' % detail) if detail else ""))
    s = sarvam(con, month)
    h.append('<div class="card" id="s454sarvam"><h2 style="margin:0;font-size:16px">How well the scan reads, against Marg</h2>'
             '<div>On the %d linked bills: supplier %d · bill number %d · date %d · total %d. Item lines: %d of %d read right. Items are not judged from the scan.</div>'
             '<div><a href="%s/page/sarvam?month=%s">the Sarvam page</a></div></div>'
             % (s["n"], s["supplier"], s["billno"], s["date"], s["total"], s["items_right"], s["items_read"], prefix, month))
    if owner and not parked:
        h.append("""<script>function s454np(b,a){fetch('%s/api/s454/nopaper',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bill:b,accept:a})})
.then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error);return;}location.reload();});}</script>""" % prefix)
    h.append('<div class="muted" style="margin-top:8px"><a href="%s/page/scans?legacy=1&amp;month=%s">the old Scan links tables</a></div></div>' % (prefix, month))
    return "".join(h)


def months_with_bills(con, n=6):
    pa = _pa()
    try:
        ms = [r[0] for r in con.execute("SELECT DISTINCT COALESCE(b.month, substr(b.bill_date,1,7)) m FROM purchase_bill b WHERE " + pa.EFF_BILL +
                                        " ORDER BY m DESC LIMIT ?", (n,))]
    except sqlite3.Error:
        ms = []
    return [m for m in ms if m]


# ------------------------------------------------------------------ S726 (D840): the owner's step view -- read only, English, phone-first
CHECK_CSS = """
#s726chk{max-width:560px;margin:0 auto;font-size:17px;line-height:1.35;overflow-wrap:anywhere;word-break:break-word}
#s726chk h1{font-size:21px;margin:4px 0 10px}
#s726chk .strip{border-radius:10px;padding:10px 12px;font-weight:700;margin:0 0 10px}
#s726chk .strip.hold{background:#fff4e0;border:1px solid #e0b060;color:#7a4a00}
#s726chk .strip.clear{background:#e8f4ea;border:1px solid #8cc39a;color:#1f4d25}
#s726chk details{border-top:1px solid #e6e2dc}
#s726chk details.last{border-bottom:1px solid #e6e2dc}
#s726chk summary{display:flex;justify-content:space-between;align-items:center;gap:10px;min-height:48px;cursor:pointer;list-style:none}
#s726chk summary::-webkit-details-marker{display:none}
#s726chk summary .l{min-width:0}
#s726chk summary .n{font-weight:800;white-space:nowrap}
#s726chk .grey summary{color:#9a958e}
#s726chk ul{margin:0 0 10px 18px;padding:0;font-size:15px}
#s726chk li{margin:4px 0}
#s726chk .mut{color:#666;font-size:14px}
#s726chk .msel{margin:12px 0}
#s726chk select{min-height:40px;font-size:16px;max-width:100%}
"""


def check_month(con, months):
    """(month, its register or None): the oldest counted month (2026-10 on) not fully settled; else the newest counted month."""
    v = setting(con, "purchase.register_from", "2026-10-01")
    first = max(v[:7] if re.match(r"^\d{4}-\d\d", v) else "2026-10", "2026-10")
    counted = sorted(m for m in months if re.match(r"^\d{4}-\d\d$", m) and m >= first and month_class(con, m) == "counted")
    for m in counted:
        r = register(con, m)
        if r["settled"] < r["total"] or r["open_scans"]:
            return m, r
    if counted:
        return counted[-1], None
    return (months[0] if months else today().strftime("%Y-%m")), None


def _ck_line(x, tail):
    return "%s %s%s" % (esc(x["supplier"]), esc(x["bill_no"]), tail)


def check_rows(r, cx):
    """The seven rows of the step view as [(label, count text, [list lines as HTML], grey)] -- read only; the register's own states."""
    month_ids = {x["id"] for x in r["rows"]}
    rows = [x for x in r["rows"] if not str(x.get("whose") or "").startswith("Nobody (")]     # a parked month's new states ask nobody
    paired = [x for x in r["rows"] if x.get("scan") is not None]
    unpaired = [x for x in r["rows"] if x.get("scan") is None and x["state"] != "double"]
    l1 = [_ck_line(x, " · %s · %s" % (esc(rs(x["amount_p"])), esc(STATE_EN[x["state"]].lower()))) for x in unpaired]
    rec = []
    for x in rows:
        if x["state"] == "no_scan" and not x.get("missing"):
            rec.append(_ck_line(x, " · %s · %s" % (esc(rs(x["amount_p"])), "a question" if x.get("whose") == "Reception: a question" else "to scan")))
        elif x["state"] == "unread_pair":
            rec.append(_ck_line(x, " · scan %s · paired, nothing read: rescan" % esc(x["stamp"])))
    hinted = {sid for sid, bid in cx.likely.items() if bid in month_ids}
    for s in r["scans"]:
        if s["state"] in ("probably", "vendor", "to_name", "unread") and not (s["state"] == "probably" and s["id"] in hinted):
            rec.append("Scan %s · %s" % (esc(s["stamp"]), esc(SCAN_EN[s["state"]])))
    amir = []
    for x in rows:
        if x["state"] == "amount_differs":
            ag = x.get("agree") or {}
            d = ag.get("diff") or 0
            amir.append(_ck_line(x, " %s%s" % (esc(rs2(abs(d))), ' <span class="mut">· the %s reads %s · %s</span>'
                                               % ("paper" if ag.get("paper") else "scan", "more" if d > 0 else "less", esc(x.get("whose") or "")))))
        elif x["state"] == "double":
            amir.append(_ck_line(x, ' <span class="mut">· entered twice in Marg</span>'))
    rnd = []
    for x in rows:
        a = x.get("agree") or {}
        if x["state"] in ("verified", "has_scan") and a.get("diff") and abs(int(a["diff"])) <= 100:
            rnd.append(_ck_line(x, " · paper %s · %s" % (esc(rs2(a.get("scan_p"))), esc(rs2(abs(int(a["diff"])))))))
    you = []
    for x in rows:
        if x["state"] == "second_look":
            you.append(_ck_line(x, ' · second look <span class="mut">· %s</span>' % esc(x.get("note") or "")))
        elif x["state"] == "no_scan" and x.get("missing"):
            you.append(_ck_line(x, " · %s · paper not found" % esc(rs(x["amount_p"]))))
    return [("Scans paired", "%d / %d" % (len(paired), r["total"]), l1 or ["Every bill has its scan."], False),
            ("With reception", str(len(rec)), rec, False),
            ("Differences → Amir", str(len(amir)), amir, False),
            ("Rounding (supplier's figure paid)", str(len(rnd)), rnd, False),
            ("You & Shavez", str(len(you)), you, False),
            ("Supplier summaries", "later", ["Comes after rows 1–5."], True),
            ("Lock & NEFT", "after 1–6", ["Opens when rows 1–6 are clear."], True)]


def check_body(con, month, prefix, months, r=None):
    """S726 (D840): the owner's step view of one month -- a header, the NEFT strip, seven one-line rows (each opens its list), a month
    select. Reads only: register() and the scan state the last pass left."""
    r = r if r is not None else register(con, month)
    cx = Ctx(con)
    total_p = sum(int(x["amount_p"] or 0) for x in r["rows"])
    open_n = (r["total"] - r["settled"]) + r["open_scans"]
    try:
        mname = MONTHS[int(month[5:7]) - 1]
    except (ValueError, IndexError):
        mname = month
    h = ['<div id="s726chk"><style>%s</style>' % CHECK_CSS]
    h.append('<h1 id="s726head">%s · %d bill%s · %s</h1>' % (esc(mname), r["total"], "" if r["total"] == 1 else "s", esc(rs(total_p))))
    if r["cls"] != "counted":
        quiet = [x for x in r["rows"] if str(x.get("whose") or "").startswith("Nobody (")]
        h.append('<div class="mut" id="s726parked" style="margin:-6px 0 8px">%s is parked: shown for reading only; nobody is asked.%s</div>'
                 % (esc(month_name(month)), (" %d bill%s under the new rules (%s) wait with nobody." % (len(quiet), "" if len(quiet) == 1 else "s",
                    esc(", ".join("%s %s · %s" % (x["supplier"], x["bill_no"], STATE_EN[x["state"]]) for x in quiet[:6])))) if quiet else ""))
    if open_n:
        h.append('<div class="strip hold" id="s726strip">NEFT on hold · %d open</div>' % open_n)
    else:
        h.append('<div class="strip clear" id="s726strip">All clear ✓</div>')
    rows = check_rows(r, cx)
    for i, (lab, n, lines, grey) in enumerate(rows, 1):
        h.append('<details class="%s%s" data-row="%d"><summary><span class="l"><b>%d</b> %s</span><span class="n">%s</span></summary>'
                 '<ul>%s</ul></details>' % ("grey" if grey else "row", " last" if i == len(rows) else "", i, i, esc(lab), esc(n),
                                           "".join("<li>%s</li>" % x for x in lines) or "<li>Nothing here.</li>"))
    opts = "".join('<option value="%s"%s>%s</option>' % (esc(m), " selected" if m == month else "", esc(month_name(m))) for m in months)
    h.append('<div class="msel">Month <select id="s726month" onchange="location.href=\'%s/page/check?month=\'+this.value">%s</select></div>'
             % (esc(prefix), opts))
    h.append('<div class="mut">Read only. The full list is on <a href="%s/page/scans?month=%s">the month\'s register</a>.</div></div>'
             % (esc(prefix), esc(month)))
    return "".join(h)


def accept_nopaper(con, who, bill_id, accept):
    """The owner's tap on a "paper not found" row of a counted month: accepted without paper, or undone. (ok, message)."""
    r = con.execute("SELECT b.month, b.bill_date FROM purchase_bill b WHERE b.id=?", (int(bill_id),)).fetchone()
    if not r:
        return False, "no such bill"
    ym = r[0] or str(r[1] or "")[:7]
    if month_class(con, ym) != "counted":
        return False, "A parked month has no accept tap."
    m = con.execute("SELECT accepted_at FROM s454_paper_missing WHERE bill_id=?", (int(bill_id),)).fetchone()
    if not m:
        return False, "Reception has not said this paper is missing."
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    if accept:
        con.execute("UPDATE s454_paper_missing SET accepted_by=?, accepted_at=? WHERE bill_id=?", (who, now, int(bill_id)))
    else:
        con.execute("UPDATE s454_paper_missing SET accepted_by=NULL, accepted_at=NULL WHERE bill_id=?", (int(bill_id),))
    try:
        _pa()._audit(con, who, "s454_paper_accepted" if accept else "s454_paper_accept_undone", int(bill_id), dict(kit="S454 P2"))
    except Exception:                                         # noqa: BLE001
        pass
    con.commit()
    return True, "Accepted without paper." if accept else "Undone."


# ------------------------------------------------------------------ what reaches a person (S454 7.3) -- counted months only
def scan_wait(con):
    """(n, oldest days) of the counted lines of "Bill scan karna hai" (the reception screen's own list)."""
    try:
        import porders_s454                                   # noqa: PLC0415
        lines = porders_s454.scan_lines(con)
    except Exception:                                         # noqa: BLE001
        return 0, 0
    t = today()
    ages = [(t - _date(x.get("date"))).days for x in lines if _date(x.get("date"))]
    return len(lines), (max(ages) if ages else 0)


def owner_lines(con):
    out = []
    try:
        n, age = scan_wait(con)
        if n and age > int_setting(con, "purchase.scan_wait_days", 3):
            out.append(dict(cls="warn", target="porders", text="Bill scan waiting: %d · the oldest %d days (reception's Bill scan karna hai)" % (n, age)))
        pm = [r for r in con.execute("SELECT m.bill_id, b.month, b.bill_date, b.supplier, b.bill_no FROM s454_paper_missing m JOIN purchase_bill b "
                                     "ON b.id=m.bill_id WHERE m.accepted_at IS NULL")
              if month_class(con, r[1] or str(r[2] or "")[:7]) == "counted"
              and not con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=?", (r[0],)).fetchone()]
        if pm:
            out.append(dict(cls="info", target="scans", text="Paper not found by reception: %d bill%s -- your tap accepts it on the register (%s)"
                            % (len(pm), "" if len(pm) == 1 else "s", ", ".join("%s %s" % (_pa().supplier_key(r[3]), r[4]) for r in pm[:4]))))
        wait = int_setting(con, "purchase.entry_wait_days", 7)
        try:
            lst = _pa().scans_for_amir(con).get("list") or []
        except Exception:                                     # noqa: BLE001
            lst = []
        t = today()
        old = [x for x in lst if _date(x.get("scan_day")) and (t - _date(x["scan_day"])).days > wait and month_class(con, str(x["scan_day"])[:7]) == "counted"]
        if old:
            out.append(dict(cls="info", target="scans", text="Scanned and not yet in Marg for more than %d days: %d bill%s (oldest %s) -- for your eyes only"
                            % (wait, len(old), "" if len(old) == 1 else "s", ddmon(min(x["scan_day"] for x in old)))))
    except Exception:                                         # noqa: BLE001 -- Needs you never waits on this
        pass
    return out


def shavez_line(con):
    """Shavez's morning page: one line while a counted line of "Bill scan karna hai" waits -- dict(n, age, url) or None."""
    n, age = scan_wait(con)
    if not n:
        return None
    return dict(n=n, age=age, url="/finance/porders/s454/scan", text="Bill scan baaki: %d · sabse purana %d din" % (n, age))



# ---- S736 (06-Nov-2026, Sanjeevni session 396, kit S736_RECEPTION_BILL_LIST; D840, D847, F-1142, F-1143, F-1154) ---------------------------
#  THE OWNER'S DECISIONS ON THE STEP VIEW (owner-only, POST /finance/purchase/api/s736/decide -> s736_decide below), kept in
#  finance.db s736_decision (one row per scan; Undo deletes it; every tap audited):
#    paper         Second look: the paper's figure stands -- written as reception's own "= the scan -> Marg galat" answer is
#                  (purchase_scan_state.paper_amount = the scan's own reading, amount_state 'marg_wrong'; the old two kept on the decision
#                  row for Undo) AND the bill marked WRONG at the paper's figure (purchase_bill.verdict/wrong_amount_p/reason -- S440's own
#                  "Marg galat" branch, so the month page, the supplier payment group and _resolve_wrong see it); refused when the bill already
#                  carries a verdict or its month is finalised. The pair becomes Amount differs, "Amir: a Marg correction".
#    scan_misread  Second look: the scan misread -- the amount given for the paper stands; the pair is judged on it (settled when it agrees).
#    accept        A scan reception rescanned twice and still in trouble (porders_s454.s736_plan's escalated): the scan stands as it is --
#                  a "Paired, nothing read" pair is then judged as an ordinary pair, and the server never asks for it again.
#  A decision holds only while the scan's own reading (raw_p) -- and, for the two second-look decisions, the amount given (paper_p) -- are
#  what they were at the tap; a changed reading puts the pair back to its state.
#  THE STEP VIEW: row 2 also lists the rescans the server or a person asked for (with the try); row 3 is "Differences" (F-1154: each line
#  names whose it is -- Amir, reception or you); row 5 carries the Second look buttons, the scans after two tries (Open paper · Accept)
#  and the decisions taken (Undo). The NEFT strip counts those scans too. Everything else of the register is unchanged.
KIT_S736 = "S736_RECEPTION_BILL_LIST"
S736_DDL = ("CREATE TABLE IF NOT EXISTS s736_decision (asset_bill_id INTEGER PRIMARY KEY, decision TEXT NOT NULL, bill_id INTEGER, raw_p INTEGER, "
            "paper_p INTEGER, by TEXT, at TEXT, old_paper_p INTEGER, old_amount_state TEXT, old_confirmed_by TEXT, old_confirmed_at TEXT, bill_marked INTEGER)")
S736_DECISIONS = ("paper", "scan_misread", "accept")
S736_REASON_EN = {"unread": "nothing read", "blurred": "blurred", "cut": "cut off", "no_total": "no total", "not_adding": "lines do not add up",
                  "not_bill": "not a bill"}


def _s736_load(con):
    try:
        return {int(r[0]): dict(decision=r[1], raw_p=r[2], paper_p=r[3], bill_id=r[4], by=r[5], at=r[6], old_paper_p=r[7], old_amount_state=r[8]) for r in
                con.execute("SELECT asset_bill_id, decision, raw_p, paper_p, bill_id, by, at, old_paper_p, old_amount_state FROM s736_decision")}
    except sqlite3.Error:
        return {}


_Ctx_before_s736 = Ctx


class Ctx(_Ctx_before_s736):                                  # noqa: F811 -- S736: + the owner's decisions
    def __init__(self, con):
        _Ctx_before_s736.__init__(self, con)
        self.s736 = _s736_load(con)


def _s736_n(v):
    return None if v is None else int(v)


def _s736_dec(cx, s, kinds):
    """The owner's decision on this scan when it is one of `kinds` and still holds (the scan's reading, and the amount given, unchanged)."""
    sid = s.get("id") if s else None
    if sid is None:
        return None
    d = (getattr(cx, "s736", None) or {}).get(int(sid))
    if not d or d.get("decision") not in kinds:
        return None
    raw = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
    if _s736_n(d.get("raw_p")) != _s736_n(raw):
        return None
    if d["decision"] == "scan_misread" and _s736_n(d.get("paper_p")) != _s736_n(cx.paper.get(int(sid))):
        return None
    if d["decision"] == "paper" and _s736_n(raw) != _s736_n(cx.paper.get(int(sid))):
        return None
    return d["decision"]


_s726_state_before_s736 = s726_state


def s726_state(cx, s, a, present=True):                       # noqa: F811
    """S736: an accepted scan is never 'Paired, nothing read'; a second look the owner decided is judged as an ordinary pair."""
    st = _s726_state_before_s736(cx, s, a, present)
    if st == "unread_pair" and _s736_dec(cx, s, ("accept",)):
        return pair_state(a)
    if st == "second_look" and _s736_dec(cx, s, ("scan_misread",)):
        return pair_state(a)
    return st


_note_before_s736 = _note


def _note(cx, st, a, b, s, l):                                # noqa: F811
    """S736: the owner's decision named in the note; 'the paper's figure stands' is Amir's correction."""
    n, w = _note_before_s736(cx, st, a, b, s, l)
    if _s736_dec(cx, s, ("paper",)):
        n = "Your second look: the paper's figure stands (the scan's own reading). " + n
    elif _s736_dec(cx, s, ("scan_misread",)):
        n = ("Your second look: the scan misread; the amount given (%s) stands. " % rs2(cx.paper.get(int(s["id"])))) + n
    elif _s736_dec(cx, s, ("accept",)):
        n = "You accepted this scan as it is. " + n
    return n, w


def _s736_p4():
    import porders_s454                                       # noqa: PLC0415 -- beside this file
    return porders_s454


def _s736_view(con):
    try:
        return _s736_p4().s736_view(con)
    except Exception:                                         # noqa: BLE001 -- the step view never waits on it
        return None


def s736_decide(con, who, b):
    """The owner's tap on the step view (the header above) -> (ok, message). Audited; commits."""
    try:
        sid = int((b or {}).get("scan") or 0)
    except (TypeError, ValueError):
        sid = 0
    d = str((b or {}).get("decision") or "")
    if not sid:
        return False, "No scan named."
    con.execute(S736_DDL)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    if d == "undo":
        row = con.execute("SELECT decision, raw_p, old_paper_p, old_amount_state, old_confirmed_by, old_confirmed_at, bill_marked, bill_id, by "
                          "FROM s736_decision WHERE asset_bill_id=?", (sid,)).fetchone()
        if not row:
            return False, "Nothing to undo."
        msg = "Undone."
        if row[0] == "paper":                                 # put reception's own answer back -- only if nobody has changed it since
            cur_ = con.execute("SELECT paper_amount, amount_state FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone()
            if cur_ and _s736_n(cur_[0]) == _s736_n(row[1]) and str(cur_[1] or "") == "marg_wrong":
                con.execute("UPDATE purchase_scan_state SET paper_amount=?, amount_state=?, confirmed_by=?, confirmed_at=? WHERE asset_bill_id=?",
                            (row[2], row[3], row[4], row[5], sid))
            else:
                msg = "The paper amount was answered again after your tap -- that answer stands; your decision is removed."
            if row[6] and row[7]:                             # the WRONG mark this tap made, only while it is still that mark
                con.execute("UPDATE purchase_bill SET verdict=NULL, verdict_by=NULL, verdict_at=NULL, wrong_amount_p=NULL, reason=NULL "
                            "WHERE id=? AND verdict='WRONG' AND wrong_amount_p=? AND verdict_by=?", (int(row[7]), row[1], row[8]))
        con.execute("DELETE FROM s736_decision WHERE asset_bill_id=?", (sid,))
        _s736_audit(con, who, "s736_decision_undone", sid, dict(kit=KIT_S736))
        con.commit()
        return True, msg
    if d not in S736_DECISIONS:
        return False, "Not a decision."
    if con.execute("SELECT 1 FROM s736_decision WHERE asset_bill_id=?", (sid,)).fetchone():
        return False, "Already decided — undo it first."
    scans = asset_scans(con) or {}
    s = scans.get(sid)
    lk = con.execute("SELECT bill_id FROM purchase_scan_link WHERE asset_bill_id=?", (sid,)).fetchone()
    bill = None
    if lk:
        r = con.execute("SELECT * FROM purchase_bill WHERE id=?", (int(lk[0]),)).fetchone()
        bill = dict(r) if r else None
    if d in ("paper", "scan_misread"):
        if s is None or bill is None:
            return False, "This scan is no longer paired."
        if month_class(con, str(bill.get("month") or str(bill.get("bill_date") or "")[:7])) != "counted":
            return False, "A parked month has no second look."
        cx = Ctx(con)
        st = s726_state(cx, s, agree(cx, s, bill), True)
        if st != "second_look":
            return False, "This pair is no longer a second look."
        raw, paper = s.get("amount_p"), cx.paper.get(sid)
        if raw in (None, 0):
            return False, "The scan read no amount of its own."
        if d == "paper":
            fin = con.execute("SELECT status FROM purchase_month WHERE month=?", (str(bill.get("month") or str(bill.get("bill_date") or "")[:7]),)).fetchone()
            if fin and fin[0] == "final":
                return False, "This month is finalised -- nothing is changed in it."
            if bill.get("verdict"):
                return False, "This bill already carries a verdict (%s) -- change it on the month's register." % bill.get("verdict")
            if not con.execute("SELECT 1 FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone():
                return False, "The amount given is not on the scan's own row -- answer it on the register."
        old = con.execute("SELECT paper_amount, amount_state, confirmed_by, confirmed_at FROM purchase_scan_state WHERE asset_bill_id=?", (sid,)).fetchone()
        old_pp, old_st, old_cb, old_ca = (old[0], old[1], old[2], old[3]) if old else (None, None, None, None)
    else:
        try:
            esc_ids = {int(x["scan"]) for x in _s736_p4().s736_plan(con)["escalated"]}
        except Exception:                                     # noqa: BLE001
            esc_ids = set()
        if sid not in esc_ids:
            return False, "This scan is not waiting for you."
        if s is None:
            try:
                acon = _pa()._assets_con()
                row = acon.execute("SELECT total_amount FROM bills WHERE id=?", (sid,)).fetchone() if acon is not None else None
                if acon is not None:
                    acon.close()
            except Exception:                                 # noqa: BLE001
                row = None
            raw = _amount_p(row[0]) if row else None
        else:
            raw = s.get("amount_p")
        paper = None
        old_pp = old_st = old_cb = old_ca = None
    marked = 1 if d == "paper" else 0
    con.execute("INSERT INTO s736_decision (asset_bill_id, decision, bill_id, raw_p, paper_p, by, at, old_paper_p, old_amount_state, old_confirmed_by, "
                "old_confirmed_at, bill_marked) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (sid, d, (bill or {}).get("id"), raw, paper, who, now, old_pp, old_st, old_cb, old_ca, marked))
    if d == "paper":                                          # S440's own "Marg galat" branch, in the owner's name (porders.api_scan_amount)
        cur = con.execute("UPDATE purchase_scan_state SET paper_amount=?, amount_state='marg_wrong', confirmed_by=?, confirmed_at=? WHERE asset_bill_id=?",
                          (raw, who, now, sid))
        why = "bill %s %s: paper Rs %s, Marg Rs %s (the owner's second look, %s)" % (bill.get("bill_no"), _pa().supplier_key(bill.get("supplier") or ""),
                                                                                 rs2(raw)[1:], rs2(bill.get("amount_p"))[1:], who)
        cur2 = con.execute("UPDATE purchase_bill SET verdict='WRONG', verdict_by=?, verdict_at=?, wrong_amount_p=?, reason=? WHERE id=? AND verdict IS NULL",
                           (who, now, raw, why, bill["id"]))
        if cur.rowcount != 1 or cur2.rowcount != 1:
            con.rollback()
            return False, "Nothing was changed -- the scan's row or the bill changed meanwhile; open the page again."
        _s736_audit(con, who, "verdict", bill["id"], dict(verdict="WRONG", wrong_amount_p=raw, reason=why, before=None, via="S736 second look"))
    _s736_audit(con, who, "s736_decision", sid, dict(decision=d, bill=(bill or {}).get("id"), raw_p=raw, paper_p=paper, kit=KIT_S736))
    con.commit()
    return True, {"paper": "The paper's figure stands — Amir corrects Marg.", "scan_misread": "The scan misread — the amount given stands.",
                  "accept": "Accepted as it is."}[d]


def _s736_audit(con, who, action, ref, detail):
    try:
        _pa()._audit(con, who, action, ref, detail)
    except Exception:                                         # noqa: BLE001 -- the row itself is the record
        pass


def _s736_btn(scan, decision, label, bill=None):
    return ('<button type="button" class="s736b" data-scan="%d" data-d="%s"%s onclick="s736d(this)">%s</button>'
            % (int(scan), esc(decision), (' data-bill="%d"' % int(bill)) if bill else "", esc(label)))


def check_rows(r, cx):                                        # noqa: F811 -- S736: rows 2, 3 and 5 as the header above says
    """The seven rows of the step view as [(label, count text, [list lines as HTML], grey)] -- the register's own states, and (S736) the
    rescans asked, the scans after two tries and the owner's decisions (r['s736'], from porders_s454.s736_view)."""
    v = r.get("s736") or {}
    month = r.get("month") or ""
    asks = [a for a in (v.get("asks") or []) if a.get("month") == month]
    esc_ = [x for x in (v.get("escalated") or []) if x.get("month") == month]
    dec = [x for x in (v.get("decided") or []) if x.get("month") == month]
    ask_by_scan = {int(a["scan"]): a for a in asks}
    esc_ids = {int(x["scan"]) for x in esc_}                  # a scan after two tries is row 5's, not reception's
    month_ids = {x["id"] for x in r["rows"]}
    rows = [x for x in r["rows"] if not str(x.get("whose") or "").startswith("Nobody (")]     # a parked month's new states ask nobody
    paired = [x for x in r["rows"] if x.get("scan") is not None]
    unpaired = [x for x in r["rows"] if x.get("scan") is None and x["state"] != "double"]
    l1 = [_ck_line(x, " · %s · %s" % (esc(rs(x["amount_p"])), esc(STATE_EN[x["state"]].lower()))) for x in unpaired]

    def asked(sid):
        a = ask_by_scan.get(int(sid)) if sid is not None else None
        if not a:
            return ""
        return ' <span class="mut">· rescan asked by %s, try %d</span>' % ("the server" if a["by"] == "server" else esc(a["by"].split(" ")[0].title() or "?"), a["try_n"])
    rec, shown = [], set()
    for x in rows:
        if x["state"] == "no_scan" and not x.get("missing"):
            rec.append(_ck_line(x, " · %s · %s" % (esc(rs(x["amount_p"])), "a question" if x.get("whose") == "Reception: a question" else "to scan")))
        elif x["state"] == "unread_pair" and x.get("scan") not in esc_ids:
            rec.append(_ck_line(x, " · scan %s · paired, nothing read: rescan%s" % (esc(x["stamp"]), asked(x.get("scan")))))
            shown.add(x.get("scan"))
    hinted = {sid for sid, bid in cx.likely.items() if bid in month_ids}
    for s in r["scans"]:
        if s["id"] in esc_ids:
            continue
        if s["state"] in ("probably", "vendor", "to_name", "unread") and not (s["state"] == "probably" and s["id"] in hinted):
            rec.append("Scan %s · %s%s" % (esc(s["stamp"]), esc(SCAN_EN[s["state"]]), asked(s["id"])))
            shown.add(s["id"])
    for a in asks:
        if a["scan"] not in shown:
            rec.append("Scan %s · %s · rescan asked by %s, try %d" % (esc(a["stamp"]), esc(S736_REASON_EN.get(a["reason"], a["reason"])),
                                                                 "the server" if a["by"] == "server" else esc(a["by"].split(" ")[0].title() or "?"), a["try_n"]))
    amir = []
    for x in rows:
        if x["state"] == "amount_differs":
            ag = x.get("agree") or {}
            d = ag.get("diff") or 0
            amir.append(_ck_line(x, " %s%s" % (esc(rs2(abs(d))), ' <span class="mut">· the %s reads %s · %s</span>'
                                               % ("paper" if ag.get("paper") else "scan", "more" if d > 0 else "less", esc(x.get("whose") or "")))))
        elif x["state"] == "double":
            amir.append(_ck_line(x, ' <span class="mut">· entered twice in Marg · Amir: a Marg correction</span>'))
    rnd = []
    for x in rows:
        a = x.get("agree") or {}
        if x["state"] in ("verified", "has_scan") and a.get("diff") and abs(int(a["diff"])) <= 100:
            rnd.append(_ck_line(x, " · paper %s · %s" % (esc(rs2(a.get("scan_p"))), esc(rs2(abs(int(a["diff"])))))))
    you = []
    for x in rows:
        if x["state"] == "second_look":
            btns = ""
            if v.get("ok") and x.get("scan") is not None:
                btns = ('<div class="s736row">%s%s</div>' % (_s736_btn(x["scan"], "paper", "Paper's figure stands — Amir corrects", x["id"]),
                                                             _s736_btn(x["scan"], "scan_misread", "Scan misread — settled", x["id"])))
            you.append(_ck_line(x, ' · second look <span class="mut">· %s</span>%s' % (esc(x.get("note") or ""), btns)))
        elif x["state"] == "no_scan" and x.get("missing"):
            you.append(_ck_line(x, " · %s · paper not found" % esc(rs(x["amount_p"]))))
    for x in esc_:
        head = " ".join(z for z in (x.get("vendor") or "", x.get("bill_no") or "") if z) or "Scan"
        you.append('%s · scan %s · rescanned %d times, still: %s<div class="s736row"><a class="s736b" href="/scanapp/bills/%d/file" target="_blank" '
                   'rel="noopener">Open paper</a>%s</div>' % (esc(head), esc(x["stamp"]), int(x["tries"]), esc(S736_REASON_EN.get(x["reason"], x["reason"])),
                                                             int(x["scan"]), _s736_btn(x["scan"], "accept", "Accept")))
    n_you = len(you)
    if dec:
        you.append('<span class="mut"><b>Decided</b> (undo any):</span>')
    for x in dec:
        word = {"paper": "the paper's figure stands", "scan_misread": "the scan misread", "accept": "accepted as it is"}.get(x["decision"], x["decision"])
        head = " ".join(z for z in (x.get("vendor") or "", x.get("bill_no") or "") if z) or "Scan"
        you.append('<span class="mut">%s · scan %s · %s (%s)</span><div class="s736row">%s</div>' % (esc(head), esc(x["stamp"]), esc(word), esc(ddmon(x.get("at")) or ""),
                                                                               _s736_btn(x["scan"], "undo", "Undo")))
    return [("Scans paired", "%d / %d" % (len(paired), r["total"]), l1 or ["Every bill has its scan."], False),
            ("With reception", str(len(rec)), rec, False),
            ("Differences", str(len(amir)), amir, False),
            ("Rounding (supplier's figure paid)", str(len(rnd)), rnd, False),
            ("You & Shavez", str(n_you), you, False),
            ("Supplier summaries", "later", ["Comes after rows 1–5."], True),
            ("Lock & NEFT", "after 1–6", ["Opens when rows 1–6 are clear."], True)]


S736_CSS = """
#s726chk .s736row{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 2px}
#s726chk .s736b{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border:1px solid #1f3864;border-radius:10px;background:#fff;color:#1f3864;
 font:600 14px system-ui,sans-serif;text-decoration:none;cursor:pointer}
#s726chk .s736b[disabled]{opacity:.5;cursor:default}
#s726chk #s736msg{display:none;border-radius:10px;padding:10px 12px;margin:0 0 10px;font-weight:700}
"""
S736_JS = """
<script>function s736d(b){var m=document.getElementById('s736msg');b.disabled=true;
fetch(%s,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scan:parseInt(b.getAttribute('data-scan')),decision:b.getAttribute('data-d')})})
.then(function(r){return r.json().catch(function(){return {};}).then(function(j){return [r,j];});}).then(function(x){
if(x[0].ok&&x[1].ok){location.reload();return;}b.disabled=false;if(m){m.style.display='block';m.style.background='#fbe7e5';m.style.color='#8c1d18';m.textContent=x[1].message||('HTTP '+x[0].status);}})
.catch(function(e){b.disabled=false;if(m){m.style.display='block';m.textContent=String(e);}});}</script>
"""


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S736: + the asks, the scans after two tries, the decisions
    """S726 (D840): the owner's step view of one month -- a header, the NEFT strip, seven one-line rows (each opens its list), a month
    select. Reads only (the buttons of row 5 post to /api/s736/decide; nothing is written by this GET)."""
    r = r if r is not None else register(con, month)
    v = _s736_view(con)
    r = dict(r, s736=v or {})
    cx = Ctx(con)
    total_p = sum(int(x["amount_p"] or 0) for x in r["rows"])
    open_n = (r["total"] - r["settled"]) + r["open_scans"]
    if v and r["cls"] == "counted":                           # S736: a rescan asked, or a scan after two tries, holds the month too
        unsettled = {x.get("scan") for x in r["rows"] if x["state"] not in ("verified", "has_scan", "accepted")} | {s["id"] for s in r["scans"]}
        extra = {int(a["scan"]) for a in (v.get("asks") or []) if a.get("month") == month} | {int(x["scan"]) for x in (v.get("escalated") or [])
                                                                                               if x.get("month") == month}
        open_n += len(extra - unsettled)
    try:
        mname = MONTHS[int(month[5:7]) - 1]
    except (ValueError, IndexError):
        mname = month
    h = ['<div id="s726chk"><style>%s%s</style>' % (CHECK_CSS, S736_CSS)]
    h.append('<h1 id="s726head">%s · %d bill%s · %s</h1>' % (esc(mname), r["total"], "" if r["total"] == 1 else "s", esc(rs(total_p))))
    h.append('<div id="s736msg"></div>')
    if r["cls"] != "counted":
        quiet = [x for x in r["rows"] if str(x.get("whose") or "").startswith("Nobody (")]
        h.append('<div class="mut" id="s726parked" style="margin:-6px 0 8px">%s is parked: shown for reading only; nobody is asked.%s</div>'
                 % (esc(month_name(month)), (" %d bill%s under the new rules (%s) wait with nobody." % (len(quiet), "" if len(quiet) == 1 else "s",
                    esc(", ".join("%s %s · %s" % (x["supplier"], x["bill_no"], STATE_EN[x["state"]]) for x in quiet[:6])))) if quiet else ""))
    if open_n:
        h.append('<div class="strip hold" id="s726strip">NEFT on hold · %d open</div>' % open_n)
    else:
        h.append('<div class="strip clear" id="s726strip">All clear ✓</div>')
    rows = check_rows(r, cx)
    for i, (lab, n, lines, grey) in enumerate(rows, 1):
        h.append('<details class="%s%s" data-row="%d"><summary><span class="l"><b>%d</b> %s</span><span class="n">%s</span></summary>'
                 '<ul>%s</ul></details>' % ("grey" if grey else "row", " last" if i == len(rows) else "", i, i, esc(lab), esc(n),
                                           "".join("<li>%s</li>" % x for x in lines) or "<li>Nothing here.</li>"))
    opts = "".join('<option value="%s"%s>%s</option>' % (esc(m), " selected" if m == month else "", esc(month_name(m))) for m in months)
    h.append('<div class="msel">Month <select id="s726month" onchange="location.href=\'%s/page/check?month=\'+this.value">%s</select></div>'
             % (esc(prefix), opts))
    h.append('<div class="mut">Read only, but for the buttons in row 5. Reception\'s own list: <a href="/finance/porders/s454/billkaam">Aaj ka bill kaam</a> · '
             'the full list is on <a href="%s/page/scans?month=%s">the month\'s register</a>.</div></div>' % (esc(prefix), esc(month)))
    h.append(S736_JS % json.dumps(prefix + "/api/s736/decide"))
    return "".join(h)
# ---- S736 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S738 (06-Nov-2026, Sanjeevni session 396, kit S738_AMIR_CORRECTIONS; D839, D840; the owner's OK 21:28 IST on the mock
#      https://claude.ai/artifact/8wUuc5o8bNUp19xWRFdtXs) ----------------------------------------------------------------------------------
#  AMIR'S CORRECTIONS. s738_fixes(con): every bill of a COUNTED month whose register line is "Amir: a Marg correction" -- one item each,
#  worded by kind:
#    less    the paper reads LESS than Marg: "Marg mein bill <paper> kijiye".
#    more    the paper reads MORE than Marg: the scan's item lines Marg's entry of that bill does not carry (matched by quantity + rate, a
#            learnt name or an akin name) -- listed ONLY when they add up to the difference (within max(Rs 2, 1%)); either way the do line
#            names both roads (a return written on the bill: the full bill + a purchase return; else the missing lines), as the plan's
#            section 3 gives Amir the paper beside him.
#    double  the bill entered twice in Marg: "Marg mein ek entry hataiye".
#  Proof is ONLY his own export: a line leaves when the register no longer puts it on Amir (Marg = the paper). s738_sync(con, fixes) keeps
#  s738_fix (bill_id, kind, first_seen, last_seen, settled_at, settled_export, gone_at): first seen, still seen, settled (with the newest
#  bill-wise export's arrival) or gone (no longer a counted line for another reason). Called from Amir's own page (amir_day.settle -- that
#  file's only write on a read); the owner's step view only READS it.
#  THE OWNER'S STEP VIEW (PC first, his changes 21:23-21:27): each line of rows 1-5 that has a scan carries the bill date, the scan's stamp
#  and a FOLDED "Show scan" -- opened, the scan itself (a lazy iframe / image from /finance/purchase/api/s738/scan/<id>) beside what the
#  scan read against Marg (supplier, bill no., date, total) and the paper amount given; row 3 says for each line whose it is and since when,
#  and lists a correction Amir's export proved with its date (not counted). A back-to-top button. On a wide screen each line is a row of
#  columns; on a phone it stays one card per line.
KIT_S738 = "S738_AMIR_CORRECTIONS"
S738_DDL = ("CREATE TABLE IF NOT EXISTS s738_fix (bill_id INTEGER PRIMARY KEY, kind TEXT, month TEXT, first_seen TEXT NOT NULL, last_seen TEXT, "
            "settled_at TEXT, settled_export TEXT, gone_at TEXT, marg_p INTEGER)")
S738_NOT_ITEM = re.compile(r"\b(FREIGHT|CARTAGE|ROUND|ROUNDING|DISCOUNT|DISC|GST|CGST|SGST|IGST|TAX|TOTAL|ADJ|ADJUST|LESS|CESS|CHARGES?|POSTAGE)\b", re.I)


def _s738_counted_months(con):
    v = setting(con, "purchase.register_from", "2026-10-01")
    first = max(v[:7] if re.match(r"^\d{4}-\d\d", v) else "2026-10", "2026-10")
    try:
        final = {str(r[0]) for r in con.execute("SELECT month FROM purchase_month WHERE status='final'")}
    except sqlite3.Error:
        final = set()
    ms = [m for m in months_with_bills(con, 24) if m >= first and month_class(con, m) == "counted" and m not in final]
    return sorted(ms)


def _s738_scan_items(sid):
    """The scan's own item lines (claude_reading, the good reading) -- assets.db READ ONLY. [] when none."""
    acon = _pa()._assets_con()
    if acon is None:
        return []
    try:
        r = acon.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1 ORDER BY rowid DESC LIMIT 1", (int(sid),)).fetchone()
    except sqlite3.Error:
        r = None
    finally:
        acon.close()
    try:
        data = json.loads(r[0]) if r and r[0] else {}
    except ValueError:
        data = {}
    return [i for i in (data.get("items") or []) if isinstance(i, dict)]


def _s738_missing(con, bill, sid, diff_p):
    """The scan's lines Marg's entry of this bill does not carry -- only when they add up to the paper's extra (diff_p > 0)."""
    try:
        import item_check as IC                               # noqa: PLC0415 -- beside this file, read only
    except Exception:                                         # noqa: BLE001
        return []
    items = _s738_scan_items(sid)
    if not items:
        return []
    try:
        ml = IC.marg_lines(con, bill)
    except Exception:                                         # noqa: BLE001
        return []
    paired = {id(a) for a, _b in IC.pairs_of(items, ml)} if ml else set()
    learnt = {}
    try:
        for r in con.execute("SELECT scan_norm, marg_item FROM s454_item_name WHERE supplier_norm=?", (bill.get("supplier_norm"),)):
            learnt[str(r[0])] = str(r[1])
    except sqlite3.Error:
        pass
    marg_names = [str(l.get("item") or "") for l in ml]
    paired_m = {id(b) for _a, b in IC.pairs_of(items, ml)} if ml else set()
    for l in ml:                                              # every Marg line must be accounted for on the paper (paired or akin)
        if id(l) not in paired_m and not any(IC.names_akin(str(l.get("item") or ""), str(it.get("name") or it.get("item") or "")) for it in items):
            return []
    psum = sum(int(_amount_p(it.get("amount")) or 0) for it in items)
    paper = int(bill.get("amount_p") or 0) + int(diff_p)
    if abs(psum - paper) > max(200, abs(paper) // 100):        # the paper's own lines must add up to the paper's total
        return []
    out = []
    for it in items:
        if id(it) in paired:
            continue
        nm = str(it.get("name") or it.get("item") or "")
        if IC.name_norm(nm) in learnt and any(IC.name_norm(learnt[IC.name_norm(nm)]) == IC.name_norm(m) for m in marg_names):
            continue
        if any(IC.names_akin(nm, m) for m in marg_names):
            continue
        if S738_NOT_ITEM.search(nm):
            return []                                         # a freight / round-off / tax line: never named as a line to add
        amt = _amount_p(it.get("amount"))
        out.append(dict(name=nm, qty=it.get("quantity"), amount_p=amt))
    tot = sum(int(x["amount_p"] or 0) for x in out)
    if not out or any(x["amount_p"] in (None, 0) for x in out) or abs(tot - int(diff_p)) > 200:
        return []
    return out


def s738_fixes(con, fast=False):
    """READ ONLY: the corrections that are Amir's now (the header above) -> [dict(bill_id, month, supplier, bill_no, date, scan, stamp, kind,
    marg_p, paper_p, diff_p, items, numbers)], oldest bill first. A month that cannot be read RAISES (nothing is then synced). fast: the
    missing lines are not worked out (the scan door only needs the scans). Inside ONE web request its repeated reads share one result
    (flask.g, keyed by the connection and its change count); outside a request nothing is kept."""
    memo, key = None, (id(con), con.total_changes, bool(fast))
    try:
        from flask import g, has_request_context              # noqa: PLC0415
        if has_request_context():
            memo = g.__dict__.setdefault("_s738_memo", {})
    except Exception:                                         # noqa: BLE001
        memo = None
    if memo is not None and key in memo:
        return [dict(f) for f in memo[key]]
    out = []
    for m in _s738_counted_months(con):
        r = register(con, m)
        for x in r["rows"]:
            if not str(x.get("whose") or "").startswith("Amir"):
                continue
            item = dict(bill_id=int(x["id"]), month=m, supplier=x["supplier"], bill_no=str(x["bill_no"] or ""), date=str(x.get("date") or "")[:10],
                        scan=x.get("scan"), stamp=x.get("stamp") or "", marg_p=int(x.get("amount_p") or 0), paper_p=None, diff_p=0, items=[],
                        numbers=[])
            if x["state"] == "double":
                item["kind"] = "double"
                item["numbers"] = [s.strip() for s in str(x["bill_no"] or "").split(" and ") if s.strip()]
            elif x["state"] == "amount_differs":
                ag = x.get("agree") or {}
                paper = ag.get("scan_p")
                if paper in (None, 0):
                    continue
                item["paper_p"] = int(paper)
                item["diff_p"] = int(paper) - item["marg_p"]
                item["kind"] = "less" if item["diff_p"] < 0 else "more"
                if item["kind"] == "more" and item["scan"] is not None and not fast:
                    b = con.execute("SELECT * FROM purchase_bill WHERE id=?", (item["bill_id"],)).fetchone()
                    item["items"] = _s738_missing(con, dict(b), int(item["scan"]), item["diff_p"]) if b else []
            else:
                continue
            out.append(item)
    out.sort(key=lambda z: (z["date"], z["bill_id"]))
    if memo is not None:
        memo[key] = [dict(f) for f in out]
    return out


def _s738_newest_billwise(con):
    try:
        r = con.execute("SELECT MAX(received_at) FROM purchase_export WHERE type='BILLWISE'").fetchone()
        return str(r[0] or "") if r else ""
    except sqlite3.Error:
        return ""


def s738_sync(con, fixes, now=None):
    """Keeps s738_fix in step with the list (the header above). Writes only s738_fix and audit rows; commits when it wrote. -> (new, settled)."""
    now = now or dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute(S738_DDL)
    have = {int(r[0]): dict(kind=r[1], settled_at=r[2], gone_at=r[3], first_seen=r[4], marg_p=r[5]) for r in
            con.execute("SELECT bill_id, kind, settled_at, gone_at, first_seen, marg_p FROM s738_fix")}
    cur_ids = {int(f["bill_id"]): f for f in fixes or []}
    new = settled = 0
    for bid, f in cur_ids.items():
        h = have.get(bid)
        if h is None:
            con.execute("INSERT INTO s738_fix (bill_id, kind, month, first_seen, last_seen, marg_p) VALUES (?,?,?,?,?,?)",
                        (bid, f["kind"], f["month"], now, now, f["marg_p"]))
            new += 1
        elif h["settled_at"] or h["gone_at"]:                 # back on the list (a later export undid it): open again
            con.execute("UPDATE s738_fix SET kind=?, last_seen=?, settled_at=NULL, settled_export=NULL, gone_at=NULL, first_seen=?, marg_p=? WHERE bill_id=?",
                        (f["kind"], now, now, f["marg_p"], bid))
        else:
            con.execute("UPDATE s738_fix SET kind=?, last_seen=? WHERE bill_id=?", (f["kind"], now, bid))
    open_ = [bid for bid, h in have.items() if not h["settled_at"] and not h["gone_at"] and bid not in cur_ids]
    if open_:
        exp = _s738_newest_billwise(con)
        lk = links(con)
        cx = Ctx(con)
        scans = asset_scans(con) or {}
        pa = _pa()
        for bid in open_:
            h = have[bid]
            b = con.execute("SELECT b.* FROM purchase_bill b WHERE b.id=? AND " + pa.EFF_BILL, (bid,)).fetchone()
            ok = False
            after = bool(exp) and str(exp) > str(h.get("first_seen") or "")      # an export that came after the line was first shown
            if b is not None and after:
                b = dict(b)
                if h.get("kind") == "double":                 # proved when no other live entry of it is left
                    twin = con.execute("SELECT COUNT(*) FROM purchase_bill b WHERE b.id<>? AND b.supplier_norm=? AND lower(trim(b.bill_no))=lower(trim(?)) "
                                       "AND b.bill_date=? AND b.amount_p=? AND " + pa.EFF_BILL,
                                       (bid, b["supplier_norm"], b["bill_no"], b["bill_date"], b["amount_p"])).fetchone()[0]
                    ok = twin == 0
                elif bid in lk and lk[bid]["scan"] in scans and h.get("marg_p") is not None and int(b["amount_p"] or 0) != int(h["marg_p"]):
                    s = scans[lk[bid]["scan"]]
                    ok = s726_state(cx, s, agree(cx, s, b), True) in ("verified", "has_scan")
            if ok:
                con.execute("UPDATE s738_fix SET settled_at=?, settled_export=? WHERE bill_id=?", (now, exp, bid))
                settled += 1
                try:
                    _pa()._audit(con, "server", "s738_fix_proved", bid, dict(export=exp, kit=KIT_S738))
                except Exception:                             # noqa: BLE001
                    pass
            else:
                con.execute("UPDATE s738_fix SET gone_at=? WHERE bill_id=?", (now, bid))
    con.commit()
    return new, settled


def s738_tracked(con):
    try:
        return {int(r[0]): dict(kind=r[1], month=r[2], first_seen=r[3], last_seen=r[4], settled_at=r[5], settled_export=r[6], gone_at=r[7]) for r in
                con.execute("SELECT bill_id, kind, month, first_seen, last_seen, settled_at, settled_export, gone_at FROM s738_fix")}
    except sqlite3.Error:
        return {}


def _s738_dmy(iso):
    d = _date(iso)
    return d.strftime("%d-%m-%Y") if d else ""


def _s738_dm(iso):
    s = str(iso or "")
    return ("%s-%s" % (s[8:10], s[5:7])) if len(s) >= 10 else ""


_S738_CTX = {}                                                # set by check_body for the lines it draws (one request)


def _s738_panel(sid):
    """The opened part: the scan (lazy) beside what it read against Marg."""
    c = _S738_CTX
    s = (c.get("scans") or {}).get(int(sid)) or {}
    b = (c.get("bill_of") or {}).get(int(sid)) or {}
    paper = (c.get("paper") or {}).get(int(sid))
    rows = [("Supplier", s.get("vendor") or "—", b.get("supplier") or ""), ("Bill no.", s.get("bill_no") or "—", b.get("bill_no") or ""),
            ("Date", _s738_dm(s.get("bill_date")) or "—", _s738_dm(b.get("bill_date"))),
            ("Total", rs2(s.get("amount_p")) if s.get("amount_p") else "—", rs2(b.get("amount_p")) if b.get("amount_p") is not None else "")]
    tab = "".join("<tr><th>%s</th><td>%s</td><td>%s</td></tr>" % (esc(k), esc(v1), esc(v2)) for k, v1, v2 in rows)
    if paper is not None:
        tab += "<tr><th>Paper amount given</th><td>%s</td><td></td></tr>" % esc(rs2(paper))
    mo = _scan_moment(s) if s else None
    when = ('<div class="s738w">Scanned %s</div>' % esc(mo.strftime("%d-%m %H:%M"))) if mo else ""
    src = "%s/api/s738/scan/%d" % (c.get("prefix") or "/finance/purchase", int(sid))
    return ('<div class="s738vb"><div class="s738f" data-src="%s"></div><div class="s738t"><div class="s738th">Read on the scan · Marg</div>'
            '<table><tr><th></th><th>Scan</th><th>Marg</th></tr>%s</table>%s<a href="%s" target="_blank" rel="noopener">Open the scan in a new tab</a></div></div>'
            % (esc(src), tab, when, esc(src)))


def _s738_split(tail):
    """(the difference, whose / status) out of a line's tail as the step view's rows write it."""
    t = tail.lstrip(" ·")
    m = re.match(r'^(.*?)\s*<span class="mut">·\s*(.*)</span>\s*$', t, re.S)
    if m:
        diff, rest = m.group(1).strip(), m.group(2).strip()
        mm = re.match(r"^the (paper|scan) reads (more|less) · (.*)$", rest, re.S)
        if mm and diff:
            return "%s %s on %s" % (diff, mm.group(2), mm.group(1)), mm.group(3)
        return diff, rest
    return t, ""


def _s738_cells(x, tail):
    sid = x.get("scan")
    diff, who = _s738_split(tail)
    return ('<span class="c1">%s %s</span><span class="c2">%s</span><span class="c3">%s</span><span class="c4">%s</span><span class="c5">%s</span>'
            % (esc(x["supplier"]), esc(x["bill_no"]), esc(_s738_dmy(x.get("date"))), ("scan %s" % esc(x.get("stamp") or "")) if sid is not None else "no scan",
               diff, who))


def _s738_wrap(cells, sid, bill_id=None):
    attr = (' data-bill="%d"' % int(bill_id)) if bill_id is not None else ""
    if sid is None:
        return '<div class="s738l"%s>%s<span class="c6"></span></div>' % (attr, cells)
    return ('<details class="s738v" ontoggle="s738open(this)"><summary class="s738l"%s>%s<span class="c6"><span class="s738b">'
            '<span class="sh">Show scan &#9662;</span><span class="hd">Hide scan &#9652;</span></span></span></summary>%s</details>'
            % (attr, cells, _s738_panel(sid)))


def _s738_viewer(sid):                                        # the scan-only lines ("Scan B-0182 · ..."): the button and the panel alone
    return ('<details class="s738v s738v2" ontoggle="s738open(this)"><summary class="s738b"><span class="sh">Show scan &#9662;</span>'
            '<span class="hd">Hide scan &#9652;</span></summary>%s</details>' % _s738_panel(sid))


def _ck_line(x, tail):                                        # noqa: F811 -- S738: the bill date, the scan, the folded viewer (columns on a PC)
    return _s738_wrap(_s738_cells(x, tail), x.get("scan"), x["id"])


_check_rows_before_s738 = check_rows


def check_rows(r, cx):                                        # noqa: F811 -- S738: row 3 says whose and since when, and lists the proved
    rows = _check_rows_before_s738(r, cx)
    tr = _S738_CTX.get("tracked") or {}
    month = r.get("month") or ""
    lab, n, lines, grey = rows[2]
    extra = []
    for x in r["rows"]:
        if x["state"] in ("amount_differs", "double") and str(x.get("whose") or "").startswith("Amir"):
            t = tr.get(int(x["id"]))
            if t and not t.get("settled_at"):
                extra.append((int(x["id"]), "on Amir's list since %s" % _s738_dm(t.get("first_seen"))))
    proved = [(bid, t) for bid, t in tr.items() if t.get("settled_at") and t.get("month") == month]
    new_lines = list(lines)
    for bid, note in extra:
        new_lines = [ln.replace("Amir: a Marg correction", "Amir: a Marg correction · %s" % esc(note), 1) if ('data-bill="%d"' % bid) in ln else ln
                     for ln in new_lines]
    for bid, t in proved:
        b = con_bill(r, bid)
        if b is None:
            continue
        new_lines.append('<div class="s738l s738ok"><span class="c1">%s %s</span><span class="c2">%s</span><span class="c3"></span><span class="c4"></span>'
                         '<span class="c5">Amir · corrected — his export of %s shows Marg = the paper ✓</span><span class="c6"></span></div>'
                         % (esc(b["supplier"]), esc(b["bill_no"]), esc(_s738_dmy(b.get("date"))), esc(_s738_dm(t.get("settled_export") or t.get("settled_at")))))
    rows[2] = (lab, n, new_lines, grey)
    hdr = ('<div class="s738hd"><span>Supplier · bill</span><span>Bill date</span><span>Scan</span><span>Difference</span><span>Whose · status</span>'
           '<span></span></div>')
    for i, (lab_, n_, ls_, g_) in enumerate(rows[:5]):
        if any('class="s738l"' in ln for ln in ls_):
            rows[i] = (lab_, n_, [hdr] + list(ls_), g_)
    by_stamp = {str(s.get("stamp_no") or ""): int(k) for k, s in (_S738_CTX.get("scans") or {}).items() if s.get("stamp_no")}
    for i, (lab_, n_, ls_, g_) in enumerate(rows[:5]):        # the lines that name only a scan ("Scan B-0182 · ...") get the viewer too
        out = []
        for ln in ls_:
            m = re.match(r"^Scan ([A-Za-z0-9#-]+) ", ln) if not ln.startswith("<") else None
            sid = by_stamp.get(m.group(1)) if m else None
            out.append(ln + _s738_viewer(sid) if sid is not None else ln)
        rows[i] = (lab_, n_, out, g_)
    return rows


def con_bill(r, bid):
    for x in r["rows"]:
        if int(x["id"]) == int(bid):
            return x
    return None


S738_CSS = """
#s726chk{max-width:1100px}
#s726chk details.row,#s726chk details.grey{display:block}
#s726chk li{list-style:none;margin:0;padding:6px 0;border-top:1px solid #f0ece6}
#s726chk ul{margin:0 0 10px 0;padding:0}
#s726chk .s738l{display:flex;flex-wrap:wrap;gap:2px 10px;align-items:baseline}
#s726chk .s738l .c1{font-weight:700;flex:0 0 100%}
#s726chk .s738l .c2,#s726chk .s738l .c3{color:#555}
#s726chk .s738l .c4{flex:0 0 100%}
#s726chk .s738l .c5{color:#555;flex:1 1 100%}
#s726chk .s738ok .c5{color:#1f4d25}
#s726chk .s738hd{display:none}
@media(min-width:900px){
 #s726chk .s738l,#s726chk .s738hd{display:grid;grid-template-columns:minmax(0,2.2fr) minmax(0,1fr) minmax(0,1fr) minmax(0,1.3fr) minmax(0,2.2fr) 130px;
  gap:6px 14px;align-items:center}
 #s726chk .s738l .c1,#s726chk .s738l .c4,#s726chk .s738l .c5{flex:none}
 #s726chk .s738hd{font-size:13px;color:#555;font-weight:700;padding:2px 0}
}
#s726chk details.s738v{border:0;margin:0}
#s726chk details.s738v>summary{list-style:none;cursor:pointer;min-height:44px}
#s726chk details.s738v>summary::-webkit-details-marker{display:none}
#s726chk .s738b{display:inline-flex;align-items:center;min-height:40px;padding:0 14px;border:1px solid #1f3864;border-radius:9px;color:#1f3864;
 font-weight:600;font-size:14px;background:#fff;white-space:nowrap}
#s726chk details.s738v[open] .s738b{background:#1f3864;color:#fff}
#s726chk .s738b .hd{display:none}
#s726chk details.s738v[open] .s738b .hd{display:inline}
#s726chk details.s738v[open] .s738b .sh{display:none}
#s726chk details.s738v2>summary{display:inline-flex}
#s726chk .s738vb{display:flex;flex-wrap:wrap;gap:12px;margin:8px 0 10px}
#s726chk .s738f{flex:1 1 520px;min-width:0;min-height:560px;background:#e6e8ee;border:1px solid #cfd3db;border-radius:8px;box-sizing:border-box}
#s726chk .s738f iframe{width:100%;height:640px;border:0;border-radius:8px;display:block}
#s726chk .s738f img{max-width:100%;border-radius:8px;display:block}
#s726chk .s738f .s738err{padding:14px;color:#555;font-size:15px}
#s726chk .s738t{flex:0 1 300px;font-size:14px;overflow-wrap:normal;word-break:normal}
#s726chk .s738th{font-weight:700;font-size:15px;margin:0 0 6px}
#s726chk .s738t table{border-collapse:collapse;margin-bottom:8px}
#s726chk .s738t th,#s726chk .s738t td{text-align:left;padding:3px 10px 3px 0;vertical-align:top;border:0;text-transform:none;letter-spacing:0;
 font-size:14px;background:none}
#s726chk .s738t th{color:#555;font-weight:600}
#s726chk .s738w{color:#555;margin:0 0 6px}
#s738up{position:fixed;right:18px;bottom:18px;width:52px;height:52px;border-radius:26px;border:0;background:#1f3864;color:#fff;font-size:24px;
 font-weight:800;cursor:pointer;z-index:70}
"""
S738_JS = """
<script>function s738open(d){if(!d.open)return;var f=d.querySelector('.s738f');if(!f||f.getAttribute('data-done'))return;f.setAttribute('data-done','1');
var src=f.getAttribute('data-src');fetch(src,{method:'HEAD'}).then(function(r){var t=(r.headers.get('Content-Type')||'');
if(t.indexOf('pdf')>=0){var fr=document.createElement('iframe');fr.src=src+'#navpanes=0&view=FitH';fr.title='scan';f.appendChild(fr);}
else if(r.ok){var im=document.createElement('img');im.src=src;im.alt='scan';f.appendChild(im);}
else{s738no(f);}}).catch(function(){s738no(f);});}
function s738no(f){var d=document.createElement('div');d.className='s738err';d.textContent='The scan could not be opened here — use "Open the scan in a new tab" beside it.';f.appendChild(d);}</script>
<button type="button" id="s738up" aria-label="Back to top" onclick="window.scrollTo({top:0,behavior:'smooth'})">&#8593;</button>
"""

_check_body_before_s738 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S738: the viewer's facts, the CSS, the button
    r = r if r is not None else register(con, month)
    scans = asset_scans(con) or {}
    cx = Ctx(con)
    bill_of = {}
    for x in r["rows"]:
        if x.get("scan") is not None:
            b = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (int(x["id"]),)).fetchone()
            if b:
                bill_of[int(x["scan"])] = dict(supplier=_pa().supplier_key(b[0]), bill_no=b[1], bill_date=b[2], amount_p=b[3])
    _S738_CTX.clear()
    _S738_CTX.update(scans=scans, bill_of=bill_of, paper=dict(cx.paper), prefix=prefix, tracked=s738_tracked(con))
    try:
        h = _check_body_before_s738(con, month, prefix, months, r)
    finally:
        _S738_CTX.clear()
    return h.replace("</style>", S738_CSS + "</style>", 1) + S738_JS


def s738_scan_ok(con, sid, doctor, login):
    """May this person open scan sid through /api/s738/scan? The doctor: any captured pharmacy scan. Amir: only a scan on his list."""
    if doctor:
        return True
    try:
        return int(sid) in {int(f["scan"]) for f in s738_fixes(con, fast=True) if f.get("scan") is not None}
    except Exception:                                         # noqa: BLE001
        return False
# ---- S738 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S740 (07-Nov-2026, Sanjeevni session 399, kit S740_PURCHASE_RETURNS; D839 kit 3 as the owner refined it 06:02 - 06:28 IST; his "build"
#      06:35 on the mock https://claude.ai/artifact/SSDYXCz12GfTGn3Uy7uKUe rev 5) ---------------------------------------------------------------
#  PURCHASE RETURNS, TRACKED UNTIL THE DEALER'S PAPER RESOLVES THEM. Every pending return stays on Amir's page and the owner's step view until
#  the dealer's credit note or revised bill resolves it; a month with a pending return is not clear (its NEFT waits).
#  THE DEFAULT (the owner 06:12 - 06:20): goods returned at delivery are entered NET (only what was kept), so Marg's stock is the shelf's and the
#  paper reading more than Marg is what keeps the return tracked. A dealer settles a return in one of two ways (06:02): he REVISES the same bill
#  (Marg keeps that bill at the revised amount; no purchase return) or gives a CREDIT NOTE (Marg: the full bill + a purchase return).
#  THE KINDS (s740_model -- READ ONLY, one result per web request):
#    on_bill  a bill whose paper reads MORE than Marg (S738's "more") and reception answered "Haan, wapsi likhi hai" (s740_answer; the owner's
#             own word seeds Janta 21965, D839). Its row leaves S738's list. Resolved by: a REVISED bill -- a scan of the same supplier and
#             bill number reading paper - return (within max(Rs 2, 1%)) with Marg at that figure; or a CREDIT NOTE -- a Marg purchase return
#             (a minus bill) of that supplier for the return's amount, dated on/after the bill, with Marg holding the full bill and the
#             credit note's own paper scanned; or the dealer TAKING IT OFF a later bill (a scan's own return line for that amount).
#    marg     every Marg purchase return of a counted month that no other return claims (goods sent back later, entered from a slip):
#             resolved when its own paper (the credit note) is scanned and agrees.
#    own      the owner's own record -- "Yes, returned to <dealer>" on a stock-count shortage (a whole strip / box short of an item bought
#             in the last 180 days from ONE dealer only; stock_watch_loss_line) or "Record a return" (dealer, item, quantity, all picked;
#             the value at the last purchase rate). Amir enters the purchase return; then as "marg".
#  A minus bill is compared with its paper by its size (agree() below; porders' amount question likewise). The register's rows of a return
#  carry whose it is ("Return: ..."), never "Amir: a Marg correction", so S738's list does not carry them twice.
#  s740_sync keeps s740_track (first seen / resolved / gone) -- called from Amir's own page and reception's list; the owner's GET writes
#  nothing. assets.db READ ONLY. Nothing here prints a phone number, an account number or a key.
KIT_S740 = "S740_PURCHASE_RETURNS"
S740_DDL = (
    "CREATE TABLE IF NOT EXISTS s740_answer (sup TEXT NOT NULL, bill_no TEXT NOT NULL, bill_date TEXT NOT NULL, answer TEXT NOT NULL, paper_p INTEGER, "
    "marg_p INTEGER, ret_p INTEGER, by TEXT, at TEXT NOT NULL, undone_at TEXT, undone_by TEXT, PRIMARY KEY (sup, bill_no, bill_date))",
    "CREATE TABLE IF NOT EXISTS s740_own (id INTEGER PRIMARY KEY AUTOINCREMENT, sup TEXT NOT NULL, supplier TEXT, item TEXT, qty REAL, unit TEXT, "
    "est_p INTEGER, source TEXT NOT NULL, loss_id INTEGER, by TEXT, at TEXT NOT NULL, withdrawn_at TEXT, withdrawn_by TEXT)",
    "CREATE TABLE IF NOT EXISTS s740_flag (loss_id INTEGER PRIMARY KEY, answer TEXT NOT NULL, by TEXT, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS s740_same (bill_id INTEGER PRIMARY KEY, answer TEXT NOT NULL, rkey TEXT, by TEXT, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS s740_cn_look (bill_id INTEGER PRIMARY KEY, marg_p INTEGER NOT NULL, scan_p INTEGER, by TEXT, at TEXT NOT NULL)",
    "CREATE TABLE IF NOT EXISTS s740_track (rkey TEXT PRIMARY KEY, kind TEXT, month TEXT, first_seen TEXT NOT NULL, last_seen TEXT, resolved_at TEXT, "
    "road TEXT, ref TEXT, gone_at TEXT, off_ref TEXT)")
S740_FLAG_DAYS = 180                                          # "bought from ONE dealer" looks back this far
S740_FLAG_FROM = "2026-10-01"                                 # count shortages before this are history
S740_RET_LINE = re.compile(r"\b(RETURNS?|RETURNED|RTN|SALES?\s*RETURNS?|GOODS\s*RETURN\w*|CREDIT\s*NOTE|DEBIT\s*NOTE|CR\.?\s*NOTE|CR\.?\s*N\.?|CRN|"
                           r"C\.?\s*N\.?|D\.?\s*N\.?|CN\s*ADJ\w*|RETRN|DN\s*NO)\b|\b[CD]\s*/\s*N\b|\bCN\d|\bRET\.(?=\s*(GOODS|EXP|$))|\b(EXPIRY|EXP\.?)\s*RET\b|"
                           r"\bLESS\W*RET\b",
                           re.I)   # never bare RET (retard); a line counts only when it is NEGATIVE as well
S740_NOT_RET = re.compile(r"\b(DISC\w*|ROUND\w*|CESS|FREIGHT|CARTAGE|RATE|DIFF\w*|SCHEME|SCH|PRICE)\b|^\s*(C|S|I)?GST\b|^\s*TAX\b", re.I)   # a tax line itself, not a
# return line that mentions GST
S740_SETTLED = ("verified", "has_scan", "accepted")


def s740_ensure(con):
    for ddl in S740_DDL:
        con.execute(ddl)
    if "off_ref" not in {r[1] for r in con.execute("PRAGMA table_info(s740_track)")}:   # a table made before the column
        con.execute("ALTER TABLE s740_track ADD COLUMN off_ref TEXT")


def _s740_tol(p):
    return max(200, abs(int(p or 0)) // 100)


def _s740_nl(s):
    return str(s or "").strip().lower()


def _s740_now():
    try:
        import order_sheet as _OS                             # noqa: PLC0415
        return _OS.now().replace(microsecond=0, tzinfo=None).isoformat()
    except Exception:                                         # noqa: BLE001
        return (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).replace(microsecond=0).isoformat()


def _s740_rows(con, sql, args=()):
    try:
        return [dict(r) if isinstance(r, sqlite3.Row) else r for r in con.execute(sql, args).fetchall()]
    except sqlite3.Error:
        return []


def _s740_answers(con):
    out = {}
    try:
        for r in con.execute("SELECT sup, bill_no, bill_date, answer, paper_p, marg_p, ret_p, by, at, undone_at FROM s740_answer"):
            if r[9]:
                continue
            out[(str(r[0]), _s740_nl(r[1]), str(r[2]))] = dict(answer=r[3], paper_p=r[4], marg_p=r[5], ret_p=r[6], by=r[7], at=r[8])
    except sqlite3.Error:
        pass
    return out


def _s740_readings(ids):
    """{scan id: its item lines} for many scans in ONE read of assets.db (READ ONLY)."""
    ids = sorted({int(i) for i in ids if i is not None})
    if not ids:
        return {}
    acon = _pa()._assets_con()
    if acon is None:
        return None
    out = {}
    try:
        for i in range(0, len(ids), 400):
            part = ids[i:i + 400]
            for bid, data in acon.execute("SELECT bill_id, data FROM claude_reading WHERE ok=1 AND bill_id IN (%s) ORDER BY rowid"
                                          % ",".join("?" * len(part)), part):
                try:
                    d = json.loads(data) if data else {}
                except ValueError:
                    d = {}
                out[int(bid)] = [x for x in (d.get("items") or []) if isinstance(x, dict)]
    except sqlite3.Error:
        return None
    finally:
        acon.close()
    return out


def _s740_amt_p(v):
    try:
        return int(round(float(v) * 100))
    except (TypeError, ValueError):
        return None


def _s740_taken_off(items, total_p):
    """The amount a dealer's BILL takes off as a return, in paise; 0 when none. Only a bill counts: its total positive, and goods lines (positive)
    worth more than what it takes off. Only a line that is NEGATIVE (amount, else quantity) AND says return (RETURN / RTN / CREDIT NOTE --
    never a bare RET, which is a medicine's name: "ADALAT RET") counts. A credit note read with minus lines is not a bill and counts nothing."""
    if not total_p or int(total_p) <= 0:
        return 0, ""
    ret = goods = 0
    words = []
    for it in items or []:
        nm = str(it.get("name") or "")
        a = _s740_amt_p(it.get("amount"))
        if a is None or a == 0:
            continue
        try:
            q = float(it.get("quantity") if it.get("quantity") is not None else 0)
        except (TypeError, ValueError):
            q = 0
        neg = a < 0 or q < 0
        if neg and S740_RET_LINE.search(nm) and not S740_NOT_RET.search(nm):
            ret += abs(a)
            words.append(nm)
        elif a > 0 and not neg:
            goods += a
    return (ret, " ".join(words)) if (ret and goods > ret) else (0, "")


def _s740_norm(s):
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def _s740_tokens(text):
    """The words of a return line, separators inside a word removed ("ZR-1" -> "ZR1", "A/2026/12" -> "A202612")."""
    toks = [_s740_norm(t) for t in re.split(r"[\s,;:()\[\]]+", str(text or ""))]
    toks = [t for t in toks if t]
    out = set()
    for i, t in enumerate(toks):
        if t.isdigit() and len(t) < 3:                        # "2", "45": a count -- unless it follows CN / PR / NO / BILL / DN
            nxt = toks[i + 1] if i + 1 < len(toks) else ""
            if (i and toks[i - 1] in ("CN", "CRN", "PR", "NO", "BILL", "DN", "NOTE", "CREDITNOTE")
                    and not re.match(r"^(STRIPS?|STRP|PCS?|NOS?|TABS?|CAPS?|TUBES?|PKTS?|PACKS?|AMPS?|BOX(ES)?|BOTTLES?|BTL|VIALS?|UNITS?|QTY)$", nxt)):
                out.add(t)
            continue
        out.add(t)
    return out


def _s740_pick_off(offs, used_off, ok, bill_no, named_only=False):          # bill_no: one number or several (the purchase return's, the bill's)
    me_paper = int(getattr(_S740_T, "cur_paper", 0) or 0)        # a return written on a bill: its own paper re-read under another number is
    if me_paper:                                                  # never a deduction (the same total)
        ok0 = ok
        ok = lambda o: ok0(o) and abs(int(o.get("total_p") or 0) - me_paper) > 100   # noqa: E731
    """The deduction for a return: among those that fit (ok), the one whose return line names this return's bill first; else the earliest
    that names NO return's bill (a deduction naming another return is that return's)."""
    adj_of, me = getattr(_S740_T, "adj_of", None) or {}, getattr(_S740_T, "cur_key", None)
    pre = (getattr(_S740_T, "pre", None) or {}).get(me)      # this return's own deduction, found before the claim: whatever its date
    c = [o for o in offs if o["scan"] not in used_off and adj_of.get(o["stamp"], me) == me and (ok(o) or o["scan"] == pre)]   # never ANOTHER's
    if not c:
        return None
    nbs = {_s740_norm(b) for b in (bill_no if isinstance(bill_no, (tuple, list)) else (bill_no,)) if _s740_norm(b)}
    named = [o for o in c if nbs & (o.get("names") or set())]
    if named:
        return named[0]
    own = [o for o in c if o["scan"] == pre and (not o.get("names") or nbs & o["names"])
           and not (me_paper and abs(int(o.get("total_p") or 0) - me_paper) <= 100)]   # its own, unless it names ANOTHER return
    if own:
        return own[0]
    if named_only:
        return None
    free = sorted([o for o in c if not o.get("names")], key=lambda o: (o["bdate"], o["scan"]))
    return free[0] if free else None


def _s740_unit(packing):
    p = str(packing or "")
    m = re.match(r"^\s*1\s*\*\s*(\d+)", p)
    return "strip" if (m and int(m.group(1)) > 1) else "pc"


def _s740_qty_words(qty, unit):
    q = float(qty or 0)
    n = int(q) if q == int(q) else q
    return "%s %s" % (n, unit if n == 1 else (unit + "s"))


def _s740_last_rate(con, sup, item):
    """(rate per Marg unit in paise, packing) of the item's last purchase from this dealer (minus bills left out)."""
    r = _s740_rows(con, "SELECT l.rate_p, l.packing FROM purchase_line l WHERE l.supplier_norm=? AND lower(trim(l.item))=lower(trim(?)) AND l.rate_p>0 "
                        "AND NOT EXISTS (SELECT 1 FROM purchase_bill b WHERE b.supplier_norm=l.supplier_norm AND lower(trim(b.bill_no))=lower(trim(l.bill_no)) "
                        "AND b.bill_date=l.bill_date AND b.amount_p<0) ORDER BY l.bill_date DESC, l.id DESC LIMIT 1", (sup, item))
    if not r:
        return None, ""
    r = r[0]
    return (int(r["rate_p"]) if isinstance(r, dict) else int(r[0])), (r["packing"] if isinstance(r, dict) else r[1]) or ""


_S740_MEMO = {}                                               # outside a web request: id(con) -> (con, changes, time, model), one entry, 20 s


def s740_model(con):
    """READ ONLY: dict(returns=[...], questions=[...], flags=[...], adjusted=[...], assets_ok) -- the header above. One result per web
    request; outside one, the same result for 20 seconds while the connection has written nothing."""
    import time as _time                                      # noqa: PLC0415
    memo, key = None, (id(con), con.total_changes)
    try:
        from flask import g, has_request_context              # noqa: PLC0415
        if has_request_context():
            memo = g.__dict__.setdefault("_s740_memo", {})
    except Exception:                                         # noqa: BLE001
        memo = None
    if memo is not None and key in memo:
        return memo[key]
    if memo is None:
        hit = _S740_MEMO.get(id(con))
        if hit and hit[0] is con and hit[1] == con.total_changes and _time.time() - hit[2] < 20:
            return hit[3]
    out = _s740_build(con)
    if memo is not None:
        memo[key] = out
    else:
        _S740_MEMO.clear()
        _S740_MEMO[id(con)] = (con, con.total_changes, _time.time(), out)
    return out


def _s740_first(con):
    v = setting(con, "purchase.register_from", "2026-10-01")
    return max(v[:7] if re.match(r"^\d{4}-\d\d", v) else "2026-10", "2026-10")


def _s740_months(con):
    """Every counted month from purchase.register_from on -- a FINALISED month too while it holds a return (an answer, a purchase return or
    the owner's record): its pending returns stay until resolved (the owner 06:08)."""
    first = _s740_first(con)
    ms = sorted(m for m in months_with_bills(con, 24) if m >= first and month_class(con, m) == "counted")
    try:
        final = {str(r[0]) for r in con.execute("SELECT month FROM purchase_month WHERE status='final'")}
    except sqlite3.Error:
        final = set()
    if not final:
        return ms
    held = {str(r["bill_date"])[:7] for r in _s740_rows(con, "SELECT bill_date FROM s740_answer WHERE answer='yes' AND undone_at IS NULL")}
    held |= {str(r["m"] or "")[:7] for r in _s740_rows(con, "SELECT COALESCE(month, substr(bill_date,1,7)) AS m FROM purchase_bill WHERE amount_p<0")}
    return [m for m in ms if m not in final or m in held]


def _s740_revised(cx, scans, r, b, set_aside=False):
    """A scan of the same supplier and bill number reading the paper less the return -- the dealer's revised bill. (sid, paise, stamp) | None.
    S824 (F-1378): set_aside=True reads the scans of s824_set_aside (each has dup_of) by the same rules, and returns (sid, paise, stamp, True)."""
    P, A = int(r["paper_p"] or 0), int(r["amount_p"] or 0)
    net = P - A
    for sid, s in scans.items():
        if sid == r.get("scan") or str(s.get("lane") or "pharmacy") != "pharmacy" or (s.get("dup_of") and not set_aside):
            continue
        if billno(s.get("bill_no"), b["bill_no"]) != "agree":
            continue
        sa = scan_amount(cx, s)
        if not sa or abs(int(sa) - P) <= 100 or abs(int(sa) - net) > _s740_tol(A):
            continue
        if supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)) != "agree":
            continue
        if set_aside:
            return (sid, int(sa), s.get("stamp_no") or "#%d" % sid, True)
        return (sid, int(sa), s.get("stamp_no") or "#%d" % sid)
    return None


def _s740_build(con):
    pa = _pa()
    cx = Ctx(con)
    first = _s740_first(con)
    months = _s740_months(con)
    qmonths = set(_s738_counted_months(con))                  # questions only where S738 itself still works (a finalised month asks nothing new)
    scans = asset_scans(con)
    assets_ok = scans is not None
    scans = scans or {}
    lk = links(con)
    ans = _s740_answers(con)
    tr = s740_tracked(con)
    _S740_T.look = {int(r["bill_id"]): int(r["marg_p"]) for r in _s740_rows(con, "SELECT bill_id, marg_p FROM s740_cn_look")}
    rowby, qrows = {}, {}
    for m in months:
        for x in _register_before_s740(con, m)["rows"]:
            rowby[int(x["id"])] = x
            if m in qmonths:
                qrows[int(x["id"])] = x
    bills = [dict(r) for r in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL + " ORDER BY b.bill_date, b.id")]
    bills = [b for b in bills if str(b.get("month") or str(b["bill_date"])[:7]) >= first]
    minus = [b for b in bills if int(b["amount_p"] or 0) < 0]
    aside = None                                              # S824 (F-1378): the set-aside scans, read once and only when needed
    rets = []
    for b in bills:
        if int(b["amount_p"] or 0) <= 0:
            continue
        a = ans.get((str(b["supplier_norm"]), _s740_nl(b["bill_no"]), str(b["bill_date"])))
        if not a or a["answer"] != "yes":
            continue
        r = dict(kind="on_bill", key="bill:%s|%s|%s" % (b["supplier_norm"], _s740_nl(b["bill_no"]), b["bill_date"]),
                 month=str(b.get("month") or str(b["bill_date"])[:7]), sup=str(b["supplier_norm"]), supplier=pa.supplier_key(b["supplier"]),
                 bill_id=int(b["id"]), bill_no=str(b["bill_no"] or ""), date=str(b["bill_date"])[:10], amount_p=int(a["ret_p"] or 0),
                 paper_p=int(a["paper_p"] or 0), marg_p=int(b["amount_p"] or 0), scan=(lk.get(int(b["id"])) or {}).get("scan"),
                 opened=str(a["at"] or ""), by=str(a["by"] or ""))
        r["_rev"] = _s740_revised(cx, scans, r, b)
        if r["_rev"] is None and assets_ok:                   # S824 (F-1378): a revised bill set aside by a "same paper" answer
            if aside is None:
                aside = s824_set_aside(con)
            rv = _s740_revised(cx, aside, r, b, set_aside=True)
            if rv is not None and abs(int(b["amount_p"] or 0) - rv[1]) <= 100:   # only when Marg already holds the revised figure: a set-aside
                r["_rev"] = rv                                # scan never outranks a credit note, never sends Amir to a paper he cannot open
        rets.append(r)
    for o in _s740_rows(con, "SELECT o.*, l.at AS loss_at FROM s740_own o LEFT JOIN stock_watch_loss_line l ON l.id=o.loss_id "
                             "WHERE o.withdrawn_at IS NULL ORDER BY o.id") or _s740_rows(con, "SELECT *, NULL AS loss_at FROM s740_own WHERE withdrawn_at IS NULL ORDER BY id"):
        rets.append(dict(kind="own", key="own:%d" % o["id"], own_id=int(o["id"]), month=str(o["at"])[:7], sup=str(o["sup"]), cut=str(o["loss_at"] or o["at"]),
                         supplier=o["supplier"] or o["sup"], bill_id=None, bill_no="", date=str(o["at"])[:10], amount_p=int(o["est_p"] or 0),
                         item=o["item"] or "", qty=o["qty"], unit=o["unit"] or "pc", source=o["source"], scan=None, opened=str(o["at"]),
                         by=str(o["by"] or "")))
    # a dealer's later BILL taking a return off (its own return lines)
    tr_res = {k for k, t in tr.items() if t.get("resolved_at")}
    keep = {str(t.get("off_ref") or "") for t in tr.values() if t.get("off_ref") and not t.get("gone_at")}   # a deduction tied to a return stays read
    open_days = [(((_date(str(r.get("cut") or r["date"])[:10]) or today()) - dt.timedelta(days=45)).isoformat() if r["kind"] == "own" else r["date"])
                 for r in rets if r["key"] not in tr_res]             # the owner's own: the dealer may have taken it off up to 45 days before
    open_days += [str(mb["bill_date"])[:10] for mb in minus
                  if "mret:%s|%s|%s" % (mb["supplier_norm"], _s740_nl(mb["bill_no"]), mb["bill_date"]) not in tr_res]
    s_from = ((_date(min(open_days)) or today()) - dt.timedelta(days=3)).isoformat()[:7] if open_days else today().isoformat()[:7]
    prev = (today().replace(day=1) - dt.timedelta(days=1)).isoformat()[:7]
    s_from = min([s_from, prev] + list(qmonths))              # last month and every month not yet finalised always read (the owner reviews them)
    s_from = max(s_from, (today() - dt.timedelta(days=120)).isoformat()[:7])     # never more than four months of scans per read
    sup_scans = [s for s in scans.values() if str(s.get("lane") or "pharmacy") == "pharmacy" and not s.get("dup_of")
                 and (str(s.get("month") or "") >= max(first, s_from) or (s.get("stamp_no") or "#%d" % int(s["id"])) in keep)]
    readings = _s740_readings([s["id"] for s in sup_scans])
    if readings is None:
        assets_ok, readings = False, {}
    own_scans = {int(r["scan"]) for r in rets if r.get("scan") is not None}   # a return's own paper is never a deduction
    offs = []
    for s in sup_scans:
        x, words = _s740_taken_off(readings.get(int(s["id"])), scan_amount(cx, s))
        bd = str(s.get("bill_date") or "")[:10]
        if x and _date(bd):                                   # the later bill's OWN date must be read
            offs.append(dict(scan=int(s["id"]), stamp=s.get("stamp_no") or "#%d" % int(s["id"]), vendor=s.get("vendor") or "", day=str(s.get("day") or "")[:10],
                             bdate=bd, bill_no=str(s.get("bill_no") or ""), amount_p=x, sid=int(s["id"]), total_p=scan_amount(cx, s), text=words))
    bill_of_scan = {int(v["scan"]): int(bid) for bid, v in lk.items() if v.get("scan") is not None}
    seen_off, kept = set(), []
    offs.sort(key=lambda o: (o["scan"] not in bill_of_scan, o["scan"]))   # the scan Marg's bill is linked to first
    for o in offs:
        if o["scan"] in own_scans:
            continue
        k = (_s740_norm(o["vendor"]), _s740_norm(o["bill_no"]), o["bdate"])
        if o["bill_no"] and k in seen_off:                    # the same later bill scanned twice: one deduction
            continue
        seen_off.add(k)
        bid = bill_of_scan.get(o["scan"])
        b2 = con.execute("SELECT amount_p FROM purchase_bill WHERE id=?", (bid,)).fetchone() if bid is not None else None
        o.update(bill_id=bid, marg_p=(int(b2[0] or 0) if b2 is not None else None))
        kept.append(o)
    offs = kept
    for o in offs:                                            # a deduction names a return of ITS OWN dealer only
        nm = {_s740_norm(r["bill_no"]) for r in rets if r.get("bill_no") and supplier(cx, o["vendor"], r["supplier"]) == "agree"}
        nm |= {_s740_norm(mb["bill_no"]) for mb in minus if supplier(cx, o["vendor"], mb["supplier"]) == "agree"}
        o["names"] = {t for t in _s740_tokens(o.get("text")) if t in nm}
    claimed = {}
    lines_of = {}
    same = {int(x["bill_id"]): dict(answer=x["answer"], rkey=x["rkey"]) for x in _s740_rows(con, "SELECT bill_id, answer, rkey FROM s740_same")}
    maybe = {}                                                # a later purchase return that MAY be the credit note a settled return's deduction cited
    for mb in minus:                                          # an item printed on two lines (two batches) is ONE quantity, by its size
        lq = {}
        for r in _s740_rows(con, "SELECT item, qty FROM purchase_line WHERE supplier_norm=? AND lower(trim(bill_no))=lower(trim(?)) AND bill_date=?",
                            (mb["supplier_norm"], mb["bill_no"], mb["bill_date"])):
            lq[_s740_nl(r["item"])] = lq.get(_s740_nl(r["item"]), 0.0) + abs(float(r["qty"] or 0))
        lines_of[int(mb["id"])] = lq
    for r in sorted(rets, key=lambda z: (z["opened"], z["key"])):
        if r.get("_rev"):                                     # settled by the dealer's revised bill: it takes no purchase return
            continue
        off_day = ""
        if r["kind"] == "on_bill":                            # the dealer took it off a later bill: only a credit note that existed by that
            nb_ = _s740_norm(r["bill_no"])
            fit = sorted([o for o in offs if o["scan"] != r.get("scan") and o["bdate"] > r["date"]   # bill's date can be the same return
                          and billno(o["bill_no"], r["bill_no"]) == "differ" and abs(int(o["total_p"] or 0) - int(r.get("paper_p") or 0)) > 100
                          and abs(o["amount_p"] - r["amount_p"]) <= _s740_tol(r["amount_p"])
                          and supplier(cx, o["vendor"], r["supplier"]) == "agree" and (not o.get("names") or nb_ in o["names"])],
                         key=lambda o: (nb_ not in (o.get("names") or set()), o["bdate"], o["scan"]))   # one naming THIS bill first; never another's
            t_ = tr.get(r["key"]) or {}
            tied = next((o for o in offs if t_.get("off_ref") and o["stamp"] == t_["off_ref"]), None)
            pre = tied or (fit[0] if fit else None)
            if pre is not None:
                off_day = pre["bdate"]
                r["_pre_off"] = pre["scan"]
                r["_pre_names"] = set(pre.get("names") or set())
            elif not assets_ok and t_.get("off_ref"):         # the scans unreadable: a return the tracker tied to a deduction claims nothing new
                off_day = r["date"]
        best = None
        for mb in minus:
            if int(mb["id"]) in claimed or str(mb["supplier_norm"]) != r["sup"]:
                continue
            size = -int(mb["amount_p"] or 0)
            if r["kind"] == "on_bill":
                ok = str(mb["bill_date"]) >= r["date"] and abs(size - r["amount_p"]) <= _s740_tol(r["amount_p"])
                sa = same.get(int(mb["id"])) or {}
                if ok and sa.get("answer") == "other" and sa.get("rkey") == r["key"]:   # the owner said: another return -- never this one's
                    ok = False
                elif ok and _s740_norm(mb["bill_no"]) in (r.get("_pre_names") or set()):
                    pass                                      # the deduction NAMES this purchase return: the same credit note, whatever Marg's date
                elif ok and off_day and str(mb["bill_date"]) > off_day:           # after the deduction: the same credit note, or another return?
                    if not (sa.get("answer") == "same" and sa.get("rkey") == r["key"]):
                        if assets_ok and not sa:
                            maybe.setdefault(int(mb["id"]), r)
                        ok = False
            else:
                # the owner's own: a purchase return dated within 45 days before it was recorded (Marg may carry the slip's date) that no
                # one saw as a return of its own before it was recorded -- carrying the item in about that quantity, or else about that value
                d0 = ((_date(r["date"]) or today()) - dt.timedelta(days=45)).isoformat()
                mk = "mret:%s|%s|%s" % (mb["supplier_norm"], _s740_nl(mb["bill_no"]), mb["bill_date"])
                seen = (tr.get(mk) or {}).get("first_seen")
                fsd = str(mb.get("first_seen_day") or "")[:10]
                cut = str(r.get("cut") or r["opened"])
                if str(mb["bill_date"]) < d0 or (seen and str(seen) <= cut) or (fsd and fsd < cut[:10]):
                    continue
                lines_mb = lines_of.get(int(mb["id"]), {})
                q = lines_mb.get(_s740_nl(r.get("item")))
                want = float(r.get("qty") or 0)
                if lines_mb:                                  # its lines are in: the item must be on it
                    ok = q is not None and want > 0 and abs(q - want) <= max(1.0, want / 2)
                else:                                         # no lines yet: about the value
                    ok = abs(size - r["amount_p"]) <= max(_s740_tol(r["amount_p"]), r["amount_p"] * 3 // 10)
            if ok and (best is None or str(mb["bill_date"]) < str(best["bill_date"])):
                best = mb
        if best is not None:
            claimed[int(best["id"])] = r["key"]
            r["mb"] = dict(id=int(best["id"]), bill_no=str(best["bill_no"] or ""), date=str(best["bill_date"])[:10], size=-int(best["amount_p"] or 0))
    keys = {r["key"] for r in rets}
    for mb in minus:
        if int(mb["id"]) in claimed:
            continue
        k = "mret:%s|%s|%s" % (mb["supplier_norm"], _s740_nl(mb["bill_no"]), mb["bill_date"])
        if k in keys:                                         # the same return entered twice in Marg: ONE return, its stage 'double'
            continue
        keys.add(k)
        rets.append(dict(kind="marg", key=k, maybe_of=(maybe.get(int(mb["id"])) or {}).get("key"),
                         maybe_bill=(maybe.get(int(mb["id"])) or {}).get("bill_no"),
                         month=str(mb.get("month") or str(mb["bill_date"])[:7]), sup=str(mb["supplier_norm"]), supplier=pa.supplier_key(mb["supplier"]),
                         bill_id=int(mb["id"]), bill_no=str(mb["bill_no"] or ""), date=str(mb["bill_date"])[:10], amount_p=-int(mb["amount_p"] or 0),
                         scan=(lk.get(int(mb["id"])) or {}).get("scan"), opened=str(mb.get("first_seen_day") or mb["bill_date"]),
                         mb=dict(id=int(mb["id"]), bill_no=str(mb["bill_no"] or ""), date=str(mb["bill_date"])[:10], size=-int(mb["amount_p"] or 0))))
    used_off = set()
    _S740_T.adj_of = {str(t.get("off_ref") or ""): k for k, t in tr.items() if t.get("off_ref") and not t.get("gone_at")}
    _S740_T.pre = {r["key"]: r.get("_pre_off") for r in rets if r.get("_pre_off") is not None}
    for r in sorted(rets, key=lambda z: (z["kind"] == "own", z["opened"], z["key"])):
        _S740_T.cur_key = r["key"]
        _S740_T.cur_paper = int(r.get("paper_p") or 0) if r["kind"] == "on_bill" else 0
        _s740_stage(con, cx, r, scans, lk, rowby, offs, used_off)
        r.pop("_rev", None)
        r.pop("_pre_off", None)
        r.pop("_pre_names", None)
    _S740_T.cur_key = None
    _S740_T.cur_paper = 0
    later_ok = [(int(r["adj"]["paper_p"]), int(r["adj"]["marg_p"])) for r in rets if r.get("adj") and r["adj"].get("marg_p") is not None]   # every later
    # bill that took a return off, settled or not, by its paper and its CURRENT Marg figure: S740's card owns it, never S440's question
    own_open = [r for r in rets if r["kind"] == "own" and not r["resolved"]]
    adjusted = [o for o in offs if o["scan"] not in used_off and o["scan"] not in own_scans and not any(
        supplier(cx, o["vendor"], r["supplier"]) == "agree" and abs(o["amount_p"] - r["amount_p"]) <= max(_s740_tol(r["amount_p"]), r["amount_p"] * 3 // 10)
        and ((_date(str(r.get("cut") or r["date"])[:10]) or today()) - dt.timedelta(days=45)).isoformat() <= o["bdate"]
        <= ((_date(str(r.get("cut") or r["date"])[:10]) or today()) + dt.timedelta(days=45)).isoformat() for r in own_open) and not any(
        r["kind"] == "on_bill" and supplier(cx, o["vendor"], r["supplier"]) == "agree"
        and (billno(o["bill_no"], r["bill_no"]) == "agree" or (billno(o["bill_no"], r["bill_no"]) == "not_read"
                                                              and abs(int(o["total_p"] or 0) - int(r.get("paper_p") or 0)) <= 100)) for r in rets)]
    for o in adjusted:
        o["supplier"] = next((r["supplier"] for r in rets if supplier(cx, o["vendor"], r["supplier"]) == "agree"), o["vendor"])
    rets.sort(key=lambda z: (z["month"], z["date"], z["key"]))
    return dict(returns=rets, questions=_s740_questions(con, ans, qrows), no_answers=_s740_no_answers(con, ans, qrows), adjusted=adjusted,
                first=first, assets_ok=assets_ok, later_ok=later_ok)


def _s740_paper_ok(rowby, lk, bid):
    look = getattr(_S740_T, "look", None) or {}               # set by _s740_build for its own thread: {bill id: Marg's amount when the owner looked}
    x = rowby.get(int(bid))
    if x is not None:
        if x["state"] == "amount_differs" and int(bid) in look and int(look[int(bid)]) == int(x.get("amount_p") or 0):
            return True, x                                    # the owner looked: the credit note was misread, its paper is Marg's
        return x["state"] in S740_SETTLED, x
    return int(bid) in lk, None


def _s740_stage(con, cx, r, scans, lk, rowby, offs, used_off):
    """Sets r['stage'] (resolved | waiting | do_revised | do_full | do_return | do_own | do_amount | paper), r['road'], r['ref'], r['hi'], r['en'],
    r['whose'] and r['resolved'] -- the header above."""
    rs_ = rs
    A = int(r["amount_p"] or 0)
    r.update(road="", ref="", resolved=False)
    sup_name = r["supplier"]
    if r["kind"] == "on_bill":
        b = con.execute("SELECT * FROM purchase_bill WHERE id=?", (r["bill_id"],)).fetchone()
        b = dict(b) if b else dict(supplier=r["supplier"], bill_no=r["bill_no"], bill_date=r["date"], amount_p=r["marg_p"])
        M, P = int(b.get("amount_p") or 0), int(r["paper_p"] or 0)
        r["marg_p"] = M
        rev = r.get("_rev")
        off = _s740_pick_off(offs, used_off, lambda o: (o["scan"] != r.get("scan") and o["bdate"] > r["date"]
                             and billno(o["bill_no"], r["bill_no"]) == "differ" and abs(int(o["total_p"] or 0) - P) > 100
                             and abs(o["amount_p"] - A) <= _s740_tol(A) and supplier(cx, o["vendor"], b["supplier"]) == "agree"), r["bill_no"])
        mb = r.get("mb")
        if rev is not None:
            if len(rev) < 4:                                  # S824: a set-aside scan is named in the words, never linked (the door serves captured scans)
                r["revised"] = dict(scan=rev[0], amount_p=rev[1], stamp=rev[2])
            if abs(M - rev[1]) <= 100:
                r.update(stage="resolved", road="revised", ref=rev[2], resolved=True,
                         en="Settled: the dealer revised the bill to %s (scan %s) and Marg holds it." % (rs_(rev[1]), rev[2]))
            else:
                r.update(stage="do_revised", hi="Dealer ne bill badla hai (naya bill &#8377;%s). Marg mein bill &#8377;%s kijiye." % (_s740_hrs(rev[1]), _s740_hrs(rev[1])),
                         en="The dealer revised the bill to %s (scan %s); Marg holds %s — Amir sets Marg to %s." % (rs_(rev[1]), rev[2], rs_(M), rs_(rev[1])),
                         whose="Return: Amir enters it in Marg")
        elif mb is not None:
            if abs(M - P) > 100:
                off2 = _s740_pick_off(offs, used_off, lambda o: (o["scan"] != r.get("scan") and o["bdate"] > r["date"]   # a later bill that took
                                      and billno(o["bill_no"], r["bill_no"]) == "differ" and abs(o["amount_p"] - A) <= _s740_tol(A)   # it off too stays
                                      and supplier(cx, o["vendor"], b["supplier"]) == "agree"), (mb["bill_no"], r["bill_no"]))      # held meanwhile
                if off2 is not None:
                    used_off.add(off2["scan"])
                    r["adj"] = dict(scan=off2["scan"], stamp=off2["stamp"], bill_id=off2.get("bill_id"), bill_no=off2["bill_no"],
                                    goods_p=int(off2["total_p"] or 0) + int(off2["amount_p"] or 0), off_p=int(off2["amount_p"]),
                                    paper_p=int(off2["total_p"] or 0), marg_p=off2.get("marg_p"))
                r.update(stage="do_full", hi="Dealer ka credit note Marg mein aa gaya (purchase return %s). Ab Marg mein bill &#8377;%s kijiye (poora bill)."
                         % (_esc_h(mb["bill_no"]), _s740_hrs(P)),
                         en="Credit note %s is in Marg; the bill is still %s in Marg — Amir enters the full bill %s." % (mb["bill_no"], rs_(M), rs_(P)),
                         whose="Return: Amir enters it in Marg")
            else:
                _s740_mb_stage(r, mb, rowby, lk, "Settled: full bill %s and purchase return %s in Marg; the credit note is scanned." % (rs_(M), mb["bill_no"]),
                               cx, offs, used_off)
                if r.get("stage") == "paper":
                    r.update(hi="Poora bill aur purchase return Marg mein hain. Dealer ke credit note ka scan baaki hai (reception).",
                             en="Full bill and purchase return %s in Marg; the credit note's paper is to be scanned (reception)." % mb["bill_no"])
        elif off is not None:
            used_off.add(off["scan"])
            _s740_adj(r, off, "Settled: the dealer took %s off a later bill (scan %s)" % (rs_(off["amount_p"]), off["stamp"]))
        elif abs(M - P) <= 100:
            r.update(stage="do_return", hi="Marg mein %s ka &#8377;%s ka purchase return banaiye (dealer ke credit note se)." % (_esc_h(sup_name), _s740_hrs(A)),
                     en="Marg holds the full bill %s but no purchase return yet — Amir enters the purchase return %s." % (rs_(M), rs_(A)),
                     whose="Return: Amir enters it in Marg")
        else:
            r.update(stage="waiting", hi="Dealer ka credit note ya naya bill aane par hi Marg mein badlaav kijiye.",
                     en="Waiting for the dealer's paper: a revised bill or a credit note. Marg holds %s (the goods kept)." % rs_(M),
                     whose="Return: waiting for the dealer's paper")
        return
    mb = r.get("mb")
    if r["kind"] == "marg" and r.get("maybe_of"):              # the owner's question: the same credit note as a settled return's, or another?
        r.update(stage="check_same", hi="Yeh purchase return %s (&#8377;%s) Doctor sahab dekh rahe hain &mdash; abhi Marg mein kuch mat badaliye."
                 % (_esc_h(mb["bill_no"]), _s740_hrs(mb["size"])),
                 en="Purchase return %s (%s) came after the dealer took the same amount off a later bill for bill %s's return. The same credit "
                    "note? Then that return is in the books twice: Amir enters bill %s in full. Or another return?" % (
                     mb["bill_no"], rs_(mb["size"]), r.get("maybe_bill") or "", r.get("maybe_bill") or ""),
                 whose="You: the same return or another?")
        return
    if r["kind"] == "own" and mb is None:                     # goods gone, Marg not told: the purchase return comes first, whatever the dealer did
        what = "%s · %s" % (r.get("item") or "", _s740_qty_words(r.get("qty"), r.get("unit") or "pc"))
        r.update(stage="do_own", hi="Marg mein %s ka purchase return banaiye: %s." % (_esc_h(sup_name), _esc_h(what)),
                 en="Recorded by you (%s, %s): %s, about %s — Amir enters the purchase return." % (
                     "from the stock count" if r.get("source") == "count" else "by hand", ddmon(r["opened"]), what, rs_(A)),
                 whose="Return: Amir enters it in Marg")
        return
    _s740_mb_stage(r, mb, rowby, lk, "Settled: purchase return %s (%s) in Marg; its credit note is scanned and agrees." % (mb["bill_no"], rs_(mb["size"])),
                   cx, offs, used_off)


def _s740_adj(r, off, en_ok):
    """A return the dealer took off a later bill: settled only when Marg holds that later bill at the GOODS (its paper + what it took off) --
    the return is already in the books (net entry, or Marg's purchase return), so a net figure there would count it twice."""
    G = int(off["total_p"] or 0) + int(off["amount_p"] or 0)
    M = off.get("marg_p")
    r["adj"] = dict(scan=off["scan"], stamp=off["stamp"], bill_id=off.get("bill_id"), bill_no=off["bill_no"], goods_p=G, off_p=int(off["amount_p"]),
                    paper_p=int(off["total_p"] or 0), marg_p=M)
    if M is not None and abs(int(M) - G) <= _s740_tol(G):
        r.update(stage="resolved", road="adjusted", ref=off["stamp"], resolved=True, en="%s; Marg holds that bill at the goods' %s." % (en_ok, rs(G)))
    elif M is None:
        r.update(stage="do_goods", road="", ref="",
                 hi="%s ke bill %s mein dealer ne wapsi &#8377;%s ghatai hai. Yeh bill Marg mein &#8377;%s (poora maal) se daaliye."
                 % (_esc_h(r["supplier"]), _esc_h(off["bill_no"]), _s740_hrs(off["amount_p"]), _s740_hrs(G)),
                 en="The dealer took %s off bill %s (scan %s); that bill is not in Marg yet — Amir enters it at the goods' %s." % (
                     rs(off["amount_p"]), off["bill_no"], off["stamp"], rs(G)), whose="Return: Amir enters it in Marg")
    else:
        r.update(stage="do_goods", road="", ref="",
                 hi="%s ke bill %s mein dealer ne wapsi &#8377;%s ghatai hai. Marg mein yeh bill &#8377;%s (poora maal) kijiye &mdash; wapsi pehle se hisaab mein hai."
                 % (_esc_h(r["supplier"]), _esc_h(off["bill_no"]), _s740_hrs(off["amount_p"]), _s740_hrs(G)),
                 en="The dealer took %s off bill %s (scan %s); Marg holds %s — Amir sets it to the goods' %s (the return is already in the books)." % (
                     rs(off["amount_p"]), off["bill_no"], off["stamp"], rs(M), rs(G)), whose="Return: Amir enters it in Marg")


def _s740_mb_stage(r, mb, rowby, lk, en_ok, cx=None, offs=(), used_off=None):
    """The stage of a return whose purchase return is in Marg (mb): its paper scanned and agreeing settles it."""
    rs_ = rs
    paper_ok, x = _s740_paper_ok(rowby, lk, mb["id"])
    if paper_ok:
        off = None
        if cx is not None and used_off is not None:           # the credit note came AND the dealer printed "Less CN ..." on a later bill:
            off = _s740_pick_off(offs, used_off, lambda o: (o["bdate"] >= mb["date"] and billno(o["bill_no"], mb["bill_no"]) != "agree"   # that bill
                                 and o["scan"] != r.get("scan") and abs(o["amount_p"] - int(mb["size"])) <= _s740_tol(mb["size"])        # stays at
                                 and supplier(cx, o["vendor"], r["supplier"]) == "agree"), (mb["bill_no"], r.get("bill_no") or ""))       # the goods
        if off is not None:
            used_off.add(off["scan"])
            _s740_adj(r, off, en_ok.rstrip(".") + "; the dealer also took it off a later bill (scan %s)" % off["stamp"])
            if r.get("resolved"):
                r.update(road="credit", ref=mb["bill_no"])
            return
        r.update(stage="resolved", road="credit", ref=mb["bill_no"], resolved=True, en=en_ok)
    elif x is not None and x["state"] == "double":
        r.update(stage="double", hi="Yeh purchase return Marg mein do baar hai (%s) &mdash; upar ki list se ek entry hataiye." % _esc_h(mb["bill_no"]),
                 en="Purchase return %s is entered twice in Marg — Amir removes one (his correction list)." % mb["bill_no"],
                 whose=str(x.get("whose") or "Amir: a Marg correction"))
    elif x is not None and x["state"] == "amount_differs" and (x.get("agree") or {}).get("scan_p"):
        pp = abs(int((x.get("agree") or {}).get("scan_p") or 0))
        r.update(stage="do_amount", hi="Kaagaz dekh kar Marg mein purchase return %s theek kijiye: kaagaz par &#8377;%s, Marg mein &#8377;%s."
                 % (_esc_h(mb["bill_no"]), _s740_hrs(pp), _s740_hrs(mb["size"])),
                 en="Purchase return %s: its credit note reads %s, Marg %s — Amir checks the paper and corrects Marg." % (mb["bill_no"], rs_(pp), rs_(mb["size"])),
                 whose="Return: Amir enters it in Marg")
    elif x is not None and x.get("scan") is not None:
        r.update(stage="paper_check", hi="Wapsi Marg mein hai (purchase return %s); uske kaagaz ki jaanch baaki hai." % _esc_h(mb["bill_no"]),
                 en="Purchase return %s (%s): its paper is scanned and being checked — %s." % (mb["bill_no"], rs_(mb["size"]), x.get("whose") or "—"),
                 whose="Return: " + str(x.get("whose") or "being checked"))
    else:
        off = None
        if cx is not None and used_off is not None:           # no credit note: the dealer took it off a later bill instead
            d_ = max(mb["date"], r["date"])
            if r["kind"] == "own":                                # the dealer may take it off before Amir enters the purchase return
                d_ = ((_date(str(r.get("cut") or r["date"])[:10]) or today()) - dt.timedelta(days=45)).isoformat()
            off = _s740_pick_off(offs, used_off, lambda o: ((o["bdate"] > d_ or (o["bdate"] == d_ and billno(o["bill_no"], mb["bill_no"]) == "differ"
                                                                                 and (not r.get("bill_no") or billno(o["bill_no"], r["bill_no"]) == "differ")))
                                 and billno(o["bill_no"], mb["bill_no"]) != "agree" and o["scan"] != r.get("scan")
                                 and abs(o["amount_p"] - int(mb["size"])) <= _s740_tol(mb["size"])
                                 and supplier(cx, o["vendor"], r["supplier"]) == "agree"), (mb["bill_no"], r.get("bill_no") or ""))
        if off is not None:
            used_off.add(off["scan"])
            _s740_adj(r, off, "Settled: purchase return %s (%s) in Marg; the dealer took it off a later bill (scan %s)" % (mb["bill_no"], rs_(mb["size"]), off["stamp"]))
            return
        r.update(stage="paper", hi="Wapsi Marg mein hai (purchase return %s). Dealer ka kaagaz (credit note) scan hona baaki hai." % _esc_h(mb["bill_no"]),
                 en="Purchase return %s (%s) is in Marg; its paper (the credit note) is to be scanned — reception." % (mb["bill_no"], rs_(mb["size"])),
                 whose="Return: reception scans the credit note")


def _esc_h(s):
    return esc(str(s or ""))


def _s740_hrs(p):
    """Rupees for a Hindi line (no currency sign: the caller writes it)."""
    t = rs(abs(int(p or 0)))
    return t.replace("₹", "")


def _s740_questions(con, ans, rowby):
    """Reception's one question: the bills whose paper reads MORE than Marg and are Amir's correction (S738's 'more', read from the register as
    it stands before this section -- never through s738_fixes, which reads the register this section wraps) with no answer yet."""
    out = []
    for bid, x in sorted(rowby.items(), key=lambda z: (str(z[1].get("date") or ""), z[0])):
        if x["state"] != "amount_differs" or not str(x.get("whose") or "").startswith("Amir"):
            continue
        ag = x.get("agree") or {}
        paper, marg = ag.get("scan_p"), int(x.get("amount_p") or 0)
        if paper in (None, 0) or marg <= 0 or int(paper) <= marg:
            continue
        b = con.execute("SELECT supplier_norm, bill_no, bill_date, month FROM purchase_bill WHERE id=?", (int(bid),)).fetchone()
        if b is None or (str(b[0]), _s740_nl(b[1]), str(b[2])) in ans:
            continue
        out.append(dict(bill_id=int(bid), supplier=x["supplier"], bill_no=str(x["bill_no"] or ""), date=str(x.get("date") or "")[:10],
                        paper_p=int(paper), marg_p=marg, diff_p=int(paper) - marg, scan=x.get("scan"), stamp=x.get("stamp") or "",
                        month=str(b[3] or str(b[2])[:7])))
    return out


def _s740_no_answers(con, ans, qrows):
    """Reception's "Nahi" on a bill whose paper still reads more than Marg (the owner may undo a wrong one)."""
    out = []
    for bid, x in qrows.items():
        if x["state"] != "amount_differs":
            continue
        b = con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE id=?", (int(bid),)).fetchone()
        a = ans.get((str(b[0]), _s740_nl(b[1]), str(b[2]))) if b is not None else None
        if a and a["answer"] == "no":
            out.append(dict(bill_id=int(bid), supplier=x["supplier"], bill_no=str(x["bill_no"] or ""), date=str(x.get("date") or "")[:10],
                            paper_p=a["paper_p"], marg_p=int(x.get("amount_p") or 0), by=a["by"], at=a["at"], month=str(x.get("date") or "")[:7]))
    return out


def _s740_flags(con):
    """The count shortages that may be returns with no paper: a whole strip / box short, of an item bought in the last 180 days from ONE dealer
    only, not answered, not already recorded. READ ONLY. Built for the owner's row and his tap only (never inside the model): one read of
    the open loss lines, one grouped read of their items' purchases."""
    out = []
    answered = {int(r["loss_id"]) for r in _s740_rows(con, "SELECT loss_id FROM s740_flag")} | {
        int(r["loss_id"]) for r in _s740_rows(con, "SELECT loss_id FROM s740_own WHERE loss_id IS NOT NULL")}
    lines = []
    for l in _s740_rows(con, "SELECT id, at, item, gap_units, pack, packing FROM stock_watch_loss_line WHERE void_at IS NULL AND at >= ? ORDER BY id",
                        (S740_FLAG_FROM,)):
        if int(l["id"]) in answered:
            continue
        pack = int(l.get("pack") or 1) or 1
        gap = float(l.get("gap_units") or 0)
        if gap < pack or abs(gap / pack - round(gap / pack)) > 1e-9:
            continue
        lines.append(dict(l, pack=pack, gap=gap))
    if not lines:
        return out
    items = sorted({_s740_nl(l["item"]) for l in lines})
    d_min = min(((_date(str(l["at"])[:10]) or today()) - dt.timedelta(days=S740_FLAG_DAYS)).isoformat() for l in lines)
    minus = {(str(r["supplier_norm"]), _s740_nl(r["bill_no"]), str(r["bill_date"])) for r in
             _s740_rows(con, "SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE amount_p<0")}
    bought = {}
    for i0 in range(0, len(items), 300):
        part = items[i0:i0 + 300]
        for r in _s740_rows(con, "SELECT lower(trim(item)) AS it, supplier_norm, bill_no, bill_date, rate_p, packing FROM purchase_line WHERE bill_date>=? "
                                 "AND lower(trim(item)) IN (%s) ORDER BY bill_date" % ",".join("?" * len(part)), [d_min] + part):
            if (str(r["supplier_norm"]), _s740_nl(r["bill_no"]), str(r["bill_date"])) in minus:
                continue
            bought.setdefault(r["it"], []).append(r)
    for l in lines:
        day = str(l["at"])[:10]
        d0 = ((_date(day) or today()) - dt.timedelta(days=S740_FLAG_DAYS)).isoformat()
        rows = [r for r in bought.get(_s740_nl(l["item"]), []) if d0 <= str(r["bill_date"]) <= day]
        sups = {str(r["supplier_norm"]) for r in rows}
        if len(sups) != 1:
            continue
        sup = sups.pop()
        last = rows[-1]
        rate = int(last["rate_p"] or 0)
        unit = _s740_unit(last["packing"] or l.get("packing"))
        qty = l["gap"] / (l["pack"] if unit == "strip" else 1)
        out.append(dict(loss_id=int(l["id"]), at=str(l["at"]), item=l["item"], gap=l["gap"], pack=l["pack"], qty=qty, unit=unit, sup=sup,
                        supplier=_pa().supplier_key(sup), last_no=str(last["bill_no"] or ""), last_date=str(last["bill_date"] or ""),
                        est_p=int(round(rate * qty))))
    return out


def _s740_already(con, sup, item, since_day, model=None):
    """A purchase return of this dealer carrying this item that reached the server on or after since_day and stands as a return of its own
    (Amir entered it from a slip) -> its bill no. | ''. An older return is another return."""
    m = model or s740_model(con)
    for r in m["returns"]:
        if r["kind"] != "marg" or r["sup"] != str(sup):
            continue
        b = con.execute("SELECT first_seen_day, bill_date FROM purchase_bill WHERE id=?", (int(r["bill_id"]),)).fetchone()
        if b is None or str(b[0] or b[1] or "")[:10] < str(since_day)[:10]:
            continue
        if _s740_rows(con, "SELECT 1 FROM purchase_line WHERE supplier_norm=? AND lower(trim(bill_no))=? AND bill_date=? AND lower(trim(item))=? LIMIT 1",
                      (r["sup"], _s740_nl(r["bill_no"]), r["date"], _s740_nl(item))):
            return r["bill_no"]
    return ""


# ------------------------------------------------------------------ writes (each audited; each commits)
def s740_answer_put(con, who, bill_id, yes):
    """Reception's answer to "Bill par ya parchi par wapsi likhi hai?" -- only for a bill now on the question list. -> (ok, message)."""
    s740_ensure(con)
    m = s740_model(con)
    q = next((x for x in m["questions"] if int(x["bill_id"]) == int(bill_id)), None)
    if q is None:
        return False, "Yeh sawaal ab list par nahi hai."
    b = con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE id=?", (int(bill_id),)).fetchone()
    now = _s740_now()
    try:
        con.execute("INSERT INTO s740_answer (sup, bill_no, bill_date, answer, paper_p, marg_p, ret_p, by, at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (str(b[0]), _s740_nl(b[1]), str(b[2]), "yes" if yes else "no", q["paper_p"], q["marg_p"], q["diff_p"], who, now))
    except sqlite3.IntegrityError:
        con.rollback()
        return False, "Is bill ka jawab pehle hi diya ja chuka hai."
    _pa()._audit(con, who, "s740_answer", int(bill_id), dict(answer="yes" if yes else "no", paper=q["paper_p"], marg=q["marg_p"], kit=KIT_S740))
    con.commit()
    return True, ""


def s740_seed(con, sup, bill_no, bill_date, who, why):
    """The owner's own word for a bill already known (Janta 21965, D839): answered 'yes' as reception would. Idempotent. -> 'seeded' | 'already'
    | 'not_a_question' (the bill is not on the question list now: nothing written)."""
    if (str(sup), _s740_nl(bill_no), str(bill_date)) in _s740_answers(con):
        return "already"
    b = con.execute("SELECT b.id FROM purchase_bill b WHERE b.supplier_norm=? AND lower(trim(b.bill_no))=? AND b.bill_date=? AND " + _pa().EFF_BILL,
                    (sup, _s740_nl(bill_no), bill_date)).fetchone()
    if b is None:
        return "not_a_question"
    q = next((x for x in s740_model(con)["questions"] if int(x["bill_id"]) == int(b[0])), None)
    if q is None:
        return "not_a_question"
    s740_ensure(con)
    con.execute("INSERT INTO s740_answer (sup, bill_no, bill_date, answer, paper_p, marg_p, ret_p, by, at) VALUES (?,?,?,?,?,?,?,?,?)",
                (str(sup), _s740_nl(bill_no), str(bill_date), "yes", q["paper_p"], q["marg_p"], q["diff_p"], who, _s740_now()))
    _pa()._audit(con, who, "s740_answer", int(b[0]), dict(answer="yes", seed=why, kit=KIT_S740))
    con.commit()
    return "seeded"


def s740_undo_answer(con, who, bill_id):
    """The owner: a wrong answer is undone -- the question goes back to reception. -> (ok, message)."""
    s740_ensure(con)
    b = con.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE id=?", (int(bill_id),)).fetchone()
    if b is None:
        return False, "No such bill."
    cur = con.execute("UPDATE s740_answer SET undone_at=?, undone_by=? WHERE sup=? AND bill_no=? AND bill_date=? AND undone_at IS NULL",
                      (_s740_now(), who, str(b[0]), _s740_nl(b[1]), str(b[2])))
    if not cur.rowcount:
        return False, "Nothing to undo."
    con.execute("DELETE FROM s740_answer WHERE sup=? AND bill_no=? AND bill_date=? AND undone_at IS NOT NULL", (str(b[0]), _s740_nl(b[1]), str(b[2])))
    _pa()._audit(con, who, "s740_answer_undone", int(bill_id), dict(kit=KIT_S740))
    con.commit()
    return True, ""


def s740_flag_put(con, who, loss_id, yes):
    """The owner's answer on a count shortage: yes -> a pending return of his own (from the count); no -> a stock loss, as now."""
    s740_ensure(con)
    f = next((x for x in _s740_flags(con) if int(x["loss_id"]) == int(loss_id)), None)
    if f is None:
        return False, "This line is no longer open."
    now = _s740_now()
    already = _s740_already(con, f["sup"], f["item"], f["at"]) if yes else ""
    try:                                                      # the flag first: a second tap at once is refused here
        con.execute("INSERT INTO s740_flag (loss_id, answer, by, at) VALUES (?,?,?,?)",
                    (int(loss_id), ("in_marg:" + already) if already else ("yes" if yes else "no"), who, now))
    except sqlite3.IntegrityError:
        con.rollback()
        return False, "This line is already answered."
    if yes and not already:
        con.execute("INSERT INTO s740_own (sup, supplier, item, qty, unit, est_p, source, loss_id, by, at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (f["sup"], f["supplier"], f["item"], f["qty"], f["unit"], f["est_p"], "count", int(loss_id), who, now))
    _pa()._audit(con, who, "s740_count_flag", int(loss_id), dict(answer="yes" if yes else "no", in_marg=already, item=f["item"], supplier=f["sup"],
                                                                kit=KIT_S740))
    con.commit()
    if already:
        return True, "Already in Marg as purchase return %s -- nothing more to enter; it shows under Returns." % already
    return True, ""


def s740_choices(con, sup=None):
    """For "Record a return": the dealers bought from in the last 365 days, or (sup given) the items bought from that dealer with the last
    rate and the unit. READ ONLY."""
    d0 = (today() - dt.timedelta(days=365)).isoformat()
    if not sup:
        return [dict(sup=str(r["supplier_norm"] if isinstance(r, dict) else r[0]), name=_pa().supplier_key(r["supplier_norm"] if isinstance(r, dict) else r[0]))
                for r in _s740_rows(con, "SELECT DISTINCT supplier_norm FROM purchase_bill WHERE amount_p>0 AND bill_date>=? ORDER BY supplier_norm", (d0,))]
    out = []
    for r in _s740_rows(con, "SELECT item, MAX(bill_date) AS d FROM purchase_line WHERE supplier_norm=? AND bill_date>=? GROUP BY lower(trim(item)) "
                             "ORDER BY item", (sup, d0)):
        item = r["item"] if isinstance(r, dict) else r[0]
        rate, packing = _s740_last_rate(con, sup, item)
        if rate:
            out.append(dict(item=item, rate_p=rate, unit=_s740_unit(packing)))
    return out


def s740_record(con, who, sup, item, qty):
    """The owner's "Record a return": dealer, item and quantity are PICKED (never typed); the value is the last purchase rate x qty."""
    s740_ensure(con)
    try:
        qty = float(qty)
    except (TypeError, ValueError):
        return False, "Pick a quantity."
    if qty != qty or qty in (float("inf"), float("-inf")) or qty <= 0 or qty > 999 or qty != int(qty):
        return False, "Pick a quantity."
    if sup not in {c["sup"] for c in s740_choices(con)}:
        return False, "Pick a dealer from the list."
    ch = next((c for c in s740_choices(con, sup) if c["item"] == item), None)
    if ch is None:
        return False, "Pick an item from the list."
    now = _s740_now()
    already = _s740_already(con, sup, item, (today() - dt.timedelta(days=7)).isoformat())
    if already:
        return False, "Already in Marg as purchase return %s -- it shows under Returns; nothing to record." % already
    d10 = (dt.datetime.fromisoformat(now) - dt.timedelta(minutes=10)).isoformat()
    if con.execute("SELECT 1 FROM s740_own WHERE sup=? AND item=? AND qty=? AND withdrawn_at IS NULL AND at>=?", (sup, item, qty, d10)).fetchone():
        return False, "This return was recorded a moment ago."
    cur = con.execute("INSERT INTO s740_own (sup, supplier, item, qty, unit, est_p, source, loss_id, by, at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (sup, _pa().supplier_key(sup), item, qty, ch["unit"], int(round(ch["rate_p"] * qty)), "record", None, who, now))
    _pa()._audit(con, who, "s740_record", cur.lastrowid, dict(supplier=sup, item=item, qty=qty, kit=KIT_S740))
    con.commit()
    return True, ""


def s740_cn_look(con, who, bill_id):
    """The owner looked at a purchase return's credit note: the scan misread it, its paper is Marg's figure. Only for a return now on Amir's
    card as 'correct the amount'. -> (ok, message)."""
    x = next((r for r in s740_pending(con) if r.get("stage") == "do_amount" and r.get("mb") and int(r["mb"]["id"]) == int(bill_id)), None)
    if x is None:
        return False, "This line is no longer open."
    b = con.execute("SELECT amount_p FROM purchase_bill WHERE id=?", (int(bill_id),)).fetchone()
    s740_ensure(con)
    try:
        con.execute("INSERT INTO s740_cn_look (bill_id, marg_p, scan_p, by, at) VALUES (?,?,?,?,?)", (int(bill_id), int(b[0]), None, who, _s740_now()))
    except sqlite3.IntegrityError:
        con.rollback()
        return False, "Already looked at."
    _pa()._audit(con, who, "s740_cn_look", int(bill_id), dict(marg=int(b[0]), kit=KIT_S740))
    con.commit()
    return True, ""


def s740_same_put(con, who, bill_id, is_same):
    """The owner's answer on a purchase return that came after a settled return's deduction: the same credit note (that return then claims it:
    Amir enters its bill in full) or another return (its own). -> (ok, message)."""
    x = next((r for r in s740_pending(con) if r.get("stage") == "check_same" and int(r["bill_id"]) == int(bill_id)), None)
    if x is None:
        return False, "This line is no longer open."
    s740_ensure(con)
    try:
        con.execute("INSERT INTO s740_same (bill_id, answer, rkey, by, at) VALUES (?,?,?,?,?)",
                    (int(bill_id), "same" if is_same else "other", x["maybe_of"], who, _s740_now()))
    except sqlite3.IntegrityError:
        con.rollback()
        return False, "Already answered."
    _pa()._audit(con, who, "s740_same", int(bill_id), dict(answer="same" if is_same else "other", rkey=x["maybe_of"], kit=KIT_S740))
    con.commit()
    return True, ""


def s740_withdraw(con, who, own_id):
    """The owner withdraws a return he recorded (recorded by mistake)."""
    s740_ensure(con)
    cur = con.execute("UPDATE s740_own SET withdrawn_at=?, withdrawn_by=? WHERE id=? AND withdrawn_at IS NULL", (_s740_now(), who, int(own_id)))
    if not cur.rowcount:
        return False, "Nothing to withdraw."
    _pa()._audit(con, who, "s740_withdraw", int(own_id), dict(kit=KIT_S740))
    con.commit()
    return True, ""


def s740_sync(con, model=None, now=None):
    """Keeps s740_track in step: a return first seen / resolved (the road and the paper) / open again / gone; last_seen once a day. Writes only
    s740_track and audit rows, and only what changed; commits when it wrote. Nothing when the scans could not be read (a scan database that
    is down must not flip a resolved return). -> (new, resolved, gone)."""
    model = model or s740_model(con)
    if not model.get("assets_ok", True):
        return 0, 0, 0
    has = con.execute("SELECT 1 FROM sqlite_master WHERE name='s740_track'").fetchone() is not None
    if not has and not model["returns"]:
        return 0, 0, 0
    s740_ensure(con)
    now = now or _s740_now()
    day = now[:10]
    have = {str(r[0]): dict(resolved_at=r[1], gone_at=r[2], last_seen=r[3], road=r[4], ref=r[5], off_ref=r[6]) for r in
            con.execute("SELECT rkey, resolved_at, gone_at, last_seen, road, ref, off_ref FROM s740_track")}
    before = con.total_changes
    cur_keys, new, res, gone = set(), 0, 0, 0
    for r in model["returns"]:
        k = r["key"]
        cur_keys.add(k)
        h = have.get(k)
        off_ref = (r.get("adj") or {}).get("stamp")
        if h is None:
            con.execute("INSERT INTO s740_track (rkey, kind, month, first_seen, last_seen, resolved_at, road, ref, off_ref) VALUES (?,?,?,?,?,?,?,?,?)",
                        (k, r["kind"], r["month"], now, now, now if r["resolved"] else None, r["road"] or None, r["ref"] or None, off_ref))
            new += 1
            res += 1 if r["resolved"] else 0
            continue
        if r["resolved"] and (not h["resolved_at"] or h["gone_at"]):
            con.execute("UPDATE s740_track SET last_seen=?, resolved_at=?, road=?, ref=?, off_ref=?, gone_at=NULL WHERE rkey=?",
                        (now, now, r["road"], r["ref"], off_ref, k))
            _pa()._audit(con, "server", "s740_resolved", k, dict(road=r["road"], ref=r["ref"], kit=KIT_S740))
            res += 1
        elif r["resolved"] and (str(h.get("road") or "") != str(r["road"] or "") or str(h.get("ref") or "") != str(r["ref"] or "")
                                or (off_ref and str(h.get("off_ref") or "") != str(off_ref))):
            con.execute("UPDATE s740_track SET last_seen=?, road=?, ref=?, off_ref=COALESCE(?, off_ref) WHERE rkey=?",
                        (now, r["road"], r["ref"], off_ref, k))   # settled another way now (a tied deduction is never let go)
            _pa()._audit(con, "server", "s740_resettled", k, dict(road=r["road"], ref=r["ref"], was_road=h.get("road"), was_ref=h.get("ref"), kit=KIT_S740))
        elif not r["resolved"] and (h["resolved_at"] or h["gone_at"]):
            con.execute("UPDATE s740_track SET last_seen=?, resolved_at=NULL, road=NULL, ref=NULL, off_ref=?, gone_at=NULL WHERE rkey=?", (now, off_ref, k))
            if h["resolved_at"]:
                _pa()._audit(con, "server", "s740_reopened", k, dict(was_road=h.get("road"), was_ref=h.get("ref"), kit=KIT_S740))
        elif off_ref and str(h.get("off_ref") or "") != str(off_ref):
            con.execute("UPDATE s740_track SET last_seen=?, off_ref=? WHERE rkey=?", (now, off_ref, k))   # a deduction tied while pending
        elif str(h["last_seen"] or "")[:10] != day:
            con.execute("UPDATE s740_track SET last_seen=? WHERE rkey=?", (now, k))
    for k, h in have.items():
        if k not in cur_keys and not h["gone_at"]:
            con.execute("UPDATE s740_track SET gone_at=? WHERE rkey=?", (now, k))
            gone += 1
    if con.total_changes != before:
        con.commit()
    return new, res, gone


def s740_tracked(con):
    try:
        return {str(r[0]): dict(first_seen=r[1], resolved_at=r[2], road=r[3], ref=r[4], gone_at=r[5], off_ref=r[6]) for r in
                con.execute("SELECT rkey, first_seen, resolved_at, road, ref, gone_at, off_ref FROM s740_track")}
    except sqlite3.Error:
        return {}


def s740_pending(con):
    """The pending returns (every open month) -- what Amir's page and the owner's row carry."""
    return [r for r in s740_model(con)["returns"] if not r["resolved"]]


# ------------------------------------------------------------------ the register knows a return when it sees one
_agree_before_s740 = agree


def agree(cx, s, b):                                          # noqa: F811 -- S740: a minus bill (a purchase return) is compared by its size
    try:
        mp = int(b["amount_p"] or 0)
    except (KeyError, TypeError, ValueError, IndexError):
        mp = 0
    if mp < 0:
        b = dict(b)
        b["amount_p"] = -mp
        s = dict(s)
        for k in ("amount_p", "total_amount"):
            try:
                if s.get(k) is not None and float(s[k]) < 0:
                    s[k] = -s[k]
            except (TypeError, ValueError):
                pass
        sid = int(s["id"]) if s.get("id") is not None else None
        if sid is not None and sid in getattr(cx, "paper", {}) and (cx.paper.get(sid) or 0) < 0:
            cx = _S740Cx(cx, sid)
    return _agree_before_s740(cx, s, b)


class _S740Cx(object):
    """A Ctx whose one paper amount (a credit note's, typed with its minus) is read by its size."""

    def __init__(self, cx, sid):
        self._cx = cx
        self.paper = dict(cx.paper)
        self.paper[sid] = -self.paper[sid]

    def __getattr__(self, k):
        return getattr(self._cx, k)


_register_before_s740 = register


import threading as _s740_threading                        # noqa: E402
_S740_T = _s740_threading.local()                             # per worker thread: the re-entry guard and the step view's context


def register(con, month):                                     # noqa: F811 -- S740: a return's rows say whose they are
    r = _register_before_s740(con, month)
    if getattr(_S740_T, "inside", False):                     # never inside its own model (no re-entry)
        return r
    _S740_T.inside = True
    try:
        _s740_overlay(con, r)
    except Exception as e:                                    # noqa: BLE001 -- the register stands as it was
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S740 overlay: %r" % (e,), file=_sys.stderr)
    finally:
        _S740_T.inside = False
    return r


def _s740_overlay(con, r):
    try:
        has = con.execute("SELECT 1 FROM sqlite_master WHERE name='s740_answer'").fetchone() is not None
    except sqlite3.Error:
        has = False
    minus = any(int(x.get("amount_p") or 0) < 0 for x in r["rows"])
    if not has and not minus:
        return
    by, later = {}, {}
    if has or minus:
        for x in s740_model(con)["returns"]:
            if x.get("bill_id") is not None and x["kind"] in ("on_bill", "marg"):
                by[int(x["bill_id"])] = x
            if x.get("mb"):
                by.setdefault(int(x["mb"]["id"]), x)
            if x.get("adj") and x["adj"].get("bill_id") is not None:
                later[int(x["adj"]["bill_id"])] = x
    changed = False
    for row in r["rows"]:
        lx = later.get(int(row["id"]))
        if lx is not None:                                    # the dealer's later bill that took a return off: Marg keeps its goods
            a = lx["adj"]
            row["note"] = ("The dealer took return %s (%s) off this bill; Marg keeps the goods' %s. " % (lx.get("bill_no") or (lx.get("mb") or {}).get("bill_no") or "",
                                                                                                  rs(a["off_p"]), rs(a["goods_p"]))) + (row.get("note") or "")
            at_goods = a.get("marg_p") is not None and abs(int(a["marg_p"]) - int(a["goods_p"])) <= _s740_tol(a["goods_p"])
            if lx["resolved"] or at_goods:                    # held at the goods: nothing to do on THIS bill
                if row["state"] not in S740_SETTLED:
                    row["state"] = "has_scan"
                    changed = True
                row["whose"] = "Nobody"
            else:
                if row["state"] in S740_SETTLED:
                    row["state"] = "amount_differs"
                    changed = True
                row["whose"] = "Return: Amir enters it in Marg"
            continue
        x = by.get(int(row["id"]))
        neg = int(row.get("amount_p") or 0) < 0
        if x is None and not neg:
            continue
        if x is not None and x["kind"] == "on_bill" and int(x["bill_id"]) == int(row["id"]):
            lead = "A return of %s is written on the paper (%s, %s). " % (rs(x["amount_p"]), x.get("by") or "reception", ddmon(x["opened"]))
            if x["resolved"]:
                if row["state"] not in S740_SETTLED:
                    row["state"] = "has_scan"
                    changed = True
                row["whose"] = "Nobody"
            else:
                row["whose"] = x.get("whose") or "Return: waiting for the dealer's paper"
            row["note"] = lead + x.get("en", "") + ((" " + row["note"]) if row.get("note") else "")
            row["s740"] = x["key"]
            continue
        if neg:
            if x is not None and x["resolved"] and row["state"] == "amount_differs":
                row["state"], row["whose"] = "has_scan", "Nobody"       # the owner looked: the credit note was misread
                changed = True
            row["note"] = "Purchase return (Marg). " + (row.get("note") or "")
            if x is not None and x.get("stage") == "do_amount":
                row["whose"] = "Return: Amir enters it in Marg"   # S740's own card carries it (never S738's twice)
            if x is not None:
                row["s740"] = x["key"]
    if changed:
        r["counts"] = {k: sum(1 for z in r["rows"] if z["state"] == k) for k in STATES}
        r["settled"] = r["counts"]["verified"] + r["counts"]["has_scan"] + r["counts"]["accepted"]


# ------------------------------------------------------------------ the owner's step view: row 8 "Returns"
S740_CSS = """
#s740rt .s740l{display:flex;flex-wrap:wrap;gap:4px 10px;align-items:baseline;padding:8px 0 2px;border-top:1px solid #e3e6ec}
#s740rt .s740l + .s740m{margin-bottom:2px}
#s740rt .s740k{font-weight:700}#s740rt .s740m{color:#5b5b5b;font-size:13px}
#s740rt .s740p{display:inline-block;border-radius:999px;padding:1px 8px;font-size:12px;font-weight:700;background:#fbf0dc;color:#8a5300}
#s740rt .s740d{background:#e3f3e7;color:#1d6b33}
#s740rt button{font:inherit;font-size:14px;border-radius:8px;padding:6px 12px;min-height:38px;margin:4px 6px 6px 0;border:1px solid #1f3864;background:#fff;color:#1f3864;cursor:pointer}
#s740rt button.s740y{background:#1f3864;color:#fff}
#s740rt select{font:inherit;font-size:14px;width:100%;max-width:420px;padding:6px}
#s740rec .s740q button{min-width:40px;min-height:40px;font-size:18px}
details[data-row="8"] summary{color:inherit}
#s740rec{display:flex;flex-direction:column;gap:6px;border:1px dashed #b8c2d6;border-radius:10px;padding:8px 10px;margin-top:4px}
#s740rec .s740q{display:flex;gap:8px;align-items:center}
"""
S740_JS = """<script>
async function s740post(btn,u,b){if(btn){if(btn.disabled)return;btn.disabled=true;}
try{const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b||{})});
const j=await r.json().catch(()=>({}));if(!r.ok||!j.ok){alertBox(j.message||j.error||('HTTP '+r.status));if(btn)btn.disabled=false;return;}
if(j.message){alertBox(j.message);}setTimeout(function(){location.reload();},j.message?1800:0);}catch(e){alertBox(String(e));if(btn)btn.disabled=false;}}
function alertBox(t){var m=document.getElementById('s740msg');if(m){m.textContent=t;m.style.display='block';}}
async function s740sup(sel){var it=document.getElementById('s740item');it.innerHTML='<option value="">Item…</option>';s740q(0,true);
if(!sel.value){return;}try{const r=await fetch(sel.dataset.u+'?supplier='+encodeURIComponent(sel.value));const j=await r.json();
(j.items||[]).forEach(function(x){var o=document.createElement('option');o.value=x.item;o.textContent=x.item;o.dataset.rate=x.rate_p;o.dataset.unit=x.unit;it.appendChild(o);});}catch(e){alertBox(String(e));}}
function s740q(d,reset){var q=document.getElementById('s740qty');var n=reset?1:Math.max(1,Math.min(999,parseInt(q.dataset.n||'1')+d));q.dataset.n=n;
var it=document.getElementById('s740item');var o=it.options[it.selectedIndex];var u=(o&&o.dataset.unit)||'pc';
q.textContent=n+' '+(n==1?u:u+'s');var v=document.getElementById('s740val');
if(o&&o.dataset.rate){var p=Math.round(parseInt(o.dataset.rate)*n);v.textContent='About ₹'+(p/100).toLocaleString('en-IN',{maximumFractionDigits:0})+' at the last purchase rate';}else{v.textContent='';}}
function s740rec(u){var s=document.getElementById('s740sup').value,i=document.getElementById('s740item').value,n=parseInt(document.getElementById('s740qty').dataset.n||'1');
if(!s||!i){alertBox('Pick the dealer and the item.');return;}s740post(document.getElementById('s740go'),u,{supplier:s,item:i,qty:n});}
</script>"""


def _s740_line(con, x, tr, owner_buttons, prefix):
    t = tr.get(x["key"]) or {}
    since = _s738_dm(t.get("first_seen") or x["opened"])
    if x["kind"] == "on_bill":
        head = "%s %s · %s" % (esc(x["supplier"]), esc(x["bill_no"]), esc(_s738_dmy(x["date"])))
        what = "Return %s written on the bill" % esc(rs(x["amount_p"]))
    elif x["kind"] == "own":
        head = "%s · %s · %s" % (esc(x["supplier"]), esc(x.get("item") or ""), esc(_s740_qty_words(x.get("qty"), x.get("unit") or "pc")))
        what = "Recorded by you (%s) · about %s" % ("stock count" if x.get("source") == "count" else "by hand", esc(rs(x["amount_p"])))
    else:
        head = "%s · purchase return %s · %s" % (esc(x["supplier"]), esc(x["bill_no"]), esc(_s738_dmy(x["date"])))
        what = "Sent back from stock · %s" % esc(rs(x["amount_p"]))
    if x["resolved"]:
        st = '<span class="s740p s740d">resolved %s</span>' % esc(_s738_dm(t.get("resolved_at")) if t.get("resolved_at") else "")
        whose = ""
    else:
        st = '<span class="s740p">pending</span>'
        whose = '<span class="s740m">%s · since %s</span>' % (esc(x.get("whose") or ""), esc(since))
    btn = ""
    if owner_buttons and not x["resolved"]:
        if x["kind"] == "own":
            btn = '<button onclick="s740post(this,\'%s/api/s740/withdraw\',{id:%d})">Withdraw (recorded by mistake)</button>' % (esc(prefix), x["own_id"])
        elif x.get("stage") == "check_same":
            btn = ('<button class="s740y" onclick="s740post(this,\'%s/api/s740/same\',{bill:%d,same:true})">The same return — Amir enters bill %s in full</button>'
                   '<button onclick="s740post(this,\'%s/api/s740/same\',{bill:%d,same:false})">Another return</button>'
                   % (esc(prefix), int(x["bill_id"]), esc(x.get("maybe_bill") or ""), esc(prefix), int(x["bill_id"])))
        elif x.get("stage") == "do_amount" and x.get("mb"):
            btn = ('<button onclick="s740post(this,\'%s/api/s740/cnlook\',{bill:%d})">The scan misread — the paper is Marg\'s %s</button>'
                   % (esc(prefix), int(x["mb"]["id"]), esc(rs(x["mb"]["size"]))))
        elif x["kind"] == "on_bill" and x.get("stage") == "waiting":
            btn = '<button onclick="s740post(this,\'%s/api/s740/undo\',{bill:%d})">Undo the answer (ask reception again)</button>' % (esc(prefix), x["bill_id"])
    view = _s738_viewer(int(x["scan"])) if x.get("scan") is not None else ""
    return ('<div class="s740l" data-s740="%s"><span class="s740k">%s</span><span>%s</span>%s%s</div><div class="s740m">%s</div>%s%s'
            % (esc(x["key"]), head, what, st, whose, esc(x.get("en") or ""), btn, view))


def s740_owner_row(con, month, prefix, model=None):
    """(label, n text, lines, grey) -- row 8 of the step view: the returns of this month (pending and resolved) and every earlier month's still
    pending; the count shortages to answer; the Record-a-return form; a dealer's return line no return matches. READ ONLY."""
    m = model or s740_model(con)
    tr = s740_tracked(con)
    mine = [x for x in m["returns"] if (x["month"] == month) or (x["month"] < month and not x["resolved"])]
    pend = [x for x in mine if not x["resolved"]]
    lines = ['<div id="s740rt"><div id="s740msg" class="mut" style="display:none;color:#8c1d18"></div>']    # joined into ONE line below
    for x in sorted(mine, key=lambda z: (z["resolved"], z["month"], z["date"])):
        lines.append(_s740_line(con, x, tr, True, prefix))
    for a in [a for a in m.get("no_answers") or [] if a["month"] <= month]:
        lines.append('<div class="s740l" data-s740no="%d"><span class="s740k">Reception said: no return written</span><span>%s %s · %s · paper %s, Marg %s'
                     '</span></div><div class="s740m">%s, %s. Amir is asked to add the missing lines. If a return was written, undo the answer.</div>'
                     '<div class="s740l"><button onclick="s740post(this,\'%s/api/s740/undo\',{bill:%d})">Undo the answer (ask reception again)</button></div>'
                     % (a["bill_id"], esc(a["supplier"]), esc(a["bill_no"]), esc(_s738_dmy(a["date"])), esc(rs(a["paper_p"])), esc(rs(a["marg_p"])),
                        esc(a["by"] or ""), esc(ddmon(a["at"])), esc(prefix), a["bill_id"]))
    flags = _s740_flags(con)
    for f in flags:
        lines.append('<div class="s740l" data-s740flag="%d"><span class="s740k">Possibly returned — no paper</span><span>%s · %s short at the count of %s</span>'
                     '</div><div class="s740m">Bought only from %s in the last %d days (last bill %s, %s). Was it returned to %s?</div>'
                     '<div class="s740l"><button class="s740y" onclick="s740post(this,\'%s/api/s740/flag\',{loss:%d,yes:true})">Yes, returned to %s</button>'
                     '<button onclick="s740post(this,\'%s/api/s740/flag\',{loss:%d,yes:false})">No, a stock loss</button></div>'
                     % (f["loss_id"], esc(f["item"]), esc(_s740_qty_words(f["qty"], f["unit"])), esc(ddmon(f["at"])), esc(f["supplier"]), S740_FLAG_DAYS,
                        esc(f["last_no"] or "—"), esc(ddmon(f["last_date"]) if f["last_date"] else "—"), esc(f["supplier"]), esc(prefix), f["loss_id"],
                        esc(f["supplier"]), esc(prefix), f["loss_id"]))
    for o in [o for o in m["adjusted"] if str(o.get("bdate") or "")[:7] == month]:
        lines.append('<div class="s740l"><span class="s740k">A dealer\'s bill takes off a return</span><span>%s · scan %s · %s</span></div>'
                     '<div class="s740m">No pending return matches it. If goods went back, record the return below.</div>%s'
                     % (esc(o.get("supplier") or o["vendor"]), esc(o["stamp"]), esc(rs(o["amount_p"])), _s738_viewer(o["scan"])))
    opts = "".join('<option value="%s">%s</option>' % (esc(c["sup"]), esc(c["name"])) for c in s740_choices(con))
    lines.append('<div id="s740rec"><b>Record a return</b><span class="s740m">When you hear of a return first. Everything is picked; nothing is typed.</span>'
                 '<select id="s740sup" data-u="%s/api/s740/items" onchange="s740sup(this)"><option value="">Dealer…</option>%s</select>'
                 '<select id="s740item" onchange="s740q(0,true)"><option value="">Item…</option></select>'
                 '<div class="s740q"><button onclick="s740q(-1)" aria-label="less">−</button><span id="s740qty" data-n="1">1 pc</span>'
                 '<button onclick="s740q(1)" aria-label="more">+</button></div><span id="s740val" class="s740m"></span>'
                 '<div><button class="s740y" id="s740go" onclick="s740rec(\'%s/api/s740/record\')">Record the return</button></div></div></div>'
                 % (esc(prefix), opts, esc(prefix)))
    n = "%d pending" % len(pend) + (" · %d to answer" % len(flags) if flags else "")
    return ("Returns (pending until the dealer's credit note or revised bill)", n, ["".join(lines)], False)


_check_rows_before_s740 = check_rows


def check_rows(r, cx):                                        # noqa: F811 -- S740: row 8, Returns
    rows = _check_rows_before_s740(r, cx)
    ctx = getattr(_S740_T, "check", None)
    if not ctx:
        return rows
    try:
        rows = list(rows) + [s740_owner_row(ctx["con"], r.get("month") or "", ctx["prefix"])]
    except Exception as e:                                    # noqa: BLE001 -- the seven rows stand
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S740 row: %r" % (e,), file=_sys.stderr)
    return rows


_check_body_before_s740 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S740: row 8, the NEFT strip holds on a pending return
    _S740_T.check = dict(con=con, prefix=prefix)
    try:
        h = _check_body_before_s740(con, month, prefix, months, r)
    finally:
        _S740_T.check = None
    try:
        n = sum(1 for x in s740_pending(con) if x["month"] <= month)
        word = "%d pending return%s" % (n, "" if n == 1 else "s")
    except Exception as e:                                    # noqa: BLE001 -- fails CLOSED: the strip holds
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S740 strip: %r" % (e,), file=_sys.stderr)
        n, word = 1, "the returns could not be read"
    if n:
        if '<div class="strip clear" id="s726strip">All clear ✓</div>' in h:
            h = h.replace('<div class="strip clear" id="s726strip">All clear ✓</div>', '<div class="strip hold" id="s726strip">NEFT on hold · %s</div>' % word, 1)
        else:
            h = re.sub(r'(<div class="strip hold" id="s726strip">NEFT on hold · \d+ open)', r"\1 · " + word, h, count=1)
    return h.replace("</style>", S740_CSS + "</style>", 1) + S740_JS


_s738_scan_ok_before_s740 = s738_scan_ok


def s738_scan_ok(con, sid, doctor, login):                   # noqa: F811 -- S740: Amir also opens the scan of a return on his list
    if _s738_scan_ok_before_s740(con, sid, doctor, login):
        return True
    try:
        return int(sid) in {int(x["scan"]) for x in s740_pending(con) if x.get("scan") is not None} | {
            int(x["revised"]["scan"]) for x in s740_pending(con) if x.get("revised")}
    except Exception:                                         # noqa: BLE001
        return False
# ---- S740 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S749 (08-Nov-2026, Sanjeevni session 405, kit S749_ONE_SOURCE; D865, D866; F-1181, F-1182, F-1183; the owner's go 05:56 IST, the mock
#      https://claude.ai/artifact/BpPSuh8Cm2gPVmkzLDwmXi approved 06:04 with one addition: every action inline on his step view) -----------------
#  ONE SOURCE, ONE LANGUAGE. register() stays the one source every page reads; this section gives it the owner's words and his rulings:
#    * PAPER MATCHES is the one good state (verified and has-its-scan read alike; "has its scan" is gone from his screens).
#    * EVERY DIFFERENCE, Rs 1 INCLUDED, IS AMIR'S: in a counted month a bill settles only when Marg = the paper TO THE RUPEE (band_p -> 0;
#      total(): paise never hold a bill, a rupee does). A difference of one rupee (under two) is a ROUND-OFF -- straight to Amir's card ("Marg mein bill
#      <paper> kijiye (round-off)"), never a question to reception; beyond that reception types the paper's figure as before (porders asks
#      through s749_reception_asks). The "You" state (amount_state owner) is gone: it is Amir's correction; a dispute comes to row 5.
#    * OWNER-CONFIRMED SUPPLIERS (setting purchase.owner_confirm_suppliers, Ravi Medical Agency first): no scan asked, never "no scan";
#      one CONFIRM line to the owner per bill (s749_confirm; Undo; "Ask reception for the paper" puts one bill back on reception's list);
#      a scan that comes pairs as usual. Reception's Scan karo never lists them (porders.unscanned_bills).
#    * EVERYTHING INLINE on the step view: the scan folded open; Confirm; the second-look pair; the return answers; "Not this bill" (the pair
#      undone, audited, Undo) and "Pick the right bill" (the owner's own pair, audited, Undo); Accept without paper; Ask reception to
#      rescan. A Marg correction is still proved ONLY by Amir's export (F-1162) -- no tap here settles one.
#    * Build and decision numbers never on his screens (_s749_plain). The same month strip on the step view, the register and the audit page.
#  READ ONLY of assets.db. Nothing here prints a phone number, an account number or a key.
KIT_S749 = "S749_ONE_SOURCE"
S749_DDL = ("CREATE TABLE IF NOT EXISTS s749_confirm (bill_id INTEGER PRIMARY KEY, decision TEXT NOT NULL, by TEXT, at TEXT NOT NULL)",
            "CREATE TABLE IF NOT EXISTS s749_act (id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, scan INTEGER, bill_id INTEGER, old_grade TEXT, "
            "old_rule TEXT, old_at TEXT, by TEXT, at TEXT NOT NULL, undone_at TEXT, undone_by TEXT)")
S749_SUPS_KEY = "purchase.owner_confirm_suppliers"
STATES = STATES + ("confirm", "confirmed")                    # noqa: F811 -- the owner-confirmed supplier's bill: to confirm / confirmed by him
STATE_EN.update({"verified": "Paper matches", "has_scan": "Paper matches", "amount_differs": "Difference → Amir", "no_scan": "No scan",
                 "double": "Difference → Amir", "accepted": "Accepted without paper", "second_look": "Second look (yours)",
                 "unread_pair": "Rescan (reception)", "confirm": "Confirm (yours)", "confirmed": "Confirmed by you"})
S749_SETTLED = ("verified", "has_scan", "accepted", "confirmed")
S749_PLAIN = (("manoj (D839, S740 seed)", "your word"), (" (S726)", ""))
S749_STRIP_RE = re.compile(r"\s*\((?:S\d{3}|D\d{3}|F-\d{3,4})(?:[^)]*)\)")
S749_ROUND_RE = re.compile(r"\s*Paper ₹[\d,]+(?:\.\d\d)? · ₹[\d,]+(?:\.\d\d)? rounding — supplier's figure paid\.?")


def _s749_gap(scan_p, marg_p):
    """The difference between the paper and Marg, in paise, by its size."""
    return abs(int(scan_p or 0) - int(marg_p or 0))


def _s749_roundoff(scan_p, marg_p):
    """A round-off: the paper and Marg differ by a rupee (one rupee or more, under two) -- Marg's round-off field, Amir's to set."""
    if scan_p in (None, 0):
        return False
    return 100 <= _s749_gap(scan_p, marg_p) < 200


def _s749_plain(t, counted=True):
    """His words: no build or decision number; in a counted month no 'rounding -- supplier's figure paid' (every rupee is Amir's now; a parked
    month was cleared at the supplier's figure and says so)."""
    t = str(t or "")
    for a, b in S749_PLAIN:
        t = t.replace(a, b)
    if counted:
        t = S749_ROUND_RE.sub("", t)
    t = S749_STRIP_RE.sub("", t)
    return t.strip()


def _s749_owner_sups(con):
    """The owner-confirmed suppliers (setting purchase.owner_confirm_suppliers, comma-separated), as supplier keys."""
    pa = _pa()
    return {pa.supplier_key(x) for x in setting(con, S749_SUPS_KEY, "").split(",") if x.strip()}


def s749_owner_supplier(con, supplier):
    return bool(supplier) and _pa().supplier_key(supplier) in _s749_owner_sups(con)


def s749_confirms(con):
    try:
        return {int(r[0]): dict(decision=r[1], by=r[2], at=r[3]) for r in con.execute("SELECT bill_id, decision, by, at FROM s749_confirm")}
    except sqlite3.Error:
        return {}


def s749_ensure(con):
    for ddl in S749_DDL:
        con.execute(ddl)


# ------------------------------------------------------------------ the band: to the rupee in a counted month
def band_p(cx, b):                                            # noqa: F811 -- S749: a counted month settles only to the rupee
    ym = str(b.get("month") or str(b.get("bill_date") or "")[:7])
    return 0 if (not ym or ym >= getattr(cx, "first", "2026-10")) else cx.noise


_total_before_s749 = total


def total(scan_p, marg_p, noise):                             # noqa: F811 -- S749: band 0 = the rupee figures must agree
    if noise != 0:
        return _total_before_s749(scan_p, marg_p, noise)
    if scan_p is None or int(scan_p) == 0:
        return "not_read", None
    d = int(scan_p) - int(marg_p or 0)
    return ("equal" if abs(d) < 100 else "differ"), d                 # to the rupee: paise never hold a bill; a rupee does


def s749_reception_asks(con, scan_p, marg_p, ym):
    """porders' amount question (S440): in a counted month only beyond a round-off (the rupee figures two or more apart); a parked month keeps
    purchase.total_noise_rs. A round-off goes to Amir by itself."""
    if not scan_p:
        return False
    if ym and month_class(con, str(ym)[:7]) == "counted":
        return _s749_gap(scan_p, marg_p) >= 200
    return abs(int(scan_p) - int(marg_p or 0)) > noise_p(con)


# ------------------------------------------------------------------ the register in his words
_register_before_s749 = register


def register(con, month):                                     # noqa: F811 -- S749: one language; the You state gone; round-offs Amir's; Confirm
    """Inside ONE web request the same month is read once (flask.g, keyed by the connection and its change count): the hub, the audit page
    and the gate ask for it several times. Outside a request nothing is kept."""
    memo, key = None, (id(con), con.total_changes, month)
    try:
        from flask import g, has_request_context              # noqa: PLC0415
        if has_request_context():
            memo = g.__dict__.setdefault("_s749_reg_memo", {})
    except Exception:                                         # noqa: BLE001
        memo = None
    if memo is not None and key in memo:
        return memo[key]
    r = _register_before_s749(con, month)
    try:
        _s749_overlay(con, r)
    except Exception as e:                                    # noqa: BLE001 -- the register stands as it was
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S749 overlay: %r" % (e,), file=_sys.stderr)
    if memo is not None:
        memo[key] = r
    return r


class _S749TLDict(object):
    """S738's drawing context, one per worker thread (two pages drawn at once never clobber each other's scan panels)."""

    def __init__(self):
        self._l = _s740_threading.local()

    def _d(self):
        d = getattr(self._l, "d", None)
        if d is None:
            d = self._l.d = {}
        return d

    def get(self, k, default=None):
        return self._d().get(k, default)

    def __getitem__(self, k):
        return self._d()[k]

    def __setitem__(self, k, v):
        self._d()[k] = v

    def __contains__(self, k):
        return k in self._d()

    def clear(self):
        self._d().clear()

    def update(self, *a, **k):
        self._d().update(*a, **k)

    def items(self):
        return self._d().items()


_S738_CTX = _S749TLDict()                                     # noqa: F811


def _s749_overlay(con, r):
    sups = _s749_owner_sups(con)
    conf = s749_confirms(con) if sups else {}
    counted = r.get("cls") == "counted"
    for row in r["rows"]:
        st = row.get("state")
        a = row.get("agree") or {}
        if st == "no_scan" and row.get("scan") is None and counted and row.get("supplier") in sups and not row.get("missing"):
            d = conf.get(int(row["id"]))
            name = str(row["supplier"]).title()
            if d and d.get("decision") == "confirm":
                row.update(state="confirmed", whose="Nobody", note="Confirmed by you on %s. %s is settled by you; no scan asked." % (ddmon(d["at"]), name))
            elif d and d.get("decision") == "scan":
                row["note"] = "You asked reception for this paper on %s. %s" % (ddmon(d["at"]), row.get("note") or "")
            else:
                row.update(state="confirm", whose="You: confirm", note="%s is settled by you: no scan asked. Confirm when the bill is as you paid it." % name)
            row["s749"] = "owner_sup"
        elif st == "amount_differs" and not row.get("s740") and counted and not str(row.get("whose") or "").startswith("Return"):
            whose = str(row.get("whose") or "")
            rnd = bool(a.get("scan_p")) and _s749_roundoff(a["scan_p"], row.get("amount_p"))
            if whose in ("You", "Nobody", "") or (rnd and not a.get("paper")):
                row["whose"] = "Amir: a Marg correction"           # the You state is gone; a difference is never nobody's (fail-safe)
            if rnd:
                row["s749"] = "roundoff"
                row["note"] = "Round-off: the paper reads %s, Marg %s. Marg to be set to %s." % (rs2(a["scan_p"]), rs2(row.get("amount_p")), rs2(a["scan_p"]))
            elif whose in ("You", "Nobody", "") and a.get("scan_p"):
                row["note"] = "The paper reads %s, Marg %s. Marg to be set to %s." % (rs2(a["scan_p"]), rs2(row.get("amount_p")), rs2(a["scan_p"]))
        row["note"] = _s749_plain(row.get("note") or "", counted)
        row["whose"] = _s749_plain(row.get("whose") or "", counted)
    r["counts"] = {k: sum(1 for z in r["rows"] if z["state"] == k) for k in STATES}
    r["settled"] = sum(r["counts"][k] for k in S749_SETTLED)
    if r["total"] and r["settled"] == r["total"] and not r.get("open_scans") and not r.get("done_date"):
        r["done_date"] = today().isoformat()


_s738_fixes_before_s749 = s738_fixes


def s738_fixes(con, fast=False):                              # noqa: F811 -- S749: a one-rupee difference is a round-off on Amir's card
    out = _s738_fixes_before_s749(con, fast)
    for f in out:
        if f.get("kind") in ("less", "more") and f.get("paper_p") and _s749_roundoff(f["paper_p"], f["marg_p"]):
            f["kind"], f["items"] = "roundoff", []
    return out


# ------------------------------------------------------------------ the owner's taps (each audited; each commits)
def _s749_counted_bill(con, bill_id):
    """The live bill, or (None, why) -- a counted, unfinalised month only."""
    pa = _pa()
    b = con.execute("SELECT b.* FROM purchase_bill b WHERE b.id=? AND " + pa.EFF_BILL, (int(bill_id),)).fetchone()
    if b is None:
        return None, "No such bill."
    b = dict(b)
    ym = str(b.get("month") or str(b.get("bill_date") or "")[:7])
    if month_class(con, ym) != "counted":
        return None, "A parked month is read only."
    fin = con.execute("SELECT status FROM purchase_month WHERE month=?", (ym,)).fetchone()
    if fin and fin[0] == "final":
        return None, "This month is finalised -- nothing is changed in it."
    return b, ""


def s749_confirm_put(con, who, bill_id, decision):
    """Confirm (yours): 'confirm' settles the bill of an owner-confirmed supplier; 'scan' asks reception for its paper instead; 'undo' removes
    either. -> (ok, message)."""
    s749_ensure(con)
    b, why = _s749_counted_bill(con, bill_id)
    if b is None:
        return False, why
    if _pa().supplier_key(b.get("supplier")) not in _s749_owner_sups(con):
        return False, "This supplier's bills are not settled by you."
    if con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=?", (int(bill_id),)).fetchone():
        return False, "This bill has its scan -- it is judged by the paper."
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    if decision == "undo":
        cur = con.execute("DELETE FROM s749_confirm WHERE bill_id=?", (int(bill_id),))
        if not cur.rowcount:
            return False, "Nothing to undo."
        _s736_audit(con, who, "s749_confirm_undone", int(bill_id), dict(kit=KIT_S749))
        con.commit()
        return True, "Undone."
    if decision not in ("confirm", "scan"):
        return False, "Not a decision."
    con.execute("INSERT OR REPLACE INTO s749_confirm (bill_id, decision, by, at) VALUES (?,?,?,?)", (int(bill_id), decision, who, now))
    _s736_audit(con, who, "s749_confirm", int(bill_id), dict(decision=decision, supplier=_pa().supplier_key(b.get("supplier")), bill_no=b.get("bill_no"),
                                                              amount_p=b.get("amount_p"), kit=KIT_S749))
    con.commit()
    return True, "Confirmed -- settled by you." if decision == "confirm" else "Reception is asked for the paper."


def s749_scan_asked(con):
    """The bills of owner-confirmed suppliers the owner asked reception to scan after all -> {bill id}."""
    try:
        return {int(r[0]) for r in con.execute("SELECT bill_id FROM s749_confirm WHERE decision='scan'")}
    except sqlite3.Error:
        return set()


def _s749_hint_no(con, who, sid, bill_id, add=True):
    """The matcher must never pair this scan and this bill again (add) -- or may again (undo). purchase_scan_state.hint_no, as reception's Nahi."""
    _pa()._ensure_s439(con)
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("INSERT OR IGNORE INTO purchase_scan_state (asset_bill_id, why, detail, checked_at) VALUES (?,?,?,?)", (int(sid), "linked", "linked", now))
    row = con.execute("SELECT hint_no FROM purchase_scan_state WHERE asset_bill_id=?", (int(sid),)).fetchone()
    nos = {int(x) for x in str((row[0] if row else "") or "").split(",") if x.strip().isdigit()}
    nos = (nos | {int(bill_id)}) if add else (nos - {int(bill_id)})
    con.execute("UPDATE purchase_scan_state SET hint_no=?, confirmed_by=?, confirmed_at=? WHERE asset_bill_id=?",
                (",".join(str(x) for x in sorted(nos)) or None, who, now, int(sid)))


def _s749_pass(con, who):
    try:
        _pa()._rematch(con, who)
    except Exception as e:                                    # noqa: BLE001 -- the next page read runs the pass
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S749 pass: %r" % (e,), file=_sys.stderr)


def s749_unpair(con, who, sid, bill_id):
    """Not this bill: the pair is undone (audited, Undo); the scan never pairs with that bill by itself again. -> (ok, message)."""
    s749_ensure(con)
    b, why = _s749_counted_bill(con, bill_id)
    if b is None:
        return False, why
    l = con.execute("SELECT grade, matched_on, linked_at FROM purchase_scan_link WHERE bill_id=? AND asset_bill_id=?", (int(bill_id), int(sid))).fetchone()
    if l is None:
        return False, "This scan is not paired with that bill."
    if b.get("verdict"):
        return False, "This bill carries a verdict (%s) -- it is not unpaired here." % b.get("verdict")
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("DELETE FROM purchase_scan_link WHERE bill_id=? AND asset_bill_id=?", (int(bill_id), int(sid)))
    con.execute("UPDATE purchase_bill SET scan_bill_id=NULL WHERE id=? AND scan_bill_id=?", (int(bill_id), int(sid)))
    _s749_hint_no(con, who, sid, bill_id, add=True)
    cur = con.execute("INSERT INTO s749_act (kind, scan, bill_id, old_grade, old_rule, old_at, by, at) VALUES ('unpair',?,?,?,?,?,?,?)",
                      (int(sid), int(bill_id), l[0], l[1], l[2], who, now))
    _s736_audit(con, who, "s749_unpaired", int(bill_id), dict(scan=int(sid), act=cur.lastrowid, was_grade=l[0], was_rule=l[1], kit=KIT_S749))
    con.commit()
    _s749_pass(con, who)
    return True, "Unpaired. Pick the right bill below, or leave the scan to reception."


def s749_pick_options(con, sid):
    """The bills the owner may pair this scan with: unscanned, of a counted month, within 120 days of the scan; the supplier's own first."""
    scans = asset_scans(con) or {}
    s = scans.get(int(sid))
    if s is None or con.execute("SELECT 1 FROM purchase_scan_link WHERE asset_bill_id=?", (int(sid),)).fetchone():
        return []                                              # gone, or the rules found its bill by themselves meanwhile
    pa = _pa()
    cx = Ctx(con)
    day = _date(s.get("bill_date")) or _date(s.get("day")) or today()
    linked = {int(r[0]) for r in con.execute("SELECT bill_id FROM purchase_scan_link")}
    out = []
    for b in con.execute("SELECT b.* FROM purchase_bill b WHERE " + pa.EFF_BILL + " ORDER BY b.bill_date DESC, b.id DESC"):
        b = dict(b)
        if int(b["id"]) in linked or int(b.get("amount_p") or 0) <= 0:
            continue
        bd = _date(b.get("bill_date"))
        if bd is None or abs((bd - day).days) > 120 or month_class(con, str(b.get("month") or str(b["bill_date"])[:7])) != "counted":
            continue
        same = supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(int(sid))) == "agree"
        out.append(dict(id=int(b["id"]), supplier=pa.supplier_key(b["supplier"]), bill_no=str(b.get("bill_no") or ""), date=str(b["bill_date"])[:10],
                        amount_p=int(b.get("amount_p") or 0), same=same))
    out.sort(key=lambda x: (not x["same"], x["date"]))
    return out[:40]


def s749_pair(con, who, sid, bill_id):
    """Pick the right bill: the owner's own pair (grade CONFIRMED, audited, Undo). -> (ok, message)."""
    s749_ensure(con)
    b, why = _s749_counted_bill(con, bill_id)
    if b is None:
        return False, why
    if con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=?", (int(bill_id),)).fetchone():
        return False, "That bill already has its scan."
    if con.execute("SELECT 1 FROM purchase_scan_link WHERE asset_bill_id=?", (int(sid),)).fetchone():
        return False, "This scan is already paired -- undo that first."
    if int(sid) not in (asset_scans(con) or {}):
        return False, "This scan is not a captured pharmacy scan."
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                (int(bill_id), int(sid), "CONFIRMED", "the owner picked it", now))
    con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (int(sid), int(bill_id)))
    _s749_hint_no(con, who, sid, bill_id, add=False)
    cur = con.execute("INSERT INTO s749_act (kind, scan, bill_id, by, at) VALUES ('pair',?,?,?,?)", (int(sid), int(bill_id), who, now))
    _s736_audit(con, who, "scan_link", int(bill_id), dict(scan=int(sid), grade="CONFIRMED", rule="the owner picked it", act=cur.lastrowid,
                                                           supplier=_pa().supplier_key(b.get("supplier")), bill_no=b.get("bill_no"), kit=KIT_S749))
    con.commit()
    _s749_pass(con, who)
    return True, "Paired with bill %s." % (b.get("bill_no") or "")


def s749_undo_act(con, who, act_id):
    """Undo of 'Not this bill' (the old pair put back, when both are still free) or of 'Pick the right bill' (the pair removed)."""
    s749_ensure(con)
    a = con.execute("SELECT id, kind, scan, bill_id, old_grade, old_rule, old_at FROM s749_act WHERE id=? AND undone_at IS NULL", (int(act_id),)).fetchone()
    if a is None:
        return False, "Nothing to undo."
    now = dt.datetime.now().replace(microsecond=0).isoformat()
    sid, bid = int(a[2]), int(a[3])
    _b, why = _s749_counted_bill(con, bid)
    if _b is None:
        return False, why
    if a[1] == "unpair":
        if con.execute("SELECT 1 FROM purchase_scan_link WHERE bill_id=? OR asset_bill_id=?", (bid, sid)).fetchone():
            return False, "The scan or the bill has been paired since -- undo that pair first."
        con.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                    (bid, sid, a[4] or "CONFIRMED", a[5] or "the owner's undo", a[6] or now))
        con.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (sid, bid))
        _s749_hint_no(con, who, sid, bid, add=False)
    else:
        cur = con.execute("DELETE FROM purchase_scan_link WHERE bill_id=? AND asset_bill_id=?", (bid, sid))
        if not cur.rowcount:
            return False, "That pair is no longer there."
        con.execute("UPDATE purchase_bill SET scan_bill_id=NULL WHERE id=? AND scan_bill_id=?", (bid, sid))
    con.execute("UPDATE s749_act SET undone_at=?, undone_by=? WHERE id=?", (now, who, int(act_id)))
    _s736_audit(con, who, "s749_act_undone", bid, dict(scan=sid, act=int(act_id), kind=a[1], kit=KIT_S749))
    con.commit()
    _s749_pass(con, who)
    return True, "Undone."


def s749_acts(con, month_ids):
    """The owner's pairs and unpairs of these bills not undone, newest first."""
    try:
        rows = con.execute("SELECT id, kind, scan, bill_id, by, at FROM s749_act WHERE undone_at IS NULL ORDER BY id DESC").fetchall()
    except sqlite3.Error:
        return []
    return [dict(id=int(r[0]), kind=r[1], scan=r[2], bill_id=r[3], by=r[4], at=r[5]) for r in rows if int(r[3]) in month_ids]


# ------------------------------------------------------------------ the month strip (the step view, the register, the audit page)
def s749_months(con):
    """The months shown on the strip: every counted month from purchase.register_from, newest first, and the parked months after them."""
    ms = months_with_bills(con, 24)
    counted = sorted([m for m in ms if month_class(con, m) == "counted"], reverse=True)
    parked = sorted([m for m in ms if month_class(con, m) == "parked"], reverse=True)
    t = today().strftime("%Y-%m")
    if t not in counted and month_class(con, t) == "counted":
        counted.insert(0, t)
    return counted + parked


def s749_month_strip(con, month, href_fn, idprefix="s749ms"):
    """One row of month chips, the chosen one filled; a parked month greyed. href_fn(ym) -> the page's own address for that month."""
    chips = []
    for m in s749_months(con):
        cls = "on" if m == month else ("park" if month_class(con, m) != "counted" else "")
        try:
            lab = "%s %s" % (MONTHS3[int(m[5:7]) - 1], m[2:4])
        except (ValueError, IndexError):
            lab = m
        chips.append('<a class="s749m %s" href="%s">%s</a>' % (cls, esc(href_fn(m)), esc(lab)))
    return ('<div class="s749strip" id="%s"><style>.s749strip{display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px}'
            '.s749strip .s749m{display:inline-flex;align-items:center;min-height:36px;padding:0 12px;border:1px solid #1f3864;border-radius:18px;'
            'color:#1f3864;background:#fff;text-decoration:none;font-weight:600;font-size:15px}.s749strip .s749m.on{background:#1f3864;color:#fff}'
            '.s749strip .s749m.park{color:#8a7a5c;border-color:#c9c1b2}</style>%s</div>' % (esc(idprefix), "".join(chips)))


# ------------------------------------------------------------------ what each page says of a month (the hub, the console, the pay sheet)
def s749_month_open(con, month, r=None):
    """READ ONLY: the open items of a month as the step view counts them -> dict(match, amir, confirm, reception, you, returns, open, words,
    neft) -- 'words' is the one line every page shows ('77 paper matches · 6 differences → Amir · 1 to confirm · 1 return pending')."""
    r = r if r is not None else register(con, month)
    cx = Ctx(con)
    g = _s749_groups(con, r, cx)
    try:
        rets = [x for x in s740_pending(con) if x["month"] <= month]
    except Exception:                                         # noqa: BLE001 -- fails closed: the month is not clear
        rets = [dict(key="?")]
    c = r.get("counts") or {}
    n = dict(match=c.get("verified", 0) + c.get("has_scan", 0) + c.get("accepted", 0) + c.get("confirmed", 0),   # S755 (F-1188): as row 1's heading
             accepted=c.get("accepted", 0), confirmed=c.get("confirmed", 0),
             amir=len(g["amir"]), confirm=len(g["confirm"]), reception=g["n_reception"], you=g["n_you"], returns=len(rets))
    n["open"] = n["amir"] + n["confirm"] + n["reception"] + n["you"] + n["returns"]
    bits = ["%d paper match%s" % (n["match"], "" if n["match"] == 1 else "es")]
    if n["amir"]:
        bits.append("%d difference%s → Amir" % (n["amir"], "" if n["amir"] == 1 else "s"))
    if n["confirm"]:
        bits.append("%d to confirm" % n["confirm"])
    if n["reception"]:
        bits.append("%d with reception" % n["reception"])
    if n["you"]:
        bits.append("%d for you" % n["you"])
    if n["returns"]:
        bits.append("%d return%s pending" % (n["returns"], "" if n["returns"] == 1 else "s"))
    n["words"] = " · ".join(bits)
    n["neft"] = "NEFT on hold" if n["open"] else "clear"
    n["total"] = r.get("total", 0)
    return n


def s749_lock_reasons(con, month):
    """The register's own holds for the lock gate (rows 2-6 of the step view), in his words; [] when clear. A parked month holds nothing."""
    if month_class(con, month) != "counted":
        return []
    n = s749_month_open(con, month)
    out = []
    if n["amir"]:
        out.append("%d difference%s → Amir (Marg to be corrected to the paper, proved by his export)" % (n["amir"], "" if n["amir"] == 1 else "s"))
    if n["confirm"]:
        out.append("%d bill%s to confirm (yours: an owner-confirmed supplier)" % (n["confirm"], "" if n["confirm"] == 1 else "s"))
    if n["reception"]:
        out.append("%d with reception (a scan, a rescan or a question)" % n["reception"])
    if n["you"]:
        out.append("%d for you and Shavez (a second look or a paper not found)" % n["you"])
    if n["returns"]:
        out.append("%d return%s pending (the dealer's credit note or revised bill)" % (n["returns"], "" if n["returns"] == 1 else "s"))
    return out


# ------------------------------------------------------------------ the step view: the eight rows, everything inline
def _s749_next(x):
    """'Next: ...' for an open register row, in his words."""
    st, a = x.get("state"), x.get("agree") or {}
    whose = str(x.get("whose") or "")
    if st in ("amount_differs", "double") and whose.startswith("Amir"):
        if st == "double":
            return "Next: Amir removes one entry in Marg. Proved by his export."
        return "Next: Marg bill → %s%s. Proved by his export." % (rs2(a.get("scan_p")), " (round-off)" if x.get("s749") == "roundoff" else "")
    if st == "amount_differs" and whose.startswith("Reception"):
        return "Next: reception confirms the paper's figure (the scan reads %s, Marg %s)." % (rs(a.get("scan_p")), rs(x.get("amount_p")))
    if st == "amount_differs" and whose.startswith("Return"):
        return "Next: the dealer's revised bill or credit note → Amir enters it. Also under Returns."
    if st == "confirm":
        return "Next: your tap settles it; or ask reception for the paper."
    if st == "no_scan" and x.get("missing"):
        return "Next: accept it without paper, or ask reception again."
    if st == "no_scan":
        return "Next: reception scans the bill%s." % (" (a question is open)" if whose == "Reception: a question" else "")
    if st == "unread_pair":
        return "Next: reception rescans the paper."
    if st == "second_look":
        return "Next: your two buttons -- the paper's figure stands, or the scan misread."
    return ""


def _s749_cells(x, what, who):
    """One line of the step view in columns: supplier · bill, the date, the scan, what, whose · next."""
    sid = x.get("scan")
    return ('<span class="c1">%s %s</span><span class="c2">%s</span><span class="c3">%s</span><span class="c4">%s</span><span class="c5">%s</span>'
            % (esc(x["supplier"]), esc(x["bill_no"]), esc(_s738_dmy(x.get("date"))), ("scan %s" % esc(x.get("stamp") or "")) if sid is not None else "no scan",
               what, who))


def _s749_btn(label, body, cls="s736b"):
    """An inline button posting JSON (s749post in S749_JS); body is a dict."""
    return '<button type="button" class="%s" onclick=\'s749post(this,%s)\'>%s</button>' % (esc(cls), esc(json.dumps(body)), esc(label))


def _s749_line(x, what, who, acts, viewer=True):
    """A register row as one inline line: the columns, the folded scan, and its own actions."""
    sid = x.get("scan")
    cells = _s749_cells(x, what, who)
    body = ('<div class="s749acts">%s</div>' % "".join(acts)) if acts else ""
    if sid is None or not viewer:
        return '<div class="s738l" data-bill="%d">%s<span class="c6"></span></div>%s' % (int(x["id"]), cells, body)
    return ('<details class="s738v" ontoggle="s738open(this)"><summary class="s738l" data-bill="%d">%s<span class="c6"><span class="s738b">'
            '<span class="sh">Show scan &#9662;</span><span class="hd">Hide scan &#9652;</span></span></span></summary>%s</details>%s'
            % (int(x["id"]), cells, _s738_panel(sid), body))


def _s749_groups(con, r, cx):
    """The register's rows of one month sorted into the step view's rows -> dict(amir, confirm, reception, you, confirmed, scans, asks, esc,
    n_reception, n_you): the ONE tally the step view, the hub, the console, the register chips and the lock gate all read."""
    rows = [x for x in (r.get("rows") or []) if not str(x.get("whose") or "").startswith("Nobody (")]
    if "s736" not in r:
        r = dict(r, s736=_s736_view(con) or {})
    v = r.get("s736") or {}
    month = r.get("month") or ""
    asks = [a for a in (v.get("asks") or []) if a.get("month") == month]
    esc_ = [x for x in (v.get("escalated") or []) if x.get("month") == month]
    esc_ids = {int(x["scan"]) for x in esc_}
    g = dict(amir=[], confirm=[], reception=[], you=[], confirmed=[], scans=[], asks=asks, esc=esc_)
    for x in rows:
        st, whose = x.get("state"), str(x.get("whose") or "")
        if st in ("amount_differs", "double") and whose.startswith("Amir"):
            g["amir"].append(x)
        elif st == "amount_differs" and whose.startswith("Return"):
            pass                                               # a return's bill is row 6's (and the returns count's), never counted twice
        elif st == "amount_differs" and whose.startswith("Reception"):
            g["reception"].append(x)
        elif st == "confirm":
            g["confirm"].append(x)
        elif st == "confirmed":
            g["confirmed"].append(x)
        elif st == "no_scan" and x.get("missing"):
            g["you"].append(x)
        elif st == "no_scan":
            g["reception"].append(x)
        elif st == "unread_pair" and x.get("scan") not in esc_ids:
            g["reception"].append(x)
        elif st == "second_look":
            g["you"].append(x)
    month_ids = {x["id"] for x in (r.get("rows") or [])}
    hinted = {sid for sid, bid in cx.likely.items() if bid in month_ids}
    for s in (r.get("scans") or []):
        if s["id"] in esc_ids:
            continue
        if s["state"] in ("probably", "vendor", "to_name", "unread") and not (s["state"] == "probably" and s["id"] in hinted):
            g["scans"].append(s)
    shown = {x.get("scan") for x in g["reception"]} | {int(s["id"]) for s in g["scans"]}
    g["asks_extra"] = [a for a in asks if int(a["scan"]) not in shown]
    g["n_reception"] = len(g["reception"]) + len(g["scans"]) + len(g["asks_extra"])
    g["n_you"] = len(g["you"]) + len(esc_)
    return g


def s749_rows(con, r, cx, prefix):
    """The eight rows of the step view: [(label, sub, count text, [lines as HTML], grey)]."""
    v = r.get("s736") or {}
    month = r.get("month") or ""
    g = _s749_groups(con, r, cx)
    tr = s738_tracked(con)
    asks = g["asks"]
    ask_by_scan = {int(a["scan"]): a for a in asks}
    esc_ = g["esc"]
    dec = [x for x in (v.get("decided") or []) if x.get("month") == month]
    try:
        verd = {int(x[0]) for x in con.execute("SELECT id FROM purchase_bill WHERE verdict IS NOT NULL")}
    except sqlite3.Error:
        verd = set()
    acts = s749_acts(con, {x["id"] for x in (r.get("rows") or [])})
    act_by_scan = {int(a["scan"]): a for a in acts if a.get("scan") is not None}
    hdr = ('<div class="s738hd"><span>Supplier · bill</span><span>Bill date</span><span>Scan</span><span>What</span><span>Whose · next</span><span></span></div>')
    u_rescan = "/finance/porders/api/s454/rescan"
    u_nopaper = prefix + "/api/s454/nopaper"

    def rescan_btn(x):
        sid = x.get("scan")
        if sid is None:
            return ""
        if int(sid) in ask_by_scan:
            return '<span class="mut">rescan asked, try %d</span>' % int(ask_by_scan[int(sid)].get("try_n") or 1)
        return _s749_btn("Ask reception to rescan", dict(u=u_rescan, b=dict(asset_bill_id=int(sid), reason="blurred")))

    def notthis_btn(x):
        sid = x.get("scan")
        if sid is None or x.get("s740") or int(x["id"]) in verd:        # a bill with a verdict is not unpaired here (the door refuses it)
            return ""
        return _s749_btn("Not this bill", dict(u=prefix + "/api/s749/unpair", b=dict(scan=int(sid), bill=int(x["id"])), pick=1))

    # 1 · Paper matches
    c = r.get("counts") or {}
    n_match = c.get("verified", 0) + c.get("has_scan", 0)
    n_head = n_match + c.get("accepted", 0) + c.get("confirmed", 0)                           # S755: the body counts as the heading does
    l1 = ['<div class="mut">Nothing to do here. The %d bill%s that match are on <a href="%s/page/scans?month=%s">the full list</a>%s.</div>'
          % (n_head, "" if n_head == 1 else "s", esc(prefix), esc(month),
             (" (%d matched to the rupee%s%s)" % (n_match, (", %d accepted without paper" % c.get("accepted", 0)) if c.get("accepted") else "",
                                                 (", %d confirmed by you" % c.get("confirmed", 0)) if c.get("confirmed") else ""))
             if (c.get("accepted") or c.get("confirmed")) else "")]
    if g["confirmed"]:
        for x in g["confirmed"]:
            l1.append(_s749_line(x, "%s · confirmed by you" % esc(rs(x["amount_p"])), esc(x.get("note") or ""),
                                 [_s749_btn("Undo", dict(u=prefix + "/api/s749/confirm", b=dict(bill=int(x["id"]), decision="undo")))]))
    # 2 · Differences → Amir
    l2 = []
    for x in g["amir"]:
        a = x.get("agree") or {}
        t = tr.get(int(x["id"]))
        since = (" · since %s" % _s738_dm(t.get("first_seen"))) if t and not t.get("settled_at") else ""
        if x.get("state") == "double":
            what = "%s · entered twice in Marg" % esc(rs(x["amount_p"]))
        else:
            what = "paper %s · Marg %s%s" % (esc(rs2(a.get("scan_p"))), esc(rs2(x["amount_p"])), " · round&#8209;off" if x.get("s749") == "roundoff" else "")
        who = "%s%s<br>%s" % (esc("Dealer's paper awaited" if str(x.get("whose") or "").startswith("Return") else "Amir"), esc(since), esc(_s749_next(x)))
        l2.append(_s749_line(x, what, who, [notthis_btn(x), rescan_btn(x)]))
    for bid, t in [(bid, t) for bid, t in tr.items() if t.get("settled_at") and t.get("month") == month]:
        b = con_bill(r, bid)
        if b is not None:
            l2.append('<div class="s738l s738ok" data-bill="%d"><span class="c1">%s %s</span><span class="c2">%s</span><span class="c3"></span>'
                      '<span class="c4">corrected ✓</span><span class="c5">Amir · his export of %s shows Marg = the paper</span><span class="c6"></span></div>'
                      % (int(bid), esc(b["supplier"]), esc(b["bill_no"]), esc(_s738_dmy(b.get("date"))), esc(_s738_dm(t.get("settled_export") or t.get("settled_at")))))
    # 3 · Confirm — yours
    l3 = []
    for x in g["confirm"]:
        l3.append(_s749_line(x, esc(rs(x["amount_p"])), "You<br>" + esc(_s749_next(x)),
                             [_s749_btn("Confirm", dict(u=prefix + "/api/s749/confirm", b=dict(bill=int(x["id"]), decision="confirm")), "s736b s749y"),
                              _s749_btn("Ask reception for the paper", dict(u=prefix + "/api/s749/confirm", b=dict(bill=int(x["id"]), decision="scan")))]))
    sups = sorted(_s749_owner_sups(con))
    l3.append('<div class="mut">Suppliers you settle yourself: %s. Another dealer is added by a word to Claude.</div>' % esc(", ".join(s.title() for s in sups) or "none yet"))
    # 4 · With reception
    l4 = []
    for x in g["reception"]:
        st = x.get("state")
        acts_ = [notthis_btn(x), rescan_btn(x)]
        if st == "no_scan" and x.get("s749") == "owner_sup":
            acts_ = [_s749_btn("Undo (back to Confirm)", dict(u=prefix + "/api/s749/confirm", b=dict(bill=int(x["id"]), decision="undo")))]
        if st == "no_scan":
            what = "%s · %s" % (esc(rs(x["amount_p"])), "a question is open" if x.get("whose") == "Reception: a question" else "to scan")
        elif st == "unread_pair":
            what = "paired, nothing read: rescan"
        else:
            what = "scan %s · Marg %s · the paper's figure to confirm" % (esc(rs2((x.get("agree") or {}).get("scan_p"))), esc(rs2(x["amount_p"])))
        l4.append(_s749_line(x, what, "Reception<br>" + esc(_s749_next(x)), acts_))
    for s in g["scans"]:
        tail = ""
        if int(s["id"]) in ask_by_scan:
            tail = ' <span class="mut">· rescan asked, try %d</span>' % int(ask_by_scan[int(s["id"])].get("try_n") or 1)
        l4.append("Scan %s · %s%s%s" % (esc(s["stamp"]), esc(SCAN_EN[s["state"]]), tail, _s738_viewer(int(s["id"]))))
    for a in g["asks_extra"]:
        if True:
            l4.append("Scan %s · %s · rescan asked by %s, try %d" % (esc(a["stamp"]), esc(S736_REASON_EN.get(a["reason"], a["reason"])),
                                                                 "the server" if a["by"] == "server" else esc(str(a["by"]).split(" ")[0].title() or "?"), a["try_n"]))
    # 5 · You & Shavez
    l5 = []
    for x in g["you"]:
        if x.get("state") == "second_look":
            btns = []
            if v.get("ok") and x.get("scan") is not None:
                btns = [_s736_btn(x["scan"], "paper", "Paper's figure stands — Amir corrects", x["id"]), _s736_btn(x["scan"], "scan_misread", "Scan misread — settled", x["id"])]
            l5.append(_s749_line(x, "second look", "You & Shavez<br>" + esc(x.get("note") or ""), btns + [rescan_btn(x)]))
        else:
            l5.append(_s749_line(x, "%s · paper not found" % esc(rs(x["amount_p"])), "You<br>" + esc(_s749_next(x)),
                                 ['<button type="button" class="s736b s749y" onclick="s454np(%d,1)">Accept without paper</button>' % int(x["id"])]))
    for x in esc_:
        head = " ".join(z for z in (x.get("vendor") or "", x.get("bill_no") or "") if z) or "Scan"
        l5.append('%s · scan %s · rescanned %d times, still: %s<div class="s749acts"><a class="s736b" href="/scanapp/bills/%d/file" target="_blank" rel="noopener">Open paper</a>%s</div>'
                  % (esc(head), esc(x["stamp"]), int(x["tries"]), esc(S736_REASON_EN.get(x["reason"], x["reason"])), int(x["scan"]), _s736_btn(x["scan"], "accept", "Accept")))
    n_you = len(l5)
    decided = []
    for x in dec:
        word = {"paper": "the paper's figure stands", "scan_misread": "the scan misread", "accept": "accepted as it is"}.get(x["decision"], x["decision"])
        head = " ".join(z for z in (x.get("vendor") or "", x.get("bill_no") or "") if z) or "Scan"
        decided.append('<span class="mut">%s · scan %s · %s (%s)</span><div class="s749acts">%s</div>' % (esc(head), esc(x["stamp"]), esc(word), esc(ddmon(x.get("at")) or ""),
                                                                                               _s736_btn(x["scan"], "undo", "Undo")))
    for x in (r.get("rows") or []):
        if x.get("state") == "accepted":
            decided.append('<span class="mut">%s %s · %s</span><div class="s749acts"><button type="button" class="s736b" onclick="s454np(%d,0)">Undo</button></div>'
                           % (esc(x["supplier"]), esc(x["bill_no"]), esc(x.get("note") or "accepted without paper"), int(x["id"])))
    for a in acts:
        b = con_bill(r, a["bill_id"])
        if b is None:
            continue
        decided.append('<span class="mut">%s %s · %s scan %s (%s)</span><div class="s749acts">%s</div>'
                       % (esc(b["supplier"]), esc(b["bill_no"]), "unpaired from" if a["kind"] == "unpair" else "paired by you with", esc(str(a.get("scan"))),
                          esc(ddmon(a.get("at")) or ""), _s749_btn("Undo", dict(u=prefix + "/api/s749/undo", b=dict(act=int(a["id"]))))))
    if decided:
        l5.append('<span class="mut"><b>Decided</b> (undo any):</span>')
        l5.extend(decided)
    # 6 · Returns (S740's row, in his words)
    try:
        lab6, n6, l6, g6 = s740_owner_row(con, month, prefix)
    except Exception as e:                                    # noqa: BLE001 -- the row says so
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S749 returns row: %r" % (e,), file=_sys.stderr)
        n6, l6 = "could not be read", ["<div class='mut'>The returns could not be read -- the strip holds.</div>"]
    # 8 · Lock & NEFT
    try:
        rets_n = sum(1 for x in s740_pending(con) if x["month"] <= month)
    except Exception:                                         # noqa: BLE001
        rets_n = 1
    open_n = len(g["amir"]) + len(g["confirm"]) + len(l4) + n_you + rets_n
    holds = []
    if g["amir"]:
        holds.append("%d difference%s" % (len(g["amir"]), "" if len(g["amir"]) == 1 else "s"))
    if g["confirm"]:
        holds.append("%d to confirm" % len(g["confirm"]))
    if l4:
        holds.append("%d with reception" % len(l4))
    if n_you:
        holds.append("%d for you" % n_you)
    if rets_n:
        holds.append("%d return%s" % (rets_n, "" if rets_n == 1 else "s"))
    reps = ""
    try:
        pa = _pa()
        s_ = pa._month_summary(con, month)
        words = []
        for e in pa._month_reports(con, month, s_):
            w = {"SUPPLIERWISE": "supplier-wise", "BILLWISE": "bill-wise", "ITEMS": "item-wise"}.get(e["key"], e["label"])
            if e["state"] == "received" and not (e["key"] == "ITEMS" and e.get("no_lines")):
                words.append("%s ✓" % w)
            elif e["state"] == "received":
                words.append("%s — %d bill%s still without lines" % (w, e["no_lines"], "" if e["no_lines"] == 1 else "s"))
            else:
                words.append("%s — not yet" % w)
        reps = "Marg's month-end reports: %s." % " · ".join(words)
    except Exception:                                         # noqa: BLE001
        reps = "Marg's month-end reports: could not be read."
    l8 = ['<div>%s %s</div><div class="mut">The lock and the NEFT read this page and Marg\'s reports · nothing else. <a href="%s/page/pay/%s">The payment sheet</a>.</div>'
          % (("Holding: %s." % " · ".join(holds)) if holds else "Nothing holds here.", esc(reps), esc(prefix), esc(month))]
    rows = [("Paper matches", "the paper and Marg agree to the rupee", "%d / %d" % (n_match + c.get("accepted", 0) + c.get("confirmed", 0), r.get("total", 0)), l1, False),
            ("Differences → Amir", "Marg to be corrected to the paper's figure, ₹1 included", str(len(g["amir"])), [hdr] + l2 if l2 else ["Nothing here."], False),
            ("Confirm — yours", "suppliers you settle yourself; no scan asked", str(len(g["confirm"])), ([hdr] if g["confirm"] else []) + l3, False),
            ("With reception", "a scan, a rescan or a one-tap question", str(len(l4)), ([hdr] if g["reception"] else []) + (l4 or ["Nothing with reception."]), False),
            ("You & Shavez", "a disputed reading or a paper not found — your buttons", str(n_you), l5 or ["Nothing here."], False),
            ("Returns", "pending until the dealer's revised bill or credit note", n6, l6, False),
            ("Dealer summaries", "each dealer's month statement against Marg", "later", ["Comes later. Until then the lock does not wait for it."], True),
            ("Lock & NEFT", "opens when rows 2–6 are clear and Marg's month-end reports are in", ("%d open" % open_n) if open_n else "clear", l8, False)]
    return rows, open_n


S749_CSS = """
#s726chk .s749sub{display:block;font-weight:400;font-size:14px;color:#666}
#s726chk .s749acts{display:flex;flex-wrap:wrap;gap:8px;margin:4px 0 6px}
#s726chk .s749y{background:#1f3864;color:#fff}
#s726chk .s738l .c5{white-space:normal}
#s726chk #s749pick{border:1px dashed #b8c2d6;border-radius:10px;padding:8px 10px;margin:6px 0}
#s726chk #s749pick select{font:inherit;font-size:15px;min-height:40px;max-width:100%}
"""
S749_JS = """
<script>
function s749post(b,o){var m=document.getElementById('s736msg');if(b.disabled)return;b.disabled=true;
fetch(o.u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(o.b||{})})
.then(function(r){return r.json().catch(function(){return {};}).then(function(j){return [r,j];});}).then(function(x){
if(x[0].ok&&x[1].ok){if(o.pick){s749pick(o.b.scan,x[1].message||'');return;}if(x[1].message&&m){m.style.display='block';m.style.background='#e8f4ea';m.style.color='#1f4d25';m.textContent=x[1].message;}
setTimeout(function(){location.reload();},x[1].message?900:0);return;}
b.disabled=false;if(m){m.style.display='block';m.style.background='#fbe7e5';m.style.color='#8c1d18';m.textContent=x[1].message||x[1].error||('HTTP '+x[0].status);}})
.catch(function(e){b.disabled=false;if(m){m.style.display='block';m.textContent=String(e);}});}
function s749pick(scan,msg){var m=document.getElementById('s736msg');if(m){m.style.display='block';m.style.background='#e8f4ea';m.style.color='#1f4d25';m.textContent=msg;}
fetch(S749_PREFIX+'/api/s749/pick?scan='+encodeURIComponent(scan)).then(function(r){return r.json();}).then(function(j){var opts=j.options||[];
if(!opts.length){if(m){m.textContent=msg+' The scan found its bill by itself, or has none to offer.';}setTimeout(function(){location.reload();},1500);return;}
var d=document.getElementById('s749pick');if(!d){d=document.createElement('div');d.id='s749pick';var h=document.getElementById('s736msg');h.parentNode.insertBefore(d,h.nextSibling);}
d.textContent='';var b=document.createElement('b');b.textContent='Pick the right bill for scan '+scan;d.appendChild(b);d.appendChild(document.createElement('br'));
var sel=document.createElement('select');sel.id='s749sel';var o0=document.createElement('option');o0.value='';o0.textContent='Leave it to reception';sel.appendChild(o0);
opts.forEach(function(x){var o=document.createElement('option');o.value=String(x.id);o.textContent=(x.same?'':'(another dealer) ')+x.supplier+' '+x.bill_no+' · '+x.date+' · ₹'+x.amount;sel.appendChild(o);});
d.appendChild(sel);d.appendChild(document.createTextNode(' '));var bt=document.createElement('button');bt.type='button';bt.className='s736b s749y';bt.textContent='Pair';bt.onclick=function(){s749pair(parseInt(scan));};d.appendChild(bt);}).catch(function(){location.reload();});}
function s749pair(scan){var s=document.getElementById('s749sel');if(!s||!s.value){location.reload();return;}
s749post(s,{u:S749_PREFIX+'/api/s749/pair',b:{scan:scan,bill:parseInt(s.value)}});}
</script>
"""


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S749: the step view whole, in his words, everything inline
    """The owner's step view of one month: the month strip, the header, the NEFT strip, eight rows (each opens its lines; every line carries its
    scan folded and its own actions), the way to the full list. Reads only; the buttons post to their own doors."""
    r = r if r is not None else register(con, month)
    v = _s736_view(con)
    r = dict(r, s736=v or {})
    cx = Ctx(con)
    scans = asset_scans(con) or {}
    bill_of = {}
    for x in (r.get("rows") or []):
        if x.get("scan") is not None:
            b = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (int(x["id"]),)).fetchone()
            if b:
                bill_of[int(x["scan"])] = dict(supplier=_pa().supplier_key(b[0]), bill_no=b[1], bill_date=b[2], amount_p=b[3])
    total_p = sum(int(x["amount_p"] or 0) for x in (r.get("rows") or []))
    try:
        mname = MONTHS[int(month[5:7]) - 1]
    except (ValueError, IndexError):
        mname = month
    _S738_CTX.clear()
    _S738_CTX.update(scans=scans, bill_of=bill_of, paper=dict(cx.paper), prefix=prefix, tracked=s738_tracked(con))
    _S740_T.check = dict(con=con, prefix=prefix)
    try:
        rows, open_n = s749_rows(con, r, cx, prefix)
    finally:
        _S738_CTX.clear()
        _S740_T.check = None
    h = ['<div id="s726chk"><style>%s%s%s%s%s</style>' % (CHECK_CSS, S736_CSS, S738_CSS, S740_CSS, S749_CSS)]
    h.append(s749_month_strip(con, month, lambda m: "%s/page/check?month=%s" % (prefix, m)))
    h.append('<h1 id="s726head">%s · %d bill%s · %s</h1>' % (esc(mname), r.get("total", 0), "" if r.get("total", 0) == 1 else "s", esc(rs(total_p))))
    h.append('<div id="s736msg"></div>')
    if r.get("cls") != "counted":
        quiet = [x for x in (r.get("rows") or []) if str(x.get("whose") or "").startswith("Nobody (")]
        h.append('<div class="mut" id="s726parked" style="margin:-6px 0 8px">%s is parked: shown for reading only; nobody is asked.%s</div>'
                 % (esc(month_name(month)), (" %d bill%s under the new rules (%s) wait with nobody." % (len(quiet), "" if len(quiet) == 1 else "s",
                    esc(", ".join("%s %s · %s" % (x["supplier"], x["bill_no"], STATE_EN[x["state"]]) for x in quiet[:6])))) if quiet else ""))
        open_n = 0
    if open_n:
        h.append('<div class="strip hold" id="s726strip">NEFT on hold · %d open</div>' % open_n)
    else:
        h.append('<div class="strip clear" id="s726strip">All clear ✓</div>')
    h.append('<div class="mut" style="margin:0 0 6px">Open = a bill that still needs someone. Each line says what it is, what happens next and whose it is.</div>')
    for i, (lab, sub, n, lines, grey) in enumerate(rows, 1):
        h.append('<details class="%s%s" data-row="%d"%s><summary><span class="l"><b>%d</b> %s<span class="s749sub">%s</span></span><span class="n">%s</span></summary>'
                 '<ul>%s</ul></details>' % ("grey" if grey else "row", " last" if i == len(rows) else "", i, " open" if (i in (2, 3) and lines and n not in ("0", "later")) else "",
                                           i, esc(lab), esc(sub), esc(n), "".join("<li>%s</li>" % x for x in lines) or "<li>Nothing here.</li>"))
    h.append('<div class="mut" style="margin-top:10px">The full list, the same words: <a href="%s/page/scans?month=%s">the register</a> · '
             '<a href="%s/page/month/%s">the purchase audit</a> · <a href="%s/page/pay/%s">the payment sheet</a> · <a href="%s/page/hub">the hub</a> (orders, stock, the phone book) · '
             'reception\'s own list: <a href="/finance/porders/s454/billkaam">Aaj ka bill kaam</a>.</div></div>'
             % (esc(prefix), esc(month), esc(prefix), esc(month), esc(prefix), esc(month), esc(prefix)))
    h.append(S736_JS % json.dumps(prefix + "/api/s736/decide"))
    h.append(S738_JS)
    h.append(S740_JS)
    h.append('<script>var S749_PREFIX=%s;</script>' % json.dumps(prefix))
    h.append(S749_JS)
    h.append("""<script>function s454np(b,a){fetch(%s,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bill:b,accept:a})})
.then(function(r){return r.json();}).then(function(j){var m=document.getElementById('s736msg');if(!j.ok){if(m){m.style.display='block';m.style.background='#fbe7e5';m.style.color='#8c1d18';m.textContent=j.message||j.error;}return;}location.reload();});}</script>"""
             % json.dumps(prefix + "/api/s454/nopaper"))
    return "".join(h)


# ------------------------------------------------------------------ the register page: the full list, the same words
def page_body(con, month, prefix, owner, months):            # noqa: F811 -- S749: the full list in his words; the month strip; the read quality folded
    r = register(con, month)
    c = r["counts"]
    parked = r["cls"] != "counted"
    n = s749_month_open(con, month, r)
    h = ['<div id="s454reg"><style>%s%s</style>' % (CSS, "#s454reg .bl .c5{color:#555}#s454reg .st.confirm{color:#1f3864}#s454reg .st.confirmed{color:#1f4d25}"
                                                           "#s454reg details.s738v{border:0}#s454reg details.s738v>summary{list-style:none;cursor:pointer}"
                                                           "#s454reg .s738vb{display:flex;flex-wrap:wrap;gap:12px;margin:8px 0}#s454reg .s738f{flex:1 1 420px;min-height:420px;background:#e6e8ee;border-radius:8px}"
                                                           "#s454reg .s738f iframe{width:100%;height:560px;border:0}#s454reg .s738f img{max-width:100%}#s454reg .s738t{max-width:100%;overflow-x:auto}#s454reg .s738t table{border-collapse:collapse}"
                                                           "#s454reg .s738t th,#s454reg .s738t td{text-align:left;padding:2px 10px 2px 0;border:0;font-size:14px}")]
    h.append(s749_month_strip(con, month, lambda m: "%s/page/scans?month=%s" % (prefix, m)))
    h.append('<h1>Purchase bills: %s</h1>' % esc(month_name(month)))
    h.append('<div class="muted">The full list -- one row per Marg bill, the same words as your <a href="%s/page/check?month=%s">purchase check</a>. '
             'Tap a row with a scan to see the paper beside what it read.</div>' % (esc(prefix), esc(month)))
    if parked:
        h.append('<div class="park">%s is parked: nothing here raises an alert and nobody is asked.</div>' % esc(MONTHS[int(month[5:7]) - 1]))
    chips = ["%d bills in Marg" % r["total"], n["words"]]
    if c["accepted"]:
        chips.append("%d accepted without paper" % c["accepted"])
    if c["confirmed"]:
        chips.append("%d confirmed by you" % c["confirmed"])
    h.append('<div class="hd" id="s454heads">%s</div>' % "".join('<span class="chipn">%s</span>' % esc(x) for x in chips))
    if parked:
        h.append('<div id="s454settled"><b>%d of %d settled</b>.</div>' % (r["settled"], r["total"]))
    elif n["open"]:
        h.append('<div id="s454settled"><b>%d of %d settled</b> · %d open · NEFT on hold.</div>' % (r["settled"], r["total"], n["open"]))
    else:
        h.append('<div id="s454settled"><b>%d of %d ✓</b> All clear.</div>' % (r["total"], r["total"]))
    order = {"confirm": 0, "no_scan": 0, "unread_pair": 0, "amount_differs": 1, "second_look": 1, "double": 1, "has_scan": 3, "verified": 3, "accepted": 4, "confirmed": 4}
    rows = sorted(r["rows"], key=lambda x: (order.get(x["state"], 9), x["date"], x["id"]))
    scans = asset_scans(con) or {}
    _S738_CTX.clear()
    _S738_CTX.update(scans=scans, bill_of={}, paper=dict(Ctx(con).paper), prefix=prefix, tracked={})
    items = []
    try:
        for x in rows:
            tap = ""
            if owner and not parked and x["state"] in ("no_scan", "accepted") and (x.get("missing") or x["state"] == "accepted"):
                tap = (' <button class="sm" onclick="s454np(%d,%d)">%s</button>' % (x["id"], 0 if x["state"] == "accepted" else 1,
                                                                                 "Undo" if x["state"] == "accepted" else "Accept without paper"))
            a = x.get("agree") or {}
            paper = rs2(a["scan_p"]) if a.get("scan_p") else "—"
            word = s749_word(x)
            head = ('<div class="a">%s · %s · %s · Marg %s · paper %s</div><div><span class="st %s">%s</span>%s%s</div><div class="b">%s%s</div>'
                    % (esc(ddmon(x["date"])), esc(x["supplier"]), esc(x["bill_no"]), esc(rs(x["amount_p"])), esc(paper), x["state"], esc(word),
                       (" · scan " + esc(x["stamp"])) if x["stamp"] else "", tap, esc(x["note"]),
                       (' <i class="c5">%s</i>' % esc(_s749_next(x) or ("Whose: %s" % x["whose"]))) if x["whose"] and x["whose"] != "Nobody" else ""))
            if x.get("scan") is not None and x["scan"] in scans:
                b_ = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill WHERE id=?", (int(x["id"]),)).fetchone()
                if b_:
                    _S738_CTX["bill_of"][int(x["scan"])] = dict(supplier=_pa().supplier_key(b_[0]), bill_no=b_[1], bill_date=b_[2], amount_p=b_[3])
                items.append('<details class="bl s738v" data-bill="%d" data-state="%s" ontoggle="s738open(this)"><summary>%s</summary>%s</details>'
                             % (x["id"], x["state"], head, _s738_panel(int(x["scan"]))))
            else:
                items.append('<div class="bl" data-bill="%d" data-state="%s">%s</div>' % (x["id"], x["state"], head))
    finally:
        _S738_CTX.clear()
    first, rest = items[:15], items[15:]
    h.append('<div class="card" id="s454bills"><h2 style="margin:0;font-size:16px">The bills, open ones first</h2>%s%s</div>'
             % ("".join(first), ('<details><summary>Show all %d</summary>%s</details>' % (len(items), "".join(rest))) if rest else ""))
    sc = r["scan_counts"]
    srows = "".join('<tr><td>%s</td><td>%d</td><td>%s</td></tr>' % (esc(SCAN_EN[k]), sc[k], esc(SCAN_WHOSE[k])) for k in SCAN_STATES if sc[k])
    detail = "".join('<div class="bl"><div class="a">%s · %s</div><div class="b">%s · %s · %s</div></div>'
                     % (esc(x["stamp"]), esc(SCAN_EN[x["state"]]), esc(x["vendor"] or "no supplier read"), esc(x["bill_no"] or "no number"),
                        esc(rs(x["amount_p"]) if x["amount_p"] else "no amount")) for x in r["scans"])
    h.append('<div class="card" id="s454scans"><h2 style="margin:0;font-size:16px">Scans with no Marg bill: %d</h2>%s%s</div>'
             % (len(r["scans"]), ('<table><tr><td><b>What it is</b></td><td><b>Scans</b></td><td><b>Whose</b></td></tr>%s</table>' % srows) if srows else
                '<div class="muted">None.</div>', ('<details><summary>each scan</summary>%s</details>' % detail) if detail else ""))
    try:
        s = sarvam(con, month)
        nr, had, notap = readiness(con)
        h.append('<details class="card" id="s454sarvam"><summary style="cursor:pointer;font-weight:600">How well the scan reads, and the last 7 days</summary>'
                 '<div>On the %d linked bills: supplier %d · bill number %d · date %d · total %d read right. Item lines: %d of %d. '
                 '<a href="%s/page/sarvam?month=%s">the Sarvam page</a>.</div>'
                 '<div>Last 7 days: %d bill%s entered in Marg · %d had their scan before the entry · %d paired with no tap.</div>'
                 '<div class="muted"><a href="%s/page/scans?legacy=1&amp;month=%s">the old Scan links tables</a></div></details>'
                 % (s["n"], s["supplier"], s["billno"], s["date"], s["total"], s["items_right"], s["items_read"], esc(prefix), esc(month),
                    nr, "" if nr == 1 else "s", had, notap, esc(prefix), esc(month)))
    except Exception:                                         # noqa: BLE001 -- the list stands without it
        pass
    if owner and not parked:
        h.append("""<script>function s454np(b,a){fetch('%s/api/s454/nopaper',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({bill:b,accept:a})})
.then(function(r){return r.json();}).then(function(j){if(!j.ok){alert(j.message||j.error);return;}location.reload();});}</script>""" % prefix)
    h.append(S738_JS.replace('<button type="button" id="s738up"', '<button type="button" id="s738up" style="display:none"'))
    h.append("</div>")
    return "".join(h)


def s749_word(x):
    """The state word of a register row as every page prints it."""
    whose = str(x.get("whose") or "")
    if whose.startswith("Return"):
        return "Return pending"
    if x.get("state") in ("amount_differs", "double") and whose.startswith("Reception"):
        return "Difference (reception confirms the figure)"
    return STATE_EN.get(x["state"], x["state"])


def s749_audit_states(con, month):
    """For the audit page (purchase_app.page_month): {bill id: (the state word, whose · next)} from the one register."""
    out = {}
    try:
        r = register(con, month)
    except Exception:                                         # noqa: BLE001
        return out
    for x in r["rows"]:
        word = s749_word(x)
        nxt = _s749_next(x) or ("" if x.get("whose") in ("Nobody", "", None) else str(x.get("whose")))
        out[int(x["id"])] = (word, _s749_plain(nxt), x["state"])
    return out
# ---- S749 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S750 (08-Nov-2026, Sanjeevni session 406, kit S750_MONTH_END; D849, F-1175; the owner's go 09:03 IST, the mock
#      https://claude.ai/artifact/G7giUj7RrbiJAv2w8kHwvb approved 09:45 with his words: 'summary', not 'statement'; the dealer ledger) ------
#  THE MONTH END. Row 7 of the step view -- DEALER SUMMARIES -- each dealer's month summary (the paper reception scans under Pharmacy with
#  the 'summary' tick; the Scan App lands it as kind='Summary', doc_kind='summary', and its reader reads it as a summary, claude_reading
#  doc_kind 'summary') held against Marg's bills of the month less Marg's purchase returns. A dealer AGREES when the two are equal to the
#  rupee. A difference is EXPLAINED when row 2 (the paper differs from Marg -> Amir) or row 6 (a return pending) already carries it -- it
#  holds nothing new. An unexplained difference is HIS: a bill on the summary we do not have, a bill in Marg the dealer does not list, an
#  amount only the dealer has wrong -- *Ask the dealer* (waits, 'asked dd-mm') · *Carry to next month* (the amount shows under next month's
#  Carried in; this month stops waiting) · *Accept* (the dealer's figure stands on the sheet; a card asks Amir to enter the bill when its
#  paper comes). A dealer with no summary is AWAITED -- *Ask reception to scan it* puts a line on Aaj ka bill kaam -- or marked once
#  *Gives no summary* (a standing word, Undo). An owner-confirmed dealer (row 3): his Confirm counts as the summary. Every answer is a row
#  in s750_answer with Undo, audited (purchase_audit, kit=S750). The lock (purchase_app._lock_gate, s749_lock_reasons) and n['open']
#  (s749_month_open -- the parent's month_read reads it; its keys stay, one is added) wait for the dealers too. The ledger reads live in
#  purchase_app (/page/ledger). assets.db READ ONLY (the summary rows and their readings). Nothing here sends a message, taps a button for
#  anyone, writes a pay line or changes a Marg figure. Nothing here prints a phone number, an account number or a key.
KIT_S750 = "S750_MONTH_END"
S750_TOL_P = 100                                              # 'to the rupee': a summary that rounds differently by one rupee agrees
S750_DDL = ("CREATE TABLE IF NOT EXISTS s750_answer (id INTEGER PRIMARY KEY AUTOINCREMENT, dealer TEXT NOT NULL, month TEXT NOT NULL, "
            "kind TEXT NOT NULL, amount_p INTEGER, note TEXT, by TEXT, at TEXT NOT NULL, undone_at TEXT, undone_by TEXT)",
            "CREATE TABLE IF NOT EXISTS s750_dealer_of (scan INTEGER PRIMARY KEY, dealer TEXT NOT NULL, by TEXT, at TEXT NOT NULL)")
S750_KINDS = ("ask", "carry", "accept", "none", "scan", "rescan")
S750_KIND_EN = {"ask": "asked the dealer", "carry": "carried to next month", "accept": "accepted the dealer's figure",
                "none": "gives no summary", "scan": "reception asked to scan the summary", "rescan": "reception asked to rescan the summary"}


def s750_ensure(con):
    """The writers' tables (the installer makes them too). Readers never call this: a GET writes nothing, and a read-only copy must read."""
    for ddl in S750_DDL:
        con.execute(ddl)


def _s750_rows(con, sql, args=()):
    """A read of an S750 table that may not exist yet (before the install's seed, or on a copy): [] then, never a write."""
    try:
        return con.execute(sql, args).fetchall()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            return []
        raise


def _s750_now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _s750_prev_month(ym):
    try:
        y, m = int(ym[:4]), int(ym[5:7])
    except (TypeError, ValueError):
        return ""
    return "%04d-%02d" % ((y - 1, 12) if m == 1 else (y, m - 1))


def _s750_next_month(ym):
    try:
        y, m = int(ym[:4]), int(ym[5:7])
    except (TypeError, ValueError):
        return ""
    return "%04d-%02d" % ((y + 1, 1) if m == 12 else (y, m + 1))


def _s750_digits(s):
    return str(s or "").translate({ord(c): None for c in " -/._"}).upper().lstrip("0") or ""


def _s750_tail_match(a, b):
    """Two bill numbers name the same bill when one ends the other's digits (Marg clips long numbers; a summary prints 'SF 004043' for '4043')."""
    da, db_ = re.sub(r"\D", "", str(a or "")).lstrip("0"), re.sub(r"\D", "", str(b or "")).lstrip("0")
    if not da or not db_:
        return False
    if len(da) < 3 and len(db_) < 3:
        return da == db_
    return da.endswith(db_) or db_.endswith(da)


# ------------------------------------------------------------------ the summaries (assets.db READ ONLY)
def s750_summary_scans(con=None):
    """{scan id: dict} -- the summary papers reception scanned under Pharmacy (kind 'Summary', not rejected, not a duplicate) with their
    reading (claude_reading, doc_kind 'summary'); None when assets.db is unreachable."""
    pa = _pa()
    acon = pa._assets_con()
    if acon is None:
        return None
    try:
        cols = {r[1] for r in acon.execute("PRAGMA table_info(bills)")}
        sel = [c for c in ("id", "stamp_no", "vendor", "bill_no", "bill_date", "bill_month", "total_amount", "submitted_at", "created_at", "ocr_status",
                           "dup_of", "lane", "status", "kind", "doc_kind", "rescan_of") if c in cols]
        rows = [dict(r) for r in acon.execute("SELECT %s FROM bills WHERE kind='Summary' AND COALESCE(status,'')<>'rejected' AND dup_of IS NULL "
                                              "ORDER BY id" % ", ".join(sel))]
        ids = [int(r["id"]) for r in rows]
        rd = {}
        if ids:
            q = "SELECT bill_id, ok, doc_kind, data, error FROM claude_reading WHERE bill_id IN (%s)" % ",".join("?" * len(ids))
            for r in acon.execute(q, ids):
                try:
                    data = json.loads(r[3]) if r[3] else {}
                except ValueError:
                    data = {}
                rd[int(r[0])] = dict(ok=int(r[1] or 0), doc_kind=r[2], data=data if isinstance(data, dict) else {}, error=r[4])
    except sqlite3.Error:
        return None
    finally:
        acon.close()
    out = {}
    set_aside = {int(r["rescan_of"]) for r in rows if r.get("rescan_of")}
    for r in rows:
        sid = int(r["id"])
        if sid in set_aside:
            continue                                          # rescanned: the new scan speaks
        r["day"] = _scan_day(r)
        rr = rd.get(sid) or {}
        d = rr.get("data") or {}
        is_sum = (rr.get("doc_kind") == "summary" or d.get("doc_kind") == "summary")
        r["read"] = bool(rr.get("ok")) and is_sum and d.get("is_summary") is not False
        r["reading"] = d if r["read"] else {}
        if r["read"]:
            r["read_error"] = ""
        elif bool(rr.get("ok")) and is_sum:
            r["read_error"] = "the reader says this paper is not a dealer's summary"
        elif bool(rr.get("ok")):
            r["read_error"] = "read as a bill, not as a summary -- a rescan asks the right question"
        else:
            r["read_error"] = rr.get("error") or ("" if rr else "not read yet")
        r["bill_prompt"] = bool(rr.get("ok")) and not is_sum
        lines = []
        for ln in (d.get("lines") or []) if r["read"] else []:
            if not isinstance(ln, dict):
                continue
            lines.append(dict(kind=str(ln.get("kind") or "other"), no=str(ln.get("no") or ""), date=str(ln.get("date") or "")[:10] if ln.get("date") else "",
                              amount_p=_amount_p(ln.get("amount"))))
        r["lines"] = lines
        pt = str((d.get("period_to") or "")) if r["read"] else ""
        bm = str(r.get("bill_month") or "")
        lm = _s753_lines_month(lines)                         # S753: the month the listed bills fall in -- the paper's own word, not its printing date
        if lm:
            r["month"] = lm
        elif re.match(r"^\d{4}-\d\d-\d\d$", pt):
            r["month"] = pt[:7]
        elif re.match(r"^\d{4}-\d\d$", bm) and bm != str(r.get("day") or "")[:7]:
            r["month"] = bm                                   # reception chose an earlier month on purpose
        elif r.get("day"):
            r["month"] = _s750_prev_month(str(r["day"])[:7])  # a summary is scanned early the next month; the intake's default month is the scan's
        else:
            r["month"] = bm
        bills_p = sum(x["amount_p"] for x in lines if x["kind"] == "bill" and x["amount_p"] is not None)
        credits_p = sum(x["amount_p"] for x in lines if x["kind"] in ("credit", "payment") and x["amount_p"] is not None)
        tb = _amount_p(d.get("total_bills")) if r["read"] else None
        cl = _amount_p(d.get("closing")) if r["read"] else None
        op = _amount_p(d.get("opening")) if r["read"] else None
        if any(x["kind"] == "bill" and x["amount_p"] is not None for x in lines):
            fig = bills_p - sum(x["amount_p"] for x in lines if x["kind"] == "credit" and x["amount_p"] is not None)
        elif tb is not None:
            fig = tb
        elif cl is not None:
            fig = cl - (op or 0)
        else:
            fig = None
        r.update(bills_p=bills_p, credits_p=credits_p, total_bills_p=tb, closing_p=cl, opening_p=op, figure_p=fig)
        out[sid] = r
    return out


def _s750_dealer_of(con, scans):
    """{scan id: dealer key}: the owner's pick first (s750_dealer_of), then the intake's vendor, then the reading's dealer name matched to the
    pharmacy's suppliers (learned spellings, aliases, the key itself); '' when none fits."""
    pa = _pa()
    picked = {int(r[0]): str(r[1]) for r in _s750_rows(con, "SELECT scan, dealer FROM s750_dealer_of")}
    for sid, s in scans.items():
        s["picked"] = sid in picked
    sups = {}
    for r in con.execute("SELECT DISTINCT supplier_norm, supplier FROM purchase_bill WHERE supplier_norm IS NOT NULL"):
        sups.setdefault(str(r[0]), str(r[1] or r[0]))
    try:
        cx = Ctx(con)
        learned = dict(cx.learned or {})
        alias = cx.alias or {}
    except Exception:                                         # noqa: BLE001
        learned, alias = {}, {}
    out = {}
    for sid, s in scans.items():
        if sid in picked:
            out[sid] = picked[sid]
            continue
        cands = [_s753_not_us(s.get("vendor")), _s753_not_us((s.get("reading") or {}).get("dealer"))]   # S753: never the buyer, Sanjeevni itself
        key = ""
        for c in cands:
            if not c:
                continue
            k = pa.supplier_key(c)
            if k in sups:
                key = k
                break
            if learned.get(k) in sups:
                key = learned[k]
                break
            hit = [sk for sk in sups if pa._vendor_match(k, sk) or sk in (alias.get(k) or ())]
            if len(hit) == 1:
                key = hit[0]
                break
        s["dealer_by_bills"] = False
        if not key:                                           # S753: no printed name matched -- the bills on the paper name the dealer
            key = _s753_dealer_by_bills(con, s, sups)
            s["dealer_by_bills"] = bool(key)
        out[sid] = key
    return out


def s750_answers(con, month=None):
    """{(dealer, month): the standing answer dict} -- the newest not-undone answer per dealer and month. 'none' is a standing word: it stands
    for every month from the one it was given in."""
    out, none_from = {}, {}
    rows = _s750_rows(con, "SELECT id, dealer, month, kind, amount_p, note, by, at FROM s750_answer WHERE undone_at IS NULL ORDER BY id")
    for r in rows:
        a = dict(id=int(r[0]), dealer=str(r[1]), month=str(r[2]), kind=str(r[3]), amount_p=r[4], note=r[5] or "", by=r[6] or "", at=r[7])
        if a["kind"] == "none":
            if a["dealer"] not in none_from or a["month"] < none_from[a["dealer"]][0]:
                none_from[a["dealer"]] = (a["month"], a["id"])
            out[(a["dealer"], a["month"])] = a
        elif a["kind"] in ("scan", "rescan"):
            out.setdefault((a["dealer"], a["month"]), a)       # a reception ask never replaces the owner's answer
            if out[(a["dealer"], a["month"])]["kind"] in ("scan", "rescan"):
                out[(a["dealer"], a["month"])] = a
        else:
            out[(a["dealer"], a["month"])] = a
    if month:
        for d, (m0, aid) in none_from.items():
            if m0 <= month and (d, month) not in out:
                out[(d, month)] = dict(id=aid, dealer=d, month=m0, kind="none", amount_p=None, note="", by="", at="", standing=True)
    return out


def s750_carried_in(con, month):
    """{dealer: paise} carried INTO this month by the owner's 'carry' answers of the month before -- only while that month's summary still
    lists the bill Marg does not have. Once Amir enters it (Marg carries it in its own month) the carry is stale and nothing is carried in."""
    pm = _s750_prev_month(month)
    carries = {d: a for (d, m), a in s750_answers(con).items() if m == pm and a["kind"] == "carry" and a.get("amount_p")}
    if not carries:
        return {}
    try:
        still = {d["key"]: d for d in s750_dealers(con, pm)}
    except Exception:                                         # noqa: BLE001 -- fails closed: nothing is carried in from a month that cannot be read
        return {}
    out = {}
    for d, a in carries.items():
        x = still.get(d)
        if x is None or x["state"] != "differs" or not any(i["kind"] == "on_summary" for i in x["issues"]):
            continue
        out[d] = out.get(d, 0) + int(a["amount_p"])
    return out


# ------------------------------------------------------------------ the dealers of a month, each against its summary
def s750_dealers(con, month, r=None, cx=None, scans=None):
    """The dealers of a month -> list of dicts(key, name, bills, marg_p, returns_p, summary, state, diff_p, why, explained, issues, answer,
    holds, words). READ ONLY. state: agrees | differs | awaited | none | confirm | unreadable | unknown. holds = the lock waits for it.
    Memoised per request (flask.g) by (connection, its change count, month), as register() is -- the step view, the sheet and the gate ask several times."""
    memo = None
    try:
        from flask import g as _g                             # noqa: PLC0415
        memo = _g.__dict__.setdefault("_s750_memo", {})
    except Exception:                                         # noqa: BLE001 -- outside a request: no memo
        memo = None
    mk = (id(con), con.total_changes, month)
    if memo is not None and mk in memo:
        return memo[mk]
    out = _s750_dealers_build(con, month, r, cx, scans)
    if memo is not None:
        memo[mk] = out
    return out


def _s750_dealers_build(con, month, r=None, cx=None, scans=None):
    pa = _pa()
    r = r if r is not None else register(con, month)
    cx = cx if cx is not None else Ctx(con)
    counted = month_class(con, month) == "counted"
    running = month >= str(today())[:7]                       # the month has not ended: no summary is awaited yet (the owner, 11:30 IST 8-Nov)
    bills = {}
    for b in con.execute("SELECT b.id, b.supplier_norm, b.supplier, b.bill_no, b.bill_date, b.amount_p, b.scan_bill_id FROM purchase_bill b "
                         "WHERE COALESCE(b.month, substr(b.bill_date,1,7))=? AND %s ORDER BY b.supplier, b.bill_date, b.bill_no" % pa.EFF_BILL, (month,)):
        bills.setdefault(str(b[1] or ""), dict(name=str(b[2] or b[1] or ""), rows=[]))["rows"].append(
            dict(id=int(b[0]), bill_no=str(b[3] or ""), date=str(b[4] or ""), amount_p=int(b[5] or 0), scan=b[6]))
    scans = scans if scans is not None else (s750_summary_scans(con) or {})
    dealer_of = _s750_dealer_of(con, scans) if scans else {}
    by_dealer = {}
    unknown = []
    for sid, s in scans.items():
        if s.get("month") != month:
            continue
        k = dealer_of.get(sid) or ""
        if not k:
            unknown.append(s)
            continue
        by_dealer.setdefault(k, []).append(s)                 # S848: every summary paper of the dealer for the month
    by_dealer = {k: _s848_one(v) for k, v in by_dealer.items()}   # S848: parts add up; a revision or a repeat -- the newest speaks
    answers = s750_answers(con, month)
    row_of = {int(x["id"]): x for x in (r.get("rows") or [])}
    try:
        rets = [x for x in s740_pending(con) if x.get("month") == month]
    except Exception:                                         # noqa: BLE001
        rets = []
    out = []
    for key in sorted(set(bills) | set(by_dealer), key=lambda k: (bills.get(k) or {}).get("name") or k):
        brow = bills.get(key) or dict(name=key, rows=[])
        d = dict(key=key, name=brow["name"], bills=brow["rows"], marg_p=sum(x["amount_p"] for x in brow["rows"] if x["amount_p"] > 0),
                 returns_p=-sum(x["amount_p"] for x in brow["rows"] if x["amount_p"] < 0), summary=by_dealer.get(key), answer=answers.get((key, month)),
                 why=[], issues=[], explained=True, diff_p=0, holds=False, state="awaited", words="")
        d["net_p"] = d["marg_p"] - d["returns_p"]
        s = d["summary"]
        a = d["answer"]
        if a and a["kind"] == "none":
            d["state"] = "none"
        elif s is None:
            if s749_owner_supplier(con, key):
                d["state"] = "confirm"
            elif running:
                d["state"] = "running"
            else:
                d["state"] = "awaited"
                d["holds"] = counted
        elif not s.get("read"):
            d["state"] = "unreadable"
            d["why"].append("the summary could not be read (%s)" % (s.get("read_error") or "no reading"))
            d["holds"] = counted
        else:
            d["diff_p"] = int((s.get("figure_p") or 0) - d["net_p"])
            if abs(d["diff_p"]) <= S750_TOL_P:
                d["state"] = "agrees"
            else:
                d["state"] = "differs"
                _s750_explain(con, d, s, row_of, rets, cx)
                if d["explained"]:
                    d["holds"] = False
                elif a and a["kind"] in ("carry", "accept"):
                    d["holds"] = False
                else:
                    d["holds"] = counted                       # unanswered, or asked and still waiting
        d["words"] = _s750_words(d)
        out.append(d)
    for s in unknown:
        out.append(dict(key="", name=_s753_not_us((s.get("reading") or {}).get("dealer")) or _s753_not_us(s.get("vendor")) or "a dealer the reader could not name", bills=[],
                        marg_p=0, returns_p=0, net_p=0, summary=s, answer=None, why=["the summary names no dealer of this month -- pick the dealer"],
                        issues=[], explained=False, diff_p=0, holds=counted, state="unknown", words="dealer not recognised"))
    return out


def _s750_explain(con, d, s, row_of, rets, cx):
    """Why the summary and Marg differ, bill by bill. Each unexplained item is an issue of the owner's; an item row 2 or row 6 already carries
    is explained."""
    marg = list(d["bills"])
    used = set()
    s_bills = [x for x in s["lines"] if x["kind"] == "bill"]
    s_credits = [x for x in s["lines"] if x["kind"] == "credit"]
    paper = (cx.paper or {}) if cx is not None else {}
    for ln in s_bills:
        hit = None
        for b in marg:
            if b["id"] in used or b["amount_p"] <= 0:
                continue
            if ln["no"] and _s750_tail_match(ln["no"], b["bill_no"]):
                hit = b
                break
        if hit is None and ln["amount_p"] is not None:
            same = [b for b in marg if b["id"] not in used and b["amount_p"] > 0 and abs(b["amount_p"] - ln["amount_p"]) <= S750_TOL_P
                    and (not ln["date"] or ln["date"] == b["date"])]
            if len(same) == 1:
                hit = same[0]
        if hit is None:
            where = con.execute("SELECT month FROM purchase_bill WHERE supplier_norm=? AND bill_no=? AND month<>? LIMIT 1", (d["key"], ln["no"], s["month"])).fetchone() if ln["no"] else None
            if where:
                d["why"].append("bill %s (%s) is on the summary; Marg has it in %s -- paid on that month's sheet" % (ln["no"], rs(ln["amount_p"]), month_name(where[0])))
                continue
            d["why"].append("bill %s · %s · %s is on the summary; not in Marg, no paper scanned" % (ln["no"] or "?", _s738_dmy(ln["date"]) if ln["date"] else "no date", rs(ln["amount_p"])))
            d["issues"].append(dict(kind="on_summary", no=ln["no"], date=ln["date"], amount_p=ln["amount_p"] or 0))
            d["explained"] = False
            continue
        used.add(hit["id"])
        if ln["amount_p"] is not None and abs(ln["amount_p"] - hit["amount_p"]) > S750_TOL_P:
            row = row_of.get(hit["id"]) or {}
            pp = paper.get(hit.get("scan")) if hit.get("scan") is not None else None
            if row.get("state") in ("amount_differs", "double") and pp is not None and abs(pp - ln["amount_p"]) <= S750_TOL_P:
                d["why"].append("bill %s: summary and paper %s, Marg %s -- row 2, Amir corrects Marg" % (hit["bill_no"], rs(ln["amount_p"]), rs(hit["amount_p"])))
            else:
                d["why"].append("bill %s: summary %s, Marg%s %s -- the dealer's figure differs" % (hit["bill_no"], rs(ln["amount_p"]), " and paper" if pp is not None and abs(pp - hit["amount_p"]) <= S750_TOL_P else "", rs(hit["amount_p"])))
                d["issues"].append(dict(kind="amount", no=hit["bill_no"], date=hit["date"], amount_p=ln["amount_p"] - hit["amount_p"], bill_id=hit["id"]))
                d["explained"] = False
    for b in marg:
        if b["id"] in used or b["amount_p"] <= 0:
            continue
        if not s_bills:
            break                                             # a summary with no bill lines read: only the totals are compared
        d["why"].append("bill %s · %s · %s is in Marg; the summary does not list it" % (b["bill_no"], _s738_dmy(b["date"]), rs(b["amount_p"])))
        d["issues"].append(dict(kind="in_marg_only", no=b["bill_no"], date=b["date"], amount_p=-b["amount_p"], bill_id=b["id"]))
        d["explained"] = False
    for c in s_credits:
        amt = c["amount_p"] or 0
        rhit = [x for x in rets if x.get("supplier") == d["key"] or x.get("sup") == d["key"]]
        rhit = [x for x in rhit if abs(int(x.get("amount_p") or 0) - amt) <= S750_TOL_P] or rhit
        mret = [b for b in marg if b["amount_p"] < 0 and abs(-b["amount_p"] - amt) <= S750_TOL_P]
        if mret:
            d["why"].append("credit %s on the summary = Marg's purchase return %s" % (rs(amt), mret[0]["bill_no"]))
        elif rhit:
            d["why"].append("credit %s on the summary is the return pending on row 6 (%s %s) -- clears when Amir enters the purchase return" % (rs(amt), d["name"], rhit[0].get("bill_no") or ""))
        else:
            d["why"].append("credit %s on the summary; Marg carries no return for it" % rs(amt))
            d["issues"].append(dict(kind="credit", no=c["no"], date=c["date"], amount_p=-amt))
            d["explained"] = False
    for b in marg:
        if b["amount_p"] >= 0 or not s_bills:
            continue
        if not any(abs(-b["amount_p"] - (c["amount_p"] or 0)) <= S750_TOL_P for c in s_credits):
            d["why"].append("Marg's purchase return %s (%s) -- the summary carries no credit note for it; ask the dealer" % (b["bill_no"], rs(-b["amount_p"])))
            d["issues"].append(dict(kind="marg_return_only", no=b["bill_no"], date=b["date"], amount_p=-b["amount_p"], bill_id=b["id"]))
            d["explained"] = False
    if not s_bills and not s_credits and d["diff_p"]:
        pend = [x for x in rets if x.get("supplier") == d["key"] or x.get("sup") == d["key"]]
        if pend and abs(sum(int(x.get("amount_p") or 0) for x in pend) + d["diff_p"]) <= S750_TOL_P:
            d["why"].append("the summary is the return pending on row 6 less -- clears when Amir enters the purchase return")
        else:
            d["why"].append("the summary's figure %s against Marg's %s; the summary's lines were not read, so the reason is not named" % (rs(s.get("figure_p")), rs(d["net_p"])))
            d["issues"].append(dict(kind="total", no="", date="", amount_p=d["diff_p"]))
            d["explained"] = False
    if not d["issues"] and not d["explained"]:
        d["explained"] = True


def _s750_words(d):
    s = d.get("summary") or {}
    if d["state"] == "agrees":
        return "Agrees ✓ · summary scanned %s · %d bill%s · Marg %s" % (ddmon(s.get("day")) or "", len([b for b in d["bills"] if b["amount_p"] > 0]),
                                                                        "" if len(d["bills"]) == 1 else "s", rs(d["net_p"]))
    if d["state"] == "differs":
        more = "more" if d["diff_p"] > 0 else "less"
        return "Summary %s %s than Marg (%s) · scanned %s" % (rs(abs(d["diff_p"])), more, rs(d["net_p"]), ddmon(s.get("day")) or "")
    if d["state"] == "awaited":
        return "Awaited · %d bill%s · Marg %s" % (len(d["bills"]), "" if len(d["bills"]) == 1 else "s", rs(d["net_p"]))
    if d["state"] == "running":
        return "Month running — the summary comes after the month ends · %d bill%s · Marg %s so far" % (len(d["bills"]), "" if len(d["bills"]) == 1 else "s", rs(d["net_p"]))
    if d["state"] == "none":
        return "Gives no summary · Marg %s" % rs(d["net_p"])
    if d["state"] == "confirm":
        return "An owner-confirmed dealer: your Confirm on row 3 counts as the summary · Marg %s" % rs(d["net_p"])
    if d["state"] == "unreadable":
        return "Summary scanned %s, could not be read · Marg %s" % (ddmon(s.get("day")) or "", rs(d["net_p"]))
    return d.get("words") or d["state"]


def s750_open(con, month, r=None):
    """READ ONLY: the dealers' holds of a month -> dict(differ, awaited, unread, asked, carried, accepted, none, agree, n, holds=[words])."""
    if month_class(con, month) != "counted":
        return dict(differ=0, awaited=0, unread=0, asked=0, carried=0, accepted=0, none=0, agree=0, running=0, n=0, holds=[], words="")
    try:
        ds = s750_dealers(con, month, r)
    except Exception as e:                                    # noqa: BLE001 -- fails closed: the month is not clear
        return dict(differ=0, awaited=0, unread=1, asked=0, carried=0, accepted=0, none=0, agree=0, running=0, n=1,
                    holds=["the dealer summaries could not be read (%s)" % str(e)[:80]], words="dealer summaries not read")
    n = dict(differ=0, awaited=0, unread=0, asked=0, carried=0, accepted=0, none=0, agree=0, running=0, n=0, holds=[])
    for d in ds:
        a = d.get("answer") or {}
        if d["state"] == "agrees":
            n["agree"] += 1
        elif d["state"] == "none":
            n["none"] += 1
        elif d["state"] == "differs" and d["holds"] and a.get("kind") == "ask":
            n["asked"] += 1
        elif d["state"] == "differs" and d["holds"]:
            n["differ"] += 1
        elif d["state"] == "differs" and a.get("kind") == "carry":
            n["carried"] += 1
        elif d["state"] == "differs" and a.get("kind") == "accept":
            n["accepted"] += 1
        elif d["state"] in ("awaited",):
            n["awaited"] += 1
        elif d["state"] == "running":
            n["running"] += 1
        elif d["state"] in ("unreadable", "unknown"):
            n["unread"] += 1
    n["n"] = n["differ"] + n["awaited"] + n["unread"] + n["asked"]
    if n["differ"]:
        n["holds"].append("%d dealer summar%s differ%s from Marg (yours: ask the dealer, carry or accept)" % (n["differ"], "y" if n["differ"] == 1 else "ies", "s" if n["differ"] == 1 else ""))
    if n["asked"]:
        n["holds"].append("%d dealer%s asked, waiting for the answer" % (n["asked"], "" if n["asked"] == 1 else "s"))
    if n["awaited"]:
        n["holds"].append("%d dealer summar%s awaited (reception scans it, or you mark the dealer as giving none)" % (n["awaited"], "y" if n["awaited"] == 1 else "ies"))
    if n["unread"]:
        n["holds"].append("%d dealer summar%s could not be read or named" % (n["unread"], "y" if n["unread"] == 1 else "ies"))
    bits = []
    if n["agree"]:
        bits.append("%d agree" % n["agree"])
    if n["differ"] + n["asked"]:
        bits.append("%d differ" % (n["differ"] + n["asked"]))
    if n["awaited"]:
        bits.append("%d awaited" % n["awaited"])
    if n["unread"]:
        bits.append("%d unread" % n["unread"])
    if n["carried"] + n["accepted"]:
        bits.append("%d settled by you" % (n["carried"] + n["accepted"]))
    if n["running"]:
        bits.append("%d after the month ends" % n["running"])
    n["words"] = " · ".join(bits) or ("none" if not ds else "")
    return n


def s750_lock_reasons(con, month):
    """The dealers' holds for the lock gate, in his words; [] when clear."""
    return list(s750_open(con, month).get("holds") or [])


# ------------------------------------------------------------------ s749_month_open / s749_lock_reasons: the dealers hold too (keys kept)
_s749_month_open_before_s750 = s749_month_open
_s749_lock_reasons_before_s750 = s749_lock_reasons


def s749_month_open(con, month, r=None):                      # noqa: F811 -- S750: + dealers; every earlier key and its meaning kept
    n = _s749_month_open_before_s750(con, month, r)
    try:
        dn = s750_open(con, month, r)
    except Exception:                                         # noqa: BLE001 -- fails closed
        dn = dict(n=1, differ=0, asked=0, awaited=0, unread=1, words="not read")
    n["dealers"] = int(dn.get("n") or 0)
    n["dealer_words"] = dn.get("words") or ""
    if n["dealers"]:
        n["open"] = int(n.get("open") or 0) + n["dealers"]
        bits = []
        if dn.get("differ") or dn.get("asked"):
            k = int(dn.get("differ") or 0) + int(dn.get("asked") or 0)
            bits.append("%d dealer summar%s differ%s" % (k, "y" if k == 1 else "ies", "s" if k == 1 else ""))
        if dn.get("awaited"):
            bits.append("%d dealer summar%s awaited" % (dn["awaited"], "y" if dn["awaited"] == 1 else "ies"))
        if dn.get("unread"):
            bits.append("%d dealer summar%s unread" % (dn["unread"], "y" if dn["unread"] == 1 else "ies"))
        n["words"] = " · ".join([n["words"]] + bits) if n.get("words") else " · ".join(bits)
        n["neft"] = "NEFT on hold"
    return n


def s749_lock_reasons(con, month):                            # noqa: F811 -- S750: the dealers' holds join the register's
    out = list(_s749_lock_reasons_before_s750(con, month))
    if month_class(con, month) != "counted":
        return out
    try:
        out.extend(s750_lock_reasons(con, month))
    except Exception as e:                                    # noqa: BLE001 -- fails closed
        out.append("the dealer summaries could not be read (%s)" % str(e)[:80])
    return out


# ------------------------------------------------------------------ the owner's answers (doors in purchase_app: /api/s750/*)
def s750_answer_put(con, who, dealer, month, kind, amount_p=None, note=""):
    """One answer on a dealer's line: ask | carry | accept | none | scan | rescan. Audited; Undo by s750_undo."""
    s750_ensure(con)
    dealer, month, kind = str(dealer or "").strip(), str(month or "").strip(), str(kind or "").strip()
    if kind not in S750_KINDS:
        return False, "That answer is not one of this row's."
    if not re.match(r"^\d{4}-\d\d$", month) or month_class(con, month) != "counted":
        return False, "%s is not a counted month." % (month or "that")
    if not dealer or len(dealer) > 120 or not con.execute("SELECT 1 FROM purchase_bill WHERE supplier_norm=? LIMIT 1", (dealer,)).fetchone():
        return False, "No dealer of that name in Marg."
    fin = _s750_final(con, month)
    if fin:
        return False, ("%s is locked; reopen it first." if fin is True else "%s: the month's status could not be read.") % month_name(month)
    if kind in ("scan", "rescan") and (s750_answers(con, month).get((dealer, month)) or {}).get("kind") == "none":
        return False, "%s gives no summary (your word) -- undo that word first." % dealer
    if kind in ("carry", "accept"):
        ds = [d for d in s750_dealers(con, month) if d["key"] == dealer]
        if not ds:
            return False, "No bills of %s in %s." % (dealer, month_name(month))
        d = ds[0]
        if kind == "carry":
            amount_p = sum(int(i["amount_p"]) for i in d["issues"] if i["kind"] == "on_summary" and int(i["amount_p"]) > 0) if amount_p is None else int(amount_p)
            if amount_p <= 0:
                return False, "Nothing of %s to carry: the summary lists no bill we do not have." % d["name"]
        else:
            amount_p = int((d["summary"] or {}).get("figure_p") or 0) if amount_p is None else int(amount_p)
            if amount_p <= 0:
                return False, "The summary's figure could not be read -- nothing to accept."
    now = _s750_now()
    cur = con.execute("INSERT INTO s750_answer (dealer, month, kind, amount_p, note, by, at) VALUES (?,?,?,?,?,?,?)",
                      (dealer, month, kind, amount_p, str(note or "")[:200], who, now))
    _s736_audit(con, who, "s750_answer", "%s/%s" % (dealer, month), dict(kind=kind, amount_p=amount_p, id=cur.lastrowid, kit=KIT_S750))
    con.commit()
    words = {"ask": "Asked the dealer -- the line waits, 'asked %s'." % ddmon(now[:10]),
             "carry": "%s carried to %s: it shows under Carried in there; %s stops waiting for it." % (rs(amount_p), month_name(_s750_next_month(month)), month_name(month)),
             "accept": "The dealer's figure %s stands on the sheet; Amir's card asks him to enter the bill when its paper comes." % rs(amount_p),
             "none": "%s gives no summary -- from %s on, the lock does not wait for one." % (dealer, month_name(month)),
             "scan": "Reception's list asks for %s's %s summary." % (dealer, month_name(month)),
             "rescan": "Reception's list asks for a rescan of %s's summary." % dealer}
    return True, words[kind]


def _s750_final(con, month):
    """True when the month is locked -- or when its status could not be read (fails closed; the message says which)."""
    try:
        return str((_pa()._month_status(con, month) or {}).get("status") or "") == "final"
    except Exception:                                         # noqa: BLE001 -- fails closed
        return "unread"


def s750_undo(con, who, act_id):
    s750_ensure(con)
    r = con.execute("SELECT id, dealer, month, kind FROM s750_answer WHERE id=? AND undone_at IS NULL", (int(act_id or 0),)).fetchone()
    if not r:
        return False, "That answer is already undone, or was never given."
    fin = _s750_final(con, str(r[2]))
    if fin:
        return False, ("%s is locked; reopen it first." if fin is True else "%s: the month's status could not be read.") % month_name(str(r[2]))
    con.execute("UPDATE s750_answer SET undone_at=?, undone_by=? WHERE id=?", (_s750_now(), who, int(r[0])))
    _s736_audit(con, who, "s750_answer_undone", "%s/%s" % (r[1], r[2]), dict(kind=r[3], id=int(r[0]), kit=KIT_S750))
    con.commit()
    return True, "Undone: %s." % S750_KIND_EN.get(str(r[3]), str(r[3]))


def s750_dealer_pick(con, who, scan, dealer):
    """The owner names the dealer of a summary the reader could not place."""
    s750_ensure(con)
    scan, dealer = int(scan or 0), str(dealer or "").strip()[:120]
    if not scan:
        return False, "Pick a dealer."
    try:
        sc = (s750_summary_scans(con) or {}).get(scan)
    except Exception:                                         # noqa: BLE001
        sc = None
    fin = _s750_final(con, str(sc["month"])) if (sc is not None and sc.get("month")) else False
    if fin:
        return False, ("%s is locked; reopen it first." if fin is True else "%s: the month's status could not be read.") % month_name(str(sc["month"]))
    if not dealer:                                            # the Undo: the scan is nobody's again
        r = con.execute("SELECT dealer FROM s750_dealer_of WHERE scan=?", (scan,)).fetchone()
        if not r:
            return False, "That scan was never named."
        con.execute("DELETE FROM s750_dealer_of WHERE scan=?", (scan,))
        _s736_audit(con, who, "s750_dealer_of_undone", str(scan), dict(dealer=str(r[0]), kit=KIT_S750))
        con.commit()
        return True, "Undone: summary scan %d is nobody's again -- pick the dealer." % scan
    if not con.execute("SELECT 1 FROM purchase_bill WHERE supplier_norm=? LIMIT 1", (dealer,)).fetchone():
        return False, "%s is not a dealer Marg knows." % dealer
    con.execute("INSERT OR REPLACE INTO s750_dealer_of (scan, dealer, by, at) VALUES (?,?,?,?)", (scan, dealer, who, _s750_now()))
    _s736_audit(con, who, "s750_dealer_of", str(scan), dict(dealer=dealer, kit=KIT_S750))
    con.commit()
    return True, "Summary scan %d is %s's." % (scan, dealer)


def s750_reception_asks(con):
    """For Aaj ka bill kaam: [dict(dealer, name, month, kind ('scan'|'rescan'), scan, stamp)] -- the owner's open asks whose summary has not come."""
    out = []
    try:
        scans = s750_summary_scans(con) or {}
        dealer_of = _s750_dealer_of(con, scans) if scans else {}
    except Exception:                                         # noqa: BLE001
        scans, dealer_of = {}, {}
    names = {str(r[0]): str(r[1] or r[0]) for r in con.execute("SELECT DISTINCT supplier_norm, supplier FROM purchase_bill WHERE supplier_norm IS NOT NULL")}
    for (d, m), a in s750_answers(con).items():
        if a["kind"] not in ("scan", "rescan"):
            continue
        have = [s for sid, s in scans.items() if dealer_of.get(sid) == d and s.get("month") == m and str(s.get("day") or "") >= str(a["at"])[:10]]
        if have and (a["kind"] == "scan" or any(s.get("read") for s in have)):
            continue                                          # the paper came (a rescan: and reads) -- the line goes by itself
        last = max([s for sid, s in scans.items() if dealer_of.get(sid) == d and s.get("month") == m], key=lambda s: int(s["id"]), default=None)
        out.append(dict(dealer=d, name=names.get(d, d), month=m, kind=a["kind"], scan=int(last["id"]) if last else None, stamp=(last or {}).get("stamp_no") or "",
                        at=a["at"]))
    return out


def s750_amir_enter(con):
    """For Amir's card: the bills the owner ACCEPTED from a dealer's summary that Marg still does not carry -> [dict(dealer, name, no, date, amount_p, month)]."""
    out = []
    for (d, m), a in s750_answers(con).items():
        if a["kind"] != "accept":
            continue
        try:
            ds = [x for x in s750_dealers(con, m) if x["key"] == d]
        except Exception:                                     # noqa: BLE001
            continue
        for x in ds:
            for i in x["issues"]:
                if i["kind"] == "on_summary":
                    out.append(dict(dealer=d, name=x["name"], no=i["no"], date=i["date"], amount_p=int(i["amount_p"] or 0), month=m))
    return out


# ------------------------------------------------------------------ row 7 and row 8 on the step view
def _s750_panel(d, prefix):
    """The opened part of a dealer's line: the summary's lines as read beside Marg's bills of the month, and the scan (lazy)."""
    s = d.get("summary") or {}
    sid = int(s["id"])
    rows = []
    for ln in (s.get("lines") or [])[:60]:
        rows.append("<tr><th>%s</th><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc({"bill": "Bill", "credit": "Credit", "payment": "Payment"}.get(ln["kind"], "Line")),
                                                                              esc(ln["no"] or "—"), esc(_s738_dm(ln["date"]) if ln["date"] else "—"), esc(rs(ln["amount_p"]))))
    if len(s.get("lines") or []) > 60:
        rows.append("<tr><td colspan='4'>… %d more lines</td></tr>" % (len(s["lines"]) - 60))
    tot = []
    nb = sum(1 for x in (s.get("lines") or []) if isinstance(x, dict) and x.get("kind") == "bill")   # S753: the owner's ask (17:32 IST 8-Nov)
    if s.get("total_bills_p") is not None:
        tot.append(("%d bill%s %s" % (nb, "" if nb == 1 else "s", rs(s["total_bills_p"]))) if nb else ("bills %s" % rs(s["total_bills_p"])))
    elif nb:
        tot.append("%d bill%s" % (nb, "" if nb == 1 else "s"))
    if s.get("dealer_by_bills"):
        tot.append("dealer named by its bills")
    if s.get("opening_p"):
        tot.append("opening %s" % rs(s["opening_p"]))
    if s.get("closing_p") is not None:
        tot.append("closing %s" % rs(s["closing_p"]))
    marg = "".join("<tr><th>Marg</th><td>%s</td><td>%s</td><td>%s</td></tr>" % (esc(b["bill_no"]), esc(_s738_dm(b["date"])), esc(rs(b["amount_p"]))) for b in d["bills"][:60])
    mo = _scan_moment(s) if s else None
    when = ('<div class="s738w">Scanned %s · %s</div>' % (esc(mo.strftime("%d-%m %H:%M")), esc(" · ".join(tot)))) if mo else ""
    when += _s848_parts_html(s, prefix)                      # S848: a summary in parts names every paper
    src = "%s/api/s738/scan/%d" % (prefix, sid)
    return ('<div class="s738vb"><div class="s738f" data-src="%s"></div><div class="s738t"><div class="s738th">Read on the summary · Marg\'s bills</div>'
            '<table><tr><th></th><th>No.</th><th>Date</th><th>Amount</th></tr>%s%s</table>%s<a href="%s" target="_blank" rel="noopener">Open the scan in a new tab</a></div></div>'
            % (esc(src), "".join(rows) or "<tr><td colspan='4'>no lines read</td></tr>", marg, when, esc(src)))


def _s750_line(con, d, month, prefix):
    """One dealer's line in his columns (dealer · the summary's figure, the scan date, the scan, what, whose · next) with its actions."""
    s = d.get("summary") or {}
    a = d.get("answer") or {}
    sid = int(s["id"]) if s.get("id") is not None else None
    what = esc(_s750_words(d))
    who, acts = "", []
    u = prefix + "/api/s750/answer"
    body = dict(dealer=d["key"], month=month)
    undo = (lambda label="Undo": _s749_btn(label, dict(u=prefix + "/api/s750/undo", b=dict(act=int(a["id"])))))
    if d["state"] == "agrees":
        who = "Nobody. Payable %s." % esc(rs(d["net_p"]))
        if a.get("kind") in ("carry", "accept"):
            who += " Your '%s' (%s) is stale -- Marg now carries the bill; undo it." % (esc(S750_KIND_EN[a["kind"]]), esc(rs(a.get("amount_p"))))
            acts.append(undo())
    elif d["state"] == "none":
        who = "Nobody (%s)." % esc(("your word %s" % ddmon(str(a.get("at") or "")[:10])) if a.get("at") else "your standing word")
        if a.get("id"):
            acts.append(undo())
    elif d["state"] == "confirm":
        who = "Row 3."
    elif d["state"] == "running":
        who = "Nobody yet · reception scans the dealer's summary when it comes, early next month."
        acts.append(_s749_btn("%s gives no summary" % d["name"].title(), dict(u=u, b=dict(body, decision="none"))))
    elif d["state"] == "awaited":
        if a.get("kind") == "scan":
            who = "Reception: on Aaj ka bill kaam since %s." % esc(ddmon(str(a.get("at") or "")[:10]))
            acts.append(undo("Undo the ask"))
        else:                                             # S755 / S756: the words follow the month -- a parked month asks nobody
            who = _s756_awaited_words(con, month)
        acts.append(_s749_btn("%s gives no summary" % d["name"].title(), dict(u=u, b=dict(body, decision="none"))))
    elif d["state"] == "unreadable":
        if a.get("kind") == "rescan":
            who = "Reception: rescan asked %s." % esc(ddmon(str(a.get("at") or "")[:10]))
            acts.append(undo("Undo the ask"))
        else:
            who = "Reception rescans it, or you mark the dealer."
            acts.append(_s749_btn("Ask reception to rescan", dict(u=u, b=dict(body, decision="rescan")), "s736b s749y"))
            acts.append(_s749_btn("%s gives no summary" % d["name"].title(), dict(u=u, b=dict(body, decision="none"))))
    elif d["state"] == "differs":
        why = "<br>".join("Why: %s" % esc(w) for w in d["why"][:6]) + ("<br>… %d more" % (len(d["why"]) - 6) if len(d["why"]) > 6 else "")
        nxt = month_name(_s750_next_month(month)).split()[0]
        if d["explained"]:
            who = "%s<br><b>Nothing for you here</b> · it clears through rows 2 and 6." % why
        elif a.get("kind") == "carry":
            who = "%s<br>%s carried to %s by you (%s)." % (why, esc(rs(a.get("amount_p"))), esc(nxt), esc(ddmon(str(a.get("at") or "")[:10])))
            if not any(i["kind"] == "on_summary" for i in d["issues"]):
                who += " <b>That carry is stale</b> · Marg now carries the bill; nothing is carried; undo it."
            acts.append(undo())
        elif a.get("kind") == "accept":
            who = "%s<br>Accepted by you (%s): the dealer's figure %s stands; Amir enters the bill when its paper comes." % (why, esc(ddmon(str(a.get("at") or "")[:10])), esc(rs(a.get("amount_p"))))
            acts.append(undo())
        else:
            if a.get("kind") == "ask":
                who = "%s<br>Asked the dealer %s · waiting." % (why, esc(ddmon(str(a.get("at") or "")[:10])))
                acts.append(undo("Undo the ask"))
            else:
                who = "%s<br><b>Yours.</b>" % why
                acts.append(_s749_btn("Ask the dealer", dict(u=u, b=dict(body, decision="ask")), "s736b s749y"))
            if any(i["kind"] == "on_summary" and int(i["amount_p"]) > 0 for i in d["issues"]):
                acts.append(_s749_btn("Carry to %s" % nxt, dict(u=u, b=dict(body, decision="carry"))))
            acts.append(_s749_btn("Accept the dealer's figure", dict(u=u, b=dict(body, decision="accept"))))
    elif d["state"] == "unknown":
        who = "Pick the dealer: " + _s750_pick_html(con, d, prefix)
    if sid is not None and s.get("picked") and d["state"] != "unknown":
        acts.append(_s749_btn("Not %s summary" % _s755_poss(d["name"].title()), dict(u=prefix + "/api/s750/dealer_of", b=dict(scan=sid, dealer=""))))
    cells = ('<span class="c1">%s%s</span><span class="c2">%s</span><span class="c3">%s</span><span class="c4">%s</span><span class="c5">%s</span>'
             % (esc(d["name"].title()), (" · " + esc(rs(s["figure_p"]))) if s.get("figure_p") is not None else "", esc(_s738_dmy(s.get("day")) if s.get("day") else ""),
                ("scan %s" % esc(s.get("stamp_no") or "")) if sid is not None else "no summary", what, who))
    cls = " s738ok" if d["state"] == "agrees" else ""
    body_h = ('<div class="s749acts">%s</div>' % "".join(acts)) if acts else ""
    if sid is None:
        h = '<div class="s738l%s" data-dealer="%s">%s<span class="c6"></span></div>%s' % (cls, esc(d["key"]), cells, body_h)
    else:
        h = ('<details class="s738v" ontoggle="s738open(this)"><summary class="s738l%s" data-dealer="%s">%s<span class="c6"><span class="s738b">'
             '<span class="sh">Show summary &#9662;</span><span class="hd">Hide summary &#9652;</span></span></span></summary>%s</details>%s'
             % (cls, esc(d["key"]), cells, _s750_panel(d, prefix), body_h))
    if d["key"]:
        h += '<div class="mut" style="margin:-2px 0 6px"><a href="%s/page/ledger/%s">%s ledger</a></div>' % (esc(prefix), esc(_s750_q(d["key"])), esc(_s755_poss(d["name"].title())))
    return h


def _s750_q(key):
    from urllib.parse import quote                            # noqa: PLC0415
    return quote(str(key or ""), safe="")


def _s750_pick_html(con, d, prefix):
    s = d.get("summary") or {}
    names = [(str(r[0]), str(r[1] or r[0]).title()) for r in con.execute("SELECT DISTINCT supplier_norm, supplier FROM purchase_bill WHERE supplier_norm IS NOT NULL ORDER BY supplier")]
    opts = "".join('<option value="%s">%s</option>' % (esc(k), esc(n)) for k, n in names)
    sid = int(s.get("id") or 0)
    return ('<select id="s750pick%d" style="font:inherit;min-height:36px;max-width:100%%"><option value="">— the dealer —</option>%s</select> '
            '<button type="button" class="s736b s749y" onclick=\'var s=document.getElementById("s750pick%d");if(s&&s.value){s749post(this,{u:%s,b:{scan:%d,dealer:s.value}});}\'>This dealer</button>'
            % (sid, opts, sid, json.dumps(prefix + "/api/s750/dealer_of"), sid))


_s749_rows_before_s750 = s749_rows


def s749_rows(con, r, cx, prefix):                            # noqa: F811 -- S750: row 7 is the dealers' summaries; row 8 waits for them too
    rows, open_n = _s749_rows_before_s750(con, r, cx, prefix)
    month = r.get("month") or ""
    try:
        ds = s750_dealers(con, month, r, cx)
        dn = s750_open(con, month, r)
    except Exception as e:                                    # noqa: BLE001 -- the row says so; the strip holds
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S750 row 7: %r" % (e,), file=_sys.stderr)
        rows[6] = ("Dealer summaries", "each dealer's month summary against Marg, returns included", "could not be read",
                   ["<div class='mut'>The dealer summaries could not be read -- the strip holds.</div>"], False)
        return rows, open_n + 1
    counted = r.get("cls") == "counted"
    hdr7 = ('<div class="s738hd"><span>Dealer · summary</span><span>Scanned</span><span>Scan</span><span>What</span><span>Whose · next</span><span></span></div>')
    order = {"differs": 0, "unknown": 0, "unreadable": 1, "awaited": 2, "agrees": 3, "confirm": 4, "running": 5, "none": 6}
    ds = sorted(ds, key=lambda d: (order.get(d["state"], 9), 0 if d.get("holds") else 1, d["name"]))
    l7 = [('<div class="mut"><b>How it works:</b> reception scans each dealer\'s %s summary under Pharmacy with the <i>summary</i> tick. The server reads every bill '
           'on it and its credit notes and holds it against Marg\'s %s bills for that dealer less Marg\'s purchase returns. A dealer agrees when the two are equal '
           'to the rupee. A difference that row 2 (Amir\'s corrections) or row 6 (returns) already explains needs nothing from you. A dealer who gives no summary is marked once and not waited for. '
           'Once the month has ended, every awaited summary is on reception\'s list by itself, and you and Shavez are told each morning until all are in.</div>'
           % (esc(month_name(month)), esc(month_name(month))))]
    if ds:
        l7.append(hdr7)
        l7.extend(_s750_line(con, d, month, prefix) for d in ds)
    else:
        l7.append("No bills of %s yet." % esc(month_name(month)))
    acts = _s750_rows(con, "SELECT id, dealer, month, kind, amount_p, at FROM s750_answer WHERE month=? AND undone_at IS NULL ORDER BY id DESC LIMIT 12", (month,))
    if acts:
        l7.append('<span class="mut"><b>Your answers</b> (undo any):</span>')
        for a_ in acts:
            l7.append('<span class="mut">%s · %s%s (%s)</span><div class="s749acts">%s</div>'
                      % (esc(str(a_[1]).title()), esc(S750_KIND_EN.get(str(a_[3]), str(a_[3]))), (" " + esc(rs(a_[4]))) if a_[4] else "", esc(ddmon(str(a_[5])[:10]) or ""),
                         _s749_btn("Undo", dict(u=prefix + "/api/s750/undo", b=dict(act=int(a_[0]))))))
    l7.append('<div class="mut">Every dealer\'s running ledger · bills with their items, returns, summaries, payments, the balance, item quantities by month and by '
              'financial year: <a href="%s/page/ledger">the dealer ledgers</a>.</div>' % esc(prefix))
    n7 = dn.get("words") or ("none" if not ds else "")
    rows[6] = ("Dealer summaries", "each dealer's month summary against Marg, returns included", n7, l7, False)
    lab8, sub8, n8, l8, g8 = rows[7]
    d_open = int(dn.get("n") or 0) if counted else 0
    open_n = open_n + d_open
    holds7 = []
    k = int(dn.get("differ") or 0) + int(dn.get("asked") or 0)
    if k:
        holds7.append("%d dealer summar%s differ%s" % (k, "y" if k == 1 else "ies", "s" if k == 1 else ""))
    if dn.get("awaited"):
        holds7.append("%d dealer summar%s awaited" % (dn["awaited"], "y" if dn["awaited"] == 1 else "ies"))
    if dn.get("unread"):
        holds7.append("%d dealer summar%s unread" % (dn["unread"], "y" if dn["unread"] == 1 else "ies"))
    if l8 and holds7 and counted:
        first = l8[0]
        if first.startswith("<div>Nothing holds here."):
            first = first.replace("<div>Nothing holds here.", "<div>Holding: %s." % esc(" · ".join(holds7)), 1)
        elif first.startswith("<div>Holding: "):
            first = re.sub(r"^(<div>Holding: [^.]*)\.", lambda m_: m_.group(1) + " · " + esc(" · ".join(holds7)) + ".", first, count=1)
        l8 = [first] + list(l8[1:])
    l8 = list(l8) + ['<div class="mut">D849: the month locks when Marg = the papers (rows 1–6) and Marg = the dealers\' summaries (row 7), and Marg\'s month-end '
                     're-export after the last correction is in · that export is the proof the corrections went in. The NEFT then goes on the dealers\' own figures.</div>']
    rows[7] = (lab8, "opens when rows 2–7 are clear and Marg's re-export after the last correction is in", ("%d open" % open_n) if open_n else "clear", l8, g8)
    return rows, open_n


# ------------------------------------------------------------------ the payment sheet's dealer column (purchase_app reads it)
def s750_sheet(con, month):
    """{dealer key: dict(state, words, figure_p, accepted_p, carried_out_p, carried_in_p, payable_p or None)} for the payment sheet. READ ONLY.
    payable_p is the dealer's figure when the line agrees or the owner accepted it; None when Marg's figure stands."""
    out = {}
    if month_class(con, month) != "counted":
        return out
    cin = s750_carried_in(con, month)
    for d in s750_dealers(con, month):
        if not d["key"]:
            continue
        a = d.get("answer") or {}
        acc = int(a["amount_p"]) if a.get("kind") == "accept" and a.get("amount_p") else None
        car = int(a["amount_p"]) if a.get("kind") == "carry" and a.get("amount_p") else 0
        fig = (d.get("summary") or {}).get("figure_p")
        if d["state"] == "agrees":
            word, pay = "agrees", (int(fig) if fig is not None else None)
        elif d["state"] == "differs" and acc is not None:
            word, pay = "accepted", acc
        elif d["state"] == "differs" and car:
            word, pay = "carried", None
        elif d["state"] == "differs" and d.get("explained"):
            word, pay = "differs · rows 2/6", None
        elif d["state"] == "differs":
            word, pay = "differs · yours", None
        elif d["state"] == "awaited":
            word, pay = "awaited", None
        elif d["state"] == "running":
            word, pay = "month running", None
        elif d["state"] == "none":
            word, pay = "none given", None
        elif d["state"] == "confirm":
            word, pay = "your Confirm", None
        else:
            word, pay = d["state"], None
        out[d["key"]] = dict(state=d["state"], words=word, figure_p=fig, accepted_p=acc, carried_out_p=car, carried_in_p=int(cin.get(d["key"], 0)), payable_p=pay,
                             holds=bool(d.get("holds")))
    for k, v in cin.items():
        out.setdefault(k, dict(state="", words="", figure_p=None, accepted_p=None, carried_out_p=0, carried_in_p=int(v), payable_p=None, holds=False))
    return out
# ---- S750 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S753 (08-Nov-2026, Sanjeevni session 408, kit S753_SUMMARY_SCANS_READ; the owner's word 17:19 - 17:32 IST 08-Nov) ------------------------
#  Reception scans a dealer's month summary on the pharmacy lane like any bill, tick or no tick; the Scan App recognises it by its content
#  (that half is the Scan App's, asked by the owner's prompt S408_SCANAPP_PROMPT_SUMMARY_READ). This half, read only:
#    (1) THE MONTH FROM THE BILLS LISTED (_s753_lines_month): the month most of the summary's bill lines are dated in, before the reader's
#        period_to -- a statement printed "as on 02-11" listing October's bills is October's (Daanshi B-0303, read under November today).
#    (2) NEVER THE PHARMACY ITSELF AS THE DEALER (_s753_not_us): "Sanjeevni Medicos" in any spelling is the BUYER on every statement; a reader
#        or intake that names it is ignored and the dealer is found another way.
#    (3) THE DEALER FROM THE BILLS ON THE PAPER (_s753_dealer_by_bills) -- the FALLBACK, when no printed name matched: each bill line's number
#        and amount is looked for among Marg's purchase bills; the one dealer whose bills they are is the summary's dealer; a short number must be equal, never a tail (L.K. Drug House's
#        statement prints no name: its bills RT-090058 and RT-092205 are L.K.'s in Marg). Two dealers fitting = none; the owner's pick stands
#        first as before (s750_dealer_of). The viewer's footer says "dealer named by its bills".
#    (4) THE COUNT OF BILLS beside their total on the folded viewer's footer ("12 bills ₹65,357") -- the owner's ask, 17:32 IST.
#  purchase_app._s446_file_bytes takes the kinds it may serve; /api/s738/scan serves a Summary too (the doctor only -- Amir's list never
#  carries one). assets.db READ ONLY. Nothing here writes, sends or taps anything.
KIT_S753 = "S753_SUMMARY_SCANS_READ"
_S753_US = re.compile(r"SANJ[EI]+V[AE]?N[IY]\s*MEDICO", re.I)   # the pharmacy's own name, however the reader spells it


def _s753_not_us(name):
    """The name unless it is the pharmacy itself (the buyer on every dealer's statement) -- then ''."""
    s = str(name or "").strip()
    return "" if (not s or _S753_US.search(s)) else s


def _s753_lines_month(lines):
    """The month most of a summary's BILL lines are dated in ('YYYY-MM'), or '' when there are no dated bill lines or two months tie."""
    n = {}
    for ln in lines or []:
        if not isinstance(ln, dict) or ln.get("kind") != "bill":
            continue
        d = str(ln.get("date") or "")
        if re.match(r"^\d{4}-\d\d(-\d\d)?$", d):
            n[d[:7]] = n.get(d[:7], 0) + 1
    if not n:
        return ""
    best = sorted(n.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(best) > 1 and best[0][1] == best[1][1]:
        return ""
    return best[0][0]


def _s753_same_no(a, b):
    """The summary's bill number names Marg's: equal digits when either is short (a 'Z-1' never claims every number ending in 1); a long
    number may be clipped by Marg or prefixed by the dealer ('SF 004043' is '4043'; 'YS/0706/2026-27' is 'YS070620262')."""
    da, db_ = re.sub(r"\D", "", str(a or "")).lstrip("0"), re.sub(r"\D", "", str(b or "")).lstrip("0")
    if not da or not db_:
        return False
    if len(da) < 4 or len(db_) < 4:
        return da == db_
    return da.endswith(db_) or db_.endswith(da)


def _s753_dealer_by_bills(con, s, sups):
    """The one dealer (supplier_norm, among sups) whose Marg bills the summary's bill lines are -- by number tail and amount; '' when none or
    more than one fits. READ ONLY. Used only when no printed name matched (the owner, 17:27 IST 08-Nov: 'a fallback')."""
    lines = [x for x in (s.get("lines") or []) if isinstance(x, dict) and x.get("kind") == "bill" and x.get("amount_p") is not None and x.get("no")]
    if not lines:
        return ""
    hits = {}
    for ln in lines:
        try:
            rows = con.execute("SELECT supplier_norm, bill_no FROM purchase_bill WHERE amount_p=? AND supplier_norm IS NOT NULL", (int(ln["amount_p"]),)).fetchall()
        except sqlite3.Error:
            return ""
        for k in {str(r[0] or "") for r in rows if str(r[0] or "") in sups and _s753_same_no(ln["no"], r[1])}:
            hits[k] = hits.get(k, 0) + 1                      # one per dealer per LINE -- a bill Marg holds twice counts once
    if not hits:
        return ""
    best = sorted(hits.items(), key=lambda kv: (-kv[1], kv[0]))
    if len(best) > 1 and best[0][1] == best[1][1]:
        return ""                                             # two dealers fit as well: the owner picks
    return best[0][0]
# ---- S753 end -------------------------------------------------------------------------------------------------------------------------------



# ---- S755 (08-Nov-2026, Sanjeevni session 408, kit S755_SUMMARY_REMINDERS; D870, F-1190 -- the owner's go 19:10 IST) -------------------------
#  THE AWAITED SUMMARIES CHASE THEMSELVES. Once a month has ended (counted, before the running month), every dealer still AWAITED on row 7
#  -- no summary scanned, no word of the owner's (gives no summary / carried / accepted / asked) -- is on reception's Aaj ka bill kaam by
#  itself: the S750 card without the owner's tap (s750_reception_asks below adds them, auto=True; porders_s454 words the card "the month has
#  ended -- the summary has not come"). The card leaves when the summary comes or the owner marks the dealer. The owner's own ask (the S750
#  door) still stands first and keeps its words. One line a day to the owner and Shavez on the clinic app until none is awaited is
#  owner_notice._part_summaries (its own file). Row 7's awaited line says so; its "Ask reception to scan it" button is gone -- the ask is
#  automatic. Also here: F-1188 (s749_month_open's match counts the accepted and confirmed bills, as row 1's heading does), the possessive
#  (_s755_poss: "A.A. Pharmaceuticals' ledger"), " -- " read as " · " on rows 7 and 8, row 1's body counts as its heading does, row 7's help
#  sentence in plain English. READ ONLY: nothing here writes.
KIT_S755 = "S755_SUMMARY_REMINDERS"


def _s755_poss(name):
    """The possessive of a dealer's name: "Yogendra Agencies' ledger", "Daanshi Pharma's ledger"."""
    s = str(name or "")
    return s + ("'" if s.endswith(("s", "S")) else "'s")


def _s755_ended_months(con):
    """The counted months before the running one, newest first -- the months whose summaries are awaited (D869: the running month never is)."""
    tm = str(today())[:7]
    try:
        ms = months_with_bills(con, 24)
    except Exception:                                         # noqa: BLE001
        return []
    return sorted([m for m in ms if m < tm and month_class(con, m) == "counted"], reverse=True)


def s755_awaited(con, month):
    """The dealers of an ended month still awaited (no summary, no word of the owner's) -> [dict(dealer, name, month, bills, marg_p)]. READ ONLY."""
    out = []
    for d in s750_dealers(con, month):
        if d.get("state") == "awaited" and d.get("key"):
            out.append(dict(dealer=d["key"], name=d["name"], month=month, bills=len(d.get("bills") or []), marg_p=int(d.get("net_p") or 0)))
    return sorted(out, key=lambda x: x["name"])


_s750_reception_asks_before_s755 = s750_reception_asks


def s750_reception_asks(con):                                 # noqa: F811 -- S755: + every awaited dealer of an ended month, by itself
    out = list(_s750_reception_asks_before_s755(con))
    have = {(a["dealer"], a["month"]) for a in out}
    for m in _s755_ended_months(con):
        try:
            aw = s755_awaited(con, m)
        except Exception:                                     # noqa: BLE001 -- the list stands as the owner's asks alone
            continue
        for d in aw:
            if (d["dealer"], m) in have:
                continue
            out.append(dict(dealer=d["dealer"], name=d["name"], month=m, kind="scan", scan=None, stamp="", at="", auto=True))
    return out
# ---- S755 end -------------------------------------------------------------------------------------------------------------------------------



# ---- S756 (09-Nov-2026, Sanjeevni session 412, kit S756_SUMMARY_DEALER_WA; the owner's go 06:31 IST, his wording 06:27 IST) -------------------
#  THE DEALER IS REMINDED, AND THE OWNER SEES OCTOBER ON ONE SCREEN.
#  (1) s756_queue(con, now) -- THE WRITER, called ONLY by owner_notice's five-minute tick (cron), never by a page. From the 7th of the month
#      after an ended counted month (setting summary_wa.from_day, 7), at or after summary_wa.hhmm (11:30 IST), every day, Sundays too: ONE
#      supplier_msg row, kind 'summary', per awaited dealer per day (ref = YYYYMMDD; the table's UNIQUE month/vendor/kind/ref makes it once),
#      the owner's own words with the month in Hindi, to the dealer's payment-message number (the phone book, as the NEFT message uses). No
#      number: the row is 'skipped' with 'number nahi' and the snapshot says "number missing". A paused dealer (s756_pause) gets nothing. The
#      reception phone sends it on the supplier_msg road (/finance/api/supplier-msg/next). An unsent row is withdrawn ('skipped') when the
#      day turns, when its dealer is no longer awaited, or when he is paused -- a phone that was off never sends a backlog.
#      FAILS CLOSED: assets.db unreadable (s750_summary_scans None) -> nothing is queued and everything unsent is withdrawn (every dealer
#      would look awaited). A month with a summary not yet named to a dealer is HELD. A locked month: nothing. A dealer awaited for two
#      months is told of the OLDEST only, one message a day. Failed sends are withdrawn, never retried; nothing is left after 20:00
#      (summary_wa.until). Switches (each also withdraws what is unsent): summary_wa.on = off; owner_notice's ALL_OFF, OWNER_NOTICE_OFF,
#      owner_notice.on.
#  (2) s756_snapshot(con, month, prefix) -- READ ONLY: the top of the purchase check of an ended counted month (the mock he approved,
#      06:31 IST): the counts, the awaited dealers with bills, Marg, days waiting, the last reminder and Pause / Resume, the differences that
#      are his, the rest folded, the parked months named as not chased.
#  (3) Row 7: its count line names every dealer (agree · differ · explained · your confirm · awaited ...); the awaited line of a parked month
#      no longer claims reception's list; of a counted month it says the dealer is reminded too.
#  Pause / Resume: s756_pause_put (the door /api/s756/pause, the doctor only, audited). Nothing here prints a phone number.
KIT_S756 = "S756_SUMMARY_DEALER_WA"
S756_DDL = ("CREATE TABLE IF NOT EXISTS s756_pause (id INTEGER PRIMARY KEY AUTOINCREMENT, dealer TEXT NOT NULL, paused_at TEXT NOT NULL, "
            "paused_by TEXT, resumed_at TEXT, resumed_by TEXT)",)
S756_HI_MONTHS = ("जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई", "जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर")
S756_BODY = "संजीवनी मेडिकोज़, बरेली: %s के बिलों की समरी अभी तक हमें नहीं मिली है। समय से पेमेंट के लिए शीघ्र भेज दें, धन्यवाद।"
S756_CSS = ("#s756{background:#fff;border:1px solid #e3e1da;border-radius:12px;padding:14px 16px;margin:0 0 14px}"
            "#s756 h2{font-size:19px;margin:0}#s756 .k{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:#5d636d}"
            "#s756 .top{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:flex-end}"
            "#s756 .chips{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}#s756 .chip{border-radius:8px;padding:4px 10px;font-weight:700;font-size:14px;background:#eceef2;color:#3a404a}"
            "#s756 .chip.aw{background:#fde9d9;color:#8a3b0c}#s756 .chip.yo{background:#fbeaea;color:#8f1f1f}#s756 .chip.ok{background:#e6f2ea;color:#1d5a33}"
            "#s756 .box{border:1px solid #ecebe6;border-radius:10px;padding:10px 12px;margin:8px 0}#s756 .bh{font-weight:700;margin-bottom:4px}"
            "#s756 .tw{overflow-x:auto}#s756 table{border-collapse:collapse;width:100%;font-size:14.5px}"
            "#s756 th{text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#5d636d;padding:4px 8px;border-bottom:1px solid #e6e3dc}"
            "#s756 td{padding:6px 8px;border-bottom:1px solid #f0eee9;vertical-align:top}#s756 td.r,#s756 th.r{text-align:right}"
            "#s756 .miss{color:#6e4d00;background:#fdf3d7;border-radius:6px;padding:1px 7px;font-weight:700}#s756 .pz{color:#1c4f8f;font-weight:700}"
            "#s756 details{border:1px solid #ecebe6;border-radius:10px;padding:8px 12px;margin:6px 0}#s756 summary{font-weight:700;cursor:pointer}"
            "#s756 .mut{color:#5d636d;font-size:13.5px}#s756 .why{color:#49505c;font-size:14px}")


def _s756_hi(month):
    try:
        return "%s %s" % (S756_HI_MONTHS[int(month[5:7]) - 1], month[:4])
    except (ValueError, IndexError, TypeError):
        return str(month)


def s756_body(month):
    """The owner's words (06:27 IST 9-Nov), the month in Hindi. A list of months (a dealer awaited for two) reads 'अक्टूबर 2026 और नवंबर 2026'."""
    ms = sorted(month) if isinstance(month, (list, tuple)) else [month]
    return S756_BODY % " और ".join(_s756_hi(m) for m in ms)


def _s756_paused(con):
    """{dealer: paused_at} -- the dealers whose reminders the owner paused. {} before the table exists (a read never creates it)."""
    return {str(r[0]): str(r[1]) for r in _s750_rows(con, "SELECT dealer, MAX(paused_at) FROM s756_pause WHERE resumed_at IS NULL GROUP BY dealer")}


def _s756_from(month, con):
    """The first day a dealer of `month` is reminded: summary_wa.from_day (7) of the next month."""
    nm = _s750_next_month(month)
    day = max(1, min(28, int_setting(con, "summary_wa.from_day", 7)))
    try:
        return dt.date(int(nm[:4]), int(nm[5:7]), day)
    except ValueError:
        return None


def _s756_hhmm(con):
    try:
        hh, mm = [int(x) for x in setting(con, "summary_wa.hhmm", "11:30").split(":")[:2]]
        if 0 <= hh < 24 and 0 <= mm < 60:
            return hh, mm
    except ValueError:
        pass
    return 11, 30


def _s756_days(month, d):
    """Days since the month's last day (October on 9-Nov: 9)."""
    nm = _s750_next_month(month)
    try:
        first = dt.date(int(nm[:4]), int(nm[5:7]), 1)
    except ValueError:
        return 0
    return max(0, (d - first).days + 1)


def _s756_ended(con, d):
    """The counted months before d's month, newest first (as _s755_ended_months, on the caller's IST day)."""
    tm = d.strftime("%Y-%m")
    try:
        ms = months_with_bills(con, 24)
    except Exception:                                         # noqa: BLE001
        return []
    return sorted([m for m in ms if m < tm and month_class(con, m) == "counted"], reverse=True)


def _s756_msgs(con, month):
    """{dealer: [rows, newest first]} of a month's kind-'summary' messages -- never the number, never the body."""
    out = {}
    for r in _s750_rows(con, "SELECT id, vendor_norm, ref, status, queued_at, sent_at, last_error, handed_at FROM supplier_msg "
                             "WHERE kind='summary' AND month=? ORDER BY id DESC", (month,)):
        out.setdefault(str(r[1]), []).append(dict(id=int(r[0]), ref=r[2], status=str(r[3]), queued_at=str(r[4] or ""), sent_at=str(r[5] or ""),
                                                   err=str(r[6] or ""), handed_at=str(r[7] or "")))
    return out


def _s756_sm():
    import supplier_msg                                       # noqa: PLC0415 -- beside this file; its queue and the phone book's number
    return supplier_msg


S756_DAY_DDL = "CREATE TABLE IF NOT EXISTS s756_day (day TEXT PRIMARY KEY, at TEXT NOT NULL, queued INTEGER, skipped INTEGER, held TEXT)"
S756_FAILED = "the reception phone could not send it"


def _s756_until(con):
    try:
        hh, mm = [int(x) for x in setting(con, "summary_wa.until", "20:00").split(":")[:2]]
        if 0 <= hh < 24 and 0 <= mm < 60:
            return hh, mm
    except ValueError:
        pass
    return 20, 0


def _s756_withdraw(con, where, args, why):
    """Withdraw (status 'skipped', the reason in last_error) every reminder not yet in the phone's hand that matches `where`. -> rows."""
    try:
        cur = con.execute("UPDATE supplier_msg SET status='skipped', last_error=? WHERE kind='summary' AND "
                          "(status='failed' OR (status='queued' AND handed_at IS NULL)) AND (%s)" % where, (why,) + tuple(args))
        return cur.rowcount or 0
    except sqlite3.OperationalError:                          # no supplier_msg table yet: nothing to withdraw
        return 0


def s756_withdraw_all(con, why):
    """Every reminder not yet in the phone's hand withdrawn -- the switches, the installer's restore, the undo. -> rows. Never raises.
    Counts first: with nothing to withdraw (every tick while a switch is off) it writes nothing."""
    try:
        if not con.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='summary' AND (status='failed' OR (status='queued' AND handed_at IS NULL))").fetchone()[0]:
            return 0
        n = _s756_withdraw(con, "1=1", (), why)
        con.commit()
        return n
    except Exception:                                         # noqa: BLE001
        return 0


def s756_held(ds):
    """A month whose summaries include one not yet named to a dealer ('unknown') is HELD: it may be any awaited dealer's."""
    return any(d.get("state") == "unknown" for d in (ds or []))


def s756_queue(con, now=None):
    """THE WRITER (owner_notice's tick only). -> dict(queued, skipped, withdrawn, held, why | error). Never raises.
    Order (the cold review): FIRST, unconditionally, nothing of an earlier day and no failed reminder is left for the phone (a failed one is
    not retried); then the switch and the day's end withdraw the rest; only then is assets.db read -- unreadable withdraws everything."""
    res = dict(queued=0, skipped=0, withdrawn=0, held="", why="")
    try:
        now = now or dt.datetime.now()
        d0 = now.date()
        ref = int(d0.strftime("%Y%m%d"))
        res["withdrawn"] += _s756_withdraw(con, "COALESCE(ref, 0) <> ?", (ref,), "superseded")
        res["withdrawn"] += _s756_withdraw(con, "status='failed'", (), S756_FAILED)
        con.commit()
        if setting(con, "summary_wa.on", "on").strip().lower() != "on":
            res["withdrawn"] += s756_withdraw_all(con, "switched off")
            res["why"] = "summary_wa.on is off"
            return res
        hh, mm = _s756_hhmm(con)
        uh, um = _s756_until(con)
        mnow = now.hour * 60 + now.minute
        if mnow >= uh * 60 + um:
            res["withdrawn"] += s756_withdraw_all(con, "too late in the day")
            res["why"] = "after summary_wa.until (%02d:%02d)" % (uh, um)
            return res
        SM = _s756_sm()
        SM.ensure(con)
        con.execute(S756_DAY_DDL)
        due = mnow >= hh * 60 + mm
        months = [m for m in _s756_ended(con, d0) if (_s756_from(m, con) or dt.date.max) <= d0]
        done = con.execute("SELECT 1 FROM s756_day WHERE day=?", (d0.isoformat(),)).fetchone() is not None
        unsent = con.execute("SELECT id, month, vendor_norm FROM supplier_msg WHERE kind='summary' AND status='queued' AND handed_at IS NULL").fetchall()
        need = bool(due and months and not done)
        if not need and not unsent:
            con.commit()
            res["why"] = "nothing to do"
            return res
        scans = s750_summary_scans(con)
        if scans is None:
            res["withdrawn"] += s756_withdraw_all(con, "assets.db unreadable")
            res["why"] = "assets.db unreadable -- nothing queued, nothing left for the phone (fails closed)"
            return res
        awaited, held = {}, []
        for m in months:
            if _s750_final(con, m):
                continue                                      # locked (or its status unread): nobody is chased
            ds = s750_dealers(con, m, scans=scans)
            if s756_held(ds):
                held.append(m)                                # a summary not yet named may be any awaited dealer's: the month waits
                continue
            for d in ds:
                if d.get("state") == "awaited" and d.get("key"):
                    awaited[(m, d["key"])] = d
        res["held"] = ",".join(held)
        paused = _s756_paused(con)
        for r in unsent:
            m, key = str(r[1]), str(r[2])
            why = ("paused" if key in paused else "held: a summary of the month is not yet named" if m in held
                   else "no longer awaited" if (m, key) not in awaited else "")
            if why:
                res["withdrawn"] += _s756_withdraw(con, "id=?", (int(r[0]),), why)
        if need:
            by = {}
            for (m, key), d in awaited.items():
                by.setdefault(key, []).append((m, d))
            for key in sorted(by):
                if key in paused:
                    continue
                if con.execute("SELECT 1 FROM supplier_msg WHERE kind='summary' AND vendor_norm=? AND ref=? LIMIT 1", (key, ref)).fetchone():
                    continue                                  # one message per dealer per day, whatever the months
                m0, d = sorted(by[key], key=lambda x: x[0])[0]  # the OLDEST awaited month only (the second review): the row names one month,
                to = SM._digits(con, d["name"])                 # so the re-check above withdraws it exactly when that month is no longer awaited
                if to and con.execute("SELECT 1 FROM supplier_msg WHERE kind='summary' AND ref=? AND to_number=? LIMIT 1", (ref, to)).fetchone():
                    continue                                  # one message a day per NUMBER too (two Marg names of one firm, sister firms)
                SM._queue_row(con, m0, key, d["name"], "summary", ref, to, s756_body(m0), None if to else "number nahi")
                res["queued" if to else "skipped"] += 1
            con.execute("INSERT OR REPLACE INTO s756_day (day, at, queued, skipped, held) VALUES (?,?,?,?,?)",
                        (d0.isoformat(), _s750_now(), res["queued"], res["skipped"], res["held"]))
        con.commit()
        return res
    except Exception as e:                                    # noqa: BLE001 -- the tick goes on; the log says why
        try:
            con.rollback()
            s756_withdraw_all(con, "the queue raised")        # an error leaves nothing for the phone
        except Exception:                                     # noqa: BLE001
            pass
        return dict(res, error=("%s: %s" % (e.__class__.__name__, e))[:160])


def s756_pause_put(con, who, dealer, on):
    """Pause (on) or resume a dealer's reminders. Audited. A pause withdraws his unsent message at once."""
    dealer = str(dealer or "").strip()
    if not dealer or len(dealer) > 120:
        return False, "No dealer named."
    row = con.execute("SELECT supplier FROM purchase_bill WHERE supplier_norm=? AND supplier IS NOT NULL LIMIT 1", (dealer,)).fetchone()
    if not row:
        return False, "No dealer of that name in Marg."
    name = " ".join(str(row[0]).split()).title()
    for ddl in S756_DDL:
        con.execute(ddl)
    now = _s750_now()
    paused = _s756_paused(con)
    if on:
        if dealer in paused:
            return True, "Reminders to %s are already paused." % name
        con.execute("INSERT INTO s756_pause (dealer, paused_at, paused_by) VALUES (?,?,?)", (dealer, now, who))
        try:
            con.execute("UPDATE supplier_msg SET status='skipped', last_error='paused' WHERE kind='summary' AND vendor_norm=? AND "
                        "(status='failed' OR (status='queued' AND handed_at IS NULL))", (dealer,))
        except sqlite3.OperationalError:
            pass
        msg = "Reminders to %s paused · nothing more is sent until you resume." % name
    else:
        if dealer not in paused:
            return True, "Reminders to %s are not paused." % name
        con.execute("UPDATE s756_pause SET resumed_at=?, resumed_by=? WHERE dealer=? AND resumed_at IS NULL", (now, who, dealer))
        hh, mm = _s756_hhmm(con)
        msg = "Reminders to %s resume with the next %02d:%02d message." % (name, hh, mm)
    _s736_audit(con, who, "s756_pause", dealer, dict(on=bool(on), kit=KIT_S756))
    con.commit()
    return True, msg


def _s756_cat(d):
    st = d.get("state")
    if st == "differs":
        if d.get("explained"):
            return "explained"
        return "yours" if d.get("holds") else "settled"
    return {"agrees": "agree", "awaited": "awaited", "confirm": "confirm", "none": "none", "unreadable": "unread", "unknown": "unread",
            "running": "running"}.get(st, "other")


S756_WORDS = (("agree", "%d agree"), ("yours", "%d differ%s"), ("explained", "%d explained"), ("settled", "%d settled by you"),
              ("confirm", "%d your confirm"), ("none", "%d give%s no summary"), ("unread", "%d unread"), ("awaited", "%d awaited"),
              ("running", "%d after the month ends"), ("other", "%d other"))


def _s756_words(ds):
    """Row 7's count line, every dealer named once: '11 agree · 1 differs · 2 explained · 1 your confirm · 6 awaited'."""
    n = {}
    for d in ds:
        c = _s756_cat(d)
        n[c] = n.get(c, 0) + 1
    out = []
    for k, w in S756_WORDS:
        v = n.get(k, 0)
        if not v:
            continue
        if k == "yours":
            out.append(w % (v, "s" if v == 1 else ""))
        elif k == "none":
            out.append(w % (v, "s" if v == 1 else ""))
        else:
            out.append(w % v)
    return " · ".join(out)


def _s756_awaited_words(con, month):
    """Row 7's awaited line, true to the month."""
    if month_class(con, month) != "counted":
        return "Parked month · nobody is asked and nobody is reminded."
    fr = _s756_from(month, con)
    tail = (" · the dealer is reminded on WhatsApp each day from %s" % ddmon(fr.isoformat())) if fr else ""
    return "On reception's list by itself since the month ended · you and Shavez are told each morning until it comes%s." % tail


def _s756_name(d):
    return " ".join(str(d.get("name") or d.get("key") or "").split()).title()


def _s756_last(con, d, month, msgs, paused, fr, d0):
    """The 'Last reminder' cell of an awaited dealer: never a number."""
    key = d["key"]
    if key in paused:
        return '<span class="pz">Paused by you</span> · since %s' % esc(ddmon(paused[key][:10]))
    rows = msgs.get(key) or []
    sent = [r for r in rows if r["status"] == "sent"]
    try:
        has_no = not _s756_sm()._digits(con, d["name"])
    except Exception:                                         # noqa: BLE001
        has_no = False
    if has_no:
        return '<span class="miss">number missing</span> · nothing sent'
    if fr and d0 < fr:
        return "starts %s" % esc(ddmon(fr.isoformat()))
    last = rows[0] if rows else None
    before = (" · %d sent before" % len(sent)) if sent else ""
    if last and last["status"] == "queued":
        return "queued %s · waiting for the reception phone%s" % (esc(ddmon(last["queued_at"][:10]) + " " + last["queued_at"][11:16]), before)
    if last and (last["status"] == "failed" or (last["status"] == "skipped" and last["err"] == S756_FAILED)):
        return "the reception phone could not send it (%s) · tried again next day%s" % (esc(ddmon(last["queued_at"][:10])), before)
    if sent:
        s = sent[0]["sent_at"]
        return "%s %s · %d sent" % (esc(ddmon(s[:10])), esc(s[11:16]), len(sent))
    hh, mm = _s756_hhmm(con)
    return "the first one at %02d:%02d" % (hh, mm)


def s756_snapshot(con, month, prefix):
    """READ ONLY. The snapshot at the top of the purchase check of an ended counted month; '' for any other month."""
    d0 = today()
    if not re.match(r"^\d{4}-\d\d$", str(month or "")) or month >= d0.strftime("%Y-%m") or month_class(con, month) != "counted":
        return ""
    ds = s750_dealers(con, month)
    if not ds:
        return ""
    cats = {}
    for d in ds:
        cats.setdefault(_s756_cat(d), []).append(d)
    aw = sorted(cats.get("awaited", []), key=lambda d: (-int(d.get("net_p") or 0), d["name"]))
    yours = sorted(cats.get("yours", []), key=lambda d: d["name"])
    fr = _s756_from(month, con)
    msgs = _s756_msgs(con, month)
    paused = _s756_paused(con)
    u = prefix + "/api/s750/answer"
    mn = month_name(month)
    h = ['<style>%s</style><div id="s756">' % S756_CSS]
    days = _s756_days(month, d0)
    rem = ("reminders from %s" % ddmon(fr.isoformat())) if fr else ""
    h.append('<div class="top"><div><div class="k">Dealer summaries · %s · one screen</div><h2>Where %s stands</h2></div>'
             '<div class="mut">%s ended %d day%s ago%s</div></div>'
             % (esc(mn), esc(mn.split()[0]), esc(mn.split()[0]), days, "" if days == 1 else "s", (" · " + esc(rem)) if rem else ""))
    chip = []
    chip.append('<span class="chip">%d dealers</span>' % len(ds))
    if aw:
        chip.append('<span class="chip aw">%d awaited · %s</span>' % (len(aw), esc(rs(sum(int(d.get("net_p") or 0) for d in aw)))))
    if yours:
        chip.append('<span class="chip yo">%d differ%s — yours</span>' % (len(yours), "s" if len(yours) == 1 else ""))
    for k, cls, w in (("agree", " ok", "agree"), ("explained", "", "differ, already explained"), ("settled", "", "settled by you"),
                      ("confirm", "", "your confirm"), ("none", "", "give no summary"), ("unread", " yo", "could not be read")):
        if cats.get(k):
            chip.append('<span class="chip%s">%d %s</span>' % (cls, len(cats[k]), esc(w)))
    h.append('<div class="chips">%s</div>' % "".join(chip))
    if aw:
        rows = []
        for d in aw:
            key = d["key"]
            if key in paused:
                btn = _s749_btn("Resume", dict(u=prefix + "/api/s756/pause", b=dict(dealer=key, on=False)), "s736b s749y")
            else:
                btn = _s749_btn("Pause reminders", dict(u=prefix + "/api/s756/pause", b=dict(dealer=key, on=True)))
            rows.append('<tr><td><b>%s</b></td><td class="r">%d</td><td class="r">%s</td><td>%d days</td><td>%s</td><td class="r">%s</td></tr>'
                        % (esc(_s756_name(d)), len(d.get("bills") or []), esc(rs(d.get("net_p"))), days,
                           _s756_last(con, d, month, msgs, paused, fr, d0), btn))
        off = setting(con, "summary_wa.on", "on").strip().lower() != "on"
        hold = ('<div style="margin:4px 0 6px"><span class="miss">Reminders switched off</span> · no dealer is reminded until they are '
                'switched on again (setting summary_wa.on).</div>') if off else ""
        hold += ('<div style="margin:4px 0 6px"><span class="miss">Reminders held</span> · a summary scanned for %s is not yet named to a dealer — '
                'it may be one of these. Pick its dealer on row 7; the reminders go again from the next day.</div>' % esc(mn)) if s756_held(ds) else ""
        h.append('<div class="box"><div class="bh">Awaited · %d — the dealer is reminded each day until it comes · also on reception\'s list</div>%s'
                 '<div class="tw"><table><tr><th>Dealer</th><th class="r">Bills</th><th class="r">Marg</th><th>Waiting</th><th>Last reminder</th><th></th></tr>%s</table></div>'
                 '<div class="mut">A dealer who never sends one: <b>gives no summary</b> on row 7 stops the reminders for good. The message is your own words, '
                 'from the reception phone.</div></div>' % (len(aw), hold, "".join(rows)))
    if yours:
        items = []
        for d in yours:
            s = d.get("summary") or {}
            a = d.get("answer") or {}
            fig = s.get("figure_p")
            dp = (int(fig) - int(d.get("net_p") or 0)) if fig is not None else None
            head = "<b>%s</b> · summary %s · Marg %s%s" % (esc(_s756_name(d)), esc(rs(fig)), esc(rs(d.get("net_p"))),
                                                         (" · %s %s" % (esc(rs(abs(dp))), "short" if dp < 0 else "over")) if dp else "")
            why = "".join('<div class="why">%s</div>' % esc(w) for w in (d.get("why") or [])[:3])
            if a.get("kind") == "ask":
                acts = '<div class="mut">Asked the dealer %s · waiting.</div>' % esc(ddmon(str(a.get("at") or "")[:10]))
            else:
                body = dict(dealer=d["key"], month=month)
                acts = '<div class="s749acts">%s%s</div>' % (_s749_btn("Ask the dealer", dict(u=u, b=dict(body, decision="ask")), "s736b s749y"),
                                                             _s749_btn("Accept the dealer's figure", dict(u=u, b=dict(body, decision="accept"))))
            items.append('<div style="margin:6px 0">%s%s%s</div>' % (head, why, acts))
        h.append('<div class="box"><div class="bh">Differs — yours · %d</div>%s</div>' % (len(yours), "".join(items)))
    if cats.get("unread"):
        h.append('<div class="box"><div class="bh">Could not be read · %d</div><div class="mut">%s · on row 7 below.</div></div>'
                 % (len(cats["unread"]), esc(", ".join(_s756_name(d) for d in cats["unread"]))))

    def fold(k, title, line):
        if cats.get(k):
            h.append('<details><summary>%s</summary><div class="mut" style="padding-top:4px">%s</div></details>'
                     % (title, " · ".join(line(d) for d in sorted(cats[k], key=lambda x: x["name"]))))
    if cats.get("agree"):
        fold("agree", "Agree · %d — nothing for you · payable %s" % (len(cats["agree"]), esc(rs(sum(int(d.get("net_p") or 0) for d in cats["agree"])))),
             lambda d: esc(_s756_name(d)))
    fold("explained", "Differ, already explained · %d — they clear through Amir's corrections and the returns" % len(cats.get("explained", [])),
         lambda d: "%s %s" % (esc(_s756_name(d)), esc(rs(abs(int(d.get("diff_p") or 0))))))
    fold("settled", "Settled by you · %d" % len(cats.get("settled", [])), lambda d: esc(_s756_name(d)))
    fold("confirm", "Your confirm counts as the summary · %d" % len(cats.get("confirm", [])), lambda d: "%s %s" % (esc(_s756_name(d)), esc(rs(d.get("net_p")))))
    fold("none", "Give no summary (your word) · %d" % len(cats.get("none", [])), lambda d: esc(_s756_name(d)))
    other = []
    for m in _s756_ended(con, d0):
        if m == month:
            continue
        try:
            n_aw = len(s755_awaited(con, m))
        except Exception:                                     # noqa: BLE001
            continue
        if n_aw:
            other.append('<a href="%s/page/check?month=%s">%s</a> · %d awaited' % (esc(prefix), esc(m), esc(month_name(m)), n_aw))
    parked = [m.strip() for m in setting(con, "purchase.parked_months", "2026-09").split(",") if m.strip()]
    for m in sorted(parked, reverse=True):
        other.append("%s — parked; not chased" % esc(month_name(m)))
    if other:
        h.append('<details><summary>Earlier months</summary><div class="mut" style="padding-top:4px">%s</div></details>' % "<br>".join(other))
    h.append('</div>')
    return "".join(h)


_s749_rows_before_s756 = s749_rows


def s749_rows(con, r, cx, prefix):                            # noqa: F811 -- S756: row 7's count line names every dealer
    rows, open_n = _s749_rows_before_s756(con, r, cx, prefix)
    try:
        month = r.get("month") or ""
        if month_class(con, month) == "counted" and len(rows) > 6:
            words = _s756_words(s750_dealers(con, month, r, cx))
            if words:
                lab, sub, _n, lines, grey = rows[6]
                rows[6] = (lab, sub, words, lines, grey)
    except Exception as e:                                    # noqa: BLE001 -- the row keeps S750's own count
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S756 row 7 count: %r" % (e,), file=_sys.stderr)
    return rows, open_n


_check_body_before_s756 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S756: the snapshot at the top of an ended month's check
    h = _check_body_before_s756(con, month, prefix, months, r)
    try:
        snap = s756_snapshot(con, month, prefix)
    except Exception as e:                                    # noqa: BLE001 -- the page stands without it
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S756 snapshot: %r" % (e,), file=_sys.stderr)
        snap = ""
    if snap:
        h = h.replace('<div id="s736msg"></div>', '<div id="s736msg"></div>' + snap, 1)
    return h
# ---- S756 end -------------------------------------------------------------------------------------------------------------------------------


# ---- S848_SUMMARY_PARTS (17-Nov-2026, Sanjeevni session 473): a dealer's summary sent in PARTS ------------------------------------------------
#  L.K. Drug House sent October in two papers (B-0296 ₹3,656 mid-month, B-0332 ₹9,178 at the month's end); only the newest spoke, so the
#  dealer read '₹3,656 short' and the month's lock held. Now, for one dealer and one month: when every paper is read, each lists bills, and no
#  bill or credit appears on two papers, the papers are PARTS -- they add up (lines, figure, totals) and the newest paper's id speaks for the
#  scan. Any overlap means a revised or repeated summary: the newest speaks, exactly as before. One paper: unchanged (the same dict).
KIT_S848 = "S848_SUMMARY_PARTS"


def _s848_same(x, y):
    """Two lines of two papers are the same item: the same kind, and the number names the same bill -- or, with a number missing, the same
    amount (to the rupee) on the same date."""
    if x.get("kind") != y.get("kind"):
        return False
    if x.get("no") and y.get("no"):
        return _s750_tail_match(x["no"], y["no"])
    if x.get("amount_p") is None or y.get("amount_p") is None:
        return False
    return abs(int(x["amount_p"]) - int(y["amount_p"])) <= S750_TOL_P and str(x.get("date") or "") == str(y.get("date") or "")


def _s848_parts(papers):
    """True when the papers are parts of one month's summary (see the block's head)."""
    if len(papers) < 2:
        return False
    for p in papers:
        if not p.get("read") or not any(ln.get("kind") == "bill" for ln in (p.get("lines") or [])) or p.get("figure_p") is None:
            return False
    for i, a in enumerate(papers):
        for b in papers[i + 1:]:
            for x in (a.get("lines") or []):
                if x.get("kind") not in ("bill", "credit"):
                    continue
                if any(_s848_same(x, y) for y in (b.get("lines") or [])):
                    return False
    return True


def _s848_one(papers):
    """The summary that speaks for one dealer's month: the newest paper, or -- when the papers are parts -- all of them added up."""
    papers = sorted(papers, key=lambda p: int(p["id"]))
    newest = papers[-1]
    if not _s848_parts(papers):
        return newest
    m = dict(newest)
    m["lines"] = sorted([dict(ln) for p in papers for ln in (p.get("lines") or [])], key=lambda ln: (str(ln.get("date") or ""), str(ln.get("no") or "")))
    for k in ("figure_p", "bills_p", "credits_p"):
        m[k] = sum(int(p.get(k) or 0) for p in papers)
    tb = [p.get("total_bills_p") for p in papers]
    m["total_bills_p"] = sum(int(x) for x in tb) if all(x is not None for x in tb) else None
    m["opening_p"] = papers[0].get("opening_p")
    m["closing_p"] = newest.get("closing_p")
    m["dealer_by_bills"] = any(p.get("dealer_by_bills") for p in papers)
    m["parts"] = [dict(id=int(p["id"]), stamp_no=p.get("stamp_no") or "", figure_p=p.get("figure_p"), day=p.get("day")) for p in papers]
    m["stamp_no"] = " + ".join(str(p.get("stamp_no") or ("#%d" % int(p["id"]))) for p in papers)
    return m


def _s848_parts_html(s, prefix):
    """'From 2 papers: B-0296 · ₹3,656 (open) + B-0332 · ₹9,178 (open)' -- or '' for a summary of one paper."""
    parts = (s or {}).get("parts") or []
    if len(parts) < 2:
        return ""
    bits = ['%s · %s (<a href="%s" target="_blank" rel="noopener">open</a>)' % (esc(p["stamp_no"] or "#%d" % p["id"]), esc(rs(p["figure_p"])),
                                                                                 esc("%s/api/s738/scan/%d" % (prefix, p["id"]))) for p in parts]
    return '<div class="s738w">The dealer sent this month in %d papers: %s — added together.</div>' % (len(parts), " + ".join(bits))
# ---- S848 end -------------------------------------------------------------------------------------------------------------------------------


# ---- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D995): Amir also opens the scans of his card's question ----------------------
_s738_scan_ok_before_s849 = s738_scan_ok


def s738_scan_ok(con, sid, doctor, login):                   # noqa: F811 -- S849
    if _s738_scan_ok_before_s849(con, sid, doctor, login):
        return True
    try:
        import scan_ask                                       # noqa: PLC0415
        return scan_ask.amir_may_see(con, sid)
    except Exception:                                         # noqa: BLE001
        return False
# ---- S849 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S855_MONTH_ASKS (17-Nov-2026, Sanjeevni session 476; the owner 17:08-17:12): a month's open asks -- a Marg report to export again, a
#  bill still marked Wrong -- shown wherever they apply (month_asks.py, one source). Fail-soft: without month_asks, every page as before.
#  Here: the purchase check -- row 8 counts them (no more "clear" while one is open) and the same card stands at the top of the page.
_s749_rows_before_s855 = s749_rows


def s749_rows(con, r, cx, prefix):                            # noqa: F811 -- S855: row 8 carries the month's asks
    rows, open_n = _s749_rows_before_s855(con, r, cx, prefix)
    try:
        month = r.get("month") or ""
        if month and month_class(con, month) == "counted" and len(rows) > 7:
            import month_asks as _ma855                        # noqa: PLC0415
            n, lines = _ma855.row8_lines(con, month)
            if n or lines:
                lab, sub, cnt, l8, grey = rows[7]
                tot = open_n + n
                rows[7] = (lab, sub, ("%d open" % tot) if tot else cnt, list(lines) + list(l8), grey)
                open_n = tot
    except Exception as e:                                    # noqa: BLE001 -- row 8 as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S855 row 8: %r" % (e,), file=_sys.stderr)
    return rows, open_n


_check_body_before_s855 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S855: the month's asks at the top
    h = _check_body_before_s855(con, month, prefix, months, r)
    try:
        if month_class(con, month) == "counted":
            import month_asks as _ma855                        # noqa: PLC0415
            card = _ma855.card_html(con, month, prefix, True, where="check")
            if card:
                at = h.find('<h1 id="s726head">')
                h = (h[:at] + card + h[at:]) if at >= 0 else (card + h)
    except Exception as e:                                    # noqa: BLE001 -- the page as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S855 card: %r" % (e,), file=_sys.stderr)
    return h
# ---- S855 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S857_CHECK_OPEN_PATHS (17-Nov-2026, Sanjeevni session 476; the owner 20:54): the purchase check names what is open --------------------------
#  The strip 'NEFT on hold · N open' names the open items and expands inline: each with its row, whose it is and its full path to resolution
#  (month_asks.open_items, one source); every row holding something open is highlighted; 'Open row N' opens that row in place. Row 7's
#  'your confirm' says which it is: 'settled by your confirmation' (row 3 has nothing waiting) or 'waiting for your confirmation (row 3)'.
#  Fail-soft: without month_asks, the page as before.
import re as _re857
S857_CSS = ("<style>#s726chk details.s857{cursor:pointer}#s726chk details.s857>summary{list-style:none;font-weight:600}"
            "#s726chk details.s857>summary::-webkit-details-marker{display:none}#s726chk .s857tap{font-weight:400;font-size:13px;opacity:.85;white-space:nowrap}"
            "#s726chk .s857i{background:#fff;color:#1d2939;border:1px solid #fedf89;border-radius:8px;padding:8px 10px;margin:8px 0;font-weight:400}"
            "#s726chk .s857i ol{margin:6px 0 4px 18px;padding:0}#s726chk .s857w{font-size:13px;color:#667085}"
            "#s726chk details.row.s857open{border-left:5px solid #dc6803;background:#fffaeb}</style>")
S857_JS = ("<script>function s857row(n){var e=document.getElementById('s857r'+n);if(e){e.open=true;e.scrollIntoView({behavior:'smooth',block:'start'});}"
           "return false;}</script>")


def _s857_words(h, pending):
    if pending:
        h = _re857.sub(r"(\d+) your confirm\b", r"\1 waiting for your confirmation (row 3)", h)
        h = h.replace("Your confirm counts as the summary", "Waiting for your confirmation on row 3 — it will stand as the summary")
        h = h.replace("your Confirm on row 3 counts as the summary", "your confirmation on row 3 is awaited — it will stand as the summary")
    else:
        h = _re857.sub(r"(\d+) your confirm\b", r"\1 settled by your confirmation", h)
        h = h.replace("Your confirm counts as the summary", "Settled by your confirmation — it stands as the summary")
        h = h.replace("your Confirm on row 3 counts as the summary", "settled by your confirmation on row 3 — it stands as the summary")
    return h


def _s857_item(it):
    steps = "".join("<li>%s</li>" % esc(s) for s in it.get("steps") or [])
    return ('<div class="s857i"><b>Row %d · %s</b><div class="s857w">Whose: %s</div><ol>%s</ol>'
            '<a href="#s857r%d" onclick="return s857row(%d)">Open row %d ▸</a></div>'
            % (int(it["row"]), esc(it["what"]), esc(it.get("whose") or ""), steps, int(it["row"]), int(it["row"]), int(it["row"])))


_check_body_before_s857 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S857: what is open, named, with its path
    h = _check_body_before_s857(con, month, prefix, months, r)
    try:
        if month_class(con, month) != "counted":
            return h
        import month_asks as _ma857                            # noqa: PLC0415
        if _ma857.is_off():                                    # its switches (and an older kit's frozen walk) -- the page as before S857
            return h
        items = _ma857.open_items(con, month)
        unread = any(str(it.get("what") or "").startswith("The purchase check could not be read") for it in items)
        if not unread:                                         # review: row 3's state from the same reading; nothing reassuring when unread
            h = _s857_words(h, any(int(it["row"]) == 3 for it in items))
        rows_open = {int(it["row"]) for it in items}
        k = [0]

        def _rid(m):
            k[0] += 1
            n = k[0]
            if n > 8:
                return m.group(0)
            return '<details id="s857r%d" class="row%s' % (n, " s857open" if n in rows_open else "")
        h = _re857.sub(r'<details class="row', _rid, h)
        m = _re857.search(r'<div class="strip hold" id="s726strip">([^<]*)</div>', h)
        if m and items:
            names = "; ".join(it["what"] for it in items[:3]) + (" and %d more" % (len(items) - 3) if len(items) > 3 else "")
            new = ('<details class="strip hold s857" id="s726strip"><summary>%s — %s <span class="s857tap">· tap to see what each needs ▾</span></summary>%s</details>'
                   % (m.group(1), esc(names), "".join(_s857_item(it) for it in items)))
            h = h[:m.start()] + new + h[m.end():]
        h = h + S857_CSS + S857_JS
    except Exception as e:                                    # noqa: BLE001 -- the page as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S857: %r" % (e,), file=_sys.stderr)
    return h
# ---- S857 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S867_CONFIRM_WORDS (18-Nov-2026, Sanjeevni session 481; D1003 item 1) ------------------------------------------------------------------
#  An owner-confirmed dealer (Ravi Medical Agency: no summary; the owner's Confirm on row 3 stands for it) read 'your Confirm' on the payment sheet
#  and 'your Confirm on row 3 counts as the summary' on the dealer ledger and row 7 -- the same words whether he had confirmed or not. Now they
#  say which, PER DEALER, from the ONE tally (_s749_groups: row 3's bills waiting vs confirmed), in the purchase check's own words (S857):
#  'settled by your confirmation' or 'waiting for your confirmation (purchase check, row 3)'. A counted month only (row 3 exists only there).
#  The state, the figures, the holds and the payable never change -- words only. A tally that cannot be read reassures nobody ('see the
#  purchase check, row 3'). Fail-soft: any other error, the words as before. Re-entry guarded (the tally never asks for itself).
import threading as _s867_threading                        # noqa: E402
_S867_IN = _s867_threading.local()
S867_SHORT = {"settled": "settled by your confirmation", "waiting": "waiting for your confirmation (purchase check, row 3)",
              "unread": "your confirmation — see the purchase check, row 3"}
S867_LONG = {"settled": "Settled by your confirmation — it stands as the summary · Marg %s",
             "waiting": "Waiting for your confirmation on row 3 of the purchase check — it will stand as the summary · Marg %s",
             "unread": "Your confirmation stands as the summary — see row 3 of the purchase check for whether it is given · Marg %s"}


def s867_confirm_state(con, month):
    """READ ONLY: {dealer key: 'waiting' | 'settled'} for the owner-confirmed dealers' bills of a month (a bill on row 3 = waiting; only
    confirmed bills = settled; a dealer with neither is not listed), or None when the tally cannot be read."""
    try:
        r = register(con, month)
        g = _s749_groups(con, r, Ctx(con))
    except Exception as e:                                    # noqa: BLE001 -- unread: nothing reassuring
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S867 tally: %r" % (e,), file=_sys.stderr)
        return None
    out = {}
    for x in g.get("confirmed") or []:
        out[str(x.get("supplier") or "")] = "settled"
    for x in g.get("confirm") or []:
        out[str(x.get("supplier") or "")] = "waiting"
    return out


def _s867_states(con, month, keys):
    """{key: 'settled' | 'waiting' | 'unread'} for the given confirm-state dealer keys of a counted month; {} when not counted, inside the
    tally itself, or on any error."""
    if not keys or getattr(_S867_IN, "on", False) or month_class(con, month) != "counted":
        return {}
    _S867_IN.on = True
    try:
        st = s867_confirm_state(con, month)
    finally:
        _S867_IN.on = False
    if st is None:
        return {k: "unread" for k in keys}
    return {k: st[k] for k in keys if k in st}


_s750_dealers_before_s867 = s750_dealers
_s750_sheet_before_s867 = s750_sheet


def s750_dealers(con, month, r=None, cx=None, scans=None):    # noqa: F811 -- S867: an owner-confirmed dealer's words say settled / waiting
    ds = _s750_dealers_before_s867(con, month, r, cx, scans)
    try:
        conf = [d for d in ds if d.get("state") == "confirm"]
        sts = _s867_states(con, month, [d["key"] for d in conf])
        for d in conf:
            s = sts.get(d["key"])
            if s:
                d["words"] = S867_LONG[s] % rs(d.get("net_p") or 0)
    except Exception as e:                                    # noqa: BLE001 -- the words as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S867: %r" % (e,), file=_sys.stderr)
    return ds


def s750_sheet(con, month):                                   # noqa: F811 -- S867: the payment sheet's word for an owner-confirmed dealer
    out = _s750_sheet_before_s867(con, month)
    try:
        keys = [k for k, v in out.items() if v.get("state") == "confirm"]
        sts = _s867_states(con, month, keys)
        for k in keys:
            s = sts.get(k)
            if s:
                out[k] = dict(out[k], words=S867_SHORT[s])
    except Exception as e:                                    # noqa: BLE001 -- the words as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S867: %r" % (e,), file=_sys.stderr)
    return out
# ---- S867 end ---------------------------------------------------------------------------------------------------------------------------
