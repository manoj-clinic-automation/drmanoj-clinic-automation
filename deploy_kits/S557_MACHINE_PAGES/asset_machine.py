#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""asset_machine.py -- S557_MACHINE_PAGES (D719: "an asset's parts, cover history and spends, each with its scanned bill").

THE OWNER'S RULING
    The machine page (/assets/<id>) carries, under its own details: one cover line at the top ("Covered: AMC by <provider>
    till dd-mm-yyyy" / "Under warranty till ..." / "No cover"; amber within 30 days of its end, red once lapsed) and one line
    of totals; then three folds -- Parts, Cover history, Spends -- each row with its scanned bill ("its paper", B-____).
    Every live cover and every part's warranty puts ONE reminder on the renewals list. A paper filed as Clinic equipment can
    become a new machine record, pre-filled from the paper, keeping the paper as its purchase bill. Nothing is ever deleted:
    a part is marked removed, a cover is voided, a reminder is resolved.

WHAT THIS FILE IS
    A part of the asset app (asset_register.py), mounted by one guarded import at its foot, after sorting_desk.py: if this
    file cannot load, the app runs exactly as before (its hooks there fall back to nothing). Its addresses (the /scanapp
    prefix is added by the app's middleware):
        POST /assets/<id>/parts/add            POST /assets/<id>/parts/<pid>/remove
        POST /assets/<id>/covers/add           POST /assets/<id>/covers/<cid>/void
        POST /assets/<id>/spends/add           POST /assets/<id>/spends/<sid>/paper
        GET|POST /bills/<id>/machine           a new machine record from a paper (the owner)
    The same gate as the asset pages (owner and manager; reception never). Switch `machine.on` (absent = OFF): while OFF a
    manager sees the machine page exactly as before and every route here refuses him; the owner always has it.

FIX ROUND 1 (S557_FIX1, the independent review's BL1 / C1)
    No table uses AUTOINCREMENT, so SQLite re-issues the id of a deleted newest machine, paper or reminder. A part / cover is
    therefore shown on a machine only when its asset_created_at equals that machine's assets.created_at, and a part / cover /
    spend shows a paper only when its bill_created_at equals that paper's bills.created_at (both written in the request that
    makes the link). The heal (at every start and when Renewals opens) DETACHES a row whose fingerprint no longer holds --
    asset_id = -asset_id, or bill_id = NULL -- audited in desk_audit, never deleted. A reminder is S557's own only if its id is
    the row's expiry_id, it is entity='asset' for that machine and its label starts with one of OWN_PREFIXES; any other row is
    never updated or resolved -- the link is let go and a fresh reminder made.

WHAT IT DELIBERATELY DOES NOT DO
    It moves or changes no field of an existing machine (the old contract fields are only shown, read-only). It never
    deletes a row or a file. It never links a pharmacy paper, a patient's paper, or (for a manager) a Personal paper.
    Standard library and Flask only.
"""
import datetime
import functools
import json
import re
import sqlite3
import sys
import time

from flask import abort, flash, g, redirect, render_template_string, request, url_for
from markupsafe import Markup

VERSION = "S557"
AR = None                     # the asset app's module, handed in by init()
TODAY = None                  # the walk sets a made-up day here
MOUNTED = False
SWITCH = "machine.on"
PATIENT = "patient_paper"
REMIND_DEFAULT = 30
KINDS = (("warranty", "Warranty"), ("amc", "AMC"), ("cmc", "CMC"), ("insurance", "Insurance"), ("other", "Other"))
KIND_NAME = dict(KINDS)
# S557_FIX1 (BL1): the ONE list of S557's own reminder labels. A reminder is S557's own only when its id is the row's
# expiry_id, it is entity='asset' for the row's machine, AND its label starts with one of these (the app's own labels --
# 'Warranty', 'Contract renewal', 'Item expiry', 'Part warranty: x' -- never do).
OWN_PREFIXES = tuple(n + " — " for _k, n in KINDS) + ("Cover — ", "Part warranty — ")
SPEND_TYPES = (("Repair", "Repair"), ("Other service", "Service visit"), ("Spare purchase", "Spare purchase"))
EQUIP_CATEGORY = "Dr MK Clinic Equipment"
CLINIC_ENTITY = "Dr Manoj Clinic"

DDL = (
    "CREATE TABLE IF NOT EXISTS asset_part(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, name TEXT NOT NULL, make TEXT, "
    "model TEXT, serial TEXT, fitted_on TEXT, warranty_till TEXT, bill_id INTEGER, removed_on TEXT, removed_by TEXT, "
    "expiry_id INTEGER, by_whom TEXT, at TEXT, asset_created_at TEXT, bill_created_at TEXT)",
    "CREATE TABLE IF NOT EXISTS asset_cover(id INTEGER PRIMARY KEY, asset_id INTEGER NOT NULL, kind TEXT NOT NULL CHECK(kind IN "
    "('warranty','amc','cmc','insurance','other')), provider TEXT, from_day TEXT, till_day TEXT NOT NULL, cost REAL, bill_id "
    "INTEGER, remind_days INTEGER NOT NULL DEFAULT 30, expiry_id INTEGER, voided_at TEXT NOT NULL DEFAULT '', voided_by TEXT NOT "
    "NULL DEFAULT '', by_whom TEXT, at TEXT, asset_created_at TEXT, bill_created_at TEXT)",
)
# S557_FIX1 (BL1, C1): no table here uses AUTOINCREMENT, so SQLite re-issues the id of a deleted newest machine or paper. A
# link is therefore trusted only with its fingerprint: the machine's assets.created_at (asset_created_at) and the paper's
# bills.created_at (bill_created_at), written in the same request that makes the link. Additive columns, guarded for two workers.
FP_COLUMNS = (("asset_part", "asset_created_at"), ("asset_part", "bill_created_at"),
              ("asset_cover", "asset_created_at"), ("asset_cover", "bill_created_at"),
              ("service_logs", "bill_id"), ("service_logs", "bill_created_at"))


class Refused(Exception):
    """One plain line for the person; nothing is saved."""


# ---------------------------------------------------------------------------------------------- the database's part
def ensure(db):
    """Additive and idempotent: the two tables, service_logs.bill_id and the fingerprint columns (S557_FIX1). Two gunicorn
    workers start at once: 'already exists' / 'duplicate column' from the second is normal."""
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    for tbl, col in FP_COLUMNS:
        have = {r[1] for r in db.execute("PRAGMA table_info(%s)" % tbl)}
        if have and col not in have:
            try:
                db.execute("ALTER TABLE %s ADD COLUMN %s %s" % (tbl, col, "INTEGER" if col == "bill_id" else "TEXT"))
            except sqlite3.OperationalError as ex:
                if "duplicate column" not in str(ex).lower():
                    raise
    db.commit()


def _fp_ok(db):
    """True when every fingerprint column is present (ensure has run)."""
    try:
        for tbl, col in FP_COLUMNS:
            if col not in {r[1] for r in db.execute("PRAGMA table_info(%s)" % tbl)}:
                return False
        return True
    except sqlite3.Error:
        return False


def asset_fp(db, aid):
    """The machine's fingerprint (assets.created_at), or None when there is no such machine."""
    r = db.execute("SELECT created_at FROM assets WHERE id=?", (aid,)).fetchone() if aid else None
    return r[0] if r else None


def bill_fp(db, bid):
    """The paper's fingerprint (bills.created_at), or None when there is no such paper."""
    r = db.execute("SELECT created_at FROM bills WHERE id=?", (bid,)).fetchone() if bid else None
    return r[0] if r else None


def paper_ok(db, bid, fp):
    """A row's paper link is trusted only when the paper still carries the fingerprint stored with the link."""
    return bool(bid) and fp is not None and bill_fp(db, bid) == fp


def _own_reminder(row, aid):
    """S557_FIX1 (BL1): an expiries row is S557's own for this machine only if entity='asset', entity_id = the machine and its
    label starts with one of OWN_PREFIXES (the id test -- id = the row's expiry_id -- is made by the caller)."""
    return (row is not None and row["entity"] == "asset" and row["entity_id"] == aid
            and str(row["label"] or "").startswith(OWN_PREFIXES))


def strays(db):
    """S557_FIX1: the rows whose link no longer holds -- (machine, paper):
    machine: [(table, row id, asset_id, expiry_id)] -- a part / cover whose machine is gone or is a different machine now
             (assets.created_at differs from asset_created_at, or the fingerprint is NULL);
    paper:   [(table, row id, bill_id)] -- a part / cover / spend whose paper is gone or is a different paper now."""
    mach, pap = [], []
    for tbl in ("asset_part", "asset_cover"):
        for r in db.execute("SELECT t.id, t.asset_id, t.expiry_id FROM %s t WHERE t.asset_id>0 AND NOT EXISTS (SELECT 1 FROM assets a "
                            "WHERE a.id=t.asset_id AND t.asset_created_at IS NOT NULL AND a.created_at=t.asset_created_at) ORDER BY t.id" % tbl):
            mach.append((tbl, r[0], r[1], r[2]))
    for tbl in ("asset_part", "asset_cover", "service_logs"):
        for r in db.execute("SELECT t.id, t.bill_id FROM %s t WHERE t.bill_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM bills b "
                            "WHERE b.id=t.bill_id AND t.bill_created_at IS NOT NULL AND b.created_at=t.bill_created_at) ORDER BY t.id" % tbl):
            pap.append((tbl, r[0], r[1]))
    return mach, pap


def detach(db, mach, pap):
    """Detach (never delete): a stray part / cover gets asset_id = -asset_id and its expiry link cleared; a stray paper link
    gets bill_id = NULL. Each is audited in desk_audit with what it was. No commit."""
    for tbl, rid, aid, eid in mach:
        db.execute("UPDATE %s SET asset_id=-asset_id, expiry_id=NULL WHERE id=? AND asset_id=?" % tbl, (rid, aid))
        _audit(db, "machine_detached", {"table": tbl, "row": rid, "asset": aid, "expiry_id": eid, "was": "machine re-issued or gone"})
    for tbl, rid, bid in pap:
        db.execute("UPDATE %s SET bill_id=NULL, bill_created_at=NULL WHERE id=? AND bill_id=?" % tbl, (rid, bid))
        _audit(db, "machine_paper_detached", {"table": tbl, "row": rid, "bill": bid, "was": "paper re-issued or gone"})
    return len(mach) + len(pap)


def _tables_ok(db):
    try:
        n = db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name IN ('asset_part','asset_cover','expiries','assets')").fetchone()[0]
        return n == 4
    except sqlite3.Error:
        return False


def _cover_label(c):
    return "%s — %s" % (KIND_NAME.get(c["kind"], "Cover"), (c["provider"] or "").strip() or "no provider named")


def _part_label(p):
    return "Part warranty — %s" % ((p["name"] or "").strip() or "a part")


def _wanted(db, aid, afp):
    """[(table, row id, expiry_id, desired)] for one machine -- only the rows made on THIS machine (asset_created_at = its
    created_at). desired = (label, due, threshold, resolved) for a reminder that must exist, or ('resolve',) for one that may
    exist and must be resolved."""
    out = []
    covers = db.execute("SELECT * FROM asset_cover WHERE asset_id=? AND asset_created_at=? ORDER BY id", (aid, afp)).fetchall()
    cur = {}
    for c in covers:
        if c["voided_at"]:
            continue
        k = ((c["till_day"] or ""), c["id"])
        if c["kind"] not in cur or k > cur[c["kind"]][0]:
            cur[c["kind"]] = (k, c["id"])
    for c in covers:
        if c["voided_at"] or cur.get(c["kind"], (None, None))[1] != c["id"]:
            out.append(("asset_cover", c["id"], c["expiry_id"], ("resolve",)))          # voided, or an earlier period
        else:
            out.append(("asset_cover", c["id"], c["expiry_id"],
                        (_cover_label(c), c["till_day"], int(c["remind_days"] or REMIND_DEFAULT), 0)))
    for p in db.execute("SELECT * FROM asset_part WHERE asset_id=? AND asset_created_at=? ORDER BY id", (aid, afp)).fetchall():
        if p["removed_on"] or not (p["warranty_till"] or "").strip():
            out.append(("asset_part", p["id"], p["expiry_id"], ("resolve",)))
        else:
            out.append(("asset_part", p["id"], p["expiry_id"], (_part_label(p), p["warranty_till"], REMIND_DEFAULT, 0)))
    return out


def sync_asset(db, aid, dry=False):
    """One machine's reminders on the renewals list (the expiries table): exactly one row per live cover (the newest period
    of each kind) and per live part with a warranty -- created once, kept in expiry_id, updated, never duplicated; a newer
    cover's older period, a voided cover and a removed part have theirs resolved. No commit. Returns the changes (made, or
    needed when dry)."""
    afp = asset_fp(db, aid)
    if afp is None:
        return 0                                                     # the machine is gone: nothing is re-created for it
    n = 0
    for tbl, rid, eid, want in _wanted(db, aid, afp):
        row = db.execute("SELECT * FROM expiries WHERE id=?", (eid,)).fetchone() if eid else None
        if row is not None and not _own_reminder(row, aid):
            # S557_FIX1 (BL1): the id now belongs to a reminder S557 did not make (an id re-issued by SQLite) -- it is never
            # updated or resolved; this row lets go of it and gets a fresh reminder of its own below.
            n += 1
            if not dry:
                db.execute("UPDATE %s SET expiry_id=NULL WHERE id=?" % tbl, (rid,))
                _audit(db, "machine_reminder_let_go", {"table": tbl, "row": rid, "asset": aid, "expiry_id": eid})
            row = None
            if want[0] == "resolve":
                continue
        if want[0] == "resolve":
            if row is not None and row["resolved"] != 1:
                n += 1
                if not dry:
                    db.execute("UPDATE expiries SET resolved=1 WHERE id=?", (row["id"],))
            continue
        label, due, thr, res = want
        if row is None:
            n += 1
            if not dry:
                # re-link first: this machine's own reminder of the same label (S557's form -- the same three tests) that no
                # other cover or part holds
                own = db.execute("SELECT * FROM expiries WHERE entity='asset' AND entity_id=? AND label=? "
                                 "AND id NOT IN (SELECT expiry_id FROM asset_cover WHERE expiry_id IS NOT NULL "
                                 "UNION SELECT expiry_id FROM asset_part WHERE expiry_id IS NOT NULL) ORDER BY resolved, id DESC LIMIT 1",
                                 (aid, label)).fetchone()
                if own is not None and not _own_reminder(own, aid):
                    own = None
                if own:
                    db.execute("UPDATE expiries SET due_date=?, threshold_days=?, resolved=? WHERE id=?", (due, thr, res, own[0]))
                    new_id = own[0]
                else:
                    new_id = db.execute("INSERT INTO expiries(entity, entity_id, label, due_date, threshold_days, resolved) "
                                        "VALUES('asset',?,?,?,?,?)", (aid, label, due, thr, res)).lastrowid
                db.execute("UPDATE %s SET expiry_id=? WHERE id=?" % tbl, (new_id, rid))
        elif (row["label"], row["due_date"], row["threshold_days"], row["resolved"]) != (label, due, thr, res):
            n += 1
            if not dry:
                db.execute("UPDATE expiries SET label=?, due_date=?, threshold_days=?, resolved=? WHERE id=?",
                           (label, due, thr, res, row["id"]))
    return n


def _asset_ids(db):
    return [r[0] for r in db.execute("SELECT asset_id FROM asset_cover WHERE asset_id>0 UNION SELECT asset_id FROM asset_part "
                                     "WHERE asset_id>0 ORDER BY 1")]


def heal(db):
    """The ensure/heal: first detaches every part / cover / paper link whose fingerprint no longer holds (S557_FIX1), then
    re-links any cover or part whose reminder is missing and brings every reminder into line. Writes only when something is
    out of line; then under one write lock (two workers never both create the same reminder)."""
    if not _tables_ok(db) or not _fp_ok(db):
        return 0
    db.row_factory = sqlite3.Row
    mach, pap = strays(db)
    if not (mach or pap) and not sum(sync_asset(db, a, dry=True) for a in _asset_ids(db)):
        return 0
    own = not db.in_transaction
    if own:
        db.execute("BEGIN IMMEDIATE")
    try:
        mach, pap = strays(db)                                       # read again under the lock
        n = detach(db, mach, pap)
        n += sum(sync_asset(db, a) for a in _asset_ids(db))
        if own:
            db.commit()
        return n
    except Exception:
        if own:
            db.rollback()
        raise


def ensure_at_mount(db_path, tries=3, wait=1.0, timeout=3):
    """At mount, in each worker: the tables, then the heal. 'database is locked' is retried briefly and then left to the
    installer's data step and the next start, so the pages still mount."""
    for i in range(max(1, tries)):
        db = None
        try:
            db = sqlite3.connect(db_path, timeout=timeout)
            db.row_factory = sqlite3.Row
            ensure(db)
            heal(db)
            return True
        except sqlite3.OperationalError as ex:
            if "locked" not in str(ex).lower():
                raise
            if i + 1 < tries:
                time.sleep(wait)
        finally:
            if db is not None:
                db.close()
    print("asset_machine: the database stayed locked at mount; left to the installer's data step", file=sys.stderr)
    return False


def ensure_path(db_path):
    """For the installer's data step: the tables and the column, then the heal. Returns the reminders healed."""
    con = sqlite3.connect(db_path, timeout=20)
    con.row_factory = sqlite3.Row
    try:
        ensure(con)
        return heal(con)
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


def machine_on(db):
    try:
        r = db.execute("SELECT value FROM settings WHERE key=?", (SWITCH,)).fetchone()
        return bool(r and (r[0] or "").strip().lower() == "on")
    except sqlite3.Error:
        return False


def _iso(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:                                                # noqa: BLE001
        return None


def dmy(s):
    d = _iso(s)
    return d.strftime("%d-%m-%Y") if d else (s or "")


_DMY = re.compile(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4}|\d{2})")
_YMD = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")


def parse_date(s):
    """dd-mm-yyyy, d-m-yy, dd/mm/yyyy (day first; a two-digit year is 20yy) or yyyy-mm-dd -> a date; else None (as the desk)."""
    t = str(s if s is not None else "").strip()
    try:
        m = _YMD.fullmatch(t)
        if m:
            return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        m = _DMY.fullmatch(t)
        if m:
            return datetime.date(int(m.group(3)) + (2000 if len(m.group(3)) == 2 else 0), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None
    return None


def _date(v, what, required=False):
    t = str(v or "").strip()
    if not t:
        if required:
            raise Refused("Type the %s (dd-mm-yyyy)." % what)
        return None
    d = parse_date(t)
    if d is None:
        raise Refused("The %s “%s” is not understood — type it as dd-mm-yyyy. Nothing was saved." % (what, t[:20]))
    return d.isoformat()


def _money(v):
    s = str(v if v is not None else "").replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").strip()
    if not s:
        return None
    try:
        n = float(s)
    except ValueError:
        n = None
    if n is None or n != n or n in (float("inf"), float("-inf")) or n < 0:
        raise Refused("The amount “%s” is not a number. Nothing was saved." % str(v)[:20])
    return n


def _txt(v, n=120):
    return (str(v or "").strip()[:n]) or None


def inr(x):
    if x is None:
        return "—"
    return "₹" + AR._inr(x)


def _audit(db, action, detail):
    """Everything without a bill goes to the desk's audit (desk_audit, S551); a linked paper also gets a bill audit row."""
    try:
        at = AR._now_ist() if AR is not None else (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                   (at, _who() or "S557 heal", action, json.dumps(detail or {}, ensure_ascii=False)[:500]))
    except sqlite3.OperationalError:
        pass


# ---------------------------------------------------------------------------------------------- "its paper" (A6)
def _lane(b):
    return b["lane"] or AR.KIND_LANE.get(b["kind"], "clinic")


def _stamp(b):
    return b["stamp_no"] or ("#%d" % b["id"])


def find_paper(db, no):
    t = re.sub(r"\s+", "", str(no or "")).upper()
    if not t:
        return None
    b = db.execute("SELECT * FROM bills WHERE upper(stamp_no)=?", (t,)).fetchone()
    if b is None:
        m = re.fullmatch(r"B?-?(\d{1,7})", t)
        if m:
            b = db.execute("SELECT * FROM bills WHERE upper(stamp_no)=?", ("B-%04d" % int(m.group(1)),)).fetchone()
    return b


def refusal(b, owner):
    """Why this person may not link (or see) this paper here -- '' when they may."""
    if b is None:
        return "There is no such paper."
    if _lane(b) == "pharmacy":
        return "%s is a pharmacy paper — it belongs to the Sanjeevni side and is not linked to a machine." % _stamp(b)
    if (b["subgroup"] or "") == PATIENT:
        return "%s is a patient’s paper — it belongs to the surgical case pack, not to a machine." % _stamp(b)
    if (b["subgroup"] or "") == "personal" and not owner:
        return "%s cannot be linked from here." % _stamp(b)
    return ""


def paper_from_box(db, v, owner):
    """The 'B-____' box: '' -> None; a paper this person may see -> its id; anything else -> Refused (one line)."""
    if not str(v or "").strip():
        return None
    b = find_paper(db, v)
    if b is None:
        raise Refused("There is no paper numbered %s. Nothing was saved." % str(v).strip()[:20])
    why = refusal(b, owner)
    if why:
        raise Refused(why + " Nothing was saved.")
    return b["id"]


def _paper_view(db, bid, fp, owner, show_price):
    """{stamp, href} for a row's paper, or None (none linked, the paper is not the one linked -- its fingerprint differs,
    S557_FIX1 -- or not for this person's eyes)."""
    if not bid:
        return None
    b = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    if b is None or fp is None or b["created_at"] != fp or refusal(b, owner) or not show_price:
        return None
    return {"stamp": _stamp(b), "href": url_for("bill_view", bid=b["id"])}


def linked(db, bid, owner):
    """[(asset id, name, as)] -- the machines this paper is linked to, as purchase / part / cover / spend; only the machines
    this person may see (a hidden or owner-only machine never shows to a manager)."""
    out = []
    # S557_FIX1: a part / cover / spend counts only when the paper still carries the fingerprint stored with the link, and a
    # part / cover only on the machine it was made on (asset_created_at). The purchase link is the app's own assets.bill_id.
    fpb = "(SELECT b.created_at FROM bills b WHERE b.id=?)"
    q = (("purchase", "SELECT a.id, a.name, a.hidden, l.visibility FROM assets a JOIN locations l ON l.id=a.location_id WHERE a.bill_id=?", 1),
         ("part", "SELECT a.id, a.name, a.hidden, l.visibility FROM asset_part p JOIN assets a ON a.id=p.asset_id AND a.created_at=p.asset_created_at "
                  "JOIN locations l ON l.id=a.location_id WHERE p.bill_id=? AND p.bill_created_at=" + fpb, 2),
         ("cover", "SELECT a.id, a.name, a.hidden, l.visibility FROM asset_cover c JOIN assets a ON a.id=c.asset_id AND a.created_at=c.asset_created_at "
                   "JOIN locations l ON l.id=a.location_id WHERE c.bill_id=? AND c.voided_at='' AND c.bill_created_at=" + fpb, 2),
         ("spend", "SELECT a.id, a.name, a.hidden, l.visibility FROM service_logs s JOIN assets a ON a.id=s.asset_id JOIN locations l ON l.id=a.location_id "
                   "WHERE s.bill_id=? AND s.bill_created_at=" + fpb, 2))
    seen = set()
    for as_, sql, np_ in q:
        try:
            rows = db.execute(sql, (bid,) * np_).fetchall()
        except sqlite3.Error:
            continue
        for r in rows:
            if not owner and (r["hidden"] or r["visibility"] == "owner_only"):
                continue
            if (r["id"], as_) not in seen:
                seen.add((r["id"], as_))
                out.append((r["id"], r["name"], as_))
    return out


def linked_text(db, bid, owner=None):
    """'Linked to <machine> as purchase' -- for the desk's Clinic-equipment note (plain text). '' when not linked, or for a
    manager while the machine pages are switched off."""
    try:
        owner = _owner() if owner is None else owner
        if not owner and not machine_on(db):
            return ""
        lk = linked(db, bid, owner)
        return ("Linked to " + "; ".join("%s as %s" % (n, w) for _i, n, w in lk) + ".") if lk else ""
    except Exception:                                                # noqa: BLE001
        return ""


PAPER_LINE_TPL = """{% if lk %}<b>Machine:</b> Linked to {% for aid, nm, w in lk %}<a href="{{url_for('asset_view',aid=aid)}}">{{nm}}</a> as {{w}}{{'; ' if not loop.last}}{% endfor %}<br>{% elif add %}<b>Machine:</b> <a href="{{add}}">+ asset record</a> <span class=muted>— a new machine record, pre-filled from this paper</span><br>{% endif %}"""


def paper_line(b):
    """The bill page's line (A6): 'Linked to <machine> as ...', or for the owner a Clinic-equipment paper's '+ asset record'."""
    db = AR.get_db()
    owner = _owner()
    if not owner and not machine_on(db):
        return Markup("")
    if refusal(b, owner):
        return Markup("")
    lk = linked(db, b["id"], owner)
    add = ""
    if (not lk and owner and (b["subgroup"] or "") == "clinic_equipment" and b["status"] == "approved"):
        add = url_for("s557_from_paper", bid=b["id"])
    return Markup(render_template_string(PAPER_LINE_TPL, lk=lk, add=add))


def can_from_paper(db, b, owner):
    """May this paper become a new machine record now? The owner, an accepted paper, not pharmacy / a patient's, no machine
    yet. No request needed (the month's data is also read outside one)."""
    if not owner or b["status"] != "approved" or refusal(b, owner):
        return False
    return not db.execute("SELECT 1 FROM assets WHERE bill_id=? LIMIT 1", (b["id"],)).fetchone()


# ---------------------------------------------------------------------------------------------- the machine page (A1-A4)
def cover_line(db, a, today=None):
    """(text, state) -- the live cover with the latest end date; state '' / 'amber' (30 days or less to its end) / 'red'."""
    today = today or _today()
    c = db.execute("SELECT * FROM asset_cover WHERE asset_id=? AND asset_created_at=? AND voided_at='' ORDER BY till_day DESC, id DESC LIMIT 1",
                   (a["id"], a["created_at"])).fetchone()
    if c is None:
        return "No cover", ""
    till = _iso(c["till_day"])
    prov = (c["provider"] or "").strip()
    if c["kind"] == "warranty":
        what = "Under warranty" + ((" (" + prov + ")") if prov else "")
    elif c["kind"] == "other":
        what = "Covered" + ((": " + prov) if prov else "")
    else:
        what = "Covered: %s%s" % (KIND_NAME[c["kind"]] if c["kind"] != "insurance" else "insurance", (" by " + prov) if prov else "")
    if till is None:
        return "%s till %s" % (what, c["till_day"]), "amber"
    days = (till - today).days
    if days < 0:
        return "%s — lapsed on %s" % (what, till.strftime("%d-%m-%Y")), "red"
    if days <= 30:
        return "%s till %s — %d day%s left" % (what, till.strftime("%d-%m-%Y"), days, "" if days == 1 else "s"), "amber"
    return "%s till %s" % (what, till.strftime("%d-%m-%Y")), ""


def totals_line(db, a, show_price):
    logs = db.execute("SELECT COUNT(*), COALESCE(SUM(cost),0) FROM service_logs WHERE asset_id=?", (a["id"],)).fetchone()
    paid = db.execute("SELECT COALESCE(SUM(cost),0) FROM asset_cover WHERE asset_id=? AND asset_created_at=? AND voided_at=''",
                      (a["id"], a["created_at"])).fetchone()[0]
    n = logs[0]
    nn = "1 repair/service" if n == 1 else "%d repairs/services" % n
    when = (" (%s)" % dmy(a["purchase_date"])) if a["purchase_date"] else ""
    if not show_price:
        return "Bought%s · %s since" % (when or " — date not set", nn)
    bought = ("Bought for %s%s" % (inr(a["price"]), when)) if a["price"] is not None else ("Bought%s — price not set" % when)
    return "%s · Spent since %s on %s · Cover paid %s" % (bought, inr(logs[1]), nn, inr(paid))


TOP_TPL = """<div class=card id=s557top style="padding:10px 14px">
<div id=s557cover class="{{state}}" style="font-size:16px;font-weight:700;padding:4px 8px;border-radius:6px">{{line}}{% if state=='red' %} <span class="badge red">lapsed</span>{% elif state=='amber' %} <span class="badge amber">ending soon</span>{% endif %}</div>
<div id=s557totals class=muted style="font-size:13px;margin:4px 8px 0">{{totals}}</div></div>"""

FOLDS_TPL = """<div id=s557folds>
<details class=card id=s557parts open><summary style="cursor:pointer;font-weight:600;color:#3a5a78">Parts <span class=muted>({{parts|length}} fitted{% if removed %} · {{removed|length}} removed{% endif %})</span></summary>
{% if parts %}<table style="margin-top:8px"><tr><th>Part</th><th>Make</th><th>Model</th><th>Serial</th><th>Fitted on</th><th>Warranty till</th><th>Its paper</th><th></th></tr>
{% for p in parts %}<tr><td>{{p.name}}</td><td>{{p.make or '—'}}</td><td>{{p.model or '—'}}</td><td>{{p.serial or '—'}}</td><td>{{p.fitted}}</td><td>{{p.till or '—'}}</td>
<td>{% if p.paper %}<a href="{{p.paper.href}}">{{p.paper.stamp}}</a>{% else %}<span class=muted>—</span>{% endif %}</td>
<td>{% if can_write %}<form method=post action="{{url_for('s557_part_remove',aid=aid,pid=p.id)}}" style="display:flex;gap:4px;align-items:center;margin:0" onsubmit="return confirm('Mark this part as replaced / removed? It stays in the list of removed parts.')"><input name=day value="{{today}}" style="max-width:100px;margin:0" aria-label="removed on"><button class="btn small">Replaced / removed</button></form>{% endif %}</td></tr>{% endfor %}</table>{% else %}<p class=muted>No parts recorded.</p>{% endif %}
{% if removed %}<details style="margin-top:8px" id=s557removed><summary class=muted style="cursor:pointer">Removed parts ({{removed|length}})</summary>
<table style="margin-top:6px"><tr><th>Part</th><th>Make / model</th><th>Serial</th><th>Fitted on</th><th>Removed on</th><th>By</th><th>Its paper</th></tr>
{% for p in removed %}<tr><td>{{p.name}}</td><td>{{p.make or ''}} {{p.model or ''}}</td><td>{{p.serial or '—'}}</td><td>{{p.fitted}}</td><td>{{p.removed}}</td><td>{{p.removed_by or ''}}</td><td>{% if p.paper %}<a href="{{p.paper.href}}">{{p.paper.stamp}}</a>{% endif %}</td></tr>{% endfor %}</table></details>{% endif %}
{% if can_write %}<form method=post action="{{url_for('s557_part_add',aid=aid)}}" style="margin-top:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:6px;align-items:end">
<label>Part*<input name=name required></label><label>Make<input name=make></label><label>Model<input name=model></label><label>Serial<input name=serial></label>
<label>Fitted on<input name=fitted_on placeholder="dd-mm-yyyy"></label><label>Warranty till<input name=warranty_till placeholder="dd-mm-yyyy"></label><label>Its paper<input name=paper placeholder="B-____"></label>
<div><button class="btn small">Add a part</button></div></form>{% endif %}</details>
<details class=card id=s557covers><summary style="cursor:pointer;font-weight:600;color:#3a5a78">Cover history <span class=muted>({{covers|length}})</span></summary>
{% if old %}<p class=muted id=s557old style="margin:8px 0 0">From the old record: {{old}}</p>{% endif %}
{% if covers %}<table style="margin-top:8px"><tr><th>Kind</th><th>Provider</th><th>From</th><th>Till</th>{% if show_price %}<th>Cost</th>{% endif %}<th>Its paper</th><th></th></tr>
{% for c in covers %}<tr{% if c.voided %} style="text-decoration:line-through;color:#8a97a5"{% endif %}><td>{{c.kind}}</td><td>{{c.provider or '—'}}</td><td>{{c.frm or '—'}}</td><td>{{c.till}}</td>{% if show_price %}<td>{{c.cost}}</td>{% endif %}
<td>{% if c.paper %}<a href="{{c.paper.href}}">{{c.paper.stamp}}</a>{% else %}<span class=muted>—</span>{% endif %}</td>
<td>{% if c.voided %}<span class=muted>voided {{c.voided}}</span>{% elif c.current %}<span class="badge green">current</span>{% else %}<span class=muted>earlier period</span>{% endif %}
{% if can_write and not c.voided %}<form method=post action="{{url_for('s557_cover_void',aid=aid,cid=c.id)}}" style="display:inline;margin:0" onsubmit="return confirm('Void this cover? It stays in the history, struck through.')"><button class="btn small danger">Void</button></form>{% endif %}</td></tr>{% endfor %}</table>{% else %}<p class=muted>No cover recorded here yet.</p>{% endif %}
{% if can_write %}<form method=post action="{{url_for('s557_cover_add',aid=aid)}}" style="margin-top:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:6px;align-items:end">
<label>Kind<select name=kind>{% for k, nm in kinds %}<option value="{{k}}">{{nm}}</option>{% endfor %}</select></label><label>Provider<input name=provider></label>
<label>From<input name=from_day placeholder="dd-mm-yyyy"></label><label>Till*<input name=till_day placeholder="dd-mm-yyyy" required></label>
{% if show_price %}<label>Cost ₹<input name=cost inputmode=decimal></label>{% endif %}<label>Remind days before<input name=remind_days value=30 inputmode=numeric></label><label>Its paper<input name=paper placeholder="B-____"></label>
<div><button class="btn small">Add cover</button></div></form><p class=muted style="margin:4px 0 0">A renewal is simply the next period; earlier periods stay as history. A mistake is voided, never deleted.</p>{% endif %}</details>
<details class=card id=s557spends><summary style="cursor:pointer;font-weight:600;color:#3a5a78">Spends <span class=muted>({{spends|length}}{% if show_price and spends %} · {{spent}}{% endif %})</span></summary>
{% if spends %}<table style="margin-top:8px"><tr><th>Date</th><th>What was done</th>{% if show_price %}<th>Amount</th>{% endif %}<th>By whom</th><th>Its paper</th></tr>
{% for s in spends %}<tr><td>{{s.day}}</td><td>{{s.work}} <span class=muted>{{s.type}}</span></td>{% if show_price %}<td>{{s.cost}}</td>{% endif %}<td>{{s.by or ''}}</td>
<td>{% if s.paper %}<a href="{{s.paper.href}}">{{s.paper.stamp}}</a>{% elif can_write and not s.bill_id %}<form method=post action="{{url_for('s557_spend_paper',aid=aid,sid=s.id)}}" style="display:flex;gap:4px;margin:0"><input name=paper placeholder="B-____" style="max-width:90px;margin:0"><button class="btn small">link</button></form>{% else %}<span class=muted>—</span>{% endif %}</td></tr>{% endfor %}</table>
{% if show_price and years %}<p id=s557years style="margin:6px 0 0"><b>Per year:</b> {% for y, t in years %}{{y}} {{t}}{{' · ' if not loop.last}}{% endfor %}</p>{% endif %}{% else %}<p class=muted>No spends recorded.</p>{% endif %}
{% if can_write %}<form method=post action="{{url_for('s557_spend_add',aid=aid)}}" style="margin-top:10px;display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:6px;align-items:end">
<label>Date*<input name=day value="{{today}}" required></label><label>Kind<select name=svc_type>{% for k, nm in spend_types %}<option value="{{k}}">{{nm}}</option>{% endfor %}</select></label>
<label>What was done*<input name=work required></label>{% if show_price %}<label>Amount ₹<input name=cost inputmode=decimal></label>{% endif %}<label>By whom<input name=done_by></label><label>Its paper<input name=paper placeholder="B-____"></label>
<div><button class="btn small">Add a spend</button></div></form><p class=muted style="margin:4px 0 0">The service log's own form below keeps working; its entries show here too.</p>{% endif %}</details>
</div>"""


def _old_record(a, show_price):
    ct = (a["contract_type"] or "").strip()
    if not ct or ct == "None":
        return ""
    s = ct + ((" — " + a["provider"]) if a["provider"] else "")
    if show_price and a["contract_cost"]:
        s += " · %s/yr" % inr(a["contract_cost"])
    return s + " (shown as it was; nothing moved)"


def sections(a):
    """(top, folds) for the machine page -- empty for a manager while machine.on is OFF (the page exactly as before)."""
    db = AR.get_db()
    owner = _owner()
    if not owner and not machine_on(db):
        return Markup(""), Markup("")
    show_price = AR.can_see_price(a)
    can_write = (g.user["role"] in ("owner", "manager"))
    line, state = cover_line(db, a)
    top = render_template_string(TOP_TPL, line=line, state=state, totals=totals_line(db, a, show_price))
    parts, removed = [], []
    afp = a["created_at"]                                            # S557_FIX1: only the rows made on THIS machine
    for p in db.execute("SELECT * FROM asset_part WHERE asset_id=? AND asset_created_at=? ORDER BY COALESCE(fitted_on,''), id", (a["id"], afp)):
        d = {"id": p["id"], "name": p["name"], "make": p["make"], "model": p["model"], "serial": p["serial"],
             "fitted": dmy(p["fitted_on"]) if p["fitted_on"] else "—", "till": dmy(p["warranty_till"]) if p["warranty_till"] else "",
             "removed": dmy(p["removed_on"]) if p["removed_on"] else "", "removed_by": p["removed_by"],
             "paper": _paper_view(db, p["bill_id"], p["bill_created_at"], owner, show_price)}
        (removed if p["removed_on"] else parts).append(d)
    cur = {}
    rows = db.execute("SELECT * FROM asset_cover WHERE asset_id=? AND asset_created_at=? ORDER BY till_day DESC, id DESC", (a["id"], afp)).fetchall()
    for c in rows:
        if not c["voided_at"] and c["kind"] not in cur:
            cur[c["kind"]] = c["id"]
    covers = [{"id": c["id"], "kind": KIND_NAME.get(c["kind"], c["kind"]), "provider": c["provider"],
               "frm": dmy(c["from_day"]) if c["from_day"] else "", "till": dmy(c["till_day"]),
               "cost": inr(c["cost"]) if c["cost"] is not None else "—", "voided": dmy(c["voided_at"]) if c["voided_at"] else "",
               "current": cur.get(c["kind"]) == c["id"], "paper": _paper_view(db, c["bill_id"], c["bill_created_at"], owner, show_price)} for c in rows]
    spends, years, total = [], {}, 0.0
    for s in db.execute("SELECT * FROM service_logs WHERE asset_id=? ORDER BY log_date DESC, id DESC", (a["id"],)):
        tname = {"Other service": "Service visit"}.get(s["svc_type"] or "", s["svc_type"] or "")
        spends.append({"id": s["id"], "day": dmy(s["log_date"]), "work": s["work"], "type": tname,
                       "cost": inr(s["cost"]) if s["cost"] is not None else "—", "by": s["done_by"],
                       "bill_id": s["bill_id"] if paper_ok(db, s["bill_id"], s["bill_created_at"]) else None,
                       "paper": _paper_view(db, s["bill_id"], s["bill_created_at"], owner, show_price)})
        if s["cost"] is not None:
            y = (s["log_date"] or "")[:4] or "?"
            years[y] = years.get(y, 0.0) + float(s["cost"])
            total += float(s["cost"])
    folds = render_template_string(
        FOLDS_TPL, aid=a["id"], parts=parts, removed=removed, covers=covers, spends=spends, show_price=show_price,
        can_write=can_write, kinds=KINDS, spend_types=SPEND_TYPES, today=_today().strftime("%d-%m-%Y"),
        years=[(y, inr(t)) for y, t in sorted(years.items(), reverse=True)], spent=inr(total), old=_old_record(a, show_price))
    return Markup(top), Markup(folds)


# ---------------------------------------------------------------------------------------------- the routes
def _writer(f):
    """The asset pages' gate (login; reception never), the machine visible to this person, owner or manager -- and, for a
    manager, the switch on."""
    @functools.wraps(f)
    def w(aid, *a, **k):
        if g.user["role"] not in ("owner", "manager"):
            abort(403)
        asset = AR.asset_or_403(aid)
        if not _owner() and not machine_on(AR.get_db()):
            abort(403)
        return f(asset, *a, **k)
    return w


def _done(aid, msg, anchor):
    flash(msg)
    return redirect(url_for("asset_view", aid=aid) + "#" + anchor)


def _act(aid, anchor, fn):
    """One action: fn(db) -> the line to show; one commit; a Refused line rolls back and saves nothing."""
    db = AR.get_db()
    try:
        msg = fn(db)
        db.commit()
    except Refused as e:
        db.rollback()
        return _done(aid, str(e), anchor)
    return _done(aid, msg, anchor)


def part_add(a):
    f = request.form

    def go(db):
        name = _txt(f.get("name"))
        if not name:
            raise Refused("Type the part's name. Nothing was saved.")
        owner = _owner()
        bid = paper_from_box(db, f.get("paper"), owner)
        fitted = _date(f.get("fitted_on"), "fitted-on date")
        till = _date(f.get("warranty_till"), "warranty date")
        cur = db.execute("INSERT INTO asset_part(asset_id, name, make, model, serial, fitted_on, warranty_till, bill_id, by_whom, at, "
                         "asset_created_at, bill_created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                         (a["id"], name, _txt(f.get("make"), 80), _txt(f.get("model"), 80), _txt(f.get("serial"), 80), fitted, till,
                          bid, _who(), AR._now_ist(), a["created_at"], bill_fp(db, bid)))
        sync_asset(db, a["id"])
        _audit(db, "machine_part_add", {"asset": a["id"], "part": cur.lastrowid, "bill": bid})
        if bid:
            AR._audit_bill(db, bid, "machine_link", {"asset": a["id"], "as": "part", "part": cur.lastrowid})
        return "Part added: %s." % name
    return _act(a["id"], "s557parts", go)


def part_remove(a, pid):
    def go(db):
        p = db.execute("SELECT * FROM asset_part WHERE id=? AND asset_id=? AND asset_created_at=?", (pid, a["id"], a["created_at"])).fetchone()
        if p is None:
            raise Refused("There is no such part on this machine.")
        if p["removed_on"]:
            raise Refused("%s is already marked removed." % p["name"])
        day = _date(request.form.get("day"), "date") or _today().isoformat()
        db.execute("UPDATE asset_part SET removed_on=?, removed_by=? WHERE id=?", (day, _who(), pid))
        sync_asset(db, a["id"])
        _audit(db, "machine_part_removed", {"asset": a["id"], "part": pid, "day": day})
        return "%s marked replaced / removed on %s — kept in Removed parts." % (p["name"], dmy(day))
    return _act(a["id"], "s557parts", go)


def cover_add(a):
    f = request.form

    def go(db):
        kind = (f.get("kind") or "").strip().lower()
        if kind not in KIND_NAME:
            raise Refused("Choose the kind of cover. Nothing was saved.")
        owner = _owner()
        till = _date(f.get("till_day"), "till date", required=True)
        frm = _date(f.get("from_day"), "from date")
        if frm and frm > till:
            raise Refused("The cover ends before it starts. Nothing was saved.")
        cost = _money(f.get("cost")) if AR.can_see_price(a) else None
        try:
            rd = int(str(f.get("remind_days") or REMIND_DEFAULT).strip())
        except ValueError:
            raise Refused("Remind days must be a number. Nothing was saved.")
        rd = max(1, min(rd, 365))
        bid = paper_from_box(db, f.get("paper"), owner)
        cur = db.execute("INSERT INTO asset_cover(asset_id, kind, provider, from_day, till_day, cost, bill_id, remind_days, by_whom, at, "
                         "asset_created_at, bill_created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                         (a["id"], kind, _txt(f.get("provider")), frm, till, cost, bid, rd, _who(), AR._now_ist(), a["created_at"], bill_fp(db, bid)))
        sync_asset(db, a["id"])
        _audit(db, "machine_cover_add", {"asset": a["id"], "cover": cur.lastrowid, "kind": kind, "till": till, "bill": bid})
        if bid:
            AR._audit_bill(db, bid, "machine_link", {"asset": a["id"], "as": "cover", "cover": cur.lastrowid})
        return "Cover added: %s till %s." % (KIND_NAME[kind], dmy(till))
    return _act(a["id"], "s557covers", go)


def cover_void(a, cid):
    def go(db):
        c = db.execute("SELECT * FROM asset_cover WHERE id=? AND asset_id=? AND asset_created_at=?", (cid, a["id"], a["created_at"])).fetchone()
        if c is None:
            raise Refused("There is no such cover on this machine.")
        if c["voided_at"]:
            raise Refused("That cover is already voided.")
        db.execute("UPDATE asset_cover SET voided_at=?, voided_by=? WHERE id=?", (AR._now_ist(), _who(), cid))
        sync_asset(db, a["id"])
        _audit(db, "machine_cover_void", {"asset": a["id"], "cover": cid})
        return "Cover voided — it stays in the history, struck through."
    return _act(a["id"], "s557covers", go)


def spend_add(a):
    f = request.form

    def go(db):
        work = _txt(f.get("work"), 300)
        if not work:
            raise Refused("Type what was done. Nothing was saved.")
        day = _date(f.get("day"), "date", required=True)
        st = f.get("svc_type") if f.get("svc_type") in dict(SPEND_TYPES) else "Repair"
        cost = _money(f.get("cost")) if AR.can_see_price(a) else None
        bid = paper_from_box(db, f.get("paper"), _owner())
        cur = db.execute("INSERT INTO service_logs(asset_id, log_date, work, cost, done_by, is_pm, svc_type, created_by, bill_id, bill_created_at) "
                         "VALUES(?,?,?,?,?,0,?,?,?,?)", (a["id"], day, work, cost, _txt(f.get("done_by")), st, g.user["id"], bid, bill_fp(db, bid)))
        _audit(db, "machine_spend_add", {"asset": a["id"], "log": cur.lastrowid, "bill": bid})
        if bid:
            AR._audit_bill(db, bid, "machine_link", {"asset": a["id"], "as": "spend", "log": cur.lastrowid})
        return "Spend added: %s on %s." % (work[:60], dmy(day))
    return _act(a["id"], "s557spends", go)


def spend_paper(a, sid):
    def go(db):
        s = db.execute("SELECT * FROM service_logs WHERE id=? AND asset_id=?", (sid, a["id"])).fetchone()
        if s is None:
            raise Refused("There is no such entry on this machine.")
        if paper_ok(db, s["bill_id"], s["bill_created_at"]):
            raise Refused("That entry already has its paper.")
        bid = paper_from_box(db, request.form.get("paper"), _owner())
        if not bid:
            raise Refused("Type the paper's number (B-____).")
        db.execute("UPDATE service_logs SET bill_id=?, bill_created_at=? WHERE id=?", (bid, bill_fp(db, bid), sid))
        _audit(db, "machine_spend_paper", {"asset": a["id"], "log": sid, "bill": bid})
        AR._audit_bill(db, bid, "machine_link", {"asset": a["id"], "as": "spend", "log": sid})
        return "Paper linked."
    return _act(a["id"], "s557spends", go)


# ---------------------------------------------------------------------------------------------- a machine from a paper (A6)
def prefill(db, b):
    """From the paper: supplier, date, amount; the item's name, make, model, serial from Claude's reading (ok=1 rows; the
    table may be absent), else from the paper's own first item."""
    pf = {"vendor": b["vendor"] or "", "date": dmy(b["bill_date"]) if b["bill_date"] else "",
          "price": ("%g" % b["total_amount"]) if b["total_amount"] is not None else "", "name": "", "make": "", "model": "", "serial": ""}
    items = []
    try:
        r = db.execute("SELECT data FROM claude_reading WHERE bill_id=? AND ok=1", (b["id"],)).fetchone()
        data = json.loads(r[0] or "{}") if r else {}
        items = [i for i in (data.get("items") or []) if isinstance(i, dict)] if isinstance(data, dict) else []
    except (sqlite3.Error, TypeError, ValueError):
        items = []
    pick = next((i for i in items if any(str(i.get(k) or "").strip() for k in ("make", "model", "serial"))), items[0] if items else None)
    if pick:
        pf.update(name=str(pick.get("name") or "").strip(), make=str(pick.get("make") or "").strip(),
                  model=str(pick.get("model") or "").strip(), serial=str(pick.get("serial") or "").strip())
    else:
        it = db.execute("SELECT * FROM bill_items WHERE bill_id=? ORDER BY id LIMIT 1", (b["id"],)).fetchone()
        if it:
            pf.update(name=it["item_name"] or "", make=it["make"] or "", model=it["model"] or "", serial=it["serial_no"] or "")
    if not pf["name"]:
        pf["name"] = " ".join(x for x in (pf["make"], pf["model"]) if x)
    return {k: (v or "")[:120] for k, v in pf.items()}


FROM_PAPER_TPL = """<p><a class="btn small" href="{{url_for('bill_view',bid=b['id'])}}">← {{stamp}}</a></p>
<h2>New machine record from {{stamp}}</h2>
<div class=card><p class=muted style="margin-top:0">Pre-filled from the paper{{' and Claude’s reading' if claude else ''}} — check each box. The paper stays linked as this machine's purchase bill. Filed under {{entity}}; Edit afterwards for the rest.</p>
<form method=post>
<label>Name*</label><input name=name value="{{pf.name}}" required>
<label>Category</label><select name=category>{% for c in cats %}<option {{'selected' if c==cat}}>{{c}}</option>{% endfor %}</select>
<label>Supplier</label><input name=vendor value="{{pf.vendor}}">
<label>Purchase date</label><input name=purchase_date value="{{pf.date}}" placeholder="dd-mm-yyyy">
<label>Price (₹)</label><input name=price value="{{pf.price}}" inputmode=decimal>
<label>Make</label><input name=make value="{{pf.make}}"><label>Model</label><input name=model value="{{pf.model}}">
<label>Serial</label><input name=serial_no value="{{pf.serial}}">
<br><br><button>Save the machine</button></form></div>"""


def from_paper(bid):
    db = AR.get_db()
    b = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    if b is None:
        abort(404)
    why = refusal(b, True)
    if why or b["status"] == "rejected":
        flash(why or "That paper is set aside.")
        return redirect(url_for("bill_view", bid=bid))
    have = db.execute("SELECT id FROM assets WHERE bill_id=? ORDER BY id LIMIT 1", (bid,)).fetchone()
    if have:
        flash("%s is already the purchase bill of this machine." % _stamp(b))
        return redirect(url_for("asset_view", aid=have[0]))
    pf = prefill(db, b)
    if request.method == "POST":
        f = request.form
        try:
            name = _txt(f.get("name"))
            if not name:
                raise Refused("Type the machine's name. Nothing was saved.")
            pdate = _date(f.get("purchase_date"), "purchase date")
            price = _money(f.get("price"))
            cat = f.get("category") if f.get("category") in AR.CATEGORIES else EQUIP_CATEGORY
            ent = db.execute("SELECT id FROM entities WHERE name=?", (CLINIC_ENTITY,)).fetchone()
            loc = AR.entity_default_location_id(CLINIC_ENTITY)
            if loc is None:
                raise Refused("There is no location to file the machine under. Nothing was saved.")
            mm = " · ".join(x for x in (("Make " + f.get("make").strip()) if (f.get("make") or "").strip() else "",
                                             ("Model " + f.get("model").strip()) if (f.get("model") or "").strip() else "") if x)
            notes = ("From %s: %s" % (_stamp(b), mm)) if mm else ("From %s." % _stamp(b))
            cur = db.execute("INSERT INTO assets(name, location_id, category, purchase_date, price, vendor, serial_no, status, contract_type, "
                             "notes, created_by, entity_id, zone_id, kind, bill_id) VALUES(?,?,?,?,?,?,?,'Active','None',?,?,?,NULL,'Asset',?)",
                             (name, loc, cat, pdate, price, _txt(f.get("vendor")), _txt(f.get("serial_no"), 80), notes, g.user["id"],
                              ent[0] if ent else None, bid))
            aid = cur.lastrowid
            it = db.execute("SELECT id FROM bill_items WHERE bill_id=? AND asset_id IS NULL ORDER BY id LIMIT 1", (bid,)).fetchone()
            if it:
                db.execute("UPDATE bill_items SET asset_id=? WHERE id=?", (aid, it[0]))        # the A-D20 bridge, both ways
            AR._backfill_asset_from_bill(db, aid, bid)                                          # A-D24: only fills blanks
            AR._audit_bill(db, bid, "machine_link", {"asset": aid, "as": "purchase"})
            _audit(db, "machine_from_paper", {"asset": aid, "bill": bid})
            db.commit()
        except Refused as e:
            db.rollback()
            flash(str(e))
            return redirect(url_for("s557_from_paper", bid=bid))
        flash("Machine saved — %s is its purchase bill." % _stamp(b))
        return redirect(url_for("asset_view", aid=aid))
    claude = False
    try:
        claude = bool(db.execute("SELECT 1 FROM claude_reading WHERE bill_id=? AND ok=1", (bid,)).fetchone())
    except sqlite3.Error:
        claude = False
    return AR.page(FROM_PAPER_TPL, b=b, stamp=_stamp(b), pf=pf, cats=AR.CATEGORIES, cat=EQUIP_CATEGORY, entity=CLINIC_ENTITY,
                   claude=claude, flow=AR._flow("New machine", url_for("bill_view", bid=bid)))


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):
    """Called once, at the foot of asset_register.py, after sorting_desk is mounted."""
    global AR, MOUNTED
    AR = ar
    ensure_at_mount(ar.DB_PATH)
    app, lr = ar.app, ar.login_required
    app.add_url_rule("/assets/<int:aid>/parts/add", "s557_part_add", lr(_writer(part_add)), methods=["POST"])
    app.add_url_rule("/assets/<int:aid>/parts/<int:pid>/remove", "s557_part_remove", lr(_writer(part_remove)), methods=["POST"])
    app.add_url_rule("/assets/<int:aid>/covers/add", "s557_cover_add", lr(_writer(cover_add)), methods=["POST"])
    app.add_url_rule("/assets/<int:aid>/covers/<int:cid>/void", "s557_cover_void", lr(_writer(cover_void)), methods=["POST"])
    app.add_url_rule("/assets/<int:aid>/spends/add", "s557_spend_add", lr(_writer(spend_add)), methods=["POST"])
    app.add_url_rule("/assets/<int:aid>/spends/<int:sid>/paper", "s557_spend_paper", lr(_writer(spend_paper)), methods=["POST"])
    app.add_url_rule("/bills/<int:bid>/machine", "s557_from_paper", ar.owner_required(from_paper), methods=["GET", "POST"])
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data step:  python3 asset_machine.py --ensure <assets.db>
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        print("asset_machine %s: tables and column ready; reminders healed: %d" % (VERSION, ensure_path(sys.argv[2])))
    else:
        print(__doc__)
