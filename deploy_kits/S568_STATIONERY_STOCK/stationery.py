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
"""
import datetime
import json
import math
import re
import sqlite3
import sys
import time

from flask import abort, flash, g, redirect, request, url_for

VERSION = "S568"
FIX = "S568_FIX1"             # K1 CORRECTIONS 1-2: the stock follows where the paper is now; the staff screen as the owner's mock-up
AR = None                     # the asset app's module, handed in by init()
TODAY = None                  # the walk sets a made-up day here
MOUNTED = False
SWITCH = "stationery.issue_on"
PLACES = (("lab", "Lab"), ("reception", "Reception"), ("sanjeevni", "Sanjeevni"), ("clinic", "Clinic"))
PLACE_WORD = dict(PLACES)
UNITS = ("piece", "pack", "ream", "box", "packet", "register", "book", "file", "roll", "bundle", "set", "dozen")

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
    return "l.voided_at='' AND l.item_id IS NOT NULL AND l.not_stock=0 AND l.qty IS NOT NULL AND " + _paper_sql(db, "b")


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
    no, name, q, unit, rate, iid, ns = t
    return (no, name, "" if q is None else "%.4f" % q, unit, "" if rate is None else "%.4f" % rate, iid or 0, ns)


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
        if sel == "ns":
            new.append((no, name, q, unit, rate, None, 1))
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
        new.append((no, name, q, unit, rate, iid, 0))
    old = saved_lines(db, b)
    oldk = sorted(_key_of((l["line_no"], l["name"], l["qty"], l["unit"], l["rate"], l["item_id"], l["not_stock"])) for l in old)
    newk = sorted(_key_of(t) for t in new)
    ok, why = paper_counts(db, b)
    nm = len([t for t in new if t[5]])
    if oldk == newk:
        return ["Stationery: unchanged."] if new else []
    first = db.execute("SELECT MIN(ts), MIN(day) FROM stationery_line WHERE bill_id=? AND bill_created_at=?", (b["id"], b["created_at"] or "")).fetchone()
    ts = first[0] if (first and first[0] is not None) else time.time()
    day = first[1] if (first and first[1]) else _today().isoformat()
    now = _now()
    if old:
        db.execute("UPDATE stationery_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (now, who, b["id"], b["created_at"] or ""))
    for no, name, q, unit, rate, iid, ns in sorted(new):
        db.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at) "
                   "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (b["id"], b["created_at"] or "", no, name, q, unit, rate, iid, ns, day, ts, who, now))
    _audit(db, "stationery_lines", {"bill": b["id"], "lines": len(new), "matched": nm, "replaced": len(old), "new_items": made})
    msg = ("Stationery: %d line%s matched" % (nm, "" if nm == 1 else "s")) + (" (%d new on the list)" % made if made else "")
    if nm:
        msg += " — into the stock." if ok else " — not added to the stock: %s." % why
    else:
        msg += "."
    if old:
        msg += " Its earlier lines are replaced, never counted twice."
    return [msg]


def void_lines(db, b, who=None, why=""):
    """The paper's live lines voided (kept) -- a re-save that takes it out of Stationery & packaging. No commit."""
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
        raise ValueError("Kisko diya — Lab, Reception, Sanjeevni ya Clinic chuno.")
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


def inventory(db, ym):
    """The owner's page: one row per item, this month's issues, counts and the papers that fed the stock."""
    items = item_rows(db)
    book = stock_book(db)
    recv = received_rows(db)
    try:
        allines = [dict(r) for r in db.execute("SELECT l.*, b.stamp_no AS stamp " + _JOIN + " WHERE l.voided_at='' AND l.item_id IS NOT NULL "
                                               "AND l.rate IS NOT NULL AND b.dup_of IS NULL ORDER BY l.ts, l.id")]
        issues = [dict(r) for r in db.execute("SELECT * FROM stationery_move WHERE voided_at='' AND substr(day,1,7)=? ORDER BY ts, id", (ym,))]
        counts = [dict(r) for r in db.execute("SELECT * FROM stationery_count WHERE substr(day,1,7)=? ORDER BY ts, id", (ym,))]
    except sqlite3.Error:
        allines, issues, counts = [], [], []
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
                     "used": item_used(db, i)})
    iss = [{"day": x["day"], "item": (byid.get(x["item_id"]) or {}).get("name", "?"), "unit": (byid.get(x["item_id"]) or {}).get("unit", ""),
            "qty": x["qty"], "place": PLACE_WORD.get(x["place"], x["place"]), "who": x["by_whom"] or "",
            "over": (x["stock_before"] is not None and x["qty"] > x["stock_before"] + 1e-9), "before": x["stock_before"]} for x in issues]
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
    return {"rows": rows, "issues": iss, "counts": cts, "fed": sorted(fed.values(), key=lambda f: f["bid"]), "mixed": mixed_n(db, ym)}


# ---------------------------------------------------------------------------------------------- the pages
OFF_LINE = "Yeh page abhi band hai — Dr Manoj chalu karenge."

STOCK_TPL = """<h2 style="margin-bottom:4px">Stationery &amp; packaging — the stock</h2>
<p class=muted style="margin-top:0">{{label}} · general stationery tracked by quantity. Received comes from the challans, bills and estimate slips matched on the sorting desk (each paper once); issued from <a href="{{url_for('s568_issue')}}">Stationery diya</a>.</p>
<div class=card id=s568mixed><b>Mixed challans this month: {{inv.mixed}}</b> <span class=muted>— clinic and lab items on one paper; raise it with the supplier.</span></div>
<div class=card style="overflow:auto"><table id=s568inv><tr><th>Item</th><th>In stock</th><th>Received this month</th><th>Issued this month (Lab · Reception · Sanjeevni · Clinic)</th><th>Last rate paid</th><th>Agreed rate</th><th>Low at</th></tr>
{% for r in inv.rows if r.active %}<tr data-item="{{r.id}}"><td><b>{{r.name}}</b> <span class=muted>({{r.unit}})</span>{% if r.is_low %} <span class="badge amber" id=s568low{{r.id}}>low stock</span>{% endif %}{% if r.over %} <span class="badge amber">issued above stock</span>{% endif %}</td>
<td class=s568stock>{{q(r.stock)}}</td><td>{{q(r.recv)}}</td><td>{% for k, w in places %}{{q(r.by_place[k])}}{{' · ' if not loop.last}}{% endfor %}</td>
<td>{{rs(r.last_rate) if r.last_rate is not none else '—'}}{% if r.last_stamp %} <span class=muted>({{r.last_stamp}})</span>{% endif %}</td><td>{{rs(r.rate) if r.rate is not none else '—'}}</td><td>{{q(r.low) if r.low is not none else '—'}}</td></tr>{% endfor %}
{% if not active_n %}<tr><td colspan=7 class=muted>No item on the list yet — add one below, or “Add to the list” from a challan line on the sorting desk.</td></tr>{% endif %}</table></div>
<div class=card><b>Count</b> <span class=muted>— type what is on the shelf for any items (leave the rest empty). The first count of an item is its opening stock; a later count records any difference as “not accounted for” and sets the stock to the count.</span>
<form method=post action="{{url_for('s568_count')}}" style="margin-top:8px"><input type=hidden name=back value=stock>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:6px 14px">{% for r in inv.rows if r.active %}<label style="margin:0">{{r.name}} <span class=muted>({{r.unit}})</span><input name="c{{r.id}}" inputmode=decimal style="max-width:120px"></label>{% endfor %}</div>
<button class="btn small" style="margin-top:8px">Save the count</button></form></div>
<div class=card><b>This month's issues</b>{% if inv.issues %}<table><tr><th>Day</th><th>Item</th><th>Quantity</th><th>To</th><th>By</th><th></th></tr>
{% for x in inv.issues %}<tr><td>{{dmy(x.day)}}</td><td>{{x.item}}</td><td>{{q(x.qty)}} {{x.unit}}</td><td>{{x.place}}</td><td class=muted>{{x.who}}</td><td>{% if x.over %}<span class="badge amber">above stock ({{q(x.before)}} then)</span>{% endif %}</td></tr>{% endfor %}</table>{% else %}<p class=muted>None yet.</p>{% endif %}</div>
<div class=card><b>Counts this month</b>{% if inv.counts %}<table><tr><th>Day</th><th>Item</th><th>Counted</th><th></th><th>By</th></tr>
{% for x in inv.counts %}<tr><td>{{dmy(x.day)}}</td><td>{{x.item}}</td><td>{{q(x.counted)}} {{x.unit}}</td><td>{% if x.opening %}opening stock{% elif x.diff and (x.diff|abs) > 0.0001 %}not accounted for: {{q(x.diff)}} {{x.unit}}{% else %}matches the stock{% endif %}</td><td class=muted>{{x.who}}</td></tr>{% endfor %}</table>{% else %}<p class=muted>None this month.</p>{% endif %}</div>
<div class=card><b>The papers that fed the stock this month</b>{% if inv.fed %}<ul style="margin:6px 0 0">{% for f in inv.fed %}<li><a href="{{href(f.bid)}}">{{f.stamp}}</a> · {{f.vendor or 'supplier not read'}} · {{f.kind}} · {{f.n}} line{{'' if f.n==1 else 's'}}</li>{% endfor %}</ul>{% else %}<p class=muted>None this month.</p>{% endif %}</div>
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
<button class="btn s568save">Save</button></form></div>
<div class=card><b>Ginti</b> <span class=muted>— shelf par kitna hai, likho (baaki khaali chhodo).</span>
<form method=post action="{{url_for('s568_count')}}" style="margin-top:8px"><input type=hidden name=back value=diya>
<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:6px 14px">{% for i in items %}<label style="margin:0">{{i.name}} <span class=muted>({{i.unit}})</span><input name="c{{i.id}}" inputmode=decimal style="max-width:110px"></label>{% endfor %}</div>
<button class="btn small" style="margin-top:8px">Ginti save karo</button></form></div>{% endif %}"""


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
    return AR.page(STOCK_TPL, inv=inv, label=AR._month_label(ym), places=PLACES, units=UNITS, q=lambda x: _plain(x) if x is not None else "—",
                   rs=rs, plain=_plain, href=_href, dmy=_dmy, active_n=len([r for r in inv["rows"] if r["active"]]),
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
        return redirect(url_for("s568_issue"))
    return AR.page(DIYA_TPL, ok=ok, off=OFF_LINE, items=item_rows(db, active_only=True), places=PLACES,
                   flow=AR._flow("Stationery diya", url_for("s568_stock") if _role() == "owner" else url_for("dashboard")))


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


def menu_items(role):
    """For the scan app's one menu (asset_register._s559_items): the owner's Stationery page; a manager's Stationery diya
    while the switch is ON. Nothing for anyone else."""
    try:
        if role == "owner":
            return [("s568_stock", "Stationery", url_for("s568_stock"))]
        if role == "manager" and issue_on(AR.get_db()):
            return [("s568_issue", "Stationery diya", url_for("s568_issue"))]
    except Exception:                                                # noqa: BLE001
        pass
    return []


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
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data step:  python3 stationery.py --ensure <assets.db>
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        print("stationery %s: tables ready (%s)" % (VERSION, ", ".join(ensure_path(sys.argv[2]))))
    else:
        print(__doc__)
