#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""surgery_cases.py -- kit S579_SURGERY_CASES (session S325, 18-Oct-2026, D735). One record per surgery.
S680_IPD_CASES_RECORD (session S368, 29-Oct-2026, D801) -- the IPD cases build, kit 1 of 6: THE RECORD. One record per admission.
  Renamed "IPD cases" on every screen (the URLs stay /finance/surgery). A case carries a TYPE (surgical · surgical without
  implant · conservative), a SOURCE (table surg_source, seeded Clinic · DTH · Imran · Awdhesh; a new name joins the list), a PAYER
  of five (cash · cash package · TPA cashless · Ayushman · other scheme -- column payer_kind; the old column payer is kept as the
  vendor ledger's class: package -> cash, TPA -> cashless, other -> deendayal, so every ledger, cheque and receipt rule reads
  exactly as before), the admission date, the hospital's IPD number, the diagnosis and a medicolegal tick. SETTINGS (Dr Manoj only).
  Shavez sees everything on a case except the implant's ACTUAL cost (what is actually due to the vendor), Dr Manoj's alone (D801 (6)).
S680 FINAL (session S370, 30-Oct-2026, D804 -- the owner's review of the screens, 30-Oct 04:06-05:46, and the mock-up boards 7-12):
  * Not one "closed" but THREE statuses on every case, each a filter: the patient (not admitted yet / admitted / discharged), the
    hospital money (pending / received) and the implant payment (not raised · bill raised · cheque received · paid · vendor
    confirmed · not needed). Columns implant_status and money_status; the stage column is kept and follows the dates by itself.
  * The search finds a case by name, clinic ID, case no., IPD no., UHID and the FULL MOBILE -- the mobile(s) kept on the case
    (column mobile, typed once or filled from the patient picked) and the console's patients mirror /root/wa/console.db
    (READ ONLY; the Case Pack's own search source, rebuilt every 10 minutes). Numbers are shown on screen; never in the repository.
  * The list is compact; tapping a patient opens the case IN PLACE, below the row, and every entry is made there (each form goes
    back to the list with that case open). One "Next" line says what is waiting; the case is in stage sections -- 1 admission,
    2 surgery & implant, 3 discharge & papers, 4 the hospital bill, 5 payment & what remains, 6 implant settlement, 7 follow-up,
    8 what happened -- the section for the current step open, the rest folded; 4, 6 and 7 say which later kit fills them.
  * Compact forms: sized fields, two or more to a line on a PC, one on a phone. Clinic ID optional. UHID beside the IPD number.
    TPA / scheme a drop-down (table surg_tpa; added from the form or on Settings). The Case Pack number PICKED from that patient's
    Case Pack entries (/root/wa/casepack/case_ledger.csv, READ ONLY). Removal reasons are tapped, not typed.
  * Old cases (backfill, from 1-Apr-2025) sit in the SAME list, marked "old case"; their form is the same compact form with the
    implant, its vendor and both payment statuses -- nothing compulsory but the name and the payer.

THE OWNER, 18-Oct-2026 10:51-11:39 IST (his words, in short):
  "I want this on the server ... build some flows inside that using the scanner app for scanning pre-approval records of
   Ayushman and patients and maybe cashless patients and the later on records such as the file cover, the billing page,
   implant page, discharge summary, and maintain ledger of the implants ... vendor-wise, patient-wise ... and I want to keep
   a record of all such patients. So that payment reconciliation can be done whenever the payment is made from the hospital
   for the cash patients and the credit patients" (credit = cashless insurance, Ayushman, Deendayal Upadhyaya Yojana).
  Implants: "vendor bills patient, credit for cashless and ayushman and deen dayal ones; cash patients only few need bill and
   the bill is in patient name, rest are on estimate only, billed to me, and i clear vendor dues in cash, periodically (for
   these i need an amount which is charged to the patient); for cashless i need to add an amount that is to be actually paid
   to vendor, which can be different from the billed amount; he gets a cheque for full bill amount, and his ledger shows the
   details, private only to me, which i can share to vendor; also the cheques issued for credit patients dont have patient
   details always." The gap between the full bill and the actual amount counts in his favour on that vendor's ledger (11:32).
  Hospital: one transfer for many patients; "the monthly hospital statement is the one to be reconciled, or i need to
   manually enter the amounts paid against each patient from the statement" (11:39).

  /finance/surgery                         the cases: filters, search, the three statuses; a case opens in place
  /finance/surgery/new                     a new case (from the Case Pack's "Continue" link, prefilled, or directly)
  /finance/surgery/backfill                an old case (from 1-Apr-2025), the same form
  /finance/surgery/case/<id>               one case, in its stage sections (?frag=1: the sections alone, for the list)
  /finance/surgery/vendors, /vendor/<id>   the implant vendors' ledgers -- the owner only; printable to share with the vendor
  /finance/surgery/receipts, /receipt/<id> the hospital's payments (one monthly statement each) -- the owner only
  /finance/surgery/settings                admission, nursing a day, his share, the sources, the TPA / scheme names -- the owner only
  Unit 'surgery': shavez maker (cases, papers, implant lines, statuses -- no money pages), the doctor checker (everything).
  Money rows are never edited: a correction is a void with its reason plus a new row. Every write goes through the app's
  audit helper. Tables on the first request, never at import (F-303). Papers are stored under the Case Pack's own folder,
  which the nightly encrypted backup already carries whole (S424).
"""
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import urllib.error
import urllib.request
from urllib.parse import quote

from flask import Blueprint, redirect, request, send_file

bp = Blueprint("surgery_cases", __name__)

APP_VERSION = "S680-IPD-2.0"       # S680 final (S370, 30-Oct-2026, D804); S680 v3 (S368) and S581 before it
_db = None
_require = None
_audit = None
_unit = "surgery"

PAPER_DIR = os.environ.get("SURGERY_PAPER_DIR", "/root/wa/casepack/surgery_papers")
CONSOLE_DB = os.environ.get("SURGERY_CONSOLE_DB", "/root/wa/console.db")                 # READ ONLY: the patients mirror
CASE_LEDGER = os.environ.get("SURGERY_CASE_LEDGER", "/root/wa/casepack/case_ledger.csv")  # READ ONLY: the Case Pack's cases
CALL_URL = os.environ.get("SURGERY_CALL_URL", "http://127.0.0.1:8097/call")          # call_api.py: MyOperator's user dialer
WA_ENV = os.environ.get("SURGERY_WA_ENV", "/root/wa/.env")                            # READ ONLY: CALL_API_SECRET (never shown)
RING_AGENTS = os.environ.get("SURGERY_RING_AGENTS", "/root/portal/ring_agents.json")  # READ ONLY: login -> the MyOperator name
CALL_GAP = 60                                    # one IVR call per case per 60 seconds (as Call ke baad)
ON_KEY = "surgery_cases.on"
DEFAULT_HOSPITAL = "Dhanwantari Tomar Hospital"
MAX_P = 10000000000              # Rs 10 crore for one typed figure
MAX_FILE = 30 * 1024 * 1024
BASE = "/finance/surgery"

PAYERS = (("cash", "Cash"), ("cashless", "Cashless (insurance)"), ("ayushman", "Ayushman"), ("deendayal", "Deendayal"))
PAYER_WORD = dict(PAYERS)
CREDIT = ("cashless", "ayushman", "deendayal")
# S680 (D801): the payer as he names it -- five kinds. The old column 'payer' (four values, CHECKed) stays as the ledger's class.
KINDS = (("cash", "Cash"), ("package", "Cash · package"), ("tpa", "TPA cashless"), ("ayushman", "Ayushman"), ("other", "Other scheme"))
KIND_WORD = dict(KINDS)
KIND_SHORT = {"cash": "Cash", "package": "Package", "tpa": "TPA", "ayushman": "Ayushman", "other": "Other"}
KIND_CLASS = {"cash": "cash", "package": "cash", "tpa": "cashless", "ayushman": "ayushman", "other": "deendayal"}
LEGACY_KIND = {"cash": "cash", "cashless": "tpa", "ayushman": "ayushman", "deendayal": "other"}
CREDIT_KINDS = ("tpa", "ayushman", "other")
CP_KIND = {"ayush": "ayushman", "ayushman": "ayushman", "tpa": "tpa", "cashless": "tpa", "cash": "cash", "package": "package",
           "other": "other", "deendayal": "other"}          # the Case Pack's words for its payer -> ours
TYPES = (("surgical", "Surgical"), ("noimplant", "Surgical · no implant"), ("conservative", "Conservative"))
TYPE_WORD = dict(TYPES)
SEED_SOURCES = ("Clinic", "DTH", "Imran", "Awdhesh")          # D801 (5): add-as-needed, searchable
SET_ADMISSION, SET_NURSING, SET_SHARE = "ipd.admission_p", "ipd.nursing_p", "ipd.share_pct"
DEF_ADMISSION, DEF_NURSING = 120000, 50000                      # D801 (1): Rs 1,200 admission, Rs 500 a day nursing
BACKFILL_FROM = "2025-04-01"                                    # the owner, 30-Oct-2026: old cases from April 2025 onward
STAGES = (("planned", "Planned"), ("applied", "Pre-approval applied"), ("approved", "Pre-approved"), ("admitted", "Admitted"),
          ("operated", "Operated"), ("discharged", "Discharged"), ("billed", "Bill / claim sent"), ("closed", "Closed"))
STAGE_WORD = dict(STAGES)
# S680 final (D804): the three statuses
PSTAT = (("planned", "Not admitted yet"), ("admitted", "Admitted"), ("discharged", "Discharged"))
MONEY = (("pending", "Pending"), ("received", "Received"))
IMPLANT_STEPS = (("pending", "Not raised yet"), ("raised", "Bill raised"), ("cheque", "Cheque received"),
                 ("paid", "Paid to the vendor"), ("confirmed", "Vendor confirmed"), ("na", "Not needed"))
IMPLANT_WORD = dict(IMPLANT_STEPS)
ISHOW = (("pending", "Pending"), ("paid", "Paid"), ("na", "Not needed"))
CASESHOW = (("all", "All cases"), ("new", "New cases only"), ("old", "Old cases only (backfilled)"))
PAPERS = (("preapproval", "Pre-approval"), ("file_cover", "File cover"), ("billing", "Billing page"),
          ("implant", "Implant page / stickers"), ("discharge", "Discharge summary"), ("xray", "X-ray images"),
          ("scan", "MRI / CT / other scans and reports"), ("mlc", "Medicolegal (MLC) papers"), ("police", "Police memo"),
          ("other", "Other papers"))
PAPER_WORD = dict(PAPERS)
NEEDED_CASH = ("file_cover", "billing", "implant", "discharge")
NEEDED_CREDIT = ("preapproval",) + NEEDED_CASH
VOID_WHY = (("wrong", "wrong entry"), ("twice", "entered twice"), ("amount", "wrong amount"), ("case", "wrong patient / case"))
BANK_TABLES = ("bank_statement_line", "yesbank_account_statement_line", "icici_statement_line")

SCHEMA = """
CREATE TABLE IF NOT EXISTS surg_case (
  id INTEGER PRIMARY KEY,
  case_no TEXT NOT NULL UNIQUE,
  clinic_id TEXT NOT NULL DEFAULT '',
  patient TEXT NOT NULL,
  payer TEXT NOT NULL CHECK(payer IN ('cash','cashless','ayushman','deendayal')),
  insurer TEXT NOT NULL DEFAULT '',
  hospital TEXT NOT NULL DEFAULT '',
  procedure_text TEXT NOT NULL DEFAULT '',
  surgery_date TEXT NOT NULL DEFAULT '',
  discharge_date TEXT NOT NULL DEFAULT '',
  stage TEXT NOT NULL DEFAULT 'planned',
  casepack_id TEXT NOT NULL DEFAULT '',
  due_p INTEGER,
  note TEXT NOT NULL DEFAULT '',
  created_by TEXT, created_at TEXT, changed_by TEXT, changed_at TEXT,
  voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS surg_paper (
  id INTEGER PRIMARY KEY,
  case_id INTEGER,
  receipt_id INTEGER,
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL,
  mime TEXT NOT NULL,
  by_whom TEXT, at TEXT,
  voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS surg_vendor (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE COLLATE NOCASE,
  note TEXT NOT NULL DEFAULT '',
  created_by TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS surg_implant (
  id INTEGER PRIMARY KEY,
  case_id INTEGER NOT NULL,
  vendor_id INTEGER NOT NULL,
  item TEXT NOT NULL,
  qty INTEGER NOT NULL DEFAULT 1,
  bill_p INTEGER NOT NULL,
  bill_to TEXT NOT NULL CHECK(bill_to IN ('patient','doctor')),
  charge_p INTEGER,
  payable_p INTEGER,
  by_whom TEXT, at TEXT,
  voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS surg_vendor_pay (
  id INTEGER PRIMARY KEY,
  vendor_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  amount_p INTEGER NOT NULL,
  mode TEXT NOT NULL CHECK(mode IN ('cash','bank','cheque')),
  note TEXT NOT NULL DEFAULT '',
  by_whom TEXT, at TEXT,
  voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS surg_cheque (
  id INTEGER PRIMARY KEY,
  vendor_id INTEGER NOT NULL,
  day TEXT NOT NULL,
  amount_p INTEGER NOT NULL,
  cheque_no TEXT NOT NULL DEFAULT '',
  from_whom TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  by_whom TEXT, at TEXT,
  voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS surg_cheque_alloc (
  id INTEGER PRIMARY KEY,
  cheque_id INTEGER NOT NULL,
  case_id INTEGER NOT NULL,
  amount_p INTEGER NOT NULL,
  by_whom TEXT, at TEXT
);
CREATE TABLE IF NOT EXISTS surg_receipt (
  id INTEGER PRIMARY KEY,
  day TEXT NOT NULL,
  amount_p INTEGER NOT NULL,
  from_whom TEXT NOT NULL DEFAULT '',
  period TEXT NOT NULL DEFAULT '',
  ref TEXT NOT NULL DEFAULT '',
  bank_table TEXT NOT NULL DEFAULT '',
  bank_line_id INTEGER,
  note TEXT NOT NULL DEFAULT '',
  by_whom TEXT, at TEXT,
  voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', void_why TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS surg_receipt_alloc (
  id INTEGER PRIMARY KEY,
  receipt_id INTEGER NOT NULL,
  case_id INTEGER NOT NULL,
  amount_p INTEGER NOT NULL,
  by_whom TEXT, at TEXT
);
CREATE INDEX IF NOT EXISTS ix_surg_case_payer ON surg_case(payer);
CREATE INDEX IF NOT EXISTS ix_surg_paper_case ON surg_paper(case_id);
CREATE INDEX IF NOT EXISTS ix_surg_paper_receipt ON surg_paper(receipt_id);
CREATE INDEX IF NOT EXISTS ix_surg_implant_case ON surg_implant(case_id);
CREATE INDEX IF NOT EXISTS ix_surg_implant_vendor ON surg_implant(vendor_id);
CREATE INDEX IF NOT EXISTS ix_surg_calloc_cheque ON surg_cheque_alloc(cheque_id);
CREATE INDEX IF NOT EXISTS ix_surg_ralloc_receipt ON surg_receipt_alloc(receipt_id);
CREATE INDEX IF NOT EXISTS ix_surg_ralloc_case ON surg_receipt_alloc(case_id);
"""
# The unit's two logins, written once on the first request if the unit has no rows yet (the owner may later switch a row off;
# a row that exists, active or not, is never touched again).
SEED_ROLES = (("shavez", "maker", "S579 surgery cases: cases, papers, implant lines"),
              ("manoj", "checker", "S579 surgery cases: everything, the money pages his alone"))

_schema_done = False


def init(app, db_getter, require_fn, audit_fn=None, unit="surgery"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, _unit
    _db, _require, _audit, _unit = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def _ensure(con):
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    # S680 (D801, D804): the record's new fields -- added, never rebuilt; every old row keeps its values
    def add(table, col):
        try:
            con.execute("ALTER TABLE %s ADD COLUMN %s" % (table, col))
        except sqlite3.OperationalError as e:    # only "the column is already there" is passed over; a lock or a fault stops here
            if "duplicate column" not in str(e).lower():
                raise
    for col in ("case_type TEXT NOT NULL DEFAULT 'surgical'", "source_id INTEGER", "payer_kind TEXT NOT NULL DEFAULT ''",
                "admit_date TEXT NOT NULL DEFAULT ''", "ipd_no TEXT NOT NULL DEFAULT ''", "diagnosis TEXT NOT NULL DEFAULT ''",
                "mlc INTEGER NOT NULL DEFAULT 0", "backfill INTEGER NOT NULL DEFAULT 0",
                "uhid TEXT NOT NULL DEFAULT ''", "mobile TEXT NOT NULL DEFAULT ''",
                "implant_status TEXT NOT NULL DEFAULT ''", "money_status TEXT NOT NULL DEFAULT ''"):
        add("surg_case", col)
    add("surg_vendor", "hidden TEXT NOT NULL DEFAULT ''")   # S581: a vendor with no live entries can be taken off the lists
    con.execute("CREATE TABLE IF NOT EXISTS surg_source (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE COLLATE NOCASE, "
                "hidden TEXT NOT NULL DEFAULT '', created_by TEXT, created_at TEXT)")
    for nm in SEED_SOURCES:                      # INSERT OR IGNORE: one he has taken off the list is never brought back
        con.execute("INSERT OR IGNORE INTO surg_source (name, created_by, created_at) VALUES (?,?,?)", (nm, "S680", _stamp()))
    # D804: the TPA / scheme names -- a list of its own; the names already written on cases join it (never brought back if hidden)
    con.execute("CREATE TABLE IF NOT EXISTS surg_tpa (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE COLLATE NOCASE, "
                "hidden TEXT NOT NULL DEFAULT '', created_by TEXT, created_at TEXT)")
    con.execute("INSERT OR IGNORE INTO surg_tpa (name, created_by, created_at) SELECT DISTINCT insurer, 'S680', ? FROM surg_case "
                "WHERE insurer<>'' AND voided_at=''", (_stamp(),))
    # S370 (the owner, 30-Oct 12:49 / 13:07): a call placed from the case through MyOperator's IVR -- who, when, the number's last 4
    con.execute("CREATE TABLE IF NOT EXISTS surg_call (id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL, last4 TEXT NOT NULL DEFAULT '', "
                "result TEXT NOT NULL DEFAULT 'trying', why TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT)")
    # an old row heals by itself: its payer kind from its payer (BUILD_NORM 1)
    con.execute("UPDATE surg_case SET payer_kind = CASE payer WHEN 'cashless' THEN 'tpa' WHEN 'deendayal' THEN 'other' ELSE payer END "
                "WHERE payer_kind='' OR (CASE payer_kind WHEN 'package' THEN 'cash' WHEN 'tpa' THEN 'cashless' WHEN 'other' THEN 'deendayal' "
                "ELSE payer_kind END) <> payer")
    try:
        con.execute("UPDATE business_unit SET name='IPD cases' WHERE code=? AND name='Surgery cases'", (_unit,))
    except Exception:                            # noqa: BLE001 -- no business_unit table (the walk's bare database)
        pass
    try:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES (?,?,1,1)", (_unit, "IPD cases"))
        n = con.execute("SELECT COUNT(*) FROM unit_role WHERE unit=?", (_unit,)).fetchone()[0]
        if not n:
            for user, role, note in SEED_ROLES:
                con.execute("INSERT INTO unit_role (unit, username, role, active, note) VALUES (?,?,?,1,?)", (_unit, user, role, note))
    except Exception:                            # noqa: BLE001 -- no unit_role table (the walk's bare database): nothing to seed
        pass
    con.commit()
    _schema_done = True


# ---------------------------------------------------------------- small helpers
def _now():
    """The box's clock is IST. SURGERY_NOW=<iso> pins it for the walk."""
    v = os.environ.get("SURGERY_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)


def _today():
    return _now().date()


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def _inr(n):
    """S581: Indian grouping -- 1,50,000 and 12,34,567, not 150,000."""
    s = str(int(n))
    if len(s) <= 3:
        return s
    head, parts = s[:-3], []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts) + "," + s[-3:]


def _r(p):
    if p is None:
        return "—"
    neg = p < 0
    s = "₹ " + _inr(int(round(abs(p) / 100.0)))
    return ("− " + s) if neg else s


def _iso_ok(d):
    try:
        return dt.date(int(d[:4]), int(d[5:7]), int(d[8:10])).isoformat() == d
    except (ValueError, IndexError, TypeError):
        return False


def _human(iso):
    return dt.date.fromisoformat(iso).strftime("%d-%b-%Y") if _iso_ok(iso or "") else (iso or "—")


def _short(iso):
    """18-Oct (this year) or 01-Jun-2025."""
    if not _iso_ok(iso or ""):
        return "—"
    d = dt.date.fromisoformat(iso)
    return d.strftime("%d-%b") if d.year == _today().year else d.strftime("%d-%b-%Y")


def _paise(v, allow_blank=False):
    """A rupee figure typed by a person. Blank -> None when allowed; anything else that is not a clean number -> False."""
    s = str(v or "").replace(",", "").replace("₹", "").strip()
    if not s:
        return None if allow_blank else False
    if not re.fullmatch(r"\d+(\.\d{1,2})?", s):
        return False
    p = int(round(float(s) * 100))
    return p if 0 <= p <= MAX_P else False


def _txt(v, n=200):
    return re.sub(r"\s+", " ", str(v or "")).strip()[:n]


def _digits(s):
    return re.sub(r"\D", "", str(s or ""))


def mobiles(v):
    """D804: the phone number(s) as typed -> '98765xxxxx, 91234xxxxx' (ten digits each; a leading 91 or 0 dropped);
    '' when blank; False when what was typed is not a phone number."""
    s = str(v or "").strip()
    if not s:
        return ""
    out = []
    for part in re.split(r"[,;/\n]+", s):
        d = _digits(part)
        if not d:
            continue
        if len(d) == 20:                         # two numbers typed with only a space between them
            groups = [d[:10], d[10:]]
        else:
            if len(d) in (11, 12) and (d.startswith("0") or d.startswith("91")):
                d = d[-10:]
            groups = [d]
        for g in groups:
            if len(g) != 10 or g[0] not in "6789":
                return False
            if g not in out:
                out.append(g)
    return ", ".join(out[:3])


def _spaced(m):
    return m[:5] + " " + m[5:] if len(m) == 10 else m


def show_mobiles(v):
    return ", ".join(_spaced(m) for m in str(v or "").split(", ") if m)


def mask_mobile(v):
    """The list's short form, as the mock-up: 98xxx 43210 (+1 when a second number is kept)."""
    ms = [m for m in str(v or "").split(", ") if m]
    if not ms:
        return ""
    m = ms[0]
    s = (m[:2] + "xxx " + m[5:]) if len(m) == 10 else m
    return s + (" +%d" % (len(ms) - 1) if len(ms) > 1 else "")


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r[0] if r and r[0] not in (None, "") else default
    except Exception:                            # noqa: BLE001
        return default


def is_on(con):
    return str(_setting(con, ON_KEY, "1")).strip() != "0"


def _audit_safe(con, table, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)
        con.commit()
    except Exception:                            # noqa: BLE001 -- a fault in the audit never loses the write
        pass


def _back(path, **kw):
    frag = ""
    if "#" in path:                              # D804: the list with a case open keeps its anchor after the query
        path, frag = path.split("#", 1)
        frag = "#" + frag
    q = "&".join("%s=%s" % (k, quote(str(v), safe="")) for k, v in kw.items() if v not in (None, ""))
    return redirect(path + (("&" if "?" in path else "?") + q if q else "") + frag)


def _ret_of(f, default):
    """D804: where a form made in place goes back to -- the list with that case open, or the case page. Only a path of this
    page is followed (never another site, never another page of the app)."""
    r = str(f.get("ret") or "").strip()
    if r and (r == BASE or r.startswith(BASE + "?") or r.startswith(BASE + "/")) and not re.search(r"[\s\\]|//|\.\.", r):
        return r
    return default


def _gate():
    """(user, is_checker, error_response). maker or checker of the unit; a maker only while the switch is on.
    The tables and the unit's two logins are made BEFORE the role check -- otherwise the first request is refused for want of them."""
    con = _db()
    _ensure(con)
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return None, False, (_shell("IPD cases", "<div class='card'><h2>Not permitted</h2><p>This is the IPD cases page. "
                                    "Your login is not on it. Ask Dr Manoj if this is wrong.</p></div>"), 403)
    roles = set(u.get("roles") or [])
    checker = "checker" in roles
    if not checker and not is_on(con):
        return None, False, (_shell("IPD cases", "<div class='card'><h2>IPD cases</h2><p>This page is closed for now — "
                                    "Dr Manoj will open it.</p></div>"), 403)
    return u, checker, None


def _owner():
    u, checker, err = _gate()
    if err:
        return None, err
    if not checker:
        return None, (_shell("IPD cases", "<div class='card'><h2>Dr Manoj only</h2><p>This page is for Dr Manoj.</p>"
                                              "<a class='btn' href='%s'>← Cases</a></div>" % BASE), 403)
    return u, None


# ---------------------------------------------------------------- reading
def case(con, cid):
    return con.execute("SELECT * FROM surg_case WHERE id=?", (cid,)).fetchone()


def papers(con, cid=None, rid=None):
    if rid is not None:
        return con.execute("SELECT * FROM surg_paper WHERE receipt_id=? AND voided_at='' ORDER BY id", (rid,)).fetchall()
    return con.execute("SELECT * FROM surg_paper WHERE case_id=? AND voided_at='' ORDER BY id", (cid,)).fetchall()


def implants(con, cid):
    return con.execute("SELECT i.*, v.name AS vendor FROM surg_implant i JOIN surg_vendor v ON v.id=i.vendor_id "
                       "WHERE i.case_id=? AND i.voided_at='' ORDER BY i.id", (cid,)).fetchall()


def received(con, cid):
    r = con.execute("SELECT COALESCE(SUM(a.amount_p),0) FROM surg_receipt_alloc a JOIN surg_receipt r ON r.id=a.receipt_id "
                    "WHERE a.case_id=? AND r.voided_at=''", (cid,)).fetchone()
    return r[0] or 0


def needed(payer, case_type="surgical", mlc=0):
    """The papers a case must have. S680: a case without an implant (surgical no implant, conservative) never asks for the
    implant page; a medicolegal case asks for the MLC papers and the police memo."""
    base = NEEDED_CREDIT if payer in CREDIT else NEEDED_CASH
    if case_type != "surgical":
        base = tuple(k for k in base if k != "implant")
    if mlc:
        base = base + ("mlc", "police")
    return base


def _col(row, key, default=None):
    """A column of a row that may come from before S680 (or from a narrow SELECT)."""
    try:
        return row[key] if key in row.keys() else default
    except Exception:                            # noqa: BLE001
        return default


def needed_for(c):
    return needed(c["payer"], _col(c, "case_type", "surgical") or "surgical", _col(c, "mlc", 0) or 0)


def missing_papers(con, c):
    have = {r["kind"] for r in papers(con, c["id"])}
    return [k for k in needed_for(c) if k not in have]


def kind_of(row):
    """S680: the payer kind of a case row (payer_kind; an old row read through its payer)."""
    k = _col(row, "payer_kind", "") or ""
    return k if k in KIND_WORD else LEGACY_KIND.get(_col(row, "payer", "cash"), "cash")


def pword(row):
    return KIND_WORD[kind_of(row)]


# ---- D804: the three statuses. Each has its SQL twin for the filters; the walk proves the two agree.
_GOT = ("(SELECT COALESCE(SUM(a.amount_p),0) FROM surg_receipt_alloc a JOIN surg_receipt r ON r.id=a.receipt_id "
        "WHERE a.case_id=c.id AND r.voided_at='')")
SQL_DISCH = "(c.discharge_date<>'' OR c.stage IN ('discharged','billed','closed') OR c.backfill=1)"
SQL_INSIDE = "(c.admit_date<>'' OR c.stage IN ('admitted','operated'))"
SQL_P = {"discharged": SQL_DISCH, "admitted": "(NOT %s AND %s)" % (SQL_DISCH, SQL_INSIDE),
         "planned": "(NOT %s AND NOT %s)" % (SQL_DISCH, SQL_INSIDE)}
SQL_MREC = "(c.money_status='received' OR (COALESCE(c.due_p,0)>0 AND %s>=c.due_p))" % _GOT     # COALESCE: a NULL never hides a case
SQL_M = {"received": SQL_MREC, "pending": "(NOT %s AND (%s OR c.money_status='pending'))" % (SQL_MREC, SQL_DISCH)}
SQL_INA = "(c.case_type<>'surgical' OR c.implant_status='na')"
SQL_I = {"na": SQL_INA, "paid": "(NOT %s AND c.implant_status IN ('paid','confirmed'))" % SQL_INA,
         "pending": "(NOT %s AND c.implant_status NOT IN ('paid','confirmed'))" % SQL_INA}


def pstatus(c):
    if (c["discharge_date"] or "") or c["stage"] in ("discharged", "billed", "closed") or _col(c, "backfill", 0):
        return "discharged"
    if (_col(c, "admit_date", "") or "") or c["stage"] in ("admitted", "operated"):
        return "admitted"
    return "planned"


def mstatus(c, got):
    if (_col(c, "money_status", "") or "") == "received" or (c["due_p"] and c["due_p"] > 0 and got >= c["due_p"]):
        return "received"
    if pstatus(c) == "discharged" or (_col(c, "money_status", "") or "") == "pending":
        return "pending"
    return ""


def istatus(c):
    """('na' | 'paid' | 'pending', the step's word)."""
    st = _col(c, "implant_status", "") or ""
    if (_col(c, "case_type", "surgical") or "surgical") != "surgical" or st == "na":
        return "na", "not needed"
    if st in ("paid", "confirmed"):
        return "paid", IMPLANT_WORD[st].lower()
    return "pending", IMPLANT_WORD.get(st or "pending").lower()


def auto_stage(c_stage, admit, surgery, discharge, kind):
    """The old stage column follows the dates by itself (D804: the statuses replace it on screen); a case already past
    discharge keeps 'bill sent' or 'closed'."""
    if c_stage in ("billed", "closed"):
        return c_stage
    if discharge:
        return "discharged"
    if surgery and surgery <= _today().isoformat():
        return "operated"
    if admit and admit <= _today().isoformat():
        return "admitted"
    if c_stage in ("applied", "approved"):
        return c_stage
    return "applied" if kind in CREDIT_KINDS else "planned"


def sources(con, all_=False):
    return con.execute("SELECT * FROM surg_source %sORDER BY name COLLATE NOCASE" % ("" if all_ else "WHERE hidden='' ")).fetchall()


def source_name(con, sid):
    if sid is None:
        return ""
    r = con.execute("SELECT name FROM surg_source WHERE id=?", (sid,)).fetchone()
    return r["name"] if r else ""


def source_id(con, name, who, unhide=True):
    """The id of a source by its name (any case); a name not on the list joins it; one taken off the list comes back -- only
    when Dr Manoj writes it (unhide); Shavez's case still takes the name."""
    name = _txt(name, 60)
    if not name:
        return None
    r = con.execute("SELECT id, hidden FROM surg_source WHERE name=?", (name,)).fetchone()
    if r:
        if r["hidden"] and unhide:
            con.execute("UPDATE surg_source SET hidden='' WHERE id=?", (r["id"],))
        return r["id"]
    return con.execute("INSERT INTO surg_source (name, created_by, created_at) VALUES (?,?,?)", (name, who, _stamp())).lastrowid


def tpas(con, all_=False):
    return con.execute("SELECT * FROM surg_tpa %sORDER BY name COLLATE NOCASE" % ("" if all_ else "WHERE hidden='' ")).fetchall()


def tpa_keep(con, name, who, unhide=True):
    """D804: a TPA / scheme name written on a case joins the list (one taken off the list comes back); returns the name as
    the list spells it."""
    name = _txt(name, 80)
    if not name:
        return ""
    r = con.execute("SELECT id, name, hidden FROM surg_tpa WHERE name=?", (name,)).fetchone()
    if r:
        if r["hidden"] and unhide:
            con.execute("UPDATE surg_tpa SET hidden='' WHERE id=?", (r["id"],))
        return r["name"]
    con.execute("INSERT INTO surg_tpa (name, created_by, created_at) VALUES (?,?,?)", (name, who, _stamp()))
    return name


def ipd_settings(con):
    """(admission_p, nursing_p, share_pct or None) -- D801 (1), his to edit on the Settings page."""
    def num(key, default):
        try:
            v = int(_setting(con, key, ""))
            return v if 0 <= v <= MAX_P else default
        except ValueError:
            return default
    sh = _setting(con, SET_SHARE, "")
    try:
        shv = float(sh) if sh != "" else None
        shv = shv if shv is None or 0 <= shv <= 100 else None
    except ValueError:
        shv = None
    return num(SET_ADMISSION, DEF_ADMISSION), num(SET_NURSING, DEF_NURSING), shv


# ---- D804: the patients mirror (READ ONLY) and the Case Pack's cases (READ ONLY)
def _console_rows():
    """Every row of the console's patients mirror, read only; [] when it is not there (the search then uses the rest)."""
    if not os.path.isfile(CONSOLE_DB):
        return []
    try:
        con = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB, uri=True, timeout=5)
        try:
            con.row_factory = sqlite3.Row
            return con.execute("SELECT phone10, name, clinic_id, patient_uid, last_visit FROM patients").fetchall()
        finally:
            con.close()
    except Exception:                            # noqa: BLE001 -- the mirror is being rebuilt or has another shape
        return []


def console_find(q):
    """[{cid, name, mobile, uid, last}] -- the S172 search's rule: the name contains it, the clinic ID or UID is it, or four or
    more digits are in the phone."""
    ql, qd, out = q.lower(), _digits(q), []
    for m in _console_rows():
        nm, cid, uid, ph = (m["name"] or "").strip(), (m["clinic_id"] or "").strip(), (m["patient_uid"] or "").strip(), _digits(m["phone10"])
        if (ql and ql in nm.lower()) or (cid and cid.lower() == ql) or (uid and uid.lower() == ql) or (len(qd) >= 4 and qd in ph):
            out.append(dict(cid=cid, name=nm, mobile=ph[-10:] if len(ph) >= 10 else ph, uid=uid, last=(m["last_visit"] or "").strip()))
            if len(out) >= 20:
                break
    return out


def console_mobile(cid, uid):
    """The full mobile of one patient from the mirror (by UID, else clinic ID); '' if none."""
    cid, uid = (cid or "").strip().upper(), (uid or "").strip()
    for m in _console_rows():
        if (uid and (m["patient_uid"] or "").strip() == uid) or (cid and (m["clinic_id"] or "").strip().upper() == cid):
            ph = _digits(m["phone10"])
            return ph[-10:] if len(ph) >= 10 else ""
    return ""


def _register_mobile(cid, name):
    if not cid:
        return ""
    try:
        r = _db().execute("SELECT mobile FROM surg_case WHERE voided_at='' AND mobile<>'' AND upper(clinic_id)=upper(?) ORDER BY id DESC LIMIT 1",
                          (cid,)).fetchone()
        return (r["mobile"] or "").split(", ")[0] if r else ""
    except Exception:                            # noqa: BLE001
        return ""


def console_cids_by_phone(qd):
    return {(m["clinic_id"] or "").strip().upper() for m in _console_rows() if (m["clinic_id"] or "").strip() and qd in _digits(m["phone10"])}


def casepack_entries(cid="", uid="", name=""):
    """[(case_id, case_date, what)] -- that patient's Case Pack cases (the newest row of each), newest first; read only."""
    if not os.path.isfile(CASE_LEDGER):
        return []
    cid, uid, name = (cid or "").strip().upper(), (uid or "").strip(), (name or "").strip().upper()
    by = {}
    try:
        with open(CASE_LEDGER, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                k = (r.get("Case_ID") or "").strip()
                if not k:
                    continue
                rc, ru, rn = (r.get("Clinic_Specific_Id") or "").strip().upper(), (r.get("Patient_UID") or "").strip(), (r.get("Patient_Name") or "").strip().upper()
                hit = (cid and rc == cid) or (uid and ru == uid) or (not cid and not uid and name and rn == name)
                if hit:
                    by[k] = ((r.get("Case_Date") or "").strip()[:10], _txt(r.get("OT_Procedure") or r.get("Consent_Procedure") or r.get("Estimate_Title"), 60))
    except Exception:                            # noqa: BLE001 -- unreadable: nothing offered, the box stays typeable
        return []
    return [(k, d, w) for k, (d, w) in sorted(by.items(), reverse=True)][:12]


def search_patients(con, q):
    """D804: [{cid, name, mobile, uid, hint}] -- this register's own cases first, then the patient master and the console's
    mirror (which brings the full mobile). Read only."""
    q = (q or "").strip()
    if len(q) < 2:
        return []
    like = "%" + q.replace("%", "").replace("_", "") + "%"
    qd = _digits(q)
    out, have = [], {}
    sql = ("SELECT clinic_id, patient, mobile, uhid, MAX(case_no) AS n FROM surg_case WHERE voided_at='' AND (patient LIKE ? OR clinic_id LIKE ? "
           "OR uhid LIKE ?%s) GROUP BY clinic_id, patient ORDER BY n DESC LIMIT 10" % (" OR mobile LIKE ?" if len(qd) >= 4 else ""))
    for r in con.execute(sql, (like, like, like) + (("%" + qd + "%",) if len(qd) >= 4 else ())):
        d = dict(cid=r["clinic_id"] or "", name=r["patient"], mobile=r["mobile"] or "", uid="", hint="", case_no=r["n"])
        out.append(d)
        if d["cid"]:
            have[d["cid"].upper()] = d
    try:
        for r in con.execute("SELECT clinic_id, name FROM patient_ref WHERE merged_into IS NULL AND (clinic_id LIKE ? OR name LIKE ?) "
                             "ORDER BY id DESC LIMIT 20", (like, like)):
            k = (r["clinic_id"] or "").upper()
            if k not in have:
                d = dict(cid=r["clinic_id"] or "", name=r["name"] or "?", mobile="", uid="", hint="patient master")
                out.append(d)
                have[k] = d
    except Exception:                            # noqa: BLE001 -- no patient master here: the register's own only
        pass
    for m in console_find(q):
        k = m["cid"].upper()
        if k and k in have:
            have[k]["mobile"] = have[k]["mobile"] or m["mobile"]
            have[k]["uid"] = have[k]["uid"] or m["uid"]
            continue
        d = dict(m, hint="last visit %s" % m["last"] if m["last"] else "clinic patient")
        out.append(d)
        if k:
            have[k] = d
    return out[:25]


def _env_key(name):
    """One KEY=value from the server's env file, read fresh; '' if absent. Never printed."""
    try:
        with open(WA_ENV, encoding="utf-8") as fh:
            for line in fh:
                k, _s, v = line.strip().partition("=")
                if k.strip() == name:
                    return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def ivr_agent(login):
    """The MyOperator name the call service knows this login by (ring_agents.json, as Call ke baad reads it); '' if none."""
    try:
        with open(RING_AGENTS, encoding="utf-8") as fh:
            d = json.load(fh)
        for x in (d.get("agents") or {}).values():
            if isinstance(x, dict) and str(x.get("user") or "").lower() == str(login or "").lower() and str(x.get("name") or "").strip():
                return str(x["name"]).strip()
    except Exception:                            # noqa: BLE001 -- unreadable: nobody can call from here
        pass
    return ""


def next_case_no(con, year=None):
    """S680: numbered in the year of admission (an old case of 2025 is S-2025-....); otherwise this year."""
    y = year if isinstance(year, int) and 2000 <= year <= 2999 else _today().year
    r = con.execute("SELECT case_no FROM surg_case WHERE case_no LIKE ? ORDER BY case_no DESC LIMIT 1", ("S-%d-%%" % y,)).fetchone()
    n = int(r[0].split("-")[-1]) + 1 if r else 1
    return "S-%d-%04d" % (y, n)


def vendor_payable(con, vid, cid):
    """What the vendor is actually owed for his implants on one credit case (payable if set, else the bill)."""
    r = con.execute("SELECT COALESCE(SUM(COALESCE(payable_p, bill_p)),0) FROM surg_implant WHERE vendor_id=? AND case_id=? AND voided_at=''",
                    (vid, cid)).fetchone()
    return r[0] or 0


def vendor_ledger(con, vid):
    """(rows, balance_p, waiting, unassigned). rows: (day, text, debit_p, credit_p). balance > 0: the doctor owes the vendor.
    Cash cases: each implant line is owed to the vendor (billed to the doctor, cleared in cash).
    Credit cases: the vendor is paid by cheque for the full bill; when a cheque is assigned to a patient, the cheque counts for
    the doctor and the actual amount due to the vendor counts against him -- so the gap is in his favour (the owner, 11:32).
    S370: an OLD case (backfill) stays out of the balance and the awaiting-cheque list -- its implant was settled, or not, before
    this register; its own status says which, and kit 4 settles them on the vendor's page. A cheque assigned to one still counts."""
    rows = []
    for r in con.execute("SELECT i.*, c.case_no, c.patient, c.payer, c.surgery_date FROM surg_implant i JOIN surg_case c ON c.id=i.case_id "
                         "WHERE i.vendor_id=? AND i.voided_at='' AND c.voided_at='' AND c.payer='cash' AND c.backfill=0 "
                         "ORDER BY c.surgery_date, i.id", (vid,)):
        extra = (" · charged to the patient %s" % _r(r["charge_p"])) if r["charge_p"] is not None else ""
        rows.append((r["surgery_date"] or (r["at"] or "")[:10], "%s · %s (%s) · %s%s" % (
            "Bill in the patient's name" if r["bill_to"] == "patient" else "Estimate, billed to Dr Manoj",
            r["patient"], r["case_no"], r["item"] + (" ×%d" % r["qty"] if r["qty"] != 1 else ""), extra), r["bill_p"], 0))
    for p in con.execute("SELECT * FROM surg_vendor_pay WHERE vendor_id=? AND voided_at='' ORDER BY day, id", (vid,)):
        rows.append((p["day"], "Paid by Dr Manoj (%s)%s" % (p["mode"], (" · " + p["note"]) if p["note"] else ""), 0, p["amount_p"]))
    done_cases = {}
    for a in con.execute("SELECT a.*, q.day, q.cheque_no, q.from_whom, c.case_no, c.patient FROM surg_cheque_alloc a "
                         "JOIN surg_cheque q ON q.id=a.cheque_id JOIN surg_case c ON c.id=a.case_id "
                         "WHERE q.vendor_id=? AND q.voided_at='' ORDER BY q.day, a.id", (vid,)):
        rows.append((a["day"], "Cheque %s from %s for %s (%s)" % (a["cheque_no"] or "—", a["from_whom"] or "—", a["patient"], a["case_no"]),
                     0, a["amount_p"]))
        if a["case_id"] not in done_cases:
            done_cases[a["case_id"]] = (a["day"], a["patient"], a["case_no"])
    for cid, (day, pat, no) in done_cases.items():
        rows.append((day, "Actually due to the vendor for %s (%s)" % (pat, no), vendor_payable(con, vid, cid), 0))
    rows.sort(key=lambda x: (x[0] or "", x[1]))
    bal = sum(r[2] - r[3] for r in rows)
    waiting = con.execute("SELECT DISTINCT c.id, c.case_no, c.patient, c.payer, c.payer_kind, c.surgery_date FROM surg_implant i JOIN surg_case c ON c.id=i.case_id "
                          "WHERE i.vendor_id=? AND i.voided_at='' AND c.voided_at='' AND c.payer<>'cash' AND c.backfill=0 AND c.id NOT IN "
                          "(SELECT a.case_id FROM surg_cheque_alloc a JOIN surg_cheque q ON q.id=a.cheque_id WHERE q.vendor_id=? AND q.voided_at='') "
                          "ORDER BY c.surgery_date", (vid, vid)).fetchall()
    unassigned = []
    for q in con.execute("SELECT * FROM surg_cheque WHERE vendor_id=? AND voided_at='' ORDER BY day", (vid,)):
        used = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM surg_cheque_alloc WHERE cheque_id=?", (q["id"],)).fetchone()[0] or 0
        if used < q["amount_p"]:
            unassigned.append((q, q["amount_p"] - used))
    return rows, bal, waiting, unassigned


def receipt_used(con, rid):
    return con.execute("SELECT COALESCE(SUM(amount_p),0) FROM surg_receipt_alloc WHERE receipt_id=?", (rid,)).fetchone()[0] or 0


def bank_candidates(con, amount_p, day):
    """Bank credits of exactly this amount, from 10 days before to 60 days after the receipt's day, not already tied."""
    out = []
    lo = (dt.date.fromisoformat(day) - dt.timedelta(days=10)).isoformat()
    hi = (dt.date.fromisoformat(day) + dt.timedelta(days=60)).isoformat()
    taken = {(r[0], r[1]) for r in con.execute("SELECT bank_table, bank_line_id FROM surg_receipt WHERE bank_line_id IS NOT NULL AND voided_at=''")}
    for t in BANK_TABLES:
        try:
            for r in con.execute("SELECT id, txn_date, description, deposit_p, account_ref FROM %s WHERE deposit_p=? AND txn_date BETWEEN ? AND ? "
                                 "ORDER BY txn_date LIMIT 10" % t, (amount_p, lo, hi)):
                if (t, r["id"]) not in taken:
                    out.append((t, r))
        except Exception:                        # noqa: BLE001 -- that bank's table does not exist here
            continue
    return out


def bank_line(con, t, lid):
    if t not in BANK_TABLES or lid is None:
        return None
    try:
        return con.execute("SELECT id, txn_date, description, deposit_p, account_ref FROM %s WHERE id=?" % t, (lid,)).fetchone()
    except Exception:                            # noqa: BLE001
        return None


def _tail(acc):
    d = re.sub(r"\D", "", str(acc or ""))
    return ("…" + d[-4:]) if d else str(acc or "")[:12]


# ---------------------------------------------------------------- pages: the cases
MSG = {"saved": "✓ Saved", "new": "✓ The case is made", "voided": "✓ Removed (kept in the record with its reason)",
       "paper": "✓ The paper is filed", "implant": "✓ The implant line is added", "paid": "✓ The payment is written",
       "cheque": "✓ The cheque is written", "alloc": "✓ The amounts against each patient are saved", "bank": "✓ Tied to the bank line",
       "vendor": "✓ The vendor is added", "hidden": "✓ The vendor is off the lists", "receipt": "✓ The hospital payment is written", "switch": "✓ Changed",
       "settings": "✓ Settings saved", "source": "✓ The list of sources is changed", "tpa": "✓ The list of TPA / scheme names is changed",
       "status": "✓ Status saved", "call": "📞 Your mobile will ring now — pick it up and MyOperator joins the patient.", "backfill": ""}
ERR = {"patient": "Write the patient's name.", "payer": "Choose the payer: cash, cash package, TPA cashless, Ayushman or other scheme.",
       "date": "Write a correct date.", "source": "Choose or write where the patient came from (the source).", "type": "Choose the type of case.",
       "share": "Write your share as a number from 0 to 100, or leave it blank.",
       "early": "Old cases start from 1-Apr-2025 — this date is earlier.", "dup": "",
       "mobile": "The mobile number is not right — ten digits (two numbers may be written with a comma between them).",
       "amount": "Write the amount in rupees (digits only).", "item": "Write what the implant is.", "vendor": "Choose or write the vendor.",
       "why": "Choose why it is being removed.", "gone": "That entry was not found (perhaps already removed).",
       "over": "The amounts against the patients add up to more than the payment.", "stage": "Choose a stage.",
       "status": "Choose one of the statuses shown.",
       "callagent": "Your phone is not on the IVR — ask Dr Manoj to add your login to the call list.",
       "callwait": "This case was called a moment ago — wait a minute and press again.",
       "callnum": "There is no ten-digit mobile on this case to call.", "calldown": "The call was not placed: the IVR service did not answer.",
       "callno": "The call was not placed: MyOperator refused it.", "callkey": "The call was not placed: calling is not set up on the server.",
       "kind": "Unknown kind of paper.", "dupvendor": "That vendor is already in the list.", "line": "That bank line is not available.",
       "off": "This page is closed for now."}


def _flash(a):
    m, e = MSG.get(a.get("msg") or "", ""), ERR.get(a.get("err") or "", "")
    return ("<div class='ok'>%s</div>" % m if m else "") + ("<div class='bad'>%s</div>" % e if e else "")


def _nav(checker, here=""):
    links = [("home", "/portal", "← Home"), ("cases", BASE, "Cases"), ("new", BASE + "/new", "+ New case"),
             ("backfill", BASE + "/backfill", "+ Old case (backfill)")]
    if checker:
        links += [("vendors", BASE + "/vendors", "Implant vendors"), ("receipts", BASE + "/receipts", "Hospital payments"),
                  ("settings", BASE + "/settings", "Settings")]
    return "<div class='tabs'>%s</div>" % "".join("<a class='tab%s' href='%s'>%s</a>" % (" on" if k == here else "", u, w)
                                                  for k, u, w in links)


def _opts(pairs, cur, first=None):
    out = ["<option value=''>%s</option>" % _esc(first)] if first is not None else []
    out += ["<option value='%s'%s>%s</option>" % (_esc(k), " selected" if str(k) == str(cur) else "", _esc(w)) for k, w in pairs]
    return "".join(out)


def _chips(name, pairs, cur, required=False):
    """Tappable choices (radio buttons that look like chips; work without a script)."""
    return "<div class='chips'>%s</div>" % "".join(
        "<label class='radio'><input type=radio name=%s value='%s'%s%s> %s</label>" % (name, _esc(k), " checked" if k == cur else "",
                                                                              " required" if required else "", _esc(w))
        for k, w in pairs)


def _why_chips():
    """D804: the reason for a removal is tapped, not typed."""
    return "<div class='chips why'>%s</div>" % "".join(
        "<label class='radio'><input type=radio name=why value='%s'> %s</label>" % (k, w) for k, w in VOID_WHY)


def _why_select():
    return _why_chips()


def _source_chips(con, cur="", required=True):
    """S680/D804: the sources as chips, and '+' to write a new one (it joins the list when the case is saved; the box also
    searches the list as it is typed)."""
    names = [s["name"] for s in sources(con)]
    if cur and cur not in names:
        names.append(cur)
    chips = "".join("<label class='radio'><input type=radio name=source value='%s'%s%s> %s</label>" % (
        _esc(n), " checked" if n == cur else "", " required" if required else "", _esc(n)) for n in names)
    return ("<div class='chips src'>%s<input name=source_new class='in s' list=ipd_sources placeholder='+ another' autocomplete=off "
            "oninput='ipdSrc(this)'><datalist id=ipd_sources>%s</datalist></div>") % (
        chips, "".join("<option value='%s'>" % _esc(n) for n in names))


def _tpa_box(con, cur=""):
    """D804: the TPA / scheme as a drop-down; '+ add' writes a new name (it joins the list when the case is saved)."""
    names = [t["name"] for t in tpas(con)]
    if cur and cur not in names:
        names.append(cur)
    return ("<span class='tpa'><select name=insurer class='in m' onchange='ipdTpa(this)'><option value=''>—</option>%s"
            "<option value='+'>+ add a name</option></select><input name=insurer_new class='in m' placeholder='the TPA or scheme' "
            "style='display:none'></span>") % "".join(
        "<option value='%s'%s>%s</option>" % (_esc(n), " selected" if n == cur else "", _esc(n)) for n in names)


def _cp_box(entries, cur=""):
    """D804: the Case Pack number picked from the patient's own Case Pack cases."""
    keys = [k for k, _d, _w in entries]
    opts = "".join("<option value='%s'%s>%s%s</option>" % (_esc(k), " selected" if k == cur else "", _esc(k),
                                                         (" · " + _short(d)) if d else "") + "" for k, d, _w in entries)
    if cur and cur not in keys:
        opts += "<option value='%s' selected>%s</option>" % (_esc(cur), _esc(cur))
    return "<select name=casepack_id class='in m'><option value=''>none</option>%s</select>" % opts


def _chip(word, tone):
    return "<span class='chip c-%s'>%s</span>" % (tone, word)


def status_chips(c, got):
    p = pstatus(c)
    out = [_chip({"planned": "Not admitted yet", "admitted": "Admitted", "discharged": "Discharged"}[p], "blue" if p == "admitted" else "grey")]
    m = mstatus(c, got)
    out.append(_chip("Hospital money: " + (m or "—"), {"received": "ok", "pending": "warn"}.get(m, "grey")))
    i, w = istatus(c)
    out.append(_chip("Implant: " + w, {"paid": "ok", "na": "grey"}.get(i, "warn")))
    return " ".join(out)


def next_step(con, c, got, miss=None):
    """D804: the one line that says what is waiting, and the section that does it."""
    surgical = (_col(c, "case_type", "surgical") or "surgical") == "surgical"
    old = _col(c, "backfill", 0)
    if not old and not (_col(c, "admit_date", "") or ""):
        return "Enter the admission date and the IPD number when the patient is admitted.", 1
    if not old and surgical and not c["surgery_date"]:
        return "Enter the surgery: its date and the operation.", 2
    if surgical and not implants(con, c["id"]) and not old:
        return "Add the implant (vendor, what it is, the vendor's bill).", 2
    if pstatus(c) != "discharged":
        return "At discharge: the discharge date, then scan the papers.", 3
    miss = missing_papers(con, c) if miss is None else miss
    if miss and not old:
        return "Scan the missing papers: %s." % ", ".join(PAPER_WORD[k] for k in miss), 3
    if mstatus(c, got) != "received":
        return "Hospital money pending — mark it received when it comes (from the hospital's statement).", 5
    i, w = istatus(c)
    if i == "pending":
        return "Implant payment: %s — move it on as the bill and the cheque go." % w, 2
    return "Nothing waiting on this case.", 0


def _days(c):
    ad = _col(c, "admit_date", "") or ""
    if not _iso_ok(ad):
        return None
    end = c["discharge_date"] if _iso_ok(c["discharge_date"] or "") else None
    n = ((dt.date.fromisoformat(end) if end else _today()) - dt.date.fromisoformat(ad)).days
    return max(n, 1) if n >= 0 else None


def _dates(c):
    ad, dd = _col(c, "admit_date", "") or "", c["discharge_date"] or ""
    if not ad and not dd:
        return "—"
    return "<span class=nw>%s</span> → <span class=nw>%s</span>" % (_short(ad) if ad else "—", _short(dd) if dd else ("<span class='good'>admitted</span>" if ad else "—"))


def _where(a, con):
    """The list's filters as SQL. Returns (where, args, the filters' values)."""
    v = dict(src=a.get("src") if (a.get("src") or "").isdigit() else "",
             type=a.get("type") if a.get("type") in TYPE_WORD else "",
             p=a.get("p") or {"cash": "cash", "credit": "credit", "cashless": "tpa", "ayushman": "ayushman", "deendayal": "other"}.get(a.get("t") or "", ""),
             pt=a.get("pt") if a.get("pt") in SQL_P else "", money=a.get("money") if a.get("money") in SQL_M else "",
             imp=a.get("imp") if a.get("imp") in SQL_I else "", show=a.get("show") if a.get("show") in ("old", "new") else "",
             q=_txt(a.get("q"), 40))
    v["p"] = v["p"] if (v["p"] in KIND_WORD or v["p"] == "credit") else ""          # S680: an old ?t= link still filters
    where, args = ["c.voided_at=''"], []
    if v["p"] == "credit":
        where.append("c.payer_kind IN ('tpa','ayushman','other')")
    elif v["p"]:
        where.append("c.payer_kind=?")
        args.append(v["p"])
    if v["type"]:
        where.append("c.case_type=?")
        args.append(v["type"])
    if v["pt"]:
        where.append(SQL_P[v["pt"]])
    if v["money"]:
        where.append(SQL_M[v["money"]])
    if v["imp"]:
        where.append(SQL_I[v["imp"]])
    if v["show"] == "old":
        where.append("c.backfill=1")
    elif v["show"] == "new":
        where.append("c.backfill=0")
    q = v["q"]
    if q:
        like = "%" + q + "%"
        parts = ["c.patient LIKE ?", "c.clinic_id LIKE ?", "c.case_no LIKE ?", "c.ipd_no LIKE ?", "c.uhid LIKE ?"]
        args += [like] * 5
        qd = _digits(q)
        if len(qd) in (11, 12) and (qd.startswith("0") or qd.startswith("91")):
            qd = qd[-10:]                        # with +91 or a leading 0 typed: the ten digits, as mobiles() keeps them
        if len(qd) >= 5 and re.fullmatch(r"[\d\s+-]+", q):   # D804: the full mobile (only a number is searched as one)
            parts.append("replace(c.mobile,' ','') LIKE ?")
            args.append("%" + qd + "%")
            cids = sorted(console_cids_by_phone(qd))[:200]
            if cids:
                parts.append("upper(c.clinic_id) IN (%s)" % ",".join("?" * len(cids)))
                args += cids
        where.append("(" + " OR ".join(parts) + ")")
    return where, args, v


@bp.route(BASE, methods=["GET", "POST"])
def list_page():
    """S370: the search box posts (a phone number never sits in an address, so never in the web server's log)."""
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    a = request.values
    where, args, v = _where(a, con)
    counts = {}                                  # per source, over the list as filtered by everything but the source itself (no limit)
    for r in con.execute("SELECT c.source_id, s.name AS source, COUNT(*) AS n FROM surg_case c LEFT JOIN surg_source s ON s.id=c.source_id "
                         "WHERE %s GROUP BY c.source_id" % " AND ".join(where), args):
        counts[(r["source_id"], r["source"] or "no source")] = r["n"]
    if v["src"]:
        where.append("c.source_id=?")
        args.append(int(v["src"]))
    n_ip = con.execute("SELECT COUNT(*) FROM surg_case c WHERE %s AND %s" % (" AND ".join(where), SQL_I["pending"]), args).fetchone()[0]
    n_mp = con.execute("SELECT COUNT(*) FROM surg_case c WHERE %s AND %s" % (" AND ".join(where), SQL_M["pending"]), args).fetchone()[0]
    rows = con.execute("SELECT c.*, s.name AS source FROM surg_case c LEFT JOIN surg_source s ON s.id=c.source_id WHERE %s "
                       "ORDER BY COALESCE(NULLIF(c.admit_date,''), NULLIF(c.surgery_date,''), substr(c.created_at,1,10)) DESC, c.id DESC "
                       "LIMIT 500" % " AND ".join(where), args).fetchall()
    keep = [(k, v[k]) for k in ("src", "type", "p", "pt", "money", "imp", "show", "q") if v[k] and not (k == "q" and len(_digits(v[k])) >= 5)]
    here = BASE + ("?" + "&".join("%s=%s" % (k, quote(str(x), safe="")) for k, x in keep) if keep else "")
    out = [_nav(checker, "cases"), _flash(a)]
    if checker and not is_on(con):
        out.append("<div class='bad'>Closed for Shavez. <form method='post' action='%s/switch' class='inline'><input type=hidden name=on value=1>"
                   "<button class='save'>Open it</button></form></div>" % BASE)
    srcs = [(s["id"], s["name"]) for s in sources(con, all_=True) if not s["hidden"] or str(s["id"]) == v["src"]]
    quick = [("", "All"), ("pt=admitted", "Admitted"), ("money=pending", "Money pending"), ("imp=pending", "Implant pending"), ("show=old", "Old")]
    curq = "&".join("%s=%s" % kv for kv in keep if kv[0] != "q")
    out.append("<div class='qchips'><form method='post' action='%s' class='row2'><label class='f grow'><input name=q class='in' type=search value='%s' "
               "placeholder='name · mobile · IPD · UHID'></label><button class='btn sec2'>Find</button></form><div class='chips'>%s"
               "<a class='qc' href='#' onclick=\"document.body.classList.toggle('showfilt');return false\">More filters ▾</a></div></div>" % (
                   BASE, _esc(v["q"]), "".join("<a class='qc%s' href='%s%s'>%s</a>" % (" on" if k == curq else "", BASE, ("?" + k) if k else "", w)
                                               for k, w in quick)))
    out.append("<form method='post' action='%s' class='sec filt'><div class='sb row2'>"
               "<label class='f grow'>Search<input name=q class='in' type=search value='%s' placeholder='name · mobile · clinic ID · IPD · UHID · case no.'></label>"
               "<label class='f'>Patient<select name=pt class='in s'>%s</select></label>"
               "<label class='f'>Hospital money<select name=money class='in s'>%s</select></label>"
               "<label class='f'>Implant payment<select name=imp class='in s'>%s</select></label>"
               "<label class='f'>Payer<select name=p class='in s'>%s</select></label>"
               "<label class='f'>Source<select name=src class='in s'>%s</select></label>"
               "<label class='f'>Type<select name=type class='in s'>%s</select></label>"
               "<label class='f'>Cases<select name=show class='in s'>%s</select></label>"
               "<button class='btn'>Show</button></div></form>" % (
                   BASE, _esc(v["q"]), _opts(PSTAT, v["pt"], "Any"), _opts(MONEY, v["money"], "Any"), _opts(ISHOW, v["imp"], "Any"),
                   _opts((("credit", "Credit — all"),) + KINDS, v["p"], "All"), _opts(srcs, v["src"], "All"),
                   _opts(TYPES, v["type"], "All"), _opts(CASESHOW[1:], v["show"], "All cases")))
    if counts or n_ip or n_mp:
        kq = "&".join("%s=%s" % (k, quote(str(x), safe="")) for k, x in keep if k != "src")
        out.append("<p class='sm'>By source: %s%s%s</p>" % (" · ".join(
            ("<a href='%s?src=%s%s'>%s %d</a>" % (BASE, sid, ("&" + kq) if kq else "", _esc(nm), n)) if sid else "%s %d" % (_esc(nm), n)
            for (sid, nm), n in sorted(counts.items(), key=lambda x: (-x[1], x[0][1].lower()))),
            " · <a href='%s?imp=pending'><b>Implant payment pending: %d</b></a>" % (BASE, n_ip),
            " · <a href='%s?money=pending'><b>Hospital money pending: %d</b></a>" % (BASE, n_mp)))
    opened = int(a.get("open")) if (a.get("open") or "").isdigit() else None
    if opened and opened not in {c["id"] for c in rows}:       # S370: a case opened from a search the address no longer carries
        oc = con.execute("SELECT c.*, s.name AS source FROM surg_case c LEFT JOIN surg_source s ON s.id=c.source_id "
                         "WHERE c.id=? AND c.voided_at=''", (opened,)).fetchone()
        rows = ([oc] if oc else []) + list(rows)
    body = []
    for c in rows:
        got = received(con, c["id"])
        nxt, _sec = next_step(con, c, got)
        mm = re.match(r"Scan the missing papers: (.*)\.$", nxt)
        if mm and mm.group(1).count(",") >= 1:   # the list keeps it to one short phrase; the case itself names them
            nxt = "Scan %d missing papers." % (mm.group(1).count(",") + 1)
        ids = " · ".join(x for x in (("UHID " + _esc(c["uhid"])) if c["uhid"] else "", ("IPD " + _esc(c["ipd_no"])) if c["ipd_no"] else "",
                                     "<span class=nw>%s</span>" % _esc(show_mobiles(c["mobile"])) if c["mobile"] else "",
                                     "<b class='warn'>MLC</b>" if c["mlc"] else "",
                                     "<span class='chip c-grey'>old case</span>" if c["backfill"] else "") if x)
        dx = " · ".join(x for x in (_esc(c["diagnosis"]), _esc(c["procedure_text"])) if x) or "—"
        inner = ""
        if opened == c["id"]:
            inner = case_sections(con, c, checker, ret="%s%sopen=%d#c%d" % (here, "&" if "?" in here else "?", c["id"], c["id"]), who=u.get("user", ""))
        body.append(
            "<details class='crow' id='c%d' data-id='%d'%s><summary>"
            "<span class='cp'><b>%s</b> <span class='sm'>%s</span><br><span class='sm'>%s</span></span>"
            "<span class='cs'>%s<br><span class='sm'>%s</span></span>"
            "<span class='cy'>%s%s</span>"
            "<span class='cd'>%s</span>"
            "<span class='cx'>%s</span>"
            "<span class='cst'>%s</span>"
            "<span class='cn'>%s</span></summary><div class='cbody'>%s</div></details>" % (
                c["id"], c["id"], " open" if opened == c["id"] else "",
                _esc(c["patient"]), _esc(c["case_no"]), ids or "&nbsp;",
                _esc(c["source"] or "—"), TYPE_WORD.get(c["case_type"], c["case_type"]),
                _esc(pword(c)), ("<br><span class='sm'>%s</span>" % _esc(c["insurer"])) if c["insurer"] else "",
                _dates(c), dx, status_chips(c, got), _esc(nxt), inner))
    head = ("<div class='chead'><span class='cp'>Patient</span><span class='cs'>Source · type</span><span class='cy'>Payer</span>"
            "<span class='cd'>Admitted → discharged</span><span class='cx'>Diagnosis · operation</span><span class='cst'>Status</span>"
            "<span class='cn'>Next step</span></div>")
    out.append("<div class='sec clist'>%s%s</div>" % (head, "".join(body) or "<p class='sb sm'>No cases here.</p>"))
    out.append("<p class='sm'>%d case%s. Tap a patient: the case opens below the row, on this page, and every entry is made there. "
               "Old cases sit in this same list, marked <span class='chip c-grey'>old case</span>. Everyone on this page sees everything "
               "on a case except the implant's actual cost, which only Dr Manoj sees.</p>" % (len(rows), "" if len(rows) == 1 else "s"))
    return _shell("IPD cases", "<h1>IPD cases <span class=sm>· one record per admission</span></h1>" + "".join(out) + LIST_JS % here)


LIST_JS = """<script>
(function(){var here=%r;
function load(d){var b=d.querySelector('.cbody');if(!b||b.dataset.done)return;b.dataset.done=1;b.innerHTML="<p class='sm'>Opening…</p>";
var id=d.dataset.id,ret=here+(here.indexOf('?')<0?'?':'&')+'open='+id+'#c'+id;
fetch('/finance/surgery/case/'+id+'?frag=1&ret='+encodeURIComponent(ret),{credentials:'same-origin'}).then(function(r){return r.text()})
.then(function(t){b.innerHTML=t}).catch(function(){b.innerHTML="<p><a href='/finance/surgery/case/"+id+"'>Open the case</a></p>"})}
document.querySelectorAll('details.crow').forEach(function(d){if(d.open&&d.querySelector('.cbody').children.length)d.querySelector('.cbody').dataset.done=1;
d.addEventListener('toggle',function(){if(d.open)load(d)})});
var o=document.querySelector('details.crow[open]');if(o)o.scrollIntoView({block:'start'});})();
</script>"""


# ---------------------------------------------------------------- the case: its stage sections (in place on the list, or its own page)
def _sec(n, title, summary, body, open_):
    return "<details class='sec stg'%s id='s%d'><summary class='sh'>%s · %s <span class='fold'>%s</span></summary><div class='sb'>%s</div></details>" % (
        " open" if open_ else "", n, n, title, summary, body)


def _hid(ret):
    return "<input type=hidden name=ret value='%s'>" % _esc(ret) if ret else ""


def case_sections(con, c, checker, ret="", who=None):
    """D804: one case in its stage sections. Every form carries ret (the list with this case open, or the case page)."""
    cid = c["id"]
    got = received(con, cid)
    miss = missing_papers(con, c)
    nxt, open_n = next_step(con, c, got, miss)
    srcname = source_name(con, c["source_id"])
    days = _days(c)
    adm, nur, _share = ipd_settings(con)
    head = ("<div class='chd'><b>%s</b> · <span class='sm nw'>%s</span>%s%s%s%s</div>"
            "<div class='chips'>%s%s%s%s%s</div>") % (
        _esc(c["patient"]), _esc(c["case_no"]), (" · <span class=nw>UHID " + _esc(c["uhid"]) + "</span>") if c["uhid"] else "",
        (" · <span class=nw>IPD " + _esc(c["ipd_no"]) + "</span>") if c["ipd_no"] else "",
        (" · <span class=nw>" + _esc(show_mobiles(c["mobile"])) + "</span>") if c["mobile"] else "",
        (" · <span class=nw>clinic ID " + _esc(c["clinic_id"]) + "</span>") if c["clinic_id"] else "",
        _chip(_esc(srcname), "blue") if srcname else "", _chip(TYPE_WORD.get(c["case_type"], c["case_type"]), "blue"),
        _chip(_esc(pword(c)) + ((" · " + _esc(c["insurer"])) if c["insurer"] else ""), "blue"),
        _chip("Case Pack " + _esc(c["casepack_id"]), "grey") if c["casepack_id"] else "", _chip("MLC", "bad") if c["mlc"] else "")
    agent = ivr_agent(who if who is not None else _login())
    ms_ = [m for m in str(c["mobile"] or "").split(", ") if m]
    if ms_:
        head += "<div class='chips calls'>%s</div>" % "".join(
            ("<form method='post' action='%s/case/%d/call' class='inline'>%s<input type=hidden name=n value='%d'>"
             "<button class='btn sm2'>📞 Call %s (IVR)</button></form>" % (BASE, cid, _hid(ret), i, _esc(_spaced(m))))
            if agent else ("<button class='btn sm2 sec2' disabled title='Your phone is not on the IVR call list'>📞 %s — IVR not set for "
                           "your login</button>" % _esc(_spaced(m)))
            for i, m in enumerate(ms_))
    out = [head, "<div class='next'><b>Next</b> %s <span class='sm'>%s</span></div>" % (_esc(nxt), status_chips(c, got))]
    if c["backfill"]:
        out.append("<p class='sm'>An old case, entered afterwards (backfill). Nothing on it is compulsory; papers are not asked for — add any that are found.</p>")
    # 1 admission -- the record
    out.append(_sec(1, "Admission", "%s%s · %s" % ((("done " + _short(c["admit_date"])) + ((" · %d day%s" % (days, "" if days == 1 else "s")) if days else ""))
                                                  if c["admit_date"] else "to enter",
                                                  (" · " + _esc(srcname)) if srcname else "", _esc(c["diagnosis"]) or "diagnosis —"),
                    _record_form(con, c, ret), open_n == 1))
    # 2 surgery, implant, assistants
    ims = implants(con, cid)
    irows = []
    for i in ims:
        money = "<td class=r>%s</td>" % (_r(i["charge_p"]) if i["charge_p"] is not None else "—")
        if checker:
            money += "<td class=r>%s</td>" % (_r(i["payable_p"]) if i["payable_p"] is not None else "—")
        irows.append("<tr><td>%s</td><td>%s</td><td class=r>%d</td><td class=r>%s</td><td>%s</td>%s</tr>" % (
            _esc(i["vendor"]), _esc(i["item"]), i["qty"], _r(i["bill_p"]),
            "In the patient's name" if i["bill_to"] == "patient" else "Dr Manoj (estimate)", money))
    ihead = "<tr><th>Vendor</th><th>Implant</th><th class=r>Qty</th><th class=r>Vendor's bill</th><th>Billed to</th><th class=r>Charged to patient</th>%s</tr>" % (
        "<th class=r>Actually due to vendor <span class='you'>you only</span></th>" if checker else "")
    surg = ("<form method='post' action='%s/case/%d/edit' class='row2'>%s"
            "<label class='f'>Surgery date<input type=date name=surgery_date class='in s' value='%s'></label>"
            "<label class='f grow'>Operation or treatment<input name=procedure_text class='in' value='%s' placeholder='e.g. PFN right hip · traction'></label>"
            "<button class='btn sec2'>Save</button></form>") % (BASE, cid, _hid(ret), _esc(c["surgery_date"]), _esc(c["procedure_text"]))
    ist, iw = istatus(c)
    ichips = ("<form method='post' action='%s/case/%d/status' class='row2'>%s<label class='f'>Implant payment <span class=sm>(now: %s)</span>%s</label>"
              "<button class='btn sec2'>Save</button></form>") % (
        BASE, cid, _hid(ret), _esc(iw), _chips("implant_status", IMPLANT_STEPS, _col(c, "implant_status", "") or ""))
    out.append(_sec(2, "Surgery, implant, assistants",
                    "%s%s · implant: %s" % (_short(c["surgery_date"]) if c["surgery_date"] else "surgery —",
                                           (" · " + _esc(c["procedure_text"])) if c["procedure_text"] else "", iw),
                    surg + "<table class='grid'><thead>%s</thead><tbody>%s</tbody></table>" % (
                        ihead, "".join(irows) or "<tr><td colspan=7 class=sm>No implant yet.</td></tr>") +
                    _implant_form(con, c, checker, ret) + (_void_list("implant", [(i["id"], "%s — %s" % (i["vendor"], i["item"])) for i in ims], ret, cid) if ims else "") +
                    ichips + "<p class='sm'>Assistants (technician, assisting doctor) and each implant's own payment steps come with the next "
                    "part of the build; their payments will be Dr Manoj's private entry.</p>", open_n == 2))
    # 3 discharge & papers
    plist = papers(con, cid)
    by = {}
    for p in plist:
        by.setdefault(p["kind"], []).append(p)
    need = needed_for(c)
    prow = []
    for k, w in PAPERS:
        files = by.get(k, [])
        state = ("<span class='good'>✓ %d</span>" % len(files)) if files else ("<span class='warn'>missing</span>" if k in need and not c["backfill"] else "<span class=sm>—</span>")
        links = " ".join("<a href='%s/paper/%d' target=_blank>%s</a>" % (BASE, p["id"], "page %d" % (i + 1)) for i, p in enumerate(files))
        prow.append("<tr><td>%s%s</td><td>%s</td><td>%s</td><td><a class='btn sm2 sec2' href='%s/case/%d/scan/%s%s'>Scan / upload</a></td></tr>" % (
            _esc(w), " <span class=sm>(needed)</span>" if k in need else "", state, links, BASE, cid, k,
            ("?ret=" + quote(ret, safe="")) if ret else ""))
    have_n = sum(1 for k in need if k in by)
    disch = ("<form method='post' action='%s/case/%d/edit' class='row2'>%s"
             "<label class='f'>Discharged on<input type=date name=discharge_date class='in s' value='%s'></label>"
             "<label class='f'>Days<input class='in xs' value='%s' disabled></label>"
             "<span class='sm'>Nursing at %s a day%s (from Settings; the bill step will let it be changed)</span>"
             "<button class='btn sec2'>Save</button></form>") % (
        BASE, cid, _hid(ret), _esc(c["discharge_date"]), days if days else "", _r(nur),
        (" × %d = %s" % (days, _r(nur * days))) if days else "")
    out.append(_sec(3, "Discharge & papers", "%s · papers %d of %d" % (("discharged " + _short(c["discharge_date"])) if c["discharge_date"] else "not discharged",
                                                                      have_n, len(need)),
                    disch + "<table class='grid ptab'><tbody>%s</tbody></table>" % "".join(prow) +
                    (_void_list("paper", [(p["id"], "%s — %s" % (PAPER_WORD.get(p["kind"], p["kind"]), (p["at"] or "")[:16])) for p in plist], ret, cid) if plist else "") +
                    "<p class='sm'>Thumbnails, and the new kinds (police FIR copy, previous hospital's papers, LAMA, DOPR), come with the next part of the build.</p>",
                    open_n == 3))
    # 4 the hospital bill (kit 3)
    out.append(_sec(4, "Hospital bill", "comes in a later part of the build",
                    "<p class='sm'>The bill's figures typed from the hospital's bill (total, discount, nursing, other doctors, X-ray / pathology, "
                    "misc; on a credit case what was billed, sanctioned and received, and the deductions), and your share worked out from them, "
                    "come in kit 3. Admission %s and nursing %s a day are kept on Settings.</p>" % (_r(adm), _r(nur)), False))
    # 5 payment & what remains -- everyone on the page sees the money from the hospital (D801 (6)); its pages are Dr Manoj's
    allocs = con.execute("SELECT a.amount_p, r.id, r.day, r.from_whom, r.period FROM surg_receipt_alloc a JOIN surg_receipt r ON r.id=a.receipt_id "
                         "WHERE a.case_id=? AND r.voided_at='' ORDER BY r.day", (cid,)).fetchall()
    lines = "".join(("<li><a href='%s/receipt/%d'>%s · %s%s</a> — %s</li>" % (BASE, r["id"], _human(r["day"]), _esc(r["from_whom"]),
                                                                           (" · " + _esc(r["period"])) if r["period"] else "", _r(r["amount_p"])))
                    if checker else ("<li>%s · %s%s — %s</li>" % (_human(r["day"]), _esc(r["from_whom"]),
                                                                 (" · " + _esc(r["period"])) if r["period"] else "", _r(r["amount_p"])))
                    for r in allocs) or "<li class=sm>Nothing received yet.</li>"
    bal = (c["due_p"] - got) if c["due_p"] is not None else None
    ms = mstatus(c, got)
    due_box = ("<label class='f'>Amount due to Dr Manoj from the hospital (₹) <span class='you'>you only</span>"
               "<input name=due class='in s amt' inputmode=decimal value='%s'></label>" % (
                   ("%.2f" % (c["due_p"] / 100.0)).rstrip("0").rstrip(".") if c["due_p"] is not None else "")) if checker else ""
    mform = ("<form method='post' action='%s/case/%d/status' class='row2'>%s<label class='f'>Hospital money <span class=sm>(now: %s)</span>%s</label>%s"
             "<button class='btn sec2'>Save</button></form>") % (
        BASE, cid, _hid(ret), ms or "—", _chips("money_status", MONEY, c["money_status"] or ""), due_box)
    out.append(_sec(5, "Payment & what remains", "hospital money: %s" % (ms or "—"),
                    "<h3>Money from the hospital</h3><p class='big'>Due %s · received %s · balance %s</p><ul>%s</ul>%s" % (
                        _r(c["due_p"]), _r(got), _r(bal) if bal is not None else "—", lines, mform), open_n == 5))
    # 6 implant settlement (kit 4), 7 follow-up (kit 6)
    out.append(_sec(6, "Implant settlement", "implant: %s" % iw,
                    "<p class='sm'>The implant bills desk (bill raised, the cheque's number, date and amount, the vendor's confirmation — every "
                    "pending one listed for the accounts) comes in kit 4. Until then the implant payment is moved on in section 2.</p>", False))
    out.append(_sec(7, "Follow-up after discharge", "comes in a later part of the build",
                    "<p class='sm'>A list of discharged patients to track and send WhatsApp from (through the clinic's own sender and "
                    "templates) comes in kit 6. No fixed schedule.</p>", False))
    # 8 what happened, in order
    ev = [((c["created_at"] or "")[:16], c["created_by"] or "", "the case was made" + (" (old case)" if c["backfill"] else ""))]
    if c["changed_at"] and c["changed_at"] != c["created_at"]:
        ev.append(((c["changed_at"] or "")[:16], c["changed_by"] or "", "last change"))
    ev += [((p["at"] or "")[:16], p["by_whom"] or "", "%s filed" % PAPER_WORD.get(p["kind"], p["kind"])) for p in plist]
    ev += [((i["at"] or "")[:16], i["by_whom"] or "", "implant entered (%s)" % i["item"]) for i in ims]
    ev += [((k["at"] or "")[:16], k["by_whom"] or "", "IVR call to …%s (%s)" % (k["last4"], {"accepted": "placed", "trying": "trying"}.get(k["result"], "not placed")))
           for k in con.execute("SELECT * FROM surg_call WHERE case_id=? ORDER BY id", (cid,))]
    ev.sort()
    out.append(_sec(8, "What happened, in order", "%d entr%s" % (len(ev), "y" if len(ev) == 1 else "ies"),
                    "<p class='sm'>%s</p>" % " · ".join("%s · %s — %s" % (_esc(t), _esc(w), _esc(x)) for t, w, x in ev), False))
    if checker:
        out.append("<details class='vd'><summary>Remove this whole case (made by mistake)</summary><form method='post' action='%s/void' class='row2'>"
                   "<input type=hidden name=kind value=case><input type=hidden name=id value='%d'><input type=hidden name=back value='%s'>%s"
                   "<button class='clear'>Remove the case</button></form></details>" % (BASE, cid, BASE, _why_chips()))
    return "<div class='case'>%s</div>" % "".join(out)


def _void_list(kind, items, ret, cid):
    word = {"paper": "a wrongly filed paper", "implant": "a wrong implant line"}[kind]
    return ("<details class='vd'><summary>Remove %s</summary><form method='post' action='%s/void' class='row2'>"
            "<input type=hidden name=kind value=%s><input type=hidden name=back value='%s'>"
            "<select name=id class='in m'><option value=''>— choose —</option>%s</select>%s<button class='clear'>Remove</button></form></details>") % (
        word, BASE, kind, _esc(ret or "%s/case/%d" % (BASE, cid)),
        "".join("<option value='%d'>%s</option>" % (i, _esc(t)) for i, t in items), _why_chips())


def _implant_form(con, c, checker, ret):
    vendors = con.execute("SELECT id, name FROM surg_vendor WHERE hidden='' ORDER BY name").fetchall()
    credit = c["payer"] in CREDIT
    return ("<details%s><summary>+ Add an implant line</summary><form method='post' action='%s/case/%d/implant' class='row2'>%s"
            "<label class='f'>Vendor<select name=vendor_id class='in m'><option value=''>— choose —</option>%s</select></label>"
            "<label class='f'>…or a new vendor<input name=vendor_new class='in m' placeholder='vendor name'></label>"
            "<label class='f grow'>Implant<input name=item class='in' placeholder='e.g. PFN 10x240 with screws'></label>"
            "<label class='f'>Qty<input name=qty class='in xs' value='1' inputmode=numeric></label>"
            "<label class='f'>Vendor's bill (₹)<input name=bill class='in s amt' inputmode=decimal></label>"
            "<label class='f'>Billed to<span class='chips'><label class='radio'><input type=radio name=bill_to value=patient%s> In the patient's name</label>"
            "<label class='radio'><input type=radio name=bill_to value=doctor%s> To Dr Manoj (estimate)</label></span></label>"
            "<label class='f'>Charged to the patient (₹, cash)<input name=charge class='in s amt' inputmode=decimal></label>%s"
            "<button class='btn'>Add</button></form></details>") % (
        "" if implants(con, c["id"]) else " open", BASE, c["id"], _hid(ret),
        "".join("<option value='%d'>%s</option>" % (v["id"], _esc(v["name"])) for v in vendors),
        " checked" if credit else "", "" if credit else " checked",
        ("<label class='f'>Actually due to the vendor (₹) <span class='you'>you only</span>"
         "<input name=payable class='in s amt' inputmode=decimal></label>") if checker else "")


def _record_form(con, c, ret):
    """Section 1: the record itself, compact (D804)."""
    entries = casepack_entries(c["clinic_id"], "", c["patient"])
    return ("<form method='post' action='%s/case/%d/edit'>%s"
            "<div class='row2'><label class='f grow2'>Patient's name<input name=patient class='in' value='%s' required></label>"
            "<label class='f'>Mobile<input name=mobile class='in m' value='%s' inputmode=tel placeholder='10-digit mobile'></label>"
            "<label class='f'>Clinic ID <span class=sm>(optional)</span><input name=clinic_id class='in s' value='%s'></label>"
            "<label class='f'>Case Pack%s</label></div>"
            "<div class='row2'><label class='f'>Admitted on<input type=date name=admit_date class='in s' value='%s'></label>"
            "<label class='f'>IPD no.<input name=ipd_no class='in s' value='%s'></label>"
            "<label class='f'>UHID<input name=uhid class='in s' value='%s'></label>"
            "<label class='f grow2'>Diagnosis<input name=diagnosis class='in' value='%s'></label></div>"
            "<div class='row2'><label class='f'>Type%s</label><label class='f'>Source%s</label>"
            "<label class='f'>Medicolegal%s</label></div>"
            "<div class='row2'><label class='f'>Payer%s</label><label class='f'>TPA / scheme%s</label>"
            "<label class='f'>Hospital<input name=hospital class='in m' value='%s'></label>"
            "<label class='f grow'>Note<input name=note class='in' value='%s'></label></div>"
            "<button class='btn'>Save</button></form>") % (
        BASE, c["id"], _hid(ret), _esc(c["patient"]), _esc(show_mobiles(c["mobile"])), _esc(c["clinic_id"]), _cp_box(entries, c["casepack_id"]),
        _esc(c["admit_date"]), _esc(c["ipd_no"]), _esc(c["uhid"]), _esc(c["diagnosis"]),
        _chips("case_type", TYPES, c["case_type"]), _source_chips(con, source_name(con, c["source_id"]), required=c["source_id"] is not None),
        _chips("mlc", (("0", "No"), ("1", "Yes — MLC")), "1" if c["mlc"] else "0"),
        _chips("payer", KINDS, kind_of(c)), _tpa_box(con, c["insurer"]), _esc(c["hospital"]), _esc(c["note"]))


@bp.route(BASE + "/case/<int:cid>")
def case_page(cid):
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    c = case(con, cid)
    if not c or c["voided_at"]:
        if request.args.get("frag"):
            return "<p class='bad'>That case was not found (perhaps removed).</p>", 404
        return _shell("IPD case", _nav(checker) + "<div class='card'><h2>Not found</h2></div>"), 404
    a = request.args
    if a.get("frag"):                            # D804: the sections alone, opened in place on the list
        return case_sections(con, c, checker, ret=_ret_of(a, "%s/case/%d" % (BASE, cid)), who=u.get("user", ""))
    return _shell("%s %s" % (c["case_no"], c["patient"]), "<h1>IPD case</h1>" + _nav(checker) + _flash(a) +
                  "<p><a href='%s?open=%d#c%d'>← back to the list</a></p>" % (BASE, cid, cid) +
                  case_sections(con, c, checker, ret="%s/case/%d" % (BASE, cid), who=u.get("user", "")))


# ---------------------------------------------------------------- the forms: one form, three uses (new · backfill · the record)
def _case_fields(f, back, keep, con=None, who=""):
    """The record's fields from a form, checked. Only the fields the form carries (D804: a section's form changes only its own
    fields). (dict, None) or (None, redirect)."""
    out = {}
    if "payer" in f:
        kind = f.get("payer") or ""
        kind = kind if kind in KIND_WORD else LEGACY_KIND.get(kind, "")        # a form from before S680 still lands
        if not kind:
            return None, _back(back, err="payer", **keep)
        out.update(payer=KIND_CLASS[kind], payer_kind=kind)
    if "case_type" in f:
        ctype = f.get("case_type") or "surgical"
        if ctype not in TYPE_WORD:
            return None, _back(back, err="type", **keep)
        out["case_type"] = ctype
    for k in ("surgery_date", "discharge_date", "admit_date"):
        if k in f:
            v = (f.get(k) or "").strip()
            if v and not _iso_ok(v):
                return None, _back(back, err="date", **keep)
            out[k] = v
    if "mobile" in f:
        m = mobiles(f.get("mobile"))
        if m is False:
            return None, _back(back, err="mobile", **keep)
        out["mobile"] = m
    for k, n in (("procedure_text", 160), ("ipd_no", 30), ("diagnosis", 160), ("uhid", 30), ("clinic_id", 30), ("casepack_id", 30), ("note", 300)):
        if k in f:
            out[k] = _txt(f.get(k), n)
    if "insurer" in f or "insurer_new" in f:
        nm = _txt(f.get("insurer_new"), 80)
        if nm or f.get("insurer") != "+":        # '+ add a name' with nothing written changes nothing
            out["insurer"] = nm or _txt(f.get("insurer"), 80)
    if "mlc" in f:
        out["mlc"] = 1 if f.get("mlc") == "1" else 0
    return out, None


def _source_of(f):
    return _txt(f.get("source_new"), 60) or _txt(f.get("source"), 60)


def _patient_form(con, a, mode):
    """The new-case and the old-case form (board 9 / 12). mode: 'new' | 'backfill'."""
    cid, name = _txt(a.get("cid"), 30), _txt(a.get("name"), 80)
    uid = _txt(a.get("uid"), 40)
    # S370: the mobile is looked up here, never carried in an address -- the mirror, else this register's own case; after a
    # refused save the box is left empty (the number typed is never silently swapped for another)
    mob = "" if a.get("err") else ((console_mobile(cid, uid) if (cid or uid) else "") or _register_mobile(cid, name))
    hint = CP_KIND.get((a.get("payer") or "").strip().lower(), "")
    ctype = a.get("type") if a.get("type") in TYPE_WORD else "surgical"
    q = _txt(a.get("q"), 40)
    path = BASE + ("/new" if mode == "new" else "/backfill")
    # the Find box belongs to its own form (ipdfind, outside the case form -- forms never nest), tied to it by form=
    pick = ["<div class='row2'><label class='f grow'>Find<input name=q form=ipdfind class='in' type=search value='%s' "
            "placeholder='name or mobile or clinic ID — picks the patient and the Case Pack'></label><button class='btn sec2' form=ipdfind>Find</button></div>" % _esc(q)]
    if q:
        res = search_patients(con, q)
        if not res:
            pick.append("<p class='sm'>Nobody found — write the name below.</p>")
        for r in res:
            pick.append("<a class='pick' href='%s?cid=%s&name=%s&uid=%s&payer=%s'><b>%s</b> %s %s <span class='sm'>%s</span></a>" % (
                path, quote(r["cid"] or "", safe=""), quote(r["name"] or "", safe=""), quote(r["uid"] or "", safe=""), quote(hint, safe=""), _esc(r["name"]), ("· " + _esc(r["cid"])) if r["cid"] else "",
                ("· " + _esc(show_mobiles(r["mobile"]))) if r["mobile"] else "", _esc(r["hint"])) +
                (("<p class='sm'>↑ already has case %s — <a href='%s?q=%s'>open it</a> instead of making a second one, unless this is a new "
                  "admission.</p>") % (_esc(r["case_no"]), BASE, quote(r["case_no"], safe="")) if r.get("case_no") else ""))
    lo, hi = (BACKFILL_FROM, _today().isoformat()) if mode == "backfill" else ("", "")
    lim = (" min='%s' max='%s'" % (lo, hi)) if mode == "backfill" else ""
    entries = casepack_entries(cid, uid, name)
    cp = _txt(a.get("cp"), 30)
    old = ""
    if mode == "backfill":
        vendors = con.execute("SELECT id, name FROM surg_vendor WHERE hidden='' ORDER BY name").fetchall()
        old = ("<section class='sec'><div class='sh'>3 · What is known of it now <span class='fold'>fill what the old file shows; leave the rest</span></div><div class='sb'>"
               "<div class='row2'><label class='f'>Surgery date<input type=date name=surgery_date class='in s'%s></label>"
               "<label class='f'>Discharged on<input type=date name=discharge_date class='in s'%s></label>"
               "<label class='f grow'>Operation or treatment<input name=procedure_text class='in'></label></div>"
               "<div class='row2'><label class='f'>Implant<input name=item class='in m' placeholder='e.g. bipolar 46'></label>"
               "<label class='f'>Vendor<select name=vendor_id class='in m'><option value=''>— choose —</option>%s</select></label>"
               "<label class='f'>…or a new vendor<input name=vendor_new class='in m'></label>"
               "<label class='f'>Vendor's bill (₹)<input name=bill class='in s amt' inputmode=decimal></label></div>"
               "<div class='row2'><label class='f'>Implant payment%s</label></div>"
               "<div class='row2'><label class='f'>Hospital money%s</label></div></div></section>") % (
            lim, lim, "".join("<option value='%d'>%s</option>" % (v["id"], _esc(v["name"])) for v in vendors),
            _chips("implant_status", IMPLANT_STEPS, "pending"), _chips("money_status", MONEY, "pending"))
    form = ("<form id=ipdfind method='post' action='%s'><input type=hidden name=find value=1></form><form method='post' action='%s'>"
            "<section class='sec'><div class='sh'>1 · Patient</div><div class='sb'>%s"
            "<input type=hidden name=uid value='%s'>"
            "<div class='row2'><label class='f grow2'>Name<input name=patient class='in' value='%s' required></label>"
            "<label class='f'>Mobile%s<input name=mobile class='in m' value='%s' inputmode=tel placeholder='10-digit mobile'></label>"
            "<label class='f'>Clinic ID <span class=sm>(optional)</span><input name=clinic_id class='in m' value='%s'></label>"
            "<label class='f'>Case Pack%s</label></div></div></section>"
            "<section class='sec'><div class='sh'>2 · Admission</div><div class='sb'>"
            "<div class='row2'><label class='f'>Admitted on%s<input type=date name=admit_date class='in s'%s></label>"
            "<label class='f'>IPD no.<input name=ipd_no class='in s'></label><label class='f'>UHID<input name=uhid class='in s'></label>"
            "<label class='f grow2'>Diagnosis<input name=diagnosis class='in' placeholder='e.g. fracture shaft femur left'></label></div>"
            "<div class='row2'><label class='f'>Type%s</label><label class='f'>Source%s</label><label class='f'>Medicolegal%s</label></div>"
            "<div class='row2'><label class='f'>Payer%s</label><label class='f'>TPA / scheme%s</label>"
            "<label class='f'>Hospital<input name=hospital class='in m' value='%s'></label></div>"
            "%s</div></section>%s"
            "<div class='row2'><button class='btn'>%s</button><span class='sm'>%s</span></div></form>") % (
        path, path, "".join(pick), _esc(uid), _esc(name), " <span class='warn'>(write it again)</span>" if a.get("err") else "",
        _esc(show_mobiles(mob)), _esc(cid), _cp_box(entries, cp),
        "", lim,
        _chips("case_type", TYPES, ctype), _source_chips(con, required=(mode == "new")),
        _chips("mlc", (("0", "No"), ("1", "Yes — MLC")), "0"), _chips("payer", KINDS, hint, required=True), _tpa_box(con),
        _esc(DEFAULT_HOSPITAL), "" if mode == "backfill" else
        "<div class='row2'><label class='f'>Surgery date<input type=date name=surgery_date class='in s'></label>"
        "<label class='f grow'>Operation or treatment<input name=procedure_text class='in' placeholder='e.g. PFN right hip · traction'></label></div>",
        old, "Make the case" if mode == "new" else "Save this old case",
        "Surgery, implant and papers come on the case page, step by step. Nothing else is asked now." if mode == "new" else
        "Only the name and the payer are needed. After saving, this page opens empty for the next old case.")
    return form


@bp.route(BASE + "/new")
def new_page():
    u, checker, err = _gate()
    if err:
        return err
    return _new_view(u, checker, request.args)


def _new_view(u, checker, a):
    con = _db()
    out = [_nav(checker, "new"), _flash(a)]
    if a.get("cp"):
        out.append("<div class='ok'>From the Case Pack — %s</div>" % _esc(a.get("cp")))
    out.append(_patient_form(con, a, "new"))
    return _shell("New IPD case", "<h1>New IPD case</h1>" + "".join(out))


def _insert_case(con, f, who, new, extra):
    """Numbered in the admission year (else the year of the surgery or the discharge, else this year); two workers may number at
    once: the UNIQUE index decides, the loser takes the next."""
    yr = next((int(d[:4]) for d in (new.get("admit_date"), new.get("surgery_date"), new.get("discharge_date")) if d), None)
    cols = dict(clinic_id="", patient="", payer="cash", insurer="", hospital=DEFAULT_HOSPITAL, procedure_text="", surgery_date="",
                discharge_date="", stage="planned", casepack_id="", case_type="surgical", source_id=None, payer_kind="cash",
                admit_date="", ipd_no="", diagnosis="", mlc=0, uhid="", mobile="", implant_status="", money_status="", backfill=0, note="")
    cols.update({k: v for k, v in new.items() if k in cols})
    cols.update(extra)
    for _attempt in range(5):
        no = next_case_no(con, yr)
        try:
            cur = con.execute("INSERT INTO surg_case (case_no, created_by, created_at, changed_by, changed_at, %s) VALUES (?,?,?,?,?,%s)" % (
                ", ".join(cols), ",".join("?" * len(cols))), [no, who, _stamp(), who, _stamp()] + list(cols.values()))
            return no, cur.lastrowid
        except sqlite3.IntegrityError:
            continue
    return None, None


@bp.route(BASE + "/new", methods=["POST"])
def post_new():
    u, checker, err = _gate()
    if err:
        return err
    if request.form.get("find"):                 # the Find box (posted: a phone number never sits in an address)
        return _new_view(u, checker, request.form)
    con, f, who = _db(), request.form, u.get("user", "")
    patient = _txt(f.get("patient"), 80)
    keep = dict(cid=f.get("clinic_id"), name=patient, uid=f.get("uid"))
    if not patient:
        return _back(BASE + "/new", err="patient", cid=f.get("clinic_id"))
    if "payer" not in f:
        return _back(BASE + "/new", err="payer", **keep)
    new, bad = _case_fields(f, BASE + "/new", keep)
    if bad:
        return bad
    if not _source_of(f):
        return _back(BASE + "/new", err="source", **keep)
    if new["payer_kind"] in CREDIT_KINDS:      # as S680 v3: a credit case starts at pre-approval
        stage = "applied"
    elif new.get("admit_date") and new["admit_date"] <= _today().isoformat():
        stage = "admitted"
    else:
        stage = "planned"
    sid = source_id(con, _source_of(f), who, unhide=checker)
    if new.get("insurer"):
        new["insurer"] = tpa_keep(con, new["insurer"], who, unhide=checker)
    no, rid = _insert_case(con, f, who, dict(new, patient=patient, hospital=_txt(f.get("hospital"), 80) or DEFAULT_HOSPITAL),
                           dict(stage=stage, source_id=sid))
    if not no:
        con.rollback()
        return _back(BASE + "/new", err="gone")
    con.commit()
    _audit_safe(con, "surg_case", rid, "insert", None,
                dict(case_no=no, payer=new["payer_kind"], patient=patient, case_type=new.get("case_type", "surgical"), source_id=sid), who)
    return _back("%s?open=%d#c%d" % (BASE, rid, rid), msg="new")


@bp.route(BASE + "/case/<int:cid>/edit", methods=["POST"])
def post_edit(cid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    c = case(con, cid)
    if not c or c["voided_at"]:
        return _back(BASE, err="gone")
    back = _ret_of(f, "%s/case/%d" % (BASE, cid))
    if "stage" in f and f.get("stage") not in STAGE_WORD:
        return _back(back, err="stage")
    fields, bad = _case_fields(f, back, {})
    if bad:
        return bad
    new = dict(fields)
    if "patient" in f:
        new["patient"] = _txt(f.get("patient"), 80) or c["patient"]
    if "hospital" in f:
        new["hospital"] = _txt(f.get("hospital"), 80) or c["hospital"]
    src = _source_of(f)
    want_source = ("source" in f or "source_new" in f) and bool(src)   # a form without the source box keeps the source
    if ("source" in f or "source_new" in f) and not want_source and c["source_id"] is not None:
        return _back(back, err="source")         # a source once given is never emptied; a case from before S680 may stay without
    if checker and "due" in f:
        d = _paise(f.get("due"), allow_blank=True)
        if d is False:
            return _back(back, err="amount")
        new["due_p"] = d
    # the stage follows the dates by itself; a stage sent by a form (the old edit form) is still taken
    merged = {k: new.get(k, c[k]) for k in ("admit_date", "surgery_date", "discharge_date", "payer_kind")}
    if merged["discharge_date"] and merged["admit_date"] and merged["discharge_date"] < merged["admit_date"]:
        return _back(back, err="date")
    new["stage"] = f["stage"] if "stage" in f else auto_stage(c["stage"], merged["admit_date"], merged["surgery_date"],
                                                                 merged["discharge_date"], merged["payer_kind"])
    if c["backfill"] and "stage" not in f and new["stage"] not in ("discharged", "billed", "closed"):
        new["stage"] = "discharged"              # an old case is a discharged one, whatever dates are filled in later
    if want_source:                              # written only after every check has passed (nothing half-written on a refusal)
        new["source_id"] = source_id(con, src, who, unhide=checker)
    if new.get("insurer"):
        new["insurer"] = tpa_keep(con, new["insurer"], who, unhide=checker)
    before = {k: c[k] for k in new}
    con.execute("UPDATE surg_case SET %s, changed_by=?, changed_at=? WHERE id=?" % ", ".join("%s=?" % k for k in new),
                list(new.values()) + [who, _stamp(), cid])
    con.commit()
    _audit_safe(con, "surg_case", cid, "update", before, new, who)
    return _back(back, msg="saved")


@bp.route(BASE + "/case/<int:cid>/status", methods=["POST"])
def post_status(cid):
    """D804: the implant payment and the hospital money -- moved on by anyone on the page."""
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    c = case(con, cid)
    if not c or c["voided_at"]:
        return _back(BASE, err="gone")
    back = _ret_of(f, "%s/case/%d" % (BASE, cid))
    new = {}
    if "implant_status" in f:
        if f.get("implant_status") not in IMPLANT_WORD:
            return _back(back, err="status")
        new["implant_status"] = f["implant_status"]
    if "money_status" in f:
        if f.get("money_status") not in dict(MONEY):
            return _back(back, err="status")
        new["money_status"] = f["money_status"]
    if checker and "due" in f:
        d = _paise(f.get("due"), allow_blank=True)
        if d is False:
            return _back(back, err="amount")
        new["due_p"] = d
    if not new:
        return _back(back, err="status")
    before = {k: c[k] for k in new}
    con.execute("UPDATE surg_case SET %s, changed_by=?, changed_at=? WHERE id=?" % ", ".join("%s=?" % k for k in new),
                list(new.values()) + [who, _stamp(), cid])
    con.commit()
    _audit_safe(con, "surg_case", cid, "status", before, new, who)
    return _back(back, msg="status")


def _login():
    try:
        u, _e = _require("maker", "checker", unit=_unit)
        return (u or {}).get("user", "")
    except Exception:                            # noqa: BLE001
        return ""


@bp.route(BASE + "/case/<int:cid>/call", methods=["POST"])
def post_call(cid):
    """S370: call the case's patient through MyOperator's IVR -- the caller's own mobile rings first, then MyOperator joins the
    patient (call_api.py, as Call ke baad and the inbox do). The number is the case's STORED mobile (which one: n), never one from
    the page. One call per case per CALL_GAP seconds. Kept in surg_call with the last 4 digits only."""
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    c = case(con, cid)
    if not c or c["voided_at"]:
        return _back(BASE, err="gone")
    back = _ret_of(f, "%s/case/%d" % (BASE, cid))
    ms = [m for m in str(c["mobile"] or "").split(", ") if re.fullmatch(r"[6-9]\d{9}", m)]
    n = int(f["n"]) if (f.get("n") or "0").isdigit() else -1
    if not (0 <= n < len(ms)):
        return _back(back, err="callnum")
    agent = ivr_agent(who)
    if not agent:
        return _back(back, err="callagent")
    con.commit()
    con.execute("BEGIN IMMEDIATE")               # the check and the row in one step: a double tap on two workers places one call
    try:
        since = (_now() - dt.timedelta(seconds=CALL_GAP)).strftime("%Y-%m-%d %H:%M:%S")
        if con.execute("SELECT 1 FROM surg_call WHERE case_id=? AND at>?", (cid, since)).fetchone():
            con.rollback()
            return _back(back, err="callwait")
        rid = con.execute("INSERT INTO surg_call (case_id, last4, by_whom, at) VALUES (?,?,?,?)", (cid, ms[n][-4:], who, _stamp())).lastrowid
        con.commit()
    except Exception:                            # noqa: BLE001
        con.rollback()
        raise
    key = _env_key("CALL_API_SECRET")
    res, why, e = "refused", "", None
    if not key:
        e = "callkey"
    else:
        req = urllib.request.Request(CALL_URL, data=json.dumps({"agent": agent, "patient_number": ms[n], "reference_id": "IPD%d" % cid}).encode("utf-8"),
                                     method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Call-Key", key)
        try:
            with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=8) as resp:   # never through a proxy
                st, raw = resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as x:
            st, raw = x.code, x.read().decode("utf-8", "replace")
        except Exception:                        # noqa: BLE001 -- the service is down or slow
            st, raw = 0, ""
        try:
            j = json.loads(raw) if raw else {}
        except ValueError:
            j = {}
        j = j if isinstance(j, dict) else {}
        if st == 200 and j.get("accepted") is True:
            res = "accepted"
        elif st == 0:
            res, e = "error", "calldown"
        else:
            e = "callagent" if (st == 400 and "agent" in str(j.get("reason") or "").lower()) else "callno"
            why = re.sub(r"\d{5,}", lambda m: "…" + m.group(0)[-4:], " ".join(str(j.get("reason") or ("http %s" % st)).split()))[:120]
    con.execute("UPDATE surg_call SET result=?, why=? WHERE id=?", (res, why, rid))
    con.commit()
    _audit_safe(con, "surg_call", rid, "ivr_call", None, dict(case_id=cid, last4=ms[n][-4:], result=res), who)
    return _back(back, err=e) if e else _back(back, msg="call")


def _vendor_of(con, f, who):
    """The vendor chosen or newly written (S581: written again -> back on the lists). None when neither."""
    newv = _txt(f.get("vendor_new"), 80)
    if newv:
        r = con.execute("SELECT id FROM surg_vendor WHERE name=?", (newv,)).fetchone()
        if r:
            con.execute("UPDATE surg_vendor SET hidden='' WHERE id=?", (r["id"],))
            return r["id"]
        return con.execute("INSERT INTO surg_vendor (name, created_by, created_at) VALUES (?,?,?)", (newv, who, _stamp())).lastrowid
    if (f.get("vendor_id") or "").isdigit():
        r = con.execute("SELECT id FROM surg_vendor WHERE id=?", (int(f["vendor_id"]),)).fetchone()
        return r["id"] if r else None
    return None


@bp.route(BASE + "/case/<int:cid>/implant", methods=["POST"])
def post_implant(cid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    c = case(con, cid)
    back = _ret_of(f, "%s/case/%d" % (BASE, cid))
    if not c or c["voided_at"]:
        return _back(BASE, err="gone")
    item = _txt(f.get("item"), 160)
    if not item:
        return _back(back, err="item")
    qty = int(f["qty"]) if (f.get("qty") or "").strip().isdigit() and 0 < int(f["qty"]) < 1000 else 1
    bill = _paise(f.get("bill"))
    charge = _paise(f.get("charge"), allow_blank=True)
    payable = _paise(f.get("payable"), allow_blank=True) if checker else None      # the actual cost: Dr Manoj only (D801 (6))
    if bill is False or not bill or charge is False or payable is False:
        return _back(back, err="amount")
    vid = _vendor_of(con, f, who)                # written only after the amounts have passed (nothing half-written)
    if not vid:
        con.rollback()
        return _back(back, err="vendor")
    bill_to = f.get("bill_to") if f.get("bill_to") in ("patient", "doctor") else ("patient" if c["payer"] in CREDIT else "doctor")
    cur = con.execute("INSERT INTO surg_implant (case_id, vendor_id, item, qty, bill_p, bill_to, charge_p, payable_p, by_whom, at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                      (cid, vid, item, qty, bill, bill_to, charge, payable, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_implant", cur.lastrowid, "insert", None, dict(case_id=cid, vendor_id=vid, item=item, bill_p=bill), who)
    return _back(back, msg="implant")


@bp.route(BASE + "/void", methods=["POST"])
def post_void():
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = _ret_of({"ret": f.get("back")}, BASE)
    sep = "&" if "?" in back else "?"
    if "#" in back:
        back, frag = back.split("#", 1)
        frag = "#" + frag
        sep = "&" if "?" in back else "?"
    else:
        frag = ""
    table = {"paper": "surg_paper", "implant": "surg_implant", "pay": "surg_vendor_pay", "cheque": "surg_cheque",
             "receipt": "surg_receipt", "case": "surg_case"}.get(f.get("kind"))
    if table in ("surg_vendor_pay", "surg_cheque", "surg_receipt", "surg_case") and not checker:
        return redirect(back + sep + "err=gone" + frag)
    rid = f.get("id") or ""
    if not table or not rid.isdigit():
        return redirect(back + sep + "err=gone" + frag)
    if f.get("why") not in dict(VOID_WHY):
        return redirect(back + sep + "err=why" + frag)
    r = con.execute("SELECT * FROM %s WHERE id=? AND voided_at=''" % table, (int(rid),)).fetchone()
    if not r:
        return redirect(back + sep + "err=gone" + frag)
    con.execute("UPDATE %s SET voided_at=?, voided_by=?, void_why=? WHERE id=? AND voided_at=''" % table, (_stamp(), who, f["why"], int(rid)))
    con.commit()
    _audit_safe(con, table, int(rid), "void", {k: r[k] for k in r.keys() if k in ("amount_p", "bill_p", "kind", "case_no", "path")},
                dict(why=f["why"]), who)
    return redirect(back + sep + "msg=voided" + frag)


# ---------------------------------------------------------------- papers: the scanner, the upload, the file
def _scan_host(title, upload_url, fields, name_base, back_url):
    cfg = {"title": title, "uploadUrl": upload_url, "fileField": "file", "uploadFields": fields, "nameBase": name_base,
           "backUrl": back_url, "allowIdCard": False, "allowBatch": False, "directFile": True}
    return ("<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>body{margin:0;background:#f4f6fa;color:#0f172a;font:15px/1.5 system-ui,sans-serif}"
            ".top{background:#0b1220;color:#fff;padding:12px 16px;font-weight:650;display:flex;gap:12px;align-items:center;position:sticky;top:0;z-index:30}"
            ".top a{color:#e2e8f0;text-decoration:none;font-size:13px;padding:8px 13px;border-radius:9px;background:rgba(255,255,255,.13)}"
            "</style></head><body>"
            "<script>window.SCANNER_CONFIG = %s;</script><div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script><script src='/finance/scan/widget.js?v=581'></script></body></html>") % (
        _esc(title), json.dumps(cfg).replace("</", "<\\/"))


@bp.route(BASE + "/case/<int:cid>/scan/<kind>")
def scan_page(cid, kind):
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    c = case(con, cid)
    if not c or c["voided_at"] or kind not in PAPER_WORD:
        return _back(BASE, err="kind" if c else "gone")
    ret = _ret_of(request.args, "%s/case/%d" % (BASE, cid))       # D804: back to where the scan was asked for (the list, in place)
    frag = ""
    if "#" in ret:
        ret, frag = ret.split("#", 1)
        frag = "#" + frag
    return _scan_host("%s — %s (%s)" % (PAPER_WORD[kind], c["patient"], c["case_no"]), "%s/api/case/%d/paper/%s" % (BASE, cid, kind),
                      {"case_id": str(cid), "kind": kind}, "%s_%s" % (c["case_no"], kind), ret + ("&" if "?" in ret else "?") + "msg=paper" + frag)


def _sniff(blob):
    if blob[:5] == b"%PDF-":
        return "pdf", "application/pdf"
    if blob[:3] == b"\xff\xd8\xff":
        return "jpg", "image/jpeg"
    if blob[:8] == b"\x89PNG\r\n\x1a\n":
        return "png", "image/png"
    if blob[:4] == b"RIFF" and blob[8:12] == b"WEBP":
        return "webp", "image/webp"
    return None, None


def _store(blob, sub, base):
    ext, mime = _sniff(blob)
    if not ext:
        return None, None, None
    sha = hashlib.sha256(blob).hexdigest()
    folder = os.path.join(PAPER_DIR, sub)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, "%s_%s.%s" % (re.sub(r"[^A-Za-z0-9_-]", "_", base), sha[:10], ext))
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(blob)
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, path)
    return path, sha, mime


def _take_upload():
    f = request.files.get("file")
    if not f:
        return None, ("no_file", 400)
    blob = f.read(MAX_FILE + 1)
    if not blob:
        return None, ("empty_file", 400)
    if len(blob) > MAX_FILE:
        return None, ("too_big", 413)
    return blob, None


@bp.route(BASE + "/api/case/<int:cid>/paper/<kind>", methods=["POST"])
def api_paper(cid, kind):
    from flask import jsonify                    # noqa: PLC0415
    u, checker, err = _gate()
    if err:
        return jsonify(ok=False, error="not_permitted"), 403
    con, who = _db(), u.get("user", "")
    c = case(con, cid)
    if not c or c["voided_at"]:
        return jsonify(ok=False, error="no_case"), 404
    if kind not in PAPER_WORD:
        return jsonify(ok=False, error="bad_kind"), 400
    blob, e = _take_upload()
    if e:
        return jsonify(ok=False, error=e[0]), e[1]
    path, sha, mime = _store(blob, os.path.join((c["surgery_date"] or c["created_at"] or "0000")[:4], c["case_no"]), "%s_%s" % (c["case_no"], kind))
    if not path:
        return jsonify(ok=False, error="not_pdf_or_image", message="Only a PDF or a photo can be filed."), 415
    dup = con.execute("SELECT id FROM surg_paper WHERE case_id=? AND sha256=? AND voided_at=''", (cid, sha)).fetchone()
    if dup:
        return jsonify(ok=True, duplicate=True, id=dup["id"])
    cur = con.execute("INSERT INTO surg_paper (case_id, kind, path, sha256, bytes, mime, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                      (cid, kind, path, sha, len(blob), mime, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_paper", cur.lastrowid, "upload", None, dict(case_id=cid, kind=kind, sha256=sha, bytes=len(blob)), who)
    return jsonify(ok=True, id=cur.lastrowid, sha256=sha[:12])


@bp.route(BASE + "/paper/<int:pid>")
def get_paper(pid):
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    p = con.execute("SELECT * FROM surg_paper WHERE id=? AND voided_at=''", (pid,)).fetchone()
    if not p:
        return _shell("Paper", "<div class='card'><h2>Not found</h2></div>"), 404
    if p["receipt_id"] and not checker:
        return _shell("Paper", "<div class='card'><h2>Dr Manoj only</h2></div>"), 403
    # S581: a paper of a removed case or a removed hospital payment is removed with it
    owner_row = (case(con, p["case_id"]) if p["case_id"] else
                 con.execute("SELECT voided_at FROM surg_receipt WHERE id=?", (p["receipt_id"],)).fetchone() if p["receipt_id"] else None)
    if not owner_row or owner_row["voided_at"]:
        return _shell("Paper", "<div class='card'><h2>Not found</h2><p>This paper belonged to a removed record.</p></div>"), 404
    real = os.path.realpath(p["path"])
    if not real.startswith(os.path.realpath(PAPER_DIR) + os.sep) or not os.path.isfile(real):
        return _shell("Paper", "<div class='card'><h2>The file is missing</h2></div>"), 404
    resp = send_file(real, mimetype=p["mime"], as_attachment=False)
    resp.headers["Cache-Control"] = "private, no-store"
    return resp


# ---------------------------------------------------------------- the vendors (the owner only)
@bp.route(BASE + "/vendors")
def vendors_page():
    u, err = _owner()
    if err:
        return err
    con = _db()
    rows = []
    for v in con.execute("SELECT * FROM surg_vendor WHERE hidden='' ORDER BY name"):
        _r_, bal, waiting, unassigned = vendor_ledger(con, v["id"])
        rows.append("<tr><td><a href='%s/vendor/%d'>%s</a></td><td class=r>%s</td><td>%s</td><td>%s</td></tr>" % (
            BASE, v["id"], _esc(v["name"]), ("You owe " + _r(bal)) if bal > 0 else (("Owes you " + _r(-bal)) if bal < 0 else "settled"),
            ("%d awaiting cheque" % len(waiting)) if waiting else "—",
            ("%d cheque(s) not assigned" % len(unassigned)) if unassigned else "—"))
    body = (_nav(True, "vendors") + _flash(request.args) +
            "<div class='card'><table class='grid'><thead><tr><th>Vendor</th><th class=r>Balance</th><th>Credit patients</th><th>Cheques</th></tr></thead>"
            "<tbody>%s</tbody></table></div>"
            "<form method='post' action='%s/vendors' class='card'><h2>Add a vendor</h2><div class='row'><input name=name class='note' placeholder='vendor name'>"
            "<button class='save'>Add</button></div></form>") % ("".join(rows) or "<tr><td colspan=4 class=mut>No vendors yet.</td></tr>", BASE)
    return _shell("Implant vendors", "<h1>Implant vendors</h1>" + body)


@bp.route(BASE + "/vendors", methods=["POST"])
def post_vendor():
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    name = _txt(request.form.get("name"), 80)
    if not name:
        return _back(BASE + "/vendors", err="vendor")
    r = con.execute("SELECT id, hidden FROM surg_vendor WHERE name=?", (name,)).fetchone()
    if r and r["hidden"]:                        # S581: a vendor taken off the lists comes back when added again
        con.execute("UPDATE surg_vendor SET hidden='' WHERE id=?", (r["id"],))
        con.commit()
        _audit_safe(con, "surg_vendor", r["id"], "unhide", None, dict(name=name), who)
        return _back(BASE + "/vendors", msg="vendor")
    if r:
        return _back(BASE + "/vendors", err="dupvendor")
    cur = con.execute("INSERT INTO surg_vendor (name, created_by, created_at) VALUES (?,?,?)", (name, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_vendor", cur.lastrowid, "insert", None, dict(name=name), who)
    return _back(BASE + "/vendors", msg="vendor")


@bp.route(BASE + "/vendor/<int:vid>")
def vendor_page(vid):
    u, err = _owner()
    if err:
        return err
    con = _db()
    v = con.execute("SELECT * FROM surg_vendor WHERE id=?", (vid,)).fetchone()
    if not v:
        return _back(BASE + "/vendors", err="gone")
    rows, bal, waiting, unassigned = vendor_ledger(con, vid)
    run, trs = 0, []
    for day, text, dr, cr in rows:
        run += dr - cr
        trs.append("<tr><td class=d>%s</td><td>%s</td><td class=r>%s</td><td class=r>%s</td><td class=r>%s</td></tr>" % (
            _human(day), _esc(text), _r(dr) if dr else "", _r(cr) if cr else "", _r(run)))
    verdict = ("Dr Manoj owes %s %s" % (_esc(v["name"]), _r(bal))) if bal > 0 else (
        ("%s owes Dr Manoj %s" % (_esc(v["name"]), _r(-bal))) if bal < 0 else "Settled")
    wait = "".join("<li><a href='%s/case/%d'>%s · %s</a> — %s, surgery %s, actually due %s</li>" % (
        BASE, w["id"], w["case_no"], _esc(w["patient"]), pword(w), _human(w["surgery_date"]), _r(vendor_payable(con, vid, w["id"])))
        for w in waiting) or "<li class=mut>None.</li>"
    una = "".join("<li><a href='%s/cheque/%d'>Cheque %s · %s · %s</a> — %s not yet assigned to patients</li>" % (
        BASE, q["id"], _esc(q["cheque_no"]) or "—", _human(q["day"]), _esc(q["from_whom"]), _r(left)) for q, left in unassigned) or "<li class=mut>None.</li>"
    today = _today().isoformat()
    pays = con.execute("SELECT * FROM surg_vendor_pay WHERE vendor_id=? AND voided_at='' ORDER BY day DESC LIMIT 30", (vid,)).fetchall()
    chqs = con.execute("SELECT * FROM surg_cheque WHERE vendor_id=? AND voided_at='' ORDER BY day DESC LIMIT 30", (vid,)).fetchall()
    forms = ("<div class='card noprint'><h2>Write an entry</h2>"
             "<details><summary>Dr Manoj paid this vendor</summary><form method='post' action='%s/vendor/%d/pay'>"
             "<label>Date<input type=date name=day class='note' value='%s'></label><label>Amount (₹)<input name=amount class='amt' inputmode=decimal></label>"
             "<label>How</label><div class='chips'><label class='chip'><input type=radio name=mode value=cash checked> Cash</label>"
             "<label class='chip'><input type=radio name=mode value=bank> Bank</label><label class='chip'><input type=radio name=mode value=cheque> Cheque</label></div>"
             "<label>Note<input name=note class='note'></label><button class='save'>Write it</button></form></details>"
             "<details><summary>The vendor received a cheque for credit patients</summary><form method='post' action='%s/vendor/%d/cheque'>"
             "<label>Date<input type=date name=day class='note' value='%s'></label><label>Amount (₹)<input name=amount class='amt' inputmode=decimal></label>"
             "<label>Cheque number<input name=cheque_no class='note'></label><label>From (hospital / insurer / scheme)<input name=from_whom class='note' value='%s'></label>"
             "<label>Note<input name=note class='note'></label><button class='save'>Write it, then choose its patients</button></form></details>%s</div>") % (
        BASE, vid, today, BASE, vid, today, _esc(DEFAULT_HOSPITAL), _void_money(vid, pays, chqs))
    body = (_nav(True, "vendors") + _flash(request.args) +
            "<div class='card'><h2>%s — implant ledger</h2><p class='big'>%s</p><p class='mut noprint'>Only you can see this page. "
            "To share it with the vendor, <a href='#' onclick='window.print();return false'>print it or save it as a PDF</a>.</p>"
            "<table class='grid'><thead><tr><th>Date</th><th>Entry</th><th class=r>Owed to vendor</th><th class=r>In Dr Manoj's favour</th><th class=r>Running</th></tr></thead>"
            "<tbody>%s</tbody></table><p class=mut>Running balance: above zero, Dr Manoj owes the vendor; below zero, the vendor owes Dr Manoj.</p></div>"
            "<div class='card'><h2>Credit patients still awaiting the vendor's cheque</h2><ul>%s</ul></div>"
            "<div class='card'><h2>Cheques not yet assigned to patients</h2><ul>%s</ul></div>%s%s") % (
        _esc(v["name"]), verdict, "".join(trs) or "<tr><td colspan=5 class=mut>No entries yet.</td></tr>", wait, una, forms,
        _hide_form(con, vid))
    return _shell("%s ledger" % v["name"], body)


def vendor_live(con, vid):
    """S581: how many live entries a vendor has (implant lines on live cases, payments, cheques)."""
    a = con.execute("SELECT COUNT(*) FROM surg_implant i JOIN surg_case c ON c.id=i.case_id WHERE i.vendor_id=? AND i.voided_at='' "
                    "AND c.voided_at=''", (vid,)).fetchone()[0]
    b = con.execute("SELECT COUNT(*) FROM surg_vendor_pay WHERE vendor_id=? AND voided_at=''", (vid,)).fetchone()[0]
    q = con.execute("SELECT COUNT(*) FROM surg_cheque WHERE vendor_id=? AND voided_at=''", (vid,)).fetchone()[0]
    return a + b + q


def _hide_form(con, vid):
    if vendor_live(con, vid):
        return ""
    return ("<details class='card vd noprint'><summary>Remove this vendor from the lists (it has no entries)</summary>"
            "<form method='post' action='%s/vendor/%d/hide' class='row'><button class='clear'>Remove from the lists</button></form>"
            "<p class=mut>Kept in the record; writing the same name again brings it back.</p></details>" % (BASE, vid))


@bp.route(BASE + "/vendor/<int:vid>/hide", methods=["POST"])
def post_vendor_hide(vid):
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    v = con.execute("SELECT * FROM surg_vendor WHERE id=?", (vid,)).fetchone()
    if not v or vendor_live(con, vid):
        return _back("%s/vendor/%d" % (BASE, vid), err="gone")
    con.execute("UPDATE surg_vendor SET hidden=? WHERE id=?", (_stamp(), vid))
    con.commit()
    _audit_safe(con, "surg_vendor", vid, "hide", dict(name=v["name"]), dict(hidden=True), who)
    return _back(BASE + "/vendors", msg="hidden")


def _void_money(vid, pays, chqs):
    opts = ["<option value='pay:%d'>Payment %s · %s</option>" % (p["id"], _human(p["day"]), _r(p["amount_p"])) for p in pays]
    opts += ["<option value='cheque:%d'>Cheque %s · %s · %s</option>" % (q["id"], _esc(q["cheque_no"]) or "—", _human(q["day"]), _r(q["amount_p"])) for q in chqs]
    if not opts:
        return ""
    return ("<details class='vd'><summary>Remove a wrong payment or cheque</summary><form method='post' action='%s/vendor/%d/void' class='row'>"
            "<select name=what class='note'><option value=''>— choose —</option>%s</select>%s<button class='clear'>Remove</button></form></details>") % (BASE, vid, "".join(opts), _why_select())


@bp.route(BASE + "/vendor/<int:vid>/void", methods=["POST"])
def post_vendor_void(vid):
    u, err = _owner()
    if err:
        return err
    kind, _s, rid = (request.form.get("what") or "").partition(":")
    if kind not in ("pay", "cheque"):
        return _back("%s/vendor/%d" % (BASE, vid), err="gone")
    con, who = _db(), u.get("user", "")
    table = "surg_vendor_pay" if kind == "pay" else "surg_cheque"
    why = request.form.get("why")
    if why not in dict(VOID_WHY):
        return _back("%s/vendor/%d" % (BASE, vid), err="why")
    r = con.execute("SELECT * FROM %s WHERE id=? AND vendor_id=? AND voided_at=''" % table, (int(rid) if rid.isdigit() else -1, vid)).fetchone()
    if not r:
        return _back("%s/vendor/%d" % (BASE, vid), err="gone")
    con.execute("UPDATE %s SET voided_at=?, voided_by=?, void_why=? WHERE id=?" % table, (_stamp(), who, why, r["id"]))
    con.commit()
    _audit_safe(con, table, r["id"], "void", dict(amount_p=r["amount_p"], day=r["day"]), dict(why=why), who)
    return _back("%s/vendor/%d" % (BASE, vid), msg="voided")


def _money_form(f):
    day = (f.get("day") or "").strip()
    if not _iso_ok(day) or day > _today().isoformat():
        return None, None, "date"
    amt = _paise(f.get("amount"))
    if amt is False or not amt:
        return None, None, "amount"
    return day, amt, None


@bp.route(BASE + "/vendor/<int:vid>/pay", methods=["POST"])
def post_pay(vid):
    u, err = _owner()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = "%s/vendor/%d" % (BASE, vid)
    if not con.execute("SELECT 1 FROM surg_vendor WHERE id=?", (vid,)).fetchone():
        return _back(BASE + "/vendors", err="gone")
    day, amt, e = _money_form(f)
    if e:
        return _back(back, err=e)
    mode = f.get("mode") if f.get("mode") in ("cash", "bank", "cheque") else "cash"
    cur = con.execute("INSERT INTO surg_vendor_pay (vendor_id, day, amount_p, mode, note, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                      (vid, day, amt, mode, _txt(f.get("note"), 200), who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_vendor_pay", cur.lastrowid, "insert", None, dict(vendor_id=vid, day=day, amount_p=amt, mode=mode), who)
    return _back(back, msg="paid")


@bp.route(BASE + "/vendor/<int:vid>/cheque", methods=["POST"])
def post_cheque(vid):
    u, err = _owner()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = "%s/vendor/%d" % (BASE, vid)
    if not con.execute("SELECT 1 FROM surg_vendor WHERE id=?", (vid,)).fetchone():
        return _back(BASE + "/vendors", err="gone")
    day, amt, e = _money_form(f)
    if e:
        return _back(back, err=e)
    cur = con.execute("INSERT INTO surg_cheque (vendor_id, day, amount_p, cheque_no, from_whom, note, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                      (vid, day, amt, _txt(f.get("cheque_no"), 40), _txt(f.get("from_whom"), 80), _txt(f.get("note"), 200), who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_cheque", cur.lastrowid, "insert", None, dict(vendor_id=vid, day=day, amount_p=amt), who)
    return _back("%s/cheque/%d" % (BASE, cur.lastrowid), msg="cheque")


def _alloc_table(rows, name_prefix):
    return "".join(
        "<tr><td><a href='%s/case/%d'>%s</a></td><td>%s</td><td>%s</td><td class=d>%s</td><td class=r>%s</td>"
        "<td><input name='%s%d' class='amt' inputmode=decimal value='%s'></td></tr>" % (
            BASE, r["id"], r["case_no"], _esc(r["patient"]), pword(r), _human(r["surgery_date"]),
            _r(r["hint_p"]) if r["hint_p"] is not None else "—", name_prefix, r["id"],
            ("%.2f" % (r["now_p"] / 100.0)).rstrip("0").rstrip(".") if r["now_p"] else "") for r in rows)


def _read_alloc(f, prefix, allowed):
    out = {}
    for k, v in f.items():
        if k.startswith(prefix) and k[len(prefix):].isdigit():
            cid = int(k[len(prefix):])
            p = _paise(v, allow_blank=True)
            if p is False:
                return None
            if p and cid in allowed:
                out[cid] = p
    return out


@bp.route(BASE + "/cheque/<int:qid>")
def cheque_page(qid):
    u, err = _owner()
    if err:
        return err
    con = _db()
    q = con.execute("SELECT q.*, v.name AS vendor FROM surg_cheque q JOIN surg_vendor v ON v.id=q.vendor_id WHERE q.id=? AND q.voided_at=''", (qid,)).fetchone()
    if not q:
        return _back(BASE + "/vendors", err="gone")
    now = {r["case_id"]: r["amount_p"] for r in con.execute("SELECT case_id, amount_p FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))}
    rows = []
    for c in con.execute("SELECT DISTINCT c.* FROM surg_case c JOIN surg_implant i ON i.case_id=c.id WHERE i.vendor_id=? AND i.voided_at='' "
                         "AND c.voided_at='' AND c.payer<>'cash' ORDER BY c.surgery_date", (q["vendor_id"],)):
        bill = con.execute("SELECT COALESCE(SUM(bill_p),0) FROM surg_implant WHERE vendor_id=? AND case_id=? AND voided_at=''",
                           (q["vendor_id"], c["id"])).fetchone()[0]
        d = dict(c)
        d["hint_p"], d["now_p"] = bill, now.get(c["id"], 0)
        rows.append(d)
    used = sum(now.values())
    body = (_nav(True, "vendors") + _flash(request.args) +
            "<div class='card'><h2>Cheque %s · %s · %s</h2><p class='big'>%s from %s — assigned %s, left %s</p>"
            "<p class=mut>Write how much of this cheque was for each patient (the vendor's bill for that patient is shown). "
            "The cheque counts in your favour; what is actually due to the vendor for that patient counts against you.</p>"
            "<form method='post' action='%s/cheque/%d'><table class='grid'><thead><tr><th>Case</th><th>Patient</th><th>Payer</th><th>Surgery</th>"
            "<th class=r>Vendor's bill</th><th>From this cheque (₹)</th></tr></thead><tbody>%s</tbody></table>"
            "<button class='save'>Save</button></form><a class='btn' href='%s/vendor/%d'>← %s ledger</a></div>") % (
        _esc(q["cheque_no"]) or "—", _human(q["day"]), _esc(q["vendor"]), _r(q["amount_p"]), _esc(q["from_whom"]) or "—", _r(used),
        _r(q["amount_p"] - used), BASE, qid, _alloc_table(rows, "c") or "<tr><td colspan=6 class=mut>No credit patients with this vendor's implants yet.</td></tr>",
        BASE, q["vendor_id"], _esc(q["vendor"]))
    return _shell("Cheque", body)


@bp.route(BASE + "/cheque/<int:qid>", methods=["POST"])
def post_cheque_alloc(qid):
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    q = con.execute("SELECT * FROM surg_cheque WHERE id=? AND voided_at=''", (qid,)).fetchone()
    if not q:
        return _back(BASE + "/vendors", err="gone")
    allowed = {r[0] for r in con.execute("SELECT DISTINCT c.id FROM surg_case c JOIN surg_implant i ON i.case_id=c.id WHERE i.vendor_id=? "
                                         "AND i.voided_at='' AND c.voided_at='' AND c.payer<>'cash'", (q["vendor_id"],))}
    al = _read_alloc(request.form, "c", allowed)
    back = "%s/cheque/%d" % (BASE, qid)
    if al is None:
        return _back(back, err="amount")
    if sum(al.values()) > q["amount_p"]:
        return _back(back, err="over")
    before = {r["case_id"]: r["amount_p"] for r in con.execute("SELECT case_id, amount_p FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))}
    con.execute("DELETE FROM surg_cheque_alloc WHERE cheque_id=?", (qid,))
    for cid, p in al.items():
        con.execute("INSERT INTO surg_cheque_alloc (cheque_id, case_id, amount_p, by_whom, at) VALUES (?,?,?,?,?)", (qid, cid, p, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_cheque_alloc", qid, "assign", before, al, who)
    return _back(back, msg="alloc")


# ---------------------------------------------------------------- the hospital's payments (the owner only)
@bp.route(BASE + "/receipts")
def receipts_page():
    u, err = _owner()
    if err:
        return err
    con = _db()
    rows = []
    for r in con.execute("SELECT * FROM surg_receipt WHERE voided_at='' ORDER BY day DESC, id DESC LIMIT 200"):
        used = receipt_used(con, r["id"])
        rows.append("<tr><td class=d><a href='%s/receipt/%d'>%s</a></td><td>%s%s</td><td class=r>%s</td><td class=r>%s</td><td>%s</td><td>%s</td></tr>" % (
            BASE, r["id"], _human(r["day"]), _esc(r["from_whom"]), (" · " + _esc(r["period"])) if r["period"] else "", _r(r["amount_p"]),
            _r(r["amount_p"] - used) if used != r["amount_p"] else "<span class='good'>✓ all assigned</span>",
            "<span class='good'>✓</span>" if papers(con, rid=r["id"]) else "<span class='warn'>no statement</span>",
            "<span class='good'>✓ bank</span>" if r["bank_line_id"] else "—"))
    body = (_nav(True, "receipts") + _flash(request.args) +
            "<div class='card'><p class=mut>Each hospital payment is one statement. Write the payment, scan its statement, then write the amount paid against each patient.</p>"
            "<table class='grid'><thead><tr><th>Date</th><th>From</th><th class=r>Amount</th><th class=r>Not yet against a patient</th><th>Statement</th><th>Bank</th></tr></thead>"
            "<tbody>%s</tbody></table></div>"
            "<form method='post' action='%s/receipts' class='card'><h2>Write a hospital payment</h2>"
            "<label>Date paid<input type=date name=day class='note' value='%s'></label><label>Amount (₹)<input name=amount class='amt' inputmode=decimal></label>"
            "<label>From<input name=from_whom class='note' value='%s'></label><label>For the month / period<input name=period class='note' placeholder='e.g. September 2026'></label>"
            "<label>UTR / reference<input name=ref class='note'></label><button class='save'>Write it</button></form>") % (
        "".join(rows) or "<tr><td colspan=6 class=mut>None yet.</td></tr>", BASE, _today().isoformat(), _esc(DEFAULT_HOSPITAL))
    return _shell("Hospital payments", "<h1>Hospital payments</h1>" + body)


@bp.route(BASE + "/receipts", methods=["POST"])
def post_receipt():
    u, err = _owner()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    day, amt, e = _money_form(f)
    if e:
        return _back(BASE + "/receipts", err=e)
    cur = con.execute("INSERT INTO surg_receipt (day, amount_p, from_whom, period, ref, note, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                      (day, amt, _txt(f.get("from_whom"), 80) or DEFAULT_HOSPITAL, _txt(f.get("period"), 40), _txt(f.get("ref"), 60),
                       _txt(f.get("note"), 200), who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_receipt", cur.lastrowid, "insert", None, dict(day=day, amount_p=amt), who)
    return _back("%s/receipt/%d" % (BASE, cur.lastrowid), msg="receipt")


@bp.route(BASE + "/receipt/<int:rid>")
def receipt_page(rid):
    u, err = _owner()
    if err:
        return err
    con = _db()
    r = con.execute("SELECT * FROM surg_receipt WHERE id=? AND voided_at=''", (rid,)).fetchone()
    if not r:
        return _back(BASE + "/receipts", err="gone")
    a = request.args
    now = {x["case_id"]: x["amount_p"] for x in con.execute("SELECT case_id, amount_p FROM surg_receipt_alloc WHERE receipt_id=?", (rid,))}
    show_all = a.get("all") == "1"
    rows = []
    for c in con.execute("SELECT * FROM surg_case WHERE voided_at='' ORDER BY surgery_date, id"):
        got_other = received(con, c["id"]) - now.get(c["id"], 0)
        left = (c["due_p"] - got_other) if c["due_p"] is not None else None
        # a case already against this payment is ALWAYS on the form (the form is the whole truth when saved)
        if not show_all and c["id"] not in now and (c["hospital"] != r["from_whom"] or (left is not None and left <= 0)):
            continue
        d = dict(c)
        d["hint_p"] = (left - now.get(c["id"], 0)) if left is not None else None    # S581: still due AFTER this payment
        d["now_p"] = now.get(c["id"], 0)
        rows.append(d)
    used = sum(now.values())
    st = papers(con, rid=rid)
    stl = " ".join("<a href='%s/paper/%d' target=_blank>statement page %d</a>" % (BASE, p["id"], i + 1) for i, p in enumerate(st)) or "<span class='warn'>not scanned yet</span>"
    line = bank_line(con, r["bank_table"], r["bank_line_id"])
    if line:
        bank = "<p class='good'>Tied to the bank: %s · %s · %s · %s</p>" % (_human(line["txn_date"]), _tail(line["account_ref"]), _r(line["deposit_p"]), _esc((line["description"] or "")[:80]))
    else:
        cands = bank_candidates(con, r["amount_p"], r["day"])
        bank = ("<form method='post' action='%s/receipt/%d/bank'><p>Bank credits of exactly %s near this date:</p>%s<button class='save'>Tie it</button></form>" % (
            BASE, rid, _r(r["amount_p"]), "".join("<label class='pick'><input type=radio name=line value='%s:%d'> %s · %s · %s</label>" % (
                t, x["id"], _human(x["txn_date"]), _tail(x["account_ref"]), _esc((x["description"] or "")[:80])) for t, x in cands))
                if cands else "<p class=mut>No bank credit of exactly %s found yet (statements arrive when you drop them in Drive). "
                              "It can be tied later.</p>" % _r(r["amount_p"]))
    body = (_nav(True, "receipts") + _flash(a) +
            "<div class='card'><h2>%s · %s%s</h2><p class='big'>%s%s — against patients %s, left %s</p><p>%s · <a class='btn' href='%s/receipt/%d/scan'>Scan / upload the statement</a></p>%s</div>"
            "<form method='post' action='%s/receipt/%d' class='card'><h2>Amount paid against each patient (from the statement)</h2>"
            "<p class=mut>For each case: what is still due after the amounts in this statement. %s</p>"
            "<table class='grid'><thead><tr><th>Case</th><th>Patient</th><th>Payer</th><th>Surgery</th><th class=r>Still due after this</th><th>Paid in this statement (₹)</th></tr></thead>"
            "<tbody>%s</tbody></table><button class='save'>Save</button></form>"
            "<details class='card vd'><summary>Remove this payment (wrong entry)</summary><form method='post' action='%s/void' class='row'>"
            "<input type=hidden name=kind value=receipt><input type=hidden name=id value='%d'><input type=hidden name=back value='%s/receipts'>%s"
            "<button class='clear'>Remove</button></form></details>") % (
        _human(r["day"]), _esc(r["from_whom"]), (" · " + _esc(r["period"])) if r["period"] else "", _r(r["amount_p"]),
        (" · UTR / ref " + _esc(r["ref"])) if r["ref"] else "", _r(used),
        _r(r["amount_p"] - used), stl, BASE, rid, bank, BASE, rid,
        ("<a href='%s/receipt/%d'>Show only this hospital's open cases</a>" % (BASE, rid)) if show_all else
        ("<a href='%s/receipt/%d?all=1'>Show every case</a>" % (BASE, rid)),
        _alloc_table(rows, "a") or "<tr><td colspan=6 class=mut>No open cases for this hospital.</td></tr>", BASE, rid, BASE, _why_select())
    return _shell("Hospital payment", body)


@bp.route(BASE + "/receipt/<int:rid>", methods=["POST"])
def post_receipt_alloc(rid):
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    r = con.execute("SELECT * FROM surg_receipt WHERE id=? AND voided_at=''", (rid,)).fetchone()
    if not r:
        return _back(BASE + "/receipts", err="gone")
    allowed = {x[0] for x in con.execute("SELECT id FROM surg_case WHERE voided_at=''")}
    al = _read_alloc(request.form, "a", allowed)
    back = "%s/receipt/%d" % (BASE, rid)
    if al is None:
        return _back(back, err="amount")
    if sum(al.values()) > r["amount_p"]:
        return _back(back, err="over")
    before = {x["case_id"]: x["amount_p"] for x in con.execute("SELECT case_id, amount_p FROM surg_receipt_alloc WHERE receipt_id=?", (rid,))}
    # an untouched case that was assigned before keeps its amount only if it was on the form; the form always carries every
    # assigned case (they are listed), so the form is the whole truth for this receipt
    con.execute("DELETE FROM surg_receipt_alloc WHERE receipt_id=?", (rid,))
    for cid, p in al.items():
        con.execute("INSERT INTO surg_receipt_alloc (receipt_id, case_id, amount_p, by_whom, at) VALUES (?,?,?,?,?)", (rid, cid, p, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_receipt_alloc", rid, "assign", before, al, who)
    return _back(back, msg="alloc")


@bp.route(BASE + "/receipt/<int:rid>/bank", methods=["POST"])
def post_receipt_bank(rid):
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    r = con.execute("SELECT * FROM surg_receipt WHERE id=? AND voided_at=''", (rid,)).fetchone()
    back = "%s/receipt/%d" % (BASE, rid)
    if not r:
        return _back(BASE + "/receipts", err="gone")
    t, _s, lid = (request.form.get("line") or "").partition(":")
    ok = {(tt, x["id"]) for tt, x in bank_candidates(con, r["amount_p"], r["day"])}
    if not lid.isdigit() or (t, int(lid)) not in ok:
        return _back(back, err="line")
    con.execute("UPDATE surg_receipt SET bank_table=?, bank_line_id=? WHERE id=?", (t, int(lid), rid))
    con.commit()
    _audit_safe(con, "surg_receipt", rid, "bank_tie", None, dict(bank_table=t, bank_line_id=int(lid)), who)
    return _back(back, msg="bank")


@bp.route(BASE + "/receipt/<int:rid>/scan")
def receipt_scan_page(rid):
    u, err = _owner()
    if err:
        return err
    con = _db()
    r = con.execute("SELECT * FROM surg_receipt WHERE id=? AND voided_at=''", (rid,)).fetchone()
    if not r:
        return _back(BASE + "/receipts", err="gone")
    return _scan_host("Hospital statement — %s %s" % (_human(r["day"]), r["from_whom"]), "%s/api/receipt/%d/statement" % (BASE, rid),
                      {"receipt_id": str(rid)}, "hospital_statement_%s" % r["day"], "%s/receipt/%d?msg=paper" % (BASE, rid))


@bp.route(BASE + "/api/receipt/<int:rid>/statement", methods=["POST"])
def api_receipt_statement(rid):
    from flask import jsonify                    # noqa: PLC0415
    u, err = _owner()
    if err:
        return jsonify(ok=False, error="not_permitted"), 403
    con, who = _db(), u.get("user", "")
    r = con.execute("SELECT * FROM surg_receipt WHERE id=? AND voided_at=''", (rid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_receipt"), 404
    blob, e = _take_upload()
    if e:
        return jsonify(ok=False, error=e[0]), e[1]
    path, sha, mime = _store(blob, os.path.join(r["day"][:4], "hospital_statements"), "statement_%s_r%d" % (r["day"], rid))
    if not path:
        return jsonify(ok=False, error="not_pdf_or_image"), 415
    cur = con.execute("INSERT INTO surg_paper (receipt_id, kind, path, sha256, bytes, mime, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                      (rid, "hospital_statement", path, sha, len(blob), mime, who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_paper", cur.lastrowid, "upload", None, dict(receipt_id=rid, sha256=sha), who)
    return jsonify(ok=True, id=cur.lastrowid)


@bp.route(BASE + "/switch", methods=["POST"])
def post_switch():
    u, err = _owner()
    if err:
        return err
    con, who = _db(), u.get("user", "")
    v = "1" if request.form.get("on") == "1" else "0"
    con.execute("INSERT INTO setting (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (ON_KEY, v))
    con.commit()
    _audit_safe(con, "setting", 0, "update", None, {ON_KEY: v}, who)
    return _back(BASE, msg="switch")


# ---------------------------------------------------------------- backfill -- old cases from 1-Apr-2025 (S680; D804: the same compact form)
def _dup_case(con, clinic_id, patient, admit):
    """A live case of the same patient with the same admission date (clinic ID when given, else the name)."""
    if clinic_id:
        return con.execute("SELECT case_no FROM surg_case WHERE voided_at='' AND admit_date=? AND upper(clinic_id)=upper(?)",
                           (admit, clinic_id)).fetchone()
    return con.execute("SELECT case_no FROM surg_case WHERE voided_at='' AND admit_date=? AND upper(patient)=upper(?)",
                       (admit, patient)).fetchone()


@bp.route(BASE + "/backfill")
def backfill_page():
    u, checker, err = _gate()
    if err:
        return err
    return _backfill_view(u, checker, request.args)


def _backfill_view(u, checker, a):
    con = _db()
    n_old = con.execute("SELECT COUNT(*) FROM surg_case WHERE voided_at='' AND backfill=1").fetchone()[0]
    out = [_nav(checker, "backfill"), _flash(a)]
    if a.get("err") == "dup" and a.get("no"):
        out.append("<div class='bad'>Already entered as <b>%s</b> — not entered twice.</div>" % _esc(a.get("no")))
    if a.get("msg") == "backfill" and a.get("no"):
        rid = a.get("id") if (a.get("id") or "").isdigit() else ""
        out.append("<div class='ok'>Saved as <b>%s</b>.%s Enter the next old case below.</div>" % (
            _esc(a.get("no")), (" <a href='%s?show=old&open=%s#c%s'>Open it to add more</a>." % (BASE, rid, rid)) if rid else ""))
    out.append("<p class='sm'>Old cases from %s onward — <b>%d entered so far</b>. They sit in the same list as the new ones, marked "
               "<span class='chip c-grey'>old case</span>, and open the same way; nothing on them is compulsory but the name and the payer, "
               "and papers are not asked for.</p>" % (_human(BACKFILL_FROM), n_old))
    out.append(_patient_form(con, a, "backfill"))
    return _shell("Backfill old IPD cases", "<h1>Backfill old IPD cases</h1>" + "".join(out))


@bp.route(BASE + "/backfill", methods=["POST"])
def post_backfill():
    u, checker, err = _gate()
    if err:
        return err
    if request.form.get("find"):                 # the Find box (posted)
        return _backfill_view(u, checker, request.form)
    con, f, who = _db(), request.form, u.get("user", "")
    back = BASE + "/backfill"
    patient = _txt(f.get("patient"), 80)
    keep = dict(cid=f.get("clinic_id"), name=patient, uid=f.get("uid"))
    if not patient:
        return _back(back, err="patient", cid=f.get("clinic_id"))
    if "payer" not in f:
        return _back(back, err="payer", **keep)
    new, bad = _case_fields(f, back, keep)
    if bad:
        return bad
    today = _today().isoformat()
    ds = [new.get(k, "") for k in ("admit_date", "surgery_date", "discharge_date")]
    if any(d and d < BACKFILL_FROM for d in ds):
        return _back(back, err="early", **keep)
    if any(d and d > today for d in ds) or (ds[0] and ds[2] and ds[2] < ds[0]):
        return _back(back, err="date", **keep)
    ist = f.get("implant_status") or ""
    mst = f.get("money_status") or ""
    if (ist and ist not in IMPLANT_WORD) or (mst and mst not in dict(MONEY)):
        return _back(back, err="status", **keep)
    item = _txt(f.get("item"), 160)
    bill = _paise(f.get("bill"), allow_blank=True)
    if bill is False:
        return _back(back, err="amount", **keep)
    has_vendor = bool(_txt(f.get("vendor_new"), 80) or (f.get("vendor_id") or "").isdigit())
    if (has_vendor or bill) and not item:
        return _back(back, err="item", **keep)
    if item and not has_vendor:
        return _back(back, err="vendor", **keep)
    if ds[0]:
        dup = _dup_case(con, new.get("clinic_id", ""), patient, ds[0])
        if dup:
            return _back(back, err="dup", no=dup["case_no"])
    # every check has passed: now the writes (the source, the TPA name, the vendor, the case, its implant) -- one commit
    sid = source_id(con, _source_of(f), who, unhide=checker) if _source_of(f) else None
    if new.get("insurer"):
        new["insurer"] = tpa_keep(con, new["insurer"], who, unhide=checker)
    vid = _vendor_of(con, f, who) if item else None
    if item and not vid:
        con.rollback()
        return _back(back, err="vendor", **keep)
    no, rid = _insert_case(con, f, who, dict(new, patient=patient, hospital=_txt(f.get("hospital"), 80) or DEFAULT_HOSPITAL),
                           dict(stage="discharged", source_id=sid, backfill=1, implant_status=ist, money_status=mst))
    if not no:
        con.rollback()
        return _back(back, err="gone")
    if item:
        credit = new["payer"] in CREDIT
        con.execute("INSERT INTO surg_implant (case_id, vendor_id, item, qty, bill_p, bill_to, by_whom, at) VALUES (?,?,?,?,?,?,?,?)",
                    (rid, vid, item, 1, bill or 0, "patient" if credit else "doctor", who, _stamp()))
    con.commit()
    _audit_safe(con, "surg_case", rid, "backfill", None,
                dict(case_no=no, payer=new["payer_kind"], patient=patient, admit_date=ds[0], implant=item, implant_status=ist,
                     money_status=mst), who)
    return _back(back, msg="backfill", no=no, id=rid)


# ---------------------------------------------------------------- Settings (the owner only, D801 (1) and (5); D804: the TPA names)
def _rupees_in(p):
    return ("%.2f" % (p / 100.0)).rstrip("0").rstrip(".")


@bp.route(BASE + "/settings")
def settings_page():
    u, err = _owner()
    if err:
        return err
    con = _db()
    adm, nur, share = ipd_settings(con)
    scount = {r[0]: r[1] for r in con.execute("SELECT source_id, COUNT(*) FROM surg_case WHERE voided_at='' GROUP BY source_id")}
    tcount = {(r[0] or "").upper(): r[1] for r in con.execute("SELECT insurer, COUNT(*) FROM surg_case WHERE voided_at='' GROUP BY upper(insurer)")}
    srows = "".join(
        "<tr><td>%s%s</td><td class=r>%d</td><td><form method='post' action='%s/settings/source' class='inline'>"
        "<input type=hidden name=id value='%d'><input type=hidden name=do value='%s'><button class='clear'>%s</button></form></td></tr>" % (
            _esc(s["name"]), " <span class=mut>(off the list)</span>" if s["hidden"] else "", scount.get(s["id"], 0), BASE, s["id"],
            "show" if s["hidden"] else "hide", "Put back on the list" if s["hidden"] else "Take off the list")
        for s in sources(con, all_=True))
    trows = "".join(
        "<tr><td>%s%s</td><td class=r>%d</td><td><form method='post' action='%s/settings/tpa' class='inline'>"
        "<input type=hidden name=id value='%d'><input type=hidden name=do value='%s'><button class='clear'>%s</button></form></td></tr>" % (
            _esc(t["name"]), " <span class=mut>(off the list)</span>" if t["hidden"] else "", tcount.get(t["name"].upper(), 0), BASE, t["id"],
            "show" if t["hidden"] else "hide", "Put back on the list" if t["hidden"] else "Take off the list")
        for t in tpas(con, all_=True))
    body = (_nav(True, "settings") + _flash(request.args) +
            "<form method='post' action='%s/settings' class='card'><h2>The hospital's charges and your share</h2>"
            "<p class=mut>On a cash bill the hospital keeps the admission charge and nursing for each day; on a cash package only the "
            "admission charge. Your share is a fixed percentage of the rest. These figures are used by the money steps of each case "
            "(nursing is filled in on a case as the days × this figure, and can be changed there).</p>"
            "<div class='row2'><label class='f'>Admission charge (₹)<input name=admission class='in s amt' inputmode=decimal value='%s'></label>"
            "<label class='f'>Nursing, per day (₹)<input name=nursing class='in s amt' inputmode=decimal value='%s'></label>"
            "<label class='f'>Your share of the rest (%%) <span class=mut>— blank until you decide it</span>"
            "<input name=share class='in s amt' inputmode=decimal value='%s' placeholder='not set yet'></label>"
            "<button class='btn'>Save</button></div></form>"
            "<div class='card'><h2>Sources — where patients come from</h2>"
            "<p class=mut>A new name typed on a case joins this list by itself. Taking one off the list keeps its cases as they are.</p>"
            "<table class='grid narrow'><thead><tr><th>Source</th><th class=r>Cases</th><th></th></tr></thead><tbody>%s</tbody></table>"
            "<form method='post' action='%s/settings/source' class='row2' style='margin-top:10px'><input type=hidden name=do value=add>"
            "<input name=name class='in m' placeholder='a new source'><button class='btn'>Add</button></form></div>"
            "<div class='card'><h2>TPA and scheme names</h2>"
            "<p class=mut>The drop-down on every case. A name written on a case with “+ add a name” joins it by itself.</p>"
            "<table class='grid narrow'><thead><tr><th>TPA / scheme</th><th class=r>Cases</th><th></th></tr></thead><tbody>%s</tbody></table>"
            "<form method='post' action='%s/settings/tpa' class='row2' style='margin-top:10px'><input type=hidden name=do value=add>"
            "<input name=name class='in m' placeholder='a TPA or scheme name'><button class='btn'>Add</button></form></div>"
            "<div class='card'><h2>Implant vendors</h2><p><a class='btn sec2' href='%s/vendors'>The vendors' list and ledgers</a></p></div>") % (
        BASE, _rupees_in(adm), _rupees_in(nur), ("%g" % share) if share is not None else "",
        srows or "<tr><td colspan=3 class=mut>No sources yet.</td></tr>", BASE,
        trows or "<tr><td colspan=3 class=mut>No names yet — add the first one here or from a case.</td></tr>", BASE, BASE)
    return _shell("IPD cases — settings", "<h1>IPD cases — settings</h1>" + body)


@bp.route(BASE + "/settings", methods=["POST"])
def post_settings():
    u, err = _owner()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back = BASE + "/settings"
    adm, nur = _paise(f.get("admission")), _paise(f.get("nursing"))
    if adm is False or nur is False:
        return _back(back, err="amount")
    sh = str(f.get("share") or "").replace("%", "").strip()
    if sh:
        if not re.fullmatch(r"\d{1,3}(\.\d{1,2})?", sh) or float(sh) > 100:
            return _back(back, err="share")
        sh = "%g" % float(sh)
    before = dict(zip((SET_ADMISSION, SET_NURSING, SET_SHARE), ipd_settings(con)))
    for k, v in ((SET_ADMISSION, str(adm)), (SET_NURSING, str(nur)), (SET_SHARE, sh)):
        con.execute("INSERT INTO setting (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (k, v))
    con.commit()
    _audit_safe(con, "setting", 0, "update", before, {SET_ADMISSION: adm, SET_NURSING: nur, SET_SHARE: sh}, who)
    return _back(back, msg="settings")


def _list_post(table, msg, add_fn):
    u, err = _owner()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    back, do = BASE + "/settings", f.get("do")
    if do == "add":
        if not add_fn(con, f.get("name"), who):
            con.rollback()
            return _back(back, err="source" if table == "surg_source" else "gone")
        con.commit()
        _audit_safe(con, table, 0, "insert", None, dict(name=_txt(f.get("name"), 80)), who)
        return _back(back, msg=msg)
    if do in ("hide", "show") and (f.get("id") or "").isdigit():
        r = con.execute("SELECT * FROM %s WHERE id=?" % table, (int(f["id"]),)).fetchone()
        if r:
            con.execute("UPDATE %s SET hidden=? WHERE id=?" % table, (_stamp() if do == "hide" else "", r["id"]))
            con.commit()
            _audit_safe(con, table, r["id"], do, dict(name=r["name"], hidden=r["hidden"]), dict(hidden=do == "hide"), who)
            return _back(back, msg=msg)
    return _back(back, err="gone")


@bp.route(BASE + "/settings/source", methods=["POST"])
def post_settings_source():
    return _list_post("surg_source", "source", source_id)


@bp.route(BASE + "/settings/tpa", methods=["POST"])
def post_settings_tpa():
    return _list_post("surg_tpa", "tpa", tpa_keep)


# ---------------------------------------------------------------- the look
def _shell(title, body):
    """The owner's pages' plain look, in English; the IPD pages in the mock-up's compact look (D804, boards 7-12)."""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#46525b;--line:#9fb0bb;--soft:#d5dde2;--accent:#14456e;--paper:#fff;--bg:#e4eaee;--entry:#fffbe6}
*{box-sizing:border-box}
body{margin:0;padding:12px 14px;background:var(--bg);color:var(--ink);font:15px/1.5 "Segoe UI",system-ui,-apple-system,sans-serif}
a{color:var(--accent)}
h1{font-size:21px;margin:0 0 10px;color:var(--accent)}h2{font-size:18px;margin:0 0 10px;color:var(--accent)}h3{font-size:15px;margin:10px 0 6px;color:var(--accent)}
.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:12px 14px;margin:0 0 12px;overflow-x:auto}
details summary{cursor:pointer;color:var(--accent);font-weight:600;padding:4px 0}
label{display:block;margin:8px 0 2px;font-weight:600}
.mut,.sm{color:var(--mut);font-size:13px}.big{font-size:17px;font-weight:600}
table.grid{width:100%%;border-collapse:collapse;font-size:14px;margin:6px 0}
.grid th,.grid td{border-bottom:1px solid var(--soft);padding:7px 8px;vertical-align:top;text-align:left}.grid thead th{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mut);border-bottom:2px solid var(--line)}
.r{text-align:right!important;white-space:nowrap}.d{white-space:nowrap}tfoot td{background:#dff0d8;font-weight:700}
input.amt{text-align:right}
.note{width:100%%;min-height:40px;padding:6px 9px;border:2px solid var(--line);border-radius:8px;font-size:15px;background:var(--entry)}
select.note{background:#fff}.grid input.amt{min-height:36px}
.row{display:flex;gap:8px;align-items:center;margin:0 0 10px;flex-wrap:wrap}.row .note{flex:1}
button.save,.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;min-height:40px;padding:0 14px;border-radius:8px;border:2px solid var(--accent);background:var(--accent);color:#fff;font:inherit;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none;white-space:nowrap}
.btn.sec2,a.btn{background:#fff;color:var(--accent)}.btn.sm2{min-height:32px;padding:0 10px;font-size:13px}
button.clear{background:#fff;color:#8c2f2f;border:2px solid #8c2f2f;border-radius:8px;min-height:36px;padding:0 12px;font-size:14px;cursor:pointer}
.tabs{display:flex;gap:6px;margin:0 0 10px;flex-wrap:wrap}
a.tab{text-align:center;border:2px solid var(--accent);border-radius:9px;padding:7px 12px;font-weight:600;font-size:14px;color:var(--accent);background:#fff;text-decoration:none;white-space:nowrap}
a.tab.on{background:var(--accent);color:#fff}
.chips{display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.chip{display:inline-block;font-size:12px;font-weight:600;border-radius:12px;padding:2px 9px;white-space:nowrap;line-height:18px;margin:1px 0}
.c-blue{background:#dbe7f3;color:#14456e}.c-ok{background:#dff0d8;color:#2c6e2f}.c-warn{background:#fdf0d5;color:#8a5a00}.c-bad{background:#fadbd8;color:#9c2a20}.c-grey{background:#eef2f4;color:#46525b}
.chips label.chip{border:2px solid var(--line);border-radius:8px;padding:6px 10px;font-size:14px;background:#fff;font-weight:500}
label.radio{display:inline-flex;align-items:center;gap:6px;border:2px solid var(--line);border-radius:8px;padding:5px 10px;font-size:14px;font-weight:500;background:#fff;min-height:38px;margin:0;color:var(--ink);cursor:pointer}
label.radio:has(input:checked){border-color:var(--accent);background:#dbe7f3;font-weight:600}
label.radio input{margin:0}
a.pick,label.pick{display:block;border:1px solid var(--line);border-radius:8px;padding:8px 10px;margin:5px 0;color:var(--ink);background:#fff;text-decoration:none;font-weight:400}
.ok{background:#dff0d8;border-left:6px solid #2c6e2f;padding:8px 12px;margin-bottom:10px}
.bad{background:#fbe4e2;border-left:6px solid #8c2f2f;padding:8px 12px;margin-bottom:10px}
.good{color:#1d6b2f;font-weight:600}.warn{color:#8a5a00;font-weight:600}
.inline{display:inline}.vd summary{font-size:13px;color:#8c2f2f;font-weight:400}
.you{background:#ece6f7;color:#4a2f7c;border-radius:10px;padding:1px 7px;font-size:12px;font-weight:600}
.sec{background:#fff;border:1px solid var(--line);border-radius:12px;margin:0 0 10px}
.sh{display:flex;align-items:center;gap:10px;padding:9px 14px;border-bottom:1px solid var(--soft);font-weight:700;font-size:15px;color:var(--accent);flex-wrap:wrap}
details.stg:not([open]) > .sh{border-bottom:0}
.sb{padding:10px 14px}
.fold{color:var(--mut);font-weight:400;font-size:13px;margin-left:auto}
.in{min-height:40px;font:inherit;font-size:14px;padding:0 10px;border:2px solid var(--line);border-radius:8px;background:var(--entry);color:var(--ink);width:100%%}
select.in{background:#fff}.in.s{width:150px}.in.xs{width:90px}.in.m{width:220px}
label.f{display:flex;flex-direction:column;gap:3px;font-size:12px;color:var(--mut);font-weight:600;margin:0}
.row2{display:flex;gap:10px 14px;flex-wrap:wrap;align-items:flex-end;margin:0 0 10px}
.row2 .grow{flex:1 1 260px}.row2 .grow2{flex:2 1 280px}
.next{display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:#fdf0d5;border:1px solid #e3c98a;border-radius:12px;padding:9px 14px;margin:8px 0 10px}
.chd{font-size:16px;margin:2px 0 6px}
.clist{overflow:hidden}
.chead,details.crow > summary{display:grid;grid-template-columns:2.2fr 1fr 1.1fr 1.1fr 1.6fr 1.7fr 1.5fr;gap:10px;align-items:start;padding:9px 14px;list-style:none}
details.crow > summary::-webkit-details-marker{display:none}
.chead{font-size:12px;text-transform:uppercase;letter-spacing:.03em;color:var(--mut);font-weight:600;border-bottom:2px solid var(--line)}
details.crow{border-bottom:1px solid var(--soft)}details.crow > summary{color:var(--ink);font-weight:400;font-size:14px}
details.crow > summary b{color:var(--accent)}details.crow[open] > summary{background:#eef4fa}
.cbody{padding:4px 14px 12px;background:#f6f8fa}.cbody:empty{display:none}
.cn{color:#8a5a00;font-size:13px}
.filt .sb{padding:10px 14px}.filt .in.s{width:140px}
.nw{white-space:nowrap}table.grid.narrow{width:auto;min-width:440px}label.f{white-space:nowrap}
.qchips{display:none}.qchips .row2{margin:0 0 6px}a.qc{display:inline-flex;align-items:center;min-height:36px;padding:0 11px;border:2px solid var(--line);border-radius:18px;
background:#fff;color:var(--ink);text-decoration:none;font-size:13px;font-weight:600}a.qc.on{border-color:var(--accent);background:#dbe7f3;color:var(--accent)}
@media (max-width:760px){
 body{padding:10px}.chead{display:none}
 details.crow > summary{display:flex;flex-wrap:wrap;gap:4px 10px}
 details.crow > summary > span{flex:1 1 auto}.cp{flex-basis:100%%!important}.cx{display:none}.cn{flex-basis:100%%!important}
 .in.s,.in.m,.in.xs,.filt .in.s{width:100%%}label.f{flex:1 1 100%%}.row2 .grow,.row2 .grow2{flex-basis:100%%}
 .cbody{padding:4px 6px 10px}.sb{padding:10px}
 .qchips{display:block;margin:0 0 10px}form.filt{display:none}body.showfilt form.filt{display:block}label.f{white-space:normal}table.grid.narrow{min-width:0;width:100%%}
 table.ptab tr{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;padding:7px 0;border-bottom:1px solid var(--soft)}
 table.ptab td{border:0;padding:0}table.ptab td:first-child{flex:1 1 100%%;font-weight:600}table.ptab td:last-child{margin-left:auto}
}
@media print{.noprint,.tabs,.vd,form{display:none!important}body{background:#fff;padding:0}.card{border:0}}
</style></head><body>%s
<script>
function ipdSrc(i){var on=i.value.trim()!=='';i.form.querySelectorAll('input[name=source]').forEach(function(r){if(on){if(r.required)r.dataset.req=1;r.checked=false;r.required=false}else if(r.dataset.req){r.required=true}})}
function ipdTpa(s){var t=s.parentNode.querySelector('input[name=insurer_new]');if(!t)return;t.style.display=s.value==='+'?'':'none';if(s.value==='+')t.focus()}
</script></body></html>""" % (_esc(title), body)
