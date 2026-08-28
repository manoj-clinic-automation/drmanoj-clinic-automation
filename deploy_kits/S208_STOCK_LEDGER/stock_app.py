#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""stock_app.py — the stock loop, as a blueprint inside the finance app.

    expected (Marg) -> counted (staff) -> difference -> cause -> closed

WHY IT LIVES INSIDE finance_app AND NOT BESIDE IT
    Same Flask process, same finance.db, same unit_role table, same fail-closed
    gate, same backup. A second service would mean a second set of users, a
    second backup nobody takes, and a second thing to notice has died.

WHAT IT IS FOR
    Stock leaves the shop by several doors. It is sold, or returned to a
    vendor -- Marg records those well. It is also issued for clinic use, thrown
    away expired, broken, received and never entered, or sold and never billed.
    Those leave no trace at all until a physical count finds the hole, and by
    then nobody remembers which door it went out of.

    So: capture the difference the day it is found, name the door while the
    memory is fresh, and keep it open until Marg's own numbers agree again.
    Over a few counts that becomes the only honest answer to "where does the
    stock go", by cause, by item, by month, in rupees.

INSTALL: two lines in finance_app.py. See README.md.

Flask and the standard library only, to match the app it joins.
"""
import datetime as dt
import io
import json
import os
import sqlite3
import sys

from flask import Blueprint, jsonify, request

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "stock_schema.sql")

bp = Blueprint("stock", __name__)

# The doors stock goes out of. UNEXPLAINED is the default and it is meant to be
# used: a cause guessed to make the list look tidy is worse than an honest
# blank, because it becomes a number in a report later.
CAUSES = ("UNEXPLAINED", "EXPIRY", "BREAKAGE", "ISSUE", "RECEIVE",
          "BILLING", "FOUND", "THEFT")
CAUSE_LABEL = {
    "UNEXPLAINED": "not yet explained",
    "EXPIRY":      "expired, removed",
    "BREAKAGE":    "broken or damaged",
    "ISSUE":       "issued for clinic use",
    "RECEIVE":     "received but not entered",
    "BILLING":     "sold but not billed, or billed as another item",
    "FOUND":       "turned up later",
    "THEFT":       "taken",
}

_db = None            # () -> sqlite3.Connection, injected by init()
_require = None       # (*roles) -> (user, errorresponse), injected by init()
_unit = "medical"
_marg_token = ""    # the pharmacy sender's token, injected by init()


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def ensure_schema(con):
    """Idempotent. Safe to call on every boot; safe to call twice."""
    with io.open(SCHEMA, "r", encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.commit()


def init(app, db_getter, require_fn, unit="medical", url_prefix="/stock",
         marg_token=""):
    """Mount the blueprint. finance_app calls this once, after its own setup.

    marg_token is the pharmacy sender's token (FINANCE_MARG_TOKEN). It is
    injected so that /api/snapshot can be posted by the machine on manojz that
    already holds it. It grants NO identity and NO role -- see _snapshot_auth.
    """
    global _db, _require, _unit, _marg_token
    _db, _require, _unit = db_getter, require_fn, unit
    _marg_token = marg_token or ""
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


def _snapshot_auth():
    """Who may load a Marg snapshot: a signed-in checker/maker, OR the sender.

    WHY THE SECOND DOOR EXISTS
        The whole point of this ledger is that a difference closes ITSELF when
        Marg's own numbers next agree. That needs the newest export pushed in
        by a machine, nightly, with nobody signed in. Requiring a human role
        here is what made push_snapshot.py unusable: it was refused before the
        route ever ran, and the only evidence went to a console nobody reads.

    WHY IT IS NARROW
        The token grants exactly this one path. It returns no identity and no
        role, so it cannot set a cause, cannot submit a count, cannot read the
        losses -- it can only load Marg's own published stock figures, which is
        what it already holds a copy of. Defense in depth: the app's front gate
        checks this token too, and this handler checks it again, exactly as
        /finance/api/marg-push does.

    Returns (user, None) when allowed, (None, error_response) when not.
    """
    if _marg_token and request.headers.get("X-Finance-Marg") == _marg_token:
        return {"user": "push_snapshot", "roles": []}, None
    return _require("checker", "maker")


# ------------------------------------------------------------------ helpers
def _rate_p(con, item):
    r = con.execute("SELECT rate_p FROM stock_rate WHERE item=?", (item,)).fetchone()
    return (r[0] if not hasattr(r, "keys") else r["rate_p"]) if r else None


def _value_p(con, item, diff):
    rp = _rate_p(con, item)
    return None if rp is None else int(round(rp * diff))


def reconcile(con, as_on):
    """Close every open difference the newest export now agrees with.

    THE RULE, and it is deliberately strict: a difference closes only when the
    export's quantity equals what the counter actually found. Not "moved in the
    right direction", not "close enough". Anything else is a second, smaller
    difference and it stays open under its own number.

    Nobody has to remember to tick anything off. That is the point -- a manual
    'mark as done' step is the step that stops being done in week three.
    """
    closed = 0
    rows = con.execute(
        "SELECT d.id, d.item, d.counted_qty FROM stock_diff d WHERE d.status='open'"
    ).fetchall()
    for r in rows:
        did = r[0] if not hasattr(r, "keys") else r["id"]
        item = r[1] if not hasattr(r, "keys") else r["item"]
        cq = r[2] if not hasattr(r, "keys") else r["counted_qty"]
        s = con.execute("SELECT qty FROM stock_snapshot WHERE as_on=? AND item=?",
                        (as_on, item)).fetchone()
        if s is None:
            continue
        qty = s[0] if not hasattr(s, "keys") else s["qty"]
        if int(qty) == int(cq):
            con.execute("UPDATE stock_diff SET status='reconciled', closed_as_on=?, "
                        "closed_at=? WHERE id=?", (as_on, now_iso(), did))
            closed += 1
    con.commit()
    return closed


# ------------------------------------------------------------------- routes
@bp.route("/api/healthz")
def healthz():
    con = _db()
    ensure_schema(con)
    n_open = con.execute("SELECT COUNT(*) FROM stock_diff WHERE status='open'").fetchone()[0]
    n_counts = con.execute("SELECT COUNT(*) FROM stock_count").fetchone()[0]
    return jsonify(ok=True, unit=_unit, counts=n_counts, open_diffs=n_open,
                   causes=list(CAUSES))


@bp.route("/api/snapshot", methods=["POST"])
def api_snapshot():
    """Load one Marg closing-stock export's quantities, then auto-reconcile.

    Body: {"as_on":"27-08-2026","source":"...","items":[{"item":..,"qty":..,
           "packing":..,"pack_size":..,"rate_p":..}, ...]}
    """
    u, err = _snapshot_auth()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    as_on = (b.get("as_on") or "").strip()
    items = b.get("items") or []
    if not as_on or not isinstance(items, list) or not items:
        return jsonify(ok=False, error="bad_request",
                       message="as_on and a non-empty items list are required."), 400
    con = _db()
    ensure_schema(con)
    n = 0
    for it in items:
        name = (it.get("item") or "").strip()
        if not name:
            continue
        con.execute(
            "INSERT INTO stock_snapshot (as_on,item,qty,packing,pack_size,loaded_at,source) "
            "VALUES (?,?,?,?,?,?,?) ON CONFLICT(as_on,item) DO UPDATE SET "
            "qty=excluded.qty, packing=excluded.packing, pack_size=excluded.pack_size, "
            "loaded_at=excluded.loaded_at, source=excluded.source",
            (as_on, name, int(it.get("qty") or 0), it.get("packing"),
             int(it.get("pack_size") or 1), now_iso(), b.get("source")))
        if it.get("rate_p") is not None:
            con.execute(
                "INSERT INTO stock_rate (item,rate_p,pack_size,as_of,source) VALUES (?,?,?,?,?) "
                "ON CONFLICT(item) DO UPDATE SET rate_p=excluded.rate_p, "
                "as_of=excluded.as_of, source=excluded.source",
                (name, int(it["rate_p"]), int(it.get("pack_size") or 1), as_on, b.get("source")))
        n += 1
    con.commit()
    closed = reconcile(con, as_on)
    return jsonify(ok=True, as_on=as_on, items=n, reconciled=closed)


@bp.route("/api/count", methods=["POST"])
def api_count():
    """Submit a completed count. Differences are raised here, once.

    Body: {"marg_as_on":..,"bill_no":..,"bill_date":..,"items_total":376,
           "items":[{"item":..,"marg_qty":..,"counted_qty":..,"strips":..,
                     "loose":..,"pack_size":..,"packing":..,"counted_by":..,
                     "entered_by":..,"at":..,"batches":{...}}]}
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    for k in ("marg_as_on", "bill_no", "bill_date"):
        if not (b.get(k) or "").strip():
            return jsonify(ok=False, error="bad_request",
                           message="marg_as_on, bill_no and bill_date are required — "
                                   "a count that is not pinned to a bill cannot be "
                                   "reconciled later."), 400
    items = b.get("items") or []
    if not items:
        return jsonify(ok=False, error="bad_request", message="No counted items."), 400

    con = _db()
    ensure_schema(con)
    cur = con.execute(
        "INSERT INTO stock_count (unit,marg_as_on,bill_no,bill_date,started_at,"
        "submitted_at,submitted_by,items_total,items_counted,status) "
        "VALUES (?,?,?,?,?,?,?,?,?,'submitted')",
        (_unit, b["marg_as_on"].strip(), b["bill_no"].strip().upper(),
         b["bill_date"].strip(), b.get("started_at") or now_iso(), now_iso(),
         u.get("user") or "", int(b.get("items_total") or len(items)), len(items)))
    cid = cur.lastrowid

    raised = 0
    for it in items:
        name = (it.get("item") or "").strip()
        if not name:
            continue
        marg = int(it.get("marg_qty") or 0)
        got = int(it.get("counted_qty") or 0)
        ps = int(it.get("pack_size") or 1)
        bat = it.get("batches")
        con.execute(
            "INSERT OR REPLACE INTO stock_count_item (count_id,item,packing,pack_size,"
            "marg_qty,counted_qty,strips,loose,counted_by,entered_by,at,batches) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (cid, name, it.get("packing"), ps, marg, got, it.get("strips"),
             it.get("loose"), it.get("counted_by"), it.get("entered_by"),
             it.get("at") or now_iso(),
             json.dumps(bat, ensure_ascii=False) if bat else None))
        if got != marg:
            d = got - marg
            con.execute(
                "INSERT INTO stock_diff (count_id,item,found_on,marg_qty,counted_qty,"
                "diff,pack_size,value_p,cause,status,counted_by) "
                "VALUES (?,?,?,?,?,?,?,?,'UNEXPLAINED','open',?)",
                (cid, name, b["marg_as_on"].strip(), marg, got, d, ps,
                 _value_p(con, name, d), it.get("counted_by")))
            raised += 1
    con.commit()
    return jsonify(ok=True, count_id=cid, items=len(items), differences=raised)


@bp.route("/api/open")
def api_open():
    # S208: this had no role check at all. Behind finance_app's fail-closed
    # gate it was never public, but "protected by something else" is how a
    # route ends up open the day it is mounted somewhere else. The machine
    # token must reach NOTHING but /api/snapshot, and this is what makes that
    # true in this file rather than in another one.
    u, err = _require("checker", "maker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    rows = con.execute(
        "SELECT id,item,found_on,marg_qty,counted_qty,diff,value_p,cause,cause_note,"
        "counted_by FROM stock_diff WHERE status='open' "
        "ORDER BY ABS(diff) DESC, item").fetchall()
    out = [dict(r) if hasattr(r, "keys") else dict(zip(
        ("id", "item", "found_on", "marg_qty", "counted_qty", "diff", "value_p",
         "cause", "cause_note", "counted_by"), r)) for r in rows]
    return jsonify(ok=True, open=len(out), items=out, causes=list(CAUSES),
                   labels=CAUSE_LABEL)


@bp.route("/api/diff/<int:did>/cause", methods=["POST"])
def api_cause(did):
    """Name the door it went out of. Checker only -- this is the judgement."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    cause = (b.get("cause") or "").strip().upper()
    if cause not in CAUSES:
        return jsonify(ok=False, error="bad_cause",
                       message="cause must be one of: %s" % ", ".join(CAUSES)), 400
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT id FROM stock_diff WHERE id=?", (did,)).fetchone()
    if not r:
        return jsonify(ok=False, error="not_found"), 404
    con.execute("UPDATE stock_diff SET cause=?, cause_note=?, cause_by=?, cause_at=? "
                "WHERE id=?", (cause, b.get("note"), u.get("user") or "",
                               now_iso(), did))
    con.commit()
    return jsonify(ok=True, id=did, cause=cause, label=CAUSE_LABEL[cause])


@bp.route("/api/losses")
def api_losses():
    """Where the stock actually goes, by cause and by item.

    Shortages only (diff < 0) for the loss totals -- a surplus is a different
    question and is reported separately rather than netted off. Netting them
    would hide two errors behind one small number.

    S208: role-checked here as well as at the app's front gate. This is money
    by cause -- it is not a page for whoever happens to be signed in.
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    frm = request.args.get("from") or "0000-00-00"
    to = request.args.get("to") or "9999-99-99"
    by_cause = con.execute(
        "SELECT cause, COUNT(*) n, SUM(-diff) units, SUM(COALESCE(-value_p,0)) value_p "
        "FROM stock_diff WHERE diff<0 AND found_on BETWEEN ? AND ? "
        "GROUP BY cause ORDER BY units DESC", (frm, to)).fetchall()
    by_item = con.execute(
        "SELECT item, COUNT(*) times, SUM(-diff) units, SUM(COALESCE(-value_p,0)) value_p "
        "FROM stock_diff WHERE diff<0 AND found_on BETWEEN ? AND ? "
        "GROUP BY item ORDER BY units DESC LIMIT 40", (frm, to)).fetchall()
    surplus = con.execute(
        "SELECT COUNT(*) n, SUM(diff) units FROM stock_diff "
        "WHERE diff>0 AND found_on BETWEEN ? AND ?", (frm, to)).fetchone()
    repeat = con.execute(
        "SELECT item, COUNT(*) times FROM stock_diff WHERE found_on BETWEEN ? AND ? "
        "GROUP BY item HAVING COUNT(*)>1 ORDER BY times DESC LIMIT 20",
        (frm, to)).fetchall()

    def L(rows, keys):
        return [dict(r) if hasattr(r, "keys") else dict(zip(keys, r)) for r in rows]
    return jsonify(
        ok=True, **{"from": frm}, to=to,
        by_cause=L(by_cause, ("cause", "n", "units", "value_p")),
        by_item=L(by_item, ("item", "times", "units", "value_p")),
        repeat_offenders=L(repeat, ("item", "times")),
        surplus=dict(surplus) if hasattr(surplus, "keys")
        else dict(zip(("n", "units"), surplus)),
        labels=CAUSE_LABEL)
