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
#    total     -- within Rs 1 is equal; up to purchase.total_noise_rs (10) agrees, with the difference shown; more differs. A paper
#                 amount reception typed stands in for the scan's reading.
#  The states of a Marg bill that has a scan -- each in exactly one:
#    Amount differs  -- paired, the total differs by more than the noise (one question; then the paper's amount decides)
#    Verified        -- the total agrees, the bill number agrees, and at least one of supplier and date agrees (the matcher's own rule)
#    Has its scan    -- paired, the total agrees or was not read, and not Verified (reception's "Haan", or the auto-link). Nobody is asked.
#  The auto-link: a scan whose supplier agrees and whose amount is within Rs 1 of EXACTLY ONE unscanned bill of that supplier (dated from
#  porders.scan_from, within 60 days of the scan, not refused for it) is paired with no card (audit auto_link).
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
STATES = ("verified", "has_scan", "amount_differs", "no_scan", "double", "accepted")
STATE_EN = {"verified": "Verified", "has_scan": "Has its scan", "amount_differs": "Amount differs", "no_scan": "No scan",
            "double": "Entered twice in Marg", "accepted": "Accepted without paper"}
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
    """Upper case; punctuation and brackets dropped; '&' = AND; standalone PVT, LTD, P, CO, M/S dropped; a trailing BAREILLY dropped."""
    t = str(s or "").upper()
    t = re.sub(r"\bM\s*/\s*S\b\.?", " ", t)
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
    tc, diff = total(tp, b["amount_p"], cx.noise)
    return dict(supplier=supplier(cx, s.get("vendor"), b["supplier"], cx.chosen.get(sid)), billno=billno(s.get("bill_no"), b["bill_no"]),
                date=date_md(s.get("bill_date"), b["bill_date"]), total=tc, diff=diff, scan_p=tp, paper=(sid in cx.paper))


def verified(a):
    return a["total"] in ("equal", "noise") and a["billno"] == "agree" and (a["supplier"] == "agree" or a["date"] == "agree")


def pair_state(a):
    if a["total"] == "differ":
        return "amount_differs"
    return "verified" if verified(a) else "has_scan"


def sarvam_flags(cx, s, b):
    """The Sarvam counter (F-690): supplier and bill number by the rules; the date as read (a wrong year is a miss here); the total beyond Rs 1."""
    sd = _date(s.get("bill_date"))
    raw_total = s.get("amount_p") if "amount_p" in s else _amount_p(s.get("total_amount"))
    return dict(supplier_ok=int(supplier(cx, s.get("vendor"), b["supplier"]) == "agree"),        # what the scan READ: reception's choice is not a reading
                billno_ok=int(billno(s.get("bill_no"), b["bill_no"]) == "agree"),
                date_ok=int(bool(sd) and sd.isoformat() == str(b["bill_date"])[:10]),
                total_ok=int(raw_total is not None and abs(int(raw_total) - int(b["amount_p"] or 0)) <= 100))


# ------------------------------------------------------------------ the auto-link (used by purchase_app._rematch)
def autolink_choice(cx, s, bills, taken, scan_from, refused=()):
    """The one unscanned bill this scan pairs with by itself, or None: its supplier agrees, its amount is within Rs 1 of EXACTLY ONE
    unscanned bill of that supplier dated from scan_from and within HINT_DAYS of the scan (paper date or scan day), not refused for it."""
    sp = scan_amount(cx, s)
    if sp is None or int(sp) == 0:
        return None
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
    return out[0] if len(out) == 1 else None


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
            st = pair_state(a)
            row.update(scan=l["scan"], stamp=s.get("stamp_no") or ("#%d" % l["scan"]), state=st, agree=a)
            row["note"], row["whose"] = _note(cx, st, a, b, s, l)
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
    if a["total"] == "noise":
        bits.append("Paper %s, %s rounding." % (rs(a["scan_p"]), rs(abs(a["diff"]))))
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
    order = {"no_scan": 0, "amount_differs": 1, "double": 2, "has_scan": 3, "accepted": 4, "verified": 5}
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
