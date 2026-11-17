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

S603_AMIR_CALENDAR_SAFE (20-Oct-2026; F-952, F-786, F-726 a; rule (c) of 05-Oct):
  * ONE EXPORT FACT.  _export_fact(cx, day) = the server's own receipts of a purchase export (mi_file / purchase_export) after the visit's
    first bill-entry tap; the re-export band (_reexport_due) and the owner's 48-hour line (_s603_export_lines) read it -- never his step-3 tap.
  * Step 4 reads the export that COVERS the 1st..today first (then the newest): a month-end export taken second no longer hides the covering
    one.  A pair that did not arrive says since when (his tap's hh:mm in the reason).
  * The owner's ending for a proof whose items Marg's closing does not print under their name: 'absent' (stock_app._s488_why, F-786).

S638_EXPIRY_WATCH (24-Oct-2026; D771 / D777 / D780, the owner's "yes" to the mock-up): the card gains the expiry watch's rows, read ONCE
in state() as S.expiry (expiry_watch.amir_rows, fail-soft): "Mahine ki report: Batch Stock (poora store) text mein save karein" with the
steps from the owner's screenshots, until the month's Batch Stock is received; "Marg mein expiry write-off ya stockist ko return karein"
with the expired batches; "Marg mein in N dawaon ka batch theek karein" (folded list). his_line is False on every one: they are monthly
work proved only by the next Batch Stock, so they never hold his day open (no gate he cannot clear).
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

KIT = "S690_AMIR_BATCH_FIX"                               # the kit that last placed this file (S533 built the page; S584 named it; S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner's 48-hour line; S638: the expiry watch's rows; S678: a report the server's own door holds is never "nahi aayi"; S690: the Batch Stock as step 4's third export)
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

# S587 (fix D of D737; the approved mock-up): the DISPLAY order of the steps -- Marg sudhar (id 6) before the Export (id 3), so the purchase
# report is taken after every entry of the morning.  Ids never change: every route, S.done, the gate, amir_step_log.step and the duty map's
# due_sql keep them (history is not rewritten).  pos(id) is the number the banner shows; id_at(pos) the step at that position.
ORDER = (1, 2, 6, 3, 4, 5, 7)
LABEL_OF = dict(STEPS)


def pos(step_id):
    return ORDER.index(int(step_id)) + 1


def id_at(position):
    return ORDER[max(1, min(7, int(position))) - 1]

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
S494_KINDS = {"ask": -1, "category": 0, "vendor_bill": 1, "tap": 2}      # S814: "ask" -- the owner's question from the Marg watch, first on the card
S814_ANS = {"fixed": "Marg mein theek kar diya", "right": "Sahi hai, galti nahi", "supplier": "Supplier ne bill badla", "unknown": "Pata nahi",
            "returned": "Grahak ne maal wapas kiya", "mistake": "Bill galti se bana tha"}
S494_CAT_TYPE = "CATEGORY_WISE_ITEM_LIST"
# S533: a reopen no longer erases what he said -- it stamps reopened_at; a job counts as SAID only when said after the newest reopen.
S494_SAID = "said_at IS NOT NULL AND said_at > COALESCE(reopened_at, '')"
S494_OPEN = "show_from IS NOT NULL AND done_at IS NULL AND NOT (" + S494_SAID + ")"

S488_WHYS = ("no_closing", "no_figure", "pur_behind", "no_before", "rebased", "absent")   # S603 (F-786): absent = Marg's closing does not print them

# ---- the duty map's three SQLs (DUTY_MAP.json v11 copies them byte-equal; the code below RUNS them) ----
_BILLS_BASE = ("SELECT b.id, b.first_seen_day FROM purchase_bill b JOIN purchase_export e ON e.md5 = b.bw_md5 "
               "WHERE e.type = 'BILLWISE' AND e.superseded_by IS NULL AND b.bill_date >= '%s'" % BILLS_FROM)
_BILLS_UNANSWERED = (" AND NOT EXISTS (SELECT 1 FROM amir_bill_answer a WHERE a.bill_id = b.id OR (a.bill_id IS NULL AND "
                     "a.supplier_norm = b.supplier_norm AND a.bill_no = b.bill_no AND a.bill_date = b.bill_date))")
_SALT_LAST_S444 = ("SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file "
                   "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'")
# S763 (F-802, D879): the newest moment the server has a verified salt list for -- its first receipt (mi_file), or the moment the very same
# bytes were EXPORTED AGAIN (setting 'mi_again:SALT_WISE_ITEM_LIST', moved forward only by marg_door._s763_again). mi_file is never moved.
_SALT_LAST = ("SELECT MAX(t) FROM (SELECT substr(replace(received_at,'T',' '),1,19) AS t FROM mi_file "
              "WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED' UNION ALL "
              "SELECT substr(replace(value,'T',' '),1,19) AS t FROM setting WHERE key='mi_again:SALT_WISE_ITEM_LIST' AND value <> '')")


def _salt_due(last):
    return ("WITH l(t) AS (" + last + ") SELECT COUNT(*) AS n, MIN(substr(replace(s.done_at,'T',' '),1,19)) AS since "
            "FROM purchase_salt_task s, l WHERE COALESCE(s.done,0) = 1 AND s.done_at IS NOT NULL AND s.done_at <> '' "
            "AND (l.t IS NULL OR substr(replace(s.done_at,'T',' '),1,19) > l.t)")


_SALT_DUE_S444 = _salt_due(_SALT_LAST_S444)                              # S763: a copy with no setting table is read as before
DUTY_SQL = {
    "amir.bills_answer": "SELECT COUNT(*) AS n, MIN(first_seen_day) AS since FROM (" + _BILLS_BASE + _BILLS_UNANSWERED + ")",
    "amir.own_correction": "SELECT COUNT(*) AS n, MIN(substr(replace(marked_at,'T',' '),1,19)) AS since FROM amir_self_wait WHERE cleared_at IS NULL",
    "amir.salt_list": _salt_due(_SALT_LAST),                            # S763 (F-802): the same list exported again counts
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


def _door_receipt(cx, kind, day, first):
    """S678: the server's OWN receipt of a pair report -- the newest VERIFIED mi_file of type PURCHASE_<kind> that Marg stamped on `day`
    (its YYYYMMDD-HHMMSS name) and whose printed period covers first..day -> {stamp, at (hh:mm)}; None when there is none.  The door
    takes the medical PC's push within seconds; purchase_export waits for manojz's pull (29-Oct: manojz asleep 00:22-09:43)."""
    try:
        if not _table_exists(cx, "mi_file"):
            return None
        r = cx.execute("SELECT stamp, received_at FROM mi_file WHERE verdict='VERIFIED' AND type=? AND substr(stamp,1,8)=? "
                       "AND date_from<>'' AND date_to<>'' "
                       "AND substr(date_from,1,10)<=? AND substr(date_to,1,10)>=? ORDER BY stamp DESC LIMIT 1",
                       ("PURCHASE_" + kind, str(day).replace("-", ""), first, day)).fetchone()
    except Exception:                                                  # noqa: BLE001
        return None
    if not r:
        return None
    try:                                                               # a bill entered after this file: the re-export band rules, not the door
        t = cx.execute("SELECT MAX(done_at) FROM amir_step_log WHERE day=? AND step=2", (day,)).fetchone() \
            if _table_exists(cx, "amir_step_log") else None
    except Exception:                                                  # noqa: BLE001
        t = None
    t2 = _norm_ts(t[0]) if (t and t[0]) else None
    if t2 and (_norm_ts(r[1]) or "") < t2:                             # the server's receipt clock against the server's tap clock
        return None
    return {"stamp": r[0], "at": _hhmm(r[0]) or _hhmm(r[1])}


def _export_state(cx, day, wait_since=None):
    """Did today's pair arrive, is each one verified -- and is one still on its way?  (S241 / S243 / S244, kept)

        ok    verified -- arrived, today's stamp, 1st to date
        wait  he has exported and the grace window has not run out yet
        bad   the window ran out, or a file of his DID arrive and is wrong
        none  he has not said he exported yet -- nothing is expected
    S603: of the day's exports the one that COVERS the 1st..today is read first, then the newest (a month-end export taken second no longer
    hides the covering one); a pair that did not arrive carries since = his tap's hh:mm in its reason.
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
             ORDER BY CASE WHEN substr(COALESCE(period_from,''),1,10) <= ? AND substr(COALESCE(period_to,''),1,10) >= ? THEN 0 ELSE 1 END,
                      COALESCE(export_stamp, received_at) DESC
                LIMIT 1""",
            (kind, day, first, day),
        ).fetchone()
        door = _door_receipt(cx, kind, day, first) if str(day) >= _today() else None   # S678: today only -- a past day keeps its own reading
        if row is None and door is not None:
            out.append({"kind": kind, "label": label, "have": False, "state": "wait", "waited": waited, "door": door["at"],
                        "reason": "server par %s baje aa gayi -- padhi ja rahi hai, dobara nahi nikaalni" % door["at"],
                        "reason_en": "at the server since %s (VERIFIED at the door) -- its rows wait for the manojz leg" % door["at"]})
            continue
        if row is None:
            since = None
            if wait_since is None:
                state, why, en = "none", "abhi nikaali nahi gayi", "not received"
            elif within:
                state, why, en = "wait", "file ban gayi hai, aa rahi hai", "still arriving"
            else:
                since = _hhmm(wait_since)                      # S603: since when -- the moment of his tap rides in the reason
                state, why, en = "bad", "%s baje se nahi aayi" % since, "not received since %s (his tap)" % since
            out.append({"kind": kind, "label": label, "have": False, "state": state, "waited": waited, "reason": why, "reason_en": en, "since": since})
            continue
        d = dict(zip(("md5", "period_from", "period_to", "export_stamp", "n_rows", "received_at"), tuple(row)))
        ok_from = (d.get("period_from") or "")[:10] <= first
        ok_to = (d.get("period_to") or "")[:10] >= day
        if not (ok_from and ok_to) and door is not None and (_norm_ts(door["stamp"]) or "") > (_norm_ts(d.get("export_stamp") or d.get("received_at")) or ""):   # S678: a NEWER covering one is at the door
            out.append({"kind": kind, "label": label, "have": False, "state": "wait", "waited": waited, "door": door["at"],
                        "reason": "server par %s baje aa gayi -- padhi ja rahi hai, dobara nahi nikaalni" % door["at"],
                        "reason_en": "at the server since %s (VERIFIED at the door) -- its rows wait for the manojz leg" % door["at"]})
            continue
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
        again = _table_exists(cx, "setting")                                # S763: every real copy has it; a bare test db may not
        r = cx.execute(_SALT_LAST if again else _SALT_LAST_S444).fetchone()
        out["last_list"] = r[0] if r else None
        r = cx.execute(DUTY_SQL["amir.salt_list"] if again else _SALT_DUE_S444).fetchone()
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
    """S626 (F-988): the month packs on Amir's page, as [(month, seen)] oldest first -- every ready month he has not marked seen, and
    the NEWEST ready month always, seen or not, so the two statements stay on his page until the next month's pack is ready (the
    owner's note of 22-Oct, point 5).  A month with nothing on the shelf is never listed."""
    out = []
    try:
        import packs                                           # noqa: PLC0415 -- READ ONLY: amir_pack(con, month)
        got = []
        for m in _s446_prev_months(3):
            p = packs.amir_pack(cx, m)
            if p.get("ready"):
                got.append((m, bool(p.get("seen"))))
        newest = got[-1][0] if got else None
        out = [(m, s) for (m, s) in got if (not s) or m == newest]
    except Exception:                                          # noqa: BLE001
        out = []
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


def _export_fact(cx, day):
    """S603 (F-952): THE export fact of a visit day, in one place -- (lo, fact, t2).  lo = the day's OLDEST step-2 tap ('Sab bill daal diye'),
    t2 = its newest; fact = the newest moment the SERVER received a purchase export after lo: a VERIFIED mi_file of the pair's families (the
    collector) or a purchase_export row of them (the pusher; superseded or not -- a receipt is a receipt), any day (a file landing after midnight
    counts).  Every moment through _norm_ts.  (None, None, None) when the day has no step-2 tap.  Read by _reexport_due (his band) and by
    _s603_export_lines (the owner's line) -- never his step-3 tap."""
    if not _table_exists(cx, "amir_step_log"):
        return None, None, None
    r = cx.execute("SELECT MIN(done_at), MAX(done_at) FROM amir_step_log WHERE day=? AND step=2", (day,)).fetchone()
    lo = _norm_ts(r[0]) if (r and r[0]) else None
    t2 = _norm_ts(r[1]) if (r and r[1]) else None
    if not lo or not t2:
        return None, None, None
    facts = []
    for table, sql in (("mi_file", "SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM mi_file WHERE verdict='VERIFIED' "
                                   "AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,19) > ?"),
                       ("purchase_export", "SELECT MAX(substr(replace(received_at,'T',' '),1,19)) FROM purchase_export "
                                           "WHERE type IN ('BILLWISE','ITEMWISE','BILLITEMWISE') AND substr(replace(received_at,'T',' '),1,19) > ?")):
        try:
            if _table_exists(cx, table):
                x = cx.execute(sql, (lo,)).fetchone()
                f = _norm_ts(x[0]) if (x and x[0]) else None
                if f:
                    facts.append(f)
        except Exception:                                                  # noqa: BLE001
            pass
    return lo, (max(facts) if facts else None), t2


def _reexport_due(cx, day, ticks):
    """S587 (F-926 / D737 D), rewritten by S603 (F-952): (due, since) -- True when the day's newest step-2 tap ('Sab bill daal diye') is later
    than the day's export FACT (_export_fact: the server's newest receipt of a purchase export after the day's first step-2 tap).  Rests on his
    step-2 taps and the server's own receipts -- never on his step-3 tap (F-952: on 18-Oct the tap cleared the band and no file ever came).
    (False, None) while no fact exists yet (then the step-4 gate says the report is not taken; no band before the visit's first file).
    `ticks` is kept for the callers and is unused here.  since = the newest step-2 tap's moment."""
    _lo, fact, t2 = _export_fact(cx, day)
    if not t2 or not fact:
        return False, None
    return (t2 > fact), t2


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
    S.reexport_due, S.reexport_since = _reexport_due(cx, day, S.ticks)   # S587 (F-926 / D737 D)
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
    S.expiry = []                                              # S638 (D780): the expiry watch's rows, read once (fail-soft)
    try:
        import expiry_watch                                    # noqa: PLC0415
        S.expiry = expiry_watch.amir_rows(cx)
    except Exception:                                          # noqa: BLE001
        S.expiry = []
    S.batchstock = {}                                          # S690: step 4's third export (fail-soft)
    try:
        import expiry_watch                                    # noqa: PLC0415
        S.batchstock = expiry_watch.batch_stock_state(cx)
    except Exception:                                          # noqa: BLE001
        S.batchstock = {}
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
    rows.extend(getattr(S, "expiry", None) or [])              # S638 (D780): the Batch Stock card, the expired batches, the batch fixes
    for m, seen in S.packs or []:                              # S626 (F-988): a seen month keeps its links; only the button goes
        rows.append(("packs", "<div class=line><span class=big>Mahine ka pack &mdash; %s</span>%s"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/yes'>Yes Bank Sanjeevni statement (PDF)</a></p>"
                     "<p><a class='btn plain' href='/finance/amir/pack/%s/icici'>ICICI Sanjeevni statement (PDF)</a></p>"
                     "%s</div>"
                     % (_esc(_s446_month_name(m)),
                        ("<p><a class='btn plain' href='/finance/amir/pack/%s/neft'>Paid NEFT sheet (PDF)</a></p>" % m) if (S.neft_ok or {}).get(m) else "",
                        m, m,
                        "" if seen else ("<form method=post action='/finance/amir/pack/%s/seen'><button class=btn name=go value=1>Dekh liya</button></form>" % m)),
                     "", False))
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
    if getattr(S, "reexport_due", False):                     # S587 (F-926 / D737 D): a bill entered after the export -- the day waits for a fresh export
        gate.append((3, "Purchase report dobara nikaalni hai — bill entry export ke baad hui hai", "re-export due: a bill was entered after the export"))
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
    for n in ORDER:                                            # S587: the display order (ids unchanged)
        if n == 7:
            continue
        if n == 4 and S.export_wait and not S.done.get(4):   # S244: a report in transit never parks him on step 4
            continue
        if not S.done.get(n):
            return n
    return 7


def _ready_to_close(S):
    return all(S.done.get(n) for n in GATE_STEPS) and not getattr(S, "reexport_due", False)   # S587: the day does not close until a fresh export


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
    for p, n in enumerate(ORDER, 1):                           # S587: the position shown, the id in the route
        label = LABEL_OF[n]
        if n == current:
            cls = "on"
        elif S.done.get(n):
            cls = "ok"
        elif n == 4 and S.export_wait:
            cls = "wait"
        else:
            cls = ""
        out.append("<a class='%s' href='/finance/amir/step/%d'>%d<br>%s</a>" % (cls, n, p, _esc(label)))
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
    band = _reexport_band(S) if (getattr(S, "reexport_due", False) and pos(step) >= 4) else ""   # S587: on every step after the export's position
    return _shell("Amir -- kaam", who + _banner(step, S) + band + card + _notes_html(S) + head + body + _neft_card_s407()
                  + "<p class=foot>Step %d of 7 &middot; <a href='/portal?all=1'>Sab tiles</a></p>" % pos(step), head_extra)


def _reexport_band(S):
    """S587 (F-926 / D737 D): one red line on the positions after the export while a bill was entered after it -- the door is the export step."""
    return ("<div class=band id=reexport style='background:#fff4f4;border-color:var(--bad);color:var(--bad)'>"
            "Purchase report dobara nikaaliye &mdash; bill entry export ke baad hui hai. <a href='/finance/amir/step/3'>Kholiye</a></div>")


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


def _s690_batchstock_card(S):
    """S690: step 4's third export -- the Batch Stock (whole store), saved AFTER the vouchers.  Never a gate."""
    b = getattr(S, "batchstock", None) or {}
    st = b.get("state") or "none"
    if st == "ok":
        line = ("<div class=line><span class='big good'>Batch Stock (poora store) &#10003;</span><br>"
                "<span class=sub>%s &middot; %s dawa &middot; %s baje &middot; batch sudhar ki jaanch ho gayi &mdash; "
                "<a href='/finance/amir/step/3'>step 3 dekhiye</a></span></div>"
                % (_esc(_ddmmyyyy(b.get("as_on")) if b.get("as_on") else ""), _esc(b.get("items") or 0), _esc(b.get("at") or "")))
        return "<div class=card><h2>Teesri report</h2>%s</div>" % line
    if st == "wait":
        return ("<div class=card><h2>Teesri report</h2><div class=line><span class='big warn'>Batch Stock (poora store) &hellip;</span><br>"
                "<span class=sub>Server par %s baje aa gayi &mdash; jaanch ho rahi hai (5 minute). Aapko kuch nahi karna.</span></div></div>"
                % _esc(b.get("at") or ""))
    if st == "bad":
        return ("<div class=card><h2 class=bad>Batch Stock poore store ki nahi thi &#10007;</h2><div class=line>"
                "<span class='big bad'>Batch Stock (poora store) &#10007;</span><br><span class=sub>%s baje ki report %s. "
                "Select Store mein <b>WHOLE</b> chun kar dobara nikaaliye.</span></div></div>" % (_esc(b.get("at") or ""), _esc(b.get("reason") or "")))
    return ("<div class=card><h2>Teesri report: Batch Stock (poora store)</h2>"
            "<div class=line><span class=big>Batch Stock (poora store)</span><br>"
            "<span class=sub>Abhi nikaali nahi gayi. Voucher daalne ke <b>BAAD</b> nikaaliye &mdash; isi se pata chalta hai kaun sa batch theek ho gaya.</span>"
            "<div style='background:#f3f7fb;border:1px solid #cfe0ef;border-radius:10px;padding:8px 12px;margin:8px 0 0;font-size:15px'><b>Tarika</b>"
            "<ol style='margin:6px 0 0;padding-left:20px'>"
            "<li>Marg main screen &rarr; <b>Stocks</b> &rarr; <b>Batch Stock</b></li>"
            "<li>Select Store &rarr; <b>WHOLE</b> &rarr; Enter</li>"
            "<li>Selected Company <b>No</b> &middot; Stock as on: jo date Marg dikhaye &middot; Stock Status <b>Available</b> &middot; "
            "Selected Salt <b>No</b> &middot; More Options <b>No</b> &rarr; <b>Accept</b></li>"
            "<li>Report menu &rarr; <b>A Stock Statement</b> &middot; Index On &rarr; <b>B Alphabatic</b></li>"
            "<li>Separate Printing <b>1 No</b>, dono Chr box khaali &rarr; Enter &rarr; <b>View</b></li>"
            "<li>Text mein save kijiye &mdash; jaise purchase report</li></ol></div></div></div>")


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
        elif st == "wait" and e.get("door"):                           # S678
            out.append("<div class=line><span class='big warn'>%s &hellip;</span><br>"
                       "<span class=sub>Server par %s baje aa gayi &mdash; padhi ja rahi hai.</span></div>"
                       % (_esc(e["label"]), _esc(e["door"])))
        elif st == "wait":
            out.append("<div class=line><span class='big warn'>%s &hellip;</span><br>"
                       "<span class=sub>File abhi aa rahi hai.</span></div>" % _esc(e["label"]))
        elif st == "none":
            out.append("<div class=line><span class=big>%s</span><br>"
                       "<span class=sub>Abhi nikaali nahi gayi.</span></div>" % _esc(e["label"]))
        else:
            out.append("<div class=line><span class='big bad'>%s &#10007;</span><br>"
                       "<span class=sub>%s</span></div>" % (_esc(e["label"]), _esc(e.get("reason", ""))))
    door_waits = [e for e in S.exports if e.get("state") == "wait"]                         # S678: a door wait never hides a
    if waiting and (bad or notyet) and all(e.get("door") for e in door_waits):                 # wrong or missing report -- the
        waiting = False                                                                    # bad / not-yet head and buttons rule
    door_only = waiting and all(e.get("door") for e in door_waits)
    if door_only:
        head = ("<div class=card><h2 class=warn>Report server par aa gayi hai</h2>"
                "<p class=big>Padhi ja rahi hai &mdash; bill ki list thodi der mein aayegi.</p>"
                "<p>Aapko dobara nahi nikaalni. Aage ka kaam kijiye -- yeh screen khud dekhti rahegi.</p></div>")
    elif waiting:
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
    body = head + "<div class=card><h2>Do report</h2>%s</div>" % "".join(out) + _s690_batchstock_card(S)    # S690
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


def _s494_tap(cx, who, val, note=""):
    """A tap on his card (S494 4.5): 'cat' (every shown, open category row), 'scan:<id>' / 'nf:<id>' (a vendor_bill row), 'tap:<id>'
    (a tap row).  A row not shown, not open, of another kind, or not a number changes nothing.  One audit row per row changed."""
    try:
        val = str(val or "").strip()
        now = _stamp()
        ma = re.match(r"^ask:(\d{1,9}):([a-z]{3,10})$", val)       # S814: his answer to the owner's question -- one tap, a short line
        if ma:
            r = cx.execute("SELECT id, key, sub_hi FROM amir_job WHERE id=? AND kind='ask' AND " + S494_OPEN, (int(ma.group(1)),)).fetchone()
            code = ma.group(2)
            if not r or code not in S814_ANS or code not in str(r[2] or "").split(","):
                return 0
            line = re.sub(r"[\s|]+", " ", str(note or "")).strip()[:300]
            what = code + (("|" + line) if line else "")
            if cx.execute("UPDATE amir_job SET said_at=?, said_by=?, said_what=?, done_at=?, done_how='answered' WHERE id=? AND done_at IS NULL",
                          (now, who, what, now, r[0])).rowcount != 1:   # S446 review S5: a double tap answers once
                cx.rollback()
                return 0
            _audit(cx, who, "job", r[1], {"answered": code, "line": line or None})
            cx.commit()
            return 1
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
    for j in jobs:                                             # S814: the owner's question, first -- the answers are one tap each
        if j["kind"] != "ask":
            continue
        codes = [c for c in str(j.get("sub_hi") or "").split(",") if c in S814_ANS]
        q = "<br>".join(_esc(x) for x in str(j.get("text_hi") or j["subject"]).split("\n"))
        btns = "".join("<button class='btn plain' name=ans value='%s' style='display:block;width:100%%;text-align:left;margin:0 0 6px'>%s</button>"
                       % (c, _esc(S814_ANS[c])) for c in codes)
        out.append("<div class=line style='border-left:4px solid var(--bad);padding-left:8px'><span class=big><b>Doctor sahab ka sawaal</b></span><br>"
                   "<span>%s</span><form method=post style='margin-top:8px'><button type=submit disabled hidden aria-hidden=true></button>"
                   "<input type=hidden name=job value='ask:%d'>"
                   "<input name=note maxlength=300 placeholder='Kuch likhna ho to pehle yahan likhiye (zaroori nahi)' "
                   "style='width:100%%;padding:8px;margin:0 0 8px;border:1px solid #d0d5dd;border-radius:8px'>%s</form></div>" % (q, j["id"], btns))
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
            jv = str(f.get("job") or "")
            if jv.startswith("sna:"):                          # S849: his answer to 'scanned bill not found in Marg'
                try:
                    import scan_ask                            # noqa: PLC0415
                    scan_ask.amir_tap(cx, user, jv)
                except Exception:                              # noqa: BLE001
                    pass
                return _go(n)
            if jv.startswith("ask:") and f.get("ans"):         # S814: the answer button names the answer
                jv = "%s:%s" % (jv, f.get("ans"))
            _s494_tap(cx, user, jv, f.get("note") or "")
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
        return _go(nxt if pos(nxt) >= pos(n) else id_at(pos(n) + 1) if pos(n) < 7 else 7)   # S587 (R1-B1): by position, never id arithmetic
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
    if getattr(S, "reexport_due", False):                     # S587 (F-926): his line, same day -- Needs-you is not touched
        body += "<div class=card id=reexport><p class='big bad'>re-export due since %s</p><p class=sub>a bill was entered after the purchase export; the day waits for a fresh export</p></div>" % _esc(_hhmm(S.reexport_since))
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
        if closed or pos(nxt) > pos(n):                        # S587 (R1-B1): by position
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
    elif closed or pos(nxt) > pos(3):                          # S587 (R1-B1): by position
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
    if why == "absent":                                    # S603 (F-786): the closing came; the items are not printed under their name
        names = [str(x) for x in (pr.get("absent") or [])]
        return head + "%d item(s) not printed under their name in it: %s (still wrong in Marg — the hub's correction list; Amir)" % (
            len(names), ", ".join(names[:3]) + (" …" if len(names) > 3 else ""))
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


def _s603_export_lines(cx):
    """S603 (rule (c) of 05-Oct; F-952): the owner's one line per OPEN visit day of the last 7 days (start_capture_lines's window) whose newest
    step-3 tap ('Dono report nikaal di') is amir.proof_wait_hours old or more: no export fact after the visit's first bill-entry tap -> 'never
    reached the server'; a step-2 tap after the fact -> 're-export owed'.  The fact is _export_fact's -- never _export_state (a past day's live
    pair is superseded by the next export).  Gone by itself when the fact lands.  English; a closed day (state()'s rule: the newest step-7 row
    is the close) is never named."""
    out = []
    try:
        if not _table_exists(cx, "amir_step_log"):
            return out
        lo_day = (_now() - timedelta(days=7)).strftime("%Y-%m-%d")
        wait_min = _setting(cx, "amir.proof_wait_hours") * 60
        for (day,) in cx.execute("SELECT DISTINCT day FROM amir_step_log WHERE day >= ? ORDER BY day", (lo_day,)).fetchall():
            rows = cx.execute("SELECT step, done_at, note FROM amir_step_log WHERE day=? ORDER BY id", (day,)).fetchall()
            t7 = [r for r in rows if int(r[0]) == 7]
            if t7 and t7[-1][2] == "close":
                continue
            t3s = [r[1] for r in rows if int(r[0]) == 3]
            t3 = _norm_ts(t3s[-1]) if t3s else None
            m = _mins_since(t3) if t3 else None
            if m is None or m < wait_min:
                continue
            lo, fact, t2 = _export_fact(cx, day)
            if not lo:
                continue
            ddmm = _dm_hm(day, time=False)
            if not fact:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Amir's purchase export of %s never reached the server — he tapped 'nikaal di' at %s; the day stays open until the pair lands (Amir)"
                                     % (ddmm, _dm_hm(t3))))
            elif t2 > fact:
                out.append(dict(cls="warn", target="checks-marg",
                                text="Amir entered a bill at %s on %s after that day's export and no purchase export has landed since — re-export owed (Amir)"
                                     % (_hhmm(t2), ddmm)))
    except Exception:                                                  # noqa: BLE001
        return out
    return out


def needs_you_lines(con):
    """The owner's Needs-you lines: settle first; then (a) the salt list, (b) his own correction, (c) Darpan's claims, the count's
    stage line and verdict lines, the orthotics verified, (d) the count's vouchers, the proof's wait, D712's arrivals, S603's export
    waits (never reached / re-export owed, after amir.proof_wait_hours), the one-time jobs, Sarvam, the duty map's orphans and the
    refused reports."""
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
            # S536: only once the count has passed the orthotic stages (C or done). The moment is the root's FIRST stage-C release --
            # amir_stage releases the first medicine lot on the read that first finds A and B passed, and state() has just called it on
            # this connection -- else B's verification (a count with no medicine batch goes straight to done). Its own try: a fault here
            # drops this one line only. Read-only (amir_day writes no stage event).
            try:
                if st.get("stage") in ("C", "done"):
                    r = con.execute("SELECT MIN(at) FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release'",
                                    (int(st["count_id"]),)).fetchone()
                    mom = (r[0] if r else None) or (st.get("B") or {}).get("verified_at")
                    dd = _days_since(mom) if mom else None
                    if dd is not None and dd <= 2:
                        out.append(dict(cls="warn", target="stock", text="Orthotics verified and renamed -- live orthotic ordering can start (count #%d, %s)"
                                        % (st["count_id"], _dm_hm(mom, time=False))))
            except Exception:                              # noqa: BLE001
                pass
            out.extend(_voucher_line(con, S))
            w = _s488_wait_line(con, st)
            if w:
                out.append(w)
        out.extend(_d712_owner_lines(con, S))
        out.extend(_s603_export_lines(con))                    # S603 (F-952): a visit's export that never came / a re-export owed, after 48 h
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



# ---- S738 (06-Nov-2026, Sanjeevni session 396, kit S738_AMIR_CORRECTIONS; D839, D840; the owner's OK 21:28 IST on the mock) -------------
#  "Purchase bill Marg mein theek karein" on the Marg sudhar card: every correction scan_register.s738_fixes gives (the paper reads less
#  than Marg / more -- with the paper's lines Marg lacks when they add up / entered twice), each with the bill date and "Kaagaz dekhiye"
#  (/finance/purchase/api/s738/scan/<id>, the scan inline). His line (step 6's tick), proved only by his own export: Marg = the paper and
#  the line leaves by itself. settle() keeps scan_register's s738_fix in step (only when the list itself was read). A green line counts
#  the corrections his exports proved in the last 14 days. A back-to-top link on every page (no JavaScript: href '#').
KIT_S738 = "S738_AMIR_CORRECTIONS"
_state_before_s738 = state


def state(cx, day, who="", step=None, owner=False):           # noqa: F811
    S = _state_before_s738(cx, day, who, step, owner)
    S.s738, S.s738_ok, S.s738_proved = [], False, 0
    try:
        import scan_register as SR                             # noqa: PLC0415
        S.s738 = SR.s738_fixes(cx)
        S.s738_ok = True
        cut = (datetime.now(IST).replace(tzinfo=None) - timedelta(days=14)).replace(microsecond=0).isoformat()
        S.s738_proved = sum(1 for t in SR.s738_tracked(cx).values() if t.get("settled_at") and str(t["settled_at"]) >= cut)
    except Exception as e:                                     # noqa: BLE001 -- his day never waits on it
        print("amir_day S738: the corrections could not be read: %s" % str(e)[:200], file=sys.stderr)
    _derive(S)
    return S


def _s738_rs(p):
    if p is None:
        return _rupees(p)
    p = int(p)
    whole = _rupees(abs(p) - abs(p) % 100)
    return ("-" if p < 0 else "") + (whole if abs(p) % 100 == 0 else "%s.%02d" % (whole, abs(p) % 100))


def _s738_card(fx):
    out = []
    for f in fx:
        nos = f.get("numbers") or [f["bill_no"]]
        head = "<div class=who>%s &middot; Bill %s</div><div style='font-size:15px'><b>Bill ki tareekh: %s</b></div>" % (
            _esc(f["supplier"]), _esc(nos[0] if f["kind"] == "double" else f["bill_no"]), _esc(_ddmmyyyy(f["date"])))
        if f["kind"] == "less":
            body = ("<div style='font-size:15px'>Marg mein &#8377;%s &middot; kaagaz par &#8377;%s &mdash; <b class=bad>&#8377;%s kam</b></div>"
                    "<p class=good><b>Marg mein bill &#8377;%s kijiye</b></p>"
                    % (_esc(_s738_rs(f["marg_p"])), _esc(_s738_rs(f["paper_p"])), _esc(_s738_rs(abs(f["diff_p"]))), _esc(_s738_rs(f["paper_p"]))))
        elif f["kind"] == "more":
            if f.get("items"):
                lines = "".join("<div>%s &middot; %s &middot; &#8377;%s</div>" % (_esc(i.get("name")), _esc(i.get("qty") if i.get("qty") not in (None, "") else "-"),
                                                                             _esc(_s738_rs(i.get("amount_p")))) for i in f["items"])
                body = ("<div style='font-size:15px'>Marg mein &#8377;%s &middot; kaagaz par &#8377;%s &mdash; <b class=bad>&#8377;%s zyada</b></div>"
                        "<p>Bill par yeh item hain, Marg mein nahi:</p><div class=band>%s</div>"
                        "<p class=good><b>Bill par wapsi likhi ho to: poora bill aur purchase return. Warna: yeh line Marg mein jodiye.</b></p>"
                        % (_esc(_s738_rs(f["marg_p"])), _esc(_s738_rs(f["paper_p"])), _esc(_s738_rs(f["diff_p"])), lines))
            else:
                body = ("<div style='font-size:15px'>Marg mein &#8377;%s &middot; kaagaz par &#8377;%s &mdash; <b class=bad>&#8377;%s zyada</b></div>"
                        "<p class=good><b>Bill ke item Marg se milaiye. Bill par wapsi likhi ho to: poora bill aur purchase return. "
                        "Warna: chhooti line Marg mein jodiye.</b></p>"
                        % (_esc(_s738_rs(f["marg_p"])), _esc(_s738_rs(f["paper_p"])), _esc(_s738_rs(f["diff_p"]))))
        else:
            body = ("<div style='font-size:15px'>Yeh bill Marg mein do baar hai (Bill %s)</div><p class=good><b>Marg mein ek entry hataiye</b></p>"
                    % _esc(" aur ".join(nos)))
        link = ("<a class='btn plain' style='display:inline-block;width:auto;margin:0' href='/finance/purchase/api/s738/scan/%d' target=_blank "
                "rel=noopener>Kaagaz dekhiye</a>" % int(f["scan"])
                if f.get("scan") is not None else "")
        out.append("<div class=bill data-s738='%d'>%s%s%s</div>" % (int(f["bill_id"]), head, body, link))
    return ("<div class=line id=s738><span class=big>Purchase bill Marg mein theek karein &middot; %d</span>"
            "<p class=sub>Har bill ka kaagaz saath mein hai. Marg mein kaagaz jaisa kijiye.</p>%s"
            "<p class=sub style='background:#eef0f4;border-radius:8px;padding:8px'>Theek karne ke baad aaj ki report export (step 4) kijiye &mdash; "
            "Marg mein sahi aate hi line khud hat jayegi.</p></div>" % (len(fx), "".join(out)))


_card_rows_before_s738 = _card_rows


def _card_rows(S):                                            # noqa: F811
    rows = _card_rows_before_s738(S)
    fx = getattr(S, "s738", None) or []
    add = []
    if fx:
        add.append(("s738", _s738_card(fx), "purchase bill corrections: %d" % len(fx), True))
    n = int(getattr(S, "s738_proved", 0) or 0)
    if n:
        add.append(("s738ok", "<div class=line><span class=good>Pichhli visit ke sudhar Marg mein mil gaye &#10003; &middot; %d</span></div>" % n, "", False))
    if not add:
        return rows
    at = 0
    for i, r in enumerate(rows):
        if r[0] in ("stage", "sunday", "fixes", "scans"):
            at = i + 1
    return rows[:at] + add + rows[at:]


_settle_before_s738 = settle


def settle(cx, S, needs_you=False):                           # noqa: F811
    out = _settle_before_s738(cx, S, needs_you)
    if getattr(S, "s738_ok", False):
        try:
            import scan_register as SR                         # noqa: PLC0415
            try:
                new, proved = SR.s738_sync(cx, S.s738)
            except Exception:                                  # noqa: BLE001
                cx.rollback()
                raise
            if proved:                                         # this very read proved some: the green line says so at once
                cut = (datetime.now(IST).replace(tzinfo=None) - timedelta(days=14)).replace(microsecond=0).isoformat()
                S.s738_proved = sum(1 for t in SR.s738_tracked(cx).values() if t.get("settled_at") and str(t["settled_at"]) >= cut)
                _derive(S)
        except Exception as e:                                 # noqa: BLE001
            print("amir_day S738: the corrections could not be kept: %s" % str(e)[:200], file=sys.stderr)
    return out


_shell_before_s738 = _shell


def _shell(title, body, head_extra=""):                       # noqa: F811 -- S738: back to the top, no JavaScript
    page = _shell_before_s738(title, body, head_extra)
    up = ("<a href='#' id=s738up aria-label='Upar jaiye' style='position:fixed;right:16px;bottom:16px;width:52px;height:52px;border-radius:26px;"
          "background:var(--accent);color:#fff;font-size:24px;font-weight:800;display:flex;align-items:center;justify-content:center;"
          "text-decoration:none;z-index:70'>&#8593;</a>")
    return page.replace("</body>", up + "</body>", 1)
# ---- S738 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S740 (07-Nov-2026, Sanjeevni session 399, kit S740_PURCHASE_RETURNS; D839 kit 3 as the owner refined it 06:02 - 06:28 IST) -------------
#  "Wapsi baaki" on the Marg sudhar card: every pending purchase return (scan_register.s740_pending) stays here until the dealer's credit note
#  or revised bill resolves it (the owner 06:08). A return waiting for the dealer's paper is shown as a line with nothing to do but the
#  rule ("aane par hi badlaav"); the day the paper comes it says what to enter. His line (step 6's tick) only when a return has something
#  for him to enter. S738's "more" card: once reception has answered "Nahi" it says only "add the lines"; unanswered it says not to change
#  Marg for a return (the net entry is the default, the owner 06:12 - 06:20). settle() keeps s740_track in step. Nothing for him to tap.
KIT_S740 = "S740_PURCHASE_RETURNS"
S740_DO = ("do_revised", "do_full", "do_return", "do_own", "do_amount", "do_goods")
_state_before_s740 = state


def state(cx, day, who="", step=None, owner=False):           # noqa: F811
    S = _state_before_s740(cx, day, who, step, owner)
    S.s740, S.s740_ok, S.s740_no = [], False, set()
    try:
        import scan_register as SR                             # noqa: PLC0415
        m = SR.s740_model(cx)
        S.s740 = [r for r in m["returns"] if not r["resolved"]]
        S.s740_ok = True
        ans = SR._s740_answers(cx)
        for f in getattr(S, "s738", None) or []:
            b = cx.execute("SELECT supplier_norm, bill_no, bill_date FROM purchase_bill WHERE id=?", (int(f["bill_id"]),)).fetchone()
            if b is not None and (ans.get((str(b[0]), SR._s740_nl(b[1]), str(b[2]))) or {}).get("answer") == "no":
                S.s740_no.add(int(f["bill_id"]))
    except Exception as e:                                     # noqa: BLE001 -- his day never waits on it
        print("amir_day S740: the returns could not be read: %s" % str(e)[:200], file=sys.stderr)
    _derive(S)
    return S


S740_MORE_A = ("<p class=good><b>Bill par wapsi likhi ho to: poora bill aur purchase return. Warna: yeh line Marg mein jodiye.</b></p>")
S740_MORE_B = ("<p class=good><b>Bill ke item Marg se milaiye. Bill par wapsi likhi ho to: poora bill aur purchase return. "
               "Warna: chhooti line Marg mein jodiye.</b></p>")
S740_ASKED = ("<p class=good><b>Reception se poochha gaya hai ki bill par wapsi likhi hai ya nahi. Wapsi ho to abhi Marg mat badaliye &mdash; "
              "dealer ka kaagaz aane tak. Warna: %s</b></p>")
S740_NO = "<p class=good><b>Bill ki yeh line Marg mein nahi hai. Jodiye, aur Marg mein bill &#8377;%s kijiye.</b></p>"
_s738_card_before_s740 = _s738_card


def _s738_card(fx):                                           # noqa: F811 -- S740: the "more" card's words by reception's answer
    h = _s738_card_before_s740(fx)
    no = getattr(_S740_NO_BILLS, "v", None) or set()
    for f in fx:
        if f.get("kind") != "more":
            continue
        mark = "<div class=bill data-s738='%d'>" % int(f["bill_id"])
        i = h.find(mark)
        if i < 0:
            continue
        j = h.find("<div class=bill data-s738=", i + len(mark))
        j = len(h) if j < 0 else j
        part = h[i:j]
        if int(f["bill_id"]) in no:
            new = S740_NO % _esc(_s738_rs(f.get("paper_p")))
            part = part.replace(S740_MORE_A, new, 1).replace(S740_MORE_B, new, 1)
        else:
            part = part.replace(S740_MORE_A, S740_ASKED % "yeh line Marg mein jodiye.", 1).replace(S740_MORE_B, S740_ASKED % "chhooti line Marg mein jodiye.", 1)
        h = h[:i] + part + h[j:]
    return h


import threading as _s740_threading                        # noqa: E402
_S740_NO_BILLS = _s740_threading.local()                      # per worker thread: the bills reception answered "Nahi"


def _s740_card(rets):
    out = []
    for r in rets:
        if r["kind"] == "on_bill":
            head = ("<div class=who>%s &middot; Bill %s</div><div style='font-size:15px'><b>Bill ki tareekh: %s</b> &middot; wapsi &#8377;%s</div>"
                    % (_esc(r["supplier"]), _esc(r["bill_no"]), _esc(_ddmmyyyy(r["date"])), _esc(_s738_rs(r["amount_p"]))))
        elif r["kind"] == "own":
            head = ("<div class=who>%s</div><div style='font-size:15px'>%s &middot; kaagaz nahi</div>" % (_esc(r["supplier"]), _esc(r.get("item") or "")))
        else:
            head = ("<div class=who>%s &middot; Purchase return %s</div><div style='font-size:15px'><b>Tareekh: %s</b> &middot; &#8377;%s</div>"
                    % (_esc(r["supplier"]), _esc(r["bill_no"]), _esc(_ddmmyyyy(r["date"])), _esc(_s738_rs(r["amount_p"]))))
        body = ("<p class=good><b>%s</b></p>" % (r.get("hi") or "") if r.get("stage") in S740_DO else
                "<p style='margin:6px 0 0;color:#1b1b1b;font-size:15px'><b>%s</b></p>" % (r.get("hi") or ""))
        links = []
        if r.get("scan") is not None:
            links.append("<a class='btn plain' style='display:inline-block;width:auto;margin:0 6px 0 0' href='/finance/purchase/api/s738/scan/%d' "
                         "target=_blank rel=noopener>Kaagaz dekhiye</a>" % int(r["scan"]))
        if r.get("revised"):
            links.append("<a class='btn plain' style='display:inline-block;width:auto;margin:0' href='/finance/purchase/api/s738/scan/%d' "
                         "target=_blank rel=noopener>Naya bill dekhiye</a>" % int(r["revised"]["scan"]))
        out.append("<div class=bill data-s740='%s'>%s%s%s</div>" % (_esc(r["key"]), head, body, "".join(links)))
    return ("<div class=line id=s740><span class=big>Wapsi baaki &middot; %d</span>"
            "<p class=sub>Har wapsi yahan rahegi jab tak dealer ka credit note ya naya bill na aa jaye.</p>%s</div>" % (len(rets), "".join(out)))


_card_rows_before_s740 = _card_rows


def _card_rows(S):                                            # noqa: F811
    _S740_NO_BILLS.v = set(getattr(S, "s740_no", None) or set())
    try:
        rows = _card_rows_before_s740(S)
    finally:
        _S740_NO_BILLS.v = None
    rets = getattr(S, "s740", None) or []
    if not rets:
        return rows
    n_do = sum(1 for r in rets if r.get("stage") in S740_DO)
    try:
        card = _s740_card(rets)
    except Exception as e:                                     # noqa: BLE001 -- his page never breaks on it
        print("amir_day S740: the card could not be drawn: %s" % str(e)[:200], file=sys.stderr)
        return rows
    add = [("s740", card, "returns pending: %d (%d to enter)" % (len(rets), n_do), bool(n_do))]
    at = 0
    for i, r in enumerate(rows):
        if r[0] in ("stage", "sunday", "fixes", "scans", "s738", "s738ok"):
            at = i + 1
    return rows[:at] + add + rows[at:]


_settle_before_s740 = settle


def settle(cx, S, needs_you=False):                           # noqa: F811
    out = _settle_before_s740(cx, S, needs_you)
    if getattr(S, "s740_ok", False):
        try:
            import scan_register as SR                         # noqa: PLC0415
            try:
                SR.s740_sync(cx)
            except Exception:                                  # noqa: BLE001
                cx.rollback()
                raise
        except Exception as e:                                 # noqa: BLE001
            print("amir_day S740: the returns could not be kept: %s" % str(e)[:200], file=sys.stderr)
    return out
# ---- S740 end ---------------------------------------------------------------------------------------------------------------------------



# ---- S749 (08-Nov-2026, Sanjeevni session 405, kit S749_ONE_SOURCE; D865): one source on Amir's side too --------------------------------------
#  (1) A ROUND-OFF on his card: a bill whose paper and Marg differ by exactly one rupee (scan_register.s738_fixes kind 'roundoff') says
#      "Marg mein bill <paper> kijiye (round-off)" -- every rupee is corrected in Marg; proved only by his export, as before.
#  (2) The owner's English summary (/finance/amir/day) reads HIS list: "Marg sudhar: N bills to correct (the bills) · Wapsi baaki: N · proved
#      by his exports ✓ N (14 days) · bills waiting for entry: N" -- from scan_register.s738_fixes / s738_tracked / s740_pending and
#      purchase_app.scans_for_amir, the same readers his own page uses. Reads only.
KIT_S749 = "S749_ONE_SOURCE"
_s738_card_before_s749 = _s738_card


def _s738_card(fx):                                           # noqa: F811 -- S749: the round-off card
    rnd = [f for f in fx if f.get("kind") == "roundoff"]
    rest = [f for f in fx if f.get("kind") != "roundoff"]
    h = _s738_card_before_s749(rest) if rest else ""
    if not rnd:
        return h
    out = []
    for f in rnd:
        head = "<div class=who>%s &middot; Bill %s</div><div style='font-size:15px'><b>Bill ki tareekh: %s</b></div>" % (
            _esc(f["supplier"]), _esc(f["bill_no"]), _esc(_ddmmyyyy(f["date"])))
        body = ("<div style='font-size:15px'>Marg mein &#8377;%s &middot; kaagaz par &#8377;%s &mdash; <b class=bad>&#8377;%s ka round&#8209;off</b></div>"
                "<p class=good><b>Marg mein bill &#8377;%s kijiye (round&#8209;off)</b></p>"
                % (_esc(_s738_rs(f["marg_p"])), _esc(_s738_rs(f["paper_p"])), _esc(_s738_rs(abs(int(f["diff_p"])))), _esc(_s738_rs(f["paper_p"]))))
        link = ("<a class='btn plain' style='display:inline-block;width:auto;margin:0' href='/finance/purchase/api/s738/scan/%d' target=_blank "
                "rel=noopener>Kaagaz dekhiye</a>" % int(f["scan"]) if f.get("scan") is not None else "")
        out.append("<div class=bill data-s738='%d'>%s%s%s</div>" % (int(f["bill_id"]), head, body, link))
    block = "".join(out)
    if h:
        # the round-off cards join the correction card, and its count carries them
        h = h.replace("Purchase bill Marg mein theek karein &middot; %d" % len(rest), "Purchase bill Marg mein theek karein &middot; %d" % len(fx), 1)
        i = h.rfind("<p class=sub style='background:#eef0f4")
        return (h[:i] + block + h[i:]) if i > 0 else (h + block)
    return ("<div class=line id=s738><span class=big>Purchase bill Marg mein theek karein &middot; %d</span>"
            "<p class=sub>Har bill ka kaagaz saath mein hai. Marg mein kaagaz jaisa kijiye &mdash; round-off bhi.</p>%s"
            "<p class=sub style='background:#eef0f4;border-radius:8px;padding:8px'>Theek karne ke baad aaj ki report export (step 4) kijiye &mdash; "
            "Marg mein sahi aate hi line khud hat jayegi.</p></div>" % (len(fx), block))


def _s749_owner_card(cx):
    """The owner's English card: his list as his page carries it. Reads only; a fault is one line."""
    try:
        import scan_register as SR                             # noqa: PLC0415
        fx = SR.s738_fixes(cx, fast=True)
        names = ", ".join("%s %s" % (f["supplier"].title(), f["bill_no"]) for f in fx[:8]) + (" and %d more" % (len(fx) - 8) if len(fx) > 8 else "")
        rets = [r for r in SR.s740_pending(cx)]
        rnames = ", ".join("%s %s" % (r["supplier"].title(), r.get("bill_no") or r.get("item") or "") + (" (dealer's paper awaited)" if r.get("stage") == "waiting" else "")
                           for r in rets[:6])
        cut = (datetime.now(IST).replace(tzinfo=None) - timedelta(days=14)).replace(microsecond=0).isoformat()
        proved = sum(1 for t in SR.s738_tracked(cx).values() if t.get("settled_at") and str(t["settled_at"]) >= cut)
        try:
            import purchase_app                                # noqa: PLC0415
            waiting = len(purchase_app.scans_for_amir(cx).get("list") or [])
        except Exception:                                      # noqa: BLE001
            waiting = -1
        return ("<div class=card id=s749amir><h2>Amir -- his list today</h2>"
                "<div class=line>Marg sudhar: <b>%d</b> bill%s to correct%s</div>"
                "<div class=line>Wapsi baaki: <b>%d</b>%s</div>"
                "<div class=line>Proved by his exports (14 days): <b>%d</b> &#10003;</div>"
                "<div class=line>Bills scanned, waiting for his entry: <b>%s</b></div>"
                "<p class=sub>The same list his page carries. A correction leaves only when his export shows Marg = the paper.</p>"
                "<div class=line><a href='/finance/purchase/page/check'>Your purchase check</a> &middot; <a href='/finance/amir/step/6'>his card</a></div></div>"
                % (len(fx), "" if len(fx) == 1 else "s", (" (%s)" % _esc(names)) if names else "", len(rets), (" (%s)" % _esc(rnames)) if rnames else "",
                   proved, waiting if waiting >= 0 else "not read"))
    except Exception as e:                                     # noqa: BLE001
        return "<div class=card id=s749amir><h2>Amir -- his list today</h2><div class=line>not read: %s</div></div>" % _esc(str(e)[:120])


_shell_before_s749 = _shell


def _shell(title, body, head_extra=""):                       # noqa: F811 -- S749: the owner's day page carries Amir's list
    if title == "Amir's day" and "<div class=card id=s444salt>" in body:
        try:
            cx = _db()
            body = body.replace("<div class=card id=s444salt>", _s749_owner_card(cx) + "<div class=card id=s444salt>", 1)
        except Exception as e:                                 # noqa: BLE001
            print("amir_day S749: the owner's card could not be drawn: %s" % str(e)[:200], file=sys.stderr)
    return _shell_before_s749(title, body, head_extra)
# ---- S749 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S750 (08-Nov-2026, Sanjeevni session 406, kit S750_MONTH_END; D849): the bill the owner accepted from a dealer's summary -----------------
#  When the owner ACCEPTS a dealer's summary that lists a bill Marg does not carry (row 7 of his step view), Amir's page gets one card:
#  "Dealer ke hisaab par yeh bill hai, Marg mein nahi -- kaagaz aane par entry karein", one line per bill (dealer, number, date, amount).
#  The line leaves by itself when Marg carries the bill (scan_register.s750_amir_enter reads the one register). Reads only; nothing here
#  changes Amir's Aaj ka kaam list (D690) or any Marg figure.
KIT_S750 = "S750_MONTH_END"
_state_before_s750 = state
_card_rows_before_s750 = _card_rows


def state(cx, day, who="", step=None, owner=False):           # noqa: F811 -- S750: the accepted bills Amir is to enter
    S = _state_before_s750(cx, day, who, step, owner)
    S.s750 = []
    try:
        import scan_register as SR                             # noqa: PLC0415
        S.s750 = SR.s750_amir_enter(cx)
    except Exception as e:                                     # noqa: BLE001 -- his day never waits on it
        print("amir_day S750: the accepted bills could not be read: %s" % str(e)[:200], file=sys.stderr)
    return S


def _s750_card(items):
    out = []
    for i in items:
        out.append("<div class=bill data-s750='%s'><div class=who>%s &middot; Bill %s</div><div style='font-size:15px'><b>Bill ki tareekh: %s</b> &middot; <b>&#8377;%s</b></div>"
                   "<p class=good><b>Dealer ke %s ke hisaab par yeh bill hai, Marg mein nahi &mdash; kaagaz aane par Marg mein entry karein.</b></p></div>"
                   % (_esc("%s|%s" % (i["dealer"], i["no"])), _esc(str(i["name"]).title()), _esc(i["no"] or "?"), _esc(_ddmmyyyy(i["date"]) if i.get("date") else "?"),
                      _esc(_s738_rs(int(i["amount_p"] or 0))), _esc(_s750_hi_month(i.get("month")))))
    return ("<div class=line id=s750><span class=big>Dealer ke hisaab ka bill, Marg mein nahi &middot; %d</span>"
            "<p class=sub>Doctor sahab ne dealer ka hisaab maan liya hai. Bill ka kaagaz aane par Marg mein entry karein; Marg mein aate hi line khud hat jayegi.</p>%s</div>"
            % (len(items), "".join(out)))


def _s750_hi_month(ym):
    names = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    try:
        return "%s %s" % (names[int(ym[5:7]) - 1], ym[:4])
    except (TypeError, ValueError, IndexError):
        return str(ym or "")


def _card_rows(S):                                            # noqa: F811 -- S750
    rows = _card_rows_before_s750(S)
    items = getattr(S, "s750", None) or []
    if not items:
        return rows
    at = 0
    for i, r in enumerate(rows):
        if r[0] in ("stage", "sunday", "fixes", "scans", "s738", "s738ok"):
            at = i + 1
    return rows[:at] + [("s750", _s750_card(items), "dealer summary bills to enter: %d" % len(items), True)] + rows[at:]
# ---- S750 end --------------------------------------------------------------------------------------------------------


# ---- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D995) -------------------------------------------------------------------------
#  A scan still on his enter list after Marg's purchases moved the owner's days past its bill becomes ONE QUESTION, first on his card: the scan,
#  the dealer's likely Marg bill with its own scan and lines, one-tap answers (scan_ask.amir_view). While asked it leaves his plain enter list
#  (step 2 and the card's count). His tap is 'sna:<scan>:<answer>:<bill>' (step(), before every other job). Fail-soft: without scan_ask, as before.
_state_before_s849 = state


def state(cx, day, who="", step=None, owner=False):           # noqa: F811 -- S849
    S = _state_before_s849(cx, day, who, step, owner)
    S.s849 = []
    try:
        import scan_ask                                        # noqa: PLC0415
        ids, S.s849 = scan_ask.amir_view(cx)
        if ids:
            S.scans = [b for b in (S.scans or []) if int(b.get("id") or 0) not in ids]
    except Exception as e:                                     # noqa: BLE001 -- his day never waits on it
        print("amir_day S849: the questions could not be read: %s" % str(e)[:200], file=sys.stderr)
    return S


_card_rows_before_s849 = _card_rows


def _card_rows(S):                                            # noqa: F811 -- S849: the questions first on his card
    rows = _card_rows_before_s849(S)
    q = getattr(S, "s849", None) or []
    return [("s849", h, "a scanned bill not found in Marg", True) for h in q] + rows
# ---- S849 end ---------------------------------------------------------------------------------------------------------------------------
