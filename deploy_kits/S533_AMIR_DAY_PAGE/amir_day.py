"""
amir_day.py -- Amir's day, as seven steps on a phone.  (S241, D472; rebuilt whole by S533_AMIR_DAY_PAGE, D706 / D708 / D709 / D712)

One page, one thing at a time, a 1 -> 7 banner at the top, a confirmation after each step, and a DAY CLOSED screen at the end.
The owner's design is in claude/S240_AMIR_DAY_FLOW.md; the rulings behind it are D468-D477, and the rebuild's are D706-D712.

The principles this file keeps (S241-S246):
  * He is never asked whether a report arrived.  The server reads the exports it already holds and TELLS him.
  * The bill list fills itself from the bill-wise export.  He types no bill number, ever.
  * The answer to a bill is one tap ("Theek hai", or "Theek nahi" and a reason).  An unanswered bill comes back.
  * A day he leaves half-done stays OPEN, never failed.  Attendance never blocks his work.
  * He raises a claim; he never chases one.  Chasing is Darpan's queue.
No JavaScript (the only client behaviour is step 4's meta refresh while a report is in transit).  Amir's screens are Roman Hindi;
the owner's view of the same day is English.

S533 (the rebuild, charter v1.1):
  * READ ONCE.  state(cx, day, who) reads every fact a page needs once per request -- the log, the pair, the bills, the salt list, the
    stage (stock_app.amir_stage, once), its words (stock_app._s521_stage_words, once), the scans (purchase_app.scans_for_amir, once),
    the card's inputs -- and derives the gate once.  It writes nothing of this file's own.
  * WORDS ONCE.  Each line is built once, as a (hi, en) pair, in the row the screen reads: Amir's step 7, his card, the owner's
    /finance/amir/day, the visit summary and Needs-you print the same row.
  * APPEND ONLY.  A tap is a row (amir_step_log, amir_bill_answer); a second tap is a new row that replaces the old one, which stays.
    The system's own clear of his "Meri entry galat thi" is its own row beside his.  Nothing is ever deleted here.
  * settle(cx, S) is the only write of this file on a read (Amir's GETs and Needs-you): his corrections cleared once Marg shows them,
    the one-time jobs proved, the returns count re-made when its inputs moved.  Audited; idle when there is nothing to settle.
  * DUTY_SQL holds the three duty-map SQLs; the duty map copies them byte-equal and the code here RUNS them.
  * D712: Amir's bill line comes from the scan ("Scan hua bill Marg mein baaki: N"), never from a reception tap; an arrival with
    nothing scanned is the owner's line only.
"""

import html
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, redirect, url_for

bp = Blueprint("amir_day", __name__)

_db = None
_require = None
_unit = "medical"
# Any role on the unit may open his own day (the medical unit has one maker, one checker and four viewers; Amir is a viewer).
# Every write records who made it, so the record stays attributable at the wider gate.
_roles = ("maker", "checker", "viewer")

KIT = "S533_AMIR_DAY_PAGE"
IST = timezone(timedelta(hours=5, minutes=30))

# The two reports that make up the daily pair (D469).
PAIR = (
    ("ITEMWISE", "Item-detail purchase report"),
    ("BILLWISE", "Bill-wise purchase report"),
)

REASONS = (
    ("ok",        "Theek hai"),
    ("self",      "Meri entry galat thi — Marg mein theek kar di"),    # S444 (F-670): his own slip -- no claim; clears itself
    ("short",     "Kam maal aaya"),
    ("nodeal",    "Deal nahi mili"),
    ("discount",  "Discount kam"),
    ("supplier",  "Supplier galat likha"),
    ("other",     "Aur koi baat"),
)
REASON_MAP = dict(REASONS)

# A reason that is not "ok" or "self" (or "supplier") raises a claim for Darpan to chase (D471).
CLAIM_REASONS = ("short", "nodeal", "discount", "other")

STEPS = (
    (1, "Punch"),
    (2, "Bill entry"),
    (3, "Export"),
    (4, "Check"),
    (5, "Bills"),
    (6, "Marg sudhar"),
    (7, "Band"),
)

# Steps that decide whether a day is finished.  Step 1 is a nudge, step 3 an instruction, step 7 the close itself.
GATE_STEPS = (2, 4, 5, 6)

SALT_LIST_TYPE = "SALT_WISE_ITEM_LIST"
_STAMP14 = re.compile(r"^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$")      # Marg's own YYYYMMDD-HHMMSS stamp

# S244: how long a freshly exported report may be in transit before the screen stops saying "aa rahi hai".  The clock starts when
# HE says he has exported (the newest step-3 row), never when the page is opened.
try:
    EXPORT_GRACE_MIN = int(os.environ.get("AMIR_EXPORT_GRACE_MIN") or 6)
except (TypeError, ValueError):
    EXPORT_GRACE_MIN = 6
if EXPORT_GRACE_MIN < 1 or EXPORT_GRACE_MIN > 60:
    EXPORT_GRACE_MIN = 6
EXPORT_POLL_SEC = 20                     # how often step 4 re-checks itself while a report is in transit

# S246: bills dated before this are settled and never shown again (owner, 13-Sep-2026).  S533: a literal (the env override is gone).
BILLS_FROM = "2026-09-01"

# ---- the owner's settings (S444, S488, S494): setting rows; these are the defaults ----
S444_TOL_P = 100                                     # Rs 1 -- "equal within Rs 1"
S444_DUTY_MAP = os.environ.get("DUTY_MAP_JSON", "/root/deploy/repo/claude_code_briefs/DUTY_MAP.json")
S444_DEFAULTS = {"amir.salt_owed_days": 2, "amir.self_exports": 2, "amir.claim_open_days": 7, "amir.voucher_visits": 2,
                 "amir.proof_wait_hours": 48, "amir.refused_keep_hours": 36, "amir.job_wait_days": 10}
S444_NOTES = {"amir.salt_owed_days": "S444: visits a SALT WISE ITEM LIST may be owed before the owner's Needs-you line (S533: visit days)",
              "amir.self_exports": "S444: bill-wise exports after Amir's own correction before the owner's line",
              "amir.claim_open_days": "S444: days a claim for Darpan may stay open before the owner's line",
              "amir.voucher_visits": "S444: Amir's visits without opening the count vouchers before the owner's line",
              "amir.proof_wait_hours": "S488: hours a count's voucher proof may wait before the owner's warn line",
              "amir.refused_keep_hours": "S488: hours a refused report stays on the owner's Needs-you list (kept past midnight)",
              "amir.job_wait_days": "Amir's one-time Marg jobs: days before your Needs-you list names them"}

# ---- S494 (D686): Amir's one-time Marg jobs ----
S494_DDL = ("CREATE TABLE IF NOT EXISTS amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, "
            "text_hi TEXT, sub_hi TEXT, created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, "
            "done_at TEXT, done_how TEXT)")
S494_KINDS = {"category": 0, "vendor_bill": 1, "tap": 2}
S494_CAT_TYPE = "CATEGORY_WISE_ITEM_LIST"
# S533: a reopen no longer erases what he said -- it stamps reopened_at; a job counts as SAID only when said after the newest reopen.
S494_SAID = "said_at IS NOT NULL AND said_at > COALESCE(reopened_at, '')"
S494_OPEN = "show_from IS NOT NULL AND done_at IS NULL AND NOT (" + S494_SAID + ")"

S488_WHYS = ("no_closing", "no_figure", "pur_behind", "no_before", "rebased")

# ---- the duty map's three SQLs (DUTY_MAP.json v11 copies them byte-equal; the code below RUNS them) ----
_BILLS_BASE = ("SELECT b.id, b.first_seen_day FROM purchase_bill b JOIN purchase_export e ON e.md5 = b.bw_md5 "
               "WHERE e.type = 'BILLWISE' AND e.superseded_by IS NULL AND b.bill_date >= '%s'" % BILLS_FROM)
_BILLS_UNANSWERED = (" AND NOT EXISTS (SELECT 1 FROM amir_bill_answer a WHERE a.bill_id = b.id OR (a.bill_id IS NULL AND "
                     "a.supplier_norm = b.supplier_norm AND a.bill_no = b.bill_no AND a.bill_date = b.bill_date))")
_SALT_LAST = ("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file "
              "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'")
DUTY_SQL = {
    "amir.bills_answer": "SELECT COUNT(*) AS n, MIN(first_seen_day) AS since FROM (" + _BILLS_BASE + _BILLS_UNANSWERED + ")",
    "amir.own_correction": "SELECT COUNT(*) AS n, MIN(substr(replace(marked_at,'T',' '),1,19)) AS since FROM amir_self_wait WHERE cleared_at IS NULL",
    "amir.salt_list": ("WITH l(t) AS (" + _SALT_LAST + ") SELECT COUNT(*) AS n, MIN(substr(replace(s.done_at,'T',' '),1,19)) AS since "
                       "FROM purchase_salt_task s, l WHERE COALESCE(s.done,0) = 1 AND s.done_at IS NOT NULL AND s.done_at <> '' "
                       "AND (l.t IS NULL OR substr(replace(s.done_at,'T',' '),1,19) > l.t)"),
}


# ==========================================================================================================================================
# clock and text
# ==========================================================================================================================================
def _now():
    return datetime.now(IST)


def _today():
    return _now().strftime("%Y-%m-%d")


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _norm_ts(s):
    """Any stored time -> 'YYYY-MM-DD HH:MM:SS' so stamps of different writers compare as text (charter 11): Marg's YYYYMMDD-HHMMSS,
    ISO with a 'T' and a zone, or a space."""
    if not s:
        return None
    s = str(s).strip()
    m = _STAMP14.match(s)
    if m:
        return "%s-%s-%s %s:%s:%s" % m.groups()
    s = s.replace("T", " ")
    if len(s) >= 19:
        return s[:19]
    if len(s) == 16:
        return s + ":00"
    if len(s) == 10:
        return s + " 00:00:00"
    return None


def _hhmm(s):
    t = _norm_ts(s)
    return t[11:16] if t else ""


def _dm_hm(ts, time=True):
    """'2026-09-13 08:12:00' -> '13-09 08:12' (time=False: '13-09'); '' when it cannot be read."""
    t = _norm_ts(ts)
    if not t:
        return ""
    return ("%s-%s %s" % (t[8:10], t[5:7], t[11:16])) if time else ("%s-%s" % (t[8:10], t[5:7]))


def _ddmmyyyy(day):
    """'2026-09-13' -> '13-09-2026' -- the shape Marg's own date boxes use."""
    d = str(day or "")[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", d):
        return str(day or "")
    return "%s-%s-%s" % (d[8:10], d[5:7], d[:4])


def _mins_since(ts):
    t = _norm_ts(ts)
    if not t:
        return None
    try:
        d = datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
    except (TypeError, ValueError):
        return None
    return max(0, int((_now() - d).total_seconds() // 60))


def _month_first(day):
    return (str(day or "")[:8] + "01") if len(str(day or "")) == 10 else ""


def _days_since(ts):
    """Calendar days from a stored stamp's day to today (IST); None when it cannot be read."""
    t = _norm_ts(ts)
    if not t:
        return None
    try:
        return (datetime.strptime(_today(), "%Y-%m-%d") - datetime.strptime(t[:10], "%Y-%m-%d")).days
    except ValueError:
        return None


def _rupees(paise):
    """Paise -> '1,234' (whole rupees); '-' when there is no figure."""
    try:
        return "{:,}".format(int(round(int(paise) / 100.0)))
    except (TypeError, ValueError):
        return "-"


def _esc(v):
    return html.escape("" if v is None else str(v))


def _plural(n, one, many):
    return one if int(n) == 1 else many


# ==========================================================================================================================================
# schema -- one function, once per process per database file (charter: additive, never at import)
# ==========================================================================================================================================
_ENSURED = set()


def _db_file(cx):
    try:
        for r in cx.execute("PRAGMA database_list").fetchall():
            if r[1] == "main":
                return r[2] or ("mem:%d" % id(cx))
    except Exception:                                                  # noqa: BLE001
        pass
    return "mem:%d" % id(cx)


def _cols(cx, table):
    return {r[1] for r in cx.execute("PRAGMA table_info(%s)" % table).fetchall()}


def ensure(cx):
    """amir_day, amir_step_log, amir_bill_answer, amir_claim, amir_self_wait (+bill_id), amir_job (+reopened_at) and their indexes.
    CREATE IF NOT EXISTS / ALTER only where absent.  The two older tables (the step ticks and the bill dispositions) are history: never created, read or
    written here (data_s533 copied them)."""
    key = _db_file(cx)
    if key in _ENSURED:
        return
    cx.execute("CREATE TABLE IF NOT EXISTS amir_day (day TEXT PRIMARY KEY, opened_at TEXT, closed_at TEXT, closed_by TEXT, "
               "reopened_at TEXT, reopened_by TEXT)")
    cx.execute("CREATE TABLE IF NOT EXISTS amir_step_log (id INTEGER PRIMARY KEY, day TEXT NOT NULL, step INTEGER NOT NULL, "
               "done_at TEXT NOT NULL, by_user TEXT, note TEXT, replaces INTEGER)")
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_step_log_day ON amir_step_log (day, step, id)")
    cx.execute("CREATE TABLE IF NOT EXISTS amir_bill_answer (id INTEGER PRIMARY KEY, bill_id INTEGER, supplier_norm TEXT NOT NULL, "
               "bill_no TEXT NOT NULL, bill_date TEXT NOT NULL, day TEXT, reason TEXT NOT NULL, by_user TEXT, at TEXT NOT NULL, "
               "note TEXT, replaces INTEGER)")
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_bill_answer_bill ON amir_bill_answer (bill_id, id)")
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_bill_answer_triple ON amir_bill_answer (supplier_norm, bill_no, bill_date, id)")
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_claim(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        supplier      TEXT,
        supplier_norm TEXT,
        bill_no       TEXT,
        bill_date     TEXT,
        amount_p      INTEGER,
        reason        TEXT,
        raised_by     TEXT,
        raised_at     TEXT,
        state         TEXT NOT NULL DEFAULT 'open',
        contacted_note TEXT,
        settled_outcome TEXT,
        settled_at    TEXT,
        settled_by    TEXT,
        closed_auto   INTEGER NOT NULL DEFAULT 0
    )""")
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_claim_state ON amir_claim(state, raised_at)")
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_self_wait(
        supplier_norm TEXT NOT NULL,
        bill_no       TEXT NOT NULL,
        bill_date     TEXT NOT NULL,
        marked_at     TEXT NOT NULL,
        marked_by     TEXT,
        marg_p        INTEGER,                 -- Marg's amount on the newest export when he said 'self'
        paper_p       INTEGER,                 -- the paper's amount then
        paper_src     TEXT,
        export_md5    TEXT,                    -- that newest bill-wise export
        export_at     TEXT,                    -- its received_at: only LATER exports can clear the bill
        cleared_at    TEXT,
        cleared_how   TEXT,
        PRIMARY KEY(supplier_norm, bill_no, bill_date))""")
    if "bill_id" not in _cols(cx, "amir_self_wait"):
        cx.execute("ALTER TABLE amir_self_wait ADD COLUMN bill_id INTEGER")
    cx.execute(S494_DDL)
    if "reopened_at" not in _cols(cx, "amir_job"):
        cx.execute("ALTER TABLE amir_job ADD COLUMN reopened_at TEXT")
    cx.commit()
    _ENSURED.add(key)


def _table_exists(cx, name):
    return cx.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _setting(cx, key):
    try:
        r = cx.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        v = r[0] if r is not None else None
        return max(0, int(v)) if v not in (None, "") else S444_DEFAULTS[key]
    except Exception:                                                  # noqa: BLE001
        return S444_DEFAULTS[key]


def s444_seed_settings(cx):
    """The seven day/visit counts as setting rows (INSERT OR IGNORE: a value already set is never moved).  Installers call it."""
    n = 0
    for k, v in S444_DEFAULTS.items():
        cur = cx.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, str(v), S444_NOTES[k]))
        n += cur.rowcount or 0
    return n


def _audit(cx, who, action, ref, detail):
    """Every write of this file leaves one purchase_audit row.  A failed audit is said on stderr; the write still commits."""
    try:
        d = dict(detail or {})
        d.setdefault("kit", KIT)
        cx.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                   (_stamp(), who, action, ref, json.dumps(d, sort_keys=True, default=str)))
    except Exception as e:                                             # noqa: BLE001
        print("amir_day: audit %s %s not written: %s" % (action, ref, str(e)[:120]), file=sys.stderr)


def _export_day_sql(p=""):
    """The DAY of a purchase_export row, in SQL, from Marg's own stamp -- one expression, purchase_app's (S533)."""
    import purchase_app                                                # noqa: PLC0415
    return purchase_app.EXPORT_DAY_SQL.format(p=p)


# ==========================================================================================================================================
# state -- READ ONCE PER REQUEST.  No write of this file's own (the callees' own writes on read are theirs: amir_stage's once-only stage
# events, scans_for_amir's rematch, amir_rate_due's mirror).
# ==========================================================================================================================================
class State(object):
    pass


def _export_state(cx, day, wait_since=None):
    """Did today's pair arrive, is each one verified -- and is one still on its way?  (S241 / S243 / S244, kept)

        ok    verified -- arrived, today's stamp, 1st to date
        wait  he has exported and the grace window has not run out yet
        bad   the window ran out, or a file of his DID arrive and is wrong
        none  he has not said he exported yet -- nothing is expected
    `wait_since` is the newest step-3 row: the moment he last said the export was taken.  Each entry carries reason (hi) and
    reason_en (the owner's)."""
    waited = _mins_since(wait_since) if wait_since else None
    within = (waited is not None) and (waited < EXPORT_GRACE_MIN)
    ws = _norm_ts(wait_since) if wait_since else None
    out = []
    if not _table_exists(cx, "purchase_export"):
        for kind, label in PAIR:
            out.append({"kind": kind, "label": label, "have": False, "state": "bad", "waited": waited,
                        "reason": "purchase_export table not present yet", "reason_en": "purchase_export table not present yet"})
        return out
    first = day[:8] + "01"
    for kind, label in PAIR:
        row = cx.execute(
            """SELECT md5, period_from, period_to, export_stamp, n_rows, received_at
                 FROM purchase_export
                WHERE type = ?
                  AND superseded_by IS NULL
                  AND """ + _export_day_sql() + """ = ?
             ORDER BY COALESCE(export_stamp, received_at) DESC
                LIMIT 1""",
            (kind, day),
        ).fetchone()
        if row is None:
            if wait_since is None:
                state, why, en = "none", "abhi nikaali nahi gayi", "not received"
            elif within:
                state, why, en = "wait", "file ban gayi hai, aa rahi hai", "still arriving"
            else:
                state, why, en = "bad", "aaj ki nahi aayi", "today's has not arrived"
            out.append({"kind": kind, "label": label, "have": False, "state": state, "waited": waited, "reason": why, "reason_en": en})
            continue
        d = dict(zip(("md5", "period_from", "period_to", "export_stamp", "n_rows", "received_at"), tuple(row)))
        ok_from = (d.get("period_from") or "")[:10] <= first
        ok_to = (d.get("period_to") or "")[:10] >= day
        if not (ok_from and ok_to):
            arrived = _norm_ts(d.get("export_stamp") or d.get("received_at"))
            fresh = bool(arrived and ws and arrived >= ws)
            if fresh or not within:
                state, why, en = "bad", "tareekh galat hai -- 1 tareekh se aaj tak chahiye", "wrong period -- it must run from the 1st to today"
            else:
                state, why, en = "wait", "file ban gayi hai, aa rahi hai", "still arriving"
            out.append({"kind": kind, "label": label, "have": False, "state": state, "waited": waited, "rows": d.get("n_rows"),
                        "at": _hhmm(d.get("export_stamp") or d.get("received_at")), "reason": why, "reason_en": en})
            continue
        out.append({"kind": kind, "label": label, "have": True, "state": "ok", "waited": waited, "rows": d.get("n_rows"),
                    "period": "%s se %s" % (_ddmmyyyy(d.get("period_from")), _ddmmyyyy(d.get("period_to"))),
                    "period_en": "%s to %s" % (_ddmmyyyy(d.get("period_from")), _ddmmyyyy(d.get("period_to"))),
                    "at": _hhmm(d.get("export_stamp") or d.get("received_at"))})
    return out


def _answers(cx):
    """Every amir_bill_answer row, oldest first, keyed two ways: {bill_id: [rows]} and {(sn, no, date): [rows]} (bill_id NULL only)."""
    by_id, by_triple = {}, {}
    if not _table_exists(cx, "amir_bill_answer"):
        return by_id, by_triple
    for r in cx.execute("SELECT id, bill_id, supplier_norm, bill_no, bill_date, day, reason, by_user, at, note, replaces "
                        "FROM amir_bill_answer ORDER BY id").fetchall():
        a = dict(zip(("id", "bill_id", "supplier_norm", "bill_no", "bill_date", "day", "reason", "by_user", "at", "note", "replaces"), tuple(r)))
        if a["bill_id"] is not None:
            by_id.setdefault(int(a["bill_id"]), []).append(a)
        else:
            by_triple.setdefault((a["supplier_norm"], a["bill_no"], a["bill_date"]), []).append(a)
    return by_id, by_triple


def _newest_answer(ans, bill_id, sn, bno, bdt):
    """The newest answer of one bill: MAX(id) over its rows by bill_id, and the rows with no bill_id that carry its triple."""
    by_id, by_triple = ans
    rows = list(by_id.get(int(bill_id), [])) if bill_id is not None else []
    rows += by_triple.get((sn, bno, bdt), [])
    return max(rows, key=lambda a: a["id"]) if rows else None


def _bills(cx, day, ans):
    """The bills of the base set (DUTY_SQL["amir.bills_answer"]'s inner select without its answer filter) in four states by the newest
    answer: pending (none -- today = first sight today, carry = earlier), waiting (his own 'self'), flagged (not ok), answered (ok, not
    listed).  The pending set is the duty's own SQL; one "since when": purchase_bill.first_seen_day."""
    out = dict(today=[], carry=[], flagged=[], waiting=[], by_id={})
    if not (_table_exists(cx, "purchase_bill") and _table_exists(cx, "purchase_export") and _table_exists(cx, "amir_bill_answer")):
        return out
    try:
        base = [int(r[0]) for r in cx.execute(_BILLS_BASE).fetchall()]
        pending = {int(r[0]) for r in cx.execute(_BILLS_BASE + _BILLS_UNANSWERED).fetchall()}
    except Exception as e:                                             # noqa: BLE001 -- first_seen_day not yet there: said, not hidden
        print("amir_day: the bills could not be read: %s" % str(e)[:160], file=sys.stderr)
        return out
    if not base:
        return out
    rows = {}
    q = ("SELECT b.id, b.supplier_norm, b.bill_no, b.bill_date, b.supplier, b.amount_p, b.bw_amount_p, b.scan_bill_id, b.bw_md5, "
         "COALESCE(b.first_seen_day, " + _export_day_sql("e.") + ") AS first_seen_day, e.export_stamp, e.received_at "
         "FROM purchase_bill b JOIN purchase_export e ON e.md5 = b.bw_md5 WHERE b.id IN (%s)")
    for i in range(0, len(base), 400):
        chunk = base[i:i + 400]
        for r in cx.execute(q % ",".join("?" * len(chunk)), chunk).fetchall():
            d = dict(zip(("id", "supplier_norm", "bill_no", "bill_date", "supplier", "amount_p", "bw_amount_p", "scan_bill_id", "bw_md5",
                          "first_seen_day", "export_stamp", "export_received"), tuple(r)))
            d["marg_p"] = d["bw_amount_p"] if d["bw_amount_p"] is not None else d["amount_p"]
            rows[d["id"]] = d
    for bid, d in rows.items():
        a = _newest_answer(ans, bid, d["supplier_norm"], d["bill_no"], d["bill_date"])
        d["answer"] = a
        if bid in pending:
            (out["today"] if d["first_seen_day"] == day else out["carry"]).append(d)
        elif a and a["reason"] == "self":
            out["waiting"].append(d)
        elif a and a["reason"] != "ok":
            out["flagged"].append(d)
        out["by_id"][bid] = d
    for k in ("today", "carry", "flagged", "waiting"):
        out[k].sort(key=lambda x: ((x.get("bill_date") or ""), (x.get("supplier") or "")), reverse=True)
    for d in out["today"] + out["carry"]:
        d["warn"] = _supplier_warn_s285(cx, d)
        d["twin"] = _twin_bills_s307(cx, d)
    return out


def _scan_links(cx, bill_ids):
    """{bill_id: asset_bill_id} -- purchase_bill.scan_bill_id first, else the newest purchase_scan_link row (S439 / S440's order)."""
    out = {}
    if not bill_ids:
        return out
    try:
        if _table_exists(cx, "purchase_scan_link"):
            ids = list(bill_ids)
            for i in range(0, len(ids), 400):
                chunk = ids[i:i + 400]
                for bid, sid in cx.execute("SELECT bill_id, MAX(asset_bill_id) FROM purchase_scan_link WHERE bill_id IN (%s) GROUP BY bill_id"
                                           % ",".join("?" * len(chunk)), chunk).fetchall():
                    if sid is not None:
                        out[int(bid)] = int(sid)
    except Exception:                                                  # noqa: BLE001
        pass
    return out


def _paper(cx, bills):
    """ONE pass for every listed bill: Marg's amount (its live bill-wise export, with that export's stamp) beside the paper's amount and
    the scan's day.  The paper amount in purchase_scan_state first, else the scan's read total in assets.db -- opened once, read only,
    closed.  Sets b["paper"] = dict(marg_p, export_at, paper_p, scan_day, state ok|diff|noscan|noamount)."""
    if not bills:
        return 0
    links = _scan_links(cx, [b["id"] for b in bills])
    sid_of = {}
    for b in bills:
        sid = b.get("scan_bill_id")
        sid_of[b["id"]] = int(sid) if sid is not None else links.get(b["id"])
    sids = sorted({s for s in sid_of.values() if s is not None})
    paper_amount, scan_info = {}, {}
    opened = 0
    if sids:
        try:
            if "paper_amount" in _cols(cx, "purchase_scan_state"):
                for sid, amt in cx.execute("SELECT asset_bill_id, paper_amount FROM purchase_scan_state WHERE asset_bill_id IN (%s)"
                                           % ",".join("?" * len(sids)), sids).fetchall():
                    if amt is not None:
                        paper_amount[int(sid)] = int(amt)
        except Exception:                                              # noqa: BLE001
            pass
        try:
            import purchase_app                                        # noqa: PLC0415 -- its read-only door to assets.db
            acon = purchase_app._assets_con()
            opened = 1
            if acon is not None:
                try:
                    for r in acon.execute("SELECT id, total_amount, created_at FROM bills WHERE id IN (%s)" % ",".join("?" * len(sids)), sids).fetchall():
                        scan_info[int(r[0])] = (r[1], r[2])
                finally:
                    acon.close()
        except Exception:                                              # noqa: BLE001
            pass
    for b in bills:
        sid = sid_of.get(b["id"])
        marg = b.get("marg_p")
        p = dict(marg_p=marg, export_at=b.get("export_stamp") or b.get("export_received"), paper_p=None, scan_day=None, state="noscan", src=None)
        if sid is not None:
            tot, created = scan_info.get(sid, (None, None))
            p["scan_day"], p["src"] = created, "scan"
            if sid in paper_amount:
                p["paper_p"], p["src"] = paper_amount[sid], "paper"
            elif tot not in (None, ""):
                try:
                    p["paper_p"] = int(round(float(tot) * 100))
                except (TypeError, ValueError):
                    p["paper_p"] = None
            if p["paper_p"] is not None and marg is not None:
                p["state"] = "ok" if abs(int(marg) - int(p["paper_p"])) <= S444_TOL_P else "diff"
            else:
                p["state"] = "noamount"
        b["paper"] = p
    return opened


def _s444_salt(cx):
    """The salt list (rule B, F-839): owed while salt ticks are newer than the newest VERIFIED SALT WISE ITEM LIST by received_at.
    Runs DUTY_SQL["amir.salt_list"]; days / owed_days are Amir's VISIT days since the oldest owed tick (stock_app._s446_visits_since).
    -> dict(pending, ticks, last_list, oldest_tick, days, owed_days, fresh)."""
    out = {"pending": False, "ticks": 0, "last_list": None, "oldest_tick": None, "days": None, "owed_days": None, "fresh": False}
    try:
        r = cx.execute(_SALT_LAST).fetchone()
        out["last_list"] = r[0] if r else None
        r = cx.execute(DUTY_SQL["amir.salt_list"]).fetchone()
        n, since = (int(r[0] or 0), r[1]) if r else (0, None)
        if n:
            visits = 0
            try:
                import stock_app                                       # noqa: PLC0415 -- the one rule for his visits
                visits = len(stock_app._s446_visits_since(cx, since))
            except Exception:                                          # noqa: BLE001
                visits = 0
            out.update(pending=True, ticks=n, oldest_tick=since, days=visits, owed_days=visits)
        else:
            out["fresh"] = bool(out["last_list"])
    except Exception:                                                  # noqa: BLE001
        pass
    return out


def _salt_owner(s):
    """The salt list in the owner's English: (css warn|ok|mut, one line) -- rule B, the same fact as Amir's card."""
    s = s or {}
    if s.get("pending"):
        last = ("last list %s" % _dm_hm(s["last_list"])) if s.get("last_list") else "no list seen yet"
        return "warn", ("Waiting for Marg's SALT WISE ITEM LIST -- %d salt task%s ticked since the last list (%s); owed for %d of Amir's visits."
                        % (int(s.get("ticks") or 0), _plural(s.get("ticks") or 0, "", "s"), last, int(s.get("owed_days") or 0)))
    if s.get("fresh"):
        return "ok", "Salt list arrived %s, after the last salt tick." % _dm_hm(s.get("last_list"))
    return "mut", "No salt tick waiting. No SALT WISE ITEM LIST seen yet."


def _s446_prev_months(n=3):
    t = _now()
    y, mo = t.year, t.month
    out = []
    for _i in range(n):
        mo -= 1
        if mo == 0:
            y, mo = y - 1, 12
        out.append("%04d-%02d" % (y, mo))
    return list(reversed(out))                                 # oldest first


S446_MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")


def _s446_month_name(m):
    try:
        return "%s %s" % (S446_MONTHS[int(m[5:7]) - 1], m[:4])
    except (TypeError, ValueError, IndexError):
        return str(m)


def _s446_packs(cx):
    out = []
    try:
        import packs                                           # noqa: PLC0415 -- READ ONLY: amir_pack(con, month)
        for m in _s446_prev_months(3):
            p = packs.amir_pack(cx, m)
            if p.get("ready") and not p.get("seen"):
                out.append(m)
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _s446_board(st, anchor):
    return "/finance/stock/page/amir?count=%d#%s" % (int((st or {}).get("count_id") or 0), anchor)


def _s494_cat(sp, item, md5=None):
    """Marg's category of an item by its exact name: in one list (its md5), else the newest by as_on. None when there is none."""
    if md5:
        r = sp.q("SELECT value FROM sp_item_fact WHERE fact='category' AND name=? AND source_md5=? LIMIT 1", item, md5)
    else:
        r = sp.q("SELECT value FROM sp_item_fact WHERE fact='category' AND name=? ORDER BY as_on DESC LIMIT 1", item)
    v = str(r[0]["value"] or "").strip() if r else ""
    return v or None


def _s494_label(cx, sp):
    """The orthotic label: the most common newest category among the Orthotics names (the category jobs' items left out); None with
    fewer than ten names carrying one."""
    skip = {r[0] for r in cx.execute("SELECT subject FROM amir_job WHERE kind='category'")}
    count, order = {}, []
    for (nm,) in cx.execute("SELECT item FROM stock_item_section WHERE section='Orthotics' ORDER BY item").fetchall():
        if nm in skip:
            continue
        v = _s494_cat(sp, nm)
        if v:
            if v not in count:
                order.append(v)
            count[v] = count.get(v, 0) + 1
    if sum(count.values()) < 10:
        return None
    return max(order, key=lambda k: (count[k], -order.index(k)))


def _s494_lists(cx, sp):
    """(newest, newest_read): Marg's VERIFIED category lists by received_at -- the newest of all, and the newest the spine has read."""
    out = []
    for md5_, rec, dfrom, dto in cx.execute("SELECT md5, received_at, date_from, date_to FROM mi_file WHERE type=? AND verdict='VERIFIED'",
                                            (S494_CAT_TYPE,)).fetchall():
        at = _norm_ts(rec)
        if at:
            out.append(dict(md5=md5_, at=at, day=(str(dto or "")[:10] or str(dfrom or "")[:10] or at[:10])))
    out.sort(key=lambda x: x["at"], reverse=True)
    newest = out[0] if out else None
    read = None
    for x in out:
        if sp.q("SELECT 1 AS x FROM sp_item_fact WHERE fact='category' AND source_md5=? LIMIT 1", x["md5"]):
            read = x
            break
    return newest, read


def _s494_bank(cx, vendor):
    try:
        return cx.execute("SELECT 1 FROM purchase_vendor_contact WHERE vendor_norm=? AND COALESCE(acct_no,'') <> '' AND COALESCE(ifsc,'') <> ''",
                          (vendor,)).fetchone() is not None
    except Exception:                                          # noqa: BLE001
        return False


def _s494_scanned(cx, vendor):
    try:
        return cx.execute("SELECT 1 FROM purchase_scan_link l JOIN purchase_bill b ON b.id = l.bill_id WHERE b.supplier_norm = ? LIMIT 1",
                          (vendor,)).fetchone() is not None
    except Exception:                                          # noqa: BLE001
        return False


def _s494_read(cx):
    """The jobs, read once: every row not done (for the system's part) and the open ones (his card), the category label and Marg's
    category of each category job's item -- the spine opened once and closed.  dict(rows, jobs, label, newest, read, cat_read, cat_newest)."""
    out = dict(rows=[], jobs=[], label=None, newest=None, read=None, cat_read={}, cat_newest={})
    try:
        rows = [dict(zip(("id", "key", "kind", "subject", "text_hi", "sub_hi", "show_from", "said_at", "said_what", "reopened_at", "done_at", "said"), tuple(r)))
                for r in cx.execute("SELECT id, key, kind, subject, text_hi, sub_hi, show_from, said_at, said_what, reopened_at, done_at, "
                                    "CASE WHEN " + S494_SAID + " THEN 1 ELSE 0 END FROM amir_job ORDER BY id").fetchall()]
        out["rows"] = [r for r in rows if r["done_at"] is None]
        jobs = [r for r in out["rows"] if r["kind"] in S494_KINDS and r["show_from"] is not None and not r["said"]]
        jobs.sort(key=lambda j: (S494_KINDS[j["kind"]], j["id"]))
        cats = [r for r in out["rows"] if r["kind"] == "category"]
        if cats:
            sp = None
            try:
                import stock_watch                             # noqa: PLC0415 -- never spine_read.Spine: it raises when the spine is missing
                sp = stock_watch.Spine()
                if sp.ok:
                    out["label"] = _s494_label(cx, sp)
                    if out["label"]:
                        out["newest"], out["read"] = _s494_lists(cx, sp)
                        for j in cats:
                            out["cat_read"][j["subject"]] = _s494_cat(sp, j["subject"], out["read"]["md5"] if out["read"] else None)
                            if out["newest"]:
                                out["cat_newest"][j["subject"]] = _s494_cat(sp, j["subject"], out["newest"]["md5"])
            finally:
                try:
                    if sp is not None and getattr(sp, "con", None) is not None:
                        sp.con.close()
                except Exception:                              # noqa: BLE001
                    pass
            for j in jobs:
                if j["kind"] == "category":
                    j["label"] = out["label"]
        for j in jobs:
            if j["kind"] == "vendor_bill":
                b = cx.execute("SELECT bill_no, bill_date FROM purchase_bill WHERE supplier_norm=? ORDER BY bill_date DESC, id DESC LIMIT 1",
                               (j["subject"],)).fetchone()
                j["bill"] = (b[0], b[1]) if b else None
        out["jobs"] = jobs
    except Exception:                                          # noqa: BLE001
        pass
    return out


def state(cx, day, who="", step=None, owner=False):
    """Every fact the pages need, read once.  `step` 5 (or an open correction waiting) asks for the paper pass; `owner` adds what only
    the owner's Needs-you reads (the count's open vouchers)."""
    S = State()
    S.day, S.who = day, who or ""
    # ---- the log: the newest row per step of the day; the close and the reopen
    S.log, S.ticks = [], {}
    if _table_exists(cx, "amir_step_log"):
        for r in cx.execute("SELECT id, step, done_at, by_user, note, replaces FROM amir_step_log WHERE day=? ORDER BY id", (day,)).fetchall():
            row = dict(zip(("id", "step", "done_at", "by_user", "note", "replaces"), tuple(r)))
            S.log.append(row)
            S.ticks[int(row["step"])] = row
    t7 = S.ticks.get(7)
    S.closed = dict(at=t7["done_at"], by=t7["by_user"], id=t7["id"]) if (t7 and t7["note"] == "close") else None
    reo = [r for r in S.log if int(r["step"]) == 7 and r["note"] == "reopen"]
    S.reopened = dict(at=reo[-1]["done_at"], by=reo[-1]["by_user"], id=reo[-1]["id"]) if reo else None
    od = cx.execute("SELECT opened_at FROM amir_day WHERE day=?", (day,)).fetchone() if _table_exists(cx, "amir_day") else None
    S.opened_at = od[0] if od else None
    # ---- the pair, and the newest live bill-wise export (the step-2 card's date)
    S.wait_since = (S.ticks.get(3) or {}).get("done_at")
    S.exports = _export_state(cx, day, S.wait_since)
    S.waited_min = _mins_since(S.wait_since) if S.wait_since else None
    S.wait_left_min = max(1, EXPORT_GRACE_MIN - S.waited_min) if S.waited_min is not None else None
    S.export_wait = any(e.get("state") == "wait" for e in S.exports)
    S.export_bad = any(e.get("state") == "bad" for e in S.exports)
    S.export_none = any(e.get("state") == "none" for e in S.exports)
    S.bw_last = None
    try:
        r = cx.execute("SELECT export_stamp, received_at FROM purchase_export WHERE type='BILLWISE' AND superseded_by IS NULL "
                       "ORDER BY received_at DESC LIMIT 1").fetchone()
        S.bw_last = (r[0] or r[1]) if r else None
    except Exception:                                          # noqa: BLE001
        S.bw_last = None
    # ---- purchase.entry_mode (paper | both)
    S.entry_mode = "paper"
    try:
        r = cx.execute("SELECT value FROM setting WHERE key='purchase.entry_mode'").fetchone()
        v = str(r[0]).strip() if r and r[0] else "paper"
        S.entry_mode = v if v in ("paper", "both") else "paper"
    except Exception:                                          # noqa: BLE001
        pass
    # ---- the bills: one base set, four states
    S.answers = _answers(cx)
    S.bills = _bills(cx, day, S.answers)
    S.open_waits = []
    if _table_exists(cx, "amir_self_wait"):
        S.open_waits = [dict(zip(("supplier_norm", "bill_no", "bill_date", "marked_at", "marg_p", "paper_p", "export_md5", "export_at", "bill_id"), tuple(r)))
                        for r in cx.execute("SELECT supplier_norm, bill_no, bill_date, marked_at, marg_p, paper_p, export_md5, export_at, bill_id "
                                            "FROM amir_self_wait WHERE cleared_at IS NULL ORDER BY marked_at").fetchall()]
    S.assets_opened = 0
    if step == 5 or S.open_waits:
        listed = S.bills["today"] + S.bills["carry"] + S.bills["flagged"] + S.bills["waiting"]
        S.assets_opened = _paper(cx, listed)
    # ---- the salt list (rule B), the stage and its words, the card's inputs -- each once
    S.salt = _s444_salt(cx)
    S.stage, S.sw = None, {}
    try:
        import stock_app                                       # noqa: PLC0415
        S.stage = stock_app.amir_stage(cx)
    except Exception:                                          # noqa: BLE001
        S.stage = None
    try:
        import stock_app                                       # noqa: PLC0415
        S.sw = (stock_app._s521_stage_words(cx, S.stage) or {}) if S.stage else {}
    except Exception:                                          # noqa: BLE001
        S.sw = {}
    S.vouchers_open = []
    if owner:
        try:
            import stock_app                                   # noqa: PLC0415
            S.vouchers_open = stock_app.amir_vouchers_open(cx)
        except Exception:                                      # noqa: BLE001
            S.vouchers_open = []
    S.watch = dict(sunday=False, fixes=0, bill_pending=[])
    try:
        import stock_watch                                     # noqa: PLC0415
        v = stock_watch.amir_view(cx)
        if v.get("ok"):
            S.watch = dict(sunday=((v.get("plan") or {}).get("status") == "open"), fixes=len(v.get("fixes") or []),
                           bill_pending=list(v.get("bill_pending") or []))
    except Exception:                                          # noqa: BLE001
        pass
    S.scans, S.held, S.scans_ok = [], [], False
    try:
        import purchase_app                                    # noqa: PLC0415
        r = purchase_app.scans_for_amir(cx)
        S.scans, S.held, S.scans_ok = list(r.get("list") or []), list(r.get("held") or []), bool(r.get("ok"))
    except Exception:                                          # noqa: BLE001
        pass
    S.rates = []
    try:
        import stock_app                                       # noqa: PLC0415
        S.rates = stock_app.amir_rate_due(cx) or []
    except Exception:                                          # noqa: BLE001
        S.rates = []
    S.packs = _s446_packs(cx)
    S.neft_ok = {}
    try:
        import supplier_msg                                    # noqa: PLC0415
        S.neft_ok = {m: bool(supplier_msg.s452_neft_confirmed(cx, m)) for m in _s446_prev_months(3)}
    except Exception:                                          # noqa: BLE001
        pass
    S.jobs = _s494_read(cx) if _table_exists(cx, "amir_job") else dict(rows=[], jobs=[], label=None, newest=None, read=None, cat_read={}, cat_newest={})
    S.notes = []
    _derive(S)
    return S


# ==========================================================================================================================================
# the derivation -- the card, the gate, the extras: one place, two sides (hi for Amir, en for the owner)
# ==========================================================================================================================================
def _card_rows(S):
    """The card's rows in order, each (kind, hi_html, en_text, his_line): the stage lines, the Sunday and the fixes, D712's scan line,
    the rates, the one-time jobs, the packs.  `his_line` marks his Marg work (the step-6 gate)."""
    rows = []
    st = S.stage
    sw = S.sw or {}
    if st:
        for ln in sw.get("lines") or []:
            if ln.get("anchor"):
                rows.append(("stage", "<div class=line><a class=btn href='%s'>%s</a></div>" % (_esc(_s446_board(st, ln["anchor"])), _esc(ln.get("hi") or "")),
                             ln.get("hi") or "", True))
            else:
                rows.append(("stage", "<div class=line><span class=big>%s</span></div>" % _esc(ln.get("hi") or ""), ln.get("hi") or "", False))
    if S.watch.get("sunday"):
        rows.append(("sunday", "<div class=line><a class='btn plain' href='%s'>Poori ginti ka Sunday chuniye &mdash; kholiye</a></div>" % _esc(_s446_board(st, "rest")),
                     "the full count's Sunday to pick", True))
    if S.watch.get("fixes"):
        rows.append(("fixes", "<div class=line><a class='btn plain' href='%s'>Stock ke sudhar: %d &mdash; kholiye</a></div>" % (_esc(_s446_board(st, "rest")), int(S.watch["fixes"])),
                     "stock fixes: %d" % int(S.watch["fixes"]), True))
    if S.scans:                                                # D712: the scans reception made that Marg's purchase export does not carry
        rows.append(("scans", "<div class=line><a class='btn plain' href='/finance/amir/step/2#scans'>Scan hua bill Marg mein baaki: %d &mdash; kholiye</a></div>" % len(S.scans),
                     "scanned bills not yet in Marg: %d" % len(S.scans), True))
    if S.rates:
        rows.append(("rates", "<div class=line><a class='btn plain' href='%s'>%d item ka rate Marg mein daalna hai &mdash; kholiye</a></div>" % (_esc(_s446_board(st, "rates")), len(S.rates)),
                     "selling rates to put in Marg: %d" % len(S.rates), True))
    for h in _s494_lines(S.jobs.get("jobs") or []):
        rows.append(("jobs", h, "one-time Marg jobs: %d" % len(S.jobs.get("jobs") or []), True))
    for m in S.packs or []:
        rows.append(("packs", "<div class=line><span class=big>Mahine ka pack &mdash; %s</span>%s"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/yes'>Yes Bank Sanjeevni statement (PDF)</a></p>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/icici'>ICICI Sanjeevni statement (PDF)</a></p>"
                     "<form method=post action='/finance/amir/pack/%s/seen'><button class=btn name=go value=1>Dekh liya</button></form></div>"
                     % (_esc(_s446_month_name(m)),
                        ("<p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (PDF)</a></p>" % m) if (S.neft_ok or {}).get(m) else "",
                        m, m, m), "", False))
    return rows


def _derive(S):
    S.card = _card_rows(S)
    S.card_has_his_line = any(r[3] for r in S.card)
    b = S.bills
    S.done = {
        1: 1 in S.ticks,
        2: 2 in S.ticks,
        3: 3 in S.ticks,
        4: all(e["have"] for e in S.exports),                 # proven, never ticked
        5: (not b["today"]) and (not b["carry"]),
        6: (6 in S.ticks) or (not S.card_has_his_line),
        7: S.closed is not None,
    }
    gate = []
    if not S.done[2]:
        gate.append((2, "Bill daalne ki pushti baaki hai", "bills not confirmed entered"))
    for e in S.exports:
        if e["have"]:
            continue
        if e.get("state") == "wait":
            gate.append((4, "%s abhi aa rahi hai" % e["label"], "%s still arriving" % e["label"]))
        elif e.get("state") == "none":
            gate.append((4, "%s abhi nikaali nahi gayi" % e["label"], "%s not received" % e["label"]))
        else:
            gate.append((4, "%s mein dikkat hai: %s — phir se nikaaliye" % (e["label"], e.get("reason") or ""),
                         "%s bad: %s" % (e["label"], e.get("reason_en") or e.get("reason") or "")))
    n = len(b["today"]) + len(b["carry"])
    if n:
        gate.append((5, "%d bill par tap baaki hai" % n, "%d bill%s still to tap" % (n, _plural(n, "", "s"))))
    if not S.done[6]:
        gate.append((6, "Marg sudhar: 'Aaj ke item theek kar diye' dabana baaki", "Marg corrections not confirmed"))
    S.gate_open = gate
    extra = []
    if S.salt.get("pending"):
        extra.append(("SALT WISE ITEM LIST nahi aayi", "SALT WISE ITEM LIST not received"))
    if S.stage and (S.sw or {}).get("card_hi") and (S.sw or {}).get("owner_en"):
        extra.append((S.sw["card_hi"], S.sw["owner_en"]))
    if b["flagged"]:
        extra.append(("Flag kiye hue bill: %d" % len(b["flagged"]), "flagged bills: %d" % len(b["flagged"])))
    if b["waiting"]:
        extra.append(("Aapki sudhaar ka intezaar: %d" % len(b["waiting"]), "his corrections awaiting Marg: %d" % len(b["waiting"])))
    S.extra = extra


def _next_step(S):
    for n, _label in STEPS:
        if n == 7:
            continue
        if n == 4 and S.export_wait and not S.done.get(4):   # S244: a report in transit never parks him on step 4
            continue
        if not S.done.get(n):
            return n
    return 7


def _ready_to_close(S):
    return all(S.done.get(n) for n in GATE_STEPS)


def owner_state_line(S):
    """The owner's state line for the day: (head, second line or '')."""
    if S.closed:
        head = "CLOSED at %s" % _hhmm(S.closed["at"])
    elif S.gate_open:
        head = "OPEN — holding: " + "; ".join(g[2] for g in S.gate_open)
    else:
        head = "OPEN — ready to close"
    if S.reopened:
        head += " (reopened %s by %s)" % (_hhmm(S.reopened["at"]), S.reopened["by"] or "?")
    second = ("not holding: " + "; ".join(x[1] for x in S.extra)) if S.extra else ""
    return head, second


# ==========================================================================================================================================
# settle -- the ONLY writes of this file on a read (Amir's GETs and Needs-you; never the owner's day or the visit summary).  One commit.
# ==========================================================================================================================================
def _bill_row(cx, bill_id, sn, bno, bdt):
    cols = ("id", "supplier_norm", "bill_no", "bill_date", "supplier", "amount_p", "bw_amount_p", "bw_md5", "scan_bill_id")
    r = None
    if bill_id is not None:
        r = cx.execute("SELECT %s FROM purchase_bill WHERE id=?" % ", ".join(cols), (int(bill_id),)).fetchone()
    if r is None and sn is not None:
        r = cx.execute("SELECT %s FROM purchase_bill WHERE supplier_norm=? AND bill_no=? AND bill_date=? ORDER BY id DESC LIMIT 1" % ", ".join(cols),
                       (sn, bno, bdt)).fetchone()
    if r is None:
        return None
    d = dict(zip(cols, tuple(r)))
    d["marg_p"] = d["bw_amount_p"] if d["bw_amount_p"] is not None else d["amount_p"]
    return d


def _export_row(cx, md5):
    if not md5:
        return None
    r = cx.execute("SELECT md5, received_at, export_stamp, superseded_by FROM purchase_export WHERE md5=?", (md5,)).fetchone()
    return dict(zip(("md5", "received_at", "export_stamp", "superseded_by"), tuple(r))) if r else None


def _self_clear(cx, S, notes):
    """His 'Meri entry galat thi' waits clear THEMSELVES, judged only on exports received LATER than the one he flagged:
      (i)   the bill's live bill-wise export carries the paper's amount (+-Rs 1)          -> marg_matches, a system 'ok' row
      (i-b) no paper amount known and that export's amount differs from the one he flagged -> marg_changed, a system 'ok' row
      (ii)  the export the bill names has been superseded (Marg no longer lists the bill)  -> left_export, a system 'ok' row
      (iii) his own newest answer is no longer 'self'                                      -> 'answered <reason>', no system row
    His row is never touched: a system row replaces it.  Returns the count cleared."""
    n = 0
    for w in list(S.open_waits):
        sn, bno, bdt = w["supplier_norm"], w["bill_no"], w["bill_date"]
        b = _bill_row(cx, w.get("bill_id"), sn, bno, bdt)
        bid = b["id"] if b else w.get("bill_id")
        a = _newest_answer(S.answers, bid, sn, bno, bdt)
        if not a or a["reason"] != "self":
            how = "answered %s" % ((a or {}).get("reason") or "-")
            cx.execute("UPDATE amir_self_wait SET cleared_at=?, cleared_how=? WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND cleared_at IS NULL",
                       (_stamp(), how, sn, bno, bdt))
            _audit(cx, "system", "amir_self_cleared", "%s|%s|%s" % (sn, bno, bdt), {"how": how, "bill_id": bid})
            S.open_waits.remove(w)
            n += 1
            continue
        if not b:
            continue
        ex_at = _norm_ts(w.get("export_at")) or ""
        e = _export_row(cx, b["bw_md5"])
        if not e:
            continue
        how, note, said = None, None, None
        if e["superseded_by"]:
            sup = _export_row(cx, e["superseded_by"])
            if sup and (_norm_ts(sup["received_at"]) or "") > ex_at:
                how, note = "left_export", "auto: the bill left the live export"
                said = "%s bill %s — Marg ki nayi export mein yeh bill nahi hai; aapka 'galat thi' clear ho gaya &#10003;"
        elif (_norm_ts(e["received_at"]) or "") > ex_at:
            m = b["marg_p"]
            listed = S.bills["by_id"].get(b["id"]) or {}
            paper = (listed.get("paper") or {}).get("paper_p")
            if paper is None:
                paper = w.get("paper_p")
            if paper is not None:
                if m is not None and abs(int(m) - int(paper)) <= S444_TOL_P:
                    how, note = "marg_matches", "auto: Marg carries the paper amount"
            elif m is not None and w.get("marg_p") is not None and int(m) != int(w["marg_p"]):
                how, note = "marg_changed", "auto: Marg's amount changed"
            if how:
                said = "%s bill %s — Marg mein ab theek, aapka 'galat thi' clear ho gaya &#10003;"
        if not how:
            continue
        now = _stamp()
        cx.execute("UPDATE amir_self_wait SET cleared_at=?, cleared_how=? WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND cleared_at IS NULL",
                   (now, how, sn, bno, bdt))
        cx.execute("INSERT INTO amir_bill_answer (bill_id, supplier_norm, bill_no, bill_date, day, reason, by_user, at, note, replaces) "
                   "VALUES (?,?,?,?,?,?,?,?,?,?)", (b["id"], b["supplier_norm"], b["bill_no"], b["bill_date"], S.day, "ok", "system", now, note, a["id"]))
        _audit(cx, "system", "amir_self_cleared", "%s|%s|%s" % (sn, bno, bdt),
               {"how": how, "bill_id": b["id"], "marg_p": b["marg_p"], "flagged_marg_p": w.get("marg_p"), "export": e["md5"], "replaces": a["id"]})
        S.open_waits.remove(w)
        S.bills["waiting"] = [x for x in S.bills["waiting"] if x["id"] != b["id"]]
        notes.append(said % (_esc(b.get("supplier") or sn), _esc(bno)))
        n += 1
    return n


def _s494_refresh(cx, S):
    """The system's part of the one-time jobs (S494 4.3), on what state() read: the category rows come onto his card with his rename
    list (stage B / C / done); Marg's newest category list read by the spine proves them -- or brings one back (reopened_at, his
    words kept) when it still shows another category; a vendor's row is done once its bank details are on record or a scan is linked.
    Every change audited."""
    n = 0
    J = S.jobs or {}
    rows = J.get("rows") or []
    if not rows:
        return 0
    now = _stamp()
    cats = [r for r in rows if r["kind"] == "category"]
    if cats:
        if any(r["show_from"] is None for r in cats) and S.stage and S.stage.get("stage") in ("B", "C", "done"):
            for r in cats:
                if r["show_from"] is None:
                    k = cx.execute("UPDATE amir_job SET show_from=? WHERE id=? AND show_from IS NULL AND done_at IS NULL", (now, r["id"])).rowcount or 0
                    if k:
                        _audit(cx, "system", "job_shown", r["key"], {"with": "the rename list"})
                    n += k
        label, newest, read = J.get("label"), J.get("newest"), J.get("read")
        if label:
            for r in cats:
                cat = (J.get("cat_read") or {}).get(r["subject"])
                if cat is not None and cat.upper() == label.upper():
                    k = cx.execute("UPDATE amir_job SET done_at=?, done_how='seen in Marg' WHERE id=? AND done_at IS NULL", (now, r["id"])).rowcount or 0
                    if k:
                        _audit(cx, "system", "job_done", r["key"], {"how": "seen in Marg", "category": cat})
                    n += k
                    continue
                if r["said"] and newest and read and newest["md5"] == read["md5"] and newest["at"] > (_norm_ts(r["said_at"]) or ""):
                    if cat is not None:                        # that list shows it under another category: back on his card
                        k = cx.execute("UPDATE amir_job SET reopened_at=? WHERE id=?", (now, r["id"])).rowcount or 0
                        if k:
                            _audit(cx, "system", "job_reopened", r["key"], {"category": cat, "list": newest["md5"]})
                        n += k
    for r in rows:
        if r["kind"] != "vendor_bill":
            continue
        how = "bank details on record" if _s494_bank(cx, r["subject"]) else ("scan linked" if _s494_scanned(cx, r["subject"]) else None)
        if how:
            k = cx.execute("UPDATE amir_job SET done_at=?, done_how=? WHERE id=? AND done_at IS NULL", (now, how, r["id"])).rowcount or 0
            if k:
                _audit(cx, "system", "job_done", r["key"], {"how": how})
            n += k
    return n


def _returns_basis(cx):
    """The owner's returns rule kept as setting returns.pending_ok = '<n>|<oldest yyyy-mm-dd>' (S454 12), re-made only when its input
    stamp moves (charter 4).  The stamp, setting returns.pending_ok_basis: the six months joined with ',' + '|' + the count of notes
    returns_kinds.month_notes gives over them + '|' + the newest of their `date` and `approval.decided_at`.  Returns 1 when re-made."""
    try:
        import returns_kinds                                   # noqa: PLC0415
        t = _now().date()
        y, m = t.year, t.month
        months = []
        for _i in range(6):
            months.append("%04d-%02d" % (y, m))
            m -= 1
            if m == 0:
                y, m = y - 1, 12
        months = list(reversed(months))
        per = {ym: returns_kinds.month_notes(cx, "medical", ym) for ym in months}
        notes = [x for ym in months for x in per[ym]]
        newest = max([str(x.get("date") or "") for x in notes] + [str((x.get("approval") or {}).get("decided_at") or "") for x in notes] + [""])
        basis = "%s|%d|%s" % (",".join(months), len(notes), newest)
        r = cx.execute("SELECT value FROM setting WHERE key='returns.pending_ok_basis'").fetchone()
        have = cx.execute("SELECT value FROM setting WHERE key='returns.pending_ok'").fetchone()
        if r is not None and r[0] == basis and have is not None:
            return 0
        n, dates = 0, []
        for ym in months:
            s = returns_kinds.enrich(cx, "medical", ym, per[ym], with_prev=False)
            n += int(s.get("pending_ok") or 0)
            dates += [str(x.get("date"))[:10] for x in per[ym] if x.get("pending_ok") and x.get("date")]
        cx.execute("INSERT INTO setting (key, value, note) VALUES ('returns.pending_ok', ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                   ("%d|%s" % (n, min(dates) if dates else ""), "S454 (12): the owner's returns rule's own count, kept for the duty map (manoj.returns_ok)"))
        cx.execute("INSERT INTO setting (key, value, note) VALUES ('returns.pending_ok_basis', ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                   (basis, "S533: what returns.pending_ok was made from -- re-made only when this moves (charter 4)"))
        _audit(cx, "system", "returns_pending_ok", "returns.pending_ok", {"value": "%d|%s" % (n, min(dates) if dates else ""), "basis": basis})
        return 1
    except Exception as e:                                     # noqa: BLE001
        print("amir_day: returns.pending_ok not re-made: %s" % str(e)[:160], file=sys.stderr)
        return 0


def settle(cx, S, needs_you=False):
    """The GET-time writes, in order: (1) his corrections cleared, (2) the jobs proved, (3) the returns count (Needs-you only).
    One commit; nothing written when there is nothing to settle.  Returns the notes the page prints (one per thing settled)."""
    notes = []
    try:
        _self_clear(cx, S, notes)
        _s494_refresh(cx, S)
        if needs_you:
            _returns_basis(cx)
        cx.commit()
    except Exception as e:                                     # noqa: BLE001
        print("amir_day: settle failed: %s" % str(e)[:200], file=sys.stderr)
        try:
            cx.rollback()
        except Exception:                                      # noqa: BLE001
            pass
    S.notes = notes
    _derive(S)
    return notes


# ==========================================================================================================================================
# rendering
# ==========================================================================================================================================
_CSS = """
:root{--ink:#1b1b1b;--soft:#6b6b6b;--line:#e3e3e3;--ok:#137333;--warn:#8a6d00;
      --bad:#a50e0e;--bg:#fafafa;--accent:#12457a}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif}
.wrap{max-width:720px;margin:0 auto;padding:14px}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:17px;margin:0 0 10px}
p{margin:0 0 10px}
.sub{color:var(--soft);font-size:14px;margin:0 0 14px}
.card{background:#fff;border:1px solid var(--line);border-radius:10px;
      padding:14px;margin:0 0 14px}
.steps{display:flex;gap:6px;margin:0 0 14px;flex-wrap:wrap}
.steps span,.steps a{flex:1 1 auto;min-width:38px;text-align:center;font-size:12px;
            padding:6px 4px;border-radius:8px;border:1px solid var(--line);
            background:#fff;color:var(--soft);text-decoration:none;display:block}
.steps .on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.steps .ok{background:#e7f3e9;border-color:#bfe0c6;color:var(--ok)}
.steps .wait{background:#fff8e1;border-color:#f0e0a8;color:var(--warn)}
.band{background:#fff8e1;border:1px solid #f0e0a8;border-radius:10px;padding:11px 12px;
      margin:0 0 14px;font-size:15px}
.band a{color:var(--accent)}
.dates{background:#f3f7fb;border:1px solid #cfe0ef;border-radius:10px;padding:12px;
       margin:10px 0 0}
.dates .d{font-size:21px;font-weight:700;letter-spacing:.5px}
.btn{display:block;width:100%;padding:14px 18px;font-size:17px;font-weight:600;
     border-radius:10px;border:1px solid var(--accent);background:var(--accent);
     color:#fff;text-align:center;text-decoration:none;cursor:pointer;margin:0 0 10px}
.btn.plain{background:#fff;color:var(--accent)}
.btn.quiet{background:#fff;color:var(--soft);border-color:var(--line);font-weight:400;font-size:15px}
.good,.ok{color:var(--ok)}
.bad{color:var(--bad)}
.warn{color:var(--warn)}
.mut{color:var(--soft)}
.line{padding:10px 0;border-bottom:1px solid var(--line)}
.line:last-child{border-bottom:0}
.big{font-size:17px;font-weight:600}
.bill{border:1px solid var(--line);border-radius:10px;padding:12px;margin:0 0 12px}
.bill .who{font-weight:600}
.bill .meta{color:var(--soft);font-size:14px;margin:2px 0 10px}
.bill .tap{display:block;padding:15px 13px;border:1px solid #bfe0c6;border-radius:10px;
           background:#f2f9f4;color:var(--ok);font-size:17px;font-weight:600;margin:0 0 8px}
.bill .tap input{margin-right:11px;transform:scale(1.35);vertical-align:-2px}
.bill .swarn{margin:0 0 8px;padding:11px 13px;border:1px solid #f0c36d;border-radius:10px;
            background:#fff8e6;color:#6b4e00;font-size:15px;line-height:1.45}
.bill details.notok{border:1px solid var(--line);border-radius:10px;background:#fff}
.bill details.notok summary{padding:15px 13px;font-size:17px;font-weight:600;
            color:var(--bad);cursor:pointer;list-style:none}
.bill details.notok summary::-webkit-details-marker{display:none}
.bill details.notok summary::after{content:" \25BE";color:var(--soft);float:right}
.bill details.notok[open] summary{border-bottom:1px solid var(--line)}
.bill details.notok[open] summary::after{content:" \25B4"}
.why{padding:4px 13px 13px}
.why label{display:block;padding:13px 11px;border:1px solid var(--line);border-radius:8px;
           margin:9px 0 0;font-size:16px}
.why input{margin-right:10px;transform:scale(1.3);vertical-align:-2px}
.bill .was{background:#fff8e1;border:1px solid #f0e0a8;border-radius:8px;
           padding:9px 11px;margin:0 0 10px;font-size:14px;color:var(--warn)}
.bill:has(input:checked){border-color:var(--ok);box-shadow:0 0 0 1px var(--ok) inset}
.bill:has(details input:checked){border-color:var(--bad);box-shadow:0 0 0 1px var(--bad) inset}
.savebar{position:sticky;bottom:0;background:var(--bg);padding:10px 0 4px;
         border-top:1px solid var(--line);margin:14px 0 0}
.savebar .btn{margin:0}
.note{background:#fff8e1;border:1px solid #f0e0a8;border-radius:10px;padding:12px;margin:0 0 14px}
.settled{background:#e7f3e9;border:1px solid #bfe0c6;border-radius:10px;padding:10px 12px;margin:0 0 14px;color:var(--ok)}
.tscroll{overflow-x:auto;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th{color:var(--soft);font-weight:600}
.foot{color:var(--soft);font-size:13px;margin:16px 0 0;text-align:center}
details.visit{background:#fff;border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:0 0 14px}
details.visit summary{cursor:pointer;font-weight:600;font-size:17px}
details.visit .k{color:var(--soft);font-size:13px}
"""


def _shell(title, body, head_extra=""):
    return ("<!doctype html><html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "%s<title>%s</title><style>%s</style></head><body><div class=wrap>%s"
            "</div></body></html>" % (head_extra, _esc(title), _CSS, body))


def _banner(current, S):
    out = ["<div class=steps>"]
    for n, label in STEPS:
        if n == current:
            cls = "on"
        elif S.done.get(n):
            cls = "ok"
        elif n == 4 and S.export_wait:
            cls = "wait"
        else:
            cls = ""
        out.append("<a class='%s' href='/finance/amir/step/%d'>%d<br>%s</a>" % (cls, n, n, _esc(label)))
    out.append("</div>")
    return "".join(out)


def _neft_card_s407():
    """S407 (D623): the NEFT line on every step while an event is live (supplier_msg); fail-soft: his day never waits for it."""
    try:
        import supplier_msg                                        # noqa: PLC0415
        return supplier_msg.amir_card(_db())
    except Exception:                                              # noqa: BLE001
        return ""


def row_marg_sudhar(S, top=True):
    """THE card: its rows from _card_rows, printed once.  The heading only while it holds a line of his Marg work."""
    if not S.card:
        return ""
    head = "<h2 class=bad>Marg sudhar &mdash; abhi baaki</h2>" if (top and S.card_has_his_line) else ""
    style = "border:2px solid var(--bad)" if S.card_has_his_line else ""
    return "<div class=card id=s444duty style='%s'>%s%s</div>" % (style, head, "".join(r[1] for r in S.card))


def _notes_html(S):
    if not S.notes:
        return ""
    return "".join("<div class=settled>%s</div>" % n for n in S.notes)


def _page(step, S, title, body, subtitle="", head_extra=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    who = ("<p class=sub style='text-align:right;margin:0 0 6px'>Signed in: %s</p>" % _esc(S.who)) if S.who else ""
    card = row_marg_sudhar(S, top=True) if step != 6 else ""
    return _shell("Amir -- kaam", who + _banner(step, S) + card + _notes_html(S) + head + body + _neft_card_s407()
                  + "<p class=foot>Step %d of 7 &middot; <a href='/portal?all=1'>Sab tiles</a></p>" % step, head_extra)


def _export_band(S):
    """One amber line on the later steps while the pair is not settled -- never blocks."""
    if S.done.get(4):
        return ""
    if S.export_bad:
        return "<div class=band><a href='/finance/amir/step/4'>Ek report dobara nikaalni hai &mdash; kholiye</a></div>"
    if S.export_wait:
        return ("<div class=band>Report abhi ban rahi hai -- file ka intezaar hai. "
                "<a href='/finance/amir/step/4'>Dekhiye</a></div>")
    return ""


def _denied():
    return _shell("Nahin khul saka",
                  "<div class=card><h2>Yeh page aapke liye nahin hai</h2>"
                  "<p>Apne login se kholiye, ya doctor sahab ko bataiye.</p>"
                  "</div>"), 403


def _go(step):
    return redirect(url_for("amir_day.step", n=step), code=303)


# ---- the steps: each only PLACES rows ----
def _step1(S):
    body = ("<div class=card><p class=big>Sabse pehle biometric punch kar lijiye.</p>"
            "<p>Punch ho gaya ho to neeche daba dijiye. Kaam yahin se shuru hoga.</p>"
            "<form method=post><input type=hidden name=tick value=1><input type=hidden name=punch value=yes>"
            "<button class=btn name=go value=1>Punch ho gaya</button></form>"
            "<form method=post><input type=hidden name=tick value=1><input type=hidden name=punch value=no>"
            "<button class='btn quiet' name=go value=1>Punch nahi ho paya -- aage badhiye</button>"
            "</form></div>"
            "<p class=sub>Punch na hone se kaam nahi rukta. Aapka jawab yahin likha jaata hai.</p>")
    return _page(1, S, "Punch", body)


def _scan_line(b):
    bd = ("bill %s" % _ddmmyyyy(b["bill_date"])) if b.get("bill_date") else "bill ki tareekh scan par saaf nahi"
    return ("<div class=line><span class=big>%s</span> <span class=sub>%s &middot; scan: %s, %s &middot; %s</span><br>"
            "<a class='btn plain' href='/finance/purchase/api/scan-file/%d'>Download</a></div>"
            % (_esc(b.get("stamp")), _esc(b.get("supplier")), _esc(b.get("scan_ddmm")), _esc(b.get("who") or "?"), _esc(bd), int(b["id"])))


def _step2_scans(S):
    """Step 2's scan card, both modes, id=scans (the card's D712 door lands here): the scans reception made that the newest live
    bill-wise export does not carry -- the same list as the card's count."""
    bills = S.scans
    today = [b for b in bills if b.get("today")]
    when = ("Marg ki aakhri purchase export (%s) mein nahi the" % _dm_hm(S.bw_last)) if S.bw_last else "Marg ki purchase export mein nahi the"
    zipl = ("<p><a class=btn href='/finance/purchase/api/scan-files/today.zip'>Aaj ke sab (%d) &mdash; ek zip</a></p>" % len(today)) if today else ""
    rows = "".join(_scan_line(b) for b in bills)
    if S.entry_mode == "paper":
        return ("<div class=card id=scans><h2>Scan ho chuke bill (%d)</h2>"
                "<p class=sub>Reception ne jo bill scan kiye hain aur %s, woh yahan dikhenge. Aap apne register se jaise daalte hain, "
                "waise hi daaliye. Chahein to bill ki file yahan se le sakte hain.</p>%s%s</div>" % (len(bills), _esc(when), zipl, rows))
    held = S.held
    if not bills and not held:
        return ""
    grey = ("<p class=sub id=s452held style='color:#777'>%d scan reception ke paas hain &mdash; abhi Marg mein nahi daalne</p>" % len(held)) if held else ""
    return ("<div class=card id=scans><h2>Marg mein daalne ke bill (%d)</h2>"
            "<p class=sub>Sirf woh scan jo %s. Marg ki digital entry mein upload kijiye &mdash; Marg ki entry hi "
            "bill ki asli entry hai. Marg ki export aate hi bill yahan se khud hat jayega.</p>%s%s%s</div>"
            % (len(bills), _esc(when), zipl, rows, grey))


def _step2(S):
    body = ("<div class=card><p class=big>Saare purchase aur purchase-return bill "
            "Marg mein daal dijiye -- bilkul jaisa bill par chhapa hai.</p>"
            "<p>Kuch theek mat kijiye, kuch chhodiye mat, kam maal aaya ho to bhi "
            "bill jaisa hai waisa hi daaliye. Kami agli screen par batayenge.</p>"
            "<form method=post><input type=hidden name=tick value=2>"
            "<button class=btn name=go value=2>Sab bill daal diye</button></form></div>")
    return _page(2, S, "Bill entry", _step2_scans(S) + body, "Yahi ek niyam hai jis par baaki sab tika hai.")


def _dates_block(S):
    """The two dates he must type into Marg, spelled out (S244; the owner's call: kept as values)."""
    return ("<div class=dates><div class=sub>Marg mein yeh do tareekh daaliye:</div>"
            "<div class=line>FROM &nbsp; <span class=d>%s</span></div>"
            "<div class=line>TO &nbsp;&nbsp;&nbsp;&nbsp; <span class=d>%s</span> "
            "<span class=sub>(aaj)</span></div></div>"
            % (_esc(_ddmmyyyy(_month_first(S.day))), _esc(_ddmmyyyy(S.day))))


def _step3(S):
    rows = "".join("<div class=line><span class=big>%d. %s</span><br>"
                   "<span class=sub>1 tareekh se aaj tak</span></div>"
                   % (i + 1, _esc(label)) for i, (_k, label) in enumerate(PAIR))
    body = ("<div class=card><h2>Do report nikaaliye</h2>%s%s</div>"
            "<div class=note>Counter par bikri shuru hone se pehle. Der ho jaye to "
            "bhi nikaal dijiye -- chhodiye mat.<br>"
            "<b>TO ki tareekh aaj ki honi chahiye</b> -- kal ki nahi.</div>"
            "<form method=post><input type=hidden name=tick value=3>"
            "<button class=btn name=go value=3>Dono report nikaal di</button>"
            "</form>" % (rows, _dates_block(S)))
    return _page(3, S, "Export", body)


def _step4(S):
    """Four heads: wait, bad, none, ok -- never a green tick over a red report (A5)."""
    waiting = S.export_wait
    bad = [e for e in S.exports if e.get("state") == "bad"]
    notyet = [e for e in S.exports if e.get("state") == "none"]
    out = []
    for e in S.exports:
        st = e.get("state") or ("ok" if e.get("have") else "bad")
        if st == "ok":
            out.append("<div class=line><span class='big good'>%s &#10003;</span><br>"
                       "<span class=sub>%s &middot; %s line &middot; %s baje</span></div>"
                       % (_esc(e["label"]), _esc(e.get("period", "")), _esc(e.get("rows", "")), _esc(e.get("at", ""))))
        elif st == "wait":
            out.append("<div class=line><span class='big warn'>%s &hellip;</span><br>"
                       "<span class=sub>File abhi aa rahi hai.</span></div>" % _esc(e["label"]))
        elif st == "none":
            out.append("<div class=line><span class=big>%s</span><br>"
                       "<span class=sub>Abhi nikaali nahi gayi.</span></div>" % _esc(e["label"]))
        else:
            out.append("<div class=line><span class='big bad'>%s &#10007;</span><br>"
                       "<span class=sub>%s</span></div>" % (_esc(e["label"]), _esc(e.get("reason", ""))))
    if waiting:
        head = ("<div class=card><h2 class=warn>Report aa rahi hai &mdash; %d min</h2>"
                "<p class=big>File abhi aa rahi hai.</p>"
                "<p>Aapko kuch nahi karna hai -- yeh screen khud dekhti rahegi.</p></div>" % int(S.wait_left_min or 1))
    elif bad:
        head = ("<div class=card><h2 class=bad>%s</h2></div>"
                % "<br>".join(_esc("%s mein dikkat hai: %s — phir se nikaaliye" % (e["label"], e.get("reason") or "")) for e in bad))
    elif notyet:
        head = ("<div class=card><h2>Abhi report nikaali nahi gayi</h2>"
                "<p>Pehle dono report nikaal dijiye.</p>"
                "<p><a class='btn plain' href='/finance/amir/step/3'>Report nikaalne ka tarika</a></p></div>")
    else:
        head = ("<div class=card><h2 class=good>Dono report mil gayi &#10003;</h2>"
                "<p>File aa gayi, padh li gayi. Aapse kuch nahi poochha gaya.</p></div>")
    body = head + "<div class=card><h2>Do report</h2>%s</div>" % "".join(out)
    if all(e["have"] for e in S.exports):
        body += ("<form method=post><input type=hidden name=skip value=1>"
                 "<button class=btn name=go value=4>Aage badhiye</button></form>")
    elif waiting:
        body += ("<form method=post><input type=hidden name=skip value=1>"
                 "<button class=btn name=go value=4>Aage ka kaam shuru kijiye</button></form>"
                 "<form method=post><button class='btn quiet' name=go value=4>Abhi dobara dekhiye</button></form>"
                 "<p class=sub>Report aate hi yeh khud &#10003; ho jayegi. Aap apna agla kaam kar sakte hain.</p>")
    elif bad:
        names = " aur ".join(_esc(e["label"]) for e in bad)
        body += ("<div class=note><p class=big>Dobara banaiye: %s</p>"
                 "<p><b>Marg mein report ki file band kijiye, phir nikaaliye</b> -- Marg file tab tak "
                 "dobara nahi likh sakta jab tak wo khuli hai.</p>%s</div>"
                 "<form method=post><input type=hidden name=again value=1>"
                 "<button class=btn name=go value=4>Dobara banai -- phir se dekhiye</button></form>"
                 "<form method=post><input type=hidden name=skip value=1>"
                 "<button class='btn quiet' name=go value=4>Aage ka kaam shuru kijiye</button></form>"
                 % (names, _dates_block(S)))
    refresh = ("<meta http-equiv=refresh content='%d'>" % EXPORT_POLL_SEC) if waiting else ""
    return _page(4, S, "Report", body, "Aapse nahi poochha ja raha. File khud padhi jaati hai.", head_extra=refresh)


def _paper_line(b):
    """Marg (export dd-mm hh:mm): Rs X · Kaagaz (scan dd-mm): Rs Y · mil gaya / farq / not read / no scan -- each figure with its date."""
    p = b.get("paper") or {}
    if not p:
        return ""
    marg = "Marg (export %s): &#8377;%s" % (_esc(_dm_hm(p.get("export_at"))), _esc(_rupees(p.get("marg_p"))))
    if p["state"] == "noscan":
        return "<div class=meta>%s &middot; <span class=sub>scan nahi hua</span></div>" % marg
    paper = ("&#8377;%s" % _esc(_rupees(p["paper_p"]))) if p.get("paper_p") is not None else "&mdash;"
    kag = "Kaagaz (scan %s): %s" % (_esc(_dm_hm(p.get("scan_day"), time=False) or "-"), paper)
    if p["state"] == "ok":
        tail = "<b class=good>mil gaya &#10003;</b>"
    elif p["state"] == "diff":
        tail = "<b class=bad>farq &#8377;%s</b>" % _esc(_rupees(abs(int(p["marg_p"]) - int(p["paper_p"]))))
    else:
        tail = "<span class=sub>scan mein rakam nahi padhi</span>"
    return "<div class=meta>%s &middot; %s &middot; %s</div>" % (marg, kag, tail)


def _bill_block(i, b, kind):
    """One bill, one tap (S245): 'Theek hai', or 'Theek nahi' and a reason inside a <details> -- no JavaScript.  The hidden key carries
    the bill's id and its triple."""
    key = "%d|%s|%s|%s" % (int(b["id"]), b["supplier_norm"], b["bill_no"], b["bill_date"])
    why = "".join("<label><input type=radio name='r_%d' value='%s'>%s</label>" % (i, _esc(code), _esc(label))
                  for code, label in REASONS if code != "ok")
    was = ""
    a = b.get("answer")
    if a and kind in ("flagged", "waiting"):
        when = _dm_hm(a.get("at"))
        was = ("<div class=was>Aapne likha tha: <b>%s</b>%s</div>"
               % (_esc(REASON_MAP.get(a["reason"], a["reason"])), (" &middot; %s" % _esc(when)) if when else ""))
    if kind == "waiting":
        was += ("<div class=was>Marg ki agli export ka intezaar &mdash; Marg mein sahi rakam aate hi yeh khud hat jayega. "
                "Na hate to <b>Theek hai</b> dabaiye.</div>")
    sup = b.get("supplier") or b.get("supplier_norm")
    for item, usual, n in (b.get("warn") or []):
        was += ("<div class=swarn>&#9888; <b>%s</b>: yeh item pehle <b>%s</b> se aata tha (%d bill); is bill mein <b>%s</b> hai.</div>"
                % (_esc(item), _esc(usual), int(n), _esc(sup)))
    for other, amt, same in (b.get("twin") or []):
        if same:
            was += ("<div class=swarn>&#9888; Bill %s %s ka ek aur <b>%s</b> ke naam bhi hai (&#8377;%s).</div>"
                    % (_esc(b["bill_no"]), _esc(_ddmmyyyy(b["bill_date"])), _esc(other), _esc(_rupees(amt))))
        else:
            was += ("<div class=swarn>&#9888; Bill %s %s ka ek aur <b>%s</b> ke naam bhi hai (&#8377;%s), alag rakam.</div>"
                    % (_esc(b["bill_no"]), _esc(_ddmmyyyy(b["bill_date"])), _esc(other), _esc(_rupees(amt))))
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s%s"
            "<input type=hidden name='k_%d' value='%s'>"
            "<label class=tap><input type=radio name='r_%d' value='ok'>%s</label>"
            "<details class=notok><summary>Theek nahi</summary>"
            "<div class=why>%s</div></details></div>"
            % (_esc(sup), _esc(b["bill_no"]), _esc(_ddmmyyyy(b["bill_date"])), _esc(_rupees(b.get("amount_p"))),
               _paper_line(b), was, i, _esc(key), i, _esc(REASON_MAP["ok"]), why))


def _bill_counts_hi(S):
    b = S.bills
    return "Aaj aaye bill: %d &middot; Pichhle dinon ke baaki: %d &middot; Flag kiye hue: %d" % (len(b["today"]), len(b["carry"]), len(b["flagged"]))


def _step5(S):
    b = S.bills
    pend = b["carry"] + b["today"]
    if not pend and not b["flagged"] and not b["waiting"]:
        return _page(5, S, "Bills", _export_band(S) + "<div class=card><p class='big good'>Koi bill baaki nahi hai.</p>"
                     "<p class=sub>%s</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye</button></form>" % _bill_counts_hi(S))
    body = [_export_band(S), "<div class=note id=billcounts>%s</div>" % _bill_counts_hi(S), "<form method=post>"]
    i = 0
    for x in pend:
        body.append(_bill_block(i, x, "pending"))
        i += 1
    if b["flagged"]:
        body.append("<div class=card><h2>Flag kiye hue bill -- %d</h2>"
                    "<p class=sub>Flag kiya hua bill tab tak yahin rahega jab tak Marg mein theek na ho; theek hone par Theek hai.</p></div>" % len(b["flagged"]))
        for x in b["flagged"]:
            body.append(_bill_block(i, x, "flagged"))
            i += 1
    if b["waiting"]:
        body.append("<div class=card><h2>Aapki sudhaar &mdash; Marg ki agli export ka intezaar: %d</h2></div>" % len(b["waiting"]))
        for x in b["waiting"]:
            body.append(_bill_block(i, x, "waiting"))
            i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<div class=savebar><button class=btn name=go value=5>Save kijiye</button>")
    if not pend:
        body.append("<button class='btn quiet' name=go value=5>Aage badhiye</button>")
    body.append("</div></form>")
    if pend:
        sub = "%d bill. Har bill par ek tap. Kuch gadbad ho to hi 'Theek nahi' kholiye." % len(pend)
    else:
        sub = "Aaj ke sab bill ho gaye. Neeche sirf flag kiye hue aur aapki sudhaar wale bill hain."
    return _page(5, S, "Aaj ke bill", "".join(body), sub)


def _s444_salt_card(w, close=False):
    """The salt list's one card (rule B) -- from w["s444"]["salt"] (amir_salts builds that `w` by hand; the shape stays)."""
    s = (w.get("s444") or {}).get("salt") or {}
    if not s.get("pending"):
        return ""
    last = ("aakhri list %s ki" % _dm_hm(s["last_list"])) if s.get("last_list") else "abhi tak koi list nahi aayi"
    v = int(s.get("days") or 0)
    owed = ("list aapki %d visit se nahi aayi" % v) if v else "list aaj ke tick ke baad nahi aayi"
    return ("<div class=card id=s444salt style='border:2px solid var(--bad);background:#fff4f4'>"
            "<p class='big bad'>Ek export aur: SALT WISE ITEM LIST</p>"
            "<p>Marg se SALT WISE ITEM LIST nikaalo &mdash; yahan khud tick ho jayegi. Text ya Excel, dono chalte hain.</p>"
            "<p class=sub>%d salt kaam tick hue, %s &middot; %s.</p>%s</div>"
            % (int(s.get("ticks") or 0), _esc(owed), _esc(last),
               ("<p class=sub><b>Nahi nikli to Shavez subah nikaalega.</b> Din band karne se nahi rukta.</p>" if close else "")))


def _salt_card(S, close=False):
    return _s444_salt_card({"s444": {"salt": S.salt}}, close=close)


def _step6(S, salts_open):
    body = _export_band(S)
    if S.card_has_his_line:
        body += ("<h2 class=bad>Marg sudhar &mdash; abhi baaki</h2>" + row_marg_sudhar(S, top=False) +
                 "<form method=post><input type=hidden name=tick value=6>"
                 "<button class=btn name=go value=6>Aaj ke item theek kar diye</button></form>")
    else:
        body += row_marg_sudhar(S, top=False) + "<div class=card><p class='big good'>Aaj Marg mein sudhaar ka kuch nahi hai &#10003;</p></div>"
    if salts_open:
        body += ("<div class=card id=saltsdoor><h2>Salt aur naye item: list kholiye, Marg mein sudhaar kijiye, tick lagaiye</h2>"
                 "<p><a class=btn href='/finance/amir/salts'>Salt ki list &mdash; kholiye</a></p></div>")
    body += _salt_card(S)
    body += ("<div class=note>Aaj ke bill wale item hi zaroori hain. Poori purani list "
             "aaj khatam karna zaroori nahi.</div>")
    return _page(6, S, "Marg sudhar", body)


def _summary(S):
    got = [e["label"] for e in S.exports if e["have"]]
    rows = ["<div class=line>Dono report: <b>%s</b></div>" % ("mil gayi" if len(got) == len(PAIR) else "%d / %d" % (len(got), len(PAIR)))]
    rows.append("<div class=line>%s</div>" % _bill_counts_hi(S))
    if S.bills["waiting"]:
        rows.append("<div class=line>Aapki sudhaar ka intezaar: <b>%d</b> <span class=sub>(din band karne se nahi rukta)</span></div>" % len(S.bills["waiting"]))
    rows.append("<div class=line>Marg sudhar: <b>%s</b></div>" % ("ho gaya" if S.done.get(6) else "baaki"))
    if S.salt.get("fresh"):
        rows.append("<div class=line>SALT WISE ITEM LIST: <b class=good>aa gayi &#10003;</b> %s</div>" % _esc(_dm_hm(S.salt.get("last_list"))))
    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>%s" % ("".join(rows), _salt_card(S, close=True))


def _step7(S):
    if S.closed:
        body = ("<div class=card><h2 class=good>DIN BAND &#10003;</h2>"
                "<p>%s baje band kiya.</p>" % _esc(_hhmm(S.closed["at"])))
        if S.reopened:
            body += "<p class=sub>Isse pehle %s baje dobara khola gaya tha.</p>" % _esc(_hhmm(S.reopened["at"]))
        body += "</div>"
        waiting = len(S.bills["today"]) + len(S.bills["carry"])
        if waiting:
            body += ("<div class=note><a href='/finance/amir/step/5'><b>%d naya bill aa gaya hai</b> &mdash; kholiye</a></div>" % waiting)
        body += _summary(S)
        nflag = len(S.bills["flagged"])
        body += ("<div class=card><h2>Kuch aur karna hai?</h2>"
                 "<p><a class='btn plain' href='/finance/amir/step/5'>Bill dekhiye" + ((" -- %d flag" % nflag) if nflag else "") + "</a></p>"
                 "<p><a class='btn plain' href='/finance/amir/step/6'>Salt aur naam</a></p>"
                 "<p><a class='btn plain' href='/finance/amir/step/4'>Report</a></p>"
                 "</div>"
                 "<form method=post><input type=hidden name=reopen value=1>"
                 "<button class='btn quiet' name=go value=7>Din phir se kholiye</button></form>")
        return _page(7, S, "Din band", body)
    if not _ready_to_close(S):
        body = "<div class=card id=gateopen><h2>Abhi kuch baaki hai</h2><ul>"
        for g in S.gate_open or [(0, "Kuch step abhi baaki hain", "")]:
            body += "<li>%s</li>" % _esc(g[1])
        body += "</ul>" + "".join("<p>%s <span class=sub>(din band karne se nahi rukta)</span></p>" % _esc(x[0]) for x in S.extra)
        body += "<p class=sub id=billcounts>%s</p>" % _bill_counts_hi(S)
        body += ("<p class=sub>Aaj ka din khula rehta hai. Jo ho gaya hai wo "
                 "bacha hua hai -- dobara nahi karna padega.</p></div>"
                 "<p><a class=btn href='/finance/amir'>Jahan chhoda tha wahan se</a></p>")
        body += _salt_card(S, close=True)
        return _page(7, S, "Abhi baaki", body)
    body = _summary(S)
    if S.extra:
        body += "<div class=card>%s</div>" % "".join("<p>%s <span class=sub>(din band karne se nahi rukta)</span></p>" % _esc(x[0]) for x in S.extra)
    body += "<form method=post><button class=btn name=go value=7>Din band kijiye</button></form>"
    return _page(7, S, "Din band karein?", body)


# ==========================================================================================================================================
# writes -- append, or an audited UPDATE of a system record.  Never a delete.
# ==========================================================================================================================================
def tick(cx, S, step, user, note=None):
    """One row per tap.  `replaces` = the newest row of that step today (a re-tick)."""
    now = _stamp()
    cx.execute("INSERT OR IGNORE INTO amir_day (day, opened_at) VALUES (?,?)", (S.day, now))
    prev = cx.execute("SELECT MAX(id) FROM amir_step_log WHERE day=? AND step=?", (S.day, int(step))).fetchone()[0]
    cur = cx.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note, replaces) VALUES (?,?,?,?,?,?)",
                     (S.day, int(step), now, user, note, prev))
    _audit(cx, user, "amir_step_log", "%s|%d" % (S.day, int(step)), {"note": note, "row": cur.lastrowid, "replaces": prev})
    return cur.lastrowid


def _settle_claims(cx, sn, bno, bdt, outcome, who):
    n = 0
    for (cid, amt) in cx.execute("SELECT id, amount_p FROM amir_claim WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND state <> 'settled'",
                                 (sn, bno, bdt)).fetchall():
        cx.execute("UPDATE amir_claim SET state='settled', settled_outcome=?, settled_at=?, settled_by=? WHERE id=?", (outcome, _stamp(), who, cid))
        _audit(cx, who, "amir_claim_settled", "%s|%s|%s" % (sn, bno, bdt), {"claim": cid, "amount_p": amt, "outcome": outcome})
        n += 1
    return n


def save_bills(cx, S, user, form):
    """One amir_bill_answer row per answered radio; `replaces` = the bill's previous newest row.  'self' also opens the wait record
    (s444_mark_self); 'ok' settles a claim open on the bill; a claim reason raises one for Darpan when none is open."""
    try:
        n = int(form.get("n") or 0)
    except (TypeError, ValueError):
        n = 0
    written = 0
    for i in range(min(n, 2000)):
        key = form.get("k_%d" % i) or ""
        reason = (form.get("r_%d" % i) or "").strip()
        if reason not in REASON_MAP or key.count("|") < 3:
            continue
        sid, rest = key.split("|", 1)
        parts = rest.rsplit("|", 2)
        if len(parts) != 3:
            continue
        sn, bno, bdt = parts
        try:
            bid = int(sid)
        except ValueError:
            bid = None
        b = _bill_row(cx, bid, None, None, None) if bid is not None else None
        if b is None:
            b = _bill_row(cx, None, sn, bno, bdt)
        if b is not None:
            bid, sn, bno, bdt = b["id"], b["supplier_norm"], b["bill_no"], b["bill_date"]
        prev = cx.execute("SELECT MAX(id) FROM amir_bill_answer WHERE bill_id=? OR (bill_id IS NULL AND supplier_norm=? AND bill_no=? AND bill_date=?)",
                          (bid if bid is not None else -1, sn, bno, bdt)).fetchone()[0]
        now = _stamp()
        cur = cx.execute("INSERT INTO amir_bill_answer (bill_id, supplier_norm, bill_no, bill_date, day, reason, by_user, at, note, replaces) "
                         "VALUES (?,?,?,?,?,?,?,?,NULL,?)", (bid, sn, bno, bdt, S.day, reason, user, now, prev))
        _audit(cx, user, "amir_bill_answer", "%s|%s|%s" % (sn, bno, bdt), {"reason": reason, "bill_id": bid, "row": cur.lastrowid, "replaces": prev})
        written += 1
        if reason == "self":
            s444_mark_self(cx, sn, bno, bdt, user, bill_id=bid)
        if reason == "ok":
            _settle_claims(cx, sn, bno, bdt, "amir_ok", user)
        if reason in CLAIM_REASONS:
            already = cx.execute("SELECT 1 FROM amir_claim WHERE supplier_norm=? AND bill_no=? AND bill_date=? AND state <> 'settled'",
                                 (sn, bno, bdt)).fetchone()
            if not already:
                cur = cx.execute("INSERT INTO amir_claim (supplier, supplier_norm, bill_no, bill_date, amount_p, reason, raised_by, raised_at, state) "
                                 "VALUES (?,?,?,?,?,?,?,?,'open')",
                                 (((b or {}).get("supplier") or sn), sn, bno, bdt, (b or {}).get("amount_p"), reason, user, now))
                _audit(cx, user, "amir_claim_raised", "%s|%s|%s" % (sn, bno, bdt), {"claim": cur.lastrowid, "reason": reason})
    return written


def s444_mark_self(cx, supplier_norm, bill_no, bill_date, who, settled_by=None, bill_id=None):
    """His own slip, corrected in Marg: the bill waits for Marg's next export (amir_self_wait, a system record re-armed on a second
    'self'), and any claim open on it for Darpan is settled as 'amir_own_entry'.  Returns the claims settled."""
    ensure(cx)
    b = _bill_row(cx, bill_id, supplier_norm, bill_no, bill_date)
    marg_p, md5, ex_at = None, None, ""
    if b:
        marg_p, md5 = b["marg_p"], b["bw_md5"]
        e = _export_row(cx, md5)
        ex_at = (e or {}).get("received_at") or ""
    paper, src = None, None
    if b:
        x = dict(b, export_stamp=None, export_received=ex_at)
        _paper(cx, [x])
        paper = (x.get("paper") or {}).get("paper_p")
        src = (x.get("paper") or {}).get("src")
    cx.execute("INSERT INTO amir_self_wait (supplier_norm, bill_no, bill_date, marked_at, marked_by, marg_p, paper_p, paper_src, export_md5, export_at, "
               "cleared_at, cleared_how, bill_id) VALUES (?,?,?,?,?,?,?,?,?,?,NULL,NULL,?) "
               "ON CONFLICT(supplier_norm, bill_no, bill_date) DO UPDATE SET marked_at=excluded.marked_at, marked_by=excluded.marked_by, "
               "marg_p=excluded.marg_p, paper_p=excluded.paper_p, paper_src=excluded.paper_src, export_md5=excluded.export_md5, "
               "export_at=excluded.export_at, bill_id=excluded.bill_id, cleared_at=NULL, cleared_how=NULL",
               (supplier_norm, bill_no, bill_date, _stamp(), who, marg_p, paper, src, md5, ex_at, (b or {}).get("id", bill_id)))
    n = _settle_claims(cx, supplier_norm, bill_no, bill_date, "amir_own_entry", settled_by or who)
    _audit(cx, who, "amir_self", "%s|%s|%s" % (supplier_norm, bill_no, bill_date),
           {"marg_p": marg_p, "paper_p": paper, "paper_src": src, "claims_settled": n, "bill_id": (b or {}).get("id", bill_id)})
    return n


def close(cx, S, user):
    """Din band -- once: refused while closed or not ready (a second tap writes nothing)."""
    if S.closed is not None or not _ready_to_close(S):
        return None
    t7 = S.ticks.get(7)
    now = _stamp()
    cx.execute("INSERT OR IGNORE INTO amir_day (day, opened_at) VALUES (?,?)", (S.day, now))
    cur = cx.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note, replaces) VALUES (?,7,?,?,'close',?)",
                     (S.day, now, user, t7["id"] if t7 else None))
    _audit(cx, user, "amir_day_close", S.day, {"row": cur.lastrowid})
    return cur.lastrowid


def reopen(cx, S, user):
    """Din phir se kholiye -- recorded, never erased: a 'reopen' row that replaces the close row."""
    if S.closed is None:
        return None
    cur = cx.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note, replaces) VALUES (?,7,?,?,'reopen',?)",
                     (S.day, _stamp(), user, S.closed["id"]))
    _audit(cx, user, "amir_day_reopen", S.day, {"row": cur.lastrowid, "replaces": S.closed["id"]})
    return cur.lastrowid


def _s494_tap(cx, who, val):
    """A tap on his card (S494 4.5): 'cat' (every shown, open category row), 'scan:<id>' / 'nf:<id>' (a vendor_bill row), 'tap:<id>'
    (a tap row).  A row not shown, not open, of another kind, or not a number changes nothing.  One audit row per row changed."""
    try:
        val = str(val or "").strip()
        now = _stamp()
        if val == "cat":
            hit = [(r[0], r[1], "done") for r in cx.execute("SELECT id, key FROM amir_job WHERE kind='category' AND " + S494_OPEN).fetchall()]
        else:
            m = re.match(r"^(scan|nf|tap):(\d{1,9})$", val)
            if not m:
                return 0
            kind = "tap" if m.group(1) == "tap" else "vendor_bill"
            r = cx.execute("SELECT id, key FROM amir_job WHERE id=? AND kind=? AND " + S494_OPEN, (int(m.group(2)), kind)).fetchone()
            hit = [(r[0], r[1], "not_found" if m.group(1) == "nf" else "done")] if r else []
        for jid, key, what in hit:
            if val.startswith("tap:"):
                cx.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what=?, done_at=?, done_how='tap' WHERE id=?", (now, who, what, now, jid))
            else:
                cx.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what=? WHERE id=?", (now, who, what, jid))
            _audit(cx, who, "job", key, {"tapped": val, "said": what})
        if hit:
            cx.commit()
        return len(hit)
    except Exception:                                          # noqa: BLE001
        try:
            cx.rollback()
        except Exception:                                      # noqa: BLE001
            pass
        return 0


def _s494_lines(jobs):
    """The card's job lines (the owner's approved words, S494 4.4) under 'Ek baar ke kaam'.  The category job's words read the ONE
    label the system proves them by; when no label can be read, the words say so (never a typed category)."""
    if not jobs:
        return []
    out = ["<div class=line id=s494jobs><span class=sub><b>Ek baar ke kaam</b></span></div>"]
    cats = [j for j in jobs if j["kind"] == "category"]
    if cats:
        lab = (cats[0].get("label") or "").strip()
        if lab:
            head = (("In %d item ki category Marg mein '%s' kijiye" % (len(cats), lab)) if len(cats) > 1
                    else "Is item ki category Marg mein '%s' kijiye" % lab)
        else:
            head = (("In %d item ki category Marg mein daaliye — poora naam board par hai" % len(cats)) if len(cats) > 1
                    else "Is item ki category Marg mein daaliye — poora naam board par hai")
        out.append("<div class=line><span class=big>%s</span><br><span class=sub>%s</span>"
                   "<form method=post><input type=hidden name=job value=cat><button class=btn>Kar diya</button></form></div>"
                   % (_esc(head), _esc(" · ".join(j["subject"] for j in cats))))
    vs = [j for j in jobs if j["kind"] == "vendor_bill"]
    if vs:
        head = (("In %d vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye" % len(vs)) if len(vs) > 1
                else "Is vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye")
        out.append("<div class=line><span class=big>%s</span><br><span class=sub>Bill nikaal kar reception (Alisha / Shivani) se scan karwaiye.</span></div>"
                   % _esc(head))
        for j in vs:
            b = j.get("bill")
            t = ("%s — bill %s (%s)" % (j["subject"], b[0], _ddmmyyyy(b[1]))) if b else j["subject"]
            out.append("<div class=line><span class=big>%s</span>"
                       "<form method=post><input type=hidden name=job value='scan:%d'><button class='btn plain'>Scan ho gaya</button></form>"
                       "<form method=post><input type=hidden name=job value='nf:%d'><button class='btn quiet'>Bill nahi mila</button></form></div>"
                       % (_esc(t), j["id"], j["id"]))
    for j in jobs:
        if j["kind"] != "tap":
            continue
        out.append("<div class=line><span class=big>%s</span>%s"
                   "<form method=post><input type=hidden name=job value='tap:%d'><button class=btn>Kar diya</button></form></div>"
                   % (_esc(j.get("text_hi") or j["subject"]), ("<br><span class=sub>%s</span>" % _esc(j["sub_hi"])) if j.get("sub_hi") else "", j["id"]))
    return out


# ==========================================================================================================================================
# routes
# ==========================================================================================================================================
def _who(u):
    return str((u or {}).get("username") or (u or {}).get("user") or "")


@bp.route("/finance/amir")
def home():
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    ensure(cx)
    S = state(cx, _today(), _who(u))
    settle(cx, S)
    return _go(_next_step(S))


@bp.route("/finance/amir/step/<int:n>", methods=["GET", "POST"])
def step(n):
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    if n < 1 or n > 7:
        return _go(1)
    cx = _db()
    ensure(cx)
    day = _today()
    user = _who(u)
    if request.method == "POST":
        f = request.form
        if f.get("job"):                                       # S494: a one-time job tapped on his card -- FIRST, for every step
            _s494_tap(cx, user, f.get("job"))
            return _go(n)
        S = state(cx, day, user)
        if n == 5:
            save_bills(cx, S, user, f)
        elif n == 7:
            if f.get("reopen"):
                if reopen(cx, S, user):
                    cx.commit()
                    return _go(_next_step(state(cx, day, user)))
            else:
                close(cx, S, user)
        elif n == 4:
            # Nothing on step 4 is ever a claim that a report arrived -- the server alone decides that.  "Dobara banai" restarts the
            # transit clock (a new step-3 row, the first kept); "Aage ka kaam" / "Aage badhiye" move him on.
            if f.get("again"):
                tick(cx, S, 3, user, "again")
            cx.commit()
            if f.get("skip"):
                return _go(5)
            return _go(4)
        else:
            t = f.get("tick")
            if t and t.isdigit() and int(t) == n:
                note = None
                if n == 1:
                    note = {"yes": "punched", "no": "no_punch"}.get(str(f.get("punch") or ""))
                elif n == 3:
                    note = "export"
                tick(cx, S, n, user, note)
        cx.commit()
        if n == 3:
            return _go(4)                                      # he has just said the export was taken: the transit screen once
        S2 = state(cx, day, user)
        if n == 7 and S2.closed:
            return _go(7)
        nxt = _next_step(S2)
        return _go(nxt if nxt >= n else n + 1 if n < 7 else 7)
    S = state(cx, day, user, step=n)
    settle(cx, S)
    if n == 6:
        salts_open = False
        try:
            import amir_salts                                  # noqa: PLC0415
            salts_open = bool(amir_salts._open_tasks(cx))
        except Exception:                                      # noqa: BLE001
            salts_open = False
        return _step6(S, salts_open)
    return {1: _step1, 2: _step2, 3: _step3, 4: _step4, 5: _step5, 7: _step7}[n](S)


@bp.route("/finance/amir/day")
def owner_day():
    """The owner's view of the same day, in English.  Reads; writes nothing."""
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    ensure(cx)
    day = (request.args.get("d") or _today())[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        day = _today()
    S = state(cx, day, _who(u))
    rows = []
    for e in S.exports:
        rows.append("<tr><td>%s</td><td class='%s'>%s</td><td>%s</td><td>%s</td></tr>"
                    % (_esc(e["label"]), "good" if e["have"] else "bad", "verified" if e["have"] else _esc(e.get("reason_en") or "not verified"),
                       _esc(e.get("rows", "")), _esc(e.get("at", ""))))
    head, second = owner_state_line(S)
    oc = cx.execute("SELECT COUNT(*), COALESCE(SUM(amount_p),0), MIN(raised_at) FROM amir_claim WHERE state <> 'settled'").fetchone()
    b = S.bills
    body = ("<div class=card><h2>Amir -- %s</h2><p class=big id=daystate>%s</p>%s</div>"
            "<div class=card><h2>The daily pair</h2><div class=tscroll><table>"
            "<tr><th>report</th><th>state</th><th>rows</th><th>when</th></tr>%s</table></div></div>"
            "<div class=card><h2>Bills</h2>"
            "<div class=line>Today's bills, still to tap: <b>%d</b></div>"
            "<div class=line>Carried from earlier days: <b>%d</b></div>"
            "<div class=line>Flagged: <b>%d</b></div>"
            "<div class=line>His corrections awaiting Marg: <b>%d</b></div></div>"
            "<div class=card><h2>Claims for Darpan</h2>"
            "<div class=line>Open: <b>%d</b>, worth &#8377;%s</div>"
            "<div class=line>Oldest raised: <b>%s</b></div></div>"
            % (_esc(_ddmmyyyy(day)), _esc(head), ("<p class=sub id=daynothold>%s</p>" % _esc(second)) if second else "", "".join(rows),
               len(b["today"]), len(b["carry"]), len(b["flagged"]), len(b["waiting"]),
               int(oc[0] or 0), _rupees(oc[1] or 0), _esc(_dm_hm(oc[2]) if oc[2] else "-")))
    cls, line = _salt_owner(S.salt)
    body += "<div class=card id=s444salt><h2>Salt list from Marg</h2><p class='big %s'>%s</p></div>" % (cls, _esc(line))
    body += _visit_details_html(_visit_summary(cx, S))
    return _shell("Amir's day", body)


def _visit_summary(cx, S):
    """Everything the owner reads about one visit, JSON-safe, from the same S (one verdict per step 1-7)."""
    day = S.day
    nxt = _next_step(S)
    closed = S.closed is not None
    ticks = S.ticks
    # ---- bills he tapped that day: his own rows (never the system's), the newest per bill
    mine = {}
    if _table_exists(cx, "amir_bill_answer"):
        for r in cx.execute("SELECT id, bill_id, supplier_norm, bill_no, bill_date, reason FROM amir_bill_answer "
                            "WHERE day=? AND COALESCE(by_user,'') <> 'system' ORDER BY id", (day,)).fetchall():
            k = ("id", r[1]) if r[1] is not None else ("t", r[2], r[3], r[4])
            mine[k] = r[5]
    by_reason = {}
    for reason in mine.values():
        x = by_reason.setdefault(reason, {"label": REASON_MAP.get(reason, reason), "n": 0})
        x["n"] += 1
    tapped = sum(v["n"] for v in by_reason.values())
    remaining = len(S.bills["today"]) + len(S.bills["carry"])
    bills_line = ", ".join("%s %d" % (v["label"], v["n"]) for _k, v in sorted(by_reason.items())) or "none"
    # ---- purchase reports the server received that day
    reports = []
    if _table_exists(cx, "purchase_export"):
        for r in cx.execute("SELECT type, n_rows, grand_amount_p, export_stamp, received_at, period_from, period_to FROM purchase_export "
                            "WHERE superseded_by IS NULL AND " + _export_day_sql() + " = ? ORDER BY COALESCE(export_stamp, received_at)", (day,)).fetchall():
            d = dict(zip(("type", "n_rows", "grand_amount_p", "export_stamp", "received_at", "period_from", "period_to"), tuple(r)))
            reports.append({"type": d["type"], "rows": d["n_rows"], "amount_p": d["grand_amount_p"],
                            "amount": _rupees(d["grand_amount_p"]) if d["grand_amount_p"] is not None else "",
                            "at": _hhmm(d["export_stamp"] or d["received_at"]),
                            "period": "%s to %s" % (_ddmmyyyy(d["period_from"]), _ddmmyyyy(d["period_to"]))})
    bw = [r for r in reports if r["type"] == "BILLWISE"]
    rep_bills = bw[-1]["rows"] if bw else None
    rep_amount_p = bw[-1]["amount_p"] if bw and bw[-1]["amount_p"] is not None else None
    reports_line = ("; ".join("%s %s rows%s at %s" % (r["type"], r["rows"] if r["rows"] is not None else "?",
                                                     (" Rs %s" % r["amount"]) if r["amount"] else "", r["at"]) for r in reports) or "none received")
    # ---- salt work
    by_section, ticked_by = {}, []
    if _table_exists(cx, "purchase_salt_task"):
        for sec, by, at in cx.execute("SELECT section, done_by, done_at FROM purchase_salt_task WHERE COALESCE(done, 0) = 1 AND done_at IS NOT NULL").fetchall():
            t = _norm_ts(at)
            if t and t[:10] == day:
                by_section[sec] = by_section.get(sec, 0) + 1
                if by and by not in ticked_by:
                    ticked_by.append(by)
    salt_ticked = sum(by_section.values())
    uploads = {"n": 0, "ticked": 0}
    if _table_exists(cx, "amir_salt_upload"):
        r = cx.execute("SELECT COUNT(*), COALESCE(SUM(ticked), 0) FROM amir_salt_upload WHERE substr(uploaded_at, 1, 10) = ?", (day,)).fetchone()
        uploads = {"n": int(r[0] or 0), "ticked": int(r[1] or 0)}
    salts_line = ("renames %d, new salts %d, salt changes %d, cleanup %d; %d sheet upload%s"
                  % (by_section.get("rename", 0), by_section.get("create", 0), by_section.get("change", 0),
                     by_section.get("cleanup", 0), uploads["n"], _plural(uploads["n"], "", "s")))
    # ---- claims he raised
    claims_by, claims_n, claims_p = {}, 0, 0
    for reason, n, v in cx.execute("SELECT reason, COUNT(*), COALESCE(SUM(amount_p), 0) FROM amir_claim WHERE substr(raised_at, 1, 10) = ? "
                                   "GROUP BY reason", (day,)).fetchall():
        claims_by[reason] = {"label": REASON_MAP.get(reason, reason), "n": int(n), "amount_p": int(v or 0)}
        claims_n += int(n)
        claims_p += int(v or 0)

    # ---- one verdict per step
    def tick_note(n):
        t = ticks.get(n) or {}
        who = (" by %s" % t["by_user"]) if t.get("by_user") else ""
        return "%s%s" % (_hhmm(t.get("done_at")), who)

    def tap_step(n, label, skipped_note):
        if n in ticks:
            return {"n": n, "label": label, "state": "done", "note": tick_note(n)}
        if closed or nxt > n:
            return {"n": n, "label": label, "state": "skipped", "note": skipped_note}
        return {"n": n, "label": label, "state": "not yet", "note": ""}

    s1 = tap_step(1, "Punch", "no tap")
    if 1 in ticks and ticks[1].get("note") == "punched":
        s1["note"] = "punched -- " + tick_note(1)
    elif 1 in ticks and ticks[1].get("note") == "no_punch":
        s1.update(state="not done", note="no punch -- he tapped 'Punch nahi ho paya' " + tick_note(1))
    steps = [s1, tap_step(2, "Bill entry", "no 'all bills entered' tap")]
    have_all = all(e["have"] for e in S.exports)
    if 3 in ticks:
        steps.append({"n": 3, "label": "Export", "state": "done", "note": tick_note(3)})
    elif have_all:
        steps.append({"n": 3, "label": "Export", "state": "done", "note": "both reports arrived; the tap itself was not made"})
    elif closed or nxt > 3:
        steps.append({"n": 3, "label": "Export", "state": "skipped", "note": "no export tap"})
    else:
        steps.append({"n": 3, "label": "Export", "state": "not yet", "note": ""})
    if have_all:
        steps.append({"n": 4, "label": "Check", "state": "done",
                      "note": "; ".join("%s %s rows at %s" % (e["label"], e.get("rows", ""), e.get("at", "")) for e in S.exports)})
    else:
        steps.append({"n": 4, "label": "Check", "state": "not done", "note": "; ".join(g[2] for g in S.gate_open if g[0] == 4)})
    counts = "today %d, carried %d, flagged %d, his corrections %d" % (len(S.bills["today"]), len(S.bills["carry"]), len(S.bills["flagged"]), len(S.bills["waiting"]))
    if remaining == 0 and tapped == 0:
        steps.append({"n": 5, "label": "Bills", "state": "not needed", "note": "no bill waited for a tap (%s)" % counts})
    elif remaining == 0:
        steps.append({"n": 5, "label": "Bills", "state": "done", "note": "%d tapped (%s)" % (tapped, bills_line)})
    elif tapped:
        steps.append({"n": 5, "label": "Bills", "state": "partly", "note": "%d tapped, %d still to tap (%s)" % (tapped, remaining, counts)})
    else:
        steps.append({"n": 5, "label": "Bills", "state": "not yet", "note": "%d to tap (%s)" % (remaining, counts)})
    if 6 not in ticks and not S.card_has_his_line:
        s6 = {"n": 6, "label": "Marg sudhar", "state": "not needed", "note": "nothing of his on the card"}
    else:
        s6 = tap_step(6, "Marg sudhar", "no 'Aaj ke item theek kar diye' tap")
    if salt_ticked:
        s6["note"] = ("%s; %d salt task%s ticked" % (s6["note"], salt_ticked, _plural(salt_ticked, "", "s"))).strip("; ")
    steps.append(s6)
    gate_en = [g[2] for g in S.gate_open]
    extra_en = [x[1] for x in S.extra]
    if closed:
        steps.append({"n": 7, "label": "Band", "state": "done", "note": "%s%s" % (_hhmm(S.closed["at"]), (" by %s" % S.closed["by"]) if S.closed.get("by") else "")})
    else:
        steps.append({"n": 7, "label": "Band", "state": "open",
                      "note": ("; ".join(gate_en) or "ready to close") + ((" · not holding: " + "; ".join(extra_en)) if extra_en else "")})
    css, owner_line = _salt_owner(S.salt)
    return {
        "ok": True, "kit": KIT, "day": day,
        "state": "CLOSED" if closed else "OPEN",
        "closed_at": _norm_ts(S.closed["at"]) if closed else None,
        "reopened_at": _norm_ts(S.reopened["at"]) if S.reopened else None,
        "reopened_by": S.reopened["by"] if S.reopened else None,
        "opened_at": S.opened_at,
        "next_step": nxt, "left": gate_en + extra_en,
        "bills": {"tapped": tapped, "by_reason": by_reason, "remaining_today": len(S.bills["today"]),
                  "carried": len(S.bills["carry"]), "flagged": len(S.bills["flagged"]), "waiting": len(S.bills["waiting"]), "line": bills_line},
        "reports": {"rows": reports, "bills": rep_bills, "amount_p": rep_amount_p,
                    "amount": _rupees(rep_amount_p) if rep_amount_p is not None else "", "line": reports_line},
        "salts": {"ticked": salt_ticked, "by_section": by_section, "renames": by_section.get("rename", 0),
                  "ticked_by": ticked_by, "uploads": uploads, "line": salts_line},
        "claims": {"n": claims_n, "amount_p": claims_p, "amount": _rupees(claims_p), "by_reason": claims_by},
        "salt_list": {"pending": bool(S.salt.get("pending")), "fresh": bool(S.salt.get("fresh")), "owner_line": owner_line, "css": css},
        "steps": steps,
        "generated_at": _stamp(),
    }


def _visit_details_html(v):
    """The collapsed block for /finance/amir/day.  Server-rendered, no JavaScript."""
    rows = []
    for st in v["steps"]:
        cls = "good" if st["state"] == "done" else ("" if st["state"] == "not needed" else "warn")
        rows.append("<tr><td>%d</td><td>%s</td><td class='%s'>%s</td><td class=k>%s</td></tr>"
                    % (st["n"], _esc(st["label"]), cls, _esc(st["state"]), _esc(st.get("note", ""))))
    sl = v["salt_list"]
    head = "%s -- %s%s%s" % (_ddmmyyyy(v["day"]), v["state"],
                             (" at %s" % _hhmm(v["closed_at"])) if v.get("closed_at") else "",
                             (" (reopened %s)" % _hhmm(v["reopened_at"])) if v.get("reopened_at") else "")
    return ("<details class=visit><summary>Amir's visit &mdash; what was done</summary>"
            "<p class=sub>%s</p>"
            "<div class=tscroll><table><tr><th>step</th><th></th><th>verdict</th><th>detail</th></tr>%s</table></div>"
            "<div class=line>Bills tapped: <b>%d</b> <span class=k>(%s)</span></div>"
            "<div class=line>Purchase reports received: <span class=k>%s</span></div>"
            "<div class=line>Salt tasks ticked: <b>%d</b> <span class=k>(%s%s)</span></div>"
            "<div class=line>Claims raised for Darpan: <b>%d</b>, worth &#8377;%s</div>"
            "<div class=line>Salt list from Marg: <span class='%s'>%s</span></div>"
            "</details>"
            % (_esc(head), "".join(rows),
               v["bills"]["tapped"], _esc(v["bills"]["line"]),
               _esc(v["reports"]["line"]),
               v["salts"]["ticked"], _esc(v["salts"]["line"]),
               (" by %s" % ", ".join(v["salts"]["ticked_by"])) if v["salts"]["ticked_by"] else "",
               v["claims"]["n"], _esc(v["claims"]["amount"]),
               _esc(sl.get("css", "")), _esc(sl.get("owner_line", ""))))


@bp.route("/finance/amir/day/api/visit-summary")
def visit_summary():
    """The owner's summary of one visit.  Checker only -- the hub's block reads this.  Reads; writes nothing."""
    u, err = _require("checker", unit=_unit)
    if err:
        return {"ok": False, "error": "not_permitted", "message": "Only the checker may read the visit summary."}, 403
    day = (request.args.get("date") or request.args.get("d") or _today())[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        return {"ok": False, "error": "bad_date", "message": "date must be yyyy-mm-dd"}, 400
    cx = _db()
    ensure(cx)
    return _visit_summary(cx, state(cx, day, _who(u)))


@bp.route("/finance/amir/api/healthz")
def healthz():
    return {"ok": True, "kit": KIT, "at": _stamp()}


def init(app, db_getter, require_fn, unit="medical", roles=("maker", "checker", "viewer"), url_prefix=""):
    global _db, _require, _unit, _roles
    _db, _require, _unit, _roles = db_getter, require_fn, unit, tuple(roles)
    app.register_blueprint(bp, url_prefix=url_prefix)
    # The salt sheet rides on this mount rather than on a second one, so adding it never touches finance_app.py again.
    try:
        import amir_salts                                    # noqa: PLC0415
        amir_salts.init(app, db_getter, require_fn, unit=unit, roles=roles, url_prefix=url_prefix)
    except Exception:
        pass
    return bp


# ==========================================================================================================================================
# the bill warnings (S285, S307) -- statements, never a question (D708)
# ==========================================================================================================================================
def _twin_bills_s307(cx, b):
    """S307: other bills with THIS bill number and THIS date under ANOTHER supplier, each still carried by a live bill-wise export:
    [(supplier, amount_p, same_amount)].  Any failure to read means no warning, never a broken page."""
    out = []
    try:
        rows = cx.execute(
            "SELECT b.supplier_norm, MAX(b.supplier), MAX(b.amount_p) FROM purchase_bill b "
            "JOIN purchase_export e ON e.md5 = b.bw_md5 "
            "WHERE e.superseded_by IS NULL AND e.type = 'BILLWISE' AND b.bill_no = ? AND b.bill_date = ? "
            "AND b.supplier_norm <> ? GROUP BY b.supplier_norm ORDER BY b.supplier_norm",
            (b.get("bill_no"), b.get("bill_date"), b.get("supplier_norm"))).fetchall()
        mine = b.get("amount_p")
        for s_norm, s_name, amt in rows:
            out.append((s_name or s_norm, amt, mine is not None and amt is not None and int(amt) == int(mine)))
    except Exception:                                          # noqa: BLE001
        return out
    return out


def _supplier_warn_s285(cx, b):
    """S285: for each item on this bill, the suppliers who supplied it on EARLIER bills (counted by bill).  If this supplier never has
    and another has on two or more bills: (item, that supplier, how many bills).  Any failure to read means no warning."""
    out = []
    try:
        if not _table_exists(cx, "purchase_line"):
            return out
        live = "EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND e.md5 = l.source_md5)"
        items = cx.execute(
            "SELECT DISTINCT l.item FROM purchase_line l WHERE l.supplier_norm = ? AND l.bill_no = ? AND l.bill_date = ? "
            "AND l.item IS NOT NULL AND " + live + " ORDER BY l.item",
            (b.get("supplier_norm"), b.get("bill_no"), b.get("bill_date"))).fetchall()
        for (item,) in items:
            hist = cx.execute(
                "SELECT l.supplier_norm, COUNT(DISTINCT l.bill_no || '|' || l.bill_date) AS n FROM purchase_line l "
                "WHERE l.item = ? AND l.supplier_norm IS NOT NULL AND l.bill_date < ? AND " + live + " GROUP BY l.supplier_norm",
                (item, b.get("bill_date"))).fetchall()
            mine = sum(int(n) for s, n in hist if s == b.get("supplier_norm"))
            others = sorted(((int(n), s) for s, n in hist if s != b.get("supplier_norm")), reverse=True)
            if mine == 0 and others and others[0][0] >= 2:
                out.append((item, others[0][1], others[0][0]))
    except Exception:                                          # noqa: BLE001
        return out
    return out


# ==========================================================================================================================================
# S488 (kept): a waiting proof's English ending for the owner; the warn line once it has waited amir.proof_wait_hours
# ==========================================================================================================================================
def _s488_why(pr):
    pr = pr or {}
    return pr.get("why") if (pr.get("state") == "export" and pr.get("why") in S488_WHYS) else None


def _s488_ending(pr):
    """The owner's English ending for a waiting proof; '' when no reason can be had (the caller keeps its own words).
    stock_app._s524_english_ending reads this."""
    why = _s488_why(pr)
    if not why:
        return ""
    if why == "no_closing":
        return "waiting for a closing-stock export since %s (Amir / Shavez)" % _dm_hm(pr.get("since"))
    head = "Marg's closing of %s arrived %s; " % (str(pr.get("closing_day") or "")[:5], _dm_hm(pr.get("closing_at")))
    if why == "no_figure":
        return head + ("waiting for our own figure for that day (made when its sale report lands — Shavez; on a no-sale day, "
                       "the empty report)")
    if why == "pur_behind":
        return head + "waiting for a purchase export that reaches that day (Amir)"
    return head + "held on the system's side (no comparable export before the vouchers / figures re-based) — for the chat"


def _s488_wait_line(cx, st):
    """The owner's warn line once the proof -- stage A's, or stage C's oldest waiting lot -- has waited amir.proof_wait_hours or more."""
    try:
        import stock_app                                       # noqa: PLC0415
        pr = stock_app._s488_stage_proof(st)
    except Exception:                                          # noqa: BLE001
        return None
    e = _s488_ending(pr)
    m = _mins_since((pr or {}).get("since")) if e else None
    if m is None:
        return None
    h = m // 60
    if h < _setting(cx, "amir.proof_wait_hours"):
        return None
    return dict(cls="warn", target="stock", text="Count #%d: the voucher proof has waited %d hours — %s" % (int(st["count_id"]), h, e))


# ==========================================================================================================================================
# the owner's Needs-you lines (sanjeevni_approvals' hook) -- English, each with who and since when, each gone by itself
# ==========================================================================================================================================
def _s444_duty_lines(cx):
    """The duty map's machine part: every ORPHAN duty (no door on the person's own home) whose owner line no code raises yet ('coded'
    empty) -- its due_sql run read-only; due longer than allowed_days -> one line.  A missing map is silence; an unreadable one is one
    grey line."""
    import sqlite3                                                     # noqa: PLC0415 -- the read-only door for the map's queries
    path = os.environ.get("DUTY_MAP_JSON") or S444_DUTY_MAP
    if not path or not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            m = json.load(fh)
        duties = list(m.get("duties") or [])
    except Exception as e:                                             # noqa: BLE001
        return [dict(cls="info", target="checks-marg", text="The duty map (DUTY_MAP.json) could not be read: %s" % str(e)[:80])]
    try:
        dbfile = [r[2] for r in cx.execute("PRAGMA database_list").fetchall() if r[1] == "main"][0]
    except Exception:                                                  # noqa: BLE001
        dbfile = ""
    if not dbfile:
        return []
    out = []
    ro = sqlite3.connect("file:%s?mode=ro" % dbfile, uri=True, timeout=5)
    try:
        people = m.get("people") or {}
        for du in duties:
            sql = str(du.get("due_sql") or "").strip().rstrip(";").strip()
            if du.get("coded") or (du.get("door") and du.get("raise") is not True) or not du.get("owner_line") or not sql:
                continue
            if not re.match(r"(?is)^(select|with)\b", sql) or ";" in sql:
                continue
            try:
                r = ro.execute(sql).fetchone()
                n = int((r[0] if r else 0) or 0)
                since = r[1] if (r is not None and len(r) > 1) else None
            except Exception:                                          # noqa: BLE001
                continue
            if n <= 0:
                continue
            days = _days_since(since) if since else None
            try:
                allowed = int(du.get("allowed_days") or 0)
            except (TypeError, ValueError):
                allowed = 0
            if days is not None and days < allowed:
                continue
            try:
                text = str(du["owner_line"]).format(n=n, days=(days if days is not None else "?"), since=_dm_hm(since, time=False) if since else "-",
                                                    person=people.get(du.get("person"), du.get("person") or ""))
            except Exception:                                          # noqa: BLE001
                text = "%s: %d due (%s)" % (du.get("duty") or du.get("id"), n, people.get(du.get("person"), du.get("person") or ""))
            out.append(dict(cls="warn", target="checks-marg", text=text, duty=du.get("id")))
    finally:
        ro.close()
    return out


def _s444_refused_lines(cx):
    """A report refused in the last amir.refused_keep_hours hours (S488) -- one line per known type, its newest refusal, dropped once a
    VERIFIED file of that type arrives later; every unrecognised file together in ONE line."""
    out = []
    if not _table_exists(cx, "mi_file"):
        return out
    cut = (_now() - timedelta(hours=_setting(cx, "amir.refused_keep_hours"))).strftime("%Y-%m-%d %H:%M:%S")
    known, unknown = {}, []
    for typ, verdict, reason, pcv, at in cx.execute(
            "SELECT type, verdict, reason, pc_verdict, received_at FROM mi_file WHERE substr(received_at,1,10) >= ? "
            "AND (verdict <> 'VERIFIED' OR COALESCE(pc_verdict,'') = 'REFUSED')", (cut[:10],)).fetchall():
        t = _norm_ts(at)
        if not t or t < cut:
            continue
        if typ in (None, "", "_UNKNOWN"):
            unknown.append(t)
        elif typ not in known or t >= known[typ][0]:
            known[typ] = (t, verdict, reason, pcv)
    today = _today()
    for typ in sorted(known, key=lambda k: known[k][0]):
        t, verdict, reason, pcv = known[typ]
        if any((_norm_ts(r[0]) or "") > t for r in cx.execute("SELECT received_at FROM mi_file WHERE type=? AND verdict='VERIFIED'", (typ,)).fetchall()):
            continue                                                   # exported again and verified: gone by itself
        why = (reason or "").strip() or (("the medical PC refused it (%s)" % pcv) if pcv else (verdict or ""))
        out.append(dict(cls="warn", target="checks-marg",
                        text="Report refused %s %s: %s -- %s (Shavez / Amir to export it again)"
                             % ("today" if t[:10] == today else _dm_hm(t, time=False), t[11:16], typ, why[:120])))
    if unknown:
        out.append(dict(cls="warn", target="checks-marg",
                        text="%d unrecognised file(s) refused since %s (newest %s)" % (len(unknown), _dm_hm(min(unknown)), max(unknown)[11:16])))
    return out


def _voucher_line(cx, S):
    """(d) the count's vouchers, named by stage: the lot he has not touched for amir.voucher_visits of his visits (stock_app's one rule
    for a visit)."""
    out = []
    st = S.stage
    try:
        if not st or st.get("stage") not in ("A", "C"):
            return out
        import stock_app                                       # noqa: PLC0415
        oc = {c["count_id"]: c for c in (S.vouchers_open or [])}.get(st["count_id"]) or {}
        A, C = st.get("A") or {}, st.get("C") or {}
        n = A.get("open") if st["stage"] == "A" else len(C.get("today") or [])
        if not n:
            return out
        since = max([x for x in ((C.get("lot_at") if st["stage"] == "C" else oc.get("made_first")), oc.get("last_touch")) if x] or [""])
        visits = stock_app._s446_visits_since(cx, _norm_ts(since) or "")
        if len(visits) >= _setting(cx, "amir.voucher_visits"):
            what = "Stage A, orthotic" if st["stage"] == "A" else "Stage C, medicine lot"
            out.append(dict(cls="warn", target="checks-marg",
                            text="Count vouchers waiting (%s): %d -- Amir has not opened them in %d visits (%s), count #%d"
                                 % (what, n, len(visits), ", ".join(_dm_hm(v, time=False) for v in visits[-3:]), st["count_id"])))
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _d712_owner_lines(cx, S):
    """D712: goods tapped as arrived (stock_watch's own list, read inside amir_view) with NO scan from that supplier on or after the
    arrival day less arrival.bill_grace_days -- the owner's eyes only; Amir's card counts the scans, never the taps."""
    out = []
    try:
        import purchase_app                                    # noqa: PLC0415
        try:
            import stock_watch                                 # noqa: PLC0415
            grace = int(stock_watch.settings(cx).get("bill_grace_days") or 3)
        except Exception:                                      # noqa: BLE001
            grace = 3
        scans = [(purchase_app.supplier_key(x.get("supplier") or x.get("read_vendor") or ""), str(x.get("scan_day") or "")[:10])
                 for x in (S.scans or []) + (S.held or [])]
        for row in S.watch.get("bill_pending") or []:
            day = str(row.get("date") or "")[:10]
            if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
                continue
            k = purchase_app.supplier_key(row.get("vendor") or "")
            low = (datetime.strptime(day, "%Y-%m-%d") - timedelta(days=grace)).strftime("%Y-%m-%d")
            if any(sk == k and sd and sd >= low for sk, sd in scans):
                continue
            out.append(dict(cls="info", target="porders",
                            text="Goods tapped as arrived on %s from %s: no bill scanned, nothing in Marg (%s days) -- for your eyes only"
                                 % (_dm_hm(day, time=False), row.get("vendor") or "-", _days_since(day))))
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _s494_owner_lines(cx, S):
    """The jobs' owner lines (S494 4.6) -- English, target checks-marg, each gone by itself; on what state() read."""
    out = []
    try:
        if not _table_exists(cx, "amir_job"):
            return out
        for _jid, vendor, said_what, done_how in cx.execute("SELECT id, subject, said_what, done_how FROM amir_job WHERE kind='vendor_bill' ORDER BY id").fetchall():
            if _s494_bank(cx, vendor):
                continue
            if done_how == "scan linked":
                out.append(dict(cls="warn", target="checks-marg", text="Bank details to type for %s -- its bill is scanned" % vendor))
            elif done_how is None and said_what == "done":
                out.append(dict(cls="warn", target="checks-marg", text="Bank details to type for %s -- Amir says its bill is scanned" % vendor))
            elif done_how is None and said_what == "not_found":
                out.append(dict(cls="warn", target="checks-marg", text="Amir could not find a bill of %s -- its bank details are still needed" % vendor))
        J = S.jobs or {}
        newest, read = J.get("newest"), J.get("read")
        if J.get("label") and newest and read and newest["md5"] == read["md5"]:
            for r in J.get("rows") or []:
                if r["kind"] == "category" and r["said"] and r.get("said_what") == "done":
                    if newest["at"] > (_norm_ts(r["said_at"]) or "") and (J.get("cat_newest") or {}).get(r["subject"]) is None:
                        out.append(dict(cls="info", target="checks-marg",
                                        text="%s is not on Marg's category list of %s -- its category could not be proved" % (r["subject"], _dm_hm(newest["day"], time=False))))
        wait = _setting(cx, "amir.job_wait_days")
        old = []
        for subject, show in cx.execute("SELECT subject, show_from FROM amir_job WHERE " + S494_OPEN + " ORDER BY show_from, id").fetchall():
            dd = _days_since(show)
            if dd is not None and dd >= wait:
                old.append((subject, show, dd))
        if old:
            out.append(dict(cls="warn", target="checks-marg", text="Amir's one-time Marg jobs not done: %d -- since %s (%d days): %s"
                            % (len(old), _dm_hm(old[0][1], time=False), old[0][2], ", ".join(x[0] for x in old[:3]))))
    except Exception:                                          # noqa: BLE001
        return out
    return out


def needs_you_lines(con):
    """The owner's Needs-you lines: settle first; then (a) the salt list, (b) his own correction, (c) Darpan's claims, the count's
    stage line and verdict lines, the orthotics verified, (d) the count's vouchers, the proof's wait, D712's arrivals, the one-time
    jobs, Sarvam, the duty map's orphans and the refused reports."""
    out = []
    try:
        ensure(con)
        S = state(con, _today(), "", owner=True)
        settle(con, S, needs_you=True)
        # (a) the salt list owed -- counted in Amir's visits
        s = S.salt
        if s.get("pending") and (s.get("owed_days") or 0) >= _setting(con, "amir.salt_owed_days"):
            out.append(dict(cls="warn", target="checks-marg",
                            text="Salt list not received for %d of Amir's visits -- %d salt corrections unproven (Amir; Shavez if it did not come; owed since %s)"
                                 % (int(s.get("owed_days") or 0), int(s.get("ticks") or 0), _dm_hm(s.get("oldest_tick"), time=False))))
        # (b) his own corrections not yet seen in Marg after amir.self_exports exports
        r = con.execute(DUTY_SQL["amir.own_correction"]).fetchone()
        if r and int(r[0] or 0):
            need = _setting(con, "amir.self_exports")
            hit = []
            for marked, ex_at in con.execute("SELECT marked_at, export_at FROM amir_self_wait WHERE cleared_at IS NULL ORDER BY marked_at").fetchall():
                k = con.execute("SELECT COUNT(DISTINCT md5) FROM purchase_export WHERE type='BILLWISE' AND substr(replace(received_at,'T',' '),1,19) > ?",
                                (_norm_ts(ex_at) or "",)).fetchone()[0]
                if k >= need:
                    hit.append((marked, k))
            if hit:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Amir's own correction not yet seen in Marg: %d bill%s -- since %s (%d exports since)"
                                     % (len(hit), _plural(len(hit), "", "s"), _dm_hm(hit[0][0], time=False), hit[0][1])))
        # (c) Darpan's claims open too long (calendar days)
        days_c = _setting(con, "amir.claim_open_days")
        for _cid, sup, bno, amt, raised, by in con.execute("SELECT id, supplier, bill_no, amount_p, raised_at, raised_by FROM amir_claim "
                                                            "WHERE state <> 'settled' ORDER BY raised_at").fetchall():
            dd = _days_since(raised)
            if dd is not None and dd >= days_c:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Claim for Darpan open %d days: %s bill %s Rs %s (raised by %s %s)" % (dd, sup or "-", bno, _rupees(amt), by or "-", _dm_hm(raised, time=False))))
        st = S.stage
        if st:
            sw = S.sw or {}
            out.append(dict(cls="info", target="stock", text="Count #%d: %s" % (st["count_id"], sw.get("owner_en") or "")))
            out.extend(sw.get("owner_lines") or [])
            bat = (st.get("B") or {}).get("verified_at")
            if bat and _days_since(bat) is not None and _days_since(bat) <= 2:
                out.append(dict(cls="warn", target="stock", text="Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)" % (st["count_id"], _dm_hm(bat, time=False))))
            out.extend(_voucher_line(con, S))
            w = _s488_wait_line(con, st)
            if w:
                out.append(w)
        out.extend(_d712_owner_lines(con, S))
        out.extend(_s494_owner_lines(con, S))
        try:
            import purchase_app                                # noqa: PLC0415
            out.extend(purchase_app.sarvam_lines(con))
        except Exception:                                      # noqa: BLE001
            pass
        out.extend(_s444_duty_lines(con))
        out.extend(_s444_refused_lines(con))
    except Exception as e:                                     # noqa: BLE001
        print("amir_day: needs_you_lines stopped: %s" % str(e)[:200], file=sys.stderr)
        return out
    return out
