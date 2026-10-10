"""card_lines.py -- S504 (10-Oct-2026, session 304). The card statements, read line by line on the server.

THE OWNER, 10-Oct-2026: the card sheet "is too crude, the explanation of the spend needs a look for being properly categorised
for me and accountant use ... like COCO is the main petrol pump where fuel is filled".

What it does. Every card statement on the shelf (the decrypted twin, or the original the shelf opened itself) is read here,
every line of it -- HDFC Business Regalia (its 2025 layout and its present one) and ICICI's (Amazon Pay, Coral) -- and the
statement is PROVED: the debits read must add up to the 'Purchases' the statement prints and the credits to its 'Payments /
Credits'. A statement that does not prove is kept, shown, and never put in a pack as if whole.

Each line gets a KIND (spend, refund, card repayment, fuel surcharge or its waiver, EMI principal, interest / fee / tax) and a
MERCHANT -- the narration with its reference numbers, card numbers, clock times and trailing 'IN' taken off. A merchant has
ONE category, named once (seeded below for the ones already known; the rest are listed on the packs page for the owner to
name), and each category carries two words: a plain one for the owner and the ledger the accountant posts it to.

Read-only towards everything but its own four tables (card_stmt, card_line, card_merchant, card_category). Never prints a
card number in full: a card is its last four. Idempotent on the statement's sha256.
"""
import datetime as dt
import hashlib
import os
import re
import subprocess

# ------------------------------------------------------------------------------------------------ the categories (owner, ledger)
CATEGORIES = (
    # key            owner's word                       the accountant's ledger
    ("fuel",        "Fuel (petrol / diesel)",           "Fuel Expenses"),
    ("electricity", "Electricity bill",                 "Electricity Charges"),
    ("gas",         "Cooking gas",                      "Household Expenses (Personal)"),
    ("phone",       "Phone & internet",                 "Telephone & Internet Charges"),
    ("software",    "Software & subscriptions",         "Software & Subscriptions"),
    ("apps",        "Apps & entertainment (Apple, Google Play)", "Personal Expenses (Drawings)"),
    ("tax",         "Income tax",                       "Income Tax (Drawings)"),
    ("insurance",   "Insurance premium",                "Insurance Premium"),
    ("medical",     "Medical & lab tests",              "Medical Expenses"),
    ("grocery",     "Groceries & household",            "Household Expenses (Personal)"),
    ("shopping",    "Online shopping (Amazon etc.)",    "Personal Expenses (Drawings)"),
    ("clothes",     "Clothes & personal",               "Personal Expenses (Drawings)"),
    ("food",        "Food & dining",                    "Food & Entertainment"),
    ("travel",      "Travel & hotels",                  "Travelling Expenses"),
    ("clinic",      "Clinic purchases",                 "Clinic Expenses"),
    ("equipment",   "Equipment (EMI purchases)",        "Equipment Purchase"),
    ("transfer",    "Money to a person",                "Drawings (Personal)"),
    ("charges",     "Bank charges, interest & GST",     "Bank Charges & Interest"),
    ("repayment",   "Card bill paid",                   "Card Payment (Contra)"),
    ("unnamed",     "Not named yet",                    "Suspense (to be named)"),
)
CAT = {k: (o, l) for k, o, l in CATEGORIES}

# merchant words -> category, the ones already known (the owner names the rest once, on the packs page; his word wins)
SEED = (
    ("COCO", "fuel"), ("INDIAN OIL", "fuel"), ("SHAKTI SERVICE", "fuel"), ("EVERGREEN SERVICE", "fuel"), ("BHARAT PETRO", "fuel"),
    ("HINDUSTAN PETRO", "fuel"), ("HPCL", "fuel"), ("BPCL", "fuel"), ("FILLING STATION", "fuel"), ("PETROL", "fuel"), ("FUEL", "fuel"),
    ("UPPCL", "electricity"), ("ELECTRICITY", "electricity"), ("CENTRAL U.P. GAS", "gas"), ("CENTRAL UP GAS", "gas"),
    ("AIRTEL", "phone"), ("JIO", "phone"), ("VODAFONE", "phone"), ("BSNL", "phone"),
    ("ANTHROPIC", "software"), ("CANVA", "software"), ("CLICKUP", "software"), ("SARVAM", "software"), ("DEEPSTASH", "software"),
    ("GODADDY", "software"), ("GOOGLE CLOUD", "software"), ("GOOGLE WORKSPACE", "software"), ("OPENAI", "software"),
    ("NOTION", "software"), ("HOSTINGER", "software"), ("ZOHO", "software"), ("MICROSOFT", "software"),
    ("APPLE", "apps"), ("GOOGLE PLAY", "apps"), ("NETFLIX", "apps"), ("SPOTIFY", "apps"), ("YOUTUBE", "apps"),
    ("IT CC", "tax"), ("INCOME TAX", "tax"), ("ICICI LOMBARD", "insurance"), ("NATIONAL INSURANCE", "insurance"), ("LIC ", "insurance"), ("STAR HEALTH", "insurance"),
    ("LAL PATHLABS", "medical"), ("PHARM", "medical"), ("BLINKIT", "grocery"), ("AMAZON PAY IN GROCERY", "grocery"),
    ("BIGBASKET", "grocery"), ("ZEPTO", "grocery"), ("SWIGGY INSTAMART", "grocery"),
    ("AMAZON", "shopping"), ("FLIPKART", "shopping"), ("MYNTRA", "clothes"), ("ENVOGUE", "clothes"), ("P AND R THE LABEL", "clothes"),
    ("CAFE COFFEE DAY", "food"), ("ZOMATO", "food"), ("SWIGGY", "food"), ("RESTAURANT", "food"),
    ("HOTEL", "travel"), ("MAKEMYTRIP", "travel"), ("IRCTC", "travel"), ("INDIGO", "travel"), ("UBER", "travel"), ("OLA ", "travel"),
)

KIND_WORDS = (   # (kind, words in the narration) -- the order matters; the first that fits wins
    ("repayment", ("BPPY CC PAYMENT", "CC PAYMENT", "AUTODEBIT PAYMENT", "CREDIT CARD PAYMENT", "PAYMENT RECEIVED", "NETBANKING TRANSFER", "PAYMENT RECD", "BBPS PAYMENT RECEIVED", "THANK YOU")),
    ("fuel_charge", ("FUEL SURCHARGE", "PETRO SURCHARGE")),
    ("emi_principal", ("PRINCIPAL AMOUNT AMORTIZATION", "PRINCIPAL AMOUNT")),
    ("charges", ("INTEREST AMOUNT AMORTIZATION", "IGST", "CGST", "SGST", "GST ", "DCC TRANSACTION", "MARKUP", "FINANCE CHARGE",
                 "LATE PAYMENT", "ANNUAL FEE", "PROCESSING FEE", "INTEREST")),
)

_D = r"(\d{2}/\d{2}/\d{4})"
_AMT = r"([\d,]+\.\d{1,2})"
MON = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


class CardStatementError(ValueError):
    pass


def _p(s):
    """'1,37,319.84' -> 13731984 paise."""
    s = str(s).replace(",", "").strip()
    if not re.match(r"^\d+(\.\d{1,2})?$", s):
        raise CardStatementError("not an amount: %r" % s[:20])
    w, _, f = s.partition(".")
    return int(w) * 100 + int((f + "00")[:2])


def _iso(d):
    return "%s-%s-%s" % (d[6:10], d[3:5], d[0:2])


def _words_date(s):
    """'September 12, 2026' / '15 Sep, 2026' -> '2026-09-12'."""
    m = re.search(r"([A-Za-z]{3})[a-z]*\.?\s+(\d{1,2}),\s*(\d{4})", s)
    if m and m.group(1).lower() in MON:
        return "%s-%02d-%02d" % (m.group(3), MON[m.group(1).lower()], int(m.group(2)))
    m = re.search(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*,?\s+(\d{4})", s)
    if m and m.group(2).lower() in MON:
        return "%s-%02d-%02d" % (m.group(3), MON[m.group(2).lower()], int(m.group(1)))
    return None


def pdf_text(path):
    r = subprocess.run(["pdftotext", "-layout", path, "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
    return r.stdout.decode("utf-8", "replace")


def merchant_of(desc):
    """The merchant, as words: reference numbers, card numbers, UPI ids, clock times and a trailing country code taken off."""
    s = desc.upper()
    s = re.sub(r"\(REF#.*?\)?$", " ", s)
    s = re.sub(r"\bREF#\s*\S+", " ", s)
    s = re.sub(r"^UPI-\d+-", "", s)
    s = re.sub(r"^\d{2}:\d{2}(:\d{2})?\s+", "", s)
    s = re.sub(r"<\d+/\d+>", " ", s)
    s = re.sub(r"HTTPS?://\S*", " ", s)
    s = re.sub(r"\s+\d+\s+[\d.]+$", " ", s)                       # a reward and a foreign amount run into the narration
    s = re.sub(r"\s+[+-]\s*\d+\s*$", " ", s)
    s = re.sub(r"\d{4,}", " ", s)
    s = re.sub(r"\b\d[\d\-*/]{3,}\b", " ", s)
    s = re.sub(r"\*", " ", s)
    s = re.sub(r"^(EMI|RAZ|IND|PAY|SI)\s+", "", s)
    s = re.sub(r"\s+(IN|US|GB|SG|IE|CA|KA|TN|G)\s*$", "", s)
    s = re.sub(r"\s+(IN|US|GB|SG|IE|CA|KA|TN|G)\s*$", "", s)
    s = re.sub(r"\s+", " ", s).strip(" -.,")
    return s[:60]


def kind_of(desc, credit):
    u = desc.upper()
    for k, words in KIND_WORDS:
        if any(w in u for w in words):
            if k == "repayment" and not credit:
                continue
            return k
    return "refund" if credit else "spend"


def _emi_merchant(desc):
    m = re.search(r"AMORTIZATION\s*-\s*(?:<\d+/\d+>)?\s*(.+)$", desc, re.I)
    return merchant_of(m.group(1)) if m else None


# ------------------------------------------------------------------------------------------------ the layouts
def _parse_icici(lines):
    out, tail = [], ""
    for i, ln in enumerate(lines):
        mt = re.search(r"(?:^|\s)(\d{4})X{4,10}(\d{4})\s*$", ln)
        if mt:
            tail = mt.group(2) if mt.group(1) != "0000" else ""     # '0000XXXX....' heads the payments received, not a card
            continue
        m = re.search(r"(?:^|\s)" + _D + r"\s+(\d{8,})\s+(.*?)\s*$", ln)     # the spends overview may print beside a line
        if not m:
            continue
        toks = [t for t in re.split(r"\s{2,}", m.group(3)) if t]
        if not toks:
            continue
        am = re.match(r"^" + _AMT + r"(?:\s+(CR|Cr|DR|Dr))?$", toks[-1])
        if not am:
            continue
        toks = toks[:-1]
        intl = ""
        if toks and re.match(r"^[\d.,]+\s+[A-Z]{3}$", toks[-1]):
            intl = toks.pop()
        if toks and re.match(r"^-?\d+$", toks[-1]):
            toks.pop()
        desc = " ".join(toks).strip()
        if desc and i + 1 < len(lines):                 # a narration too long for its column runs on below it, in the same column
            col = ln.find(toks[0])
            nxt = lines[i + 1]
            lead = len(nxt) - len(nxt.lstrip())
            if nxt.strip() and abs(lead - col) <= 2 and not re.search(_D, nxt) and not re.search(_AMT + r"\s*(CR|Cr)?\s*$", nxt):
                desc = desc + ("" if desc.endswith(("-", "/")) else " ") + re.split(r"\s{2,}", nxt.strip())[0]
        out.append(dict(txn_date=_iso(m.group(1)), description=desc, amount_p=_p(am.group(1)),
                        credit=bool(am.group(2) and am.group(2).upper() == "CR"), intl=intl, tail=tail))
    return out


def _icici_totals(lines):
    for i, ln in enumerate(lines):
        if re.search(r"Purchases\s*/\s*Charges", ln) and re.search(r"Payments\s*/\s*Credits", ln):
            for nxt in lines[i + 1:i + 6]:
                v = re.findall(_AMT, nxt)
                if len(v) >= 5:
                    return dict(previous=_p(v[1]), debits=_p(v[2]), cash=_p(v[3]), credits=_p(v[4]), due=_p(v[0]))
    return None


def _parse_hdfc_new(lines):
    out = []
    start = next((i for i, ln in enumerate(lines) if re.search(r"Domestic Transactions|International Transactions", ln)), None)
    if start is None:
        return out
    for i in range(start, len(lines)):
        ln = lines[i]
        m = re.match(r"^\s*" + _D + r"\s*\|\s*(\d{2}:\d{2})\s*(.*?)\s*$", ln)
        if not m:
            continue
        rest = re.sub(r"\s+l\s*$", "", m.group(3))
        am = re.search(r"(\+\s*)?[^\d\s,.+]?\s?" + _AMT + r"\s*$", rest)
        if not am:
            continue
        credit = bool(am.group(1))
        body = rest[:am.start()].rstrip()
        body = re.sub(r"\s{2,}\+\d+\s*$", "", body)
        desc = re.sub(r"\s{2,}", " ", body).strip()
        if not desc:                                    # the description is wrapped above and below the date line
            above = lines[i - 1].strip() if i > 0 and not re.match(r"^\s*" + _D, lines[i - 1]) else ""
            below = lines[i + 1].strip() if i + 1 < len(lines) and not re.match(r"^\s*" + _D, lines[i + 1]) else ""
            desc = (above + " " + below).strip()
        out.append(dict(txn_date=_iso(m.group(1)), description=desc, amount_p=_p(am.group(2)), credit=credit, intl="", tail=""))
    return out


def _hdfc_new_totals(lines):
    for i, ln in enumerate(lines):
        if "=" in ln and len(re.findall(r"[^\d\s,.]\s?" + _AMT, ln)) >= 4:
            v = re.findall(r"[^\d\s,.]\s?" + _AMT, ln)
            prev = None
            for back in lines[max(0, i - 3):i][::-1]:
                pv = re.findall(_AMT, back)
                if pv:
                    prev = _p(pv[-1])
                    break
            return dict(previous=prev, credits=_p(v[0]), debits=_p(v[1]), finance=_p(v[2]), due=_p(v[3]))
    return None


def _parse_hdfc_old(lines):
    out = []
    start = next((i for i, ln in enumerate(lines) if re.search(r"Domestic Transactions|International Transactions|Transaction Description", ln, re.I)), None)
    if start is None:
        return out
    for ln in lines[start:]:
        m = re.match(r"^\s*" + _D + r"(?:\s+\d{2}:\d{2}:\d{2})?\s+(.*?)\s*$", ln)
        if not m:
            continue
        toks = [t for t in re.split(r"\s{2,}", m.group(2)) if t]
        if not toks:
            continue
        am = re.match(r"^" + _AMT + r"(?:\s+(Cr|CR))?$", toks[-1])
        if not am:
            continue
        toks = toks[:-1]
        if len(toks) > 1 and re.match(r"^-?\d+$", toks[-1]):
            toks.pop()
        out.append(dict(txn_date=_iso(m.group(1)), description=" ".join(toks).strip(), amount_p=_p(am.group(1)),
                        credit=bool(am.group(2)), intl="", tail=""))
    return out


def _hdfc_old_totals(lines):
    for i, ln in enumerate(lines):
        if "Account Summary" in ln:
            for nxt in lines[i + 1:i + 10]:
                v = re.findall(_AMT, nxt)
                if len(v) >= 5:
                    return dict(previous=_p(v[0]), credits=_p(v[1]), debits=_p(v[2]), finance=_p(v[3]), due=_p(v[4]))
    return None


def parse_text(text):
    """-> dict(bank, layout, card_tail, statement_date, period_from, period_to, lines, printed, read, proof_ok, proof)."""
    lines = text.splitlines()
    if re.search(r"Purchases\s*/\s*Charges", text) and re.search(r"SerNo", text):
        bank, layout = "ICICI", "icici"
        rows, printed = _parse_icici(lines), _icici_totals(lines)
        pm = re.search(r"Statement period\s*:\s*(.+?)\s+to\s+(.+?\d{4})", text)
        pf, pt = (_words_date(pm.group(1)), _words_date(pm.group(2))) if pm else (None, None)
        sd = pt
        if not sd:
            sm = re.search(r"STATEMENT DATE\s*.*\n\s*(.+?\d{4})", text)
            sd = _words_date(sm.group(1)) if sm else None
    elif "PREVIOUS STATEMENT DUES" in text:
        bank, layout = "HDFC", "hdfc_2025b"
        rows, printed = _parse_hdfc_new(lines), _hdfc_new_totals(lines)
        sm = re.search(r"Statement Date\s+(\d{1,2}\s+[A-Za-z]{3},?\s+\d{4})", text)
        sd = _words_date(sm.group(1)) if sm else None
        bm = re.search(r"Billing Period\s+(\d{1,2}\s+[A-Za-z]{3},?\s+\d{4})\s*-\s*(\d{1,2}\s+[A-Za-z]{3},?\s+\d{4})", text)
        pf, pt = (_words_date(bm.group(1)), _words_date(bm.group(2))) if bm else (None, sd)
    elif "Account Summary" in text and re.search(r"Statement Date\s*:\s*\d{2}/\d{2}/\d{4}", text):
        bank, layout = "HDFC", "hdfc_2025a"
        rows, printed = _parse_hdfc_old(lines), _hdfc_old_totals(lines)
        sd = _iso(re.search(r"Statement Date\s*:\s*" + _D, text).group(1))
        pf, pt = None, sd
    else:
        raise CardStatementError("not a card statement layout this reader knows (HDFC Regalia, ICICI Amazon Pay / Coral)")
    if not sd:
        raise CardStatementError("no statement date printed")
    tails = [(a, b) for a, b in re.findall(r"(\d{4})\s?\d{2}XX\s?XXXX\s?(\d{4})", text)] + re.findall(r"(\d{4})X{6,10}(\d{4})", text)
    tail = next((b for a, b in tails if a != "0000"), "")
    dr = sum(r["amount_p"] for r in rows if not r["credit"])
    cr = sum(r["amount_p"] for r in rows if r["credit"])
    proof, ok = "no printed totals found", False
    if printed:
        want_dr = printed["debits"]
        alt_dr = printed["debits"] + (printed.get("finance") or 0)
        ok = (dr in (want_dr, alt_dr)) and cr == printed["credits"]
        proof = ("debits read %s = printed %s; credits read %s = printed %s" if ok else
                 "debits read %s vs printed %s; credits read %s vs printed %s -- DOES NOT PROVE") % (
                     _rs(dr), _rs(want_dr), _rs(cr), _rs(printed["credits"]))
    for r in rows:
        r["kind"] = kind_of(r["description"], r["credit"])
        r["merchant"] = (_emi_merchant(r["description"]) if r["kind"] == "emi_principal" else None) or merchant_of(r["description"])
        r["tail"] = r["tail"] or tail
    return dict(bank=bank, layout=layout, card_tail=tail, statement_date=sd, period_from=pf, period_to=pt or sd, lines=rows,
                printed=printed, read=dict(debits=dr, credits=cr), proof_ok=ok, proof=proof)


def _rs(p):
    p = int(p or 0)
    s = "%d" % (abs(p) // 100)
    if len(s) > 3:
        h, t = s[:-3], s[-3:]
        h = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", h)
        s = h + "," + t
    return ("-" if p < 0 else "") + "Rs " + s + ".%02d" % (abs(p) % 100)


# ------------------------------------------------------------------------------------------------ the tables
DDL = (
    "CREATE TABLE IF NOT EXISTS card_stmt (id INTEGER PRIMARY KEY, file_id INTEGER, slot_key TEXT, bank TEXT, layout TEXT, card_tail TEXT,"
    " statement_date TEXT, period_from TEXT, period_to TEXT, printed_debits_p INTEGER, printed_credits_p INTEGER, read_debits_p INTEGER,"
    " read_credits_p INTEGER, proof_ok INTEGER, proof TEXT, lines INTEGER, sha256 TEXT UNIQUE, read_at TEXT)",
    "CREATE TABLE IF NOT EXISTS card_line (id INTEGER PRIMARY KEY, stmt_id INTEGER NOT NULL, slot_key TEXT, card_tail TEXT, txn_date TEXT,"
    " description TEXT, merchant TEXT, kind TEXT, amount_p INTEGER, credit INTEGER, intl TEXT, seq INTEGER)",
    "CREATE INDEX IF NOT EXISTS card_line_stmt ON card_line(stmt_id)",
    "CREATE INDEX IF NOT EXISTS card_line_merchant ON card_line(merchant)",
    "CREATE TABLE IF NOT EXISTS card_merchant (merchant TEXT PRIMARY KEY, category TEXT NOT NULL, set_by TEXT, set_at TEXT)",
    "CREATE TABLE IF NOT EXISTS card_category (key TEXT PRIMARY KEY, owner_label TEXT NOT NULL, ledger TEXT NOT NULL, sort INTEGER)",
    "CREATE TABLE IF NOT EXISTS card_stmt_file (file_id INTEGER PRIMARY KEY, stmt_id INTEGER NOT NULL)",
)


def ensure(con):
    for s in DDL:
        con.execute(s)
    for i, (k, o, l) in enumerate(CATEGORIES):
        con.execute("INSERT OR IGNORE INTO card_category (key, owner_label, ledger, sort) VALUES (?,?,?,?)", (k, o, l, i))


def _now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ingest(con, file_id, slot_key, text, sha=None):
    """Read one statement into card_stmt / card_line. Idempotent on the shelf file and on the text's sha256; the same statement
    under another file (one mail saved twice, or the original beside its decrypted twin) is mapped to the statement already read and
    never written twice. Returns (stmt_id, parsed or None, new)."""
    ensure(con)
    if file_id:
        m = con.execute("SELECT stmt_id FROM card_stmt_file WHERE file_id=?", (file_id,)).fetchone()
        if m:
            return m[0], None, False
    sha = sha or hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()
    had = con.execute("SELECT id FROM card_stmt WHERE sha256=?", (sha,)).fetchone()
    if had:
        if file_id:
            con.execute("INSERT OR IGNORE INTO card_stmt_file (file_id, stmt_id) VALUES (?,?)", (file_id, had[0]))
        return had[0], None, False
    p = parse_text(text)
    pr = p["printed"] or {}
    twin = con.execute("SELECT id FROM card_stmt WHERE slot_key=? AND statement_date=? AND read_debits_p=? AND read_credits_p=?",
                       (slot_key, p["statement_date"], p["read"]["debits"], p["read"]["credits"])).fetchone()
    if twin:
        if file_id:
            con.execute("INSERT OR IGNORE INTO card_stmt_file (file_id, stmt_id) VALUES (?,?)", (file_id, twin[0]))
        return twin[0], p, False
    cur = con.execute("INSERT INTO card_stmt (file_id, slot_key, bank, layout, card_tail, statement_date, period_from, period_to, printed_debits_p,"
                      " printed_credits_p, read_debits_p, read_credits_p, proof_ok, proof, lines, sha256, read_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (file_id, slot_key, p["bank"], p["layout"], p["card_tail"], p["statement_date"], p["period_from"], p["period_to"],
                       pr.get("debits"), pr.get("credits"), p["read"]["debits"], p["read"]["credits"], 1 if p["proof_ok"] else 0, p["proof"],
                       len(p["lines"]), sha, _now()))
    sid = cur.lastrowid
    if file_id:
        con.execute("INSERT OR IGNORE INTO card_stmt_file (file_id, stmt_id) VALUES (?,?)", (file_id, sid))
    for i, r in enumerate(p["lines"]):
        con.execute("INSERT INTO card_line (stmt_id, slot_key, card_tail, txn_date, description, merchant, kind, amount_p, credit, intl, seq)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?)", (sid, slot_key, r["tail"], r["txn_date"], r["description"][:200], r["merchant"], r["kind"],
                                                        r["amount_p"], 1 if r["credit"] else 0, r["intl"], i))
    return sid, p, True


def category_of(con, merchant, kind):
    """The owner's word for a merchant wins; then the seed words; then the line's own kind; else 'unnamed'."""
    if kind == "repayment":
        return "repayment"
    if kind == "charges":
        return "charges"
    if kind == "fuel_charge":
        return "fuel"
    r = con.execute("SELECT category FROM card_merchant WHERE merchant=?", (merchant,)).fetchone()
    if r and r[0] in CAT:
        return r[0]
    u = " " + (merchant or "").upper() + " "
    for w, c in SEED:
        if w in u:
            return c
    return "unnamed"


def name_merchant(con, merchant, category, who):
    """The owner names a merchant once; every line of it, past and future, follows."""
    ensure(con)
    if category not in CAT or category in ("repayment", "charges") or not merchant:
        return dict(ok=False, error="bad_request"), 400
    con.execute("INSERT INTO card_merchant (merchant, category, set_by, set_at) VALUES (?,?,?,?) ON CONFLICT(merchant) DO UPDATE SET "
                "category=excluded.category, set_by=excluded.set_by, set_at=excluded.set_at", (merchant[:60], category, str(who)[:40], _now()))
    con.commit()
    return dict(ok=True, merchant=merchant, category=category), 200


def month_lines(con, month):
    """Every line of the card statements DATED in the month (the statements attached to that month's pack), with its category."""
    ensure(con)
    out = []
    cur = con.execute("SELECT l.*, s.statement_date, s.proof_ok FROM card_line l JOIN card_stmt s ON s.id=l.stmt_id "
                      "WHERE substr(s.statement_date,1,7)=? ORDER BY l.slot_key, l.txn_date, l.seq", (month,))
    cols = [c[0] for c in cur.description]
    for r in cur.fetchall():
        d = dict(zip(cols, r))
        c = category_of(con, d["merchant"], d["kind"])
        d["category"], d["owner_label"], d["ledger"] = c, CAT[c][0], CAT[c][1]
        out.append(d)
    return out


def unnamed(con, limit=40):
    """The merchants still to be named, the biggest first (all statements), with how many lines and how much."""
    ensure(con)
    agg = {}
    for m, k, a, cr in con.execute("SELECT merchant, kind, amount_p, credit FROM card_line"):
        if category_of(con, m, k) != "unnamed":
            continue
        g = agg.setdefault(m, [0, 0])
        g[0] += 1
        g[1] += -a if cr else a
    return [dict(merchant=m, lines=v[0], amount_p=v[1]) for m, v in sorted(agg.items(), key=lambda x: -abs(x[1][1]))][:limit]


def month_view(con, month, labels=None):
    """What the packs page shows for a month: each card's statement dated in it (proved or not), the month's lines by category with
    the owner's word and the accountant's ledger, every line, the merchants still to be named, and the categories one may choose."""
    ensure(con)
    labels = labels or {}
    st = [dict(slot=r[0], label=labels.get(r[0], r[0]), statement_date=r[1], proof_ok=bool(r[2]), proof=r[3], lines=r[4], card_tail=r[5])
          for r in con.execute("SELECT slot_key, statement_date, proof_ok, proof, lines, card_tail FROM card_stmt WHERE substr(statement_date,1,7)=? "
                               "ORDER BY slot_key, statement_date", (month,))]
    lines = month_lines(con, month)
    by = {}
    for d in lines:
        g = by.setdefault(d["category"], dict(category=d["category"], owner_label=d["owner_label"], ledger=d["ledger"], debit_p=0, credit_p=0, lines=0))
        g["lines"] += 1
        g["credit_p" if d["credit"] else "debit_p"] += d["amount_p"]
    order = {k: i for i, (k, _o, _l) in enumerate(CATEGORIES)}
    cats = sorted(by.values(), key=lambda g: order.get(g["category"], 99))
    for g in cats:
        g["net_p"] = g["debit_p"] - g["credit_p"]
    return dict(statements=st, by_category=cats,
                lines=[dict(date=d["txn_date"], card=labels.get(d["slot_key"], d["slot_key"]), tail=d["card_tail"], description=d["description"],
                            merchant=d["merchant"], kind=d["kind"], category=d["category"], owner_label=d["owner_label"], ledger=d["ledger"],
                            amount_p=d["amount_p"], credit=bool(d["credit"]), intl=d["intl"]) for d in lines],
                unnamed=unnamed(con), categories=[dict(key=k, owner_label=o, ledger=l) for k, o, l in CATEGORIES if k not in ("repayment", "charges")],
                all_proved=bool(st) and all(x["proof_ok"] for x in st))


def month_sheet_rows(con, month, labels=None):
    """The accountant's workbook for the month: (by ledger, every line). Amounts in rupees."""
    v = month_view(con, month, labels)
    head1 = ["Ledger (accountant)", "What it is (owner)", "Debits (Rs)", "Credits (Rs)", "Net (Rs)", "Lines"]
    r1 = [head1] + [[g["ledger"], g["owner_label"], g["debit_p"] / 100.0, g["credit_p"] / 100.0, g["net_p"] / 100.0, g["lines"]] for g in v["by_category"]]
    head2 = ["Date", "Card", "Narration (as the statement prints it)", "Merchant", "What it is (owner)", "Ledger (accountant)", "Dr (Rs)", "Cr (Rs)", "Foreign amount"]
    r2 = [head2] + [[l["date"][8:10] + "-" + l["date"][5:7] + "-" + l["date"][0:4], l["card"] + (" ..." + l["tail"] if l["tail"] else ""), l["description"],
                     l["merchant"], l["owner_label"], l["ledger"], (None if l["credit"] else l["amount_p"] / 100.0),
                     (l["amount_p"] / 100.0 if l["credit"] else None), l["intl"] or None] for l in v["lines"]]
    head3 = ["Card", "Statement dated", "Lines", "Proof against the statement's own totals"]
    r3 = [head3] + [[s["label"], s["statement_date"], s["lines"], ("PROVED -- " if s["proof_ok"] else "NOT PROVED -- ") + (s["proof"] or "")] for s in v["statements"]]
    return v, [("By ledger", r1), ("Every line", r2), ("Statements", r3)]
