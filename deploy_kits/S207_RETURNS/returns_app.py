#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""returns_app.py -- the purchase-return lifecycle, as a blueprint inside the finance app.

    booked -> supplier told -> at reception -> handed over -> awaiting note -> closed

WHY THIS EXISTS
    A purchase return is the only transaction where the goods leave before the
    paper arrives.  Between the shelf and the credit note the stock is ours on
    nobody's books and in somebody's hands.  Five months of history holds five
    returns worth Rs 6,919 -- one of them Rs 4,042 on its own -- and there is
    no record anywhere of who carried any of them out of the door.

    An uncredited return is not a discrepancy.  It is money the vendor owes us
    and nobody is counting.  This blueprint counts it, names every hand-off,
    and asks once a day about anything still open.

WHY THE STATUS IS A CACHE AND THE EVENTS ARE THE TRUTH
    Every stage writes an append-only row to pret_event.  The status column on
    the header is rebuilt from that trail (see rebuild_status), so a status
    that has been fiddled with is detectable rather than authoritative.  A
    lifecycle whose history can be edited is a lifecycle nobody can rely on
    three months later, which is exactly when a return gets chased.

    It also refuses to skip stages, and says so in words a person can act on.
    A return that jumps from booked to closed is the shape of the loss this is
    supposed to prevent.

INSTALL: two lines in finance_app.py.  See README.md.

Flask and the standard library only, to match the app it joins.
"""
import datetime as dt
import io
import os
import re
import sqlite3

from flask import Blueprint, jsonify, request

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "returns_schema.sql")

bp = Blueprint("returns", __name__)

# The stages, in the only order they may happen.  NOTIFIED is optional in
# practice -- a vendor is sometimes told when his man is already at the counter
# -- so it is allowed to be skipped, and nothing else is.
FLOW = ("BOOKED", "NOTIFIED", "AT_RECEPTION", "HANDED", "AWAITING_NOTE", "CLOSED")
SKIPPABLE = ("NOTIFIED",)
TERMINAL = ("CLOSED", "WRITTEN_OFF", "REFUSED")

STAGE_LABEL = {
    "BOOKED":        "set aside for return",
    "NOTIFIED":      "supplier told",
    "AT_RECEPTION":  "at reception, custody taken",
    "HANDED":        "handed to their man",
    "AWAITING_NOTE": "waiting for the credit note",
    "CLOSED":        "credit note entered, closed",
    "WRITTEN_OFF":   "written off, no credit expected",
    "REFUSED":       "vendor refused it",
}

REASONS = ("NEAR_EXPIRY", "EXPIRED", "DAMAGED", "WRONG_SUPPLY", "NOT_MOVING")
REASON_LABEL = {
    "NEAR_EXPIRY":  "close to expiry",
    "EXPIRED":      "already expired",
    "DAMAGED":      "damaged or broken",
    "WRONG_SUPPLY": "not what was ordered",
    "NOT_MOVING":   "does not sell",
}

# How long a return may sit at each stage before the daily reminder names it.
# Deliberately short at the start and long at the end: goods sitting in a
# corner marked "to return" is how a return quietly becomes a write-off, while
# a vendor genuinely does take weeks over a credit note.
CHASE_DAYS = {
    "BOOKED":        3,
    "NOTIFIED":      3,
    "AT_RECEPTION":  2,
    "HANDED":        1,
}

# AWAITING_NOTE is NOT a day count. Owner's ruling, 28-Aug-2026: a credit note
# is due "UPTO 7TH OF NEXT MTH" -- the 7th of the month AFTER the goods went out.
#
# WHY IT IS A DATE AND NOT A NUMBER OF DAYS, WHICH IS WHAT I HAD BUILT
#     A rolling 21 days chases a 2-August return on the 23rd, when the vendor
#     has not closed his month yet and there is nothing to chase; and it chases
#     a 29-August return on 19 September, twelve days after the deadline had
#     already passed. Vendors settle by the month, so the deadline is a date in
#     the month, and every return handed over in the same month falls due on the
#     same day. That is also the shape a person can hold in their head: "anything
#     from last month should be credited by the 7th."
CREDIT_NOTE_DUE_DAY = 7


def credit_due(handed_on):
    """The date a credit note is due for goods that went out on handed_on.

    The 7th of the following month. December rolls to January of the next year,
    which is the one case a naive month+1 gets wrong.
    """
    d = dt.date.fromisoformat(str(handed_on)[:10])
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return dt.date(y, m, CREDIT_NOTE_DUE_DAY)

_db = None
_require = None
_unit = "medical"


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def today():
    return dt.date.today().isoformat()


def ensure_schema(con):
    """Idempotent. Safe to call on every boot; safe to call twice."""
    with io.open(SCHEMA, "r", encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.commit()


def init(app, db_getter, require_fn, unit="medical", url_prefix="/returns"):
    """Mount the blueprint. finance_app calls this once, after its own setup."""
    global _db, _require, _unit
    _db, _require, _unit = db_getter, require_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ------------------------------------------------------------------ helpers
def _v(row, key, idx):
    return row[key] if hasattr(row, "keys") else row[idx]


def next_ref(con, when=None):
    """PR-2026-0001.  Financial year, not calendar year -- Marg counts that way
    and so does every conversation about a return."""
    d = dt.date.fromisoformat(when) if when else dt.date.today()
    fy = d.year if d.month >= 4 else d.year - 1
    pre = "PR-%d-" % fy
    r = con.execute("SELECT ref FROM pret WHERE ref LIKE ? ORDER BY ref DESC LIMIT 1",
                    (pre + "%",)).fetchone()
    n = (int(_v(r, "ref", 0).rsplit("-", 1)[1]) + 1) if r else 1
    return "%s%04d" % (pre, n)


def rebuild_status(con, pret_id):
    """The status from the trail alone. The stored column is only a cache."""
    rows = con.execute("SELECT kind FROM pret_event WHERE pret_id=? ORDER BY id",
                       (pret_id,)).fetchall()
    st = "BOOKED"
    for r in rows:
        k = _v(r, "kind", 0)
        if k in FLOW or k in TERMINAL:
            st = k
    return st


def can_advance(cur, nxt):
    """(ok, why-not). Stages may be skipped only where SKIPPABLE says so."""
    if nxt in ("WRITTEN_OFF", "REFUSED"):
        return (cur not in TERMINAL,
                "" if cur not in TERMINAL else "This return is already %s." % STAGE_LABEL[cur])
    if cur in TERMINAL:
        return False, "This return is already %s and cannot move again." % STAGE_LABEL[cur]
    if nxt not in FLOW:
        return False, "%s is not a stage." % nxt
    i, j = FLOW.index(cur), FLOW.index(nxt)
    if j <= i:
        return False, "It is already at '%s'." % STAGE_LABEL[cur]
    skipped = [s for s in FLOW[i + 1:j] if s not in SKIPPABLE]
    if skipped:
        return False, ("It cannot go straight to '%s' -- nobody has recorded '%s' yet. "
                       "That gap is exactly where a return goes missing."
                       % (STAGE_LABEL[nxt], STAGE_LABEL[skipped[0]]))
    return True, ""


def days_since(iso):
    if not iso:
        return None
    try:
        d = dt.date.fromisoformat(iso[:10])
    except ValueError:
        return None
    return (dt.date.today() - d).days


def stage_since(con, pret_id, status):
    r = con.execute("SELECT at FROM pret_event WHERE pret_id=? AND kind=? "
                    "ORDER BY id DESC LIMIT 1", (pret_id, status)).fetchone()
    if r:
        return _v(r, "at", 0)
    r = con.execute("SELECT created_at FROM pret WHERE id=?", (pret_id,)).fetchone()
    return _v(r, "created_at", 0) if r else None


def overdue(con):
    """Everything open past its stage's patience. The daily reminder is this."""
    out = []
    rows = con.execute("SELECT id, ref, vendor, status, value_p, chase_muted FROM pret "
                       "WHERE status NOT IN ('CLOSED','WRITTEN_OFF','REFUSED')").fetchall()
    for r in rows:
        pid, ref = _v(r, "id", 0), _v(r, "ref", 1)
        st = _v(r, "status", 3)
        if _v(r, "chase_muted", 5):
            continue
        since = stage_since(con, pid, st)
        age = days_since(since)
        if st == "AWAITING_NOTE":
            # due on the 7th of the month after the goods went out -- and it is
            # the HANDED date that starts the clock, not the day somebody got
            # round to marking it as awaiting.
            h = con.execute("SELECT handed_on FROM pret WHERE id=?", (pid,)).fetchone()
            base = (_v(h, "handed_on", 0) if h else None) or since
            try:
                due = credit_due(base)
            except (ValueError, TypeError):
                continue
            if dt.date.today() <= due:
                continue
            limit = (due - dt.date.fromisoformat(str(base)[:10])).days
            age = (dt.date.today() - dt.date.fromisoformat(str(base)[:10])).days
            due_txt = due.isoformat()
        else:
            limit = CHASE_DAYS.get(st)
            due_txt = None
            if age is None or limit is None or age < limit:
                continue
        items = [_v(x, "item", 0) for x in con.execute(
            "SELECT item FROM pret_line WHERE pret_id=? ORDER BY id", (pid,)).fetchall()]
        out.append({"id": pid, "ref": ref, "vendor": _v(r, "vendor", 2),
                    "status": st, "stage": STAGE_LABEL.get(st, st),
                    "days": age, "limit": limit, "due_on": due_txt,
                    "value_p": _v(r, "value_p", 4), "items": items})
    out.sort(key=lambda x: (-(x["days"] - x["limit"]), x["ref"]))
    return out


def match_credits(con):
    """Close what the vendor's own credit note now confirms.

    THE RULE, matching the stock loop: a line closes only when a credit note
    for the same item and batch covers its quantity. Not 'about right'. A
    part-credit leaves the remainder open under the same reference, because a
    vendor who credits half is exactly the case worth seeing.
    """
    closed_lines, closed_refs = 0, []
    lines = con.execute(
        "SELECT l.id,l.pret_id,l.item,l.batch,l.qty,l.matched_qty,p.vendor "
        "FROM pret_line l JOIN pret p ON p.id=l.pret_id "
        "WHERE l.matched_qty < l.qty AND p.status NOT IN ('CLOSED','WRITTEN_OFF','REFUSED')"
    ).fetchall()
    for l in lines:
        lid, pid = _v(l, "id", 0), _v(l, "pret_id", 1)
        item, batch = _v(l, "item", 2), _v(l, "batch", 3)
        need = int(_v(l, "qty", 4)) - int(_v(l, "matched_qty", 5))
        vendor = _v(l, "vendor", 6)
        q = ("SELECT id,qty,note_no,note_on FROM pret_credit WHERE used_by IS NULL "
             "AND item=? AND (? IS NULL OR batch IS NULL OR batch=?) "
             "AND (? IS NULL OR vendor IS NULL OR vendor=?) ORDER BY id")
        for c in con.execute(q, (item, batch, batch, vendor, vendor)).fetchall():
            if need <= 0:
                break
            cq = int(_v(c, "qty", 1))
            take = min(cq, need)
            con.execute("UPDATE pret_line SET matched_qty=matched_qty+? WHERE id=?", (take, lid))
            con.execute("UPDATE pret_credit SET used_by=? WHERE id=?", (lid, _v(c, "id", 0)))
            need -= take
            if need <= 0:
                closed_lines += 1
                con.execute("UPDATE pret SET note_no=COALESCE(note_no,?), "
                            "note_on=COALESCE(note_on,?) WHERE id=?",
                            (_v(c, "note_no", 2), _v(c, "note_on", 3), pid))
    # a return closes when every one of its lines is fully credited
    for pid in {_v(l, "pret_id", 1) for l in lines}:
        r = con.execute("SELECT COUNT(*) FROM pret_line WHERE pret_id=? AND matched_qty < qty",
                        (pid,)).fetchone()
        if int(_v(r, "COUNT(*)", 0)) == 0:
            con.execute("INSERT INTO pret_event (pret_id,at,actor,kind,detail) "
                        "VALUES (?,?,?,?,?)",
                        (pid, now_iso(), "system", "CLOSED",
                         "credit note matched automatically"))
            con.execute("UPDATE pret SET status='CLOSED', closed_on=?, closed_by='system', "
                        "updated_at=? WHERE id=?", (today(), now_iso(), pid))
            rr = con.execute("SELECT ref FROM pret WHERE id=?", (pid,)).fetchone()
            closed_refs.append(_v(rr, "ref", 0))
    con.commit()
    return closed_lines, closed_refs


# ------------------------------------------------------------------- routes
@bp.route("/api/healthz")
def healthz():
    con = _db()
    ensure_schema(con)
    n_open = con.execute("SELECT COUNT(*) FROM pret WHERE status NOT IN "
                         "('CLOSED','WRITTEN_OFF','REFUSED')").fetchone()[0]
    n_all = con.execute("SELECT COUNT(*) FROM pret").fetchone()[0]
    return jsonify(ok=True, unit=_unit, returns=n_all, open=n_open,
                   overdue=len(overdue(con)), stages=list(FLOW),
                   reasons=list(REASONS))


@bp.route("/api/book", methods=["POST"])
def api_book():
    """Raise a return. One vendor, one or more item lines.

    Body: {"vendor":..,"booked_by":"Darpan","lines":[{"item":..,"batch":..,
           "expiry":"02/2025","qty":25,"pack_size":1,"reason":"EXPIRED",
           "rate_p":..,"purchase_bill":..}, ...]}

    vendor may be blank -- a return recorded without one is far better than a
    return not recorded -- but a line with no item or no quantity is refused,
    because that is not a record of anything.
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    who = (b.get("booked_by") or "").strip()
    lines = b.get("lines") or []
    if not who:
        return jsonify(ok=False, error="bad_request",
                       message="Who is setting these aside? A name is required."), 400
    clean = []
    for l in lines:
        item = (l.get("item") or "").strip()
        try:
            qty = int(l.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0
        if not item or qty <= 0:
            continue
        reason = (l.get("reason") or "NEAR_EXPIRY").strip().upper()
        if reason not in REASONS:
            return jsonify(ok=False, error="bad_reason",
                           message="'%s' is not a reason. Use one of: %s"
                                   % (reason, ", ".join(REASONS))), 400
        clean.append((item, l.get("batch"), l.get("expiry"), qty,
                      int(l.get("pack_size") or 1), l.get("packing"), reason,
                      l.get("rate_p"), l.get("purchase_bill")))
    if not clean:
        return jsonify(ok=False, error="no_lines",
                       message="Nothing to return -- every line needs an item and a quantity."), 400
    con = _db()
    ensure_schema(con)
    ref = next_ref(con, b.get("booked_on"))
    val = sum(int(c[7]) * c[3] for c in clean if c[7] is not None) or None
    cur = con.execute(
        "INSERT INTO pret (ref,vendor,status,booked_on,booked_by,value_p,created_at,updated_at) "
        "VALUES (?,?,'BOOKED',?,?,?,?,?)",
        (ref, (b.get("vendor") or "").strip() or None, b.get("booked_on") or today(),
         who, val, now_iso(), now_iso()))
    pid = cur.lastrowid
    for c in clean:
        con.execute("INSERT INTO pret_line (pret_id,item,batch,expiry,qty,pack_size,packing,"
                    "reason,rate_p,purchase_bill,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (pid,) + c + (now_iso(),))
    con.execute("INSERT INTO pret_event (pret_id,at,actor,person,kind,detail) "
                "VALUES (?,?,?,?,'BOOKED',?)",
                (pid, now_iso(), u, who, "%d line(s) set aside" % len(clean)))
    con.commit()
    return jsonify(ok=True, ref=ref, id=pid, lines=len(clean), value_p=val)


@bp.route("/api/advance", methods=["POST"])
def api_advance():
    """Move one return to its next stage, naming the person who did it.

    Body: {"ref":"PR-2026-0001","to":"HANDED","person":"Shavez",
           "collector":"Ravi's man","collector_ph":"98xxxxxxxx","detail":".."}
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ref = (b.get("ref") or "").strip()
    to = (b.get("to") or "").strip().upper()
    person = (b.get("person") or "").strip()
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT id,status FROM pret WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_return",
                       message="No return called %s." % (ref or "(blank)")), 404
    pid, cur = _v(r, "id", 0), _v(r, "status", 1)
    if not person:
        return jsonify(ok=False, error="no_person",
                       message="Whose hands is it in now? A name is required at every "
                               "stage -- that is the whole point of this list."), 400
    ok, why = can_advance(cur, to)
    if not ok:
        return jsonify(ok=False, error="bad_stage", message=why,
                       status=cur, stage=STAGE_LABEL.get(cur, cur)), 409
    con.execute("INSERT INTO pret_event (pret_id,at,actor,person,kind,detail) "
                "VALUES (?,?,?,?,?,?)",
                (pid, now_iso(), u, person, to, (b.get("detail") or "").strip() or None))
    sets, args = ["status=?", "updated_at=?"], [to, now_iso()]
    col = {"NOTIFIED": ("notified_on", "notified_by"),
           "AT_RECEPTION": ("reception_on", "reception_by"),
           "HANDED": ("handed_on", "handed_by"),
           "CLOSED": ("closed_on", "closed_by")}.get(to)
    if col:
        sets += ["%s=?" % col[0], "%s=?" % col[1]]
        args += [today(), person]
    if to == "HANDED":
        sets += ["collector=?", "collector_ph=?"]
        args += [(b.get("collector") or "").strip() or None,
                 (b.get("collector_ph") or "").strip() or None]
    if to == "CLOSED":
        sets += ["note_no=COALESCE(?,note_no)", "note_on=COALESCE(?,note_on)"]
        args += [(b.get("note_no") or "").strip() or None, b.get("note_on") or today()]
    args.append(pid)
    con.execute("UPDATE pret SET %s WHERE id=?" % ",".join(sets), args)
    con.commit()
    return jsonify(ok=True, ref=ref, status=to, stage=STAGE_LABEL.get(to, to),
                   rebuilt=rebuild_status(con, pid))


@bp.route("/api/credits", methods=["POST"])
def api_credits():
    """Load credit notes read out of Marg, then match and close what they cover.

    Body: {"source":"..","credits":[{"vendor":..,"item":..,"batch":..,"qty":25,
           "note_no":..,"note_on":"2026-09-04","value_p":..}, ...]}
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    rows = b.get("credits") or []
    if not isinstance(rows, list) or not rows:
        return jsonify(ok=False, error="bad_request",
                       message="A non-empty credits list is required."), 400
    con = _db()
    ensure_schema(con)
    n = 0
    for c in rows:
        item = (c.get("item") or "").strip()
        try:
            q = int(c.get("qty") or 0)
        except (TypeError, ValueError):
            q = 0
        if not item or q <= 0:
            continue
        dup = con.execute("SELECT id FROM pret_credit WHERE item=? AND COALESCE(batch,'')=? "
                          "AND qty=? AND COALESCE(note_no,'')=?",
                          (item, c.get("batch") or "", q, c.get("note_no") or "")).fetchone()
        if dup:
            continue
        con.execute("INSERT INTO pret_credit (vendor,item,batch,qty,note_no,note_on,value_p,"
                    "source,loaded_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    ((c.get("vendor") or "").strip() or None, item, c.get("batch"), q,
                     c.get("note_no"), c.get("note_on"), c.get("value_p"),
                     b.get("source"), now_iso()))
        n += 1
    con.commit()
    lines, refs = match_credits(con)
    return jsonify(ok=True, loaded=n, lines_credited=lines, closed=refs)


@bp.route("/api/open")
def api_open():
    """Everything not yet closed, oldest first, with its stage and its age."""
    con = _db()
    ensure_schema(con)
    out = []
    for r in con.execute("SELECT id,ref,vendor,status,booked_on,value_p,chase_muted "
                         "FROM pret WHERE status NOT IN ('CLOSED','WRITTEN_OFF','REFUSED') "
                         "ORDER BY booked_on, ref").fetchall():
        pid = _v(r, "id", 0)
        st = _v(r, "status", 3)
        lines = [{"item": _v(x, "item", 0), "batch": _v(x, "batch", 1),
                  "qty": _v(x, "qty", 2), "pack_size": _v(x, "pack_size", 3),
                  "reason": _v(x, "reason", 4),
                  "reason_label": REASON_LABEL.get(_v(x, "reason", 4), _v(x, "reason", 4)),
                  "credited": _v(x, "matched_qty", 5)}
                 for x in con.execute("SELECT item,batch,qty,pack_size,reason,matched_qty "
                                      "FROM pret_line WHERE pret_id=? ORDER BY id",
                                      (pid,)).fetchall()]
        out.append({"ref": _v(r, "ref", 1), "vendor": _v(r, "vendor", 2), "status": st,
                    "stage": STAGE_LABEL.get(st, st), "booked_on": _v(r, "booked_on", 4),
                    "age_days": days_since(_v(r, "booked_on", 4)),
                    "at_stage_days": days_since(stage_since(con, pid, st)),
                    "value_p": _v(r, "value_p", 5),
                    "muted": bool(_v(r, "chase_muted", 6)), "lines": lines})
    return jsonify(ok=True, count=len(out), returns=out)


@bp.route("/api/chase")
def api_chase():
    """The daily reminder, as data. Whatever sends it reads this."""
    con = _db()
    ensure_schema(con)
    o = overdue(con)
    return jsonify(ok=True, count=len(o), as_on=today(), overdue=o,
                   value_p=sum(x["value_p"] or 0 for x in o))


@bp.route("/api/trail")
def api_trail():
    """The custody trail of one return, and whether its status matches it."""
    con = _db()
    ensure_schema(con)
    ref = (request.args.get("ref") or "").strip()
    r = con.execute("SELECT id,status FROM pret WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_return",
                       message="No return called %s." % (ref or "(blank)")), 404
    pid, st = _v(r, "id", 0), _v(r, "status", 1)
    ev = [{"at": _v(x, "at", 0), "actor": _v(x, "actor", 1), "person": _v(x, "person", 2),
           "kind": _v(x, "kind", 3), "stage": STAGE_LABEL.get(_v(x, "kind", 3), _v(x, "kind", 3)),
           "detail": _v(x, "detail", 4)}
          for x in con.execute("SELECT at,actor,person,kind,detail FROM pret_event "
                               "WHERE pret_id=? ORDER BY id", (pid,)).fetchall()]
    rebuilt = rebuild_status(con, pid)
    return jsonify(ok=True, ref=ref, status=st, rebuilt=rebuilt,
                   consistent=(st == rebuilt), events=ev)


@bp.route("/api/mute", methods=["POST"])
def api_mute():
    """Stop chasing one return, with a reason. It stays open and stays counted."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ref = (b.get("ref") or "").strip()
    why = (b.get("detail") or "").strip()
    if not why:
        return jsonify(ok=False, error="no_reason",
                       message="Silencing a reminder needs a reason on the record."), 400
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT id FROM pret WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_return", message="No return called %s." % ref), 404
    pid = _v(r, "id", 0)
    on = 0 if b.get("unmute") else 1
    con.execute("UPDATE pret SET chase_muted=?, updated_at=? WHERE id=?", (on, now_iso(), pid))
    con.execute("INSERT INTO pret_event (pret_id,at,actor,kind,detail) VALUES (?,?,?,?,?)",
                (pid, now_iso(), u, "UNMUTED" if not on else "MUTED", why))
    con.commit()
    return jsonify(ok=True, ref=ref, muted=bool(on))


@bp.route("/api/vendor_quality")
def api_vendor_quality():
    """Returns by vendor and reason. A purchasing signal, once there is enough of it.

    It says so out loud when there is not: five returns in five months is not a
    pattern, and a dashboard that presents it as one will get a vendor blamed.
    """
    con = _db()
    ensure_schema(con)
    rows = con.execute(
        "SELECT COALESCE(p.vendor,'(not recorded)') v, l.reason, COUNT(*) n, "
        "SUM(COALESCE(l.rate_p,0)*l.qty) val FROM pret_line l JOIN pret p ON p.id=l.pret_id "
        "GROUP BY v, l.reason ORDER BY val DESC").fetchall()
    total = con.execute("SELECT COUNT(*) FROM pret").fetchone()[0]
    out = [{"vendor": _v(r, "v", 0), "reason": _v(r, "reason", 1),
            "reason_label": REASON_LABEL.get(_v(r, "reason", 1), _v(r, "reason", 1)),
            "returns": _v(r, "n", 2), "value_p": _v(r, "val", 3)} for r in rows]
    return jsonify(ok=True, rows=out, total_returns=total,
                   enough_to_judge=total >= 30,
                   caveat=None if total >= 30 else
                   "Only %d returns on record. Too few to judge any vendor by -- "
                   "read this as a list, not as a verdict." % total)
