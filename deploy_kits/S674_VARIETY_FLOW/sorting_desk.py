#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sorting_desk.py -- S551_SORTING_DESK (D722, D719, D710, D664; the owner's "Look ok, build now", 14-Oct-2026).

THE OWNER'S RULING
    One sorting desk on the laptop for him and Shavez: the waiting papers on the left, the scan large in the middle, what
    was read (editable) and ONE list "Where does it go?" on the right, one Save -- next paper. Beside it: Bills awaited
    (challans by supplier, each supplier set once to how it bills), the Implant stock ledger (owed, paid, balance per
    supplier) and The month (section by section). A patient's paper is set aside here, out of every total -- it belongs to
    the surgical case pack. A section, a sub-section or whose expense a paper is, is never guessed: only a person's Save.
    Sorted = accepted (a challan waits for its bill). A paper already accepted can be changed on the desk, by a person,
    audited (his deliberate widening of the rules).

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded import at its foot, after clinic_papers.py: if this
    file cannot load, the app runs exactly as before. Its addresses (the /scanapp prefix is added by the app's middleware):
        GET  /desk                    the desk                     GET  /desk/api/list        the waiting papers (JSON)
        GET  /desk/api/paper/<id>     one paper (JSON)             GET  /desk/api/find?no=    "Open B-____"
        POST /desk/api/save           one Save: one transaction, one commit, audited
        GET  /desk/awaited            Bills awaited, by supplier   POST /desk/awaited/mode, /desk/awaited/pay
        GET  /desk/implants           Implant stock ledger         POST /desk/implants/pay, /void, /check
        GET  /desk/month              The month, section by section
        POST /desk/switch             the owner's three switches (scan.cv, scan.lanes5, desk.on)
    The owner and the managers (checker_required). While desk.on is OFF a manager sees one line; the owner uses it fully.

WHAT IT DELIBERATELY DOES NOT DO
    It never calls the app's doors (they commit, flash and redirect): each door's rule is a small helper here, with no
    commit, and Save commits once. It never moves a paper off the pharmacy lane and never lists one. It never deletes a row
    or a file (rejected, voided_at, final). It never saves a suggestion: only a person's Save. packs.py, scanner_widget.js
    and the finance side are not touched. Standard library and Flask only; no CDN, no library, no build step.
"""
import datetime
import functools
import json
import math
import re
import sqlite3
import sys
import time

from flask import abort, g, jsonify, redirect, render_template_string, request, session, url_for
from markupsafe import Markup

VERSION = "S551.2"             # S551.2 = fix round 1 (S551_FIX1: C2, C3, C4, N4, N5, N6)
CORRECTIONS = "S555"          # S555_DESK_CORRECTIONS: Save always on screen, dd-mm-yyyy, the misread-date rule, the own name,
#                               Claude's reading beside each box (VERSION is kept: S551's walk reads it)
MACHINE = "S557"              # S557_MACHINE_PAGES: the machine-pages switch, one word per lane, a non-number amount ignored
ROAD = "S559"                 # S559_ONE_ROAD: the one menu on the desk's pages, /desk?open=<id>, every paper row to the desk
RECEIPTS = "S560"             # S560_RECEIPTS_STATEMENTS: Receipt and Statement (never spend), one payment record, the desk on one screen
TIDY = "S563"                 # S563_SCANAPP_TIDY: Restore a set-aside paper (F-902), never straight to accepted, the statement's order
LAST = "S566"                 # S566_SCANAPP_LAST_FIXES: a restore checks for a double first; every waiting paper reachable; one count
STOCK = "S568"                # S568_STATIONERY_STOCK: Stationery & packaging, its lines to the stock, the mixed tick, Add from a file
PEXP = "Pharmacy expense"     # S568 item 7: the Aumni preset's kind (never 'Pharmacy': Sanjeevni's registers never pair it)
STOCK_FIX = "S568_FIX1"       # S568 FIX1 (K1 CORRECTION 3): "Add a paper from a file" takes a PDF or a photo only
BATTERY = "S571"              # S571_BATTERIES: the switch batteries.on; a battery's bill offered on the desk; the payer pre-selects
PROCROOM = "S634"             # S634_PROCROOM_LIST: a Procedure room paper's lines -- product, quantity, brand, place; no rate (procroom.py)
PROCROOM_S635 = "S635"        # S635_PROCROOM_ORDERS: his order (counts nothing) and the slip joined to it, chosen in the same panel
AR = None                     # the asset app's module, handed in by init()
CP = None                     # clinic_papers, already mounted by the app
TODAY = None                  # the walk sets a made-up day here; every date rule also takes `today` as an argument

OFF_LINE = "The sorting desk opens when Dr Manoj switches it on."
PATIENT = "patient_paper"
CONS = ("procedure", "xray_small", "xray_11x14", "others", "stationery")          # S568 item 1
CLINIC_DEST = CONS + ("implant_stock", "clinic_equipment")
LEFT_ON_LANE = ("construction", "personal", "resume", "misc")      # left on its lane (a SORT_LANE; else Other document)
SECTION_KEEP = ("construction", "resume", "misc", "personal")       # kept on a personal expense; anything else is cleared

DESTINATIONS = (      # the board's six groups -- the one list "Where does it go?"
    ("Clinic consumables", (("procedure", "Procedure room"), ("xray_small", "X-ray small film"),
                            ("xray_11x14", "X-ray 11 × 14"), ("others", "Others"), ("stationery", "Stationery & packaging"))),      # S568
    ("Clinic expense", (("implant_stock", "Implant stock"), ("clinic_equipment", "Clinic equipment"),      # S560 item 1
                ("construction", "Construction work"))),
    ("My expense — Dr MK / Dr Bhawna", (("pe", "Personal expense"), ("personal", "Personal (you only)"))),      # S560 item 1
    ("Handed over", (("pharmacy", "Pharmacy — Sanjeevni"), ("lab", "NK Pathology"))),
    ("Documents", (("resume", "Resumes"), ("misc", "Miscellaneous"))),
    ("Not here", ((PATIENT, "A patient’s paper — surgical case pack"),)),
)
DEST_NAME = dict(kv for _t, items in DESTINATIONS for kv in items)
NOTES = {             # the board's grey line for the chosen destination
    "implant_stock": "Goes to the implant stock ledger of this supplier (owed until paid).",
    "stationery": "Clinic stationery and packaging. Match its lines to the stationery list below — the stock goes up once.",      # S568
    "procedure": "Procedure-room goods. Give each line its product and its place below — the rates are Dr Manoj's alone.",      # S634
    PATIENT: "Kept aside, out of every total. It belongs to the surgical case pack.",
    "pharmacy": "Handed to Sanjeevni, as today.",
    "lab": "NK Pathology side; a bill goes into the accountants’ pack 8.1.",
    "construction": "Counted on its own; never called clinic or MK by the system.",
    "pe": "Into Personal expenses; the accountants’ pack 8.2 or 8.3.",
}
KINDS = (("bill", "Bill"), ("estimate", "Estimate slip"), ("challan", "Challan"), ("receipt", "Receipt"), ("statement", "Statement"))      # S560
CLAUDE_KIND = {"tax_invoice": "bill", "bill": "bill", "estimate": "estimate", "quotation": "estimate", "challan": "challan"}
MODES = (("monthly", "Monthly bill"), ("sometimes", "A bill now and then"), ("paid", "Paid on challan — no bill"))
MODE_RULE = {
    "monthly": "Challans wait for the month’s bill. Amber if no bill by the 10th of next month. When the bill comes, the desk offers the month’s challans — one tap joins them.",
    "sometimes": "Challans wait without turning amber, oldest first, with their age. When a bill comes, the desk shows every open challan — tick the ones it covers.",
    "paid": "The challan or estimate is the final paper. It never waits. Note the payment on it when you pay.",
    "": "Not set yet. Its challans wait and turn amber after %d days (today’s rule). Set how this supplier bills.",
}
HOW = ("Bank / UPI", "Cheque", "Cash")
SWITCHES = (("scan.cv", "Smart scanner"), ("scan.lanes5", "Reception buttons"), ("desk.on", "Sorting desk for Shavez"),
            ("machine.on", "Machine pages for Shavez"),                                  # S557 A7
            ("stationery.issue_on", "Stationery diya for managers"),                    # S568 item 4 (absent = OFF)
            ("batteries.on", "Batteries for Shavez"))                                   # S571 item 6 (absent = OFF)
MONTH_SECTIONS = (("procedure", "Procedure room", ("procedure",)),
                  ("xray", "X-ray films", ("xray_small", "xray_11x14", "xray")),
                  ("others", "Others", ("others",)),
                  ("stationery", "Stationery & packaging", ("stationery",)),                  # S568 item 1
                  ("implant_stock", "Implant stock", ("implant_stock",)),
                  ("construction", "Construction work", ("construction",)),
                  ("clinic_equipment", "Clinic equipment", ("clinic_equipment",)))
S441_WHO = "server (S441 double-scan rule)"


class DeskError(Exception):
    def __init__(self, msg, code=400):
        Exception.__init__(self, msg)
        self.code = code


# ---------------------------------------------------------------------------------------------- the database's part
BILL_COLS = (("paid_on", "TEXT"), ("paid_amount", "REAL"), ("to_accountant", "INTEGER NOT NULL DEFAULT 0"),      # S560 item 6
             ("mixed", "INTEGER NOT NULL DEFAULT 0"))                                                     # S568 item 6
DDL = (
    "CREATE TABLE IF NOT EXISTS challan_supplier(supplier_key TEXT PRIMARY KEY, name TEXT, mode TEXT NOT NULL "
    "CHECK(mode IN ('monthly','sometimes','paid')), set_by TEXT, set_at TEXT)",
    "CREATE TABLE IF NOT EXISTS implant_payment(id INTEGER PRIMARY KEY, supplier_key TEXT NOT NULL, day TEXT NOT NULL, "
    "amount REAL NOT NULL, how TEXT NOT NULL, against TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, "
    "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS implant_check(supplier_key TEXT, upto TEXT, by_whom TEXT, at TEXT)",
    "CREATE TABLE IF NOT EXISTS desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT)",
    # S560 item 5: ONE payment record per paper -- a re-save updates it in place (FIX1 B1; the old values kept in payment_changed),
    # a mistake is voided; every bill reference with its fingerprint (S557)
    "CREATE TABLE IF NOT EXISTS paper_payment(id INTEGER PRIMARY KEY, paid_on TEXT NOT NULL, amount REAL NOT NULL, mode TEXT NOT NULL "
    "CHECK(mode IN ('cash','cheque','bank')), ref TEXT NOT NULL DEFAULT '', proof_bill_id INTEGER, proof_created_at TEXT NOT NULL DEFAULT '', "
    "by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    # FIX1 B1: a re-save changes the payment -- its old allocation rows are voided (kept) and new ones written; one live row per bill
    "CREATE TABLE IF NOT EXISTS paper_payment_bill(payment_id INTEGER NOT NULL, bill_id INTEGER NOT NULL, bill_created_at TEXT NOT NULL DEFAULT '', "
    "amount REAL NOT NULL, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '', PRIMARY KEY(payment_id, bill_id, voided_at))",
)


def ensure(db):
    """Additive and idempotent. Two gunicorn workers start at once: 'duplicate column' / 'already exists' from the
    second is normal (as clinic_papers.ensure)."""
    have = {r[1] for r in db.execute("PRAGMA table_info(bills)")}
    for col, typ in BILL_COLS:
        if col not in have:
            try:
                db.execute("ALTER TABLE bills ADD COLUMN %s %s" % (col, typ))
            except sqlite3.OperationalError as ex:
                if "duplicate column" not in str(ex).lower():
                    raise
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    db.commit()


def ensure_at_mount(db_path, tries=3, wait=1.0, timeout=3):
    """At mount, in each gunicorn worker (FIX1 N4): 'database is locked' is retried briefly and then ignored for this
    worker -- the installer's data step has already made the tables -- so the desk still mounts. Any other error raises.
    Returns True when ensure() ran, False when the lock outlasted the tries."""
    for i in range(max(1, tries)):
        db = None
        try:
            db = sqlite3.connect(db_path, timeout=timeout)
            ensure(db)
            return True
        except sqlite3.OperationalError as ex:
            if "locked" not in str(ex).lower():
                raise
            if i + 1 < tries:
                time.sleep(wait)
        finally:
            if db is not None:
                db.close()
    print("sorting_desk: the database stayed locked at mount; its tables are left to the installer's data step", file=sys.stderr)
    return False


def ensure_path(db_path, floor=None):
    """For the installer: the tables and columns, and desk.floor = the install day when it is absent. Returns the floor."""
    con = sqlite3.connect(db_path, timeout=20)
    try:
        ensure(con)
        if floor:
            con.execute("INSERT OR IGNORE INTO settings(key,value) VALUES('desk.floor',?)", (floor,))
            con.commit()
        r = con.execute("SELECT value FROM settings WHERE key='desk.floor'").fetchone()
        return r[0] if r else ""
    finally:
        con.close()


# ---------------------------------------------------------------------------------------------- small helpers
def _today():
    return TODAY or datetime.date.today()


def _who():
    try:
        return g.user["display_name"] or g.user["username"]
    except Exception:                                                # noqa: BLE001
        return ""


def _owner():
    try:
        return g.user["role"] == "owner"
    except Exception:                                                # noqa: BLE001
        return False


def _setting(db, key, default):
    try:
        r = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if (r and r[0] is not None) else default
    except sqlite3.Error:
        return default


def desk_on(db):
    return (_setting(db, "desk.on", "off") or "").strip().lower() == "on"


def _int_setting(db, key, default):
    try:
        return max(1, int(str(_setting(db, key, default)).strip()))
    except (TypeError, ValueError):
        return default


def _audit_desk(db, action, detail):
    db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
               (AR._now_ist(), _who(), action, json.dumps(detail or {}, ensure_ascii=False)[:500]))


def _stamp(b):
    return b["stamp_no"] or ("#%d" % b["id"])


def _col(b, k):
    try:
        return b[k]
    except (IndexError, KeyError):
        return None


def _lane(b):
    return b["lane"] or AR.KIND_LANE.get(b["kind"], "clinic")


def _row(db, bid):
    return db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE b.id=?", (bid,)).fetchone()


def _key(v):
    return CP._supplier_key(v)


def _iso(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:                                                # noqa: BLE001
        return None


def _dmy(s):
    """S555 item 2: every date the desk and its three pages show reads dd-mm-yyyy."""
    d = _iso(s)
    return d.strftime("%d-%m-%Y") if d else (s or "")


def _dm(s):
    d = _iso(s)
    return d.strftime("%d-%m-%Y") if d else (s or "")


_DMY = re.compile(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})")
_YMD = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def parse_date(s):
    """S555 item 2: a typed date -> datetime.date, or None when it cannot be understood. Accepts dd-mm-yyyy, d-m-yy and
    dd/mm/yyyy (day first, as the clinic writes; a two-digit year is 20yy) and yyyy-mm-dd."""
    t = str(s if s is not None else "").strip()
    try:
        m = _YMD.fullmatch(t)
        if m:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = _DMY.fullmatch(t)
        if m:
            y = int(m.group(3)) + (2000 if len(m.group(3)) == 2 else 0)
            return datetime.date(y, int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
    return None


def typed_date(v, stored=None):
    """A date typed in a box -> ISO yyyy-mm-dd for the database ('' -> None). A value left as it was shown stays as it
    is; anything else that cannot be understood is refused with one plain line, and nothing is saved."""
    t = str(v if v is not None else "").strip()
    if not t:
        return None
    if stored and t in (str(stored).strip(), _dmy(stored)):
        return stored
    d = parse_date(t)
    if d is None:
        raise DeskError("The date “%s” is not understood — type it as dd-mm-yyyy. Nothing was saved." % t[:20])
    return d.isoformat()


def _ym_short(ym):
    try:
        return datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%b %Y")
    except Exception:                                                # noqa: BLE001
        return ym or ""


def _ym_shift(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) + k
    while m < 1:
        y, m = y - 1, m + 12
    while m > 12:
        y, m = y + 1, m - 12
    return "%04d-%02d" % (y, m)


def _amount(v):
    """The amount as typed: '1,30,003', '₹650', 'Rs 650' -> a number (rupees); '' -> None; anything else -> raises."""
    s = str(v if v is not None else "").replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    if not s:
        return None
    n = AR._num(s)
    if n is None:
        raise DeskError("The amount “%s” is not a number." % str(v)[:20])
    return n


def _plain(x):
    """An amount for an input box: 130003 -> '130003', 12.5 -> '12.50', None -> ''."""
    if x is None:
        return ""
    try:
        f = float(x)
    except (TypeError, ValueError):
        return ""
    if not math.isfinite(f):                                         # S557 B2
        return ""
    return ("%d" % f) if f == int(f) else ("%.2f" % f)


def _inr(x):
    if x is None:
        return "—"
    return "₹" + AR._inr(x)


def _norm_name(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def _yuvika(vendor):
    return bool(CP._hits(re.sub(r"\s+", " ", (vendor or "").lower()).strip(), ["yuvika"], whole=False))


def _quiet(fn, *a):
    """Call a helper that may flash (clinic_papers._accept): its flash is not relied on, and is taken back so it never
    appears later on another page. The result is read from the return value and the audit."""
    try:
        before = list(session.get("_flashes", []))
    except Exception:                                                # noqa: BLE001
        before = None
    r = fn(*a)
    try:
        if before is not None and session.get("_flashes", []) != before:
            session["_flashes"] = before
    except Exception:                                                # noqa: BLE001
        pass
    return r


def modes(db):
    try:
        return {r[0]: r[1] for r in db.execute("SELECT supplier_key, mode FROM challan_supplier")}
    except sqlite3.Error:
        return {}


def awaiting_challans(db, owner=True):
    """The challans waiting for their bill -- never the pharmacy lane (the Sanjeevni side keeps its own, D689 item 2), never
    a patient's paper (FIX1 C2: it is only in Kept apart), and a Personal one only for the owner (FIX1 C4, F-891)."""
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    return db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE b.doc_kind='challan' "
                      "AND COALESCE(b.challan_state,'awaiting')='awaiting' AND b.status<>'rejected' AND b.dup_of IS NULL "
                      "AND b.page_of IS NULL AND COALESCE(b.lane,'clinic')<>'pharmacy' "
                      "AND COALESCE(b.subgroup,'')<>'" + PATIENT + "'" + pers + " ORDER BY b.id").fetchall()


def awaited_open(db, owner):
    """S566 item 4: the open challans the Bills awaited page lists for this viewer -- every awaiting_challans row; a challan
    whose supplier is not read is in its own card ('Supplier not read'), never dropped. The menu's count is len() of this."""
    return list(awaiting_challans(db, owner))


def reading(db, bid):
    """Claude's reading of the paper (S550): rows with ok=1 only; None when there is none or the table is absent."""
    try:
        r = db.execute("SELECT doc_kind, data FROM claude_reading WHERE bill_id=? AND ok=1", (bid,)).fetchone()
    except sqlite3.Error:
        return None
    if not r:
        return None
    try:
        data = json.loads(r[1] or "{}")
    except (TypeError, ValueError):
        data = {}
    if not isinstance(data, dict):
        data = {}
    items = [i for i in (data.get("items") or []) if isinstance(i, dict) and str(i.get("name") or "").strip()]
    amt = data.get("total_amount")
    try:
        amt = float(amt) if (amt not in (None, "") and not isinstance(amt, bool)) else None
    except (TypeError, ValueError):
        amt = None
    if amt is not None and not math.isfinite(amt):                  # S557 B2 (S555 review N1): NaN / inf -> ignored
        amt = None
    dt = parse_date(data.get("bill_date")) or parse_date(data.get("date_as_read"))
    return {"doc_kind": r[0] or data.get("doc_kind"), "made_out_to": data.get("made_out_to"), "items": items,
            # S555 item 5: Claude's supplier, number, date and amount (vendor, bill_no, bill_date / date_as_read, total_amount)
            "supplier": str(data.get("vendor") or "").strip(), "number": str(data.get("bill_no") or "").strip(),
            "date": dt.isoformat() if dt else "", "amount": amt}


def items_of(db, b, rd=None):
    """[(name, qty, unit)] -- Claude's reading when there is one, else the paper's own items."""
    if rd and rd["items"]:
        return [(str(i.get("name")).strip(), i.get("qty"), str(i.get("unit") or "").strip()) for i in rd["items"]]
    return [(r[0], r[1], (r[2] or "")) for r in db.execute(
        "SELECT item_name, quantity, pack_size FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)) if r[0]]


def _qty(q):
    try:
        f = float(q)
        if not math.isfinite(f):                                     # S557 B2: a quantity that is not a number shows nothing
            return ""
        return ("%d" % f) if f == int(f) else ("%g" % f)
    except (TypeError, ValueError, OverflowError):
        return str(q) if q not in (None, "") else ""


def items_line(items, n=8):
    out = []
    for name, q, unit in items[:n]:
        qs = _qty(q)
        out.append(name + ((" × " + qs + ((" " + unit) if unit else "")) if qs else ""))
    return " · ".join(out) + (" · and %d more" % (len(items) - n) if len(items) > n else "")


def compare_items(bill_names, challan_names):
    """The bill's items against the ticked challans' items, on a normalised name."""
    b = {_norm_name(x) for x in bill_names if _norm_name(x)}
    c = {_norm_name(x) for x in challan_names if _norm_name(x)}
    n = len(b & c)
    return {"match": n, "of": len(c), "extra": len(b - c), "missing": len(c) - n,
            "text": "Items on the bill against the ticked challans: %d of %d match · %d extra on the bill · %d missing"
                    % (n, len(c), len(b - c), len(c) - n)}


# ---------------------------------------------------------------------------------------------- the flags (s3.6)
def misread_date(b, today=None):
    """S555 item 3: a bill_date before 2015-01-01, more than 7 days after the scan day, or more than 400 days before it.
    The scan day is the paper's created_at, else `today` (a year-old bill scanned late is a real paper, not a misread)."""
    bd = (b["bill_date"] or "").strip()
    if not bd:
        return False
    d = _iso(bd) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", bd) else None
    if d is None:
        return True
    today = today or _today()
    if d < datetime.date(2015, 1, 1):
        return True
    scan = _iso(b["created_at"]) or today
    return d > scan + datetime.timedelta(days=7) or (scan - d).days > 400


def nothing_read(db, b):
    return CP._is_blank(b, CP._items_text(db, b["id"]))


def _marks(db, bid=None):
    """{bill_id: {action: the newest audit id}} for the actions the desk's list reads."""
    acts = ("desk_saved", "d710_not_accepted", "desk_dup_same", "desk_dup_restored", "desk_restored", "desk_blank_restored",
            "desk_closed_kept")                               # S566: + the restores; + a closed challan kept as a record (FIX1)
    sql = "SELECT bill_id, action, MAX(id) FROM bill_audit WHERE action IN (?,?,?,?,?,?,?)"
    args = list(acts)
    if bid is not None:
        sql += " AND bill_id=?"
        args.append(bid)
    out = {}
    for b_, a, mx in db.execute(sql + " GROUP BY bill_id, action", args):
        out.setdefault(b_, {})[a] = mx
    return out


def held(b, mk):
    """The D710 hold: _accept wrote d710_not_accepted after the last desk Save, and no person has answered (no dup_flag)."""
    m = mk.get(b["id"], {})
    na = m.get("d710_not_accepted")
    return bool(na and na > m.get("desk_saved", 0) and not (b["dup_flag"] or "") and b["status"] == "draft"
                and _lane(b) == "clinic" and not b["dup_of"])


def hold_first(db, b):
    """The accepted paper a held one looks like a second scan of."""
    try:
        exact, _near = AR._dup_by_triple(db, b["id"], approved_only=True)
    except Exception:                                                # noqa: BLE001
        exact = None
    if exact:
        return exact
    r = db.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action='d710_not_accepted' ORDER BY id DESC LIMIT 1",
                   (b["id"],)).fetchone()
    try:
        st = json.loads(r[0] or "{}").get("same_as") if r else None
    except (TypeError, ValueError):
        st = None
    return db.execute("SELECT id, stamp_no FROM bills WHERE stamp_no=?", (st,)).fetchone() if st else None


def s441_aside(b, today=None, days=30):
    """An S441 set-aside (scan_checks_s441._set_aside): rejected as a sure double scan, in the last `days` days."""
    if not (b["status"] == "rejected" and b["dup_of"] and (b["dup_flag"] or "") == "yes"):
        return False
    if (b["approved_by"] or "") != S441_WHO:
        return False
    d = _iso(b["approved_at"])
    return bool(d and 0 <= ((today or _today()) - d).days <= days)


# ---------------------------------------------------------------------------------------------- the waiting list
def waiting(db, owner, today=None):
    """The papers waiting on the desk, newest first (s3.3). Never a pharmacy-lane paper; Personal only for the owner."""
    today = today or _today()
    floor = (_setting(db, "desk.floor", "") or "").strip()
    fl = floor or "9999-99-99"                        # no floor = nothing listed by the floor rules
    days = _int_setting(db, "desk.s441_days", 30)
    mk = _marks(db)
    sup_wait = {_key(c["vendor"]) for c in awaiting_challans(db, owner)} - {""}
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    rows = db.execute(
        "SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE COALESCE(b.lane,'clinic')<>'pharmacy' AND b.page_of IS NULL" + pers +
        " AND ((b.status<>'rejected' AND b.dup_of IS NULL AND ((COALESCE(b.lane,'clinic') IN ('clinic','other_doc') "
        "AND COALESCE(b.subgroup,'')='') OR substr(b.created_at,1,10)>=? "
        "OR b.status='draft' OR b.id IN (SELECT a.bill_id FROM bill_audit a WHERE a.action IN ('desk_restored','desk_blank_restored')))) "      # S566 items 1, 3
        "OR (b.status='rejected' AND b.dup_of IS NOT NULL AND b.dup_flag='yes' AND substr(b.created_at,1,10)>=?)) "
        "ORDER BY b.id DESC LIMIT 2000", (fl, fl)).fetchall()
    out = []
    for b in rows:
        if _lane(b) == "pharmacy":                    # an old row with no lane whose kind says pharmacy
            continue
        live = b["status"] != "rejected" and not b["dup_of"]
        lane, sg = _lane(b), (b["subgroup"] or "")
        if sg == PATIENT:                             # FIX1 C2: a patient's paper is in Kept apart only (Open B-____ still opens it)
            continue
        if _s674_listed(db, b):                       # S674: a listed supplier's paper is sorted on the Stationery page, never here
            continue
        after = (b["created_at"] or "")[:10] >= fl
        why = []
        if live and lane in ("clinic", "other_doc") and not sg:
            why.append("unsorted")
        if after and live:
            m = mk.get(b["id"], {})
            if not m.get("desk_saved"):
                if misread_date(b, today):
                    why.append("date")
                if nothing_read(db, b):
                    why.append("nothing")
                if (b["doc_kind"] or "") not in ("challan", "receipt", "statement") and _key(b["vendor"]) in sup_wait:      # S560
                    why.append("covers")
            if held(b, mk):
                why.append("hold")
        if live and _s566_restored(mk.get(b["id"], {})):            # S566 item 1: restored, not saved on the desk since
            why.append("restored")
        if live and not why and _s566_waits(b, owner, mk.get(b["id"], {})):    # S566 item 3: a waiting paper no other list shows
            why.append("waiting")
        if after and not live and s441_aside(b, today, days):
            m = mk.get(b["id"], {})
            if not (m.get("desk_dup_same") or m.get("desk_dup_restored")):
                why.append("s441")
        if why:
            out.append((b, why))
    return _s560_with_fixes(db, owner, out, today)      # S560 item 7: the papers to put right, on top


def _hint(db, b, why):
    fx = _s560_fix_hint(db, b, why)                                 # S560 item 7: the reason, in the list
    if fx:
        return fx
    if "restored" in why:                                           # S566 item 1
        return "restored — sort it"
    if why == ["waiting"]:                                          # S566 item 3
        return ("challan — supplier not read" if ((b["doc_kind"] or "") == "challan" and not _key(b["vendor"]))
                else "not accepted yet — check")
    if "hold" in why:
        f = hold_first(db, b)
        return "looks like a second scan of %s" % (_stamp(f) if f else "an accepted paper")
    if "s441" in why:
        f = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()
        return "set aside as a second scan of %s — check" % (_stamp(f) if f else "another paper")
    if "date" in why:
        return "date looks misread — check"
    if "nothing" in why:
        return "nothing could be read"
    if (b["doc_kind"] or "") == "challan":
        return "challan — bill awaited"
    if "covers" in why:
        return "a bill — this supplier has open challans"
    if _yuvika(b["vendor"]):
        return "Yuvika — always chosen by a person"
    s = CP.suggest(db, b["vendor"], CP._items_text(db, b["id"]), bool(b["bill_no"]), b["total_amount"] is not None)
    if not s:
        return "no suggestion"
    if s["kind"] == "sub":
        return "suggested: " + s["label"]
    if s["kind"] == "lane":
        return "looks like " + s["label"]
    return "see the note"


def list_json(db, owner, today=None):
    rows = waiting(db, owner, today)
    out = []
    for b, why in rows[:300]:
        out.append({"id": b["id"], "stamp": _stamp(b), "month": _ym_short(b["mo"]), "supplier": b["vendor"] or "",
                    "hint": _hint(db, b, why), "why": why})
    return {"ok": True, "papers": out, "total": len(rows)}


# ---------------------------------------------------------------------------------------------- one paper
def current_dest(b):
    """The paper's own current place, as a destination key ('' when it has none)."""
    lane, sg = _lane(b), (b["subgroup"] or "")
    if lane == "pharmacy":
        return "pharmacy"
    if sg in CLINIC_DEST + LEFT_ON_LANE + (PATIENT,):
        return sg
    if lane == "owner_expense":
        return "pe"
    if lane == "lab_purchase":
        return "lab"
    return ""


def supplier_note(db, key, name, mode, today=None, owner=True):
    today = today or _today()
    chs = [c for c in awaiting_challans(db, owner) if _key(c["vendor"]) == key] if key else []
    nm = name or "This supplier"
    if mode == "paid":
        return "%s is paid on its challan — the challan or estimate is the final paper." % nm
    if not chs and not mode:
        return ""
    oldest = _dm(chs[0]["bill_date"] or chs[0]["created_at"]) if chs else ""
    if mode == "monthly":
        n = len([c for c in chs if c["mo"] == today.strftime("%Y-%m")])
        return "%s bills every month — %d open challan%s this month." % (nm, n, "" if n == 1 else "s")
    if mode == "sometimes":
        return "%s bills now and then — %d open challan%s%s." % (nm, len(chs), "" if len(chs) == 1 else "s",
                                                                      (", oldest " + oldest) if chs else "")
    return "%s has %d open challan%s, oldest %s — set how it bills on Bills awaited." % (nm, len(chs), "" if len(chs) == 1 else "s", oldest)


def covers(db, b, mode, today=None, owner=True):
    """'This bill covers these challans' -- the desk's own rule: monthly -> the challans of the bill's month, pre-ticked;
    otherwise every awaiting challan of the supplier, unticked, oldest first, with its age. Never a patient's paper; a
    Personal challan only for the owner (FIX1 C2, C4)."""
    today = today or _today()
    key = _key(b["vendor"])
    if not key or (b["doc_kind"] or "") == "challan":
        return []
    chs = [c for c in awaiting_challans(db, owner) if _key(c["vendor"]) == key and c["id"] != b["id"]
           and c["status"] in ("draft", "captured")]
    tick = mode == "monthly"
    if tick:
        chs = [c for c in chs if c["mo"] == b["mo"]]
    chs.sort(key=lambda c: ((c["bill_date"] or c["created_at"] or "")[:10], c["id"]))
    out = []
    for c in chs:
        it = items_of(db, c, reading(db, c["id"]))
        out.append({"id": c["id"], "stamp": _stamp(c), "date": _dm(c["bill_date"] or c["created_at"]),
                    "age": CP._age_days(c, today), "n": len(it), "names": [x[0] for x in it], "ticked": tick,
                    "amount": c["total_amount"]})
    return out


OWN_LINE = ("This is your own name — the reader took the buyer. Type the supplier, or choose Miscellaneous if it is "
            "the clinic’s own paper.")


def own_name(db, vendor):
    """S555 item 4: the supplier box holds the owner's / clinic's own name -- the SAME own-name words clinic_papers.suggest()
    uses for its 'addressed to you' note (CP._words(db, 'own_name'), matched as suggest() matches them). No second list."""
    v = re.sub(r"\s+", " ", (vendor or "").lower()).strip()
    return bool(v and CP._hits(v, CP._words(db, "own_name"), whole=False))


def _numkey(s):
    return re.sub(r"\s+", "", str(s or "")).lower()


def claude_lines(db, b, rd, owner):
    """S555 items 4, 5: under each of the four boxes, Claude's value when it DIFFERS from the stored one (supplier: first two
    words; number: spaces and case ignored; date: as typed dates are read; amount: to the rupee) -- shown as "Claude read:
    <value> -- use it"; one tap fills the box and nothing is saved until Save. And the own-name line for the supplier box.
    Never for a pharmacy paper or a Personal paper to a manager; made_out_to is never shown here."""
    if _lane(b) == "pharmacy" or ((b["subgroup"] or "") == "personal" and not owner):
        return {}, ""
    own = own_name(db, b["vendor"])
    out = {}
    if rd:
        sup = rd.get("supplier") or ""
        if sup and not own_name(db, sup) and _key(sup) != _key(b["vendor"]):
            out["vendor"] = {"show": sup, "fill": sup}
        no = rd.get("number") or ""
        if no and _numkey(no) != _numkey(b["bill_no"]):
            out["bill_no"] = {"show": no, "fill": no}
        cd = parse_date(rd.get("date"))
        if cd and cd != (parse_date(b["bill_date"]) or _iso(b["bill_date"])):          # S557 B3 (review N2)
            out["date"] = {"show": cd.strftime("%d-%m-%Y"), "fill": cd.strftime("%d-%m-%Y")}
        ca = rd.get("amount")
        if ca is not None:
            sa = b["total_amount"]
            if sa is None or int(round(float(ca))) != int(round(float(sa))):
                out["amount"] = {"show": _inr(ca), "fill": _plain(ca)}
    return out, (OWN_LINE if own else "")


def _s557_machine():
    m = sys.modules.get("asset_machine")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s557_linked(db, b, owner):
    """S557 A6: 'Linked to <machine> as ...' for the Clinic-equipment destination note ('' when not linked / not mounted)."""
    try:
        m = _s557_machine()
        return m.linked_text(db, b["id"], owner) if m else ""
    except Exception:                                                # noqa: BLE001
        return ""


def _s557_add_to(db, b, owner, a, it1):
    """S557 A6: where '+ asset record' goes -- ('machine', bill id): a new machine pre-filled from the paper (asset_machine);
    else ('item', bill item id): the old bill-item bridge; else None. No url_for here (month_data is also read outside a request)."""
    if a or not owner or b["status"] != "approved":
        return None
    try:
        m = _s557_machine()
        if m:
            return ("machine", b["id"]) if m.can_from_paper(db, b, owner) else None
    except Exception:                                                # noqa: BLE001
        pass
    return ("item", it1[0]) if it1 else None


def paper_json(db, b, owner, today=None):
    today = today or _today()
    rd = reading(db, b["id"])
    it = items_of(db, b, rd)
    key = _key(b["vendor"])
    md = modes(db)
    mode = md.get(key, "")
    kind = b["doc_kind"] or ""
    kind_from = "paper" if kind in ("bill", "estimate", "challan", "receipt", "statement") else ""      # S560
    if not kind_from:
        kind = ""
        rk, rblock = _s560_claude_kind(db, b, rd)                   # S560 item 2
        if rk:
            kind, kind_from = rk, "Claude's reading"
        elif rblock:
            pass
        elif mode in ("monthly", "sometimes"):
            kind, kind_from = "challan", "this supplier's challans"
    hints, dest, dest_line = [], "", ""
    yuv = _yuvika(b["vendor"])
    cur = current_dest(b)
    patient = bool(rd and rd.get("made_out_to") == "patient")
    if (b["subgroup"] or "") == "xray":
        hints.append("X-ray film, size not known — choose the size.")
    if yuv:
        hints.append("Yuvika supplies the pharmacy and the clinic — a person always chooses." +
                     ((" Now: " + DEST_NAME.get(cur, cur) + ".") if cur else ""))
    else:
        if cur:
            dest, dest_line = cur, "Where it is now."
        elif patient:
            dest = PATIENT
        s = CP.suggest(db, b["vendor"], " ; ".join(x[0] for x in it), bool(b["bill_no"]), b["total_amount"] is not None)
        if s and s["kind"] == "sub" and s["value"] in CP.CONSUMABLE:
            if not dest and s["value"] in CONS:
                dest, dest_line = s["value"], "Suggested from %s — check before Save." % s["why"]
            elif s["value"] == "xray" and not dest:
                hints.append("Looks like X-ray film (%s) — choose the size." % s["why"])
        elif s and s["kind"] in ("sub", "lane"):
            hints.append("Looks like %s — from %s. A hint only: you choose." % (s["label"], s["why"]))
        elif s:
            hints.append(s["why"][0].upper() + s["why"][1:] + ".")
    if patient:
        hints.insert(0, "Claude read this as made out to a patient — check")
    mk = _marks(db, b["id"])
    flags = {"date": misread_date(b, today), "nothing": nothing_read(db, b), "hold": "", "s441": ""}
    if held(b, mk):
        f = hold_first(db, b)
        flags["hold"] = _stamp(f) if f else "an accepted paper"
    if b["status"] == "rejected" and b["dup_of"] and (b["dup_flag"] or "") == "yes":
        f = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()
        flags["s441"] = _stamp(f) if f else "another paper"
    can_page = (b["status"] in ("draft", "captured") and _lane(b) != "pharmacy" and not b["dup_of"] and not b["page_of"]
                and db.execute("SELECT 1 FROM bills WHERE page_of=? LIMIT 1", (b["id"],)).fetchone() is None)
    status = {"approved": "accepted", "draft": "not accepted yet", "captured": "filed", "rejected": "set aside"}.get(b["status"], b["status"])
    if (b["subgroup"] or "") == "clinic_equipment" and b["status"] == "draft":
        status = "Waiting for Dr Manoj's Save"
    if kind == "challan" and (b["challan_state"] or "") == "joined":
        status = "joined into its bill"
    name = b["vendor"] or ""
    claude, own_line = claude_lines(db, b, rd, owner)                # S555 items 4, 5
    return {"ok": True, "id": b["id"], "stamp": _stamp(b), "supplier": name, "bill_no": b["bill_no"] or "",
            "date": _dmy(b["bill_date"]) if b["bill_date"] else "", "amount": _plain(b["total_amount"]),
            "claude": claude, "own_line": own_line,
            "scanned": _dmy(b["created_at"]), "month": _ym_short(b["mo"]),
            "file": url_for("bill_file", bid=b["id"]) if b["source_stored"] else "",
            "items": ("Read: " + items_line(it)) if it else "No items read.", "bill_names": [x[0] for x in it],
            "kind": kind, "kind_from": kind_from, "dest": dest, "dest_line": dest_line, "current": DEST_NAME.get(cur, ""),
            "who": "bhawna" if (_col(b, "pe_who") or "") == "bhawna" else "mk", "hints": hints,
            "supplier_note": _s568_note(db, key, supplier_note(db, key, name, mode, today, owner), today), "mode": mode,      # S568 item 6
            "covers": covers(db, b, mode, today, owner), "flags": flags, "can_page": bool(can_page),
            "status": status, "lane": AR._lane_word_s555(b), "linked": _s557_linked(db, b, owner),      # S557 B1, A6
            "owner_line": ("Waiting for Dr Manoj's Save" if (not owner and (b["subgroup"] or "") == "clinic_equipment"
                                                            and b["status"] == "draft") else ""),
            **_s560_paper(db, b, owner, rd, today), **_s568_paper(db, b, owner, rd),      # S560: paid state ...; S568: the stationery panel
            **_s571_paper(db, b, owner),                                                     # S571: the battery offer (nothing without batteries.py)
            **_s634_paper(db, b, owner, rd, dest)}                                           # S634: the Procedure room panel (nothing without procroom.py)


def _visible(b, owner):
    """May this person open this paper on the desk? Never a pharmacy paper; Personal only for the owner."""
    if not b:
        return "There is no such paper."
    if _lane(b) == "pharmacy":
        return "%s is a pharmacy paper — the Sanjeevni side keeps it; it is not opened on the desk." % _stamp(b)
    if (b["subgroup"] or "") == "personal" and not owner:
        return "Personal papers are the owner's alone."
    return ""


# ---------------------------------------------------------------------------------------------- the Save (one transaction)
def _relane(db, b, to, status0):
    """The desk's own lane helper (not bill_lane): it may move an APPROVED paper off the clinic lane (the owner's widening).
    Kind and status from _lane_kind_status; approved_by / approved_at kept as history; audited as 'relane'."""
    frm = _lane(b)
    if to == frm:
        return False
    if frm == "pharmacy":
        raise DeskError("A pharmacy paper is never moved off the pharmacy lane from the desk.")
    kind, status = AR._lane_kind_status(to)
    if to == "pharmacy" and (b["doc_kind"] or "") == "challan":
        kind = "Challan"                              # as the intake does: the Sanjeevni register does not take it
    db.execute("UPDATE bills SET lane=?, kind=?, status=? WHERE id=?", (to, kind, status, b["id"]))
    AR._audit_bill(db, b["id"], "relane", {"from": frm, "to": to, "status_from": status0, "status": status, "via": "desk"})
    return True


def _set_sub(db, bid, to, status0):
    b = _row(db, bid)
    frm = b["subgroup"] or ""
    if (to or "") == frm:
        return False
    db.execute("UPDATE bills SET subgroup=? WHERE id=?", (to or None, bid))
    AR._audit_bill(db, bid, "subgroup", {"from": frm, "to": to or "", "status_from": status0, "status": b["status"], "via": "desk"})
    return True


def _fields(db, b, p):
    """The header read on the paper, corrected with bill_edit's normalisation -- never by deleting its items."""
    new = {}
    if "vendor" in p:
        new["vendor"] = (str(p.get("vendor") or "")).strip() or None
    if "bill_no" in p:
        new["bill_no"] = (str(p.get("bill_no") or "")).strip() or None
    if "bill_date" in p:
        new["bill_date"] = typed_date(p.get("bill_date"), b["bill_date"])          # S555 item 2: refused if not understood
    if "total_amount" in p:
        new["total_amount"] = _amount(p.get("total_amount"))
    ch = {k: v for k, v in new.items() if v != b[k]}
    if not ch:
        return False
    db.execute("UPDATE bills SET %s WHERE id=?" % ",".join("%s=?" % k for k in ch), tuple(ch.values()) + (b["id"],))
    AR._audit_bill(db, b["id"], "desk_fields", {"from": {k: b[k] for k in ch}, "to": ch})
    AR._set_late(db, b["id"])
    return True


def _doc_kind(db, b, k, mode):
    if k not in ("bill", "estimate", "challan", "receipt", "statement"):      # S560
        return False
    old, st_old = (b["doc_kind"] or ""), b["challan_state"]
    if k == "challan":
        st = "final" if mode == "paid" else (st_old if (old == "challan" and st_old in ("awaiting", "final", "closed")) else "awaiting")
    else:
        st = None
    # FIX1 C3: an ACCEPTED paper saved as a challan that waits goes back to draft (clinic) / its lane's status, so it can be
    # joined to its bill (_page_ok refuses an approved page) -- this also frees a challan the old heal had accepted.
    reopen = k == "challan" and st == "awaiting" and b["status"] == "approved"
    if old == k and st == st_old and not reopen:
        return False
    if old != k or st != st_old:
        db.execute("UPDATE bills SET doc_kind=?, challan_state=? WHERE id=?", (k, st, b["id"]))
        AR._audit_bill(db, b["id"], "doc_kind", {"from": old, "to": k, "challan_state_from": st_old, "challan_state": st, "via": "desk"})
    if reopen:
        lane = _lane(b)
        back_to = "draft" if lane == "clinic" else AR._lane_kind_status(lane)[1]
        db.execute("UPDATE bills SET status=? WHERE id=?", (back_to, b["id"]))
        AR._audit_bill(db, b["id"], "desk_challan_reopened", {"status_from": b["status"], "status": back_to, "lane": lane,
                                                              "challan_state": st, "via": "desk"})
    return True


def _challan_waits(b):
    return (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "awaiting") != "final"


def accept_by_person(db, bid, who):
    """D710 'Not the same -- keep': accepted by a person's answer, without the triple check (the app's approve steps)."""
    b = _row(db, bid)
    if not b or _lane(b) != "clinic" or b["status"] != "draft" or _challan_waits(b):
        return False
    db.execute("UPDATE bills SET status='approved', approved_by=?, approved_at=? WHERE id=?", (who, AR._now_ist(), bid))
    try:
        AR.upsert_vendor(db, b["vendor"], b["vendor_phone"], b["vendor_email"])
        for r in db.execute("SELECT id FROM assets WHERE bill_id=?", (bid,)).fetchall():
            AR._backfill_asset_from_bill(db, r[0], bid)
    except Exception:                                                # noqa: BLE001
        pass
    AR._audit_bill(db, bid, "d710_accepted_by_person", {"by": who, "group": b["subgroup"]})
    return True


def _by_stamp(db, no):
    no = re.sub(r"\s+", "", str(no or "")).upper()
    if not no:
        return None
    if no.isdigit():
        no = "B-%04d" % int(no)
    return db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE upper(b.stamp_no)=?", (no,)).fetchone()


def save(db, bid, p, today=None):
    """ONE Save of the desk: fields, kind, destination, joins, Dr MK / Dr Bhawna, a flag's answer. No commit here: the
    route commits once, or rolls everything back. Returns a dict(message=...)."""
    owner, who = _owner(), _who()
    b = _row(db, bid)
    err = _visible(b, owner)
    if err:
        raise DeskError(err, 403 if "owner's alone" in err else (404 if not b else 400))
    st = _stamp(b)
    if b["page_of"]:
        raise DeskError("%s is a page of another paper — open that paper." % st)
    status0 = b["status"]
    flag = str(p.get("flag") or "").strip()
    dest = str(p.get("dest") or "").strip()
    aside = b["status"] == "rejected" and b["dup_of"] and (b["dup_flag"] or "") == "yes"
    if b["status"] == "rejected" and not aside:
        raise DeskError("%s is set aside. Press Restore on it first, then Save." % st)      # S563 F-902
    person_ok = False
    msgs = []
    if aside:                                                       # an S441 set-aside, answered both ways
        first = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()
        fst = _stamp(first) if first else "another paper"
        if flag == "same":
            AR._audit_bill(db, bid, "desk_dup_same", {"of": b["dup_of"], "via": "desk"})
            AR._audit_bill(db, bid, "desk_saved", {"answer": "same", "via": "desk"})
            return {"message": "%s stays set aside as a second scan of %s." % (st, fst)}
        if flag != "restore":
            raise DeskError("First answer: is %s the same paper as %s?" % (st, fst))
        _k, back_to = AR._lane_kind_status(_lane(b))
        db.execute("UPDATE bills SET status=?, dup_of=NULL, dup_flag='no', reject_reason=NULL WHERE id=?", (back_to, bid))
        AR._audit_bill(db, bid, "desk_dup_restored", {"dup_of": b["dup_of"], "dup_why": b["dup_why"], "status": b["status"],
                                                      "reject_reason": b["reject_reason"], "to": back_to, "via": "desk"})
        msgs.append("%s is a paper of its own again." % st)
        b = _row(db, bid)
        if not dest and not p.get("page_of") and not p.get("blank"):
            AR._audit_bill(db, bid, "desk_saved", {"answer": "restore", "via": "desk"})
            return {"message": msgs[0] + " It waits on the desk to be sorted."}
    elif held(b, _marks(db, bid)):                                  # the D710 hold, answered both ways
        first = hold_first(db, b)
        fst = _stamp(first) if first else "an accepted paper"
        if flag == "same":
            if not first:
                raise DeskError("The accepted paper it matches could not be found — correct what was read instead.")
            AR._audit_bill(db, bid, "desk_saved", {"answer": "same", "via": "desk"})
            kept = AR._mark_dup(db, bid, first, "desk")
            if kept == bid:                                              # S651 (D761): the clearer scan kept
                return {"message": "%s is kept; %s is set aside as its second scan." % (st, fst)}
            return {"message": "%s is set aside as a second scan of %s." % (st, fst)}
        if flag != "keep":
            raise DeskError("First answer: is %s a second scan of %s?" % (st, fst))
        db.execute("UPDATE bills SET dup_flag='no' WHERE id=?", (bid,))
        AR._audit_bill(db, bid, "not_duplicate", {"cand": first["id"] if first else None, "via": "desk"})
        person_ok = True
        b = _row(db, bid)
    if p.get("blank"):                                              # Blank -- discard: marked, never deleted
        AR._audit_bill(db, bid, "desk_saved", {"blank": True, "via": "desk"})
        db.execute("UPDATE bills SET status='rejected', reject_reason=?, approved_by=?, approved_at=? WHERE id=?",
                   ("blank — discarded on the sorting desk", who, AR._now_ist(), bid))
        AR._audit_bill(db, bid, "desk_blank", {"status_from": b["status"], "lane": _lane(b), "via": "desk"})
        return {"message": "%s is discarded as blank (kept on record)." % st}
    pg = str(p.get("page_of") or "").strip()
    if pg:                                                          # a page of another paper -> the shared join
        head = _by_stamp(db, pg)
        if not head:
            raise DeskError("There is no paper numbered %s." % pg.upper())
        if head["id"] == bid:
            raise DeskError("A paper cannot be a page of itself.")
        herr = _visible(head, owner)
        if herr:
            raise DeskError(herr, 403 if "owner's alone" in herr else 400)
        if not CP._head_ok(head):
            raise DeskError("%s cannot take pages: a rejected paper, a duplicate or itself a page." % _stamp(head))
        if not CP._page_ok(db, b, head):
            raise DeskError("%s cannot become a page: an approved paper, a duplicate, or one that has pages of its own." % st)
        AR._audit_bill(db, bid, "desk_saved", {"page_of": head["id"], "via": "desk"})
        joined, loose = CP.join_pages(db, head, [b], who)
        if not joined:
            raise DeskError("%s could not be joined into %s." % (st, _stamp(head)))
        return {"message": "%s is joined into %s.%s" % (st, _stamp(head), " (Not in one PDF: a photo, not a PDF.)" if loose else "")}
    dest, s560 = _s560_pre(db, b, p, dest, owner, today)           # S560: a receipt / statement is filed with the bill it pays
    if dest not in DEST_NAME:
        raise DeskError("Choose where it goes.")
    if dest == "personal" and not owner:
        raise DeskError("Personal papers are the owner's alone.", 403)
    k_new = str(p.get("kind") or "").strip()
    AR._audit_bill(db, bid, "desk_saved", {"dest": dest, "kind": k_new or None, "via": "desk", "s560": 1})   # first: a hold written below is newer
    _fields(db, b, p)
    b = _row(db, bid)
    mode = modes(db).get(_key(b["vendor"]), "")
    _doc_kind(db, b, k_new, mode)
    b = _row(db, bid)
    lane = _lane(b)
    accept = False
    if dest in CLINIC_DEST:
        _relane(db, b, "clinic", status0)
        _set_sub(db, bid, dest, status0)
        b = _row(db, bid)
        if dest == "clinic_equipment" and b["kind"] != "Asset":
            db.execute("UPDATE bills SET kind='Asset' WHERE id=?", (bid,))
            AR._audit_bill(db, bid, "kind", {"from": b["kind"], "to": "Asset", "via": "desk"})
        accept = not (dest == "clinic_equipment" and not owner)
        if dest == "clinic_equipment" and not owner and b["status"] == "draft":
            msgs.append("Waiting for Dr Manoj's Save.")
    elif dest in LEFT_ON_LANE:
        if lane not in CP.SORT_LANES:
            _relane(db, b, "other_doc", status0)
        _set_sub(db, bid, dest, status0)
        accept = True                                               # as set_group does: a clinic draft is accepted
    elif dest == "pe":
        _relane(db, b, "owner_expense", status0)
        sg = _row(db, bid)["subgroup"] or ""
        if sg and sg not in SECTION_KEEP:
            _set_sub(db, bid, None, status0)
        val = "bhawna" if str(p.get("who") or "").strip().lower() == "bhawna" else None
        if (_col(_row(db, bid), "pe_who") or None) != val:
            db.execute("UPDATE bills SET pe_who=? WHERE id=?", (val, bid))
            AR._audit_bill(db, bid, "pe_who", {"to": val or "mk", "via": "desk"})
    elif dest == "pharmacy":
        _relane(db, b, "pharmacy", status0)
        _set_sub(db, bid, None, status0)
    elif dest == "lab":
        _relane(db, b, "lab_purchase", status0)
        _set_sub(db, bid, None, status0)
    elif dest == PATIENT:
        _relane(db, b, "other_doc", status0)
        _set_sub(db, bid, PATIENT, status0)
    accept = accept and not s560.get("no_accept")                 # S560: a receipt / statement is never accepted as a bill
    b = _row(db, bid)
    if (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "") == "closed" and b["status"] == "draft":   # S566 FIX1
        AR._audit_bill(db, bid, "desk_closed_kept", {"via": "desk"})
        msgs.append("%s is a closed challan — kept as a record; no bill will come." % st)
    elif accept and _lane(b) == "clinic" and b["status"] == "draft":
        if _challan_waits(b):
            msgs.append("A challan: filed, waiting for its bill (Bills awaited).")
        elif person_ok:
            accept_by_person(db, bid, who)
        elif not _quiet(CP._accept, db, bid, who):
            f = hold_first(db, b)
            msgs.append("NOT accepted: the same supplier, number and amount are already accepted as %s — it waits on the desk."
                        % (_stamp(f) if f else "another paper"))
    joins = []
    for x in (p.get("joins") or []):
        if str(x).isdigit() and int(x) not in joins:
            joins.append(int(x))
    if joins:
        b = _row(db, bid)
        if (b["doc_kind"] or "") == "challan":
            raise DeskError("A challan cannot cover other challans — choose Bill.")
        if not CP._head_ok(b):
            raise DeskError("%s cannot take pages." % st)
        # FIX1 C4: the same list the covers box shows this person -- a Personal challan is never joinable by a non-owner
        offered = {c["id"]: c for c in awaiting_challans(db, owner) if _key(c["vendor"]) == _key(b["vendor"]) and c["id"] != bid}
        pages = []
        for j in joins:
            if j not in offered:
                raise DeskError("Challan #%d is not an open challan of this supplier." % j)
            pages.append(db.execute("SELECT b.* FROM bills b WHERE b.id=?", (j,)).fetchone())
        done, _loose = CP.join_pages(db, _row(db, bid), pages, who)
        if len(done) != len(pages):
            raise DeskError("A ticked challan could not be joined (accepted, or already a page). Nothing was saved.")
        msgs.append("%d challan%s joined." % (len(done), "" if len(done) == 1 else "s"))
    msgs += _s560_post(db, bid, p, s560, status0)                   # S560: filed, the payment, the construction tick
    msgs += _s568_post(db, bid, p, dest)                            # S568 items 3, 6: the stationery lines; the mixed mark
    msgs += _s634_post(db, bid, p, dest)                            # S634: the Procedure room lines (procroom.py)
    b = _row(db, bid)
    return {"message": "%s → %s.%s" % (st, DEST_NAME[dest], (" " + " ".join(msgs)) if msgs else ""),
            "status": b["status"]}


# ---------------------------------------------------------------------------------------------- Bills awaited (s3.4)
def challan_amber(mode, c_month, age_days, has_bill, today, amber_days):
    """Monthly: amber when no bill of the challan's month by the 10th of the next month. Now and then: never. Paid: never
    waits. Any other supplier: today's rule, after `amber_days` days."""
    if mode in ("sometimes", "paid"):
        return False
    if mode == "monthly":
        if has_bill:
            return False
        try:
            nxt = _ym_shift(c_month, 1)
            return today > datetime.date(int(nxt[:4]), int(nxt[5:7]), 10)
        except (TypeError, ValueError):
            return False
    return age_days >= amber_days


def _bills_by_month(db):
    out = set()
    for r in db.execute("SELECT b.vendor, " + CP.MONTH_OF + " FROM bills b WHERE COALESCE(b.doc_kind,'bill')<>'challan' "
                        "AND b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL AND COALESCE(b.lane,'clinic')<>'pharmacy'"):
        out.add((_key(r[0]), r[1]))
    return out


def awaited(db, owner, today=None):
    today = today or _today()
    md = modes(db)
    names = {}
    try:
        for r in db.execute("SELECT supplier_key, name FROM challan_supplier"):
            names[r[0]] = r[1]
    except sqlite3.Error:
        pass
    amber_days = CP._amber_days(db)
    bills = _bills_by_month(db)
    cards = {}
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"

    def card(key, vendor):
        if key not in cards:
            cards[key] = {"key": key, "name": (names.get(key) or vendor or key) if key else "Supplier not read",
                          "mode": md.get(key, "") if key else "", "rows": [],
                          "unpaid": [], "what": set(), "n_wait": 0, "noread": not key}      # S566 item 4: its own card
        return cards[key]
    for c in awaited_open(db, owner):                               # S566 item 4: the list the menu counts
        key = _key(c["vendor"])                                     # '' = supplier not read: its own card, never dropped
        cd = card(key, c["vendor"])
        mode = cd["mode"]
        age = CP._age_days(c, today)
        it = items_of(db, c, reading(db, c["id"]))
        cd["rows"].append({"id": c["id"], "stamp": _stamp(c), "date": _dm(c["bill_date"] or c["created_at"]),
                           "age": "%d day%s" % (age, "" if age == 1 else "s"), "items": items_line(it) or "no items read",
                           "amber": challan_amber(mode, c["mo"], age, (key, c["mo"]) in bills, today, amber_days),
                           "month": c["mo"], "final": False})
        cd["n_wait"] += 1
        cd["what"].add(AR._lane_word_s555(c) + ((" · " + CP.SUB.get(c["subgroup"], "")) if c["subgroup"] else ""))      # S557 B1
    since = (today - datetime.timedelta(days=60)).isoformat()
    for f in db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE b.doc_kind='challan' AND b.challan_state='final' "
                        "AND b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL AND COALESCE(b.lane,'clinic')<>'pharmacy'" + pers +
                        " AND COALESCE(b.subgroup,'')<>'" + PATIENT + "' ORDER BY b.id"):
        key = _key(f["vendor"])
        if not key or (f["paid_on"] and (f["paid_on"] or "") < since):
            continue
        cd = card(key, f["vendor"])
        it = items_of(db, f, reading(db, f["id"]))
        cd["rows"].append({"id": f["id"], "stamp": _stamp(f), "date": _dm(f["bill_date"] or f["created_at"]),
                           "age": ("paid " + _dm(f["paid_on"])) if f["paid_on"] else "not yet paid",
                           "items": (items_line(it) or "no items read") + ((" · " + _inr(f["total_amount"])) if f["total_amount"] is not None else ""),
                           "amber": False, "month": f["mo"], "final": True})
        if not f["paid_on"]:
            cd["unpaid"].append({"id": f["id"], "stamp": _stamp(f), "amount": f["total_amount"]})
        cd["what"].add(AR._lane_word_s555(f) + ((" · " + CP.SUB.get(f["subgroup"], "")) if f["subgroup"] else ""))      # S557 B1
    out = []
    for cd in cards.values():
        m = cd["mode"]
        n = cd["n_wait"]
        if m == "monthly":
            nm = len([r for r in cd["rows"] if not r["final"] and r["month"] == today.strftime("%Y-%m")])
            foot = "%d open challan%s this month · amounts come with the month’s bill" % (nm, "" if nm == 1 else "s")
        elif m == "sometimes":
            foot = "%d open challan%s · quantities counted on the month page; money when the bill comes" % (n, "" if n == 1 else "s")
        elif m == "paid":
            foot = "Paid on challans and estimates — no bill ever"
        else:
            foot = "%d open challan%s · set how this supplier bills" % (n, "" if n == 1 else "s")
        if cd["noread"]:                                            # S566 item 4
            foot = "%d challan%s with no supplier read · open each on the desk and type the supplier" % (n, "" if n == 1 else "s")
        cd["foot"] = foot
        cd["rule"] = MODE_RULE[m] if m else (MODE_RULE[""] % amber_days)
        cd["what"] = " / ".join(sorted(x for x in cd["what"] if x))
        out.append(cd)
    out.sort(key=lambda c: (c["noread"], c["name"].lower()))      # S566: 'Supplier not read' last
    return out, amber_days


def set_mode(db, key, mode, name=""):
    """One tap on a supplier's card. Paid on challan turns its awaiting challans final (each audited) and accepts a sorted
    clinic one like a bill. No commit."""
    if mode not in dict(MODES):
        raise DeskError("Choose how this supplier bills.")
    old = modes(db).get(key, "")
    db.execute("INSERT INTO challan_supplier(supplier_key, name, mode, set_by, set_at) VALUES(?,?,?,?,?) "
               "ON CONFLICT(supplier_key) DO UPDATE SET mode=excluded.mode, name=COALESCE(challan_supplier.name, excluded.name), "
               "set_by=excluded.set_by, set_at=excluded.set_at", (key, name or None, mode, _who(), AR._now_ist()))
    _audit_desk(db, "challan_mode", {"supplier": key, "from": old, "to": mode})
    n = 0
    if mode == "paid":
        for c in awaiting_challans(db, _owner()):                    # a manager's tap never touches a Personal paper
            if _key(c["vendor"]) != key:
                continue
            db.execute("UPDATE bills SET challan_state='final' WHERE id=?", (c["id"],))
            AR._audit_bill(db, c["id"], "challan_final", {"via": "desk", "mode": "paid"})
            n += 1
            if _lane(c) == "clinic" and c["status"] == "draft" and (c["subgroup"] or ""):
                _quiet(CP._accept, db, c["id"], _who())
    return n


def note_paid(db, bid, day, amount):
    """Paid on challan: the payment recorded on the paper itself (bills.paid_on, paid_amount; audited on the bill)."""
    b = _row(db, bid)
    if not b or (b["doc_kind"] or "") != "challan" or (b["challan_state"] or "") != "final":
        raise DeskError("Only a paid-on-challan paper takes its payment here.")
    if (b["subgroup"] or "") == "personal" and not _owner():
        raise DeskError("Personal papers are the owner's alone.", 403)
    if not str(day or "").strip():
        raise DeskError("Type the day it was paid.")
    d = typed_date(day)                                              # S555 item 2: refused with one plain line
    amt = _amount(amount)
    if not amt or amt <= 0:
        raise DeskError("Type the amount paid.")
    db.execute("UPDATE bills SET paid_on=?, paid_amount=? WHERE id=?", (d, amt, bid))
    AR._audit_bill(db, bid, "paid", {"from_on": b["paid_on"], "from_amount": b["paid_amount"], "on": d, "amount": amt, "via": "desk"})
    return d, amt


# ---------------------------------------------------------------------------------------------- Implant stock ledger (s3.5)
def ledger(db, today=None):
    """{supplier key: dict(name, rows, owed, paid, balance, checked)} -- the implant stock papers and the payments."""
    sups = {}

    def sup(key, name):
        if key not in sups:
            sups[key] = {"key": key, "name": name or key, "rows": [], "owed": 0.0, "paid": 0.0, "checked": ""}
        return sups[key]
    rows = db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE b.subgroup='implant_stock' "
                      "AND (b.status<>'rejected' OR b.challan_state='joined') AND COALESCE(b.lane,'clinic')<>'pharmacy' "
                      "ORDER BY COALESCE(NULLIF(b.bill_date,''), substr(b.created_at,1,10)), b.id").fetchall()
    for b in rows:
        key = _key(b["vendor"])
        if not key:
            continue
        s = sup(key, b["vendor"])
        dk, cs = (b["doc_kind"] or ""), (b["challan_state"] or "")
        it = items_line(items_of(db, b, reading(db, b["id"])))
        owed = paid = None
        if dk == "challan" and cs == "joined":
            head = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["challan_of"],)).fetchone() if b["challan_of"] else None
            kind, it = "Challan", (it + " · " if it else "") + ("joined into " + _stamp(head) if head else "joined")
        elif dk == "challan" and cs == "final":
            kind, owed, paid = "Challan (final)", b["total_amount"], _col(b, "paid_amount")
        elif dk == "challan" and cs == "closed":                   # FIX1 N5: a closed challan is never owed
            kind = "Challan (closed)"
        elif dk == "challan":
            kind, owed = "Challan", b["total_amount"]
        elif dk in ("receipt", "statement"):                         # S560: never owed -- the bill is
            kind = "Receipt" if dk == "receipt" else "Statement"
        else:
            kind, owed = ("Estimate slip" if dk == "estimate" else "Bill"), b["total_amount"]
        s["rows"].append({"sort": (b["bill_date"] or b["created_at"] or "")[:10], "d": _dm(b["bill_date"] or b["created_at"]),
                          "p": _stamp(b), "bid": b["id"], "k": kind, "i": it or "—", "o": owed, "pd": paid, "pay": None})
        s["owed"] += owed or 0
        s["paid"] += paid or 0
    _s560_ledger(db, rows, sups)                                    # S560 item 5
    try:
        pays = db.execute("SELECT * FROM implant_payment ORDER BY day, id").fetchall()
        checks = {r[0]: r[1] for r in db.execute("SELECT supplier_key, MAX(upto) FROM implant_check GROUP BY supplier_key")}
    except sqlite3.Error:
        pays, checks = [], {}
    for p in pays:
        if p["supplier_key"] not in sups:
            continue
        s = sups[p["supplier_key"]]
        live = not p["voided_at"]
        s["rows"].append({"sort": p["day"], "d": _dm(p["day"]), "p": "—", "bid": None,
                          "k": "Payment" if live else "Payment (voided)",
                          "i": p["how"] + ((" · against " + p["against"]) if p["against"] else "") + ("" if live else " · voided by %s" % (p["voided_by"] or "")),
                          "o": None, "pd": p["amount"] if live else None, "pay": p["id"] if live else None})
        if live:
            s["paid"] += p["amount"] or 0
    for k, s in sups.items():
        s["rows"].sort(key=lambda r: (r["sort"] or "", 0 if r["bid"] else 1))
        s["balance"] = s["owed"] - s["paid"]
        s["checked"] = ("checked up to " + _dmy(checks[k])) if checks.get(k) else "not yet checked against a statement"
    return sups


# ---------------------------------------------------------------------------------------------- The month (s3.7)
def month_data(db, ym, owner, today=None):
    """The month, section by section. Consumables: the same papers as /papers/month (clinic lane, draft or approved, not a
    challan, the month = MONTH_OF), plus a final challan's amount; an awaiting challan counts by quantity only."""
    today = today or _today()
    secs = []
    cache = {}
    pm560 = paid_map(db)                                             # S560

    def early_rates(rsubs, rlanes):
        """FIX1 N6: 'Rate before' = the item's last rate in an earlier month, read ONLY from the consumables groups (for a
        consumables row) or the row's own section (for any other) -- never Personal, a personal expense or a patient's paper."""
        ck_ = (rsubs, rlanes)
        if ck_ not in cache:
            early = {}
            for r in db.execute("SELECT bi.item_name, bi.rate, " + CP.MONTH_OF + " AS mo, b.bill_date, bi.id FROM bill_items bi JOIN bills b ON b.id=bi.bill_id "
                                "WHERE bi.rate IS NOT NULL AND b.status<>'rejected' AND b.dup_of IS NULL "
                                "AND COALESCE(b.lane,'clinic') IN (" + ",".join("?" * len(rlanes)) + ") "
                                "AND b.subgroup IN (" + ",".join("?" * len(rsubs)) + ") AND " + CP.MONTH_OF + "<?",
                                rlanes + rsubs + (ym,)):
                k = _norm_name(r[0])
                cand = (r[2] or "", r[3] or "", r[4])
                if k and (k not in early or cand > early[k][0]):
                    early[k] = (cand, r[1])
            cache[ck_] = early
        return cache[ck_]
    for key, name, subs in MONTH_SECTIONS:
        if key in ("procedure", "xray", "others", "stationery"):          # S568
            early = early_rates(CONS + ("xray",), ("clinic",))
        elif key == "construction":
            early = early_rates(subs, ("clinic", "other_doc"))
        else:
            early = early_rates(subs, ("clinic",))
        ph = ",".join("?" * len(subs))
        lanes = _s566_lanes(key)
        money, finals = _s566_paid_rows(db, key, subs, ym)           # S566 item 6: the one selection month_total reads too
        waits = db.execute("SELECT b.* FROM bills b WHERE " + lanes + " AND b.dup_of IS NULL AND b.page_of IS NULL AND b.doc_kind='challan' "
                           "AND COALESCE(b.challan_state,'awaiting')='awaiting' AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.id",
                           subs + (ym,)).fetchall()
        paid_rows = list(money) + list(finals)
        total = _s566_total(paid_rows)                               # S566 item 6: the one sum
        nb = len([b for b in money if (b["doc_kind"] or "bill") != "estimate"])
        ne = len([b for b in money if (b["doc_kind"] or "") == "estimate"])
        nc = len(finals) + len(waits)
        if key == "xray":
            n_s = len([b for b in paid_rows + list(waits) if b["subgroup"] == "xray_small"])
            n_l = len([b for b in paid_rows + list(waits) if b["subgroup"] == "xray_11x14"])
            n_u = len([b for b in paid_rows + list(waits) if b["subgroup"] == "xray"])
            papers = "%d bill%s · small film %d · 11 × 14 %d%s" % (nb, "" if nb == 1 else "s", n_s, n_l, (" · size not known %d" % n_u) if n_u else "")
        else:
            papers = "%d bill%s · %d estimate slip%s · %d challan%s" % (nb, "" if nb == 1 else "s", ne, "" if ne == 1 else "s", nc, "" if nc == 1 else "s")
        if key == "construction":
            papers += " · clinic / MK not decided"
        papers += _s560_month_bits(db, key, paid_rows, pm560)          # S560
        noamt = len([b for b in paid_rows if b["total_amount"] is None])
        items = {}
        paid_ids = {b["id"] for b in paid_rows}
        for b in paid_rows + list(waits):
            for r in db.execute("SELECT item_name, quantity, rate FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)):
                k = _norm_name(r[0])
                if not k:
                    continue
                it = items.setdefault(k, {"n": r[0], "q": 0.0, "hasq": False, "r": None, "rk": None})
                if r[1] is not None:
                    it["q"] += r[1]
                    it["hasq"] = True
                if r[2] is not None and b["id"] in paid_ids:
                    rk = ((b["bill_date"] or ""), b["id"])
                    if it["rk"] is None or rk >= it["rk"]:
                        it["r"], it["rk"] = r[2], rk
        rows = []
        for k, it in sorted(items.items(), key=lambda kv: kv[1]["n"].lower()):
            e = early.get(k)
            rows.append({"n": it["n"], "q": _qty(it["q"]) if it["hasq"] else "—", "r": _inr(it["r"]) if it["r"] is not None else "—",
                         "b": ("%s (%s)" % (_inr(e[1]), _ym_short(e[0][0]).split(" ")[0])) if e else "—"})
        eq = []
        if key == "clinic_equipment":
            for b in paid_rows:
                a = db.execute("SELECT id, name FROM assets WHERE bill_id=? ORDER BY id LIMIT 1", (b["id"],)).fetchone()
                it1 = db.execute("SELECT id FROM bill_items WHERE bill_id=? ORDER BY id LIMIT 1", (b["id"],)).fetchone()
                eq.append({"bid": b["id"], "stamp": _stamp(b), "vendor": b["vendor"] or "", "amount": b["total_amount"],
                           "asset": a["id"] if a else None, "asset_name": a["name"] if a else "",
                           "add": (it1[0] if (it1 and owner and b["status"] == "approved" and not a) else None),
                           "add_to": _s557_add_to(db, b, owner, a, it1),                         # S557 A6
                           "status": b["status"]})
        secs.append({"key": key, "name": name, "papers": papers, "total": total, "noamt": noamt, "rows": rows, "eq": eq,
                     "money_ids": [b["id"] for b in paid_rows], "final_ids": [b["id"] for b in finals]})
    base = ("FROM bills b WHERE b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL AND " + CP.MONTH_OF + "=?")
    one = lambda sql, *a: db.execute("SELECT COUNT(*) " + base + sql, (ym,) + a).fetchone()[0]     # noqa: E731
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    pe_all = one(" AND b.lane='owner_expense'" + pers)
    pe_bh = one(" AND b.lane='owner_expense' AND COALESCE(b.pe_who,'')='bhawna'" + pers)
    apart = {"pharmacy": one(" AND b.lane='pharmacy' AND COALESCE(b.kind,'')<>'" + PEXP + "'"), "lab": one(" AND b.lane='lab_purchase'"),   # S568
             "mk": pe_all - pe_bh, "bh": pe_bh, "patient": one(" AND b.subgroup=?", PATIENT)}
    apart.update(_s568_apart(db, ym))                                 # S568 item 7: Sanjeevni -- pharmacy expenses (never a section)
    nwait = one(" AND b.doc_kind='challan' AND COALESCE(b.challan_state,'awaiting')='awaiting' AND COALESCE(b.lane,'clinic')<>'pharmacy'"
                " AND COALESCE(b.subgroup,'')<>?" + pers, PATIENT)        # FIX1 C2: a patient's challan is in Kept apart only
    return secs, apart, nwait


# ---------------------------------------------------------------------------------------------- the switches
def switch_states(db):
    return {"scan.cv": bool(AR._scan_cv_on()), "scan.lanes5": bool(AR._lanes5_on()), "desk.on": desk_on(db),
            "machine.on": (_setting(db, "machine.on", "off") or "").strip().lower() == "on",      # S557 A7
            "stationery.issue_on": (_setting(db, "stationery.issue_on", "off") or "").strip().lower() == "on",      # S568
            "batteries.on": (_setting(db, "batteries.on", "off") or "").strip().lower() == "on"}      # S571


SWITCH_TPL = """<div class=card id=s551switches style="display:flex;flex-wrap:wrap;gap:10px;align-items:center">
<b style="font-size:15px;color:#2c4258;margin-right:6px">Switches</b>
{% for k, nm in sw %}<form method=post action="{{url_for('s551_switch')}}" style="display:inline-flex;align-items:center;gap:6px;margin:0 8px 0 0">
<input type=hidden name=key value="{{k}}"><input type=hidden name=on value="{{'0' if st[k] else '1'}}"><input type=hidden name=back value="{{back}}">
<span style="font-size:14px">{{nm}}</span><button style="padding:4px 10px;border-radius:12px;font-size:12px;background:{{'#2b6e4f' if st[k] else '#8a97a5'}}" title="tap to switch {{'off' if st[k] else 'on'}}">{{'ON' if st[k] else 'OFF'}}</button></form>{% endfor %}
<a href="{{url_for('admin')}}#claude-reads" style="font-size:14px">Claude reading →</a></div>"""


def switches_card(back=None):
    """For the scan app's front page (one hook there, behind 'is defined'): the owner's three switches. '' for anyone else
    and '' on any error -- that page must never fail because of this card."""
    try:
        if not _owner():
            return ""
        return Markup(render_template_string(SWITCH_TPL, st=switch_states(AR.get_db()), sw=SWITCHES,
                                             back=back or AR._here(full=True)))
    except Exception:                                                # noqa: BLE001
        return ""


def month_href():
    """The menus' link: The month for the owner, and for a manager once the desk is switched on; else the old page."""
    try:
        if _owner() or desk_on(AR.get_db()):
            return url_for("s551_month")
    except Exception:                                                # noqa: BLE001
        pass
    return url_for("d664_month")


# ---------------------------------------------------------------------------------------------- the pages
def _bg():
    pal = AR.setting_or("palette", AR.DEFAULT_PALETTE)
    return AR.PALETTES.get(pal, AR.PALETTES[AR.DEFAULT_PALETTE])[1]


CSS = """<style>
*{box-sizing:border-box}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;background:{{bg}};color:#1f2a36;line-height:1.4}
a{color:#2b5d8a}a:hover{color:#1d4366}
.top{display:flex;align-items:center;gap:18px;padding:10px 18px;background:#fff;border-bottom:1px solid #d6dde6;flex-wrap:wrap}
.top .t{font-size:17px;font-weight:700}
.muted{color:#4a5866}.small{font-size:12px}
.card{background:#fff;border:1px solid #d6dde6;border-radius:12px;padding:14px}
.b{min-height:34px;padding:4px 10px;border-radius:8px;font-size:13px;font-family:inherit;cursor:pointer;color:#1f2a36;border:1px solid #c9d2dc;background:#fff}
.b.on{border:2px solid #2b5d8a;background:#e3edf7;font-weight:700}
.go{min-height:34px;border-radius:8px;border:0;background:#2b5d8a;color:#fff;font-size:14px;cursor:pointer;padding:0 14px;font-family:inherit}
input,select{font-size:14px;padding:6px;border:1px solid #c9d2dc;border-radius:6px;font-family:inherit}
.msg{background:#eaf3ec;border:1px solid #9cc5a6;border-radius:8px;padding:8px 12px;margin:10px 18px 0}
.msg.bad{background:#fbecec;border-color:#e0a4a4}
.chip{font-size:13px;color:#4a5866;border:1px solid #c9d2dc;border-radius:14px;padding:3px 10px;text-decoration:none}
</style>"""

HEAD = """<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1"><title>{{title}}</title>""" + CSS

OFF_TPL = HEAD + """</head><body>{{s559_bar() if s559_bar is defined else ''}}<div class=top><span class=t>Sorting desk</span></div>
<p style="margin:24px 18px;font-size:17px">{{line}}</p><p style="margin:0 18px"><a href="{{url_for('d664_papers')}}">Papers to sort →</a> (the manual path keeps working)</p></body></html>"""


def _off_page():
    return render_template_string(OFF_TPL, bg=_bg(), line=OFF_LINE, title="Sorting desk")


def _gate(f):
    """While desk.on is OFF a manager gets one line (a page) or a refusal (the JSON and the forms); the owner passes."""
    @functools.wraps(f)
    def w(*a, **k):
        if not _owner() and not desk_on(AR.get_db()):
            if request.path.startswith("/desk/api/") or request.method == "POST":
                return jsonify(ok=False, error=OFF_LINE), 403
            return _off_page()
        return f(*a, **k)
    return w


def _chip(db):
    st = switch_states(db)
    return "Switches: smart scanner %s · reception buttons %s · desk for Shavez %s" % (
        "ON" if st["scan.cv"] else "OFF", "ON" if st["scan.lanes5"] else "OFF", "ON" if st["desk.on"] else "OFF")


DESK_TPL = HEAD + """<style>
html,body{height:100%;overflow:hidden}
#app{height:100vh;display:flex;flex-direction:column}
#main{display:flex;flex:1 1 auto;min-height:0}
#left{width:220px;flex:none;background:#fff;border-right:1px solid #d6dde6;display:flex;flex-direction:column;min-height:0}
#left.fold{width:44px}#left.fold .in{display:none}#left .unfold{display:none}#left.fold .unfold{display:block;margin:10px auto}
#left .hd{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-bottom:1px solid #e6ebf0}
#list{overflow:auto;flex:1 1 auto}
.row{display:block;width:100%;text-align:left;border:0;border-bottom:1px solid #eef1f4;padding:9px 12px;cursor:pointer;font-family:inherit;color:#1f2a36;background:#fff}
.row.on{background:#e3edf7}.row .r1{display:flex;justify-content:space-between;font-size:13px}.row .r2{display:block;font-size:14px;margin-top:2px}.row .r3{display:block;font-size:12px;color:#4a5866;margin-top:2px}
#mid{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;padding:12px 14px;gap:8px}
#scanbox{flex:1 1 auto;min-height:0;background:#5a6470;border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center}
#scan{width:100%;height:100%;border:0;background:#fbfaf7;transition:transform .2s}
#right{width:clamp(440px,45vw,640px);flex:none;background:#fff;border-left:1px solid #d6dde6;display:flex;flex-direction:column;min-height:0;overflow:hidden}
#empty{padding:12px 14px}
#panel{flex:1 1 auto;min-height:0;display:flex;flex-direction:column}
#fields{overflow:auto;flex:1;min-height:0;padding:8px 14px;display:flex;flex-direction:column;gap:8px}
#foot{flex:none;padding:6px 14px 8px;border-top:1px solid #d6dde6;background:#fff;display:flex;flex-direction:column;gap:5px}
.cr{font-size:12px;color:#5b6878;margin-top:2px}.cr b{font-weight:600;color:#3d4a57}
.use{border:0;background:none;color:#2b5d8a;text-decoration:underline;cursor:pointer;font-size:12px;padding:0;font-family:inherit}
#right label{font-size:12px;color:#4a5866}#right label input{display:block;width:100%;font-size:14px}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.amber{font-size:13px;background:#fff4dc;border:1px solid #e8c77a;border-radius:8px;padding:8px 10px}
.green{font-size:13px;background:#eaf3ec;border:1px solid #9cc5a6;border-radius:8px;padding:8px 10px;display:flex;flex-direction:column;gap:4px}
.gt{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:#5b6878;margin:1px 0 2px}
.dests{display:flex;flex-wrap:wrap;gap:4px}
.d{min-height:36px;padding:3px 9px;border-radius:8px;font-size:13px;font-family:inherit;cursor:pointer;color:#1f2a36;border:1px solid #c9d2dc;background:#fff}
.d.on{border:2px solid #2b5d8a;background:#e3edf7;font-weight:700}.d.pe.on{border-color:#6b4a8a;background:#efe7f6}
@media (max-width:1300px){.d[data-d=stationery]{max-width:86px;line-height:1.1;padding:2px 8px}}
#save{min-height:44px;border-radius:10px;border:0;background:#2b6e4f;color:#fff;font-size:16px;font-weight:700;cursor:pointer;font-family:inherit}
#save:disabled{background:#9aa8a1;cursor:default}
.err{color:#9c2b2b;font-size:13px}
.flag{font-size:13px;background:#fff4dc;border:1px solid #e8c77a;border-radius:8px;padding:8px 10px}
#groups{display:flex;flex-wrap:wrap;gap:3px 12px}.grp{display:flex;flex-direction:column}
#readbox{border:1px solid #e6ebf0;border-radius:8px;padding:5px 8px}#readbox>summary{cursor:pointer;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#readbox .ed{color:#2b5d8a;text-decoration:underline}
.kinds{display:flex;flex-wrap:wrap;gap:4px}.kinds .b{min-height:36px;font-size:13px;padding:3px 9px}
.box{flex-direction:column;gap:4px;font-size:13px;background:#f6f8fa;border:1px solid #e1e7ee;border-radius:8px;padding:8px}
#right .box .opt{display:flex;gap:6px;align-items:center;font-size:13px;color:#1f2a36}#right .box .opt input{width:auto;display:inline}.box .in{margin-left:22px}
.pay{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}#right .pay input{font-size:13px;padding:4px}
.modes{display:flex;gap:4px;flex-wrap:wrap}.modes .b{min-height:30px}#paidf>summary{cursor:pointer;font-size:13px;color:#2b5d8a}
.paidline{font-size:12px;color:#2b6e4f}#morecue{text-align:center;font-size:12px;color:#2b5d8a;cursor:pointer}#app>.top{padding:5px 18px}
</style></head><body><div id=app>
{{s559_bar() if s559_bar is defined else ''}}<div class=top><span class=t>Sorting desk</span><span class=muted id=wt style="font-size:14px">{{n}} paper{{'' if n==1 else 's'}} waiting · newest first</span>
{% if cant %}<span id=s559cant style="font-size:13px;color:#6b7785">{{cant}}</span>{% endif %}
<span style="flex-grow:1"></span>
<a href="{{url_for('s551_awaited')}}" style="font-size:14px">Bills awaited</a>
<a href="{{url_for('s551_implants')}}" style="font-size:14px">Implant stock ledger</a>
<a href="{{url_for('s551_month')}}" style="font-size:14px">The month</a>
{% if owner %}<a class=chip href="{{url_for('s551_month')}}#s551switches">{{chip}}</a>{% else %}<span class=chip>{{chip}}</span>{% endif %}</div>
<div id=main>
<div id=left><div class=in style="display:flex;flex-direction:column;min-height:0;flex:1 1 auto"><div class=hd><b style="font-size:14px">Waiting</b><button type=button class=b id=fold aria-label="Fold the list">fold ‹</button></div>
<form id=openf style="display:flex;gap:6px;margin:0;padding:8px 12px;border-bottom:1px solid #e6ebf0"><input id=openno placeholder="Open B-____" style="flex:1 1 auto;min-width:0;font-size:13px;padding:4px 6px"><button class=b type=submit>Open</button></form>
<div id=openerr class=err style="padding:0 12px"></div>
{% if add_href %}<a id=s568addlink href="{{add_href}}" style="display:block;padding:4px 12px 6px;font-size:13px;border-bottom:1px solid #e6ebf0">+ Add a paper from a file</a>{% endif %}
<div id=list></div></div><button type=button class="b unfold" id=unfold aria-label="Open the list">›</button></div>
<div id=mid><div style="display:flex;gap:8px;align-items:center"><b style="font-size:15px" id=hstamp>—</b><span class=muted style="font-size:13px" id=hwhen></span><span style="flex-grow:1"></span>
<span class=muted style="font-size:12px">every page and zoom: the viewer's own buttons</span><button type=button class=b id=turn>Turn ↻</button></div>
<div id=scanbox><iframe id=scan title="the scan" src="about:blank"></iframe></div></div>
<div id=right>
<div id=empty class=muted style="display:none">Nothing waiting. Open any paper by its number above.</div>
<div id=panel><div id=fields>
<div id=flags style="display:flex;flex-direction:column;gap:6px"></div>
<details id=readbox><summary id=readsum><b>Read:</b> — <span class=ed>edit ▾</span></summary><div style="display:flex;flex-direction:column;gap:6px;padding-top:6px"><b style="font-size:13px">What was read <span style="font-weight:400" class=muted>— correct anything</span></b>
<div class=grid2><div><label>Supplier<input id=f_vendor></label><div class=cr id=cr_vendor></div></div><div><label>Bill / challan no<input id=f_no></label><div class=cr id=cr_bill_no></div></div><div><label>Date<input id=f_date placeholder="dd-mm-yyyy"></label><div class=cr id=cr_date></div></div><div><label>Amount<input id=f_amt inputmode=decimal></label><div class=cr id=cr_amount></div></div></div><div class=cr id=ownline style="display:none"></div>
<div class=muted style="font-size:12px" id=items></div></div></details><div class=muted style="font-size:12px" id=status></div><div id=paidline class=paidline style="display:none"></div>
<div style="display:flex;flex-direction:column;gap:4px"><div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap"><b style="font-size:13px">What kind of paper</b>
<div class=kinds id=kinds></div></div><div class=muted style="font-size:12px" id=kindfrom></div><div class=muted style="font-size:12px" id=kindnote></div>
<div class=amber id=supnote style="display:none"></div>
<div class=green id=covers style="display:none"></div>
<div class=box id=rcpt style="display:none"></div><div class=box id=stmt style="display:none"></div><details id=paidf style="display:none"><summary>Paid?</summary><div id=paidbody></div></details></div>
<div style="display:flex;flex-direction:column;gap:4px"><div id=groupsbox><b style="font-size:13px">Where does it go?</b><div id=groups></div></div><div id=filedwith class=muted style="display:none;font-size:13px"></div>
<div id=who style="display:none;gap:6px;margin-top:4px"><button type=button class="d pe" data-who=mk>Dr MK</button><button type=button class="d pe" data-who=bhawna>Dr Bhawna</button></div>
<label id=accbox style="display:none;gap:6px;align-items:center;font-size:13px;color:#1f2a36"><input type=checkbox id=acc style="width:auto;display:inline"> Send to accountant <span class=muted>(off unless ticked; only a construction bill)</span></label>
<div class=muted style="font-size:12px" id=destnote></div><div id=hints class=muted style="font-size:12px"></div>
<label id=mixbox style="display:none;gap:6px;align-items:center;font-size:13px;color:#1f2a36"><input type=checkbox id=mixed style="width:auto;display:inline"> mixed: clinic + lab items</label>
<div class=box id=st568 style="display:none"></div><div class=box id=pr634 style="display:none"></div><div class=box id=bt571 style="display:none"></div></div>
</div><div id=foot><div id=morecue style="display:none">more ▾</div><div id=pagebox style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px"><label style="font-size:13px;color:#1f2a36;display:flex;gap:6px;align-items:center"><input type=checkbox id=pg_on style="width:auto;display:inline"> A page of another paper — join into</label><input id=pg_no placeholder="B-____" style="width:80px;font-size:13px;padding:4px">
<button type=button class=b id=blank title="marks it rejected; nothing is deleted">Blank — discard</button></div>
<button type=button id=save disabled>Choose where it goes</button>
<div class=err id=err></div>
<div class=muted style="font-size:12px" id=savednote>Save files it, accepts it and opens the next paper.</div></div>
</div></div></div></div>
<script>""" + r"""
(function(){
var C={{cfg|tojson}};
var S={list:[],cur:null,dest:'',kind:'',who:'mk',flag:'',saved:0,rot:0,ticks:{}};
function $(i){return document.getElementById(i);}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function getJ(u){return fetch(u,{credentials:'same-origin',cache:'no-store'}).then(function(r){return r.json().then(function(j){j._s=r.status;return j;},function(){return{ok:false,error:'The server did not answer ('+r.status+').'};});});}
function pu(id){return C.paper.replace(/\/0$/,'/'+id);}
function norm(s){return String(s||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();}
function loadList(openId){return getJ(C.list).then(function(j){S.list=j.papers||[];var n=j.total||0;$('wt').textContent=n+' paper'+(n==1?'':'s')+' waiting · newest first';drawList();
 if(openId!==undefined){if(openId){openPaper(openId);}else if(S.list.length){openPaper(S.list[0].id);}else{showEmpty();}}});}
function drawList(){var h='';S.list.forEach(function(p){h+='<button type=button class="row'+(S.cur&&S.cur.id==p.id?' on':'')+'" data-id="'+p.id+'"><span class=r1><b>'+esc(p.stamp)+'</b><span class=muted>'+esc(p.month)+'</span></span><span class=r2>'+esc(p.supplier||'supplier not read')+'</span><span class=r3>'+esc(p.hint)+'</span></button>';});
 $('list').innerHTML=h||'<p class=muted style="padding:12px">Nothing waiting.</p>';}
function showEmpty(){S.cur=null;$('panel').style.display='none';$('empty').style.display='block';$('scan').src='about:blank';$('hstamp').textContent='—';$('hwhen').textContent='';}
function openPaper(id){$('err').textContent='';return getJ(pu(id)).then(function(j){if(!j.ok){$('err').textContent=j.error||'Cannot open it.';$('openerr').textContent=j.error||'';return;}
 $('openerr').textContent='';S.cur=j;S.dest=j.dest||'';S.kind=j.kind||'';S.who=j.who||'mk';S.flag='';S.rot=0;S.ticks={};(j.covers||[]).forEach(function(c){S.ticks[c.id]=!!c.ticked;});s560init(j);s568init(j);s634init(j);s571init(j);draw();drawList();});}
function draw(){var j=S.cur;$('empty').style.display='none';$('panel').style.display='flex';
 $('hstamp').textContent=j.stamp+' · '+(j.supplier||'supplier not read');$('hwhen').textContent='scanned '+j.scanned+' · '+j.lane;
 $('scan').src=j.file||'about:blank';$('scan').style.transform='';
 $('f_vendor').value=j.supplier;$('f_no').value=j.bill_no;$('f_date').value=j.date;$('f_amt').value=j.amount;crs(j);sumline();$('readbox').open=S.readopen;paidline(j);$('paidbody').innerHTML='';
 $('items').textContent=j.items;$('status').textContent='Now: '+(j.current||'not sorted')+' · '+j.status+(j.owner_line?' · '+j.owner_line:'');
 var f=fixb(j);if(j.flags.hold){f+='<div class=flag>Looks like a second scan of <b>'+esc(j.flags.hold)+'</b>.<br><label><input type=radio name=fl value=same> It is the same — set aside</label><br><label><input type=radio name=fl value=keep> Not the same — keep</label></div>';}
 if(j.flags.s441){f+='<div class=flag>Set aside as a second scan of <b>'+esc(j.flags.s441)+'</b>.<br><label><input type=radio name=fl value=same> Same — leave it set aside</label><br><label><input type=radio name=fl value=restore> Not the same — bring it back</label></div>';}
 if(j.flags.date){f+='<div class=flag>The date looks misread — check.</div>';}
 if(j.flags.nothing){f+='<div class=flag>Nothing could be read — type what you see.</div>';}
 $('flags').innerHTML=f;Array.prototype.forEach.call(document.querySelectorAll('input[name=fl]'),function(r){r.addEventListener('change',function(){S.flag=r.value;paint();});});
 $('pagebox').style.display=j.can_page?'flex':'none';$('pg_on').checked=false;$('pg_no').value='';
 var h='';C.groups.forEach(function(g){h+='<div class=grp><div class=gt>'+esc(g[0])+'</div><div class=dests>';g[1].forEach(function(d){if(d[0]=='pe'){h+='<button type=button class="d pe" data-d=pe data-who=mk>Dr MK</button><button type=button class="d pe" data-d=pe data-who=bhawna>Dr Bhawna</button>';}else{h+='<button type=button class="d" data-d="'+d[0]+'">'+esc(d[1])+'</button>';}});h+='</div></div>';});$('groups').innerHTML=h;
 $('hints').innerHTML=(j.hints||[]).map(function(x){return '<div>'+esc(x)+'</div>';}).join('');
 $('supnote').style.display=j.supplier_note?'block':'none';$('supnote').textContent=j.supplier_note||'';paint();}
function useb(x,k){return 'Claude read: <b>'+esc(x.show)+'</b> — <button type=button class=use data-f="'+k+'" data-v="'+esc(x.fill)+'">use it</button>';}
function crs(j){var c=j.claude||{};['vendor','bill_no','date','amount'].forEach(function(k){var x=c[k];if(k=='vendor'&&j.own_line){x=null;}$('cr_'+k).innerHTML=x?useb(x,k):'';});
 var o=j.own_line?esc(j.own_line):'';if(j.own_line&&c.vendor){o+=' '+useb(c.vendor,'vendor');}$('ownline').innerHTML=o;$('ownline').style.display=o?'block':'none';}
function paint(){var j=S.cur;if(!j){return;}
 var k='';C.kinds.forEach(function(x){k+='<button type=button class="b'+(S.kind==x[0]?' on':'')+'" data-k="'+x[0]+'">'+esc(x[1])+'</button>';});$('kinds').innerHTML=k;
 $('kindfrom').textContent=(j.kind&&S.kind==j.kind&&j.kind_from&&j.kind_from!='paper')?'pre-chosen from '+j.kind_from:'';
 Array.prototype.forEach.call(document.querySelectorAll('#groups .d'),function(b){var dd=b.getAttribute('data-d'),w=b.getAttribute('data-who');b.className='d'+(dd=='pe'?' pe':'')+((S.dest==dd&&(!w||S.who==w))?' on':'');});
 $('who').style.display='none';Array.prototype.forEach.call(document.querySelectorAll('#who .d'),function(b){b.className='d pe'+(S.who==b.getAttribute('data-who')?' on':'');});
 var note=C.notes[S.dest]||'';if(S.dest=='clinic_equipment'&&!C.owner){note='Waiting for Dr Manoj’s Save after yours: it is filed, not accepted.';}
 if(S.dest=='clinic_equipment'&&j.linked){note=(note?note+' ':'')+j.linked;}
 if(S.dest&&S.dest==j.dest&&j.dest_line){note=(note?note+' ':'')+j.dest_line;}$('destnote').textContent=note;
 var cv=j.covers||[];if(S.kind=='bill'&&cv.length){var c='<b>This bill covers these challans</b>',names=[];cv.forEach(function(x){c+='<label style="font-size:13px;color:#1f2a36"><input type=checkbox data-c="'+x.id+'" '+(S.ticks[x.id]?'checked':'')+' style="width:auto;display:inline"> '+esc(x.stamp)+' · '+esc(x.date)+' · '+x.n+' item'+(x.n==1?'':'s')+(x.ticked?'':' · '+x.age+' days')+'</label>';if(S.ticks[x.id]){names=names.concat(x.names);}});
  var B={},Cn={},m=0,cnt=0,ex=0;(j.bill_names||[]).forEach(function(n){if(norm(n))B[norm(n)]=1;});names.forEach(function(n){if(norm(n))Cn[norm(n)]=1;});Object.keys(Cn).forEach(function(n){cnt++;if(B[n])m++;});Object.keys(B).forEach(function(n){if(!Cn[n])ex++;});
  c+='<span style="color:#3d5a45">Items on the bill against the ticked challans: '+m+' of '+cnt+' match · '+ex+' extra on the bill · '+(cnt-m)+' missing</span>';$('covers').innerHTML=c;$('covers').style.display='flex';
  Array.prototype.forEach.call(document.querySelectorAll('#covers input[data-c]'),function(x){x.addEventListener('change',function(){S.ticks[x.getAttribute('data-c')]=x.checked;paint();});});}
 else{$('covers').style.display='none';}
 s560paint(j);s568paint(j);s634paint(j);s571paint(j);paint2();}
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-id],[data-d],[data-k],[data-who],[data-f]'):null;if(!t){return;}
 if(t.hasAttribute('data-id')){openPaper(t.getAttribute('data-id'));}
 else if(t.hasAttribute('data-d')){S.dest=t.getAttribute('data-d');if(t.hasAttribute('data-who')){S.who=t.getAttribute('data-who');}paint();}
 else if(t.hasAttribute('data-k')){S.kind=t.getAttribute('data-k');paint();}
 else if(t.hasAttribute('data-who')){S.who=t.getAttribute('data-who');paint();}
 else if(t.hasAttribute('data-f')){var F={vendor:'f_vendor',bill_no:'f_no',date:'f_date',amount:'f_amt'};$(F[t.getAttribute('data-f')]).value=t.getAttribute('data-v');}});
$('pg_on').addEventListener('change',paint);$('pg_no').addEventListener('input',paint);
$('fold').addEventListener('click',function(){$('left').className='fold';});$('unfold').addEventListener('click',function(){$('left').className='';});
$('turn').addEventListener('click',function(){S.rot=(S.rot+90)%360;$('scan').style.transform=S.rot?'rotate('+S.rot+'deg)':'';});
$('openf').addEventListener('submit',function(e){e.preventDefault();var v=$('openno').value.trim();if(!v){return;}getJ(C.find+'?no='+encodeURIComponent(v)).then(function(j){if(j.ok){openPaper(j.id);}else{$('openerr').textContent=j.error||'Not found.';}});});
function post(body){$('save').disabled=true;$('err').textContent='';return fetch(C.save,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){return j;},function(){return{ok:false,error:'The server did not answer ('+r.status+'). Nothing was saved.'};});})
 .then(function(j){if(!j.ok){$('err').textContent=j.error||'Not saved.';paint();return;}S.saved++;$('savednote').textContent=S.saved+' saved this sitting — each can be changed again from its own page. Last: '+j.message;loadList(j.next||0);});}
$('save').addEventListener('click',function(){var j=S.cur;if(!j){return;}var b={id:j.id,vendor:$('f_vendor').value,bill_no:$('f_no').value,bill_date:$('f_date').value,total_amount:$('f_amt').value,kind:S.kind,dest:S.dest,who:S.who,flag:S.flag,joins:[]};
 if(S.kind=='bill'){(j.covers||[]).forEach(function(c){if(S.ticks[c.id]){b.joins.push(c.id);}});}
 s560body(b,j);s568body(b,j);s634body(b,j);if($('pg_on').checked&&$('pg_no').value.trim()){b.page_of=$('pg_no').value.trim();b.dest='';}post(b);});
$('blank').addEventListener('click',function(){var j=S.cur;if(!j){return;}if(!confirm('Discard '+j.stamp+' as blank? It is kept on record, marked rejected.')){return;}post({id:j.id,blank:true,flag:S.flag});});
// S560_RECEIPTS_STATEMENTS: the desk on one laptop screen; Receipt and Statement; "Paid?"; Send to accountant; the papers to put right
function inr(x){var n=parseFloat(String(x||'').replace(/[^0-9.\-]/g,''));if(!isFinite(n)){return '₹0';}var s=Math.round(Math.abs(n)).toString(),t=s.slice(-3),h=s.slice(0,-3);if(h){h=h.replace(/\B(?=(\d{2})+(?!\d))/g,',');t=h+','+t;}return (n<0?'-':'')+'₹'+t;}
function num(x){var n=parseFloat(String(x==null?'':x).replace(/[^0-9.\-]/g,''));return isFinite(n)?n:0;}
function d2i(s){s=String(s||'').trim();var m=s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);if(m){return m[1]+'-'+('0'+m[2]).slice(-2)+'-'+('0'+m[3]).slice(-2);}m=s.match(/^(\d{1,2})[-\/.](\d{1,2})[-\/.](\d{2}|\d{4})$/);if(!m){return '';}var y=m[3].length==2?'20'+m[3]:m[3];return y+'-'+('0'+m[2]).slice(-2)+'-'+('0'+m[1]).slice(-2);}
function addDays(iso,k){var d=new Date(iso+'T00:00:00Z');d.setUTCDate(d.getUTCDate()+k);return d.toISOString().slice(0,10);}
function sumline(){var v=$('f_vendor').value.trim(),n=$('f_no').value.trim(),d=$('f_date').value.trim(),a=$('f_amt').value.trim();
 $('readsum').innerHTML='<b>Read:</b> '+esc(v||'supplier not read')+(n?' · no. '+esc(n):'')+(d?' · '+esc(d):'')+(a?' · '+esc(inr(a)):'')+' <span class=ed>edit ▾</span>';}
function s560init(j){S.acc=!!j.to_acc;var rc=j.rc||{},st=j.st||{};S.rc={pays:rc.cur||'',paid_on:rc.paid_on||'',amount:rc.amount||'',mode:rc.mode||'',ref:rc.ref||''};
 (rc.cands||[]).forEach(function(c){if(c.pre){S.rc.pays=String(c.id);}});
 S.st={frm:st.frm||'',to:st.to||'',total:st.total||'',paid_on:st.paid_on||'',amount:st.amount||'',mode:st.mode||'',ref:st.ref||'',ticks:{}};stTick();
 var cu=(st.cands||[]).filter(function(c){return c.cur;});if(cu.length){S.st.ticks={};cu.forEach(function(c){S.st.ticks[c.id]=true;});}
 var e=(j.pay||{}).edit;S.pay=e?{paid_on:e.paid_on||'',amount:e.amount||'',mode:e.mode||'',ref:e.ref||''}:{paid_on:'',amount:'',mode:'',ref:''};S.paytouched=false;S.payopen=false;S.readopen=!!(j.flags&&(j.flags.nothing||j.flags.date));}
function stShown(){var j=S.cur,f=d2i(S.st.frm),t=d2i(S.st.to);return ((j.st||{}).cands||[]).filter(function(c){return c.cur||((!f||c.iso>=addDays(f,-7))&&(!t||c.iso<=addDays(t,7)));});}
function recline(j,on){var p=j.pay||{};return (on&&p.of)?'<div class=paidline>Recorded: '+esc(p.of)+' — saving again changes this payment, never adds a second.</div>':'';}
function stTick(){var f=d2i(S.st.frm),t=d2i(S.st.to);S.st.ticks={};if(!f&&!t){return;}((S.cur.st||{}).cands||[]).forEach(function(c){if((!f||c.iso>=f)&&(!t||c.iso<=t)){S.st.ticks[c.id]=true;}});}
function payBoxes(p,o){return '<div class=pay><label>Paid on<input data-sv="'+p+'.paid_on" value="'+esc(o.paid_on)+'" placeholder="dd-mm-yyyy"></label><label>Amount<input data-sv="'+p+'.amount" value="'+esc(o.amount)+'" inputmode=decimal></label>'
 +'<label>Cheque / ref no<input data-sv="'+p+'.ref" value="'+esc(o.ref)+'"></label></div><div class=modes>'+(C.modes||[]).map(function(m){return '<button type=button class="b'+(o.mode==m[0]?' on':'')+'" data-mode="'+p+':'+m[0]+'">'+esc(m[1])+'</button>';}).join('')+'</div>';}
function rcCand(){var j=S.cur,id=S.rc.pays;var c=((j.rc||{}).cands||[]).filter(function(x){return String(x.id)==id;})[0];if(c){return c;}if(id.indexOf('st:')==0){return ((j.rc||{}).stmts||[]).filter(function(x){return 'st:'+x.id==id;})[0]||null;}return null;}
function forced(){if(S.kind=='receipt'){var c=rcCand();return c?{dest:c.dest,stamp:c.stamp}:null;}
 if(S.kind=='statement'){var t=stShown().filter(function(c){return S.st.ticks[c.id];});return t.length?{dest:t[0].dest,stamp:t[0].stamp}:null;}return null;}
function s560linked(){var f=forced();return !!(f&&f.dest);}
function s560why(){var j=S.cur;if(j.fix&&j.fix.key=='blank'&&j.status=='set aside'){return 'Restore it first (above)';}if(j.aside&&j.status=='set aside'){return 'Restore it first (above)';}
 if(S.kind=='receipt'){if(!S.rc.pays||S.rc.pays=='st'){return 'Choose the bill it pays';}if(S.rc.pays.indexOf('st:')!=0&&!(S.rc.paid_on&&S.rc.amount&&S.rc.mode)){return 'Type the payment: date, amount, how';}}
 if(S.kind=='statement'&&!(S.st.paid_on&&S.st.amount&&S.st.mode)){return 'Type the payment: date, amount, how';}
 if(S.kind=='bill'&&(S.pay.paid_on||S.pay.amount)&&!(S.pay.paid_on&&S.pay.amount&&S.pay.mode)){return 'Paid?: date, amount and how';}return '';}
function stDiff(){var y=num(S.st.total),x=0;stShown().forEach(function(c){if(S.st.ticks[c.id]){x+=num(c.out||c.amount);}});var z=y-x;
 if($('stdiff')){$('stdiff').textContent='Ticked '+inr(x)+' of statement '+inr(y)+' — difference '+inr(z);$('stgrey').style.display=Math.abs(z)>=0.5?'block':'none';}}
function fixb(j){if(!j.fix){return j.aside?'<div class=flag id=s563aside><b>'+esc(j.aside.text)+'</b><br><button type=button class=b data-restore=1>Restore</button></div>':'';}var k=j.fix.key,h='<div class=flag id=s560fix><b>'+esc(j.fix.text)+'</b><br>';
 if(k=='blank'){h+='<button type=button class=b data-fix=restore>Restore</button> <button type=button class=b data-fix=keep>Leave it set aside</button>';}
 else if(k=='receipt'||k=='statement'){h+='<button type=button class=b data-s560k="'+k+'">Make it a '+(k=='receipt'?'Receipt':'Statement')+'</button> <button type=button class=b data-fix=keep>No — leave it</button>';}
 else{h+='<span class=muted>A hint only: you choose.</span> <button type=button class=b data-fix=keep>Leave it</button>';}return h+'</div>';}
function paidline(j){var p=j.pay||{},h='';if(p.of){h='<div>'+esc(p.of)+'</div>';}
 (p.state?(p.lines||[]):[]).forEach(function(l){h+='<div>'+esc(l.text)+(l.proof_stamp?' · '+(l.file?'<a href="'+esc(l.file)+'" target=_blank>'+esc(l.proof_stamp)+' scan</a>':esc(l.proof_stamp)):'')+(l.pid?' <button type=button class=use data-void="'+l.pid+'">void</button>':'')+'</div>';});
 if(p.state=='part'){h='<div><b>'+esc(p.word)+'</b></div>'+h;}$('paidline').innerHTML=h;$('paidline').style.display=h?'block':'none';}
function s560paint(j){var r='',s='',f=forced();
 if(S.kind=='receipt'){var rc=j.rc||{};r=recline(j,rc.recorded)+'<b>Pays which bill?</b>';(rc.cands||[]).forEach(function(c){r+='<label class=opt><input type=radio name=rcp data-rc="'+c.id+'"'+(S.rc.pays==String(c.id)?' checked':'')+'> '+esc(c.stamp)+(c.no?' · no. '+esc(c.no):'')+' · '+esc(c.date)+' · '+esc(c.inr)+' · '+esc(c.lane)+'</label>';});
  if(!(rc.cands||[]).length){r+='<div class=muted>No unpaid bill of this supplier in the last 180 days.</div>';}
  r+='<label class=opt><input type=radio name=rcp data-rc=none'+(S.rc.pays=='none'?' checked':'')+'> No bill — paid directly</label><label class=opt><input type=radio name=rcp data-rc=st'+(S.rc.pays.indexOf('st')==0?' checked':'')+'> A statement</label>';
  if(S.rc.pays.indexOf('st')==0){(rc.stmts||[]).forEach(function(x){r+='<label class="opt in"><input type=radio name=rcs data-rc="st:'+x.id+'"'+(S.rc.pays=='st:'+x.id?' checked':'')+'> '+esc(x.stamp)+' · '+esc(x.date)+' · '+esc(x.inr)+'</label>';});if(!(rc.stmts||[]).length){r+='<div class="muted in">No statement of this supplier yet.</div>';}}
  r+=payBoxes('rc',S.rc);}
 $('rcpt').innerHTML=r;$('rcpt').style.display=r?'flex':'none';
 if(S.kind=='statement'){s=recline(j,(j.st||{}).recorded)+'<div class=pay><label>Period from<input data-sv="st.frm" value="'+esc(S.st.frm)+'" placeholder="dd-mm-yyyy"></label><label>to<input data-sv="st.to" value="'+esc(S.st.to)+'" placeholder="dd-mm-yyyy"></label><label>Total<input data-sv="st.total" value="'+esc(S.st.total)+'" inputmode=decimal></label></div>'+payBoxes('st',S.st)+'<b>Which invoices does it cover?</b>';
  var sh=stShown();sh.forEach(function(c){s+='<label class=opt><input type=checkbox data-stt="'+c.id+'"'+(S.st.ticks[c.id]?' checked':'')+'> '+esc(c.stamp)+(c.no?' · no. '+esc(c.no):'')+' · '+esc(c.date)+' · '+esc(c.inr)+' · '+esc(c.lane)+'</label>';});
  if(!sh.length){s+='<div class=muted>No unpaid invoice of this supplier in that period.</div>';}s+='<div id=stdiff style="font-size:13px"></div><div id=stgrey class=muted style="display:none;font-size:12px">An invoice may not be scanned yet.</div>';}
 $('stmt').innerHTML=s;$('stmt').style.display=s?'flex':'none';stDiff();
 var pf=$('paidf'),pp=j.pay||{},paid=pp.state=='paid';pf.style.display=S.kind=='bill'?'block':'none';
 pf.querySelector('summary').textContent=paid?'Paid on '+(pp.last_on||'')+' — change?':'Paid?';
 if(S.kind=='bill'&&!$('paidbody').innerHTML){$('paidbody').innerHTML=(paid&&!pp.edit)?'<div class=muted>'+esc(pp.edit_no||'Already paid.')+'</div>':payBoxes('pay',S.pay);}
 if(S.kind!='bill'){$('paidbody').innerHTML='';pf.open=false;}
 $('groupsbox').style.display=(f&&f.dest)?'none':'block';$('filedwith').style.display=(f&&f.dest)?'block':'none';
 $('filedwith').textContent=(f&&f.dest)?'Filed with '+f.stamp+', on its place: '+(C.names[f.dest]||f.dest)+'. Never counted as spend — the bill is.':'';
 var ab=S.dest=='construction'&&S.kind=='bill'&&!(f&&f.dest);$('accbox').style.display=ab?'flex':'none';$('acc').checked=ab&&S.acc;
 $('kindnote').textContent=(S.kind=='receipt'||S.kind=='statement')?'Never counted as spend — the bill is.':'';cue();}
function cue(){var f=$('fields');if(!f){return;}$('morecue').style.display=(f.scrollHeight>f.clientHeight+2)?'block':'none';}
function s560body(b,j){b.to_accountant=!!(S.acc&&S.dest=='construction'&&S.kind=='bill');
 if(S.kind=='receipt'){b.receipt={pays:(S.rc.pays=='st'?'':S.rc.pays),paid_on:S.rc.paid_on,amount:S.rc.amount,mode:S.rc.mode,ref:S.rc.ref};b.joins=[];}
 if(S.kind=='statement'){b.statement={from:S.st.frm,to:S.st.to,total:S.st.total,paid_on:S.st.paid_on,amount:S.st.amount,mode:S.st.mode,ref:S.st.ref,covers:stShown().filter(function(c){return S.st.ticks[c.id];}).map(function(c){return c.id;})};b.joins=[];}
 if(S.kind=='bill'&&(S.pay.paid_on||S.pay.amount)&&(!(j.pay||{}).edit||S.paytouched)){b.pay={paid_on:S.pay.paid_on,amount:S.pay.amount,mode:S.pay.mode,ref:S.pay.ref};}}
function jpost(u,body){return fetch(u,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(x){return x;},function(){return{ok:false,error:'The server did not answer ('+r.status+').'};});});}
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-fix],[data-restore],[data-void],[data-s560k],[data-rc],[data-mode],[data-stt],#morecue'):null;if(!t||!S.cur){return;}var j=S.cur;
 if(t.id=='morecue'){$('fields').scrollTop=$('fields').scrollHeight;return;}
 if(t.hasAttribute('data-restore')){jpost(C.restore,{id:j.id}).then(function(x){if(!x.ok){$('err').textContent=x.error||'Not saved.';return;}$('savednote').textContent=x.message;loadList(j.id);});return;}
 if(t.hasAttribute('data-fix')){jpost(C.fix,{id:j.id,answer:t.getAttribute('data-fix')}).then(function(x){if(!x.ok){$('err').textContent=x.error||'Not saved.';return;}$('savednote').textContent=x.message;loadList(t.getAttribute('data-fix')=='restore'?j.id:0);});}
 else if(t.hasAttribute('data-void')){if(!confirm('Void this payment? It stays on record, marked voided.')){return;}jpost(C.void,{id:parseInt(t.getAttribute('data-void'),10)}).then(function(x){if(!x.ok){$('err').textContent=x.error||'Not saved.';return;}$('savednote').textContent=x.message;openPaper(j.id);});}
 else if(t.hasAttribute('data-s560k')){S.kind=t.getAttribute('data-s560k');paint();}
 else if(t.hasAttribute('data-rc')){S.rc.pays=t.getAttribute('data-rc');paint();}
 else if(t.hasAttribute('data-mode')){var m=t.getAttribute('data-mode').split(':');S[m[0]].mode=m[1];if(m[0]=='pay'){S.paytouched=true;}paint();if(m[0]=='pay'){$('paidbody').innerHTML=payBoxes('pay',S.pay);paint();}}
 else if(t.hasAttribute('data-stt')){S.st.ticks[t.getAttribute('data-stt')]=t.checked;stDiff();paint();}});
document.addEventListener('input',function(e){var t=e.target;if(!S.cur){return;}if(t.hasAttribute&&t.hasAttribute('data-sv')){var k=t.getAttribute('data-sv').split('.');S[k[0]][k[1]]=t.value;if(k[0]=='pay'){S.paytouched=true;}if(k[0]=='st'&&k[1]=='total'){stDiff();}paint2();}
 else if(t.id=='f_vendor'||t.id=='f_no'||t.id=='f_date'||t.id=='f_amt'){sumline();}});
document.addEventListener('change',function(e){var t=e.target;if(t.hasAttribute&&t.hasAttribute('data-sv')){var k=t.getAttribute('data-sv');if(k=='st.frm'||k=='st.to'){stTick();paint();}}if(t.id=='acc'){S.acc=t.checked;}});
function paint2(){var j=S.cur;var fl=S.flag,pg=$('pg_on').checked&&$('pg_no').value.trim();var why=s560why();var ok=!!(S.dest||pg||fl=='same'||fl=='restore'||s560linked())&&!((j.flags.hold||j.flags.s441)&&!fl)&&!(why&&!pg&&fl!='same'&&fl!='restore');
 $('save').disabled=!ok;$('save').textContent=ok?'Save — next paper':(why&&(S.dest||s560linked())?why:((j.flags.hold||j.flags.s441)&&!fl?'Answer the question above':'Choose where it goes'));}
// S568_STATIONERY_STOCK: the Stationery & packaging panel (match / Add to the list / not a stock item) and the mixed tick
function inr2(x){var n=parseFloat(x);if(!isFinite(n)){return '';}return (Math.round(n*100)%100)?('₹'+n.toFixed(2)):inr(n);}
function s568init(j){S.stk=null;var bx=$('st568');if(bx){bx.innerHTML='';bx.removeAttribute('data-for');}
 if(j.stk){S.stk={lines:(j.stk.lines||[]).map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,rate:l.rate,item:String(l.item==null?'':l.item),hand:l.hand,sug:l.sug,saved:l.saved};})};}S.mixed=!!j.mixed;}
function s568uk(u){u=String(u||'').toLowerCase().replace(/[^a-z]/g,'');var m={pcs:'piece',pc:'piece',pieces:'piece',nos:'piece',no:'piece',nag:'piece',pkt:'packet',pkts:'packet',packets:'packet',packs:'pack',pk:'pack',reams:'ream',boxes:'box',rolls:'roll',sets:'set',books:'book',registers:'register',files:'file',dozens:'dozen',doz:'dozen',bundles:'bundle'};return m[u]||u;}
function s568flag(l){var it=null;((S.cur.stk||{}).items||[]).forEach(function(x){if(String(x.id)==l.item){it=x;}});if(!it){return '';}
 var lu=s568uk(l.unit),iu=s568uk(it.unit);if(lu&&iu&&lu!=iu){return 'unit differs — on the paper: '+l.unit+', on the list: '+it.unit;}
 if(l.rate==null||l.rate===''||it.rate==null){return '';}return Math.round(parseFloat(l.rate)*100)!=Math.round(parseFloat(it.rate)*100)?'rate '+inr2(l.rate)+' — list '+inr2(it.rate):'';}
function s568flags(){((S.stk||{}).lines||[]).forEach(function(l,i){var e=document.querySelector('[data-stf="'+i+'"]');if(e){e.textContent=s568flag(l);}});}
function s568paint(j){var box=$('st568'),mb=$('mixbox');if(!box||!mb){return;}
 mb.style.display=((S.kind=='bill'||S.kind=='challan')&&(S.dest=='stationery'||S.dest=='lab'))?'flex':'none';$('mixed').checked=!!S.mixed;
 if(S.dest!='stationery'||!j.stk||!S.stk){box.style.display='none';return;}
 if(box.getAttribute('data-for')==String(j.id)&&box.innerHTML){box.style.display='flex';s568flags();return;}
 var h='<b>Stationery lines</b><span class=muted>Match each line to the list, “+ Add to the list”, or “not a stock item”. A line left alone counts nothing.</span>';
 if(!j.stk.counts){h+='<div class=muted>'+esc(j.stk.why)+'.</div>';}if(j.stk.noread){h+='<div class=muted>No items read — fill the line by hand.</div>';}
 S.stk.lines.forEach(function(l,i){var o='<option value="">— choose —</option>';(j.stk.items||[]).forEach(function(x){o+='<option value="'+x.id+'"'+(String(x.id)==l.item?' selected':'')+'>'+esc(x.name)+' ('+esc(x.unit)+')</option>';});
  o+='<option value=new'+(l.item=='new'?' selected':'')+'>+ Add to the list</option><option value=ns'+(l.item=='ns'?' selected':'')+'>not a stock item</option>';
  h+='<div class=stl style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">'+(l.hand?'<input data-stn="'+i+'" value="'+esc(l.name)+'" placeholder="item" style="width:150px;font-size:13px;padding:4px">':'<span style="min-width:120px">'+esc(l.name)+'</span>')
   +'<input data-stq="'+i+'" value="'+esc(l.qty)+'" inputmode=decimal style="width:60px;font-size:13px;padding:4px"><span class=muted>'+esc(l.unit||'')+'</span>'
   +'<select data-sti="'+i+'" style="font-size:13px;padding:3px">'+o+'</select>'+((l.sug&&!l.saved)?'<span class=muted>suggested</span>':'')+'<span class=err data-stf="'+i+'"></span></div>';});
 box.innerHTML=h;box.setAttribute('data-for',String(j.id));box.style.display='flex';s568flags();cue();}
function s568body(b,j){if(S.dest=='stationery'&&j.stk&&S.stk){b.st_lines=S.stk.lines.map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,rate:l.rate,item:l.item};});}
 if($('mixbox')&&$('mixbox').style.display!='none'){b.mixed=!!$('mixed').checked;}}
document.addEventListener('input',function(e){var t=e.target;if(!S.stk||!t.hasAttribute){return;}
 if(t.hasAttribute('data-stq')){S.stk.lines[+t.getAttribute('data-stq')].qty=t.value;}else if(t.hasAttribute('data-stn')){S.stk.lines[+t.getAttribute('data-stn')].name=t.value;}});
document.addEventListener('change',function(e){var t=e.target;if(t.id=='mixed'){S.mixed=t.checked;return;}if(!S.stk||!t.hasAttribute||!t.hasAttribute('data-sti')){return;}var l=S.stk.lines[+t.getAttribute('data-sti')];l.item=t.value;l.sug=false;s568flags();});
// S634_PROCROOM_LIST: the Procedure room panel -- each line's product (or "not on the list"), quantity, brand and place; no rate
function s634init(j){S.pr=null;var bx=$('pr634');if(bx){bx.innerHTML='';bx.removeAttribute('data-for');}
 if(j.pr){S.pr={lines:(j.pr.lines||[]).map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,brand:l.brand||'',place:l.place||'proc',item:String(l.item==null?'':l.item),hand:l.hand,sug:l.sug,saved:l.saved,orth:l.orth};}),role:j.pr.role||'slip',order:String(j.pr.order||''),book:j.pr.book||''};}}
function s634flag(l){if(l.item=='free'&&l.place=='proc'){return 'a Procedure room line needs a product from the list — or “Not on the list”';}
 if(l.place=='sanj'){return 'orthotics — goes to Sanjeevni, flagged for Dr Manoj';}if(l.item=='ask'){return 'waits for Dr Manoj to add it to his list';}return '';}
function s634flags(){((S.pr||{}).lines||[]).forEach(function(l,i){var e=document.querySelector('[data-prf="'+i+'"]');if(e){e.textContent=s634flag(l);}});}
function s634paint(j){var box=$('pr634');if(!box){return;}
 if(S.dest!='procedure'||!j.pr||!S.pr){box.style.display='none';return;}
 if(box.getAttribute('data-for')==String(j.id)&&box.innerHTML){box.style.display='flex';s634flags();return;}
 var h='<b>Procedure room lines</b><span class=muted>Give each line its product, quantity and place. A line left without a product counts nothing. No rates here — Dr Manoj adds them.</span>';
 var ro=S.pr.role=='order';h+='<div data-pr635=1 style="display:flex;flex-wrap:wrap;gap:12px;align-items:center"><label style="margin:0;display:inline-flex;gap:5px;align-items:center;font-weight:normal"><input type=radio name=prrole value=slip data-prr=1'+(ro?'':' checked')+' style="width:auto;margin:0"> A slip or a bill (it counts)</label>'+'<label style="margin:0;display:inline-flex;gap:5px;align-items:center;font-weight:normal"><input type=radio name=prrole value=order data-prr=1'+(ro?' checked':'')+' style="width:auto;margin:0"> Dr Manoj’s order (it counts nothing)</label></div>';
 if(ro){h+='<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center"><span>Book page no.</span><input data-prbk=1 value="'+esc(S.pr.book)+'" placeholder="book page no." style="width:120px;font-size:13px;padding:4px"><span class=muted>His signed order: its lines are kept and count nothing — the slip that comes against it counts.</span></div>';}
 else{var oo='<option value="">— no order —</option>',ol=(j.pr.olines||{})[S.pr.order]||[];(j.pr.orders||[]).forEach(function(x){oo+='<option value="'+x.id+'"'+(String(x.id)==S.pr.order?' selected':'')+'>'+esc(x.lab)+'</option>';});
  h+='<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center"><span>Against order</span><select data-pro=1 style="font-size:13px;padding:3px;max-width:340px">'+oo+'</select>'+(ol.length?'<a href="#" data-prfill=1 style="font-size:13px">Fill the lines from this order</a>':'')+'</div>';}
 if(!j.pr.counts){h+='<div class=muted>'+esc(j.pr.why)+'.</div>';}if(j.pr.noread){h+='<div class=muted>'+(j.pr.filled?'No items read — filled from the order; correct anything that differs on the slip.':'No items read — fill the line by hand.')+'</div>';}
 S.pr.lines.forEach(function(l,i){var o='<option value="">— product —</option>',bl='';(j.pr.items||[]).forEach(function(x){o+='<option value="'+x.id+'"'+(String(x.id)==l.item?' selected':'')+'>'+esc(x.name)+(x.rare?' (rarely used)':'')+'</option>';if(String(x.id)==l.item){bl=(x.brands||[]).join(', ');}});
  if(j.pr.owner){o+='<option value=new'+(l.item=='new'?' selected':'')+'>+ Add to the list</option>';}
  o+='<option value=ask'+(l.item=='ask'?' selected':'')+'>Not on the list — for Dr Manoj</option><option value=free'+(l.item=='free'?' selected':'')+'>Not a list item (by its name)</option>';
  var p='';(j.pr.places||[]).forEach(function(x){p+='<option value="'+x[0]+'"'+(x[0]==l.place?' selected':'')+'>'+esc(x[1])+'</option>';});
  h+='<div class=prl style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;border-top:1px solid #e6ebf0;padding:6px 0 2px">'+(l.hand?'<input data-prn="'+i+'" value="'+esc(l.name)+'" placeholder="what it is" style="width:150px;font-size:13px;padding:4px">':'<span style="min-width:120px">'+esc(l.name)+'</span>')
   +'<input data-prq="'+i+'" value="'+esc(l.qty)+'" inputmode=decimal placeholder="qty" style="width:56px;font-size:13px;padding:4px"><span class=muted>'+esc(l.unit||'')+'</span>'
   +'<select data-pri="'+i+'" style="font-size:13px;padding:3px;max-width:230px">'+o+'</select>'
   +'<input data-prb="'+i+'" value="'+esc(l.brand)+'" placeholder="brand" title="'+esc(bl?('Brands: '+bl):'Brand, if written')+'" style="width:90px;font-size:13px;padding:4px">'
   +'<select data-prp="'+i+'" style="font-size:13px;padding:3px">'+p+'</select>'+((l.sug&&!l.saved)?'<span class=muted>suggested</span>':'')+'<span class=err data-prf="'+i+'"></span></div>';});
 h+='<a href="#" data-pradd=1 style="font-size:13px">+ Another line</a>';
 box.innerHTML=h;box.setAttribute('data-for',String(j.id));box.style.display='flex';s634flags();cue();}
function s634body(b,j){if(S.dest=='procedure'&&j.pr&&S.pr){b.pr_lines=S.pr.lines.map(function(l){return {no:l.no,name:l.name,qty:l.qty,unit:l.unit,brand:l.brand,place:l.place,item:l.item,sug:!!(l.sug&&!l.saved)};});b.pr_role=S.pr.role=='order'?'order':'slip';b.pr_order=S.pr.role=='order'?'':S.pr.order;b.pr_book=S.pr.role=='order'?S.pr.book:'';}}
document.addEventListener('input',function(e){var t=e.target;if(!S.pr||!t.hasAttribute){return;}
 if(t.hasAttribute('data-prq')){var lq=S.pr.lines[+t.getAttribute('data-prq')];lq.qty=t.value;lq.sug=false;}else if(t.hasAttribute('data-prn')){S.pr.lines[+t.getAttribute('data-prn')].name=t.value;}
 else if(t.hasAttribute('data-prb')){S.pr.lines[+t.getAttribute('data-prb')].brand=t.value;}else if(t.hasAttribute('data-prbk')){S.pr.book=t.value;}});
document.addEventListener('change',function(e){var t=e.target;if(!S.pr||!t.hasAttribute){return;}
 if(t.hasAttribute('data-pri')){var l=S.pr.lines[+t.getAttribute('data-pri')];l.item=t.value;l.sug=false;s634flags();}
 else if(t.hasAttribute('data-prp')){var lp=S.pr.lines[+t.getAttribute('data-prp')];lp.place=t.value;lp.sug=false;s634flags();}
 else if(t.hasAttribute('data-prr')||t.hasAttribute('data-pro')){if(t.hasAttribute('data-prr')){S.pr.role=t.value;}else{S.pr.order=t.value;}var bo=$('pr634');if(bo){bo.removeAttribute('data-for');}s634paint(S.cur);}});
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-pradd]'):null;if(!t||!S.pr||!S.cur){return;}e.preventDefault();
 var n=0;S.pr.lines.forEach(function(l){if(l.no>n){n=l.no;}});S.pr.lines.push({no:n+1,name:'',qty:'',unit:'',brand:'',place:'proc',item:'',hand:true,sug:false,saved:false,orth:false});
 var bx=$('pr634');if(bx){bx.removeAttribute('data-for');}s634paint(S.cur);});
// S635_PROCROOM_ORDERS: the order's lines into the panel on one tap (product, quantity, brand, place -- no rate)
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-prfill]'):null;if(!t||!S.pr||!S.cur||!S.cur.pr){return;}e.preventDefault();
 var ol=(S.cur.pr.olines||{})[S.pr.order]||[];if(!ol.length){return;}S.pr.lines=ol.map(function(x,k){return {no:k+1,name:x.name,qty:x.qty,unit:x.unit||'',brand:x.brand||'',place:x.place||'proc',item:String(x.item==null?'':x.item),hand:false,sug:true,saved:false,orth:x.place=='sanj'};});
 var bf=$('pr634');if(bf){bf.removeAttribute('data-for');}s634paint(S.cur);cue();});
// S571_BATTERIES: "Battery fitted at <place> on <date> — this bill?" -- one tap links it (its own POST; the paper is never changed);
// a linked paper still waiting: "Where does it go?" pre-selected from the place's payer, in the browser only -- nothing is saved until Save
function s571init(j){var b=j.bat||null;S.pre571='';if(b&&b.pre&&!S.dest){S.dest=b.pre;S.pre571=b.pre;}}
function s571paint(j){var x=$('bt571');if(!x){return;}var b=j.bat||null,h='';
 if(b&&b.linked){h+='<div class=paidline id=bt571linked>'+esc(b.linked)+((S.pre571&&S.dest==S.pre571)?' “'+esc(C.names[S.pre571]||S.pre571)+'” is pre-chosen from the place’s payer ('+esc(b.payer||'')+') — nothing is saved until Save.':'')+'</div>';}
 ((b&&b.offers)||[]).forEach(function(o){h+='<div class=bt571o>'+esc(o.text)+' <button type=button class=b data-bt571="'+o.fit+'">Yes — link it</button></div>';});
 x.innerHTML=h;x.style.display=h?'flex':'none';}
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-bt571]'):null;if(!t||!S.cur||!S.cur.bat){return;}var j=S.cur;
 jpost(j.bat.link,{fit:parseInt(t.getAttribute('data-bt571'),10),paper:j.id,as:'bill'}).then(function(r){if(!r.ok){$('err').textContent=r.error||'Not linked.';return;}$('savednote').textContent=r.message;openPaper(j.id);});});
$('readbox').addEventListener('toggle',function(){S.readopen=$('readbox').open;cue();});
window.addEventListener('resize',cue);
loadList(C.open||0);
})();
</script></body></html>"""


def desk_page():
    db = AR.get_db()
    owner = _owner()
    groups = [[t, [list(d) for d in items if (d[0] != "personal" or owner)]] for t, items in DESTINATIONS]
    cfg = {"list": url_for("s551_api_list"), "paper": url_for("s551_api_paper", bid=0), "find": url_for("s551_api_find"),
           "save": url_for("s551_api_save"), "groups": groups, "kinds": [list(k) for k in KINDS], "notes": NOTES, "owner": owner,
           "fix": url_for("s560_fix"), "void": url_for("s560_void"), "restore": url_for("s563_restore"), "modes": [list(m) for m in PAY_MODES],
           "names": {k: v for k, v in DEST_NAME.items() if (k != "personal" or owner)}}      # S560
    n = len(waiting(db, owner))
    cfg["open"], cant = _s559_open(db, owner, request.args.get("open"))      # S559 item 3
    return render_template_string(DESK_TPL, bg=_bg(), cfg=cfg, n=n, owner=owner, chip=_chip(db), title="Sorting desk", cant=cant,
                                  add_href=(url_for("s568_add") if "s568_add" in AR.app.view_functions else ""))      # S568 item 7


def _s559_open(db, owner, v):
    """S559 item 3: (the paper's id, '') when /desk?open= names a paper this person may open on the desk -- by id, or by
    its stamp; (0, the line) when it names one that is unknown ('No paper <typed>') or refused (_visible's reason: never
    pharmacy; Personal only for the owner); (0, '') when nothing is named. S566 item 8: a bare number stays the record id
    (every link the app makes carries it); a stamp is read as B-0162, b-0162, B-162, B162 or b162 (_s566_stamp_form)."""
    v = re.sub(r"\s+", "", str(v or ""))[:20]
    if not v:
        return 0, ""
    try:
        b = _row(db, int(v)) if v.isdigit() else _by_stamp(db, _s566_stamp_form(v))
    except (ValueError, OverflowError, sqlite3.Error):
        b = None
    if b is None:
        return 0, "No paper %s" % v
    err = _visible(b, owner)
    if err:
        return 0, err
    return b["id"], ""


def api_list():
    return jsonify(list_json(AR.get_db(), _owner()))


def api_paper(bid):
    db = AR.get_db()
    b = _row(db, bid)
    err = _visible(b, _owner())
    if err:
        return jsonify(ok=False, error=err), (404 if not b else 403)
    return jsonify(paper_json(db, b, _owner()))


def api_find():
    db = AR.get_db()
    b = _by_stamp(db, request.args.get("no"))
    err = _visible(b, _owner())
    if err:
        return jsonify(ok=False, error=("There is no paper numbered %s." % (request.args.get("no") or "").strip()[:20]) if not b else err), (404 if not b else 403)
    return jsonify(ok=True, id=b["id"], stamp=_stamp(b))


def api_save():
    db = AR.get_db()
    p = request.get_json(silent=True) or {}
    try:
        bid = int(p.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="No paper was given."), 400
    try:
        res = save(db, bid, p)
        db.commit()
    except DeskError as e:
        db.rollback()
        return jsonify(ok=False, error=str(e)), e.code
    except Exception as e:                                           # noqa: BLE001
        db.rollback()
        return jsonify(ok=False, error="The save did not go through (%s). Nothing was changed." % type(e).__name__), 500
    nxt = [x["id"] for x in list_json(db, _owner())["papers"] if x["id"] != bid]
    res.update(ok=True, next=(nxt[0] if nxt else 0))
    return jsonify(res)


PAGE_HEAD = HEAD + """</head><body>{{s559_bar() if s559_bar is defined else ''}}"""      # S559 item 1: Bills awaited, the ledger, The month

AWAITED_TPL = PAGE_HEAD + """<div class=top><a href="{{url_for('s551_desk')}}" style="font-size:14px">‹ Sorting desk</a><span class=t>Bills awaited — challans by supplier</span><span class=muted style="font-size:14px">Each supplier is set once to how they actually bill.</span></div>
{% if msg %}<div class="msg{{' bad' if bad else ''}}">{{msg}}</div>{% endif %}
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;padding:14px 18px">
{% for s in cards %}<div class=card style="display:flex;flex-direction:column;gap:10px">
<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:17px">{{s.name}}</b><span class=muted style="font-size:13px">{{s.what}}</span></div>
{% if not s.noread %}<div style="display:flex;flex-direction:column;gap:6px"><span class="muted small">How they bill</span>
<div style="display:flex;flex-wrap:wrap;gap:6px">{% for k, nm in modes %}<form method=post action="{{url_for('s551_awaited_mode')}}" style="margin:0"><input type=hidden name=key value="{{s.key}}"><input type=hidden name=name value="{{s.name}}"><input type=hidden name=mode value="{{k}}"><button class="b{{' on' if s.mode==k else ''}}">{{nm}}</button></form>{% endfor %}</div>
<span style="font-size:13px;color:#3d4a57;background:#f3f5f8;border-radius:8px;padding:8px 10px">{{s.rule}}</span></div>
{% else %}<span id=s566noread style="font-size:13px;color:#3d4a57;background:#f3f5f8;border-radius:8px;padding:8px 10px">The supplier is not read on these challans. Open each on the sorting desk and type the supplier; it then joins that supplier's card.</span>{% endif %}
<div style="display:flex;flex-direction:column;border:1px solid #e6ebf0;border-radius:8px">{% for r in s.rows %}<div style="padding:9px 10px;border-bottom:1px solid #eef1f4;background:{{'#fff1d6' if r.amber else '#fff'}}" class="{{'amber-row' if r.amber else ''}}">
<div style="display:flex;justify-content:space-between;font-size:14px"><b><a href="{{s559_href(r.id) if s559_href is defined else url_for('bill_view',bid=r.id)}}" style="text-decoration:none;color:inherit">{{r.stamp}}</a> · {{r.date}}</b><span>{{r.age}}</span></div>
<div style="font-size:13px;color:#3d4a57;margin-top:3px">{{r['items']}}</div></div>{% endfor %}</div>
<div style="font-size:13px;color:#3d4a57">{{s.foot}}</div>
{% if s.mode=='paid' and s.unpaid %}<form method=post action="{{url_for('s551_awaited_pay')}}" style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px;align-items:end;margin:0">
<label class="muted small" style="grid-column:1/3">Paper<select name=bid style="display:block;width:100%">{% for u in s.unpaid %}<option value="{{u.id}}">{{u.stamp}}{% if u.amount is not none %} · {{inr(u.amount)}}{% endif %}</option>{% endfor %}</select></label>
<label class="muted small">Paid on<input name=paid_on placeholder="dd-mm-yyyy" style="display:block;width:100%"></label>
<label class="muted small">Amount<input name=amount placeholder="₹" style="display:block;width:100%"></label>
<button class=go style="grid-column:1/3">Note payment</button></form>{% endif %}
</div>{% endfor %}
{% if not cards %}<div class=card><b>No challan is waiting for its bill.</b></div>{% endif %}</div>
<div style="padding:0 18px 14px;font-size:13px" class=muted>Any other supplier’s challan waits here and turns amber after {{amber}} days. Challans never go into the accountants’ pack — only bills do (a paid-on-challan paper with its payment counts as the bill). Pharmacy challans are the Sanjeevni side’s and are not listed here.</div></body></html>"""

LEDGER_TPL = PAGE_HEAD + """<div class=top><a href="{{url_for('s551_desk')}}" style="font-size:14px">‹ Sorting desk</a><span class=t>Implant stock ledger</span><span class=muted style="font-size:14px">Your inventory only — a patient's implant bill belongs to the surgical case pack.</span></div>
{% if msg %}<div class="msg{{' bad' if bad else ''}}">{{msg}}</div>{% endif %}
<div style="display:flex;gap:14px;padding:14px 18px;align-items:flex-start">
<div class=card style="width:260px;flex:none;padding:0;overflow:hidden"><div class=muted style="padding:10px 12px;font-size:13px;border-bottom:1px solid #eef1f4">Implant suppliers</div>
{% for s in sups %}<a href="{{url_for('s551_implants', s=s.key)}}" style="display:block;text-decoration:none;color:#1f2a36;border-bottom:1px solid #eef1f4;padding:10px 12px;background:{{'#e3edf7' if cur and s.key==cur.key else '#fff'}}"><span style="display:block;font-size:15px;font-weight:700">{{s.name}}</span><span class=muted style="display:block;font-size:13px">balance {{inr(s.balance)}}</span></a>{% endfor %}
{% if not sups %}<p class=muted style="padding:12px;margin:0">No implant stock paper yet. On the desk, choose Implant stock.</p>{% endif %}</div>
{% if cur %}<div class=card style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:12px">
<div style="display:flex;justify-content:space-between;align-items:baseline"><b style="font-size:19px">{{cur.name}}</b><span class=muted style="font-size:13px" id=checked>{{cur.checked}}</span></div>
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px">
<div style="background:#f3f5f8;border-radius:10px;padding:10px 12px"><div class="muted small">Owed (bills and priced challans)</div><div style="font-size:20px;font-weight:700" id=owed>{{inr(cur.owed)}}</div></div>
<div style="background:#f3f5f8;border-radius:10px;padding:10px 12px"><div class="muted small">Paid</div><div style="font-size:20px;font-weight:700" id=paid>{{inr(cur.paid)}}</div></div>
<div style="background:#fff4dc;border-radius:10px;padding:10px 12px"><div class="muted small">Balance</div><div style="font-size:20px;font-weight:700" id=balance>{{inr(cur.balance)}}</div></div></div>
<div style="border:1px solid #e6ebf0;border-radius:8px;overflow:auto">
<div style="display:grid;grid-template-columns:90px 90px 120px minmax(0,1fr) 110px 110px;gap:8px;padding:8px 10px;font-size:12px;background:#f3f5f8" class=muted><span>Date</span><span>Paper</span><span>Kind</span><span>Items</span><span style="text-align:right">Owed</span><span style="text-align:right">Paid</span></div>
{% for r in cur.rows %}<div style="display:grid;grid-template-columns:90px 90px 120px minmax(0,1fr) 110px 110px;gap:8px;padding:9px 10px;font-size:14px;border-top:1px solid #eef1f4">
<span>{{r.d}}</span><span>{% if r.bid %}<a href="{{s559_href(r.bid) if s559_href is defined else url_for('bill_view',bid=r.bid)}}">{{r.p}}</a>{% else %}{{r.p}}{% endif %}</span><span>{{r.k}}</span><span style="color:#3d4a57">{{r.i}}{% if r.pay %} <form method=post action="{{url_for('s551_implants_void')}}" style="display:inline;margin:0" onsubmit="return confirm('Void this payment? It stays on record, marked voided.')"><input type=hidden name=id value="{{r.pay}}"><input type=hidden name=s value="{{cur.key}}"><button class=b style="min-height:24px;padding:0 6px;font-size:11px">void</button></form>{% endif %}</span>
<span style="text-align:right">{{inr(r.o) if r.o is not none else ('—' if r.k.startswith('Challan') else '')}}</span><span style="text-align:right">{{inr(r.pd) if r.pd is not none else ''}}</span></div>{% endfor %}</div>
<div style="display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap">
<form method=post action="{{url_for('s551_implants_pay')}}" style="display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap;margin:0"><input type=hidden name=s value="{{cur.key}}">
<label class="muted small">Paid on<input name=day placeholder="dd-mm-yyyy" style="display:block;width:130px"></label>
<label class="muted small">Amount<input name=amount placeholder="₹" style="display:block;width:120px"></label>
<label class="muted small">How<select name=how style="display:block">{% for h in how %}<option>{{h}}</option>{% endfor %}</select></label>
<label class="muted small">Against<input name=against placeholder="bill no(s)" style="display:block;width:160px"></label>
<button class=go>Note payment</button></form><span style="flex-grow:1"></span>
<form method=post action="{{url_for('s551_implants_check')}}" style="margin:0"><input type=hidden name=s value="{{cur.key}}"><button class=b style="border-color:#2b5d8a;color:#2b5d8a;min-height:36px">Checked against their statement up to today</button></form></div>
<div class=muted style="font-size:13px">A challan with no price shows its items and waits for its bill (Bills awaited); it is owed only once priced. A joined challan shows its items and owes nothing — its bill owes. You or Shavez note payments here.</div></div>{% endif %}</div></body></html>"""

MONTH_TPL = PAGE_HEAD + """<div class=top><a href="{{url_for('s551_desk')}}" style="font-size:14px">‹ Sorting desk</a><span class=t>Scan app &amp; assets — the month</span>
<a class=b href="{{url_for('s551_month', ym=prev)}}" style="text-decoration:none;display:inline-flex;align-items:center">‹ {{short(prev)}}</a><b style="font-size:16px">{{label(ym)}}</b>{% if nxt %}<a class=b href="{{url_for('s551_month', ym=nxt)}}" style="text-decoration:none;display:inline-flex;align-items:center">{{short(nxt)}} ›</a>{% endif %}
<span style="flex-grow:1"></span></div>
{% if owner %}<div style="padding:10px 18px 0">{{switches}}</div>{% endif %}
<div style="display:flex;gap:14px;padding:14px 18px;align-items:flex-start">
<div style="flex:1 1 auto;min-width:0;display:flex;flex-direction:column;gap:10px">
{% for s in secs %}<details class=card style="padding:0" {{'open' if loop.first}} id="sec-{{s.key}}"><summary style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 14px;cursor:pointer;list-style:none">
<span style="font-size:16px;font-weight:700">{{s.name}}</span><span class=muted style="font-size:13px;flex-grow:1">{{s.papers}}{% if s.noamt %} · {{s.noamt}} with no amount read{% endif %}</span><span style="font-size:17px;font-weight:700" class=sectotal data-total="{{'%.2f'|format(s.total)}}">{{inr(s.total)}}</span><span class=muted>▾</span></summary>
<div style="border-top:1px solid #eef1f4">
<div style="display:grid;grid-template-columns:minmax(0,1fr) 110px 120px 140px;gap:8px;padding:8px 14px;font-size:12px;background:#f6f8fa" class=muted><span>Item</span><span style="text-align:right">Quantity</span><span style="text-align:right">Rate now</span><span style="text-align:right">Rate before</span></div>
{% for it in s.rows %}<div style="display:grid;grid-template-columns:minmax(0,1fr) 110px 120px 140px;gap:8px;padding:8px 14px;font-size:14px;border-top:1px solid #f0f2f5"><span>{{it.n}}</span><span style="text-align:right">{{it.q}}</span><span style="text-align:right">{{it.r}}</span><span style="text-align:right" class=muted>{{it.b}}</span></div>{% endfor %}
{% if not s.rows %}<p class=muted style="margin:8px 14px">No items this month.</p>{% endif %}
{% for e in s.eq %}<div style="padding:8px 14px;font-size:14px;border-top:1px solid #f0f2f5"><a href="{{s559_href(e.bid) if s559_href is defined else url_for('bill_view',bid=e.bid)}}">{{e.stamp}}</a> · {{e.vendor or 'supplier not read'}} · {{inr(e.amount)}}
{% if e.asset %} · <a href="{{url_for('asset_view',aid=e.asset)}}">{{e.asset_name or 'its machine'}}</a>{% elif e.add_to %} · <a href="{{url_for('s557_from_paper', bid=e.add_to[1]) if e.add_to[0]=='machine' else url_for('asset_edit', bill_item=e.add_to[1])}}">+ asset record</a>{% elif e.status=='draft' %} · <span class=muted>Waiting for Dr Manoj's Save</span>{% endif %}</div>{% endfor %}
</div></details>{% endfor %}</div>
<div style="width:320px;flex:none;display:flex;flex-direction:column;gap:10px">
<div class=card style="display:flex;flex-direction:column;gap:6px" id=keptapart><b style="font-size:15px">Kept apart</b>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>Pharmacy — Sanjeevni</span><b>{{apart.pharmacy}} scan{{'' if apart.pharmacy==1 else 's'}}</b></div>
{% if apart.pexp %}<div id=s568pexp style="display:flex;justify-content:space-between;gap:8px;font-size:14px"><span>Sanjeevni — pharmacy expenses</span><b>{{apart.pexp}} · {{inr(apart.pexp_total)}} · paid by Dr MK's card</b></div>{% endif %}
<div style="display:flex;justify-content:space-between;font-size:14px"><span>NK Pathology</span><b>{{apart.lab}} scan{{'' if apart.lab==1 else 's'}}</b></div>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>Personal expenses</span><b>Dr MK {{apart.mk}} · Dr Bhawna {{apart.bh}}</b></div>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>A patient's paper (case pack)</span><b id=patients>{{apart.patient}}</b></div></div>
<div class=card style="display:flex;flex-direction:column;gap:6px"><b style="font-size:15px">Not in the totals</b>
<div style="font-size:14px">Challans waiting for a bill — counted by quantity only ({{nwait}})</div>
<div style="font-size:14px">Papers still to sort ({{nsort}}) — <a href="{{url_for('s551_desk')}}">open the desk</a></div></div>
<div class=muted style="font-size:13px">One page replaces “Clinic consumables by month” and “Consumption &amp; rate history”. The month is the one set on the bill, else its bill date, else the month it was scanned; from 22-Oct-2026 a bill dated in an earlier month than its scan counts in its own month (a person's earlier month still wins); supplier spellings are merged. An estimate slip and a paid-on-challan paper count in money; a challan still waiting counts by quantity only.</div></div></div></body></html>"""

def _msg_args():
    m = (request.args.get("msg") or "")[:200]
    return m, request.args.get("bad") == "1"


def awaited_page():
    db = AR.get_db()
    cards, amber = awaited(db, _owner())
    m, bad = _msg_args()
    return render_template_string(AWAITED_TPL, bg=_bg(), title="Bills awaited", cards=cards, modes=MODES, amber=amber, inr=_inr, msg=m, bad=bad)


def _back_to(ep, msg, bad=False, **kw):
    return redirect(url_for(ep, msg=msg, **(dict(bad=1) if bad else {}), **kw))


def awaited_mode():
    db = AR.get_db()
    key = (request.form.get("key") or "").strip()
    mode = (request.form.get("mode") or "").strip()
    if not key:
        return _back_to("s551_awaited", "No supplier was given.", True)
    try:
        n = set_mode(db, key, mode, (request.form.get("name") or "").strip()[:80])
        db.commit()
    except DeskError as e:
        db.rollback()
        return _back_to("s551_awaited", str(e), True)
    return _back_to("s551_awaited", "Saved: %s — %s.%s" % ((request.form.get("name") or key)[:60], dict(MODES)[mode],
                                                              (" %d challan%s now the final paper." % (n, "" if n == 1 else "s")) if n else ""))


def awaited_pay():
    db = AR.get_db()
    try:
        bid = int(request.form.get("bid") or 0)
        d, amt = note_paid(db, bid, request.form.get("paid_on"), request.form.get("amount"))
        db.commit()
    except (DeskError, ValueError) as e:
        db.rollback()
        return _back_to("s551_awaited", str(e) if isinstance(e, DeskError) else "Choose the paper.", True)
    return _back_to("s551_awaited", "Payment noted: %s on %s." % (_inr(amt), _dmy(d)))


def implants_page():
    db = AR.get_db()
    sups = sorted(ledger(db).values(), key=lambda s: s["name"].lower())
    k = request.args.get("s") or ""
    cur = next((s for s in sups if s["key"] == k), sups[0] if sups else None)
    m, bad = _msg_args()
    return render_template_string(LEDGER_TPL, bg=_bg(), title="Implant stock ledger", sups=sups, cur=cur, how=HOW, inr=_inr, msg=m, bad=bad)


def implants_pay():
    db = AR.get_db()
    key = (request.form.get("s") or "").strip()
    if key not in ledger(db):
        return _back_to("s551_implants", "Choose an implant supplier.", True)
    try:
        d = typed_date(request.form.get("day"))                      # S555 item 2: dd-mm-yyyy, d-m-yy, dd/mm/yyyy, yyyy-mm-dd
        amt = _amount(request.form.get("amount"))
    except DeskError as e:
        return _back_to("s551_implants", str(e), True, s=key)
    how = request.form.get("how") if request.form.get("how") in HOW else None
    if not (d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) and _iso(d)) or not amt or amt <= 0 or not how:
        return _back_to("s551_implants", "Type the day, the amount and how it was paid.", True, s=key)
    against = re.sub(r"\s+", " ", request.form.get("against") or "").strip()[:120]
    cur = db.execute("INSERT INTO implant_payment(supplier_key, day, amount, how, against, by_whom, at) VALUES(?,?,?,?,?,?,?)",
                     (key, d, amt, how, against, _who(), AR._now_ist()))
    _audit_desk(db, "implant_payment", {"id": cur.lastrowid, "supplier": key, "day": d, "amount": amt, "how": how, "against": against})
    db.commit()
    return _back_to("s551_implants", "Payment noted: %s on %s." % (_inr(amt), _dmy(d)), s=key)


def implants_void():
    db = AR.get_db()
    key = (request.form.get("s") or "").strip()
    try:
        pid = int(request.form.get("id") or 0)
    except ValueError:
        pid = 0
    r = db.execute("SELECT * FROM implant_payment WHERE id=? AND voided_at=''", (pid,)).fetchone()
    if not r:
        return _back_to("s551_implants", "That payment is not there (or already voided).", True, s=key)
    db.execute("UPDATE implant_payment SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (AR._now_ist(), _who(), pid))
    _audit_desk(db, "implant_payment_void", {"id": pid, "supplier": r["supplier_key"], "amount": r["amount"]})
    db.commit()
    return _back_to("s551_implants", "Payment voided (kept on record).", s=r["supplier_key"])


def implants_check():
    db = AR.get_db()
    key = (request.form.get("s") or "").strip()
    if key not in ledger(db):
        return _back_to("s551_implants", "Choose an implant supplier.", True)
    upto = _today().isoformat()
    db.execute("INSERT INTO implant_check(supplier_key, upto, by_whom, at) VALUES(?,?,?,?)", (key, upto, _who(), AR._now_ist()))
    _audit_desk(db, "implant_check", {"supplier": key, "upto": upto})
    db.commit()
    return _back_to("s551_implants", "Checked against their statement up to %s." % _dmy(upto), s=key)


def month_page():
    db = AR.get_db()
    owner = _owner()
    this = _today().strftime("%Y-%m")
    ym = request.args.get("ym", "")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym or ""):
        ym = this
    secs, apart, nwait = month_data(db, ym, owner)
    return render_template_string(MONTH_TPL, bg=_bg(), title="The month", secs=secs, apart=apart, nwait=nwait, ym=ym,
                                  prev=_ym_shift(ym, -1), nxt=(_ym_shift(ym, 1) if ym < this else None),
                                  label=AR._month_label, short=lambda x: AR._month_label(x).split(" ")[0], inr=_inr, owner=owner,
                                  switches=switches_card(AR._here(full=True)) if owner else "",
                                  nsort=len(waiting(db, owner)))


def switch():
    key = request.form.get("key") or ""
    on = request.form.get("on") or ""
    if key not in dict(SWITCHES) or on not in ("0", "1"):
        abort(400)
    db = AR.get_db()
    old = _setting(db, key, "off")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, "on" if on == "1" else "off"))
    _audit_desk(db, "switch", {"key": key, "from": old, "to": "on" if on == "1" else "off"})
    db.commit()
    return redirect(AR._safe_from(request.form.get("back")) or url_for("s551_desk"))


# ---------------------------------------------------------------------------------------------- S560_RECEIPTS_STATEMENTS (D728)
# The owner's rulings, 14-Oct-2026: a Receipt and a Statement are paper kinds, NEVER counted as spend (the bill is); a receipt
# pays one bill (or a statement, or "No bill -- paid directly"); a statement pays several invoices by one cheque; a bill can be
# marked paid directly. ONE payment record (paper_payment + paper_payment_bill) -- a re-save updates it in place, the old values
# kept in payment_changed (FIX1 B1); a mistake is voided -- every bill
# reference carrying its fingerprint (bill_created_at, S557's rule) so a re-issued id never inherits a payment. Construction
# bills may be marked "Send to accountant". Existing papers are fixed only by a person's tap: the desk lists them at the top of
# Waiting, with the reason; nothing is changed by a data step and no paper is special-cased by its stamp.
# FIX1 (15-Oct-2026) B1: a payment is recorded ONCE -- re-saving a receipt / statement, or "Paid on ... — change?" on a paid bill,
# changes the payment already recorded (its old allocation rows voided, kept; new ones written); an allocation never exceeds what
# the bill still owes.
# FIX2 (15-Oct-2026) C4: a receipt / statement saved as any other kind -- in the same Save its own live payment is voided (and
# that payment's allocations), audited; on the clinic lane the paper goes back to draft so the Save's normal accept runs.
NOT_SPEND = ("receipt", "statement")
PAY_MODES = (("cash", "Cash"), ("cheque", "Cheque"), ("bank", "Bank / UPI"))
PAY_WORD = dict(PAY_MODES)
RECEIPT_WORDS = ("receipt", "money receipt", "received with thanks", "payment received", "received from")
STATEMENT_WORDS = ("statement", "statement of account", "ledger", "account statement")
RECEIPT_DAYS = 180                 # the bills a receipt may pay: the supplier's, of the last 180 days, not yet fully paid
RECEIPT_MATCH_DAYS = 60            # the likely one: exactly one bill of the same amount within 60 days
STATEMENT_SLACK = 7                # a statement's invoices: inside its period, give or take 7 days
FIX_TEXT = {"blank": "Set aside as blank, but it reads as a bill — restore?",
            "receipt": "This looks like a receipt",
            "statement": "This looks like a statement"}


def _s560_fp(b):
    return (_col(b, "created_at") or "")


def _s560_file(bid):
    try:
        return url_for("bill_file", bid=bid)
    except RuntimeError:                                             # outside a request (a walk's direct call)
        return "/bills/%d/file" % bid


def _s560_live_allocs(db, b):
    """The live allocations of this bill (not voided; its fingerprint holds): rows of paper_payment + alloc."""
    try:
        return db.execute("SELECT p.*, a.amount AS alloc FROM paper_payment_bill a JOIN paper_payment p ON p.id=a.payment_id "
                          "WHERE a.bill_id=? AND a.bill_created_at=? AND p.voided_at='' AND a.voided_at='' ORDER BY p.paid_on, p.id",
                          (b["id"], _s560_fp(b))).fetchall()
    except sqlite3.Error:
        return []


def _s560_proof(db, p):
    """The receipt / statement paper of a payment, when its fingerprint still holds; else None."""
    if not p["proof_bill_id"]:
        return None
    try:
        r = db.execute("SELECT id, stamp_no, source_stored, created_at, doc_kind FROM bills WHERE id=?", (p["proof_bill_id"],)).fetchone()
    except sqlite3.Error:
        return None
    return r if (r is not None and (r["created_at"] or "") == (p["proof_created_at"] or "")) else None


def _s560_state(total, paid):
    if not paid or paid <= 0:
        return "unpaid"
    try:
        if total is None or float(paid) + 0.5 >= float(total):
            return "paid"
    except (TypeError, ValueError):
        return "paid"
    return "part"


def _s560_pay_text(paid_on, amount, mode, ref):
    return "Paid %s · %s · %s%s" % (_dmy(paid_on), _inr(amount), PAY_WORD.get(mode, mode or ""),
                                     (" · no. " + ref) if ref else "")


def paid_state(db, b):
    """A bill's paid state (S560 item 5): the sum of its live allocations (and the paid-on-challan payment kept on the paper
    itself, bills.paid_on / paid_amount, read alongside) against its total_amount -> dict(state 'paid' | 'part' | 'unpaid' | ''
    for a receipt / statement, word, paid, total, lines [dict(text, pid, proof_id, proof_stamp, file)], of)."""
    dk = (_col(b, "doc_kind") or "")
    out = {"state": "", "word": "", "paid": 0.0, "total": b["total_amount"], "lines": [], "of": ""}
    if dk in NOT_SPEND:
        try:
            pays = db.execute("SELECT * FROM paper_payment WHERE proof_bill_id=? AND proof_created_at=? AND voided_at='' ORDER BY id",
                              (b["id"], _s560_fp(b))).fetchall()
        except sqlite3.Error:
            pays = []
        bits = []
        for p in pays:
            n = []
            for a in db.execute("SELECT a.bill_id, a.amount, a.bill_created_at FROM paper_payment_bill a WHERE a.payment_id=? AND a.voided_at='' ORDER BY a.bill_id", (p["id"],)):
                r = db.execute("SELECT id, stamp_no, created_at FROM bills WHERE id=?", (a[0],)).fetchone()
                if r is not None and (r["created_at"] or "") == (a[2] or ""):
                    n.append(_stamp(r))
            bits.append(_s560_pay_text(p["paid_on"], p["amount"], p["mode"], p["ref"]) +
                        ((" — pays " + ", ".join(n)) if n else " — no bill, paid directly"))
            out["lines"].append({"text": bits[-1], "pid": p["id"], "proof_id": None, "proof_stamp": "", "file": ""})
        try:
            for a in db.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action='desk_receipt_to_statement' ORDER BY id DESC LIMIT 1", (b["id"],)):
                d = json.loads(a[0] or "{}")
                r = db.execute("SELECT id, stamp_no, created_at FROM bills WHERE id=?", (d.get("statement"),)).fetchone()
                if r is not None and (r["created_at"] or "") == (d.get("statement_created_at") or ""):
                    out["of"] = "Receipt for the statement %s" % _stamp(r)
        except (sqlite3.Error, TypeError, ValueError):
            pass
        if not out["of"] and bits:
            out["of"] = ("Receipt" if dk == "receipt" else "Statement") + " — " + "; ".join(bits)
        return out
    paid = 0.0
    for p in _s560_live_allocs(db, b):
        paid += p["alloc"] or 0
        pr = _s560_proof(db, p)
        out["lines"].append({"text": _s560_pay_text(p["paid_on"], p["alloc"], p["mode"], p["ref"]), "pid": p["id"],
                             "proof_id": pr["id"] if pr else None, "proof_stamp": _stamp(pr) if pr else "",
                             "file": _s560_file(pr["id"]) if (pr and pr["source_stored"]) else ""})
    if _col(b, "paid_on") and _col(b, "paid_amount"):
        paid += b["paid_amount"] or 0
        out["lines"].append({"text": "Paid %s · %s (noted on the paper)" % (_dmy(b["paid_on"]), _inr(b["paid_amount"])), "pid": None,
                             "proof_id": None, "proof_stamp": "", "file": ""})
    out["paid"] = paid
    out["state"] = _s560_state(b["total_amount"], paid)
    out["word"] = {"paid": "Paid", "part": "Part-paid %s of %s" % (_inr(paid), _inr(b["total_amount"])), "unpaid": ""}[out["state"]]
    return out


def paid_map(db):
    """{(bill id, bill created_at): the sum of its live allocations} -- one read for a list page (All papers, The month)."""
    try:
        return {(r[0], r[1] or ""): (r[2] or 0) for r in db.execute(
            "SELECT a.bill_id, a.bill_created_at, SUM(a.amount) FROM paper_payment_bill a JOIN paper_payment p ON p.id=a.payment_id "
            "WHERE p.voided_at='' AND a.voided_at='' GROUP BY a.bill_id, a.bill_created_at")}
    except sqlite3.Error:
        return {}


def state_from_map(pm, b):
    if (_col(b, "doc_kind") or "") in NOT_SPEND:
        return ""
    paid = pm.get((b["id"], _s560_fp(b)), 0) + ((_col(b, "paid_amount") or 0) if _col(b, "paid_on") else 0)
    return _s560_state(b["total_amount"], paid)


def _s560_pay_bills(db, pid):
    """FIX1 B1: {bill id: (bill_created_at, amount)} -- the live allocations of one payment (none when pid is None)."""
    if not pid:
        return {}
    try:
        return {r[0]: (r[1] or "", float(r[2] or 0)) for r in db.execute(
            "SELECT bill_id, bill_created_at, amount FROM paper_payment_bill WHERE payment_id=? AND voided_at=''", (pid,))}
    except sqlite3.Error:
        return {}


def _s560_mine(db, pid, row):
    """FIX1 B1: what this payment itself already allocates to this bill (its fingerprint must hold)."""
    x = _s560_pay_bills(db, pid).get(row["id"])
    return x[1] if (x and x[0] == _s560_fp(row)) else 0.0


def _s560_outstanding(db, b, pid=None):
    """What the bill still owes -- leaving out what payment `pid` itself pays on it (a re-save changes that payment)."""
    st = paid_state(db, b)
    if b["total_amount"] is None:
        return None
    return max(0.0, float(b["total_amount"]) - (st["paid"] - _s560_mine(db, pid, b)))


def _s560_cap(amt, owes):
    """FIX1 B1: an allocation is capped at what the bill still owes."""
    return round(float(amt), 2) if owes is None else round(max(0.0, min(float(amt), float(owes))), 2)


def _s560_proof_pay(db, proof):
    """FIX1 B1: the live payment this receipt / statement already recorded (the latest), or None."""
    if proof is None:
        return None
    try:
        return db.execute("SELECT * FROM paper_payment WHERE proof_bill_id=? AND proof_created_at=? AND voided_at='' ORDER BY id DESC LIMIT 1",
                          (proof["id"], _s560_fp(proof))).fetchone()
    except sqlite3.Error:
        return None


def _s560_stmt_link(db, b):
    """The statement this receipt was linked to (its fingerprint holding), or None."""
    try:
        a = db.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action='desk_receipt_to_statement' ORDER BY id DESC LIMIT 1", (b["id"],)).fetchone()
        if not a:
            return None
        d = json.loads(a[0] or "{}")
        r = db.execute("SELECT id, created_at FROM bills WHERE id=?", (d.get("statement"),)).fetchone()
        return r["id"] if (r is not None and (r["created_at"] or "") == (d.get("statement_created_at") or "")) else None
    except (sqlite3.Error, TypeError, ValueError):
        return None


def _s560_direct_edit(db, b, st=None):
    """FIX1 B1: 'Paid?' on a bill already fully paid -> (the one direct payment it changes, '') or (None, why it cannot)."""
    if (_col(b, "doc_kind") or "") in NOT_SPEND:
        return None, ""
    st = st or paid_state(db, b)
    if st["state"] != "paid":
        return None, ""
    pids = [ln["pid"] for ln in st["lines"] if ln["pid"]]
    noted = [ln for ln in st["lines"] if not ln["pid"]]
    if len(pids) == 1 and not noted:
        p = db.execute("SELECT * FROM paper_payment WHERE id=? AND voided_at=''", (pids[0],)).fetchone()
        if p is not None and not p["proof_bill_id"] and len(_s560_pay_bills(db, p["id"])) == 1:
            return p, ""
        pr = _s560_proof(db, p) if p is not None else None
        if pr is not None:
            return None, "It is paid by %s — to change the payment, open that %s." % (
                _stamp(pr), "statement" if (pr["doc_kind"] or "") == "statement" else "receipt")
    if noted and not pids:
        return None, "Its payment is noted on the paper itself."
    return None, "It is paid by more than one payment — void the wrong one first."


def _s560_update_payment(db, pay, proof, allocs, f, note=""):
    """FIX1 B1: a re-save CHANGES the payment already recorded -- never a second one. Its date, amount, mode and ref are
    updated in place (the old values kept in the audit); when the bills it pays or their amounts change, its old allocation
    rows are voided (kept, with voided_at / voided_by) and the new ones written. Returns True when anything changed."""
    d, amt, mode, ref = f
    pid = pay["id"]
    old = sorted((r[0], r[1] or "", round(float(r[2] or 0), 2)) for r in db.execute(
        "SELECT bill_id, bill_created_at, amount FROM paper_payment_bill WHERE payment_id=? AND voided_at=''", (pid,)))
    new = sorted((row["id"], _s560_fp(row), round(float(a), 2)) for row, a in allocs)
    same_f = (pay["paid_on"], round(float(pay["amount"]), 2), pay["mode"], pay["ref"] or "") == (d, round(float(amt), 2), mode, ref)
    if same_f and old == new:
        return False
    now, who = AR._now_ist(), _who()
    if not same_f:
        db.execute("UPDATE paper_payment SET paid_on=?, amount=?, mode=?, ref=? WHERE id=? AND voided_at=''", (d, amt, mode, ref, pid))
    if old != new:
        vt, n = now, 1
        while db.execute("SELECT 1 FROM paper_payment_bill WHERE payment_id=? AND voided_at=? LIMIT 1", (pid, vt)).fetchone():
            n += 1
            vt = "%s #%d" % (now, n)
        db.execute("UPDATE paper_payment_bill SET voided_at=?, voided_by=? WHERE payment_id=? AND voided_at=''", (vt, who, pid))
        for row, a in allocs:
            db.execute("INSERT INTO paper_payment_bill(payment_id, bill_id, bill_created_at, amount) VALUES(?,?,?,?)",
                       (pid, row["id"], _s560_fp(row), round(float(a), 2)))
    det = {"payment": pid, "from": {"paid_on": pay["paid_on"], "amount": pay["amount"], "mode": pay["mode"], "ref": pay["ref"],
                                    "bills": [[x[0], x[2]] for x in old]},
           "to": {"paid_on": d, "amount": amt, "mode": mode, "ref": ref, "bills": [[x[0], x[2]] for x in new]}, "note": note, "via": "desk"}
    for bid_ in sorted({x[0] for x in old} | {x[0] for x in new}):
        AR._audit_bill(db, bid_, "payment_changed", det)
    if proof is not None:
        AR._audit_bill(db, proof["id"], "payment_changed", det)
    _audit_desk(db, "paper_payment_change", det)
    return True


def _s560_void_own(db, pay, proof, why):
    """FIX1 B1: a receipt re-saved as the receipt of a statement -- its own payment is voided (kept on record): the money is
    the statement's, counted once."""
    db.execute("UPDATE paper_payment SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (AR._now_ist(), _who(), pay["id"]))
    for x in sorted(_s560_pay_bills(db, pay["id"])):
        AR._audit_bill(db, x, "payment_voided", {"payment": pay["id"], "why": why, "via": "desk"})
    AR._audit_bill(db, proof["id"], "payment_voided", {"payment": pay["id"], "why": why, "via": "desk"})
    _audit_desk(db, "paper_payment_void", {"id": pay["id"], "amount": pay["amount"], "why": why})


def _s560_void_allocs(db, pid):
    """FIX2 C4: a voided payment's live allocation rows voided too (kept, with voided_at / voided_by). Returns how many."""
    now, who = AR._now_ist(), _who()
    vt, n = now, 1
    while db.execute("SELECT 1 FROM paper_payment_bill WHERE payment_id=? AND voided_at=? LIMIT 1", (pid, vt)).fetchone():
        n += 1
        vt = "%s #%d" % (now, n)
    return db.execute("UPDATE paper_payment_bill SET voided_at=?, voided_by=? WHERE payment_id=? AND voided_at=''", (vt, who, pid)).rowcount


def _s560_left(amt, a, row):
    return (" %s more than %s still owed — not counted on it." % (_inr(float(amt) - a), _stamp(row))) if float(amt) - a >= 0.005 else ""


def _s560_day(b):
    return _iso(b["bill_date"]) or _iso(b["created_at"])


def _s560_text(db, b, rd):
    bits = [b["vendor"] or "", b["bill_no"] or "", CP._items_text(db, b["id"])]
    if rd:
        bits += [rd.get("supplier") or "", rd.get("number") or ""] + [str(i.get("name") or "") for i in rd.get("items") or []]
    return re.sub(r"\s+", " ", " ; ".join(bits).lower()).strip()


def _s563_words_text(b, rd):
    """S563 (S560-N2): what the receipt / statement words are matched on -- the vendor, the bill number and Claude's supplier
    and number only, never an item name (a 'Receipt book' line on a stationery bill is goods, not a receipt). _s560_text, which
    _s560_prefill also reads for cash / cheque / UTR, is unchanged."""
    bits = [b["vendor"] or "", b["bill_no"] or ""]
    if rd:
        bits += [str(rd.get("supplier") or ""), str(rd.get("number") or "")]
    return re.sub(r"\s+", " ", " ; ".join(bits).lower()).strip()


def _s560_claude_kind(db, b, rd):
    """S560 item 2: the kind pre-chosen from Claude's reading (never saved alone) -> (kind or '', blocked). A reading whose
    text says receipt / statement pre-chooses it only when the reader's own kind allows it ('other': the reader has no receipt
    or statement kind) -- otherwise nothing is pre-chosen (blocked=True). Else the reader's kind as before."""
    t = _s563_words_text(b, rd)                                     # S563 (S560-N2): never the item names
    for k, words in (("receipt", RECEIPT_WORDS), ("statement", STATEMENT_WORDS)):
        if CP._hits(t, list(words)):
            return (k, False) if (rd and (rd.get("doc_kind") or "") == "other") else ("", True)
    if rd and CLAUDE_KIND.get(rd.get("doc_kind") or ""):
        return CLAUDE_KIND[rd["doc_kind"]], False
    return "", False


def _s560_prefill(db, b, rd):
    """The payment boxes pre-filled from what was read (Claude's reading first): date, amount, how, cheque / reference no."""
    amt = rd.get("amount") if (rd and rd.get("amount") is not None) else b["total_amount"]
    day = (rd.get("date") if rd else "") or (b["bill_date"] if _iso(b["bill_date"]) else "")
    t = _s560_text(db, b, rd)
    mode = "cheque" if re.search(r"\b(cheque|chq)\b", t) else ("bank" if re.search(r"\b(neft|rtgs|imps|upi|utr)\b", t) else
                                                             ("cash" if re.search(r"\bcash\b", t) else ""))
    m = re.search(r"\b(?:cheque|chq|utr|ref)\.?\s*(?:no\.?|number)?\s*[-:#]?\s*([0-9]{5,22})", t)
    return {"paid_on": _dmy(day) if day else "", "amount": _plain(amt), "mode": mode, "ref": m.group(1) if m else ""}


def _s560_payable(db, b, owner, today=None, days=RECEIPT_DAYS, pid=None):
    """The supplier's (by _supplier_key) bills and challans-turned-final of the last `days` days, NOT yet fully paid, newest
    first -- never this paper, a pharmacy paper, a patient's paper, a rejected one, a duplicate or a page; Personal only for
    the owner. FIX1 B1: the bills payment `pid` (this paper's own) already pays stay offered, owing what they owed before it.
    [(row, outstanding or None, its day)]."""
    today = today or _today()
    key = _key(b["vendor"])
    if not key:
        return []
    since = today - datetime.timedelta(days=days)
    own = _s560_pay_bills(db, pid)
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    out = []
    for r in db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE b.id<>? AND b.status<>'rejected' AND b.dup_of IS NULL "
                        "AND b.page_of IS NULL AND COALESCE(b.lane,'clinic')<>'pharmacy' AND COALESCE(b.subgroup,'')<>'" + PATIENT + "'" + pers +
                        " AND (COALESCE(b.doc_kind,'bill')='bill' OR (b.doc_kind='challan' AND b.challan_state='final')) "
                        "ORDER BY b.id DESC LIMIT 3000", (b["id"],)):
        if _key(r["vendor"]) != key:
            continue
        x = own.get(r["id"])
        mine = x[1] if (x and x[0] == _s560_fp(r)) else 0.0
        d = _s560_day(r)
        if d is None or (d < since and not x):
            continue
        paid = paid_state(db, r)["paid"] - mine
        if not x and _s560_state(r["total_amount"], paid) == "paid":
            continue
        out.append((r, (max(0.0, float(r["total_amount"]) - paid) if r["total_amount"] is not None else None), d))
    out.sort(key=lambda x: (x[2], x[0]["id"]), reverse=True)
    return out


def _s560_cand(db, r, outst, d):
    return {"id": r["id"], "stamp": _stamp(r), "no": r["bill_no"] or "", "date": _dmy(d.isoformat()), "iso": d.isoformat(),
            "amount": _plain(r["total_amount"]), "inr": _inr(r["total_amount"]) if r["total_amount"] is not None else "no amount",
            "out": _plain(outst), "lane": AR._lane_word_s555(r), "dest": current_dest(r)}


def receipt_cands(db, b, owner, today=None, amt=None, day=None, pid=None):
    """S560 item 3: 'Pays which bill?' -- the likely one pre-ticked when EXACTLY one bill has the same amount within 60 days.
    FIX1 B1: a receipt that already recorded its payment (pid) has the bill that payment pays ticked (cur) instead."""
    rows = _s560_payable(db, b, owner, today, pid=pid)
    out = [_s560_cand(db, r, o, d) for r, o, d in rows]
    if pid:
        mine = _s560_pay_bills(db, pid)
        for c in out:
            if c["id"] in mine:
                c["cur"] = c["pre"] = True
        return out
    try:
        a = float(amt) if amt not in (None, "") else None
    except (TypeError, ValueError):
        a = None
    ref = _iso(day) or (today or _today())
    same = [c for (r, o, d), c in zip(rows, out) if a is not None and r["total_amount"] is not None
            and abs(float(r["total_amount"]) - a) < 0.5 and abs((ref - d).days) <= RECEIPT_MATCH_DAYS]
    if len(same) == 1:
        same[0]["pre"] = True
    return out


def statements_of(db, b, owner, today=None):
    """The supplier's statements (a receipt may pay a statement instead of one bill)."""
    key = _key(b["vendor"])
    if not key:
        return []
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    out = []
    for r in db.execute("SELECT b.* FROM bills b WHERE b.id<>? AND b.doc_kind='statement' AND b.status<>'rejected' AND b.dup_of IS NULL "
                        "AND COALESCE(b.lane,'clinic')<>'pharmacy'" + pers + " ORDER BY b.id DESC LIMIT 500", (b["id"],)):
        if _key(r["vendor"]) == key:
            out.append({"id": r["id"], "stamp": _stamp(r), "date": _dmy(r["bill_date"] or r["created_at"]),
                        "inr": _inr(r["total_amount"]) if r["total_amount"] is not None else "no amount", "dest": current_dest(r)})
    return out


def _s560_reading_lines(rd):
    n = 0
    for i in (rd.get("items") or []) if rd else []:
        try:
            if i.get("amount") not in (None, "") and math.isfinite(float(i.get("amount"))):
                n += 1
        except (TypeError, ValueError):
            pass
    return n


def _s560_looks_receipt(db, b, rd):
    """A filed paper whose Claude kind or read text says receipt: the text's words; or the reader's 'other' paper with an
    amount and no goods line, while the same supplier has a bill of that amount within 60 days."""
    if CP._hits(_s563_words_text(b, rd), list(RECEIPT_WORDS)):     # S563 (S560-N2)
        return True
    if not rd or (rd.get("doc_kind") or "") != "other" or rd.get("amount") is None or rd.get("items"):
        return False
    key = _key(b["vendor"] or rd.get("supplier"))
    if not key:
        return False
    d0 = _iso(rd.get("date")) or _s560_day(b) or _today()
    for r in db.execute("SELECT b.id, b.vendor, b.total_amount, b.bill_date, b.created_at FROM bills b WHERE b.id<>? AND b.dup_of IS NULL "
                        "AND COALESCE(b.doc_kind,'bill') IN ('bill','estimate') AND COALESCE(b.lane,'clinic')<>'pharmacy'", (b["id"],)):
        if _key(r["vendor"]) != key:
            continue
        amts = [r["total_amount"]]
        rr = reading(db, r["id"])
        if rr:
            amts.append(rr.get("amount"))
        d = _iso(r["bill_date"]) or _iso(r["created_at"])
        if d and abs((d0 - d).days) <= RECEIPT_MATCH_DAYS and any(x is not None and abs(float(x) - float(rd["amount"])) < 0.5 for x in amts):
            return True
    return False


def _s560_looks_statement(db, b, rd):
    """A single bill whose reading shows several invoice lines and a period: the text's words; or the reader's 'other' paper
    with three or more priced lines and no single bill number and no single date (the lines carry their own -- a period)."""
    if CP._hits(_s563_words_text(b, rd), list(STATEMENT_WORDS)):   # S563 (S560-N2)
        return True
    return bool(rd and (rd.get("doc_kind") or "") == "other" and _s560_reading_lines(rd) >= 3 and not rd.get("number") and not rd.get("date"))


def _s560_fix_of(db, b, owner, answered=None):
    """(key, text) when this paper is one to put right by one person's tap, else None. By rule only, never by stamp."""
    if b is None or _lane(b) == "pharmacy" or b["page_of"] or ((b["subgroup"] or "") == "personal" and not owner):
        return None
    if answered is None:
        answered = db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='desk_fix_answered' LIMIT 1", (b["id"],)).fetchone() is not None
    if answered:
        return None
    dk = b["doc_kind"] or ""
    if b["status"] == "rejected":
        if b["dup_of"] or not (b["reject_reason"] or "").lower().startswith("blank"):
            return None
        rd = reading(db, b["id"])
        if rd and (rd.get("supplier") or "").strip() and rd.get("amount") is not None:
            return ("blank", FIX_TEXT["blank"])
        return None
    if b["dup_of"] or dk in NOT_SPEND + ("challan",) or (b["subgroup"] or "") == PATIENT:
        return None
    rd = reading(db, b["id"])
    if rd and _s560_looks_receipt(db, b, rd):
        return ("receipt", FIX_TEXT["receipt"])
    if rd and _s560_looks_statement(db, b, rd):
        return ("statement", FIX_TEXT["statement"])
    if _lane(b) == "clinic" and (b["subgroup"] or "") in CONS and b["status"] in ("draft", "approved"):
        s = CP.suggest(db, b["vendor"], CP._items_text(db, b["id"]), bool(b["bill_no"]), b["total_amount"] is not None)
        if s and s["kind"] == "sub" and s["value"] == "resume":
            return ("resume", "looks like " + s["label"])                 # the existing grey hint (_hint's words)
    return None


def fixes(db, owner, today=None):
    """S560 item 7: the existing papers to put right, each by one person's tap, newest first -- [(row, key, text)]."""
    answered = {r[0] for r in db.execute("SELECT DISTINCT bill_id FROM bill_audit WHERE action='desk_fix_answered'")}
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    out = []
    for b in db.execute("SELECT b.*, " + CP.MONTH_OF + " AS mo FROM bills b WHERE COALESCE(b.lane,'clinic')<>'pharmacy' AND b.page_of IS NULL "
                        "AND b.dup_of IS NULL" + pers + " AND ((b.status='rejected' AND lower(COALESCE(b.reject_reason,'')) LIKE 'blank%') "
                        "OR (b.status<>'rejected' AND (EXISTS(SELECT 1 FROM claude_reading c WHERE c.bill_id=b.id AND c.ok=1) "
                        "OR (COALESCE(b.lane,'clinic')='clinic' AND b.subgroup IN ('procedure','xray_small','xray_11x14','others'))))) "
                        "ORDER BY b.id DESC LIMIT 1500"):
        if b["id"] in answered or _lane(b) == "pharmacy":
            continue
        f = _s560_fix_of(db, b, owner, answered=False)
        if f:
            out.append((b, f[0], f[1]))
    return out


def _s560_with_fixes(db, owner, out, today=None):
    """waiting() + the papers to put right, at the top of Waiting (each keeps its other reasons)."""
    try:
        fx = fixes(db, owner, today)
    except sqlite3.Error:
        return out
    if not fx:
        return out
    ids = {b["id"] for b, _k, _t in fx}
    why_of = {b["id"]: w for b, w in out}
    return [(b, ["fix:" + k] + why_of.get(b["id"], [])) for b, k, _t in fx] + [(b, w) for b, w in out if b["id"] not in ids]


def _s560_fix_hint(db, b, why):
    for w in why:
        if w.startswith("fix:"):
            k = w[4:]
            if k == "resume":
                f = _s560_fix_of(db, b, True, answered=False)
                return f[1] if f else "looks like Resumes"
            return FIX_TEXT.get(k, "")
    return None


def _s560_paper(db, b, owner, rd, today=None):
    """paper_json's S560 part: the paid state, the receipt's and the statement's lists, the pre-filled payment, the fix."""
    today = today or _today()
    own = _s560_proof_pay(db, b)                                    # FIX1 B1: the payment this paper already recorded
    pid = own["id"] if own is not None else None
    mine = _s560_pay_bills(db, pid)
    pre = _s560_prefill(db, b, rd)
    if own is not None:
        pre = dict(pre, paid_on=_dmy(own["paid_on"]), amount=_plain(own["amount"]), mode=own["mode"], ref=own["ref"] or "")
    st = paid_state(db, b)
    e, why = _s560_direct_edit(db, b, st)                           # FIX1 B1: "Paid on ... — change?"
    st["edit_no"] = why
    st["edit"] = ({"pid": e["id"], "paid_on": _dmy(e["paid_on"]), "amount": _plain(e["amount"]), "mode": e["mode"], "ref": e["ref"] or ""}
                  if e is not None else None)
    ons = [p_["paid_on"] for p_ in _s560_live_allocs(db, b)]
    st["last_on"] = _dmy(max(ons)) if ons else (_dmy(b["paid_on"]) if _col(b, "paid_on") else "")
    f = _s560_fix_of(db, b, owner)
    pay = []
    for r, o, d in _s560_payable(db, b, owner, today, pid=pid):
        c = _s560_cand(db, r, o, d)
        if r["id"] in mine:
            c["cur"] = True
        pay.append(c)
    frm, to, total = "", (pre["paid_on"] if (rd and rd.get("date")) else ""), pre["amount"]
    if own is not None and (b["doc_kind"] or "") == "statement":
        a = db.execute("SELECT detail FROM bill_audit WHERE bill_id=? AND action='desk_statement' ORDER BY id DESC LIMIT 1", (b["id"],)).fetchone()
        try:
            dd = json.loads(a[0] or "{}") if a else {}
        except (TypeError, ValueError):
            dd = {}
        frm, to = _dmy(dd.get("from")) if dd.get("from") else "", _dmy(dd.get("to")) if dd.get("to") else ""
        total = _plain(dd.get("total")) if dd.get("total") is not None else _plain(b["total_amount"])
    link = _s560_stmt_link(db, b) if (b["doc_kind"] or "") == "receipt" else None
    cur = ("none" if (own is not None and not mine) else ("st:%d" % link if (link and own is None) else ""))
    return {"pay": st, "fix": ({"key": f[0], "text": f[1]} if f else None), "aside": _s563_aside(b, f),      # S563 F-902
            "to_acc": bool(_col(b, "to_accountant")),
            "dk": b["doc_kind"] or "", "rc": dict(pre, cands=receipt_cands(db, b, owner, today, pre["amount"], parse_date(pre["paid_on"]), pid=pid),
                                                   stmts=statements_of(db, b, owner, today), cur=cur, recorded=own is not None or bool(link)),
            "st": dict(pre, frm=frm, to=to, total=total, cands=pay, recorded=own is not None)}


def _s560_pay_fields(r, need=True):
    """The payment typed on the desk -> (paid_on ISO, amount, mode, ref); refused with one plain line, nothing saved."""
    r = r or {}
    if not str(r.get("paid_on") or "").strip():
        if not need:
            return None
        raise DeskError("Type the day it was paid (dd-mm-yyyy). Nothing was saved.")
    d = typed_date(r.get("paid_on"))
    amt = _amount(r.get("amount"))
    if amt is None or amt <= 0:
        raise DeskError("Type the amount paid. Nothing was saved.")
    mode = str(r.get("mode") or "").strip().lower()
    if mode not in PAY_WORD:
        raise DeskError("Choose how it was paid: Cash, Cheque or Bank / UPI. Nothing was saved.")
    ref = re.sub(r"\s+", " ", str(r.get("ref") or "")).strip()[:60]
    return d, amt, mode, ref


def _s560_pre(db, b, p, dest, owner, today=None):
    """Before the Save's destination: the receipt / statement / 'Paid?' asked for, checked; the destination a receipt or a
    statement is FILED to (the lane of the bill it pays). Returns (dest, s)."""
    today = today or _today()
    k = str(p.get("kind") or "").strip()
    s = {"kind": k, "no_accept": k in NOT_SPEND}
    forced = None
    if k in NOT_SPEND and p.get("joins"):
        raise DeskError("A receipt or a statement takes no challans — choose Bill to join them.")
    was = (b["doc_kind"] or "")
    s["was"] = was
    if was in NOT_SPEND and k in ("bill", "estimate", "challan"):   # FIX2 C4: a receipt / statement turned into a bill (or estimate / challan)
        s["unproof"] = _s560_proof_pay(db, b)                       # its own payment, if any -- voided in _s560_post
        if b["status"] == "captured" and _lane(b) == "clinic":       # back to draft, so the Save's accept (with its duplicate check) runs
            db.execute("UPDATE bills SET status='draft' WHERE id=?", (b["id"],))
            AR._audit_bill(db, b["id"], "desk_not_spend_undone", {"kind_from": was, "kind": k, "status_from": "captured",
                                                                  "status": "draft", "via": "desk"})
    own = _s560_proof_pay(db, b) if k in NOT_SPEND else None       # FIX1 B1: a re-save changes this payment, never adds one
    pid = own["id"] if own is not None else None
    s["own"] = own
    if k == "receipt":
        r = p.get("receipt") or {}
        pays = str(r.get("pays") or "").strip()
        if not pays:
            raise DeskError("A receipt: choose the bill it pays, a statement, or “No bill — paid directly”.")
        if pays == "none":
            s["pay"] = _s560_pay_fields(r)
        elif pays.startswith("st:"):
            sid = int(pays[3:]) if pays[3:].isdigit() else 0
            ok = {x["id"] for x in statements_of(db, b, owner, today)}
            if sid not in ok:
                raise DeskError("That statement is not one of this supplier’s.")
            s["stmt"] = _row(db, sid)
            s["pay"] = _s560_pay_fields(r, need=False)
            forced = current_dest(s["stmt"])
        else:
            bid = int(pays) if pays.isdigit() else 0
            ok = {r_["id"] for r_, _o, _d in _s560_payable(db, b, owner, today, pid=pid)}
            if bid not in ok:
                raise DeskError("That bill is not an unpaid bill of this supplier.")
            s["bill"] = _row(db, bid)
            s["pay"] = _s560_pay_fields(r)
            forced = current_dest(s["bill"])
        src = s.get("bill") or s.get("stmt")
    elif k == "statement":
        r = p.get("statement") or {}
        offered = {r_["id"]: r_ for r_, _o, _d in _s560_payable(db, b, owner, today, pid=pid)}
        cov = []
        for x in (r.get("covers") or []):
            if str(x).isdigit() and int(x) not in [c["id"] for c in cov]:
                if int(x) not in offered:
                    raise DeskError("A ticked invoice is not an unpaid invoice of this supplier.")
                cov.append(offered[int(x)])
        s["covers"] = cov
        s["pay"] = _s560_pay_fields(r)
        s["period"] = (typed_date(r.get("from")) if str(r.get("from") or "").strip() else None,
                       typed_date(r.get("to")) if str(r.get("to") or "").strip() else None)
        s["total"] = _amount(r.get("total")) if str(r.get("total") or "").strip() else None
        if s["total"] is not None:
            p["total_amount"] = _plain(s["total"])
        forced = current_dest(cov[0]) if cov else None
        src = cov[0] if cov else None
    else:
        src = None
        if p.get("pay") and any(str((p.get("pay") or {}).get(x) or "").strip() for x in ("paid_on", "amount")):
            if k not in ("bill", "") or (not k and (b["doc_kind"] or "bill") != "bill"):
                raise DeskError("“Paid?” is for a bill.")
            s["direct"] = _s560_pay_fields(p.get("pay"))
            st0 = paid_state(db, b)
            if st0["state"] == "paid":                              # FIX1 B1: "Paid on ... — change?" changes that payment
                e, why = _s560_direct_edit(db, b, st0)
                if e is None:
                    raise DeskError("%s is already paid. %s Nothing was saved." % (_stamp(b), why))
                s["own"] = e
    if forced:
        if forced == "personal" and not owner:
            raise DeskError("Personal papers are the owner's alone.", 403)
        dest = forced
        if forced == "pe" and src is not None:
            p["who"] = "bhawna" if (_col(src, "pe_who") or "") == "bhawna" else "mk"
    return dest, s


def record_payment(db, proof, allocs, f, note=""):
    """ONE new payment (a re-save goes through _s560_update_payment instead: in place, never a second): paper_payment + one
    paper_payment_bill per bill it pays, each with the bill's fingerprint;
    audited on every paper it touches and in the desk's book. Returns the payment's id."""
    d, amt, mode, ref = f
    cur = db.execute("INSERT INTO paper_payment(paid_on, amount, mode, ref, proof_bill_id, proof_created_at, by_whom, at) VALUES(?,?,?,?,?,?,?,?)",
                     (d, amt, mode, ref, proof["id"] if proof is not None else None, _s560_fp(proof) if proof is not None else "", _who(), AR._now_ist()))
    pid = cur.lastrowid
    for row, a in allocs:
        db.execute("INSERT INTO paper_payment_bill(payment_id, bill_id, bill_created_at, amount) VALUES(?,?,?,?)", (pid, row["id"], _s560_fp(row), a))
        AR._audit_bill(db, row["id"], "paid_by_payment", {"payment": pid, "amount": a, "paid_on": d, "mode": mode, "ref": ref,
                                                          "proof": proof["id"] if proof is not None else None, "via": "desk"})
    if proof is not None:
        AR._audit_bill(db, proof["id"], "payment_recorded", {"payment": pid, "amount": amt, "paid_on": d, "mode": mode, "ref": ref,
                                                             "bills": [r_["id"] for r_, _a in allocs], "note": note, "via": "desk"})
    _audit_desk(db, "paper_payment", {"id": pid, "amount": amt, "paid_on": d, "mode": mode, "proof": proof["id"] if proof is not None else None,
                                      "bills": [r_["id"] for r_, _a in allocs]})
    return pid


def _s560_post(db, bid, p, s, status0):
    """After the Save's destination: a receipt / statement FILED, never accepted, never counted; its payment recorded; a
    bill's 'Paid?'; the construction tick; the fix answered. Returns the lines for the message."""
    msgs = []
    b = _row(db, bid)
    k = s.get("kind")
    if s.get("unproof") is not None:                                # FIX2 C4: its payment as a receipt / statement voided, kept
        had = _s560_pay_bills(db, s["unproof"]["id"])
        _s560_void_own(db, s["unproof"], b, "now a %s, not a %s" % (k or "bill", s.get("was")))
        _s560_void_allocs(db, s["unproof"]["id"])
        msgs.append("Its payment as a %s is voided (kept on record)%s." % (s.get("was"), " — the bill it paid is unpaid again" if had else ""))
    if k in NOT_SPEND:
        if b["status"] in ("draft", "approved"):
            db.execute("UPDATE bills SET status='captured' WHERE id=?", (bid,))
            AR._audit_bill(db, bid, "desk_not_spend_filed", {"kind": k, "status_from": b["status"], "status": "captured",
                                                             "lane": _lane(b), "via": "desk"})
        b = _row(db, bid)
        own = s.get("own")                                          # FIX1 B1: the payment already recorded -- changed, never doubled
        pid = own["id"] if own is not None else None
        once = "The payment is changed (one payment, never two)."
        if k == "receipt":
            if s.get("stmt") is not None:
                sm = s["stmt"]
                if own is not None:
                    _s560_void_own(db, own, b, "now the receipt of the statement %s" % _stamp(sm))
                if _s560_stmt_link(db, b) != sm["id"]:
                    AR._audit_bill(db, bid, "desk_receipt_to_statement", {"statement": sm["id"], "statement_created_at": _s560_fp(sm),
                                                                           "pay": list(s["pay"]) if s.get("pay") else None, "via": "desk"})
                    AR._audit_bill(db, sm["id"], "desk_receipt_linked", {"receipt": bid, "via": "desk"})
                msgs.append("The receipt of the statement %s (its payment is the statement's — counted once)." % _stamp(sm))
            elif s.get("bill") is not None:
                bl = _row(db, s["bill"]["id"])
                a = _s560_cap(s["pay"][1], _s560_outstanding(db, bl, pid))
                allocs = [(bl, a)] if a > 0 else []
                if own is not None:
                    if _s560_update_payment(db, own, b, allocs, s["pay"], "receipt"):
                        msgs.append(once)
                else:
                    record_payment(db, b, allocs, s["pay"], "receipt")
                msgs.append("%s is %s.%s" % (_stamp(bl), paid_state(db, _row(db, bl["id"]))["word"].lower() or "noted", _s560_left(s["pay"][1], a, bl)))
            else:
                if own is not None:
                    if _s560_update_payment(db, own, b, [], s["pay"], "no bill — paid directly"):
                        msgs.append(once)
                else:
                    record_payment(db, b, [], s["pay"], "no bill — paid directly")
                msgs.append("No bill — paid directly.")
        else:
            left = s["pay"][1]
            allocs = []
            byday = sorted(s.get("covers") or [], key=lambda r_: ((_s560_day(r_) or _today()), r_["id"]))
            nototal = [r_ for r_ in byday if r_["total_amount"] is None]      # S563 (S560-N4): the invoices with a total first
            for row in [r_ for r_ in byday if r_["total_amount"] is not None] + nototal:
                o = _s560_outstanding(db, row, pid)
                a = min(left, o if o is not None else left)
                if a > 0:
                    allocs.append((row, round(a, 2)))
                    left -= a
            if own is not None:
                if _s560_update_payment(db, own, b, allocs, s["pay"], "statement"):
                    msgs.append(once)
            else:
                record_payment(db, b, allocs, s["pay"], "statement")
            AR._audit_bill(db, bid, "desk_statement", {"from": s["period"][0], "to": s["period"][1], "total": s.get("total"),
                                                       "covers": [r_["id"] for r_ in s.get("covers") or []], "via": "desk"})
            msgs.append("%d invoice%s marked paid by this statement." % (len(allocs), "" if len(allocs) == 1 else "s"))
            if nototal:                                                 # S563 (S560-N4): said
                msgs.append(_s563_nototal_line(nototal, [(r_, a_) for r_, a_ in allocs if r_["total_amount"] is None]))
    elif s.get("direct"):
        f, own = s["direct"], s.get("own")
        a = _s560_cap(f[1], _s560_outstanding(db, b, own["id"] if own is not None else None))
        allocs = [(b, a)] if a > 0 else []
        if own is not None:
            ch = _s560_update_payment(db, own, None, allocs, f, "marked paid on the desk")
            msgs.append(("Changed: " if ch else "Unchanged: ") + _s560_pay_text(*f) + "." + _s560_left(f[1], a, b))
        else:
            record_payment(db, None, allocs, f, "marked paid on the desk")
            msgs.append("Marked: " + _s560_pay_text(*f) + "." + _s560_left(f[1], a, b))
    b = _row(db, bid)
    is_cb = (b["subgroup"] or "") == "construction" and (b["doc_kind"] or "bill") == "bill" and b["status"] != "rejected"
    cur = bool(_col(b, "to_accountant"))
    want = (bool(p.get("to_accountant")) if "to_accountant" in p else cur) if is_cb else False
    if cur != want:
        db.execute("UPDATE bills SET to_accountant=? WHERE id=?", (1 if want else 0, bid))
        AR._audit_bill(db, bid, "to_accountant", {"from": int(cur), "to": int(want), "via": "desk"})
        if want:
            msgs.append("Marked to send to the accountant.")
    if not db.execute("SELECT 1 FROM bill_audit WHERE bill_id=? AND action='desk_fix_answered' LIMIT 1", (bid,)).fetchone():
        AR._audit_bill(db, bid, "desk_fix_answered", {"answer": "saved", "via": "desk"})
    return msgs


def _s560_ledger(db, rows, sups):
    """The implant ledger's Paid adds the S560 payments of implant-stock bills: one row per allocation, each once (its own
    'Note payment' rows stay as they are -- the two kinds of record side by side, each once)."""
    for b in rows:
        if (b["doc_kind"] or "") in NOT_SPEND or ((b["doc_kind"] or "") == "challan" and (b["challan_state"] or "") == "joined"):
            continue
        key = _key(b["vendor"])
        if key not in sups:
            continue
        s = sups[key]
        for p in _s560_live_allocs(db, b):
            pr = _s560_proof(db, p)
            s["rows"].append({"sort": p["paid_on"], "d": _dm(p["paid_on"]), "p": _stamp(pr) if pr else "—", "bid": pr["id"] if pr else None,
                              "k": "Payment", "i": "%s%s · for %s%s" % (PAY_WORD.get(p["mode"], p["mode"]), (" no. " + p["ref"]) if p["ref"] else "",
                                                                       _stamp(b), (" · receipt / statement " + _stamp(pr)) if pr else ""),
                              "o": None, "pd": p["alloc"], "pay": None, "s560": p["id"]})
            s["paid"] += p["alloc"] or 0


def _s560_month_bits(db, key, paid_rows, pm=None):
    """The month page: 'paid N / unpaid M' per section; the Construction card's 'K marked for the accountant'."""
    pm = paid_map(db) if pm is None else pm
    st = [state_from_map(pm, b) for b in paid_rows]
    bits = " · paid %d / unpaid %d" % (len([x for x in st if x == "paid"]), len([x for x in st if x != "paid"]))
    if key == "construction":
        n = len([b for b in paid_rows if (b["doc_kind"] or "bill") == "bill" and _col(b, "to_accountant")])
        bits += " · %d marked for the accountant" % n
    return bits


def fix_answer():
    """POST /desk/api/fix {id, answer: restore | keep}: one person's tap on a paper listed to put right."""
    db = AR.get_db()
    p = request.get_json(silent=True) or {}
    try:
        bid = int(p.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="No paper was given."), 400
    owner = _owner()
    b = _row(db, bid)
    err = _visible(b, owner)
    if err:
        return jsonify(ok=False, error=err), (404 if not b else 403)
    f = _s560_fix_of(db, b, owner)
    ans = str(p.get("answer") or "")
    if not f or ans not in ("restore", "keep") or (ans == "restore" and f[0] != "blank"):
        return jsonify(ok=False, error="Nothing to answer on %s." % _stamp(b)), 400
    try:
        if ans == "restore":
            back = _s563_restore(db, b, "blank")                        # S563: the one shared restore -- never straight to accepted
            msg = "%s is back on its lane (%s). Sort it now — its Save accepts it as usual." % (_stamp(b), back)
        else:
            msg = "%s: left as it is." % _stamp(b)
        AR._audit_bill(db, bid, "desk_fix_answered", {"answer": ans, "fix": f[0], "via": "desk"})
        db.commit()
    except DeskError as e:                                           # S566 item 1: 'This looks like B-xxxx — open it instead.'
        db.rollback()
        return jsonify(ok=False, error=str(e)), e.code
    except Exception as e:                                           # noqa: BLE001
        db.rollback()
        return jsonify(ok=False, error="Not saved (%s). Nothing was changed." % type(e).__name__), 500
    return jsonify(ok=True, message=msg, id=bid)


def pay_void():
    """POST /desk/api/payment/void {id}: a mistaken payment voided -- kept on record, never counted again."""
    db = AR.get_db()
    p = request.get_json(silent=True) or {}
    try:
        pid = int(p.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="No payment was given."), 400
    r = db.execute("SELECT * FROM paper_payment WHERE id=? AND voided_at=''", (pid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="That payment is not there (or already voided)."), 404
    bills = [x[0] for x in db.execute("SELECT bill_id FROM paper_payment_bill WHERE payment_id=? AND voided_at=''", (pid,))] + ([r["proof_bill_id"]] if r["proof_bill_id"] else [])
    owner = _owner()
    for x in bills:
        e = _visible(_row(db, x), owner)
        if e and "owner's alone" in e:
            return jsonify(ok=False, error=e), 403
    db.execute("UPDATE paper_payment SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (AR._now_ist(), _who(), pid))
    for x in bills:
        AR._audit_bill(db, x, "payment_voided", {"payment": pid, "via": "desk"})
    _audit_desk(db, "paper_payment_void", {"id": pid, "amount": r["amount"]})
    db.commit()
    return jsonify(ok=True, message="Payment voided (kept on record).")


# --- S560_RECEIPTS_STATEMENTS end ---


# ---------------------------------------------------------------------------------------------- S563_SCANAPP_TIDY
def _s563_aside_day(b):
    """The day a paper was set aside: approved_at, which every set-aside path writes at that moment (IST); else the day it
    was scanned (created_at, UTC, shown in IST)."""
    if _iso(_col(b, "approved_at")):
        return _dmy(b["approved_at"])
    try:
        t = datetime.datetime.strptime(str(b["created_at"])[:19], "%Y-%m-%d %H:%M:%S") + datetime.timedelta(minutes=330)
        return t.strftime("%d-%m-%Y")
    except (TypeError, ValueError):
        return _dmy(b["created_at"])


def _s563_aside(b, f=None):
    """S563 (F-902): a paper set aside (status 'rejected') that is not a joined page (page_of) and not an S441 double scan
    (dup_of) shows ONE line, 'Already set aside on dd-mm-yyyy — Restore?', and a Restore button. Not while the blank fix's
    line shows (f = ('blank', ..)): one Restore button serves both. Never depends on desk_fix_answered. Else None."""
    if b is None or b["status"] != "rejected" or b["page_of"] or b["dup_of"] or (f and f[0] == "blank"):
        return None
    return {"text": "Already set aside on %s — Restore?" % _s563_aside_day(b)}


def _s563_restore(db, b, via):
    """S563: THE restore of a paper set aside -- F-902's line ('aside') and the blank fix ('blank'). The status a fresh paper
    on its lane has (AR._lane_kind_status: clinic draft, the other lanes captured), never straight back to approved (S560-N3:
    the next Save runs the normal accept, with its duplicate check); reject_reason, approved_by and approved_at cleared; lane,
    subgroup, kind, doc_kind, pe_who and challan_state kept as they are (D664). Audited: who, when, from what. Refuses a page
    and a double scan. No commit (the route commits once). Returns the status."""
    st = _stamp(b)
    if b["status"] != "rejected":
        raise DeskError("%s is not set aside." % st)
    if b["page_of"]:
        raise DeskError("%s is a page of another paper — open that paper." % st)
    if b["dup_of"]:
        raise DeskError("%s is set aside as a second scan — answer that question on it instead." % st)
    hit = _s566_restore_dup(db, b)                                 # S566 item 1 (N5): never counted twice blind, on every lane
    if hit is not None:
        raise DeskError("This looks like %s — open it instead." % _stamp(hit))
    back = AR._lane_kind_status(_lane(b))[1]
    db.execute("UPDATE bills SET status=?, reject_reason=NULL, approved_by=NULL, approved_at=NULL WHERE id=? AND status='rejected'",
               (back, b["id"]))
    AR._audit_bill(db, b["id"], "desk_blank_restored" if via == "blank" else "desk_restored",
                   {"status_from": "rejected", "status": back, "reject_reason": b["reject_reason"], "approved_by": b["approved_by"],
                    "approved_at": b["approved_at"], "lane": _lane(b), "by": _who(), "at": AR._now_ist(), "via": "desk " + via})
    return back


def _s563_nototal_line(nototal, got):
    """S563 (S560-N4): the Save's words when a statement covers an invoice that has no total."""
    st = ", ".join(_stamp(r_) for r_ in nototal)
    one = len(nototal) == 1
    if got:
        return "%s %s no total: only what was left after the invoices with a total went to %s (%s)." % (
            st, "has" if one else "have", "it" if one else "them", _inr(sum(a_ for _r, a_ in got)))
    return "%s %s no total: nothing was left for %s after the invoices with a total." % (st, "has" if one else "have", "it" if one else "them")


def restore_answer():
    """POST /desk/api/restore {id}: S563 (F-902) -- 'Already set aside on ... — Restore?'. The paper must be one this person
    may open (_visible: a Personal paper is the owner's alone). Neither reads nor writes desk_fix_answered."""
    db = AR.get_db()
    p = request.get_json(silent=True) or {}
    try:
        bid = int(p.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="No paper was given."), 400
    b = _row(db, bid)
    err = _visible(b, _owner())
    if err:
        return jsonify(ok=False, error=err), (404 if not b else 403)
    try:
        back = _s563_restore(db, b, "aside")
        db.commit()
    except DeskError as e:
        db.rollback()
        return jsonify(ok=False, error=str(e)), e.code
    except Exception as e:                                           # noqa: BLE001
        db.rollback()
        return jsonify(ok=False, error="Not saved (%s). Nothing was changed." % type(e).__name__), 500
    return jsonify(ok=True, message="%s is back on its lane (%s). Sort it now — its Save files it as usual." % (_stamp(b), back), id=bid)


# --- S563_SCANAPP_TIDY end ---


# ---------------------------------------------------------------------------------------------- S566_SCANAPP_LAST_FIXES
def _s566_restore_dup(db, b):
    """S566 item 1 (S563-K1-N5): before a set-aside paper is restored, on every lane, the live paper (not rejected, any
    status) it would be a second count of -- (a) AR._dup_by_triple's exact match on the row; (b) when the row has no supplier
    or no amount, the same exact triple built from Claude's reading (supplier, number, amount; AR._triple's normalisation)
    against the bills of the last AR.DUP_WINDOW_DAYS; (c) the same capture again (AR._dup_by_fp, fine distance at most
    AR.DUP_EXACT). The row found, else None. Reads only."""
    bid = b["id"]
    try:
        exact, _near = AR._dup_by_triple(db, bid)
    except Exception:                                                # noqa: BLE001
        exact = None
    if exact is not None:
        return exact
    if not (b["vendor"] or "").strip() or b["total_amount"] is None:
        rd = reading(db, bid)
        if rd and (rd.get("supplier") or "").strip() and (rd.get("number") or "").strip() and rd.get("amount") is not None:
            v, n, t = AR._triple({"vendor": rd["supplier"], "bill_no": rd["number"], "total_amount": rd["amount"]})
            since = (datetime.date.today() - datetime.timedelta(days=AR.DUP_WINDOW_DAYS)).isoformat()
            for r in db.execute("SELECT id, stamp_no, vendor, bill_no, total_amount FROM bills WHERE id<>? AND status<>'rejected' "
                                "AND substr(created_at,1,10)>=? ORDER BY id ASC LIMIT 2000", (bid, since)):
                if AR._triple(r) == (v, n, t) and v and n:
                    return r
    fp, fpc = _col(b, "fp"), _col(b, "fpc")
    if fp and fpc:
        try:
            r, df, _dc = AR._dup_by_fp(db, bid, fp, fpc)
        except Exception:                                            # noqa: BLE001
            r, df = None, None
        if r is not None and df is not None and df <= AR.DUP_EXACT:
            return r
    return None


def _s566_restored(m):
    """S566 item 1: the newest desk_restored / desk_blank_restored mark is newer than the newest desk_saved (from _marks)."""
    r = max(m.get("desk_restored", 0) or 0, m.get("desk_blank_restored", 0) or 0)
    return bool(r and r > (m.get("desk_saved", 0) or 0))


def _s566_waits(b, owner, m=None):
    """S566 item 3: a paper whose status reads 'Waiting' (draft) that no other list shows -- not a double scan, not a page,
    not the pharmacy lane, not a patient's paper, Personal only for the owner; EXCEPT an awaiting challan whose supplier is
    read (it is on Bills awaited), a clinic_equipment paper for anyone but the owner (it waits on Dr Manoj's Save), and
    (FIX1, K1 CORRECTION 2) a closed challan a desk Save has kept as a record (its desk_closed_kept mark in `m`, from _marks).
    Whatever its scan day and whether or not it was saved on the desk before. Nothing is written (D664)."""
    if b["status"] != "draft" or b["dup_of"] or b["page_of"] or _lane(b) == "pharmacy":
        return False
    if (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "") == "closed" and (m or {}).get("desk_closed_kept"):
        return False
    sg = b["subgroup"] or ""
    if sg == PATIENT or (sg == "personal" and not owner):
        return False
    if (b["doc_kind"] or "") == "challan" and (b["challan_state"] or "awaiting") == "awaiting" and _key(b["vendor"]):
        return False
    if sg == "clinic_equipment" and not owner:
        return False
    return True


def _s566_stamp_form(v):
    """S566 item 8: B-0162, b-0162, B-162, B162, b162 -> 'B-0162'; anything else as typed (_by_stamp reads it as before)."""
    m = re.fullmatch(r"[Bb]-?0*(\d{1,6})", v or "")
    return ("B-%04d" % int(m.group(1))) if m else v


def _s566_lanes(key):
    """S566 item 6: the lanes / statuses a section's challans are read from (month_data's own two strings)."""
    if key == "construction":
        return "COALESCE(b.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND b.status IN ('draft','approved','captured')"
    return "COALESCE(b.lane,'clinic')='clinic' AND b.status IN ('draft','approved')"


# FIX1 (K1 BLOCKER 1): the SQL twin of held() -- a D710-held double (a clinic draft whose d710_not_accepted is newer than its
# last desk_saved, not yet answered) is never money: it drops out of The month and the home card until someone answers it.
_S566_NOT_HELD = (" AND NOT (b.status='draft' AND COALESCE(b.lane,'clinic')='clinic' AND COALESCE(b.dup_flag,'')='' "
                  "AND EXISTS (SELECT 1 FROM bill_audit h WHERE h.bill_id=b.id AND h.action='d710_not_accepted' AND h.id > "
                  "COALESCE((SELECT MAX(s.id) FROM bill_audit s WHERE s.bill_id=b.id AND s.action='desk_saved'),0)))")


def _s566_paid_rows(db, key, subs, ym):
    """S566 item 6: (money, finals) -- month_data's own two queries for one section, now shared; FIX1: both leave out a
    D710-held double (_S566_NOT_HELD), so the accepted original counts once."""
    ph = ",".join("?" * len(subs))
    live = CP._live_sections(db) if key == "construction" else CP._live(db)
    lanes = _s566_lanes(key)
    money = db.execute("SELECT b.* FROM bills b WHERE " + live + _S566_NOT_HELD + " AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                       subs + (ym,)).fetchall()
    finals = db.execute("SELECT b.* FROM bills b WHERE " + lanes + " AND b.dup_of IS NULL AND b.page_of IS NULL" + _S566_NOT_HELD + " AND b.doc_kind='challan' "
                        "AND b.challan_state='final' AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.id", subs + (ym,)).fetchall()
    return money, finals


def _s566_total(paid_rows):
    """S566 item 6: a section's total -- the one sum, month_data's and month_total's."""
    return sum((b["total_amount"] or 0) for b in paid_rows)


def month_total(db, ym, owner=True):
    """S566 item 6: The month's grand total -- the sum of its section totals (the same rows, the same sum; no items loop).
    The home card's 'Spend this month' reads this. `owner` kept for the caller's clarity (no section is Personal)."""
    tot = 0
    for key, _nm, subs in MONTH_SECTIONS:
        money, finals = _s566_paid_rows(db, key, subs, ym)
        tot += _s566_total(list(money) + list(finals))
    return tot


# --- S566_SCANAPP_LAST_FIXES end ---


# ---------------------------------------------------------------------------------------------- S568_STATIONERY_STOCK (D730)
# The owner's rulings, 16-Oct-2026: a clinic stationery / packaging paper goes to the new clinic consumables group "Stationery &
# packaging"; its lines are matched on the desk to the stationery list (stationery.py), the stock going up once (counted when
# read, R1 B2); a challan or bill can be ticked "mixed: clinic + lab items"; "Add a paper from a file" goes through the intake's
# own code path, with ONE preset -- the Aumni envelopes, a Sanjeevni pharmacy expense paid by Dr MK's card (kind 'Pharmacy
# expense', written before the intake's first commit; paid on the paper itself, audited as card -- no paper_payment row).
def _s674_listed(db, b):
    """S674: is this paper a listed stationery supplier's (the Stationery page sorts it)? False when stationery.py is not mounted."""
    st = _s568_st()
    try:
        return st is not None and bool(st.is_listed(db, b["vendor"]))
    except Exception:                                                # noqa: BLE001
        return False


def _s568_st():
    """stationery.py, when it is mounted; else None (the panel and its lines then give nothing)."""
    m = sys.modules.get("stationery")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s568_paper(db, b, owner, rd):
    """paper_json's S568 part: the mixed mark; the stationery panel (its lines, the active items, whether they count)."""
    out = {"mixed": bool(_col(b, "mixed")), "stk": None}
    st = _s568_st()
    if st is None or _lane(b) == "pharmacy":
        return out
    try:
        out["stk"] = st.panel(db, b, rd)
    except Exception as ex:                                          # noqa: BLE001
        print("S568 panel: %s" % ex, file=sys.stderr)
    return out


def _s568_note(db, key, note, today=None):
    """The desk's supplier note (R1 note 18) + 'Mixed challans this month: N' when this supplier has any."""
    st = _s568_st()
    if st is None or not key:
        return note
    try:
        n = st.mixed_n(db, (today or _today()).strftime("%Y-%m"), key)
    except Exception:                                                # noqa: BLE001
        n = 0
    if not n:
        return note
    add = "Mixed challans this month: %d (clinic + lab items on one paper — raise it with the supplier)." % n
    return (note + " " + add) if note else add


def _s568_post(db, bid, p, dest):
    """In the Save's transaction: the mixed tick (a challan or a bill; audited); the stationery lines when the paper is in
    Stationery & packaging (a re-save replaces them, never adds); a paper moved out of it has its lines voided (kept)."""
    msgs = []
    b = _row(db, bid)
    if "mixed" in p and "mixed" in b.keys() and (b["doc_kind"] or "bill") in ("bill", "challan"):
        want, cur = (1 if p.get("mixed") else 0), int(b["mixed"] or 0)
        if want != cur:
            db.execute("UPDATE bills SET mixed=? WHERE id=?", (want, bid))
            AR._audit_bill(db, bid, "mixed", {"from": cur, "to": want, "via": "desk"})
            msgs.append("Marked: mixed clinic + lab items." if want else "The mixed mark is taken off.")
    st = _s568_st()
    if st is None:
        return msgs
    b = _row(db, bid)
    if hasattr(st, "is_goods") and _s674_listed(db, b) and st.is_goods(b):        # S674: a listed supplier's challan is sorted on the Stationery page
        if "st_lines" in p:
            raise DeskError("%s is %s's — its lines are sorted on the Stationery page, not here. Nothing was saved." % (_stamp(b), b["vendor"]))
    if dest == "stationery" and (b["subgroup"] or "") == "stationery":
        if "st_lines" in p:
            try:
                msgs += st.save_lines(db, b, p.get("st_lines") or [], _who())
            except ValueError as e:
                raise DeskError(str(e) + " Nothing was saved.")
    elif st.has_lines(db, b):
        try:
            st.void_lines(db, b, _who(), "saved on the desk to %s" % DEST_NAME.get(dest, dest))
        except ValueError as e:                                      # S674: lines on a supplier statement stay
            raise DeskError(str(e) + " Nothing was saved.")
        msgs.append("Its stationery lines are taken off the stock (it is no longer in Stationery & packaging).")
    return msgs


def _s568_apart(db, ym):
    """The month's 'Sanjeevni — pharmacy expenses': count and total (the amount read, else the amount paid) -- never a section,
    never in month_total."""
    try:
        r = db.execute("SELECT COUNT(*), SUM(COALESCE(b.total_amount, b.paid_amount)) FROM bills b WHERE b.kind=? AND b.status<>'rejected' "
                       "AND b.dup_of IS NULL AND b.page_of IS NULL AND " + CP.MONTH_OF + "=?", (PEXP, ym)).fetchone()
        return {"pexp": r[0] or 0, "pexp_total": r[1] or 0}
    except sqlite3.Error:
        return {"pexp": 0, "pexp_total": 0}


S568_FILE_EXT = ("pdf", "jpg", "jpeg", "png", "webp", "heic")       # S568 FIX1: the intake's PDF and photo types -- never doc / docx
S568_FILE_REFUSED = "That file cannot be taken — only a PDF or a photo (pdf, jpg, jpeg, png, webp, heic). Nothing was saved."

ADD_TPL = PAGE_HEAD +"""<div class=top><a href="{{url_for('s551_desk')}}" style="font-size:14px">‹ Sorting desk</a><span class=t>Add a paper from a file</span><span class=muted style="font-size:14px">A PDF or a photo — it goes in as a scan does: the stamp, the double-scan check, the reading.</span></div>
{% if msg %}<div class="msg{{' bad' if bad else ''}}" id=s568msg>{{msg}}</div>{% endif %}
<form method=post enctype=multipart/form-data class=card id=s568add style="margin:14px 18px;display:flex;flex-direction:column;gap:10px;max-width:660px">
<label style="font-size:14px">The file<input type=file name=paper_file accept=".pdf,.jpg,.jpeg,.png,.webp,.heic,application/pdf,image/jpeg,image/png,image/webp,image/heic" style="display:block;margin-top:4px"></label>
<b style="font-size:14px">What is it?</b>
<label style="font-size:14px;display:flex;gap:6px;align-items:center"><input type=radio name=what value=paper checked style="width:auto"> A paper for the scan app, on the lane</label>
<div style="margin-left:24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap"><select name=lane>{% for k, w in lanes %}<option value="{{k}}">{{w}}</option>{% endfor %}</select>
<label style="font-size:14px;display:flex;gap:6px;align-items:center"><input type=checkbox name=challan value=1 style="width:auto"> It is a challan (goods came; the bill comes later)</label></div>
<label style="font-size:14px;display:flex;gap:6px;align-items:center"><input type=radio name=what value=pexp style="width:auto"> Sanjeevni pharmacy expense — paid by Dr MK's card</label>
<div style="margin-left:24px;display:flex;gap:12px;flex-wrap:wrap"><label style="font-size:13px">Paid on<input name=paid_on placeholder="dd-mm-yyyy" style="display:block;width:130px"></label><label style="font-size:13px">Amount<input name=amount placeholder="₹" inputmode=decimal style="display:block;width:120px"></label></div>
<div class=muted style="margin-left:24px;font-size:12px">Filed on the pharmacy lane as a pharmacy expense — never a medicine bill, so Sanjeevni's register never pairs it with a Marg bill — and marked paid by your card. It shows on The month as “Sanjeevni — pharmacy expenses”, never in the clinic's totals. No card number is asked for or kept.</div>
<label style="font-size:14px">Note <span class=muted>(optional)</span><input name=note maxlength=120 style="display:block;width:100%"></label>
<button class=go style="min-height:40px;font-size:15px">Save</button></form></body></html>"""


def _s568_lanes():
    """The intake's own lane choices for this user (asset_register._intake_lanes_s544), in the app's words."""
    role = ""
    try:
        role = g.user["role"] or ""
    except Exception:                                                # noqa: BLE001
        pass
    out = []
    for k in AR._intake_lanes_s544(role):
        w = (getattr(AR, "LANE_WORD", {}) or {}).get(k) or AR.LANES[k][0]
        out.append((k, w))
    return out


def add_page():
    """GET / POST /desk/add -- S568 item 7: a PDF or an image through the intake's own code path (_create_intake_bill: the
    same storage, stamp, fingerprint double check and reading). The plain form offers the intake's choices only (the lanes
    this user has, the challan tick). The preset: the pharmacy lane, kind 'Pharmacy expense' written before the intake's
    first commit (kind_over), status captured; paid on the paper itself (bills.paid_on / paid_amount, the day and amount
    typed) with one bill_audit 'paid' {how: card}. Owner and managers; managers only while the desk is on (the _gate)."""
    lanes = _s568_lanes()
    if request.method == "GET":
        m, bad = _msg_args()
        return render_template_string(ADD_TPL, bg=_bg(), title="Add a paper from a file", lanes=lanes, msg=m, bad=bad)
    f = request.form
    fobj = request.files.get("paper_file")
    note = (f.get("note") or "").strip()[:120]
    if not (fobj and fobj.filename):
        return _back_to("s568_add", "Choose the file (a PDF or a photo). Nothing was saved.", True)
    ext = fobj.filename.rsplit(".", 1)[1].lower() if "." in fobj.filename else ""      # the intake's own reading of it
    if ext not in S568_FILE_EXT:                                    # S568 FIX1 (K1 CORRECTION 3): a PDF or a photo only
        return _back_to("s568_add", S568_FILE_REFUSED, True)
    pexp =(f.get("what") or "") == "pexp"
    if pexp:
        try:
            if not str(f.get("paid_on") or "").strip():
                raise DeskError("Type the day it was paid (dd-mm-yyyy). Nothing was saved.")
            d = typed_date(f.get("paid_on"))
            amt = _amount(f.get("amount"))
            if amt is None or amt <= 0:
                raise DeskError("Type the amount paid. Nothing was saved.")
        except DeskError as e:
            return _back_to("s568_add", str(e), True)
        bid = AR._create_intake_bill(fobj, note, "pharmacy", {}, challan=False, kind_over=PEXP)
    else:
        lane = (f.get("lane") or "").strip()
        if lane not in dict(lanes):
            return _back_to("s568_add", "Choose the lane. Nothing was saved.", True)
        bid = AR._create_intake_bill(fobj, note, lane, {}, challan=(f.get("challan") == "1"))
    if not bid:
        return _back_to("s568_add", S568_FILE_REFUSED, True)
    db = AR.get_db()
    b = _row(db, bid)
    if b["dup_of"]:
        first = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["dup_of"],)).fetchone()
        return _back_to("s568_add", "%s is the same file as %s — it is set aside as a second copy%s." % (
            _stamp(b), _stamp(first) if first else "an earlier paper", " (not marked paid)" if pexp else ""), True)
    if pexp:
        db.execute("UPDATE bills SET paid_on=?, paid_amount=? WHERE id=?", (d, amt, bid))
        AR._audit_bill(db, bid, "paid", {"how": "card", "note": "Dr MK's card", "via": "add_from_file", "on": d, "amount": amt})
        _audit_desk(db, "add_from_file", {"id": bid, "preset": "pharmacy_expense"})
        db.commit()
        return _back_to("s568_add", "Saved as %s — Sanjeevni pharmacy expense, paid by Dr MK's card (%s on %s)." % (_stamp(b), _inr(amt), _dmy(d)))
    _audit_desk(db, "add_from_file", {"id": bid, "lane": b["lane"]})
    db.commit()
    if _lane(b) == "pharmacy":
        return _back_to("s568_add", "Saved as %s on the pharmacy lane (the Sanjeevni side keeps it)." % _stamp(b))
    return redirect(url_for("s551_desk", open=bid))


# --- S568_STATIONERY_STOCK end ---


# ---------------------------------------------------------------------------------------------- S571_BATTERIES (D730 (1))
# A B.L. Computers / Jasoria paper on the desk: "Battery fitted at <place> on <date> — this bill?" when that place's battery has its
# bill awaited (batteries.desk_offer: the desk's visibility rules; an owner-only place to the owner only). Linking is its own POST
# (/batteries/link) and never writes the paper (D664). A linked paper not sorted yet: the place's payer pre-selects "Where does it
# go?" in the browser only (clinic -> Clinic equipment, NK Pathology -> NK Pathology, owner -> Personal; 'to confirm' -> nothing).
def _s571_bt():
    """batteries.py, when it is mounted; else None (the offer then gives nothing)."""
    m = sys.modules.get("batteries")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s571_paper(db, b, owner):
    bt = _s571_bt()
    if bt is None or _lane(b) == "pharmacy":
        return {}
    try:
        return bt.desk_offer(db, b, owner, current_dest(b))
    except Exception as ex:                                          # noqa: BLE001
        print("S571 offer: %s" % ex, file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------------------------- S634_PROCROOM_LIST (D773 Kit 1)
# The owner's rulings, 23-Oct-2026 (S342, D773): a Procedure room paper's lines each get a product from his list (procroom.py) and a
# place -- Procedure room, Home use (Dr MK), Clinic equipment, OT, Sanjeevni (orthotics, flagged for him). The desk's panel carries
# NO rate: the rates are his alone, on his Procedure room page. Without procroom.py the desk runs exactly as before.
def _s634_pr():
    """procroom.py, when it is mounted; else None (the panel and its lines then give nothing)."""
    m = sys.modules.get("procroom")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _s634_paper(db, b, owner, rd, dest=""):
    """paper_json's S634 part: the Procedure room panel (its lines, the products, the places, whether they count) -- no rate."""
    out = {"pr": None}
    pr = _s634_pr()
    if pr is None or _lane(b) == "pharmacy":
        return out
    if not owner and ((b["subgroup"] or "") == "procedure" or dest == "procedure" or _yuvika(b["vendor"])):
        out["stk"] = None                                            # D773: a Procedure room paper -- in it, suggested to it, or Yuvika's --
        #                                                              sends no stationery panel (it carries the paper's rates) to a non-owner
    try:
        out["pr"] = pr.panel(db, b, rd, owner)
    except Exception as ex:                                          # noqa: BLE001
        print("S634 panel: %s" % ex, file=sys.stderr)
    return out


def _s634_post(db, bid, p, dest):
    """In the Save's transaction: the Procedure room lines when the paper is in Procedure room (a re-save replaces them, never
    adds); a paper moved out of it has its lines voided (kept)."""
    pr = _s634_pr()
    if pr is None:
        return []
    b = _row(db, bid)
    if dest == "procedure" and (b["subgroup"] or "") == "procedure":
        if "pr_lines" in p:
            try:
                return pr.save_lines(db, b, p.get("pr_lines") or [], _who(), _owner(), p)       # S635: + pr_role, pr_order, pr_book
            except ValueError as e:
                raise DeskError(str(e) + " Nothing was saved.")
        return []
    if pr.has_lines(db, b):
        pr.void_lines(db, b, _who(), "saved on the desk to %s" % DEST_NAME.get(dest, dest))
        return ["Its Procedure room lines are taken off (it is no longer in Procedure room)."]
    return []


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):
    """Called once, at the foot of asset_register.py, after clinic_papers is mounted."""
    global AR, CP
    AR = ar
    CP = getattr(ar, "_clinic_papers", None) or sys.modules.get("clinic_papers")
    if CP is None or not hasattr(CP, "join_pages") or not hasattr(CP, "APART_KEYS"):
        raise RuntimeError("clinic_papers with S551's join_pages is not mounted")
    ensure_at_mount(ar.DB_PATH)                                      # FIX1 N4: a locked database never unmounts the desk
    app, cr = ar.app, ar.checker_required
    app.add_url_rule("/desk", "s551_desk", cr(_gate(desk_page)))
    app.add_url_rule("/desk/api/list", "s551_api_list", cr(_gate(api_list)))
    app.add_url_rule("/desk/api/paper/<int:bid>", "s551_api_paper", cr(_gate(api_paper)))
    app.add_url_rule("/desk/api/find", "s551_api_find", cr(_gate(api_find)))
    app.add_url_rule("/desk/api/save", "s551_api_save", cr(_gate(api_save)), methods=["POST"])
    app.add_url_rule("/desk/awaited", "s551_awaited", cr(_gate(awaited_page)))
    app.add_url_rule("/desk/awaited/mode", "s551_awaited_mode", cr(_gate(awaited_mode)), methods=["POST"])
    app.add_url_rule("/desk/awaited/pay", "s551_awaited_pay", cr(_gate(awaited_pay)), methods=["POST"])
    app.add_url_rule("/desk/implants", "s551_implants", cr(_gate(implants_page)))
    app.add_url_rule("/desk/implants/pay", "s551_implants_pay", cr(_gate(implants_pay)), methods=["POST"])
    app.add_url_rule("/desk/implants/void", "s551_implants_void", cr(_gate(implants_void)), methods=["POST"])
    app.add_url_rule("/desk/implants/check", "s551_implants_check", cr(_gate(implants_check)), methods=["POST"])
    app.add_url_rule("/desk/month", "s551_month", cr(_gate(month_page)))
    app.add_url_rule("/desk/api/fix", "s560_fix", cr(_gate(fix_answer)), methods=["POST"])                  # S560 item 7
    app.add_url_rule("/desk/api/payment/void", "s560_void", cr(_gate(pay_void)), methods=["POST"])         # S560 item 5
    app.add_url_rule("/desk/api/restore", "s563_restore", cr(_gate(restore_answer)), methods=["POST"])     # S563 F-902
    app.add_url_rule("/desk/add", "s568_add", cr(_gate(add_page)), methods=["GET", "POST"])                 # S568 item 7
    app.add_url_rule("/desk/switch", "s551_switch", ar.owner_required(switch), methods=["POST"])
    app.jinja_env.globals.update(s551_on=True, s551_switches_card=switches_card, s551_month_href=month_href)
    return VERSION


if __name__ == "__main__":
    # the installer's data step:  python3 sorting_desk.py --ensure <assets.db> [--floor YYYY-MM-DD]
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        fl = sys.argv[sys.argv.index("--floor") + 1] if "--floor" in sys.argv else None
        print("sorting_desk %s: tables and columns ready; desk.floor = %s" % (VERSION, ensure_path(sys.argv[2], fl) or "(not set)"))
    else:
        print(__doc__)
