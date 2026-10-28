#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""stationery.py -- S568_STATIONERY_STOCK (D730; the owner's "Go", 09:24 IST 16-Oct-2026).

THE OWNER'S RULING (D730 item 2)
    General stationery (A4 packs, notebooks, registers, files) is a clinic expense in the group "Stationery & packaging",
    tracked internally BY QUANTITY against an item list with rates. The list can grow at any time. The owner keeps an
    inventory: received, issued and in stock.

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded hook at its foot, after sorting_desk.init: if this
    file is absent or cannot load, the app runs exactly as before (the desk's stationery panel and the menu item then
    show nothing). Its tables come from its own ensure(db) (additive, idempotent):
        stationery_item   the item list -- name, unit, agreed rate, low-stock level, active / retired
        stationery_line   a desk Save's matched lines, per paper, as SNAPSHOTS (never keyed on bill_items.id); a re-save
                          voids the paper's old lines (kept) and writes the new ones -- never a second set
        stationery_move   the issues (stock goes down): item, quantity, to Lab / Reception / Sanjeevni / Clinic
        stationery_count  the counts: the first count of an item is its opening stock; a later one records the difference
                          as "not accounted for" and sets the stock to the count
    Received is COMPUTED WHEN READ from the saved lines (S568_BRIEF_R1 B2, with S568 FIX1 = K1 CORRECTION 1), by these rules only:
        a line counts only while a paper with the same id AND the same created_at exists and dup_of IS NULL;
        S568 FIX1: and only while that paper is still a live paper in Stationery & packaging (the clinic lane, the group
        stationery) -- or is a challan / estimate joined into one;
        a challan (doc_kind 'challan') and an estimate slip count while live (not set aside, not a page) or while joined (a
        joined one is status 'rejected' with page_of set, or challan_state joined / deleted) into a live Stationery paper;
        a bill (COALESCE(doc_kind,'bill')='bill') counts only when not rejected, page_of IS NULL, and no challan / estimate
        has page_of or challan_of = its id;
        any other paper counts nothing.
    So a join, an undo of a join, a Delete after a join, a hard delete -- and (FIX1) a re-sort on the papers page, a re-lane,
    Blank -- discard, or a rejection -- need no hook: the next read is right, and past figures correct themselves.
    Addresses (the /scanapp prefix is added by the app's middleware):
        GET  /stationery            the owner's page: the inventory, this month's issues, the papers that fed the stock,
                                    the counts, the item list (+ Add item, edited in place, retired -- never deleted once used)
        POST /stationery/item       the item list (owner)
        GET  /stationery/diya       "Stationery diya" -- the staff screen (Roman Hinglish): item, quantity, to whom, Save
        POST /stationery/diya       one issue, no confirmation tap (the server checks behind it)
        POST /stationery/count      a count (the owner; a manager with the switch ON, from Stationery diya)
    Who: the owner always. A manager only while the switch stationery.issue_on is ON (absent = OFF; a row on the owner's
    Switches card). The reception login never (the app's checker gate refuses it).

S585_STATIONERY_ISSUE_MANY (D738; the owner, 14:41-15:10 IST 18-Oct-2026: "develop a system where multiple items can be issued on one
screen"; Shavez's sheet STATIONARY.xlsx "so you can populate that also, and we can edit it later on if needed")
    Stationery diya with the switch stationery.many ON: one screen -- "1 · Kisko diya?" (Lab · Reception · Sanjeevni · Clinic · X-ray),
    "2 · Kya aur kitna diya?" (every active item: shelf stock, -, the number, +) and ONE "Save karo (N)": one issue per item with a
    number, through issue(), in ONE transaction (all or none) -- POST /stationery/diya/many, refused while the switch is OFF.
    The switch OFF (absent = OFF): exactly S568's one-item screen, byte for byte; ON, that screen stays at /stationery/diya?one=1.
    The switch is a card at the top of the owner's Stationery page (POST /stationery/many) -- not on the Switches card, which lives
    in sorting_desk.py and is not touched (R1 C1).
    X-ray is a place (issue(), the many-items screen, the owner's tables); the one-item screen keeps its four (ONE_PLACES, R1 B1).
    Void (the owner only, POST /stationery/void): a line is kept, struck through, and leaves the stock (stock_book ignores voided
    moves); voiding a line made before the latest count changes nothing -- the count stands. Audited in desk_audit.
    Shavez's sheet: seven lines written once by the installer (python3 stationery.py --history <db>; the key stationery.history_s585),
    each 1 s before its item's opening count, so the opening stock stands exactly; never in "this month"; listed in their own fold.
"""
import datetime
import json
import math
import re
import sqlite3
import sys
import time

from flask import abort, flash, g, redirect, render_template_string, request, url_for
from markupsafe import Markup

VERSION = "S674"               # S674_VARIETY_FLOW (D797): the Variety flow on this page -- S568/S585 whole, plus the block below
FIX = "S568_FIX1"             # K1 CORRECTIONS 1-2: the stock follows where the paper is now; the staff screen as the owner's mock-up
MANY = "S585"                 # S585_STATIONERY_ISSUE_MANY (D738): many items on one screen, X-ray as a place, Void, Shavez's sheet
MANY_SWITCH = "stationery.many"                  # absent = OFF: the staff page is exactly S568's one-item screen
HISTORY_KEY = "stationery.history_s585"          # set by the installer's data step when the sheet's lines are written
HISTORY_BY = "history (Shavez sheet)"            # the sheet's lines are known by this by_whom
AR = None                     # the asset app's module, handed in by init()
TODAY = None                  # the walk sets a made-up day here
MOUNTED = False
SWITCH = "stationery.issue_on"
PLACES = (("lab", "Lab"), ("reception", "Reception"), ("sanjeevni", "Sanjeevni"), ("clinic", "Clinic"), ("xray", "X-ray"))   # S585: X-ray
ONE_PLACES = PLACES[:4]       # S585 (R1 B1): the one-item screen's own frozen four -- its bytes stay S568's
PLACE_WORD = dict(PLACES)
UNITS = ("piece", "pack", "ream", "box", "packet", "register", "book", "file", "roll", "bundle", "set", "dozen")
# S585 s3.4: Shavez's sheet STATIONARY.xlsx by the owner's mapping (15:10 IST 18-Oct-2026) -- (the item's EXACT name, quantity, place, what)
HISTORY = (("Register 72 pages", 6, "reception", "the OPD register"),
           ("Register 104 pages", 6, "reception", "the lab register kept at reception"),
           ("Register 192 pages", 3, "lab", "the lab register"),
           ("Register 104 pages", 6, "lab", "the A/C register"),
           ("Small notebook (copy)", 2, "lab", "the expense copy"),
           ("Notebook (copy) 72 pages", 6, "sanjeevni", "Medical's daily detail"),
           ("Small notebook (copy)", 2, "xray", "X-ray"))

DDL = (
    "CREATE TABLE IF NOT EXISTS stationery_item(id INTEGER PRIMARY KEY, name TEXT NOT NULL, unit TEXT NOT NULL DEFAULT 'piece', "
    "rate REAL, low_level REAL, active INTEGER NOT NULL DEFAULT 1, made_by TEXT, made_at TEXT, from_bill_id INTEGER, "
    "from_bill_created_at TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS stationery_line(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, bill_created_at TEXT NOT NULL DEFAULT '', "
    "line_no INTEGER NOT NULL, name TEXT NOT NULL DEFAULT '', qty REAL, unit TEXT NOT NULL DEFAULT '', rate REAL, item_id INTEGER, "
    "not_stock INTEGER NOT NULL DEFAULT 0, day TEXT NOT NULL, ts REAL NOT NULL, by_whom TEXT, at TEXT, "
    "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS stationery_move(id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, qty REAL NOT NULL, place TEXT NOT NULL, "
    "day TEXT NOT NULL, ts REAL NOT NULL, stock_before REAL, by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', "
    "voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS stationery_count(id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, counted REAL NOT NULL, stock_before REAL, "
    "diff REAL, opening INTEGER NOT NULL DEFAULT 0, day TEXT NOT NULL, ts REAL NOT NULL, by_whom TEXT, at TEXT)",
    "CREATE INDEX IF NOT EXISTS stationery_line_bill ON stationery_line(bill_id)",
)
TABLES = ("stationery_item", "stationery_line", "stationery_move", "stationery_count")


# ---------------------------------------------------------------------------------------------- the database's part
def ensure(db):
    """Additive and idempotent. Two gunicorn workers start at once: 'already exists' from the second is normal."""
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    ensure_s674(db)                                                  # S674: the statement table; side and stmt_id on stationery_line
    db.commit()


def ensure_at_mount(db_path, tries=3, wait=1.0, timeout=3):
    """As sorting_desk.ensure_at_mount: 'database is locked' is retried briefly, then left to the installer's data step."""
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
    print("stationery: the database stayed locked at mount; its tables are left to the installer's data step", file=sys.stderr)
    return False


def ensure_path(db_path):
    con = sqlite3.connect(db_path, timeout=20)
    try:
        ensure(con)
    finally:
        con.close()
    return TABLES


# ---------------------------------------------------------------------------------------------- small helpers
def _today():
    return TODAY or datetime.date.today()


def _ym():
    return _today().strftime("%Y-%m")


def _who():
    try:
        return g.user["display_name"] or g.user["username"]
    except Exception:                                                # noqa: BLE001
        return ""


def _role():
    try:
        return g.user["role"] or ""
    except Exception:                                                # noqa: BLE001
        return ""


def _now():
    try:
        return AR._now_ist()
    except Exception:                                                # noqa: BLE001
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _setting(db, key, default):
    try:
        r = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r[0] if (r and r[0] is not None) else default
    except sqlite3.Error:
        return default


def issue_on(db):
    return (_setting(db, SWITCH, "off") or "").strip().lower() == "on"


def many_on(db):
    """S585: the many-items screen -- absent = OFF."""
    return (_setting(db, MANY_SWITCH, "off") or "").strip().lower() == "on"


def may_issue(db, role=None):
    """The owner always; a manager only while stationery.issue_on is ON; the reception login never."""
    role = _role() if role is None else role
    return role == "owner" or (role == "manager" and issue_on(db))


def _num(v):
    if v is None or isinstance(v, bool):
        return None
    s = str(v).replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    if not s:
        return None
    try:
        f = float(s)
    except (TypeError, ValueError):
        return None
    return f if math.isfinite(f) else None


def _plain(x):
    if x is None:
        return ""
    f = float(x)
    return ("%d" % f) if f == int(f) else ("%g" % round(f, 3))


def _grp(n):
    s = "%d" % n
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
    return head + "," + tail


def rs(x):
    """₹ with Indian grouping; paise shown only when there are any."""
    if x is None:
        return "—"
    f = float(x)
    neg = f < 0
    f = abs(f)
    if round(f, 2) == int(round(f, 2)):
        t = _grp(int(round(f)))
    else:
        t = _grp(int(f)) + ("%.2f" % (f - int(f)))[1:]
    return ("-" if neg else "") + "₹" + t


def qty_text(q, unit):
    if q is None:
        return "—"
    return "%s %s" % (_plain(q), unit or "")


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


_UNIT_SAME = {"pcs": "piece", "pc": "piece", "pieces": "piece", "nos": "piece", "no": "piece", "nag": "piece", "pkt": "packet",
              "pkts": "packet", "packets": "packet", "packs": "pack", "pk": "pack", "reams": "ream", "boxes": "box", "rolls": "roll",
              "sets": "set", "books": "book", "registers": "register", "files": "file", "dozens": "dozen", "doz": "dozen",
              "bundles": "bundle"}


def unit_key(u):
    u = re.sub(r"[^a-z]", "", str(u or "").lower())
    return _UNIT_SAME.get(u, u)


def pack_of(unit):
    """S624 (F-979): N when a unit names a count ('packet of 100', 'box of 50'), else None."""
    m = re.search(r"\bof\s+(\d+)\b", str(unit or "").lower())
    n = int(m.group(1)) if m else 0
    return n if n > 1 else None


def pack_check(qty, line_unit, item):
    """S624 (F-979): '' -- or a plain line when an item is counted in packets of N and the line's quantity is N or a whole multiple
    of N while the line does not itself say packets: the paper may mean single pieces (B-0013: 'Token 100' = 1 packet of 100)."""
    q = _num(qty)
    if item is None or q is None:
        return ""
    n = pack_of(item["unit"])
    if not n or q < n or abs(q / n - round(q / n)) > 1e-9 or unit_key(line_unit) not in ("", "piece"):
        return ""                                                    # only a line in pieces (or with no unit) is questioned
    return ("%s: %s saved, and the list counts it in '%s' — if the paper means %s single pieces, type %s instead and Save again."
            % (item["name"], _plain(q), item["unit"], _plain(q), _plain(q / n)))


def rate_flag(line_rate, line_unit, item):
    """S568 item 3 (R1 note 19): '' -- or 'rate ₹x — list ₹y' when both rates are there and differ after rounding to paise, in
    the item's unit; a line in another unit says 'unit differs' instead (never compared as a rate)."""
    if item is None:
        return ""
    lu, iu = unit_key(line_unit), unit_key(item["unit"])
    if lu and iu and lu != iu:
        return "unit differs — on the paper: %s, on the list: %s" % (line_unit, item["unit"])
    if line_rate is None or item["rate"] is None:
        return ""
    if round(float(line_rate), 2) != round(float(item["rate"]), 2):
        return "rate %s — list %s" % (rs(line_rate), rs(item["rate"]))
    return ""


# ---------------------------------------------------------------------------------------------- the item list
def item_rows(db, active_only=False):
    try:
        rows = db.execute("SELECT * FROM stationery_item" + (" WHERE active=1" if active_only else "") +
                          " ORDER BY active DESC, lower(name), id").fetchall()
    except sqlite3.Error:
        return []
    return [dict(r) for r in rows]


def item_used(db, iid):
    for sql in ("SELECT 1 FROM stationery_line WHERE item_id=? LIMIT 1", "SELECT 1 FROM stationery_move WHERE item_id=? LIMIT 1",
                "SELECT 1 FROM stationery_count WHERE item_id=? LIMIT 1"):
        if db.execute(sql, (iid,)).fetchone():
            return True
    return False


def _audit(db, action, detail):
    """Into the desk's own book (desk_audit, sorting_desk's table); fail-soft when it is absent."""
    try:
        db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                   (_now(), _who(), action, json.dumps(detail or {}, ensure_ascii=False)[:500]))
    except sqlite3.Error:
        pass


def add_item(db, name, unit, rate, low, who=None, paper=None):
    """A new item -- or the active item of the same name (normalised), never a second one. Returns (id, made). No commit."""
    name = re.sub(r"\s+", " ", str(name or "")).strip()[:120]
    if not name:
        raise ValueError("Type the item's name.")
    k = norm(name)
    for it in item_rows(db, active_only=True):
        if norm(it["name"]) == k:
            return it["id"], False
    unit = re.sub(r"\s+", " ", str(unit or "")).strip()[:30] or "piece"
    cur = db.execute("INSERT INTO stationery_item(name, unit, rate, low_level, active, made_by, made_at, from_bill_id, from_bill_created_at) "
                     "VALUES(?,?,?,?,1,?,?,?,?)", (name, unit, rate, low, who if who is not None else _who(), _now(),
                                                    paper["id"] if paper is not None else None,
                                                    (paper["created_at"] or "") if paper is not None else ""))
    _audit(db, "stationery_item_added", {"id": cur.lastrowid, "name": name, "unit": unit, "rate": rate, "low": low,
                                         "from_bill": paper["id"] if paper is not None else None})
    return cur.lastrowid, True


def prematch(name, items):
    """A pre-match by name (offered, never saved without a person's Save): the active item whose name equals the line's, else
    the one item whose every word stands in the line's name (the longest such name; a tie = no pre-match)."""
    k = norm(name)
    if not k:
        return None
    for it in items:
        if norm(it["name"]) == k:
            return it
    words = set(k.split())
    cands = [it for it in items if norm(it["name"]) and set(norm(it["name"]).split()) <= words]
    if not cands:
        return None
    cands.sort(key=lambda it: -len(norm(it["name"])))
    if len(cands) > 1 and len(norm(cands[0]["name"])) == len(norm(cands[1]["name"])):
        return None
    return cands[0]


# ---------------------------------------------------------------------------------------------- a paper's lines
def _cols(db):
    return {r[1] for r in db.execute("PRAGMA table_info(bills)")}


def _here_sql(a):
    """S568 FIX1 (K1 CORRECTION 1): the paper is in Stationery & packaging NOW -- the clinic lane and the group stationery."""
    return "COALESCE(%s.lane,'clinic')='clinic' AND COALESCE(%s.subgroup,'')='stationery'" % (a, a)


def _paper_sql(db, a="b", here=True):
    """R1 B2's rules with K1 CORRECTION 1 (S568 FIX1), as one condition on the paper `a`: its lines count only while it is still
    a live paper in Stationery & packaging, or a challan / estimate joined into one.
        live:   not a second scan; on the clinic lane in the group stationery (here=False leaves this test out -- the desk's
                panel asks it of a paper about to be saved there);
        a challan / estimate: not set aside and not a page (status<>'rejected', page_of IS NULL, not joined) -- or JOINED
                (page_of set, or challan_state joined / deleted) into a paper that is itself live in Stationery & packaging;
                so one re-sorted elsewhere, moved to another lane, discarded as blank or rejected counts nothing;
        a bill: not set aside, not a page, and no challan / estimate joined into it;
        anything else: nothing.
    Stock is computed when read, so a paper moved out by any door (the desk, the papers page's chooser, the re-lane route, Blank)
    stops counting at the next read, and one moved back counts again -- no hook and no data step."""
    cols = _cols(db)
    has_cs, has_co = "challan_state" in cols, "challan_of" in cols
    cof = (" OR c.challan_of=%s.id" % a) if has_co else ""
    joined = "%s.page_of IS NOT NULL" % a + ((" OR COALESCE(%s.challan_state,'') IN ('joined','deleted')" % a) if has_cs else "")
    head = ("COALESCE(%s.page_of, %s.challan_of)" % (a, a)) if has_co else ("%s.page_of" % a)
    live_head = ("EXISTS (SELECT 1 FROM bills h WHERE h.id=" + head + " AND h.dup_of IS NULL AND h.status<>'rejected' "
                 "AND h.page_of IS NULL AND " + _here_sql("h") + ")")
    own = (" AND " + _here_sql(a)) if here else ""
    return ("(%s.dup_of IS NULL%s AND ("
            "(COALESCE(%s.doc_kind,'') IN ('challan','estimate') AND ("
            "(%s.status<>'rejected' AND NOT (%s)) OR ((%s) AND %s)))"
            " OR (COALESCE(%s.doc_kind,'bill')='bill' AND %s.status<>'rejected' AND %s.page_of IS NULL AND NOT EXISTS ("
            "SELECT 1 FROM bills c WHERE COALESCE(c.doc_kind,'') IN ('challan','estimate') AND (c.page_of=%s.id%s)))))"
            % (a, own, a, a, joined, joined, live_head, a, a, a, a, cof))


def _counted_sql(db):
    """R1 B2's rules with K1 CORRECTION 1, as one WHERE over stationery_line l JOIN bills b."""
    return "l.voided_at='' AND l.item_id IS NOT NULL AND l.not_stock=0 AND l.qty IS NOT NULL AND COALESCE(l.side,'clinic')='clinic' AND " + _paper_sql(db, "b")      # S674


_JOIN = "FROM stationery_line l JOIN bills b ON b.id=l.bill_id AND COALESCE(b.created_at,'')=l.bill_created_at"


def paper_counts(db, b, here=True):
    """(True, '') when this paper's matched lines go into the stock now; else (False, why). The same rule as the stock's read
    (_paper_sql). here=False: as if it were saved in Stationery & packaging now (the desk's panel, before its Save)."""
    try:
        if db.execute("SELECT 1 FROM bills b WHERE b.id=? AND " + _paper_sql(db, "b", here), (b["id"],)).fetchone():
            return True, ""
    except sqlite3.Error:
        return False, "the stock could not be read"
    dk = (b["doc_kind"] or "")
    if b["dup_of"]:
        return False, "a second scan adds nothing to the stock"
    if dk in ("receipt", "statement"):
        return False, "a receipt or a statement adds nothing to the stock"
    if here and not ((b["lane"] or "clinic") == "clinic" and (b["subgroup"] or "") == "stationery"):
        return False, "it is not in Stationery & packaging now, so its lines add nothing to the stock"
    if dk in ("challan", "estimate"):
        if b["page_of"] or (b["challan_state"] if "challan_state" in b.keys() else "") in ("joined", "deleted"):
            return False, "the paper it is joined into is not in Stationery & packaging now, so its lines add nothing to the stock"
        return False, "a paper set aside adds nothing to the stock"
    if b["status"] == "rejected" or b["page_of"]:
        return False, "a paper set aside, or a page of another paper, adds nothing to the stock"
    cols = _cols(db)
    q = "SELECT COUNT(*) FROM bills c WHERE COALESCE(c.doc_kind,'') IN ('challan','estimate') AND (c.page_of=?" + (" OR c.challan_of=?" if "challan_of" in cols else "") + ")"
    n = db.execute(q, (b["id"], b["id"]) if "challan_of" in cols else (b["id"],)).fetchone()[0]
    if n:
        return False, "this bill joins %d challan%s — the stock came from %s; the bill adds nothing more" % (n, "" if n == 1 else "s", "it" if n == 1 else "them")
    return False, "its lines add nothing to the stock"


def saved_lines(db, b):
    try:
        return [dict(r) for r in db.execute("SELECT * FROM stationery_line WHERE bill_id=? AND bill_created_at=? AND voided_at='' ORDER BY line_no, id",
                                            (b["id"], b["created_at"] or ""))]
    except sqlite3.Error:
        return []


def read_lines(db, b, rd):
    """The paper's lines -- Claude's reading (name, qty, unit, rate) when there is one, else the paper's own items."""
    out = []
    if rd and rd.get("items"):
        for i in rd["items"]:
            out.append({"name": re.sub(r"\s+", " ", str(i.get("name") or "")).strip(), "qty": _num(i.get("qty")),
                        "unit": str(i.get("unit") or "").strip(), "rate": _num(i.get("rate"))})
    else:
        for r in db.execute("SELECT item_name, quantity, pack_size, rate FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)):
            out.append({"name": re.sub(r"\s+", " ", str(r[0] or "")).strip(), "qty": _num(r[1]), "unit": (r[2] or "").strip(), "rate": _num(r[3])})
    return [x for x in out if x["name"]]


def panel(db, b, rd):
    """The desk's Stationery & packaging panel for one paper: its lines (saved snapshot first, else the read line with a
    pre-match by name), the active items, and whether its lines go into the stock now."""
    items = item_rows(db)
    byid = {i["id"]: i for i in items}
    act = [i for i in items if i["active"]]
    rl = read_lines(db, b, rd)
    saved = {}
    for s in saved_lines(db, b):
        saved.setdefault(s["line_no"], s)
    n = max([len(rl)] + list(saved.keys())) if (rl or saved) else 0
    lines = []
    for k in range(1, n + 1):
        s, r = saved.get(k), (rl[k - 1] if k - 1 < len(rl) else None)
        if s is not None:
            it = byid.get(s["item_id"]) if s["item_id"] else None
            lines.append({"no": k, "name": s["name"], "qty": _plain(s["qty"]), "unit": s["unit"], "rate": s["rate"],
                          "item": ("ns" if s["not_stock"] else (s["item_id"] or "")), "saved": True, "sug": False, "hand": r is None,
                          "flag": rate_flag(s["rate"], s["unit"], it) if it else ""})
        elif r is not None:
            sg = prematch(r["name"], act)
            lines.append({"no": k, "name": r["name"], "qty": _plain(r["qty"]), "unit": r["unit"], "rate": r["rate"],
                          "item": (sg["id"] if sg else ""), "saved": False, "sug": bool(sg), "hand": False,
                          "flag": rate_flag(r["rate"], r["unit"], sg) if sg else ""})
    noread = not rl and not saved
    if noread:
        lines.append({"no": 1, "name": "", "qty": "", "unit": "", "rate": None, "item": "", "saved": False, "sug": False, "hand": True, "flag": ""})
    ok, why = paper_counts(db, b, here=False)                       # the panel shows only with Stationery & packaging chosen
    return {"lines": lines, "items": [{"id": i["id"], "name": i["name"], "unit": i["unit"], "rate": i["rate"]} for i in act],
            "noread": noread, "counts": ok, "why": why}


def _key_of(t):
    no, name, q, unit, rate, iid, ns = t[:7]
    side = t[7] if len(t) > 7 else "clinic"                          # S674
    return (no, name, "" if q is None else "%.4f" % q, unit, "" if rate is None else "%.4f" % rate, iid or 0, ns, side)


def save_lines(db, b, lines, who=None):
    """One desk Save's lines for this paper. An untouched line (nothing chosen) is not stored and never blocks the Save. A line
    matched to an item needs its quantity; 'new' adds the line to the list first (its name, unit and rate); 'ns' = not a stock
    item. A re-save REPLACES the paper's own lines (the old ones voided and kept) -- never adds them again; their day and order
    are the paper's first stationery save. No commit. Returns the Save's words. Refusals raise ValueError (plain words)."""
    who = _who() if who is None else who
    items = {i["id"]: i for i in item_rows(db)}
    new, made = [], 0
    for x in list(lines or [])[:300]:
        if not isinstance(x, dict):
            continue
        try:
            no = int(x.get("no"))
        except (TypeError, ValueError):
            continue
        if no < 1 or no > 500:
            continue
        sel = str(x.get("item") if x.get("item") is not None else "").strip()
        if not sel:
            continue                                                 # untouched: counts nothing, never blocks the Save
        name = re.sub(r"\s+", " ", str(x.get("name") or "")).strip()[:120]
        unit = re.sub(r"\s+", " ", str(x.get("unit") or "")).strip()[:30]
        rate = _num(x.get("rate"))
        q = _num(x.get("qty"))
        side = "nk" if str(x.get("side") or "").strip() == "nk" else "clinic"            # S674: the desk sends none -> clinic
        if sel == "ns":
            new.append((no, name, q, unit, rate, None, 1, side))
            continue
        if q is None or q <= 0:
            raise ValueError("Stationery line %d (%s): type the quantity received — or leave the line unmatched." % (no, name or "no name"))
        if sel == "new":
            if not name:
                raise ValueError("Stationery line %d: type the item's name to add it to the list." % no)
            iid, mk = add_item(db, name, unit or "piece", rate, None, who, b)
            made += 1 if mk else 0
            items = {i["id"]: i for i in item_rows(db)}
        else:
            iid = int(sel) if sel.isdigit() else 0
            if iid not in items:
                raise ValueError("Stationery line %d: that item is not on the list." % no)
            if not items[iid]["active"] and not any(l["item_id"] == iid and l["line_no"] == no for l in saved_lines(db, b)):
                raise ValueError("Stationery line %d: %s is retired — bring it back on the Stationery page first." % (no, items[iid]["name"]))
        new.append((no, name, q, unit, rate, iid, 0, side))
    old = saved_lines(db, b)
    if any((l["stmt_id"] if "stmt_id" in l.keys() else None) for l in old):                 # S674: on a statement -- never counted twice
        raise ValueError("%s is on a statement — its lines are changed from the statement, not here." % ((b["stamp_no"] or "").strip() or ("#%d" % b["id"])))
    oldk = sorted(_key_of((l["line_no"], l["name"], l["qty"], l["unit"], l["rate"], l["item_id"], l["not_stock"], (l["side"] if "side" in l.keys() else "clinic"))) for l in old)
    newk = sorted(_key_of(t) for t in new)
    ok, why = paper_counts(db, b)
    nm = len([t for t in new if t[5] and t[7] == "clinic"])           # S674: the stock's lines are the clinic's
    nk = len([t for t in new if t[5] and t[7] == "nk"])
    if oldk == newk:
        return ["Stationery: unchanged."] if new else []
    first = db.execute("SELECT MIN(ts), MIN(day) FROM stationery_line WHERE bill_id=? AND bill_created_at=?", (b["id"], b["created_at"] or "")).fetchone()
    ts = first[0] if (first and first[0] is not None) else time.time()
    day = first[1] if (first and first[1]) else _today().isoformat()
    now = _now()
    if old:
        db.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (now, who, b["id"], b["created_at"] or ""))
    for no, name, q, unit, rate, iid, ns, side in sorted(new):
        db.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at, side) "
                   "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (b["id"], b["created_at"] or "", no, name, q, unit, rate, iid, ns, day, ts, who, now, side))
    _audit(db, "stationery_lines", {"bill": b["id"], "lines": len(new), "matched": nm, "replaced": len(old), "new_items": made})
    msg = ("Stationery: %d line%s matched" % (nm, "" if nm == 1 else "s")) + (" (%d new on the list)" % made if made else "")
    if nm:
        msg += " — into the stock." if ok else " — not added to the stock: %s." % why
    else:
        msg += "."
    if nk:
        msg += " %d line%s to NK Pathology's ledger (not the clinic's stock)." % (nk, "" if nk == 1 else "s")       # S674
    if old:
        msg += " Its earlier lines are replaced, never counted twice."
    chk = [pack_check(t[2], t[3], items.get(t[5])) for t in new if t[5] and not t[6]]          # S624 (F-979)
    chk = [c for c in chk if c]
    if chk:
        msg += " Check: " + " ".join(chk)
    return [msg]


def void_lines(db, b, who=None, why=""):
    """The paper's live lines voided (kept) -- a re-save that takes it out of Stationery & packaging. No commit.
    S674: a line on a statement is never voided from here (it would be billed again) -- refused with the words."""
    try:
        if db.execute("SELECT 1 FROM stationery_line WHERE bill_id=? AND bill_created_at=? AND voided_at='' AND stmt_id IS NOT NULL LIMIT 1",
                      (b["id"], b["created_at"] or "")).fetchone():
            raise ValueError("%s is on a supplier statement — its lines stay; withdraw the statement first (Stationery, section 5)." % ((b["stamp_no"] or "").strip() or ("#%d" % b["id"])))
    except sqlite3.OperationalError:
        pass                                                         # no stmt_id column yet (before the first mount): nothing is on a statement
    n = db.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (_now(), _who() if who is None else who, b["id"], b["created_at"] or "")).rowcount
    if n:
        _audit(db, "stationery_lines_voided", {"bill": b["id"], "lines": n, "why": why})
    return n


def has_lines(db, b):
    return bool(saved_lines(db, b))


# ---------------------------------------------------------------------------------------------- the stock
def received_rows(db):
    """Every line counted into the stock now (R1 B2's rules), with its paper."""
    try:
        return [dict(r) for r in db.execute("SELECT l.*, b.stamp_no AS stamp, b.vendor AS vendor, b.doc_kind AS dk " + _JOIN +
                                            " WHERE " + _counted_sql(db) + " ORDER BY l.ts, l.id")]
    except sqlite3.Error:
        return []


def stock_book(db):
    """{item id: dict(stock, counted, recv, iss)} -- stock = the last count + received after it - issued after it (no count
    yet: received - issued). The order is each record's own moment (ts; a paper's lines: its first stationery save)."""
    out = {}
    try:
        counts = [dict(r) for r in db.execute("SELECT * FROM stationery_count ORDER BY ts, id")]
        issues = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE voided_at='' ORDER BY ts, id")]
    except sqlite3.Error:
        counts, issues = [], []
    last = {}
    for c in counts:
        last[c["item_id"]] = c
    recv = received_rows(db)
    for it in item_rows(db):
        i = it["id"]
        lc = last.get(i)
        since = lc["ts"] if lc else None
        r = sum(x["qty"] for x in recv if x["item_id"] == i and (since is None or x["ts"] > since))
        s = sum(x["qty"] for x in issues if x["item_id"] == i and (since is None or x["ts"] > since))
        out[i] = {"stock": (lc["counted"] if lc else 0.0) + r - s, "counted": bool(lc)}
    return out


def stock_of(db, iid):
    return stock_book(db).get(iid, {"stock": 0.0})["stock"]


def issue(db, iid, qty, place, who=None):
    """One issue: stock goes down. A quantity above the stock is still saved (flagged on the owner's page). No commit."""
    it = next((i for i in item_rows(db, active_only=True) if i["id"] == iid), None)
    if it is None:
        raise ValueError("Kya diya — list se chuno.")
    q = _num(qty)
    if q is None or q <= 0:
        raise ValueError("Kitna diya — number likho.")
    if place not in PLACE_WORD:
        raise ValueError("Kisko diya — Lab, Reception, Sanjeevni, Clinic ya X-ray chuno.")
    before = stock_of(db, iid)
    cur = db.execute("INSERT INTO stationery_move(item_id, qty, place, day, ts, stock_before, by_whom, at) VALUES(?,?,?,?,?,?,?,?)",
                     (iid, q, place, _today().isoformat(), time.time(), before, _who() if who is None else who, _now()))
    _audit(db, "stationery_issue", {"id": cur.lastrowid, "item": iid, "qty": q, "place": place, "stock_before": before})
    return it, q, before


def count(db, got, who=None):
    """{item id: counted}. The first count of an item is its opening stock; a later one records the difference as 'not
    accounted for' and sets the stock to the count. No commit. Returns [(item, counted, before, diff, opening)]."""
    out = []
    items = {i["id"]: i for i in item_rows(db, active_only=True)}
    book = stock_book(db)
    for iid, n in sorted(got.items()):
        if iid not in items:
            continue
        had = db.execute("SELECT 1 FROM stationery_count WHERE item_id=? LIMIT 1", (iid,)).fetchone() is not None
        before = book.get(iid, {"stock": 0.0})["stock"]
        diff = n - before
        db.execute("INSERT INTO stationery_count(item_id, counted, stock_before, diff, opening, day, ts, by_whom, at) VALUES(?,?,?,?,?,?,?,?,?)",
                   (iid, n, before, diff, 0 if had else 1, _today().isoformat(), time.time(), _who() if who is None else who, _now()))
        _audit(db, "stationery_count", {"item": iid, "counted": n, "before": before, "opening": not had})
        out.append((items[iid], n, before, diff, not had))
    return out


def mixed_n(db, ym, key=None):
    """S568 item 6: the papers ticked 'mixed: clinic + lab items' this month (a joined challan still counts); one supplier's when
    `key` (clinic_papers._supplier_key) is given."""
    cp = sys.modules.get("clinic_papers")
    if cp is None or "mixed" not in _cols(db):
        return 0
    n = 0
    for r in db.execute("SELECT b.vendor FROM bills b WHERE COALESCE(b.mixed,0)=1 AND b.dup_of IS NULL AND (b.status<>'rejected' OR b.page_of IS NOT NULL) "
                        "AND " + cp.MONTH_OF + "=?", (ym,)):
        if key is None or cp._supplier_key(r[0]) == key:
            n += 1
    return n


def _issue_view(x, byid, lastc):
    """S585: one issue line for the owner's page -- voided (kept, struck through), made before the item's latest count (voiding it
    changes nothing), or one of Shavez's sheet."""
    it = byid.get(x["item_id"]) or {}
    lc = lastc.get(x["item_id"])
    voided = bool(x["voided_at"])
    return {"id": x["id"], "day": x["day"], "item": it.get("name", "?"), "unit": it.get("unit", ""), "qty": x["qty"],
            "place": PLACE_WORD.get(x["place"], x["place"]), "who": x["by_whom"] or "",
            "over": (not voided and x["stock_before"] is not None and x["qty"] > x["stock_before"] + 1e-9), "before": x["stock_before"],
            "voided": voided, "vby": x["voided_by"] or "", "vat": (x["voided_at"] or "")[:16],
            "pre": (lc is not None and x["ts"] <= lc), "hist": (x["by_whom"] or "") == HISTORY_BY}


def inventory(db, ym):
    """The owner's page: one row per item, this month's issues, counts and the papers that fed the stock."""
    items = item_rows(db)
    book = stock_book(db)
    recv = received_rows(db)
    try:
        allines = [dict(r) for r in db.execute("SELECT l.*, b.stamp_no AS stamp " + _JOIN + " WHERE l.voided_at='' AND l.item_id IS NOT NULL "
                                               "AND l.rate IS NOT NULL AND b.dup_of IS NULL ORDER BY l.ts, l.id")]
        issues = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE voided_at='' AND substr(day,1,7)=? AND COALESCE(by_whom,'')<>? "
                                              "ORDER BY ts, id", (ym, HISTORY_BY))]                  # S585 C3: the sheet is never "this month"
        shown = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE COALESCE(by_whom,'')<>? ORDER BY ts, id", (HISTORY_BY,))]
        hist = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE COALESCE(by_whom,'')=? ORDER BY ts, id", (HISTORY_BY,))]
        lastc = {r[0]: r[1] for r in db.execute("SELECT item_id, MAX(ts) FROM stationery_count GROUP BY item_id")}
        counts = [dict(r) for r in db.execute("SELECT * FROM stationery_count WHERE substr(day,1,7)=? ORDER BY ts, id", (ym,))]
    except sqlite3.Error:
        allines, issues, counts = [], [], []
        shown, hist, lastc = [], [], {}
    byid = {i["id"]: i for i in items}
    rows = []
    for it in items:
        i = it["id"]
        st = book.get(i, {"stock": 0.0})["stock"]
        rm = sum(x["qty"] for x in recv if x["item_id"] == i and (x["day"] or "")[:7] == ym)
        bp = {k: sum(x["qty"] for x in issues if x["item_id"] == i and x["place"] == k) for k, _w in PLACES}
        lr = [x for x in allines if x["item_id"] == i]
        rows.append({"id": i, "name": it["name"], "unit": it["unit"], "rate": it["rate"], "low": it["low_level"], "active": it["active"],
                     "stock": st, "recv": rm, "by_place": bp, "last_rate": lr[-1]["rate"] if lr else None,
                     "last_stamp": lr[-1]["stamp"] if lr else "", "is_low": (it["low_level"] is not None and st <= it["low_level"]),
                     "over": any(x["item_id"] == i and x["stock_before"] is not None and x["qty"] > x["stock_before"] + 1e-9 for x in issues),
                     "used": item_used(db, i),
                     "pack": sorted({x["stamp"] or ("#%d" % x["bill_id"]) for x in recv if x["item_id"] == i and (x["day"] or "")[:7] == ym
                                     and pack_check(x["qty"], x["unit"], it)})})                                   # S624 (F-979): this month's
    iss = [_issue_view(x, byid, lastc) for x in shown if (x["day"] or "")[:7] == ym]                     # S585: voided lines shown, struck
    older = [_issue_view(x, byid, lastc) for x in reversed(shown) if (x["day"] or "")[:7] != ym]         # S585: the "Show all issues" fold
    hst = [_issue_view(x, byid, lastc) for x in hist]                                                     # S585: Shavez's sheet
    cts = [{"day": x["day"], "item": (byid.get(x["item_id"]) or {}).get("name", "?"), "unit": (byid.get(x["item_id"]) or {}).get("unit", ""),
            "counted": x["counted"], "before": x["stock_before"], "diff": x["diff"], "opening": bool(x["opening"]), "who": x["by_whom"] or ""}
           for x in counts]
    fed = {}
    for x in recv:
        if (x["day"] or "")[:7] != ym:
            continue
        f = fed.setdefault(x["bill_id"], {"bid": x["bill_id"], "stamp": x["stamp"] or ("#%d" % x["bill_id"]), "vendor": x["vendor"] or "",
                                          "kind": {"challan": "Challan", "estimate": "Estimate slip"}.get(x["dk"] or "", "Bill"), "n": 0})
        f["n"] += 1
    return {"rows": rows, "issues": iss, "counts": cts, "fed": sorted(fed.values(), key=lambda f: f["bid"]), "mixed": mixed_n(db, ym),
            "older": older, "history": hst}


# ---------------------------------------------------------------------------------------------- the pages
OFF_LINE = "Yeh page abhi band hai — Dr Manoj chalu karenge."

STOCK_TPL = """<h2 style="margin-bottom:4px">Stationery &amp; packaging — the stock</h2>
<p class=muted style="margin-top:0">{{label}} · general stationery tracked by quantity. Received comes from the challans, bills and estimate slips matched on the sorting desk (each paper once); issued from <a href="{{url_for('s568_issue')}}">Stationery diya</a>.</p>
<div class=card id=s585switch><form method=post action="{{url_for('s585_many')}}" style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin:0"><input type=hidden name=on value="{{'0' if many else '1'}}">
<b style="font-size:14px">Many items on one screen</b> <span class=muted>— Stationery diya for the staff: every item on one screen, one Save. OFF = the one-item screen.</span>
<button style="padding:4px 10px;border-radius:12px;font-size:12px;background:{{'#2b6e4f' if many else '#8a97a5'}}" title="tap to switch {{'off' if many else 'on'}}">{{'ON' if many else 'OFF'}}</button></form></div>
{{flow_top}}
<div class="card s674" id=s674stockhead><b>3 · Clinic stock — the stock book</b> <span class=muted>— received · issued · in stock · counts · the item list, as before.</span></div>
<div class=card id=s568mixed><b>Mixed challans this month: {{inv.mixed}}</b> <span class=muted>— clinic and lab items on one paper; raise it with the supplier.</span></div>
<div class=card style="overflow:auto"><table id=s568inv><tr><th>Item</th><th>In stock</th><th>Received this month</th><th>Issued this month ({% for k, w in places %}{{w}}{{' · ' if not loop.last}}{% endfor %})</th><th>Last rate paid</th><th>Agreed rate</th><th>Low at</th></tr>
{% for r in inv.rows if r.active %}<tr data-item="{{r.id}}"><td><b>{{r.name}}</b> <span class=muted>({{r.unit}})</span>{% if r.is_low %} <span class="badge amber" id=s568low{{r.id}}>low stock</span>{% endif %}{% if r.over %} <span class="badge amber">issued above stock</span>{% endif %}{% if r.pack %} <span class="badge amber" id=s624pack{{r.id}} title="a line of {{r.pack|join(', ')}} may be in single pieces, not {{r.unit}}">check the quantity ({{r.pack|join(', ')}})</span>{% endif %}</td>
<td class=s568stock>{{q(r.stock)}}</td><td>{{q(r.recv)}}</td><td>{% for k, w in places %}{{q(r.by_place[k])}}{{' · ' if not loop.last}}{% endfor %}</td>
<td>{{rs(r.last_rate) if r.last_rate is not none else '—'}}{% if r.last_stamp %} <span class=muted>({{r.last_stamp}})</span>{% endif %}</td><td>{{rs(r.rate) if r.rate is not none else '—'}}</td><td>{{q(r.low) if r.low is not none else '—'}}</td></tr>{% endfor %}
{% if not active_n %}<tr><td colspan=7 class=muted>No item on the list yet — add one below, or “Add to the list” from a challan line on the sorting desk.</td></tr>{% endif %}</table></div>
<div class=card><b>Count</b> <span class=muted>— type what is on the shelf for any items (leave the rest empty). The first count of an item is its opening stock; a later count records any difference as “not accounted for” and sets the stock to the count.</span>
<form method=post action="{{url_for('s568_count')}}" style="margin-top:8px"><input type=hidden name=back value=stock>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px 14px">{% for r in inv.rows if r.active %}<label style="margin:0">{{r.name}} <span class=muted>({{r.unit}})</span><input name="c{{r.id}}" inputmode=decimal style="max-width:120px"></label>{% endfor %}</div>
<button class="btn small" style="margin-top:8px">Save the count</button></form></div>
{% macro s585row(x) %}<tr data-move="{{x.id}}"{% if x.voided %} class=s585v{% endif %}><td class=s>{{'no date' if x.hist else dmy(x.day)}}</td><td class=s>{{x.item}}</td><td class=s>{{q(x.qty)}} {{x.unit}}</td><td class=s>{{x.place}}</td><td class="s muted">{{x.who}}</td>
<td>{% if x.over %}<span class="badge amber">above stock ({{q(x.before)}} then)</span> {% endif %}{% if x.hist %}<span class=muted>from Shavez's sheet</span> {% endif %}{% if x.pre and not x.voided and not x.hist %}<span class=muted>before the latest count</span>{% endif %}</td>
<td>{% if x.voided %}<span class=muted>voided{{' by ' ~ x.vby if x.vby}} {{x.vat}}</span>{% else %}<form method=post action="{{url_for('s585_void')}}" style="margin:0" onsubmit="return confirm('Void this issue? It stays on the page, struck through.')"><input type=hidden name=id value="{{x.id}}"><button class="btn small danger">Void</button></form>{% endif %}</td></tr>{% endmacro %}
<style>.s585v td.s{text-decoration:line-through;color:#8a97a5}</style>
<div class=card id=s585issues><b>This month's issues</b> <span class=muted>— Void corrects a wrong line: it stays here, struck through, and leaves the stock. Voiding an issue made before the latest count does not change the stock — the count stands.</span>
{% if inv.issues %}<div style="overflow:auto"><table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th><th></th></tr>
{% for x in inv.issues %}{{s585row(x)}}{% endfor %}</table></div>{% else %}<p class=muted>None yet.</p>{% endif %}</div>
<details class=card id=s585older><summary><b>Show all issues</b> <span class=muted>— the earlier months ({{inv.older|length}})</span></summary>
{% if inv.older %}<div style="overflow:auto"><table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th><th></th></tr>
{% for x in inv.older %}{{s585row(x)}}{% endfor %}</table></div>{% else %}<p class=muted>None.</p>{% endif %}</details>
{% if inv.history %}<details class=card id=s585hist><summary><b>Earlier issues — from Shavez's sheet (no date)</b> <span class=muted>({{inv.history|length}}) — issued before the opening count: not in this month's figures, and they do not change the stock</span></summary>
<div style="overflow:auto"><table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th><th></th></tr>
{% for x in inv.history %}{{s585row(x)}}{% endfor %}</table></div></details>{% endif %}
<div class=card><b>Counts this month</b>{% if inv.counts %}<table><tr><th>Day</th><th>Item</th><th>Counted</th><th></th><th>By</th></tr>
{% for x in inv.counts %}<tr><td>{{dmy(x.day)}}</td><td>{{x.item}}</td><td>{{q(x.counted)}} {{x.unit}}</td><td>{% if x.opening %}opening stock{% elif x.diff and (x.diff|abs) > 0.0001 %}not accounted for: {{q(x.diff)}} {{x.unit}}{% else %}matches the stock{% endif %}</td><td class=muted>{{x.who}}</td></tr>{% endfor %}</table>{% else %}<p class=muted>None this month.</p>{% endif %}</div>
<div class=card><b>The papers that fed the stock this month</b>{% if inv.fed %}<ul style="margin:6px 0 0">{% for f in inv.fed %}<li><a href="{{href(f.bid)}}">{{f.stamp}}</a> · {{f.vendor or 'supplier not read'}} · {{f.kind}} · {{f.n}} line{{'' if f.n==1 else 's'}}</li>{% endfor %}</ul>{% else %}<p class=muted>None this month.</p>{% endif %}</div>
{{flow_bottom}}
<div class=card id=s568items><b>The item list</b> <span class=muted>— edited in place; an item with moves is retired, never deleted.</span>
<form method=post action="{{url_for('s568_item')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:flex-end;margin:8px 0"><input type=hidden name=do value=add>
<label style="margin:0">Name<input name=name required style="max-width:220px"></label><label style="margin:0">Unit<input name=unit list=s568units value=pack style="max-width:100px"></label>
<label style="margin:0">Agreed rate ₹<input name=rate inputmode=decimal style="max-width:100px"></label><label style="margin:0">Low at<input name=low inputmode=decimal style="max-width:80px"></label><button class="btn small">+ Add item</button></form>
<datalist id=s568units>{% for u in units %}<option value="{{u}}">{% endfor %}</datalist>
{% for r in inv.rows %}<form method=post action="{{url_for('s568_item')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0;{{'opacity:.6' if not r.active}}"><input type=hidden name=id value="{{r.id}}">
<input name=name value="{{r.name}}" style="max-width:220px"><input name=unit value="{{r.unit}}" list=s568units style="max-width:100px"><input name=rate value="{{plain(r.rate)}}" inputmode=decimal style="max-width:100px" placeholder="rate"><input name=low value="{{plain(r.low)}}" inputmode=decimal style="max-width:80px" placeholder="low at">
<button class="btn small" name=do value=edit>Save</button>{% if r.active %}{% if r.used %}<button class="btn small" name=do value=retire>Retire</button>{% else %}<button class="btn small" name=do value=delete>Delete</button>{% endif %}{% else %}<span class=muted>retired</span> <button class="btn small" name=do value=restore>Bring back</button>{% endif %}</form>{% endfor %}</div>"""

# S568 FIX1 (K1 CORRECTION 2): the owner's mock-up, artboard Issue.dc.html (390 x 844, a phone), line by line -- the title
# "Stationery diya"; "Kya diya" (the item list), "Kitne" (quantity), "Kisko"; four large place buttons in a 2 x 2 grid (one tap
# picks; at least 52 px tall); one Save; after Save the flash "Ho gaya — <item> <qty> <unit>, <place> ko. Stock mein ab <N>."
# Phone width first: the form is one column up to 420 px wide. The Ginti card (R1 C9) stays as the one addition.
DIYA_TPL = """<style>
#s568diya{max-width:420px}
#s568diya label.s568lb{font-size:16px;font-weight:600;color:#2c4258;margin:14px 0 6px}
#s568diya select,#s568diya input[name=qty]{font-size:17px;min-height:48px;max-width:none;width:100%}
#s568diya .s568grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:0 0 6px}
#s568diya .s568place{position:relative;display:block;margin:0}
#s568diya .s568place input{position:absolute;opacity:0;width:1px;height:1px;margin:0;padding:0}
#s568diya .s568place span{display:flex;align-items:center;justify-content:center;min-height:56px;box-sizing:border-box;border:1px solid #c9d2dc;border-radius:12px;background:#fff;font-size:18px;font-weight:600;color:#2c4258;cursor:pointer;user-select:none}
#s568diya .s568place input:checked+span{border:2px solid #2b5d8a;background:#e3edf7;color:#1f3864}
#s568diya .s568place input:focus-visible+span{outline:2px solid #9db8d4;outline-offset:2px}
#s568diya .s568save{display:block;width:100%;min-height:52px;margin-top:16px;font-size:18px;font-weight:700;border-radius:12px}
</style>
<h2 style="margin-bottom:4px">Stationery diya</h2>
{% if not ok %}<div class=card><p style="font-size:17px">{{off}}</p></div>{% else %}
<div class=card id=s568diya><form method=post action="{{url_for('s568_issue')}}">
<label class=s568lb for=s568item style="margin-top:0">Kya diya</label><select name=item id=s568item><option value="">— chuno —</option>{% for i in items %}<option value="{{i.id}}">{{i.name}} ({{i.unit}})</option>{% endfor %}</select>
<label class=s568lb for=s568qty>Kitne</label><input name=qty id=s568qty inputmode=decimal autocomplete=off>
<label class=s568lb>Kisko</label><div class=s568grid role=radiogroup aria-label=Kisko>{% for k, w in places %}<label class=s568place><input type=radio name=place value="{{k}}"><span>{{w}}</span></label>{% endfor %}</div>
{% if one %}<input type=hidden name=one value=1>{% endif %}<button class="btn s568save">Save</button></form></div>
<div class=card><b>Ginti</b> <span class=muted>— shelf par kitna hai, likho (baaki khaali chhodo).</span>
<form method=post action="{{url_for('s568_count')}}" style="margin-top:8px"><input type=hidden name=back value=diya>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:6px 14px">{% for i in items %}<label style="margin:0">{{i.name}} <span class=muted>({{i.unit}})</span><input name="c{{i.id}}" inputmode=decimal style="max-width:110px"></label>{% endfor %}</div>
<button class="btn small" style="margin-top:8px">Ginti save karo</button></form></div>{% endif %}"""


# S585: the many-items screen, built to the owner's mock-up (claude_code_briefs/S585_MOCKUP_Main.dc.html, 390 px wide): the title, the
# line "Ek baar mein kai cheezein — sirf jo diya, uska number likho"; "1 · Kisko diya?" -- five buttons in a three-column grid, at least
# 48 px tall; "2 · Kya aur kitna diya?" -- one row per active item: its name, "shelf pe <stock> <unit>", a 44 px "−", the number (a box
# that can be typed in), a 44 px "+"; a row with a number is green; the line of what will be saved; ONE "Save karo (N)" -- grey until a
# place and a number are chosen, and disabled on the first tap (R1 C7). The Ginti card below is DIYA_TPL's own, cut from it.
GINTI_TPL = DIYA_TPL[DIYA_TPL.index("<div class=card><b>Ginti</b>"):DIYA_TPL.rindex("{% endif %}")]
MANY_JS = r"""<script>(function(){var f=document.getElementById('s585form');if(!f)return;
var sv=document.getElementById('s585save'),sm=document.getElementById('s585sum');
function val(i){var s=String(i.value||'').replace(/,/g,'').trim();if(!s)return 0;var v=Number(s);return (isFinite(v)&&v>=0)?v:NaN;}
function upd(){var pl=f.querySelector('input[name=place]:checked'),ch=[],bad=[];
Array.prototype.forEach.call(f.querySelectorAll('.s585row'),function(r){var i=r.querySelector('input'),v=val(i);
if(isNaN(v)){bad.push(i.value);r.classList.remove('on');return;}r.classList.toggle('on',v>0);if(v>0)ch.push(r.getAttribute('data-name')+' '+v);});
var pw=pl?pl.nextElementSibling.textContent:'';
if(bad.length){sm.textContent='“'+bad[0]+'” number nahi hai — theek karo.';}
else if(!ch.length){sm.textContent=pw?('Abhi kuch nahi chuna → '+pw):'Abhi kuch nahi chuna.';}
else{sm.textContent=ch.length+(ch.length==1?' cheez':' cheezein')+' · '+ch.join(', ')+(pw?' → '+pw:' — Kisko diya chuno');}
var ready=!!pl&&ch.length>0&&!bad.length;sv.disabled=!ready;sv.textContent=ready?('Save karo ('+ch.length+')'):'Save karo';}
f.addEventListener('click',function(e){var b=e.target.closest?e.target.closest('button'):null;if(!b||b.type!=='button')return;
var i=b.parentNode.querySelector('input'),v=val(i);if(isNaN(v))v=0;v=v+(b.classList.contains('s585plus')?1:-1);i.value=v>0?String(v):'';upd();});
f.addEventListener('input',upd);f.addEventListener('change',upd);
f.addEventListener('submit',function(e){if(sv.disabled||f.getAttribute('data-sent')){e.preventDefault();return;}
f.setAttribute('data-sent','1');sv.disabled=true;sv.textContent='Save ho raha hai…';});
window.addEventListener('pageshow',function(){f.removeAttribute('data-sent');upd();});upd();})();</script>"""
MANY_TPL = """<style>
#s585many{max-width:560px;box-sizing:border-box}
#s585many .s585h{font-size:16px;font-weight:700;color:#2c4258;margin:14px 0 8px}
#s585many .s585grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}
#s585many .s585place{position:relative;display:block;margin:0}
#s585many .s585place input{position:absolute;opacity:0;width:1px;height:1px;margin:0;padding:0}
#s585many .s585place span{display:flex;align-items:center;justify-content:center;min-height:48px;box-sizing:border-box;padding:0 4px;border:2px solid #c3ced9;border-radius:12px;background:#fff;font-size:16px;font-weight:600;color:#1d2733;text-align:center;cursor:pointer;user-select:none}
#s585many .s585place input:checked+span{border-color:#1f4e79;background:#1f4e79;color:#fff}
#s585many .s585place input:focus-visible+span{outline:2px solid #9db8d4;outline-offset:2px}
#s585many .s585row{display:flex;align-items:center;gap:10px;padding:10px 12px;margin:0 0 8px;border-radius:12px;background:#fff;border:1px solid #d5dde5}
#s585many .s585row.on{background:#eaf4ec;border-color:#7fb38e}
#s585many .s585nm{flex:1 1 auto;min-width:0}
#s585many .s585nm b{display:block;font-size:15px;font-weight:600;color:#1d2733;overflow-wrap:anywhere}
#s585many .s585nm span{display:block;font-size:13px;color:#4a5866}
#s585many .s585ctl{display:flex;align-items:center;gap:6px;flex:0 0 auto}
#s585many .s585ctl button{width:44px;height:44px;min-height:44px;padding:0;border-radius:10px;font-size:22px;line-height:1}
#s585many .s585minus{background:#fff;color:#1d2733;border:1px solid #b7c3cf}
#s585many .s585plus{background:#e8f0f8;color:#1f4e79;border:1px solid #1f4e79}
#s585many .s585ctl input{width:52px;max-width:52px;min-height:44px;margin:0;padding:4px;text-align:center;font-size:18px;font-weight:700}
#s585many .s585foot{position:sticky;bottom:0;background:#fff;border-top:1px solid #d5dde5;padding:12px 0 4px;margin-top:6px}
#s585many .s585sum{font-size:14px;color:#33414f;margin:0 0 8px}
#s585many .s585save{display:block;width:100%;min-height:52px;font-size:17px;font-weight:700;border-radius:12px;background:#1e6b35}
#s585many .s585save:disabled{background:#9aa6b2;cursor:default}
</style>
<h2 style="margin-bottom:4px">Stationery diya</h2>
{% if not ok %}<div class=card><p style="font-size:17px">{{off}}</p></div>{% else %}
<p class=muted style="margin-top:0;font-size:14px">Ek baar mein kai cheezein — sirf jo diya, uska number likho.</p>
<div class=card id=s585many><form method=post action="{{url_for('s585_issue_many')}}" id=s585form>
<div class=s585h style="margin-top:0">1 · Kisko diya?</div>
<div class=s585grid role=radiogroup aria-label="Kisko diya">{% for k, w in places %}<label class=s585place><input type=radio name=place value="{{k}}"><span>{{w}}</span></label>{% endfor %}</div>
<div class=s585h>2 · Kya aur kitna diya?</div>
{% for i in rows %}<div class=s585row data-item="{{i.id}}" data-name="{{i.name}}"><div class=s585nm><b>{{i.name}}</b><span>shelf pe {{q(i.stock)}} {{i.unit}}</span></div><div class=s585ctl><button type=button class=s585minus aria-label="Ek kam">−</button><input name="q{{i.id}}" inputmode=decimal autocomplete=off placeholder=0 aria-label="{{i.name}}: kitna"><button type=button class=s585plus aria-label="Ek zyada">+</button></div></div>
{% endfor %}{% if not rows %}<p class=muted>List mein abhi koi cheez nahi hai.</p>{% endif %}
<div class=s585foot><p class=s585sum id=s585sum>Abhi kuch nahi chuna.</p><button class="btn s585save" id=s585save disabled>Save karo</button></div></form>
<p class=muted style="margin:10px 0 0">Ek-ek cheez dena ho to: <a href="{{url_for('s568_issue', one=1)}}">purana screen</a></p></div>
""" + MANY_JS + "\n" + GINTI_TPL + "{% endif %}"


def _href(bid):
    try:
        return AR._s559_paper_href(bid)
    except Exception:                                                # noqa: BLE001
        return url_for("bill_view", bid=bid)


def _dmy(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10]).strftime("%d-%m-%Y")
    except Exception:                                                # noqa: BLE001
        return s or ""


def stock_page():
    db = AR.get_db()
    ym = _ym()
    inv = inventory(db, ym)
    ctx = flow_ctx(db, ym)                                           # S674
    return AR.page(STOCK_TPL, inv=inv, label=AR._month_label(ym), places=PLACES, units=UNITS, q=lambda x: _plain(x) if x is not None else "—",
                   rs=rs, plain=_plain, href=_href, dmy=_dmy, active_n=len([r for r in inv["rows"] if r["active"]]), many=many_on(db),
                   flow_top=flow_top(db, ym, ctx), flow_bottom=flow_bottom(db, ym, ctx),
                   flow=AR._flow("Stationery", url_for("s551_desk") if "s551_desk" in AR.app.view_functions else url_for("bills_list")))


def item_post():
    db = AR.get_db()
    f = request.form
    do = (f.get("do") or "").strip()
    try:
        if do == "add":
            iid, made = add_item(db, f.get("name"), f.get("unit"), _num(f.get("rate")), _num(f.get("low")))
            db.commit()
            flash(("Added to the list: %s." if made else "%s is already on the list.") % re.sub(r"\s+", " ", f.get("name") or "").strip()[:120])
            return redirect(url_for("s568_stock") + "#s568items")
        iid = int(f.get("id") or 0)
        it = next((i for i in item_rows(db) if i["id"] == iid), None)
        if it is None:
            flash("That item is not on the list.")
            return redirect(url_for("s568_stock") + "#s568items")
        if do == "edit":
            name = re.sub(r"\s+", " ", f.get("name") or "").strip()[:120]
            if not name:
                raise ValueError("Type the item's name.")
            if any(norm(i["name"]) == norm(name) and i["id"] != iid and i["active"] for i in item_rows(db)):
                raise ValueError("%s is already on the list." % name)
            new = {"name": name, "unit": re.sub(r"\s+", " ", f.get("unit") or "").strip()[:30] or "piece",
                   "rate": _num(f.get("rate")), "low_level": _num(f.get("low"))}
            ch = {k: v for k, v in new.items() if v != it[k]}
            if ch:
                db.execute("UPDATE stationery_item SET %s WHERE id=?" % ",".join("%s=?" % k for k in ch), tuple(ch.values()) + (iid,))
                _audit(db, "stationery_item_changed", {"id": iid, "from": {k: it[k] for k in ch}, "to": ch})
            msg = "Saved: %s." % name if ch else "Unchanged: %s." % name
        elif do == "retire":
            db.execute("UPDATE stationery_item SET active=0 WHERE id=?", (iid,))
            _audit(db, "stationery_item_retired", {"id": iid})
            msg = "Retired: %s (its moves stay)." % it["name"]
        elif do == "restore":
            db.execute("UPDATE stationery_item SET active=1 WHERE id=?", (iid,))
            _audit(db, "stationery_item_restored", {"id": iid})
            msg = "Back on the list: %s." % it["name"]
        elif do == "delete":
            if item_used(db, iid):
                raise ValueError("%s has moves — it is retired, never deleted." % it["name"])
            db.execute("DELETE FROM stationery_item WHERE id=?", (iid,))
            _audit(db, "stationery_item_deleted", {"id": iid, "name": it["name"]})
            msg = "Deleted: %s (it had no moves)." % it["name"]
        else:
            abort(400)
        db.commit()
    except ValueError as e:
        db.rollback()
        msg = str(e)
    flash(msg)
    return redirect(url_for("s568_stock") + "#s568items")


def done_line(it, q, place, after):
    """S568 FIX1 (the mock-up's line): 'Ho gaya — A4 sheets 2 pack, Lab ko. Stock mein ab 10.'"""
    return "Ho gaya — %s %s %s, %s ko. Stock mein ab %s." % (it["name"], _plain(q), it["unit"] or "", PLACE_WORD.get(place, place), _plain(after))


def issue_page():
    db = AR.get_db()
    ok = may_issue(db)
    if request.method == "POST":
        if not ok:
            return OFF_LINE, 403
        try:
            iid = int(request.form.get("item") or 0)
        except ValueError:
            iid = 0
        try:
            it, q, before = issue(db, iid, request.form.get("qty"), (request.form.get("place") or "").strip())
            db.commit()
            flash(done_line(it, q, (request.form.get("place") or "").strip(), stock_of(db, it["id"])))      # S568 FIX1
        except ValueError as e:
            db.rollback()
            flash(str(e) + " Kuch save nahi hua.")
        return redirect(url_for("s568_issue", one=1) if (request.form.get("one") == "1" and many_on(db)) else url_for("s568_issue"))
    many = many_on(db)                                               # S585: absent = OFF
    one = many and request.args.get("one") == "1"
    flow = AR._flow("Stationery diya", url_for("s568_stock") if _role() == "owner" else url_for("dashboard"))
    if many and not one:
        return many_page(db, ok, flow)
    return AR.page(DIYA_TPL, ok=ok, off=OFF_LINE, items=item_rows(db, active_only=True), places=ONE_PLACES, one=one, flow=flow)


def many_page(db, ok, flow):
    """S585: the many-items screen -- every active item with its shelf stock (one stock_book read)."""
    items = item_rows(db, active_only=True)
    book = stock_book(db) if ok else {}
    rows = [{"id": i["id"], "name": i["name"], "unit": i["unit"], "stock": book.get(i["id"], {"stock": 0.0})["stock"]} for i in items]
    return AR.page(MANY_TPL, ok=ok, off=OFF_LINE, rows=rows, items=items, places=PLACES, q=lambda x: _plain(x) if x is not None else "—",
                   flow=flow)


def count_post():
    db = AR.get_db()
    back = "s568_issue" if (request.form.get("back") == "diya" or _role() != "owner") else "s568_stock"
    if not may_issue(db):
        return OFF_LINE, 403
    got = {}
    bad = []
    for k, v in request.form.items():
        if k.startswith("c") and k[1:].isdigit() and str(v).strip():
            n = _num(v)
            if n is None or n < 0:
                bad.append(v)
            else:
                got[int(k[1:])] = n
    if bad:
        flash(("The count “%s” is not a number. Nothing was saved." if back == "s568_stock" else "Ginti “%s” number nahi hai. Kuch save nahi hua.") % str(bad[0])[:20])
        return redirect(url_for(back))
    res = count(db, got)
    db.commit()
    if back == "s568_stock":
        flash("Count saved for %d item%s." % (len(res), "" if len(res) == 1 else "s") if res else "Nothing typed — nothing saved.")
    else:
        flash("Ginti save ho gayi (%d item)." % len(res) if res else "Kuch nahi likha — kuch save nahi hua.")
    return redirect(url_for(back))


def done_many(done, place):
    """S585: 'Save ho gaya ✓ — Register 192 pages 2 piece, Small notebook (copy) 1 piece → Lab'."""
    return "Save ho gaya ✓ — %s → %s" % (", ".join("%s %s %s" % (it["name"], _plain(q), it["unit"] or "") for it, q in done).replace("  ", " "),
                                        PLACE_WORD.get(place, place))


def many_post():
    """S585 (R1 C7): the many-items screen's ONE Save -- one issue per item with a number, through issue(), then ONE commit (all or
    none). Refused while stationery.many is OFF; a place and at least one number are needed (the server checks, not the grey button)."""
    db = AR.get_db()
    if not may_issue(db):
        return OFF_LINE, 403
    back = url_for("s568_issue")
    if not many_on(db):
        flash("Yeh screen abhi band hai. Kuch save nahi hua.")
        return redirect(back)
    place = (request.form.get("place") or "").strip()
    act = item_rows(db, active_only=True)
    got, bad = {}, []
    for k, v in request.form.items():
        if k.startswith("q") and k[1:].isdigit() and str(v).strip():
            n = _num(v)
            if n is None or n < 0:
                bad.append(v)
            elif n > 0:
                got[int(k[1:])] = n
    if bad:
        flash("“%s” number nahi hai. Kuch save nahi hua." % str(bad[0])[:20])
        return redirect(back)
    if place not in PLACE_WORD:
        flash("Kisko diya — chuno. Kuch save nahi hua.")
        return redirect(back)
    if not got:
        flash("Kuch nahi chuna — kuch save nahi hua.")
        return redirect(back)
    order = [i["id"] for i in act] + sorted(k for k in got if k not in {i["id"] for i in act})
    done = []
    try:
        for iid in order:
            if iid in got:
                it, q, _before = issue(db, iid, got[iid], place)
                done.append((it, q))
        db.commit()
    except (ValueError, sqlite3.Error) as e:
        db.rollback()
        flash("%s Kuch save nahi hua." % (str(e) if isinstance(e, ValueError) else "Database ne mana kiya."))
        return redirect(back)
    flash(done_many(done, place))
    return redirect(back)


def many_switch():
    """S585 (R1 C1): the owner's ON / OFF for the many-items screen -- the shape of sorting_desk.switch()."""
    on = request.form.get("on") or ""
    if on not in ("0", "1"):
        abort(400)
    db = AR.get_db()
    old = _setting(db, MANY_SWITCH, "off")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (MANY_SWITCH, "on" if on == "1" else "off"))
    _audit(db, "stationery_many_switch", {"from": old, "to": "on" if on == "1" else "off"})
    db.commit()
    flash("Many items on one screen: %s. Stationery diya now shows %s." % (("ON", "every item on one screen") if on == "1" else ("OFF", "the one-item screen")))
    return redirect(url_for("s568_stock"))


def void_post():
    """S585 s3.3: the owner voids one issue line -- kept (voided_at / voided_by), struck through, out of the stock. A line made before
    the item's latest count changes nothing: the count stands."""
    db = AR.get_db()
    back = url_for("s568_stock") + "#s585issues"
    try:
        mid = int(request.form.get("id") or 0)
    except ValueError:
        mid = 0
    r = db.execute("SELECT * FROM stationery_move WHERE id=?", (mid,)).fetchone()
    if r is None:
        flash("That issue is not on the list — nothing changed.")
        return redirect(back)
    if r["voided_at"]:
        flash("That issue was already voided — nothing changed.")
        return redirect(back)
    it = next((i for i in item_rows(db) if i["id"] == r["item_id"]), None) or {"name": "?", "unit": ""}
    lc = db.execute("SELECT MAX(ts) FROM stationery_count WHERE item_id=?", (r["item_id"],)).fetchone()[0]
    pre = lc is not None and r["ts"] <= lc
    db.execute("UPDATE stationery_move SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (_now(), _who(), mid))
    _audit(db, "stationery_issue_voided", {"id": mid, "item": r["item_id"], "qty": r["qty"], "place": r["place"], "day": r["day"],
                                           "before_count": pre, "sheet": (r["by_whom"] or "") == HISTORY_BY})
    db.commit()
    msg = "Voided: %s %s %s to %s." % (it["name"], _plain(r["qty"]), it["unit"] or "", PLACE_WORD.get(r["place"], r["place"]))
    if pre:
        msg += " It was made before the latest count, so the stock does not change — the count stands."
    else:
        msg += " In stock now: %s %s." % (_plain(stock_of(db, r["item_id"])), it["unit"] or "")
    flash(msg.replace("  ", " "))
    return redirect(back)


def history_step(db_path, plan=None, who=HISTORY_BY, key=HISTORY_KEY, shift=-1.0, out=print):
    """S585 s3.4 (R1 C4): the installer's data step -- Shavez's sheet, once. ONE transaction (BEGIN IMMEDIATE) with its done-key,
    checked first; items by their EXACT names among the ACTIVE items; each line 1 s before its item's OPENING count (day = that count's
    day), stock_before NULL, by_whom 'history (Shavez sheet)'; an absent item, or one with no opening count, is skipped with one line;
    the stock figures are read before and after inside the transaction -- any difference rolls everything back. Returns 0 / 1."""
    plan = HISTORY if plan is None else plan
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.isolation_level = None
    try:
        con.execute("BEGIN IMMEDIATE")
        if _setting(con, key, None) is not None:
            out("history: already done (%s is set) -- nothing written" % key)
            con.execute("ROLLBACK")
            return 0
        items = item_rows(con, active_only=True)
        allit = {i["id"]: i for i in item_rows(con)}
        before = stock_book(con)
        at = _now()
        wrote = 0
        for name, qty, place, what in plan:
            it = next((i for i in items if i["name"] == name), None)
            if it is None:
                out("history: skipped -- no active item named '%s' (%s to %s, %s)" % (name, _plain(qty), PLACE_WORD.get(place, place), what))
                continue
            oc = con.execute("SELECT * FROM stationery_count WHERE item_id=? AND opening=1 ORDER BY ts, id LIMIT 1", (it["id"],)).fetchone()
            if oc is None:
                out("history: skipped -- '%s' has no opening count yet (%s to %s, %s)" % (name, _plain(qty), PLACE_WORD.get(place, place), what))
                continue
            if con.execute("SELECT 1 FROM stationery_move WHERE item_id=? AND place=? AND qty=? AND by_whom=? LIMIT 1",
                           (it["id"], place, float(qty), who)).fetchone():
                out("history: already there -- %s %s to %s" % (name, _plain(qty), PLACE_WORD.get(place, place)))
                continue
            con.execute("INSERT INTO stationery_move(item_id, qty, place, day, ts, stock_before, by_whom, at) VALUES(?,?,?,?,?,NULL,?,?)",
                        (it["id"], float(qty), place, oc["day"], float(oc["ts"]) + shift, who, at))
            wrote += 1
            out("history: wrote %s %s %s -> %s (%s); day %s, 1 s before its opening count" % (name, _plain(qty), it["unit"] or "",
                                                                                         PLACE_WORD.get(place, place), what, oc["day"]))
        after = stock_book(con)
        moved = sorted(i for i in set(before) | set(after)
                       if abs(before.get(i, {"stock": 0.0})["stock"] - after.get(i, {"stock": 0.0})["stock"]) > 1e-9)
        for i in sorted(before, key=lambda k: (allit.get(k) or {}).get("name", "").lower()):
            if before[i].get("counted"):
                out("stock: %s -- before %s, after %s" % ((allit.get(i) or {}).get("name", "?"), _plain(before[i]["stock"]),
                                                          _plain(after.get(i, {"stock": 0.0})["stock"])))
        if moved:
            con.execute("ROLLBACK")
            out("history: REFUSED -- a stock figure changed (%s); rolled back, nothing written" % ", ".join((allit.get(i) or {}).get("name", "?") for i in moved))
            return 1
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, "%d rows %s" % (wrote, at)))
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                        (at, who, "stationery_history_s585", json.dumps({"rows": wrote}, ensure_ascii=False)))
        except sqlite3.Error:
            pass
        con.execute("COMMIT")
        out("history: %d row(s) written; %s set; the stock figures before = after (%d counted items)" % (wrote, key, len([i for i in before if before[i].get("counted")])))
        return 0
    except Exception:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


def history_void(db_path, who="undo S585", out=print):
    """S585: the data step's undo -- Shavez's lines VOIDED (marked, never deleted); the key stays, so a re-install writes nothing."""
    con = sqlite3.connect(db_path, timeout=30)
    try:
        n = con.execute("UPDATE stationery_move SET voided_at=?, voided_by=? WHERE by_whom=? AND voided_at=''", (_now(), who, HISTORY_BY)).rowcount
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)", (_now(), who, "stationery_history_voided", json.dumps({"rows": n})))
        except sqlite3.Error:
            pass
        con.commit()
    finally:
        con.close()
    out("history: %d line(s) of Shavez's sheet voided (kept, struck through)" % n)
    return 0


def menu_items(role):
    """For the scan app's one menu (asset_register._s559_items): the owner's Stationery page; a manager's Stationery diya
    while the switch is ON. Nothing for anyone else."""
    try:
        if role == "owner":
            return [("s568_stock", "Stationery", url_for("s568_stock"))]
        if role == "manager":
            out = menu_items_s674(role, AR.get_db())                     # S674
            if issue_on(AR.get_db()):
                out.append(("s568_issue", "Stationery diya", url_for("s568_issue")))
            return out
    except Exception:                                                # noqa: BLE001
        pass
    return []


# ---------------------------------------------------------------------------------------------- S674: the Variety flow (D797)
# The owner, 28-Oct-2026, on the mock-up S355_STATIONERY_FLOW_MOCKUP (his 'build', 09:31 IST): Variety supplies stationery to
# the clinic AND NK Pathology on jumbled challans, billed about once a year. So:
#   1  every challan of a listed supplier lands on his Stationery page (the desk is skipped), and is sorted there LINE BY LINE:
#      the product typed, picked from the list, or added in the same box; each line FOR the clinic or FOR NK;
#   2  a clinic line feeds the clinic stock book as before; an NK line goes to the NK ledger on the same page -- never the
#      clinic's stock (stationery_line.side);
#   3  the Variety account: every line, with its state -- unbilled / on statement / billed / paid; a line is paid once, ever;
#   4  a monthly statement made by one tap, challan-wise in the supplier's own challan numbers, each 'bill to: Clinic' or
#      'bill to: NK Pathology', a mixed challan naming which products go where; copied, sent on WhatsApp or printed; the
#      supplier bills against it; their bill or estimate is scanned, joined to the statement, the rates typed on; then paid.
# Shavez (a manager) sorts on /stationery/sort while the desk switch (desk.on) is ON -- Roman Hinglish, no rate. The rest is
# the owner's. NOT here: the NK share into NK's accounts (the finance app), a lab stock book (the NK Pathology project).
S674 = "S674"
SUPPLIERS_KEY = "stationery.suppliers"        # the supplier keys (clinic_papers._supplier_key) whose every paper lands here; '|' apart
FLOOR_KEY = "stationery.suppliers_from"       # the day the first supplier was listed: papers scanned from that day sort here, older ones stay as they are
SIDES = (("clinic", "Clinic"), ("nk", "NK Pathology"))
SIDE_WORD = dict(SIDES)
DDL_S674 = (
    "CREATE TABLE IF NOT EXISTS stationery_stmt(id INTEGER PRIMARY KEY, supplier TEXT NOT NULL DEFAULT '', ym TEXT NOT NULL, "
    "made_at TEXT NOT NULL, made_by TEXT, sent_at TEXT NOT NULL DEFAULT '', bill_id INTEGER, bill_created_at TEXT NOT NULL DEFAULT '', "
    "billed_at TEXT NOT NULL DEFAULT '', paid_at TEXT NOT NULL DEFAULT '', paid_ref TEXT NOT NULL DEFAULT '', text TEXT NOT NULL DEFAULT '', "
    "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
)
ADD_COLS_S674 = (("stationery_line", "side", "TEXT NOT NULL DEFAULT 'clinic'"), ("stationery_line", "stmt_id", "INTEGER"))


def ensure_s674(db):
    """Additive and idempotent, after S568's ensure: the statement table; two columns on a stationery_line made before them."""
    for d in DDL_S674:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    for t, c, spec in ADD_COLS_S674:
        have = {r[1] for r in db.execute("PRAGMA table_info(%s)" % t)}
        if have and c not in have:
            try:
                db.execute("ALTER TABLE %s ADD COLUMN %s %s" % (t, c, spec))
            except sqlite3.OperationalError as ex:
                if "duplicate column" not in str(ex).lower():
                    raise


def _skey(v):
    try:
        return _desk_mod()._key(v)
    except Exception:                                                # noqa: BLE001
        w = [x for x in re.sub(r"[^a-z0-9 ]", " ", (v or "").lower().replace("-", "").replace(".", "")).split()
             if x not in ("the", "ms", "m", "s", "pvt", "ltd", "p", "co", "and", "&")]
        return " ".join(w[:2])


def suppliers(db):
    """The listed suppliers' keys, in the order the owner added them."""
    return [k for k in (_setting(db, SUPPLIERS_KEY, "") or "").split("|") if k.strip()]


def is_listed(db, vendor):
    return bool(vendor) and _skey(vendor) in suppliers(db)


def _desk_mod():
    try:
        return AR._s559_desk_mod()
    except Exception:                                                # noqa: BLE001
        return None


def _reading_of(db, bid):
    sd = _desk_mod()
    if sd is None:
        return None
    try:
        return sd.reading(db, bid)
    except Exception:                                                # noqa: BLE001
        return None


def floor_day(db):
    return (_setting(db, FLOOR_KEY, "") or "").strip()[:10]


def listed_papers(db, keys=None, goods=False, since=None):
    """Every live paper of the listed suppliers: not a second scan, not set aside, not a page, never the pharmacy lane. goods=True:
    challans only (and a paper with no kind read) -- their bills and estimates are JOINED to a statement, never sorted. since: only
    papers scanned on or after that day. Newest first."""
    keys = suppliers(db) if keys is None else keys
    if not keys:
        return []
    out = []
    kinds = "('', 'challan')" if goods else "('', 'challan', 'estimate', 'bill')"
    try:
        rows = db.execute("SELECT * FROM bills b WHERE b.vendor IS NOT NULL AND b.vendor<>'' AND b.dup_of IS NULL AND b.status<>'rejected' "
                          "AND b.page_of IS NULL AND COALESCE(b.lane,'clinic')<>'pharmacy' AND COALESCE(b.doc_kind,'') IN " + kinds +
                          (" AND substr(COALESCE(b.created_at,''),1,10)>=?" if since else "") + " ORDER BY b.id DESC LIMIT 2000",
                          ((since,) if since else ())).fetchall()
    except sqlite3.Error:
        return []
    for b in rows:
        if _skey(b["vendor"]) in keys:
            out.append(b)
    return out


def is_goods(b):
    return (b["doc_kind"] or "") in ("", "challan")


LEFT_KEY = "stationery.left"                   # the papers the owner left as they are (ids, '|' apart): never offered to sort again


def left_ids(db):
    return {int(x) for x in (_setting(db, LEFT_KEY, "") or "").split("|") if x.strip().isdigit()}


def _live_lines(db, b):
    return saved_lines(db, b)


def to_sort(db):
    """The listed suppliers' papers with no sorted line yet, each with its read lines (name, qty, unit, rate) and a pre-match."""
    items = item_rows(db, active_only=True)
    out = []
    left = left_ids(db)
    if not floor_day(db):
        return []                                                    # no start day set: nothing is offered (never the whole history)
    for b in listed_papers(db, goods=True, since=floor_day(db)):
        if _live_lines(db, b) or b["id"] in left:
            continue
        if (b["subgroup"] or "") and (b["lane"] or "clinic") == "clinic" and (b["subgroup"] or "") != "stationery":
            continue                                                 # a person sorted it into another group on the desk: left as it is
        rd = _reading_of(db, b["id"])
        rl = read_lines(db, b, rd)
        lines = []
        for k, r in enumerate(rl, 1):
            sg = prematch(r["name"], items)
            lines.append({"no": k, "read": r["name"], "name": (sg["name"] if sg else r["name"]), "qty": _plain(r["qty"]) if r["qty"] is not None else "",
                          "unit": (sg["unit"] if sg else (r["unit"] or "")), "rate": r["rate"], "sug": bool(sg), "side": ""})
        if not lines:
            lines.append({"no": 1, "read": "", "name": "", "qty": "", "unit": "", "rate": None, "sug": False, "side": ""})
        out.append({"b": b, "stamp": _stamp_of(b), "lines": lines, "noread": not rl, "leave": True,
                    "lane_note": ("lane read as %s — check" % AR.LANE_WORD.get(b["lane"] or "clinic", b["lane"])) if (b["lane"] or "clinic") not in ("clinic",) else ""})
    return out


def _stamp_of(b):
    return (b["stamp_no"] or "").strip() or ("#%d" % b["id"])


def sorted_paper(db, b):
    """A sorted paper's lines for the editor (Change): its live lines with their side; refused for change when any is on a statement."""
    ls = _live_lines(db, b)
    lines = [{"no": l["line_no"], "read": "", "name": l["name"], "qty": _plain(l["qty"]) if l["qty"] is not None else "", "unit": l["unit"],
              "rate": l["rate"], "sug": False, "side": (l["side"] if "side" in l.keys() else "clinic"), "ns": bool(l["not_stock"])} for l in ls]
    return {"b": b, "stamp": _stamp_of(b), "lines": lines, "noread": False, "lane_note": "",
            "locked": any((l["stmt_id"] if "stmt_id" in l.keys() else None) for l in ls)}


def resolve_product(db, name, unit, who, paper):
    """The product box: the typed text is an item on the list (by name, normalised) -- else a new item, added now. Returns (id, made)."""
    name = re.sub(r"\s+", " ", str(name or "")).strip()[:120]
    if not name:
        return None, False
    k = norm(name)
    for it in item_rows(db):
        if norm(it["name"]) == k:
            if not it["active"]:
                db.execute("UPDATE stationery_item SET active=1 WHERE id=?", (it["id"],))
                _audit(db, "stationery_item_restored", {"id": it["id"], "via": "sort"})
                try:
                    flash("%s was retired — back on the list." % it["name"])
                except Exception:                                    # noqa: BLE001
                    pass
            return it["id"], False
    return add_item(db, name, unit or "piece", None, None, who, paper)


def sort_save(db, b, form, who=None, owner=True):
    """One Save of a listed paper's lines from the Stationery page (the owner) or Shavez's sort screen. Each line k: n<k> the product
    (typed, picked or new), q<k>, u<k>, f<k> = clinic / nk / '' (waits), r<k> the rate (the owner's screen only), ns<k> = not goods.
    Then the paper is PLACED by its lines: any clinic line -> the clinic lane, Stationery & packaging (mixed when NK lines too);
    only NK lines -> the NK Pathology lane. Audited as the desk audits (relane / subgroup / desk_saved), so the desk's list and
    the supplier-history rule see a person's sorting. No commit; refusals raise ValueError."""
    who = _who() if who is None else who
    W = (lambda en, hi: en) if owner else (lambda en, hi: hi)
    if not is_goods(b):
        raise ValueError(W("%s is their %s — it is joined to a statement, never sorted." % (_stamp_of(b), b["doc_kind"]),
                           "%s unka %s hai — yeh sort nahi hota." % (_stamp_of(b), b["doc_kind"])))
    lines, k, made = [], 0, 0
    for k in range(1, 61):
        if ("n%d" % k) not in form and ("f%d" % k) not in form:
            continue
        side = (form.get("f%d" % k) or "").strip()
        name = re.sub(r"\s+", " ", form.get("n%d" % k) or "").strip()[:120]
        if side not in ("clinic", "nk"):
            continue                                                 # a line left alone waits; never blocks the Save
        if form.get("ns%d" % k):
            lines.append({"no": k, "name": name, "qty": _num(form.get("q%d" % k)), "unit": (form.get("u%d" % k) or "").strip()[:30],
                          "rate": _num(form.get("r%d" % k)) if owner else None, "item": "ns", "side": side})
            continue
        if not name:
            raise ValueError(W("Line %d: type or pick the product." % k, "Line %d: saamaan likhein ya chunein." % k))
        q = _num(form.get("q%d" % k))
        if q is None or q <= 0:
            raise ValueError(W("Line %d (%s): type the quantity." % (k, name), "Line %d (%s): kitna, likhein." % (k, name)))
        unit = (form.get("u%d" % k) or "").strip()[:30]
        iid, mk = resolve_product(db, name, unit, who, b)
        made += 1 if mk else 0
        lines.append({"no": k, "name": name, "qty": q, "unit": unit, "rate": (_num(form.get("r%d" % k)) if owner else None), "item": str(iid), "side": side})
    if not lines:
        raise ValueError(W("Nothing chosen — pick Clinic or NK on at least one line.", "Kuch nahi chuna — kam se kam ek line par Clinic ya NK chunein."))
    sides = {l["side"] for l in lines if l["item"] != "ns"}
    _place(db, b, sides, who)                                        # the paper goes where its lines go, BEFORE the lines are counted
    b = db.execute("SELECT * FROM bills WHERE id=?", (b["id"],)).fetchone()
    msgs = save_lines(db, b, lines, who)
    pd = (b["bill_date"] or "").strip()[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", pd):                     # the line's day is the paper's own date when it has one (the account,
        db.execute("UPDATE stationery_line SET day=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''", (pd, b["id"], b["created_at"] or ""))    # the statement's month)
    return msgs + (["%d new product%s on the list." % (made, "" if made == 1 else "s")] if made else [])


def _place(db, b, sides, who):
    """The paper goes where its lines went. Clinic lines: the clinic lane, Stationery & packaging; mixed marked when NK lines too.
    Only NK lines: the NK Pathology lane. Audited like the desk; desk_saved so the desk's list lets it go."""
    bid = b["id"]
    status0 = b["status"]
    to_lane = "clinic" if "clinic" in sides else ("lab_purchase" if "nk" in sides else None)
    if to_lane is None:
        return
    frm = b["lane"] or "clinic"
    if to_lane != frm:
        kind, status = AR._lane_kind_status(to_lane)
        if to_lane != "clinic" and (b["doc_kind"] or "") == "challan":
            kind = "Challan"
        db.execute("UPDATE bills SET lane=?, kind=?, status=? WHERE id=?", (to_lane, kind, status, bid))
        AR._audit_bill(db, bid, "relane", {"from": frm, "to": to_lane, "status_from": status0, "via": "stationery"})
    if to_lane == "clinic":
        sg = b["subgroup"] or ""
        if sg and sg != "stationery" and frm == "clinic":
            raise ValueError("%s was sorted into another group on the desk (%s) — move it there first, or leave it." % (_stamp_of(b), sg))
        if sg != "stationery":
            db.execute("UPDATE bills SET subgroup='stationery' WHERE id=?", (bid,))
            AR._audit_bill(db, bid, "subgroup", {"from": sg, "to": "stationery", "status_from": status0, "via": "stationery"})
        if "mixed" in _cols(db):
            want = 1 if "nk" in sides else 0
            if int(b["mixed"] or 0) != want:
                db.execute("UPDATE bills SET mixed=? WHERE id=?", (want, bid))
                AR._audit_bill(db, bid, "mixed", {"from": int(b["mixed"] or 0), "to": want, "via": "stationery"})
    AR._audit_bill(db, bid, "desk_saved", {"via": "stationery", "sides": sorted(sides)})


# ---- the ledgers and the account
def _ym_of_line(l):
    return (l["day"] or "")[:7]


def account_rows(db, keys=None):
    """Every live line of the listed suppliers' papers (both sides), with its paper and its state."""
    keys = suppliers(db) if keys is None else keys
    if not keys:
        return []
    try:
        rows = [dict(r) for r in db.execute("SELECT l.*, b.stamp_no AS stamp, b.vendor AS vendor, b.doc_kind AS dk, b.bill_no AS bill_no, "
                                            "b.bill_date AS bill_date, b.lane AS lane, b.id AS bid " + _JOIN +
                                            " WHERE l.voided_at='' AND l.not_stock=0 AND b.dup_of IS NULL AND b.status<>'rejected' ORDER BY l.day, l.bill_id, l.line_no, l.id")]
    except sqlite3.Error:
        return []
    stmts = {s["id"]: s for s in stmt_rows(db)}
    out = []
    for l in rows:
        if _skey(l["vendor"]) not in keys:
            continue
        s = stmts.get(l.get("stmt_id"))
        if s is None or s["voided_at"]:
            st = "unbilled"
        elif s["paid_at"]:
            st = "paid"
        elif s["bill_id"]:
            st = "billed"
        else:
            st = "on statement"
        l["state"] = st
        l["stmt"] = s
        l["amount"] = (l["qty"] or 0) * l["rate"] if (l["rate"] is not None and l["qty"] is not None) else None
        l["side"] = l.get("side") or "clinic"
        l["stamp"] = (l["stamp"] or "").strip() or ("#%d" % l["bill_id"])
        out.append(l)
    return out


def nk_rows(db):
    return [l for l in account_rows(db) if l["side"] == "nk"]


def account_view(db, ym=None, product=None, state=None):
    rows = account_rows(db)
    unpaid = [l for l in rows if l["state"] in ("unbilled", "on statement", "billed")]
    yr = datetime.date.today().strftime("%Y")                         # paid_at is written by the real clock
    paid = [l for l in rows if l["state"] == "paid" and (l["stmt"]["paid_at"] or "")[:4] == yr]

    def tot(ls):
        a = sum(l["amount"] for l in ls if l["amount"] is not None)
        n = len([l for l in ls if l["amount"] is None])
        return a, n
    box = {"unpaid_clinic": tot([l for l in unpaid if l["side"] == "clinic"]), "unpaid_nk": tot([l for l in unpaid if l["side"] == "nk"]),
           "oldest": min((l["day"] for l in unpaid), default=""),
           "paid_est": tot([l for l in paid if (l["stmt"].get("bill_dk") or "") == "estimate"])[0],
           "paid_bill": tot([l for l in paid if (l["stmt"].get("bill_dk") or "") != "estimate"])[0],
           "paid_clinic": tot([l for l in paid if l["side"] == "clinic"])[0], "paid_nk": tot([l for l in paid if l["side"] == "nk"])[0]}
    if box["oldest"]:
        box["oldest_days"] = max(0, (_today() - datetime.date.fromisoformat(box["oldest"])).days)
    shown = [l for l in rows if (not ym or _ym_of_line(l) == ym) and (not product or str(l["item_id"]) == str(product)) and (not state or l["state"] == state)]
    months = sorted({_ym_of_line(l) for l in rows}, reverse=True)
    prods = sorted({(l["item_id"], l["name"]) for l in rows if l["item_id"]}, key=lambda x: x[1].lower())
    return {"rows": list(reversed(shown)), "box": box, "months": months, "prods": prods, "n": len(rows)}


# ---- the statements
def stmt_rows(db, live=True):
    try:
        rows = [dict(r) for r in db.execute("SELECT * FROM stationery_stmt ORDER BY id")]
    except sqlite3.Error:
        return []
    out = []
    for s in rows:
        if live and s["voided_at"]:
            continue
        s["bill_dk"], s["bill_stamp"] = "", ""
        if s["bill_id"]:
            try:
                b = db.execute("SELECT stamp_no, doc_kind FROM bills WHERE id=?", (s["bill_id"],)).fetchone()
                if b:
                    s["bill_dk"], s["bill_stamp"] = (b["doc_kind"] or ""), ((b["stamp_no"] or "").strip() or ("#%d" % s["bill_id"]))
            except sqlite3.Error:
                pass
        s["state"] = "paid" if s["paid_at"] else ("billed" if s["bill_id"] else ("sent" if s["sent_at"] else "made"))
        out.append(s)
    return out


def _end_of(ym):
    y, m = int(ym[:4]), int(ym[5:7])
    return (datetime.date(y + (m // 12), (m % 12) + 1, 1) - datetime.timedelta(days=1)).isoformat()


def stmt_lines_for(db, ym, key):
    """The lines a statement for this month would carry: every unbilled line of that supplier up to the month's end (an older
    unbilled line comes too, named older), grouped by paper in date order."""
    end = _end_of(ym)
    return [l for l in account_rows(db, [key]) if l["state"] == "unbilled" and (l["day"] or "")[:10] <= end]


def _group_by_paper(lines):
    papers = {}
    for l in lines:
        p = papers.setdefault(l["bill_id"], {"bid": l["bill_id"], "stamp": l["stamp"], "no": (l.get("bill_no") or "").strip(), "date": l.get("bill_date") or "",
                                             "day": l["day"], "dk": l.get("dk") or "", "lines": []})
        p["lines"].append(l)
    out = sorted(papers.values(), key=lambda p: (p["day"], p["bid"]))
    for p in out:
        sides = {l["side"] for l in p["lines"]}
        p["mixed"] = len(sides) > 1
        p["side"] = next(iter(sides)) if len(sides) == 1 else ""
    return out


def stmt_text(db, s, lines):
    """The statement as plain text -- challan-wise, in the supplier's own challan numbers; 'bill to' per challan, or per product
    on a mixed one; the quantity and a blank rate on every product."""
    sup = s["supplier"]
    vend = next((l["vendor"] for l in lines if l.get("vendor")), sup)
    out = ["Statement of stationery received — %s" % AR._month_label(s["ym"]),
           "Dr Manoj Agarwal Clinic and NK Pathology, Bareilly · from %s · challan-wise" % vend, ""]
    nc = nn = 0
    for p in _group_by_paper(lines):
        no = ("challan %s" % p["no"]) if p["no"] else p["stamp"]
        dt = _dmy(p["date"]) if p["date"] else _dmy(p["day"])
        older = " (earlier, not billed yet)" if (p["day"] or "")[:7] < s["ym"] else ""
        if p["mixed"]:
            out.append("%s · %s · MIXED — bill as marked%s" % (no, dt, older))
        else:
            out.append("%s · %s · bill to: %s%s" % (no, dt, SIDE_WORD[p["side"]], older))
        for l in p["lines"]:
            tag = (" — %s" % SIDE_WORD[l["side"]]) if p["mixed"] else ""
            out.append("    %s%s: %s %s · rate ____" % (l["name"], tag, _plain(l["qty"]), l["unit"] or ""))
            if l["side"] == "clinic":
                nc += 1
            else:
                nn += 1
    out.append("")
    out.append("%d challan%s · %d line%s · Clinic %d · NK Pathology %d" % (len(_group_by_paper(lines)), "" if len(_group_by_paper(lines)) == 1 else "s",
                                                                           nc + nn, "" if nc + nn == 1 else "s", nc, nn))
    out.append("Please bill the clinic and NK Pathology separately, as marked, against this statement.")
    return "\n".join(out)


def stmt_make(db, ym, key, who=None):
    """One tap: the statement for this month and supplier from its unbilled lines; refused when one already stands for that
    month and supplier, or when there is nothing to put on it. No commit."""
    who = _who() if who is None else who
    if any(s["ym"] == ym and s["supplier"] == key for s in stmt_rows(db)):
        raise ValueError("A statement for %s already stands — void it first to make it again." % AR._month_label(ym))
    lines = stmt_lines_for(db, ym, key)
    if not lines:
        raise ValueError("Nothing to put on a statement for %s — every sorted line is already on one." % AR._month_label(ym))
    cur = db.execute("INSERT INTO stationery_stmt(supplier, ym, made_at, made_by) VALUES(?,?,?,?)", (key, ym, _now(), who))
    sid = cur.lastrowid
    db.execute("UPDATE stationery_line SET stmt_id=? WHERE id IN (%s)" % ",".join("?" * len(lines)), [sid] + [l["id"] for l in lines])
    s = {"id": sid, "supplier": key, "ym": ym}
    txt = stmt_text(db, s, lines)
    db.execute("UPDATE stationery_stmt SET text=? WHERE id=?", (txt, sid))
    _audit(db, "stationery_stmt_made", {"id": sid, "ym": ym, "lines": len(lines)})
    return sid, len(lines)


def stmt_void(db, sid, who=None):
    """The statement withdrawn: its lines go back to unbilled; a billed or paid one is never voided."""
    s = next((x for x in stmt_rows(db) if x["id"] == sid), None)
    if s is None:
        raise ValueError("That statement is not there.")
    if s["bill_id"] or s["paid_at"]:
        raise ValueError("A billed or paid statement is kept — it is never voided.")
    db.execute("UPDATE stationery_stmt SET voided_at=?, voided_by=? WHERE id=?", (_now(), _who() if who is None else who, sid))
    db.execute("UPDATE stationery_line SET stmt_id=NULL WHERE stmt_id=?", (sid,))
    _audit(db, "stationery_stmt_voided", {"id": sid})


def stmt_join(db, sid, bill_id, rates, who=None):
    """The supplier's bill or estimate (a scanned paper, theirs, not a challan) joined to the statement; the rates typed onto its
    lines; the lines go to billed. A paper already joined to another statement is refused."""
    s = next((x for x in stmt_rows(db) if x["id"] == sid), None)
    if s is None:
        raise ValueError("That statement is not there.")
    if s["paid_at"]:
        raise ValueError("A paid statement is kept as it is.")
    b = db.execute("SELECT * FROM bills WHERE id=?", (bill_id,)).fetchone()
    if b is None or b["dup_of"] or b["status"] == "rejected":
        raise ValueError("Choose the supplier's scanned bill or estimate.")
    if (b["doc_kind"] or "bill") not in ("bill", "estimate"):
        raise ValueError("%s is a %s — join their bill or estimate, not a challan." % (_stamp_of(b), b["doc_kind"]))
    if _skey(b["vendor"]) != s["supplier"]:
        raise ValueError("%s is not this supplier's paper." % _stamp_of(b))
    if any(x["bill_id"] == bill_id and x["id"] != sid for x in stmt_rows(db)):
        raise ValueError("%s is already joined to another statement." % _stamp_of(b))
    n = 0
    for lid, rate in rates.items():
        if rate is None:
            continue
        db.execute("UPDATE stationery_line SET rate=? WHERE id=? AND stmt_id=?", (rate, lid, sid))
        n += 1
    db.execute("UPDATE stationery_stmt SET bill_id=?, bill_created_at=?, billed_at=? WHERE id=?", (bill_id, b["created_at"] or "", _now(), sid))
    _audit(db, "stationery_stmt_billed", {"id": sid, "bill": bill_id, "rates": n})
    return n


def stmt_paid(db, sid, ref, who=None):
    s = next((x for x in stmt_rows(db) if x["id"] == sid), None)
    if s is None:
        raise ValueError("That statement is not there.")
    if not s["bill_id"]:
        raise ValueError("Join the supplier's bill or estimate first — a payment is recorded against their paper.")
    if s["paid_at"]:
        raise ValueError("Already marked paid.")
    db.execute("UPDATE stationery_stmt SET paid_at=?, paid_ref=? WHERE id=?", (_now(), re.sub(r"\s+", " ", ref or "").strip()[:120], sid))
    _audit(db, "stationery_stmt_paid", {"id": sid, "ref": (ref or "")[:120]})


def stmt_sent(db, sid):
    db.execute("UPDATE stationery_stmt SET sent_at=? WHERE id=? AND sent_at=''", (_now(), sid))
    _audit(db, "stationery_stmt_sent", {"id": sid})


def supplier_phone(db, key):
    """The supplier's phone from the vendors table (read only) as digits for a WhatsApp link; '' when none."""
    try:
        for r in db.execute("SELECT name, phone FROM vendors WHERE phone IS NOT NULL AND phone<>''"):
            if _skey(r["name"]) == key:
                d = re.sub(r"\D", "", r["phone"] or "")
                if len(d) == 10:
                    d = "91" + d
                return d if 11 <= len(d) <= 15 else ""
    except sqlite3.Error:
        pass
    return ""


def their_papers(db, key):
    """The supplier's bills and estimates not joined to a statement yet -- what 'Join their bill' offers."""
    used = {s["bill_id"] for s in stmt_rows(db) if s["bill_id"]}
    return [b for b in listed_papers(db, [key]) if (b["doc_kind"] or "bill") in ("bill", "estimate") and b["id"] not in used]


def flow_view(db, ym):
    """Everything the owner's Stationery page shows for the flow: the suppliers, to-sort, sorted this month, the NK ledger, the
    account and the statements."""
    keys = suppliers(db)
    ts = to_sort(db)
    acc = account_view(db, ym=request.args.get("aym") or "", product=request.args.get("aprod") or "", state=request.args.get("astate") or "")
    stmts = list(reversed(stmt_rows(db)))
    cur = next((s for s in stmts if s["supplier"] == (keys[0] if keys else "")), None)        # the newest statement, whatever its month
    cur_month = any(s["ym"] == ym and s["supplier"] == (keys[0] if keys else "") for s in stmts)
    pending = stmt_lines_for(db, ym, keys[0]) if keys else []
    sorted_m = []
    for b in listed_papers(db):
        ls = _live_lines(db, b)
        if ls and (ls[0]["day"] or "")[:7] == ym:
            sorted_m.append({"b": b, "stamp": _stamp_of(b), "n": len(ls), "sides": sorted({(l["side"] if "side" in l.keys() else "clinic") for l in ls}),
                             "locked": any((l["stmt_id"] if "stmt_id" in l.keys() else None) for l in ls)})
    names = {}
    for b in listed_papers(db):
        names.setdefault(_skey(b["vendor"]), b["vendor"])
    return {"sups": keys, "names": names, "floor": floor_day(db), "to_sort": ts, "sorted": sorted_m, "nk": list(reversed(nk_rows(db))), "acc": acc, "stmts": stmts,
            "cur": cur, "cur_month": cur_month, "pending": pending, "pending_papers": _group_by_paper(pending), "unsorted_n": sum(len([l for l in p["lines"]]) for p in ts),
            "phone": supplier_phone(db, keys[0]) if keys else "", "theirs": their_papers(db, keys[0]) if keys else [],
            "products": item_rows(db, active_only=True)}


# ---- the pages
SORT_CSS = """<style>
.s674 .ln{display:grid;grid-template-columns:minmax(200px,2fr) 70px 110px 150px 90px;gap:6px;align-items:start;padding:6px 0;border-bottom:1px solid #eee}
.s674 .ln.h{font-size:12px;color:#5e6a63;text-transform:uppercase;letter-spacing:.05em}
.s674 .read{font-size:12px;color:#5e6a63}
.s674 .seg{display:inline-flex;border:1px solid #ccc;border-radius:4px;overflow:hidden}
.s674 .seg label{margin:0;padding:3px 9px;font-size:13px;cursor:pointer}.s674 .seg input{display:none}
.s674 .seg input:checked+span{background:#8a4b12;color:#fff}.s674 .seg label.nk input:checked+span{background:#2b5c8a;color:#fff}
.s674 .seg span{display:block;padding:3px 9px;margin:-3px -9px}
.s674 .chal{background:#f7f5f0;padding:6px 8px;border-radius:4px;margin-top:10px;font-weight:600}
.s674 .pill{display:inline-block;font-size:12px;padding:1px 8px;border-radius:10px;white-space:nowrap}
.s674 .p-cl{background:#fbf1e6;color:#8a4b12}.s674 .p-nk{background:#e9f0f7;color:#2b5c8a}.s674 .p-ok{background:#e4f1ea;color:#1d6b45}.s674 .p-wn{background:#fff5d6;color:#9a6a00}.s674 .p-mu{background:#f1f1ee;color:#5e6a63;border:1px solid #ddd}
.s674 input,.s674 select{font-size:13px;padding:3px 6px}
.s674 pre{white-space:pre-wrap;font:13px/1.4 ui-monospace,Menlo,Consolas,monospace;background:#f7f5f0;border:1px dashed #ccc;padding:10px;border-radius:6px;max-width:560px}
@media(max-width:600px){.s674 .ln{grid-template-columns:1fr 1fr}.s674 .ln.h{display:none}}
</style>"""

PAPER_FORM = """{% macro paperform(p, action, owner, words, items, back) %}
<form method=post action="{{action}}" class=s674 data-paper="{{p.b.id}}"><input type=hidden name=paper value="{{p.b.id}}"><input type=hidden name=back value="{{back}}">
<div class=chal>{{p.stamp}}{% if p.b.bill_no %} · {{words.challan}} {{p.b.bill_no}}{% endif %}{% if p.b.bill_date %} · {{dmy(p.b.bill_date)}}{% endif %} · {{words.scanned}} {{dmy((p.b.created_at or '')[:10])}}{% if p.b.submitted_by %} {{words.by}} {{p.b.submitted_by}}{% endif %}
{% if p.lane_note %} <span class="pill p-wn">{{p.lane_note}}</span>{% endif %}{% if p.locked %} <span class="pill p-mu">{{words.locked}}</span>{% endif %}</div>
{% if p.noread %}<div class=read>{{words.noread}}</div>{% endif %}
<div class="ln h"><span>{{words.product}}</span><span>{{words.qty}}</span><span>{{words.unit}}</span><span>{{words.forw}}</span><span>{% if owner %}{{words.rate}}{% endif %}</span></div>
{% for l in p.lines %}<div class=ln>
<div>{% if l.read %}<div class=read>{{words.read}}: {{l.read}}</div>{% endif %}<input name="n{{loop.index}}" list=s674items value="{{l.name}}" placeholder="{{words.type}}" style="width:100%;max-width:300px" autocomplete=off>{% if l.sug %}<div class=read>{{words.sug}}</div>{% endif %}</div>
<div><input name="q{{loop.index}}" value="{{l.qty}}" inputmode=decimal style="width:64px"></div>
<div><input name="u{{loop.index}}" list=s568units value="{{l.unit}}" style="width:100px"></div>
<div><span class=seg><label><input type=radio name="f{{loop.index}}" value=clinic{{' checked' if l.side=='clinic'}}><span>{{words.clinic}}</span></label><label class=nk><input type=radio name="f{{loop.index}}" value=nk{{' checked' if l.side=='nk'}}><span>NK</span></label></span>{% if l.ns %}<input type=hidden name="ns{{loop.index}}" value=1>{% endif %}</div>
<div>{% if owner %}<input name="r{{loop.index}}" value="{{plain(l.rate) if l.rate is not none else ''}}" inputmode=decimal style="width:80px" placeholder="{{words.pending}}">{% endif %}</div>
</div>{% endfor %}
{% for k in range(p.lines|length + 1, p.lines|length + 3) %}<div class=ln>
<div><input name="n{{k}}" list=s674items placeholder="{{words.more}}" style="width:100%;max-width:300px" autocomplete=off></div><div><input name="q{{k}}" inputmode=decimal style="width:64px"></div><div><input name="u{{k}}" list=s568units style="width:100px"></div>
<div><span class=seg><label><input type=radio name="f{{k}}" value=clinic><span>{{words.clinic}}</span></label><label class=nk><input type=radio name="f{{k}}" value=nk><span>NK</span></label></span></div><div>{% if owner %}<input name="r{{k}}" inputmode=decimal style="width:80px">{% endif %}</div>
</div>{% endfor %}
<div style="display:flex;gap:10px;align-items:center;margin-top:8px;flex-wrap:wrap">{% if not p.locked %}<button class=btn>{{words.save}} {{p.stamp}}</button>{% endif %}<span class=muted>{{words.hint}}</span></div>
</form>{% if owner and p.leave %}<form method=post action="{{url_for('s674_leave')}}" style="margin:-4px 0 6px"><input type=hidden name=paper value="{{p.b.id}}"><button class="btn small">Leave {{p.stamp}} as it is</button> <span class=muted>— not goods for the stock, or already dealt with: it is not offered again.</span></form>{% endif %}{% endmacro %}"""

OWNER_WORDS = {"challan": "challan", "scanned": "scanned", "by": "by", "locked": "on a statement — change it from the statement, not here", "noread": "No items read — type the lines by hand.",
               "product": "Product — type, pick, or add", "qty": "Qty", "unit": "Unit", "forw": "For", "rate": "Rate ₹", "read": "read", "type": "type the product…",
               "sug": "matched by the system — change it if wrong", "pending": "pending", "more": "another line…", "clinic": "Clinic", "save": "Save",
               "hint": "A name not on the list is added on Save (its unit as typed). A line with neither Clinic nor NK waits. Nothing is guessed."}
STAFF_WORDS = {"challan": "challan", "scanned": "scan", "by": "—", "locked": "statement par hai — Dr Manoj badlenge", "noread": "Kuch padha nahi gaya — line haath se likhein.",
               "product": "Saamaan — likhein ya chunein", "qty": "Kitna", "unit": "Unit", "forw": "Kiske liye", "rate": "", "read": "padha", "type": "saamaan likhein…",
               "sug": "system ne milaya — galat ho to badlein", "pending": "", "more": "aur ek line…", "clinic": "Clinic", "save": "Save karo",
               "hint": "List mein naya naam Save par jud jaata hai. Clinic ya NK na chuna to line baaki rehti hai."}

FLOW_TOP_TPL = SORT_CSS + PAPER_FORM + """
<datalist id=s674items>{% for i in f.products %}<option value="{{i.name}}">{% endfor %}</datalist>
<div class="card s674" id=s674sup><b>Suppliers whose every challan lands here</b> <span class=muted>— the sorting desk is skipped for them; the paper is placed by its lines.</span>
<form method=post action="{{url_for('s674_supplier')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px">
{% for k in f.sups %}<span class="pill p-cl">{{f.names.get(k, k)}} <button name=remove value="{{k}}" class=muted style="border:0;background:none;padding:0 2px" title="take off">×</button></span>{% endfor %}
<input name=add placeholder="a supplier's name, as on their paper" style="max-width:260px"><button class="btn small" name=do value=add>+ Add</button></form></div>
<div class="card s674" id=s674sort><b>1 · To sort — {{f.to_sort|length}} paper{{'' if f.to_sort|length == 1 else 's'}}</b> <span class=muted>— each line: the product, the quantity, and Clinic or NK. One Save per paper.{% if f.floor %} Challans scanned from {{dmy(f.floor)}}; their bills and estimates are joined to a statement (section 5), never sorted.{% else %} <b>No start day set</b> — nothing is offered until a supplier is added above.{% endif %}</span>
{% for p in f.to_sort %}{{paperform(p, url_for('s674_sort_save'), True, words, f.products, 'stock')}}{% else %}<p class=muted style="margin:6px 0 0">Nothing waiting.</p>{% endfor %}
{% if f.sorted %}<details style="margin-top:8px"><summary class=muted>Sorted this month ({{f.sorted|length}})</summary><ul style="margin:6px 0 0">{% for s in f.sorted %}<li><a href="{{href(s.b.id)}}">{{s.stamp}}</a> · {{s.n}} line{{'' if s.n == 1 else 's'}} · {% for sd in s.sides %}<span class="pill {{'p-nk' if sd=='nk' else 'p-cl'}}">{{'NK' if sd=='nk' else 'Clinic'}}</span> {% endfor %}{% if s.locked %}<span class="pill p-mu">on a statement</span>{% else %}<a href="{{url_for('s568_stock')}}?change={{s.b.id}}#s674change">change</a>{% endif %}</li>{% endfor %}</ul></details>{% endif %}
{% if change %}<div id=s674change style="margin-top:10px"><b>Change {{change.stamp}}</b>{{paperform(change, url_for('s674_sort_save'), True, words, f.products, 'stock')}}</div>{% endif %}</div>
<div class="card s674" id=s674nk><b>2 · NK Pathology — stationery from the listed suppliers, kept apart</b> <span class=muted>— never added to the clinic's stock or received.</span>
{% if f.nk %}<div style="overflow:auto"><table><tr><th>Day</th><th>Paper</th><th>Product</th><th>Qty</th><th>Rate</th><th>Amount</th><th>State</th></tr>
{% for l in f.nk %}<tr><td>{{dmy(l.day)}}</td><td><a href="{{href(l.bill_id)}}">{{l.stamp}}</a></td><td>{{l.name}}</td><td>{{plain(l.qty)}} {{l.unit}}</td><td>{{rs(l.rate) if l.rate is not none else '—'}}</td><td>{{rs(l.amount) if l.amount is not none else '—'}}</td><td>{{statepill(l.state)}}</td></tr>{% endfor %}</table></div>{% else %}<p class=muted style="margin:6px 0 0">None yet.</p>{% endif %}</div>
"""

FLOW_BOTTOM_TPL = """
<div class="card s674" id=s674acc><b>4 · The supplier account — every line supplied</b>
<form method=get action="{{url_for('s568_stock')}}#s674acc" style="display:inline-flex;gap:6px;flex-wrap:wrap;margin-left:10px"><select name=aym onchange="this.form.submit()"><option value="">All months</option>{% for m in f.acc.months %}<option value="{{m}}"{{' selected' if request.args.get('aym')==m}}>{{m}}</option>{% endfor %}</select>
<select name=aprod onchange="this.form.submit()"><option value="">All products</option>{% for pid, pn in f.acc.prods %}<option value="{{pid}}"{{' selected' if request.args.get('aprod')==(pid|string)}}>{{pn}}</option>{% endfor %}</select>
<select name=astate onchange="this.form.submit()"><option value="">All states</option>{% for st in ('unbilled','on statement','billed','paid') %}<option value="{{st}}"{{' selected' if request.args.get('astate')==st}}>{{st}}</option>{% endfor %}</select></form>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;margin:8px 0">
<div style="border:1px solid #ddd;border-radius:6px;padding:8px 12px"><b>Unpaid</b><div>Clinic: {{rs(f.acc.box.unpaid_clinic[0])}}{% if f.acc.box.unpaid_clinic[1] %} + {{f.acc.box.unpaid_clinic[1]}} line{{'' if f.acc.box.unpaid_clinic[1]==1 else 's'}} without a rate{% endif %}</div><div>NK: {{rs(f.acc.box.unpaid_nk[0])}}{% if f.acc.box.unpaid_nk[1] %} + {{f.acc.box.unpaid_nk[1]}} line{{'' if f.acc.box.unpaid_nk[1]==1 else 's'}} without a rate{% endif %}</div>{% if f.acc.box.oldest %}<div>Oldest unpaid: {{dmy(f.acc.box.oldest)}} ({{f.acc.box.oldest_days}} days)</div>{% endif %}</div>
<div style="border:1px solid #ddd;border-radius:6px;padding:8px 12px"><b>Paid this year</b><div>On estimates: {{rs(f.acc.box.paid_est)}}</div><div>On bills: {{rs(f.acc.box.paid_bill)}}</div><div>Clinic / NK: {{rs(f.acc.box.paid_clinic)}} / {{rs(f.acc.box.paid_nk)}}</div></div></div>
{% if f.acc.rows %}<div style="overflow:auto"><table><tr><th>Day</th><th>Paper</th><th>Product</th><th>Qty</th><th>For</th><th>Rate</th><th>Amount</th><th>State</th><th>Their paper</th></tr>
{% for l in f.acc.rows %}<tr><td>{{dmy(l.day)}}</td><td><a href="{{href(l.bill_id)}}">{{l.stamp}}</a>{% if l.bill_no %} <span class=muted>{{l.bill_no}}</span>{% endif %}</td><td>{{l.name}}</td><td>{{plain(l.qty)}} {{l.unit}}</td><td><span class="pill {{'p-nk' if l.side=='nk' else 'p-cl'}}">{{'NK' if l.side=='nk' else 'Clinic'}}</span></td><td>{{rs(l.rate) if l.rate is not none else '—'}}</td><td>{{rs(l.amount) if l.amount is not none else '—'}}</td><td>{{statepill(l.state)}}</td><td>{% if l.stmt and l.stmt.bill_stamp %}{{l.stmt.bill_stamp}}{% if l.stmt.paid_at %} · paid {{dmy(l.stmt.paid_at[:10])}}{% endif %}{% else %}—{% endif %}</td></tr>{% endfor %}</table></div>{% else %}<p class=muted style="margin:6px 0 0">No line yet{% if f.acc.n %} for this filter{% endif %}.</p>{% endif %}
<p class=muted style="margin:6px 0 0"><span class="pill p-mu">unbilled</span> on no statement yet · <span class="pill p-wn">on statement</span> sent, bill awaited · <span class="pill p-ok">billed / paid</span> paid once, ever</p></div>
<div class="card s674" id=s674stmt><b>5 · Monthly statement{% if f.cur %} — {{mlabel(f.cur.ym)}}{% else %} — {{label}}{% endif %}</b>
{% if f.cur %}<span class=muted>made {{f.cur.made_at[:16]}}{% if f.cur.sent_at %} · sent {{f.cur.sent_at[:16]}}{% endif %}</span> {{statepill(f.cur.state)}}{% endif %}
<p class=muted style="margin:6px 0">One tap makes it from the sorted lines not yet on a statement (older ones come too, named): challan by challan, in the supplier's own challan numbers; a mixed challan names which products go where, rates blank for the supplier to fill. A line sorted after it is sent rolls into the next month.</p>
{% if not f.cur_month %}<form method=post action="{{url_for('s674_stmt_make')}}" style="display:flex;gap:8px;flex-wrap:wrap;align-items:center"><input type=hidden name=ym value="{{ym}}"><button class=btn{{' disabled' if not f.pending}}>Make {{label}}'s statement</button>
<span class=muted>{{f.pending|length}} line{{'' if f.pending|length == 1 else 's'}} on {{f.pending_papers|length}} paper{{'' if f.pending_papers|length == 1 else 's'}} ready{% if f.unsorted_n %} · {{f.unsorted_n}} line{{'' if f.unsorted_n == 1 else 's'}} not yet sorted (section 1){% endif %}</span></form>{% endif %}
{% if f.cur %}<pre id=s674text>{{f.cur.text}}</pre>
<div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
<button class="btn small" type=button onclick="(function(){var t=document.getElementById('s674text').textContent;if(navigator.clipboard){navigator.clipboard.writeText(t).then(function(){alert('Copied.')});}})()">Copy the text</button>
{% if f.phone %}<a class="btn small" href="https://wa.me/{{f.phone}}?text={{f.cur.text|urlencode}}" target=_blank rel=noopener>Send on WhatsApp</a>{% else %}<span class=muted>(no phone on the Vendors page — copy the text)</span>{% endif %}
<button class="btn small" type=button onclick="window.print()">Print</button>
{% if not f.cur.sent_at %}<form method=post action="{{url_for('s674_stmt_sent')}}" style="margin:0"><input type=hidden name=id value="{{f.cur.id}}"><button class="btn small">Mark sent</button></form>{% endif %}
{% if not f.cur.bill_id %}<form method=post action="{{url_for('s674_stmt_void')}}" style="margin:0" onsubmit="return confirm('Withdraw this statement? Its lines go back to unbilled.')"><input type=hidden name=id value="{{f.cur.id}}"><button class="btn small danger">Withdraw</button></form>{% endif %}</div>
{% if not f.cur.bill_id %}<details style="margin-top:8px" open><summary><b>Join their bill or estimate</b> <span class=muted>— scanned already; its rates typed onto the lines</span></summary>
<form method=post action="{{url_for('s674_stmt_join')}}" style="margin-top:6px"><input type=hidden name=id value="{{f.cur.id}}">
<label style="margin:0">Their paper <select name=bill required><option value="">— choose the scanned paper —</option>{% for b in f.theirs %}<option value="{{b.id}}">{{b.stamp_no or ('#' ~ b.id)}} · {{b.doc_kind or 'bill'}}{% if b.bill_no %} {{b.bill_no}}{% endif %}{% if b.total_amount %} · {{rs(b.total_amount)}}{% endif %}</option>{% endfor %}</select></label>
<div style="overflow:auto;margin-top:6px"><table><tr><th>Paper</th><th>Product</th><th>For</th><th>Qty</th><th>Rate ₹</th></tr>{% for l in stmt_lines %}<tr><td>{{l.stamp}}</td><td>{{l.name}}</td><td>{{'NK' if l.side=='nk' else 'Clinic'}}</td><td>{{plain(l.qty)}} {{l.unit}}</td><td><input name="r{{l.id}}" value="{{plain(l.rate) if l.rate is not none else ''}}" inputmode=decimal style="width:80px"></td></tr>{% endfor %}</table></div>
<button class="btn small" style="margin-top:6px">Join and save the rates</button></form></details>
{% elif not f.cur.paid_at %}<div style="margin-top:8px">Billed: <b>{{f.cur.bill_stamp}}</b> ({{f.cur.bill_dk or 'bill'}}) on {{dmy(f.cur.billed_at[:10])}}. <form method=post action="{{url_for('s674_stmt_paid')}}" style="display:inline-flex;gap:6px;align-items:center;margin:0 0 0 8px"><input type=hidden name=id value="{{f.cur.id}}"><input name=ref placeholder="how it was paid (UPI / cheque no.)" style="max-width:220px"><button class="btn small">Mark paid</button></form></div>
{% else %}<div style="margin-top:8px">Billed {{f.cur.bill_stamp}} · paid {{dmy(f.cur.paid_at[:10])}}{% if f.cur.paid_ref %} ({{f.cur.paid_ref}}){% endif %}.</div>{% endif %}{% endif %}
{% set older = f.stmts|rejectattr('id', 'equalto', f.cur.id if f.cur else 0)|list %}{% if older %}<details style="margin-top:8px"><summary class=muted>Earlier statements ({{older|length}})</summary><ul style="margin:6px 0 0">{% for s in older %}<li>{{s.ym}} · {{statepill(s.state)}}{% if s.bill_stamp %} · {{s.bill_stamp}}{% endif %}{% if s.paid_at %} · paid {{dmy(s.paid_at[:10])}}{% endif %} · <a href="{{url_for('s674_stmt_view', sid=s.id)}}">open</a></li>{% endfor %}</ul></details>{% endif %}</div>
"""

STMT_VIEW_TPL = SORT_CSS + """<h2 style="margin-bottom:4px">Statement — {{label}}</h2><div class=s674>{{statepill(s.state)}} <span class=muted>made {{s.made_at[:16]}} by {{s.made_by}}{% if s.sent_at %} · sent {{s.sent_at[:16]}}{% endif %}{% if s.bill_stamp %} · billed {{s.bill_stamp}}{% endif %}{% if s.paid_at %} · paid {{dmy(s.paid_at[:10])}} {{s.paid_ref}}{% endif %}</span>
<pre>{{s.text}}</pre><p><a href="{{url_for('s568_stock')}}#s674stmt">← Stationery</a></p></div>"""

STAFF_SORT_TPL = SORT_CSS + PAPER_FORM + """<h2 style="margin-bottom:4px">Stationery sort</h2>
<p class=muted style="margin-top:0">{{f.to_sort|length}} paper baaki. Har line: saamaan, kitna, aur Clinic ya NK. Ek paper, ek Save.</p>
<datalist id=s674items>{% for i in f.products %}<option value="{{i.name}}">{% endfor %}</datalist><datalist id=s568units>{% for u in units %}<option value="{{u}}">{% endfor %}</datalist>
{% for p in f.to_sort %}<div class=card>{{paperform(p, url_for('s674_sort_save'), False, words, f.products, 'sort')}}</div>{% else %}<div class=card><p class=muted>Abhi kuch baaki nahi.</p></div>{% endfor %}"""


def _statepill(st):
    cls = {"unbilled": "p-mu", "on statement": "p-wn", "sent": "p-wn", "made": "p-mu", "billed": "p-ok", "paid": "p-ok"}.get(st, "p-mu")
    return Markup('<span class="pill %s">%s</span>' % (cls, st))


def flow_ctx(db, ym):
    f = flow_view(db, ym)
    change = None
    cid = request.args.get("change")
    if cid and str(cid).isdigit():
        b = db.execute("SELECT * FROM bills WHERE id=?", (int(cid),)).fetchone()
        if b is not None and is_listed(db, b["vendor"]):
            change = sorted_paper(db, b)
    stmt_lines = [l for l in account_rows(db) if f["cur"] and l.get("stmt_id") == f["cur"]["id"]] if f["cur"] else []
    return {"f": f, "change": change, "stmt_lines": stmt_lines, "words": OWNER_WORDS, "statepill": _statepill, "ym": ym}


def flow_top(db, ym, ctx):
    return Markup(render_template_string(FLOW_TOP_TPL, href=_href, dmy=_dmy, plain=_plain, rs=rs, **ctx))


def flow_bottom(db, ym, ctx):
    return Markup(render_template_string(FLOW_BOTTOM_TPL, href=_href, dmy=_dmy, plain=_plain, rs=rs, label=AR._month_label(ym), mlabel=AR._month_label, request=request, **ctx))


def may_sort(db, role=None):
    """The owner always; a manager while the desk switch (desk.on) is ON -- his desk, his sorting."""
    role = _role() if role is None else role
    if role == "owner":
        return True
    sd = _desk_mod()
    try:
        return role == "manager" and sd is not None and bool(sd.desk_on(db))
    except Exception:                                                # noqa: BLE001
        return False


def _back(form):
    return url_for("s568_stock") + "#s674sort" if (form.get("back") or "stock") == "stock" else url_for("s674_sort")


def sort_save_post():
    db = AR.get_db()
    f = request.form
    owner = _role() == "owner"
    if not may_sort(db):
        abort(403)
    try:
        b = db.execute("SELECT * FROM bills WHERE id=?", (int(f.get("paper") or 0),)).fetchone()
        if b is None or not is_listed(db, b["vendor"]):
            raise ValueError("That paper is not a listed supplier's.")
        if any((l["stmt_id"] if "stmt_id" in l.keys() else None) for l in _live_lines(db, b)):
            raise ValueError("%s is on a statement — change it from the statement, not here." % _stamp_of(b))
        msgs = sort_save(db, b, f, owner=owner)
        db.commit()
        flash(" ".join(msgs) if owner else "Save ho gaya — %s." % _stamp_of(b))
    except ValueError as e:
        db.rollback()
        flash(str(e))
    return redirect(_back(f))


def supplier_post():
    db = AR.get_db()
    f = request.form
    keys = suppliers(db)
    if f.get("remove"):
        keys = [k for k in keys if k != f.get("remove")]
        msg = "Taken off the list."
    else:
        k = _skey(f.get("add"))
        if not k:
            flash("Type the supplier's name as it reads on their paper.")
            return redirect(url_for("s568_stock") + "#s674sup")
        if k not in keys:
            keys.append(k)
        msg = "Added: every challan of %s scanned from today lands here." % (f.get("add") or "").strip()
        if not floor_day(db):
            db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (FLOOR_KEY, _today().isoformat()))
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (SUPPLIERS_KEY, "|".join(keys)))
    _audit(db, "stationery_suppliers", {"keys": keys})
    db.commit()
    flash(msg)
    return redirect(url_for("s568_stock") + "#s674sup")


def leave_post():
    """The owner leaves a paper as it is: off To sort, never offered again (the setting stationery.left); its lane and group untouched."""
    db = AR.get_db()
    bid = int(request.form.get("paper") or 0)
    ids = left_ids(db)
    ids.add(bid)
    db.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (LEFT_KEY, "|".join(str(x) for x in sorted(ids))))
    _audit(db, "stationery_left", {"bill": bid})
    db.commit()
    flash("Left as it is — it will not be offered again.")
    return redirect(url_for("s568_stock") + "#s674sort")


def stmt_make_post():
    db = AR.get_db()
    ym = (request.form.get("ym") or _ym())[:7]
    keys = suppliers(db)
    try:
        if not keys:
            raise ValueError("Add a supplier first.")
        sid, n = stmt_make(db, ym, keys[0])
        db.commit()
        flash("Statement for %s made — %d line%s. Copy it, send it, then Mark sent." % (AR._month_label(ym), n, "" if n == 1 else "s"))
    except ValueError as e:
        db.rollback()
        flash(str(e))
    return redirect(url_for("s568_stock") + "#s674stmt")


def stmt_sent_post():
    db = AR.get_db()
    stmt_sent(db, int(request.form.get("id") or 0))
    db.commit()
    flash("Marked sent.")
    return redirect(url_for("s568_stock") + "#s674stmt")


def stmt_void_post():
    db = AR.get_db()
    try:
        stmt_void(db, int(request.form.get("id") or 0))
        db.commit()
        flash("Statement withdrawn — its lines are unbilled again.")
    except ValueError as e:
        db.rollback()
        flash(str(e))
    return redirect(url_for("s568_stock") + "#s674stmt")


def stmt_join_post():
    db = AR.get_db()
    f = request.form
    try:
        sid = int(f.get("id") or 0)
        rates = {}
        for k, v in f.items():
            if k.startswith("r") and k[1:].isdigit():
                rates[int(k[1:])] = _num(v)
        n = stmt_join(db, sid, int(f.get("bill") or 0), rates)
        db.commit()
        flash("Joined — %d rate%s saved; the lines are billed." % (n, "" if n == 1 else "s"))
    except ValueError as e:
        db.rollback()
        flash(str(e))
    return redirect(url_for("s568_stock") + "#s674stmt")


def stmt_paid_post():
    db = AR.get_db()
    try:
        stmt_paid(db, int(request.form.get("id") or 0), request.form.get("ref"))
        db.commit()
        flash("Marked paid.")
    except ValueError as e:
        db.rollback()
        flash(str(e))
    return redirect(url_for("s568_stock") + "#s674stmt")


def stmt_view(sid):
    db = AR.get_db()
    s = next((x for x in stmt_rows(db, live=False) if x["id"] == sid), None)
    if s is None:
        abort(404)
    return AR.page(STMT_VIEW_TPL, s=s, label=AR._month_label(s["ym"]), statepill=_statepill, dmy=_dmy,
                   flow=AR._flow("Statement", url_for("s568_stock")))


def staff_sort_page():
    db = AR.get_db()
    if not may_sort(db):
        return AR.page("<h2>Stationery sort</h2><p class=muted>" + OFF_LINE + "</p>", flow=AR._flow("Stationery sort"))
    f = flow_view(db, _ym())
    return AR.page(STAFF_SORT_TPL, f=f, words=STAFF_WORDS, units=UNITS, dmy=_dmy, plain=_plain, rs=rs, href=_href, statepill=_statepill,
                   flow=AR._flow("Stationery sort"))


def menu_items_s674(role, db):
    try:
        if role == "manager" and may_sort(db, role):
            n = len(to_sort(db))
            return [("s674_sort", "Stationery sort (%d)" % n, url_for("s674_sort"))]
    except Exception:                                                # noqa: BLE001
        pass
    return []


def seed_suppliers_step(db_path, names=("Variety Stationers",), out=print):
    """The installer's data step: the first listed supplier, once (the setting empty); a second run changes nothing."""
    ensure_path(db_path)                                             # the table and columns, whether or not the mount got them (a locked db)
    out("tables and columns: present")
    con = sqlite3.connect(db_path, timeout=30)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT)")
        cur = (con.execute("SELECT value FROM settings WHERE key=?", (SUPPLIERS_KEY,)).fetchone() or [""])[0] or ""
        if cur.strip():
            out("suppliers: already set (%s) -- unchanged" % cur)
            return 0
        keys = [_skey(n) for n in names if _skey(n)]
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (SUPPLIERS_KEY, "|".join(keys)))
        day = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date().isoformat()   # IST, as created_at is written
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (FLOOR_KEY, day))
        con.commit()
        out("suppliers: set to %s; papers scanned from %s (IST) sort on the page (older ones stay as they are)" % ("|".join(keys), day))
        return 0
    finally:
        con.close()


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):
    """Called once, at the foot of asset_register.py, after sorting_desk is mounted."""
    global AR, MOUNTED
    AR = ar
    ensure_at_mount(ar.DB_PATH)
    app = ar.app
    app.add_url_rule("/stationery", "s568_stock", ar.owner_required(stock_page))
    app.add_url_rule("/stationery/item", "s568_item", ar.owner_required(item_post), methods=["POST"])
    app.add_url_rule("/stationery/diya", "s568_issue", ar.checker_required(issue_page), methods=["GET", "POST"])
    app.add_url_rule("/stationery/count", "s568_count", ar.checker_required(count_post), methods=["POST"])
    app.add_url_rule("/stationery/diya/many", "s585_issue_many", ar.checker_required(many_post), methods=["POST"])    # S585
    app.add_url_rule("/stationery/many", "s585_many", ar.owner_required(many_switch), methods=["POST"])              # S585
    app.add_url_rule("/stationery/void", "s585_void", ar.owner_required(void_post), methods=["POST"])                # S585
    app.add_url_rule("/stationery/sort", "s674_sort", ar.checker_required(staff_sort_page))                            # S674
    app.add_url_rule("/stationery/sort/save", "s674_sort_save", ar.checker_required(sort_save_post), methods=["POST"])
    app.add_url_rule("/stationery/supplier", "s674_supplier", ar.owner_required(supplier_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/make", "s674_stmt_make", ar.owner_required(stmt_make_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/sent", "s674_stmt_sent", ar.owner_required(stmt_sent_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/void", "s674_stmt_void", ar.owner_required(stmt_void_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/join", "s674_stmt_join", ar.owner_required(stmt_join_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/paid", "s674_stmt_paid", ar.owner_required(stmt_paid_post), methods=["POST"])
    app.add_url_rule("/stationery/statement/<int:sid>", "s674_stmt_view", ar.owner_required(stmt_view))
    app.add_url_rule("/stationery/leave", "s674_leave", ar.owner_required(leave_post), methods=["POST"])
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data step:  python3 stationery.py --ensure <assets.db>
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        print("stationery %s: tables ready (%s)" % (VERSION, ", ".join(ensure_path(sys.argv[2]))))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--history":          # S585: the installer's data step (Shavez's sheet, once)
        sys.exit(history_step(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--history-void":     # S585: its undo -- voids those lines, never deletes
        sys.exit(history_void(sys.argv[2]))
    else:
        print(__doc__)
