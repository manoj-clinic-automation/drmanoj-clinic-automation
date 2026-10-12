#!/usr/bin/env python3
"""make_s538.py -- kit S538 (session 311, 12-Oct-2026; D714; F-867, F-868, F-869).
Builds the new /root/finance/packs.py from its live bytes (FROM 368aa68c, read whole at S311) by exact, counted, anchored
edits. The new text is built in memory first (F-792); nothing is written unless every anchor occurs exactly once.
    python3 make_s538.py <packs.py FROM> <packs.py out> [<packs.html FROM> <packs.html out>]"""
import hashlib
import sys

FROM_MD5 = "368aa68cfd03176dce99816043390ea1"
HTML_FROM_MD5 = "d25452a51f2f5fdd5c1e2b39b54bd9ff"
HTML_OLD = """      if(r.key==="upi")pv+=' · <a href="/finance/packs/preview/upi?month='+j.month+'">the sheet</a>';"""
HTML_NEW = """      if(r.key==="upi")pv+=' · <a href="/finance/packs/preview/upi?month='+j.month+'">the sheet</a> · <a href="/finance/packs/preview/bankcheck?month='+j.month+'">the clinic bank check (yours only)</a>';"""

DOC_OLD = '''  * the electricity bill a card pays is found in these lines first.
"""'''
DOC_NEW = '''  * the electricity bill a card pays is found in these lines first.

S538 (12-Oct-2026, D714; F-867, F-868, F-869 -- the owner on September's pack: "your current split payment in the doctor's revenue
report is confusing ... test whether this system will remove this inconsistency"; "any other wallet payment not coming through the
email data is not a wallet payment ... only for the Consultation fees"):
  * the income sheet counts every split payment by its REAL parts (clinic_day_tender: Docterz prints "Cash: .., Online Payment: .."
    on the line); there is no "split" lump. A split whose parts the export did not carry is named as such, never guessed.
  * a booking made on Docterz's online appointment page is a CONSULTATION line carrying Razorpay's payment number (pay_...): that
    fee went to the Yes Bank clinic account. Only the consultation line is the booking -- another line of the same visit is
    expected in ICICI (F-869). Any other 'Wallet' is a reception entry error: shown as such and decided against the bank (online
    if the bank received at least that much more than Docterz shows that day, cash if not).
  * the bank check (ICICI), day by day: Docterz's online + card money against the card machine's settlement credited to the
    clinic's ICICI account the NEXT calendar day, with the month's two totals. It is the OWNER'S, kept on his packs page only --
    never in the accountants' workbook or mail, never raised to reception (his word, 07:53 IST 12-Oct: "if the total cash and the
    online payments are satisfactory then we will keep it aside ... in one place where I can see and manage"). The line under
    pack row 2 is likewise his page's only; the accountants' mail no longer carries it.
  * the payment digest is one row per charge: a renewal / confirmation mail and a receipt of the same vendor and amount within
    seven days are one payment, the receipt kept (F-868); the sheet says it is payment papers found in mail, which overlap the
    card spends.
"""'''

FN_ANCHOR = '''def build_income(con, month):
    """(1) the doctor's monthly income sheet + the date-wise clinic ledger, physiotherapy excluded (it is its own unit)."""
    if not _has(con, "clinic_day_revenue"):
        return None, "the clinic day-revenue table is not on this server"
    rows = [dict(r) for r in con.execute("SELECT * FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ? ORDER BY business_date", (month + "-01", _month_end(month)))]
    if not rows:
        return None, "no clinic day revenue rows for %s" % _month_name(month)
    ledger = [("Date", "Consultations (n)", "Consultations Rs", "X-ray (n)", "X-ray Rs", "Procedures (n)", "Procedures Rs", "Total (n)", "Total Rs", "Cash Rs", "Online Rs", "Card Rs", "Split Rs")]
    tot = [0] * 12
    for r in rows:
        t = _tender(r)
        vals = [r["cons_count"] or 0, (r["cons_amount_p"] or 0) / 100.0, r["xray_count"] or 0, (r["xray_amount_p"] or 0) / 100.0, r["proc_count"] or 0, (r["proc_amount_p"] or 0) / 100.0,
                r["total_count"] or 0, (r["total_amount_p"] or 0) / 100.0, t["cash"] / 100.0, t["online"] / 100.0, t["card"] / 100.0, t["split"] / 100.0]
        tot = [a + b for a, b in zip(tot, vals)]
        ledger.append([r["business_date"]] + vals)
    ledger.append(["TOTAL"] + tot)
    income = [("Dr Manoj Agarwal Clinic — income %s" % _month_name(month), ""), ("Days with takings", len(rows)), ("Consultations Rs", tot[1]), ("X-ray Rs", tot[3]),
              ("Procedures Rs", tot[5]), ("Total Rs", tot[7]), ("of which cash Rs", tot[8]), ("of which online Rs", tot[9]), ("of which card Rs", tot[10]), ("of which split Rs (part cash, part online)", tot[11]),
              ("Physiotherapy", "excluded (its own register)"), ("Paper OPD register", "the accountants' own add-on")]
    return _xlsx([("Income", income), ("Ledger date-wise", ledger)]), None
'''

FN_NEW = '''# ---------------------------------------------------------------- S538 (D714; F-867, F-869): the takings by their real parts
S538_BUCKET = {"Cash": "cash", "Online Payment": "online", "Net Banking": "online", "Patient APP": "online", "Debit Card": "card",
               "Credit Card": "card", "Wallet": "wallet", "Split Payment": "split"}
S538_PARTS = ("cash", "online", "card", "portal", "wallet", "split_open", "other")
SETTLE_RE = re.compile(r"ICICIPOS[\\s_]*SET", re.I)      # the card machine's daily settlement into the clinic's ICICI account
CLINIC_ICICI_SLOT = "icici_clinic"


def _is_booking(section, ref):
    """S538 (D714): a booking made on Docterz's online appointment page and paid through Razorpay into the Yes Bank clinic account
    is a CONSULTATION line carrying Razorpay's payment number. Only the consultation fee is the booking (F-869)."""
    return str(section or "").strip().lower() == "consult" and str(ref or "").strip().lower().startswith("pay_")


def _parts_from_tender(r):
    """S538: a day with no lines on the server -- its own tender totals; a split stays unparted (never guessed)."""
    t = dict.fromkeys(S538_PARTS, 0)
    try:
        raw = json.loads(r.get("tender_json") or "{}")
    except (ValueError, TypeError):
        raw = {}
    for label, p in raw.items():
        b = S538_BUCKET.get(str(label).strip())
        t["split_open" if b == "split" else (b or "other")] += int(p or 0)
    return t


def day_parts(con, day):
    """S538 (F-867): one clinic day's takings by their real parts, in paise: cash · online · card · portal (the Razorpay booking,
    consultation fee only) · wallet (a Docterz 'Wallet' with no booking number -- a reception entry error) · split_open (a split
    whose parts the export did not carry) · other (a mode this file does not know). A split payment counts by its own parts
    (clinic_day_tender). None when the server holds no line of that day."""
    if not _has(con, "clinic_day_line"):
        return None
    cols = {r[1] for r in con.execute("PRAGMA table_info(clinic_day_line)")}
    rows = con.execute("SELECT section, mode, amount_p, %s, %s FROM clinic_day_line WHERE business_date=?" % (
        "COALESCE(gateway_ref,'')" if "gateway_ref" in cols else "''", "COALESCE(clinic_id,'')" if "clinic_id" in cols else "''"), (day,)).fetchall()
    if not rows:
        return None
    out = dict.fromkeys(S538_PARTS, 0)
    out["booked"] = 0
    split_lines = 0
    portal_in_split = {}                                  # clinic ID -> the booked fee paid inside a split
    for sec, mode, amt, ref, cid in rows:
        amt = int(amt or 0)
        b = S538_BUCKET.get(str(mode or "").strip())
        if not amt:
            continue
        if _is_booking(sec, ref):
            out["portal"] += amt
            out["booked"] += 1
            if b == "split":
                portal_in_split[cid] = portal_in_split.get(cid, 0) + amt
            continue
        if b == "split":
            split_lines += amt
        else:
            out[b or "other"] += amt
    by_cid = {}                                           # the split parts, patient by patient (clinic ID)
    if _has(con, "clinic_day_tender"):
        tcols = {r[1] for r in con.execute("PRAGMA table_info(clinic_day_tender)")}
        for t, amt, cid in con.execute("SELECT tender, amount_p, %s FROM clinic_day_tender WHERE business_date=?"
                                       % ("COALESCE(clinic_id,'')" if "clinic_id" in tcols else "''"), (day,)):
            b = S538_BUCKET.get(str(t or "").strip())
            pp = by_cid.setdefault(cid, dict(cash=0, online=0, card=0, wallet=0, other=0))
            pp[b if b in pp else "other"] += int(amt or 0)            # a tender word this file does not know is named, never dropped
    # a booked consultation paid as a split: its Razorpay part sits among THAT patient's parts -- taken out once, Wallet first,
    # then online, from that patient's parts only (another patient's Wallet stays an entry error)
    for cid, fee in portal_in_split.items():
        pp = by_cid.get(cid)
        if not pp:
            continue
        for b in ("wallet", "online"):
            take = min(fee, pp[b])
            pp[b] -= take
            fee -= take
    got = 0
    for pp in by_cid.values():
        for b, v in pp.items():
            out[b] += v
            got += v
    out["split_open"] = max(0, split_lines - got)
    return out


def _clinic_icici_refs(con):
    """S538: the clinic's ICICI account as the statement lines name it -- the tails its slot learned and its files carry."""
    r = con.execute("SELECT id, ident_tail FROM stmt_slot WHERE key=?", (CLINIC_ICICI_SLOT,)).fetchone() if _has(con, "stmt_slot") else None
    if not r:
        return set()
    refs = _tailset(r[1])
    for (t,) in con.execute("SELECT tail FROM stmt_file WHERE slot_id=? AND tail IS NOT NULL AND tail<>''", (r[0],)):
        refs |= _tailset(t)
    return refs


def icici_settlements(con, lo, hi):
    """S538: the card machine's settlements credited to the clinic's ICICI account lo..hi -> ({credit date: paise}, [(from, to)]
    -- the periods its statements on the server cover)."""
    refs = sorted(_clinic_icici_refs(con))
    if not refs or not _has(con, "icici_statement_line"):
        return {}, []
    q = ",".join("?" * len(refs))
    out = {}
    for d, desc, dep in con.execute("SELECT txn_date, description, deposit_p FROM icici_statement_line WHERE account_ref IN (%s) AND deposit_p>0 "
                                    "AND txn_date BETWEEN ? AND ?" % q, tuple(refs) + (lo, hi)):
        if SETTLE_RE.search(desc or ""):
            out[d] = out.get(d, 0) + int(dep or 0)
    per = []
    if _has(con, "icici_statement_period"):
        per = [(a, b) for a, b in con.execute("SELECT period_from, period_to FROM icici_statement_period WHERE account_ref IN (%s)" % q, tuple(refs)) if a and b]
    return out, per


def bank_check(con, month):
    """S538 (D714): day by day, Docterz's online + card money (the Razorpay bookings and the 'Wallet' entries left out) against the
    ICICI card machine's settlement credited the NEXT calendar day. A row for every day either side has money. A 'Wallet' entry
    with no booking number is decided against the bank: online if the bank received at least that much more than Docterz shows that
    day, cash if not; undecided while the bank's day is not on the shelf."""
    lo, hi = month + "-01", _month_end(month)
    if not _has(con, "clinic_day_revenue"):
        return []
    rev = {r[0]: dict(r) for r in con.execute("SELECT * FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ?", (lo, hi))}
    settle, per = icici_settlements(con, lo, _iso_plus(hi, 1))
    out = []
    d = lo
    while d <= hi:
        nxt = _iso_plus(d, 1)
        p = None
        if d in rev:
            p = day_parts(con, d) or _parts_from_tender(rev[d])
        doc = (p["online"] + p["card"]) if p else 0
        w = p["wallet"] if p else 0
        known = nxt in settle or any(a <= nxt <= b for a, b in per)
        bank = settle.get(nxt, 0)
        if (not p or (doc == 0 and w == 0)) and bank == 0:
            d = nxt
            continue
        diff = (bank - doc) if known else None
        if not known:
            verdict = "the bank's statement for %s is not on the shelf yet" % _dmy(nxt)
        elif not p:
            verdict = "no Docterz entry this day -- the bank received %s" % _inr(bank)
        elif diff == 0:
            verdict = "same to the rupee" if doc else "no online or card money on either side"
        elif w and diff == w:
            verdict = "the bank received %s more -- exactly the 'Wallet' entry, so it was online money" % _inr(diff)
        elif diff > 0:
            verdict = "the bank received %s more" % _inr(diff)
        else:
            verdict = "the bank received %s less" % _inr(-diff)
        wallet_as = ""
        if w:
            wallet_as = "waiting for the bank" if not known else ("online" if diff >= w else "cash")
        out.append(dict(day=d, docterz=doc, bank=(bank if known else None), credited=nxt, diff=diff, verdict=verdict, wallet=w, wallet_as=wallet_as,
                        exact=bool(known and p and diff == 0 and doc), differs=bool(known and diff and not (w and diff == w)), docterz_day=bool(p)))
        d = nxt
    return out


def build_income(con, month):
    """(1) the doctor's monthly income sheet + the date-wise clinic ledger, physiotherapy excluded (it is its own unit).
    S538 (F-867): every split by its real parts; the Razorpay booking (consultation fee) apart; a 'Wallet' with no booking number
    named as an entry error and decided against the bank. The day-by-day bank check is NOT in this workbook (build_bank_check)."""
    if not _has(con, "clinic_day_revenue"):
        return None, "the clinic day-revenue table is not on this server"
    rows = [dict(r) for r in con.execute("SELECT * FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ? ORDER BY business_date", (month + "-01", _month_end(month)))]
    if not rows:
        return None, "no clinic day revenue rows for %s" % _month_name(month)
    ledger = [("Date", "Consultations (n)", "Consultations Rs", "X-ray (n)", "X-ray Rs", "Procedures (n)", "Procedures Rs", "Total (n)", "Total Rs",
               "Cash Rs", "Online Rs (into ICICI)", "Card Rs (into ICICI)", "Booked online Rs (Razorpay, into Yes Bank)",
               "'Wallet' with no booking Rs (entry error)", "Split, parts not in the export Rs", "Check")]
    tot = [0] * 14
    for r in rows:
        p = day_parts(con, r["business_date"]) or _parts_from_tender(r)
        parts_sum = sum(p[k] for k in S538_PARTS)
        chk = "" if parts_sum == int(r["total_amount_p"] or 0) else "the parts make %s, the day's total is %s" % (_inr(parts_sum), _inr(r["total_amount_p"]))
        if p["other"]:
            chk = (chk + "; " if chk else "") + "%s in a payment mode this sheet does not know" % _inr(p["other"])
        vals = [r["cons_count"] or 0, (r["cons_amount_p"] or 0) / 100.0, r["xray_count"] or 0, (r["xray_amount_p"] or 0) / 100.0, r["proc_count"] or 0, (r["proc_amount_p"] or 0) / 100.0,
                r["total_count"] or 0, (r["total_amount_p"] or 0) / 100.0, p["cash"] / 100.0, p["online"] / 100.0, p["card"] / 100.0, p["portal"] / 100.0,
                p["wallet"] / 100.0, p["split_open"] / 100.0]
        tot = [a + b for a, b in zip(tot, vals)]
        ledger.append([r["business_date"]] + vals + [chk])
    ledger.append(["TOTAL"] + tot + [""])
    bc = bank_check(con, month)
    w_on = sum(x["wallet"] for x in bc if x["wallet_as"] == "online") / 100.0
    w_cash = sum(x["wallet"] for x in bc if x["wallet_as"] == "cash") / 100.0
    w_wait = sum(x["wallet"] for x in bc if x["wallet_as"] == "waiting for the bank") / 100.0
    income = [("Dr Manoj Agarwal Clinic — income %s" % _month_name(month), ""), ("Days with takings", len(rows)), ("Consultations Rs", tot[1]), ("X-ray Rs", tot[3]),
              ("Procedures Rs", tot[5]), ("Total Rs", tot[7]),
              ("of which cash Rs", tot[8]),
              ("of which online Rs (UPI and net banking, into the clinic's ICICI account)", tot[9]),
              ("of which card Rs (the card machine, into the clinic's ICICI account)", tot[10]),
              ("of which booked online Rs (Docterz's appointment page through Razorpay, into the clinic's Yes Bank account; the consultation fee only)", tot[11]),
              ("of which marked 'Wallet' in Docterz with no booking number Rs (a reception entry error)", tot[12])]
    if tot[12]:
        income += [("   of these, the bank shows them as online Rs", w_on), ("   of these, the bank shows them as cash Rs", w_cash)]
        if w_wait:
            income.append(("   not yet decided (the bank's day is not on the shelf) Rs", w_wait))
    income.append(("Split payments", "counted by their own cash / online / card parts (Docterz prints them on the line)"))
    if tot[13]:
        income.append(("of which split payments whose parts the export did not carry Rs", tot[13]))
    income += [("Physiotherapy", "excluded (its own register)"), ("Paper OPD register", "the accountants' own add-on")]
    return _xlsx([("Income", income), ("Ledger date-wise", ledger)]), None


def bank_totals(bc):
    """S538: the month in the bank check's own figures -- (Docterz online + card, the bank's settlements, exact, differ, waiting)."""
    return (sum(x["docterz"] for x in bc), sum(x["bank"] or 0 for x in bc), sum(1 for x in bc if x["exact"]),
            sum(1 for x in bc if x["differs"]), sum(1 for x in bc if x["bank"] is None))


def build_bank_check(con, month):
    """S538 (D714): the OWNER'S bank check -- the month's two totals, then every day. Kept on his packs page only (a preview);
    never attached to the pack, never in its mail."""
    bc = bank_check(con, month)
    if not bc:
        return None, "no clinic day or ICICI settlement for %s" % _month_name(month)
    doc, bank, n_exact, n_diff, n_wait = bank_totals(bc)
    rows = [("Bank check (ICICI) -- %s: Docterz's online + card against the card machine's settlement of the next day" % _month_name(month), "", "", "", "", "", "", ""),
            ("Month: Docterz online + card Rs", doc / 100.0, "", "", "", "", "", ""),
            ("Month: the ICICI card machine settled Rs", bank / 100.0, "", "", "", "", "", ""),
            ("Month: bank minus Docterz Rs", (bank - doc) / 100.0, "", "", "", "", "", ""),
            ("Days the same to the rupee · days that differ%s" % (" · days waiting for the bank" if n_wait else ""),
             "%d · %d%s" % (n_exact, n_diff, (" · %d" % n_wait) if n_wait else ""), "", "", "", "", "", ""),
            ("", "", "", "", "", "", "", ""),
            ("Date", "Docterz online + card Rs", "ICICI card-machine settlement Rs", "credited on", "Bank − Docterz Rs", "What it says",
             "'Wallet' entry Rs", "the 'Wallet' counts as")]
    for x in bc:
        rows.append((x["day"], x["docterz"] / 100.0, (x["bank"] / 100.0) if x["bank"] is not None else "", x["credited"],
                     (x["diff"] / 100.0) if x["diff"] is not None else "", x["verdict"], (x["wallet"] / 100.0) if x["wallet"] else "", x["wallet_as"]))
    return _xlsx([("Bank check %s" % month, rows)]), None
'''

DIG_OLD = '''        seen.add(key)
        kept.append(dict(date=r[0], vendor=r[1], desc=desc, amount=amt, in_drive=r[5]))
        total += amt or 0
    return kept, dropped, round(total, 2)
'''
DIG_NEW = '''        seen.add(key)
        kept.append(dict(date=r[0], vendor=r[1], desc=desc, amount=amt, in_drive=r[5]))
        total += amt or 0
    return _one_row_per_charge(kept, dropped)


NOTICE_WORDS = ("RENEWAL", "CONFIRM")                                                 # S538 (F-868)
RECEIPT_WORDS = ("RECEIPT", "INVOICE", "PAYMENT SUCCESSFUL", "PAYMENT RECEIVED", " PAID", "PAID ")   # not PREPAID / UNPAID
DIGEST_PAIR_DAYS = 7


def _one_row_per_charge(kept, dropped):
    """S538 (F-868): one charge, one row -- a renewal or confirmation mail and a receipt of the same vendor and amount within
    DIGEST_PAIR_DAYS days are one payment, and the receipt is kept. Two receipts are never paired (they are two charges).
    (kept, dropped, total Rs)."""
    def kind(r):
        up = str(r.get("desc") or "").upper()
        return "receipt" if any(w in up for w in RECEIPT_WORDS) else ("notice" if any(w in up for w in NOTICE_WORDS) else "")

    def gap(a, b):
        try:
            return abs((dt.date.fromisoformat(str(a)[:10]) - dt.date.fromisoformat(str(b)[:10])).days)
        except (TypeError, ValueError):
            return 9999
    gone = set()
    for i, n in enumerate(kept):
        if kind(n) != "notice" or not n.get("amount"):
            continue
        best = None
        for j, r in enumerate(kept):
            if j == i or kind(r) != "receipt" or not r.get("amount"):
                continue
            if " ".join(str(r.get("vendor") or "").upper().split()) != " ".join(str(n.get("vendor") or "").upper().split()):
                continue
            if round(float(r["amount"]), 2) != round(float(n["amount"]), 2):
                continue
            g = gap(r.get("date"), n.get("date"))
            if g <= DIGEST_PAIR_DAYS and (best is None or g < best[0]):
                best = (g, j)
        if best:
            gone.add(i)
            dropped.append(dict(date=n["date"], vendor=n["vendor"], why="the same charge as the receipt of %s" % _dmy(kept[best[1]]["date"])))
    kept = [r for i, r in enumerate(kept) if i not in gone]
    return kept, dropped, round(sum((r["amount"] or 0) for r in kept), 2)
'''

BD_OLD = '''    rows = [("Date", "Vendor", "Description", "Amount Rs", "Attachment in Drive")]
    kept, dropped, total = digest_rows(con, month)
    for r in kept:
        rows.append((r["date"], r["vendor"], r["desc"], r["amount"] if r["amount"] is not None else "see the receipt", "yes" if r["in_drive"] else ""))
    if len(rows) == 1:
        return None, "no payments in the payment register for %s" % _month_name(month)
    rows.append(("", "", "TOTAL (rows with an amount)", total, ""))
    return _xlsx([("Payments %s" % month, rows)]), None
'''
BD_NEW = '''    rows = [("Payment papers found in mail, %s -- one row per charge; most were paid by card, so these overlap the card spends" % _month_name(month), "", "", "", ""),
            ("Date", "Vendor", "Description", "Amount Rs", "Attachment in Drive")]                     # S538 (F-868)
    kept, dropped, total = digest_rows(con, month)
    for r in kept:
        rows.append((r["date"], r["vendor"], r["desc"], r["amount"] if r["amount"] is not None else "see the receipt", "yes" if r["in_drive"] else ""))
    if len(rows) == 2:
        return None, "no payments in the payment register for %s" % _month_name(month)
    rows.append(("", "", "TOTAL (rows with an amount)", total, ""))
    return _xlsx([("Payment papers %s" % month, rows)]), None
'''

UPI_OLD = '''def clinic_upi_check(con, month):
    """S434, the owner's page only: the clinic's UPI as the bank saw it against the takings paid online (+ split)."""
    try:
        bank = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM upi_txn WHERE unit='clinic' AND substr(txn_date,1,7)=?", (month,)).fetchone()[0] or 0
        on = sp = 0
        for r in con.execute("SELECT * FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ?", (month + "-01", _month_end(month))):
            t = _tender(dict(r))
            on += t["online"]
            sp += t["split"]
        return "clinic: the bank's UPI %s · takings paid online %s + split %s (part online) · difference %s" % (_inr(bank), _inr(on), _inr(sp), _inr(bank - on - sp))
    except Exception:                                    # noqa: BLE001
        return ""
'''
UPI_NEW = '''def clinic_upi_check(con, month):
    """S434, the owner's page only. S538 (D714): Docterz's online + card money (splits by their parts) against the ICICI card
    machine's settlements, day by day -- the counts of the income workbook's Bank check sheet."""
    try:
        bc = bank_check(con, month)
        if not bc:
            return ""
        doc, bank, n_exact, n_diff, n_wait = bank_totals(bc)
        gap = bank - doc
        return ("clinic, the month: Docterz online + card %s · the ICICI card machine settled %s (%s) · %d day%s the same to the rupee, "
                "%d differ%s -- the bank check, here only (not sent)" % (
                    _inr(doc), _inr(bank), "the same" if not gap else ("%s more at the bank" % _inr(gap) if gap > 0 else "%s less at the bank" % _inr(-gap)),
                    n_exact, "" if n_exact == 1 else "s", n_diff, (", %d waiting for the bank" % n_wait) if n_wait else ""))
    except Exception:                                    # noqa: BLE001
        return ""
'''

ROW7_OLD = '''    row("digest", "7 · Monthly payment digest", "ready" if b else "missing",'''
ROW7_NEW = '''    row("digest", "7 · Payment papers found in mail (one row per charge; they overlap the card spends)", "ready" if b else "missing",'''

UPIROW_OLD = """    row("upi", "2 · UPI totals + the cash/UPI correction report", "ready" if b else "missing", why or "", [("UPI totals and pharmacy corrections - %s.xlsx" % _month_name(month), b, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")] if b else None, None)
"""
UPIROW_NEW = UPIROW_OLD + """    rows[-1]["owner_only_why"] = bool(b)                              # S538: the clinic line under it is his page's only, never the mail
"""
MAIL_OLD = """            body.append("%s  [%s]%s" % (r["title"], r["status"], ("  " + r["why"]) if r["why"] else ""))"""
MAIL_NEW = """            body.append("%s  [%s]%s" % (r["title"], r["status"], ("  " + r["why"]) if (r["why"] and not r.get("owner_only_why")) else ""))   # S538"""
PV_OLD = """    elif key.startswith("bundle_"):
        b, why = build_bundle(con, m, key[7:])"""
PV_NEW = """    elif key == "bankcheck":                                          # S538: the owner's bank check, kept here only
        b, why = build_bank_check(con, m)
        name, mime = "Bank check (ICICI) - %s.xlsx" % _month_name(m), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif key.startswith("bundle_"):
        b, why = build_bundle(con, m, key[7:])"""

CHK_OLD = """        return (bool(r) and r["status"] == "ready"), (r["why"] if r else "")"""
CHK_NEW = """        return (bool(r) and r["status"] == "ready"), ((r["why"] if not r.get("owner_only_why") else "") if r else "")   # S538: the owner's line stays his"""

EDITS = [("docstring", DOC_OLD, DOC_NEW), ("build_income", FN_ANCHOR, FN_NEW), ("digest_rows", DIG_OLD, DIG_NEW),
         ("build_digest", BD_OLD, BD_NEW), ("clinic_upi_check", UPI_OLD, UPI_NEW), ("row 7", ROW7_OLD, ROW7_NEW),
         ("upi row", UPIROW_OLD, UPIROW_NEW), ("mail body", MAIL_OLD, MAIL_NEW), ("preview", PV_OLD, PV_NEW), ("checklist words", CHK_OLD, CHK_NEW)]


def build_html(src_bytes):
    if hashlib.md5(src_bytes).hexdigest() != HTML_FROM_MD5:
        raise SystemExit("packs.html FROM is %s, expected %s -- nothing built" % (hashlib.md5(src_bytes).hexdigest(), HTML_FROM_MD5))
    text = src_bytes.decode("utf-8")
    if text.count(HTML_OLD) != 1:
        raise SystemExit("anchor 'packs.html upi link' occurs %d times -- nothing built" % text.count(HTML_OLD))
    return text.replace(HTML_OLD, HTML_NEW).encode("utf-8")


def build(src_bytes):
    if hashlib.md5(src_bytes).hexdigest() != FROM_MD5:
        raise SystemExit("FROM is %s, expected %s -- nothing built" % (hashlib.md5(src_bytes).hexdigest(), FROM_MD5))
    text = src_bytes.decode("utf-8")
    for name, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            raise SystemExit("anchor '%s' occurs %d times -- nothing built" % (name, n))
        text = text.replace(old, new)
    return text.encode("utf-8")


if __name__ == "__main__":
    with open(sys.argv[1], "rb") as fh:
        out = build(fh.read())
    with open(sys.argv[2], "wb") as fh:
        fh.write(out)
    print("built %s md5 %s (%d edits)" % (sys.argv[2], hashlib.md5(out).hexdigest(), len(EDITS)))
    if len(sys.argv) >= 5:
        with open(sys.argv[3], "rb") as fh:
            h = build_html(fh.read())
        with open(sys.argv[4], "wb") as fh:
            fh.write(h)
        print("built %s md5 %s (1 edit)" % (sys.argv[4], hashlib.md5(h).hexdigest()))
