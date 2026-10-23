#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""procroom.py -- S634_PROCROOM_LIST (D773 Kit 1; the owner's "okay to start", 08:31 IST 23-Oct-2026, on the S345 mock-ups).

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
    Kit 2 (the order scan, the month-end WhatsApp check) and Kit 3 (Shavez's next-morning screen, use and stock) follow.
"""
import datetime
import json
import math
import re
import sqlite3
import sys
import time

from flask import abort, flash, g, redirect, request, url_for

VERSION = "S634"
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
ALLOW = (("proc.gloves_cast", "2"), ("proc.gloves_ili", "1"), ("proc.gloves_box", ""))
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
)
TABLES = ("proc_item", "proc_slip", "proc_line")


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


def paper_counts(db, b, here=True):
    """(True, '') when this paper's lines count now; else (False, why) -- the same rule as the page's read (_paper_sql)."""
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
    if noread:
        lines.append({"no": 1, "name": "", "qty": "", "unit": "", "brand": "", "place": "proc", "item": "", "saved": False, "sug": False,
                      "hand": True, "orth": False})
    ok, why = paper_counts(db, b, here=False)                       # the panel shows only with Procedure room chosen
    return {"lines": lines, "items": [_item_view(i) for i in usable], "places": [list(p) for p in PLACES], "owner": bool(owner),
            "noread": noread, "counts": ok, "why": why}


def _key_of(t):
    no, name, brand, q, unit, place, iid, ask = t[:8]
    return (no, norm(name), norm(brand), "" if q is None else "%.4f" % q, unit, place, iid or 0, ask)


def save_lines(db, b, lines, who=None, owner=False):
    """One desk Save's lines for this paper. An untouched line (no product chosen) is not stored and never blocks the Save. A
    Procedure room line needs a product from the list -- or 'not on the list' (ask: it waits on his page for his list); a line kept
    elsewhere may carry its name only (free). 'new' (the owner only) adds the line's name to the list first. The rate read from
    the paper rides along unseen (rate_read); his own rate on a line that did not change is kept. A re-save REPLACES the paper's
    own lines (the old ones voided and kept). No commit. Returns the Save's words. Refusals raise ValueError (plain words)."""
    who = _who() if who is None else who
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
    n = db.execute("UPDATE proc_line SET voided_at=?, voided_by=? WHERE bill_id=? AND bill_created_at=? AND voided_at=''",
                   (_now(), _who() if who is None else who, b["id"], b["created_at"] or "")).rowcount
    if n:
        _audit(db, "proc_lines_voided", {"bill": b["id"], "lines": n, "why": why})
    return n


def has_lines(db, b):
    return bool(saved_lines(db, b))


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
                            "WHERE l.voided_at='' AND l.slip_id IS NULL AND " + _paper_sql(db, "b") + " ORDER BY l.ts, l.id"):
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
            "rare": [i for i in items if i["state"] in ("rare", "retired")], "products": items}


# ---------------------------------------------------------------------------------------------- his writes
def _by_stamp(db, no):
    no = _clean(no, 20).upper()
    if not no:
        return None
    m = re.fullmatch(r"(?:B\s*-?\s*)?(\d{1,6})", no)
    if m:
        no = "B-%04d" % int(m.group(1))
    return db.execute("SELECT * FROM bills WHERE upper(stamp_no)=? AND dup_of IS NULL", (no,)).fetchone()


def add_slip(db, day, supplier, note, lines, paper_no="", who=None):
    """A slip from his photo -- or, with paper_no, its lines (with his rates) onto that scanned paper in Procedure room (replacing
    its desk lines, the old ones voided and kept). Lines: dicts {item, name, brand, qty, unit, place, rate}. No commit."""
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
        iid = None
        if sel.isdigit() and int(sel) in items:
            iid = int(sel)
            name = name or items[iid]["name"]
        elif place == "proc":
            raise ValueError("Line %d: a Procedure room line needs a product from your list (add it to the list first)." % k)
        elif not name:
            raise ValueError("Line %d: type what it is." % k)
        unit = _clean(x.get("unit"), 30) or (items[iid]["unit"] if iid else "")
        got.append((name, _clean(x.get("brand"), 60), q, unit, iid, place, rate))
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
        for no, (name, brand, q, unit, iid, place, rate) in enumerate(got, 1):
            db.execute("INSERT INTO proc_line(bill_id, bill_created_at, slip_id, line_no, name, brand, qty, unit, item_id, ask, place, rate_read, rate, rate_by, day, ts, by_whom, at) "
                       "VALUES(?,?,NULL,?,?,?,?,?,?,0,?,NULL,?,?,?,?,?,?)",
                       (b["id"], b["created_at"] or "", no, name, brand, q, unit, iid, place, rate, (who if rate is not None else ""), d, ts, who, now))
        _audit(db, "proc_paper_lines_by_owner", {"bill": b["id"], "lines": len(got), "replaced": n})
        return "%s: %d line%s saved from the photo%s." % (b["stamp_no"] or "#%d" % b["id"], len(got), "" if len(got) == 1 else "s",
                                                         " (its earlier lines replaced, kept)" if n else "")
    sid = db.execute("INSERT INTO proc_slip(day, supplier, note, by_whom, at) VALUES(?,?,?,?,?)",
                     (d, _clean(supplier, 80) or SUPPLIER, _clean(note, 200), who, now)).lastrowid
    for no, (name, brand, q, unit, iid, place, rate) in enumerate(got, 1):
        db.execute("INSERT INTO proc_line(bill_id, bill_created_at, slip_id, line_no, name, brand, qty, unit, item_id, ask, place, rate_read, rate, rate_by, day, ts, by_whom, at) "
                   "VALUES(NULL,'',?,?,?,?,?,?,?,0,?,NULL,?,?,?,?,?,?)",
                   (sid, no, name, brand, q, unit, iid, place, rate, (who if rate is not None else ""), d, ts, who, now))
    _audit(db, "proc_slip_added", {"slip": sid, "day": d, "lines": len(got)})
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
<form method=get action="{{url_for('s634_page')}}" style="display:inline-flex;gap:4px;align-items:center;margin:0"><input type=month name=ym value="{{v.ym or ''}}" style="max-width:160px" aria-label="Month"><button class=btn>Show</button></form></div>
<div class=tiles>
<div class=tile><b>{{rs(v.here_total)}}</b><span class=muted>Procedure room · {{v.label}}</span></div>
<div class=tile><b>{{rs(v.all_total)}}</b><span class=muted>All places on these slips</span></div>
<div class=tile><b>{{v.n_slips}}</b><span class=muted>Slips{% if v.photo_only %} — {{v.photo_only}} only from your photos (not scanned){% endif %}</span></div>
</div>
{% if v.look %}<div class=look style="margin-top:10px" id=s634look><b>Worth a look</b>{% for x in v.look %}<div>{{x}}</div>{% endfor %}</div>{% endif %}
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
<input name=ili value="{{allow['proc.gloves_ili']}}" inputmode=decimal style="max-width:50px" aria-label="Pairs an ILI"> pair an ILI · a box holds <input name=box value="{{allow['proc.gloves_box']}}" inputmode=decimal style="max-width:60px" placeholder="50 or 100" aria-label="Pairs in a box"> pairs
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
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data steps:  python3 procroom.py --ensure <assets.db>  |  --seed <assets.db>
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        print("procroom %s: tables ready (%s)" % (VERSION, ", ".join(ensure_path(sys.argv[2]))))
    elif len(sys.argv) >= 3 and sys.argv[1] == "--seed":
        sys.exit(seed_step(sys.argv[2]))
    else:
        print(__doc__)
