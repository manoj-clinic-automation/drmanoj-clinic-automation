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

S227 PAD PROOF: every uploaded sheet is KEPT byte for byte in pad_uploads/
beside finance.db (md5-named, read back and verified), and every recorded sheet
has a printable receipt -- GET /api/pad/receipt/<cid>.pdf -- saying exactly what
the server ingested from it. The checker can take the original back
(/api/pad/file/<md5>.xlsx) or the whole folder (/api/pad/archive.zip).

S227 DIFF SHEET: the DIFFERENCES tab of the result workbook is the third fill-in
tab (RECOUNT strips / loose, REASON 1-7, REMARKS); the same table comes down as a
hand-fill PDF (/api/pad/diffs/<root>.pdf) for the counter; a recount joins the
count as a new part, a reason lands on the explanation layer (stock_diff_answer);
and the mismatch is valued at MRP, item-wise and in total (/api/pad/mismatch/<root>).

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
PAGE_NOW = os.path.join(HERE, "stock_now.html")
PAGE_PAD = os.path.join(HERE, "stock_pad.html")
PAGE_REPORT = os.path.join(HERE, "stock_report.html")      # S227 FINDING REPORT
PAGE_DESK = os.path.join(HERE, "stock_desk.html")          # S227 DESK: one card, one question

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


def _sale_key(name):
    """finance_returns.norm_item(), verbatim: the key the sale lines are stored under."""
    s = _re221.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return _re221.sub(r"\s+", " ", s).strip()


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
        # S227: sale_line_item.item_key is finance_returns.norm_item() of the
        # printed name -- upper case, every non-alphanumeric a space -- so
        # 'INTACOXIA-60' is keyed 'INTACOXIA 60' and a raw-name lookup priced
        # nothing with a hyphen, a dot or a quote in it. Both spellings asked.
        rows = con.execute(
            "SELECT amount_p, pack FROM sale_line_item WHERE item_key IN (?, ?) "
            "AND is_return=0 AND amount_p>0 ORDER BY business_date DESC LIMIT 200",
            (item, _sale_key(item))).fetchall()
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


# ---- S227 LANES (kit A): the price ladder, no homework for the owner ----------
# (1) the item's own sale price  (2) the last purchase rate / (1 - margin), PROVISIONAL
# (3) a typed or imported MRP in stock_mrp_manual  (4) nothing.  Every figure says which.
_ORTHO_WORDS = ("BELT", "BINDER", "BRACE", "COLLAR", "CAST", "PAD ", "SPLINT", "SUPPORT", "KNEE", "WRIST",
                "GLOVE", "SYRINGE", "COTTON", "BLADE", "CREPE", "BANDAGE", "TYNOR", "UNISON", "HOSPIK",
                "IMMOBIL", "SLING", "SHOE", "WALKER", "FINGER COT", "DRESS", "GAUZE", "ELBOW", "ANKLE",
                "CERVICAL", "LUMBAR", "STICK", "CRUTCH", "BODY AID", "FLAMINGO", "REMEDE", "LEUKO", "NIPRO")


def _is_ortho(item):
    u = " " + (item or "").upper() + " "
    return any(w in u for w in _ORTHO_WORDS)


def _stock_setting(con, key, default):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r and str(r[0]).strip() != "":
            return float(r[0])
    except Exception:                                         # noqa: BLE001
        pass
    return default


def _stock_settings(con):
    return dict(margin_med=_stock_setting(con, "stock.margin_med", 0.20),
                margin_ortho=_stock_setting(con, "stock.margin_ortho", 0.30),
                allowance_scale=_stock_setting(con, "stock.allowance_scale", 1.0),
                major_p=int(_stock_setting(con, "stock.major_p", 100000)))


def _price_p(con, item, st=None):
    """(paise per unit, source) -- source: 'sale' | 'manual' | 'provisional' | None."""
    st = st or _stock_settings(con)
    p = _mrp_p(con, item)
    if p is not None:
        return p, "sale"
    try:
        r = con.execute("SELECT mrp_p FROM stock_mrp_manual WHERE item=?", (item,)).fetchone()
        if r and r[0]:
            return int(r[0]), "manual"
    except Exception:                                         # noqa: BLE001
        pass
    c = _rate_p(con, item)
    if c:
        m = st["margin_ortho"] if _is_ortho(item) else st["margin_med"]
        return int(round(c / max(0.05, 1.0 - m))), "provisional"
    return None, None


def _price_value_p(con, item, diff, st=None):
    p, src = _price_p(con, item, st)
    return (None if p is None else int(round(p * diff))), src


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



def _feed_latest(con):
    """{(as_on, kind): {"received_at":.., "source":.., "items": {item: qty}}}
    -- THE NEWEST PUSH ONLY, per day and per feed.

    `stock_feed` is append-only and every push writes a whole set of rows, so
    one day can hold three pushes of the same feed. Reading it any other way
    means a re-export changes nothing on the screen -- which is exactly what it
    looked like on the morning of 06-Sep, after LACTOVAX was merged in Marg and
    the merged export was pushed and marked: the page still showed the old gap
    because it had no rule about WHICH of the day's pushes to believe.

    The rule is the owner's own, already written on the wall card: the server
    keeps the NEWER export of a day. An item that the newer push no longer
    carries -- a merged duplicate -- correctly disappears with it.
    """
    _feed_ensure(con)
    best = {}
    for r in con.execute("SELECT as_on, source, MAX(received_at) FROM stock_feed "
                         "GROUP BY as_on, source"):
        k = _feed_kind(r[1])
        if k not in ("marg", "expected"):
            continue
        key = (str(r[0]), k)
        if key not in best or str(r[2]) > best[key]["received_at"]:
            best[key] = dict(received_at=str(r[2]), source=str(r[1]))
    for key, v in best.items():
        v["items"] = {str(x[0]): int(x[1]) for x in con.execute(
            "SELECT item, qty FROM stock_feed WHERE as_on=? AND source=? "
            "AND received_at=?", (key[0], v["source"], v["received_at"]))}
    return best


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
CREATE TABLE IF NOT EXISTS stock_check_readiness (
  count_id    INTEGER PRIMARY KEY REFERENCES stock_count(id),
  captured_at TEXT NOT NULL,
  payload     TEXT NOT NULL
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
    # S226: the finding is sealed WITH ITS DATA HORIZON. A result read a
    # month later must show what the books could see on the day -- how far
    # sales, purchases and the stock export ran, and which credit note was
    # the last processed. Guarded: a readiness that fails must never stop a
    # count from being sealed.
    try:
        con.execute(
            "INSERT OR REPLACE INTO stock_check_readiness "
            "(count_id, captured_at, payload) VALUES (?,?,?)",
            (cid, now_iso(), json.dumps(readiness(con), ensure_ascii=False)))
    except Exception:
        pass
    return no



def _f_readiness(con, cid):
    """The data horizon frozen with this finding, or the live one labelled as
    live when the finding predates S226. Never raises."""
    try:
        r = con.execute("SELECT captured_at, payload FROM stock_check_readiness "
                        "WHERE count_id=?", (cid,)).fetchone()
        if r:
            d = json.loads(r[1])
            d["captured_at"] = r[0]
            d["frozen"] = True
            return d
    except Exception:
        pass
    try:
        d = readiness(con)
        d["frozen"] = False
        d["note"] = ("This finding was sealed before the readiness header "
                     "existed, so these lines are today's, not the day's.")
        return d
    except Exception:
        return None


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
    data = {"as_on": as_on, "items": items,
            "checker": bool(_may_decide(u)), "user": (u or {}).get("user") or ""}
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

    out = _record_count(b, u)
    return jsonify(**out)


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
        decision_labels=DECISION_LABEL, readiness=_f_readiness(con, cid))


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
    latest = _feed_latest(con)
    byday = {}
    for (as_on, kind), v in latest.items():
        for item, qty in v["items"].items():
            byday.setdefault((as_on, item), {})[kind] = qty
    per = {}
    for (as_on, item) in sorted(byday):
        v = byday[(as_on, item)]
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
        if not nz:
            verdict = "agrees every day"
        elif len(ds) == 1:
            # ONE day is not a series. Calling it the shelf on day one is
            # the overclaim the whole page exists to avoid.
            verdict = "first day compared -- too early to say which"
        elif same:
            verdict = "SAME gap every day -- look at the arithmetic"
        else:
            verdict = "gap on some days -- look at the shelf"
        out.append(dict(item=item, runs=e["runs"], last=ds[-1],
                        agreed=len(ds) - len(nz), disagreed=len(nz),
                        verdict=verdict,
                        cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item),
                        days=e["days"][-8:], deltas=ds[-8:]))
    out.sort(key=lambda x: (-x["disagreed"], -abs(x["last"] or 0)))
    feeds = [dict(as_on=r[0], source=r[1], items=r[2], first=r[3], last=r[4])
             for r in con.execute(
                 "SELECT as_on, source, COUNT(*), MIN(received_at), MAX(received_at) "
                 "FROM stock_feed GROUP BY as_on, source ORDER BY as_on DESC, source"
                 " LIMIT 40")]
    rdy = _readiness_safe(con)
    return jsonify(ok=True, items=out, feeds=feeds, readiness=rdy,
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


# ---- S226 READINESS: read first, know the data ------------------------------
# The owner, 06-Sep-2026: the drift page and the count page must OPEN with
# data-readiness lines, before any result -- "Read first, know the data."
#
# Nothing in this section computes stock, decides anything, or writes to a
# live table. It reports the HORIZON of each feed: how far the books can see.
# A difference read without that horizon is unreadable -- 13 items sat below
# zero on 05-Sep not because the shelf was empty but because purchases were
# known only to 03-Sep, and the page did not say so where a reader would look.
#
# EVERY block is guarded on its own. A readiness header that can take a page
# down is worse than no header at all (S209, four hours).

def _r_rupees(paise):
    """Paise -> 'Rs 3,54,879.00'. Indian grouping, the way every report the
    owner reads prints a figure."""
    try:
        n = int(paise or 0)
    except Exception:
        return "Rs 0.00"
    sign = "-" if n < 0 else ""
    n = abs(n)
    whole, p = divmod(n, 100)
    s = str(whole)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts + [tail])
    return "%sRs %s.%02d" % (sign, s, p)


def _r_dmy(iso):
    """yyyy-mm-dd -> dd-mm-yyyy, the way Marg prints a date. Anything that is
    not a plain ISO date is handed back untouched rather than mangled."""
    s = str(iso or "").strip()[:10]
    if _re221.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4])
    return str(iso or "")


def _r_stamp(ts):
    """An ISO timestamp -> 'dd-mm-yyyy HH:MM'."""
    s = str(ts or "").strip()
    if len(s) >= 16 and s[10] in ("T", " "):
        return "%s %s" % (_r_dmy(s[:10]), s[11:16])
    return _r_dmy(s)


def _r_days(a, b):
    """Whole days from a to b, or None when either is not a date."""
    try:
        return (dt.date.fromisoformat(str(b)[:10])
                - dt.date.fromisoformat(str(a)[:10])).days
    except Exception:
        return None


def _r_billkey(b):
    """Order bill numbers by their trailing digits, not as text. A003396 and
    A0003396 both sort by 3396; anything without digits sorts first."""
    s = str(b or "")
    m = _re221.search(r"(\d+)\s*$", s)
    return (int(m.group(1)) if m else -1, s)


def _r_sale(con):
    """The sale report's horizon: the last business day the server holds, the
    LAST BILL NUMBER of that day, and how many bills that day carries."""
    out = dict(ok=False, business_date=None, bill_no=None, bills=None,
               days_behind=None, line="Sale report: nothing has reached the server yet.")
    try:
        r = con.execute("SELECT MAX(business_date) FROM sale_line_item "
                        "WHERE unit=? AND is_return=0", (_unit,)).fetchone()
        d = (r[0] if r else None) or None
        if not d:
            return out
        bills = [str(x[0]) for x in con.execute(
            "SELECT DISTINCT bill_no FROM sale_line_item WHERE unit=? AND "
            "is_return=0 AND business_date=?", (_unit, d)).fetchall() if x[0]]
        out["business_date"] = str(d)[:10]
        out["bills"] = len(bills)
        out["bill_no"] = max(bills, key=_r_billkey) if bills else None
        out["days_behind"] = _r_days(out["business_date"], now_iso()[:10])
        out["ok"] = True
        out["line"] = ("Sale report: current to %s, last bill %s (%d bill%s that day)."
                       % (_r_dmy(out["business_date"]), out["bill_no"] or "-",
                          out["bills"], "" if out["bills"] == 1 else "s"))
    except Exception:
        out["line"] = ("Sale report: the server could not be read for this. "
                       "That is not the same as no sale report -- it is unknown.")
    return out


def _r_returns(con):
    """The last credit note processed, and the sentence the owner wants on
    every logged result."""
    out = dict(ok=False, bill_no=None, business_date=None,
               sentence="No sale return has been processed on the server yet.")
    try:
        r = con.execute("SELECT MAX(business_date) FROM sale_line_item "
                        "WHERE unit=? AND is_return=1", (_unit,)).fetchone()
        d = (r[0] if r else None) or None
        if not d:
            return out
        cns = [str(x[0]) for x in con.execute(
            "SELECT DISTINCT bill_no FROM sale_line_item WHERE unit=? AND "
            "is_return=1 AND business_date=?", (_unit, d)).fetchall() if x[0]]
        out["business_date"] = str(d)[:10]
        out["bill_no"] = max(cns, key=_r_billkey) if cns else None
        out["ok"] = True
        out["sentence"] = ("All sale returns up to credit-note %s dated %s have "
                           "been processed." % (out["bill_no"] or "-",
                                                _r_dmy(out["business_date"])))
    except Exception:
        out["sentence"] = ("The sale returns could not be read from the server, "
                           "so how far they are processed is unknown.")
    return out


def _r_purchase(con):
    """Purchases: how far they are known, and THE LAST DAY'S BILLS listed the
    way the Bill-wise purchase report shows them -- supplier, bill number,
    date, amount. The owner's words, 06-Sep."""
    out = dict(ok=False, bill_date=None, bills=[], bills_n=0, amount_p=0,
               known_to_feed=None, exports=[], days_behind=None,
               line="Purchases: nothing has reached the server yet.")
    try:
        out["known_to_feed"] = _purchases_known_to(con)
    except Exception:
        pass
    try:
        r = con.execute("SELECT MAX(bill_date) FROM purchase_bill "
                        "WHERE bill_date IS NOT NULL AND bill_date<>''").fetchone()
        d = (r[0] if r else None) or None
        if d:
            out["bill_date"] = str(d)[:10]
            for b in con.execute(
                    "SELECT supplier, bill_no, bill_date, amount_p, cash_p, credit_p "
                    "FROM purchase_bill WHERE bill_date=? ORDER BY supplier, bill_no",
                    (out["bill_date"],)):
                out["bills"].append(dict(
                    supplier=b[0], bill_no=b[1], bill_date=str(b[2] or "")[:10],
                    amount_p=int(b[3] or 0), cash_p=int(b[4] or 0),
                    credit_p=int(b[5] or 0)))
            out["bills_n"] = len(out["bills"])
            out["amount_p"] = sum(x["amount_p"] for x in out["bills"])
            out["days_behind"] = _r_days(out["bill_date"], now_iso()[:10])
            out["ok"] = True
            out["line"] = ("Purchases: current to %s -- %d bill%s that day, %s."
                           % (_r_dmy(out["bill_date"]), out["bills_n"],
                              "" if out["bills_n"] == 1 else "s",
                              _r_rupees(out["amount_p"])))
    except Exception:
        out["line"] = ("Purchases: the purchase books could not be read from the "
                       "server, so how far they are known is unknown.")
    try:
        for e in con.execute(
                "SELECT type, period_from, period_to, export_stamp, received_at, "
                "n_rows FROM purchase_export WHERE superseded_by IS NULL "
                "ORDER BY received_at DESC LIMIT 6"):
            out["exports"].append(dict(
                type=e[0], period_from=str(e[1] or "")[:10],
                period_to=str(e[2] or "")[:10], export_stamp=e[3],
                received_at=e[4], n_rows=int(e[5] or 0)))
    except Exception:
        pass
    return out


def _r_stock(con):
    """Marg's closing-stock export and our computed figure: the as-on date of
    each, when this server processed it, and how many items it carried."""
    out = dict(ok=False, marg=None, expected=None,
               line="Stock export: nothing has reached the server yet.")
    try:
        # S226b: COUNT(*) here was a ROW count, and every push appends a
        # whole set -- so three pushes of a 373-item day read as 1,119
        # items. The owner saw 746 and 1,492 on the first live screen.
        newest = {}
        for (as_on, kind), v in _feed_latest(con).items():
            cur = newest.get(kind)
            if cur is None or (as_on, v["received_at"]) > (cur["as_on"],
                                                           cur["processed_at"]):
                newest[kind] = dict(as_on=as_on, source=v["source"],
                                    items=len(v["items"]),
                                    processed_at=v["received_at"])
        out["marg"] = newest.get("marg")
        out["expected"] = newest.get("expected")
        out["ok"] = bool(out["marg"] or out["expected"])
        parts = []
        if out["marg"]:
            parts.append("Marg's closing stock: as on %s, processed here %s (%d items)."
                         % (_r_dmy(out["marg"]["as_on"]),
                            _r_stamp(out["marg"]["processed_at"]),
                            out["marg"]["items"]))
        else:
            parts.append("Marg's closing stock: never received.")
        if out["expected"]:
            parts.append("Our computed figure: as on %s, processed %s (%d items)."
                         % (_r_dmy(out["expected"]["as_on"]),
                            _r_stamp(out["expected"]["processed_at"]),
                            out["expected"]["items"]))
        else:
            parts.append("Our computed figure: never received.")
        out["line"] = " ".join(parts)
    except Exception:
        out["line"] = ("Stock export: the feed table could not be read, so the "
                       "export's date and time are unknown.")
    return out


def readiness(con):
    """The four data-readiness blocks, and the plain lines that print them.

    Returned by /api/readiness, carried on /api/drift so the page needs one
    round trip, and frozen into the record beside every sealed finding."""
    sale = _r_sale(con)
    pur = _r_purchase(con)
    stk = _r_stock(con)
    ret = _r_returns(con)
    lines = [sale["line"], pur["line"], stk["line"], ret["sentence"]]
    warn = []
    if sale.get("days_behind") is not None and sale["days_behind"] > 1:
        warn.append("The sale report is %d days behind today." % sale["days_behind"])
    if pur.get("days_behind") is not None and pur["days_behind"] > 1:
        warn.append("Purchases are %d days behind today -- anything entered into "
                    "Marg after %s is not in any figure on this page."
                    % (pur["days_behind"], _r_dmy(pur["bill_date"])))
    if stk.get("marg") and pur.get("bill_date") and \
            stk["marg"]["as_on"] > pur["bill_date"]:
        warn.append("The stock figure is for %s but purchases are known only to "
                    "%s. Count after the purchase export, not before it."
                    % (_r_dmy(stk["marg"]["as_on"]), _r_dmy(pur["bill_date"])))
    return dict(ok=True, headline="Read first -- know the data.",
                as_of=now_iso(), today=now_iso()[:10],
                sale=sale, purchase=pur, stock=stk, returns=ret,
                lines=lines, warnings=warn)


@bp.route("/api/readiness")
def api_readiness():
    """The header's own endpoint, so the count page can ask for it alone."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        return jsonify(readiness(_db()))
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, error="readiness_failed", message=str(e)), 200
# ---- end S226 READINESS -----------------------------------------------------


# ---- S226b STOCK NOW: "where do I see the latest stock in our system" -------
# The owner's question, 06-Sep, on the first live look at the readiness header.
# Until now the only stock a person could open was the COUNTING screen, which
# shows Marg's newest snapshot because that is what a counter needs. There was
# no page that simply said: this is the stock, as this system computes it, as
# on the last day it could compute.

@bp.route("/page/now")
def page_now():
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        with io.open(PAGE_NOW, "r", encoding="utf-8") as fh:
            t = fh.read()
    except OSError:
        return jsonify(ok=False, error="template_missing",
                       message="stock_now.html is not beside stock_app.py"), 503
    return t, 200, {"Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store"}


@bp.route("/api/now")
def api_now():
    """The stock as this system holds it, for the newest day it has.

    Ours and Marg's side by side, because a figure with nothing to check it
    against is a figure nobody should act on. Below-zero lines are called what
    they are: not an empty shelf, but a purchase bill that has not been
    entered yet."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    latest = _feed_latest(con)
    days = sorted({d for (d, k) in latest})
    if not days:
        return jsonify(ok=True, as_on=None, rows=[], totals={},
                       readiness=_readiness_safe(con),
                       note="No stock figure has reached this server yet.")
    as_on = days[-1]
    ours = (latest.get((as_on, "expected")) or {}).get("items", {})
    marg = (latest.get((as_on, "marg")) or {}).get("items", {})
    rows = []
    for item in sorted(set(ours) | set(marg)):
        o = ours.get(item)
        m = marg.get(item)
        gap = (o - m) if (o is not None and m is not None) else None
        rows.append(dict(item=item, ours=o, marg=m, gap=gap,
                         cost_p=_rate_p(con, item), mrp_p=_mrp_p(con, item)))
    both = [r for r in rows if r["gap"] is not None]
    totals = dict(
        items=len(rows), compared=len(both),
        agree=sum(1 for r in both if r["gap"] == 0),
        differ=sum(1 for r in both if r["gap"] != 0),
        below_zero=sum(1 for r in rows
                       if (r["ours"] is not None and r["ours"] < 0)
                       or (r["marg"] is not None and r["marg"] < 0)),
        ours_only=sum(1 for r in rows if r["marg"] is None),
        marg_only=sum(1 for r in rows if r["ours"] is None))
    rows.sort(key=lambda r: (r["gap"] is None, -abs(r["gap"] or 0), r["item"]))
    return jsonify(ok=True, as_on=as_on, rows=rows, totals=totals,
                   ours_at=(latest.get((as_on, "expected")) or {}).get("received_at"),
                   marg_at=(latest.get((as_on, "marg")) or {}).get("received_at"),
                   readiness=_readiness_safe(con))


def _readiness_safe(con):
    try:
        return readiness(con)
    except Exception:
        return None
# ---- end S226b STOCK NOW -----------------------------------------------------


def _record_count(b, u):
    """The one place a count becomes a row, a set of differences and a
    sealed finding. Extracted at S226 so the spreadsheet import and the
    counting page cannot drift apart: two ways in, one way through.
    """
    # `items` was a local of api_count, defined above the block that moved in
    # here. The extraction left it behind and only the COMMIT path touched it,
    # so the preview worked perfectly and recording threw. Caught by driving it.
    items = b.get("items") or []
    if not items:
        return dict(ok=False, error="bad_request", message="No counted items.")
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
    return dict(ok=True, count_id=cid, items=len(items), differences=raised,
                   finding_no=finding_no,
                   marg_claim_mismatches=marg_claim_mismatch,
                   snapshot_used=(len(snap) > 0))


# ---- S226 PAD IMPORT: the counted sheet becomes the count --------------------
# The owner, 06-Sep-2026, after a morning in which the counters moved to a
# spreadsheet: "entering then will be a breeze and not more than a few minutes
# job."
#
# Transcribing 373 items into a screen, one card at a time, is not a few
# minutes however fast the screen is. So the sheet they filled IS the entry.
#
# THE RULE THIS IS BUILT TO: a counted figure is never silently dropped. Every
# row the server cannot place -- a name it does not know, a negative, half a
# tablet -- is KEPT against the count and handed back on the result sheet, with
# its row number, for a person to fix. A count that quietly loses eleven lines
# is worse than one that asks again.
#
# S226 ON-PAGE (the owner, the same afternoon): the flow lives on the
# stock-check page. Details first -> the pad comes down PREFILLED -> the filled
# pad is uploaded in ONE step (/api/pad/upload reads, records and answers) ->
# the result sheet is offered -> the loop goes on until nothing is left. The
# bytes of every sheet are remembered with the count they made, so the same
# file twice is the same count, never a second one.

def _pad_raw(fs):
    """(raw bytes, md5, size) of the upload, before anything is read from it.
    Raises ValueError with a sentence a person can act on.

    S227: split out of _pad_read so the BYTES are in hand whatever the reader
    makes of them -- an unreadable upload is kept too, because 'the file I sent
    was fine' is exactly the dispute the archive exists to settle."""
    import hashlib                                            # noqa: PLC0415
    raw = fs.read()
    if not raw:
        raise ValueError("that file is empty.")
    if len(raw) > 8 * 1024 * 1024:
        raise ValueError("that file is larger than 8 MB -- it is not the count pad.")
    return raw, hashlib.md5(raw).hexdigest(), len(raw)


def _pad_parse(raw):
    """The bytes -> the reader's dict. Raises ValueError when the reader is missing."""
    try:
        import padreader                                      # noqa: PLC0415
    except ImportError:
        raise ValueError("the pad reader is not installed beside stock_app.py "
                         "(padreader.py). Nothing was read.")
    return padreader.read_pad(io.BytesIO(raw))


def _pad_read(fs):
    """(parsed, md5, bytes). Kept for the preview/commit pair; the upload
    route takes the two halves so it can keep the bytes first."""
    raw, md5, n = _pad_raw(fs)
    return _pad_parse(raw), md5, n


def _pad_norm(s):
    """The one match key, kept identical to packmap.norm (S206) and
    marg_purchase_rows.norm (S224): case, inner spacing and TRAILING DOTS --
    never content. The trailing dot matters: Marg held LACTOVAX SYP 200ML and
    LACTOVAX SYP 200ML. as two item masters for one product, and that dot cost
    the owner a morning on 06-Sep."""
    import re as _re                                          # noqa: PLC0415
    t = _re.sub(r"\s+", " ", (s or "").upper()).strip()
    return _re.sub(r"[.\s]+$", "", t)


def _pad_match(con, parsed):
    """Line the sheet up against the shop's own newest stock list."""
    as_on, snap_rows = _newest_snapshot(con)
    snap, packs = {}, {}
    for r in snap_rows:
        g = (lambda k, i: r[i] if not hasattr(r, "keys") else r[k])
        snap[g("item", 0)] = int(g("qty", 1) or 0)
        packs[g("item", 0)] = int(g("pack_size", 3) or 1)
    key = {}
    for nm in snap:
        key[_pad_norm(nm)] = nm

    matched, unmatched, blank, counted_names = [], [], [], set()
    for row in parsed["rows"]:
        real = key.get(_pad_norm(row["item"]))
        wrote = (row.get("strips") is not None or row.get("loose") is not None
                 or row["counted"] is not None)
        if real is None:
            if wrote:
                unmatched.append(dict(row=row["row"], item=row["item"],
                                      counted=row["counted"] if row["counted"] is not None
                                      else "%s strips %s loose" % (row.get("strips") or 0,
                                                                   row.get("loose") or 0)))
            continue
        # The result workbook's fill-in tabs carry no PACK SIZE column (the
        # owner's approved layout), so the reader hands strips and loose on and
        # the total is settled HERE from the shop's own pack size.
        if row["counted"] is None and (row.get("strips") is not None or row.get("loose") is not None):
            row["counted"] = (row.get("strips") or 0) * packs.get(real, 1) + (row.get("loose") or 0)
        if row["counted"] is None:
            # S227: a DIFFERENCES-tab row with no recount is NOT an uncounted
            # item -- it was counted already; the tab asks only for a recount
            # or a reason. A blank there means "no change".
            if row.get("kind") != "diff":
                blank.append(dict(row=row["row"], item=real, marg=snap[real]))
            continue
        counted_names.add(real)
        matched.append(dict(row=row["row"], item=real, marg=snap[real], ref=row.get("ref"),
                            counted=row["counted"], diff=row["counted"] - snap[real],
                            strips=row["strips"], loose=row["loose"],
                            pack_size=packs.get(real, 1), how=row["how"],
                            remarks=row["remarks"],
                            value_p=_value_p(con, real, row["counted"] - snap[real]),
                            mrp_p=_mrp_p(con, real)))
    missing = [dict(item=nm, marg=snap[nm]) for nm in sorted(snap)
               if nm not in counted_names
               and not any(b["item"] == nm for b in blank)]
    return as_on, snap, matched, unmatched, blank, missing


def _pad_summary(con, parsed, md5, nbytes):
    as_on, snap, matched, unmatched, blank, missing = _pad_match(con, parsed)
    problems = [dict(row=pr[0], item=pr[1], why=pr[2], sheet=(pr[3] if len(pr) > 3 else ""))
                for pr in parsed["problems"]]
    differ = [m for m in matched if m["diff"] != 0]
    differ.sort(key=lambda m: (-abs(m["value_p"] or 0), -abs(m["diff"])))
    # THE OWNER'S RULE, 06-Sep: "accept the staff-filled excel and not reject
    # it -- rather give a follow-up excel then and there." So nothing here
    # blocks. What can be used is recorded; what cannot -- a name the shop does
    # not know, a negative, half a tablet -- goes into a follow-up sheet handed
    # straight back, together with every item nobody reached. The only thing
    # that stops a recording is a sheet with NOTHING usable in it.
    to_fix = len(problems) + len(unmatched)
    blocked = not matched
    return dict(
        ok=True, as_on=as_on, md5=md5, bytes=nbytes,
        part_of=parsed.get("part_of"),
        rows_in_sheet=len(parsed["rows"]),
        items_in_shop=len(snap),
        counted=len(matched), agreed=len(matched) - len(differ), differed=len(differ),
        not_counted=len(blank) + len(missing),
        differences=differ[:400],
        not_counted_list=([b["item"] for b in blank] + [m["item"] for m in missing])[:400],
        unmatched=unmatched, problems=problems, to_fix=to_fix,
        short_p=sum(-(m["value_p"] or 0) for m in differ if (m["value_p"] or 0) < 0),
        over_p=sum((m["value_p"] or 0) for m in differ if (m["value_p"] or 0) > 0),
        unpriced=sum(1 for m in differ if m["value_p"] is None),
        blocked=blocked,
        blocked_why=("Not one figure in this sheet could be used, so there is "
                     "nothing to record." if blocked else None),
        followup_why=(("%d row(s) could not be used as written and %d item(s) were "
                       "not counted. They will be on a follow-up sheet, handed back "
                       "the moment this is recorded." % (to_fix, len(blank) + len(missing)))
                      if (to_fix or blank or missing) else None))



PAD_SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_count_pad_issue (
  id        INTEGER PRIMARY KEY,
  count_id  INTEGER NOT NULL REFERENCES stock_count(id),
  sheet_row INTEGER,
  written   TEXT NOT NULL,
  figure    INTEGER,
  why       TEXT NOT NULL,
  resolved_by INTEGER
);
CREATE TABLE IF NOT EXISTS stock_count_part (
  count_id    INTEGER PRIMARY KEY REFERENCES stock_count(id),
  part_of     INTEGER NOT NULL REFERENCES stock_count(id),
  recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS stock_count_pad_file (
  md5         TEXT PRIMARY KEY,
  count_id    INTEGER NOT NULL REFERENCES stock_count(id),
  filename    TEXT,
  bytes       INTEGER,
  uploaded_at TEXT NOT NULL,
  uploaded_by TEXT
);
CREATE TABLE IF NOT EXISTS stock_count_close (
  count_id  INTEGER PRIMARY KEY REFERENCES stock_count(id),
  closed_at TEXT NOT NULL,
  closed_by TEXT,
  how       TEXT NOT NULL,          -- 'complete' (server verified nothing left) | 'incomplete' (the checker closed it as it stood)
  left_not_counted INTEGER,
  left_to_fix      INTEGER
);
CREATE INDEX IF NOT EXISTS idx_pad_issue_count ON stock_count_pad_issue(count_id);
CREATE TABLE IF NOT EXISTS stock_count_pad_archive (
  md5         TEXT PRIMARY KEY,          -- the file's fingerprint; also its name in pad_uploads/
  path        TEXT NOT NULL,             -- where the bytes are kept, relative to the archive folder
  filename    TEXT,                      -- as the phone named it
  bytes       INTEGER NOT NULL,
  first_seen  TEXT NOT NULL,
  seen_by     TEXT,
  last_seen   TEXT NOT NULL,
  times       INTEGER NOT NULL DEFAULT 1,
  outcome     TEXT NOT NULL,             -- recorded | repeat | held-need_details | refused-<why>
  count_id    INTEGER,                   -- the count it made, once it made one
  verified    INTEGER NOT NULL DEFAULT 0 -- 1 = read back from disk, md5 matched
);
CREATE TABLE IF NOT EXISTS stock_mrp_manual (
  item    TEXT PRIMARY KEY,               -- S227 LANES: a typed or imported MRP, per unit, paise
  mrp_p   INTEGER NOT NULL,
  source  TEXT,
  set_by  TEXT,
  set_at  TEXT
);
CREATE TABLE IF NOT EXISTS stock_diff_lane (
  id        INTEGER PRIMARY KEY,          -- S227 LANES: the owner's word on a line, append-only
  count_id  INTEGER NOT NULL,             -- the ROOT count
  item      TEXT NOT NULL,
  action    TEXT NOT NULL,                -- WRITE_OFF | RECOVER | EXPLAINED | RECOUNT | PARKED | VERIFY_BILL | MARG_FIX | OPEN
  note      TEXT,
  by_user   TEXT,
  at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_diff_lane ON stock_diff_lane(count_id, item);
"""


def _pad_ensure(con):
    con.executescript(PAD_SCHEMA)


def _xlsx_response(data, filename):
    from flask import Response                                # noqa: PLC0415
    return Response(data, status=200, headers={
        "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "Content-Disposition": 'attachment; filename="%s"' % filename,
        "Cache-Control": "no-store"})


def _pad_iso_date(s):
    try:
        import padreader                                      # noqa: PLC0415
        return padreader.iso_date(s)
    except Exception:                                         # noqa: BLE001
        return (s or "").strip()


@bp.route("/pad.xlsx")
def pad_fresh():
    """A blank pad for the shop as it stands today. NO figure from Marg in it.

    S226 ON-PAGE: the four details come as query parameters from the
    stock-check page (cby, eby, bill, bdate) and are WRITTEN INTO the pad's
    top lines, so the sheet that comes back carries its own anchor and the
    person uploading it types nothing."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        import padwriter                                      # noqa: PLC0415
    except ImportError:
        return jsonify(ok=False, error="missing",
                       message="padwriter.py is not beside stock_app.py"), 503
    con = _db()
    ensure_schema(con)
    as_on, rows = _newest_snapshot(con)
    if not rows:
        return jsonify(ok=False, error="no_snapshot",
                       message="No stock list on this server yet."), 503
    items = []
    for r in rows:
        g = (lambda k, i: r[i] if not hasattr(r, "keys") else r[k])
        items.append((g("item", 0), g("packing", 2) or "", int(g("pack_size", 3) or 1)))
    items.sort(key=lambda t: t[0].upper())
    a = request.args
    meta = dict(counted_by=(a.get("cby") or "").strip()[:60],
                entered_by=(a.get("eby") or "").strip()[:60],
                bill_no=(a.get("bill") or "").strip().upper()[:30],
                bill_date=_pad_iso_date(a.get("bdate") or ""))
    today = dt.date.today().strftime("%d-%m-%Y")
    return _xlsx_response(padwriter.fresh_pad(items, as_on, today, meta=meta),
                          "STOCK_COUNT_%s_SHEET_1.xlsx" % today)


def _pad_family(con, cid):
    """(root_id, family ids, R) -- everything the result workbook needs, read
    for the count AND every part recorded against it. One reader, used by the
    workbook, by the upload's reply and by the recent-counts list, so the three
    can never disagree about what is left to do."""
    _pad_ensure(con)
    _f_ensure(con)
    c = con.execute("SELECT marg_as_on, bill_no, bill_date, submitted_at, submitted_by, "
                    "items_total FROM stock_count WHERE id=?", (cid,)).fetchone()
    if not c:
        return None, [], None
    root = con.execute("SELECT part_of FROM stock_count_part WHERE count_id=?", (cid,)).fetchone()
    root_id = int(root[0]) if root else cid
    if root_id != cid:
        c = con.execute("SELECT marg_as_on, bill_no, bill_date, submitted_at, submitted_by, "
                        "items_total FROM stock_count WHERE id=?", (root_id,)).fetchone() or c
    fam = [root_id] + [r[0] for r in con.execute(
        "SELECT count_id FROM stock_count_part WHERE part_of=? ORDER BY count_id", (root_id,))]
    q = ",".join("?" * len(fam))
    as_on = c[0]
    packs, packing = {}, {}
    for r in con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE as_on=?", (as_on,)):
        packs[r[0]] = int(r[2] or 1); packing[r[0]] = r[1] or ""

    items = {}
    for r in con.execute("SELECT item, marg_qty, counted_qty FROM stock_count_item "
                         "WHERE count_id IN (%s) ORDER BY count_id" % q, tuple(fam)):
        items[r[0]] = (int(r[1] or 0), int(r[2] or 0))      # the latest part wins
    diffs, matched = [], []
    for item, (m, cnt) in items.items():
        if cnt != m:
            # S227: (item, packing, pack, marg, counted, value at COST, value at MRP)
            pv, psrc = _price_value_p(con, item, cnt - m)
            diffs.append((item, packing.get(item, ""), packs.get(item, 1), m, cnt,
                          _value_p(con, item, cnt - m), pv, psrc))
        else:
            matched.append((item, packing.get(item, ""), packs.get(item, 1), m))
    matched.sort(key=lambda t: t[0].upper())
    mm = _pad_mismatch_totals(diffs)
    explained = 0
    try:
        ids = [r[0] for r in con.execute("SELECT id FROM stock_diff WHERE count_id IN (%s)" % q, tuple(fam))]
        if ids:
            explained = con.execute(
                "SELECT COUNT(DISTINCT diff_id) FROM stock_diff_answer WHERE diff_id IN (%s)"
                % ",".join("?" * len(ids)), tuple(ids)).fetchone()[0]
    except Exception:
        explained = 0
    fixes = [(r[0], r[1], r[2], r[3]) for r in con.execute(
        "SELECT sheet_row, written, figure, why FROM stock_count_pad_issue "
        "WHERE count_id IN (%s) AND resolved_by IS NULL ORDER BY count_id, sheet_row"
        % q, tuple(fam))]
    # a fix that has since been resolved (its corrected name was counted in a later
    # part) must not be asked for again
    fixes = [f for f in fixes if _pad_norm(f[1]) not in {_pad_norm(k) for k in items}]
    uncounted = [(it, packing[it], packs[it]) for it in sorted(packs, key=str.upper) if it not in items]
    who_c, who_e = [], []
    for r in con.execute("SELECT DISTINCT counted_by, entered_by FROM stock_count_item "
                         "WHERE count_id IN (%s)" % q, tuple(fam)):
        if r[0] and r[0] not in who_c: who_c.append(r[0])
        if r[1] and r[1] not in who_e: who_e.append(r[1])
    f = con.execute("SELECT finding_no FROM stock_finding WHERE count_id=?", (root_id,)).fetchone()
    cl = con.execute("SELECT closed_at, closed_by, how, left_not_counted, left_to_fix "
                     "FROM stock_count_close WHERE count_id=?", (root_id,)).fetchone()
    lines = ["", "", "", ""]; as_on_note = ""
    try:
        rr = con.execute("SELECT payload FROM stock_check_readiness WHERE count_id=?", (root_id,)).fetchone()
        if rr:
            pay = json.loads(rr[0]); lines = (pay.get("lines") or lines)[:4]
            mg = (pay.get("stock") or {}).get("marg") or {}
            if mg.get("processed_at"):
                as_on_note = "processed here " + _r_stamp(mg["processed_at"])
    except Exception:
        pass
    R = dict(count_id=cid, part_of=(root_id if root_id != cid else None),
             finding_no=(f[0] if f else ""),
             when=_r_stamp(c[3]) + " IST", when_iso=c[3],
             counted_by=", ".join(who_c) or "",
             entered_by=", ".join(who_e) or "", recorded_by=c[4] or "",
             as_on=as_on, as_on_note=as_on_note,
             bill="%s dated %s" % (c[1], c[2]), bill_no=c[1], bill_date=c[2],
             readiness_lines=lines,
             items_in_shop=len(packs), counted=len(items), agreed=len(matched),
             differed=len(diffs), sent_back=len(fixes), not_counted=len(uncounted),
             explained=explained, differences=diffs, not_counted_rows=uncounted,
             fixes=fixes, matched=matched, mismatch=mm,
             closed=(dict(at=cl[0], at_text=_r_stamp(cl[0]) + " IST", by=cl[1] or "", how=cl[2],
                          left_not_counted=cl[3] or 0, left_to_fix=cl[4] or 0) if cl else None),
             day=_r_dmy((c[3] or "")[:10]))
    return root_id, fam, R


def _pad_mismatch_totals(diffs):
    """THE VALUE OF THE STOCK MISMATCH, at MRP first (the owner's basis, D-a)
    and at cost beside it -- with the count of lines that could not be priced,
    because a total is only honest next to what it could not reach.
    diffs: (item, packing, pack, marg, counted, cost_p, mrp_p) tuples."""
    t = dict(lines=len(diffs), short_lines=0, over_lines=0, mrp_provisional=0,
             mrp_short_p=0, mrp_over_p=0, mrp_priced=0, mrp_unpriced=0,
             cost_short_p=0, cost_over_p=0, cost_priced=0, cost_unpriced=0,
             unpriced_both=0, unpriced_both_units=0)
    for d in diffs:
        units = d[4] - d[3]
        if units < 0:
            t["short_lines"] += 1
        else:
            t["over_lines"] += 1
        cost, mrp = d[5], (d[6] if len(d) > 6 else None)
        if mrp is None:
            t["mrp_unpriced"] += 1
        else:
            t["mrp_priced"] += 1
            if len(d) > 7 and d[7] == "provisional":
                t["mrp_provisional"] += 1
            if mrp < 0:
                t["mrp_short_p"] += -int(mrp)
            else:
                t["mrp_over_p"] += int(mrp)
        if cost is None:
            t["cost_unpriced"] += 1
        else:
            t["cost_priced"] += 1
            if cost < 0:
                t["cost_short_p"] += -int(cost)
            else:
                t["cost_over_p"] += int(cost)
        if cost is None and mrp is None:
            t["unpriced_both"] += 1
            t["unpriced_both_units"] += abs(units)
    t["mrp_net_p"] = t["mrp_over_p"] - t["mrp_short_p"]
    t["cost_net_p"] = t["cost_over_p"] - t["cost_short_p"]
    return t


def _pad_sheet_name(R, root_id, nparts):
    """Staff-friendly names, the owner's word. The first pad is SHEET 1; each
    remaining-work sheet is the next number; a finished count is the FINAL
    RESULT. The date is the day the count was started."""
    day = R.get("day") or ""
    if R.get("closed"):
        return "STOCK_COUNT_%s_FINAL_RESULT.xlsx" % day
    if R["sent_back"] + R["not_counted"] > 0:
        return "STOCK_COUNT_%s_SHEET_%d_REMAINING.xlsx" % (day, nparts + 1)
    return "STOCK_COUNT_%s_RESULT_TO_CLOSE.xlsx" % day


def _pad_brief(con, cid, root_id, fam, R):
    """The numbers the page shows after an upload and in the recent list."""
    remaining = R["sent_back"] + R["not_counted"]
    return dict(count_id=cid, root_id=root_id, parts=len(fam) - 1, closed=R.get("closed"),
                sheet_name=_pad_sheet_name(R, root_id, len(fam)),
                finding_no=R["finding_no"], when=R["when"], when_iso=R.get("when_iso"),
                bill_no=R["bill_no"], bill_date=R["bill_date"],
                counted_by=R["counted_by"], entered_by=R["entered_by"],
                items_in_shop=R["items_in_shop"], counted=R["counted"],
                agreed=R["agreed"], differed=R["differed"],
                sent_back=R["sent_back"], not_counted=R["not_counted"],
                remaining=remaining, complete=(remaining == 0),
                followup="/finance/stock/api/pad/followup/%d.xlsx" % root_id,
                sheets=_pad_sheets(con, root_id, fam),
                mismatch=R.get("mismatch"),
                explained=R.get("explained", 0),
                diffs_pdf=("/finance/stock/api/pad/diffs/%d.pdf" % root_id) if R["differed"] else None,
                mismatch_json="/finance/stock/api/pad/mismatch/%d" % root_id,
                report="/finance/stock/page/report?count=%d" % root_id,
                desk="/finance/stock/page/desk?count=%d" % root_id)


@bp.route("/api/pad/followup/<int:cid>.xlsx")
def pad_followup(cid):
    """THE RESULT WORKBOOK, to the owner's approved layout (06-Sep-2026):
    SUMMARY · DIFFERENCES · NOT COUNTED (fill in) · SENT BACK TO FIX (fill in)
    · MATCHED. Handed back the moment a count is recorded, and available again
    later from the same address. Reads the whole family -- the count and every
    part recorded against it -- so a second or third round shows the true
    state, not the first one's."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    try:
        import padwriter                                      # noqa: PLC0415
    except ImportError:
        return jsonify(ok=False, error="missing",
                       message="padwriter.py is not beside stock_app.py"), 503
    con = _db()
    ensure_schema(con)
    root_id, fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    return _xlsx_response(padwriter.result_workbook(R), _pad_sheet_name(R, root_id, len(fam)))


@bp.route("/page/pad")
def page_pad():
    """S226 ON-PAGE: the Excel flow lives on the stock-check page now. The
    old address still works -- it simply goes there."""
    from flask import redirect, url_for                       # noqa: PLC0415
    return redirect(url_for("stock.page_count"), code=302)


@bp.route("/api/pad/recent")
def api_pad_recent():
    """The last counts, newest first, each with its result sheet a click away
    -- so a result sheet is never lost with a closed tab."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    try:
        roots = [r[0] for r in con.execute(
            "SELECT id FROM stock_count WHERE unit=? AND id NOT IN "
            "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 8", (_unit,))]
        out = []
        for rid in roots:
            root_id, fam, R = _pad_family(con, rid)
            if R:
                out.append(_pad_brief(con, rid, root_id, fam, R))
        return jsonify(ok=True, counts=out)
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, error="server", counts=[],
                       message="the recent counts could not be read (%s)." % e.__class__.__name__), 200


def _pad_meta_from(parsed, form):
    """The four details. The sheet's own top lines first -- they were written
    when the pad came down, pinned to the bill of that moment, and a person
    may have corrected them -- then the page's boxes for whatever the sheet
    does not carry."""
    m = parsed.get("meta") or {}
    out = {}
    for k, fk in (("counted_by", "counted_by"), ("entered_by", "entered_by"),
                  ("bill_no", "bill_no"), ("bill_date", "bill_date")):
        v = (m.get(k) or "").strip() or (form.get(fk) or "").strip()
        out[k] = v[:60]
    out["bill_no"] = out["bill_no"].upper()
    out["bill_date"] = _pad_iso_date(out["bill_date"]) or out["bill_date"]
    return out


# S227 DIFF SHEET: the reason numbers on the hand-fill sheet, in STAFF_REASONS order
REASON_NUMBERS = ("count_error", "not_billed", "breakage", "expiry", "sample", "return", "dont_know")
REASON_ENGLISH = {"count_error": "count error", "not_billed": "not billed", "breakage": "breakage",
                  "expiry": "expiry", "sample": "sample / given to doctor", "return": "return",
                  "dont_know": "don't know"}


def _pad_reason_key(v):
    """'3', 3.0, 'breakage', the Hindi label or the English one -> the key; None when nothing."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    try:
        n = int(float(s))
        return REASON_NUMBERS[n - 1] if 1 <= n <= len(REASON_NUMBERS) else None
    except ValueError:
        pass
    up = s.upper()
    for k in REASON_NUMBERS:
        if up == k.upper() or up == REASON_ENGLISH[k].upper() or s == STAFF_REASONS.get(k):
            return k
    m = _re221.match(r"^\s*(\d)\b", s)
    if m and 1 <= int(m.group(1)) <= len(REASON_NUMBERS):
        return REASON_NUMBERS[int(m.group(1)) - 1]
    return None


def _pad_record_answers(con, parsed, snap, root_id, u):
    """The REASON / REMARKS a person wrote on the DIFFERENCES tab become rows of
    stock_diff_answer -- the explanation layer, append-only (S221), on the
    item's newest difference in this family. Never touches a sealed figure."""
    _pad_ensure(con)
    key = {_pad_norm(nm): nm for nm in snap}
    fam = [root_id] + [r[0] for r in con.execute(
        "SELECT count_id FROM stock_count_part WHERE part_of=?", (root_id,))]
    q = ",".join("?" * len(fam))
    n = 0
    for row in parsed["rows"]:
        if row.get("kind") != "diff":
            continue
        reason = _pad_reason_key(row.get("reason"))
        note = (row.get("remarks") or "").strip()
        if not reason and not note:
            continue
        real = key.get(_pad_norm(row["item"]))
        if real is None:
            continue
        d = con.execute("SELECT id FROM stock_diff WHERE item=? AND count_id IN (%s) "
                        "ORDER BY count_id DESC, id DESC LIMIT 1" % q, (real,) + tuple(fam)).fetchone()
        if not d:
            continue
        con.execute("INSERT INTO stock_diff_answer (diff_id, reason, note, answered_by, answered_at) "
                    "VALUES (?,?,?,?,?)", (int(d[0]), reason or "dont_know",
                                           (note or None) if reason else ("(no reason given) " + note),
                                           (u or {}).get("user") or "", now_iso()))
        n += 1
    return n


def _pad_record(con, parsed, summary, meta, u):
    """The sheet becomes a count. What could not be used is KEPT against it;
    a follow-up joins its family; a corrected row closes its issue by the
    ORIGINAL row number, never by the name. Returns the new count id."""
    as_on, snap, matched, unmatched, blank, missing = _pad_match(con, parsed)
    items = [dict(item=m["item"], marg_qty=m["marg"], counted_qty=m["counted"],
                  strips=m["strips"], loose=m["loose"], pack_size=m["pack_size"],
                  counted_by=meta["counted_by"], entered_by=meta["entered_by"]) for m in matched]
    out = _record_count(dict(marg_as_on=as_on, bill_no=meta["bill_no"], bill_date=meta["bill_date"],
                             items_total=len(snap), items=items), u)
    if not out.get("ok"):
        raise ValueError(out.get("message") or out.get("error") or "could not record")
    cid = out["count_id"]
    for pr in parsed["problems"]:
        con.execute("INSERT INTO stock_count_pad_issue (count_id, sheet_row, written, "
                    "figure, why) VALUES (?,?,?,?,?)",
                    (cid, pr[0], pr[1], None, pr[2]))
    for um in unmatched:
        con.execute("INSERT INTO stock_count_pad_issue (count_id, sheet_row, written, "
                    "figure, why) VALUES (?,?,?,?,?)",
                    (cid, um["row"], um["item"], um["counted"],
                     "this name is not in the shop list -- correct it"))
    part_of = parsed.get("part_of")
    _pad_record_answers(con, parsed, snap, int(part_of) if part_of else cid, u)
    if part_of:
        con.execute("INSERT OR REPLACE INTO stock_count_part (count_id, part_of, "
                    "recorded_at) VALUES (?,?,?)", (cid, int(part_of), now_iso()))
        fam = [int(part_of)] + [r[0] for r in con.execute(
            "SELECT count_id FROM stock_count_part WHERE part_of=?", (int(part_of),))]
        for m in matched:
            if m.get("ref"):
                con.execute("UPDATE stock_count_pad_issue SET resolved_by=? WHERE sheet_row=? "
                            "AND resolved_by IS NULL AND count_id IN (%s)"
                            % ",".join("?" * len(fam)), (cid, int(m["ref"])) + tuple(fam))
    con.commit()
    return cid


# ---- S227 PAD PROOF: the sheet is kept, and a receipt says what was ingested ----
# The owner, 06-Sep-2026: save the uploaded Excel sheets, give the stock checkers
# a PDF printout as proof of what the VPS ingested, and preserve the sheets for
# any dispute during the reconciliation of a stock mismatch.
#
# Until this, the server kept a sheet's md5, name and size -- and threw the
# bytes away. Now:
#   · every upload that reaches the server is written to pad_uploads/ beside
#     finance.db, named by its md5, read back and verified -- whatever became
#     of it (recorded, a repeat, held for details, refused). The same bytes are
#     written once, however many times they arrive.
#   · pad_uploads/INDEX.txt is a plain log a person can read: when, md5,
#     outcome, count, who, the phone's file name, size.
#   · GET /api/pad/receipt/<cid>.pdf is the receipt for one recorded sheet;
#     a copy is also written to pad_uploads/ the moment the sheet is recorded.
#   · GET /api/pad/file/<md5>.xlsx hands the checker the original back;
#     GET /api/pad/archive.zip hands the checker the whole folder.
# Recording never waits on the archive: if the disk refuses, the count is still
# recorded and the reply says kept=false -- a count is worth more than its proof,
# and the md5 is in the ledger either way.

def _pad_archive_dir(con):
    """pad_uploads/ beside the database this connection is on. Relative to the
    live db, never a hard-coded mount (the S212 lesson); beside this file when
    the db has no file (a walk on :memory:)."""
    base = None
    try:
        for r in con.execute("PRAGMA database_list"):
            if r[1] == "main" and r[2]:
                base = os.path.dirname(os.path.abspath(r[2]))
                break
    except Exception:                                         # noqa: BLE001
        base = None
    d = os.path.join(base or HERE, "pad_uploads")
    os.makedirs(d, exist_ok=True)
    return d


def _pad_keep(con, raw, md5, fname, u, outcome, count_id=None):
    """Write the bytes once, verify them, record the event. Returns
    dict(kept=bool, kept_as=name, path=full path). Never raises."""
    import hashlib                                            # noqa: PLC0415
    kept, name, path = False, md5 + ".xlsx", ""
    try:
        d = _pad_archive_dir(con)
        path = os.path.join(d, name)
        if not os.path.exists(path):
            tmp = path + ".part"
            with open(tmp, "wb") as fh:
                fh.write(raw)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, path)
        with open(path, "rb") as fh:
            kept = hashlib.md5(fh.read()).hexdigest() == md5
        ts = now_iso()
        who = (u or {}).get("user") or ""
        row = con.execute("SELECT times, count_id, outcome FROM stock_count_pad_archive WHERE md5=?",
                          (md5,)).fetchone()
        if row:
            # the row is the FILE's standing, the INDEX line is the event: a
            # sheet once recorded stays 'recorded' however often it comes again
            standing = "recorded" if (row[2] == "recorded" or outcome == "recorded") else outcome
            con.execute("UPDATE stock_count_pad_archive SET last_seen=?, times=?, outcome=?, "
                        "count_id=COALESCE(?, count_id), verified=? WHERE md5=?",
                        (ts, int(row[0] or 0) + 1, standing, count_id, 1 if kept else 0, md5))
        else:
            con.execute("INSERT INTO stock_count_pad_archive (md5, path, filename, bytes, "
                        "first_seen, seen_by, last_seen, times, outcome, count_id, verified) "
                        "VALUES (?,?,?,?,?,?,?,1,?,?,?)",
                        (md5, name, (fname or "")[:120], len(raw), ts, who, ts, outcome,
                         count_id, 1 if kept else 0))
        con.commit()
        try:
            with open(os.path.join(d, "INDEX.txt"), "a", encoding="utf-8") as fh:
                fh.write("%s IST | %s | %-18s | count %s | by %s | %s | %d bytes | %s\n" % (
                    _r_stamp(ts), md5, outcome, count_id if count_id else "-", who or "-",
                    (fname or "-").replace("|", "/"), len(raw),
                    "verified" if kept else "NOT VERIFIED"))
        except Exception:                                     # noqa: BLE001
            pass
    except Exception:                                         # noqa: BLE001
        kept = False
    return dict(kept=kept, kept_as=name, path=path)


def _pad_sheet_no(con, cid):
    """1 for the root, 2.. for each part in the order recorded."""
    root = con.execute("SELECT part_of FROM stock_count_part WHERE count_id=?", (cid,)).fetchone()
    root_id = int(root[0]) if root else cid
    fam = [root_id] + [r[0] for r in con.execute(
        "SELECT count_id FROM stock_count_part WHERE part_of=? ORDER BY count_id", (root_id,))]
    return root_id, fam, (fam.index(cid) + 1 if cid in fam else 1)


def _pad_receipt_data(con, cid):
    """Everything pad_receipt.render() needs for ONE recorded sheet, read from
    the sealed rows -- so the receipt made today and the receipt made in a
    month say the same thing."""
    _pad_ensure(con)
    c = con.execute("SELECT marg_as_on, bill_no, bill_date, submitted_at, submitted_by "
                    "FROM stock_count WHERE id=?", (cid,)).fetchone()
    if not c:
        return None
    root_id, fam, sheet_no = _pad_sheet_no(con, cid)
    packing = {}
    for r in con.execute("SELECT item, packing FROM stock_snapshot WHERE as_on=?", (c[0],)):
        packing[r[0]] = r[1] or ""
    items = []
    for r in con.execute("SELECT item, packing, marg_qty, counted_qty, strips, loose "
                         "FROM stock_count_item WHERE count_id=? ORDER BY id", (cid,)):
        items.append(dict(item=r[0], packing=r[1] or packing.get(r[0], ""), marg=int(r[2] or 0),
                          counted=int(r[3] or 0), strips=r[4], loose=r[5],
                          diff=int(r[3] or 0) - int(r[2] or 0)))
    fixes = [dict(row=r[0], written=r[1], figure=r[2], why=r[3]) for r in con.execute(
        "SELECT sheet_row, written, figure, why FROM stock_count_pad_issue "
        "WHERE count_id=? ORDER BY sheet_row", (cid,))]
    who = con.execute("SELECT counted_by, entered_by FROM stock_count_item WHERE count_id=? "
                      "LIMIT 1", (cid,)).fetchone() or ("", "")
    f = con.execute("SELECT md5, filename, bytes, uploaded_at, uploaded_by FROM "
                    "stock_count_pad_file WHERE count_id=? ORDER BY uploaded_at LIMIT 1",
                    (cid,)).fetchone()
    file = {}
    if f:
        a = con.execute("SELECT path, verified FROM stock_count_pad_archive WHERE md5=?",
                        (f[0],)).fetchone()
        file = dict(md5=f[0], filename=f[1] or "", bytes=f[2] or 0, uploaded_at=f[3],
                    uploaded_by=f[4] or "", kept=bool(a and a[1]), kept_as=(a[0] if a else ""))
    # the whole family, as the page shows it, so the receipt's last lines agree with the box
    _root, _fam, R = _pad_family(con, cid)
    whole = dict(counted=R["counted"], items_in_shop=R["items_in_shop"], differed=R["differed"],
                 not_counted=R["not_counted"], sent_back=R["sent_back"], closed=R.get("closed"))
    diffs = sum(1 for it in items if it["diff"] != 0)
    return dict(count_id=cid, root_id=root_id, sheet_no=sheet_no, recorded_at=c[3],
                recorded_by=c[4] or "", uploaded_by=file.get("uploaded_by") or c[4] or "",
                counted_by=who[0] or R["counted_by"], entered_by=who[1] or R["entered_by"],
                bill_no=c[1], bill_date=c[2], as_on=c[0], as_on_note=R.get("as_on_note", ""),
                file=file,
                this_sheet=dict(rows=len(items) + len(fixes), counted=len(items),
                                agreed=len(items) - diffs, differed=diffs, to_fix=len(fixes)),
                whole=whole, items=items, fixes=fixes)


def _pad_receipt_name(d):
    day = _r_dmy((d.get("recorded_at") or "")[:10])
    return "STOCK_COUNT_%s_SHEET_%d_PROOF.pdf" % (day, d.get("sheet_no") or 1)


def _pad_receipt_pdf(con, cid):
    """(pdf bytes, file name) or (None, why)."""
    try:
        import pad_receipt                                    # noqa: PLC0415
    except ImportError:
        return None, "pad_receipt.py is not beside stock_app.py"
    d = _pad_receipt_data(con, cid)
    if d is None:
        return None, "no such count"
    return pad_receipt.render(d), _pad_receipt_name(d)


def _pad_receipt_store(con, cid, md5):
    """A frozen copy of the receipt beside the sheet, the moment it is recorded.
    Best effort; the route can always make it again from the sealed rows."""
    try:
        pdf, name = _pad_receipt_pdf(con, cid)
        if pdf:
            d = _pad_archive_dir(con)
            with open(os.path.join(d, "%s_count%d_%s" % (md5[:8], cid, name)), "wb") as fh:
                fh.write(pdf)
            return True
    except Exception:                                         # noqa: BLE001
        pass
    return False


def _pad_receipt_url(cid):
    return "/finance/stock/api/pad/receipt/%d.pdf" % int(cid)


def _pad_sheets(con, root_id, fam):
    """One entry per sheet of the family, root first, each with its receipt."""
    out = []
    for n, cid in enumerate(fam, 1):
        f = con.execute("SELECT md5, filename, uploaded_at FROM stock_count_pad_file "
                        "WHERE count_id=? ORDER BY uploaded_at LIMIT 1", (cid,)).fetchone()
        kept = False
        if f:
            a = con.execute("SELECT verified FROM stock_count_pad_archive WHERE md5=?",
                            (f[0],)).fetchone()
            kept = bool(a and a[0])
        c = con.execute("SELECT submitted_at FROM stock_count WHERE id=?", (cid,)).fetchone()
        out.append(dict(count_id=cid, n=n, when=_r_stamp((c[0] if c else "") or "") + " IST",
                        receipt=_pad_receipt_url(cid), md5=(f[0] if f else ""),
                        filename=(f[1] if f else ""), kept=kept,
                        from_sheet=bool(f)))
    return out


@bp.route("/api/pad/receipt/<int:cid>.pdf")
def api_pad_receipt(cid):
    """The receipt for one recorded sheet -- inline, so the phone opens it and
    the person saves or prints it from there."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    pdf, name = _pad_receipt_pdf(con, cid)
    if pdf is None:
        code = 404 if name == "no such count" else 503
        return jsonify(ok=False, error="no_receipt", message=name), code
    return Response(pdf, status=200, headers={
        "Content-Type": "application/pdf",
        "Content-Disposition": 'inline; filename="%s"' % name,
        "Cache-Control": "no-store"})


# ---- S227 DIFF SHEET: the differences as a hand-fill sheet, and the mismatch value ----
def _pad_answers_by_item(con, fam):
    """The newest staff reason per ITEM across the family (append-only layer)."""
    q = ",".join("?" * len(fam))
    out = {}
    for r in con.execute(
            "SELECT d.item, a.reason, a.note, a.answered_by, a.answered_at FROM stock_diff_answer a "
            "JOIN stock_diff d ON d.id=a.diff_id WHERE d.count_id IN (%s) ORDER BY a.id" % q, tuple(fam)):
        out[r[0]] = dict(reason=r[1], label=REASON_ENGLISH.get(r[1], r[1]), note=r[2] or "",
                         by=r[3] or "", at=r[4])
    return out


def _pad_diffs_data(con, root_id):
    """Everything pad_receipt.render_diffs() needs: the family's differences,
    newest figure per item, MRP first, with any reason already given."""
    _root, fam, R = _pad_family(con, root_id)
    if R is None:
        return None
    ans = _pad_answers_by_item(con, fam)
    rows = []
    for d_ in R["differences"]:
        item, packing, ps, marg, counted, cost_p, mrp_p = d_[:7]
        rows.append(dict(item=item, packing=packing or "", pack=int(ps or 1), marg=marg,
                         counted=counted, diff=counted - marg, cost_p=cost_p, mrp_p=mrp_p,
                         mrp_source=(d_[7] if len(d_) > 7 else None), answer=ans.get(item)))
    # MRP value first (largest loss or gain), then the unpriced by size of the difference
    rows.sort(key=lambda d: (d["mrp_p"] is None, -abs(d["mrp_p"] or 0),
                             d["cost_p"] is None, -abs(d["cost_p"] or 0), -abs(d["diff"])))
    return dict(count_id=_root, sheets=len(fam), when=R["when"], when_iso=R.get("when_iso"),
                day=R.get("day"), counted_by=R["counted_by"], entered_by=R["entered_by"],
                bill_no=R["bill_no"], bill_date=R["bill_date"], as_on=R["as_on"],
                items_in_shop=R["items_in_shop"], counted=R["counted"], agreed=R["agreed"],
                differed=R["differed"], not_counted=R["not_counted"], sent_back=R["sent_back"],
                closed=R.get("closed"), explained=len(ans), mismatch=R["mismatch"], rows=rows,
                reasons=[(i + 1, REASON_ENGLISH[k], STAFF_REASONS.get(k, ""))
                         for i, k in enumerate(REASON_NUMBERS)])


@bp.route("/api/pad/mismatch/<int:cid>")
def api_pad_mismatch(cid):
    """THE VALUE OF THE STOCK MISMATCH -- the separate output the owner asked
    for, 06-Sep-2026: item-wise, and the totals at MRP (and at cost beside)."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    d = _pad_diffs_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    return jsonify(ok=True, count_id=d["count_id"], sheets=d["sheets"], when=d["when"],
                   closed=d["closed"], basis="MRP", totals=d["mismatch"],
                   explained=d["explained"], items=d["rows"],
                   diffs_pdf="/finance/stock/api/pad/diffs/%d.pdf" % d["count_id"])


@bp.route("/api/pad/diffs/<int:cid>.pdf")
def api_pad_diffs_pdf(cid):
    """THE DIFFERENCES, AS A SHEET TO FILL BY HAND -- for the counter, with
    RECOUNT / REASON / REMARKS boxes; what he writes is typed into the
    DIFFERENCES tab of the result workbook and uploaded at step 3."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    try:
        import pad_receipt                                    # noqa: PLC0415
    except ImportError:
        return jsonify(ok=False, error="missing", message="pad_receipt.py is not beside stock_app.py"), 503
    con = _db()
    ensure_schema(con)
    d = _pad_diffs_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    pdf = pad_receipt.render_diffs(d)
    name = "STOCK_COUNT_%s_DIFFERENCES_TO_CHECK.pdf" % (d.get("day") or "")
    return Response(pdf, status=200, headers={
        "Content-Type": "application/pdf",
        "Content-Disposition": 'inline; filename="%s"' % name,
        "Cache-Control": "no-store"})


# ---- S227 FINDING REPORT: the count as a document, and the life of an item ----
# The owner's spec (S226_FINDING_REPORT_SPEC) and his ask of 06-Sep-2026 after the
# first real count: the report on the whole family (a count and its parts); the
# mismatch at MRP; and on every major difference an inline, expandable list of
# the item's purchases this financial year -- vendor, date, bill number, item as
# written, quantity -- with sales and returns beside and Marg's own figures, so
# the Marg operator can reconcile from ONE screen; and the residue no document
# explains, named as such.

def _fy_start(iso):
    """1 April of the financial year that holds the date."""
    s = str(iso or "")[:10]
    try:
        y, m = int(s[:4]), int(s[5:7])
    except ValueError:
        return None
    return "%04d-04-01" % (y if m >= 4 else y - 1)


def _dmy_to_iso(s):
    """Marg's dd-mm-yyyy (or dd/mm/yyyy) -> ISO; an ISO date comes back as is."""
    t = str(s or "").strip().replace("/", "-")
    if len(t) == 10 and t[4] == "-":
        return t
    p = t.split("-")
    if len(p) == 3 and len(p[2]) == 4:
        return "%s-%02d-%02d" % (p[2], int(p[1]), int(p[0]))
    return t


def _qw(units, ps):
    """QUANTITY IN THE SHOP'S OWN WORDS -- the owner, 06-Sep-2026: '400 units is a
    confusing remnant; the qty taxonomy has to be globally implemented; 40 strips is
    neat and a quick grasp'. Strips and tabs for a strip item; pcs for a bottle,
    a vial, a belt (pack 1). Unsigned; the caller puts the sign or the verb."""
    n = abs(int(round(units or 0))); ps = max(1, int(ps or 1))
    if ps <= 1:
        return "%d pc%s" % (n, "" if n == 1 else "s")
    st, tb = divmod(n, ps)
    out = []
    if st:
        out.append("%d strip%s" % (st, "" if st == 1 else "s"))
    if tb:
        out.append("%d tab%s" % (tb, "" if tb == 1 else "s"))
    return " ".join(out) or "0 strips"


def _qws(units, ps):
    """Signed: '+48 strips', '-40 strips', '0 strips'."""
    n = int(round(units or 0))
    return ("+" if n > 0 else ("-" if n < 0 else "")) + _qw(n, ps)


def _sale_units(qty_raw, ps):
    """'strips:loose' as Marg prints it -> units; a bare number is units."""
    s = str(qty_raw or "").strip()
    if not s:
        return 0
    try:
        if ":" in s:
            a, b = s.split(":", 1)
            return int(float(a or 0)) * int(ps or 1) + int(float(b or 0))
        return int(float(s))
    except ValueError:
        return 0


def _purchase_units(qty, free, loose, ps):
    """Units on a purchase line. The owner, 06-Sep-2026, on BIO D3 MAX '20 + 300
    loose = 600': WRONG -- Marg's 'loose' column is the whole quantity in units
    (20 strips x 15 = 300), not a remainder. So: when the loose figure covers the
    strips, it IS the units (plus the free strips if they are not inside it);
    only a small loose figure is a remainder. Returns (units, basis)."""
    qty, free, loose, ps = float(qty or 0), float(free or 0), float(loose or 0), max(1, int(ps or 1))
    packs = (qty + free) * ps
    if loose and qty and loose >= qty * ps:
        if abs(loose - qty * ps) < 0.5 and free:
            return int(round(loose + free * ps)), "loose column = the units; free strips added"
        return int(round(loose)), "loose column = the units"
    return int(round(packs + loose)), "strips x pack + loose remainder"


def _dead_exports(con):
    """md5s of purchase exports a later export replaced. (Only a KNOWN replaced
    export is dropped -- a line whose md5 the export table does not know stays.)"""
    try:
        return {r[0] for r in con.execute("SELECT md5 FROM purchase_export WHERE superseded_by IS NOT NULL")}
    except Exception:                                         # noqa: BLE001
        return set()


def _item_life(con, item, ps, since_iso, upto_iso):
    """Everything on the server that moved ONE item in the window -- the spec's
    'one page per item'. Purchases by bill (vendor, date, bill no, item as the
    bill wrote it, qty, free, loose, units, rate); sales and returns totals by
    the sale lines; Marg's own closing figure day by day; and the residue."""
    ps = int(ps or 1)
    key = _pad_norm(item)
    # purchase lines: matched on the shop's own norm (case, spacing, trailing dots)
    names = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_line") if _pad_norm(r[0]) == key]
    purchases, in_units, in_lines, dropped = [], 0, 0, 0
    if names:
        q = ",".join("?" * len(names))
        vend = {}
        for r in con.execute("SELECT supplier_norm, supplier FROM purchase_bill"):
            vend.setdefault(r[0], r[1])
        dead = _dead_exports(con)
        seen = set()
        for r in con.execute(
                "SELECT supplier_norm, bill_no, bill_date, item, packing, batch, expiry, qty, free, "
                "loose_qty, rate_p, purchase_rate_p, direction, source_md5 FROM purchase_line WHERE item IN (%s) "
                "AND bill_date IS NOT NULL AND bill_date>=? AND bill_date<=? "
                "ORDER BY bill_date, bill_no, id" % q, tuple(names) + (since_iso, upto_iso)):
            # S227 DATA AUDIT (the owner's BIO D3 MAX paste): the same bill line came in
            # through two overlapping exports. Only a live export counts, and the same
            # line is never counted twice.
            if r[13] in dead:
                dropped += 1
                continue
            key = (r[0], r[1], r[2], _pad_norm(r[3]), r[5], r[7], r[8], r[9], (r[12] or "").upper()[:3])
            if key in seen:
                dropped += 1
                continue
            seen.add(key)
            qty, free, loose = float(r[7] or 0), float(r[8] or 0), float(r[9] or 0)
            line_ps = _pack_units(r[4]) or ps
            units, basis = _purchase_units(qty, free, loose, line_ps)
            back = (r[12] or "").upper().startswith("RET")
            if back:
                units = -units
            in_units += units
            in_lines += 1
            on_bill = ("%g" % qty) + ((" + %g free" % free) if free else "") + ((" + %g loose" % loose) if (loose and "remainder" in basis) else "")
            purchases.append(dict(vendor=vend.get(r[0]) or (r[0] or "").upper() or "-",
                                  bill_date=r[2], bill_date_text=_r_dmy(r[2]), bill_no=r[1] or "-",
                                  item=r[3], packing=r[4] or "", batch=r[5] or "", expiry=r[6] or "",
                                  qty=qty, free=free, loose=loose, units=units, basis=basis,
                                  qty_text=("-" if back else "") + _qw(units, line_ps), on_bill=on_bill,
                                  rate_p=r[10], purchase_rate_p=r[11],
                                  direction=("RETURN" if back else "PURCHASE")))
    # sale lines: keyed the way the ingest keys them
    sk = _sale_key(item)
    sold_units, sold_bills, ret_units, ret_cns = 0, set(), 0, set()
    for r in con.execute("SELECT bill_no, is_return, qty_raw, business_date FROM sale_line_item "
                         "WHERE unit=? AND item_key IN (?, ?) AND business_date>=? AND business_date<=?",
                         (_unit, item, sk, since_iso, upto_iso)):
        u = _sale_units(r[2], ps)
        if r[1]:
            ret_units += u; ret_cns.add(r[0])
        else:
            sold_units += u; sold_bills.add(r[0])
    # Marg's own figure, every export day in the window (+ the last one before it)
    snaps = []
    for r in con.execute("SELECT as_on, qty FROM stock_snapshot WHERE item=?", (item,)):
        snaps.append((_dmy_to_iso(r[0]), int(r[1] or 0), r[0]))
    snaps.sort()
    before = [s for s in snaps if s[0] < since_iso]
    inwin = [s for s in snaps if since_iso <= s[0] <= upto_iso]
    marg = ([before[-1]] if before else []) + inwin
    # the residue: what Marg's figure moved by, against what the documents say --
    # EXPORT DAY BY EXPORT DAY, and each residue PINPOINTED (the owner, 06-Sep-2026:
    # "you have all data, find and pinpoint, otherwise ask for a specific lookup").
    det = None
    if len(marg) >= 2:
        def docs(a_iso, b_iso):
            pu = sum(x["units"] for x in purchases if a_iso < (x["bill_date"] or "") <= b_iso)
            su = ru = 0
            for r in con.execute("SELECT is_return, qty_raw FROM sale_line_item WHERE unit=? AND item_key IN (?, ?) "
                                 "AND business_date>? AND business_date<=?", (_unit, item, sk, a_iso, b_iso)):
                u = _sale_units(r[1], ps)
                if r[0]: ru += u
                else: su += u
            return pu, su, ru
        spans, explained_total = [], 0
        used = set()
        for a, b in zip(marg, marg[1:]):
            pu, su, ru = docs(a[0], b[0])
            md = b[1] - a[1]; dd = pu - su + ru; res = md - dd
            span = dict(from_date=a[0], from_text=_r_dmy(a[0]), from_qty=a[1], to_date=b[0], to_text=_r_dmy(b[0]), to_qty=b[1],
                        marg_delta=md, purchased=pu, sold=su, returned=ru, docs_delta=dd, residue=res,
                        moved_text=_qws(md, ps), residue_text=_qws(res, ps), explained=None, lookup=None)
            if res:
                # A -- a bill dated ON the first export day (or the three days before it) whose units equal the
                #      residue: keyed in Marg after that day's export was taken. Documents agree; nothing to chase.
                # B -- two such lines together.  C -- otherwise: the specific lookup for Amir.
                lo = (dt.date.fromisoformat(a[0]) - dt.timedelta(days=3)).isoformat()
                cands = [x for x in purchases if lo <= (x["bill_date"] or "") <= a[0] and x["bill_no"] not in used and x["units"]]
                hit = [x for x in cands if x["units"] == res]
                pair = None
                if not hit:
                    for m_ in range(len(cands)):
                        for n_ in range(m_ + 1, len(cands)):
                            if cands[m_]["units"] + cands[n_]["units"] == res:
                                pair = (cands[m_], cands[n_]); break
                        if pair: break
                lines = ([hit[0]] if hit else (list(pair) if pair else []))
                if lines:
                    for x in lines: used.add(x["bill_no"])
                    span["explained"] = dict(
                        bills=[dict(bill_no=x["bill_no"], bill_date_text=x["bill_date_text"], vendor=x["vendor"], qty_text=x["qty_text"], direction=x["direction"]) for x in lines],
                        sentence="%s is %s -- keyed in Marg after that day's export was taken; the documents agree, nothing to chase."
                                 % (span["residue_text"], " and ".join("%s %s of %s (%s%s)" % ("return" if x["direction"] == "RETURN" else "bill", x["bill_no"], x["bill_date_text"], x["qty_text"],
                                                                                              (", %g free on the bill" % x["free"]) if x["free"] else "") for x in lines)))
                    explained_total += res
                else:
                    span["lookup"] = ("Marg > item ledger > %s > %s to %s: what voucher moved %s %s? No bill, return or sale on the server for it."
                                      % (item, _r_dmy(a[0]), _r_dmy(b[0]), _qw(res, ps), "in" if res > 0 else "out"))
            spans.append(span)
        a, b = marg[0], marg[-1]
        p_units, s_units, r_units = docs(a[0], b[0])
        marg_delta = b[1] - a[1]
        docs_delta = p_units - s_units + r_units
        raw = marg_delta - docs_delta
        residue = raw - explained_total
        open_spans = [x for x in spans if x["lookup"]]
        expl = [x for x in spans if x["explained"]]
        if raw == 0:
            verdict = "no residue -- every %s is accounted for by a document" % ("strip" if ps > 1 else "piece")
        elif residue == 0:
            verdict = "the %s that moved without a document is explained (%s)" % (_qws(raw, ps), "; ".join(x["explained"]["sentence"] for x in expl))
        else:
            verdict = "%s moved with NO document behind them, %s" % (_qws(residue, ps), "; ".join(
                "between %s and %s (%s)" % (x["from_text"], x["to_text"], x["residue_text"]) for x in open_spans) or "in the window")
        det = dict(from_date=a[0], from_text=_r_dmy(a[0]), from_qty=a[1], to_date=b[0], to_text=_r_dmy(b[0]),
                   to_qty=b[1], marg_delta=marg_delta, purchased=p_units, sold=s_units, returned=r_units,
                   docs_delta=docs_delta, residue=residue, raw_residue=raw, explained_units=explained_total,
                   spans=spans, lookups=[x["lookup"] for x in open_spans],
                   sentence=("From %s to %s Marg's figure moved %s; the documents explain %s (bought %s, sold %s, returned %s); %s."
                             % (_r_dmy(a[0]), _r_dmy(b[0]), _qws(marg_delta, ps), _qws(docs_delta, ps), _qw(p_units, ps), _qw(s_units, ps), _qw(r_units, ps), verdict)))
    return dict(item=item, pack_size=ps, since=since_iso, since_text=_r_dmy(since_iso), upto=upto_iso,
                upto_text=_r_dmy(upto_iso), purchase_names=names, purchase_lines_dropped=dropped,
                purchases=purchases, purchased_units=in_units, purchase_lines=in_lines,
                sold_units=sold_units, sale_bills=len(sold_bills), returned_units=ret_units, credit_notes=len(ret_cns),
                marg=[dict(as_on=s[0], text=_r_dmy(s[0]), qty=s[1]) for s in marg],
                detector=det, mrp_p=_mrp_p(con, item), cost_p=_rate_p(con, item))


@bp.route("/api/pad/item/<int:cid>/<path:item>")
def api_pad_item(cid, item):
    """The life of one item, in the count's financial year up to its as-on day."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    root_id, fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    upto = _dmy_to_iso(R["as_on"]) or (R.get("when_iso") or "")[:10]
    since = (request.args.get("from") or "").strip()[:10] or _fy_start(upto) or upto
    ps = 1
    r = con.execute("SELECT pack_size FROM stock_snapshot WHERE item=? AND as_on=?", (item, R["as_on"])).fetchone()
    if r:
        ps = int(r[0] or 1)
    return jsonify(ok=True, count_id=root_id, **_item_life(con, item, ps, since, upto))


def _pad_major(d, major_p=100000):
    """What counts as MAJOR on the report: Rs 1,000 or more at MRP (at cost when
    no MRP), or, unpriced by both, two strips or twenty units."""
    v = d.get("mrp_p") if d.get("mrp_p") is not None else d.get("cost_p")
    if v is not None:
        return abs(int(v)) >= major_p
    return abs(int(d.get("diff") or 0)) >= max(20, 2 * int(d.get("pack") or 1))


# ---- S227 LANES (kit A): the report reads itself -------------------------------
# The owner, 06-Sep-2026: less time to read; the real losses after months of sales;
# what to write off and what to pursue; the count is also a cleanup -- items not
# sold since April marked separately and explained; his work must not grow.
LANES = (
    ("recount", "Recount first", "the figure cannot be real as written -- count the shelf again"),
    ("bill", "Verify the purchase bill", "a box-sized gap with a purchase of that size in the window -- see the bill"),
    ("marg", "Marg moved without a document", "Marg's own figure moved more than the bills explain -- look in Marg first"),
    ("loss", "Real shelf loss", "Marg agrees with the bills; the shelf is short -- write off or pursue"),
    ("allowance", "Within the allowance", "a small shortage a shop expects after months of cutting strips -- write off"),
    ("over", "Over on the shelf", "more on the shelf than Marg -- never a loss"),
    ("salt", "Identical-salt swap (proposal)", "a shortage and a surplus of two brands with the same Marg salt -- a billing swap?"),
    ("dead", "No movement since April", "nothing sold this financial year -- why is it still in Marg?"),
)
LANE_TITLE = {k: t for k, t, _ in LANES}
DEAD_KIND = {
    "A": "Sitting dead -- shelf = Marg, nothing sold. Not a loss. Amir: expiry / return to vendor.",
    "B": "Adjustment stock -- no purchase bill on the server, Marg's figure moved without a document; shelf short. OWNER CONFIRMS: kept elsewhere / used or given / genuinely missing.",
    "C": "Bought this year, never sold, gone from the shelf -- top of the recheck list, then the bill.",
    "D": "Old stock, short -- bought before April, nothing sold. Write-off candidate; Amir checks expiry first.",
    "E": "Clinic-billed stock (orthotics / consumables) -- no Marg sale is expected; the shelf is the truth. Amir corrects Marg after the owner's nod.",
}
LANE_ACTIONS = ("WRITE_OFF", "RECOVER", "EXPLAINED", "RECOUNT", "PARKED", "VERIFY_BILL", "MARG_FIX", "OPEN")
LANE_ACTION_LABEL = {"WRITE_OFF": "written off", "RECOVER": "to pursue", "EXPLAINED": "explained -- no loss",
                     "RECOUNT": "sent to recount", "PARKED": "parked -- kept elsewhere", "VERIFY_BILL": "verify the bill",
                     "MARG_FIX": "correct in Marg", "OPEN": "reopened"}


def _allowance_units(sold, loose_sold, pack, unit_price_p, st):
    """The expected shrinkage for ONE item, computed, not typed: rises with movement
    (units sold; loose sales that cut strips), falls with value per unit, capped at
    one pack. A Rs 50+ unit gets nothing; an unpriced unit is treated as cheap-ish."""
    base = 0.01 * (sold or 0) + 0.05 * (loose_sold or 0)
    if (loose_sold or 0) > 0:
        base = max(base, 2.0)
    if unit_price_p is None:
        f = 0.5
    elif unit_price_p < 500:
        f = 1.0
    elif unit_price_p < 2000:
        f = 0.5
    elif unit_price_p < 5000:
        f = 0.25
    else:
        f = 0.0
    a = base * f * float(st.get("allowance_scale", 1.0))
    return int(min(a, max(1, int(pack or 1))))


def _sales_since(con, since_iso, upto_iso):
    """{sale key: (units, loose units, last sale date)} for the unit, one pass."""
    out = {}
    for r in con.execute("SELECT item_key, qty_raw, business_date, pack FROM sale_line_item WHERE unit=? "
                         "AND is_return=0 AND business_date>=? AND business_date<=?", (_unit, since_iso, upto_iso)):
        ps = _pack_units(r[3]) or 1
        s = str(r[1] or "").strip()
        st = lo = 0
        try:
            if ":" in s:
                a, b = s.split(":", 1); st, lo = int(float(a or 0)), int(float(b or 0))
            elif s:
                lo = int(float(s))
        except ValueError:
            pass
        u = st * ps + lo
        cur = out.get(r[0]) or [0, 0, ""]
        cur[0] += u; cur[1] += lo; cur[2] = max(cur[2], str(r[2] or ""))
        out[r[0]] = cur
    return out


def _purchases_since(con, since_iso, upto_iso):
    """{norm item: (units-ish lines, last bill date, box lines)} -- one pass over purchase_line."""
    out = {}
    dead = _dead_exports(con)
    seen = set()
    for r in con.execute("SELECT item, bill_date, qty, free, loose_qty, direction, source_md5, supplier_norm, bill_no, batch "
                         "FROM purchase_line WHERE bill_date IS NOT NULL AND bill_date>=? AND bill_date<=? ORDER BY id",
                         (since_iso, upto_iso)):
        if r[6] in dead:
            continue
        k = _pad_norm(r[0])
        key = (r[7], r[8], r[1], k, r[9], r[2], r[3], r[4], (r[5] or "").upper()[:3])
        if key in seen:
            continue
        seen.add(key)
        cur = out.get(k) or [0, "", 0.0]
        q = float(r[2] or 0) + float(r[3] or 0)
        cur[0] += 1; cur[1] = max(cur[1], str(r[1] or "")); cur[2] = max(cur[2], q)
        out[k] = cur
    return out


def _salts(con):
    try:
        return {r[0]: (r[1] or "").strip().upper() for r in con.execute("SELECT item_norm, salt FROM purchase_salt_marg")}
    except Exception:                                         # noqa: BLE001
        return {}


def _lane_of(d, ctx):
    """ONE lane per difference, with the reason in words. d carries item, pack,
    marg, counted, diff, mrp_p, cost_p; ctx carries the item's context."""
    pack = max(1, int(d["pack"] or 1)); diff = int(d["diff"]); marg = int(d["marg"]); cnt = int(d["counted"])
    sold, loose, last_sale = ctx["sold"], ctx["loose"], ctx["last_sale"]
    res = ctx.get("residue")
    unit_p = ctx.get("unit_p")
    # 8 -- nothing sold this financial year
    if not sold and not last_sale:
        if _is_ortho(d["item"]):
            return "dead", "E", DEAD_KIND["E"]
        if diff == 0:
            return "dead", "A", DEAD_KIND["A"]
        if ctx["bought_fy"]:
            return "dead", "C", DEAD_KIND["C"]
        if res not in (None, 0) or marg < 0:
            return "dead", "B", DEAD_KIND["B"]
        return "dead", "D", DEAD_KIND["D"]
    # 1 -- the figure cannot be real
    if marg < 0:
        return "recount", "", "Marg's own figure is negative (%d) -- a purchase or a wrong-item sale is missing in Marg; count again and check Marg" % marg
    if diff > 0 and diff >= max(2 * pack, 20) and diff >= max(1, abs(marg)) * 0.5:
        return "recount", "", "counted far above Marg (+%s, Marg %s) -- nobody has that much extra; an entry slip is likely" % (_qw(diff, pack), _qw(marg, pack))
    if pack > 1 and marg > 0 and cnt == (marg % pack) * pack + (marg // pack):
        return "recount", "", "strips and loose look swapped (Marg %d = %d strips %d tabs; counted %d)" % (marg, marg // pack, marg % pack, cnt)
    if pack > 1 and abs(diff) == pack:
        return "recount", "", "the gap is exactly one full strip -- a strip miscounted or one entry missed"
    # 2 -- box-sized, with a purchase of that size in the window
    box = 10 * pack
    nb = int(round(abs(diff) / float(box)))
    # 'about a box': within one strip, or 15% of a box, of a whole number of boxes
    # (AXIMAL 200: 28 strips 6 tabs short = 3 boxes less a fistful -- Darpan reports 3 boxes)
    if nb >= 1 and abs(abs(diff) - nb * box) <= max(pack, int(box * 0.15)):
        if ctx["max_purchase_q"] * pack >= abs(diff) - max(pack, int(box * 0.15)):
            return "bill", "", "the gap is about %d box%s of 10 strips and a purchase of that size sits in the window -- see the bill" % (nb, "" if nb == 1 else "es")
        return "recount", "", "the gap is about a whole box (%d strips) but no purchase of that size is on the server -- count again" % (abs(diff) // pack)
    # 3 -- Marg moved without a document
    if res not in (None, 0) and abs(res) >= max(2, pack):
        return "marg", "", "Marg's figure moved %s more than the documents explain %s -- an adjustment, a correction or a late bill; %s" % (
            _qws(res, pack), ctx.get("res_where") or ("since " + (ctx.get("res_from") or "the first export day")),
            "Amir looks up that span in Marg's item ledger" if ctx.get("res_where") else "look in Marg first")
    # 6 -- over
    if diff > 0:
        return "over", "", "more on the shelf than Marg (+%s) -- a wrong-item sale or an unentered purchase; never a loss" % _qw(diff, pack)
    # 5 -- within the allowance
    allow = ctx["allowance"]
    if -diff <= allow:
        return "allowance", "", "short %s, within the allowance of %s for this item (%s sold, %d loose) -- expected" % (_qw(-diff, pack), _qw(allow, pack), _qw(sold, pack), loose)
    # 4 -- real shelf loss
    return "loss", "", "Marg agrees with the documents%s; the shelf is short %s (allowance %s) -- breakage, unbilled sale or theft" % (
        (" (" + ctx["res_note"] + ")") if ctx.get("res_note") else "", _qw(-diff, pack), _qw(allow, pack))


def _lane_actions(con, root_id):
    """The newest word per item on this family, from the append-only lane table."""
    out = {}
    _pad_ensure(con)
    for r in con.execute("SELECT item, action, note, by_user, at FROM stock_diff_lane WHERE count_id=? ORDER BY id", (root_id,)):
        if r[1] == "OPEN":
            out.pop(r[0], None)          # reopened: the line has no word again (the history stays in the table)
            continue
        out[r[0]] = dict(action=r[1], label=LANE_ACTION_LABEL.get(r[1], r[1]), note=r[2] or "", by=r[3] or "", at=r[4],
                         at_text=_r_stamp(r[4]) + " IST")
    return out


def _pad_report_data(con, root_id):
    """THE REPORT, composed here and nowhere else (D349): the family's header,
    the frozen readiness lines, each part's seal, the mismatch, every difference
    in its LANE with a reason and the owner's word, the cleanup lane, the
    not-counted with the value sitting unchecked, the matched, the rows sent back."""
    _root, fam, R = _pad_family(con, root_id)
    if R is None:
        return None
    _f_ensure(con)
    _pad_ensure(con)
    st = _stock_settings(con)
    q = ",".join("?" * len(fam))
    ans = _pad_answers_by_item(con, fam)
    cause, dec = {}, {}
    for r in con.execute("SELECT id, item, cause, cause_note, count_id FROM stock_diff WHERE count_id IN (%s) "
                         "ORDER BY count_id, id" % q, tuple(fam)):
        cause[r[1]] = dict(cause=r[2], label=CAUSE_LABEL.get(r[2], r[2]), note=r[3] or "", diff_id=r[0])
    ids = [v["diff_id"] for v in cause.values()]
    for did, d in _f_latest(con, "stock_diff_decision", ids,
                            ("decision", "recover_from", "recover_p", "recovery_state", "note", "decided_by", "decided_at")).items():
        for item, v in cause.items():
            if v["diff_id"] == did:
                dec[item] = dict(d, label=DECISION_LABEL.get(d["decision"], d["decision"]))
    upto = _dmy_to_iso(R["as_on"]) or (R.get("when_iso") or "")[:10]
    since = _fy_start(upto) or upto
    sales = _sales_since(con, since, upto)
    purch = _purchases_since(con, since, upto)
    salts = _salts(con)
    words = _lane_actions(con, _root)
    packs = {}
    for r in con.execute("SELECT item, pack_size, qty FROM stock_snapshot WHERE as_on=?", (R["as_on"],)):
        packs[r[0]] = (int(r[1] or 1), int(r[2] or 0))

    def ctx_for(item, pack, need_residue):
        sk = _sale_key(item)
        s = sales.get(sk) or sales.get(item) or [0, 0, ""]
        p = purch.get(_pad_norm(item)) or [0, "", 0.0]
        up, usrc = _price_p(con, item, st)
        res, res_from, res_where, res_note, lookups = None, None, None, None, []
        if need_residue:
            try:
                life = _item_life(con, item, pack, since, upto)
                dd = life.get("detector")
                if dd:
                    res, res_from = dd["residue"], dd["from_text"]
                    lookups = dd.get("lookups") or []
                    opn = [x for x in dd.get("spans") or [] if x.get("lookup")]
                    if opn:
                        res_where = "between %s and %s" % (opn[0]["from_text"], opn[-1]["to_text"]) if len(opn) == 1 else "in %d spans between %s and %s" % (len(opn), opn[0]["from_text"], opn[-1]["to_text"])
                    if dd.get("explained_units") and not res:
                        ex = [x for x in dd["spans"] if x.get("explained")]
                        res_note = "its %s move on %s is %s, keyed after that day's export" % (
                            _qws(dd["explained_units"], pack), ex[0]["from_text"],
                            ", ".join("bill %s" % b_["bill_no"] for x in ex for b_ in x["explained"]["bills"]))
            except Exception:                                 # noqa: BLE001
                res = None
        return dict(sold=s[0], loose=s[1], last_sale=s[2], bought_fy=bool(p[0]), last_purchase=p[1],
                    max_purchase_q=p[2], unit_p=up, price_source=usrc, residue=res, res_from=res_from, res_where=res_where, res_note=res_note, lookups=lookups,
                    allowance=_allowance_units(s[0], s[1], pack, up, st), salt=salts.get(_pad_norm(item), ""))

    diffs = []
    for d_ in R["differences"]:
        item, packing, ps, marg, counted, cost_p, mrp_p = d_[:7]
        d = dict(item=item, packing=packing or "", pack=int(ps or 1), marg=marg, counted=counted,
                 diff=counted - marg, cost_p=cost_p, mrp_p=mrp_p, mrp_source=(d_[7] if len(d_) > 7 else None),
                 answer=ans.get(item), cause=cause.get(item), decision=dec.get(item), word=words.get(item),
                 life="/finance/stock/api/pad/item/%d/%s" % (_root, item))
        d["major"] = _pad_major(d, st["major_p"])
        c = ctx_for(item, d["pack"], need_residue=True)
        lane, kind, why = _lane_of(d, c)
        d.update(lane=lane, lane_title=LANE_TITLE[lane], kind=kind, why=why, allowance=c["allowance"],
                 sold_fy=c["sold"], loose_fy=c["loose"], last_sale=c["last_sale"], bought_fy=c["bought_fy"],
                 last_purchase=c["last_purchase"], residue=c["residue"], salt=c["salt"], lookups=c.get("lookups") or [],
                 needs_owner=(lane == "dead" and kind == "B" and not d["word"]))
        diffs.append(d)
    diffs.sort(key=lambda d: (d["mrp_p"] is None, -abs(d["mrp_p"] or 0), d["cost_p"] is None,
                              -abs(d["cost_p"] or 0), -abs(d["diff"])))
    # identical-salt swap PROPOSALS (D385): the same Marg salt entry, character for character;
    # one short, one over; shown, never netted silently
    by_salt = {}
    for d in diffs:
        if d["salt"] and d["lane"] not in ("dead",):
            by_salt.setdefault(d["salt"], []).append(d)
    pairs = []
    for salt, ds in by_salt.items():
        shorts = [d for d in ds if d["diff"] < 0]; overs = [d for d in ds if d["diff"] > 0]
        if shorts and overs:
            pairs.append(dict(salt=salt, short=[dict(item=d["item"], diff=d["diff"], pack=d["pack"]) for d in shorts],
                              over=[dict(item=d["item"], diff=d["diff"], pack=d["pack"]) for d in overs],
                              net=sum(d["diff"] for d in ds)))
            for d in ds:
                d["salt_pair"] = salt
    # the cleanup lane also names the MATCHED items nobody sold (sitting dead)
    dead_matched = []
    for m in R["matched"]:
        item, packing, ps, qty = m[0], m[1] or "", int(m[2] or 1), m[3]
        c = ctx_for(item, ps, need_residue=False)
        if not c["sold"] and not c["last_sale"] and qty != 0:
            up, usrc = c["unit_p"], c["price_source"]
            dead_matched.append(dict(item=item, packing=packing, pack=ps, marg=qty, counted=qty, diff=0,
                                     kind=("E" if _is_ortho(item) else "A"), why=DEAD_KIND["E" if _is_ortho(item) else "A"],
                                     mrp_p=(None if up is None else up * qty), mrp_source=usrc, bought_fy=c["bought_fy"],
                                     last_purchase=c["last_purchase"], word=words.get(item)))
    # lane totals
    lanes = []
    for key, title, blurb in LANES:
        ds = [d for d in diffs if d["lane"] == key] if key != "salt" else []
        lanes.append(dict(key=key, title=title, blurb=blurb, lines=len(ds),
                          short_units=sum(-d["diff"] for d in ds if d["diff"] < 0),
                          over_units=sum(d["diff"] for d in ds if d["diff"] > 0),
                          short_p=sum(-int(d["mrp_p"]) for d in ds if d["mrp_p"] is not None and d["mrp_p"] < 0),
                          over_p=sum(int(d["mrp_p"]) for d in ds if d["mrp_p"] is not None and d["mrp_p"] > 0),
                          unpriced=sum(1 for d in ds if d["mrp_p"] is None),
                          decided=sum(1 for d in ds if d["word"]),
                          major=sum(1 for d in ds if d["major"]),
                          pairs=(len(pairs) if key == "salt" else 0),
                          dead_matched=(len(dead_matched) if key == "dead" else 0)))
    # the owner's running totals: written off / to pursue / parked / open (at MRP, shortages)
    tot = dict(written_off_p=0, pursue_p=0, parked_p=0, open_p=0, written_off=0, pursue=0, parked=0, open=0,
               explained=0, recount=0, bill=0, marg_fix=0)
    for d in diffs:
        loss = -int(d["mrp_p"]) if (d["mrp_p"] is not None and d["mrp_p"] < 0) else 0
        w = (d["word"] or {}).get("action")
        if w == "WRITE_OFF":
            tot["written_off_p"] += loss; tot["written_off"] += 1
        elif w == "RECOVER":
            tot["pursue_p"] += loss; tot["pursue"] += 1
        elif w == "PARKED":
            tot["parked_p"] += loss; tot["parked"] += 1
        elif w == "EXPLAINED":
            tot["explained"] += 1
        elif w == "RECOUNT":
            tot["recount"] += 1; tot["open_p"] += loss; tot["open"] += 1
        elif w == "VERIFY_BILL":
            tot["bill"] += 1; tot["open_p"] += loss; tot["open"] += 1
        elif w == "MARG_FIX":
            tot["marg_fix"] += 1
        else:
            tot["open_p"] += loss; tot["open"] += 1
    snapq = {k: v[1] for k, v in packs.items()}
    notc, unchecked_p, unchecked_unpriced = [], 0, 0
    for (item, packing, ps) in R["not_counted_rows"]:
        qn = snapq.get(item, 0)
        v, vs = _price_value_p(con, item, qn, st)
        if v is None:
            unchecked_unpriced += 1
        else:
            unchecked_p += abs(int(v))
        notc.append(dict(item=item, packing=packing or "", pack=int(ps or 1), marg=qn, mrp_p=v, mrp_source=vs))
    notc.sort(key=lambda d: (d["mrp_p"] is None, -abs(d["mrp_p"] or 0), -abs(d["marg"])))
    seals = []
    for c in fam:
        f = con.execute("SELECT finding_no, sealed_at, seal_md5 FROM stock_finding WHERE count_id=?", (c,)).fetchone()
        live = _f_seal_md5(con, c) if f else None
        seals.append(dict(count_id=c, finding_no=(f[0] if f else ""), sealed_at=(f[1] if f else None),
                          sealed_text=(_r_stamp(f[1]) + " IST") if f else "not sealed", seal=(f[2] if f else ""),
                          seal_ok=(bool(f) and live == f[2])))
    who = con.execute("SELECT DISTINCT submitted_by FROM stock_count WHERE id IN (%s)" % q, tuple(fam)).fetchall()
    return dict(count_id=_root, parts=len(fam) - 1, family=fam, when=R["when"], when_iso=R.get("when_iso"),
                day=R.get("day"), counted_by=R["counted_by"], entered_by=R["entered_by"],
                submitted_by=", ".join(sorted(w[0] for w in who if w[0])), bill_no=R["bill_no"],
                bill_date=R["bill_date"], bill_date_text=_r_dmy(R["bill_date"]), as_on=R["as_on"],
                as_on_note=R.get("as_on_note", ""), readiness_lines=R.get("readiness_lines") or [],
                seals=seals, seal_ok=all(s["seal_ok"] for s in seals), closed=R.get("closed"),
                items_in_shop=R["items_in_shop"], counted=R["counted"], agreed=R["agreed"],
                differed=R["differed"], not_counted=R["not_counted"], sent_back=R["sent_back"],
                explained=len(ans), mismatch=R["mismatch"], basis="MRP", settings=st,
                fy_from=since, fy_from_text=_r_dmy(since), upto=upto, upto_text=_r_dmy(upto),
                major=sum(1 for d in diffs if d["major"]), differences=diffs, lanes=lanes, pairs=pairs,
                dead_matched=dead_matched, needs_owner=[d["item"] for d in diffs if d["needs_owner"]],
                totals=tot, actions=list(LANE_ACTIONS), action_labels=LANE_ACTION_LABEL, dead_kinds=DEAD_KIND,
                not_counted_rows=notc, unchecked_p=unchecked_p, unchecked_unpriced=unchecked_unpriced,
                matched=[dict(item=m[0], packing=m[1] or "", pack=int(m[2] or 1), qty=m[3]) for m in R["matched"]],
                fixes=[dict(row=f[0], written=f[1], figure=f[2], why=f[3]) for f in R["fixes"]],
                sheets=_pad_sheets(con, _root, fam),
                links=dict(final_sheet="/finance/stock/api/pad/followup/%d.xlsx" % _root,
                           diffs_pdf="/finance/stock/api/pad/diffs/%d.pdf" % _root,
                           mismatch="/finance/stock/api/pad/mismatch/%d" % _root,
                           finding="/finance/stock/page/finding?count=%d" % _root,
                           cleanup="/finance/stock/api/pad/cleanup/%d.xlsx" % _root,
                           amir="/finance/stock/api/pad/amir/%d.xlsx" % _root,
                           audit="/finance/stock/api/pad/audit.xlsx",
                           lookups="/finance/stock/api/pad/lookups/%d.xlsx" % _root))


@bp.route("/api/pad/decide", methods=["POST"])
def api_pad_decide():
    """THE OWNER'S WORD, in bulk or one line: {count_id, items:[...], action, note}.
    WRITE_OFF / RECOVER / EXPLAINED also land on the S221 decision layer of the
    item's newest difference, so the finding page and the report agree. The
    checker only (D-a); append-only, a change of mind is a new row."""
    u, err = _require("checker")
    if err:
        return err
    if not _may_decide(u):
        return jsonify(ok=False, error="forbidden", message="Only the doctor decides a line."), 403
    b = request.get_json(silent=True) or {}
    try:
        cid = int(b.get("count_id") or 0)
    except (TypeError, ValueError):
        cid = 0
    action = str(b.get("action") or "").upper().strip()
    items = [str(x).strip() for x in (b.get("items") or []) if str(x).strip()]
    note = (b.get("note") or "").strip()[:200]
    if not cid or action not in LANE_ACTIONS or not items:
        return jsonify(ok=False, error="bad_request", message="count, action and at least one item are needed."), 400
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    root_id, fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    q = ",".join("?" * len(fam))
    ts = now_iso(); who = (u or {}).get("user") or ""
    n = 0
    for item in items[:500]:
        con.execute("INSERT INTO stock_diff_lane (count_id, item, action, note, by_user, at) VALUES (?,?,?,?,?,?)",
                    (root_id, item, action, note or None, who, ts))
        n += 1
        if action in DECISIONS:
            d = con.execute("SELECT id FROM stock_diff WHERE item=? AND count_id IN (%s) ORDER BY count_id DESC, id DESC LIMIT 1"
                            % q, (item,) + tuple(fam)).fetchone()
            if d:
                con.execute("INSERT INTO stock_diff_decision (diff_id, decision, recover_from, recover_p, recovery_state, "
                            "note, decided_by, decided_at) VALUES (?,?,?,?,?,?,?,?)",
                            (int(d[0]), action, None, None, ("open" if action == "RECOVER" else "none"), note or None, who, ts))
    con.commit()
    return jsonify(ok=True, count_id=root_id, action=action, label=LANE_ACTION_LABEL.get(action, action), items=n)


def _xlsx_rows(title, note, heads, rows, widths):
    """A one-sheet workbook through padwriter's stdlib writer."""
    import padwriter                                          # noqa: PLC0415
    sh = padwriter.Sheet()
    sh.text(1, 0, title, padwriter.TITLE)
    sh.text(2, 0, note, padwriter.NOTE)
    for i, h in enumerate(heads):
        sh.text(4, i, h, padwriter.HEADER)
    r = 5
    for row in rows:
        for i, v in enumerate(row):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                sh.num(r, i, v, padwriter.BOX)
            else:
                sh.text(r, i, "" if v is None else str(v), padwriter.BOX)
        r += 1
    sh.widths = widths
    sh.freeze = "A5"
    return padwriter.workbook_bytes(sh, name="LIST")


@bp.route("/api/pad/cleanup/<int:cid>.xlsx")
def api_pad_cleanup(cid):
    """AMIR'S MARG CLEANUP LIST: every line the owner has decided -- item, Marg's
    figure, the new figure, the reason text -- so the vouchers are keyed once."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    rows = []
    for x in d["differences"]:
        w = x.get("word")
        if not w or w["action"] not in ("WRITE_OFF", "EXPLAINED", "MARG_FIX", "RECOVER"):
            continue
        rows.append([x["item"], x["packing"], x["marg"], x["counted"], x["diff"],
                     "%s%s" % (w["label"], (" -- " + w["note"]) if w.get("note") else ""),
                     "Stock count #%d of %s: %s" % (d["count_id"], d["day"], x["why"]),
                     w["at_text"]])
    return _xlsx_response(_xlsx_rows(
        "MARG CLEANUP LIST -- stock count #%d (%s) -- for Amir" % (d["count_id"], d["day"]),
        "Key ONE stock adjustment per line in Marg: from MARG FIGURE to NEW FIGURE, with the reason. Tick the last column when done. The next Marg export proves it.",
        ["ITEM", "PACKING", "MARG FIGURE (units)", "NEW FIGURE (units)", "CHANGE", "OWNER'S DECISION", "REASON FOR THE VOUCHER", "DECIDED AT", "DONE IN MARG (tick)"],
        rows, {0: 32, 1: 10, 2: 14, 3: 14, 4: 9, 5: 30, 6: 60, 7: 18, 8: 14}),
        "STOCK_COUNT_%s_MARG_CLEANUP_FOR_AMIR.xlsx" % (d["day"] or ""))


@bp.route("/api/pad/amir/<int:cid>.xlsx")
def api_pad_amir(cid):
    """AMIR'S CHECK LIST from the cleanup lane: sitting-dead and old-stock items to
    check for expiry / return to vendor, and the clinic-billed stock to correct."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    rows = []
    for x in d["dead_matched"] + [y for y in d["differences"] if y["lane"] == "dead"]:
        k = x.get("kind") or ""
        job = {"A": "check expiry; return to vendor if possible", "D": "check expiry; confirm the stock is gone; owner may write off",
               "E": "clinic-billed stock: Marg figure to be corrected to the shelf figure after the owner's nod",
               "C": "find the bill; check where the stock went", "B": "WAIT for the owner's word"}.get(k, "")
        rows.append([k, x["item"], x.get("packing", ""), x["marg"], x["counted"], x.get("last_purchase") or "-", job, "", ""])
    rows.sort(key=lambda r: (r[0], r[1]))
    return _xlsx_response(_xlsx_rows(
        "NO MOVEMENT SINCE APRIL -- stock count #%d (%s) -- Amir's check list" % (d["count_id"], d["day"]),
        "Nothing on this list sold this financial year. A = sitting dead (shelf matches), B = owner's word awaited, C = bought this year and gone, D = old stock short, E = clinic-billed. Write what you find in the last two columns.",
        ["KIND", "ITEM", "PACKING", "MARG FIGURE", "SHELF COUNT", "LAST PURCHASE ON SERVER", "WHAT TO DO", "EXPIRY / FOUND (write)", "DONE (tick)"],
        rows, {0: 6, 1: 32, 2: 10, 3: 12, 4: 12, 5: 18, 6: 60, 7: 26, 8: 10}),
        "STOCK_COUNT_%s_NO_MOVEMENT_FOR_AMIR.xlsx" % (d["day"] or ""))


def _purchase_audit(con, since_iso=None):
    """S227 PURCHASE DATA AUDIT -- the owner, 06-Sep-2026: 'our data is wrong ...
    look for all other instances, do a complete data audit'. Sweeps every purchase
    line on the server and reports (1) the same bill line held twice, (2) lines
    where the loose column is the whole quantity in units (the BIO D3 MAX shape --
    '20 + 300 loose' was being read as 600), (3) lines from a superseded export,
    (4) free quantities out of proportion (more than half the paid strips)."""
    since_iso = since_iso or _fy_start(dt.datetime.now().strftime("%Y-%m-%d"))
    gone = _dead_exports(con)
    vend = {}
    try:
        for r in con.execute("SELECT supplier_norm, supplier FROM purchase_bill"):
            vend.setdefault(r[0], r[1])
    except Exception:                                         # noqa: BLE001
        pass
    dup, total_loose, dead, odd_free = [], [], [], []
    seen = {}
    n = 0
    for r in con.execute("SELECT id, supplier_norm, bill_no, bill_date, item, packing, batch, qty, free, "
                         "loose_qty, direction, source_md5 FROM purchase_line WHERE bill_date IS NOT NULL "
                         "AND bill_date>=? ORDER BY bill_date, bill_no, id", (since_iso,)):
        n += 1
        row = dict(id=r[0], vendor=vend.get(r[1]) or (r[1] or "").upper() or "-", bill_no=r[2] or "-",
                   bill_date=r[3], bill_date_text=_r_dmy(r[3]), item=r[4], packing=r[5] or "",
                   batch=r[6] or "", qty=float(r[7] or 0), free=float(r[8] or 0), loose=float(r[9] or 0),
                   direction=(r[10] or "PURCHASE").upper())
        if r[11] in gone:
            dead.append(dict(row, why="its export was replaced by a later one -- not counted"))
            continue
        key = (r[1], r[2], r[3], _pad_norm(r[4]), r[6], r[7], r[8], r[9], row["direction"][:3])
        if key in seen:
            dup.append(dict(row, first_id=seen[key], why="same bill, item, batch and quantity already on the server -- counted once"))
            continue
        seen[key] = r[0]
        ps = _pack_units(r[5]) or 0
        if ps and row["loose"] and row["qty"] and row["loose"] >= row["qty"] * ps:
            u, basis = _purchase_units(row["qty"], row["free"], row["loose"], ps)
            total_loose.append(dict(row, pack=ps, units=u, was=int(round((row["qty"] + row["free"]) * ps + row["loose"])),
                                    why="the loose column (%d) is the whole quantity in units (%d strips x %d); read as %d units, not %d"
                                    % (row["loose"], row["qty"], ps, u, int(round((row["qty"] + row["free"]) * ps + row["loose"])))))
        if row["free"] and row["qty"] and row["free"] > max(2.0, row["qty"] * 0.5):
            odd_free.append(dict(row, why="free %g against %g paid -- more than half; check the bill"
                                 % (row["free"], row["qty"])))
    bills_dup = sorted({(d["bill_no"], d["vendor"]) for d in dup})
    return dict(since=since_iso, since_text=_r_dmy(since_iso), lines=n,
                duplicates=dup, duplicate_bills=len(bills_dup),
                loose_is_total=total_loose, superseded=dead, odd_free=odd_free,
                note="Duplicates and superseded lines are counted once / not at all in the report from this build on; "
                     "the rows stay in the server's tables until Amir removes the double export in Marg's purchase register.")


@bp.route("/api/pad/audit")
def api_pad_audit():
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    return jsonify(ok=True, **_purchase_audit(con))


@bp.route("/api/pad/audit.xlsx")
def api_pad_audit_xlsx():
    """THE PURCHASE DATA AUDIT as one sheet for the owner and Amir."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    a = _purchase_audit(con)
    rows = []
    for kind, lst in (("DOUBLE ENTRY", a["duplicates"]), ("LOOSE = TOTAL", a["loose_is_total"]),
                      ("OLD EXPORT", a["superseded"]), ("FREE TOO HIGH", a["odd_free"])):
        for x in lst:
            rows.append([kind, x["vendor"], x["bill_no"], x["bill_date_text"], x["item"], x["packing"], x["batch"],
                         x["qty"], x["free"], x["loose"], x["why"], ""])
    return _xlsx_response(_xlsx_rows(
        "PURCHASE DATA AUDIT -- since %s -- %d purchase lines checked" % (a["since_text"], a["lines"]),
        "DOUBLE ENTRY = the same bill line is on the server twice (the report now counts it once). LOOSE = TOTAL = Marg's loose column is the whole quantity in units, not a remainder (the report now reads it that way). OLD EXPORT = a line from an export that a later export replaced. FREE TOO HIGH = the free quantity looks wrong against the bill. Tick the last column when checked in Marg.",
        ["WHAT", "VENDOR", "BILL NO", "BILL DATE", "ITEM", "PACKING", "BATCH", "QTY", "FREE", "LOOSE", "WHY IT IS ON THIS LIST", "CHECKED (tick)"],
        rows, {0: 14, 1: 24, 2: 10, 3: 12, 4: 32, 5: 10, 6: 12, 7: 7, 8: 7, 9: 8, 10: 70, 11: 14}),
        "PURCHASE_DATA_AUDIT_%s.xlsx" % dt.datetime.now().strftime("%d-%m-%Y"))


@bp.route("/api/pad/lookups/<int:cid>.xlsx")
def api_pad_lookups(cid):
    """THE SPECIFIC LOOKUPS FOR AMIR: every span where Marg's figure moved with no
    document on the server -- item, the two export days, the quantity, the question."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    rows = []
    for x in d["differences"]:
        for q in x.get("lookups") or []:
            rows.append([x["item"], x["packing"], x["marg"], x["counted"], x["diff"], q, "", ""])
    rows.sort(key=lambda r: (r[0], r[5]))
    return _xlsx_response(_xlsx_rows(
        "MARG LEDGER LOOKUPS -- stock count #%d (%s) -- for Amir" % (d["count_id"], d["day"]),
        "Each line is ONE question for Marg's item ledger: open the item, look at the two dates, and write the voucher that moved the quantity (adjustment / correction / late bill / wrong item). Nothing else to do.",
        ["ITEM", "PACKING", "MARG FIGURE", "SHELF COUNT", "CHANGE", "THE QUESTION FOR MARG'S LEDGER", "WHAT THE LEDGER SAYS (write)", "DONE (tick)"],
        rows, {0: 32, 1: 10, 2: 12, 3: 12, 4: 9, 5: 90, 6: 40, 7: 10}),
        "STOCK_COUNT_%s_MARG_LOOKUPS_FOR_AMIR.xlsx" % (d["day"] or ""))


@bp.route("/api/pad/report/<int:cid>")
def api_pad_report(cid):
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    d = _pad_report_data(con, cid)
    if d is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    d["you"] = dict(user=(u or {}).get("user") or "", checker=_has_role(u, "checker"))
    return jsonify(ok=True, **d)


@bp.route("/page/desk")
def page_desk():
    """THE DECISION DESK -- the owner, 06-Sep-2026, on the lanes page: "too much
    data in a very confusing manner ... too complex and daunting for a human."
    One card at a time, one question, two or three big buttons, nothing to tick;
    the next card comes by itself. The checker's page; the report stays a
    read-only document."""
    u, err = _require("checker")
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    cid = request.args.get("count", "").strip()
    if not cid.isdigit():
        r = con.execute("SELECT id FROM stock_count WHERE unit=? AND id NOT IN "
                        "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1", (_unit,)).fetchone()
        cid = str(r[0]) if r else "0"
    try:
        with io.open(PAGE_DESK, "r", encoding="utf-8") as fh:
            html = fh.read()
    except IOError:
        return jsonify(ok=False, error="missing", message="stock_desk.html is not beside stock_app.py"), 503
    boot = json.dumps(dict(count_id=int(cid), user=(u or {}).get("user") or "", checker=_may_decide(u)))
    return Response(html.replace("/*__BOOT__*/", "window.BOOT=" + boot + ";"), mimetype="text/html")


@bp.route("/page/report")
def page_report():
    """The stock-check report -- the count as a document, on the phone and printed."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    from flask import Response                                # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    cid = request.args.get("count", "").strip()
    if not cid.isdigit():
        r = con.execute("SELECT id FROM stock_count WHERE unit=? AND id NOT IN "
                        "(SELECT count_id FROM stock_count_part) ORDER BY id DESC LIMIT 1", (_unit,)).fetchone()
        cid = str(r[0]) if r else "0"
    roots = [r[0] for r in con.execute(
        "SELECT id FROM stock_count WHERE unit=? AND id NOT IN (SELECT count_id FROM stock_count_part) "
        "ORDER BY id DESC LIMIT 12", (_unit,))]
    try:
        with io.open(PAGE_REPORT, "r", encoding="utf-8") as fh:
            html = fh.read()
    except IOError:
        return jsonify(ok=False, error="missing", message="stock_report.html is not beside stock_app.py"), 503
    boot = json.dumps(dict(count_id=int(cid), roots=roots, user=(u or {}).get("user") or "",
                           checker=_has_role(u, "checker")))
    return Response(html.replace("/*__BOOT__*/", "window.BOOT=" + boot + ";"), mimetype="text/html")
# ---- end S227 FINDING REPORT ---------------------------------------------------


@bp.route("/api/pad/file/<md5>.xlsx")
def api_pad_file(md5):
    """The original sheet back, byte for byte. The checker's, for a dispute."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    md5 = (md5 or "").strip().lower()
    if not _re221.match(r"^[0-9a-f]{32}$", md5):
        return jsonify(ok=False, error="bad_request", message="that is not an md5."), 400
    a = con.execute("SELECT path, filename FROM stock_count_pad_archive WHERE md5=?", (md5,)).fetchone()
    if not a:
        return jsonify(ok=False, error="not_found", message="No kept sheet with that md5."), 404
    path = os.path.join(_pad_archive_dir(con), os.path.basename(a[0]))
    if not os.path.exists(path):
        return jsonify(ok=False, error="gone", message="The sheet's record exists but its file "
                       "is not in pad_uploads/ -- tell the doctor."), 404
    with open(path, "rb") as fh:
        data = fh.read()
    safe = _re221.sub(r"[^A-Za-z0-9._-]+", "_", a[1] or "") or "sheet.xlsx"
    return _xlsx_response(data, "%s_%s" % (md5[:8], safe))


@bp.route("/api/pad/archive")
def api_pad_archive():
    """What the archive holds, newest first. The checker's."""
    u, err = _require("checker")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    d = _pad_archive_dir(con)
    rows = []
    for r in con.execute("SELECT md5, path, filename, bytes, first_seen, seen_by, last_seen, "
                         "times, outcome, count_id, verified FROM stock_count_pad_archive "
                         "ORDER BY first_seen DESC"):
        rows.append(dict(md5=r[0], kept_as=r[1], filename=r[2], bytes=r[3],
                         first_seen=_r_stamp(r[4]) + " IST", seen_by=r[5],
                         last_seen=_r_stamp(r[6]) + " IST", times=r[7], outcome=r[8],
                         count_id=r[9], verified=bool(r[10]),
                         on_disk=os.path.exists(os.path.join(d, os.path.basename(r[1] or ""))),
                         file="/finance/stock/api/pad/file/%s.xlsx" % r[0],
                         receipt=(_pad_receipt_url(r[9]) if r[9] else None)))
    return jsonify(ok=True, folder=d, files=rows, zip="/finance/stock/api/pad/archive.zip")


@bp.route("/api/pad/archive.zip")
def api_pad_archive_zip():
    """The whole pad_uploads/ folder, plus a CSV of the ledger's own rows, as
    one zip -- the off-box copy for F:\\ClinicBackup. The checker's."""
    u, err = _require("checker")
    if err:
        return err
    import csv                                                # noqa: PLC0415
    import zipfile                                            # noqa: PLC0415
    from flask import Response                                # noqa: PLC0415
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    d = _pad_archive_dir(con)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(d)):
            p = os.path.join(d, name)
            if os.path.isfile(p) and not name.endswith(".part"):
                z.write(p, "pad_uploads/" + name)
        s = io.StringIO()
        w = csv.writer(s)
        w.writerow(["md5", "kept_as", "filename", "bytes", "first_seen", "seen_by", "last_seen",
                    "times", "outcome", "count_id", "verified"])
        for r in con.execute("SELECT md5, path, filename, bytes, first_seen, seen_by, last_seen, "
                             "times, outcome, count_id, verified FROM stock_count_pad_archive "
                             "ORDER BY first_seen"):
            w.writerow(list(r))
        z.writestr("pad_uploads/ARCHIVE_LEDGER.csv", s.getvalue())
        s = io.StringIO()
        w = csv.writer(s)
        w.writerow(["md5", "count_id", "filename", "bytes", "uploaded_at", "uploaded_by"])
        for r in con.execute("SELECT md5, count_id, filename, bytes, uploaded_at, uploaded_by "
                             "FROM stock_count_pad_file ORDER BY uploaded_at"):
            w.writerow(list(r))
        z.writestr("pad_uploads/SHEETS_RECORDED.csv", s.getvalue())
    return Response(buf.getvalue(), status=200, headers={
        "Content-Type": "application/zip",
        "Content-Disposition": 'attachment; filename="pad_uploads_%s.zip"'
                               % dt.datetime.now().strftime("%Y%m%d-%H%M"),
        "Cache-Control": "no-store"})
# ---- end S227 PAD PROOF helpers ------------------------------------------------


@bp.route("/api/pad/upload", methods=["POST"])
def api_pad_upload():
    """S226 ON-PAGE -- the owner, 06-Sep-2026: "the upload should be staff
    friendly ... a processing box ... then a prompt to download Excel for the
    remaining work. And this loop should go on so that staff don't have to
    seek me for this work."

    ONE call: read the sheet, record what can be used, keep what cannot, and
    answer with what is left to do and where the result sheet is. The four
    details come from the sheet's own top lines (written in when it was
    downloaded) and the page's boxes fill any gap; if neither has them, the
    page is told exactly which are missing and asks -- nothing is recorded.

    THE SAME FILE TWICE is the same count: a sheet's bytes are remembered
    with the count they made, and uploading it again returns that count's
    result rather than recording a second one.

    S227 PAD PROOF: the bytes are KEPT first -- whatever happens next -- and
    a recorded sheet answers with its receipt (a PDF) and kept=true."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    fs = request.files.get("file")
    if fs is None:
        return jsonify(ok=False, error="no_file",
                       message="No file arrived. Choose the filled pad."), 400
    fname = (getattr(fs, "filename", "") or "")[:120]
    try:
        raw, md5, n = _pad_raw(fs)
    except ValueError as e:                                   # noqa: BLE001
        return jsonify(ok=False, error="unreadable", message=str(e), filename=fname), 200
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    try:
        parsed = _pad_parse(raw)
    except ValueError as e:                                   # noqa: BLE001
        k = _pad_keep(con, raw, md5, fname, u, "refused-no_reader")
        return jsonify(ok=False, error="unreadable", message=str(e), filename=fname,
                       md5=md5, kept=k["kept"]), 200
    except Exception as e:                                    # noqa: BLE001
        k = _pad_keep(con, raw, md5, fname, u, "refused-unreadable")
        return jsonify(ok=False, error="unreadable", filename=fname, md5=md5, kept=k["kept"],
                       message="that file could not be read as a count pad (%s)."
                               % e.__class__.__name__), 200
    try:
        prev = con.execute("SELECT count_id FROM stock_count_pad_file WHERE md5=?", (md5,)).fetchone()
        if prev:
            k = _pad_keep(con, raw, md5, fname, u, "repeat", int(prev[0]))
            root_id, fam, R = _pad_family(con, int(prev[0]))
            b = _pad_brief(con, int(prev[0]), root_id, fam, R)
            b.update(ok=True, repeat=True, filename=fname, md5=md5, kept=k["kept"],
                     receipt=_pad_receipt_url(int(prev[0])),
                     message="This exact file was already recorded as count #%d. Nothing was "
                             "recorded again -- the result sheet below is the current one."
                             % int(prev[0]))
            return jsonify(**b)
        summary = _pad_summary(con, parsed, md5, n)
        if summary["blocked"]:
            k = _pad_keep(con, raw, md5, fname, u, "refused-empty")
            return jsonify(ok=False, error="empty", filename=fname, md5=md5, kept=k["kept"],
                           message=summary["blocked_why"]), 200
        meta = _pad_meta_from(parsed, request.form)
        part_of = parsed.get("part_of")
        if part_of:
            root = con.execute("SELECT bill_no, bill_date FROM stock_count WHERE id=?",
                               (int(part_of),)).fetchone()
            if not root:
                k = _pad_keep(con, raw, md5, fname, u, "refused-no_root")
                return jsonify(ok=False, error="no_root", filename=fname, md5=md5, kept=k["kept"],
                               message="This sheet says it is part of count #%d, but there is "
                                       "no such count on this server." % int(part_of)), 200
            cl = con.execute("SELECT closed_at, how FROM stock_count_close WHERE count_id=?",
                             (int(part_of),)).fetchone()
            if cl:
                k = _pad_keep(con, raw, md5, fname, u, "refused-closed")
                return jsonify(ok=False, error="closed", filename=fname, count_id=int(part_of),
                               md5=md5, kept=k["kept"],
                               message="Count #%d was CLOSED on %s%s. This sheet belongs to it and "
                                       "cannot be added now -- nothing was recorded. For a new "
                                       "count, start again at step 1 and download a fresh pad."
                                       % (int(part_of), _r_stamp(cl[0]),
                                          "" if cl[1] == "complete" else " by the doctor, as it stood")), 200
            meta["bill_no"], meta["bill_date"] = root[0], root[1]
        need = [k for k in ("counted_by", "entered_by", "bill_no", "bill_date") if not meta[k]]
        if need:
            k = _pad_keep(con, raw, md5, fname, u, "held-need_details")
            return jsonify(ok=False, error="need_details", need=need, known=meta,
                           filename=fname, md5=md5, kept=k["kept"],
                           message="The sheet does not say %s. Fill that in above and "
                                   "upload the same file again." % " / ".join(
                                       {"counted_by": "who counted", "entered_by": "who entered",
                                        "bill_no": "the last bill number",
                                        "bill_date": "the bill date"}[k] for k in need)), 200
        cid = _pad_record(con, parsed, summary, meta, u)
        con.execute("INSERT OR REPLACE INTO stock_count_pad_file (md5, count_id, filename, "
                    "bytes, uploaded_at, uploaded_by) VALUES (?,?,?,?,?,?)",
                    (md5, cid, fname, n, now_iso(), u.get("user") or ""))
        con.commit()
        k = _pad_keep(con, raw, md5, fname, u, "recorded", cid)
        _pad_receipt_store(con, cid, md5)
        root_id, fam, R = _pad_family(con, cid)
        b = _pad_brief(con, cid, root_id, fam, R)
        b.update(ok=True, repeat=False, filename=fname, md5=md5, part_of=part_of,
                 kept=k["kept"], receipt=_pad_receipt_url(cid),
                 this_sheet=dict(rows=len(parsed["rows"]), counted=summary["counted"],
                                 agreed=summary["agreed"], differed=summary["differed"],
                                 to_fix=summary["to_fix"]))
        return jsonify(**b)
    except Exception as e:                                    # noqa: BLE001
        k = _pad_keep(con, raw, md5, fname, u, "refused-server")
        return jsonify(ok=False, error="server", filename=fname, md5=md5, kept=k["kept"],
                       message="the sheet was read, but this server could not record it "
                               "(%s). Check the recent counts below before trying again."
                               % e.__class__.__name__), 200


@bp.route("/api/pad/close/<int:cid>", methods=["POST"])
def api_pad_close(cid):
    """CLOSE THE STOCK CHECK. The owner, 06-Sep-2026: "a final close stock check
    button closes the full session with a prompt -- stock check completed, and
    should not entertain any further excel loops; the button appears after the
    VPS verifies the work ... if left incomplete, abandoned, I should have the
    power to close the stock count, so that our analytics and follow-up run."

    So: anyone who can count may close a count THE SERVER SAYS IS COMPLETE
    (nothing not counted, nothing to fix). A count with work left can be closed
    only by the checker, and is marked as closed incomplete, with what was left
    written down. A closed count takes no more sheets."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    root_id, fam, R = _pad_family(con, cid)
    if R is None:
        return jsonify(ok=False, error="not_found", message="No count #%d." % cid), 404
    if R.get("closed"):
        b = _pad_brief(con, root_id, root_id, fam, R)
        b.update(ok=True, already=True, message="Count #%d is already closed." % root_id)
        return jsonify(**b)
    remaining = R["sent_back"] + R["not_counted"]
    if remaining > 0:
        if not _may_decide(u):
            return jsonify(ok=False, error="incomplete", remaining=remaining,
                           message="Some stock count is still left: %d item(s) not counted, %d row(s) "
                                   "to fix. Download the sheet and complete it. Only the doctor can "
                                   "close a count with work left." % (R["not_counted"], R["sent_back"])), 200
        how = "incomplete"
    else:
        how = "complete"
    con.execute("INSERT OR REPLACE INTO stock_count_close (count_id, closed_at, closed_by, how, "
                "left_not_counted, left_to_fix) VALUES (?,?,?,?,?,?)",
                (root_id, now_iso(), (u or {}).get("user") or "", how, R["not_counted"], R["sent_back"]))
    con.commit()
    root_id, fam, R = _pad_family(con, root_id)
    b = _pad_brief(con, root_id, root_id, fam, R)
    b.update(ok=True, already=False, how=how,
             message=("STOCK CHECK COMPLETED -- count #%d is closed." % root_id) if how == "complete"
             else ("Count #%d closed by the doctor as it stood: %d not counted, %d to fix."
                   % (root_id, R["not_counted"], R["sent_back"])))
    return jsonify(**b)


@bp.route("/api/pad/preview", methods=["POST"])
def api_pad_preview():
    """Read the sheet and say exactly what was understood. WRITES NOTHING.
    Kept for the checker's console; the staff flow is /api/pad/upload."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    fs = request.files.get("file")
    if fs is None:
        return jsonify(ok=False, error="no_file",
                       message="No file arrived. Choose the filled count pad."), 400
    try:
        parsed, md5, n = _pad_read(fs)
    except ValueError as e:                                   # noqa: BLE001
        return jsonify(ok=False, error="unreadable", message=str(e)), 200
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, error="unreadable",
                       message="that file could not be read as a count pad (%s)."
                               % e.__class__.__name__), 200
    con = _db()
    ensure_schema(con)
    try:
        s = _pad_summary(con, parsed, md5, n)
        s["meta"] = parsed.get("meta") or {}
        return jsonify(**s)
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, error="server",
                       message="the sheet was read, but this server could not line "
                               "it up against the stock list (%s). Nothing was "
                               "recorded." % e.__class__.__name__), 200


@bp.route("/api/pad/commit", methods=["POST"])
def api_pad_commit():
    """Record the sheet as a count -- but only the sheet that was previewed.
    The two-step path; the page uses /api/pad/upload."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    fs = request.files.get("file")
    if fs is None:
        return jsonify(ok=False, error="no_file", message="No file arrived."), 400
    want = (request.form.get("md5") or "").strip()
    try:
        raw, md5, n = _pad_raw(fs)
        parsed = _pad_parse(raw)
    except Exception as e:                                    # noqa: BLE001
        return jsonify(ok=False, error="unreadable", message=str(e)), 200
    if want and want != md5:
        return jsonify(ok=False, error="changed",
                       message="This is not the file that was checked a moment ago. "
                               "Look at it again before recording it."), 200
    con = _db()
    ensure_schema(con)
    _pad_ensure(con)
    prev = con.execute("SELECT count_id FROM stock_count_pad_file WHERE md5=?", (md5,)).fetchone()
    if prev:
        return jsonify(ok=False, error="repeat",
                       message="This exact file was already recorded as count #%d." % int(prev[0])), 200
    summary = _pad_summary(con, parsed, md5, n)
    if summary["blocked"]:
        return jsonify(ok=False, error="empty", message=summary["blocked_why"]), 200
    meta = _pad_meta_from(parsed, request.form)
    if not all(meta.values()):
        return jsonify(ok=False, error="bad_request",
                       message="The bill number, its date, who counted and who "
                               "entered are all required -- a count that is not "
                               "pinned to a bill cannot be reconciled later."), 400
    try:
        cid = _pad_record(con, parsed, summary, meta, u)
    except ValueError as e:
        return jsonify(ok=False, error="bad_request", message=str(e)), 200
    con.execute("INSERT OR REPLACE INTO stock_count_pad_file (md5, count_id, filename, "
                "bytes, uploaded_at, uploaded_by) VALUES (?,?,?,?,?,?)",
                (md5, cid, (getattr(fs, "filename", "") or "")[:120], n, now_iso(), u.get("user") or ""))
    con.commit()
    k = _pad_keep(con, raw, md5, (getattr(fs, "filename", "") or "")[:120], u, "recorded", cid)
    _pad_receipt_store(con, cid, md5)
    root_id, fam, R = _pad_family(con, cid)
    b = _pad_brief(con, cid, root_id, fam, R)
    b.update(ok=True, kept=k["kept"], receipt=_pad_receipt_url(cid),
             from_pad=dict(md5=md5, rows=len(parsed["rows"]),
                                    to_fix=summary["to_fix"], not_counted=summary["not_counted"],
                                    part_of=parsed.get("part_of"),
                                    followup=("/api/pad/followup/%d.xlsx" % cid)
                                    if (summary["to_fix"] or summary["not_counted"]) else None))
    return jsonify(**b)
# ---- end S226 PAD IMPORT -----------------------------------------------------
