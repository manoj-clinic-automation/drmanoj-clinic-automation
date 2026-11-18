#!/root/wa/venv/bin/python3
# -*- coding: utf-8 -*-
"""payment_records.py -- S882 (the parent, S486, 18-Nov-2026). His payment papers, from his Drive to the box.

THE OWNER, 18-Nov-2026: sheet 7 must be "a proper document supported by the actual receipts"; he shared his
personal Drive folder "Payment Records" (the Inbox Janitor's) read-only with the box's Drive reader (18:15),
and (18:39-19:06) asked for NK Pathology's own running Agilus ledger and a MyOperator ledger built from these papers.

WHAT THIS FILE DOES
  fetch    (cron 02:20, after the 02:05 register ingest): lists the shared folder and copies the PAYMENT PDFs of the
           clinic's known senders into /root/finance/payment_records/<vendor>/<name>; one row per file in table
           payment_record_file, with what the paper is (kind) and its own figures (total; a MyOperator statement's
           usage and balance) read ONCE here, so the pages never run pdftotext.
           Read-only on Drive (drive.readonly, records_drive.py's door); idempotent on (drive_id, md5); never deletes;
           one Drive refusal or one bad file never stops the run, and every run writes its state (cold review, S882).
           Never copied: a CSV, picture or spreadsheet; a Docterz report; an Airtel bill; a policy paper; a personal
           order; anything from a sender folder not on the clinic's list (it is counted and left in Drive).
  status   one screen of counts (no paper's name, no patient's).
  layout   the newest Agilus invoice's layout with EVERY word not on a fixed list of invoice words masked and EVERY
           digit turned to 9 -- so the ledger's lines can be built without a patient's name ever leaving the box (D656).
The read helpers need no Google library: the finance app (system python) imports them.
Switch: /root/finance/_off/ALL_OFF stops the fetch. PAYMENT_RECORDS_STUB=<dir> serves the walk (<dir>/Payment Records/<vendor>/<file>).
No patient data, no secret and no number in this file (F-185).
"""
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

FIN = os.environ.get("FIN_DIR", "/root/finance")
DB = os.environ.get("FINANCE_DB", os.path.join(FIN, "finance.db"))
STORE = os.environ.get("PAYMENT_RECORDS_DIR", os.path.join(FIN, "payment_records"))
STATE = os.environ.get("PAYMENT_RECORDS_STATE", os.path.join(FIN, "payment_records.state.json"))
STUB = os.environ.get("PAYMENT_RECORDS_STUB", "")
OFF = os.path.join(FIN, "_off", "ALL_OFF")
FOLDER = "Payment Records"
FOLDER_MIME = "application/vnd.google-apps.folder"
VERSION = "S882-PAYMENT-RECORDS-1.2"
MAX_FILE = 25 * 1024 * 1024
MAX_RUN = 600
TOKEN_AGE = 40 * 60
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
AGILUS = "Agilus (NK Pathology)"

# The clinic's senders -- the Janitor's own vendor names, plus the two domain folders he named (18:39-18:48): the Dell
# monitor's receipt (dellstore.com) and ICICI's tax invoices (icicibank.com). Any other folder is left in Drive and
# counted, never copied (a new sender is added here by a kit, on his word).
KNOWN = ("Agilus (NK Pathology)", "Airtel", "Anthropic Claude", "MyOperator", "GST Invoices", "icicibank.com",
         "Insurance", "dellstore.com", "Docterz EMR", "Hostinger & Razorpay", "Google Play", "Apple", "Samsung",
         "Cashfree", "GoDaddy", "Sarvam AI")
NEVER = re.compile(r"consultation report|clinical data|order_detail|\.csv$|\.xlsx?$|\.png$|\.jpe?g$|\.gif$", re.I)

SCHEMA = """
CREATE TABLE IF NOT EXISTS payment_record_file (
  id          INTEGER PRIMARY KEY,
  drive_id    TEXT NOT NULL,
  drive_md5   TEXT NOT NULL DEFAULT '',
  vendor      TEXT NOT NULL,
  mail_date   TEXT,
  name        TEXT NOT NULL,
  size        INTEGER,
  sha256      TEXT NOT NULL,
  local_path  TEXT NOT NULL,
  kind        TEXT NOT NULL DEFAULT '',
  total_paise INTEGER,
  facts_json  TEXT NOT NULL DEFAULT '{}',
  fetched_at  TEXT NOT NULL,
  UNIQUE (drive_id, sha256)
);
CREATE INDEX IF NOT EXISTS ix_prf_vendor_date ON payment_record_file(vendor, mail_date);
"""


def now_ist():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def want(vendor, name, mime=""):
    """(True, '') when this Drive file is a payment paper to copy; else (False, the reason in words)."""
    low = (name or "").lower()
    if NEVER.search(low):
        return False, "not a payment paper (report, export or picture)"
    if not (low.endswith(".pdf") or "pdf" in (mime or "").lower()):
        return False, "not a PDF"
    if vendor not in KNOWN:
        return False, "a sender not on the clinic's list (personal or new) -- left in Drive"
    if vendor == "Docterz EMR" and not re.search(r"invoice|receipt", low):
        return False, "Docterz notification, not a payment"
    if vendor == "Airtel" and "airtelreceipt" not in low:
        return False, "Airtel bill or statement (its receipt is the payment)"
    if vendor == "Insurance" and "receipt" not in low:
        return False, "policy paper, not a receipt"
    return True, ""


def mail_date_of(name):
    m = re.match(r"(\d{4}-\d{2}-\d{2})_", name or "")
    return m.group(1) if m else None


def safe(s, n=120):
    s = re.sub(r"[^\w.\- ()&]+", "_", s or "").strip(" .") or "_"
    return s[:n]


def open_db(path=None, ro=False):
    p = path or DB
    con = sqlite3.connect("file:%s?mode=ro" % p, uri=True, timeout=30) if ro else sqlite3.connect(p, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    return con


def ensure_schema(con):
    con.executescript(SCHEMA)
    have = {r[1] for r in con.execute("PRAGMA table_info(payment_record_file)")}
    for col, decl in (("total_paise", "INTEGER"), ("facts_json", "TEXT NOT NULL DEFAULT '{}'")):
        if col not in have:
            con.execute("ALTER TABLE payment_record_file ADD COLUMN %s %s" % (col, decl))
    con.commit()


def table_ready(con):
    try:
        return bool(con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='payment_record_file'").fetchone())
    except sqlite3.Error:
        return False


# ------------------------------------------------------------------ Drive (live: records_drive; walk: the stub)
class DriveRefused(IOError):
    pass


class _Live(object):
    def __init__(self):
        if FIN not in sys.path:
            sys.path.insert(0, FIN)
        import records_drive as rd                                     # noqa: PLC0415 -- the box's one Drive door
        self.rd, self.h, self.at = rd, None, 0
        self._auth()

    def _auth(self):
        try:
            self.h, self.at = self.rd.headers(), time.time()
        except SystemExit:                                             # records_drive.die() -- one line already on stderr
            raise DriveRefused("the Drive key could not be used")

    def _get(self, url, params, timeout=60):
        if time.time() - self.at > TOKEN_AGE:
            self._auth()
        for attempt in (1, 2):
            try:
                return self.rd.get(url, params, self.h, timeout)
            except SystemExit:                                         # die(): 'Drive said <code>' on stderr, never a name
                if attempt == 2:
                    raise DriveRefused("Drive refused")
                self._auth()                                           # an expired token is the usual cause: once more

    def _list(self, q, fields="nextPageToken,files(id,name,mimeType,md5Checksum,size)"):
        out, tok = [], None
        while True:
            prm = {"q": q + " and trashed=false", "pageSize": 1000, "fields": fields}
            if tok:
                prm["pageToken"] = tok
            d = self._get(self.rd.API, prm).json()
            out.extend(d.get("files", []))
            tok = d.get("nextPageToken")
            if not tok:
                return out

    def roots(self):
        return self._list("sharedWithMe and name='%s' and mimeType='%s'" % (FOLDER, FOLDER_MIME))

    def children(self, fid):
        return self._list("'%s' in parents" % fid)

    def media(self, fid):
        return self._get(self.rd.API + "/" + fid, {"alt": "media"}, 120).content


class _Stub(object):
    def __init__(self, root):
        self.root = root

    def roots(self):
        p = os.path.join(self.root, FOLDER)
        return [{"id": p, "name": FOLDER, "mimeType": FOLDER_MIME}] if os.path.isdir(p) else []

    def children(self, fid):
        out = []
        for n in sorted(os.listdir(fid)):
            p = os.path.join(fid, n)
            if os.path.isdir(p):
                out.append({"id": p, "name": n, "mimeType": FOLDER_MIME})
            else:
                b = open(p, "rb").read()
                out.append({"id": "stub-" + hashlib.md5(p.encode()).hexdigest()[:20], "name": n,
                            "mimeType": "application/pdf" if n.lower().endswith(".pdf") else "application/octet-stream",
                            "md5Checksum": hashlib.md5(b).hexdigest(), "size": str(len(b))})
        return out

    def media(self, fid):
        for dirpath, _d, files in os.walk(self.root):
            for n in files:
                p = os.path.join(dirpath, n)
                if "stub-" + hashlib.md5(p.encode()).hexdigest()[:20] == fid:
                    if "REFUSE" in n:
                        raise DriveRefused("Drive refused")
                    return open(p, "rb").read()
        raise DriveRefused("no such file")


def drive():
    return _Stub(STUB) if STUB else _Live()


# ------------------------------------------------------------------ text, kind and figures (system python; no Google)
def text_of(path, layout=False):
    try:
        cmd = ["pdftotext"] + (["-layout"] if layout else []) + [path, "-"]
        r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=60)
        return r.stdout.decode("utf-8", "replace").replace("’", "'").replace("‘", "'")
    except Exception:                                                  # noqa: BLE001
        return ""


def kind_of(vendor, name, text):
    t = (text or "")[:4000].lower()
    low = (name or "").lower()
    if not t.strip():
        return "unreadable"                     # a locked PDF (ICICI's GST invoices) or a scan with no text
    if vendor == "MyOperator" and ("monthly statement" in t or "statement period" in t) and "invoice no" not in t:
        return "statement"
    if vendor == AGILUS:
        return "invoice" if ("invoice" in low or "invoice" in t) else "paper"
    if "receipt" in low or re.search(r"\breceipt\b|payment (?:has been )?(?:successfully )?received|received with thanks", t):
        return "receipt"
    if "invoice" in low or "invoice" in t:
        return "invoice"
    return "paper"


MONEY = r"([\d,]*\d(?:\.\d{1,2})?)"


def money_after(text, label, span=220):
    """The first money figure after a label (bracketed notes after the label skipped), else None."""
    m = re.search(re.escape(label), text or "", re.I)
    if not m:
        return None
    tail = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", text[m.end():m.end() + span])
    n = re.search(r"(?:INR|Rs\.?|₹)?\s*" + MONEY, tail)
    if not n:
        return None
    try:
        return float(n.group(1).replace(",", ""))
    except ValueError:
        return None


STRONG_TOTAL = re.compile(r"\b(grand total|amount paid|paid amount|total paid|total amount payable|total amount|net amount|"
                          r"invoice amount|invoice total|net payable|amount payable)\b", re.I)
WEAK_TOTAL = re.compile(r"(?<![a-z])(?<!sub )(?<!sub-)total\b(?!\s*(?:excluding|exclusive|tax|items?|qty|quantity|discount))", re.I)


def _figures(text, rx, span=120):
    out = []
    for m in rx.finditer(text or ""):
        tail = re.sub(r"\([^)\n]*\)", " ", text[m.end():m.end() + span])
        n = re.match(r"[ \t:=\-]*(?:INR|Rs\.?|₹|US\$|\$)?[ \t]*" + MONEY, tail)      # the SAME line only
        if not n or tail[n.end():n.end() + 1] in ("-", "/"):                             # a date, never a figure
            continue
        try:
            v = round(float(n.group(1).replace(",", "")), 2)
        except ValueError:
            continue
        if v >= 1:
            out.append(v)
    return out


def labelled_total(text):
    """One labelled total. The strong labels ('Grand Total', 'Amount Paid', 'Total Amount', 'Net Amount' ...) decide
    when present; else a plain 'Total' (never 'Sub Total' or 'Total excluding tax'). Two different figures -> None:
    'see the receipt', never a guess."""
    for rx in (STRONG_TOTAL, WEAK_TOTAL):
        v = set(_figures(text, rx))
        if v:
            return v.pop() if len(v) == 1 else None
    return None


MON3 = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}


def _d(s):
    m = re.match(r"(\d{1,2})\s+([A-Za-z]{3})\w*\s+(\d{4})", (s or "").strip())
    if not m or m.group(2).lower() not in MON3:
        return None
    try:
        return dt.date(int(m.group(3)), MON3[m.group(2).lower()], int(m.group(1))).isoformat()
    except ValueError:
        return None


def _paise(x):
    return None if x is None else int(round(x * 100))


def myoperator_statement(text):
    """MyOperator's monthly statement: the period, this month's charges (without tax), the amount payable and the
    pre-paid balance after the month. Any figure not found is None."""
    m = re.search(r"Statement period\s+(\d{1,2} \w{3} \d{4})\s+to\s+(\d{1,2} \w{3} \d{4})", text or "", re.I)
    return {"from": _d(m.group(1)) if m else None, "to": _d(m.group(2)) if m else None,
            "charges": _paise(money_after(text, "This Month's Charges")),
            "payable": _paise(money_after(text, "Total Amount Payable This Month")),
            "balance": _paise(money_after(text, "Pre-paid Balance"))}


def facts_of(vendor, path):
    """What the paper is and its own figures -- read once, at the copy."""
    plain = text_of(path)
    kind = kind_of(vendor, os.path.basename(path), plain)
    total = _paise(labelled_total(text_of(path, layout=True))) if kind in ("invoice", "receipt", "paper") else None
    facts = myoperator_statement(plain) if kind == "statement" else {}
    return kind, total, facts


# ------------------------------------------------------------------ the fetch
def _state_write(d):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=1, sort_keys=True)
    os.replace(tmp, STATE)


def state_read():
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def _place(vdir, name, data, sha):
    """The file on the box under its own name, or name__2, __3 ... when another content holds the name.
    Returns the path whose bytes ARE this content (read back), or None."""
    base, ext = os.path.splitext(os.path.join(vdir, safe(name)))
    for i in range(1, 50):
        path = base + ("" if i == 1 else "__%d" % i) + ext
        if os.path.exists(path):
            if hashlib.sha256(open(path, "rb").read()).hexdigest() == sha:
                return path
            continue
        tmp = path + ".part"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o600)
        os.replace(tmp, path)
        return path if hashlib.sha256(open(path, "rb").read()).hexdigest() == sha else None
    return None


def fetch(con, dv=None):
    """One pass. Returns the state dict. Never deletes; a file already held is never fetched again."""
    st = {"version": VERSION, "run_at": now_ist(), "ok": False, "error": "", "folders": 0, "vendors": 0,
          "seen": 0, "wanted": 0, "fetched": 0, "already": 0, "skipped": {}, "too_big": 0, "failed": 0, "left_for_next": 0}
    ensure_schema(con)
    dv = dv or drive()
    roots = dv.roots()
    st["folders"] = len(roots)
    if len(roots) != 1:
        st["error"] = ("the shared folder '%s' is not seen by the box's Drive reader" % FOLDER) if not roots else \
                      ("%d folders named '%s' are shared with the box -- which is his is not guessed" % (len(roots), FOLDER))
        return st
    os.makedirs(STORE, mode=0o700, exist_ok=True)
    held = {(r["drive_id"], r["drive_md5"]) for r in con.execute("SELECT drive_id, drive_md5 FROM payment_record_file")}
    n = 0
    for v in dv.children(roots[0]["id"]):
        if v.get("mimeType") != FOLDER_MIME:
            continue
        st["vendors"] += 1
        vendor = v["name"]
        try:
            files = dv.children(v["id"])
        except (Exception, SystemExit) as e:                           # noqa: BLE001 -- one folder never stops the run
            st["failed"] += 1
            st["last_failure"] = type(e).__name__
            continue
        for f in files:
            if f.get("mimeType") == FOLDER_MIME:
                continue
            st["seen"] += 1
            ok, why = want(vendor, f.get("name", ""), f.get("mimeType", ""))
            if not ok:
                st["skipped"][why] = st["skipped"].get(why, 0) + 1
                continue
            st["wanted"] += 1
            key = (f["id"], f.get("md5Checksum", ""))
            if key in held:
                st["already"] += 1
                continue
            if int(f.get("size") or 0) > MAX_FILE:
                st["too_big"] += 1
                continue
            if n >= MAX_RUN:
                st["left_for_next"] += 1
                continue
            try:
                data = dv.media(f["id"])
                n += 1
                sha = hashlib.sha256(data).hexdigest()
                vdir = os.path.join(STORE, safe(vendor, 60))
                os.makedirs(vdir, mode=0o700, exist_ok=True)
                path = _place(vdir, f["name"], data, sha)
                if not path:
                    st["failed"] += 1
                    continue
                kind, total, facts = facts_of(vendor, path)
                con.execute("INSERT OR IGNORE INTO payment_record_file(drive_id, drive_md5, vendor, mail_date, name, size, "
                            "sha256, local_path, kind, total_paise, facts_json, fetched_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                            (f["id"], f.get("md5Checksum", ""), vendor, mail_date_of(f["name"]), f["name"], len(data), sha,
                             path, kind, total, json.dumps(facts, sort_keys=True), now_ist()))
                con.commit()
                held.add(key)
                st["fetched"] += 1
            except (Exception, SystemExit) as e:                       # noqa: BLE001 -- one file never stops the run
                st["failed"] += 1
                st["last_failure"] = type(e).__name__
    st["ok"] = True
    return st


# ------------------------------------------------------------------ read helpers for the pages and packs.py
def files_for(con, vendor=None, date_iso=None, kind=None):
    if not table_ready(con):
        return []
    q, a = "SELECT * FROM payment_record_file WHERE 1=1", []
    for col, val in (("vendor", vendor), ("mail_date", date_iso), ("kind", kind)):
        if val:
            q += " AND %s=?" % col
            a.append(val)
    out, seen = [], set()
    for r in con.execute(q + " ORDER BY mail_date, name, id", a):
        if r["sha256"] in seen:                                        # the same paper saved twice is one paper
            continue
        seen.add(r["sha256"])
        d = dict(r)
        try:
            d["facts"] = json.loads(d.get("facts_json") or "{}")
        except ValueError:
            d["facts"] = {}
        out.append(d)
    return out


def _register(con, vendor):
    try:
        return list(con.execute("SELECT row_no, date_iso, description, amount_paise FROM payment_register "
                                "WHERE vendor=? AND date_iso IS NOT NULL ORDER BY date_iso, row_no", (vendor,)))
    except sqlite3.Error:
        return []


def myoperator_rows(con):
    """The MyOperator ledger, oldest first: every invoice and payment from the Payment Register (the mail's own
    figure; a row repeating the same date, kind and amount -- or the same invoice number -- is one), and every monthly
    statement from its PDF. Each row: date, what, charged, paid, usage, balance (MyOperator's own pre-paid balance),
    running (payments less invoices), files (payment_record_file ids)."""
    files = files_for(con, "MyOperator")
    by_date = {}
    for f in files:
        by_date.setdefault(f["mail_date"], []).append(f)
    rows, seen = [], set()
    for r in _register(con, "MyOperator"):
        d = r["description"] or ""
        if d.startswith("["):
            continue
        what = "Payment made" if re.search(r"payment .*received", d, re.I) else \
               "Invoice raised" if re.search(r"invoice", d, re.I) else None
        if not what:
            continue
        m = re.search(r"\(([A-Z]\d{4}-\d{4,})\)", d)
        key = (what, m.group(1)) if m else (r["date_iso"], what, r["amount_paise"])
        if key in seen:
            continue
        seen.add(key)
        rows.append({"date": r["date_iso"], "what": what + (" " + m.group(1) if m else ""),
                     "charged": r["amount_paise"] if what == "Invoice raised" else None,
                     "paid": r["amount_paise"] if what == "Payment made" else None, "usage": None, "balance": None,
                     "files": [f["id"] for f in by_date.get(r["date_iso"], []) if f["kind"] != "statement"]})
    for f in files:
        if f["kind"] != "statement":
            continue
        s = f["facts"]
        per = ("%s to %s" % (s.get("from"), s.get("to"))) if s.get("from") else "the month"
        rows.append({"date": f["mail_date"], "what": "Monthly statement (%s): usage charges without tax" % per,
                     "charged": None, "paid": None, "usage": s.get("charges"), "balance": s.get("balance"),
                     "payable": s.get("payable"), "files": [f["id"]]})
    rows.sort(key=lambda x: (x["date"] or "", 0 if x["what"].startswith("Invoice") else 1))
    run = 0
    for x in rows:
        run += (x.get("paid") or 0) - (x.get("charged") or 0)
        x["running"] = run
    return rows


def agilus_rows(con):
    """NK Pathology's Agilus ledger, oldest first -- ONE row per Agilus INVOICE (a paper saved twice is one): its date,
    the invoice's own labelled total, or the mail's figure from the Payment Register when the invoice has none and
    that date holds exactly one invoice and one figure; the running total. Per-patient lines: the next kit (D656)."""
    reg = {}
    for r in _register(con, AGILUS):
        if r["amount_paise"]:
            reg.setdefault(r["date_iso"], []).append(r["amount_paise"])
    inv = [f for f in files_for(con, AGILUS) if f["kind"] in ("invoice", "unreadable")]   # a locked/scanned one stays, unfigured
    per_day = {}
    for f in inv:
        per_day[f["mail_date"]] = per_day.get(f["mail_date"], 0) + 1
    rows, run = [], 0
    for f in inv:
        amt, src = f.get("total_paise"), "read from the invoice"
        if amt is None:
            cand = reg.get(f["mail_date"], [])
            if per_day.get(f["mail_date"]) == 1 and len(cand) == 1:
                amt, src = cand[0], "the mail"
            else:
                src = ""
        run += amt or 0
        rows.append({"date": f["mail_date"], "file": f["id"], "name": f["name"], "amount": amt, "source": src,
                     "running": run})
    return rows


# ------------------------------------------------------------------ the masked layout (shape only)
TEMPLATE = set("""
tax invoice bill to from patient name test tests date amount total grand rate qty sr no s gst cgst sgst igst utgst hsn sac
code description particulars net discount sub subtotal n k pathology agilus diagnostics diagnostic ltd limited private pvt
address gstin pan state place of supply number ref id sample samples collected collection received reported registration
reg age sex gender male female years yrs y m d rs inr payment mode advance balance opening closing deposit credit debit
ledger page the and for in is by at on with a an as per terms conditions authorised authorized signatory bank account
ifsc branch customer client lab centre center location city period month year due paid unit price value mrp quantity
details summary remarks note notes email phone mobile contact website www com details line item items service services
charges charge round off rounded nett payable words only rupees paise e cin cn dr drs mr mrs ms referred ref by doctor
outstanding previous current this pin code tel fax uttar pradesh bareilly mumbai india branch office regd head copy original
duplicate recipient supplier type order no. date: of to
""".split())


def mask_line(line):
    line = re.sub(r"[\w.+-]+@[\w.-]+", "<email>", line)
    line = re.sub(r"\d", "9", line)
    return re.sub(r"[^\W\d_]+", lambda m: m.group(0) if m.group(0).lower() in TEMPLATE else "X" * min(len(m.group(0)), 4), line)


def masked_layout(con, vendor=AGILUS, lines=90):
    fs = files_for(con, vendor, kind="invoice" if vendor == AGILUS else None)
    if not fs:
        return "no %s invoice on the server yet" % vendor
    t = text_of(fs[-1]["local_path"], layout=True)
    body = [mask_line(x)[:170] for x in t.splitlines() if x.strip()]
    head = ("the newest of %d %s papers, %d pages, %d text lines. Every word not on a fixed list of invoice words is X'd "
            "and every digit is 9." % (len(fs), vendor, t.count("\f") + 1 if t else 0, len(body)))
    return "\n".join([head] + body[:lines] + (["... %d more lines" % (len(body) - lines)] if len(body) > lines else []))


def status_text(con):
    st = state_read()
    out = ["payment_records %s -- last run %s: %s" % (VERSION, st.get("run_at", "never"),
                                                       "OK" if st.get("ok") else ("NOT OK: " + st.get("error", "")))]
    if st:
        out.append("  folder seen %s . sender folders %s . files seen %s . payment papers %s . copied now %s . held already %s . failed %s"
                   % (st.get("folders"), st.get("vendors"), st.get("seen"), st.get("wanted"), st.get("fetched"),
                      st.get("already"), st.get("failed")))
        for why, c in sorted((st.get("skipped") or {}).items()):
            out.append("  left in Drive: %3d  %s" % (c, why))
    if con is not None and table_ready(con):
        for r in con.execute("SELECT vendor, kind, COUNT(DISTINCT sha256) c, MAX(mail_date) last FROM payment_record_file "
                             "GROUP BY vendor, kind ORDER BY vendor, kind"):
            out.append("  on the server: %-24s %-10s %4d  newest %s" % (r["vendor"][:24], r["kind"], r["c"], r["last"]))
    return "\n".join(out)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "fetch":
        if os.path.exists(OFF):
            print("payment_records: switched off (%s)" % OFF)
            return 0
        lk = open(os.path.join(FIN, ".payment_records.lock"), "w")
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            print("payment_records: another fetch is running")
            return 0
        try:
            con = open_db()
            st = fetch(con)
        except (Exception, SystemExit) as e:                           # noqa: BLE001 -- the state is written whatever happens
            con = None
            st = {"version": VERSION, "run_at": now_ist(), "ok": False, "error": "the run stopped (%s)" % type(e).__name__}
        _state_write(st)
        print(status_text(con).splitlines()[0])
        return 0 if st.get("ok") else 2
    con = open_db(ro=True) if os.path.exists(DB) else None
    if cmd == "status":
        print(status_text(con))
        return 0
    if cmd == "layout":
        print(masked_layout(con) if con else "no database")
        return 0
    print("usage: payment_records.py fetch | status | layout")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
