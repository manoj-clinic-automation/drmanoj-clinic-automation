#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""procroom.py -- S634_PROCROOM_LIST (D773 Kit 1; the owner's "okay to start", 08:31 IST 23-Oct-2026, on the S345 mock-ups),
with S635_PROCROOM_ORDERS (D773 Kit 2; the owner's "start", 20:55 IST 24-Oct-2026): his order, order <-> delivery, the month end.

S635 -- KIT 2 (the S342 plan C 3-4; the S345 mock-up artboard 4)
    HIS ORDER: on the desk, a Procedure room paper may be marked "Dr Manoj's order" (his signed duplicate-book page) -- its lines
    are kept but COUNT NOTHING (proc_paper.role = 'order'); the slip that comes against it counts. A delivery slip is joined to its
    order on the desk (pre-chosen: the newest order before it, within 14 days, not yet delivered); one tap fills its lines from the
    order (he corrects). His page: an order with no delivery after proc.await_days (default 3) days is AWAITING; a slip with no order
    -- only papers scanned from the install on (procroom.orders_from, written by the installer; older slips are never flagged).
    THE MONTH END (his only): /procroom/month -- Yuvika's WhatsApp photos added (kept as the month's bill, beside the scans, never
    deleted), each read by the scan app's own reader (claude_reader.read, unchanged) in the background, matched to its scan and that
    scan's order; the flags: not scanned · quantities differ · rate up / down against the last · the month's total to pay. His Save
    of one photo puts his rates on the scan's lines (or its lines and rates, replacing them, when he corrected them), or -- not
    scanned -- makes a photo slip. A photo removed is kept (struck), and the slip it made is voided. No rupee on any staff screen.

THE OWNER'S RULINGS (D773, S342, 23-Oct-2026)
    The procedure-room goods have ONE product list, his: add, rename, retire, "rarely used"; a product is named by what it is and
    its size; the brand rides on each purchase line; spellings the reader produces map to it by alias. Every line of a slip has its
    own place: Procedure room · Home use (Dr MK) · Clinic equipment · OT (surgery cases, out of the procedure-room totals) ·
    Sanjeevni (orthotics -- moved there and flagged for him). Rates are HIS ONLY: never on a staff screen. History from April 2026
    (expense only) is entered from his WhatsApp photos.

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded hook at its foot: if this file is absent or cannot load,
    the app runs exactly as before (the desk's Procedure room panel and the menu item then show nothing). Its tables come from its
    own ensure(db) (additive, idempotent):
        proc_item   the product list -- name, unit, how it is counted (per patient / month-end match / allowance), state (active /
                    rare / retired), brands, other spellings, reorder level, order on the list
        proc_slip   a slip with no scan on the desk (his WhatsApp photo) -- day, supplier, a note; voided, never deleted
        proc_line   one line of a paper (desk Save, SNAPSHOTS keyed on bill id + created_at, never on bill_items.id) or of a photo
                    slip -- product (or the name only, for a line kept elsewhere), brand, quantity, unit, PLACE, the rate read from
                    the paper (rate_read) and HIS rate (rate); a re-save voids the paper's old lines (kept) and writes the new ones
    Bought is COMPUTED WHEN READ (stationery.py's rule, S568 FIX1, with the group 'procedure'): a paper's line counts only while
    the paper is a live paper in Procedure room (the clinic lane, the group procedure) or a challan / estimate joined into one; a
    bill only when no challan / estimate is joined into it. A photo slip's line counts while the slip is not voided.
    Settings (the owner's, edited on his page): proc.gloves_cast (pairs a cast or slab, default 2), proc.gloves_ili (a pair an ILI,
    default 1), proc.gloves_box (pairs in a box; unset until he says).
    Addresses (the /scanapp prefix is added by the app's middleware), all the OWNER's:
        GET  /procroom              his page: worth a look, by product, by month (the financial year), elsewhere, the slips with
                                    their rates, + a slip from a photo, rarely used and retired, the list and the allowances
        POST /procroom/item         the list: add, edit, rare, retire, bring back (a product with lines is never deleted)
        POST /procroom/slip         a slip from a photo -- or its lines onto a scanned paper (B-xxxx) when the scan is on the desk
        POST /procroom/rates        his rates on one slip's lines
        POST /procroom/void         a photo slip voided (kept, struck through)
        POST /procroom/allow        the allowances
    The desk (sorting_desk.py) calls panel() / save_lines() / void_lines() for a paper in Procedure room. Its panel carries NO rate.
    S635 (Kit 2) adds: GET /procroom/month (the month end) . POST /procroom/month/photos . GET /procroom/month/photo/<id> .
    POST /procroom/month/check . POST /procroom/month/remove . POST /procroom/month/read -- all the OWNER's. Kit 3 (Shavez's
    next-morning screen, use and stock) follows.
"""
import datetime
import json
import math
import re
import sqlite3
import sys
import time

import os
import hashlib
import threading

from flask import abort, flash, g, redirect, request, send_file, url_for

VERSION = "S635"
KIT1 = "S634"
ORDERS_FROM_KEY = "procroom.orders_from"   # S635: the install moment (UTC, as bills.created_at); a slip scanned before it is never "no order"
AWAIT_KEY = "proc.await_days"              # S635: an order with no delivery after this many days is "awaiting" (his; default 3)
AWAIT_DAYS = 3
SUGGEST_DAYS = 14                          # a slip is pre-joined only to an order at most this many days before it
PHOTO_EXT = ("jpg", "jpeg", "png", "webp", "pdf")
PHOTO_MAX = 15 * 1024 * 1024
PHOTO_DIR = "procroom_month"               # under the app's uploads folder
AR = None                     # the asset app's module, handed in by init()
TODAY = None                  # the walk sets a made-up day here
MOUNTED = False
SEED_KEY = "procroom.seed_s634"
PLACES = (("proc", "Procedure room"), ("home", "Home use (Dr MK)"), ("equip", "Clinic equipment"), ("ot", "OT (surgery cases)"),
          ("sanj", "Sanjeevni (orthotics)"))
PLACE_WORD = dict(PLACES)
HOW = (("patient", "per patient"), ("match", "month-end match"), ("allowance", "allowance"))
HOW_WORD = dict(HOW)
STATES = (("active", "in use"), ("rare", "rarely used"), ("retired", "retired"))
STATE_WORD = dict(STATES)
UNITS = ("roll", "metre", "bottle", "box", "pack", "vial", "piece", "pair")
ORTHO = ("spica", "immobiliser", "immobilizer", "brace", "splint", "collar", "knee cap", "kneecap", "orthosis", "sling", "lumbo sacral",
         "ls belt", "lumbar belt", "abdominal belt", "cervical", "arm pouch", "pouch arm", "wrist binder", "knee binder", "clavicle")
SUPPLIER = "Yuvika Surgicals"
ALLOW = (("proc.gloves_cast", "2"), ("proc.gloves_ili", "1"), ("proc.gloves_box", ""), ("proc.await_days", "3"))
# The S342 table A, the owner's names (23-Oct-2026) -- (name, unit, how, state, brands, other spellings). Primecast is a fibre-cast
# brand, retired: its few left go under Fibrecast of that size (no product of its own).
SEED = (
    ('Fibrecast bandage 5"', "roll", "patient", "active", "Gloster, Duracast, Primecast", "fiber 5, fibre 5, gloster 5, duracast 5, primecast 5, prime 5, glostein 5, fibre cast 5"),
    ('Fibrecast bandage 4"', "roll", "patient", "active", "Gloster, Duracast, Primecast", "fiber 4, fibre 4, gloster 4, duracast 4, primecast 4, prime 4, glostein 4, fibre cast 4"),
    ('Fibrecast bandage 3"', "roll", "patient", "active", "Gloster, Duracast, Primecast", "fiber 3, fibre 3, gloster 3, duracast 3, primecast 3, prime 3, glostein 3, fibre cast 3"),
    ('Fibrecast bandage 2"', "roll", "patient", "active", "Gloster, Duracast, Primecast", "fiber 2, fibre 2, gloster 2, duracast 2, primecast 2, prime 2, glostein 2, fibre cast 2"),
    ('Stockinette 3"', "metre", "match", "active", "", "stockinett 3, stockinette roll 3, stockinette 3"),
    ('Stockinette 2"', "metre", "match", "active", "", "stockinett 2, stockinette roll 2, stockinette 2"),
    ("Histocalamine lotion 60 ml", "bottle", "match", "active", "", "histocalamine, histocal, histocalamine lotion"),
    ("Examination gloves", "box", "allowance", "active", "RMS", "examination gloves, exam gloves"),
    ("Rubber sheet", "piece", "match", "active", "", "rubber sheet, rubber sheets"),
    ('Roller bandage 6"', "roll", "patient", "active", "Dyna", "bandage 6, roller bandage 6, 13 cm 4 m, 13cm 4m, 13cm 4 mt, 13 cm 4 mt, 13cm 4 m"),
    ('Roller bandage 4"', "roll", "patient", "active", "", "bandage 4, roller bandage 4"),
    ('Cast padding 4"', "roll", "patient", "active", "Sofroll", "sofroll 4, soft roll 4, soffroll 4, cast padding 4"),
    ('Cast padding 6"', "roll", "patient", "active", "Sofroll", "sofroll 6, soft roll 6, soffroll 6, cast padding 6"),
    ('Elastoplast 4"', "roll", "match", "active", "", "elastoplast 4, elastoplast"),
    ('Surgical tape roll 2"', "roll", "match", "active", "Steripore", "steripore 2, steripore, tape roll, surgical tape"),
    ("Lox 2% with adrenaline (vial)", "vial", "match", "active", "", "lox adr, lox adrenaline, lox 2 adrenaline, lox with adrenaline"),
    ("Anawin (vial)", "vial", "match", "active", "", "anawin"),
    ("Lox 2% (vial)", "vial", "match", "active", "", "lox 2, lox 2 vial"),
    ("Zig-zag cotton 500 g", "pack", "match", "active", "", "zig zag, zigzag, zig zag cotton"),
    ("Betadine lotion", "bottle", "match", "active", "", "betadine lotion"),
    ("Betadine scrub", "bottle", "match", "active", "", "betadine scrub"),
    ("Savlon", "bottle", "match", "active", "", "savlon"),
    ("Surgical blade No. 23", "piece", "match", "active", "Glassvan, Easy Glide", "blade 23, glassvan 23, glass von 23, glassvan, easy glide"),
    ("POP powder", "pack", "match", "rare", "", "pop powder, plaster powder"),
    ("Surgiwear D600 drape", "piece", "patient", "active", "Surgiwear", "d600, minor drape plain d600, minor drape"),
    ("Plain towel drape D3031", "piece", "match", "active", "", "d3031, d303, plain towel"),
    ("Ethilon 2-0", "piece", "match", "active", "", "ethilon 2 0, ethilon"),
    ('Gypsona 4"', "roll", "patient", "rare", "", "gypsona 4, gipsona 4"),
    ('Gypsona 6"', "roll", "patient", "rare", "", "gypsona 6, gipsona 6"),
    ("Gauze than (9 m)", "piece", "match", "active", "", "gauze than, gauze"),
)

DDL = (
    "CREATE TABLE IF NOT EXISTS proc_item(id INTEGER PRIMARY KEY, name TEXT NOT NULL, unit TEXT NOT NULL DEFAULT 'piece', "
    "how TEXT NOT NULL DEFAULT 'match', state TEXT NOT NULL DEFAULT 'active', brands TEXT NOT NULL DEFAULT '', "
    "aliases TEXT NOT NULL DEFAULT '', reorder REAL, sort INTEGER NOT NULL DEFAULT 0, made_by TEXT, made_at TEXT)",
    "CREATE TABLE IF NOT EXISTS proc_slip(id INTEGER PRIMARY KEY, day TEXT NOT NULL, supplier TEXT NOT NULL DEFAULT '', "
    "note TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE TABLE IF NOT EXISTS proc_line(id INTEGER PRIMARY KEY, bill_id INTEGER, bill_created_at TEXT NOT NULL DEFAULT '', "
    "slip_id INTEGER, line_no INTEGER NOT NULL, name TEXT NOT NULL DEFAULT '', brand TEXT NOT NULL DEFAULT '', qty REAL, "
    "unit TEXT NOT NULL DEFAULT '', item_id INTEGER, ask INTEGER NOT NULL DEFAULT 0, place TEXT NOT NULL DEFAULT 'proc', "
    "rate_read REAL, rate REAL, rate_by TEXT NOT NULL DEFAULT '', day TEXT NOT NULL, ts REAL NOT NULL, by_whom TEXT, at TEXT, "
    "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE INDEX IF NOT EXISTS proc_line_bill ON proc_line(bill_id)",
    "CREATE INDEX IF NOT EXISTS proc_line_slip ON proc_line(slip_id)",
    # S635: a paper's role in Procedure room -- 'order' (his order: counts nothing) or 'slip' (a delivery; joined to its order)
    "CREATE TABLE IF NOT EXISTS proc_paper(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, bill_created_at TEXT NOT NULL DEFAULT '', "
    "role TEXT NOT NULL DEFAULT 'slip', order_bill_id INTEGER, order_created_at TEXT NOT NULL DEFAULT '', book_no TEXT NOT NULL DEFAULT '', "
    "by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE INDEX IF NOT EXISTS proc_paper_bill ON proc_paper(bill_id)",
    # S635: the month end -- Yuvika's WhatsApp photos, kept as the month's bill; each read, matched, checked by him
    "CREATE TABLE IF NOT EXISTS proc_photo(id INTEGER PRIMARY KEY, ym TEXT NOT NULL, stored TEXT NOT NULL, orig_name TEXT NOT NULL DEFAULT '', "
    "md5 TEXT NOT NULL DEFAULT '', bytes INTEGER, by_whom TEXT, at TEXT, read_state TEXT NOT NULL DEFAULT 'waiting', read_json TEXT, "
    "read_at TEXT, read_error TEXT NOT NULL DEFAULT '', slip_day TEXT NOT NULL DEFAULT '', bill_id INTEGER, bill_created_at TEXT NOT NULL DEFAULT '', "
    "slip_id INTEGER, checked_at TEXT NOT NULL DEFAULT '', checked_by TEXT NOT NULL DEFAULT '', diffs TEXT NOT NULL DEFAULT '', "
    "voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
)
TABLES = ("proc_item", "proc_slip", "proc_line", "proc_paper", "proc_photo")


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
    """As stationery.ensure_at_mount: 'database is locked' is retried briefly, then left to the installer's data step."""
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
    print("procroom: the database stayed locked at mount; its tables are left to the installer's data step", file=sys.stderr)
    return False


def ensure_path(db_path):
    con = sqlite3.connect(db_path, timeout=20)
    try:
        ensure(con)
    finally:
        con.close()
    return TABLES


def seed_step(db_path, out=print):
    """The installer's data step: the owner's list (S342 table A), once. ONE transaction with its done-key, checked first; a product
    already on the list by name (normalised) is left as it is. Returns 0."""
    con = sqlite3.connect(db_path, timeout=30)
    con.row_factory = sqlite3.Row
    con.isolation_level = None
    try:
        ensure(con)
        con.execute("BEGIN IMMEDIATE")
        if _setting(con, SEED_KEY, None) is not None:
            out("seed: already done (%s is set) -- nothing written" % SEED_KEY)
            con.execute("ROLLBACK")
            return 0
        have = {norm(r["name"]) for r in con.execute("SELECT name FROM proc_item")}
        at = _now()
        wrote = 0
        for k, (name, unit, how, state, brands, aliases) in enumerate(SEED, 1):
            if norm(name) in have:
                out("seed: already on the list -- %s" % name)
                continue
            con.execute("INSERT INTO proc_item(name, unit, how, state, brands, aliases, reorder, sort, made_by, made_at) VALUES(?,?,?,?,?,?,NULL,?,?,?)",
                        (name, unit, how, state, brands, aliases, k * 10, "the owner's list (S342)", at))
            wrote += 1
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (SEED_KEY, "%d products %s" % (wrote, at)))
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                        (at, "installer S634", "procroom_seed_s634", json.dumps({"products": wrote})))
        except sqlite3.Error:
            pass
        con.execute("COMMIT")
        out("seed: %d product(s) written; %s set" % (wrote, SEED_KEY))
        return 0
    except Exception:
        if con.in_transaction:
            con.execute("ROLLBACK")
        raise
    finally:
        con.close()


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


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def _clean(s, n):
    return re.sub(r"\s+", " ", str(s or "")).strip()[:n]


def _audit(db, action, detail):
    """Into the desk's own book (desk_audit, sorting_desk's table); fail-soft when it is absent."""
    try:
        db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                   (_now(), _who(), action, json.dumps(detail or {}, ensure_ascii=False)[:500]))
    except sqlite3.Error:
        pass


def _dmy(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10]).strftime("%d-%m-%Y")
    except Exception:                                                # noqa: BLE001
        return s or ""


def _iso_day(s):
    """'23-09-2026', '23/09/2026' or '2026-09-23' -> '2026-09-23'; else None."""
    s = str(s or "").strip()
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s) or None
    try:
        if m:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat()
        m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", s)
        if m:
            return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1))).isoformat()
    except ValueError:
        return None
    return None


def fy_of(day):
    """The financial year (April to March) a day falls in, by its starting year."""
    d = day if isinstance(day, datetime.date) else datetime.date.fromisoformat(str(day)[:10])
    return d.year if d.month >= 4 else d.year - 1


def fy_months(fy, upto=None):
    """['2026-04', ... '2027-03'], cut at `upto` (YYYY-MM) when given."""
    out = []
    for k in range(12):
        y, m = fy + (3 + k) // 12, (3 + k) % 12 + 1
        ym = "%04d-%02d" % (y, m)
        if upto and ym > upto:
            break
        out.append(ym)
    return out


def is_orthotic(name):
    k = " " + norm(name) + " "
    return any((" " + w + " ") in k for w in ORTHO)


# ---------------------------------------------------------------------------------------------- the list
def item_rows(db, states=None):
    try:
        rows = db.execute("SELECT * FROM proc_item ORDER BY CASE state WHEN 'active' THEN 0 WHEN 'rare' THEN 1 ELSE 2 END, sort, lower(name), id").fetchall()
    except sqlite3.Error:
        return []
    out = [dict(r) for r in rows]
    return [r for r in out if (states is None or r["state"] in states)]


def item_used(db, iid):
    return db.execute("SELECT 1 FROM proc_line WHERE item_id=? LIMIT 1", (iid,)).fetchone() is not None


def _words(s):
    return [w for w in norm(s).split() if w]


def _split(s):
    return [x.strip() for x in re.split(r"[,;\n]", str(s or "")) if x.strip()]


def prematch(name, items):
    """A pre-match (offered, never saved without a person's Save): the product whose name or one of whose other spellings has
    every word inside the line's words -- the one with the most words wins; a tie = no pre-match. Returns (item, brand)."""
    ws = set(_words(name))
    if not ws:
        return None, ""
    best, score, tie = None, 0, False
    for it in items:
        for a in [it["name"]] + _split(it["aliases"]):
            aw = set(_words(a))
            if not aw or not aw <= ws:
                continue
            n = len(aw)
            if n > score:
                best, score, tie = it, n, False
            elif n == score and best is not None and best["id"] != it["id"]:
                tie = True
    if best is None or tie:
        return None, ""
    brand = ""
    for b in _split(best["brands"]):
        if set(_words(b)) and set(_words(b)) <= ws:
            brand = b
            break
    return best, brand


def add_item(db, name, unit="piece", how="match", state="active", brands="", aliases="", reorder=None, who=None):
    """A new product -- or the one of the same name (normalised), never a second one. Returns (id, made). No commit."""
    name = _clean(name, 120)
    if not name:
        raise ValueError("Type the product's name.")
    for it in item_rows(db):
        if norm(it["name"]) == norm(name):
            return it["id"], False
    unit = _clean(unit, 30) or "piece"
    how = how if how in HOW_WORD else "match"
    state = state if state in STATE_WORD else "active"
    srt = (db.execute("SELECT COALESCE(MAX(sort),0) FROM proc_item").fetchone()[0] or 0) + 10
    cur = db.execute("INSERT INTO proc_item(name, unit, how, state, brands, aliases, reorder, sort, made_by, made_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                     (name, unit, how, state, _clean(brands, 200), _clean(aliases, 400), reorder, srt, who if who is not None else _who(), _now()))
    _audit(db, "proc_item_added", {"id": cur.lastrowid, "name": name, "unit": unit, "how": how, "state": state})
    return cur.lastrowid, True


# ---------------------------------------------------------------------------------------------- a paper's lines (the desk)
def _cols(db):
    return {r[1] for r in db.execute("PRAGMA table_info(bills)")}


def _here_sql(a):
    """The paper is in Procedure room NOW -- the clinic lane and the group procedure."""
    return "COALESCE(%s.lane,'clinic')='clinic' AND COALESCE(%s.subgroup,'')='procedure'" % (a, a)


def _paper_sql(db, a="b", here=True):
    """stationery._paper_sql's rules (S568 R1 B2 with K1 CORRECTION 1), for Procedure room: a paper's lines count only while it is
    a live paper there, or a challan / estimate joined into one; a bill only when no challan / estimate is joined into it."""
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


def _not_order_sql(a="b"):
    """S635: the paper is not his order (an order's lines count nothing; the slip that comes against it does)."""
    return ("NOT EXISTS (SELECT 1 FROM proc_paper pp WHERE pp.bill_id=%s.id AND pp.bill_created_at=COALESCE(%s.created_at,'') "
            "AND pp.voided_at='' AND pp.role='order')" % (a, a))


def role_of(db, b):
    """S635: the paper's live role row (dict: role 'order' | 'slip', order_bill_id, order_created_at, book_no) or None."""
    try:
        r = db.execute("SELECT * FROM proc_paper WHERE bill_id=? AND bill_created_at=? AND voided_at='' ORDER BY id DESC LIMIT 1",
                       (b["id"], b["created_at"] or "")).fetchone()
    except sqlite3.Error:
        return None
    return dict(r) if r else None


def is_order(db, b):
    r = role_of(db, b)
    return bool(r and r["role"] == "order")


def paper_counts(db, b, here=True):
    """(True, '') when this paper's lines count now; else (False, why) -- the same rule as the page's read (_paper_sql)."""
    if is_order(db, b):
        return False, "it is Dr Manoj's order — an order counts nothing; the slip that comes against it does"
    try:
        if db.execute("SELECT 1 FROM bills b WHERE b.id=? AND " + _paper_sql(db, "b", here), (b["id"],)).fetchone():
            return True, ""
    except sqlite3.Error:
        return False, "the lines could not be read"
    dk = (b["doc_kind"] or "")
    if b["dup_of"]:
        return False, "a second scan adds nothing"
    if dk in ("receipt", "statement"):
        return False, "a receipt or a statement adds nothing"
    if here and not ((b["lane"] or "clinic") == "clinic" and (b["subgroup"] or "") == "procedure"):
        return False, "it is not in Procedure room now, so its lines add nothing"
    if dk in ("challan", "estimate") and (b["page_of"] or (b["challan_state"] if "challan_state" in b.keys() else "") in ("joined", "deleted")):
        return False, "the paper it is joined into is not in Procedure room now, so its lines add nothing"
    if b["status"] == "rejected" or b["page_of"]:
        return False, "a paper set aside, or a page of another paper, adds nothing"
    if dk not in ("challan", "estimate"):
        return False, "this bill joins a challan or estimate slip — the lines came from that; the bill adds nothing more"
    return False, "its lines add nothing"


def saved_lines(db, b):
    try:
        return [dict(r) for r in db.execute("SELECT * FROM proc_line WHERE bill_id=? AND bill_created_at=? AND voided_at='' ORDER BY line_no, id",
                                            (b["id"], b["created_at"] or ""))]
    except sqlite3.Error:
        return []


def read_lines(db, b, rd):
    """The paper's lines -- Claude's reading (name, qty, unit, rate) when there is one, else the paper's own items."""
    out = []
    if rd and rd.get("items"):
        for i in rd["items"]:
            out.append({"name": _clean(i.get("name"), 120), "qty": _num(i.get("qty")), "unit": _clean(i.get("unit"), 30), "rate": _num(i.get("rate"))})
    else:
        try:
            for r in db.execute("SELECT item_name, quantity, pack_size, rate FROM bill_items WHERE bill_id=? ORDER BY id", (b["id"],)):
                out.append({"name": _clean(r[0], 120), "qty": _num(r[1]), "unit": _clean(r[2], 30), "rate": _num(r[3])})
        except sqlite3.Error:
            pass
    return [x for x in out if x["name"]]


# ---------------------------------------------------------------------------------------------- S635: his orders, the slips against them
def _pday(b):
    """A paper's day: its own date, else the day it was scanned (IST)."""
    d = _iso_day(b["bill_date"]) if ("bill_date" in b.keys() and b["bill_date"]) else None
    if d:
        return d
    try:
        return (datetime.datetime.fromisoformat(str(b["created_at"])[:19]) + datetime.timedelta(minutes=330)).date().isoformat()
    except Exception:                                                # noqa: BLE001
        return ""


def _days(a, b):
    """Days from day a to day b (ISO), or None."""
    try:
        return (datetime.date.fromisoformat(str(b)[:10]) - datetime.date.fromisoformat(str(a)[:10])).days
    except Exception:                                                # noqa: BLE001
        return None


def _stamp(b):
    return b["stamp_no"] or ("#%d" % b["id"])


def _await(db):
    v = _num(_setting(db, AWAIT_KEY, None))
    return int(v) if (v is not None and v >= 0) else AWAIT_DAYS


def _yuv_or_unread(v):
    v = (v or "").strip().lower()
    return (not v) or ("yuvika" in v)


def order_rows(db):
    """Every live order: a live paper in Procedure room marked as his order. Newest first, each with its day (pday) and book no."""
    try:
        rows = db.execute("SELECT b.*, pp.book_no AS book_no FROM proc_paper pp JOIN bills b ON b.id=pp.bill_id "
                          "AND COALESCE(b.created_at,'')=pp.bill_created_at WHERE pp.voided_at='' AND pp.role='order' "
                          "AND b.dup_of IS NULL AND b.status<>'rejected' AND b.page_of IS NULL AND " + _here_sql("b")).fetchall()
    except sqlite3.Error:
        return []
    out = [dict(r) for r in rows]
    for o in out:
        o["pday"] = _pday(o)
    out.sort(key=lambda o: (o["pday"], o["id"]), reverse=True)
    return out


def slips_against(db, o):
    """The live slips (papers whose lines count in Procedure room) joined to this order, oldest first."""
    try:
        rows = db.execute("SELECT b.* FROM proc_paper pp JOIN bills b ON b.id=pp.bill_id AND COALESCE(b.created_at,'')=pp.bill_created_at "
                          "WHERE pp.voided_at='' AND pp.role='slip' AND pp.order_bill_id=? AND pp.order_created_at=? AND "
                          + _paper_sql(db, "b") + " AND " + _not_order_sql("b"), (o["id"], o["created_at"] or "")).fetchall()
    except sqlite3.Error:
        return []
    out = [dict(r) for r in rows]
    for s in out:
        s["pday"] = _pday(s)
    return sorted(out, key=lambda s: (s["pday"], s["id"]))


def _qkey(l):
    return ("i%d" % l["item_id"]) if l.get("item_id") else ("n" + norm(l.get("name")))


def _lname(byid, l):
    return (byid.get(l.get("item_id")) or {}).get("name") or l.get("name") or ""


def order_state(db, o, today=None, await_days=None, byid=None):
    """One order: its lines, the slips against it, and its state -- 'ordered' (younger than the await days), 'awaiting' (no slip
    after them), 'part' (a product came short), 'delivered'; with the differences, product by product (all places)."""
    today = today or _today()
    aw = _await(db) if await_days is None else await_days
    byid = byid if byid is not None else {i["id"]: i for i in item_rows(db)}
    ol, sl = saved_lines(db, o), slips_against(db, o)
    want, got, names = {}, {}, {}
    for l in ol:
        k = _qkey(l)
        want[k] = want.get(k, 0) + (l["qty"] or 0)
        names.setdefault(k, _lname(byid, l))
    for s in sl:
        for l in saved_lines(db, s):
            k = _qkey(l)
            got[k] = got.get(k, 0) + (l["qty"] or 0)
            names.setdefault(k, _lname(byid, l))
    diffs = []
    if sl:
        for k in want:
            if round(got.get(k, 0), 3) != round(want[k], 3):
                diffs.append("%s: ordered %s, came %s" % (names[k], _plain(want[k]), _plain(got.get(k, 0))))
        for k in got:
            if k not in want:
                diffs.append("%s: not on the order, came %s" % (names[k], _plain(got[k])))
    age = _days(o["pday"], today.isoformat())
    if not sl:
        state = "awaiting" if (age is not None and age > aw) else "ordered"
    else:
        state = "part" if any(round(got.get(k, 0), 3) < round(want[k], 3) for k in want) else "delivered"
    return {"id": o["id"], "stamp": _stamp(o), "day": o["pday"], "book": o.get("book_no") or "", "age": age, "state": state,
            "lines": [{"name": _lname(byid, l), "qty": l["qty"], "unit": l["unit"]} for l in ol],
            "slips": [{"id": s["id"], "stamp": _stamp(s), "day": s["pday"]} for s in sl], "diffs": diffs}


def desk_orders(db, b, byid=None):
    """For the desk's panel of a slip: the orders it may come against (live orders from 60 days before its day to 3 after, and the
    one it is joined to), newest first, each with its lines for the fill (NO rate) -- and the suggested one: the newest order at most
    SUGGEST_DAYS before it with no slip against it yet. Returns (orders, their lines, suggested id or None)."""
    byid = byid if byid is not None else {i["id"]: i for i in item_rows(db)}
    day = _pday(b)
    cur = role_of(db, b)
    cur_id = cur["order_bill_id"] if (cur and cur["role"] == "slip") else None
    out, olines, sug = [], {}, None
    for o in order_rows(db):
        if o["id"] == b["id"]:
            continue
        d = _days(o["pday"], day) if day else None
        if o["id"] != cur_id and (d is None or d < -3 or d > 60):
            continue
        ol = saved_lines(db, o)
        done = [s for s in slips_against(db, o) if s["id"] != b["id"]]
        out.append({"id": o["id"], "lab": "%s · %s%s · %d line%s%s" % (_stamp(o), _dmy(o["pday"])[:5],
                                                                      (" · book %s" % o["book_no"]) if o.get("book_no") else "",
                                                                      len(ol), "" if len(ol) == 1 else "s", " · delivered" if done else "")})
        olines[str(o["id"])] = [{"name": _lname(byid, l), "qty": _plain(l["qty"]), "unit": l["unit"], "brand": l["brand"], "place": l["place"],
                                 "item": str(l["item_id"]) if l["item_id"] else ("ask" if l["ask"] else "free")} for l in ol]
        if sug is None and not done and d is not None and 0 <= d <= SUGGEST_DAYS:
            sug = o["id"]
        if len(out) >= 12:
            break
    return out, olines, sug


def _save_role(db, b, extra, who):
    """S635: the paper's role from the desk's Save -- his order (with its book page number), or a slip against one of his orders, or
    a slip with no order. A change voids the old row (kept). Returns the words ('' when nothing changed). Refusals raise ValueError."""
    role = "order" if str(extra.get("pr_role") or "") == "order" else "slip"
    oid, ocr, book, o = None, "", "", None
    if role == "order":
        book = _clean(extra.get("pr_book"), 20)
    else:
        sel = str(extra.get("pr_order") or "").strip()
        if sel:
            o = next((x for x in order_rows(db) if sel.isdigit() and x["id"] == int(sel) and x["id"] != b["id"]), None)
            if o is None:
                raise ValueError("Procedure room: that is not one of Dr Manoj's orders in Procedure room now — choose another, or no order.")
            oid, ocr = o["id"], o["created_at"] or ""
    cur = role_of(db, b)
    if cur and cur["role"] == role and (cur["order_bill_id"] or None) == oid and (cur["book_no"] or "") == book:
        return ""
    if cur is None and role == "slip" and oid is None:
        return ""                                                    # a slip with no order and nothing before: nothing to keep
    now = _now()
    if cur:
        db.execute("UPDATE proc_paper SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (now, who, b["id"], b["created_at"] or ""))
    if role == "order" or oid is not None:
        db.execute("INSERT INTO proc_paper(bill_id, bill_created_at, role, order_bill_id, order_created_at, book_no, by_whom, at) VALUES(?,?,?,?,?,?,?,?)",
                   (b["id"], b["created_at"] or "", role, oid, ocr, book, who, now))
    _audit(db, "proc_paper_role", {"bill": b["id"], "role": role, "order": oid, "book": book, "was": (cur or {}).get("role")})
    if role == "order":
        return "Marked as Dr Manoj's order%s." % ((" (book page %s)" % book) if book else "")
    if oid is not None:
        return "Joined to order %s." % _stamp(o)
    return "No order now."


def _item_view(i):
    return {"id": i["id"], "name": i["name"] + (" (retired)" if i["state"] == "retired" else ""), "unit": i["unit"],
            "brands": _split(i["brands"]), "rare": i["state"] == "rare"}


def panel(db, b, rd, owner=False):
    """The desk's Procedure room panel for one paper: its lines (the saved snapshot first, else the read line with a pre-match and
    a place -- an orthotic is pre-placed at Sanjeevni and flagged), the products, whether its lines count. NO RATE in it."""
    items = item_rows(db)
    byid = {i["id"]: i for i in items}
    rl = read_lines(db, b, rd)
    saved = {}
    for s in saved_lines(db, b):
        saved.setdefault(s["line_no"], s)
    held = {s["item_id"] for s in saved.values() if s["item_id"]}
    usable = [i for i in items if i["state"] in ("active", "rare") or i["id"] in held]
    n = max([len(rl)] + list(saved.keys())) if (rl or saved) else 0
    lines = []
    for k in range(1, n + 1):
        s, r = saved.get(k), (rl[k - 1] if k - 1 < len(rl) else None)
        if s is not None:
            it = byid.get(s["item_id"]) if s["item_id"] else None
            sel = str(s["item_id"]) if s["item_id"] else ("ask" if s["ask"] else "free")
            lines.append({"no": k, "name": s["name"], "qty": _plain(s["qty"]), "unit": s["unit"] or (it["unit"] if it else ""),
                          "brand": s["brand"], "place": s["place"], "item": sel, "saved": True, "sug": False, "hand": r is None,
                          "orth": s["place"] == "sanj"})
        elif r is not None:
            it, br = prematch(r["name"], usable)
            orth = is_orthotic(r["name"]) and it is None
            lines.append({"no": k, "name": r["name"], "qty": _plain(r["qty"]), "unit": r["unit"] or (it["unit"] if it else ""),
                          "brand": br, "place": "sanj" if orth else "proc", "item": (str(it["id"]) if it else ("free" if orth else "")),
                          "saved": False, "sug": bool(it) or orth, "hand": False, "orth": orth})
    noread = not rl and not saved
    # S635: his order, or the order this slip comes against (pre-chosen: the newest open one just before it)
    r = role_of(db, b)
    role = r["role"] if r else "slip"
    ords, olines, sug = desk_orders(db, b, byid) if role == "slip" else ([], {}, None)
    if r and role == "slip":
        sel = str(r["order_bill_id"]) if (r["order_bill_id"] and str(r["order_bill_id"]) in olines) else ""
    else:
        sel = str(sug) if (sug and role == "slip") else ""
    filled = False
    if noread and sel and olines.get(sel):                           # nothing read: the system fills the lines from the order -- he corrects
        for k, x in enumerate(olines[sel], 1):
            lines.append(dict(x, no=k, saved=False, sug=True, hand=False, orth=x["place"] == "sanj"))
        filled = True
    elif noread:
        lines.append({"no": 1, "name": "", "qty": "", "unit": "", "brand": "", "place": "proc", "item": "", "saved": False, "sug": False,
                      "hand": True, "orth": False})
    ok, why = paper_counts(db, b, here=False)                       # the panel shows only with Procedure room chosen
    return {"lines": lines, "items": [_item_view(i) for i in usable], "places": [list(p) for p in PLACES], "owner": bool(owner),
            "noread": noread, "counts": ok, "why": why,
            "role": role, "order": sel, "book": (r["book_no"] if (r and role == "order") else ""), "orders": ords, "olines": olines,
            "filled": filled}


def _key_of(t):
    no, name, brand, q, unit, place, iid, ask = t[:8]
    return (no, norm(name), norm(brand), "" if q is None else "%.4f" % q, unit, place, iid or 0, ask)


def save_lines(db, b, lines, who=None, owner=False, extra=None):
    """One desk Save's lines for this paper. An untouched line (no product chosen) is not stored and never blocks the Save. A
    Procedure room line needs a product from the list -- or 'not on the list' (ask: it waits on his page for his list); a line kept
    elsewhere may carry its name only (free). 'new' (the owner only) adds the line's name to the list first. The rate read from
    the paper rides along unseen (rate_read); his own rate on a line that did not change is kept. A re-save REPLACES the paper's
    own lines (the old ones voided and kept). No commit. Returns the Save's words. Refusals raise ValueError (plain words).
    S635: extra = the desk's whole Save; its pr_role ('order' | 'slip'), pr_order (the order's paper id) and pr_book are kept first."""
    who = _who() if who is None else who
    rmsg = _save_role(db, b, extra, who) if (isinstance(extra, dict) and "pr_role" in extra) else ""
    items = {i["id"]: i for i in item_rows(db)}
    new, made, asks, skipped = [], 0, 0, []
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
        name = _clean(x.get("name"), 120)
        brand = _clean(x.get("brand"), 60)
        unit = _clean(x.get("unit"), 30)
        place = str(x.get("place") or "proc").strip()
        if place not in PLACE_WORD:
            raise ValueError("Procedure room line %d: choose where it goes." % no)
        q = _num(x.get("qty"))
        if q is None or q <= 0:
            if x.get("sug") is True:
                skipped.append(no)
                continue                                             # a suggestion nobody touched, no quantity read: counts nothing
            raise ValueError("Procedure room line %d (%s): type the quantity — or leave the line without a product." % (no, name or "no name"))
        iid, ask = None, 0
        if sel == "free":
            if place == "proc":
                raise ValueError("Procedure room line %d (%s): a Procedure room line needs a product from the list — or “Not on the list”." % (no, name or "no name"))
            if not name:
                raise ValueError("Procedure room line %d: type what it is." % no)
        elif sel == "ask":
            if not name:
                raise ValueError("Procedure room line %d: type what it is, for Dr Manoj's list." % no)
            ask = 1
        elif sel == "new":
            if not owner:
                raise ValueError("Procedure room line %d: only Dr Manoj adds to the list — choose “Not on the list”." % no)
            if not name:
                raise ValueError("Procedure room line %d: type the product's name to add it to the list." % no)
            iid, mk = add_item(db, name, unit or "piece", "match", "active", brand, "", None, who)
            made += 1 if mk else 0
            items = {i["id"]: i for i in item_rows(db)}
        else:
            iid = int(sel) if sel.isdigit() else 0
            if iid not in items:
                raise ValueError("Procedure room line %d: that product is not on the list." % no)
            if items[iid]["state"] == "retired" and not any(l["item_id"] == iid and l["line_no"] == no for l in saved_lines(db, b)):
                raise ValueError("Procedure room line %d: %s is retired — Dr Manoj brings it back on his Procedure room page first." % (no, items[iid]["name"]))
            unit = unit or items[iid]["unit"]
        asks += ask
        new.append((no, name, brand, q, unit, place, iid, ask))
    old = saved_lines(db, b)
    oldk = sorted(_key_of((l["line_no"], l["name"], l["brand"], l["qty"], l["unit"], l["place"], l["item_id"], l["ask"])) for l in old)
    newk = sorted(_key_of(t) for t in new)
    sk = (" Line%s %s left out — no quantity read; type it to count %s." % ("" if len(skipped) == 1 else "s", ", ".join(map(str, skipped)),
                                                                         "it" if len(skipped) == 1 else "them")) if skipped else ""
    if oldk == newk:
        if rmsg:
            return ["Procedure room: " + rmsg + (" Its lines unchanged." if (new or skipped) else "") + sk]
        return ["Procedure room: unchanged." + sk] if (new or skipped) else []
    ok, why = paper_counts(db, b)
    first = db.execute("SELECT MIN(ts), MIN(day) FROM proc_line WHERE bill_id=? AND bill_created_at=?", (b["id"], b["created_at"] or "")).fetchone()
    ts = first[0] if (first and first[0] is not None) else time.time()
    day = first[1] if (first and first[1]) else _today().isoformat()
    now = _now()
    reading = read_lines(db, b, _reading_of(db, b))
    keep = {}                                                        # his rate follows a line by its number and its product -- the newest row
    for l in db.execute("SELECT * FROM proc_line WHERE bill_id=? AND bill_created_at=? ORDER BY id",      # of each, so a rate he cleared stays clear
                        (b["id"], b["created_at"] or "")):
        keep[(l["line_no"], l["item_id"] or 0, norm(l["name"]))] = (l["rate"], l["rate_by"])
    if old:
        db.execute("UPDATE proc_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (now, who, b["id"], b["created_at"] or ""))
    for t in sorted(new, key=lambda t: t[0]):
        no, name, brand, q, unit, place, iid, ask = t
        rr = None
        if 0 < no <= len(reading) and norm(reading[no - 1]["name"]) == norm(name):
            rr = reading[no - 1]["rate"]
        rate, rby = keep.get((no, iid or 0, norm(name)), (None, ""))
        db.execute("INSERT INTO proc_line(bill_id, bill_created_at, slip_id, line_no, name, brand, qty, unit, item_id, ask, place, rate_read, rate, rate_by, day, ts, by_whom, at) "
                   "VALUES(?,?,NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (b["id"], b["created_at"] or "", no, name, brand, q, unit, iid, ask, place, rr, rate, rby or "", day, ts, who, now))
    elsewhere = [PLACE_WORD[t[5]] for t in new if t[5] != "proc"]
    _audit(db, "proc_lines", {"bill": b["id"], "lines": len(new), "replaced": len(old), "new_items": made, "asks": asks,
                              "places": sorted(set(t[5] for t in new))})
    n_here = len([t for t in new if t[5] == "proc"])
    msg = "Procedure room: %d line%s saved" % (len(new), "" if len(new) == 1 else "s")
    if elsewhere:
        msg += " (%d in the Procedure room; elsewhere: %s)" % (n_here, ", ".join(sorted(set(elsewhere))))
    msg += "." if ok else " — they add nothing yet: %s." % why
    if made:
        msg += " %d new on the list." % made
    if asks:
        msg += " %d not on the list — waiting for Dr Manoj." % asks
    if any(t[5] == "sanj" for t in new):
        msg += " Orthotics go to Sanjeevni — flagged for Dr Manoj."
    if old:
        msg += " Its earlier lines are replaced, never counted twice."
    if rmsg:
        msg += " " + rmsg
    return [msg + sk]


def _reading_of(db, b):
    """Claude's reading of the paper, as the desk reads it (sorting_desk's own helper), when there is one."""
    try:
        sd = sys.modules.get("sorting_desk")
        if sd is not None and hasattr(sd, "reading"):
            return sd.reading(db, b["id"])
    except Exception:                                                # noqa: BLE001
        pass
    return None


def void_lines(db, b, who=None, why=""):
    """The paper's live lines voided (kept) -- a re-save that takes it out of Procedure room. No commit."""
    who = _who() if who is None else who
    n = db.execute("UPDATE proc_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (_now(), who, b["id"], b["created_at"] or "")).rowcount
    m = 0
    try:                                                             # S635: its role (order / slip against an order) goes with it
        m = db.execute("UPDATE proc_paper SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                       (_now(), who, b["id"], b["created_at"] or "")).rowcount
    except sqlite3.Error:
        pass
    if n or m:
        _audit(db, "proc_lines_voided", {"bill": b["id"], "lines": n, "role": m, "why": why})
    return n + m


def has_lines(db, b):
    return bool(saved_lines(db, b)) or role_of(db, b) is not None


# ---------------------------------------------------------------------------------------------- what counts (read, never stored)
def counted_rows(db):
    """Every line that counts now: a paper's (the paper live in Procedure room -- _paper_sql) and a photo slip's (not voided).
    Each with its day (the paper's date, else the day it was scanned; the slip's day), its source, its paper's stamp."""
    out = []
    try:
        cp = sys.modules.get("clinic_papers")
        mo = cp.MONTH_OF if (cp is not None and hasattr(cp, "MONTH_OF")) else "substr(datetime(b.created_at,'+330 minutes'),1,7)"
        for r in db.execute("SELECT l.*, b.stamp_no AS stamp, b.vendor AS vendor, b.doc_kind AS dk, " + mo + " AS mo, "
                            "CASE WHEN b.bill_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' THEN b.bill_date ELSE substr(datetime(b.created_at,'+330 minutes'),1,10) END AS pday "
                            "FROM proc_line l JOIN bills b ON b.id=l.bill_id AND COALESCE(b.created_at,'')=l.bill_created_at "
                            "WHERE l.voided_at='' AND l.slip_id IS NULL AND " + _paper_sql(db, "b") + " AND " + _not_order_sql("b") + " ORDER BY l.ts, l.id"):
            d = dict(r)
            d["when"] = _iso_day(d["pday"]) or d["day"]
            d["mo"] = d["mo"] or (d["when"] or "")[:7]
            d["src"] = "paper"
            out.append(d)
        for r in db.execute("SELECT l.*, s.day AS sday, s.supplier AS vendor, s.note AS snote FROM proc_line l JOIN proc_slip s ON s.id=l.slip_id "
                            "WHERE l.voided_at='' AND s.voided_at='' ORDER BY s.day, l.slip_id, l.line_no, l.id"):
            d = dict(r)
            d["when"] = d["sday"]
            d["mo"] = (d["sday"] or "")[:7]
            d["src"] = "photo"
            d["stamp"] = ""
            out.append(d)
    except sqlite3.Error as ex:
        print("procroom counted_rows: %s" % ex, file=sys.stderr)
    for d in out:
        d["eff"] = d["rate"] if d["rate"] is not None else d["rate_read"]
        d["amt"] = (d["qty"] * d["eff"]) if (d["qty"] is not None and d["eff"] is not None) else None
    out.sort(key=lambda d: (d["when"] or "", d["ts"] or 0, d["id"]))
    return out


def _slip_key(d):
    return ("p%d" % d["bill_id"]) if d["src"] == "paper" else ("s%d" % d["slip_id"])


def owner_view(db, ym=None, fy=None):
    """The owner's page for a month (ym) or a financial year (fy)."""
    today = _today()
    if fy is None and ym is None:
        ym = today.strftime("%Y-%m")
    if ym is not None:
        fy0 = fy_of(datetime.date(int(ym[:4]), int(ym[5:7]), 1))
        inp = lambda d: d == ym                                       # noqa: E731
        label = AR._month_label(ym) if AR is not None else ym
    else:
        fy0 = fy
        months = set(fy_months(fy))
        inp = lambda d: d in months                                   # noqa: E731
        label = "Financial year %d-%02d" % (fy, (fy + 1) % 100)
    items = item_rows(db)
    byid = {i["id"]: i for i in items}
    allrows = counted_rows(db)
    rows = [d for d in allrows if inp(d["mo"])]
    here = [d for d in rows if d["place"] == "proc"]
    prod = []
    for it in items:
        mine = [d for d in here if d["item_id"] == it["id"]]
        hist = [d for d in allrows if d["item_id"] == it["id"] and d["place"] == "proc" and d["eff"] is not None and (d["when"] or "") <= (max([x["when"] for x in rows] or [today.isoformat()]))]
        last = hist[-1] if hist else None
        brands = {}
        for d in hist:
            k = norm(d["brand"]) or "—"
            brands[k] = dict(d, bshow=(brands.get(k) or {}).get("bshow") or d["brand"] or "—")
        if not mine and it["state"] != "active":
            continue
        prod.append({"id": it["id"], "name": it["name"], "unit": it["unit"], "state": it["state"], "how": it["how"],
                     "qty": sum(d["qty"] or 0 for d in mine), "spent": sum(d["amt"] or 0 for d in mine if d["amt"] is not None),
                     "norate": len([d for d in mine if d["eff"] is None]), "n": len(mine),
                     "last": ({"rate": last["eff"], "brand": last["brand"], "when": last["when"]} if last else None),
                     "brands": [{"brand": v["bshow"], "rate": v["eff"], "when": v["when"]} for k, v in sorted(brands.items())]})
    asks = [d for d in here if d["ask"] and not d["item_id"]]
    elsewhere = [d for d in rows if d["place"] != "proc"]
    # by month, the whole financial year of the period
    bym = []
    upto = today.strftime("%Y-%m") if fy_of(today) == fy0 else None
    for m in fy_months(fy0, upto):
        mm = [d for d in allrows if d["mo"] == m]
        slips = {_slip_key(d): d["src"] for d in mm}
        bym.append({"ym": m, "label": (AR._month_label(m) if AR is not None else m), "slips": len(slips),
                    "scanned": len([k for k, v in slips.items() if v == "paper"]), "photo": len([k for k, v in slips.items() if v == "photo"]),
                    "here": sum(d["amt"] or 0 for d in mm if d["place"] == "proc" and d["amt"] is not None),
                    "all": sum(d["amt"] or 0 for d in mm if d["amt"] is not None),
                    "norate": len([d for d in mm if d["eff"] is None])})
    # worth a look
    look = []
    seen = set()
    for d in sorted([x for x in rows if x["place"] == "proc" and x["item_id"] and x["eff"] is not None], key=lambda x: (x["when"] or "", x["id"]), reverse=True):
        k = (d["item_id"], norm(d["brand"]))
        if k in seen:
            continue
        seen.add(k)
        prev = [x for x in allrows if x["item_id"] == d["item_id"] and norm(x["brand"]) == k[1] and x["eff"] is not None and x["place"] == "proc"
                and ((x["when"] or ""), x["id"]) < ((d["when"] or ""), d["id"])]
        if prev and round(prev[-1]["eff"], 2) != round(d["eff"], 2):
            look.append("%s%s on %s — %s, was %s (%s)." % ((byid.get(d["item_id"]) or {}).get("name", d["name"]), (" (%s)" % d["brand"]) if d["brand"] else "",
                                                         _dmy(d["when"]), rs(d["eff"]), rs(prev[-1]["eff"]), _dmy(prev[-1]["when"])))
    sj = [d for d in rows if d["place"] == "sanj"]
    if sj:
        look.append("Orthotics on clinic slips — %d line%s moved to Sanjeevni (%s)." % (len(sj), "" if len(sj) == 1 else "s", ", ".join(sorted({_dmy(d["when"])[:5] for d in sj}))))
    nr = [d for d in rows if d["eff"] is None]
    if nr:
        look.append("%d line%s without a rate yet — add %s under Slips below." % (len(nr), "" if len(nr) == 1 else "s", "it" if len(nr) == 1 else "them"))
    if asks:
        look.append("%d line%s not on your list yet — under “Waiting for your list”." % (len(asks), "" if len(asks) == 1 else "s"))
    # S635: his orders of the period (and any still awaiting), and the slips with no order (scanned from the install on)
    aw = _await(db)
    ords = []
    for o in order_rows(db):
        st = order_state(db, o, today, aw, byid)
        if inp((o["pday"] or "")[:7]) or st["state"] == "awaiting":
            ords.append(st)
    floor = _setting(db, ORDERS_FROM_KEY, None)
    noord, seenb = [], set()
    live_o = {o["id"] for o in order_rows(db)}
    for d in rows:
        if not floor or d["src"] != "paper" or d["bill_id"] in seenb:
            continue
        seenb.add(d["bill_id"])
        b = db.execute("SELECT * FROM bills WHERE id=?", (d["bill_id"],)).fetchone()
        if b is None or (b["created_at"] or "") < floor or not _yuv_or_unread(b["vendor"]):
            continue
        r = role_of(db, b)
        if r and r["role"] == "slip" and r["order_bill_id"] in live_o:
            continue
        noord.append({"id": b["id"], "stamp": _stamp(b), "day": d["when"]})
    twice = []
    try:
        dps = delivery_papers(db)
        tk = taken_scans(db)
        for ph in db.execute("SELECT p.slip_day FROM proc_photo p JOIN proc_slip s ON s.id=p.slip_id WHERE p.voided_at='' AND s.voided_at='' AND p.bill_id IS NULL"):
            sd_ = ph["slip_day"] or ""
            if inp(sd_[:7]) and any(c["pday"] == sd_ and c["id"] not in tk and saved_lines(db, c) for c in dps):
                twice.append(sd_)
    except sqlite3.Error:
        pass
    if twice:
        look.append("%d photo slip%s from the month end ha%s a scan of the same day (%s) — open the month end and choose the scan, so it is counted once."
                    % (len(twice), "" if len(twice) == 1 else "s", "s" if len(twice) == 1 else "ve", ", ".join(_dmy(x)[:5] for x in sorted(twice))))
    awn = [o for o in ords if o["state"] == "awaiting"]
    if awn:
        look.append("%d order%s with no slip after %d days — under Orders and deliveries." % (len(awn), "" if len(awn) == 1 else "s", aw))
    if noord:
        look.append("%d slip%s with no order of yours — under Orders and deliveries." % (len(noord), "" if len(noord) == 1 else "s"))
    # the slips of the period
    slips = {}
    for d in rows:
        k = _slip_key(d)
        s = slips.setdefault(k, {"key": k, "src": d["src"], "when": d["when"], "vendor": d["vendor"] or "", "stamp": d["stamp"] or "",
                                 "bid": d["bill_id"], "sid": d["slip_id"], "note": d.get("snote") or "", "lines": [], "total": 0.0, "norate": 0})
        s["lines"].append({"id": d["id"], "name": (byid.get(d["item_id"]) or {}).get("name") or d["name"], "read": d["name"], "brand": d["brand"],
                           "qty": d["qty"], "unit": d["unit"], "place": PLACE_WORD.get(d["place"], d["place"]), "pk": d["place"],
                           "rate": d["rate"], "rate_read": d["rate_read"], "eff": d["eff"], "amt": d["amt"], "ask": bool(d["ask"] and not d["item_id"])})
        s["total"] += d["amt"] or 0
        s["norate"] += 1 if d["eff"] is None else 0
    slist = sorted(slips.values(), key=lambda s: (s["when"] or "", s["key"]))
    return {"label": label, "ym": ym, "fy": fy0, "is_fy": ym is None, "prod": prod, "asks": asks, "elsewhere": elsewhere, "bym": bym,
            "look": look, "slips": slist, "here_total": sum(d["amt"] or 0 for d in here if d["amt"] is not None),
            "all_total": sum(d["amt"] or 0 for d in rows if d["amt"] is not None), "n_slips": len(slist),
            "photo_only": len([s for s in slist if s["src"] == "photo"]),
            "rare": [i for i in items if i["state"] in ("rare", "retired")], "products": items,
            "orders": ords, "noorder": noord, "await": aw, "floor": floor}


# ---------------------------------------------------------------------------------------------- his writes
def _by_stamp(db, no):
    no = _clean(no, 20).upper()
    if not no:
        return None
    m = re.fullmatch(r"(?:B\s*-?\s*)?(\d{1,6})", no)
    if m:
        no = "B-%04d" % int(m.group(1))
    return db.execute("SELECT * FROM bills WHERE upper(stamp_no)=? AND dup_of IS NULL", (no,)).fetchone()


def add_slip(db, day, supplier, note, lines, paper_no="", who=None, out=None):
    """A slip from his photo -- or, with paper_no, its lines (with his rates) onto that scanned paper in Procedure room (replacing
    its desk lines, the old ones voided and kept). Lines: dicts {item, name, brand, qty, unit, place, rate}. No commit.
    S635: out (a dict) receives the new slip's id ('sid') or the paper's ('bid')."""
    who = _who() if who is None else who
    d = _iso_day(day)
    if not d:
        raise ValueError("Type the slip's date (dd-mm-yyyy).")
    items = {i["id"]: i for i in item_rows(db)}
    got = []
    for k, x in enumerate(lines, 1):
        sel = str(x.get("item") or "").strip()
        name = _clean(x.get("name"), 120)
        q = _num(x.get("qty"))
        if not sel and not name and q is None:
            continue
        place = str(x.get("place") or "proc").strip()
        if place not in PLACE_WORD:
            raise ValueError("Line %d: choose where it goes." % k)
        if q is None or q <= 0:
            raise ValueError("Line %d: type the quantity." % k)
        rate = _num(x.get("rate"))
        if rate is not None and rate < 0:
            raise ValueError("Line %d: the rate cannot be below zero." % k)
        iid, ask = None, 0
        if sel.isdigit() and int(sel) in items:
            iid = int(sel)
            name = name or items[iid]["name"]
        elif sel == "ask":                                           # S635: "not on your list yet" -- kept as it was on the desk
            if not name:
                raise ValueError("Line %d: type what it is (it is not on your list yet)." % k)
            ask = 1
        elif place == "proc":
            raise ValueError("Line %d: a Procedure room line needs a product from your list (add it to the list first)." % k)
        elif not name:
            raise ValueError("Line %d: type what it is." % k)
        unit = _clean(x.get("unit"), 30) or (items[iid]["unit"] if iid else "")
        got.append((name, _clean(x.get("brand"), 60), q, unit, iid, place, rate, ask))
    if not got:
        raise ValueError("Type at least one line.")
    now = _now()
    ts = time.time()
    if paper_no:
        b = _by_stamp(db, paper_no)
        if b is None:
            raise ValueError("There is no paper numbered %s." % _clean(paper_no, 20))
        ok, why = paper_counts(db, b)
        if not ok:
            raise ValueError("%s is not counted in Procedure room now (%s) — sort it on the desk first." % (b["stamp_no"] or "#%d" % b["id"], why))
        n = db.execute("UPDATE proc_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                       (now, who, b["id"], b["created_at"] or "")).rowcount
        for no, (name, brand, q, unit, iid, place, rate, ask) in enumerate(got, 1):
            db.execute("INSERT INTO proc_line(bill_id, bill_created_at, slip_id, line_no, name, brand, qty, unit, item_id, ask, place, rate_read, rate, rate_by, day, ts, by_whom, at) "
                       "VALUES(?,?,NULL,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?)",
                       (b["id"], b["created_at"] or "", no, name, brand, q, unit, iid, ask, place, rate, (who if rate is not None else ""), d, ts, who, now))
        _audit(db, "proc_paper_lines_by_owner", {"bill": b["id"], "lines": len(got), "replaced": n})
        if out is not None:
            out["bid"] = b["id"]
        return "%s: %d line%s saved from the photo%s." % (b["stamp_no"] or "#%d" % b["id"], len(got), "" if len(got) == 1 else "s",
                                                         " (its earlier lines replaced, kept)" if n else "")
    sid = db.execute("INSERT INTO proc_slip(day, supplier, note, by_whom, at) VALUES(?,?,?,?,?)",
                     (d, _clean(supplier, 80) or SUPPLIER, _clean(note, 200), who, now)).lastrowid
    for no, (name, brand, q, unit, iid, place, rate, ask) in enumerate(got, 1):
        db.execute("INSERT INTO proc_line(bill_id, bill_created_at, slip_id, line_no, name, brand, qty, unit, item_id, ask, place, rate_read, rate, rate_by, day, ts, by_whom, at) "
                   "VALUES(NULL,'',?,?,?,?,?,?,?,?,?,NULL,?,?,?,?,?,?)",
                   (sid, no, name, brand, q, unit, iid, ask, place, rate, (who if rate is not None else ""), d, ts, who, now))
    _audit(db, "proc_slip_added", {"slip": sid, "day": d, "lines": len(got)})
    if out is not None:
        out["sid"] = sid
    return "Slip of %s saved — %d line%s." % (_dmy(d), len(got), "" if len(got) == 1 else "s")


def set_rates(db, rates, who=None):
    """{line id: rate or None} -- his rates; a blank clears. Only a live line. No commit. Returns the number changed."""
    who = _who() if who is None else who
    n = 0
    for lid, v in rates.items():
        r = db.execute("SELECT id, rate FROM proc_line WHERE id=? AND voided_at=''", (lid,)).fetchone()
        if r is None:
            continue
        if (r["rate"] is None and v is None) or (r["rate"] is not None and v is not None and round(r["rate"], 4) == round(v, 4)):
            continue
        db.execute("UPDATE proc_line SET rate=?, rate_by=? WHERE id=?", (v, who if v is not None else "", lid))
        _audit(db, "proc_rate", {"line": lid, "from": r["rate"], "to": v})
        n += 1
    return n


def void_slip(db, sid, who=None):
    who = _who() if who is None else who
    n = db.execute("UPDATE proc_slip SET voided_at=?, voided_by=? WHERE id=? AND voided_at=''", (_now(), who, sid)).rowcount
    if n:
        _audit(db, "proc_slip_voided", {"slip": sid})
    return n


# ---------------------------------------------------------------------------------------------- S635: the month end (his only)
NO_THREAD = False                     # the walk reads inline (the reader is off there: nothing is sent anywhere)


def _upload_dir():
    d = os.path.join(AR.UPLOAD_DIR, PHOTO_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def photo_rows(db, ym=None, live=True):
    q = "SELECT * FROM proc_photo WHERE 1=1" + (" AND ym=?" if ym else "") + (" AND voided_at=''" if live else "") + " ORDER BY id"
    try:
        return [dict(r) for r in db.execute(q, (ym,) if ym else ())]
    except sqlite3.Error:
        return []


def _photo(db, pid):
    try:
        r = db.execute("SELECT * FROM proc_photo WHERE id=?", (pid,)).fetchone()
    except sqlite3.Error:
        return None
    return dict(r) if r else None


def add_photos(db, ym, files, who=None):
    """His photos for the month: each kept in the uploads folder (never deleted), one row each; the same bytes are never added twice.
    No commit. Returns (the new ids, the words for the ones not added)."""
    who = _who() if who is None else who
    ids, words = [], []
    have = {r["md5"]: r for r in photo_rows(db, None, True)}
    for f in files:
        name = _clean(os.path.basename(getattr(f, "filename", "") or ""), 120)
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        if not name:
            continue
        if ext not in PHOTO_EXT:
            words.append("%s is not a photo or a PDF (JPG, PNG, WEBP, PDF) — not added." % name)
            continue
        raw = f.read(PHOTO_MAX + 1)
        if not raw:
            words.append("%s is empty — not added." % name)
            continue
        if len(raw) > PHOTO_MAX:
            words.append("%s is over 15 MB — not added." % name)
            continue
        h = hashlib.md5(raw).hexdigest()
        if h in have:
            words.append("%s was added before (%s) — not added again." % (name, _mlabel(have[h]["ym"])))
            continue
        stored = "proc_%s_%s.%s" % (ym, h[:12], ext)
        with open(os.path.join(_upload_dir(), stored), "wb") as fh:
            fh.write(raw)
        cur = db.execute("INSERT INTO proc_photo(ym, stored, orig_name, md5, bytes, by_whom, at, read_state) VALUES(?,?,?,?,?,?,?,'waiting')",
                         (ym, stored, name, h, len(raw), who, _now()))
        ids.append(cur.lastrowid)
        have[h] = {"ym": ym}
    if ids:
        _audit(db, "proc_photos_added", {"ym": ym, "ids": ids})
    return ids, words


def _reader():
    m = sys.modules.get("claude_reader")
    if m is None:
        try:
            import claude_reader as m                                # noqa: PLC0415 -- the scan app's own reader, unchanged
        except Exception:                                            # noqa: BLE001
            return None
    return m


def read_photos(db_path, upload_dir, ids):
    """Each photo read by the scan app's reader (claude_reader.read, unchanged; no paper id, so no paper's reading is touched); the
    reading, or the words why not, onto its row. In the background (a thread). Never raises."""
    cr = _reader()
    for pid in ids:
        con = None
        try:
            con = sqlite3.connect(db_path, timeout=30)
            con.row_factory = sqlite3.Row
            r = con.execute("SELECT * FROM proc_photo WHERE id=?", (pid,)).fetchone()
            if r is None or r["voided_at"]:
                continue
            why = ""
            if cr is None:
                why = "the reader is not on this server"
            else:
                try:
                    st = cr.state(con)
                except Exception:                                    # noqa: BLE001
                    st = "off"
                if st != "on":
                    why = ("the reader has no key on this server" if st == "no key" else
                           "the reader is " + ("off" if st == "off" else st.replace("stopped:", "stopped — ")))
            if why:
                con.execute("UPDATE proc_photo SET read_state='failed', read_error=?, read_at=? WHERE id=?", (why + " — type its lines", _now(), pid))
                con.commit()
                continue
            con.execute("UPDATE proc_photo SET read_state='reading', read_at=? WHERE id=?", (_now(), pid))
            con.commit()
            data = cr.read(os.path.join(upload_dir, r["stored"]), None, db_path)
            if data:
                con.execute("UPDATE proc_photo SET read_state='read', read_json=?, read_error='', read_at=? WHERE id=?",
                            (json.dumps(data, ensure_ascii=False), _now(), pid))
            else:
                con.execute("UPDATE proc_photo SET read_state='failed', read_error=?, read_at=? WHERE id=?",
                            ("it could not be read — type its lines", _now(), pid))
            con.commit()
        except Exception as ex:                                      # noqa: BLE001
            print("procroom read_photos: %s" % ex, file=sys.stderr)
        finally:
            if con is not None:
                con.close()


def start_reading(ids):
    if not ids:
        return
    if NO_THREAD:
        read_photos(AR.DB_PATH, _upload_dir(), ids)
    else:
        threading.Thread(target=read_photos, args=(AR.DB_PATH, _upload_dir(), list(ids)), daemon=True).start()


def _mlabel(ym):
    try:
        return AR._month_label(ym)
    except Exception:                                                # noqa: BLE001
        return ym


def _reading(p):
    try:
        d = json.loads(p["read_json"] or "null")
    except (TypeError, ValueError):
        d = None
    return d if isinstance(d, dict) else None


def photo_lines(rd, usable):
    """A photo's lines as read: name, qty, rate, unit, and the product pre-matched from his list (a suggestion)."""
    out = []
    for i in ((rd or {}).get("items") or []):
        name = _clean(i.get("name"), 120)
        if not name:
            continue
        it, br = prematch(name, usable)
        out.append({"name": name, "qty": _num(i.get("qty")), "rate": _num(i.get("rate")), "unit": _clean(i.get("unit"), 30),
                    "item_id": it["id"] if it else None, "brand": br, "place": "sanj" if (is_orthotic(name) and it is None) else "proc"})
    return out


def delivery_papers(db):
    """The live slips in Procedure room that count (not his orders), Yuvika's or with no supplier read, each with its day."""
    try:
        rows = db.execute("SELECT b.* FROM bills b WHERE " + _paper_sql(db, "b") + " AND " + _not_order_sql("b")).fetchall()
    except sqlite3.Error:
        return []
    out = [dict(r) for r in rows if _yuv_or_unread(r["vendor"])]
    for x in out:
        x["pday"] = _pday(x)
    return out


def taken_scans(db):
    """{scan id: photo id} -- the scans a live photo has been checked onto."""
    try:
        return {r[0]: r[1] for r in db.execute("SELECT bill_id, id FROM proc_photo WHERE voided_at='' AND checked_at<>'' AND bill_id IS NOT NULL")}
    except sqlite3.Error:
        return {}


def match_paper(db, p, rd, cands, byid, taken=None):
    """The scan a photo shows: the one he chose; else the slip of the photo's day (by its number, else the most products in common).
    K1 B2/B3: a scan another photo was already checked onto is offered only when this photo FITS inside it -- every product on the
    photo is on the scan, none in a greater quantity (the same slip again, or the second half of a long one); a different slip of
    the same day is never folded into it."""
    if p["bill_id"]:
        return next((c for c in cands if c["id"] == p["bill_id"]), None)
    day = p["slip_day"] or (rd or {}).get("bill_date") or ""
    same = [c for c in cands if day and c["pday"] == day]
    taken = taken_scans(db) if taken is None else taken
    if any(taken.get(c["id"]) not in (None, p.get("id")) for c in same):
        pl = photo_lines(rd, list(byid.values()))
        same = [c for c in same if taken.get(c["id"]) in (None, p.get("id")) or fits(pl, saved_lines(db, c))]
    if len(same) <= 1:
        return same[0] if same else None
    bn = norm((rd or {}).get("bill_no"))
    for c in same:
        if bn and norm(c.get("bill_no")) == bn:
            return c
    pk = {_qkey(l) for l in photo_lines(rd, list(byid.values()))}
    return max(same, key=lambda c: (len(pk & {_qkey(l) for l in saved_lines(db, c)}), -c["id"]))


def fits(plines, slines):
    """Every product on the photo is on the scan, and none in a greater quantity (K1 B3)."""
    a, b = {}, {}
    for l in plines:
        a[_qkey(l)] = a.get(_qkey(l), 0) + (l["qty"] or 0)
    for l in slines:
        b[_qkey(l)] = b.get(_qkey(l), 0) + (l["qty"] or 0)
    return bool(a) and all(k in b and round(a[k], 3) <= round(b[k], 3) for k in a)


def qty_diffs(plines, slines, byid):
    """The photo's quantities against the scan's lines, product by product (all places): the words for each that differs."""
    a, b, names = {}, {}, {}
    for l in plines:
        k = _qkey(l)
        a[k] = a.get(k, 0) + (l["qty"] or 0)
        names.setdefault(k, _lname(byid, l))
    for l in slines:
        k = _qkey(l)
        b[k] = b.get(k, 0) + (l["qty"] or 0)
        names.setdefault(k, _lname(byid, l))
    out = []
    for k in list(a) + [k for k in b if k not in a]:
        if k not in b:
            out.append("%s: photo %s, not on the scan" % (names[k], _plain(a[k])))
        elif k not in a:
            out.append("%s: scan %s, not on the photo" % (names[k], _plain(b[k])))
        elif round(a[k], 3) != round(b[k], 3):
            out.append("%s: photo %s, scan %s" % (names[k], _plain(a[k]), _plain(b[k])))
    return out


def rate_words(allrows, lines, day, skip_key, byid):
    """Each line's rate against the last rate of that product (and brand, when written) before its day, from other slips: the words
    for each that went up or down."""
    out = []
    for l in lines:
        if not l.get("item_id") or l.get("rate") is None or l.get("place", "proc") != "proc":
            continue
        prev = [x for x in allrows if x["item_id"] == l["item_id"] and x["eff"] is not None and x["place"] == "proc" and _slip_key(x) != skip_key
                and (x["when"] or "") <= (day or "9999") and (not l.get("brand") or norm(x["brand"]) == norm(l["brand"]))]
        if not prev:
            continue
        last = prev[-1]["eff"]
        if round(last, 2) != round(l["rate"], 2):
            out.append("%s %s: %s (was %s)" % (_lname(byid, l), "up" if l["rate"] > last else "down", rs(l["rate"]), rs(last)))
    return out


def month_view(db, ym):
    """The month end for one month: a row per photo (its day, its scan, that scan's order, quantities, rates, amount), the month's
    total to pay, and the scanned slips of the month no photo shows."""
    items = item_rows(db)
    byid = {i["id"]: i for i in items}
    usable = [i for i in items if i["state"] in ("active", "rare")]
    allrows = counted_rows(db)
    cands = delivery_papers(db)
    live_o = {o["id"]: o for o in order_rows(db)}
    floor = _setting(db, ORDERS_FROM_KEY, None)
    try:
        now = datetime.datetime.fromisoformat(str(_now())[:19])      # the same clock the reading times are written with (IST)
    except ValueError:
        now = datetime.datetime.now()
    rows, used, total, reading = [], set(), 0.0, False
    taken = taken_scans(db)
    mine = photo_rows(db, ym)
    progress = any(not _stale(x["read_at"], now) for x in mine if x["read_at"] and x["read_state"] in ("read", "failed", "reading"))
    for p in mine:
        rd = _reading(p)
        c = match_paper(db, p, rd, cands, byid, taken)
        later = None
        if p["slip_id"] and not p["bill_id"]:                        # made a photo slip when not scanned; a scan of that day since?
            later = match_paper(db, dict(p, bill_id=None), rd, cands, byid, taken)
            c = None
        day = p["slip_day"] or (rd or {}).get("bill_date") or (c["pday"] if c else "")
        pl = photo_lines(rd, usable)
        r = role_of(db, c) if c else None
        o = live_o.get(r["order_bill_id"]) if (r and r["role"] == "slip") else None
        key = ("p%d" % c["id"]) if c else (("s%d" % p["slip_id"]) if p["slip_id"] else "")
        now_lines = [d for d in allrows if key and _slip_key(d) == key]
        stale = photo_stale(p, now, progress)
        if p["read_state"] in ("waiting", "reading") and not stale:
            reading = True
        if p["checked_at"]:
            try:
                dd = json.loads(p["diffs"] or "{}")
            except ValueError:
                dd = {}
            qw = dd.get("qty") or []
            amt = sum(d["amt"] or 0 for d in now_lines if d["amt"] is not None)
            rw = rate_words(allrows, [{"item_id": d["item_id"], "rate": d["eff"], "brand": d["brand"], "place": d["place"], "name": d["name"]}
                                      for d in now_lines], day, key, byid)
        else:
            qw = qty_diffs(pl, saved_lines(db, c), byid) if (c and rd) else []
            got = [l["qty"] * l["rate"] for l in pl if l["qty"] is not None and l["rate"] is not None]
            amt = sum(got) if got else (_num((rd or {}).get("total_amount")) if rd else None)
            rw = rate_words(allrows, pl, day, key, byid) if rd else []
        if c:
            used.add(c["id"])
        if later:
            used.add(later["id"])
        rows.append({"id": p["id"], "day": day, "name": p["orig_name"], "state": "stale" if stale else p["read_state"], "error": p["read_error"],
                     "scan": ({"id": c["id"], "stamp": _stamp(c)} if c else None), "later": ({"id": later["id"], "stamp": _stamp(later)} if later else None),
                     "order": ({"id": o["id"], "stamp": _stamp(o)} if o else None),
                     "noorder": bool(c and not o and floor and (c.get("created_at") or "") >= floor),
                     "qty": qw, "rates": rw, "amt": amt, "checked": bool(p["checked_at"]), "slip": p["slip_id"], "nlines": len(pl),
                     "count": True, "same_as": "", "fits": bool(c and rd and fits(pl, saved_lines(db, c)))})
    rows.sort(key=lambda x: (x["day"] or "9999", x["id"]))
    # B1 (K1, S635): a scan is counted ONCE in the month's total. Several photos of one scan: once one of them is checked, the scan's
    # own lines are its amount and the other photos add nothing; while none is checked, the photos' read amounts add up (the parts of
    # one long slip) -- and each later photo says it shows the same scan, so a slip sent twice is seen.
    byscan = {}
    for r in rows:
        if r["scan"]:
            byscan.setdefault(r["scan"]["id"], []).append(r)
    for sid_, rs_ in byscan.items():
        if len(rs_) < 2:
            continue
        chk = [r for r in rs_ if r["checked"]]
        first = chk[0] if chk else rs_[0]
        for r in rs_:
            if r is first:
                continue
            r["same_as"] = dmy_short(first["day"]) or "another photo"
            if chk and (r["checked"] or r["fits"]):                  # K1 B3: never drop a photo that does not fit inside the scan
                r["count"] = False
    total = sum((r["amt"] or 0) for r in rows if r["count"])
    desk_only = sorted([{"id": c["id"], "stamp": _stamp(c), "day": c["pday"]} for c in cands
                        if (c["pday"] or "")[:7] == ym and c["id"] not in used], key=lambda x: (x["day"], x["id"]))
    gone = photo_rows(db, ym, live=False)
    return {"ym": ym, "label": _mlabel(ym), "rows": rows, "total": total, "desk_only": desk_only, "reading": reading,
            "removed": [g_ for g_ in gone if g_["voided_at"]], "n": len(rows)}


def photo_stale(p, now=None, progress=False):
    """A reading that will not finish: 'reading' over 20 minutes (two models, three tries each), or 'waiting' over 10 minutes after it
    was added or asked again -- unless another photo of its month was read in the last 10 minutes (a batch still being worked)."""
    if now is None:
        try:
            now = datetime.datetime.fromisoformat(str(_now())[:19])
        except ValueError:
            now = datetime.datetime.now()
    if p["read_state"] == "reading":
        return _stale(p["read_at"], now, 1200)
    if p["read_state"] == "waiting":
        return (not progress) and _stale(max(str(p["at"] or ""), str(p["read_at"] or "")), now)
    return False


def _stale(at, now, secs=600):
    try:
        return (now - datetime.datetime.fromisoformat(str(at)[:19])).total_seconds() > secs
    except Exception:                                                # noqa: BLE001
        return True


def dmy_short(day):
    return _dmy(day)[:5] if day else ""


def photo_editor(db, p, scan_sel=None):
    """One photo opened: its day, the scans near it to choose from, and its lines -- the chosen scan's own lines with the photo's
    rates beside them (the photo's quantity shown where it differs), or, not scanned, the lines as read."""
    items = item_rows(db)
    byid = {i["id"]: i for i in items}
    usable = [i for i in items if i["state"] in ("active", "rare")]
    rd = _reading(p)
    cands = delivery_papers(db)
    pl = photo_lines(rd, usable)
    auto = match_paper(db, p, rd, cands, byid, taken_scans(db)) if not (p["slip_id"] and not p["bill_id"] and p["checked_at"]) else None
    if scan_sel == "none":
        c = None
    elif scan_sel and str(scan_sel).isdigit():
        c = next((x for x in cands if x["id"] == int(scan_sel)), None)
    else:
        c = auto
    day = p["slip_day"] or (rd or {}).get("bill_date") or (c["pday"] if c else "")
    if day:
        near = [x for x in cands if (_days(x["pday"], day) is not None and abs(_days(x["pday"], day)) <= 7) or (x["pday"] or "")[:7] == p["ym"]]
    else:                                                            # no date read: every scan of the photo's month (K1 C1)
        near = [x for x in cands if (x["pday"] or "")[:7] == p["ym"]]
    if c is not None and all(x["id"] != c["id"] for x in near):
        near.append(c)
    near.sort(key=lambda x: (x["pday"], x["id"]))
    lines = []
    if c is not None and saved_lines(db, c):
        prate = {}
        pqty = {}
        for l in pl:
            prate.setdefault(_qkey(l), l["rate"])
            pqty[_qkey(l)] = pqty.get(_qkey(l), 0) + (l["qty"] or 0)
        for l in saved_lines(db, c):
            k = _qkey(l)
            rate = l["rate"] if l["rate"] is not None else prate.get(k, l["rate_read"])
            hint = ("photo %s" % _plain(pqty[k])) if (k in pqty and round(pqty[k], 3) != round(l["qty"] or 0, 3)) else ("not on the photo" if (pl and k not in pqty) else "")
            lines.append({"lid": l["id"], "item": l["item_id"] or ("ask" if l["ask"] else None), "name": l["name"], "brand": l["brand"],
                          "qty": l["qty"], "place": l["place"], "rate": rate, "hint": hint})
        for l in pl:
            if _qkey(l) not in {_qkey(x) for x in saved_lines(db, c)}:
                lines.append({"lid": None, "item": l["item_id"], "name": l["name"], "brand": l["brand"], "qty": l["qty"], "place": l["place"],
                              "rate": l["rate"], "hint": "on the photo, not on the scan"})
    elif p["slip_id"] and c is None:
        for l in db.execute("SELECT * FROM proc_line WHERE slip_id=? AND voided_at='' ORDER BY line_no", (p["slip_id"],)):
            lines.append({"lid": None, "item": l["item_id"] or ("ask" if l["ask"] else None), "name": l["name"], "brand": l["brand"], "qty": l["qty"], "place": l["place"],
                          "rate": l["rate"], "hint": ""})
    else:
        for l in pl:
            lines.append({"lid": None, "item": l["item_id"], "name": l["name"], "brand": l["brand"], "qty": l["qty"], "place": l["place"],
                          "rate": l["rate"], "hint": ""})
    try:
        now = datetime.datetime.fromisoformat(str(_now())[:19])
    except ValueError:
        now = datetime.datetime.now()
    prog = any(not _stale(x["read_at"], now) for x in photo_rows(db, p["ym"]) if x["read_at"] and x["read_state"] in ("read", "failed", "reading"))
    return {"p": p, "rd": rd, "day": day, "scan": c, "near": near, "lines": lines, "auto": auto, "stale": photo_stale(p, now, prog),
            "products": [i for i in items if i["state"] != "retired" or any(l["item"] == i["id"] for l in lines)]}


def check_photo(db, pid, day, scan_sel, lines, who=None):
    """His Save of one photo. A scan chosen: his rates onto its lines -- or, when he changed a line (product, brand, quantity,
    place, a line added or left out), the lines with his rates replace the scan's (the old ones voided, kept); a photo slip it made
    before is voided (it is scanned now). Not scanned: a photo slip with his lines and rates (the earlier one voided). The quantities
    that differed from the scan are kept with the photo. No commit. Returns the words; refusals raise ValueError."""
    who = _who() if who is None else who
    p = _photo(db, pid)
    if p is None or p["voided_at"]:
        raise ValueError("That photo is not on this month's list.")
    d = _iso_day(day)
    if not d:
        raise ValueError("Type the slip's date (dd-mm-yyyy).")
    items = item_rows(db)
    byid = {i["id"]: i for i in items}
    rd = _reading(p)
    now = _now()
    rows = [x for x in lines if str(x.get("item") or "").strip() or _clean(x.get("name"), 120) or _num(x.get("qty")) is not None]
    if scan_sel and scan_sel != "none":
        b = db.execute("SELECT * FROM bills WHERE id=?", (int(scan_sel) if str(scan_sel).isdigit() else 0,)).fetchone()
        if b is None:
            raise ValueError("That scan is not on the desk.")
        ok, why = paper_counts(db, b)
        if not ok:
            raise ValueError("%s is not counted in Procedure room now (%s) — sort it on the desk first, or choose “not scanned”." % (_stamp(b), why))
        if not (b["stamp_no"] or "").strip():
            raise ValueError("That scan has no stamp number — open it on the desk first.")
        old = saved_lines(db, b)
        qd = qty_diffs(photo_lines(rd, list(byid.values())), old, byid) if rd else []
        om = {l["id"]: l for l in old}
        same = len(rows) == len(old) and all(str(x.get("lid") or "").isdigit() and int(x["lid"]) in om for x in rows)
        if same:
            for x in rows:
                l = om[int(x["lid"])]
                sel = str(x.get("item") or "").strip()
                was = str(l["item_id"]) if l["item_id"] else ("ask" if l["ask"] else "")
                qn = _num(x.get("qty"))
                if sel != was or norm(x.get("brand")) != norm(l["brand"]) or qn is None or l["qty"] is None \
                        or round(qn, 3) != round(l["qty"], 3) or str(x.get("place") or "proc") != l["place"]:
                    same = False
                    break
        if same and len({int(x["lid"]) for x in rows}) == len(old):
            rates = {}
            for x in rows:
                v = _num(x.get("rate"))
                if v is not None and v < 0:
                    raise ValueError("A rate cannot be below zero.")
                rates[int(x["lid"])] = v
            n = set_rates(db, rates, who)
            msg = "%s: %s." % (_stamp(b), ("rates saved on %d line%s" % (n, "" if n == 1 else "s")) if n else "its rates unchanged")
        else:
            msg = add_slip(db, d, SUPPLIER, "", rows, b["stamp_no"] or "", who)
        if p["slip_id"]:
            void_slip(db, p["slip_id"], who)
            msg += " The photo slip made before it was scanned is voided — counted once, on the scan."
        db.execute("UPDATE proc_photo SET slip_day=?, bill_id=?, bill_created_at=?, slip_id=NULL, checked_at=?, checked_by=?, diffs=? WHERE id=?",
                   (d, b["id"], b["created_at"] or "", now, who, json.dumps({"qty": qd}, ensure_ascii=False), pid))
    else:
        if not rows:
            raise ValueError("Type at least one line.")
        if p["slip_id"]:
            void_slip(db, p["slip_id"], who)
        out = {}
        msg = add_slip(db, d, SUPPLIER, "from the WhatsApp photos of %s" % _mlabel(p["ym"]), rows, "", who, out)
        db.execute("UPDATE proc_photo SET slip_day=?, bill_id=NULL, bill_created_at='', slip_id=?, checked_at=?, checked_by=?, diffs=? WHERE id=?",
                   (d, out.get("sid"), now, who, json.dumps({"qty": []}), pid))
    _audit(db, "proc_photo_checked", {"photo": pid, "day": d, "scan": scan_sel or "", "lines": len(rows)})
    return msg


def remove_photo(db, pid, who=None):
    """A photo taken off the month (kept on the server, struck through); the photo slip it made is voided. No commit."""
    who = _who() if who is None else who
    p = _photo(db, pid)
    if p is None or p["voided_at"]:
        return "That photo was not found or is already removed — nothing changed."
    db.execute("UPDATE proc_photo SET voided_at=?, voided_by=? WHERE id=?", (_now(), who, pid))
    extra = ""
    if p["slip_id"] and void_slip(db, p["slip_id"], who):
        extra = " The photo slip it made is voided."
    _audit(db, "proc_photo_removed", {"photo": pid})
    return "Photo taken off the month (kept on the server)." + extra


# ---------------------------------------------------------------------------------------------- the owner's page
PAGE_TPL = """<style>
#s634 details.card>summary{cursor:pointer;font-size:16px;font-weight:600}
#s634 .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
#s634 .tile{background:#fff;border:1px solid #dde3ea;border-radius:10px;padding:10px 14px}
#s634 .tile b{display:block;font-size:22px}
#s634 .look{background:#fff6e5;border:1px solid #ebd3a6;border-radius:10px;padding:10px 16px}
#s634 table{border-collapse:collapse;width:100%}#s634 td,#s634 th{padding:5px 6px;text-align:left;vertical-align:top}
#s634 tr+tr td{border-top:1px solid #eef1f4}#s634 .r{text-align:right}
#s634 .s634v{opacity:.55}
#s634 input.rt{max-width:90px;min-width:72px}#s634 .s634tabs a{display:inline-block;padding:5px 12px;border:1px solid #2b5d8a;border-radius:8px;text-decoration:none;margin-right:6px}
#s634 .s634tabs a.on{background:#2b5d8a;color:#fff}
</style>
<div id=s634>
<h2 style="margin-bottom:4px">Procedure room</h2>
<p class=muted style="margin-top:0">What was bought for the procedure room and at what rate — from the slips sorted on the desk and your WhatsApp photos. Rates are yours only; the staff never see them. How much was used, and what is in stock, will follow.</p>
<div class=s634tabs style="margin:6px 0 10px"><a href="{{url_for('s634_page')}}" class="{{'on' if not v.is_fy and v.ym==this_ym}}">This month</a><a href="{{url_for('s634_page', fy=v.fy)}}" class="{{'on' if v.is_fy}}">FY {{v.fy}}-{{'%02d' % ((v.fy+1) % 100)}}</a>
<form method=get action="{{url_for('s634_page')}}" style="display:inline-flex;gap:4px;align-items:center;margin:0"><input type=month name=ym value="{{v.ym or ''}}" style="max-width:160px" aria-label="Month"><button class=btn>Show</button></form>
<a href="{{url_for('s635_month', ym=v.ym or this_ym)}}" id=s635go style="margin-left:6px">Month end — Yuvika's WhatsApp</a></div>
<div class=tiles>
<div class=tile><b>{{rs(v.here_total)}}</b><span class=muted>Procedure room · {{v.label}}</span></div>
<div class=tile><b>{{rs(v.all_total)}}</b><span class=muted>All places on these slips</span></div>
<div class=tile><b>{{v.n_slips}}</b><span class=muted>Slips{% if v.photo_only %} — {{v.photo_only}} only from your photos (not scanned){% endif %}</span></div>
</div>
{% if v.look %}<div class=look style="margin-top:10px" id=s634look><b>Worth a look</b>{% for x in v.look %}<div>{{x}}</div>{% endfor %}</div>{% endif %}
<details class=card{{' open' if v.orders or v.noorder}} id=s635orders><summary>Orders and deliveries — {{v.label}}</summary>
{% if v.orders or v.noorder %}<div style="overflow:auto;margin-top:6px"><table><tr><th>Your order</th><th>Day</th><th>What</th><th>Slips against it</th><th>State</th></tr>
{% for o in v.orders %}<tr data-order="{{o.id}}"><td><a href="{{href(o.id)}}">{{o.stamp}}</a>{% if o.book %} <span class=muted>book {{o.book}}</span>{% endif %}</td><td>{{dmy(o.day)}}</td>
<td class=muted>{% for l in o.lines %}{{l.name}} {{q(l.qty)}}{{', ' if not loop.last}}{% else %}no lines yet{% endfor %}</td>
<td>{% for s in o.slips %}<a href="{{href(s.id)}}">{{s.stamp}}</a> <span class=muted>{{dmy(s.day)[:5]}}</span>{{' · ' if not loop.last}}{% else %}—{% endfor %}</td>
<td>{% if o.state=='awaiting' %}<span class="badge amber">awaiting — {{o.age}} days</span>{% elif o.state=='ordered' %}ordered{% if o.age is not none %} {{o.age}} day{{'' if o.age==1 else 's'}} ago{% endif %}{% elif o.state=='part' %}<span class="badge amber">part came</span>{% else %}delivered{% endif %}{% for x in o.diffs %}<div class=muted>{{x}}</div>{% endfor %}</td></tr>{% endfor %}
{% for s in v.noorder %}<tr data-noorder="{{s.id}}"><td><span class="badge amber">no order</span></td><td>{{dmy(s.day)}}</td><td colspan=3><a href="{{href(s.id)}}">{{s.stamp}}</a> — no order of yours is joined to this slip. Join it on the desk, or leave it.</td></tr>{% endfor %}
</table></div>{% else %}<p class=muted style="margin:6px 0">No order of yours for {{v.label}}. When your signed order page is sorted on the desk into Procedure room, choose “Dr Manoj's order”; the slip that comes against it is joined to it there.</p>{% endif %}
<p class=muted style="margin:4px 0 0">An order with no slip after {{v.await}} days shows “awaiting” (change the days under Your list and allowances).{% if v.floor %} Slips scanned before {{dmy(v.floor[:10])}} are never called “no order”.{% endif %}</p></details>
<details class=card open id=s634prod><summary>By product — {{v.label}}</summary>
<div style="overflow:auto;margin-top:6px"><table><tr><th>Product</th><th class=r>Bought</th><th class=r>Spent</th><th>Last rate · brand</th><th>Rates by brand</th></tr>
{% for p in v.prod if p.n %}<tr data-item="{{p.id}}"><td><b>{{p.name}}</b>{% if p.state=='rare' %} <span class=muted>rarely used</span>{% elif p.state=='retired' %} <span class=muted>retired</span>{% endif %}</td>
<td class=r>{{q(p.qty) if p.n else '—'}}{% if p.n %} {{p.unit}}{% endif %}</td><td class=r>{{rs(p.spent) if p.n else '—'}}{% if p.norate %} <span class="badge amber">{{p.norate}} without a rate</span>{% endif %}</td>
<td>{% if p.last %}{{rs(p.last.rate)}}{% if p.last.brand %} · {{p.last.brand}}{% endif %} <span class=muted>({{dmy(p.last.when)}})</span>{% else %}—{% endif %}</td>
<td class=muted>{% for b in p.brands %}{{b.brand if b.brand != '—' else 'no brand'}} {{rs(b.rate)}}{{' · ' if not loop.last}}{% endfor %}</td></tr>{% endfor %}
{% if not v.prod|selectattr('n')|list %}<tr><td colspan=5 class=muted>Nothing bought for the Procedure room in {{v.label}}.</td></tr>{% endif %}</table></div>
{% set idle = v.prod|rejectattr('n')|list %}{% if idle %}<p class=muted style="margin:6px 0 0">{{idle|length}} other product{{'' if idle|length == 1 else 's'}} on your list — nothing bought in {{v.label}}.</p>{% endif %}
{% if v.asks %}<div style="margin-top:8px" id=s634asks><b>Waiting for your list</b> <span class=muted>— lines the desk marked “not on the list”. Add the product below; then sort the paper again on the desk.</span>
<ul style="margin:4px 0 0">{% for d in v.asks %}<li>{{d.name}} · {{q(d.qty)}} {{d.unit}} · {% if d.stamp %}<a href="{{href(d.bill_id)}}">{{d.stamp}}</a>{% else %}photo slip {{dmy(d.when)}}{% endif %}</li>{% endfor %}</ul></div>{% endif %}
</details>
<details class=card open id=s634months><summary>By month — FY {{v.fy}}-{{'%02d' % ((v.fy+1) % 100)}}</summary>
<div style="overflow:auto;margin-top:6px"><table><tr><th>Month</th><th class=r>Slips</th><th class=r>Scanned</th><th class=r>Only a photo</th><th class=r>Procedure room</th><th class=r>All places</th><th></th></tr>
{% for m in v.bym %}<tr data-ym="{{m.ym}}"><td><a href="{{url_for('s634_page', ym=m.ym)}}">{{m.label}}</a></td><td class=r>{{m.slips}}</td><td class=r>{{m.scanned}}</td><td class=r>{{m.photo}}</td><td class=r>{{rs(m.here)}}</td><td class=r>{{rs(m.all)}}</td>
<td>{% if not m.slips %}<span class=muted>no slips yet</span>{% elif m.norate %}<span class="badge amber">{{m.norate}} without a rate</span>{% endif %}</td></tr>{% endfor %}</table></div></details>
{% if v.elsewhere %}<details class=card id=s634else><summary>Kept elsewhere — {{v.label}} ({{v.elsewhere|length}})</summary>
<div style="overflow:auto;margin-top:6px"><table><tr><th>Day</th><th>What</th><th class=r>Qty</th><th>Place</th><th class=r>Amount</th></tr>
{% for d in v.elsewhere %}<tr><td>{{dmy(d.when)}}</td><td>{{d.name}}{% if d.brand %} · {{d.brand}}{% endif %}</td><td class=r>{{q(d.qty)}}</td><td>{{places[d.place]}}{% if d.place=='sanj' %} <span class="badge amber">orthotics on a clinic slip</span>{% endif %}</td><td class=r>{{rs(d.amt) if d.amt is not none else '—'}}</td></tr>{% endfor %}</table></div></details>{% endif %}
<details class=card id=s634slips{{' open' if v.slips and not v.is_fy}}><summary>Slips and their rates — {{v.label}} ({{v.slips|length}})</summary>
<p class=muted style="margin:6px 0">Type or correct the rate on any line, then Save that slip. A blank rate is “no rate yet”. The rate read from a printed bill shows in grey until you type your own.</p>
{% for s in v.slips %}<form method=post action="{{url_for('s634_rates')}}" class=s634slip data-slip="{{s.key}}" style="border:1px solid #dde3ea;border-radius:10px;padding:8px 12px;margin:0 0 10px">
<input type=hidden name=back value="{{back}}"><div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px"><b>{{dmy(s.when)}} · {{s.vendor or 'supplier not read'}} · {% if s.src=='paper' %}<a href="{{href(s.bid)}}">{{s.stamp}}</a>{% else %}only a photo{% if s.note %} — {{s.note}}{% endif %}{% endif %}</b><span>{{rs(s.total)}}{% if s.norate %} <span class="badge amber">{{s.norate}} without a rate</span>{% endif %}</span></div>
<div style="overflow:auto"><table><tr><th>Product</th><th>Brand</th><th class=r>Qty</th><th>Place</th><th>Rate ₹</th><th class=r>Amount</th></tr>
{% for l in s.lines %}<tr><td>{{l.name}}{% if l.ask %} <span class="badge amber">not on your list</span>{% endif %}</td><td>{{l.brand}}</td><td class=r>{{q(l.qty)}} {{l.unit}}</td><td>{{l.place}}</td>
<td><input class=rt name="r{{l.id}}" value="{{plain(l.rate)}}" inputmode=decimal placeholder="{{plain(l.rate_read) if l.rate_read is not none else ''}}" aria-label="Rate of {{l.name}}"></td><td class=r>{{rs(l.amt) if l.amt is not none else '—'}}</td></tr>{% endfor %}</table></div>
<div style="display:flex;gap:8px;align-items:center;margin-top:6px"><button class=btn>Save the rates</button></div></form>
{% if s.src=='photo' %}<form method=post action="{{url_for('s634_void')}}" style="margin:-4px 0 12px" onsubmit="return confirm('Void this photo slip? It stays in the record, struck through, and counts nothing.')"><input type=hidden name=slip value="{{s.sid}}"><input type=hidden name=back value="{{back}}"><button class="btn small danger">Void this photo slip</button></form>{% endif %}
{% endfor %}{% if not v.slips %}<p class=muted>None for {{v.label}}.</p>{% endif %}</details>
<details class=card id=s634add><summary>+ A slip from a photo</summary>
<form method=post action="{{url_for('s634_slip')}}" style="margin-top:8px"><input type=hidden name=back value="{{back}}">
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end"><label style="margin:0">Date<input name=day placeholder="dd-mm-yyyy" style="max-width:130px" required></label>
<label style="margin:0">Supplier<input name=supplier value="{{supplier}}" style="max-width:200px"></label><label style="margin:0">Note<input name=note style="max-width:220px" placeholder="e.g. from the WhatsApp of 30-09"></label>
<label style="margin:0">Scanned as (if on the desk)<input name=paper placeholder="B-0007" style="max-width:110px"></label></div>
<div style="overflow:auto;margin-top:8px"><table><tr><th>Product</th><th>or what it is</th><th>Brand</th><th>Qty</th><th>Place</th><th>Rate ₹</th></tr>
{% for k in range(1, 9) %}<tr><td><select name="i{{k}}" style="max-width:220px"><option value="">—</option>{% for i in v.products if i.state!='retired' %}<option value="{{i.id}}">{{i.name}}</option>{% endfor %}</select></td>
<td><input name="n{{k}}" style="max-width:170px"></td><td><input name="b{{k}}" style="max-width:110px"></td><td><input name="q{{k}}" inputmode=decimal style="max-width:70px"></td>
<td><select name="p{{k}}">{% for pk, pw in places_list %}<option value="{{pk}}">{{pw}}</option>{% endfor %}</select></td><td><input name="r{{k}}" inputmode=decimal style="max-width:90px"></td></tr>{% endfor %}</table></div>
<p class=muted style="margin:4px 0">A Procedure room line takes a product from your list; a line kept elsewhere (home use, clinic equipment, OT, Sanjeevni) may be typed by its name. With “Scanned as”, the lines go onto that paper instead (it must be in Procedure room on the desk).</p>
<button class="btn small">Save the slip</button></form></details>
{% if v.rare %}<details class=card id=s634rare><summary>Rarely used and retired ({{v.rare|length}})</summary><div style="margin-top:6px">{% for i in v.rare %}{{i.name}} <span class=muted>({{states[i.state]}})</span>{{' · ' if not loop.last}}{% endfor %}</div></details>{% endif %}
<details class=card id=s634list><summary>Your list and allowances</summary>
<form method=post action="{{url_for('s634_allow')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0" id=s634allow><input type=hidden name=back value="{{back}}">
<b>Examination gloves:</b> <input name=cast value="{{allow['proc.gloves_cast']}}" inputmode=decimal style="max-width:50px" aria-label="Pairs a cast or slab"> pairs a cast or slab ·
<input name=ili value="{{allow['proc.gloves_ili']}}" inputmode=decimal style="max-width:50px" aria-label="Pairs an ILI"> pair an ILI · a box holds <input name=box value="{{allow['proc.gloves_box']}}" inputmode=decimal style="max-width:60px" placeholder="50 or 100" aria-label="Pairs in a box"> pairs ·
<b>An order is late after</b> <input name=await value="{{allow['proc.await_days']}}" inputmode=decimal style="max-width:50px" aria-label="Days before an order is awaiting"> days
<button class="btn small">Save</button></form>
<form method=post action="{{url_for('s634_item')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:flex-end;margin:8px 0"><input type=hidden name=do value=add><input type=hidden name=back value="{{back}}">
<label style="margin:0">Product (what and size)<input name=name required style="max-width:220px"></label><label style="margin:0">Unit<input name=unit list=s634units value=piece style="max-width:90px"></label>
<label style="margin:0">Counted<select name=how>{% for k, w in hows %}<option value="{{k}}"{{' selected' if k=='match'}}>{{w}}</option>{% endfor %}</select></label>
<label style="margin:0">Brands<input name=brands style="max-width:150px" placeholder="Gloster, Duracast"></label><label style="margin:0">Other spellings<input name=aliases style="max-width:200px"></label>
<label style="margin:0">Reorder below<input name=reorder inputmode=decimal style="max-width:70px"></label><button class="btn small">+ Add</button></form>
<datalist id=s634units>{% for u in units %}<option value="{{u}}">{% endfor %}</datalist>
{% for i in v.products %}<form method=post action="{{url_for('s634_item')}}" style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:4px 0" class="{{'s634v' if i.state=='retired'}}"><input type=hidden name=id value="{{i.id}}"><input type=hidden name=back value="{{back}}">
<input name=name value="{{i.name}}" style="max-width:220px" aria-label="Name"><input name=unit value="{{i.unit}}" list=s634units style="max-width:80px" aria-label="Unit">
<select name=how aria-label="Counted">{% for k, w in hows %}<option value="{{k}}"{{' selected' if k==i.how}}>{{w}}</option>{% endfor %}</select>
<input name=brands value="{{i.brands}}" style="max-width:150px" placeholder="brands" aria-label="Brands"><input name=aliases value="{{i.aliases}}" style="max-width:200px" placeholder="other spellings" aria-label="Other spellings">
<input name=reorder value="{{plain(i.reorder)}}" inputmode=decimal style="max-width:70px" placeholder="reorder" aria-label="Reorder below">
<button class="btn small" name=do value=edit>Save</button>
{% if i.state=='active' %}<button class="btn small" name=do value=rare>Rarely used</button>{% endif %}{% if i.state!='active' %}<button class="btn small" name=do value=restore>In use</button>{% endif %}
{% if i.state!='retired' %}<button class="btn small" name=do value=retire>Retire</button>{% endif %}<span class=muted>{{states[i.state]}}</span></form>{% endfor %}
<p class=muted>A product with lines is never deleted — retire it. Other spellings help the desk pre-choose a product from what the reader made of the handwriting.</p></details>
</div>"""

MONTH_TPL = """<style>
#s635 details.card>summary{cursor:pointer;font-size:16px;font-weight:600}
#s635 table{border-collapse:collapse;width:100%}#s635 td,#s635 th{padding:6px;text-align:left;vertical-align:top}
#s635 tr+tr td{border-top:1px solid #eef1f4}#s635 .r{text-align:right}#s635 .warn{color:#8a4f00;font-weight:600}#s635 .okw{color:#0e5a45}
#s635 tr.flag td{background:#fff6e5}#s635 input.rt{max-width:90px;min-width:70px}#s635 .tot td{border-top:2px solid #1c1c1a;font-weight:600}
</style>
<div id=s635>
<h2 style="margin-bottom:4px">Month end — Yuvika, {{v.label}}</h2>
<p class=muted style="margin-top:0">Add the photos from Yuvika's WhatsApp. Each is read, matched to its scan and your order. Open a slip, correct anything, then Save — the rates go onto the lines. Staff never see this page.</p>
<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:6px 0 10px"><a href="{{url_for('s634_page', ym=v.ym)}}">← Procedure room, {{v.label}}</a>
<form method=get action="{{url_for('s635_month')}}" style="display:inline-flex;gap:4px;align-items:center;margin:0"><input type=month name=ym value="{{v.ym}}" style="max-width:160px" aria-label="Month"><button class=btn>Show</button></form></div>
<form method=post action="{{url_for('s635_photos')}}" enctype="multipart/form-data" id=s635add style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 6px">
<input type=hidden name=ym value="{{v.ym}}"><label style="margin:0">Photos of {{v.label}} <input type=file name=photos multiple accept="image/jpeg,image/png,image/webp,application/pdf" required></label><button class=btn>Add photos</button></form>
<div class=muted id=s635count>{{v.n}} photo{{'' if v.n == 1 else 's'}} added · kept as this month's bill{% if v.reading %} · reading — this page refreshes by itself{% endif %}</div>
<div style="overflow:auto;margin-top:8px"><table id=s635tab><tr><th>Slip</th><th>Scan</th><th>Your order</th><th>Quantities</th><th>Rates</th><th class=r>Amount</th></tr>
{% for r in v.rows %}<tr data-photo="{{r.id}}" class="{{'flag' if (not r.scan or r.qty or r.rates or r.later or r.noorder or r.same_as) and r.state=='read' or r.state in ('failed','stale')}}">
<td><a href="{{url_for('s635_month', ym=v.ym, photo=r.id)}}#s635edit">{{dmy(r.day)[:5] if r.day else 'date not read'}}</a> <a class=muted href="{{url_for('s635_photo', pid=r.id)}}" target=_blank rel=noopener>photo</a>{% if r.checked %} <span class=okw>checked</span>{% endif %}</td>
<td>{% if r.scan %}<a href="{{href(r.scan.id)}}">{{r.scan.stamp}}</a>{% elif r.later %}<span class=warn>scanned later as <a href="{{href(r.later.id)}}">{{r.later.stamp}}</a> — open and choose it</span>{% else %}<span class=warn>not scanned</span>{% endif %}{% if r.same_as %}<div class=warn>same scan as the photo of {{r.same_as}}{% if not r.count %} — counted once{% else %} — if it is the same slip sent twice, take one off{% endif %}</div>{% endif %}</td>
<td>{% if r.order %}<a href="{{href(r.order.id)}}">{{r.order.stamp}}</a>{% elif r.noorder %}<span class=warn>no order</span>{% else %}—{% endif %}</td>
<td>{% if r.state in ('waiting','reading') %}<span class=muted>reading…</span>{% elif r.state=='stale' %}<span class=warn>the reading stopped — open it and Read again</span>{% elif r.state=='failed' and not r.checked %}<span class=warn>{{r.error}}</span>{% elif r.qty %}{% for x in r.qty %}<div class=warn>{{x}}</div>{% endfor %}{% if r.checked %}<div class=muted>(as it was before your check)</div>{% endif %}{% elif r.scan %}<span class=okw>same</span>{% else %}<span class=muted>from the photo only</span>{% endif %}</td>
<td>{% if r.rates %}{% for x in r.rates %}<div class=warn>{{x}}</div>{% endfor %}{% elif r.state=='read' or r.checked %}<span class=okw>as before</span>{% else %}—{% endif %}</td>
<td class=r>{% if not r.count %}<span class=muted>counted above</span>{% else %}{{rs(r.amt) if r.amt is not none else '—'}}{% endif %}</td></tr>{% endfor %}
{% if not v.rows %}<tr><td colspan=6 class=muted>No photos for {{v.label}} yet.</td></tr>{% endif %}
<tr class=tot id=s635total><td colspan=5>To pay Yuvika for {{v.label}}</td><td class=r>{{rs(v.total)}}</td></tr></table></div>
{% if v.desk_only %}<p id=s635deskonly style="margin:8px 0"><b>On the desk, not in these photos:</b> {% for s in v.desk_only %}<a href="{{href(s.id)}}">{{s.stamp}}</a> <span class=muted>{{dmy(s.day)[:5]}}</span>{{' · ' if not loop.last}}{% endfor %}</p>{% endif %}
{% if e %}<details class=card open id=s635edit style="margin-top:12px"><summary>{{dmy(e.day) if e.day else 'Date not read'}} — the lines{% if e.rd %} as read{% endif %}</summary>
<p class=muted style="margin:6px 0"><a href="{{url_for('s635_photo', pid=e.p.id)}}" target=_blank rel=noopener>Open the photo</a> · {{e.p.orig_name}}{% if e.p.read_state=='failed' %} · <span class=warn>{{e.p.read_error}}</span>{% endif %}</p>
<form method=post action="{{url_for('s635_check')}}"><input type=hidden name=ym value="{{v.ym}}"><input type=hidden name=photo value="{{e.p.id}}">
<label style="margin:0 0 6px;display:block">Its scan <select name=scan id=s635scan data-base="{{url_for('s635_month', ym=v.ym, photo=e.p.id)}}">{% for c in e.near %}<option value="{{c.id}}"{{' selected' if e.scan and e.scan.id==c.id}}>{{c.stamp_no or c.id}} · {{dmy(c.pday)[:5]}}</option>{% endfor %}<option value=none{{' selected' if not e.scan}}>not scanned — keep it as a photo slip</option></select></label>
<label style="margin:0">Date <input name=day value="{{dmy(e.day) if e.day else ''}}" placeholder="dd-mm-yyyy" style="max-width:130px" required></label>
<div style="overflow:auto;margin-top:6px"><table><tr><th>Product</th><th>or what it is</th><th>Brand</th><th>Qty</th><th>Rate ₹</th><th>Place</th></tr>
{% for l in e.lines + [none, none, none] %}{% set k = loop.index %}<tr><td><input type=hidden name="l{{k}}" value="{{l.lid if l and l.lid else ''}}"><select name="i{{k}}" style="max-width:220px"><option value="">—</option>{% for i in e.products %}<option value="{{i.id}}"{{' selected' if l and l.item==i.id}}>{{i.name}}</option>{% endfor %}<option value=ask{{' selected' if l and l.item=='ask'}}>Not on your list yet</option></select></td>
<td><input name="n{{k}}" value="{{l.name if l else ''}}" style="max-width:170px"></td><td><input name="b{{k}}" value="{{l.brand if l else ''}}" style="max-width:100px"></td>
<td><input name="q{{k}}" value="{{plain(l.qty) if l and l.qty is not none else ''}}" inputmode=decimal style="max-width:64px">{% if l and l.hint %}<div class=warn style="font-size:12px">{{l.hint}}</div>{% endif %}</td>
<td><input class=rt name="r{{k}}" value="{{plain(l.rate) if l and l.rate is not none else ''}}" inputmode=decimal aria-label="Rate"></td>
<td><select name="p{{k}}">{% for pk, pw in places_list %}<option value="{{pk}}"{{' selected' if l and l.place==pk}}>{{pw}}</option>{% endfor %}</select></td></tr>{% endfor %}</table></div>
<p class=muted style="margin:4px 0">With a scan chosen, Save puts your rates on its lines; if you change a product, quantity, brand or place, or add or leave out a line, your lines replace the scan's (the old ones kept). Not scanned: Save keeps it as a photo slip.</p>
<button class=btn>Save</button></form>
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">{% if e.p.read_state == 'failed' or e.stale %}<form method=post action="{{url_for('s635_read')}}" style="margin:0"><input type=hidden name=ym value="{{v.ym}}"><input type=hidden name=photo value="{{e.p.id}}"><button class="btn small">Read again</button></form>{% endif %}
<form method=post action="{{url_for('s635_remove')}}" style="margin:0" onsubmit="return confirm('Take this photo off the month? It stays on the server, struck through.')"><input type=hidden name=ym value="{{v.ym}}"><input type=hidden name=photo value="{{e.p.id}}"><button class="btn small danger">Take this photo off the month</button></form></div>
</details>{% endif %}
{% if v.removed %}<details class=card id=s635gone style="margin-top:10px"><summary>Taken off the month ({{v.removed|length}})</summary><div style="margin-top:6px">{% for g in v.removed %}<s>{{g.orig_name}}</s> <a class=muted href="{{url_for('s635_photo', pid=g.id)}}" target=_blank rel=noopener>photo</a>{{' · ' if not loop.last}}{% endfor %}</div></details>{% endif %}
</div>
{% if v.reading and not e %}<script>setTimeout(function(){location.reload();},15000);</script>{% endif %}
{% if e %}<script>(function(){var s=document.getElementById('s635scan');if(s){s.addEventListener('change',function(){location.href=s.getAttribute('data-base')+'&scan='+encodeURIComponent(s.value)+'#s635edit';});}})();</script>{% endif %}"""


def _href(bid):
    try:
        return AR._s559_paper_href(bid)
    except Exception:                                                # noqa: BLE001
        return url_for("bill_view", bid=bid)


def _back():
    b = request.values.get("back") or ""
    return b if re.fullmatch(r"(ym=\d{4}-\d{2}|fy=\d{4})?", b) else ""


def _go(back, anchor=""):
    u = url_for("s634_page")
    if back.startswith("ym="):
        u = url_for("s634_page", ym=back[3:])
    elif back.startswith("fy="):
        u = url_for("s634_page", fy=int(back[3:]))
    return redirect(u + anchor)


def page_view():
    db = AR.get_db()
    ym, fy = request.args.get("ym") or None, request.args.get("fy") or None
    if ym and not (re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", ym)):
        ym = None
    try:
        fy = int(fy) if (fy and not ym) else None
    except ValueError:
        fy = None
    v = owner_view(db, ym=ym, fy=fy)
    back = ("ym=%s" % ym) if ym else (("fy=%d" % fy) if fy else "")
    allow = {k: (_setting(db, k, d) or "") for k, d in ALLOW}
    return AR.page(PAGE_TPL, v=v, this_ym=_ym(), rs=rs, q=lambda x: _plain(x) if x is not None else "—", plain=_plain, dmy=_dmy, href=_href,
                   places=PLACE_WORD, places_list=PLACES, hows=HOW, states=STATE_WORD, units=UNITS, allow=allow, back=back, supplier=SUPPLIER,
                   flow=AR._flow("Procedure room", url_for("s551_month") if "s551_month" in AR.app.view_functions else url_for("bills_list")))


def item_post():
    db = AR.get_db()
    f = request.form
    do = (f.get("do") or "").strip()
    back = _back()
    try:
        if do == "add":
            iid, made = add_item(db, f.get("name"), f.get("unit"), f.get("how"), "active", f.get("brands"), f.get("aliases"), _num(f.get("reorder")))
            db.commit()
            flash(("Added to the list: %s." if made else "%s is already on the list.") % _clean(f.get("name"), 120))
            return _go(back, "#s634list")
        iid = int(f.get("id") or 0)
        it = next((i for i in item_rows(db) if i["id"] == iid), None)
        if it is None:
            flash("That product is not on the list.")
            return _go(back, "#s634list")
        if do == "edit":
            name = _clean(f.get("name"), 120)
            if not name:
                raise ValueError("Type the product's name.")
            if any(norm(i["name"]) == norm(name) and i["id"] != iid for i in item_rows(db)):
                raise ValueError("%s is already on the list." % name)
            new = {"name": name, "unit": _clean(f.get("unit"), 30) or "piece", "how": f.get("how") if f.get("how") in HOW_WORD else it["how"],
                   "brands": _clean(f.get("brands"), 200), "aliases": _clean(f.get("aliases"), 400), "reorder": _num(f.get("reorder"))}
            ch = {k: v for k, v in new.items() if v != it[k]}
            if ch:
                db.execute("UPDATE proc_item SET %s WHERE id=?" % ",".join("%s=?" % k for k in ch), tuple(ch.values()) + (iid,))
                _audit(db, "proc_item_changed", {"id": iid, "from": {k: it[k] for k in ch}, "to": ch})
            msg = ("Saved: %s." % name) if ch else ("Unchanged: %s." % name)
        elif do in ("rare", "retire", "restore"):
            st = {"rare": "rare", "retire": "retired", "restore": "active"}[do]
            db.execute("UPDATE proc_item SET state=? WHERE id=?", (st, iid))
            _audit(db, "proc_item_state", {"id": iid, "from": it["state"], "to": st})
            msg = {"rare": "%s: marked rarely used.", "retired": "%s: retired (its lines stay).", "active": "%s: in use again."}[st] % it["name"]
        else:
            abort(400)
        db.commit()
    except ValueError as e:
        db.rollback()
        msg = str(e)
    flash(msg)
    return _go(back, "#s634list")


def slip_post():
    db = AR.get_db()
    f = request.form
    back = _back()
    lines = [{"item": f.get("i%d" % k), "name": f.get("n%d" % k), "brand": f.get("b%d" % k), "qty": f.get("q%d" % k),
              "place": f.get("p%d" % k), "rate": f.get("r%d" % k)} for k in range(1, 21)]
    try:
        msg = add_slip(db, f.get("day"), f.get("supplier"), f.get("note"), lines, f.get("paper") or "")
        db.commit()
    except ValueError as e:
        db.rollback()
        msg = str(e) + " Nothing was saved."
    flash(msg)
    return _go(back, "#s634slips")


def rates_post():
    db = AR.get_db()
    back = _back()
    got, bad = {}, []
    for k, v in request.form.items():
        if k.startswith("r") and k[1:].isdigit():
            s = str(v).strip()
            n = _num(s) if s else None
            if s and (n is None or n < 0):
                bad.append(s)
            else:
                got[int(k[1:])] = n
    if bad:
        flash("The rate “%s” is not a number. Nothing was saved." % bad[0][:20])
        return _go(back, "#s634slips")
    n = set_rates(db, got)
    db.commit()
    flash(("Rates saved (%d line%s)." % (n, "" if n == 1 else "s")) if n else "No rate changed.")
    return _go(back, "#s634slips")


def void_post():
    db = AR.get_db()
    back = _back()
    try:
        sid = int(request.form.get("slip") or 0)
    except ValueError:
        sid = 0
    n = void_slip(db, sid)
    db.commit()
    flash("Photo slip voided — kept in the record, it counts nothing." if n else "That slip was not found or is already voided — nothing changed.")
    return _go(back, "#s634slips")


def allow_post():
    db = AR.get_db()
    back = _back()
    vals = {"proc.gloves_cast": request.form.get("cast"), "proc.gloves_ili": request.form.get("ili"), "proc.gloves_box": request.form.get("box")}
    if "await" in request.form:                                       # S635
        vals[AWAIT_KEY] = request.form.get("await")
    for k, v in vals.items():
        s = str(v or "").strip()
        if s and (_num(s) is None or _num(s) < 0):
            flash("“%s” is not a number. Nothing was saved." % s[:20])
            return _go(back, "#s634list")
    ch = {}
    for k, v in vals.items():
        s = _plain(_num(v)) if str(v or "").strip() else ""
        old = _setting(db, k, None)
        if (old or "") != s:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, s))
            ch[k] = {"from": old, "to": s}
    if ch:
        _audit(db, "proc_allowances", ch)
    db.commit()
    flash("Allowances saved." if ch else "Allowances unchanged.")
    return _go(back, "#s634list")


# ---------------------------------------------------------------------------------------------- S635: the month end's doors (his only)
def _ym_arg(v):
    return v if (v and re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", v)) else _ym()


def _to_month(ym, pid=None, scan=None, anchor=""):
    kw = {"ym": ym}
    if pid:
        kw["photo"] = pid
    if scan:
        kw["scan"] = scan
    return redirect(url_for("s635_month", **kw) + anchor)


def month_page():
    db = AR.get_db()
    ym = _ym_arg(request.args.get("ym"))
    v = month_view(db, ym)
    e = None
    pid = request.args.get("photo") or ""
    if pid.isdigit():
        p = _photo(db, int(pid))
        if p and not p["voided_at"] and p["ym"] == ym:
            e = photo_editor(db, p, request.args.get("scan"))
    return AR.page(MONTH_TPL, v=v, e=e, rs=rs, plain=_plain, dmy=_dmy, href=_href, places_list=PLACES,
                   flow=AR._flow("Month end", url_for("s634_page")))


def photos_post():
    db = AR.get_db()
    ym = _ym_arg(request.form.get("ym"))
    try:
        ids, words = add_photos(db, ym, request.files.getlist("photos"))
        db.commit()
    except OSError as ex:
        db.rollback()
        flash("The photos could not be kept (%s). Nothing was added." % type(ex).__name__)
        return _to_month(ym)
    start_reading(ids)
    flash(" ".join((["%d photo%s added — reading now." % (len(ids), "" if len(ids) == 1 else "s")] if ids else []) + words) or "No photo chosen.")
    return _to_month(ym)


def photo_file(pid):
    db = AR.get_db()
    p = _photo(db, pid)
    if p is None or not re.fullmatch(r"proc_\d{4}-\d{2}_[0-9a-f]{12}\.(jpg|jpeg|png|webp|pdf)", p["stored"] or ""):
        abort(404)
    path = os.path.join(_upload_dir(), p["stored"])
    if not os.path.isfile(path):
        abort(404)
    ext = p["stored"].rsplit(".", 1)[-1]
    mt = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp", "pdf": "application/pdf"}[ext]
    return send_file(path, mimetype=mt, download_name=p["orig_name"] or p["stored"])


def check_post():
    db = AR.get_db()
    f = request.form
    ym = _ym_arg(f.get("ym"))
    try:
        pid = int(f.get("photo") or 0)
    except ValueError:
        pid = 0
    scan = (f.get("scan") or "none").strip()
    lines = [{"lid": f.get("l%d" % k), "item": f.get("i%d" % k), "name": f.get("n%d" % k), "brand": f.get("b%d" % k), "qty": f.get("q%d" % k),
              "rate": f.get("r%d" % k), "place": f.get("p%d" % k)} for k in range(1, 61)]
    try:
        msg = check_photo(db, pid, f.get("day"), scan, lines)
        db.commit()
    except ValueError as e:
        db.rollback()
        flash(str(e) + " Nothing was saved.")
        return _to_month(ym, pid, scan, "#s635edit")
    flash(msg)
    return _to_month(ym, anchor="#s635tab")


def remove_post():
    db = AR.get_db()
    ym = _ym_arg(request.form.get("ym"))
    try:
        pid = int(request.form.get("photo") or 0)
    except ValueError:
        pid = 0
    msg = remove_photo(db, pid)
    db.commit()
    flash(msg)
    return _to_month(ym)


def read_post():
    db = AR.get_db()
    ym = _ym_arg(request.form.get("ym"))
    try:
        pid = int(request.form.get("photo") or 0)
    except ValueError:
        pid = 0
    n = db.execute("UPDATE proc_photo SET read_state='waiting', read_error='', read_at=? WHERE id=? AND voided_at=''", (_now(), pid)).rowcount
    db.commit()
    if n:
        start_reading([pid])
    flash("Reading it again." if n else "That photo was not found — nothing changed.")
    return _to_month(ym, pid if n else None, anchor="#s635edit")


def floor_step(db_path, out=print):
    """The installer's data step: the moment from which a slip with no order is called "no order" (UTC, as bills.created_at),
    once; a second run writes nothing. Returns 0."""
    con = sqlite3.connect(db_path, timeout=30)
    try:
        ensure(con)
        have = _setting(con, ORDERS_FROM_KEY, None)
        if have:
            out("floor: already set (%s = %s) -- nothing written" % (ORDERS_FROM_KEY, have))
            return 0
        at = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        con.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (ORDERS_FROM_KEY, at))
        try:
            con.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                        (at, "installer S635", "procroom_orders_from_s635", json.dumps({"from_utc": at})))
        except sqlite3.Error:
            pass
        con.commit()
        out("floor: %s set to %s (UTC) -- slips scanned from now on are checked for an order" % (ORDERS_FROM_KEY, at))
        return 0
    finally:
        con.close()


def menu_items(role):
    """For the scan app's one menu (asset_register._s559_items): the owner's Procedure room page. Nothing for anyone else."""
    try:
        if role == "owner":
            return [("s634_page", "Procedure room", url_for("s634_page"))]
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
    app.add_url_rule("/procroom", "s634_page", ar.owner_required(page_view))
    app.add_url_rule("/procroom/item", "s634_item", ar.owner_required(item_post), methods=["POST"])
    app.add_url_rule("/procroom/slip", "s634_slip", ar.owner_required(slip_post), methods=["POST"])
    app.add_url_rule("/procroom/rates", "s634_rates", ar.owner_required(rates_post), methods=["POST"])
    app.add_url_rule("/procroom/void", "s634_void", ar.owner_required(void_post), methods=["POST"])
    app.add_url_rule("/procroom/allow", "s634_allow", ar.owner_required(allow_post), methods=["POST"])
    app.add_url_rule("/procroom/month", "s635_month", ar.owner_required(month_page))                       # S635: the month end
    app.add_url_rule("/procroom/month/photos", "s635_photos", ar.owner_required(photos_post), methods=["POST"])
    app.add_url_rule("/procroom/month/photo/<int:pid>", "s635_photo", ar.owner_required(photo_file))
    app.add_url_rule("/procroom/month/check", "s635_check", ar.owner_required(check_post), methods=["POST"])
    app.add_url_rule("/procroom/month/remove", "s635_remove", ar.owner_required(remove_post), methods=["POST"])
    app.add_url_rule("/procroom/month/read", "s635_read", ar.owner_required(read_post), methods=["POST"])
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data steps:  python3 procroom.py --ensure <assets.db>  |  --seed <assets.db>  |  --floor <assets.db> (S635)
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        print("procroom %s: tables ready (%s)" % (VERSION, ", ".join(ensure_path(sys.argv[2]))))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--seed":
        sys.exit(seed_step(sys.argv[2]))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--floor":                   # S635
        sys.exit(floor_step(sys.argv[2]))
    else:
        print(__doc__)
