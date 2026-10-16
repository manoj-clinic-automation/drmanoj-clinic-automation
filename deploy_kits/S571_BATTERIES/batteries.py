#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batteries.py -- S571_BATTERIES (D730 (1); the owner's word, 11:57 IST 16-Oct-2026: "AND THE BATTERY ONE ?").

THE OWNER'S RULINGS (S318_BATTERY_PROPOSAL v2, his words 07:54-08:51 IST 16-Oct, the mock-up Main.dc.html / Fitted.dc.html)
    Keep a list of BATTERY PLACES, not batteries. Each place shows the battery fitted now, its warranty, when it is due, and every
    battery it has had before. Reception does nothing new. UPS batteries come from B.L. Computers (warranty 1 year; the bill comes
    with the battery, or late -- "bill awaited" until it is linked); the others from Jasoria (bill and warranty card with the
    battery; they pay for the old battery). A new UPS, inverter or vehicle added in Machines gets its battery place by itself.

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded hook at its foot, after the S568 block: if this file is
    absent or cannot load, the app runs exactly as before (the menu item, the Renewals card and the desk's offer give nothing).
    Its tables come from its own ensure(db) (additive, idempotent; the seeded places by their seed_key, never twice):
        battery_place    a place: its group, name, sub-line, payer (clinic / NK Pathology / owner / to confirm -- never guessed),
                         supplier, warranty and usual-life months, owner-only flag, the re-order line (type, Ah, V, set of N),
                         its upkeep, and a machine link with its fingerprint (asset_id + asset_created_at, S557's rule)
        battery_fit      every battery fitted in a place: fitted / removed, supplier, make, Ah, set, warranty months, price, the
                         old-battery amount (Jasoria), and the bill / warranty-card links -- each a paper's id with its
                         fingerprint (bill_id + bill_created_at); a link is trusted only while both match
        battery_upkeep   the "done" taps of the small upkeep (inverter water, UPS backup check, generator start)
    and one settings row, batteries.since, written once by the first ensure: only a machine added after it gets a place by itself.
    REMINDERS ARE COMPUTED WHEN READ (S571_BRIEF_R1 B1): nothing is written to `expiries` and S557's heal is not touched. They
    appear on the Renewals page as one card, "Batteries" (the jinja global s571_battery_card, shown by ONE hook in renewals()'s
    template next to d664's warranty card), '' on any error; it honours the page's ?all=1 view.
    LINKING A PAPER NEVER CHANGES IT (D664): its lane, section and status are never written here. The desk's own Save decides
    where the money goes; a place's payer only pre-selects the desk's choice in the browser (sorting_desk's S571 part).
    Addresses (the /scanapp prefix is added by the app's middleware):
        GET  /batteries                 the page: totals, the four groups, one row per place, + Add a battery place
        GET  /batteries/place/<id>      a place's history: the re-order line, every battery it has had, the links, upkeep done
        GET  /batteries/fit/<id>        "New battery fitted" -- the one form (B.L. or Jasoria, as the mock-up)
        POST /batteries/fit/<id>        save it (the previous battery goes into the history with its removed date)
        POST /batteries/link            link a paper as a fitting's bill or warranty card (a form, or JSON from the desk's one tap)
        POST /batteries/done            an upkeep "done" tap
        POST /batteries/place           add a place; the owner: edit, link to a machine, remove from the list
    Who: the owner sees everything. A manager sees the clinic and lab places only, and only while the switch batteries.on is ON
    (absent = OFF; a row on the owner's Switches card, sorting_desk.SWITCHES). The reception login never (the app's gate). An
    owner-only place -- its fittings, links, history and reminders -- is refused to anyone but the owner, server-side.
"""
import datetime
import json
import math
import re
import sqlite3
import sys
import time

from flask import abort, flash, g, jsonify, redirect, render_template_string, request, url_for
from markupsafe import Markup

VERSION = "S571"
AR = None                     # the asset app's module, handed in by init()
TODAY = None                  # the walk sets a made-up day here
MOUNTED = False
SWITCH = "batteries.on"
SINCE = "batteries.since"
PICK_DAYS = 90                # the paper picker and the desk offer: papers of the last 90 days (S571_BRIEF_R1 C7)
WARN_DAYS = 30                # warranty ends within 30 days; usual life amber 30 days before; a B.L. bill awaited after 30 days

GROUPS = (("online_ups", "Online UPS"), ("small_ups", "Small UPS"), ("gen_inv", "Generator and inverters"), ("vehicles", "Vehicles"))
GROUP_WORD = dict(GROUPS)
GROUP_NOTE = {"online_ups": "B.L. Computers · warranty 1 year · bill with the battery",
              "small_ups": "B.L. Computers · warranty 1 year",
              "gen_inv": "Jasoria · bill and warranty card come with the battery · old battery paid back",
              "vehicles": "Jasoria · bill and warranty card · yours only"}
GROUP_KIND = {"online_ups": "UPS place", "small_ups": "UPS place", "gen_inv": "Generator / inverter place", "vehicles": "Vehicle place"}
PAYERS = (("clinic", "Clinic"), ("nk", "NK Pathology"), ("owner", "You"), ("confirm", "to confirm"))
PAYER_WORD = dict(PAYERS)
DESK_DEST = {"clinic": "clinic_equipment", "nk": "lab", "owner": "personal"}      # R1 C6; 'to confirm' -> nothing
BL, JAS = "B.L. Computers", "Jasoria"
UPKEEP = {"water": ("Inverter water", "Water top-up due"), "backup": ("UPS backup check", "Backup check due"),
          "start": ("Generator start test", "Start test due")}
LIFE = {"car": 42, "two": 30, "inverter": 54, "ups": 30, "generator": 30}           # usual life, months (editable per place)

# The seeded places (S571 item 2, R1 C3 / C9): names only -- no contact or identity number of any kind (F-185). Each:
# (seed_key, group, name, sub-line, payer, supplier, warranty months, usual life months, owner only, set of, upkeep, every N months)
SEED = (
    ("online_ups.digital_xray", "online_ups", "Digital X-ray", "Clinic", "clinic", BL, 12, LIFE["ups"], 0, None, "backup", 3),
    ("online_ups.nk_pathology", "online_ups", "NK Pathology", "Lab · paid by NK Pathology", "nk", BL, 12, LIFE["ups"], 0, None, "backup", 3),
    ("online_ups.dth_lab", "online_ups", "DTH lab", "Dhanwantari Tomar Hospital", "confirm", BL, 12, LIFE["ups"], 0, None, "backup", 3),
    ("small_ups.reception_pc", "small_ups", "Reception PC", "Clinic", "clinic", BL, 12, LIFE["ups"], 0, 1, "backup", 3),
    ("small_ups.second_pc", "small_ups", "Second PC", "Clinic", "clinic", BL, 12, LIFE["ups"], 0, 1, "backup", 3),
    ("small_ups.lab_analysers", "small_ups", "Lab analysers", "NK Pathology", "nk", BL, 12, LIFE["ups"], 0, None, "backup", 3),
    ("small_ups.home_dvr_router", "small_ups", "Home DVR + router", "Home · yours only", "owner", BL, 12, LIFE["ups"], 1, 1, "backup", 3),
    ("gen_inv.generator", "gen_inv", "Generator", "Clinic", "clinic", JAS, None, LIFE["generator"], 0, 1, "start", 1),
    ("gen_inv.clinic_inverter", "gen_inv", "Clinic inverter", "2 batteries", "clinic", JAS, None, LIFE["inverter"], 0, 2, "water", 3),
    ("gen_inv.home_inverter", "gen_inv", "Home inverter", "2 batteries · yours only", "owner", JAS, None, LIFE["inverter"], 1, 2, "water", 3),
    ("vehicles.carnival", "vehicles", "Carnival", "Car", "owner", JAS, None, LIFE["car"], 1, 1, "", None),
    ("vehicles.wagon_r", "vehicles", "Wagon R", "Car", "owner", JAS, None, LIFE["car"], 1, 1, "", None),
    ("vehicles.vento", "vehicles", "Vento", "Car", "owner", JAS, None, LIFE["car"], 1, 1, "", None),
    ("vehicles.scooty", "vehicles", "Scooty", "Two-wheeler", "owner", JAS, None, LIFE["two"], 1, 1, "", None),
    ("vehicles.bike", "vehicles", "Bike", "Two-wheeler", "owner", JAS, None, LIFE["two"], 1, 1, "", None),
)

DDL = (
    "CREATE TABLE IF NOT EXISTS battery_place(id INTEGER PRIMARY KEY, seed_key TEXT UNIQUE, grp TEXT NOT NULL, name TEXT NOT NULL, "
    "sub TEXT NOT NULL DEFAULT '', payer TEXT NOT NULL DEFAULT 'confirm', supplier TEXT NOT NULL DEFAULT '', warranty_months INTEGER, "
    "life_months INTEGER, owner_only INTEGER NOT NULL DEFAULT 0, set_n INTEGER, btype TEXT NOT NULL DEFAULT '', ah TEXT NOT NULL DEFAULT '', "
    "volts TEXT NOT NULL DEFAULT '', upkeep TEXT NOT NULL DEFAULT '', upkeep_months INTEGER, sort INTEGER NOT NULL DEFAULT 0, "
    "asset_id INTEGER, asset_created_at TEXT, auto INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1, made_by TEXT, made_at TEXT)",
    "CREATE UNIQUE INDEX IF NOT EXISTS battery_place_asset ON battery_place(asset_id, asset_created_at) WHERE asset_id IS NOT NULL",
    "CREATE TABLE IF NOT EXISTS battery_fit(id INTEGER PRIMARY KEY, place_id INTEGER NOT NULL, fitted_on TEXT NOT NULL, removed_on TEXT, "
    "supplier TEXT NOT NULL DEFAULT '', brand TEXT NOT NULL DEFAULT '', ah TEXT NOT NULL DEFAULT '', set_n INTEGER, warranty_months INTEGER, "
    "price REAL, old_amount REAL, bill_id INTEGER, bill_created_at TEXT NOT NULL DEFAULT '', card_id INTEGER, "
    "card_created_at TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT NULL DEFAULT '')",
    "CREATE INDEX IF NOT EXISTS battery_fit_place ON battery_fit(place_id)",
    "CREATE TABLE IF NOT EXISTS battery_upkeep(id INTEGER PRIMARY KEY, place_id INTEGER NOT NULL, kind TEXT NOT NULL, done_on TEXT NOT NULL, "
    "by_whom TEXT, at TEXT)",
)
TABLES = ("battery_place", "battery_fit", "battery_upkeep")


# ---------------------------------------------------------------------------------------------- the database's part
def ensure(db):
    """Additive and idempotent. Two gunicorn workers start at once: 'already exists' from the second is normal. The seeded
    places go in by their seed_key (INSERT OR IGNORE -- a second run adds nothing, an edited seeded place is never put back);
    batteries.since is written once (INSERT OR IGNORE)."""
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    for i, s in enumerate(SEED):
        db.execute("INSERT OR IGNORE INTO battery_place(seed_key, grp, name, sub, payer, supplier, warranty_months, life_months, owner_only, "
                   "set_n, upkeep, upkeep_months, sort, made_by, made_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,'S571 seed',datetime('now'))",
                   s + ((i + 1) * 10,))
    db.execute("INSERT OR IGNORE INTO settings(key, value) VALUES(?, datetime('now'))", (SINCE,))
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
    print("batteries: the database stayed locked at mount; its tables are left to the installer's data step", file=sys.stderr)
    return False


def ensure_path(db_path):
    con = sqlite3.connect(db_path, timeout=20)
    try:
        ensure(con)
        n = con.execute("SELECT COUNT(*) FROM battery_place").fetchone()[0]
    finally:
        con.close()
    return TABLES, n


# ---------------------------------------------------------------------------------------------- small helpers
def _today():
    return TODAY or datetime.date.today()


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


def _owner():
    return _role() == "owner"


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


def switch_on(db):
    return (_setting(db, SWITCH, "off") or "").strip().lower() == "on"


def may_see(db, role=None):
    """The owner always; a manager only while batteries.on is ON; anyone else never."""
    role = _role() if role is None else role
    return role == "owner" or (role == "manager" and switch_on(db))


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


def _int(v, lo=0, hi=600):
    f = _num(v)
    if f is None:
        return None
    if f != int(f) or f < lo or f > hi:
        raise ValueError("'%s' is not a whole number from %d to %d." % (str(v)[:12], lo, hi))
    return int(f)


def _grp(n):
    s = "%d" % n
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
    return head + "," + tail


def rs(x):
    """₹ with Indian grouping; paise only when there are any."""
    if x is None:
        return "—"
    f = float(x)
    neg = f < 0
    f = abs(f)
    t = _grp(int(round(f))) if round(f, 2) == int(round(f, 2)) else _grp(int(f)) + ("%.2f" % (f - int(f)))[1:]
    return ("-" if neg else "") + "₹" + t


def _plain(x):
    if x is None:
        return ""
    f = float(x)
    return ("%d" % f) if f == int(f) else ("%g" % round(f, 2))


def _iso(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:                                                # noqa: BLE001
        return None


def dmy(s):
    d = _iso(s) if not isinstance(s, datetime.date) else s
    return d.strftime("%d-%m-%Y") if d else (s or "")


def typed_date(s):
    """A person's typed date: dd-mm-yyyy (or d-m-yy, / or .), or yyyy-mm-dd -> a date; None when empty; ValueError otherwise."""
    s = str(s or "").strip()
    if not s:
        return None
    m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", s)
    try:
        if m:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2}|\d{4})", s)
        if m:
            y = int(m.group(3))
            return datetime.date(y + 2000 if y < 100 else y, int(m.group(2)), int(m.group(1)))
    except ValueError:
        pass
    raise ValueError("The date '%s' is not a full date — type it as dd-mm-yyyy." % s[:20])


def add_months(d, n):
    if d is None or n is None:
        return None
    y, m = divmod(d.month - 1 + int(n), 12)
    y, m = d.year + y, m + 1
    last = (datetime.date(y + (m // 12), m % 12 + 1, 1) - datetime.timedelta(days=1)).day
    return datetime.date(y, m, min(d.day, last))


def months_between(a, b):
    if a is None or b is None:
        return None
    n = (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)
    return max(0, n)


def _supplier_key(v):
    cp = sys.modules.get("clinic_papers")
    if cp is not None and hasattr(cp, "_supplier_key"):
        return cp._supplier_key(v)
    w = [x for x in re.sub(r"[^a-z0-9 ]", " ", (v or "").lower().replace("-", "").replace(".", "")).split()
         if x not in ("the", "ms", "m", "s", "pvt", "ltd", "p", "co", "and", "&")]
    return " ".join(w[:2])


def sup1(v):
    """S571_BRIEF_R1 C4: a supplier is matched on the FIRST word of _supplier_key ('bl', 'jasoria')."""
    k = _supplier_key(v).split()
    return k[0] if k else ""


def is_bl(place):
    return sup1(place["supplier"]) == "bl"


def _audit(db, action, detail):
    """Into the desk's own book (desk_audit, sorting_desk's table); fail-soft when it is absent."""
    try:
        db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                   (_now(), _who(), action, json.dumps(detail or {}, ensure_ascii=False)[:500]))
    except sqlite3.Error:
        pass


# ---------------------------------------------------------------------------------------------- places, fittings, papers
def places(db, owner, active=True):
    try:
        rows = db.execute("SELECT * FROM battery_place WHERE 1=1" + (" AND active=1" if active else "") +
                          ("" if owner else " AND owner_only=0") + " ORDER BY sort, id").fetchall()
    except sqlite3.Error:
        return []
    return [dict(r) for r in rows]


def place(db, pid):
    try:
        r = db.execute("SELECT * FROM battery_place WHERE id=?", (pid,)).fetchone()
    except sqlite3.Error:
        return None
    return dict(r) if r else None


def place_for(db, pid):
    """A place this person may open, or abort: 404 when there is none; 403 for an owner-only place to anyone but the owner."""
    p = place(db, pid)
    if p is None:
        abort(404)
    if p["owner_only"] and not _owner():
        abort(403)
    return p


def fits(db, pid):
    return [dict(r) for r in db.execute("SELECT * FROM battery_fit WHERE place_id=? AND voided_at='' ORDER BY fitted_on DESC, id DESC", (pid,))]


def current_fit(db, pid):
    r = db.execute("SELECT * FROM battery_fit WHERE place_id=? AND voided_at='' AND removed_on IS NULL ORDER BY fitted_on DESC, id DESC LIMIT 1",
                   (pid,)).fetchone()
    return dict(r) if r else None


def paper_of(db, bid, created):
    """The paper a link points to -- trusted only while its id AND created_at still match (S557's fingerprint rule)."""
    if not bid:
        return None
    r = db.execute("SELECT * FROM bills WHERE id=? AND COALESCE(created_at,'')=?", (bid, created or "")).fetchone()
    return r


def machine_of(db, p):
    if not p.get("asset_id"):
        return None
    try:
        return db.execute("SELECT * FROM assets WHERE id=? AND COALESCE(created_at,'')=?", (p["asset_id"], p["asset_created_at"] or "")).fetchone()
    except sqlite3.Error:
        return None


def _stamp(b):
    return (b["stamp_no"] or "") if b is not None and b["stamp_no"] else ("#%d" % b["id"] if b is not None else "")


def _lane(b):
    sd = sys.modules.get("sorting_desk")
    if sd is not None and hasattr(sd, "_lane"):
        return sd._lane(b)
    return b["lane"] or "clinic"


def paper_visible(b, owner):
    """S571_BRIEF_R1 C7: the desk's own rules -- never a pharmacy paper, never a patient's paper, a Personal paper to the owner only."""
    if b is None:
        return False
    sd = sys.modules.get("sorting_desk")
    if sd is not None and hasattr(sd, "_visible"):
        if sd._visible(b, owner):
            return False
    else:
        if _lane(b) == "pharmacy" or ((b["subgroup"] or "") == "personal" and not owner):
            return False
    return (b["subgroup"] or "") != "patient_paper"


def _recent(b, today):
    d = _iso(b["created_at"])
    return d is not None and (today - d).days <= PICK_DAYS


def candidates(db, p, owner, today=None):
    """The paper picker: the same supplier's papers (first word, R1 C4) of the last 90 days that this person may see -- any lane but
    the pharmacy's; never a set-aside paper or a second scan. Newest first: (id, 'stamp · date · amount')."""
    today = today or _today()
    k = sup1(p["supplier"])
    if not k:
        return []
    lo = (today - datetime.timedelta(days=PICK_DAYS)).isoformat()
    out = []
    for b in db.execute("SELECT * FROM bills WHERE dup_of IS NULL AND status<>'rejected' AND substr(COALESCE(created_at,''),1,10)>=? "
                        "ORDER BY created_at DESC, id DESC LIMIT 400", (lo,)):
        if sup1(b["vendor"]) != k or not paper_visible(b, owner):
            continue
        out.append({"id": b["id"], "text": "%s · %s · %s" % (_stamp(b), dmy(b["bill_date"] or b["created_at"]),
                                                            rs(b["total_amount"]) if b["total_amount"] is not None else "no amount")})
    return out


def _pickable(db, p, bid, owner, today=None):
    try:
        bid = int(bid)
    except (TypeError, ValueError):
        return None
    b = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    if b is None or b["dup_of"] or b["status"] == "rejected" or not paper_visible(b, owner) or not _recent(b, today or _today()):
        return None
    if sup1(b["vendor"]) != sup1(p["supplier"]) or not sup1(p["supplier"]):
        return None
    return b


def fit_of_paper(db, b):
    """The fittings that hold this paper (as bill or card), trusted links only."""
    return [dict(r) for r in db.execute("SELECT * FROM battery_fit WHERE voided_at='' AND ((bill_id=? AND bill_created_at=?) OR "
                                        "(card_id=? AND card_created_at=?))", (b["id"], b["created_at"] or "", b["id"], b["created_at"] or ""))]


# ---------------------------------------------------------------------------------------------- what a place shows (computed when read)
def _state(days, threshold):
    if days is None:
        return ""
    if days < 0:
        return "red"
    return "amber" if days <= threshold else ""


def place_view(db, p, today=None):
    """One place, computed when read: the battery now, the warranty, the usual life, a B.L. bill awaited, the upkeep, the badge
    and its reminders [(kind, what, due date, days, state)]."""
    today = today or _today()
    cur = current_fit(db, p["id"])
    v = {"p": p, "cur": cur, "fitted": None, "till": None, "life": None, "await": None, "upkeep_next": None, "rem": [],
         "badge": ("Not recorded yet", "none"), "battery": "—"}
    upk = p.get("upkeep") or ""
    if upk in UPKEEP and p.get("upkeep_months"):
        last = db.execute("SELECT MAX(done_on) FROM battery_upkeep WHERE place_id=? AND kind=?", (p["id"], upk)).fetchone()[0]
        base = max([d for d in (_iso(last), _iso(cur["fitted_on"]) if cur else None, _iso(p.get("made_at"))) if d is not None] or [today])
        v["upkeep_next"] = add_months(base, p["upkeep_months"])
    if cur:
        f = _iso(cur["fitted_on"])
        v["fitted"] = f
        bits = [x for x in (cur["brand"], cur["ah"] and ("%s Ah" % cur["ah"] if re.fullmatch(r"[\d.]+", str(cur["ah"])) else cur["ah"])) if x]
        n = cur["set_n"] or p.get("set_n")
        v["battery"] = " · ".join(bits) + ((" · set of %d" % n) if (n and n > 1) else "") if bits else (("set of %d" % n) if (n and n > 1) else "recorded")
        if cur["warranty_months"]:
            v["till"] = add_months(f, cur["warranty_months"])
            dd = (v["till"] - today).days
            if dd >= 0:
                v["rem"].append(("warranty", "Warranty ends — test the battery now", v["till"], dd, _state(dd, WARN_DAYS)))
        if p.get("life_months"):
            v["life"] = add_months(f, p["life_months"])
            dd = (v["life"] - today).days
            v["rem"].append(("life", "Usual life reached — plan a replacement", v["life"], dd, _state(dd, WARN_DAYS)))
        if is_bl(p) and paper_of(db, cur["bill_id"], cur["bill_created_at"]) is None:
            v["await"] = (today - f).days
            due = f + datetime.timedelta(days=WARN_DAYS)
            dd = (due - today).days
            v["rem"].append(("bill", "B.L. bill still awaited", due, dd, "red" if dd < 0 else ""))
    if v["upkeep_next"] is not None:
        dd = (v["upkeep_next"] - today).days
        v["rem"].append(("upkeep", UPKEEP[upk][0], v["upkeep_next"], dd, _state(dd, 0)))
    life_dd = (v["life"] - today).days if v["life"] else None
    war_dd = (v["till"] - today).days if v["till"] else None
    if cur:
        if life_dd is not None and life_dd <= 0:
            v["badge"] = ("Due for replacement", "red")
        elif war_dd is not None and 0 <= war_dd <= WARN_DAYS:
            v["badge"] = ("Warranty ends today" if war_dd == 0 else "Warranty ends in %d day%s" % (war_dd, "" if war_dd == 1 else "s"), "amber")
        elif v["await"] is not None:
            v["badge"] = ("Bill awaited %d day%s" % (v["await"], "" if v["await"] == 1 else "s"), "amber")
        elif v["upkeep_next"] is not None and (v["upkeep_next"] - today).days <= 0:
            v["badge"] = (UPKEEP[upk][1], "amber")
        else:
            v["badge"] = ("OK", "ok")
    elif v["upkeep_next"] is not None and (v["upkeep_next"] - today).days <= 0:
        v["badge"] = (UPKEEP[upk][1], "amber")
    v["war_dd"], v["life_dd"] = war_dd, life_dd
    return v


def overview(db, owner, today=None):
    today = today or _today()
    vs = [place_view(db, p, today) for p in places(db, owner)]
    tot = {"due": sum(1 for v in vs if v["cur"] and v["life_dd"] is not None and v["life_dd"] <= 0),
           "warranty": sum(1 for v in vs if v["cur"] and v["war_dd"] is not None and 0 <= v["war_dd"] <= WARN_DAYS),
           "awaited": sum(1 for v in vs if v["await"] is not None), "places": len(vs)}
    groups = [(k, w, GROUP_NOTE[k], [v for v in vs if v["p"]["grp"] == k]) for k, w in GROUPS]
    return tot, groups


def reminders(db, owner, show_all=False, today=None):
    """Renewals' Batteries card: (place, what, due, days, state) -- due soon only, or every upcoming date with ?all=1."""
    today = today or _today()
    out = []
    for p in places(db, owner):
        v = place_view(db, p, today)
        for kind, what, due, dd, st in v["rem"]:
            if show_all or st:
                out.append({"pid": p["id"], "place": p["name"], "grp": GROUP_WORD.get(p["grp"], p["grp"]), "kind": kind, "what": what,
                            "due": due, "days": dd, "state": st, "upkeep": kind == "upkeep"})
    out.sort(key=lambda r: (r["due"], r["place"]))
    return out


# ---------------------------------------------------------------------------------------------- a new machine's place, by itself
_UPS = re.compile(r"\bups\b", re.I)
_INV = re.compile(r"\binverter\b", re.I)


def machine_kind(name, category):
    """S571_BRIEF_R1 C5: the category exactly 'Vehicle' -> Vehicles; the whole word inverter -> Generator and inverters; the whole
    word UPS -> Online UPS when the name says 'online', else Small UPS; anything else -> None."""
    if (category or "").strip() == "Vehicle":
        return "vehicles"
    n = name or ""
    if _INV.search(n):
        return "gen_inv"
    if _UPS.search(n):
        return "online_ups" if re.search(r"online", n, re.I) else "small_ups"
    return None


def auto_places(db):
    """Made on the Batteries page's load (any viewer), under BEGIN IMMEDIATE: a machine added AFTER batteries.since gets one place,
    at most one per (asset_id, asset_created_at) -- the unique index. Idempotent. Returns the number made."""
    since = _setting(db, SINCE, "")
    if not since:
        return 0
    made = 0
    try:
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        try:
            rows = db.execute("SELECT a.id, a.name, a.category, a.created_at, a.hidden, l.visibility lvis, en.name ent FROM assets a "
                              "LEFT JOIN locations l ON l.id=a.location_id LEFT JOIN entities en ON en.id=a.entity_id "
                              "WHERE COALESCE(a.created_at,'')>? ORDER BY a.id", (since,)).fetchall()
        except sqlite3.OperationalError:
            rows = db.execute("SELECT a.id, a.name, a.category, a.created_at, a.hidden, l.visibility lvis, NULL ent FROM assets a "
                              "LEFT JOIN locations l ON l.id=a.location_id WHERE COALESCE(a.created_at,'')>? ORDER BY a.id", (since,)).fetchall()
        for a in rows:
            k = machine_kind(a["name"], a["category"])
            if k is None:
                continue
            if db.execute("SELECT 1 FROM battery_place WHERE asset_id=? AND asset_created_at=?", (a["id"], a["created_at"])).fetchone():
                continue
            ups = k in ("online_ups", "small_ups")
            payer = {"Dr Manoj Clinic": "clinic", "NK Pathology": "nk"}.get((a["ent"] or "").strip(), "confirm")
            own = 1 if (k == "vehicles" or a["hidden"] or (a["lvis"] or "") == "owner_only") else 0
            life = LIFE["car"] if k == "vehicles" else (LIFE["ups"] if ups else LIFE["inverter"])
            upk, every = ("backup", 3) if ups else (("water", 3) if k == "gen_inv" else ("", None))
            db.execute("INSERT OR IGNORE INTO battery_place(grp, name, sub, payer, supplier, warranty_months, life_months, owner_only, set_n, "
                       "upkeep, upkeep_months, sort, asset_id, asset_created_at, auto, made_by, made_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)",
                       (k, (a["name"] or "Machine")[:80], "Added from Machines", payer, BL if ups else JAS, 12 if ups else None, life, own,
                        None, upk, every, 1000 + a["id"], a["id"], a["created_at"], "S571 (from Machines)", _now()))
            made += 1
            _audit(db, "battery_place_auto", {"asset": a["id"], "group": k})
        db.commit()
    except sqlite3.Error as ex:
        try:
            db.rollback()
        except sqlite3.Error:
            pass
        print("S571 auto places: %s" % ex, file=sys.stderr)
    return made


# ---------------------------------------------------------------------------------------------- saving
def save_fit(db, p, f, owner, who=None):
    """'New battery fitted'. The previous battery goes into the history with its removed date = this fitting's date. No commit.
    Refusals raise ValueError (plain words). Returns the new fitting's id."""
    who = _who() if who is None else who
    today = _today()
    d = typed_date(f.get("fitted_on")) or today
    if d > today:
        raise ValueError("The fitted date %s is after today." % dmy(d))
    prev = current_fit(db, p["id"])
    if prev and _iso(prev["fitted_on"]) and _iso(prev["fitted_on"]) > d:
        raise ValueError("A battery fitted on %s is already recorded here — the new one cannot be older." % dmy(prev["fitted_on"]))
    sup = re.sub(r"\s+", " ", str(f.get("supplier") or "")).strip()[:80] or p["supplier"]
    wm = _int(f.get("warranty_months"), 0, 120)
    setn = _int(f.get("set_n"), 1, 50)
    price, old = _num(f.get("price")), _num(f.get("old_amount"))
    for x, w in ((price, "price"), (old, "old-battery amount")):
        if x is not None and x < 0:
            raise ValueError("The %s cannot be below zero." % w)
    links = {}
    for k in ("bill", "card"):
        v = str(f.get(k) or "").strip()
        if v and v != "awaited":
            b = _pickable(db, p, v, owner, today)
            if b is None:
                raise ValueError("That paper cannot be linked here — pick one of %s's papers from the list." % (p["supplier"] or "the supplier"))
            links[k] = b
    if "bill" in links and "card" in links and links["bill"]["id"] == links["card"]["id"]:
        raise ValueError("The bill and the warranty card are the same paper — pick the card separately, or leave it.")
    if prev:
        db.execute("UPDATE battery_fit SET removed_on=? WHERE id=?", (d.isoformat(), prev["id"]))
    cur = db.execute("INSERT INTO battery_fit(place_id, fitted_on, supplier, brand, ah, set_n, warranty_months, price, old_amount, bill_id, "
                     "bill_created_at, card_id, card_created_at, by_whom, at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                     (p["id"], d.isoformat(), sup, re.sub(r"\s+", " ", str(f.get("brand") or "")).strip()[:80],
                      re.sub(r"\s+", " ", str(f.get("ah") or "")).strip()[:20], setn if setn is not None else p.get("set_n"), wm, price, old,
                      links["bill"]["id"] if "bill" in links else None, (links["bill"]["created_at"] or "") if "bill" in links else "",
                      links["card"]["id"] if "card" in links else None, (links["card"]["created_at"] or "") if "card" in links else "",
                      who, _now()))
    _audit(db, "battery_fitted", {"place": p["id"], "fit": cur.lastrowid, "fitted_on": d.isoformat(), "previous": prev["id"] if prev else None,
                                  "bill": links["bill"]["id"] if "bill" in links else None, "card": links["card"]["id"] if "card" in links else None})
    return cur.lastrowid


def link_paper(db, fit_id, bid, as_, owner):
    """Link a paper as a fitting's bill or warranty card. NEVER writes the paper (D664). Returns (place, fit, paper). ValueError /
    PermissionError on refusal. No commit."""
    try:
        fr = db.execute("SELECT * FROM battery_fit WHERE id=? AND voided_at=''", (int(fit_id),)).fetchone()
    except (TypeError, ValueError):
        fr = None
    if fr is None:
        raise ValueError("There is no such battery.")
    p = place(db, fr["place_id"])
    if p is None or (p["owner_only"] and not owner):
        raise PermissionError("Yeh sirf Dr Manoj ke liye hai.")
    if as_ not in ("bill", "card"):
        raise ValueError("Link it as the bill or the warranty card.")
    b = _pickable(db, p, bid, owner)
    if b is None:
        raise ValueError("That paper cannot be linked here — it is not %s's, not of the last %d days, or not yours to see." % (p["supplier"] or "the supplier", PICK_DAYS))
    other = "card" if as_ == "bill" else "bill"
    if fr[other + "_id"] == b["id"] and fr[other + "_created_at"] == (b["created_at"] or ""):
        raise ValueError("%s is already this battery's %s." % (_stamp(b), "warranty card" if other == "card" else "bill"))
    if as_ == "bill":
        held = db.execute("SELECT id FROM battery_fit WHERE voided_at='' AND id<>? AND bill_id=? AND bill_created_at=?",
                          (fr["id"], b["id"], b["created_at"] or "")).fetchone()
        if held:
            raise ValueError("%s is already the bill of another battery." % _stamp(b))
    old = (fr[as_ + "_id"], fr[as_ + "_created_at"])
    db.execute("UPDATE battery_fit SET %s_id=?, %s_created_at=? WHERE id=?" % (as_, as_), (b["id"], b["created_at"] or "", fr["id"]))
    _audit(db, "battery_paper_linked", {"fit": fr["id"], "place": p["id"], "as": as_, "paper": b["id"], "before": old[0]})
    return p, dict(fr), b


# ---------------------------------------------------------------------------------------------- the desk's offer (sorting_desk's S571 part)
def desk_offer(db, b, owner, cur_dest=""):
    """For paper_json: {'bat': {...}} or {}.
    - this paper already linked to a battery the person may see: 'linked' (its words) and 'pre' -- the desk destination the place's
      payer pre-selects in the browser (R1 C6), only while the paper is not sorted yet; 'to confirm' pre-selects nothing;
    - else, a B.L. Computers / Jasoria paper (first word) of the last 90 days: one offer per battery of that supplier whose bill is
      awaited, at a place the person may see: 'Battery fitted at <place> on <date> — this bill?'."""
    if not paper_visible(b, owner):
        return {}
    if not owner and not switch_on(db):                     # S571_FIX1 (K1 C1): batteries.on absent / OFF -- no offer, no pre-select
        return {}
    out = {"link": url_for("s571_link")}
    for fr in fit_of_paper(db, b):
        p = place(db, fr["place_id"])
        if p is None or (p["owner_only"] and not owner):
            continue
        as_bill = fr["bill_id"] == b["id"]
        out["linked"] = "Linked: %s of the battery fitted at %s on %s." % ("the bill" if as_bill else "the warranty card", p["name"], dmy(fr["fitted_on"]))
        out["place"] = p["name"]
        pre = DESK_DEST.get(p["payer"], "")
        if pre and not cur_dest and (b["status"] or "") in ("draft", "captured"):
            out["pre"] = pre
            out["payer"] = PAYER_WORD.get(p["payer"], p["payer"])
        return {"bat": out}
    k = sup1(b["vendor"])
    if not k or not _recent(b, _today()):
        return {}
    offers = []
    for p in places(db, owner):
        if sup1(p["supplier"]) != k:
            continue
        fr = current_fit(db, p["id"])
        if fr is None or paper_of(db, fr["bill_id"], fr["bill_created_at"]) is not None:
            continue
        offers.append({"fit": fr["id"], "text": "Battery fitted at %s on %s — this bill?" % (p["name"], dmy(fr["fitted_on"]))})
    if not offers:
        return {}
    out["offers"] = offers
    return {"bat": out}


# ---------------------------------------------------------------------------------------------- the pages
OFF_LINE = "Yeh page abhi band hai — Dr Manoj chalu karenge."

CSS = """<style>
#s571 .tot{display:flex;flex-wrap:wrap;gap:12px;margin:8px 0 14px}
#s571 .tot div{background:#fff;border:1px solid #DEDED8;border-radius:10px;padding:10px 16px;min-width:170px}
#s571 .tot b{display:block;font-size:24px;font-weight:600}
#s571 section{background:#fff;border:1px solid #DEDED8;border-radius:10px;overflow:hidden;margin:0 0 16px}
#s571 section .gh{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:8px;padding:10px 16px;background:#EDEDE8;border-bottom:1px solid #DEDED8}
#s571 section h3{margin:0;font-size:17px;font-weight:600;color:#1C1C1A}
#s571 .scroll{overflow-x:auto}
#s571 table{width:100%;border-collapse:collapse;font-size:14px;min-width:820px}
#s571 th{text-align:left;font-weight:500;color:#4A4A45;padding:8px 14px}
#s571 td{padding:8px 14px;border-top:1px solid #ECECE6;vertical-align:top}
#s571 .sub{font-size:12px;color:#5A5A55}
#s571 .bdg{font-size:13px;padding:3px 8px;border-radius:6px;white-space:nowrap}
#s571 .bdg.ok{background:#E6F2EE;color:#0E5A45}#s571 .bdg.amber{background:#FFF1D6;color:#7A4E00}#s571 .bdg.red{background:#FDE8E1;color:#8F2D0E}
#s571 .bdg.none{background:#EEF0F2;color:#5A5A55}
#s571 a.fitb{display:inline-block;font-size:13px;padding:7px 12px;border-radius:8px;border:1px solid #0B5F5F;color:#0B5F5F;background:#fff;text-decoration:none;white-space:nowrap}
#s571 .note{border-radius:8px;padding:10px 12px;font-size:14px}
#s571 .note.amber{background:#FFF1D6;color:#7A4E00}#s571 .note.green{background:#E6F2EE;color:#0E5A45}
#s571 form.fit{max-width:760px;display:grid;grid-template-columns:1fr 1fr;gap:8px 14px;align-items:end}
#s571 form.fit .full{grid-column:1/-1}
#s571 form.fit label{display:flex;flex-direction:column;gap:3px;font-size:14px;margin:0}
#s571 form.fit input,#s571 form.fit select{padding:6px 8px;margin:0;max-width:none;width:100%;box-sizing:border-box}
#s571 form.fit h2{margin:0;font-size:20px}
@media (max-width:640px){ #s571 form.fit{grid-template-columns:1fr} }
</style>"""

PAGE_TPL = CSS + """<div id=s571>
<h2 style="margin-bottom:4px">Batteries</h2>
<p class=muted style="margin-top:0">A list of battery places, not batteries: each shows the battery fitted now, its warranty, when it is due, and every battery it has had.</p>
<div class=tot id=s571tot><div><b style="color:#9A3412">{{tot.due}}</b>Due for replacement</div><div><b style="color:#8A5A00">{{tot.warranty}}</b>Warranty ends within 30 days</div><div><b style="color:#8A5A00">{{tot.awaited}}</b>B.L. bill awaited</div><div><b>{{tot.places}}</b>Battery places</div></div>
{% for k, name, note, rows in groups %}<section id="s571g_{{k}}"><div class=gh><h3>{{name}}</h3><span class=muted style="font-size:13px">{{note}}</span></div><div class=scroll>
<table><tr><th>Place</th><th>Battery now</th><th>Fitted</th><th>Warranty till</th><th>Status</th><th><span style="position:absolute;left:-9999px">Action</span></th></tr>
{% for v in rows %}<tr data-place="{{v.p.id}}"><td><a href="{{url_for('s571_place', pid=v.p.id)}}" style="font-weight:500">{{v.p.name}}</a><div class=sub>{{v.p.sub}}{% if v.p.payer == 'confirm' %} · paid by: to confirm{% endif %}</div></td>
<td>{{v.battery}}</td><td style="white-space:nowrap">{{dmy(v.fitted) if v.fitted else '—'}}</td><td style="white-space:nowrap">{{dmy(v.till) if v.till else '—'}}</td>
<td><span class="bdg {{v.badge[1]}}">{{v.badge[0]}}</span></td><td style="text-align:right"><a class=fitb href="{{url_for('s571_fit', pid=v.p.id)}}">New battery fitted</a></td></tr>
{% else %}<tr><td colspan=6 class=muted>No place in this group.</td></tr>{% endfor %}</table></div></section>{% endfor %}
<details class=card id=s571add><summary style="cursor:pointer;font-weight:600">+ Add a battery place</summary>
<form method=post action="{{url_for('s571_place_post')}}" style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-top:8px"><input type=hidden name=do value=add>
<label style="margin:0">Place<input name=name required style="max-width:200px"></label><label style="margin:0">Sub-line<input name=sub style="max-width:180px"></label>
<label style="margin:0">Group<select name=grp>{% for k, w in grps %}<option value="{{k}}">{{w}}</option>{% endfor %}</select></label>
<label style="margin:0">Paid by<select name=payer>{% for k, w in payers if is_owner or k != 'owner' %}<option value="{{k}}"{{' selected' if k == 'confirm'}}>{{w}}</option>{% endfor %}</select></label>
<label style="margin:0">Supplier<input name=supplier placeholder="by the group" style="max-width:150px"></label><label style="margin:0">Batteries in the set<input name=set_n inputmode=numeric style="max-width:80px"></label>
{% if is_owner %}<label style="margin:0;flex-direction:row;gap:6px;align-items:center"><input type=checkbox name=owner_only value=1 style="width:auto"> yours only</label>{% endif %}
<button class="btn small">Add</button></form></details>
<p class=muted style="font-size:14px">A new vehicle, UPS or inverter added in Machines gets its battery place here by itself.{% if made %} <b>{{made}} new place{{'' if made == 1 else 's'}} made from Machines just now.</b>{% endif %}</p>
<p class=muted style="font-size:13px">{% if is_owner %}Home batteries and vehicles are shown to you only. Shavez sees the clinic and lab places when “Batteries for Shavez” is ON on your Switches card. Reception does nothing new.{% else %}Clinic and lab places only.{% endif %}</p>
</div>"""

PLACE_TPL = CSS + """<div id=s571>
<h2 style="margin-bottom:4px">{{p.name}} — history</h2>
<p class=muted style="margin-top:0">{{grp}} · {{p.sub}}{% if p.owner_only %} · yours only{% endif %}{% if mach %} · machine: <a href="{{url_for('asset_view', aid=mach['id'])}}">{{mach['name']}}</a>{% endif %}</p>
<div class=card id=s571reorder><b>Re-order:</b> {{reorder}}</div>
<div class=card><span class="bdg {{v.badge[1]}}">{{v.badge[0]}}</span>{% if v.till %} · warranty till {{dmy(v.till)}}{% endif %}{% if v.life %} · usual life till {{dmy(v.life)}}{% endif %}
 <a class=fitb href="{{url_for('s571_fit', pid=p.id)}}" style="margin-left:10px">New battery fitted</a></div>
<div class=card style="overflow:auto"><table id=s571hist><tr><th>Fitted</th><th>Removed</th><th>Lasted</th><th>Battery</th><th>Cost</th><th>Bill</th><th>Warranty card</th></tr>
{% for h in hist %}<tr><td>{{dmy(h.fitted_on)}}</td><td>{{dmy(h.removed_on) if h.removed_on else '— in use'}}</td><td>{{h.lasted}}</td><td>{{h.battery}}</td><td>{{h.cost}}</td>
<td>{% if h.bill_href %}<a href="{{h.bill_href}}">{{h.bill}}</a>{% elif h.bill %}{{h.bill}}{% elif h.awaited %}<span style="color:#8A5A00">Bill awaited ({{h.awaited}} day{{'' if h.awaited == 1 else 's'}})</span>{% else %}<span class=muted>none linked</span>{% endif %}</td>
<td>{% if h.card_href %}<a href="{{h.card_href}}">{{h.card}}</a>{% elif h.card %}{{h.card}}{% else %}<span class=muted>—</span>{% endif %}</td></tr>
{% else %}<tr><td colspan=7 class=muted>No battery recorded here yet — “New battery fitted” records the one in place now.</td></tr>{% endfor %}</table></div>
{% if v.cur %}<div class=card id=s571links><b>The battery now — its papers</b> <span class=muted>(linking never changes the paper: its lane, section and status stay as they are)</span>
<form method=post action="{{url_for('s571_link')}}" style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-top:8px"><input type=hidden name=fit value="{{v.cur.id}}">
<label style="margin:0">Paper<select name=paper><option value="">— {{p.supplier}}'s papers, last 90 days —</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label style="margin:0">as<select name=as><option value=bill>the bill</option><option value=card>the warranty card</option></select></label><button class="btn small">Link</button></form>
{% if not cands %}<p class=muted style="margin:6px 0 0">No paper of {{p.supplier}} in the last 90 days that you may see.</p>{% endif %}</div>{% endif %}
{% if upk %}<div class=card id=s571upkeep><b>{{upk[0]}}</b> — every {{p.upkeep_months}} month{{'' if p.upkeep_months == 1 else 's'}}; next {{dmy(v.upkeep_next) if v.upkeep_next else '—'}}{% if last_done %} (last done {{dmy(last_done)}}){% endif %}
<form method=post action="{{url_for('s571_done')}}" style="display:inline;margin-left:10px"><input type=hidden name=place value="{{p.id}}"><button class="btn small">Done today</button></form></div>{% endif %}
{% if is_owner %}<details class=card id=s571edit><summary style="cursor:pointer;font-weight:600">Change this place</summary>
<form method=post action="{{url_for('s571_place_post')}}" style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-top:8px"><input type=hidden name=do value=edit><input type=hidden name=id value="{{p.id}}">
<label style="margin:0">Place<input name=name value="{{p.name}}" style="max-width:180px"></label><label style="margin:0">Sub-line<input name=sub value="{{p.sub}}" style="max-width:180px"></label>
<label style="margin:0">Paid by<select name=payer>{% for k, w in payers %}<option value="{{k}}"{{' selected' if k == p.payer}}>{{w}}</option>{% endfor %}</select></label>
<label style="margin:0">Supplier<input name=supplier value="{{p.supplier}}" style="max-width:150px"></label>
<label style="margin:0">Warranty (months)<input name=warranty_months value="{{p.warranty_months if p.warranty_months is not none else ''}}" style="max-width:70px"></label>
<label style="margin:0">Usual life (months)<input name=life_months value="{{p.life_months if p.life_months is not none else ''}}" style="max-width:70px"></label>
<label style="margin:0">Type<input name=btype value="{{p.btype}}" style="max-width:120px"></label><label style="margin:0">Ah<input name=ah value="{{p.ah}}" style="max-width:60px"></label>
<label style="margin:0">V<input name=volts value="{{p.volts}}" style="max-width:60px"></label><label style="margin:0">Set of<input name=set_n value="{{p.set_n if p.set_n is not none else ''}}" style="max-width:60px"></label>
<label style="margin:0;flex-direction:row;gap:6px;align-items:center"><input type=checkbox name=owner_only value=1 style="width:auto"{{' checked' if p.owner_only}}> yours only</label>
<button class="btn small">Save</button></form>
<form method=post action="{{url_for('s571_place_post')}}" style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-top:10px"><input type=hidden name=do value=machine><input type=hidden name=id value="{{p.id}}">
<label style="margin:0">Link to a machine<select name=asset><option value="">— none —</option>{% for a in machines %}<option value="{{a.id}}"{{' selected' if mach and mach['id'] == a.id}}>{{a.name}}</option>{% endfor %}</select></label><button class="btn small">Link</button></form>
<form method=post action="{{url_for('s571_place_post')}}" style="margin-top:10px" onsubmit="return confirm('Take {{p.name}} off the list? Its history is kept.')"><input type=hidden name=do value=remove><input type=hidden name=id value="{{p.id}}"><button class="btn small">Take off the list</button></form>
</details>{% endif %}
</div>"""

FIT_TPL = CSS + """<div id=s571>
<form method=post class="card fit" id=s571fit action="{{url_for('s571_fit', pid=p.id)}}">
<div class="muted full" style="font-size:13px">{{kind}} · {{p.supplier}}{% if p.owner_only %} · yours only{% endif %}</div>
<h2 class=full>New battery fitted — {{p.name}}</h2>
<label>Fitted on<input name=fitted_on value="{{today}}"></label>
<label>Supplier<input name=supplier value="{{p.supplier}}"></label>
{% if bl %}<label>Warranty (months)<input name=warranty_months inputmode=numeric value="{{p.warranty_months if p.warranty_months is not none else ''}}"></label>
<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}" placeholder="N"></label>
<label>Battery (make · type)<input name=brand></label><label>Ah<input name=ah></label>
<label class=full>Bill<select name=bill><option value=awaited>Bill awaited — not scanned yet</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<div class="note amber full">Bill comes with the battery — {% if scan_href %}<a href="{{scan_href}}">scan it</a>{% else %}scan it{% endif %}. If it does not come, the battery shows <b>bill awaited</b> until it reaches the sorting desk.</div>
{% else %}<label>Price ₹<input name=price inputmode=decimal id=s571price></label><label>Old battery ₹<input name=old_amount inputmode=decimal id=s571old></label>
<div class="muted full" id=s571net style="font-size:14px">Net —</div>
<label>Warranty (months)<input name=warranty_months inputmode=numeric value="{{p.warranty_months if p.warranty_months is not none else ''}}" placeholder="from the card"></label>
<label>Batteries in the set<input name=set_n inputmode=numeric value="{{p.set_n if p.set_n is not none else ''}}"></label>
<label>Battery (make · type)<input name=brand></label><label>Ah<input name=ah></label>
<label>Bill<select name=bill><option value=awaited>Not scanned yet — link it later</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<label>Warranty card<select name=card><option value="">Not scanned yet — link it later</option>{% for c in cands %}<option value="{{c.id}}">{{c.text}}</option>{% endfor %}</select></label>
<div class="note green full">Bill and warranty card came with the battery — {% if scan_href %}<a href="{{scan_href}}">scan both</a>{% else %}scan both{% endif %}; type the warranty months from the card.</div>
<script>(function(){function n(i){var v=parseFloat(String(document.getElementById(i).value||'').replace(/[^0-9.]/g,''));return isFinite(v)?v:null;}
function s(){var p=n('s571price'),o=n('s571old'),e=document.getElementById('s571net');e.textContent=(p===null)?'Net —':'Net ₹'+Math.round((p-(o||0))*100)/100;}
document.getElementById('s571price').addEventListener('input',s);document.getElementById('s571old').addEventListener('input',s);})();</script>
{% endif %}
<button class="btn full" style="min-height:44px;font-size:15px">Save</button></form></div>"""

CARD_TPL = """<div class=card id=s571card><h3 style="color:#1f3864">Batteries <span class=muted>({{rows|length}})</span></h3>
<table><tr><th>Place</th><th>Kind</th><th>What</th><th>Due</th><th>Status</th></tr>
{% for r in rows %}<tr class="{{r.state}}"><td><a href="{{url_for('s571_place', pid=r.pid)}}">{{r.place}}</a> <span class=muted>({{r.grp}})</span></td><td>Battery</td><td>{{r.what}}</td><td>{{dmy(r.due)}}</td>
<td>{% if r.state %}<span class="badge {{r.state}}">{{'overdue' if r.days < 0 else (r.days|string)+' days'}}</span>{% else %}<span class=muted>{{r.days}} days</span>{% endif %}{% if r.upkeep %} <form method=post action="{{url_for('s571_done')}}" style="display:inline"><input type=hidden name=place value="{{r.pid}}"><input type=hidden name=back value=renewals><button class="btn small">done</button></form>{% endif %}</td></tr>{% endfor %}</table></div>"""


def _href(bid):
    try:
        return AR._s559_paper_href(bid)
    except Exception:                                                # noqa: BLE001
        return url_for("bill_view", bid=bid)


def _gate(fn):
    """A manager only while batteries.on is ON (absent = OFF); the owner always (the app's checker gate refuses anyone else)."""
    def w(*a, **k):
        if not may_see(AR.get_db()):
            return OFF_LINE, 403
        return fn(*a, **k)
    w.__name__ = fn.__name__
    return w


def page_main():
    db = AR.get_db()
    owner = _owner()
    made = auto_places(db)
    tot, groups = overview(db, owner)
    return AR.page(PAGE_TPL, tot=tot, groups=groups, dmy=dmy, grps=GROUPS, payers=PAYERS, made=made,
                   flow=AR._flow("Batteries", url_for("assets_list")))


def _reorder(db, p):
    last = fits(db, p["id"])
    lf = last[0] if last else {}
    t = p.get("btype") or lf.get("brand") or "[type]"
    ah = p.get("ah") or lf.get("ah") or "[Ah]"
    v = p.get("volts") or "[V]"
    n = p.get("set_n") or lf.get("set_n")
    w = (lf.get("warranty_months") if lf else None) or p.get("warranty_months")
    return "%s · %s Ah · %s V · set of %s · supplier %s · warranty %s · paid by %s" % (
        t, ah if not str(ah).lower().endswith("ah") else str(ah)[:-2].strip(), v if not str(v).lower().endswith("v") else str(v)[:-1].strip(),
        n if n else "[N]", p.get("supplier") or "—", ("%d months" % w) if w else "from the card",
        {"owner": "you"}.get(p["payer"], PAYER_WORD.get(p["payer"], p["payer"])))


def page_place(pid):
    db = AR.get_db()
    p = place_for(db, pid)
    owner = _owner()
    today = _today()
    v = place_view(db, p, today)
    hist = []
    for h in fits(db, p["id"]):
        f, r = _iso(h["fitted_on"]), _iso(h["removed_on"])
        n = months_between(f, r or today)
        b = paper_of(db, h["bill_id"], h["bill_created_at"])
        c = paper_of(db, h["card_id"], h["card_created_at"])
        bv, cv = (b is not None and paper_visible(b, owner)), (c is not None and paper_visible(c, owner))
        cost = None
        if h["price"] is not None:
            cost = rs(h["price"] - (h["old_amount"] or 0))
            if h["old_amount"]:
                cost += " (price %s − old battery %s)" % (rs(h["price"]), rs(h["old_amount"]))
        elif bv and b["total_amount"] is not None:                  # S571_FIX1 (K1 N2): a paper the viewer may not see shows no amount
            cost = rs(b["total_amount"]) + " (the bill)"
        bits = [x for x in (h["brand"], h["ah"] and ("%s Ah" % h["ah"] if re.fullmatch(r"[\d.]+", str(h["ah"])) else h["ah"])) if x]
        hist.append({"fitted_on": h["fitted_on"], "removed_on": h["removed_on"],
                     "lasted": ("%d month%s" % (n, "" if n == 1 else "s")) + ("" if r else " so far") if n is not None else "—",
                     "battery": (" · ".join(bits) or "—") + ((" · set of %d" % h["set_n"]) if (h["set_n"] or 0) > 1 else ""),
                     "cost": cost or "—", "bill": _stamp(b) if bv else ("a paper you do not see" if b is not None else ""),
                     "bill_href": _href(b["id"]) if bv else "", "card": _stamp(c) if cv else ("a paper you do not see" if c is not None else ""),
                     "card_href": _href(c["id"]) if cv else "",
                     "awaited": ((today - f).days if (b is None and not r and is_bl(p) and f) else None)})
    upk = UPKEEP.get(p.get("upkeep") or "")
    last_done = db.execute("SELECT MAX(done_on) FROM battery_upkeep WHERE place_id=? AND kind=?", (p["id"], p.get("upkeep") or "")).fetchone()[0] if upk else None
    mach = machine_of(db, p)
    machines = []
    if owner:
        machines = [dict(a) for a in db.execute("SELECT id, name FROM assets ORDER BY name, id LIMIT 800")]
    return AR.page(PLACE_TPL, p=p, v=v, hist=hist, grp=GROUP_WORD.get(p["grp"], p["grp"]), reorder=_reorder(db, p), dmy=dmy,
                   cands=candidates(db, p, owner, today) if v["cur"] else [], upk=upk, last_done=last_done, mach=mach, machines=machines,
                   payers=PAYERS, flow=AR._flow(p["name"], url_for("s571_page")))


def page_fit(pid):
    db = AR.get_db()
    p = place_for(db, pid)
    owner = _owner()
    if request.method == "POST":
        try:
            save_fit(db, p, request.form, owner)
            db.commit()
            flash("Saved: a new battery at %s, fitted %s. The one before is in the history." % (p["name"], dmy(typed_date(request.form.get("fitted_on")) or _today())))
            return redirect(url_for("s571_place", pid=p["id"]))
        except ValueError as e:
            db.rollback()
            flash(str(e) + " Nothing was saved.")
            return redirect(url_for("s571_fit", pid=p["id"]))
    scan = ""
    try:
        if "s568_add" in AR.app.view_functions:
            scan = url_for("s568_add")
    except Exception:                                                # noqa: BLE001
        scan = ""
    return AR.page(FIT_TPL, p=p, bl=is_bl(p), kind=GROUP_KIND.get(p["grp"], "Battery place"), today=dmy(_today()),
                   cands=candidates(db, p, owner), scan_href=scan, flow=AR._flow("New battery fitted", url_for("s571_place", pid=p["id"])))


def post_link():
    db = AR.get_db()
    js = request.is_json
    d = (request.get_json(silent=True) or {}) if js else request.form
    owner = _owner()
    fit_id = d.get("fit")
    try:
        p, fr, b = link_paper(db, fit_id, d.get("paper"), str(d.get("as") or "bill"), owner)
        db.commit()
        msg = "Linked: %s is the %s of the battery fitted at %s on %s. The paper itself is unchanged." % (
            _stamp(b), "warranty card" if str(d.get("as") or "bill") == "card" else "bill", p["name"], dmy(fr["fitted_on"]))
        if js:
            return jsonify({"ok": True, "message": msg})
        flash(msg)
        return redirect(url_for("s571_place", pid=p["id"]))
    except PermissionError as e:
        db.rollback()
        if js:
            return jsonify({"ok": False, "error": str(e)}), 403
        return str(e), 403
    except ValueError as e:
        db.rollback()
        if js:
            return jsonify({"ok": False, "error": str(e) + " Nothing was linked."}), 400
        flash(str(e) + " Nothing was linked.")
        fr = None
        try:
            fr = db.execute("SELECT place_id FROM battery_fit WHERE id=?", (int(fit_id),)).fetchone()
        except (TypeError, ValueError, sqlite3.Error):
            fr = None
        return redirect(url_for("s571_place", pid=fr[0]) if fr else url_for("s571_page"))


def post_done():
    db = AR.get_db()
    try:
        pid = int(request.form.get("place") or 0)
    except ValueError:
        pid = 0
    p = place_for(db, pid)
    k = p.get("upkeep") or ""
    if k not in UPKEEP:
        flash("%s has no upkeep to mark." % p["name"])
    else:
        db.execute("INSERT INTO battery_upkeep(place_id, kind, done_on, by_whom, at) VALUES(?,?,?,?,?)",
                   (p["id"], k, _today().isoformat(), _who(), _now()))
        _audit(db, "battery_upkeep_done", {"place": p["id"], "kind": k})
        db.commit()
        flash("Done: %s at %s, today. The next one is due %s." % (UPKEEP[k][0], p["name"], dmy(add_months(_today(), p["upkeep_months"]))))
    if request.form.get("back") == "renewals":
        return redirect(url_for("renewals"))
    return redirect(url_for("s571_place", pid=p["id"]))


def post_place():
    db = AR.get_db()
    f = request.form
    do = (f.get("do") or "").strip()
    owner = _owner()
    try:
        if do == "add":
            name = re.sub(r"\s+", " ", f.get("name") or "").strip()[:80]
            if not name:
                raise ValueError("Type the place's name.")
            grp = f.get("grp") if f.get("grp") in GROUP_WORD else "small_ups"
            payer = f.get("payer") if f.get("payer") in PAYER_WORD else "confirm"
            if payer == "owner" and not owner:
                payer = "confirm"
            ups = grp in ("online_ups", "small_ups")
            sup = re.sub(r"\s+", " ", f.get("supplier") or "").strip()[:80] or (BL if ups else JAS)
            own = 1 if (owner and f.get("owner_only")) else 0
            life = LIFE["ups"] if ups else (LIFE["car"] if grp == "vehicles" else LIFE["inverter"])
            upk, every = ("backup", 3) if ups else (("water", 3) if grp == "gen_inv" else ("", None))
            cur = db.execute("INSERT INTO battery_place(grp, name, sub, payer, supplier, warranty_months, life_months, owner_only, set_n, upkeep, "
                             "upkeep_months, sort, made_by, made_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                             (grp, name, re.sub(r"\s+", " ", f.get("sub") or "").strip()[:80], payer, sup, 12 if sup1(sup) == "bl" else None,
                              life, own, _int(f.get("set_n"), 1, 50), upk, every, 900, _who(), _now()))
            _audit(db, "battery_place_added", {"id": cur.lastrowid, "group": grp, "payer": payer, "owner_only": own})
            db.commit()
            flash("Added: %s (%s)." % (name, GROUP_WORD[grp]))
            return redirect(url_for("s571_place", pid=cur.lastrowid))
        if not owner:
            abort(403)
        pid = int(f.get("id") or 0)
        p = place(db, pid)
        if p is None:
            abort(404)
        if do == "edit":
            new = {"name": re.sub(r"\s+", " ", f.get("name") or "").strip()[:80] or p["name"],
                   "sub": re.sub(r"\s+", " ", f.get("sub") or "").strip()[:80],
                   "payer": f.get("payer") if f.get("payer") in PAYER_WORD else p["payer"],
                   "supplier": re.sub(r"\s+", " ", f.get("supplier") or "").strip()[:80] or p["supplier"],
                   "warranty_months": _int(f.get("warranty_months"), 0, 120), "life_months": _int(f.get("life_months"), 1, 240),
                   "btype": re.sub(r"\s+", " ", f.get("btype") or "").strip()[:60], "ah": re.sub(r"\s+", " ", f.get("ah") or "").strip()[:20],
                   "volts": re.sub(r"\s+", " ", f.get("volts") or "").strip()[:20], "set_n": _int(f.get("set_n"), 1, 50),
                   "owner_only": 1 if f.get("owner_only") else 0}
            ch = {k: v for k, v in new.items() if v != p[k]}
            if ch:
                db.execute("UPDATE battery_place SET %s WHERE id=?" % ",".join("%s=?" % k for k in ch), tuple(ch.values()) + (pid,))
                _audit(db, "battery_place_changed", {"id": pid, "from": {k: p[k] for k in ch}, "to": ch})
            msg = ("Saved: %s." if ch else "Unchanged: %s.") % new["name"]
        elif do == "machine":
            aid = str(f.get("asset") or "").strip()
            if not aid:
                db.execute("UPDATE battery_place SET asset_id=NULL, asset_created_at=NULL WHERE id=?", (pid,))
                msg = "%s is no longer linked to a machine." % p["name"]
            else:
                a = db.execute("SELECT id, name, created_at FROM assets WHERE id=?", (int(aid),)).fetchone()
                if a is None:
                    raise ValueError("There is no such machine.")
                other = db.execute("SELECT name FROM battery_place WHERE asset_id=? AND asset_created_at=? AND id<>?", (a["id"], a["created_at"], pid)).fetchone()
                if other:
                    raise ValueError("%s is already linked to the place %s." % (a["name"], other[0]))
                db.execute("UPDATE battery_place SET asset_id=?, asset_created_at=? WHERE id=?", (a["id"], a["created_at"], pid))
                msg = "%s is linked to the machine %s." % (p["name"], a["name"])
            _audit(db, "battery_place_machine", {"id": pid, "asset": aid or None})
        elif do == "remove":
            db.execute("UPDATE battery_place SET active=0 WHERE id=?", (pid,))
            _audit(db, "battery_place_removed", {"id": pid})
            msg = "%s is off the list (its history is kept)." % p["name"]
            db.commit()
            flash(msg)
            return redirect(url_for("s571_page"))
        else:
            abort(400)
        db.commit()
        flash(msg)
        return redirect(url_for("s571_place", pid=pid))
    except ValueError as e:
        db.rollback()
        flash(str(e) + " Nothing was saved.")
        return redirect(request.referrer or url_for("s571_page"))


def renewals_card(show_all=False):
    """For the Renewals page (one hook there, beside d664's warranty card): '' when there is nothing to show or this person may not
    see the batteries; '' on any error -- that page must never fail because of this card."""
    try:
        db = AR.get_db()
        if not may_see(db):
            return ""
        rows = reminders(db, _owner(), bool(show_all))
        return Markup(render_template_string(CARD_TPL, rows=rows, dmy=dmy)) if rows else ""
    except Exception as ex:                                          # noqa: BLE001
        print("S571 renewals card: %s" % ex, file=sys.stderr)
        return ""


def menu_items(role):
    """For the scan app's one menu (asset_register._s559_items, after Machines): Batteries -- the owner; a manager while the switch
    is ON. Nothing for anyone else."""
    try:
        if role == "owner" or (role == "manager" and switch_on(AR.get_db())):
            return [("s571_page", "Batteries", url_for("s571_page"))]
    except Exception:                                                # noqa: BLE001
        pass
    return []


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):
    """Called once, at the foot of asset_register.py, after the S568 block."""
    global AR, MOUNTED
    AR = ar
    ensure_at_mount(ar.DB_PATH)
    app, cr = ar.app, ar.checker_required
    app.add_url_rule("/batteries", "s571_page", cr(_gate(page_main)))
    app.add_url_rule("/batteries/place/<int:pid>", "s571_place", cr(_gate(page_place)))
    app.add_url_rule("/batteries/fit/<int:pid>", "s571_fit", cr(_gate(page_fit)), methods=["GET", "POST"])
    app.add_url_rule("/batteries/link", "s571_link", cr(_gate(post_link)), methods=["POST"])
    app.add_url_rule("/batteries/done", "s571_done", cr(_gate(post_done)), methods=["POST"])
    app.add_url_rule("/batteries/place", "s571_place_post", cr(_gate(post_place)), methods=["POST"])
    app.jinja_env.globals.update(s571_battery_card=renewals_card)
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data step:  python3 batteries.py --ensure <assets.db>
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        t, n = ensure_path(sys.argv[2])
        print("batteries %s: tables ready (%s); battery places %d" % (VERSION, ", ".join(t), n))
    else:
        print(__doc__)
