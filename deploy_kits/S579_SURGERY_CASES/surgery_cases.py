#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""surgery_cases.py -- kit S579_SURGERY_CASES (session S325, 18-Oct-2026, D735). One record per surgery.

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
  "the casepack patient selection should have option to continue to this flow"; "sort patients on basis of cash and credit,
   with credit categories"; papers also "xray images and scans etc, medicolegal papers, police memo and all".
  Shavez and he scan, or upload scans or photos. New surgeries from now.

  /finance/surgery                         the cases: cash / credit tabs (cashless, Ayushman, Deendayal), search, the open ones
  /finance/surgery/new                     a new case (from the Case Pack's "Continue" link, prefilled, or directly)
  /finance/surgery/case/<id>               one case: details, stage, its papers (scan / upload per kind), implants, money
  /finance/surgery/vendors, /vendor/<id>   the implant vendors' ledgers -- the owner only; printable to share with the vendor
  /finance/surgery/receipts, /receipt/<id> the hospital's payments (one monthly statement each): scan the statement, enter
                                           the amount paid against each patient, optionally tie it to the bank line
  Unit 'surgery': shavez maker (cases, papers, implant lines -- no money pages), the doctor checker (everything).
  Money rows are never edited: a correction is a void with its reason plus a new row. Every write goes through the app's
  audit helper. Tables on the first request, never at import (F-303). Papers are stored under the Case Pack's own folder,
  which the nightly encrypted backup already carries whole (S424).
"""
import datetime as dt
import hashlib
import json
import os
import re
from urllib.parse import quote

from flask import Blueprint, redirect, request, send_file

bp = Blueprint("surgery_cases", __name__)

APP_VERSION = "S579-SURGERY-1.0"
_db = None
_require = None
_audit = None
_unit = "surgery"

PAPER_DIR = os.environ.get("SURGERY_PAPER_DIR", "/root/wa/casepack/surgery_papers")
ON_KEY = "surgery_cases.on"
DEFAULT_HOSPITAL = "Dhanwantari Tomar Hospital"
MAX_P = 10000000000              # Rs 10 crore for one typed figure
MAX_FILE = 30 * 1024 * 1024
BASE = "/finance/surgery"

PAYERS = (("cash", "Cash"), ("cashless", "Cashless (insurance)"), ("ayushman", "Ayushman"), ("deendayal", "Deendayal"))
PAYER_WORD = dict(PAYERS)
CREDIT = ("cashless", "ayushman", "deendayal")
STAGES = (("planned", "Planned"), ("applied", "Pre-approval applied"), ("approved", "Pre-approved"), ("admitted", "Admitted"),
          ("operated", "Operated"), ("discharged", "Discharged"), ("billed", "Bill / claim sent"), ("closed", "Closed"))
STAGE_WORD = dict(STAGES)
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
    try:
        con.execute("INSERT OR IGNORE INTO business_unit (code, name, open_sunday, active) VALUES (?,?,1,1)", (_unit, "Surgery cases"))
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


def _r(p):
    if p is None:
        return "—"
    neg = p < 0
    s = "₹ {:,}".format(int(round(abs(p) / 100.0)))
    return ("− " + s) if neg else s


def _iso_ok(d):
    try:
        return dt.date(int(d[:4]), int(d[5:7]), int(d[8:10])).isoformat() == d
    except (ValueError, IndexError, TypeError):
        return False


def _human(iso):
    return dt.date.fromisoformat(iso).strftime("%d-%b-%Y") if _iso_ok(iso or "") else (iso or "—")


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
    q = "&".join("%s=%s" % (k, quote(str(v), safe="")) for k, v in kw.items() if v not in (None, ""))
    return redirect(path + ("?" + q if q else ""))


def _gate():
    """(user, is_checker, error_response). maker or checker of the unit; a maker only while the switch is on.
    The tables and the unit's two logins are made BEFORE the role check -- otherwise the first request is refused for want of them."""
    con = _db()
    _ensure(con)
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return None, False, (_shell("Surgery cases", "<div class='card'><h2>Not permitted</h2><p>This is the surgery cases page. "
                                    "Your login is not on it. Ask Dr Manoj if this is wrong.</p></div>"), 403)
    roles = set(u.get("roles") or [])
    checker = "checker" in roles
    if not checker and not is_on(con):
        return None, False, (_shell("Surgery cases", "<div class='card'><h2>Surgery cases</h2><p>This page is closed for now — "
                                    "Dr Manoj will open it.</p></div>"), 403)
    return u, checker, None


def _owner():
    u, checker, err = _gate()
    if err:
        return None, err
    if not checker:
        return None, (_shell("Surgery cases", "<div class='card'><h2>Dr Manoj only</h2><p>This page is for Dr Manoj.</p>"
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


def needed(payer):
    return NEEDED_CREDIT if payer in CREDIT else NEEDED_CASH


def missing_papers(con, c):
    have = {r["kind"] for r in papers(con, c["id"])}
    return [k for k in needed(c["payer"]) if k not in have]


def search_patients(con, q):
    """[(clinic_id, name, hint)] -- this register's own patients first, then the patient master (clinic_id, name; read only)."""
    q = (q or "").strip()
    if len(q) < 2:
        return []
    like = "%" + q.replace("%", "").replace("_", "") + "%"
    out, have = [], set()
    for r in con.execute("SELECT clinic_id, patient, MAX(case_no) AS n FROM surg_case WHERE voided_at='' AND (patient LIKE ? OR clinic_id LIKE ?) "
                         "GROUP BY clinic_id, patient ORDER BY n DESC LIMIT 10", (like, like)):
        out.append((r["clinic_id"], r["patient"], "has case %s" % r["n"]))
        have.add((r["clinic_id"] or "").upper())
    try:
        for r in con.execute("SELECT clinic_id, name FROM patient_ref WHERE merged_into IS NULL AND (clinic_id LIKE ? OR name LIKE ?) "
                             "ORDER BY id DESC LIMIT 20", (like, like)):
            if (r["clinic_id"] or "").upper() not in have:
                out.append((r["clinic_id"], r["name"] or "?", "patient master"))
    except Exception:                            # noqa: BLE001 -- no patient master here: the register's own only
        pass
    return out[:25]


def next_case_no(con):
    y = _today().year
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
    the doctor and the actual amount due to the vendor counts against him -- so the gap is in his favour (the owner, 11:32)."""
    rows = []
    for r in con.execute("SELECT i.*, c.case_no, c.patient, c.payer, c.surgery_date FROM surg_implant i JOIN surg_case c ON c.id=i.case_id "
                         "WHERE i.vendor_id=? AND i.voided_at='' AND c.voided_at='' AND c.payer='cash' ORDER BY c.surgery_date, i.id", (vid,)):
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
    waiting = con.execute("SELECT DISTINCT c.id, c.case_no, c.patient, c.payer, c.surgery_date FROM surg_implant i JOIN surg_case c ON c.id=i.case_id "
                          "WHERE i.vendor_id=? AND i.voided_at='' AND c.voided_at='' AND c.payer<>'cash' AND c.id NOT IN "
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
       "vendor": "✓ The vendor is added", "receipt": "✓ The hospital payment is written", "switch": "✓ Changed"}
ERR = {"patient": "Write the patient's name.", "payer": "Choose cash, cashless, Ayushman or Deendayal.", "date": "Write a correct date.",
       "amount": "Write the amount in rupees (digits only).", "item": "Write what the implant is.", "vendor": "Choose or write the vendor.",
       "why": "Choose why it is being removed.", "gone": "That entry was not found (perhaps already removed).",
       "over": "The amounts against the patients add up to more than the payment.", "stage": "Choose a stage.",
       "kind": "Unknown kind of paper.", "dupvendor": "That vendor is already in the list.", "line": "That bank line is not available.",
       "off": "This page is closed for now."}


def _flash(a):
    m, e = MSG.get(a.get("msg") or "", ""), ERR.get(a.get("err") or "", "")
    return ("<div class='ok'>%s</div>" % m if m else "") + ("<div class='bad'>%s</div>" % e if e else "")


def _nav(checker, here=""):
    links = [("cases", BASE, "Cases"), ("new", BASE + "/new", "+ New case")]
    if checker:
        links += [("vendors", BASE + "/vendors", "Implant vendors"), ("receipts", BASE + "/receipts", "Hospital payments")]
    return "<div class='tabs'>%s</div>" % "".join("<a class='tab%s' href='%s'>%s</a>" % (" on" if k == here else "", u, w)
                                                  for k, u, w in links)


TABS = (("all", "All"), ("cash", "Cash"), ("credit", "Credit — all"), ("cashless", "Cashless"), ("ayushman", "Ayushman"),
        ("deendayal", "Deendayal"))


@bp.route(BASE)
def list_page():
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    a = request.args
    tab = a.get("t") if a.get("t") in dict(TABS) else "all"
    show = a.get("show") if a.get("show") in ("open", "closed", "all") else "open"
    q = _txt(a.get("q"), 40)
    where, args = ["voided_at=''"], []
    if tab == "credit":
        where.append("payer IN ('cashless','ayushman','deendayal')")
    elif tab != "all":
        where.append("payer=?")
        args.append(tab)
    if show == "open":
        where.append("stage<>'closed'")
    elif show == "closed":
        where.append("stage='closed'")
    if q:
        where.append("(patient LIKE ? OR clinic_id LIKE ? OR case_no LIKE ?)")
        args += ["%" + q + "%"] * 3
    rows = con.execute("SELECT * FROM surg_case WHERE %s ORDER BY COALESCE(NULLIF(surgery_date,''), substr(created_at,1,10)) DESC, id DESC LIMIT 500"
                       % " AND ".join(where), args).fetchall()
    out = [_nav(checker, "cases"), _flash(a)]
    if checker and not is_on(con):
        out.append("<div class='bad'>Closed for Shavez. <form method='post' action='%s/switch' class='inline'><input type=hidden name=on value=1>"
                   "<button class='save'>Open it</button></form></div>" % BASE)
    out.append("<div class='tabs small'>%s</div>" % "".join(
        "<a class='tab%s' href='%s?t=%s&show=%s'>%s</a>" % (" on" if k == tab else "", BASE, k, show, w) for k, w in TABS))
    out.append("<form method='get' action='%s' class='row'><input type=hidden name=t value='%s'>"
               "<input name=q class='note' value='%s' placeholder='Name, clinic ID or case number'>"
               "<select name=show class='note' style='flex:0 0 auto'>%s</select><button class='save'>Show</button></form>" % (
                   BASE, tab, _esc(q), "".join("<option value='%s'%s>%s</option>" % (k, " selected" if k == show else "", w)
                                               for k, w in (("open", "Not closed"), ("closed", "Closed"), ("all", "All")))))
    head = "<tr><th>Case</th><th>Patient</th><th>Payer</th><th>Surgery</th><th>Stage</th><th>Papers</th>%s</tr>" % (
        "<th class=r>Due from hospital</th><th class=r>Received</th><th class=r>Balance</th>" if checker else "")
    body, tot = [], [0, 0]
    for c in rows:
        miss = missing_papers(con, c)
        papers_cell = "<span class='good'>✓ all</span>" if not miss else "<span class='warn'>%d missing</span>" % len(miss)
        money = ""
        if checker:
            got = received(con, c["id"])
            bal = (c["due_p"] - got) if c["due_p"] is not None else None
            if c["due_p"] is not None:
                tot[0] += c["due_p"]
                tot[1] += got
            money = "<td class=r>%s</td><td class=r>%s</td><td class=r>%s</td>" % (_r(c["due_p"]), _r(got) if got else "—",
                                                                                   _r(bal) if bal is not None else "—")
        body.append("<tr><td class=d><a href='%s/case/%d'>%s</a></td><td>%s%s</td><td>%s%s</td><td class=d>%s</td><td>%s</td><td>%s</td>%s</tr>" % (
            BASE, c["id"], c["case_no"], _esc(c["patient"]), (" <span class=mut>· %s</span>" % _esc(c["clinic_id"])) if c["clinic_id"] else "",
            PAYER_WORD.get(c["payer"], c["payer"]), (" <span class=mut>· %s</span>" % _esc(c["insurer"])) if c["insurer"] else "",
            _human(c["surgery_date"]), STAGE_WORD.get(c["stage"], c["stage"]), papers_cell, money))
    foot = ""
    if checker and rows:
        foot = "<tfoot><tr><td colspan=6>%d cases</td><td class=r>%s</td><td class=r>%s</td><td class=r>%s</td></tr></tfoot>" % (
            len(rows), _r(tot[0]), _r(tot[1]), _r(tot[0] - tot[1]))
    out.append("<div class='card'><table class='grid'><thead>%s</thead><tbody>%s</tbody>%s</table>%s</div>" % (
        head, "".join(body) or "<tr><td colspan=9 class=mut>No cases here yet.</td></tr>", foot,
        "<p class=mut>Balance counts only cases where the amount due from the hospital is written.</p>" if checker else ""))
    return _shell("Surgery cases", "<h1>Surgery cases</h1>" + "".join(out))


@bp.route(BASE + "/new")
def new_page():
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    a = request.args
    cid, name = _txt(a.get("cid"), 30), _txt(a.get("name"), 80)
    hint = {"ayush": "ayushman", "tpa": "cashless"}.get(a.get("payer") or "", a.get("payer") or "")
    q = _txt(a.get("q"), 40)
    out = [_nav(checker, "new"), _flash(a)]
    if a.get("cp"):
        out.append("<div class='ok'>From the Case Pack — %s</div>" % _esc(a.get("cp")))
    pick = ["<form method='get' action='%s/new' class='row'><input name=q class='note' value='%s' placeholder='Find the patient: clinic ID or name'>"
            "<button class='save'>Find</button></form>" % (BASE, _esc(q))]
    if q:
        res = search_patients(con, q)
        if not res:
            pick.append("<p class='mut'>Nobody found — write the name below.</p>")
        for rcid, rname, rhint in res:
            pick.append("<a class='pick' href='%s/new?cid=%s&name=%s&payer=%s'><b>%s</b> %s <span class='mut'>%s</span></a>" % (
                BASE, quote(rcid or "", safe=""), quote(rname or "", safe=""), quote(hint, safe=""), _esc(rname),
                ("· " + _esc(rcid)) if rcid else "", _esc(rhint)))
    out.append("<div class='card'><h2>1 · The patient</h2>%s</div>" % "".join(pick))
    out.append("<form method='post' action='%s/new' class='card'><h2>2 · The case</h2>"
               "<input type=hidden name=casepack_id value='%s'>"
               "<label>Patient's name<input name=patient class='note' value='%s' required></label>"
               "<label>Clinic ID<input name=clinic_id class='note' value='%s'></label>"
               "<label>Payer</label><div class='chips'>%s</div>"
               "<label>Insurer / TPA (cashless)<input name=insurer class='note'></label>"
               "<label>Hospital<input name=hospital class='note' value='%s'></label>"
               "<label>Operation<input name=procedure_text class='note' placeholder='e.g. PFN right hip'></label>"
               "<label>Surgery date<input type=date name=surgery_date class='note' value='%s'></label>"
               "<button class='save'>Make the case</button></form>" % (
                   BASE, _esc(_txt(a.get("cp"), 30)), _esc(name), _esc(cid),
                   "".join("<label class='chip'><input type=radio name=payer value='%s'%s> %s</label>" % (k, " checked" if k == hint else "", w)
                           for k, w in PAYERS), _esc(DEFAULT_HOSPITAL), _today().isoformat()))
    return _shell("New surgery case", "<h1>New surgery case</h1>" + "".join(out))


@bp.route(BASE + "/new", methods=["POST"])
def post_new():
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    patient, payer = _txt(f.get("patient"), 80), f.get("payer") or ""
    if not patient:
        return _back(BASE + "/new", err="patient", cid=f.get("clinic_id"))
    if payer not in PAYER_WORD:
        return _back(BASE + "/new", err="payer", cid=f.get("clinic_id"), name=patient)
    sd = (f.get("surgery_date") or "").strip()
    if sd and not _iso_ok(sd):
        return _back(BASE + "/new", err="date", cid=f.get("clinic_id"), name=patient)
    for _attempt in range(5):                    # two workers may number at once: the UNIQUE index decides, the loser takes the next
        no = next_case_no(con)
        try:
            cur = con.execute("INSERT INTO surg_case (case_no, clinic_id, patient, payer, insurer, hospital, procedure_text, surgery_date, stage, "
                              "casepack_id, created_by, created_at, changed_by, changed_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                              (no, _txt(f.get("clinic_id"), 30), patient, payer, _txt(f.get("insurer"), 80),
                               _txt(f.get("hospital"), 80) or DEFAULT_HOSPITAL, _txt(f.get("procedure_text"), 160), sd,
                               "applied" if payer in CREDIT else "planned", _txt(f.get("casepack_id"), 30), who, _stamp(), who, _stamp()))
            con.commit()
            break
        except Exception:                        # noqa: BLE001
            con.rollback()
    else:
        return _back(BASE + "/new", err="gone")
    _audit_safe(con, "surg_case", cur.lastrowid, "insert", None, dict(case_no=no, payer=payer, patient=patient), who)
    return _back("%s/case/%d" % (BASE, cur.lastrowid), msg="new")


@bp.route(BASE + "/case/<int:cid>")
def case_page(cid):
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    c = case(con, cid)
    if not c or c["voided_at"]:
        return _shell("Surgery case", _nav(checker) + "<div class='card'><h2>Not found</h2></div>"), 404
    a = request.args
    out = [_nav(checker), _flash(a)]
    out.append("<div class='card'><h2>%s · %s%s</h2><p class='big'>%s%s · %s · %s</p><p class=mut>Surgery %s · discharge %s · stage: <b>%s</b>%s</p></div>" % (
        c["case_no"], _esc(c["patient"]), (" · " + _esc(c["clinic_id"])) if c["clinic_id"] else "",
        PAYER_WORD[c["payer"]], (" (" + _esc(c["insurer"]) + ")") if c["insurer"] else "", _esc(c["hospital"]),
        _esc(c["procedure_text"]) or "operation not written", _human(c["surgery_date"]), _human(c["discharge_date"]),
        STAGE_WORD.get(c["stage"], c["stage"]), (" · Case Pack " + _esc(c["casepack_id"])) if c["casepack_id"] else ""))
    # papers
    plist = papers(con, cid)
    by = {}
    for p in plist:
        by.setdefault(p["kind"], []).append(p)
    need = needed(c["payer"])
    prow = []
    for k, w in PAPERS:
        files = by.get(k, [])
        state = ("<span class='good'>✓ %d</span>" % len(files)) if files else ("<span class='warn'>missing</span>" if k in need else "<span class=mut>—</span>")
        links = " ".join("<a href='%s/paper/%d' target=_blank>%s</a>" % (BASE, p["id"], "page %d" % (i + 1)) for i, p in enumerate(files))
        prow.append("<tr><td>%s%s</td><td>%s</td><td>%s</td><td><a class='btn' href='%s/case/%d/scan/%s'>Scan / upload</a></td></tr>" % (
            _esc(w), " <span class=mut>(needed)</span>" if k in need else "", state, links, BASE, cid, k))
    vd = ""
    if plist:
        vd = ("<details class='vd'><summary>Remove a wrongly filed paper</summary><form method='post' action='%s/void' class='row'>"
              "<input type=hidden name=kind value=paper><input type=hidden name=back value='%s/case/%d'><select name=id class='note'>%s</select>%s"
              "<button class='clear'>Remove</button></form></details>") % (
            BASE, BASE, cid, "".join("<option value='%d'>%s — %s</option>" % (p["id"], _esc(PAPER_WORD.get(p["kind"], p["kind"])), (p["at"] or "")[:16])
                                     for p in plist), _why_select())
    out.append("<div class='card'><h2>Papers</h2><table class='grid'><tbody>%s</tbody></table>%s</div>" % ("".join(prow), vd))
    # implants
    ims = implants(con, cid)
    irows = []
    for i in ims:
        money = ""
        if checker:
            money = "<td class=r>%s</td><td class=r>%s</td>" % (_r(i["charge_p"]) if i["charge_p"] is not None else "—",
                                                                _r(i["payable_p"]) if i["payable_p"] is not None else "—")
        irows.append("<tr><td>%s</td><td>%s%s</td><td class=r>%s</td><td>%s</td>%s</tr>" % (
            _esc(i["vendor"]), _esc(i["item"]), (" ×%d" % i["qty"]) if i["qty"] != 1 else "", _r(i["bill_p"]),
            "Patient's name" if i["bill_to"] == "patient" else "Dr Manoj (estimate)", money))
    ihead = "<tr><th>Vendor</th><th>Implant</th><th class=r>Vendor's bill</th><th>Billed to</th>%s</tr>" % (
        "<th class=r>Charged to patient</th><th class=r>Actually due to vendor</th>" if checker else "")
    vendors = con.execute("SELECT id, name FROM surg_vendor ORDER BY name").fetchall()
    credit = c["payer"] in CREDIT
    iform = ("<form method='post' action='%s/case/%d/implant' class='sub'><h3>Add an implant line</h3>"
             "<label>Vendor<select name=vendor_id class='note'><option value=''>— choose —</option>%s</select></label>"
             "<label>…or a new vendor<input name=vendor_new class='note' placeholder='vendor name'></label>"
             "<label>Implant<input name=item class='note' placeholder='e.g. PFN 10x240 with screws'></label>"
             "<label>Quantity<input name=qty class='note' value='1' inputmode=numeric></label>"
             "<label>Vendor's bill amount (₹)<input name=bill class='amt' inputmode=decimal></label>"
             "<label>Billed to</label><div class='chips'><label class='chip'><input type=radio name=bill_to value=patient%s> In the patient's name</label>"
             "<label class='chip'><input type=radio name=bill_to value=doctor%s> To Dr Manoj (estimate)</label></div>%s"
             "<button class='save'>Add</button></form>") % (
        BASE, cid, "".join("<option value='%d'>%s</option>" % (v["id"], _esc(v["name"])) for v in vendors),
        " checked" if credit else "", "" if credit else " checked",
        ("<label>Charged to the patient for it (₹, cash patients)<input name=charge class='amt' inputmode=decimal></label>"
         "<label>Actually due to the vendor (₹, if less than the bill — cashless)<input name=payable class='amt' inputmode=decimal></label>")
        if checker else "")
    ivd = ""
    if ims:
        ivd = ("<details class='vd'><summary>Remove a wrong implant line</summary><form method='post' action='%s/void' class='row'>"
               "<input type=hidden name=kind value=implant><input type=hidden name=back value='%s/case/%d'><select name=id class='note'>%s</select>%s"
               "<button class='clear'>Remove</button></form></details>") % (
            BASE, BASE, cid, "".join("<option value='%d'>%s — %s</option>" % (i["id"], _esc(i["vendor"]), _esc(i["item"])) for i in ims), _why_select())
    out.append("<div class='card'><h2>Implants</h2><table class='grid'><thead>%s</thead><tbody>%s</tbody></table>%s<details%s><summary>+ Add an implant line</summary>%s</details></div>" % (
        ihead, "".join(irows) or "<tr><td colspan=6 class=mut>None yet.</td></tr>", ivd, "" if ims else " open", iform))
    # money (the owner only)
    if checker:
        got = received(con, cid)
        allocs = con.execute("SELECT a.amount_p, r.id, r.day, r.from_whom, r.period FROM surg_receipt_alloc a JOIN surg_receipt r ON r.id=a.receipt_id "
                             "WHERE a.case_id=? AND r.voided_at='' ORDER BY r.day", (cid,)).fetchall()
        lines = "".join("<li><a href='%s/receipt/%d'>%s · %s%s</a> — %s</li>" % (BASE, r["id"], _human(r["day"]), _esc(r["from_whom"]),
                                                                              (" · " + _esc(r["period"])) if r["period"] else "", _r(r["amount_p"]))
                        for r in allocs) or "<li class=mut>Nothing received yet.</li>"
        bal = (c["due_p"] - got) if c["due_p"] is not None else None
        out.append("<div class='card'><h2>Money from the hospital</h2><p class='big'>Due %s · received %s · balance %s</p><ul>%s</ul></div>" % (
            _r(c["due_p"]), _r(got), _r(bal) if bal is not None else "—", lines))
    # edit
    out.append(_edit_form(c, checker))
    if checker:
        out.append("<details class='card vd'><summary>Remove this whole case (made by mistake)</summary><form method='post' action='%s/void' class='row'>"
                   "<input type=hidden name=kind value=case><input type=hidden name=id value='%d'><input type=hidden name=back value='%s'>%s"
                   "<button class='clear'>Remove the case</button></form></details>" % (BASE, cid, BASE, _why_select()))
    return _shell("%s %s" % (c["case_no"], c["patient"]), "<h1>Surgery case</h1>" + "".join(out))


def _why_select():
    return "<select name=why class='note' style='flex:0 0 auto'><option value=''>why?</option>%s</select>" % "".join(
        "<option value='%s'>%s</option>" % (k, w) for k, w in VOID_WHY)


def _edit_form(c, checker):
    money = ("<label>Amount due to Dr Manoj from the hospital for this case (₹)<input name=due class='amt' inputmode=decimal value='%s'></label>"
             % (("%.2f" % (c["due_p"] / 100.0)).rstrip("0").rstrip(".") if c["due_p"] is not None else "")) if checker else ""
    return ("<details class='card'><summary>Change the case details</summary><form method='post' action='%s/case/%d/edit'>"
            "<label>Stage<select name=stage class='note'>%s</select></label>"
            "<label>Patient's name<input name=patient class='note' value='%s'></label>"
            "<label>Clinic ID<input name=clinic_id class='note' value='%s'></label>"
            "<label>Payer<select name=payer class='note'>%s</select></label>"
            "<label>Insurer / TPA<input name=insurer class='note' value='%s'></label>"
            "<label>Hospital<input name=hospital class='note' value='%s'></label>"
            "<label>Operation<input name=procedure_text class='note' value='%s'></label>"
            "<label>Surgery date<input type=date name=surgery_date class='note' value='%s'></label>"
            "<label>Discharge date<input type=date name=discharge_date class='note' value='%s'></label>"
            "<label>Case Pack number<input name=casepack_id class='note' value='%s'></label>"
            "<label>Note<input name=note class='note' value='%s'></label>%s"
            "<button class='save'>Save</button></form></details>") % (
        BASE, c["id"], "".join("<option value='%s'%s>%s</option>" % (k, " selected" if k == c["stage"] else "", w) for k, w in STAGES),
        _esc(c["patient"]), _esc(c["clinic_id"]),
        "".join("<option value='%s'%s>%s</option>" % (k, " selected" if k == c["payer"] else "", w) for k, w in PAYERS),
        _esc(c["insurer"]), _esc(c["hospital"]), _esc(c["procedure_text"]), _esc(c["surgery_date"]), _esc(c["discharge_date"]),
        _esc(c["casepack_id"]), _esc(c["note"]), money)


@bp.route(BASE + "/case/<int:cid>/edit", methods=["POST"])
def post_edit(cid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    c = case(con, cid)
    if not c or c["voided_at"]:
        return _back(BASE, err="gone")
    back = "%s/case/%d" % (BASE, cid)
    if f.get("stage") not in STAGE_WORD:
        return _back(back, err="stage")
    if f.get("payer") not in PAYER_WORD:
        return _back(back, err="payer")
    for k in ("surgery_date", "discharge_date"):
        if (f.get(k) or "").strip() and not _iso_ok(f.get(k).strip()):
            return _back(back, err="date")
    new = dict(stage=f["stage"], patient=_txt(f.get("patient"), 80) or c["patient"], clinic_id=_txt(f.get("clinic_id"), 30),
               payer=f["payer"], insurer=_txt(f.get("insurer"), 80), hospital=_txt(f.get("hospital"), 80) or c["hospital"],
               procedure_text=_txt(f.get("procedure_text"), 160), surgery_date=(f.get("surgery_date") or "").strip(),
               discharge_date=(f.get("discharge_date") or "").strip(), casepack_id=_txt(f.get("casepack_id"), 30), note=_txt(f.get("note"), 300))
    if checker and "due" in f:
        d = _paise(f.get("due"), allow_blank=True)
        if d is False:
            return _back(back, err="amount")
        new["due_p"] = d
    before = {k: c[k] for k in new}
    con.execute("UPDATE surg_case SET %s, changed_by=?, changed_at=? WHERE id=?" % ", ".join("%s=?" % k for k in new),
                list(new.values()) + [who, _stamp(), cid])
    con.commit()
    _audit_safe(con, "surg_case", cid, "update", before, new, who)
    return _back(back, msg="saved")


@bp.route(BASE + "/case/<int:cid>/implant", methods=["POST"])
def post_implant(cid):
    u, checker, err = _gate()
    if err:
        return err
    con, f, who = _db(), request.form, u.get("user", "")
    c = case(con, cid)
    back = "%s/case/%d" % (BASE, cid)
    if not c or c["voided_at"]:
        return _back(BASE, err="gone")
    item = _txt(f.get("item"), 160)
    if not item:
        return _back(back, err="item")
    vid = None
    newv = _txt(f.get("vendor_new"), 80)
    if newv:
        r = con.execute("SELECT id FROM surg_vendor WHERE name=?", (newv,)).fetchone()
        if r:
            vid = r["id"]
        else:
            vid = con.execute("INSERT INTO surg_vendor (name, created_by, created_at) VALUES (?,?,?)", (newv, who, _stamp())).lastrowid
    elif (f.get("vendor_id") or "").isdigit():
        r = con.execute("SELECT id FROM surg_vendor WHERE id=?", (int(f["vendor_id"]),)).fetchone()
        vid = r["id"] if r else None
    if not vid:
        con.rollback()
        return _back(back, err="vendor")
    qty = int(f["qty"]) if (f.get("qty") or "").strip().isdigit() and 0 < int(f["qty"]) < 1000 else 1
    bill = _paise(f.get("bill"))
    if bill is False or not bill:
        con.rollback()
        return _back(back, err="amount")
    bill_to = f.get("bill_to") if f.get("bill_to") in ("patient", "doctor") else ("patient" if c["payer"] in CREDIT else "doctor")
    charge = payable = None
    if checker:
        charge = _paise(f.get("charge"), allow_blank=True)
        payable = _paise(f.get("payable"), allow_blank=True)
        if charge is False or payable is False:
            con.rollback()
            return _back(back, err="amount")
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
    back = f.get("back") or BASE
    if not back.startswith(BASE):
        back = BASE
    sep = "&" if "?" in back else "?"
    table = {"paper": "surg_paper", "implant": "surg_implant", "pay": "surg_vendor_pay", "cheque": "surg_cheque",
             "receipt": "surg_receipt", "case": "surg_case"}.get(f.get("kind"))
    if table in ("surg_vendor_pay", "surg_cheque", "surg_receipt", "surg_case") and not checker:
        return redirect(back + sep + "err=gone")
    rid = f.get("id") or ""
    if not table or not rid.isdigit():
        return redirect(back + sep + "err=gone")
    if f.get("why") not in dict(VOID_WHY):
        return redirect(back + sep + "err=why")
    r = con.execute("SELECT * FROM %s WHERE id=? AND voided_at=''" % table, (int(rid),)).fetchone()
    if not r:
        return redirect(back + sep + "err=gone")
    con.execute("UPDATE %s SET voided_at=?, voided_by=?, void_why=? WHERE id=? AND voided_at=''" % table, (_stamp(), who, f["why"], int(rid)))
    con.commit()
    _audit_safe(con, table, int(rid), "void", {k: r[k] for k in r.keys() if k in ("amount_p", "bill_p", "kind", "case_no", "path")},
                dict(why=f["why"]), who)
    return redirect(back + sep + "msg=voided")


# ---------------------------------------------------------------- papers: the scanner, the upload, the file
def _scan_host(title, upload_url, fields, name_base, back_url):
    cfg = {"title": title, "uploadUrl": upload_url, "fileField": "file", "uploadFields": fields, "nameBase": name_base,
           "backUrl": back_url, "allowIdCard": False, "allowBatch": False, "directFile": True}
    return ("<!DOCTYPE html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>%s</title><style>body{margin:0;background:#f4f6fa;color:#0f172a;font:15px/1.5 system-ui,sans-serif}"
            ".top{background:#0b1220;color:#fff;padding:12px 16px;font-weight:650;display:flex;gap:12px;align-items:center;position:sticky;top:0;z-index:30}"
            ".top a{color:#e2e8f0;text-decoration:none;font-size:13px;padding:8px 13px;border-radius:9px;background:rgba(255,255,255,.13)}"
            "</style></head><body><div class=top><a href='%s'>← Back</a><span>%s</span></div>"
            "<script>window.SCANNER_CONFIG = %s;</script><div id=scanroot></div>"
            "<script src='/finance/scan/jspdf.js'></script><script src='/finance/scan/widget.js?v=579'></script></body></html>") % (
        _esc(title), _esc(back_url), _esc(title), json.dumps(cfg).replace("</", "<\\/"))


@bp.route(BASE + "/case/<int:cid>/scan/<kind>")
def scan_page(cid, kind):
    u, checker, err = _gate()
    if err:
        return err
    con = _db()
    c = case(con, cid)
    if not c or c["voided_at"] or kind not in PAPER_WORD:
        return _back(BASE, err="kind" if c else "gone")
    return _scan_host("%s — %s (%s)" % (PAPER_WORD[kind], c["patient"], c["case_no"]), "%s/api/case/%d/paper/%s" % (BASE, cid, kind),
                      {"case_id": str(cid), "kind": kind}, "%s_%s" % (c["case_no"], kind), "%s/case/%d?msg=paper" % (BASE, cid))


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
    for v in con.execute("SELECT * FROM surg_vendor ORDER BY name"):
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
    if con.execute("SELECT id FROM surg_vendor WHERE name=?", (name,)).fetchone():
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
        BASE, w["id"], w["case_no"], _esc(w["patient"]), PAYER_WORD[w["payer"]], _human(w["surgery_date"]), _r(vendor_payable(con, vid, w["id"])))
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
            "<div class='card'><h2>%s — implant ledger</h2><p class='big'>%s</p><p class='mut noprint'>Private to Dr Manoj. "
            "<a href='#' onclick='window.print();return false'>Print / save as PDF to share with the vendor</a></p>"
            "<table class='grid'><thead><tr><th>Date</th><th>Entry</th><th class=r>Owed to vendor</th><th class=r>In Dr Manoj's favour</th><th class=r>Running</th></tr></thead>"
            "<tbody>%s</tbody></table><p class=mut>Running balance: above zero, Dr Manoj owes the vendor; below zero, the vendor owes Dr Manoj.</p></div>"
            "<div class='card'><h2>Credit patients still awaiting the vendor's cheque</h2><ul>%s</ul></div>"
            "<div class='card'><h2>Cheques not yet assigned to patients</h2><ul>%s</ul></div>%s") % (
        _esc(v["name"]), verdict, "".join(trs) or "<tr><td colspan=5 class=mut>No entries yet.</td></tr>", wait, una, forms)
    return _shell("%s ledger" % v["name"], body)


def _void_money(vid, pays, chqs):
    opts = ["<option value='pay:%d'>Payment %s · %s</option>" % (p["id"], _human(p["day"]), _r(p["amount_p"])) for p in pays]
    opts += ["<option value='cheque:%d'>Cheque %s · %s · %s</option>" % (q["id"], _esc(q["cheque_no"]) or "—", _human(q["day"]), _r(q["amount_p"])) for q in chqs]
    if not opts:
        return ""
    return ("<details class='vd'><summary>Remove a wrong payment or cheque</summary><form method='post' action='%s/vendor/%d/void' class='row'>"
            "<select name=what class='note'>%s</select>%s<button class='clear'>Remove</button></form></details>") % (BASE, vid, "".join(opts), _why_select())


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
            BASE, r["id"], r["case_no"], _esc(r["patient"]), PAYER_WORD.get(r["payer"], r["payer"]), _human(r["surgery_date"]),
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
        d["hint_p"], d["now_p"] = left, now.get(c["id"], 0)
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
            "<div class='card'><h2>%s · %s%s</h2><p class='big'>%s — against patients %s, left %s</p><p>%s · <a class='btn' href='%s/receipt/%d/scan'>Scan / upload the statement</a></p>%s</div>"
            "<form method='post' action='%s/receipt/%d' class='card'><h2>Amount paid against each patient (from the statement)</h2>"
            "<p class=mut>The balance still due for each case is shown. %s</p>"
            "<table class='grid'><thead><tr><th>Case</th><th>Patient</th><th>Payer</th><th>Surgery</th><th class=r>Still due</th><th>Paid in this statement (₹)</th></tr></thead>"
            "<tbody>%s</tbody></table><button class='save'>Save</button></form>"
            "<details class='card vd'><summary>Remove this payment (wrong entry)</summary><form method='post' action='%s/void' class='row'>"
            "<input type=hidden name=kind value=receipt><input type=hidden name=id value='%d'><input type=hidden name=back value='%s/receipts'>%s"
            "<button class='clear'>Remove</button></form></details>") % (
        _human(r["day"]), _esc(r["from_whom"]), (" · " + _esc(r["period"])) if r["period"] else "", _r(r["amount_p"]), _r(used),
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


# ---------------------------------------------------------------- the look
def _shell(title, body):
    """The owner's pages' large, plain look (as physio_book's), in English."""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#4a555e;--line:#9aa8b3;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--entry:#fffbe6}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);font:17px/1.55 "Segoe UI",system-ui,-apple-system,sans-serif}
h1{font-size:23px;margin:0 0 12px;color:var(--accent)}h2{font-size:20px;margin:0 0 10px;color:var(--accent)}h3{margin:12px 0 6px;color:var(--accent)}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:14px;margin:0 0 14px;overflow-x:auto}
details summary{cursor:pointer;color:var(--accent);font-weight:600;padding:4px 0}
label{display:block;margin:8px 0 2px;font-weight:600}
.mut{color:var(--mut);font-size:15px}.big{font-size:20px;font-weight:600}
table.grid{width:100%%;border-collapse:collapse;font-size:16px}
.grid th,.grid td{border:1px solid var(--line);padding:7px;vertical-align:top}.grid thead th{background:#cfdae3}
.r{text-align:right;white-space:nowrap}.d{white-space:nowrap}tfoot td{background:#dff0d8;font-weight:700}
input.amt{width:100%%;min-height:46px;font-size:20px;padding:6px 10px;border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry)}
.note{width:100%%;min-height:44px;padding:7px;border:2px solid #5b6b76;border-radius:8px;font-size:17px;background:var(--entry)}
select.note{background:#fff}.grid input.amt{min-height:38px;font-size:17px}
.row{display:flex;gap:8px;align-items:center;margin:0 0 10px;flex-wrap:wrap}.row .note{flex:1}
button.save{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:12px 20px;font-size:17px;font-weight:600;cursor:pointer;margin-top:8px}
button.clear{background:var(--paper);color:#8c2f2f;border:2px solid #8c2f2f;border-radius:9px;padding:9px 14px;font-size:15px;cursor:pointer}
a.btn{display:inline-block;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:6px 12px;text-decoration:none;font-size:15px;background:var(--paper);white-space:nowrap}
.tabs{display:flex;gap:8px;margin:0 0 12px;flex-wrap:wrap}
a.tab{flex:1;text-align:center;border:2px solid var(--accent);border-radius:10px;padding:10px;font-weight:600;color:var(--accent);background:var(--paper);text-decoration:none;white-space:nowrap}
.tabs.small a.tab{flex:0 1 auto;padding:6px 12px;font-size:15px}a.tab.on{background:var(--accent);color:#fff}
.chips{display:flex;gap:8px;flex-wrap:wrap}.chip{display:inline-block;border:2px solid var(--line);border-radius:9px;padding:8px 12px;font-weight:500;background:#fff;margin:0}
a.pick,label.pick{display:block;border:2px solid var(--line);border-radius:9px;padding:10px;margin:6px 0;color:var(--ink);background:#fff;text-decoration:none;font-weight:400}
.ok{background:#dff0d8;border-left:6px solid #2c6e2f;padding:10px 14px;margin-bottom:12px}
.bad{background:#fbe4e2;border-left:6px solid #8c2f2f;padding:10px 14px;margin-bottom:12px}
.good{color:#1d6b2f;font-weight:600}.warn{color:#9a5b00;font-weight:600}
.inline{display:inline}.sub{border-top:1px dashed var(--line);margin-top:10px;padding-top:6px}
.vd summary{font-size:14px;color:#8c2f2f;font-weight:400}
@media print{.noprint,.tabs,.vd,form{display:none!important}body{background:#fff;padding:0}.card{border:0}}
</style></head><body>%s</body></html>""" % (_esc(title), body)
