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
import re
import sqlite3
import sys
import time

from flask import abort, g, jsonify, redirect, render_template_string, request, session, url_for
from markupsafe import Markup

VERSION = "S551.2"             # S551.2 = fix round 1 (S551_FIX1: C2, C3, C4, N4, N5, N6)
AR = None                     # the asset app's module, handed in by init()
CP = None                     # clinic_papers, already mounted by the app
TODAY = None                  # the walk sets a made-up day here; every date rule also takes `today` as an argument

OFF_LINE = "The sorting desk opens when Dr Manoj switches it on."
PATIENT = "patient_paper"
CONS = ("procedure", "xray_small", "xray_11x14", "others")
CLINIC_DEST = CONS + ("implant_stock", "clinic_equipment")
LEFT_ON_LANE = ("construction", "personal", "resume", "misc")      # left on its lane (a SORT_LANE; else Other document)
SECTION_KEEP = ("construction", "resume", "misc", "personal")       # kept on a personal expense; anything else is cleared

DESTINATIONS = (      # the board's six groups -- the one list "Where does it go?"
    ("Clinic consumables", (("procedure", "Procedure room"), ("xray_small", "X-ray small film"),
                            ("xray_11x14", "X-ray 11 × 14"), ("others", "Others"))),
    ("Clinic", (("implant_stock", "Implant stock"), ("clinic_equipment", "Clinic equipment"),
                ("construction", "Construction work"))),
    ("Personal", (("pe", "Personal expense"), ("personal", "Personal (you only)"))),
    ("Handed over", (("pharmacy", "Pharmacy — Sanjeevni"), ("lab", "NK Pathology"))),
    ("Documents", (("resume", "Resumes"), ("misc", "Miscellaneous"))),
    ("Not here", ((PATIENT, "A patient’s paper — surgical case pack"),)),
)
DEST_NAME = dict(kv for _t, items in DESTINATIONS for kv in items)
NOTES = {             # the board's grey line for the chosen destination
    "implant_stock": "Goes to the implant stock ledger of this supplier (owed until paid).",
    PATIENT: "Kept aside, out of every total. It belongs to the surgical case pack.",
    "pharmacy": "Handed to Sanjeevni, as today.",
    "lab": "NK Pathology side; a bill goes into the accountants’ pack 8.1.",
    "construction": "Counted on its own; never called clinic or MK by the system.",
    "pe": "Into Personal expenses; the accountants’ pack 8.2 or 8.3.",
}
KINDS = (("bill", "Bill"), ("estimate", "Estimate slip"), ("challan", "Challan"))
CLAUDE_KIND = {"tax_invoice": "bill", "bill": "bill", "estimate": "estimate", "quotation": "estimate", "challan": "challan"}
MODES = (("monthly", "Monthly bill"), ("sometimes", "A bill now and then"), ("paid", "Paid on challan — no bill"))
MODE_RULE = {
    "monthly": "Challans wait for the month’s bill. Amber if no bill by the 10th of next month. When the bill comes, the desk offers the month’s challans — one tap joins them.",
    "sometimes": "Challans wait without turning amber, oldest first, with their age. When a bill comes, the desk shows every open challan — tick the ones it covers.",
    "paid": "The challan or estimate is the final paper. It never waits. Note the payment on it when you pay.",
    "": "Not set yet. Its challans wait and turn amber after %d days (today’s rule). Set how this supplier bills.",
}
HOW = ("Bank / UPI", "Cheque", "Cash")
SWITCHES = (("scan.cv", "Smart scanner"), ("scan.lanes5", "Reception buttons"), ("desk.on", "Sorting desk for Shavez"))
MONTH_SECTIONS = (("procedure", "Procedure room", ("procedure",)),
                  ("xray", "X-ray films", ("xray_small", "xray_11x14", "xray")),
                  ("others", "Others", ("others",)),
                  ("implant_stock", "Implant stock", ("implant_stock",)),
                  ("construction", "Construction work", ("construction",)),
                  ("clinic_equipment", "Clinic equipment", ("clinic_equipment",)))
S441_WHO = "server (S441 double-scan rule)"


class DeskError(Exception):
    def __init__(self, msg, code=400):
        Exception.__init__(self, msg)
        self.code = code


# ---------------------------------------------------------------------------------------------- the database's part
BILL_COLS = (("paid_on", "TEXT"), ("paid_amount", "REAL"))
DDL = (
    "CREATE TABLE IF NOT EXISTS challan_supplier(supplier_key TEXT PRIMARY KEY, name TEXT, mode TEXT NOT NULL "
    "CHECK(mode IN ('monthly','sometimes','paid')), set_by TEXT, set_at TEXT)",
    "CREATE TABLE IF NOT EXISTS implant_payment(id INTEGER PRIMARY KEY, supplier_key TEXT NOT NULL, day TEXT NOT NULL, "
    "amount REAL NOT NULL, how TEXT NOT NULL, against TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, "
    "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS implant_check(supplier_key TEXT, upto TEXT, by_whom TEXT, at TEXT)",
    "CREATE TABLE IF NOT EXISTS desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT)",
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
    d = _iso(s)
    return d.strftime("%d-%b-%Y") if d else (s or "")


def _dm(s):
    d = _iso(s)
    return d.strftime("%d-%b") if d else (s or "")


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
    return {"doc_kind": r[0] or data.get("doc_kind"), "made_out_to": data.get("made_out_to"), "items": items}


def items_of(db, b, rd=None):
    """[(name, qty, unit)] -- Claude's reading when there is one, else the paper's own items."""
    if rd and rd["items"]:
        return [(str(i.get("name")).strip(), i.get("qty"), str(i.get("unit") or "").strip()) for i in rd["items"]]
    return [(r[0], r[1], (r[2] or "")) for r in db.execute(
        "SELECT item_name, quantity, pack_size FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)) if r[0]]


def _qty(q):
    try:
        f = float(q)
        return ("%d" % f) if f == int(f) else ("%g" % f)
    except (TypeError, ValueError):
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
    """A bill_date before 2015, after 31-Dec of next year, or more than 60 days from the scan."""
    bd = (b["bill_date"] or "").strip()
    if not bd:
        return False
    d = _iso(bd) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", bd) else None
    if d is None:
        return True
    today = today or _today()
    if d < datetime.date(2015, 1, 1) or d > datetime.date(today.year + 1, 12, 31):
        return True
    c = _iso(b["created_at"])
    return bool(c and abs((d - c).days) > 60)


def nothing_read(db, b):
    return CP._is_blank(b, CP._items_text(db, b["id"]))


def _marks(db, bid=None):
    """{bill_id: {action: the newest audit id}} for the actions the desk's list reads."""
    acts = ("desk_saved", "d710_not_accepted", "desk_dup_same", "desk_dup_restored")
    sql = "SELECT bill_id, action, MAX(id) FROM bill_audit WHERE action IN (?,?,?,?)"
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
        "AND COALESCE(b.subgroup,'')='') OR substr(b.created_at,1,10)>=?)) "
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
                if (b["doc_kind"] or "") != "challan" and _key(b["vendor"]) in sup_wait:
                    why.append("covers")
            if held(b, mk):
                why.append("hold")
        if after and not live and s441_aside(b, today, days):
            m = mk.get(b["id"], {})
            if not (m.get("desk_dup_same") or m.get("desk_dup_restored")):
                why.append("s441")
        if why:
            out.append((b, why))
    return out


def _hint(db, b, why):
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


def paper_json(db, b, owner, today=None):
    today = today or _today()
    rd = reading(db, b["id"])
    it = items_of(db, b, rd)
    key = _key(b["vendor"])
    md = modes(db)
    mode = md.get(key, "")
    kind = b["doc_kind"] or ""
    kind_from = "paper" if kind in ("bill", "estimate", "challan") else ""
    if not kind_from:
        kind = ""
        if rd and CLAUDE_KIND.get(rd.get("doc_kind") or ""):
            kind, kind_from = CLAUDE_KIND[rd["doc_kind"]], "Claude's reading"
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
    return {"ok": True, "id": b["id"], "stamp": _stamp(b), "supplier": name, "bill_no": b["bill_no"] or "",
            "date": b["bill_date"] or "", "amount": _plain(b["total_amount"]),
            "scanned": _dmy(b["created_at"]), "month": _ym_short(b["mo"]),
            "file": url_for("bill_file", bid=b["id"]) if b["source_stored"] else "",
            "items": ("Read: " + items_line(it)) if it else "No items read.", "bill_names": [x[0] for x in it],
            "kind": kind, "kind_from": kind_from, "dest": dest, "dest_line": dest_line, "current": DEST_NAME.get(cur, ""),
            "who": "bhawna" if (_col(b, "pe_who") or "") == "bhawna" else "mk", "hints": hints,
            "supplier_note": supplier_note(db, key, name, mode, today, owner), "mode": mode,
            "covers": covers(db, b, mode, today, owner), "flags": flags, "can_page": bool(can_page),
            "status": status, "lane": AR.LANES.get(_lane(b), ("",))[0].split(" — ")[0],
            "owner_line": ("Waiting for Dr Manoj's Save" if (not owner and (b["subgroup"] or "") == "clinic_equipment"
                                                            and b["status"] == "draft") else "")}


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
        new["bill_date"] = AR._norm_date(p.get("bill_date"))
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
    if k not in ("bill", "estimate", "challan"):
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
        raise DeskError("%s is rejected; it stays where it is." % st)
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
            AR._mark_dup(db, bid, first, "desk")
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
    if dest not in DEST_NAME:
        raise DeskError("Choose where it goes.")
    if dest == "personal" and not owner:
        raise DeskError("Personal papers are the owner's alone.", 403)
    k_new = str(p.get("kind") or "").strip()
    AR._audit_bill(db, bid, "desk_saved", {"dest": dest, "kind": k_new or None, "via": "desk"})   # first: a hold written below is newer
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
    b = _row(db, bid)
    if accept and _lane(b) == "clinic" and b["status"] == "draft":
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
            cards[key] = {"key": key, "name": names.get(key) or vendor or key, "mode": md.get(key, ""), "rows": [],
                          "unpaid": [], "what": set(), "n_wait": 0}
        return cards[key]
    for c in awaiting_challans(db, owner):
        key = _key(c["vendor"])
        if not key:
            continue
        cd = card(key, c["vendor"])
        mode = cd["mode"]
        age = CP._age_days(c, today)
        it = items_of(db, c, reading(db, c["id"]))
        cd["rows"].append({"id": c["id"], "stamp": _stamp(c), "date": _dm(c["bill_date"] or c["created_at"]),
                           "age": "%d day%s" % (age, "" if age == 1 else "s"), "items": items_line(it) or "no items read",
                           "amber": challan_amber(mode, c["mo"], age, (key, c["mo"]) in bills, today, amber_days),
                           "month": c["mo"], "final": False})
        cd["n_wait"] += 1
        cd["what"].add(AR.LANES.get(_lane(c), ("",))[0].split(" — ")[0] + ((" · " + CP.SUB.get(c["subgroup"], "")) if c["subgroup"] else ""))
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
        cd["what"].add(AR.LANES.get(_lane(f), ("",))[0].split(" — ")[0] + ((" · " + CP.SUB.get(f["subgroup"], "")) if f["subgroup"] else ""))
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
        cd["foot"] = foot
        cd["rule"] = MODE_RULE[m] if m else (MODE_RULE[""] % amber_days)
        cd["what"] = " / ".join(sorted(x for x in cd["what"] if x))
        out.append(cd)
    out.sort(key=lambda c: c["name"].lower())
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
    d = AR._norm_date(day)
    if not (d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", d) and _iso(d)):
        raise DeskError("Type the day it was paid.")
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
        else:
            kind, owed = ("Estimate slip" if dk == "estimate" else "Bill"), b["total_amount"]
        s["rows"].append({"sort": (b["bill_date"] or b["created_at"] or "")[:10], "d": _dm(b["bill_date"] or b["created_at"]),
                          "p": _stamp(b), "bid": b["id"], "k": kind, "i": it or "—", "o": owed, "pd": paid, "pay": None})
        s["owed"] += owed or 0
        s["paid"] += paid or 0
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
        if key in ("procedure", "xray", "others"):
            early = early_rates(CONS + ("xray",), ("clinic",))
        elif key == "construction":
            early = early_rates(subs, ("clinic", "other_doc"))
        else:
            early = early_rates(subs, ("clinic",))
        ph = ",".join("?" * len(subs))
        if key == "construction":
            live = CP._live_sections(db)
            lanes = "COALESCE(b.lane,'clinic') IN ('clinic','other_doc','owner_expense') AND b.status IN ('draft','approved','captured')"
        else:
            live = CP._live(db)
            lanes = "COALESCE(b.lane,'clinic')='clinic' AND b.status IN ('draft','approved')"
        money = db.execute("SELECT b.* FROM bills b WHERE " + live + " AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.bill_date, b.id",
                           subs + (ym,)).fetchall()
        finals = db.execute("SELECT b.* FROM bills b WHERE " + lanes + " AND b.dup_of IS NULL AND b.page_of IS NULL AND b.doc_kind='challan' "
                            "AND b.challan_state='final' AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.id", subs + (ym,)).fetchall()
        waits = db.execute("SELECT b.* FROM bills b WHERE " + lanes + " AND b.dup_of IS NULL AND b.page_of IS NULL AND b.doc_kind='challan' "
                           "AND COALESCE(b.challan_state,'awaiting')='awaiting' AND b.subgroup IN (" + ph + ") AND " + CP.MONTH_OF + "=? ORDER BY b.id",
                           subs + (ym,)).fetchall()
        paid_rows = list(money) + list(finals)
        total = sum((b["total_amount"] or 0) for b in paid_rows)
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
                           "status": b["status"]})
        secs.append({"key": key, "name": name, "papers": papers, "total": total, "noamt": noamt, "rows": rows, "eq": eq,
                     "money_ids": [b["id"] for b in paid_rows], "final_ids": [b["id"] for b in finals]})
    base = ("FROM bills b WHERE b.status<>'rejected' AND b.dup_of IS NULL AND b.page_of IS NULL AND " + CP.MONTH_OF + "=?")
    one = lambda sql, *a: db.execute("SELECT COUNT(*) " + base + sql, (ym,) + a).fetchone()[0]     # noqa: E731
    pers = "" if owner else " AND COALESCE(b.subgroup,'')<>'personal'"
    pe_all = one(" AND b.lane='owner_expense'" + pers)
    pe_bh = one(" AND b.lane='owner_expense' AND COALESCE(b.pe_who,'')='bhawna'" + pers)
    apart = {"pharmacy": one(" AND b.lane='pharmacy'"), "lab": one(" AND b.lane='lab_purchase'"),
             "mk": pe_all - pe_bh, "bh": pe_bh, "patient": one(" AND b.subgroup=?", PATIENT)}
    nwait = one(" AND b.doc_kind='challan' AND COALESCE(b.challan_state,'awaiting')='awaiting' AND COALESCE(b.lane,'clinic')<>'pharmacy'"
                " AND COALESCE(b.subgroup,'')<>?" + pers, PATIENT)        # FIX1 C2: a patient's challan is in Kept apart only
    return secs, apart, nwait


# ---------------------------------------------------------------------------------------------- the switches
def switch_states(db):
    return {"scan.cv": bool(AR._scan_cv_on()), "scan.lanes5": bool(AR._lanes5_on()), "desk.on": desk_on(db)}


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

OFF_TPL = HEAD + """</head><body><div class=top><span class=t>Sorting desk</span></div>
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
#left{width:250px;flex:none;background:#fff;border-right:1px solid #d6dde6;display:flex;flex-direction:column;min-height:0}
#left.fold{width:44px}#left.fold .in{display:none}#left .unfold{display:none}#left.fold .unfold{display:block;margin:10px auto}
#left .hd{display:flex;justify-content:space-between;align-items:center;padding:10px 12px;border-bottom:1px solid #e6ebf0}
#list{overflow:auto;flex:1 1 auto}
.row{display:block;width:100%;text-align:left;border:0;border-bottom:1px solid #eef1f4;padding:9px 12px;cursor:pointer;font-family:inherit;color:#1f2a36;background:#fff}
.row.on{background:#e3edf7}.row .r1{display:flex;justify-content:space-between;font-size:13px}.row .r2{display:block;font-size:14px;margin-top:2px}.row .r3{display:block;font-size:12px;color:#4a5866;margin-top:2px}
#mid{flex:1 1 auto;min-width:0;display:flex;flex-direction:column;padding:12px 14px;gap:8px}
#scanbox{flex:1 1 auto;min-height:0;background:#5a6470;border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center}
#scan{width:100%;height:100%;border:0;background:#fbfaf7;transition:transform .2s}
#right{width:400px;flex:none;background:#fff;border-left:1px solid #d6dde6;overflow:auto;padding:12px 14px;display:flex;flex-direction:column;gap:12px}
#right label{font-size:12px;color:#4a5866}#right label input{display:block;width:100%;font-size:14px}
.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:6px}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.amber{font-size:13px;background:#fff4dc;border:1px solid #e8c77a;border-radius:8px;padding:8px 10px}
.green{font-size:13px;background:#eaf3ec;border:1px solid #9cc5a6;border-radius:8px;padding:8px 10px;display:flex;flex-direction:column;gap:4px}
.gt{font-size:11px;letter-spacing:.04em;text-transform:uppercase;color:#5b6878;margin-top:4px}
.dests{display:flex;flex-wrap:wrap;gap:6px}
.d{min-height:38px;padding:6px 12px;border-radius:8px;font-size:14px;font-family:inherit;cursor:pointer;color:#1f2a36;border:1px solid #c9d2dc;background:#fff}
.d.on{border:2px solid #2b5d8a;background:#e3edf7;font-weight:700}.d.pe.on{border-color:#6b4a8a;background:#efe7f6}
#save{min-height:50px;border-radius:10px;border:0;background:#2b6e4f;color:#fff;font-size:17px;font-weight:700;cursor:pointer;font-family:inherit}
#save:disabled{background:#9aa8a1;cursor:default}
.err{color:#9c2b2b;font-size:13px}
.flag{font-size:13px;background:#fff4dc;border:1px solid #e8c77a;border-radius:8px;padding:8px 10px}
</style></head><body><div id=app>
<div class=top><span class=t>Sorting desk</span><span class=muted id=wt style="font-size:14px">{{n}} paper{{'' if n==1 else 's'}} waiting · newest first</span>
<span style="flex-grow:1"></span>
<a href="{{url_for('s551_awaited')}}" style="font-size:14px">Bills awaited</a>
<a href="{{url_for('s551_implants')}}" style="font-size:14px">Implant stock ledger</a>
<a href="{{url_for('s551_month')}}" style="font-size:14px">The month</a>
{% if owner %}<a class=chip href="{{url_for('s551_month')}}#s551switches">{{chip}}</a>{% else %}<span class=chip>{{chip}}</span>{% endif %}</div>
<div id=main>
<div id=left><div class=in style="display:flex;flex-direction:column;min-height:0;flex:1 1 auto"><div class=hd><b style="font-size:14px">Waiting</b><button type=button class=b id=fold aria-label="Fold the list">fold ‹</button></div>
<form id=openf style="display:flex;gap:6px;margin:0;padding:8px 12px;border-bottom:1px solid #e6ebf0"><input id=openno placeholder="Open B-____" style="flex:1 1 auto;min-width:0;font-size:13px;padding:4px 6px"><button class=b type=submit>Open</button></form>
<div id=openerr class=err style="padding:0 12px"></div>
<div id=list></div></div><button type=button class="b unfold" id=unfold aria-label="Open the list">›</button></div>
<div id=mid><div style="display:flex;gap:8px;align-items:center"><b style="font-size:15px" id=hstamp>—</b><span class=muted style="font-size:13px" id=hwhen></span><span style="flex-grow:1"></span>
<span class=muted style="font-size:12px">every page and zoom: the viewer's own buttons</span><button type=button class=b id=turn>Turn ↻</button></div>
<div id=scanbox><iframe id=scan title="the scan" src="about:blank"></iframe></div></div>
<div id=right>
<div id=empty class=muted style="display:none">Nothing waiting. Open any paper by its number above.</div>
<div id=panel style="display:flex;flex-direction:column;gap:12px">
<div id=flags style="display:flex;flex-direction:column;gap:6px"></div>
<div style="display:flex;flex-direction:column;gap:6px"><b style="font-size:14px">What was read <span style="font-weight:400" class=muted>— correct anything</span></b>
<div class=grid2><label>Supplier<input id=f_vendor></label><label>Bill / challan no<input id=f_no></label><label>Date<input id=f_date placeholder="dd-mm-yyyy"></label><label>Amount<input id=f_amt inputmode=decimal></label></div>
<div class=muted style="font-size:12px" id=items></div><div class=muted style="font-size:12px" id=status></div></div>
<div style="display:flex;flex-direction:column;gap:6px"><b style="font-size:14px">What kind of paper</b>
<div class=grid3 id=kinds></div><div class=muted style="font-size:12px" id=kindfrom></div>
<div class=amber id=supnote style="display:none"></div>
<div class=green id=covers style="display:none"></div></div>
<div style="display:flex;flex-direction:column;gap:6px"><b style="font-size:14px">Where does it go?</b><div id=groups></div>
<div id=who style="display:none;gap:6px;margin-top:4px"><button type=button class="d pe" data-who=mk>Dr MK</button><button type=button class="d pe" data-who=bhawna>Dr Bhawna</button></div>
<div class=muted style="font-size:12px" id=destnote></div><div id=hints class=muted style="font-size:12px"></div></div>
<div id=pagebox style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:13px"><label style="font-size:13px;color:#1f2a36;display:flex;gap:6px;align-items:center"><input type=checkbox id=pg_on style="width:auto;display:inline"> A page of another paper — join into</label><input id=pg_no placeholder="B-____" style="width:80px;font-size:13px;padding:4px">
<button type=button class=b id=blank title="marks it rejected; nothing is deleted">Blank — discard</button></div>
<button type=button id=save disabled>Choose where it goes</button>
<div class=err id=err></div>
<div class=muted style="font-size:12px" id=savednote>Save files it, accepts it and opens the next paper.</div>
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
 $('openerr').textContent='';S.cur=j;S.dest=j.dest||'';S.kind=j.kind||'';S.who=j.who||'mk';S.flag='';S.rot=0;S.ticks={};(j.covers||[]).forEach(function(c){S.ticks[c.id]=!!c.ticked;});draw();drawList();});}
function draw(){var j=S.cur;$('empty').style.display='none';$('panel').style.display='flex';
 $('hstamp').textContent=j.stamp+' · '+(j.supplier||'supplier not read');$('hwhen').textContent='scanned '+j.scanned+' · '+j.lane;
 $('scan').src=j.file||'about:blank';$('scan').style.transform='';
 $('f_vendor').value=j.supplier;$('f_no').value=j.bill_no;$('f_date').value=j.date;$('f_amt').value=j.amount;
 $('items').textContent=j.items;$('status').textContent='Now: '+(j.current||'not sorted')+' · '+j.status+(j.owner_line?' · '+j.owner_line:'');
 var f='';if(j.flags.hold){f+='<div class=flag>Looks like a second scan of <b>'+esc(j.flags.hold)+'</b>.<br><label><input type=radio name=fl value=same> It is the same — set aside</label><br><label><input type=radio name=fl value=keep> Not the same — keep</label></div>';}
 if(j.flags.s441){f+='<div class=flag>Set aside as a second scan of <b>'+esc(j.flags.s441)+'</b>.<br><label><input type=radio name=fl value=same> Same — leave it set aside</label><br><label><input type=radio name=fl value=restore> Not the same — bring it back</label></div>';}
 if(j.flags.date){f+='<div class=flag>The date looks misread — check.</div>';}
 if(j.flags.nothing){f+='<div class=flag>Nothing could be read — type what you see.</div>';}
 $('flags').innerHTML=f;Array.prototype.forEach.call(document.querySelectorAll('input[name=fl]'),function(r){r.addEventListener('change',function(){S.flag=r.value;paint();});});
 $('pagebox').style.display=j.can_page?'flex':'none';$('pg_on').checked=false;$('pg_no').value='';
 var h='';C.groups.forEach(function(g){h+='<div class=gt>'+esc(g[0])+'</div><div class=dests>';g[1].forEach(function(d){h+='<button type=button class="d'+(d[0]=='pe'?' pe':'')+'" data-d="'+d[0]+'">'+esc(d[1])+'</button>';});h+='</div>';});$('groups').innerHTML=h;
 $('hints').innerHTML=(j.hints||[]).map(function(x){return '<div>'+esc(x)+'</div>';}).join('');
 $('supnote').style.display=j.supplier_note?'block':'none';$('supnote').textContent=j.supplier_note||'';paint();}
function paint(){var j=S.cur;if(!j){return;}
 var k='';C.kinds.forEach(function(x){k+='<button type=button class="b'+(S.kind==x[0]?' on':'')+'" data-k="'+x[0]+'" style="min-height:38px;font-size:14px">'+esc(x[1])+'</button>';});$('kinds').innerHTML=k;
 $('kindfrom').textContent=(j.kind&&S.kind==j.kind&&j.kind_from&&j.kind_from!='paper')?'pre-chosen from '+j.kind_from:'';
 Array.prototype.forEach.call(document.querySelectorAll('#groups .d'),function(b){b.className='d'+(b.getAttribute('data-d')=='pe'?' pe':'')+(S.dest==b.getAttribute('data-d')?' on':'');});
 $('who').style.display=S.dest=='pe'?'flex':'none';Array.prototype.forEach.call(document.querySelectorAll('#who .d'),function(b){b.className='d pe'+(S.who==b.getAttribute('data-who')?' on':'');});
 var note=C.notes[S.dest]||'';if(S.dest=='clinic_equipment'&&!C.owner){note='Waiting for Dr Manoj’s Save after yours: it is filed, not accepted.';}
 if(S.dest&&S.dest==j.dest&&j.dest_line){note=(note?note+' ':'')+j.dest_line;}$('destnote').textContent=note;
 var cv=j.covers||[];if(S.kind=='bill'&&cv.length){var c='<b>This bill covers these challans</b>',names=[];cv.forEach(function(x){c+='<label style="font-size:13px;color:#1f2a36"><input type=checkbox data-c="'+x.id+'" '+(S.ticks[x.id]?'checked':'')+' style="width:auto;display:inline"> '+esc(x.stamp)+' · '+esc(x.date)+' · '+x.n+' item'+(x.n==1?'':'s')+(x.ticked?'':' · '+x.age+' days')+'</label>';if(S.ticks[x.id]){names=names.concat(x.names);}});
  var B={},Cn={},m=0,cnt=0,ex=0;(j.bill_names||[]).forEach(function(n){if(norm(n))B[norm(n)]=1;});names.forEach(function(n){if(norm(n))Cn[norm(n)]=1;});Object.keys(Cn).forEach(function(n){cnt++;if(B[n])m++;});Object.keys(B).forEach(function(n){if(!Cn[n])ex++;});
  c+='<span style="color:#3d5a45">Items on the bill against the ticked challans: '+m+' of '+cnt+' match · '+ex+' extra on the bill · '+(cnt-m)+' missing</span>';$('covers').innerHTML=c;$('covers').style.display='flex';
  Array.prototype.forEach.call(document.querySelectorAll('#covers input[data-c]'),function(x){x.addEventListener('change',function(){S.ticks[x.getAttribute('data-c')]=x.checked;paint();});});}
 else{$('covers').style.display='none';}
 var pg=$('pg_on').checked&&$('pg_no').value.trim();var fl=S.flag;var ready=!!(S.dest||pg||fl=='same'||fl=='restore');
 if((j.flags.hold||j.flags.s441)&&!fl){ready=false;}
 if(fl=='keep'&&!S.dest&&!pg){ready=false;}
 $('save').disabled=!ready;$('save').textContent=ready?'Save — next paper':((j.flags.hold||j.flags.s441)&&!fl?'Answer the question above':'Choose where it goes');}
document.addEventListener('click',function(e){var t=e.target.closest?e.target.closest('[data-id],[data-d],[data-k],[data-who]'):null;if(!t){return;}
 if(t.hasAttribute('data-id')){openPaper(t.getAttribute('data-id'));}
 else if(t.hasAttribute('data-d')){S.dest=t.getAttribute('data-d');paint();}
 else if(t.hasAttribute('data-k')){S.kind=t.getAttribute('data-k');paint();}
 else if(t.hasAttribute('data-who')){S.who=t.getAttribute('data-who');paint();}});
$('pg_on').addEventListener('change',paint);$('pg_no').addEventListener('input',paint);
$('fold').addEventListener('click',function(){$('left').className='fold';});$('unfold').addEventListener('click',function(){$('left').className='';});
$('turn').addEventListener('click',function(){S.rot=(S.rot+90)%360;$('scan').style.transform=S.rot?'rotate('+S.rot+'deg)':'';});
$('openf').addEventListener('submit',function(e){e.preventDefault();var v=$('openno').value.trim();if(!v){return;}getJ(C.find+'?no='+encodeURIComponent(v)).then(function(j){if(j.ok){openPaper(j.id);}else{$('openerr').textContent=j.error||'Not found.';}});});
function post(body){$('save').disabled=true;$('err').textContent='';return fetch(C.save,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){return j;},function(){return{ok:false,error:'The server did not answer ('+r.status+'). Nothing was saved.'};});})
 .then(function(j){if(!j.ok){$('err').textContent=j.error||'Not saved.';paint();return;}S.saved++;$('savednote').textContent=S.saved+' saved this sitting — each can be changed again from its own page. Last: '+j.message;loadList(j.next||0);});}
$('save').addEventListener('click',function(){var j=S.cur;if(!j){return;}var b={id:j.id,vendor:$('f_vendor').value,bill_no:$('f_no').value,bill_date:$('f_date').value,total_amount:$('f_amt').value,kind:S.kind,dest:S.dest,who:S.who,flag:S.flag,joins:[]};
 if(S.kind=='bill'){(j.covers||[]).forEach(function(c){if(S.ticks[c.id]){b.joins.push(c.id);}});}
 if($('pg_on').checked&&$('pg_no').value.trim()){b.page_of=$('pg_no').value.trim();b.dest='';}post(b);});
$('blank').addEventListener('click',function(){var j=S.cur;if(!j){return;}if(!confirm('Discard '+j.stamp+' as blank? It is kept on record, marked rejected.')){return;}post({id:j.id,blank:true,flag:S.flag});});
loadList(0);
})();
</script></body></html>"""


def desk_page():
    db = AR.get_db()
    owner = _owner()
    groups = [[t, [list(d) for d in items if (d[0] != "personal" or owner)]] for t, items in DESTINATIONS]
    cfg = {"list": url_for("s551_api_list"), "paper": url_for("s551_api_paper", bid=0), "find": url_for("s551_api_find"),
           "save": url_for("s551_api_save"), "groups": groups, "kinds": [list(k) for k in KINDS], "notes": NOTES, "owner": owner}
    n = len(waiting(db, owner))
    return render_template_string(DESK_TPL, bg=_bg(), cfg=cfg, n=n, owner=owner, chip=_chip(db), title="Sorting desk")


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


PAGE_HEAD = HEAD + """</head><body>"""

AWAITED_TPL = PAGE_HEAD + """<div class=top><a href="{{url_for('s551_desk')}}" style="font-size:14px">‹ Sorting desk</a><span class=t>Bills awaited — challans by supplier</span><span class=muted style="font-size:14px">Each supplier is set once to how they actually bill.</span></div>
{% if msg %}<div class="msg{{' bad' if bad else ''}}">{{msg}}</div>{% endif %}
<div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;padding:14px 18px">
{% for s in cards %}<div class=card style="display:flex;flex-direction:column;gap:10px">
<div style="display:flex;justify-content:space-between;align-items:baseline;gap:8px"><b style="font-size:17px">{{s.name}}</b><span class=muted style="font-size:13px">{{s.what}}</span></div>
<div style="display:flex;flex-direction:column;gap:6px"><span class="muted small">How they bill</span>
<div style="display:flex;flex-wrap:wrap;gap:6px">{% for k, nm in modes %}<form method=post action="{{url_for('s551_awaited_mode')}}" style="margin:0"><input type=hidden name=key value="{{s.key}}"><input type=hidden name=name value="{{s.name}}"><input type=hidden name=mode value="{{k}}"><button class="b{{' on' if s.mode==k else ''}}">{{nm}}</button></form>{% endfor %}</div>
<span style="font-size:13px;color:#3d4a57;background:#f3f5f8;border-radius:8px;padding:8px 10px">{{s.rule}}</span></div>
<div style="display:flex;flex-direction:column;border:1px solid #e6ebf0;border-radius:8px">{% for r in s.rows %}<div style="padding:9px 10px;border-bottom:1px solid #eef1f4;background:{{'#fff1d6' if r.amber else '#fff'}}" class="{{'amber-row' if r.amber else ''}}">
<div style="display:flex;justify-content:space-between;font-size:14px"><b><a href="{{url_for('bill_view',bid=r.id)}}" style="text-decoration:none;color:inherit">{{r.stamp}}</a> · {{r.date}}</b><span>{{r.age}}</span></div>
<div style="font-size:13px;color:#3d4a57;margin-top:3px">{{r.items}}</div></div>{% endfor %}</div>
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
<span>{{r.d}}</span><span>{% if r.bid %}<a href="{{url_for('bill_view',bid=r.bid)}}">{{r.p}}</a>{% else %}{{r.p}}{% endif %}</span><span>{{r.k}}</span><span style="color:#3d4a57">{{r.i}}{% if r.pay %} <form method=post action="{{url_for('s551_implants_void')}}" style="display:inline;margin:0" onsubmit="return confirm('Void this payment? It stays on record, marked voided.')"><input type=hidden name=id value="{{r.pay}}"><input type=hidden name=s value="{{cur.key}}"><button class=b style="min-height:24px;padding:0 6px;font-size:11px">void</button></form>{% endif %}</span>
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
{% for e in s.eq %}<div style="padding:8px 14px;font-size:14px;border-top:1px solid #f0f2f5"><a href="{{url_for('bill_view',bid=e.bid)}}">{{e.stamp}}</a> · {{e.vendor or 'supplier not read'}} · {{inr(e.amount)}}
{% if e.asset %} · <a href="{{url_for('asset_view',aid=e.asset)}}">{{e.asset_name or 'its machine'}}</a>{% elif e.add %} · <a href="{{url_for('asset_edit', bill_item=e.add)}}">+ asset record</a>{% elif e.status=='draft' %} · <span class=muted>Waiting for Dr Manoj's Save</span>{% endif %}</div>{% endfor %}
</div></details>{% endfor %}</div>
<div style="width:320px;flex:none;display:flex;flex-direction:column;gap:10px">
<div class=card style="display:flex;flex-direction:column;gap:6px" id=keptapart><b style="font-size:15px">Kept apart</b>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>Pharmacy — Sanjeevni</span><b>{{apart.pharmacy}} scan{{'' if apart.pharmacy==1 else 's'}}</b></div>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>NK Pathology</span><b>{{apart.lab}} scan{{'' if apart.lab==1 else 's'}}</b></div>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>Personal expenses</span><b>Dr MK {{apart.mk}} · Dr Bhawna {{apart.bh}}</b></div>
<div style="display:flex;justify-content:space-between;font-size:14px"><span>A patient's paper (case pack)</span><b id=patients>{{apart.patient}}</b></div></div>
<div class=card style="display:flex;flex-direction:column;gap:6px"><b style="font-size:15px">Not in the totals</b>
<div style="font-size:14px">Challans waiting for a bill — counted by quantity only ({{nwait}})</div>
<div style="font-size:14px">Papers still to sort ({{nsort}}) — <a href="{{url_for('s551_desk')}}">open the desk</a></div></div>
<div class=muted style="font-size:13px">One page replaces “Clinic consumables by month” and “Consumption &amp; rate history”. The month is the one set on the bill, else its bill date, else the month it was scanned; supplier spellings are merged. An estimate slip and a paid-on-challan paper count in money; a challan still waiting counts by quantity only.</div></div></div></body></html>"""

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
    d = AR._norm_date(request.form.get("day"))
    try:
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
