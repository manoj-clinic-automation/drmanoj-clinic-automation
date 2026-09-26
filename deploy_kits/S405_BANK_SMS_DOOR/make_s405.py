#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s405.py -- builds the three patched live files of kit S405_BANK_SMS_DOOR from the LIVE bytes by anchored
edits. Every anchor must occur exactly once, and every source must be at its FROM pin, or the build stops with
nothing written. Nothing is re-typed.

  bank_sms.py              the phone's door is never silent (bank_sms_ignored, masked); parse() becomes a ladder
                           (strict, then tolerant; parse_grade); Yes Bank SMS read into bank_sms_yes; a NEFT debit
                           equal to a finalised pay month's NEFT portion writes ONE purchase_neft_event (provisional,
                           source sms); the owner's page gains 'Last Yes Bank SMS', the Yes Bank table, the Ignored card
  sanjeevni_approvals.py   Needs you gains 'NEFT of ₹X seen on <date> — matched to <Month>. OK?' (fail-soft, from
                           bank_sms) and the two POST routes /api/neft-event/ok and /api/neft-event/reject
  finance_approvals.html   the Needs-you line renders its two buttons OK / Not this (one tap each)

Usage: make_s405.py --finance /root/finance --out DIR
"""
import hashlib
import os
import sys

FROM = {
    "bank_sms.py": "3a8f0a8863942cde3fce2d0294a86769",
    "sanjeevni_approvals.py": "675aab4a46ab8792f05b17cab15d17ee",
    "finance_approvals.html": "c319bb56d30ac960d49d4a67083a55b2",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


# ---------------------------------------------------------------- bank_sms.py
def build_bank_sms(s):
    s = rep(s, '''bank_sms.py -- S290 (17-Sep-2026). The bank's morning settlement SMS, straight from the owner's phone.
''', '''bank_sms.py -- S405 (26-Sep-2026, D621, F-634) on S290 (17-Sep-2026). The bank's morning settlement SMS, straight
from the owner's phone.

S405 -- THE DOOR IS NEVER SILENT. Nine mornings (17-25 Sep) the phone posted the ICICIPOS SMS, HTTP 200 each, and the
page read "none yet": the strict regex missed and, by the S290 design below, nothing of a miss was kept. Now:
  * every post the door does not store lands in bank_sms_ignored with a MASKED copy of the text (every digit run of
    4+ becomes '#', an account tail written the bank's way -- 'XX1234' -- stays, an amount reads 'Rs ####'), a bank
    guess and a reason; the owner's page shows them under "Ignored (N, last 30 days)";
  * parse() is a ladder: the strict S290 regex first, then a tolerant read (case-free, Rs / Rs. / INR, 'credited' or
    'credited with', dd-Mon-yy / dd/mm/yy / dd-mm-yyyy, the Info text and the balance optional, whitespace and
    newlines free); the stored row carries parse_grade 'strict' | 'tolerant';
  * a Yes Bank SMS (the owner's second macro posts to this same door) is read into bank_sms_yes: the NEFT / IMPS /
    RTGS debit (neft_debit), the cash deposit credit (cash_credit), other_debit / other_credit; a Yes Bank text that
    matches nothing goes to the ignored table with bank_guess YESBANK -- never a 4xx to the phone;
  * THE PROVISIONAL (zero taps): a neft_debit whose amount equals the NEFT portion of a FINALISED pay month with no
    live event (purchase_app's own sheet: the sum of the NEFT lines; tolerance = setting neft.sms_tolerance_p, default
    0) writes ONE purchase_neft_event row (kind provisional, source sms). The owner's Needs you then asks
    'NEFT of ₹X seen on <date> -- matched to <Month>. OK?' with OK / Not this (sanjeevni_approvals). S407 writes the
    same table from the owner's own tap and turns the pay sheet amber / green.
The 200/ignored answer to the phone is unchanged. The key and the phone's address are never printed anywhere.
''', "S405 header")
    s = rep(s, '''APP_VERSION = "S290-BANK-SMS-1.0"
''', '''APP_VERSION = "S405-BANK-SMS-2.0"
''', "version")
    s = rep(s, '''CREATE INDEX IF NOT EXISTS bank_sms_bdate ON bank_sms_settlement(business_date);
"""
''', '''CREATE INDEX IF NOT EXISTS bank_sms_bdate ON bank_sms_settlement(business_date);
-- S405 (D621): nothing the door receives is silent
CREATE TABLE IF NOT EXISTS bank_sms_ignored (
    id            INTEGER PRIMARY KEY,
    received_at   TEXT NOT NULL,
    phone_sender  TEXT NOT NULL DEFAULT '',
    bank_guess    TEXT NOT NULL,           -- ICICI | YESBANK | UNKNOWN
    reason        TEXT NOT NULL,
    masked_text   TEXT NOT NULL            -- never the raw text
);
-- S405: the Yes Bank SMS (the second macro), read tolerantly
CREATE TABLE IF NOT EXISTS bank_sms_yes (
    id            INTEGER PRIMARY KEY,
    kind          TEXT NOT NULL,           -- neft_debit | cash_credit | other_debit | other_credit
    sms_date      TEXT NOT NULL,
    amount_p      INTEGER NOT NULL,
    acct_tail     TEXT NOT NULL DEFAULT '',
    ref           TEXT NOT NULL DEFAULT '',   -- UTR / reference when the text carries one
    balance_p     INTEGER,
    masked_text   TEXT NOT NULL,
    phone_sender  TEXT NOT NULL DEFAULT '',
    received_at   TEXT NOT NULL,
    seen          INTEGER NOT NULL DEFAULT 1,
    UNIQUE (kind, sms_date, amount_p, ref)
);
-- S405 (D621): the NEFT event of a pay month -- written here from the SMS (source sms), by S407 from the owner's tap
-- (source owner). kind: provisional | rejected. confirmed_by/at = the owner's OK. bank_line_id = S407's statement line.
CREATE TABLE IF NOT EXISTS purchase_neft_event (
    id            INTEGER PRIMARY KEY,
    month         TEXT NOT NULL,
    kind          TEXT NOT NULL,
    source        TEXT NOT NULL,
    amount_p      INTEGER NOT NULL,
    sms_date      TEXT,
    utr           TEXT,
    yes_id        INTEGER,
    bank_line_id  INTEGER,
    created_at    TEXT NOT NULL,
    created_by    TEXT,
    confirmed_by  TEXT,
    confirmed_at  TEXT,
    note          TEXT
);
"""
''', "schema")
    s = rep(s, '''    con.executescript(SCHEMA)
    con.commit()
    _schema_done = True
''', '''    con.executescript(SCHEMA)
    have = {r[1] for r in con.execute("PRAGMA table_info(bank_sms_settlement)")}
    if "parse_grade" not in have:                                  # S405: which rung read the row
        con.execute("ALTER TABLE bank_sms_settlement ADD COLUMN parse_grade TEXT NOT NULL DEFAULT 'strict'")
    con.commit()
    _schema_done = True
''', "ensure parse_grade")
    s = rep(s, '''    for fmt in ("%d-%b-%y", "%d-%b-%Y"):
''', '''    for fmt in ("%d-%b-%y", "%d-%b-%Y", "%d/%b/%y", "%d/%b/%Y", "%d/%m/%y", "%d/%m/%Y",   # S405: the shapes banks use
                "%d-%m-%y", "%d-%m-%Y", "%d%b%y", "%d%b%Y"):
''', "date shapes")
    s = rep(s, '''def parse(text):
    """The settlement fields, or None when the text is not an ICICI POS settlement credit."""
    m = SMS_RE.search(text or "")
    if not m:
        return None
    mid = MID_RE.search(m.group("info"))
    d = _date(m.group("date"))
    amt = _paise(m.group("amt"))
    if not mid or d is None or not amt or amt <= 0:
        return None
    return dict(acct_tail=m.group("acct"), amount_p=amt, balance_p=_paise(m.group("bal")),
                credit_date=d.isoformat(), business_date=(d - dt.timedelta(days=1)).isoformat(),
                mid_tail=mid.group("mid"), ref=m.group("info").strip()[:80])
''', '''# ---------------------------------------------------------------- S405: the ladder, the mask, Yes Bank, the provisional
TOL_RE = re.compile(
    r"ICICI\\s*Bank\\s*(?:Acc(?:oun)?t|A/c)\\.?\\s*(?:no\\.?\\s*)?(?:XX+|X\\*+|\\*+)?\\s*(?P<acct>\\d{3,4})\\b.{0,40}?"
    r"credited(?:\\s+with)?\\s*:?\\s*(?:with\\s+)?(?:Rs\\.?|INR)\\s*(?P<amt>\\d[\\d,]*(?:\\.\\d{1,2})?)"
    r".{0,24}?\\bon\\s+(?P<date>\\d{1,2}[-/][A-Za-z0-9]{2,3}[-/]\\d{2,4})", re.I | re.S)
INFO_RE = re.compile(r"Info\\s*:?\\s*(?P<info>.+?)(?:\\.\\s|\\.$|$)", re.I | re.S)
BAL_RE = re.compile(r"(?:Avl|Avail(?:able)?)\\.?\\s*Bal(?:ance)?\\.?\\s*(?:is\\s*)?:?\\s*(?:Rs\\.?|INR)?\\s*(?P<bal>\\d[\\d,]*(?:\\.\\d{1,2})?)", re.I)
YES_RE = re.compile(r"YES\\s*BANK|YESBNK|\\bYESB\\b", re.I)
AMT_RE = re.compile(r"(?:INR|Rs\\.?)\\s*(?P<amt>\\d[\\d,]*(?:\\.\\d{1,2})?)", re.I)
DATE_RES = (re.compile(r"\\b(\\d{1,2}[-/](?:[A-Za-z]{3}|\\d{1,2})[-/]\\d{2,4})\\b"),
            re.compile(r"\\b(\\d{1,2}\\s[A-Za-z]{3}\\s\\d{2,4})\\b"),
            re.compile(r"\\b(\\d{1,2}[A-Za-z]{3}\\d{2,4})\\b"))
REF_RE = re.compile(r"(?:UTR|Ref(?:erence)?\\.?\\s*(?:No\\.?|Number|#)?|RRN|Txn\\s*(?:ID|No\\.?))\\s*[:\\-#.]?\\s*(?P<ref>[A-Za-z0-9]{6,24})", re.I)
REF2_RE = re.compile(r"\\b(?P<ref>YESB[A-Z0-9]{6,}|[A-Z]{4}N\\d{6,}[A-Z0-9]*)\\b")
TAIL_RE = re.compile(r"(?:A/?c(?:ct)?|Account|Acct)\\.?\\s*(?:no\\.?\\s*)?(?:XX+|X\\*+|\\*+|x+)?\\s*(?P<tail>\\d{4})\\b", re.I)
TAIL2_RE = re.compile(r"(?:XX+|X\\*+|\\*{2,})\\s?(?P<tail>\\d{3,4})\\b")
MASK_TAIL_RE = re.compile(r"((?:XX+|X\\*+|\\*{2,}|xx+)\\s?)(\\d{3,4})\\b")
MASK_AMT_RE = re.compile(r"((?:Rs\\.?|INR)\\s*)\\d[\\d,]*(?:\\.\\d{1,2})?", re.I)
KIND_WORDS = {"neft_debit": "NEFT / IMPS / RTGS out", "cash_credit": "cash deposit in",
              "other_debit": "other debit", "other_credit": "other credit"}


def _guess_bank(text):
    t = text or ""
    if "icici" in t.lower():
        return "ICICI"
    if YES_RE.search(t):
        return "YESBANK"
    return "UNKNOWN"


def mask(text):
    """S405: the copy the ignored table keeps. Every digit run of 4+ becomes '#'s; an account tail written the
    bank's way ('XX1234') stays; an amount reads 'Rs ####'. Never the raw text."""
    s = str(text or "")[:600]
    s = MASK_AMT_RE.sub(lambda m: m.group(1) + "####", s)
    held = []

    def _hold(m):
        held.append(m.group(0))
        return "\\x00%d\\x00" % (len(held) - 1)
    s = MASK_TAIL_RE.sub(_hold, s)
    s = re.sub(r"\\d{4,}", lambda m: "#" * len(m.group(0)), s)
    return re.sub(r"\\x00(\\d+)\\x00", lambda m: held[int(m.group(1))], s)


def _find_date(text):
    for rx in DATE_RES:
        for m in rx.finditer(text or ""):
            d = _date(m.group(1).replace(" ", "-"))
            if d is not None:
                return d
    return None


def parse(text):
    """The settlement fields, or None when the text is not an ICICI POS settlement credit.
    S405: a ladder -- the strict S290 regex first, then the tolerant read; the dict carries parse_grade."""
    t = text or ""
    m, grade = SMS_RE.search(t), "strict"
    if not m:
        m, grade = TOL_RE.search(t), "tolerant"
    if not m:
        return None
    mid = MID_RE.search(t)
    d = _date(m.group("date"))
    amt = _paise(m.group("amt"))
    if not mid or d is None or not amt or amt <= 0:
        return None
    info = (m.groupdict().get("info") or "").strip()
    if not info:
        im = INFO_RE.search(t)
        info = im.group("info").strip() if im else mid.group(0)
    bal = m.groupdict().get("bal")
    if bal is None:
        bm = BAL_RE.search(t)
        bal = bm.group("bal") if bm else None
    return dict(acct_tail=m.group("acct"), amount_p=amt, balance_p=_paise(bal) if bal else None,
                credit_date=d.isoformat(), business_date=(d - dt.timedelta(days=1)).isoformat(),
                mid_tail=mid.group("mid"), ref=info[:80], parse_grade=grade)


def icici_reason(text):
    t = text or ""
    if not MID_RE.search(t):
        return "ICICI text without a POS merchant id (not a settlement)"
    if not AMT_RE.search(t):
        return "ICICI settlement text: no amount read"
    if _find_date(t) is None:
        return "ICICI settlement text: no date read"
    return "ICICI settlement shape not recognised (strict and tolerant both missed)"


def parse_yes(text):
    """A Yes Bank SMS -> (row, None) or (None, reason). Tolerant: the first amount, the first debit/credit word, the
    first date it can read; a NEFT / RTGS / IMPS debit is neft_debit; a cash deposit credit is cash_credit; else other_*."""
    t = text or ""
    low = t.lower()
    i_d, i_c = low.find("debit"), low.find("credit")
    if i_d < 0 and i_c < 0:
        return None, "Yes Bank text without a debit or credit word"
    debit = i_c < 0 or (0 <= i_d < i_c)
    am = AMT_RE.search(t)
    amt = _paise(am.group("amt")) if am else None
    if not amt or amt <= 0:
        return None, "Yes Bank text: no amount read"
    d = _find_date(t)
    if d is None:
        return None, "Yes Bank text: no date read"
    if debit:
        kind = "neft_debit" if re.search(r"\\b(?:NEFT|RTGS|IMPS)\\b", t, re.I) else "other_debit"
    else:
        kind = "cash_credit" if re.search(r"\\bcash\\b|CASH\\s*DEP", t, re.I) else "other_credit"
    rm = REF_RE.search(t) or REF2_RE.search(t)
    tm = TAIL_RE.search(t) or TAIL2_RE.search(t)
    bm = BAL_RE.search(t)
    return dict(kind=kind, sms_date=d.isoformat(), amount_p=amt, acct_tail=(tm.group("tail") if tm else ""),
                ref=(rm.group("ref").strip()[:40] if rm else ""), balance_p=_paise(bm.group("bal")) if bm else None), None


def _ignore(con, stamp, sender, text, reason):
    con.execute("INSERT INTO bank_sms_ignored (received_at, phone_sender, bank_guess, reason, masked_text) VALUES (?,?,?,?,?)",
                (stamp, sender, _guess_bank(text), reason, mask(text)))


def _setting_int(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return int(str(r[0]).strip()) if r and str(r[0]).strip() else default
    except Exception:                            # noqa: BLE001
        return default


def neft_portion_p(con, month):
    """The NEFT portion of a pay month = the sum of the sheet's NEFT lines (purchase_app's own _pay_rows, read in
    process, never copied). None when the sheet cannot be read."""
    try:
        import purchase_app as pa                # noqa: PLC0415
        _s, groups = pa._pay_rows(con, month)
        return int(sum(g["payable_p"] for g in groups if g["route"] == "NEFT"))
    except Exception:                            # noqa: BLE001
        return None


def finalised_months(con):
    try:
        return [r[0] for r in con.execute("SELECT month FROM purchase_month WHERE status='final' ORDER BY month DESC")]
    except Exception:                            # noqa: BLE001
        return []


def _try_provisional(con, y, yes_id, stamp):
    """D621: a Yes Bank NEFT debit equal (within neft.sms_tolerance_p) to the NEFT portion of a finalised month that has
    no live event -> ONE provisional row, source sms. Returns the month, or None."""
    tol = _setting_int(con, "neft.sms_tolerance_p", 0)
    for month in finalised_months(con):
        if con.execute("SELECT 1 FROM purchase_neft_event WHERE month=? AND kind<>'rejected'", (month,)).fetchone():
            continue
        portion = neft_portion_p(con, month)
        if not portion or portion <= 0:
            continue
        if abs(portion - int(y["amount_p"])) <= tol:
            con.execute("INSERT INTO purchase_neft_event (month, kind, source, amount_p, sms_date, utr, yes_id, created_at, created_by) "
                        "VALUES (?,?,?,?,?,?,?,?,?)",
                        (month, "provisional", "sms", int(y["amount_p"]), y["sms_date"], y["ref"] or None, yes_id, stamp, "sms"))
            return month
    return None


def _inr(p):
    v = str(int(round(abs(int(p or 0)) / 100.0)))
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return "\\u20b9" + v


def _dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def _month_name(ym):
    try:
        return dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except (TypeError, ValueError):
        return ym


def needs_you_lines(con):
    """For sanjeevni_approvals (fail-soft there): one line per SMS provisional awaiting the owner's OK / Not this."""
    _ensure(con)
    out = []
    for r in con.execute("SELECT id, month, amount_p, sms_date FROM purchase_neft_event WHERE kind='provisional' "
                         "AND source='sms' AND confirmed_by IS NULL ORDER BY id"):
        out.append(dict(cls="warn", target="bank", neft_event=int(r[0]),
                        text="NEFT of %s seen on %s \\u2014 matched to %s. OK?" % (_inr(r[2]), _dmy(r[3]), _month_name(r[1]))))
    return out


def neft_event_decide(con, event_id, how, who):
    """The owner's tap: 'ok' sets confirmed_by/at; anything else marks the event rejected (Not this)."""
    _ensure(con)
    r = con.execute("SELECT id, kind, confirmed_by FROM purchase_neft_event WHERE id=?", (int(event_id),)).fetchone()
    if not r:
        return dict(ok=False, error="no_such_event", message="No such NEFT event."), 404
    if r[1] == "rejected" or r[2]:
        return dict(ok=True, already=True, id=int(r[0]), kind=r[1], confirmed_by=r[2]), 200
    stamp = _now().strftime("%Y-%m-%d %H:%M:%S")
    if how == "ok":
        con.execute("UPDATE purchase_neft_event SET confirmed_by=?, confirmed_at=? WHERE id=?", (who, stamp, int(r[0])))
        kind = "provisional"
    else:
        con.execute("UPDATE purchase_neft_event SET kind='rejected', note=? WHERE id=?", ("not this -- %s, %s" % (who, stamp), int(r[0])))
        kind = "rejected"
    con.commit()
    return dict(ok=True, id=int(r[0]), kind=kind, confirmed_by=(who if how == "ok" else None), at=stamp), 200
''', "parse ladder + S405 helpers")
    s = rep(s, '''    p = parse(text)
    if p is None:
        return jsonify(ok=True, stored=False, ignored=True), 200       # nothing of it is kept
    con = _db()
    _ensure(con)
    unit = unit_for_mid(con, p["mid_tail"])
    if unit is None:
        return jsonify(ok=True, stored=False, ignored=True, why="unknown merchant"), 200
    stamp = _now().strftime("%Y-%m-%d %H:%M:%S")
    cur = con.execute(
        "INSERT INTO bank_sms_settlement (unit, credit_date, business_date, amount_p, balance_p, acct_tail, ref, "
        "sms_text, phone_sender, received_at) VALUES (?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(unit, credit_date, amount_p, ref) DO UPDATE SET seen = seen + 1",
        (unit, p["credit_date"], p["business_date"], p["amount_p"], p["balance_p"], p["acct_tail"], p["ref"],
         text.strip(), sender, stamp))
    con.commit()
    return jsonify(ok=True, stored=True, unit=unit, business_date=p["business_date"],
                   amount=p["amount_p"] // 100), 200
''', '''    con = _db()
    _ensure(con)
    stamp = _now().strftime("%Y-%m-%d %H:%M:%S")
    p = parse(text)
    if p is None:
        # S405 (F-634): nothing is silent. A Yes Bank text is read into bank_sms_yes; anything else lands in the
        # ignored table, masked, with a reason. The phone still hears 200/ignored.
        if YES_RE.search(text):
            y, why = parse_yes(text)
            if y is not None:
                con.execute(
                    "INSERT INTO bank_sms_yes (kind, sms_date, amount_p, acct_tail, ref, balance_p, masked_text, phone_sender, received_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(kind, sms_date, amount_p, ref) DO UPDATE SET seen = seen + 1",
                    (y["kind"], y["sms_date"], y["amount_p"], y["acct_tail"], y["ref"], y["balance_p"], mask(text), sender, stamp))
                row = con.execute("SELECT id, seen FROM bank_sms_yes WHERE kind=? AND sms_date=? AND amount_p=? AND ref=?",
                                  (y["kind"], y["sms_date"], y["amount_p"], y["ref"])).fetchone()
                month = None
                if row and int(row[1]) == 1 and y["kind"] == "neft_debit":
                    month = _try_provisional(con, y, int(row[0]), stamp)
                con.commit()
                return jsonify(ok=True, stored=True, bank="YESBANK", kind=y["kind"], sms_date=y["sms_date"],
                               amount=y["amount_p"] // 100, matched_month=month), 200
            _ignore(con, stamp, sender, text, why)
            con.commit()
            return jsonify(ok=True, stored=False, ignored=True), 200
        _ignore(con, stamp, sender, text, icici_reason(text) if "icici" in text.lower() else "not a bank SMS this door reads")
        con.commit()
        return jsonify(ok=True, stored=False, ignored=True), 200
    unit = unit_for_mid(con, p["mid_tail"])
    if unit is None:
        _ignore(con, stamp, sender, text, "unknown merchant (id ending %s)" % p["mid_tail"][-4:])
        con.commit()
        return jsonify(ok=True, stored=False, ignored=True, why="unknown merchant"), 200
    con.execute(
        "INSERT INTO bank_sms_settlement (unit, credit_date, business_date, amount_p, balance_p, acct_tail, ref, "
        "sms_text, phone_sender, received_at, parse_grade) VALUES (?,?,?,?,?,?,?,?,?,?,?) "
        "ON CONFLICT(unit, credit_date, amount_p, ref) DO UPDATE SET seen = seen + 1",
        (unit, p["credit_date"], p["business_date"], p["amount_p"], p["balance_p"], p["acct_tail"], p["ref"],
         text.strip(), sender, stamp, p["parse_grade"]))
    con.commit()
    return jsonify(ok=True, stored=True, unit=unit, business_date=p["business_date"],
                   amount=p["amount_p"] // 100, parse_grade=p["parse_grade"]), 200
''', "the door")
    s = rep(s, '''    out.append("<div class='card'><h2>Bank settlement SMS</h2><p class='mut'>The morning SMS is the early figure; the MPR "
               "is the record. Last SMS received: <b>%s</b>.</p></div>" % _esc(last or "none yet"))
''', '''    last_yes = con.execute("SELECT MAX(received_at) m FROM bank_sms_yes").fetchone()["m"]          # S405
    out.append("<div class='card'><h2>Bank settlement SMS</h2><p class='mut'>The morning SMS is the early figure; the MPR "
               "is the record. Last SMS received: <b>%s</b>. Last Yes Bank SMS: <b>%s</b>.</p></div>"
               % (_esc(last or "none yet"), _esc(last_yes or "none yet")))
''', "last lines")
    s = rep(s, '''    key = _key()
    out.append("""<details class="card"><summary><b>Phone setup — MacroDroid</b> (one time)</summary>
''', '''    # S405: the Yes Bank SMS of the last 30 days, the NEFT events, and everything the door did not store (masked)
    since = (today - dt.timedelta(days=30)).isoformat()
    yrows = con.execute("SELECT kind, sms_date, amount_p, acct_tail, ref, received_at, seen FROM bank_sms_yes "
                        "WHERE received_at>=? ORDER BY received_at DESC LIMIT 60", (since,)).fetchall()
    ytab = "".join("<tr><td class='d'>%s</td><td>%s</td><td>\\u20b9 %s</td><td>\\u2026%s</td><td>%s</td><td class='mut'>%s%s</td></tr>"
                   % (_esc(_dmy(r["sms_date"])), _esc(KIND_WORDS.get(r["kind"], r["kind"])), _r(r["amount_p"]), _esc(r["acct_tail"]),
                      _esc(r["ref"]), _esc(r["received_at"]), (" \\u00d7%d" % r["seen"]) if r["seen"] > 1 else "") for r in yrows)
    ev = con.execute("SELECT month, kind, amount_p, sms_date, confirmed_by FROM purchase_neft_event ORDER BY id DESC LIMIT 12").fetchall()
    etab = "".join("<li>%s \\u2014 NEFT %s seen %s: <b>%s</b></li>"
                   % (_esc(_month_name(r["month"])), _inr(r["amount_p"]), _esc(_dmy(r["sms_date"])),
                      _esc({"provisional": ("confirmed by %s" % r["confirmed_by"]) if r["confirmed_by"] else "awaiting your OK on the approvals page",
                            "rejected": "not this (rejected)"}.get(r["kind"], r["kind"]))) for r in ev)
    out.append("<div class='card'><h2>Yes Bank SMS (last 30 days)</h2><table class='grid'><thead><tr><th>SMS date</th><th>What</th>"
               "<th>Amount</th><th>Account</th><th>Ref / UTR</th><th>Received</th></tr></thead><tbody>%s</tbody></table>%s</div>"
               % (ytab or "<tr><td colspan='6' class='mut'>No Yes Bank SMS yet \\u2014 the second macro on the phone posts them here.</td></tr>",
                  ("<p class='mut'>NEFT matched to a pay month:</p><ul>%s</ul>" % etab) if etab else ""))
    ign = con.execute("SELECT received_at, bank_guess, reason, masked_text FROM bank_sms_ignored WHERE received_at>=? "
                      "ORDER BY id DESC LIMIT 100", (since,)).fetchall()
    out.append("<details class='card'><summary><b>Ignored (%d, last 30 days)</b> \\u2014 every post the door did not store, masked</summary>%s</details>"
               % (len(ign), ("<table class='grid'><thead><tr><th>Received</th><th>Bank</th><th>Why</th><th>Text (masked)</th></tr></thead><tbody>%s</tbody></table>"
                             % "".join("<tr><td class='d'>%s</td><td>%s</td><td>%s</td><td class='mut'>%s</td></tr>"
                                       % (_esc(r[0]), _esc(r[1]), _esc(r[2]), _esc(r[3])) for r in ign))
                  if ign else "<p class='mut'>Nothing ignored in the last 30 days.</p>"))
    key = _key()
    out.append("""<details class="card"><summary><b>Phone setup — MacroDroid</b> (one time)</summary>
''', "yes bank + ignored cards")
    s = rep(s, '''<li>Android settings: MacroDroid → Battery → <b>Unrestricted</b>.</li>
''', '''<li>Macro 2 — <b>Bank SMS 2 (Yes Bank)</b>: the same HTTP action, header and body; trigger content <b>contains</b> <code>YES BANK</code> (a second trigger for <code>YESBNK</code>). Both macros post to this one door.</li>
<li>Android settings: MacroDroid → Battery → <b>Unrestricted</b>.</li>
''', "macro 2 line")
    return s


# ---------------------------------------------------------------- sanjeevni_approvals.py
def build_approvals(s):
    s = rep(s, '''#  sanjeevni_approvals.py  ·  v1.5  ·  kit S403_PURCHASE_ORDERS_LIVE  ·  Session 283 (Sanjeevni)
#
''', '''#  sanjeevni_approvals.py  ·  v1.6  ·  kit S405_BANK_SMS_DOOR  ·  Session 283 (Sanjeevni)
#
#  v1.6 (S405, D621, 26-Sep-2026): Needs you gains 'NEFT of ₹X seen on <date> -- matched to <Month>. OK?' (read from
#  bank_sms, fail-soft) with the two POST routes /api/neft-event/ok and /api/neft-event/reject (the owner's one tap).
#
''', "header")
    s = rep(s, '''VERSION = "1.5"
''', '''VERSION = "1.6"
''', "version")
    s = rep(s, '''#      POST /finance/sanjeevni/api/bank/undo     remove one unconfirmed entry you just made (checker)
''', '''#      POST /finance/sanjeevni/api/bank/undo     remove one unconfirmed entry you just made (checker)
#      POST /finance/sanjeevni/api/neft-event/ok      S405: the SMS NEFT provisional is right (checker)
#      POST /finance/sanjeevni/api/neft-event/reject  S405: 'Not this' -- the event is rejected (checker)
''', "route list")
    s = rep(s, '''    # 7 · the statement's age (a word, not a fault)
''', '''    # 10 · S405 (D621): a Yes Bank NEFT debit matched to a finalised pay month, awaiting his OK / Not this (fail-soft)
    try:
        import bank_sms  # noqa: PLC0415
        lines.extend(bank_sms.needs_you_lines(con))
    except Exception:  # noqa: BLE001
        pass
    # 7 · the statement's age (a word, not a fault)
''', "needs-you line")
    s = rep(s, '''    return jsonify(needs_you(_db()))


@bp.route("/finance/sanjeevni/api/days")
''', '''    return jsonify(needs_you(_db()))


def _neft_event(how):
    """S405 (D621): the owner's one tap on the SMS NEFT provisional. bank_sms owns the table and the rule."""
    u, err = _require("checker")
    if err:
        return err
    js = request.get_json(silent=True) or {}
    try:
        eid = int(js.get("id") or 0)
    except (TypeError, ValueError):
        eid = 0
    if not eid:
        return jsonify(ok=False, error="bad_id", message="Which NEFT event?"), 400
    import bank_sms  # noqa: PLC0415
    body, code = bank_sms.neft_event_decide(_db(), eid, how, u.get("user") or "owner")
    return jsonify(**body), code


@bp.route("/finance/sanjeevni/api/neft-event/ok", methods=["POST"])
def api_neft_event_ok():
    return _neft_event("ok")


@bp.route("/finance/sanjeevni/api/neft-event/reject", methods=["POST"])
def api_neft_event_reject():
    return _neft_event("reject")


@bp.route("/finance/sanjeevni/api/days")
''', "the two routes")
    return s


# ---------------------------------------------------------------- finance_approvals.html
def build_html(s):
    s = rep(s, '''<!doctype html>
<!-- S378_BANK_BALANCES''', '''<!doctype html>
<!-- S405_BANK_SMS_DOOR (Session 283, 26-Sep-2026, D621): a Needs-you line that carries neft_event renders its two
     buttons OK / Not this (one tap each, sanjeevni_approvals' two routes); nothing else on the page moves.
  -- kit S378 header below --
<!-- S378_BANK_BALANCES''', "header")
    s = rep(s, '''    el.innerHTML=L.map(function(l){return '<li onclick="goSec(\\''+esc(l.target)+'\\')"><span class="dot '+esc(l.cls||"warn")+'"></span>'+esc(l.text)+' <span class="mut">▸</span></li>'}).join("");
''', '''    el.innerHTML=L.map(function(l){
      var act=l.neft_event?' <button onclick="event.stopPropagation();neftEvent('+parseInt(l.neft_event,10)+',\\'ok\\')">OK</button> <button class="ghost" onclick="event.stopPropagation();neftEvent('+parseInt(l.neft_event,10)+',\\'reject\\')">Not this</button>':'';   /* S405 */
      return '<li onclick="goSec(\\''+esc(l.target)+'\\')"><span class="dot '+esc(l.cls||"warn")+'"></span>'+esc(l.text)+act+' <span class="mut">▸</span></li>'}).join("");
''', "needs line buttons")
    s = rep(s, '''/* ---- Days: one line per day, grouped by month; tap = the day panel (S365/S367) ---- */
''', '''/* ---- S405 (D621): the NEFT provisional from the bank SMS -- OK / Not this, one tap ---- */
function neftEvent(id,how){
  fetch("/finance/sanjeevni/api/neft-event/"+how,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({id:id})})
    .then(srvJSON).then(function(x){var j=x.j||{}; if(!j.ok){alert(j.message||j.error||"could not save");return} loadNeeds();})
    .catch(function(){alert("nothing was saved — the server could not be reached")});
}

/* ---- Days: one line per day, grouped by month; tap = the day panel (S365/S367) ---- */
''', "neftEvent function")
    return s


def main():
    args = dict(zip(sys.argv[1::2], sys.argv[2::2]))
    fin, out = args.get("--finance"), args.get("--out")
    if not (fin and out):
        sys.exit(__doc__)
    os.makedirs(out, exist_ok=True)
    built = {
        "bank_sms.py": build_bank_sms(load(os.path.join(fin, "bank_sms.py"), "bank_sms.py")),
        "sanjeevni_approvals.py": build_approvals(load(os.path.join(fin, "sanjeevni_approvals.py"), "sanjeevni_approvals.py")),
        "finance_approvals.html": build_html(load(os.path.join(fin, "finance_ui", "finance_approvals.html"), "finance_approvals.html")),
    }
    for name, text in built.items():
        raw = text.encode("utf-8")
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(raw)
        print("built %s  %s" % (md5(raw), name))


if __name__ == "__main__":
    main()
