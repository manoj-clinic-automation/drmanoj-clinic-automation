#!/usr/bin/env python3
# =============================================================================
#  hub_cash.py  ·  v1.0  ·  kit S869_HUB_DAYS_CASH  ·  Session 482 (Sanjeevni), 18-Nov-2026 (D1005)
#
#  THE OWNER'S OWN ENTRIES ON A COUNTER DAY, AND WHY THE DRAWER READS WHAT IT READS.
#  His words (S481, 11:16-11:59): money that never reached the drawer (a patient paid into the
#  NK Pathology UPI; a UPI into another account) and cash taken out of the drawer on a doctor's
#  word (Rs 4,000 given to Darpan by Dr Bhawna for personal expenses) explain a short handover
#  without a reason from Darpan.  Owner only; never on Darpan's or Bhati's screens.
#
#  ONE table, owner_day_entry:  kind 'other_account' = the money never entered the drawer (the
#  day's cash for the drawer is less by it); kind 'taken_out' = it left the drawer and counts
#  WITH the doctors (party dr_bhawna / dr_manoj / pool).  An entry is removed by him, never
#  deleted (removed_at).  sanjeevni_cash.days() -- the one calculation -- reads it.
#
#  Doors (checker = the owner; the Hub is his page):
#    GET  /finance/sanjeevni/api/hub-cash/healthz
#    GET  /finance/sanjeevni/api/drawer-why          why the drawer reads Rs X: each short day, its cause, its actions
#    POST /finance/sanjeevni/api/day-entry           {date, kind, amount_p, party, purpose, note}
#    POST /finance/sanjeevni/api/day-entry/remove    {id}
#    POST /finance/sanjeevni/api/received-all        {party='dr_bhawna'}: every handover to her not yet marked received, stamped by him
#  Every write is audited (audit_log, darpan_kal_audit for the receipt).  Stdlib + Flask only.
# =============================================================================
import datetime as dt
import json
import sqlite3

from flask import Blueprint, jsonify, request

VERSION = "1.0"
KIT = "S869_HUB_DAYS_CASH"
bp = Blueprint("hub_cash", __name__)
_db = _require = None
_unit = "medical"
KINDS = ("other_account", "taken_out")
PARTIES = ("dr_bhawna", "dr_manoj", "pool")
PURPOSES = ("personal", "clinic_expense", "other")
PARTY_EN = {"dr_bhawna": "Dr Bhawna", "dr_manoj": "you", "pool": "the pool"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS owner_day_entry (
    id INTEGER PRIMARY KEY,
    unit TEXT NOT NULL, business_date TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('other_account','taken_out')),
    amount_p INTEGER NOT NULL CHECK (amount_p > 0),
    party TEXT, purpose TEXT, note TEXT,
    entered_by TEXT NOT NULL, entered_at TEXT NOT NULL,
    removed_by TEXT, removed_at TEXT);
CREATE INDEX IF NOT EXISTS ix_owner_day_entry_day ON owner_day_entry (unit, business_date);
"""


def init(app, db_getter, require_fn, unit="medical"):
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


def ensure_schema(con):
    for stmt in [s.strip() for s in SCHEMA.split(";") if s.strip()]:
        con.execute(stmt)


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def rs(p):
    if p is None:
        return None
    neg, v = p < 0, abs(int(round(p / 100.0)))
    s = str(v)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s


def _dmy(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%d-%b")
    except ValueError:
        return iso


def tolerance_p(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='darpan_kal.tolerance_p'").fetchone()
        return int(r[0]) if r and str(r[0]).strip() else 5000
    except (sqlite3.OperationalError, TypeError, ValueError):
        return 5000


# ------------------------------------------------------------------ the entries (read by the one calculation)
def entries(con, unit="medical", date_from="0000-00-00", date_to="9999-12-31"):
    """{business_date: [entry dicts]} -- the live (not removed) entries. {} when the table is not there yet."""
    out = {}
    if not _has(con, "owner_day_entry"):
        return out
    for r in con.execute("SELECT id, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at "
                         "FROM owner_day_entry WHERE unit=? AND removed_at IS NULL AND business_date BETWEEN ? AND ? "
                         "ORDER BY business_date, id", (unit, date_from, date_to)):
        out.setdefault(r[1], []).append(dict(id=r[0], date=r[1], kind=r[2], amount_p=int(r[3]), party=r[4] or "",
                                              purpose=r[5] or "", note=r[6] or "", by=r[7], at=r[8]))
    return out


def entry_words(e):
    """One line for an entry, English."""
    if e["kind"] == "other_account":
        return "%s paid into another account%s%s" % (rs(e["amount_p"]), (" (%s)" % e["party"]) if e["party"] else "",
                                                     (" -- " + e["note"]) if e["note"] else "")
    who = PARTY_EN.get(e["party"], e["party"] or "the doctors")
    purp = {"personal": "personal expenses", "clinic_expense": "a clinic expense", "other": "other"}.get(e["purpose"], e["purpose"] or "")
    return "%s cash taken out, with %s%s%s" % (rs(e["amount_p"]), who, (" -- " + purp) if purp else "",
                                               (" -- " + e["note"]) if e["note"] else "")


# ------------------------------------------------------------------ why the drawer reads what it reads
def drawer_why(con, unit="medical"):
    """Every day since the anchor whose cash for the drawer exceeded what left it by more than the tolerance,
    with its cause (Darpan's reason, the owner's decision, the entries) and the actions open to the owner."""
    import sanjeevni_cash as sc                                # noqa: PLC0415
    r = sc.days(con, "0000-00-00", "9999-12-31", unit)
    if not r.get("ok"):
        return dict(ok=False, error=r.get("error"), message=r.get("message", ""))
    tol = tolerance_p(con)
    kal = {}
    if _has(con, "darpan_kal_day"):
        try:
            for k in con.execute("SELECT business_date, handed_p, handed_to, diff_p, reason, reason_note, state, verdict, "
                                 "owner_decision, owner_note, received_at FROM darpan_kal_day WHERE unit=?", (unit,)):
                kal[k[0]] = dict(handed_p=k[1], to=k[2], diff_p=k[3], reason=k[4], note=k[5], state=k[6], verdict=k[7],
                                 decision=k[8], owner_note=k[9], received=bool(k[10]))
        except sqlite3.OperationalError:                        # an older darpan_kal_day: no causes, the days still listed
            kal = {}
    ent = entries(con, unit)
    closed = []
    if _has(con, "cash_period_close"):                          # a closed period (August: its handovers covered several days each)
        closed = con.execute("SELECT date_from, date_to FROM cash_period_close WHERE unit=?", (unit,)).fetchall()
    cover = {}                                                  # a handover that paid for OTHER days: its cover rows, by the day it covers
    if _has(con, "cash_handover_cover"):
        for src, hid, cd, amt in con.execute("SELECT handover_src, handover_id, covers_date, amount_p FROM cash_handover_cover WHERE unit=?", (unit,)):
            cover.setdefault(cd, []).append((src, int(hid), int(amt)))
    days, total, not_yet = [], 0, []
    for x in r["rows"]:
        d = x["date"]
        if any(f <= d <= t for f, t in closed):
            continue
        left = 0
        for h in x["handed"]:
            if h["src"] in ("movement", "custody"):             # a recorded handover: count it for the days its cover rows name
                mine = [c for c in cover.get(d, []) if (c[0], c[1]) == (h["src"], h["id"])]
                others = sum(c[2] for cd, cs in cover.items() if cd != d for c in cs if (c[0], c[1]) == (h["src"], h["id"]))
                left += (mine[0][2] if mine else h["amount_p"] - others)
            else:
                left += h["amount_p"]
        left += sum(c[2] for c in cover.get(d, []) if not any((hh.get("src"), hh.get("id")) == (c[0], c[1]) for hh in x["handed"]))
        resid = x["into_drawer_p"] - left
        k = kal.get(d) or {}
        if resid > tol and not k and x.get("waiting_approval"):    # an ordinary morning: filed from Marg, not yet handed over
            not_yet.append(dict(date=d, day=_dmy(d), cash=rs(x["into_drawer_p"]), cash_p=x["into_drawer_p"]))
            continue
        if resid <= tol:
            continue
        cause, acts = [], []
        try:                                                    # F-1459: the bank's UPI came after the day was approved
            st = con.execute("SELECT parsed_total_p FROM upi_statement WHERE unit=? AND statement_date=?", (unit, d)).fetchone()
            if st is not None and int(st[0] or 0) != int(x["upi_p"]) and int(st[0] or 0) <= int(x["sale_p"]):
                cause.append("the bank settled %s by UPI; the day still holds %s -- the resync corrects it within 30 minutes"
                             % (rs(int(st[0] or 0)), rs(int(x["upi_p"]))))
        except sqlite3.OperationalError:
            pass
        if k.get("decision") == "accept":
            cause.append("you accepted this short on Darpan's page" + ((" -- " + k["owner_note"]) if k.get("owner_note") else ""))
        if k.get("reason") and k["reason"] != "none":
            cause.append("Darpan's reason: %s%s" % (k["reason"].replace("_", " "), (" -- " + k["note"]) if k.get("note") else ""))
        for e in ent.get(d, []):
            cause.append("your entry: " + entry_words(e))
        if not k:
            cause.append("not yet handed over -- no handover row for this day")
        elif not cause:
            cause.append("Darpan handed %s of %s -- no reason given" % (rs(int(k["handed_p"] or 0)), rs(x["into_drawer_p"])))
        acts.append("entry")
        if k and k.get("decision") != "accept":
            acts.append("accept")
        days.append(dict(date=d, day=_dmy(d), status=x["status"], cash=rs(x["into_drawer_p"]), cash_p=x["into_drawer_p"],
                         left=rs(left), left_p=left, short=rs(resid), short_p=resid, cause=cause, actions=acts,
                         handed_to=PARTY_EN.get(k.get("to"), k.get("to")) if k else None))
        total += resid
    close = r["rows"][-1]["close"] if r["rows"] else {}
    drawer = int(close.get("drawer", 0))
    waiting = sum(x["cash_p"] for x in not_yet)
    rest = drawer - total - waiting
    return dict(ok=True, drawer=rs(drawer), drawer_p=drawer, days=days, short_total=rs(total), short_total_p=total,
                not_yet=not_yet, waiting=rs(waiting), waiting_p=waiting,
                rest=rs(rest), rest_p=rest, rest_is_roundoffs=(abs(rest) <= 5 * tol), tolerance=rs(tol))


# ------------------------------------------------------------------ doors
@bp.route("/finance/sanjeevni/api/hub-cash/healthz")
def api_healthz():
    return jsonify(ok=True, version=VERSION, kit=KIT)


@bp.route("/finance/sanjeevni/api/drawer-why")
def api_drawer_why():
    u, err = _require("checker")
    if err:
        return err
    return jsonify(drawer_why(_db(), _unit))


def _valid_date(s):
    try:
        dt.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


@bp.route("/finance/sanjeevni/api/day-entry", methods=["POST"])
def api_day_entry():
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    iso = str(b.get("date") or "").strip()
    kind = str(b.get("kind") or "").strip()
    party = str(b.get("party") or "").strip()[:60]
    purpose = str(b.get("purpose") or "").strip()
    note = str(b.get("note") or "").strip()[:200]
    try:
        amt = int(b.get("amount_p"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_amount", message="type the amount in rupees"), 400
    if not _valid_date(iso) or iso > (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).date().isoformat():   # IST, not the box's clock
        return jsonify(ok=False, error="bad_date"), 400
    if kind not in KINDS or amt <= 0:
        return jsonify(ok=False, error="bad_request", message="which kind, and an amount above zero"), 400
    if kind == "taken_out":
        if party not in PARTIES:
            return jsonify(ok=False, error="bad_party", message="with whom -- Dr Bhawna, you, or the pool?"), 400
        if purpose not in PURPOSES:
            return jsonify(ok=False, error="bad_purpose", message="for what -- personal, a clinic expense, or other?"), 400
    else:
        purpose = ""
        if not party:
            return jsonify(ok=False, error="bad_party", message="which account did it go into?"), 400
    con = _db()
    ensure_schema(con)
    if not con.execute("SELECT 1 FROM day_entry WHERE unit=? AND business_date=?", (_unit, iso)).fetchone():
        return jsonify(ok=False, error="no_day", message="this day has not been filed from Marg yet"), 404
    now = now_iso()
    cur = con.execute("INSERT INTO owner_day_entry (unit, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", (_unit, iso, kind, amt, party, purpose or None, note or None, u["user"], now))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, after_json, by_whom, at) VALUES ('owner_day_entry', ?, 'create', ?, ?, ?)",
                (cur.lastrowid, json.dumps(dict(date=iso, kind=kind, amount_p=amt, party=party, purpose=purpose, note=note, kit=KIT)),
                 u["user"], now))
    con.commit()
    return jsonify(ok=True, id=cur.lastrowid, date=iso, entries=entries(con, _unit, iso, iso).get(iso, []))


@bp.route("/finance/sanjeevni/api/day-entry/remove", methods=["POST"])
def api_day_entry_remove():
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    try:
        eid = int(b.get("id"))
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_request"), 400
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT business_date, kind, amount_p, party, purpose, note FROM owner_day_entry "
                    "WHERE id=? AND unit=? AND removed_at IS NULL", (eid, _unit)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    now = now_iso()
    con.execute("UPDATE owner_day_entry SET removed_by=?, removed_at=? WHERE id=?", (u["user"], now, eid))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, by_whom, at) VALUES ('owner_day_entry', ?, 'remove', ?, ?, ?)",
                (eid, json.dumps(dict(date=r[0], kind=r[1], amount_p=int(r[2]), party=r[3], purpose=r[4], note=r[5], kit=KIT)),
                 u["user"], now))
    con.commit()
    return jsonify(ok=True, id=eid, date=r[0], entries=entries(con, _unit, r[0], r[0]).get(r[0], []))


def receive_all(con, who, party="dr_bhawna", unit="medical"):
    """Every handover to `party` not yet marked received: stamped by `who` (the owner), one darpan_kal_audit row each --
    the same stamp darpan_kal.api_received writes.  Returns the dates stamped."""
    if not _has(con, "darpan_kal_day"):
        return []
    rows = con.execute("SELECT business_date, handed_p, handed_to FROM darpan_kal_day WHERE unit=? AND handed_to=? "
                       "AND handed_p IS NOT NULL AND received_at IS NULL ORDER BY business_date", (unit, party)).fetchall()
    now = now_iso()
    done = []
    for d, hp, to in rows:
        con.execute("UPDATE darpan_kal_day SET received_by=?, received_at=?, updated_at=? WHERE unit=? AND business_date=? "
                    "AND received_at IS NULL", (who, now, now, unit, d))
        if _has(con, "darpan_kal_audit"):
            con.execute("INSERT INTO darpan_kal_audit (at, who, action, detail) VALUES (?,?,?,?)",
                        (now, who, "received", json.dumps(dict(date=d, handed_p=hp, to=to, by="the owner, for %s (%s)" % (party, KIT)))))
        done.append(d)
    return done


@bp.route("/finance/sanjeevni/api/received-all", methods=["POST"])
def api_received_all():
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    party = str(b.get("party") or "dr_bhawna").strip()
    if party not in ("dr_bhawna", "dr_manoj"):
        return jsonify(ok=False, error="bad_party"), 400
    con = _db()
    done = receive_all(con, u["user"], party, _unit)
    con.commit()
    return jsonify(ok=True, party=party, n=len(done), dates=done)
