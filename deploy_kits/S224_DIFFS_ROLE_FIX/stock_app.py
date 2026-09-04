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

v2 · S213 (F-245): the SCREENS. GET /page/count serves the S207 counting page
live, its item universe injected from this ledger's own newest stock_snapshot
(no more artifact copies of the data); GET /page/diffs serves the checker's
cause-naming screen over /api/open + /api/diff/<id>/cause. And /api/count no
longer trusts the client's marg_qty: the snapshot on THIS server is the
authority, the client's figure is only compared and reported. Every S208
route is otherwise untouched.
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
if not os.path.exists(SCHEMA):
    # in-repo (the walk runs from inside the kit folder): the schema lives in
    # the S208 kit; on the VPS it sits beside this file. Relative, never a
    # hard-coded mount (the S212 lesson).
    _alt = os.path.join(os.path.dirname(HERE), "S208_STOCK_LEDGER", "stock_schema.sql")
    if os.path.exists(_alt):
        SCHEMA = _alt
PAGE_COUNT = os.path.join(HERE, "stock_check_live.html")
PAGE_DIFFS = os.path.join(HERE, "stock_diffs.html")

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

# ---- S221 FINDING: the difference as an audit document ----------------------
PAGE_FINDING = os.path.join(HERE, "stock_finding.html")

# What the owner may rule on a line. WRITE_OFF and RECOVER are both his loss;
# they differ only in whether he intends to put it to a person. EXPLAINED is
# the honest third answer -- a counting error or a late arrival is not a loss,
# and forcing it into one of the other two would make the totals lie.
DECISIONS = ("WRITE_OFF", "RECOVER", "EXPLAINED")
DECISION_LABEL = {
    "WRITE_OFF": "written off",
    "RECOVER":   "marked for recovery",
    "EXPLAINED": "explained -- no loss",
}
# The staff's own words, in their own language. "pata nahin" is a real answer
# and is offered deliberately: a forced reason is a false reason.
STAFF_REASONS = {
    "count_error": "\u0917\u093f\u0928\u0924\u0940 \u092e\u0947\u0902 \u0917\u0932\u0924\u0940",
    "not_billed":  "\u092c\u093f\u0932 \u0928\u0939\u0940\u0902 \u092c\u0928\u093e",
    "breakage":    "\u091f\u0942\u091f / \u0916\u0930\u093e\u092c",
    "expiry":      "\u090f\u0915\u094d\u0938\u092a\u093e\u092f\u0930\u0940 \u092e\u0947\u0902 \u0917\u092f\u093e",
    "sample":      "\u0938\u0948\u0902\u092a\u0932 / \u0921\u0949\u0915\u094d\u091f\u0930 \u0915\u094b \u0926\u093f\u092f\u093e",
    "return":      "\u0935\u093e\u092a\u0938\u0940 \u0915\u093e \u092e\u093e\u0932",
    "dont_know":   "\u092a\u0924\u093e \u0928\u0939\u0940\u0902",
}
RECOVERY_BASIS = "MRP"          # the owner's ruling D-a, printed on the document

# ---- S221 TWO PRICES --------------------------------------------------------
PAGE_DRIFT = os.path.join(HERE, "stock_drift.html")

import re as _re221          # noqa: E402  -- this module does not import re itself

_PACK_RE = _re221.compile(r"(\d+)\s*\*\s*(\d+)")


def _pack_units(pack):
    """'1*10' -> 10 units in a strip; None when it cannot be read. Same rule as
    returns_desk._pack_n, which is the live-proven one."""
    m = _PACK_RE.search(str(pack or ""))
    if m:
        n = int(m.group(2))
        return n if 0 < n <= 1000 else None
    return None


def _mrp_p(con, item):
    """MRP for ONE unit, from the item's own sale lines.

    sale_line_item.amount_p is NOT an amount -- it is the printed rate of a
    full strip, repeated on every line whatever the quantity was. Divide by the
    pack and you have the unit price the shop actually charges. This is exactly
    what returns_desk._per_unit_p() already does; the rule is not new here.

    The MEDIAN across the item's lines, because a rate can change with a batch
    and one revision should not become the price. None when the item has never
    sold -- and none is returned honestly rather than falling back to cost,
    because a cost wearing an MRP label is the fault this whole kit corrects.
    """
    try:
        rows = con.execute(
            "SELECT amount_p, pack FROM sale_line_item WHERE item_key=? "
            "AND is_return=0 AND amount_p>0 ORDER BY business_date DESC LIMIT 200",
            (item,)).fetchall()
    except Exception:
        return None
    vals = []
    for r in rows:
        amt = r[0] if not hasattr(r, "keys") else r["amount_p"]
        pk = r[1] if not hasattr(r, "keys") else r["pack"]
        n = _pack_units(pk)
        if amt and n:
            vals.append(amt / float(n))
        elif amt and pk in (None, ""):
            vals.append(float(amt))
    if not vals:
        return None
    vals.sort()
    mid = len(vals) // 2
    med = vals[mid] if len(vals) % 2 else (vals[mid - 1] + vals[mid]) / 2.0
    return int(round(med))


def _mrp_value_p(con, item, diff):
    rp = _mrp_p(con, item)
    return None if rp is None else int(round(rp * diff))


FEED_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_feed (
  id INTEGER PRIMARY KEY,
  as_on TEXT NOT NULL,
  source TEXT NOT NULL,
  item TEXT NOT NULL,
  qty INTEGER NOT NULL,
  received_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_feed_item ON stock_feed(item, as_on);
CREATE INDEX IF NOT EXISTS idx_feed_ason ON stock_feed(as_on);
"""


def _feed_ensure(con):
    con.executescript(FEED_SCHEMA)


# ---- S221 PURCHASE DUE: the punch that asks for the export ------------------
PUNCH_CSV = os.environ.get("SR_PUNCH_CSV", "/root/punches.csv")
_PUR_TO_RE = _re221.compile(r"pur_to\s*=\s*(\d{4}-\d{2}-\d{2}|\d{2}-\d{2}-\d{4})")


def _iso(d):
    """dd-mm-yyyy or yyyy-mm-dd -> yyyy-mm-dd. None when it is neither."""
    s = str(d or "").strip()
    if _re221.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    m = _re221.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", s)
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else None


def _purchases_known_to(con):
    """The last date purchases are known up to, read out of the feed log.

    push_expected stamps it into the source string it sends; since
    S221_TWO_PRICES every source is kept. Nothing new is sent for this.
    """
    best = None
    try:
        for r in con.execute("SELECT DISTINCT source FROM stock_feed"):
            m = _PUR_TO_RE.search(str(r[0] or ""))
            if m:
                d = _iso(m.group(1))
                if d and (best is None or d > best):
                    best = d
    except Exception:
        return None
    return best


def _last_punch(staff_id):
    """The last date this person punched. None on ANY problem -- a missing or
    unreadable feed must never become 'he did not come'. Read exactly the way
    staff_register reads it; attendance owns the file and we only look."""
    if not staff_id:
        return None
    try:
        import csv as _csv                                    # noqa: PLC0415
        if not os.path.exists(PUNCH_CSV):
            return None
        want = str(staff_id).strip()
        last = None
        with open(PUNCH_CSV, newline="", encoding="utf-8") as fh:
            for row in _csv.DictReader(fh):
                if str(row.get("user_id") or "").strip() != want:
                    continue
                d = str(row.get("datetime") or "")[:10]
                if _re221.fullmatch(r"\d{4}-\d{2}-\d{2}", d) and (last is None or d > last):
                    last = d
    except Exception:
        return None
    return last


def purchase_due(con):
    """Is a purchase export owed, and why? READ-ONLY, and every branch says
    what it knows rather than implying more."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='purchase.staff_id'").fetchone()
        sid = (r[0] if r else None) or "101"
    except Exception:
        sid = "101"
    pur_to = _purchases_known_to(con)
    visit = _last_punch(sid)
    today = now_iso()[:10]

    def _days(a, b):
        try:
            return (dt.date.fromisoformat(b) - dt.date.fromisoformat(a)).days
        except Exception:
            return None

    out = dict(staff_id=str(sid), purchases_known_to=pur_to, last_visit=visit,
               punch_feed=os.path.exists(PUNCH_CSV), due=False, state="unknown",
               line="")
    if not pur_to:
        out["state"] = "no_purchase_date"
        out["line"] = ("No purchase date has reached the server yet. It arrives "
                       "stamped on the computed stock push, so this fills in "
                       "once that job has run.")
        return out
    out["stale_days"] = _days(pur_to, today)
    if visit and visit > pur_to:
        out["due"] = True
        out["state"] = "came_and_did_not_export"
        out["line"] = ("Purchases are known only to %s, and he was here on %s. "
                       "The export from that visit has not arrived." % (pur_to, visit))
    elif visit:
        out["state"] = "current_as_of_his_last_visit"
        out["line"] = ("Purchases are current as far as his last visit (%s). "
                       "Known to %s." % (visit, pur_to))
    else:
        out["state"] = "no_visit_seen"
        out["line"] = ("Purchases are known to %s. No punch has been seen for "
                       "this person%s." % (pur_to,
                                           "" if out["punch_feed"]
                                           else " -- and the punch feed is not readable "
                                                "from here, so this is not evidence "
                                                "that he did not come"))
    return out
# ---- end S221 PURCHASE DUE --------------------------------------------------


def _feed_kind(source):
    """Which of the two feeds this is. Anything else is kept and labelled, not
    guessed at -- an unrecognised sender must not silently become one of them."""
    s = (source or "").lower()
    if s.startswith("push_expected"):
        return "expected"
    if s.startswith("push_snapshot"):
        return "marg"
    return "other"
# ---- end S221 TWO PRICES helpers --------------------------------------------

FINDING_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_finding (
  count_id   INTEGER PRIMARY KEY REFERENCES stock_count(id),
  finding_no TEXT NOT NULL UNIQUE,
  sealed_at  TEXT NOT NULL,
  seal_md5   TEXT NOT NULL,
  basis      TEXT NOT NULL DEFAULT 'MRP',
  lines_n    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS stock_diff_answer (
  id INTEGER PRIMARY KEY, diff_id INTEGER NOT NULL REFERENCES stock_diff(id),
  reason TEXT NOT NULL, note TEXT,
  answered_by TEXT NOT NULL, answered_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_diff_decision (
  id INTEGER PRIMARY KEY, diff_id INTEGER NOT NULL REFERENCES stock_diff(id),
  decision TEXT NOT NULL, recover_from TEXT, recover_p INTEGER,
  recovery_state TEXT NOT NULL DEFAULT 'none', note TEXT,
  decided_by TEXT NOT NULL, decided_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_voucher (
  id INTEGER PRIMARY KEY, count_id INTEGER NOT NULL REFERENCES stock_count(id),
  voucher_no TEXT NOT NULL, voucher_date TEXT NOT NULL, note TEXT,
  scan_ref TEXT, recorded_by TEXT NOT NULL, recorded_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sda_diff ON stock_diff_answer(diff_id);
CREATE INDEX IF NOT EXISTS idx_sdd_diff ON stock_diff_decision(diff_id);
"""


def _f_ensure(con):
    con.executescript(FINDING_SCHEMA)


def _f_seal_md5(con, cid):
    """The finding's own fingerprint, over THE QUANTITIES ONLY.

    Deliberately NOT over value_p, and the walk is what settled it. A rate that
    arrives late legitimately fills in a blank value (the owner's D-b), and a
    seal that covered the value would then shout "these rows have changed" at
    every finding that ever waited for a rate -- a warning that fires on
    correct behaviour is a warning nobody reads.

    So the seal covers what a person could be judged by and what must never
    move: the item, what Marg expected, what was actually counted, and the
    difference. A price is an attribute that may be corrected; a count is not.
    """
    import hashlib                                            # noqa: PLC0415
    h = hashlib.md5()
    for r in con.execute(
            "SELECT item, marg_qty, counted_qty, diff "
            "FROM stock_diff WHERE count_id=? ORDER BY item", (cid,)):
        h.update(("%s|%s|%s|%s;" % (r[0], r[1], r[2], r[3])).encode("utf-8"))
    return h.hexdigest()


def _f_seal(con, cid, as_on):
    """Seal a submitted count. Idempotent: a second call never re-seals."""
    _f_ensure(con)
    if con.execute("SELECT 1 FROM stock_finding WHERE count_id=?", (cid,)).fetchone():
        return None
    n = con.execute("SELECT COUNT(*) FROM stock_diff WHERE count_id=?", (cid,)).fetchone()[0]
    no = "SF-%s-%03d" % ((as_on or "")[-4:] or "0000", cid)
    con.execute(
        "INSERT INTO stock_finding (count_id, finding_no, sealed_at, seal_md5, basis, lines_n)"
        " VALUES (?,?,?,?,?,?)",
        (cid, no, now_iso(), _f_seal_md5(con, cid), RECOVERY_BASIS, n))
    return no


def _f_latest(con, table, diff_ids, cols):
    """The newest row per diff_id. Both layers are append-only -- a change of
    mind is a new row, never an overwrite -- so 'latest' is what is shown and
    the earlier ones stay on the record."""
    out = {}
    if not diff_ids:
        return out
    q = ("SELECT %s FROM %s WHERE diff_id IN (%s) ORDER BY id"
         % (", ".join(("diff_id",) + cols), table, ",".join("?" * len(diff_ids))))
    for r in con.execute(q, tuple(diff_ids)):
        out[r[0]] = dict(zip(cols, tuple(r)[1:]))
    return out


def _f_revalue(con):
    """Give a rupee value to every OPEN difference that had none, now that a
    rate exists. Nothing already valued is touched, so a sealed number never
    moves; only a blank becomes a figure. Returns how many filled in."""
    n = 0
    for r in con.execute("SELECT id, item, diff FROM stock_diff "
                         "WHERE value_p IS NULL AND status='open'").fetchall():
        v = _value_p(con, r[1] if not hasattr(r, "keys") else r["item"],
                     r[2] if not hasattr(r, "keys") else r["diff"])
        if v is not None:
            con.execute("UPDATE stock_diff SET value_p=? WHERE id=?",
                        (v, r[0] if not hasattr(r, "keys") else r["id"]))
            n += 1
    return n
# ---- end S221 FINDING helpers ------------------------------------------------

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


def init(app, db_getter, require_fn, unit="medical",
         url_prefix="/finance/stock", marg_token=""):
    """Mount the blueprint. finance_app calls this once, after its own setup.

    WHY THE PREFIX IS /finance/stock AND NOT /stock
        The web server proxies exactly one context to this app -- /finance --
        and nothing else. Mounted at /stock the pages existed inside the app
        and answered 404 from the outside, because the request never reached
        the app at all. Riding the existing /finance context needs no web
        server change, no new config file, and no second thing to notice has
        died. It also keeps the portal's SSO cookie in scope (F-68).

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
def _newest_snapshot(con):
    """(as_on, rows) for the newest snapshot; Marg writes dd-mm-yyyy, and text
    order lies about that (the push_snapshot F-236 lesson), so the date is
    keyed properly here too."""
    def key(a):
        t = (a or "").strip().replace("/", "-").split("-")
        if len(t) == 3:
            try:
                d, m, y = (int(x) for x in t)
                if y > 1900 and 1 <= m <= 12:
                    return (y, m, d)
            except ValueError:
                pass
        return (0, 0, 0)
    dates = [r[0] for r in con.execute(
        "SELECT DISTINCT as_on FROM stock_snapshot").fetchall()]
    if not dates:
        return None, []
    as_on = max(dates, key=key)
    rows = con.execute(
        "SELECT item, qty, packing, pack_size FROM stock_snapshot "
        "WHERE as_on=? ORDER BY item", (as_on,)).fetchall()
    return as_on, rows


def _snapshot_qty_map(con, as_on):
    return {r[0] if not hasattr(r, "keys") else r["item"]:
            int((r[1] if not hasattr(r, "keys") else r["qty"]) or 0)
            for r in con.execute(
                "SELECT item, qty FROM stock_snapshot WHERE as_on=?", (as_on,))}


@bp.route("/page/count")
def page_count():
    """The staff counting screen, served live. S213 · F-245.

    The page is the S207 stock-check page, proven twice at phone width on a
    real dummy run -- with its item universe injected from THIS ledger's
    newest snapshot instead of a file built on another machine, and its
    Share button sending the finished count to /api/count, the endpoint that
    raises differences. The day this page went live, the three empty tables
    stopped needing a machine to fill them.
    """
    # S221 COUNTER VIEWER -- a named counter holds `viewer`, never `maker`:
    # maker is the day's money entry (medical.entry_role).
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    as_on, rows = _newest_snapshot(con)
    if not rows:
        return ("<h3>No stock snapshot on this server yet.</h3>"
                "<p>Load one via /api/snapshot (push_snapshot.py) first.</p>",
                503, {"Content-Type": "text/html; charset=utf-8"})
    items = []
    for r in rows:
        g = (lambda k, i: r[i] if not hasattr(r, "keys") else r[k])
        name, qty = g("item", 0), int(g("qty", 1) or 0)
        packing, ps = g("packing", 2) or "1*1", int(g("pack_size", 3) or 1)
        items.append({"n": name, "p": packing, "s": ps, "u": "",
                      "q": qty, "o": 1 if ps == 1 else 0,
                      "b": []})   # batches are not on this server (Phase B)
    data = {"as_on": as_on, "items": items}
    try:
        with io.open(PAGE_COUNT, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_check_live.html is not beside stock_app.py"), 503
    if t.count("__STOCK_DATA__") != 1:
        return jsonify(ok=False, error="template_bad",
                       message="the template must carry __STOCK_DATA__ exactly once"), 503
    html = t.replace("__STOCK_DATA__", json.dumps(data, separators=(",", ":")))
    return html, 200, {"Content-Type": "text/html; charset=utf-8",
                       "Cache-Control": "no-store"}


@bp.route("/page/diffs")
def page_diffs():
    """The checker's screen: every open difference, and the door it went out
    of. Renders /api/open; each cause button posts /api/diff/<id>/cause."""
    # S221 COUNTER VIEWER -- he may SEE the difference his count produced.
    # Naming its cause is still checker-only. S224 DIFFS ROLE: the page no
    # longer shows him that button -- /api/open tells it who is looking.
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        with io.open(PAGE_DIFFS, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_diffs.html is not beside stock_app.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store"}


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
    # S221 TWO PRICES -- keep EVERY pushed figure, append-only, with its source.
    # stock_snapshot is keyed (as_on,item) and last-write-wins, so Marg's export
    # and the computed expected figure overwrite each other whenever they share
    # an as_on. This log is what makes them comparable instead of destructive.
    _feed_ensure(con)
    _now = now_iso()
    for it in items:
        _n = (it.get("item") or "").strip()
        if _n:
            con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at)"
                        " VALUES (?,?,?,?,?)",
                        (as_on, b.get("source") or "", _n, int(it.get("qty") or 0), _now))
    con.commit()
    # S221 D-b -- "recalculate at export". Items with no rate should be rare;
    # when a rate finally arrives, every open difference that had no value
    # gets one. A value already recorded is never moved by this.
    _f_ensure(con)
    revalued = _f_revalue(con)
    con.commit()
    closed = reconcile(con, as_on)
    return jsonify(ok=True, as_on=as_on, items=n, reconciled=closed,
                   revalued=revalued)


@bp.route("/api/count", methods=["POST"])
def api_count():
    """Submit a completed count. Differences are raised here, once.

    Body: {"marg_as_on":..,"bill_no":..,"bill_date":..,"items_total":376,
           "items":[{"item":..,"marg_qty":..,"counted_qty":..,"strips":..,
                     "loose":..,"pack_size":..,"packing":..,"counted_by":..,
                     "entered_by":..,"at":..,"batches":{...}}]}
    """
    u, err = _require("checker", "maker", "viewer")     # S221 COUNTER VIEWER
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
    # v2 (S213): the client SAYS what Marg expected; this server KNOWS. The
    # snapshot here is the authority -- a stale page, or a doctored one,
    # cannot move a difference by lying about the expected figure. The
    # client's claim is still compared and the mismatches reported back.
    snap = _snapshot_qty_map(con, b["marg_as_on"].strip())
    marg_claim_mismatch = []
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
        claim = int(it.get("marg_qty") or 0)
        marg = snap.get(name, claim)          # the server's figure wins
        if name in snap and claim != marg:
            marg_claim_mismatch.append(name)
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
    # S221 FINDING -- seal it here, in the same transaction that raised the
    # differences. A finding that is sealed later is a finding that could have
    # been edited in between.
    finding_no = _f_seal(con, cid, b["marg_as_on"].strip())
    con.commit()
    return jsonify(ok=True, count_id=cid, items=len(items), differences=raised,
                   finding_no=finding_no,
                   marg_claim_mismatches=marg_claim_mismatch,
                   snapshot_used=(len(snap) > 0))


@bp.route("/api/open")
def api_open():
    # S208: this had no role check at all. Behind finance_app's fail-closed
    # gate it was never public, but "protected by something else" is how a
    # route ends up open the day it is mounted somewhere else. The machine
    # token must reach NOTHING but /api/snapshot, and this is what makes that
    # true in this file rather than in another one.
    u, err = _require("checker", "maker", "viewer")     # S221 COUNTER VIEWER
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
    # S224 DIFFS ROLE -- the page draws only the controls this login may use.
    # `you` is the same shape /api/finding sends; the latest staff answer per
    # line rides along so a maker sees what he recorded. ADDITIVE: every field
    # the S213 page read is still here, unchanged.
    _f_ensure(con)
    _ans = _f_latest(con, "stock_diff_answer", [x["id"] for x in out],
                     ("reason", "note", "answered_by", "answered_at"))
    for x in out:
        _a = _ans.get(x["id"])
        x["answer"] = (dict(_a, label=STAFF_REASONS.get(_a["reason"], _a["reason"]))
                       if _a else None)
        x["cause_label"] = CAUSE_LABEL.get(x["cause"], x["cause"])
    _mc = _may_decide(u)
    return jsonify(ok=True, open=len(out), items=out, causes=list(CAUSES),
                   labels=CAUSE_LABEL, reasons=STAFF_REASONS,
                   you=dict(user=(u or {}).get("user") or "", may_cause=_mc,
                            may_answer=(not _mc) and _has_role(u, "maker")))


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


# ---- S221 FINDING: the document and its layers -------------------------------

@bp.route("/page/finding")
def page_finding():
    """The audit document. One page, three readers: the owner adjudicates, the
    staff answer, and the print button makes the hard copy. Which of those a
    viewer gets is decided by the server on /api/finding, never by the page."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        with io.open(PAGE_FINDING, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_finding.html is not beside stock_app.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store"}


@bp.route("/api/findings")
def api_findings():
    """Every sealed finding, newest first -- the way in to the document."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _f_ensure(con)
    out = []
    for r in con.execute(
            "SELECT f.count_id, f.finding_no, f.sealed_at, f.lines_n, "
            " c.marg_as_on, c.submitted_by, c.items_counted "
            "FROM stock_finding f JOIN stock_count c ON c.id=f.count_id "
            "ORDER BY f.count_id DESC LIMIT 50"):
        out.append(dict(count_id=r[0], finding_no=r[1], sealed_at=r[2],
                        lines=r[3], marg_as_on=r[4], submitted_by=r[5],
                        items_counted=r[6]))
    return jsonify(ok=True, findings=out)


@bp.route("/api/finding/<int:cid>")
def api_finding(cid):
    """THE DOCUMENT, composed here and nowhere else (D349). The owner's screen,
    the staff's phone and the printed sheet all render this one payload, so no
    number can differ between them."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    _f_ensure(con)
    f = con.execute("SELECT finding_no, sealed_at, seal_md5, basis, lines_n "
                    "FROM stock_finding WHERE count_id=?", (cid,)).fetchone()
    if not f:
        return jsonify(ok=False, error="not_found",
                       message="No sealed finding for count %d." % cid), 404
    c = con.execute("SELECT marg_as_on, bill_no, bill_date, started_at, submitted_at,"
                    " submitted_by, items_total, items_counted FROM stock_count "
                    "WHERE id=?", (cid,)).fetchone()
    who_c, who_e = [], []
    for r in con.execute("SELECT DISTINCT counted_by, entered_by FROM stock_count_item "
                         "WHERE count_id=?", (cid,)):
        if r[0] and r[0] not in who_c:
            who_c.append(r[0])
        if r[1] and r[1] not in who_e:
            who_e.append(r[1])

    rows = con.execute(
        "SELECT id, item, marg_qty, counted_qty, diff, pack_size, value_p, cause, "
        " cause_note, status, counted_by FROM stock_diff WHERE count_id=? "
        "ORDER BY (value_p IS NULL), ABS(COALESCE(value_p,0)) DESC, item", (cid,)).fetchall()
    ids = [r[0] for r in rows]
    ans = _f_latest(con, "stock_diff_answer", ids,
                    ("reason", "note", "answered_by", "answered_at"))
    dec = _f_latest(con, "stock_diff_decision", ids,
                    ("decision", "recover_from", "recover_p", "recovery_state",
                     "note", "decided_by", "decided_at"))

    valued, unvalued = [], []
    t = dict(written_off_p=0, to_recover_p=0, explained_p=0, undecided_p=0,
             short_p=0, over_p=0, undecided_lines=0, recover_lines=0,
             writeoff_lines=0, explained_lines=0, settled_p=0)
    for r in rows:
        d = dec.get(r[0])
        a = ans.get(r[0])
        if a:
            a = dict(a, label=STAFF_REASONS.get(a["reason"], a["reason"]))
        # S221 TWO PRICES. value_p has always been the LAST PURCHASE RATE times
        # the difference -- the owner's cost -- and until this kit the document
        # called it MRP. It is now named for what it is, and a real MRP figure
        # sits beside it, from the item's own strip rate.
        _mrp = _mrp_value_p(con, r[1], r[4])
        line = dict(id=r[0], item=r[1], marg_qty=r[2], counted_qty=r[3], diff=r[4],
                    pack_size=r[5], value_p=r[6], cause=r[7],
                    cause_label=CAUSE_LABEL.get(r[7], r[7]), cause_note=r[8],
                    status=r[9], counted_by=r[10], answer=a, decision=d,
                    cost_p=r[6],                 # the purchase-rate value
                    mrp_p=_mrp,                  # the selling-rate value
                    priced_by=("both" if (r[6] is not None and _mrp is not None)
                               else "cost only" if r[6] is not None
                               else "mrp only" if _mrp is not None else "neither"),
                    line_state=("closed" if d else "open"))
        if r[6] is None:
            unvalued.append(line)
            if not d:
                t["undecided_lines"] += 1
            continue
        valued.append(line)
        v = int(r[6])
        if v < 0:
            t["short_p"] += -v
        else:
            t["over_p"] += v
        loss = -v if v < 0 else 0
        if not d:
            t["undecided_p"] += loss
            t["undecided_lines"] += 1
        elif d["decision"] == "WRITE_OFF":
            t["written_off_p"] += loss
            t["writeoff_lines"] += 1
        elif d["decision"] == "RECOVER":
            amt = int(d["recover_p"] or loss)
            if (d["recovery_state"] or "open") == "settled":
                t["settled_p"] += amt
            else:
                t["to_recover_p"] += amt
            t["recover_lines"] += 1
        elif d["decision"] == "EXPLAINED":
            t["explained_p"] += loss
            t["explained_lines"] += 1

    recovery = [dict(item=l["item"], person=(l["decision"] or {}).get("recover_from"),
                     amount_p=int((l["decision"] or {}).get("recover_p") or
                                  (-l["value_p"] if l["value_p"] and l["value_p"] < 0 else 0)),
                     state=(l["decision"] or {}).get("recovery_state") or "open")
                for l in valued
                if l["decision"] and l["decision"]["decision"] == "RECOVER"]
    writeoffs = [dict(item=l["item"], value_p=l["value_p"]) for l in valued
                 if l["decision"] and l["decision"]["decision"] == "WRITE_OFF"]

    vouchers = [dict(voucher_no=r[0], voucher_date=r[1], note=r[2], scan_ref=r[3],
                     recorded_by=r[4], recorded_at=r[5])
                for r in con.execute(
                    "SELECT voucher_no, voucher_date, note, scan_ref, recorded_by,"
                    " recorded_at FROM stock_voucher WHERE count_id=? ORDER BY id", (cid,))]

    # S221 TWO PRICES -- how many lines could be priced at all, and by which
    # route. A total is only honest beside the count of what it could not reach.
    t["priced_both"] = sum(1 for l in valued if l["priced_by"] == "both")
    t["priced_cost_only"] = sum(1 for l in valued if l["priced_by"] == "cost only")
    t["priced_mrp_only"] = sum(1 for l in valued if l["priced_by"] == "mrp only")
    t["priced_none"] = len(unvalued)
    t["mrp_short_p"] = sum(-int(l["mrp_p"]) for l in valued
                           if l["mrp_p"] is not None and l["mrp_p"] < 0)
    live = _f_seal_md5(con, cid)
    return jsonify(
        ok=True,
        you=dict(user=(u or {}).get("user") or "", may_decide=_may_decide(u)),
        finding=dict(no=f[0], count_id=cid, sealed_at=f[1], seal=f[2],
                     seal_ok=(live == f[2]), seal_now=live, basis=f[3],
                     lines_sealed=f[4], marg_as_on=c[0], bill_no=c[1],
                     bill_date=c[2], started_at=c[3], submitted_at=c[4],
                     submitted_by=c[5], items_total=c[6], items_counted=c[7],
                     counted_by=who_c, entered_by=who_e),
        lines=valued, unvalued=unvalued, totals=t,
        recovery=recovery, writeoffs=writeoffs, vouchers=vouchers,
        reasons=STAFF_REASONS, decisions=list(DECISIONS),
        decision_labels=DECISION_LABEL)


def _has_role(u, role):
    """S224 DIFFS ROLE. The live login carries the UNIT roles in `roles`
    (finance_app.require: dict(u, roles=sorted(have))) and the broker's
    clinic-wide role ('doctor', 'staff') in `role`. Look in both, so the owner
    is the checker here exactly when the unit_role table says so."""
    u = u or {}
    return role in (u.get("roles") or ()) or u.get("role") == role


def _may_decide(u):
    """Only the checker rules on a line. The server decides this, not the page."""
    return _has_role(u, "checker") or bool((u or {}).get("is_checker"))


@bp.route("/api/diff/<int:did>/answer", methods=["POST"])
def api_diff_answer(did):
    """The staff layer. Evidence, never state: it cannot change a quantity, a
    value, a cause or a decision, and the row it writes is append-only."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    reason = (b.get("reason") or "").strip()
    if reason not in STAFF_REASONS:
        return jsonify(ok=False, error="bad_reason",
                       message="reason must be one of: %s"
                               % ", ".join(sorted(STAFF_REASONS))), 400
    con = _db()
    _f_ensure(con)
    if not con.execute("SELECT 1 FROM stock_diff WHERE id=?", (did,)).fetchone():
        return jsonify(ok=False, error="not_found"), 404
    con.execute("INSERT INTO stock_diff_answer (diff_id, reason, note, answered_by,"
                " answered_at) VALUES (?,?,?,?,?)",
                (did, reason, (b.get("note") or "").strip() or None,
                 (u or {}).get("user") or "", now_iso()))
    con.commit()
    return jsonify(ok=True)


@bp.route("/api/diff/<int:did>/decision", methods=["POST"])
def api_diff_decision(did):
    """The owner's ruling on one line. Append-only; the latest is shown and
    every earlier one stays on the record.

    LOG ONLY (the owner's ruling D-c). A RECOVER writes a name and an amount
    and NOTHING ELSE HAPPENS -- no staff ledger, no advance, no deduction, not
    here and not by anything this calls. Deterrence is the purpose; the money
    is not taken by software.
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    d = (b.get("decision") or "").strip().upper()
    if d not in DECISIONS:
        return jsonify(ok=False, error="bad_decision",
                       message="decision must be one of: %s" % ", ".join(DECISIONS)), 400
    con = _db()
    _f_ensure(con)
    row = con.execute("SELECT value_p FROM stock_diff WHERE id=?", (did,)).fetchone()
    if not row:
        return jsonify(ok=False, error="not_found"), 404
    val = row[0]
    rec_from, rec_p, state = None, None, "none"
    if d == "RECOVER":
        rec_from = (b.get("recover_from") or "").strip()
        if not rec_from:
            return jsonify(ok=False, error="bad_request",
                           message="A recovery has to name a person."), 400
        # D-a: A RECOVERY IS VALUED AT MRP. Cost is the fallback ONLY when the
        # item has never sold, and the answer says which was used so the figure
        # on a person's name is never a mystery.
        _item = con.execute("SELECT item, diff FROM stock_diff WHERE id=?",
                            (did,)).fetchone()
        _mrpv = _mrp_value_p(con, _item[0], _item[1]) if _item else None
        _basis = "MRP"
        if _mrpv is None:
            _mrpv, _basis = val, ("cost (this item has never sold)"
                                  if val is not None else None)
        if _mrpv is None and b.get("recover_p") in (None, ""):
            return jsonify(ok=False, error="no_value",
                           message="This line has neither a selling price nor a purchase "
                                   "rate, so there is no amount to recover. Set a rate "
                                   "first, or type the amount."), 400
        if b.get("recover_p") not in (None, ""):
            rec_p, _basis = int(b["recover_p"]), "typed in by hand"
        else:
            rec_p = (-int(_mrpv) if _mrpv < 0 else 0)
        state = "settled" if b.get("settled") else "open"
    con.execute(
        "INSERT INTO stock_diff_decision (diff_id, decision, recover_from, recover_p,"
        " recovery_state, note, decided_by, decided_at) VALUES (?,?,?,?,?,?,?,?)",
        (did, d, rec_from, rec_p, state, (b.get("note") or "").strip() or None,
         (u or {}).get("user") or "", now_iso()))
    # D-d: the LINE closes on a decision; a recovery AMOUNT stays open on its own.
    con.execute("UPDATE stock_diff SET status='closed', closed_at=? WHERE id=?",
                (now_iso(), did))
    con.commit()
    return jsonify(ok=True, decision=d, label=DECISION_LABEL[d],
                   recover_p=rec_p, recovery_state=state,
                   basis=(_basis if d == "RECOVER" else None))


@bp.route("/api/rate", methods=["POST"])
def api_rate():
    """Type in a rate for an item Marg's export did not carry (D-b), then
    re-value every open difference that was waiting on one."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    item = (b.get("item") or "").strip()
    try:
        rate_p = int(round(float(b.get("rate_p"))))
    except (TypeError, ValueError):
        rate_p = -1
    if not item or rate_p < 0:
        return jsonify(ok=False, error="bad_request",
                       message="item and a rate in paise are required."), 400
    con = _db()
    ensure_schema(con)
    _f_ensure(con)
    con.execute("INSERT INTO stock_rate (item,rate_p,pack_size,as_of,source) "
                "VALUES (?,?,?,?, 'manual') ON CONFLICT(item) DO UPDATE SET "
                "rate_p=excluded.rate_p, as_of=excluded.as_of, source='manual'",
                (item, rate_p, int(b.get("pack_size") or 1), now_iso()[:10]))
    n = _f_revalue(con)
    con.commit()
    return jsonify(ok=True, item=item, rate_p=rate_p, revalued=n)


@bp.route("/api/voucher", methods=["POST"])
def api_voucher():
    """Record the Marg stock-adjustment voucher for this finding, by number and
    date (S207 R6: a write-off is not finished until Marg agrees). `scan_ref`
    holds wherever the scanned copy was kept -- the scan itself is preserved
    outside this table until Marg's own vouchers can be exported."""
    u, err = _require("checker", "maker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    cid = b.get("count_id")
    no = (b.get("voucher_no") or "").strip()
    date = (b.get("voucher_date") or "").strip()
    if not (cid and no and date):
        return jsonify(ok=False, error="bad_request",
                       message="count_id, voucher_no and voucher_date are required."), 400
    con = _db()
    _f_ensure(con)
    con.execute("INSERT INTO stock_voucher (count_id, voucher_no, voucher_date, note,"
                " scan_ref, recorded_by, recorded_at) VALUES (?,?,?,?,?,?,?)",
                (int(cid), no, date, (b.get("note") or "").strip() or None,
                 (b.get("scan_ref") or "").strip() or None,
                 (u or {}).get("user") or "", now_iso()))
    con.commit()
    return jsonify(ok=True)
# ---- end S221 FINDING --------------------------------------------------------


@bp.route("/page/drift")
def page_drift():
    """Expected vs Marg, run after run. The evidence the spot-count bridge will
    need before it can be armed (the owner, 03-Sep)."""
    u, err = _require("checker", "maker")
    if err:
        return err
    try:
        with io.open(PAGE_DRIFT, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_drift.html is not beside stock_app.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store"}


@bp.route("/api/drift")
def api_drift():
    """For each item and each as-on date that has BOTH feeds: what we computed,
    what Marg says, and the gap.

    A BUG is an item out by the same amount on every run. An EVENT is an item
    that agreed for weeks and then did not. Nothing here decides which; it
    keeps the series so a person can see the difference at a glance -- which a
    printed comparison, thrown away each morning, never could.
    """
    u, err = _require("checker", "maker")
    if err:
        return err
    con = _db()
    _feed_ensure(con)
    rows = con.execute(
        "SELECT as_on, source, item, qty, MAX(received_at) at FROM stock_feed "
        "GROUP BY as_on, source, item ORDER BY as_on").fetchall()
    byday = {}
    for r in rows:
        k = (r[0], r[2])
        byday.setdefault(k, {})[_feed_kind(r[1])] = r[3]
    per = {}
    for (as_on, item), v in byday.items():
        if "expected" not in v or "marg" not in v:
            continue
        d = int(v["expected"]) - int(v["marg"])
        e = per.setdefault(item, dict(item=item, runs=0, deltas=[], days=[]))
        e["runs"] += 1
        e["deltas"].append(d)
        e["days"].append(as_on)
    out = []
    for item, e in per.items():
        ds = e["deltas"]
        nz = [x for x in ds if x != 0]
        same = len(set(nz)) == 1 and len(nz) == len(ds) and len(ds) > 1
        out.append(dict(item=item, runs=e["runs"], last=ds[-1],
                        agreed=len(ds) - len(nz), disagreed=len(nz),
                        verdict=("agrees every run" if not nz else
                                 "SAME gap every run -- look at the arithmetic"
                                 if same else "gap on some runs -- look at the shelf"),
                        cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item),
                        days=e["days"][-8:], deltas=ds[-8:]))
    out.sort(key=lambda x: (-x["disagreed"], -abs(x["last"] or 0)))
    feeds = [dict(as_on=r[0], source=r[1], items=r[2], first=r[3], last=r[4])
             for r in con.execute(
                 "SELECT as_on, source, COUNT(*), MIN(received_at), MAX(received_at) "
                 "FROM stock_feed GROUP BY as_on, source ORDER BY as_on DESC, source"
                 " LIMIT 40")]
    return jsonify(ok=True, items=out, feeds=feeds,
                   purchase=purchase_due(con),
                   comparable=len(out),
                   note=("A day is comparable only when BOTH feeds arrived for it. "
                         "push_expected.py has to be running for this page to fill."))


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
