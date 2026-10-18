#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""xray_costs.py -- S582_XRAY_COSTS (D736; the owner's word, 13:03 IST 18-Oct-2026, on B-0163, the X-ray envelopes moved to
Stationery & packaging: "But it needs to be also under the xray expenses section, so that I can assess expenses of the xray
department also").

WHAT THIS FILE IS
    A part of the asset app, mounted from batteries.init (one guarded call at its end; if this file is absent or cannot load, the
    Batteries pages run exactly as before). It adds ONE owner-only page, /xray ("X-ray expenses", menu item "X-ray costs", right
    after Batteries), which adds, month by month, everything the X-ray department costs -- each rupee once:
        X-ray films            The month's own section "xray" (sorting_desk.MONTH_SECTIONS), read through its own selection
                               _s566_paid_rows and its own sum _s566_total -- never a second spend rule.
        Papers marked          any paper the owner marked for X-ray (any lane, any group; never pharmacy, never a patient's paper),
                               counted only when The month counts it in its own section, else listed "not counted: <why>".
        Machines marked        their service and repair spends (service_logs.cost by log_date, as asset_machine.totals_line) and
                               their covers (asset_cover.cost by from_day, the machine's fingerprint, not voided). Never the
                               purchase price (that is the asset).
        Battery places marked  battery_fit.price by fitted_on, not voided.
    A paper keeps its ONE group (bills.subgroup, D664): a mark never writes bills, assets, battery_place or battery_fit.

EACH RUPEE ONCE (S582_BRIEF_R1 C7)
    Order of claim: (1) a counted spend / cover / battery fitting claims its paper(s) -- the bill, and for a fitting its warranty
    card too -- trusted only with the paper's fingerprint (bills.created_at = the row's bill_created_at); the row's own cost
    counts, the paper is shown under it "its paper B-xxxx" at no amount; a link whose fingerprint does not match is shown "paper
    link stale" and claims nothing; (2) X-ray films; (3) marked papers. A paper counts at most once across the folds. One paper
    claimed by two rows counts each row's own cost and both rows say "one paper, two entries — check". The films fold always
    shows The month's own films total; when a film paper is claimed by (1), one line says how much of it is counted there.
    NOT detectable: a spend recorded on a marked machine AND as a battery fitting of a marked place with no paper on either.

THE MARKS -- table xray_mark (additive; created here, CREATE ... IF NOT EXISTS)
    kind paper / machine / battery_place, ref_id + ref_created_at (the record's fingerprint: bills.created_at, assets.created_at,
    battery_place.made_at -- a mark never passes to a new record that re-uses a deleted one's id, S557 BL1). A live mark has
    removed_at=''; the unique index xray_mark_live allows ONE live mark per (kind, ref_id, ref_created_at); every mark is INSERT OR
    IGNORE (two gunicorn workers, S582_BRIEF_R1 B2). Every mark / unmark is audited in desk_audit.
    THE SEED (the owner's own words only) runs in the installer's data step, never at mount:  python3 xray_costs.py --ensure <db>
    -- the paper B-0163 by its stamp, the battery places named exactly "Digital X-ray" and "X-ray detector (FDR) battery"; each
    absent one is skipped with one printed line; no machine is seeded; a seed the owner unmarked is never marked again (any row
    of that key in the table, live or removed, means "leave it").
"""
import datetime
import json
import re
import sqlite3
import sys
import time

from flask import abort, flash, g, redirect, request, url_for
from markupsafe import Markup

VERSION = "S582"
AR = None                     # the asset app's module, handed in by init()
TODAY = None                  # the walk sets a made-up day here
MOUNTED = False
FILMS = "xray"                # the X-ray films section's key in sorting_desk.MONTH_SECTIONS
NO_PAPER = "none:old-battery" # batteries.NO_PAPER: "Old battery — no bill / no card" -- no paper
SEED_PAPER = "B-0163"                                              # the owner's word, 13:03 IST 18-Oct-2026 (the X-ray envelopes)
SEED_PLACES = ("Digital X-ray", "X-ray detector (FDR) battery")    # exact live names (S582 brief C8)
SEED_WHO = "S582 seed"
LOOKS = re.compile(r"x[\s-]?ray|\bfdr\b|\bcr\b|digiti[sz]er", re.I)   # "looks like X-ray" -- listed first, never ticked by the system
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")
KINDS = ("paper", "machine", "battery_place")

DDL = (
    "CREATE TABLE IF NOT EXISTS xray_mark(id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('paper','machine','battery_place')), "
    "ref_id INTEGER NOT NULL, ref_created_at TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, removed_at TEXT NOT NULL DEFAULT '', "
    "removed_by TEXT NOT NULL DEFAULT '')",
    "CREATE UNIQUE INDEX IF NOT EXISTS xray_mark_live ON xray_mark(kind, ref_id, ref_created_at) WHERE removed_at=''",
)


# ---------------------------------------------------------------------------------------------- the database's part
def ensure(db):
    """Additive and idempotent: the table and its unique index. 'already exists' from a second worker is normal."""
    for d in DDL:
        try:
            db.execute(d)
        except sqlite3.OperationalError as ex:
            if "already exists" not in str(ex).lower():
                raise
    db.commit()


def ensure_at_mount(db_path, tries=3, wait=1.0, timeout=3):
    """As batteries.ensure_at_mount: 'database is locked' is retried briefly, then left to the installer's data step. No seed here."""
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
    print("xray_costs: the database stayed locked at mount; its table is left to the installer's data step", file=sys.stderr)
    return False


def _fp(db, kind, ref_id):
    """The record's fingerprint, or None when there is no such record."""
    q = {"paper": "SELECT created_at FROM bills WHERE id=?", "machine": "SELECT created_at FROM assets WHERE id=?",
         "battery_place": "SELECT made_at FROM battery_place WHERE id=?"}[kind]
    try:
        r = db.execute(q, (int(ref_id),)).fetchone()
    except (sqlite3.Error, TypeError, ValueError):
        return None
    return None if r is None else (r[0] or "")


def _ever(db, kind, ref_id, fp):
    return db.execute("SELECT 1 FROM xray_mark WHERE kind=? AND ref_id=? AND ref_created_at=? LIMIT 1", (kind, ref_id, fp)).fetchone() is not None


def seed(db, now=None):
    """The owner's own words only (the data step). Returns the printed lines. Never marks a seed the owner unmarked."""
    now = now or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out, todo = [], []
    b = db.execute("SELECT id, created_at FROM bills WHERE upper(stamp_no)=? ORDER BY id LIMIT 1", (SEED_PAPER,)).fetchone()
    if b is None:
        out.append("seed: no paper %s -- not marked" % SEED_PAPER)
    else:
        todo.append(("paper", b[0], b[1] or "", SEED_PAPER))
    for nm in SEED_PLACES:
        r = db.execute("SELECT id, made_at FROM battery_place WHERE name=? ORDER BY id LIMIT 1", (nm,)).fetchone()
        if r is None:
            out.append("seed: no battery place named '%s' -- skipped" % nm)
        else:
            todo.append(("battery_place", r[0], r[1] or "", nm))
    for kind, rid, fp, what in todo:
        if _ever(db, kind, rid, fp):
            live = db.execute("SELECT 1 FROM xray_mark WHERE kind=? AND ref_id=? AND ref_created_at=? AND removed_at=''", (kind, rid, fp)).fetchone()
            out.append("seed: %s %s -- %s" % (kind.replace("_", " "), what, "already marked" if live else "unmarked by the owner, left unmarked"))
            continue
        n = db.execute("INSERT OR IGNORE INTO xray_mark(kind, ref_id, ref_created_at, by_whom, at) VALUES(?,?,?,?,?)",
                       (kind, rid, fp, SEED_WHO, now)).rowcount
        if n:
            try:
                db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                           (now, SEED_WHO, "xray_mark_seed", json.dumps({"kind": kind, "ref": rid}, ensure_ascii=False)))
            except sqlite3.Error:
                pass
        out.append("seed: %s %s -- %s" % (kind.replace("_", " "), what, "marked for X-ray" if n else "already marked"))
    db.commit()
    return out


def ensure_path(db_path):
    con = sqlite3.connect(db_path, timeout=20)
    try:
        ensure(con)
        lines = seed(con)
        n = con.execute("SELECT COUNT(*) FROM xray_mark WHERE removed_at=''").fetchone()[0]
    finally:
        con.close()
    return lines, n


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


def _now():
    try:
        return AR._now_ist()
    except Exception:                                                # noqa: BLE001
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _audit(db, action, detail):
    """Into the desk's own book (desk_audit), fail-soft -- batteries._audit's form."""
    try:
        db.execute("INSERT INTO desk_audit(at, who, action, detail) VALUES(?,?,?,?)",
                   (_now(), _who(), action, json.dumps(detail or {}, ensure_ascii=False)[:500]))
    except sqlite3.Error:
        pass


def _grp(n):
    s = "%d" % n
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
    return head + "," + tail


def rs(x):
    """₹ with Indian grouping; paise only when there are any (batteries.rs)."""
    if x is None:
        return "—"
    f = float(x)
    neg = f < 0
    f = abs(f)
    t = _grp(int(round(f))) if round(f, 2) == int(round(f, 2)) else _grp(int(f)) + ("%.2f" % (f - int(f)))[1:]
    return ("-" if neg else "") + "₹" + t


def _iso(s):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:                                                # noqa: BLE001
        return None


def dmy(s):
    d = _iso(s)
    return d.strftime("%d-%m-%Y") if d else (s or "")


def ym_ok(v):
    return bool(re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", v or ""))


def ym_shift(ym, k):
    y, m = int(ym[:4]), int(ym[5:7]) + k
    while m < 1:
        y, m = y - 1, m + 12
    while m > 12:
        y, m = y + 1, m - 12
    return "%04d-%02d" % (y, m)


def label(ym):
    try:
        return datetime.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y")
    except Exception:                                                # noqa: BLE001
        return ym


def _month_of(s):
    """The month of a stored date -- ISO only (S582_BRIEF_R1 N2); None when the date is not read."""
    s = str(s or "").strip()
    return s[:7] if ISO.match(s) and _iso(s) else None


def _sd():
    """The sorting desk, when the app has it mounted (S582_BRIEF_R1 C2: the app's own test)."""
    try:
        return AR._s559_desk_mod()
    except Exception:                                                # noqa: BLE001
        return None


def _bt():
    m = sys.modules.get("batteries")
    return m if (m is not None and getattr(m, "MOUNTED", False)) else None


def _stamp(b):
    return (b["stamp_no"] or "") if b["stamp_no"] else "#%d" % b["id"]


def _href(bid):
    try:
        return AR._s559_paper_href(int(bid))
    except Exception:                                                # noqa: BLE001
        try:
            return url_for("bill_view", bid=int(bid))
        except Exception:                                            # noqa: BLE001
            return ""


def _lane(b):
    try:
        return b["lane"] or AR.KIND_LANE.get(b["kind"], "clinic")
    except Exception:                                                # noqa: BLE001
        return b["lane"] or "clinic"


def _films_section(sd):
    for key, name, subs in sd.MONTH_SECTIONS:
        if key == FILMS:
            return key, name, tuple(subs)
    return None


def _section_of(sd, sub):
    for key, name, subs in sd.MONTH_SECTIONS:
        if (sub or "") in subs:
            return key, name, tuple(subs)
    return None


# ---------------------------------------------------------------------------------------------- the marks
def live_marks(db, kind):
    """{ref_id: mark_id} of the live marks of this kind whose record still carries the fingerprint (a re-issued id inherits nothing)."""
    q = {"paper": "SELECT m.id, m.ref_id FROM xray_mark m JOIN bills t ON t.id=m.ref_id AND COALESCE(t.created_at,'')=m.ref_created_at",
         "machine": "SELECT m.id, m.ref_id FROM xray_mark m JOIN assets t ON t.id=m.ref_id AND COALESCE(t.created_at,'')=m.ref_created_at",
         "battery_place": "SELECT m.id, m.ref_id FROM xray_mark m JOIN battery_place t ON t.id=m.ref_id AND COALESCE(t.made_at,'')=m.ref_created_at"}[kind]
    out = {}
    try:
        for mid, rid in db.execute(q + " WHERE m.kind=? AND m.removed_at='' ORDER BY m.id", (kind,)):
            out.setdefault(rid, mid)
    except sqlite3.Error:
        return {}
    return out


def mark(db, kind, ref_id, who=None):
    """A live mark (INSERT OR IGNORE). True when one was made. Writes ONLY xray_mark (and the audit). No commit."""
    fp = _fp(db, kind, ref_id)
    if fp is None:
        raise ValueError("There is no such record.")
    n = db.execute("INSERT OR IGNORE INTO xray_mark(kind, ref_id, ref_created_at, by_whom, at) VALUES(?,?,?,?,?)",
                   (kind, int(ref_id), fp, _who() if who is None else who, _now())).rowcount
    if n:
        _audit(db, "xray_mark", {"kind": kind, "ref": int(ref_id)})
    return bool(n)


def unmark(db, kind, ref_id, who=None):
    """Every live mark of this record (its current fingerprint) is removed -- kept as a removed row. No commit."""
    fp = _fp(db, kind, ref_id)
    if fp is None:
        return 0
    n = db.execute("UPDATE xray_mark SET removed_at=?, removed_by=? WHERE kind=? AND ref_id=? AND ref_created_at=? AND removed_at=''",
                   (_now(), _who() if who is None else who, kind, int(ref_id), fp)).rowcount
    if n:
        _audit(db, "xray_unmark", {"kind": kind, "ref": int(ref_id)})
    return n


# ---------------------------------------------------------------------------------------------- the claims (each rupee once, step 1)
def _paper_by_fp(db, bid, created):
    """The paper a row points to, trusted only with its fingerprint: (row, state) -- state 'ok', 'none' (no paper) or 'stale'."""
    if not bid:
        return None, "none"
    if (created or "") == NO_PAPER:
        return None, "none"
    r = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
    if r is None or not created or (r["created_at"] or "") != created:
        return None, "stale"
    return r, "ok"


def machine_rows(db, mids):
    """Every spend and cover of the marked machines (all months): dicts with month (None = date not read), cost, papers."""
    out = []
    for aid in sorted(mids):
        a = db.execute("SELECT * FROM assets WHERE id=?", (aid,)).fetchone()
        if a is None:
            continue
        try:
            logs = db.execute("SELECT * FROM service_logs WHERE asset_id=? ORDER BY log_date, id", (aid,)).fetchall()
        except sqlite3.Error:
            logs = []
        for s in logs:
            keys = s.keys()
            p, st = _paper_by_fp(db, s["bill_id"] if "bill_id" in keys else None, s["bill_created_at"] if "bill_created_at" in keys else "")
            what = (s["work"] or "service").strip()
            if "svc_type" in keys and s["svc_type"]:
                what += " (%s)" % s["svc_type"]
            out.append({"src": "spend", "id": s["id"], "aid": aid, "machine": a["name"], "date": s["log_date"], "month": _month_of(s["log_date"]),
                        "what": "%s — %s" % (a["name"], what), "who": s["done_by"] or "", "cost": float(s["cost"] or 0), "nocost": s["cost"] is None,
                        "papers": [p] if p is not None else [], "stale": st == "stale", "note": ""})
        try:
            covs = db.execute("SELECT * FROM asset_cover WHERE asset_id=? AND asset_created_at=? AND voided_at='' ORDER BY from_day, id",
                              (aid, a["created_at"])).fetchall()
        except sqlite3.Error:
            covs = []
        for c in covs:
            p, st = _paper_by_fp(db, c["bill_id"], c["bill_created_at"])
            mo, note = _month_of(c["from_day"]), ""
            if not (c["from_day"] or "").strip():                    # S582_BRIEF_R1 C5: no from-date -> the month it was recorded in
                mo, note = _month_of(c["at"]), "no from-date"
            out.append({"src": "cover", "id": c["id"], "aid": aid, "machine": a["name"], "date": c["from_day"] or c["at"], "month": mo,
                        "what": "%s — %s cover till %s" % (a["name"], (c["kind"] or "").upper() if c["kind"] in ("amc", "cmc") else (c["kind"] or "").capitalize(), dmy(c["till_day"])),
                        "who": c["provider"] or "", "cost": float(c["cost"] or 0), "nocost": c["cost"] is None,
                        "papers": [p] if p is not None else [], "stale": st == "stale", "note": note})
    return out


def battery_rows(db, pids):
    out = []
    for pid in sorted(pids):
        p = db.execute("SELECT * FROM battery_place WHERE id=?", (pid,)).fetchone()
        if p is None:
            continue
        for f in db.execute("SELECT * FROM battery_fit WHERE place_id=? AND voided_at='' ORDER BY fitted_on, id", (pid,)):
            papers, stale = [], False
            for k in ("bill", "card"):
                b, st = _paper_by_fp(db, f[k + "_id"], f[k + "_created_at"])
                if b is not None and all(x["id"] != b["id"] for x in papers):
                    papers.append(b)
                stale = stale or st == "stale"
            bits = [x for x in (f["brand"], f["ah"] and ("%s Ah" % f["ah"])) if x]
            if (f["set_n"] or 0) > 1:
                bits.append("set of %d" % f["set_n"])
            out.append({"src": "battery", "id": f["id"], "pid": pid, "place": p["name"], "date": f["fitted_on"], "month": _month_of(f["fitted_on"]),
                        "what": "%s — battery fitted%s" % (p["name"], (" (%s)" % " · ".join(bits)) if bits else ""), "who": f["supplier"] or "",
                        "cost": float(f["price"] or 0), "nocost": f["price"] is None, "papers": papers, "stale": stale, "note": ""})
    return out


# ---------------------------------------------------------------------------------------------- the money
NOT_COUNTED = "not counted: "


def _why(db, sd, b):
    """Why The month does not count this marked paper (S582_BRIEF_R1 C4), in the order the brief names."""
    if (b["status"] or "") == "rejected":
        return "rejected / set aside"
    if b["dup_of"]:
        return "second scan"
    if b["page_of"]:
        h = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["page_of"],)).fetchone()
        return "a page of %s" % (_stamp(h) if h else "another paper")
    dk, cs = (b["doc_kind"] or ""), (b["challan_state"] or "")
    if dk == "challan":
        if cs in ("", "awaiting"):
            return "challan awaiting"
        if cs == "joined":
            h = db.execute("SELECT id, stamp_no FROM bills WHERE id=?", (b["challan_of"],)).fetchone() if b["challan_of"] else None
            return "challan joined to %s" % (_stamp(h) if h else "a bill")
        if cs == "closed":
            return "challan closed"
        if cs != "final":
            return "challan %s" % cs
    if dk == "receipt":
        return "receipt"
    if dk == "statement":
        return "statement"
    try:
        if db.execute("SELECT 1 FROM bills b WHERE b.id=?" + sd._S566_NOT_HELD, (b["id"],)).fetchone() is None:
            return "held double (D710)"
    except (sqlite3.Error, AttributeError):
        pass
    sec = _section_of(sd, b["subgroup"])
    if sec is None:
        return "in no section of The month"
    lanes = ("clinic", "other_doc", "owner_expense") if sec[0] == "construction" else ("clinic",)
    if _lane(b) not in lanes:
        return "not on the clinic lane"
    if (b["status"] or "") not in (("draft", "approved", "captured") if sec[0] == "construction" else ("draft", "approved")):
        return "not accepted (%s)" % (b["status"] or "no status")
    return "not counted by The month"


class Month(object):
    """One month's view, computed when read. All sums in rupees (float)."""


def month_view(db, ym, cache=None):
    """The page's whole month: films, marked papers, machines, batteries, the totals -- each rupee once."""
    cache = {} if cache is None else cache
    v = Month()
    v.ym = ym
    sd = _sd()
    v.desk = sd is not None
    cp = sys.modules.get("clinic_papers")
    pm, mm, bm = cache.get("marks") or (live_marks(db, "paper"), live_marks(db, "machine"), live_marks(db, "battery_place"))
    cache["marks"] = (pm, mm, bm)
    if "claims" not in cache:                                         # (1) all months: a counted row claims its paper(s)
        rows = machine_rows(db, mm) + battery_rows(db, bm)
        claim = {}
        for r in rows:
            for p in r["papers"]:
                claim.setdefault(p["id"], []).append(r)
        for r in rows:
            r["shared"] = any(len(claim.get(p["id"], [])) > 1 for p in r["papers"])
        cache["claims"] = (rows, claim)
    rows, claim = cache["claims"]

    def claimed_by(bid):
        rs_ = claim.get(bid) or []
        return rs_[0] if rs_ else None

    # (2) X-ray films -- The month's own selection and sum
    v.films, v.films_month_total, v.films_claimed, v.films_total, v.films_name = [], 0.0, [], 0.0, "X-ray films"
    film_ids = set()
    if sd is not None:
        sec = _films_section(sd)
        if sec is not None:
            key, v.films_name, subs = sec
            money, finals = sd._s566_paid_rows(db, key, subs, ym)
            paid = list(money) + list(finals)
            v.films_month_total = float(sd._s566_total(paid))
            for b in paid:
                film_ids.add(b["id"])
                c = claimed_by(b["id"])
                row = {"b": b, "stamp": _stamp(b), "href": _href(b["id"]), "date": b["bill_date"] or b["created_at"], "vendor": b["vendor"] or "",
                       "amount": b["total_amount"], "sub": {"xray_small": "small film", "xray_11x14": "11 × 14"}.get(b["subgroup"], "size not known"),
                       "final": (b["doc_kind"] or "") == "challan", "claimed": c}
                v.films.append(row)
                if c is not None:
                    v.films_claimed.append(row)
            v.films_total = v.films_month_total - sum(float(r["amount"] or 0) for r in v.films_claimed)

    # (3) marked papers -- counted only when The month counts them in their own section, for the month MONTH_OF gives them
    v.papers, v.papers_total = [], 0.0
    if pm:
        mo_sql = cp.MONTH_OF if (cp is not None and hasattr(cp, "MONTH_OF")) else "substr(b.created_at,1,7)"
        ids = sorted(pm)
        for i in range(0, len(ids), 400):
            part = ids[i:i + 400]
            for b in db.execute("SELECT b.*, " + mo_sql + " AS mo FROM bills b WHERE b.id IN (" + ",".join("?" * len(part)) + ") ORDER BY b.id", part):
                if b["mo"] != ym:
                    continue
                if _lane(b) == "pharmacy" or (b["subgroup"] or "") == "patient_paper":      # D722: never shown
                    continue
                row = {"b": b, "mark": pm[b["id"]], "stamp": _stamp(b), "href": _href(b["id"]), "date": b["bill_date"] or b["created_at"],
                       "vendor": b["vendor"] or "", "amount": b["total_amount"], "counted": False, "why": "", "under": None, "flag": ""}
                sec = _section_of(sd, b["subgroup"]) if sd is not None else None
                row["section"] = sec[1] if sec else {"personal": "Personal (you only)"}.get(b["subgroup"] or "", (b["subgroup"] or "no group").replace("_", " "))
                c = claimed_by(b["id"])
                if c is not None:
                    row["why"], row["under"] = "its paper — counted under %s" % c["what"], c
                elif b["id"] in film_ids:
                    row["why"] = "already counted under %s" % v.films_name
                elif sd is None:
                    row["why"] = NOT_COUNTED + "The month is not mounted"
                else:
                    counted = False
                    if sec is not None:
                        money, finals = sd._s566_paid_rows(db, sec[0], sec[2], ym)
                        counted = b["id"] in {x["id"] for x in list(money) + list(finals)}
                    if counted:
                        row["counted"] = True
                        if b["total_amount"] is None:
                            row["flag"] = "no amount"
                        else:
                            v.papers_total += float(b["total_amount"])
                        a = db.execute("SELECT id, name FROM assets WHERE bill_id=? ORDER BY id LIMIT 1", (b["id"],)).fetchone()
                        if a is not None:                                              # S582_BRIEF_R1 N3: counted, flagged
                            row["flag"] = (row["flag"] + " · " if row["flag"] else "") + "purchase paper of %s" % a["name"]
                    else:
                        row["why"] = NOT_COUNTED + _why(db, sd, b)
                v.papers.append(row)

    # (1) the rows of the marked machines and battery places in this month
    v.machines = [r for r in rows if r["src"] in ("spend", "cover") and r["month"] == ym]
    v.batteries = [r for r in rows if r["src"] == "battery" and r["month"] == ym]
    v.unread = [r for r in rows if r["month"] is None]
    for r in v.machines + v.batteries:
        r["paper_links"] = [(_stamp(p), _href(p["id"])) for p in r["papers"]]
    v.machines_total = sum(r["cost"] for r in v.machines)
    v.batteries_total = sum(r["cost"] for r in v.batteries)
    v.total = v.films_total + v.papers_total + v.machines_total + v.batteries_total
    return v


def first_month(db, cache):
    """The first month with any X-ray cost (films counted by The month, a counted marked paper, a spend, cover or fitting)."""
    sd = _sd()
    cp = sys.modules.get("clinic_papers")
    cand = []
    if sd is not None and cp is not None:
        sec = _films_section(sd)
        if sec is not None:
            ph = ",".join("?" * len(sec[2]))
            r = db.execute("SELECT MIN(" + cp.MONTH_OF + ") FROM bills b WHERE b.subgroup IN (" + ph + ") AND b.total_amount IS NOT NULL", sec[2]).fetchone()
            if r and r[0]:
                cand.append(r[0])
        pm = live_marks(db, "paper")
        if pm:
            ids = sorted(pm)[:900]
            r = db.execute("SELECT MIN(" + cp.MONTH_OF + ") FROM bills b WHERE b.id IN (" + ",".join("?" * len(ids)) + ")", ids).fetchone()
            if r and r[0]:
                cand.append(r[0])
    month_view(db, _today().strftime("%Y-%m"), cache)
    rows, _claim = cache["claims"]
    cand += [r["month"] for r in rows if r["month"] and r["cost"]]
    cand = [c for c in cand if ym_ok(c)]
    return min(cand) if cand else None


def since_total(db, cache, upto):
    """(the first month with a cost, the total from it to `upto` -- the current month), each month by month_view; the loop starts
    at the earliest candidate month and is bounded (S582_BRIEF_R1 N5); (None, 0) when nothing is counted yet."""
    fm = first_month(db, cache)
    if fm is None or fm > upto:
        return None, 0.0
    tot, ym, n, first = 0.0, fm, 0, None
    while ym <= upto and n < 600:
        t = month_view(db, ym, cache).total
        if t and first is None:
            first = ym
        tot += t
        ym, n = ym_shift(ym, 1), n + 1
    return first, (tot if first else 0.0)


def machines_list(db, mm):
    """Every machine: (row, looks like X-ray, ticked) -- the X-ray-looking ones first (never ticked by the system)."""
    out = []
    try:
        rows = db.execute("SELECT a.id, a.name, a.category, a.hidden, l.name loc FROM assets a LEFT JOIN locations l ON l.id=a.location_id ORDER BY a.name, a.id").fetchall()
    except sqlite3.Error:
        rows = []
    for a in rows:
        looks = bool(LOOKS.search(a["name"] or "") or LOOKS.search(a["loc"] or ""))
        out.append({"id": a["id"], "name": a["name"], "loc": a["loc"] or "", "looks": looks, "on": a["id"] in mm})
    out.sort(key=lambda x: (not x["looks"], (x["name"] or "").lower(), x["id"]))
    return out


def places_list(db, bm):
    out = []
    try:
        rows = db.execute("SELECT id, name, grp, active FROM battery_place ORDER BY sort, id").fetchall()
    except sqlite3.Error:
        rows = []
    for p in rows:
        if not p["active"] and p["id"] not in bm:
            continue
        looks = bool(LOOKS.search(p["name"] or ""))
        out.append({"id": p["id"], "name": p["name"], "looks": looks, "on": p["id"] in bm, "active": p["active"]})
    out.sort(key=lambda x: (not x["looks"],))
    return out


# ---------------------------------------------------------------------------------------------- the page
CSS = """<style>
#s582 h2{margin:0 0 4px}
#s582 .nav{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;margin:4px 0 10px}
#s582 .nav a.btn{padding:5px 12px}
#s582 .tot{font-size:17px;margin:2px 0 12px}
#s582 .tot b{font-size:22px}
#s582 details.card>summary{cursor:pointer;font-weight:600;color:#1C1C1A;font-size:16px}
#s582 details.card>summary .amt{float:right;font-weight:600}
#s582 table{width:100%;border-collapse:collapse;font-size:14px;table-layout:fixed;margin-top:8px}
#s582 th{text-align:left;font-weight:500;color:#4A4A45;padding:6px 8px}
#s582 td{padding:6px 8px;border-top:1px solid #ECECE6;vertical-align:top;overflow-wrap:anywhere}
#s582 td.r,#s582 th.r{text-align:right;white-space:nowrap}
#s582 .sub{font-size:12px;color:#5A5A55}
#s582 .nc{color:#8A5A00}
#s582 .flag{color:#9A3412;font-size:12px}
#s582 .note{background:#EEF3F8;border-radius:8px;padding:8px 10px;font-size:14px;margin:8px 0 0}
#s582 form.inl{display:inline;margin:0}
#s582 form.inl button{padding:2px 8px;font-size:12px}
#s582 .ticks{columns:2 340px;column-gap:24px;margin-top:8px}
#s582 .ticks label{display:flex;gap:8px;align-items:flex-start;break-inside:avoid;font-size:14px;margin:0 0 6px}
#s582 .ticks input{width:auto;margin:2px 0 0}
#s582 .looks{font-size:12px;color:#8A5A00}
</style>"""

COLS = Markup("""<colgroup><col style="width:105px"><col><col style="width:22%"><col style="width:150px"><col style="width:120px"></colgroup>""")

PAGE_TPL = CSS + """<div id=s582>
<h2 id=s582head>X-ray expenses — {{label(v.ym)}}</h2>
<div class=nav><a class="btn small" href="{{url_for('s582_xray', ym=prev)}}">‹ {{label(prev)}}</a>{% if nxt %}<a class="btn small" href="{{url_for('s582_xray', ym=nxt)}}">{{label(nxt)}} ›</a>{% endif %}
<form method=get action="{{url_for('s582_xray')}}" style="display:flex;gap:6px;align-items:center;margin:0"><input type=month name=ym value="{{v.ym}}" max="{{this}}" style="margin:0;max-width:170px"><button class="btn small">Show</button></form></div>
<p class=tot id=s582tot data-total="{{'%.2f'|format(v.total)}}" data-since="{{'%.2f'|format(since)}}"><b>{{rs(v.total)}}</b> this month{% if first %} · <b>{{rs(since)}}</b> since {{label(first)}}{% else %} · nothing counted for X-ray yet{% endif %}</p>
{% if v.unread %}<div class=note id=s582unread>Date not read on {{v.unread|length}} entr{{'y' if v.unread|length == 1 else 'ies'}} of the marked machines / battery places — not counted in any month: {% for r in v.unread %}{{r.what}} ({{r.date or 'no date'}}){{', ' if not loop.last}}{% endfor %}.</div>{% endif %}

<details class=card id=s582films open data-total="{{'%.2f'|format(v.films_total)}}"><summary>{{v.films_name}} <span class=amt>{{rs(v.films_total)}}</span></summary>
{% if not v.desk %}<p class=muted>The sorting desk is not mounted — The month cannot be read, so X-ray films show ₹0.</p>{% else %}
<p class=sub style="margin:6px 0 0">Read with The month’s own rule (its “{{v.films_name}}” section). The month shows <b id=s582filmsmonth data-v="{{'%.2f'|format(v.films_month_total)}}">{{rs(v.films_month_total)}}</b> for {{label(v.ym)}}.{% for r in v.films_claimed %} {{rs(r.amount or 0)}} of it ({{r.stamp}}) is counted under {{r.claimed.what}}.{% endfor %}</p>
{% if v.films %}<table>{{cols}}<tr><th>Date</th><th>What</th><th>Supplier</th><th class=r>Amount</th><th>Paper</th></tr>
{% for r in v.films %}<tr data-paper="{{r.b.id}}"><td>{{dmy(r.date)}}</td><td>{{r.sub}}{% if r.final %} · challan (final){% endif %}{% if r.claimed %}<div class=sub>counted under {{r.claimed.what}}</div>{% endif %}</td><td>{{r.vendor}}</td>
<td class=r>{% if r.claimed %}<span class=sub>{{rs(r.amount)}} (counted there)</span>{% elif r.amount is none %}no amount{% else %}{{rs(r.amount)}}{% endif %}</td><td><a href="{{r.href}}">{{r.stamp}}</a></td></tr>{% endfor %}</table>
{% else %}<p class=muted>No X-ray film paper counted this month.</p>{% endif %}{% endif %}</details>

<details class=card id=s582papers open data-total="{{'%.2f'|format(v.papers_total)}}"><summary>Papers marked for X-ray <span class=amt>{{rs(v.papers_total)}}</span></summary>
<p class=sub style="margin:6px 0 0">A marked paper stays in its own group; it adds here only when The month counts it as spend.</p>
{% if v.papers %}<table>{{cols}}<tr><th>Date</th><th>What</th><th>Supplier</th><th class=r>Amount</th><th>Paper</th></tr>
{% for r in v.papers %}<tr data-paper="{{r.b.id}}"><td>{{dmy(r.date)}}</td><td>{{r.section}}{% if r.flag %} <span class=flag>{{r.flag}}</span>{% endif %}{% if not r.counted %}<div class=sub>{{r.why}}</div>{% endif %}</td><td>{{r.vendor}}</td>
<td class=r>{% if r.counted %}{% if r.amount is none %}no amount{% else %}{{rs(r.amount)}}{% endif %}{% else %}<span class=nc>{{'not counted' if r.why.startswith('not counted') else '—'}}</span>{% endif %}</td>
<td><a href="{{r.href}}">{{r.stamp}}</a> <form method=post class=inl action="{{url_for('s582_mark')}}"><input type=hidden name=do value=unmark><input type=hidden name=kind value=paper><input type=hidden name=ref value="{{r.b.id}}"><input type=hidden name=ym value="{{v.ym}}"><button class="btn small">Unmark</button></form></td></tr>{% endfor %}</table>
{% else %}<p class=muted>No paper of {{label(v.ym)}} is marked for X-ray.</p>{% endif %}
<form method=post action="{{url_for('s582_mark')}}" id=s582markform style="display:flex;flex-wrap:wrap;gap:8px;align-items:flex-end;margin-top:10px"><input type=hidden name=do value=paper><input type=hidden name=ym value="{{v.ym}}">
<label style="margin:0">+ Mark a paper for X-ray — its stamp<input name=stamp placeholder="B-0162" required style="max-width:130px;margin:0"></label><button class="btn small">Mark</button></form></details>

<details class=card id=s582machines open data-total="{{'%.2f'|format(v.machines_total)}}"><summary>Machines marked for X-ray — service, repair and cover <span class=amt>{{rs(v.machines_total)}}</span></summary>
<p class=sub style="margin:6px 0 0">Spends by their date, covers by their from-date. A machine’s purchase price is the asset, not an expense here.</p>
{% if v.machines %}<table>{{cols}}<tr><th>Date</th><th>What</th><th>By / provider</th><th class=r>Amount</th><th>Paper</th></tr>
{% for r in v.machines %}<tr data-row="{{r.src}}-{{r.id}}"><td>{{dmy(r.date)}}</td><td><a href="{{url_for('asset_view', aid=r.aid)}}">{{r.what}}</a>{% if r.note %} <span class=flag>{{r.note}}</span>{% endif %}{% if r.shared %} <span class=flag>one paper, two entries — check</span>{% endif %}</td><td>{{r.who}}</td>
<td class=r>{% if r.nocost %}no amount{% else %}{{rs(r.cost)}}{% endif %}</td><td>{% for s, h in r.paper_links %}<span class=sub>its paper</span> <a href="{{h}}">{{s}}</a>{{' · ' if not loop.last}}{% endfor %}{% if r.stale %}<span class=flag>paper link stale</span>{% endif %}</td></tr>{% endfor %}</table>
{% else %}<p class=muted>No spend or cover of a marked machine in {{label(v.ym)}}.</p>{% endif %}</details>

<details class=card id=s582batteries open data-total="{{'%.2f'|format(v.batteries_total)}}"><summary>Batteries of the X-ray places <span class=amt>{{rs(v.batteries_total)}}</span></summary>
{% if v.batteries %}<table>{{cols}}<tr><th>Fitted</th><th>What</th><th>Supplier</th><th class=r>Price</th><th>Paper</th></tr>
{% for r in v.batteries %}<tr data-row="{{r.src}}-{{r.id}}"><td>{{dmy(r.date)}}</td><td><a href="{{url_for('s571_place', pid=r.pid) if has_bt else '#'}}">{{r.what}}</a>{% if r.shared %} <span class=flag>one paper, two entries — check</span>{% endif %}</td><td>{{r.who}}</td>
<td class=r>{% if r.nocost %}no price{% else %}{{rs(r.cost)}}{% endif %}</td><td>{% for s, h in r.paper_links %}<span class=sub>its paper</span> <a href="{{h}}">{{s}}</a>{{' · ' if not loop.last}}{% endfor %}{% if r.stale %}<span class=flag>paper link stale</span>{% endif %}</td></tr>{% endfor %}</table>
{% else %}<p class=muted style="margin:6px 0 0">No battery fitted at a marked place in {{label(v.ym)}}.</p>{% endif %}</details>

<details class=card id=s582mmarks><summary>Machines — which count for X-ray <span class=muted style="font-weight:400">({{machines|selectattr('on')|list|length}} ticked)</span></summary>
<p class=sub style="margin:6px 0 0">Tick a machine to count its service, repair and cover here. Machines whose name or room mentions X-ray, FDR, CR or digitiser are listed first — the system never ticks one by itself.</p>
<form method=post action="{{url_for('s582_mark')}}"><input type=hidden name=do value=ticks><input type=hidden name=kind value=machine><input type=hidden name=ym value="{{v.ym}}">
<div class=ticks>{% for a in machines %}<label><input type=checkbox name=on value="{{a.id}}"{{' checked' if a.on}}><input type=hidden name=listed value="{{a.id}}"><span>{{a.name}}{% if a.loc %} <span class=sub>· {{a.loc}}</span>{% endif %}{% if a.looks and not a.on %} <span class=looks>looks like X-ray — tick to count</span>{% endif %}</span></label>{% endfor %}</div>
<button class="btn small">Save the ticks</button></form></details>

<details class=card id=s582pmarks><summary>Battery places — which count for X-ray <span class=muted style="font-weight:400">({{places|selectattr('on')|list|length}} ticked)</span></summary>
<form method=post action="{{url_for('s582_mark')}}"><input type=hidden name=do value=ticks><input type=hidden name=kind value=battery_place><input type=hidden name=ym value="{{v.ym}}">
<div class=ticks>{% for p in places %}<label><input type=checkbox name=on value="{{p.id}}"{{' checked' if p.on}}><input type=hidden name=listed value="{{p.id}}"><span>{{p.name}}{% if not p.active %} <span class=sub>· off the list</span>{% endif %}{% if p.looks and not p.on %} <span class=looks>looks like X-ray — tick to count</span>{% endif %}</span></label>{% endfor %}</div>
<button class="btn small">Save the ticks</button></form></details>
<p class=muted style="font-size:13px">Yours only. Marks never change a paper, a machine or a battery place — a paper stays in its own group. Each rupee is counted once: a spend, cover or battery’s own paper is shown under it and not counted again.</p>
</div>"""


def _owner_gate(fn):
    """The owner only (inside the app's checker gate: not signed in -> 302; reception -> 403). A manager gets 403."""
    def w(*a, **k):
        if not _owner():
            abort(403)
        return fn(*a, **k)
    w.__name__ = fn.__name__
    return w


def page():
    db = AR.get_db()
    this = _today().strftime("%Y-%m")
    ym = request.args.get("ym", "")
    if not ym_ok(ym) or ym > this:
        ym = this
    cache = {}
    v = month_view(db, ym, cache)
    first, since = since_total(db, cache, this)
    pm, mm, bm = cache["marks"]
    try:
        back = url_for("s551_month") if _sd() is not None else url_for("s571_page")
    except Exception:                                                # noqa: BLE001
        back = None
    return AR.page(PAGE_TPL, v=v, label=label, rs=rs, dmy=dmy, prev=ym_shift(ym, -1), nxt=(ym_shift(ym, 1) if ym < this else None),
                   this=this, first=first, since=since, cols=COLS, machines=machines_list(db, mm), places=places_list(db, bm),
                   has_bt=_bt() is not None, flow=AR._flow("X-ray expenses", back))


def _paper_month(db, b):
    cp = sys.modules.get("clinic_papers")
    try:
        r = db.execute("SELECT " + (cp.MONTH_OF if cp is not None else "substr(b.created_at,1,7)") + " FROM bills b WHERE b.id=?", (b["id"],)).fetchone()
        return r[0] if r and ym_ok(r[0]) else None
    except sqlite3.Error:
        return None


def post_mark():
    db = AR.get_db()
    f = request.form
    do = (f.get("do") or "").strip()
    ym = f.get("ym") if ym_ok(f.get("ym")) else None
    anchor = "s582papers"
    try:
        if do == "paper":                                             # S582_BRIEF_R1 C3: batteries.by_stamp, the desk's visibility
            bt = sys.modules.get("batteries")
            typed = re.sub(r"\s+", "", f.get("stamp") or "")[:24]
            if bt is None or not hasattr(bt, "by_stamp"):
                raise ValueError("Find by stamp is not available (the Batteries part is not loaded).")
            try:
                b = bt.by_stamp(db, typed, True)
            except ValueError:
                raise ValueError("No paper %s that you may mark here." % (bt.stamp_form(typed) or "with that stamp"))
            made = mark(db, "paper", b["id"])
            db.commit()
            pmo = _paper_month(db, b)
            flash(("Marked %s for X-ray (%s). It stays in its own group." if made else "%s is already marked for X-ray (%s).")
                  % (_stamp(b), label(pmo) if pmo else "month not read"))
            ym = pmo or ym
        elif do == "unmark":
            kind = f.get("kind") if f.get("kind") in KINDS else "paper"
            n = unmark(db, kind, f.get("ref"))
            db.commit()
            flash("Unmarked — it no longer counts for X-ray." if n else "It was not marked.")
            anchor = {"paper": "s582papers", "machine": "s582mmarks", "battery_place": "s582pmarks"}[kind]
        elif do == "ticks":
            kind = f.get("kind") if f.get("kind") in ("machine", "battery_place") else None
            if kind is None:
                abort(400)
            listed = {int(x) for x in f.getlist("listed") if str(x).isdigit()}
            on = {int(x) for x in f.getlist("on") if str(x).isdigit()} & listed
            have = set(live_marks(db, kind))
            add, drop = sorted(on - have), sorted((have & listed) - on)
            for x in add:
                mark(db, kind, x)
            for x in drop:
                unmark(db, kind, x)
            db.commit()
            word = "machine" if kind == "machine" else "battery place"
            flash("Saved: %d %s%s now count for X-ray%s." % (len(on), word, "" if len(on) == 1 else "s",
                                                         (" (%d added, %d taken off)" % (len(add), len(drop))) if (add or drop) else " (no change)"))
            anchor = "s582mmarks" if kind == "machine" else "s582pmarks"
        else:
            abort(400)
    except ValueError as e:
        db.rollback()
        flash(str(e) + " Nothing was marked.")
    return redirect(url_for("s582_xray", ym=ym, _anchor=anchor) if ym else url_for("s582_xray", _anchor=anchor))


def menu_items(role):
    """For batteries.menu_items (the one menu, right after Batteries): "X-ray costs" -- the owner only; nothing for anyone else."""
    try:
        if MOUNTED and role == "owner":
            return [("s582_xray", "X-ray costs", url_for("s582_xray"))]
    except Exception:                                                # noqa: BLE001
        pass
    return []


# ---------------------------------------------------------------------------------------------- the mount
def init(ar):
    """Called once, from the end of batteries.init (guarded there)."""
    global AR, MOUNTED
    AR = ar
    ensure_at_mount(ar.DB_PATH)
    app, cr = ar.app, ar.checker_required
    app.add_url_rule("/xray", "s582_xray", cr(_owner_gate(page)))
    app.add_url_rule("/xray/mark", "s582_mark", cr(_owner_gate(post_mark)), methods=["POST"])
    MOUNTED = True
    return VERSION


if __name__ == "__main__":
    # the installer's data step:  python3 xray_costs.py --ensure <assets.db>
    if len(sys.argv) >= 3 and sys.argv[1] == "--ensure":
        ls, n = ensure_path(sys.argv[2])
        for x in ls:
            print(x)
        print("xray_costs %s: table xray_mark ready; live marks %d" % (VERSION, n))
    else:
        print(__doc__)
