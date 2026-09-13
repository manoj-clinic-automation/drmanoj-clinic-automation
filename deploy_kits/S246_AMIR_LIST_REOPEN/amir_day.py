"""
amir_day.py -- Amir's day, as seven steps on a phone.  (S241, D472)

One page, one thing at a time, a 1 -> 7 banner at the top, a confirmation after
each step, and a DAY CLOSED screen at the end.  The owner's design is in
claude/S240_AMIR_DAY_FLOW.md; the rulings behind it are D468-D477.

Principles this file is built to, and must keep:

  * He is never asked whether a report arrived.  The server reads the exports it
    already holds and TELLS him.  (D469, and "never let him certify what the
    system can verify".)
  * The bill list fills itself from the bill-wise export.  He types no bill
    number, ever.
  * The disposition of a bill is FORCED, not optional -- an optional flag is the
    one a hurried person walks past.
  * A day he leaves half-done stays OPEN, never failed.  Everything done is kept
    and the remainder comes back as "pichhla baaki".
  * Attendance never blocks his work.  Step 1 nudges; it does not gate.
  * He raises a claim; he never chases one.  Chasing is Darpan's queue.

No JavaScript.  Server-rendered HTML, phone first.  Amir's screens are Hinglish
in Latin script; the owner's view of the same day is English.

Schema is additive and lazy (F-303): created on first request, never at import.

S243_AMIR_VISIT (owner ruling 13-Sep-2026):
  * Once his salt tasks are ticked the server asks HIM for Marg's SALT WISE ITEM
    LIST and keeps it raised (red to him, amber to the owner) until the list is seen
    to arrive -- read from the mi_file row the one door writes, never asked.  It is
    a PROMPT, not a gate: the day's OPEN/CLOSED state does not depend on it.
  * "Amir's visit -- what was done": one readable summary for the owner, as JSON at
    /finance/amir/day/api/visit-summary (checker only) and as a collapsed block on
    /finance/amir/day and on the hub's Marg card.

S244_AMIR_PROCESSING (owner ruling 13-Sep-2026):
  * A report he has just exported is PROCESSING, not missing.  Saying "aaj ki nahi
    aayi" while a fresh file is still in transit is what made him export the same
    report three times on 13-Sep.  Step 4 now says: ban rahi hai -> jaanch poori ->
    and only then names what still has to be generated.
  * Processing never holds him up.  While a report is on its way step 4 is skipped
    by the "where did I leave off" jump and carries a button straight to step 5, so
    he starts his next task and the server keeps checking on its own.
  * Step 3 prints the two dates he must type into Marg, so the TO date cannot be
    yesterday's by habit.

S245_AMIR_BILLTAP (owner ruling 13-Sep-2026):
  * Step 5 was five radio buttons on every bill, all open at once -- forty choices on
    one phone screen for a normal day.  It is now ONE tap per bill: "Theek hai", or
    "Theek nahi", and the four reasons appear only when he says it is not right.
  * The reasons live in a <details>, so this is still a page with no JavaScript, and
    the answer is still one radio group per bill -- the form the server reads is
    unchanged, byte for byte.
  * `required` is gone from the radios ON PURPOSE: a required control inside a closed
    <details> cannot be focused, and the browser then refuses the whole submit without
    saying why.  The forcing was never the browser's job -- an unanswered bill is
    simply not written and comes straight back on the list, which is stronger.

S246_AMIR_LIST_REOPEN (owner rulings 13-Sep-2026):
  * WHAT THE LIST HOLDS: purchase bills dated on or after BILLS_FROM only -- everything
    before that is settled and is never shown again -- and a bill he marked NOT ok STAYS
    on the list until he marks it Theek hai.  It sits in its own band, never holds the
    day open (a credit note can take a fortnight), and marking it Theek hai settles the
    claim Darpan was chasing.
  * A bill rides in every cumulative 1st-to-date export after the one that first carried
    it, so the rows are grouped by the bill itself.  Without that, the moment there is
    more than one export a single unanswered bill is listed -- and COUNTED, in the gate
    that decides whether a day can close -- once per export it appears in.
  * DIN BAND IS NOT A DEAD END.  Every step in the banner is a link, the closed screen
    names the places he may want and says when a new bill has arrived since, and the day
    can be opened again -- recorded, never silently.
"""

import html
import json
import os
import re
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request, redirect, url_for

bp = Blueprint("amir_day", __name__)

_db = None
_require = None
_unit = "medical"
# Any role on the unit may open his own day.  The medical unit has one maker and
# one checker and four viewers, so gating on maker/checker would have shut Amir
# out of his own screen.  Every write records who made it (`by_user`), so the
# record stays attributable at the wider gate.
_roles = ("maker", "checker", "viewer")

IST = timezone(timedelta(hours=5, minutes=30))

# The two reports that make up the daily pair (D469).  One carries the supplier
# and what was supplied; the other carries the bill number and its details.
PAIR = (
    ("ITEMWISE", "Item-detail purchase report"),
    ("BILLWISE", "Bill-wise purchase report"),
)

REASONS = (
    ("ok",        "Theek hai"),
    ("short",     "Kam maal aaya"),
    ("nodeal",    "Deal nahi mili"),
    ("discount",  "Discount kam"),
    ("other",     "Aur koi baat"),
)
REASON_MAP = dict(REASONS)

# A disposition that is not "ok" raises a claim for Darpan to chase (D471).
CLAIM_REASONS = ("short", "nodeal", "discount", "other")

STEPS = (
    (1, "Punch"),
    (2, "Bill entry"),
    (3, "Export"),
    (4, "Check"),
    (5, "Bills"),
    (6, "Salt/naam"),
    (7, "Band"),
)

# Steps that decide whether a day is finished (correction 4).  Step 1 is a
# nudge, step 3 is an instruction, step 7 is the close itself.
GATE_STEPS = (2, 4, 5, 6)

# S243_AMIR_VISIT: the Marg export that proves his salt work reached Marg.  marg_ingest
# rows every file the one door takes in mi_file with this type; salts_refresh.py (cron,
# every 10 min) then applies the newest kept one to the salts page and writes its state.
SALT_LIST_TYPE = "SALT_WISE_ITEM_LIST"
SALTS_STATE = os.environ.get("SALTS_REFRESH_STATE", "/root/finance/salts_refresh.state.json")
_STAMP14 = re.compile(r"^(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})$")
_STAMP_IN_NAME = re.compile(r"__(\d{8}-\d{6})__")

# S244: how long a freshly exported report is allowed to be in transit before the
# screen stops saying "ban rahi hai" and starts saying "dobara banaiye".  Marg writes
# the file, MargPull picks it up and the door takes it in; ~5 minutes end to end on a
# normal day.  The clock starts when HE says he has exported (the step 3 tick, which
# is rewritten every time he asks for another look), never when the page is opened.
try:
    EXPORT_GRACE_MIN = int(os.environ.get("AMIR_EXPORT_GRACE_MIN") or 6)
except (TypeError, ValueError):
    EXPORT_GRACE_MIN = 6
if EXPORT_GRACE_MIN < 1 or EXPORT_GRACE_MIN > 60:
    EXPORT_GRACE_MIN = 6

# How often the step 4 screen re-checks itself while a report is in transit.
EXPORT_POLL_SEC = 20

# S246: everything before this date is settled and is never put in front of him again
# (owner, 13-Sep-2026).  Move it the next time a period is settled; env AMIR_BILLS_FROM.
BILLS_FROM = (os.environ.get("AMIR_BILLS_FROM") or "").strip() or "2026-09-01"
if not re.match(r"^\d{4}-\d{2}-\d{2}$", BILLS_FROM):
    BILLS_FROM = "2026-09-01"


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------

def _now():
    return datetime.now(IST)


def _today():
    return _now().strftime("%Y-%m-%d")


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _hhmm(s):
    """Show a stored timestamp as HH:MM, whatever shape it arrived in."""
    if not s:
        return ""
    s = str(s).replace("T", " ")
    m = _STAMP14.match(s)                     # S243: Marg's own YYYYMMDD-HHMMSS export stamp
    if m:
        s = "%s-%s-%s %s:%s:%s" % m.groups()
    return s[11:16] if len(s) >= 16 else s


def _mins_since(ts):
    """Whole minutes from a stored stamp to now, or None if it cannot be read."""
    t = _norm_ts(ts)
    if not t:
        return None
    try:
        d = datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=IST)
    except (TypeError, ValueError):
        return None
    return max(0, int((_now() - d).total_seconds() // 60))


def _ddmmyyyy(day):
    """'2026-09-13' -> '13-09-2026' -- the shape Marg's own date boxes use."""
    d = str(day or "")
    if len(d) != 10:
        return d
    return "%s-%s-%s" % (d[8:10], d[5:7], d[:4])


def _month_first(day):
    return (str(day or "")[:8] + "01") if len(str(day or "")) == 10 else ""


def _esc(v):
    return html.escape("" if v is None else str(v))


def _rupees(paise):
    try:
        p = int(paise or 0)
    except (TypeError, ValueError):
        return ""
    return "{:,}".format(round(p / 100.0))


def _ensure(cx):
    """Additive, lazy, idempotent (F-303)."""
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_day(
        day        TEXT PRIMARY KEY,
        opened_at  TEXT,
        closed_at  TEXT,
        closed_by  TEXT
    )""")
    # S246: a day that was closed can be opened again, and the record says so rather
    # than pretending it was never closed.  Additive, lazy, idempotent (F-303).
    _cols = {r[1] for r in cx.execute("PRAGMA table_info(amir_day)").fetchall()}
    for _c in ("reopened_at", "reopened_by"):
        if _c not in _cols:
            cx.execute("ALTER TABLE amir_day ADD COLUMN %s TEXT" % _c)
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_step(
        day        TEXT NOT NULL,
        step       INTEGER NOT NULL,
        done_at    TEXT,
        by_user    TEXT,
        PRIMARY KEY(day, step)
    )""")
    cx.execute("""CREATE TABLE IF NOT EXISTS amir_bill_disposition(
        supplier_norm TEXT NOT NULL,
        bill_no       TEXT NOT NULL,
        bill_date     TEXT NOT NULL,
        day           TEXT,
        reason        TEXT NOT NULL,
        by_user       TEXT,
        at            TEXT,
        PRIMARY KEY(supplier_norm, bill_no, bill_date)
    )""")
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
    cx.execute("CREATE INDEX IF NOT EXISTS ix_amir_disp_day ON amir_bill_disposition(day)")


def _table_exists(cx, name):
    r = cx.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return r is not None


def _norm_ts(s):
    """Any stored time -> 'YYYY-MM-DD HH:MM:SS' so three writers' stamps compare as text.

    marg_ingest keeps the capture stamp as YYYYMMDD-HHMMSS and received_at as ISO with
    the zone; purchase_app writes done_at as ISO with a 'T'; amir_salts with a space.
    """
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


def _dm_hm(ts):
    """'2026-09-13 08:12:00' -> '13-09 08:12' -- day-month and the time, for a phone line."""
    t = _norm_ts(ts)
    if not t:
        return ""
    return "%s-%s %s" % (t[8:10], t[5:7], t[11:16])


def _export_day_sql(p=""):
    """The DAY of a purchase_export row, in SQL, from Marg's own stamp -- both shapes.

    S243 fix: the door writes export_stamp as YYYYMMDD-HHMMSS (purchase_app STAMP_RE), so
    the S241 substr(...,1,10) = 'yyyy-mm-dd' could never match a real export; step 4 could
    never verify and every bill of the day read as carried.  `p` is the table alias prefix.
    """
    s, r = p + "export_stamp", p + "received_at"
    return ("CASE WHEN %s GLOB '[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-*' "
            "THEN substr(%s,1,4)||'-'||substr(%s,5,2)||'-'||substr(%s,7,2) "
            "ELSE substr(COALESCE(%s, %s), 1, 10) END" % (s, s, s, s, s, r))


def _salt_list_state(cx, day):
    """Marg's SALT WISE ITEM LIST against his salt ticks.  A PROMPT, never a gate (13-Sep ruling).

    pending -- ticks exist (up to the end of `day`) that no list has followed: raise it,
               red to him, amber to the owner, until a newer list is seen.
    fresh   -- a list arrived after the ticks of `day`: green, with the arrival time.
    Everything here is READ: purchase_salt_task (his ticks), mi_file (the door's record of
    every SALT_WISE_ITEM_LIST it took), salts_refresh's state file (applied to the salts page).
    Nothing here changes done[6] or the day's OPEN/CLOSED state.
    """
    end = day + " 23:59:59"
    st = {"ticks_day": 0, "ticked_by": [], "last_tick": None, "since_list": 0,
          "last_list": None, "list_verdict": "", "lists_day": 0,
          "pending": False, "fresh": False,
          "applied_at": None, "applied_file": "", "applied_stamp": None, "applied_as_on": ""}
    ticks = []
    if _table_exists(cx, "purchase_salt_task"):
        for r in cx.execute("SELECT done_at, done_by FROM purchase_salt_task "
                            "WHERE COALESCE(done, 0) = 1 AND done_at IS NOT NULL").fetchall():
            t = _norm_ts(r["done_at"])
            if t and t <= end:
                ticks.append((t, r["done_by"] or ""))
        st["ticks_day"] = sum(1 for t, _b in ticks if t[:10] == day)
        st["ticked_by"] = sorted({b for t, b in ticks if t[:10] == day and b})
        if ticks:
            st["last_tick"] = max(t for t, _b in ticks)
    if _table_exists(cx, "mi_file"):
        lists = []
        for r in cx.execute("SELECT stamp, received_at, verdict FROM mi_file WHERE type = ?",
                            (SALT_LIST_TYPE,)).fetchall():
            t = _norm_ts(r["stamp"]) or _norm_ts(r["received_at"])
            if t:
                lists.append((t, r["verdict"] or ""))
        if lists:
            t, v = max(lists)
            st["last_list"], st["list_verdict"] = t, v
            st["lists_day"] = sum(1 for t2, _v in lists if t2[:10] == day)
    if st["last_tick"]:
        if st["last_list"] is None or st["last_list"] < st["last_tick"]:
            st["pending"] = True
            st["since_list"] = sum(1 for t, _b in ticks
                                   if st["last_list"] is None or t > st["last_list"])
        elif st["ticks_day"]:
            st["fresh"] = True
    try:
        with open(SALTS_STATE, encoding="utf-8") as fh:
            j = json.load(fh)
        if isinstance(j, dict) and j.get("ok"):
            st["applied_at"] = _norm_ts(j.get("applied_at"))
            st["applied_file"] = str(j.get("file") or "")[:100]
            st["applied_as_on"] = str(j.get("as_on") or "")[:10]
            m = _STAMP_IN_NAME.search(st["applied_file"])
            if m:
                st["applied_stamp"] = _norm_ts(m.group(1))
    except (OSError, ValueError, TypeError):
        pass
    return st


def _salt_prompt_amir(w):
    """His line, Hinglish: red until the list is seen, green with the time once it is."""
    s = w.get("salt_list") or {}
    if s.get("pending"):
        when = ("aakhri list %s ki thi" % _dm_hm(s["last_list"])) if s.get("last_list") \
            else "abhi tak koi list nahi aayi"
        return ("<div class=line><span class='big bad'>Marg se SALT WISE ITEM LIST nikaalo "
                "&mdash; yahan khud tick ho jayegi</span><br>"
                "<span class=sub>%d kaam tick hue, list abhi nahi aayi &middot; %s</span></div>"
                % (int(s.get("since_list") or 0), _esc(when)))
    if s.get("fresh"):
        return ("<div class=line><span class='big good'>SALT WISE ITEM LIST aa gayi &#10003; %s"
                "</span><br><span class=sub>Aaj ke %d tick ke baad. Kuch karna nahi hai.</span></div>"
                % (_esc(_dm_hm(s.get("last_list"))), int(s.get("ticks_day") or 0)))
    return ""


def _salt_owner_line(s):
    """The same fact in English for the owner: (css class, one line)."""
    s = s or {}
    if s.get("pending"):
        last = (" (last list %s)" % _dm_hm(s["last_list"])) if s.get("last_list") else " (no list seen yet)"
        return "warn", ("Waiting for Marg's SALT WISE ITEM LIST -- %d salt task%s ticked since the last list%s. "
                        "Amir is asked for it on his screen." % (int(s.get("since_list") or 0),
                                                                  "" if s.get("since_list") == 1 else "s", last))
    if s.get("fresh"):
        return "good", ("Salt list arrived %s, after the day's %d tick%s."
                        % (_dm_hm(s.get("last_list")), int(s.get("ticks_day") or 0),
                           "" if s.get("ticks_day") == 1 else "s"))
    if s.get("last_list"):
        return "", "No salt ticks on this day. Last list from Marg %s." % _dm_hm(s["last_list"])
    return "", "No salt ticks on this day. No SALT WISE ITEM LIST seen yet."


# --------------------------------------------------------------------------
# what the server already knows
# --------------------------------------------------------------------------

def _export_state(cx, day, wait_since=None):
    """Did today's pair arrive, is each one verified -- and is one still on its way?

    Read from purchase_export, which the ingest already fills.  Nothing here
    asks Amir anything -- it reports.  A report counts for today only if its
    export stamp falls on today AND it covers the 1st of the month to date.

    S244: every entry also carries a `state`, and `have` stays exactly what it
    always was (state == "ok"), so every gate built on it is unchanged.

        ok    verified -- arrived, today's stamp, 1st to date
        wait  he has exported and the grace window has not run out yet
        bad   the window ran out, or a file of his DID arrive and is wrong
        none  he has not said he exported yet -- nothing is expected

    `wait_since` is the step 3 tick: the moment he last said the export was taken.
    """
    waited = _mins_since(wait_since) if wait_since else None
    within = (waited is not None) and (waited < EXPORT_GRACE_MIN)
    ws = _norm_ts(wait_since) if wait_since else None

    out = []
    if not _table_exists(cx, "purchase_export"):
        for kind, label in PAIR:
            out.append({"kind": kind, "label": label, "have": False, "state": "bad",
                        "waited": waited,
                        "reason": "purchase_export table not present yet"})
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
                state, why = "none", "abhi nikaali nahi gayi"
            elif within:
                state, why = "wait", "file ban gayi hai, server tak pahunch rahi hai"
            else:
                state, why = "bad", "aaj ki nahi aayi"
            out.append({"kind": kind, "label": label, "have": False,
                        "state": state, "waited": waited, "reason": why})
            continue
        d = dict(row)
        ok_from = (d.get("period_from") or "")[:10] <= first
        ok_to = (d.get("period_to") or "")[:10] >= day
        if not (ok_from and ok_to):
            # A file with the wrong period IS his file, so it is news, not silence.
            # If it landed after he last said "exported", tell him now -- waiting on a
            # file that has already arrived wrong is what wasted his morning.  If it is
            # older than that tick, his newer one may still be in transit.
            arrived = _norm_ts(d.get("export_stamp") or d.get("received_at"))
            fresh = bool(arrived and ws and arrived >= ws)
            if fresh or not within:
                state = "bad"
                why = "tareekh galat hai -- 1 tareekh se aaj tak chahiye"
            else:
                state = "wait"
                why = "file ban gayi hai, server tak pahunch rahi hai"
            out.append({"kind": kind, "label": label, "have": False,
                        "state": state, "waited": waited,
                        "rows": d.get("n_rows"),
                        "at": _hhmm(d.get("export_stamp") or d.get("received_at")),
                        "reason": why})
            continue
        out.append({"kind": kind, "label": label, "have": True, "state": "ok",
                    "waited": waited,
                    "rows": d.get("n_rows"),
                    "period": "%s se %s" % ((d.get("period_from") or "")[:10], (d.get("period_to") or "")[:10]),
                    "at": _hhmm(d.get("export_stamp") or d.get("received_at"))})
    return out


def _bills(cx, day):
    """The purchase bills that still want an answer.  (S246)

    Three lists, and only the first two hold the day open:

        today    first seen in an export OF TODAY, no answer yet
        carry    first seen on an earlier day, still no answer   -- pichhla baaki
        flagged  answered NOT ok and not yet put right: it STAYS until he marks it
                 Theek hai (owner, 13-Sep-2026), and it never holds a day open --
                 a supplier's credit note can take a fortnight.

    Bills dated before BILLS_FROM are settled and are never shown.

    The rows are grouped by the bill itself.  A bill rides in every cumulative
    1st-to-date export after the one that first carried it, so without the grouping a
    single unanswered bill is listed once per export it appears in -- and counted that
    many times in the gate that decides whether the day can close.  `seen_day` is the
    EARLIEST export that carried it, which is what makes pichhla baaki mean anything.

    The list still fills itself from the bill-wise export -- he types no bill number.
    """
    if not (_table_exists(cx, "purchase_bill") and _table_exists(cx, "purchase_export")):
        return [], [], []

    rows = cx.execute(
        """SELECT b.supplier_norm AS supplier_norm, b.bill_no AS bill_no,
                  b.bill_date AS bill_date, d.reason AS reason,
                  MAX(b.supplier)  AS supplier,
                  MAX(b.amount_p)  AS amount_p,
                  MAX(d.at)        AS flagged_at,
                  MIN(""" + _export_day_sql("e.") + """) AS seen_day
             FROM purchase_bill b
             JOIN purchase_export e ON e.md5 = b.bw_md5
        LEFT JOIN amir_bill_disposition d
                  ON d.supplier_norm = b.supplier_norm
                 AND d.bill_no       = b.bill_no
                 AND d.bill_date     = b.bill_date
            WHERE (d.reason IS NULL OR d.reason <> 'ok')
              AND e.type = 'BILLWISE'
              AND b.bill_date >= ?
         GROUP BY b.supplier_norm, b.bill_no, b.bill_date, d.reason""",
        (BILLS_FROM,),
    ).fetchall()

    today_rows, carry, flagged = [], [], []
    for r in rows:
        d = dict(r)
        if d.get("reason"):
            flagged.append(d)
        elif d.get("seen_day") == day:
            today_rows.append(d)
        else:
            carry.append(d)
    for lst in (today_rows, carry, flagged):
        lst.sort(key=lambda x: ((x.get("bill_date") or ""), (x.get("supplier") or "")),
                 reverse=True)
    return today_rows, carry, flagged


def _work(cx, day):
    """Everything the day needs, gathered once."""
    ticks = {
        int(r["step"]): dict(r)
        for r in cx.execute("SELECT step, done_at, by_user FROM amir_step WHERE day=?", (day,)).fetchall()
    }
    # S244: the step 3 tick is the transit clock.  It is rewritten every time he asks
    # for another look, so "dobara banai" restarts the window instead of inheriting it.
    wait_since = (ticks.get(3) or {}).get("done_at")
    exports = _export_state(cx, day, wait_since)
    today_bills, carry_bills, flagged_bills = _bills(cx, day)
    closed = cx.execute("SELECT closed_at, closed_by, reopened_at, reopened_by "
                        "FROM amir_day WHERE day=?", (day,)).fetchone()

    done = {}
    done[1] = 1 in ticks
    done[2] = 2 in ticks
    done[3] = 3 in ticks
    done[4] = all(e["have"] for e in exports)          # proven, never ticked
    done[5] = (not today_bills) and (not carry_bills)
    done[6] = 6 in ticks
    done[7] = bool(closed and closed["closed_at"])
    waited = _mins_since(wait_since) if wait_since else None
    return {
        "day": day, "exports": exports, "today_bills": today_bills,
        "carry_bills": carry_bills, "flagged_bills": flagged_bills,
        "ticks": ticks, "done": done,
        "closed": dict(closed) if closed else None,
        "salt_list": _salt_list_state(cx, day),           # S243: a prompt, not a gate
        # S244: the three plain facts every screen asks about the pair
        "wait_since": wait_since,
        "waited_min": waited,
        "wait_left_min": (max(1, EXPORT_GRACE_MIN - waited) if waited is not None else None),
        "export_wait": any(e.get("state") == "wait" for e in exports),
        "export_bad": any(e.get("state") == "bad" for e in exports),
        "export_none": any(e.get("state") == "none" for e in exports),
    }


def _next_step(w):
    for n, _label in STEPS:
        if n == 7:
            continue
        # S244: a report still in transit must not park him on step 4.  The server is
        # doing the waiting; he goes on to the next thing and the banner stays amber.
        if n == 4 and w.get("export_wait") and not w["done"].get(4):
            continue
        if not w["done"].get(n):
            return n
    return 7


def _ready_to_close(w):
    return all(w["done"].get(n) for n in GATE_STEPS)


def _left(w):
    """Plain words for what is still missing -- used on the owner's card too."""
    out = []
    if not w["done"].get(2):
        out.append("bills not confirmed entered")
    waiting = [e["label"] for e in w["exports"] if e.get("state") == "wait"]
    missing = [e["label"] for e in w["exports"]
               if not e["have"] and e.get("state") != "wait"]
    if waiting:
        out.append("%s still arriving" % " and ".join(waiting))
    if missing:
        out.append("%s not verified" % " and ".join(missing))
    n = len(w["today_bills"]) + len(w["carry_bills"])
    if n:
        out.append("%d bill%s still to tap" % (n, "" if n == 1 else "s"))
    if not w["done"].get(6):
        out.append("salt and name list not ticked")
    return out


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

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
.good{color:var(--ok)}
.bad{color:var(--bad)}
.warn{color:var(--warn)}
.line{padding:10px 0;border-bottom:1px solid var(--line)}
.line:last-child{border-bottom:0}
.big{font-size:17px;font-weight:600}
.bill{border:1px solid var(--line);border-radius:10px;padding:12px;margin:0 0 12px}
.bill .who{font-weight:600}
.bill .meta{color:var(--soft);font-size:14px;margin:2px 0 10px}
.opts label{display:block;padding:11px 10px;border:1px solid var(--line);
            border-radius:8px;margin:0 0 7px;font-size:16px}
.opts input{margin-right:9px;transform:scale(1.25)}
/* S245: one tap per bill; the reasons stay shut until he says it is not right */
.bill .tap{display:block;padding:15px 13px;border:1px solid #bfe0c6;border-radius:10px;
           background:#f2f9f4;color:var(--ok);font-size:17px;font-weight:600;margin:0 0 8px}
.bill .tap input{margin-right:11px;transform:scale(1.35);vertical-align:-2px}
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


def _banner(current, w):
    out = ["<div class=steps>"]
    for n, label in STEPS:
        if n == current:
            cls = "on"
        elif w["done"].get(n):
            cls = "ok"
        elif n == 4 and w.get("export_wait"):
            cls = "wait"                                  # S244: amber while in transit
        else:
            cls = ""
        # S246: every step is a link.  DIN BAND used to be a dead end -- there was no
        # way back into any step once the day was closed.
        out.append("<a class='%s' href='/finance/amir/step/%d'>%d<br>%s</a>"
                   % (cls, n, n, _esc(label)))
    out.append("</div>")
    return "".join(out)


def _page(step, w, title, body, subtitle="", head_extra=""):
    head = "<h1>%s</h1>" % _esc(title)
    if subtitle:
        head += "<p class=sub>%s</p>" % _esc(subtitle)
    return _shell("Amir -- kaam", _banner(step, w) + head + body +
                  "<p class=foot>Step %d of 7</p>" % step, head_extra)


def _export_band(w):
    """One amber line carried on the later steps while the pair is not settled.

    It never blocks and never steals the screen -- it is there so a report that
    needs re-making is not forgotten between step 4 and the close.
    """
    if w["done"].get(4):
        return ""
    if w.get("export_bad"):
        return ("<div class=band><b>Ek report dobara banani hai.</b> "
                "<a href='/finance/amir/step/4'>Kholiye</a></div>")
    if w.get("export_wait"):
        return ("<div class=band>Report abhi ban rahi hai -- server dekh raha hai. "
                "<a href='/finance/amir/step/4'>Dekhiye</a></div>")
    return ""


def _denied():
    return _shell("Nahin khul saka",
                  "<div class=card><h2>Yeh page aapke liye nahin hai</h2>"
                  "<p>Apne login se kholiye, ya doctor sahab ko bataiye.</p>"
                  "</div>"), 403


def _go(step):
    return redirect(url_for("amir_day.step", n=step), code=303)


# --------------------------------------------------------------------------
# the steps
# --------------------------------------------------------------------------

def _step1(w):
    body = ("<div class=card><p class=big>Sabse pehle biometric punch kar lijiye.</p>"
            "<p>Punch ho gaya ho to neeche daba dijiye. Kaam yahin se shuru hoga.</p>"
            "<form method=post><input type=hidden name=tick value=1>"
            "<button class=btn name=go value=1>Punch ho gaya</button></form>"
            "<form method=post><input type=hidden name=tick value=1>"
            "<button class='btn quiet' name=go value=1>Punch nahi ho paya -- aage badhiye</button>"
            "</form></div>"
            "<p class=sub>Punch na hone se kaam nahi rukta. Doctor sahab ko dikh jata hai.</p>")
    return _page(1, w, "Punch", body)


def _step2(w):
    body = ("<div class=card><p class=big>Saare purchase aur purchase-return bill "
            "Marg mein daal dijiye -- bilkul jaisa bill par chhapa hai.</p>"
            "<p>Kuch theek mat kijiye, kuch round mat kijiye, kam maal aaya ho to bhi "
            "bill jaisa hai waisa hi daaliye. Kami agli screen par batayenge.</p>"
            "<form method=post><input type=hidden name=tick value=2>"
            "<button class=btn name=go value=2>Sab bill daal diye</button></form></div>")
    return _page(2, w, "Bill entry", body,
                 "Yahi ek niyam hai jis par baaki sab tika hai.")


def _dates_block(w):
    """The two dates he must type into Marg, spelled out. (S244)

    Every failure so far has been the same one: the TO box still holding yesterday.
    Printing today's date where he can read it off the phone costs nothing.
    """
    return ("<div class=dates><div class=sub>Marg mein yeh do tareekh daaliye:</div>"
            "<div class=line>FROM &nbsp; <span class=d>%s</span></div>"
            "<div class=line>TO &nbsp;&nbsp;&nbsp;&nbsp; <span class=d>%s</span> "
            "<span class=sub>(aaj)</span></div></div>"
            % (_esc(_ddmmyyyy(_month_first(w["day"]))), _esc(_ddmmyyyy(w["day"]))))


def _step3(w):
    rows = "".join("<div class=line><span class=big>%d. %s</span><br>"
                   "<span class=sub>1 tareekh se aaj tak</span></div>"
                   % (i + 1, _esc(label)) for i, (_k, label) in enumerate(PAIR))
    body = ("<div class=card><h2>Do report nikaaliye</h2>%s%s</div>"
            "<div class=note>Counter par bikri shuru hone se pehle. Der ho jaye to "
            "bhi nikaal dijiye -- chhodiye mat.<br>"
            "<b>TO ki tareekh aaj ki honi chahiye</b> -- kal ki nahi.</div>"
            "<form method=post><input type=hidden name=tick value=3>"
            "<button class=btn name=go value=3>Dono report nikaal di -- jaanch kijiye</button>"
            "</form>" % (rows, _dates_block(w)))
    return _page(3, w, "Export", body)


def _step4(w):
    """Processing -> processing done -> and only then, what is still to be made.

    S244.  The old screen had one message for two different situations: a file that
    was still crossing the wire read exactly like a file that was never made.  He
    trusted it and exported the same report three times.
    """
    waiting = bool(w.get("export_wait"))
    todo = [e for e in w["exports"] if e.get("state") == "bad"]
    notyet = [e for e in w["exports"] if e.get("state") == "none"]

    out = []
    for e in w["exports"]:
        st = e.get("state") or ("ok" if e.get("have") else "bad")
        if st == "ok":
            out.append("<div class=line><span class='big good'>%s &#10003;</span><br>"
                       "<span class=sub>%s &middot; %s rows &middot; %s baje</span></div>"
                       % (_esc(e["label"]), _esc(e.get("period", "")),
                          _esc(e.get("rows", "")), _esc(e.get("at", ""))))
        elif st == "wait":
            out.append("<div class=line><span class='big warn'>%s &hellip;</span><br>"
                       "<span class=sub>File ban gayi hai, server tak pahunch rahi hai.</span>"
                       "</div>" % _esc(e["label"]))
        elif st == "none":
            out.append("<div class=line><span class=big>%s</span><br>"
                       "<span class=sub>Abhi nikaali nahi gayi.</span></div>"
                       % _esc(e["label"]))
        else:
            out.append("<div class=line><span class='big bad'>%s &#10007;</span><br>"
                       "<span class=sub>%s</span></div>"
                       % (_esc(e["label"]), _esc(e.get("reason", ""))))

    if waiting:
        left = w.get("wait_left_min") or 1
        head = ("<div class=card><h2 class=warn>Report ban rahi hai&hellip;</h2>"
                "<p class=big>Server file le raha hai. Lagbhag <b>%d minute</b> aur.</p>"
                "<p>Aapko kuch nahi karna hai -- yeh screen khud dekhti rahegi.</p>"
                "</div>" % int(left))
    elif notyet and not todo:
        head = ("<div class=card><h2>Abhi report nikaali nahi gayi</h2>"
                "<p>Pehle dono report nikaal dijiye.</p>"
                "<p><a class='btn plain' href='/finance/amir/step/3'>"
                "Report nikaalne ka tarika</a></p></div>")
    else:
        head = ("<div class=card><h2 class=good>Jaanch poori ho gayi &#10003;</h2>"
                "<p>Server ne dono file khud padhi hai. Aapse kuch nahi poochha gaya.</p>"
                "</div>")

    body = head + "<div class=card><h2>Do report</h2>%s</div>" % "".join(out)

    if all(e["have"] for e in w["exports"]):
        body += ("<form method=post><button class=btn name=go value=4>Aage badhiye</button>"
                 "</form>")
    elif waiting:
        body += ("<form method=post><input type=hidden name=skip value=1>"
                 "<button class=btn name=go value=4>Aage ka kaam shuru kijiye</button></form>"
                 "<form method=post><button class='btn quiet' name=go value=4>"
                 "Abhi dobara dekhiye</button></form>"
                 "<p class=sub>Report aate hi yeh khud &#10003; ho jayegi. "
                 "Aap apna agla kaam kar sakte hain.</p>")
    elif todo:
        names = " aur ".join(_esc(e["label"]) for e in todo)
        body += ("<div class=note><p class=big>Dobara banaiye: %s</p>"
                 "<p><b>Pehle desktop par khuli Excel band kijiye</b> -- Marg file tab tak "
                 "dobara nahi likh sakta jab tak wo khuli hai.</p>%s</div>"
                 "<form method=post><input type=hidden name=again value=1>"
                 "<button class=btn name=go value=4>"
                 "Dobara banai -- phir se dekhiye</button></form>"
                 "<form method=post><input type=hidden name=skip value=1>"
                 "<button class='btn quiet' name=go value=4>"
                 "Aage ka kaam shuru kijiye</button></form>"
                 % (names, _dates_block(w)))

    refresh = ("<meta http-equiv=refresh content='%d'>" % EXPORT_POLL_SEC) if waiting else ""
    return _page(4, w, "Jaanch", body,
                 "Aapse nahi poochha ja raha. Server ne khud file padhi hai.",
                 head_extra=refresh)


def _bill_block(i, b):
    """One bill, one tap.  (S245)

    What he sees is two lines: *Theek hai* and *Theek nahi*.  The four reasons sit
    inside the second one and open only when he taps it -- a <details>, so the page
    still carries no JavaScript.  All five are the same radio group, so picking a
    reason un-picks *theek hai* by itself and the form the server reads is exactly
    the one it read before.
    """
    key = "%s|%s|%s" % (b["supplier_norm"], b["bill_no"], b["bill_date"])
    ok_label = REASON_MAP.get("ok", "Theek hai")
    why = "".join(
        "<label><input type=radio name='r_%d' value='%s'>%s</label>"
        % (i, _esc(code), _esc(label))
        for code, label in REASONS if code != "ok"
    )
    was = ""
    if b.get("reason"):
        # S246: a bill he already flagged carries what he wrote and when.  Theek hai
        # is how a flag is cleared -- nothing else on this screen clears one.
        when = _dm_hm(b.get("flagged_at"))
        was = ("<div class=was>Aapne likha tha: <b>%s</b>%s</div>"
               % (_esc(REASON_MAP.get(b["reason"], b["reason"])),
                  (" &middot; %s" % _esc(when)) if when else ""))
    return ("<div class=bill><div class=who>%s</div>"
            "<div class=meta>Bill %s &middot; %s &middot; &#8377;%s</div>%s"
            "<input type=hidden name='k_%d' value='%s'>"
            "<label class=tap><input type=radio name='r_%d' value='ok'>%s</label>"
            "<details class=notok><summary>Theek nahi</summary>"
            "<div class=why>%s</div></details></div>"
            % (_esc(b.get("supplier") or b.get("supplier_norm")),
               _esc(b["bill_no"]), _esc(b["bill_date"]), _esc(_rupees(b.get("amount_p"))),
               was, i, _esc(key), i, _esc(ok_label), why))


def _step5(w):
    bills = w["today_bills"]
    carry = w["carry_bills"]
    flagged = w.get("flagged_bills") or []
    if not bills and not carry and not flagged:
        return _page(5, w, "Bills", _export_band(w) + "<div class=card><p class=big good>"
                     "Koi bill baaki nahi hai.</p></div>"
                     "<form method=post><button class=btn name=go value=5>Aage badhiye"
                     "</button></form>")

    body = [_export_band(w)]
    if carry:
        body.append("<div class=note><b>Pichhla baaki</b> -- %d bill.</div>" % len(carry))
    body.append("<form method=post>")
    i = 0
    for b in carry + bills:
        body.append(_bill_block(i, b))
        i += 1
    if flagged:
        body.append("<div class=card><h2>Flag kiye hue bill -- %d</h2>"
                    "<p class=sub>Yeh tab tak yahin rahenge jab tak theek na ho jayen. "
                    "Theek ho jaye to <b>Theek hai</b> daba dijiye.</p></div>" % len(flagged))
        for b in flagged:
            body.append(_bill_block(i, b))
            i += 1
    body.append("<input type=hidden name=n value='%d'>" % i)
    body.append("<div class=savebar><button class=btn name=go value=5>Save kijiye</button>")
    if not bills and not carry:
        body.append("<button class='btn quiet' name=go value=5>Aage badhiye</button>")
    body.append("</div></form>")
    n = len(carry) + len(bills)
    if n:
        sub = ("%d bill. Har bill par ek tap. Kuch gadbad ho to hi "
               "'Theek nahi' kholiye." % n)
    else:
        sub = "Aaj ke sab bill ho gaye. Neeche sirf flag kiye hue bill hain."
    return _page(5, w, "Aaj ke bill", "".join(body), sub)


def _step6(w):
    body = (_export_band(w) +
            "<div class=card><h2>Salt, naye item aur naam</h2>"
            "<p>Excel download kijiye, usmein se naam <b>copy</b> karke Marg mein "
            "<b>paste</b> kijiye, phir wahi file wapas upload kar dijiye. "
            "Agli export khud saabit kar degi.</p>"
            "<p><a class=btn href='/finance/amir/salts'>Salt ka kaam kholiye</a></p>"
            "<p><a class='btn quiet' href='/finance/purchase/page/salts'>"
            "Purani list (phone par tick karne ke liye)</a></p></div>"
            "<div class=note>Aaj ke bill wale item hi zaroori hain. Poori purani list "
            "aaj khatam karna zaroori nahi.</div>"
            "<form method=post><input type=hidden name=tick value=6>"
            "<button class=btn name=go value=6>Aaj ke item theek kar diye</button>"
            "</form>")
    prompt = _salt_prompt_amir(w)                       # S243: red until Marg's list is seen
    if prompt:
        body += "<div class=card>%s</div>" % prompt
    return _page(6, w, "Salt / naam", body)


def _step7(w):
    if w["done"].get(7):
        c = w["closed"] or {}
        body = ("<div class=card><h2 class=good>DIN BAND &#10003;</h2>"
                "<p>%s baje band kiya.</p>" % _esc(_hhmm(c.get("closed_at"))))
        if c.get("reopened_at"):
            body += ("<p class=sub>Isse pehle %s baje dobara khola gaya tha.</p>"
                     % _esc(_hhmm(c.get("reopened_at"))))
        body += "</div>"
        waiting = len(w["today_bills"]) + len(w["carry_bills"])
        if waiting:
            body += ("<div class=note><b>%d naya bill aa gaya hai.</b> "
                     "<a href='/finance/amir/step/5'>Kholiye</a></div>" % waiting)
        body += _summary(w)
        # S246: DIN BAND is not a dead end.  The banner above is all links, and these
        # are the three places he actually comes back for.
        nflag = len(w.get("flagged_bills") or [])
        body += ("<div class=card><h2>Kuch aur karna hai?</h2>"
                 "<p><a class='btn plain' href='/finance/amir/step/5'>Bill dekhiye"
                 + ((" -- %d flag" % nflag) if nflag else "") + "</a></p>"
                 "<p><a class='btn plain' href='/finance/amir/step/6'>Salt aur naam</a></p>"
                 "<p><a class='btn plain' href='/finance/amir/step/4'>Report ki jaanch</a></p>"
                 "</div>"
                 "<form method=post><input type=hidden name=reopen value=1>"
                 "<button class='btn quiet' name=go value=7>Din phir se kholiye</button>"
                 "</form>")
        return _page(7, w, "Din band", body)

    if not _ready_to_close(w):
        body = "<div class=card><h2>Abhi kuch baaki hai</h2><ul>"
        for item in _left(w):
            body += "<li>%s</li>" % _esc(item)
        body += ("</ul><p class=sub>Aaj ka din khula rehta hai. Jo ho gaya hai wo "
                 "bacha hua hai -- dobara nahi karna padega.</p></div>"
                 "<p><a class=btn href='/finance/amir'>Jahan chhoda tha wahan se</a></p>")
        return _page(7, w, "Abhi baaki", body)

    body = (_summary(w) +
            "<form method=post><button class=btn name=go value=7>Din band kijiye</button>"
            "</form>")
    return _page(7, w, "Din band karein?", body)


def _summary(w):
    got = [e["label"] for e in w["exports"] if e["have"]]
    rows = ["<div class=line>Dono report: <b>%s</b></div>"
            % ("mil gayi" if len(got) == len(PAIR) else "%d / %d" % (len(got), len(PAIR)))]
    rows.append("<div class=line>Bill baaki: <b>%d</b></div>"
                % (len(w["today_bills"]) + len(w["carry_bills"])))
    nflag = len(w.get("flagged_bills") or [])
    if nflag:
        rows.append("<div class=line>Flag kiye hue bill: <b>%d</b> "
                    "<span class=sub>(din band karne se nahi rukte)</span></div>" % nflag)
    rows.append("<div class=line>Salt / naam: <b>%s</b></div>"
                % ("ho gaya" if w["done"].get(6) else "baaki"))
    prompt = _salt_prompt_amir(w)                       # S243: stays raised on the close screen too
    if prompt:
        rows.append(prompt)
    return "<div class=card><h2>Aaj ka kaam</h2>%s</div>" % "".join(rows)


_RENDER = {1: _step1, 2: _step2, 3: _step3, 4: _step4, 5: _step5, 6: _step6, 7: _step7}


# --------------------------------------------------------------------------
# writes
# --------------------------------------------------------------------------

def _tick(cx, day, step, user):
    cx.execute("INSERT OR IGNORE INTO amir_day(day, opened_at) VALUES(?,?)", (day, _stamp()))
    cx.execute("INSERT OR REPLACE INTO amir_step(day, step, done_at, by_user) VALUES(?,?,?,?)",
               (day, int(step), _stamp(), user))


def _save_bills(cx, day, user, form):
    """Write one disposition per bill, and raise a claim for each deficiency.

    Forced, not optional: a bill with no answer is simply not written, and the
    step stays unfinished, so the screen comes back with it still on the list.
    """
    try:
        n = int(form.get("n") or 0)
    except (TypeError, ValueError):
        n = 0
    written = 0
    for i in range(n):
        key = form.get("k_%d" % i) or ""
        reason = (form.get("r_%d" % i) or "").strip()
        if reason not in REASON_MAP or key.count("|") != 2:
            continue
        supplier_norm, bill_no, bill_date = key.split("|")
        cx.execute(
            """INSERT OR REPLACE INTO amir_bill_disposition
               (supplier_norm, bill_no, bill_date, day, reason, by_user, at)
               VALUES(?,?,?,?,?,?,?)""",
            (supplier_norm, bill_no, bill_date, day, reason, user, _stamp()),
        )
        written += 1
        if reason == "ok":
            # S246: Theek hai on a bill he had flagged is the correction being
            # confirmed.  Close what Darpan was chasing rather than leave it open
            # against a bill that is now right -- named, timed and attributed.
            cx.execute(
                """UPDATE amir_claim
                      SET state = 'settled', settled_outcome = 'amir_ok',
                          settled_at = ?, settled_by = ?
                    WHERE supplier_norm = ? AND bill_no = ? AND bill_date = ?
                      AND state <> 'settled'""",
                (_stamp(), user, supplier_norm, bill_no, bill_date),
            )
        if reason in CLAIM_REASONS:
            already = cx.execute(
                """SELECT 1 FROM amir_claim
                    WHERE supplier_norm=? AND bill_no=? AND bill_date=?
                      AND state <> 'settled'""",
                (supplier_norm, bill_no, bill_date),
            ).fetchone()
            if not already:
                b = cx.execute(
                    """SELECT supplier, amount_p FROM purchase_bill
                        WHERE supplier_norm=? AND bill_no=? AND bill_date=?""",
                    (supplier_norm, bill_no, bill_date),
                ).fetchone() if _table_exists(cx, "purchase_bill") else None
                cx.execute(
                    """INSERT INTO amir_claim
                       (supplier, supplier_norm, bill_no, bill_date, amount_p,
                        reason, raised_by, raised_at, state)
                       VALUES(?,?,?,?,?,?,?,?,'open')""",
                    ((b["supplier"] if b else supplier_norm), supplier_norm, bill_no,
                     bill_date, (b["amount_p"] if b else None), reason, user, _stamp()),
                )
    return written


# --------------------------------------------------------------------------
# routes
# --------------------------------------------------------------------------

@bp.route("/finance/amir")
def home():
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    _ensure(cx)
    w = _work(cx, _today())
    return _go(_next_step(w))


@bp.route("/finance/amir/step/<int:n>", methods=["GET", "POST"])
def step(n):
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    if n < 1 or n > 7:
        return _go(1)

    cx = _db()
    _ensure(cx)
    day = _today()
    user = (u or {}).get("username") or (u or {}).get("user") or ""

    if request.method == "POST":
        if n == 5:
            _save_bills(cx, day, user, request.form)
        elif n == 7:
            w = _work(cx, day)
            if w["done"].get(7) and request.form.get("reopen"):
                # S246: a day closed too early is opened again -- recorded, never
                # silently.  Everything already done stays done; only the close is
                # undone, and the jump takes him to whatever is now unfinished.
                cx.execute("UPDATE amir_day SET closed_at=NULL, closed_by=NULL, "
                           "reopened_at=?, reopened_by=? WHERE day=?",
                           (_stamp(), user, day))
                cx.execute("DELETE FROM amir_step WHERE day=? AND step=7", (day,))
                cx.commit()
                return _go(_next_step(_work(cx, day)))
            if _ready_to_close(w):
                cx.execute("INSERT OR IGNORE INTO amir_day(day, opened_at) VALUES(?,?)",
                           (day, _stamp()))
                cx.execute("UPDATE amir_day SET closed_at=?, closed_by=? WHERE day=?",
                           (_stamp(), user, day))
                _tick(cx, day, 7, user)
        elif n == 4:
            # S244.  Nothing on step 4 is ever a claim that a report arrived -- the
            # server alone decides that.  "Dobara banai" only restarts the transit
            # clock; "Aage ka kaam" only moves him on.
            if request.form.get("again"):
                _tick(cx, day, 3, user)
            cx.commit()
            if request.form.get("skip"):
                return _go(5)
            return _go(4)
        else:
            tick = request.form.get("tick")
            if tick and tick.isdigit() and int(tick) == n:
                _tick(cx, day, n, user)
        cx.commit()
        w = _work(cx, day)
        if n == 3:
            # He has just said the export was taken: he sees the processing screen
            # once, whatever the jump would otherwise have done with it.
            return _go(4)
        if n == 7 and w["done"].get(7):
            return _go(7)
        nxt = _next_step(w)
        return _go(nxt if nxt >= n else n + 1 if n < 7 else 7)

    w = _work(cx, day)
    return _RENDER[n](w)


@bp.route("/finance/amir/day")
def owner_day():
    """The owner's view of the same day, in English."""
    u, err = _require(*_roles, unit=_unit)
    if err:
        return _denied()
    cx = _db()
    _ensure(cx)
    day = request.args.get("d") or _today()
    w = _work(cx, day)

    rows = []
    for e in w["exports"]:
        rows.append("<tr><td>%s</td><td class='%s'>%s</td><td>%s</td><td>%s</td></tr>"
                    % (_esc(e["label"]), "good" if e["have"] else "bad",
                       "verified" if e["have"] else "not verified",
                       _esc(e.get("rows", "")), _esc(e.get("at", "") or e.get("reason", ""))))
    left = _left(w)
    state = ("CLOSED at %s" % _hhmm((w["closed"] or {}).get("closed_at"))) if w["done"].get(7) \
        else ("OPEN -- " + "; ".join(left) if left else "OPEN -- ready to close")
    if (w["closed"] or {}).get("reopened_at"):                  # S246
        state += " (reopened %s by %s)" % (_hhmm(w["closed"]["reopened_at"]),
                                           w["closed"].get("reopened_by") or "?")

    open_claims = cx.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(amount_p),0) AS v FROM amir_claim WHERE state <> 'settled'"
    ).fetchone()
    oldest = cx.execute(
        "SELECT MIN(raised_at) AS o FROM amir_claim WHERE state <> 'settled'"
    ).fetchone()

    body = ("<div class=card><h2>Amir -- %s</h2><p class=big>%s</p></div>"
            "<div class=card><h2>The daily pair</h2><div class=tscroll><table>"
            "<tr><th>report</th><th>state</th><th>rows</th><th>when</th></tr>%s"
            "</table></div></div>"
            "<div class=card><h2>Bills</h2>"
            "<div class=line>Today, still to tap: <b>%d</b></div>"
            "<div class=line>Carried from earlier days: <b>%d</b></div></div>"
            "<div class=card><h2>Claims for Darpan</h2>"
            "<div class=line>Open: <b>%d</b>, worth &#8377;%s</div>"
            "<div class=line>Oldest raised: <b>%s</b></div></div>"
            % (_esc(day), _esc(state), "".join(rows),
               len(w["today_bills"]), len(w["carry_bills"]),
               (open_claims["n"] if open_claims else 0),
               _rupees(open_claims["v"] if open_claims else 0),
               _esc((oldest["o"] or "-") if oldest else "-")))
    # S243: the salt list, amber until it arrives; and the visit summary, collapsed
    cls, line = _salt_owner_line(w.get("salt_list"))
    body += ("<div class=card><h2>Salt list from Marg</h2><p class='big %s'>%s</p>%s</div>"
             % (cls, _esc(line), _applied_line(w.get("salt_list"))))
    body += _visit_details_html(_visit_summary(cx, day))
    return _shell("Amir's day", body)


# --------------------------------------------------------------------------
# S243_AMIR_VISIT -- "Amir's visit -- what was done", for the owner
# --------------------------------------------------------------------------

MARK_KIT = "S243_AMIR_VISIT"


def _applied_line(s):
    s = s or {}
    if not s.get("applied_at"):
        return ""
    return ("<p class=sub>Salts page refreshed %s from the list of %s.</p>"
            % (_esc(_dm_hm(s["applied_at"])), _esc(s.get("applied_as_on") or "-")))


def _visit_summary(cx, day):
    """Everything the owner wants to read about one visit, gathered once, JSON-safe.

    Counts only; no bill text beyond supplier-free numbers, no names but the login that
    did the work.  One verdict per step 1-7: done / skipped / not needed / partly / not yet
    / open.  'skipped' means the day moved past a step without its tap.
    """
    w = _work(cx, day)
    s = w["salt_list"]
    nxt = _next_step(w)
    closed = bool(w["done"].get(7))
    ticks = w["ticks"]

    # ---- bills he tapped
    by_reason = {}
    for r in cx.execute("SELECT reason, COUNT(*) AS n FROM amir_bill_disposition WHERE day = ? "
                        "GROUP BY reason", (day,)).fetchall():
        by_reason[r["reason"]] = {"label": REASON_MAP.get(r["reason"], r["reason"]), "n": int(r["n"])}
    tapped = sum(v["n"] for v in by_reason.values())
    remaining = len(w["today_bills"]) + len(w["carry_bills"])
    bills_line = ", ".join("%s %d" % (v["label"], v["n"]) for _k, v in sorted(by_reason.items())) or "none"

    # ---- purchase reports the server received that day
    reports = []
    if _table_exists(cx, "purchase_export"):
        for r in cx.execute(
                """SELECT type, n_rows, grand_amount_p, export_stamp, received_at, period_from, period_to
                     FROM purchase_export
                    WHERE superseded_by IS NULL
                      AND """ + _export_day_sql() + """ = ?
                 ORDER BY COALESCE(export_stamp, received_at)""", (day,)).fetchall():
            d = dict(r)
            reports.append({"type": d.get("type"), "rows": d.get("n_rows"),
                            "amount_p": d.get("grand_amount_p"),
                            "amount": _rupees(d.get("grand_amount_p")) if d.get("grand_amount_p") is not None else "",
                            "at": _hhmm(d.get("export_stamp") or d.get("received_at")),
                            "period": "%s to %s" % ((d.get("period_from") or "")[:10], (d.get("period_to") or "")[:10])})
    bw = [r for r in reports if r["type"] == "BILLWISE"]
    rep_bills = bw[-1]["rows"] if bw else None
    rep_amount_p = bw[-1]["amount_p"] if bw and bw[-1]["amount_p"] is not None else None
    reports_line = ("; ".join("%s %s rows%s at %s" % (r["type"], r["rows"] if r["rows"] is not None else "?",
                                                     (" Rs %s" % r["amount"]) if r["amount"] else "", r["at"])
                              for r in reports) or "none received")

    # ---- salt work
    by_section = {}
    ticked_by = []
    if _table_exists(cx, "purchase_salt_task"):
        for r in cx.execute("SELECT section, done_by, done_at FROM purchase_salt_task "
                            "WHERE COALESCE(done, 0) = 1 AND done_at IS NOT NULL").fetchall():
            t = _norm_ts(r["done_at"])
            if t and t[:10] == day:
                by_section[r["section"]] = by_section.get(r["section"], 0) + 1
                if r["done_by"] and r["done_by"] not in ticked_by:
                    ticked_by.append(r["done_by"])
    salt_ticked = sum(by_section.values())
    uploads = {"n": 0, "ticked": 0}
    if _table_exists(cx, "amir_salt_upload"):
        r = cx.execute("SELECT COUNT(*) AS n, COALESCE(SUM(ticked), 0) AS t FROM amir_salt_upload "
                       "WHERE substr(uploaded_at, 1, 10) = ?", (day,)).fetchone()
        uploads = {"n": int(r["n"] or 0), "ticked": int(r["t"] or 0)}
    salts_line = ("renames %d, new salts %d, salt changes %d, cleanup %d; %d sheet upload%s"
                  % (by_section.get("rename", 0), by_section.get("create", 0), by_section.get("change", 0),
                     by_section.get("cleanup", 0), uploads["n"], "" if uploads["n"] == 1 else "s"))

    # ---- claims he raised
    claims_by = {}
    claims_n = 0
    claims_p = 0
    for r in cx.execute("SELECT reason, COUNT(*) AS n, COALESCE(SUM(amount_p), 0) AS v FROM amir_claim "
                        "WHERE substr(raised_at, 1, 10) = ? GROUP BY reason", (day,)).fetchall():
        claims_by[r["reason"]] = {"label": REASON_MAP.get(r["reason"], r["reason"]), "n": int(r["n"]),
                                  "amount_p": int(r["v"] or 0)}
        claims_n += int(r["n"])
        claims_p += int(r["v"] or 0)

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

    steps = [tap_step(1, "Punch", "no punch tap recorded"),
             tap_step(2, "Bill entry", "no 'all bills entered' tap")]
    have_all = all(e["have"] for e in w["exports"])
    if 3 in ticks:
        steps.append({"n": 3, "label": "Export", "state": "done", "note": tick_note(3)})
    elif have_all:
        steps.append({"n": 3, "label": "Export", "state": "done",
                      "note": "both reports arrived; the tap itself was not made"})
    elif closed or nxt > 3:
        steps.append({"n": 3, "label": "Export", "state": "skipped", "note": "no export tap"})
    else:
        steps.append({"n": 3, "label": "Export", "state": "not yet", "note": ""})
    if have_all:
        steps.append({"n": 4, "label": "Check", "state": "done",
                      "note": "; ".join("%s %s rows at %s" % (e["label"], e.get("rows", ""), e.get("at", ""))
                                        for e in w["exports"])})
    else:
        missing = [e["label"] for e in w["exports"] if not e["have"]]
        steps.append({"n": 4, "label": "Check", "state": "not done",
                      "note": "%s not verified" % " and ".join(missing)})
    if remaining == 0 and tapped == 0:
        steps.append({"n": 5, "label": "Bills", "state": "not needed", "note": "no bill waited for a tap"})
    elif remaining == 0:
        steps.append({"n": 5, "label": "Bills", "state": "done", "note": "%d tapped (%s)" % (tapped, bills_line)})
    elif tapped:
        steps.append({"n": 5, "label": "Bills", "state": "partly",
                      "note": "%d tapped, %d still to tap" % (tapped, remaining)})
    else:
        steps.append({"n": 5, "label": "Bills", "state": "not yet", "note": "%d to tap" % remaining})
    s6 = tap_step(6, "Salt/naam", "no salt tap")
    if salt_ticked:
        s6["note"] = ("%s; %d task%s ticked" % (s6["note"], salt_ticked, "" if salt_ticked == 1 else "s")).strip("; ")
    steps.append(s6)
    if closed:
        c = w["closed"] or {}
        steps.append({"n": 7, "label": "Band", "state": "done",
                      "note": "%s%s" % (_hhmm(c.get("closed_at")), (" by %s" % c["closed_by"]) if c.get("closed_by") else "")})
    else:
        steps.append({"n": 7, "label": "Band", "state": "open", "note": "; ".join(_left(w)) or "ready to close"})

    cls, owner_line = _salt_owner_line(s)
    sl = dict(s)
    sl["owner_line"] = owner_line
    sl["css"] = cls
    return {
        "ok": True, "kit": MARK_KIT, "day": day,
        "state": "CLOSED" if closed else "OPEN",
        "closed_at": (w["closed"] or {}).get("closed_at") if closed else None,
        "reopened_at": (w["closed"] or {}).get("reopened_at"),
        "reopened_by": (w["closed"] or {}).get("reopened_by"),
        "opened_at": (cx.execute("SELECT opened_at FROM amir_day WHERE day = ?", (day,)).fetchone() or {"opened_at": None})["opened_at"],
        "next_step": nxt, "left": _left(w),
        "bills": {"tapped": tapped, "by_reason": by_reason, "remaining_today": len(w["today_bills"]),
                  "carried": len(w["carry_bills"]), "line": bills_line},
        "reports": {"rows": reports, "bills": rep_bills, "amount_p": rep_amount_p,
                    "amount": _rupees(rep_amount_p) if rep_amount_p is not None else "", "line": reports_line},
        "salts": {"ticked": salt_ticked, "by_section": by_section, "renames": by_section.get("rename", 0),
                  "ticked_by": ticked_by, "uploads": uploads, "line": salts_line},
        "claims": {"n": claims_n, "amount_p": claims_p, "amount": _rupees(claims_p), "by_reason": claims_by},
        "salt_list": sl,
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
    head = "%s -- %s%s%s" % (v["day"], v["state"],
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
               sl.get("css", ""), _esc(sl.get("owner_line", ""))))


@bp.route("/finance/amir/day/api/visit-summary")
def visit_summary():
    """The owner's summary of one visit.  Checker only -- the hub's block reads this."""
    u, err = _require("checker", unit=_unit)
    if err:
        return {"ok": False, "error": "not_permitted",
                "message": "Only the checker may read the visit summary."}, 403
    day = (request.args.get("date") or request.args.get("d") or _today())[:10]
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", day):
        return {"ok": False, "error": "bad_date", "message": "date must be yyyy-mm-dd"}, 400
    cx = _db()
    _ensure(cx)
    return _visit_summary(cx, day)


@bp.route("/finance/amir/api/healthz")
def healthz():
    return {"ok": True, "kit": "S246_AMIR_LIST_REOPEN", "at": _stamp()}



def init(app, db_getter, require_fn, unit="medical",
         roles=("maker", "checker", "viewer"), url_prefix=""):
    global _db, _require, _unit, _roles
    _db, _require, _unit, _roles = db_getter, require_fn, unit, tuple(roles)
    app.register_blueprint(bp, url_prefix=url_prefix)

    # The salt sheet rides on this mount rather than on a second one, so adding
    # it never touches finance_app.py again.  If the file is not there, the day
    # flow still works and step 6 falls back to the page he already has.
    try:
        import amir_salts                                    # noqa: PLC0415
        amir_salts.init(app, db_getter, require_fn, unit=unit, roles=roles,
                        url_prefix=url_prefix)
    except Exception:
        pass
    return bp
