"""S312_CLAIM_QUEUE -- Darpan's claim queue (D471, D544), Sanjeevni, session S268.

WHAT THIS IS.  A stock line the owner marks "to pursue" (stock_diff_lane.action
= 'RECOVER') becomes a CLAIM.  A claim has three states and only three:

    open  ->  contacted  ->  settled

    open       the owner has marked the line; nobody has been asked yet.
    contacted  Darpan has been asked WITH THE EVIDENCE IN HAND (S308 put thirty
               days of sale evidence on the line) and has given his answer.
               His answer is recorded as his; it is evidence, not a verdict.
    settled    the owner has decided, naming an outcome.  Terminal.

That division is the owner's own rule, in his words on the hub itself: "His
answer is evidence; your tap decides."  So Darpan can move a claim from open to
contacted and no further, and the owner settles.

WHY IT EXISTS.  Hub step 8 ("Darpan: sold without a bill?") could reach only
'wait' and 'now' -- it had no door to record an answer, so once a line was
pursued the hub's last step stayed amber for ever and the count never visibly
finished (S268 finding 3).  This module is that door.  D544: step 8 is done
when every pursued line has a claim in a terminal state.

THE SELF-CLOSE, AND AN HONEST LIMIT.  D471 asks the queue to close itself on a
matching purchase return.  IT CANNOT, TODAY, AND THIS MODULE DOES NOT PRETEND
OTHERWISE.  Measured on the 18-Sep database: purchase_line.direction is
'PURCHASE' on all 1,644 rows, there is no negative quantity and no
purchase_return table anywhere; Marg prints a return in the item-wise report as
an ordinary positive line with no marker (marg_ingest/lib/purchase_returns.py
says so in as many words), and the `is_return` flag that library computes lives
in memory on manojz and is never persisted to this box.  So:

  * the return rule IS WRITTEN below and is ASLEEP.  _returns_available()
    decides, and it is False until a return is actually stored.  The day one
    is, the rule wakes with no further change here -- that is the point of
    writing it now rather than later.
  * what DOES self-close today is real and stored: A LATER COUNT.  If a count
    after the claim finds the item agreeing, the shortage is resolved by
    evidence and the claim settles itself, 'found_at_later_count'.
  * a credit note (purchase_bill.amount_p < 0, raised after the claim) is a
    CANDIDATE only.  It carries a supplier and an amount and NO ITEM, so it can
    never prove which line it answers.  It is flagged for a tap; it closes
    nothing by itself.

WHAT THIS MODULE DOES NOT TOUCH.  amir_claim is Amir's BILL-keyed supplier
claim and stays exactly as it is -- different key, different queue, different
counters on his step 7.  A claim_line may name an amir_claim row in claim_ref
when a pursued line becomes a claim against a supplier, so the two are joinable
without either being conflated.

No page, no blueprint, no route: plain functions over a connection, called by
stock_app (the owner's side) and darpan_app (Darpan's side).  Nothing here
commits -- the caller owns the transaction.
"""

import datetime as dt
import re

_re = re

STATES = ("open", "contacted", "settled")

# Darpan's answers, as he taps them.  Hinglish label = what he reads.
ANSWERS = {
    "sold_no_bill":     "Bina bill ke gaya",
    "returned_supplier": "Supplier ko wapas gaya",
    "found":            "Mil gaya",
    "damaged":          "Toota / kharab",
    "not_known":        "Pata nahin",
}

# The owner's outcomes, as he settles.  English (his page).
OUTCOMES = {
    "sold_no_bill":      "sold without a bill",
    "returned_supplier": "went back to the supplier",
    "found":             "found -- not short after all",
    "damaged":           "damaged or broken",
    "written_off":       "written off",
    "not_known":         "never established",
    "withdrawn":         "no longer pursued",
    "found_at_later_count": "a later count found it",
}

AGE_TO_TOP_DAYS = 14          # D471: a claim ages to the top at 14 days


def norm_key(name):
    """finance_returns.norm_item(), verbatim -- the SAME key the sale lines and
    stock_app._sale_key() use.  A claim survives a rename because of this."""
    s = _re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return _re.sub(r"\s+", " ", s).strip()


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def ensure(con):
    """Additive and idempotent.  Safe to call on every request."""
    con.execute("""
      CREATE TABLE IF NOT EXISTS claim_line (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        count_id      INTEGER NOT NULL,          -- the ROOT count
        item          TEXT    NOT NULL,          -- as Marg prints it
        item_key      TEXT    NOT NULL,          -- norm_key(item)
        short_qty     INTEGER,                   -- units short at the count, positive
        value_p       INTEGER,                   -- what it is worth, paise
        state         TEXT    NOT NULL DEFAULT 'open',
        answer        TEXT,                      -- Darpan's answer, one of ANSWERS
        answer_note   TEXT,
        outcome       TEXT,                      -- the owner's, one of OUTCOMES
        note          TEXT,
        raised_by     TEXT,
        raised_at     TEXT    NOT NULL,
        contacted_by  TEXT,
        contacted_at  TEXT,
        settled_by    TEXT,
        settled_at    TEXT,
        closed_auto   INTEGER NOT NULL DEFAULT 0,
        auto_reason   TEXT,
        candidate     TEXT,                      -- a credit note that MIGHT answer this
        claim_ref     INTEGER                    -- amir_claim.id, when it becomes a bill claim
      )""")
    con.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_claim_line ON claim_line(count_id, item_key)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_claim_line_state ON claim_line(state, raised_at)")


def _table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                       (name,)).fetchone() is not None


def _cols(con, table):
    try:
        return set(r[1] for r in con.execute("PRAGMA table_info(%s)" % table))
    except Exception:
        return set()


def _returns_available(con):
    """Is a purchase RETURN stored anywhere on this box, as a return?

    Measured at S268: no.  This is deliberately a LIVE test and not a constant,
    so the sweep's return rule wakes by itself the day returns are persisted --
    by a purchase_return table, or by purchase_line finally carrying
    direction='RETURN' or a negative quantity.  Until then it is False and the
    rule below does not run, which is the honest answer, not a missing feature.
    """
    if _table(con, "purchase_return"):
        return True
    if _table(con, "purchase_line"):
        c = _cols(con, "purchase_line")
        if "direction" in c:
            r = con.execute("SELECT 1 FROM purchase_line WHERE UPPER(COALESCE(direction,''))"
                            " IN ('RETURN','PRETURN','PURCHASE_RETURN') LIMIT 1").fetchone()
            if r:
                return True
        if "qty" in c:
            r = con.execute("SELECT 1 FROM purchase_line WHERE qty < 0 LIMIT 1").fetchone()
            if r:
                return True
    return False


# ---------------------------------------------------------------- raising

def raise_for(con, count_id, item, short_qty=None, value_p=None, by_user="", ts=None,
              word_at=None):
    """The owner marked the line to pursue.  One live claim per (count, item);
    a second mark is not a second claim.

    A SETTLED claim is re-opened only when the owner's word on that line is
    NEWER than the settlement -- `word_at` is the timestamp of the newest
    stock_diff_lane row for the item, and it is the whole guard.  Without it a
    settled claim would rise from the dead on every page load, because the line
    is still marked RECOVER and always will be: the mark is what the count
    recorded, the settlement is what happened afterwards.  Reopening is then the
    owner deliberately marking the line AGAIN after settling it, which is a real
    act and deserves the same row, not a second one.

    Returns 'new' | 'reopened' | 'already' | 'settled'."""
    ensure(con)
    ts = ts or now_iso()
    key = norm_key(item)
    if not key:
        return "already"
    row = con.execute("SELECT id, state, settled_at FROM claim_line WHERE count_id=? AND item_key=?",
                      (int(count_id), key)).fetchone()
    if row is None:
        con.execute("INSERT INTO claim_line (count_id, item, item_key, short_qty, value_p, "
                    "state, raised_by, raised_at) VALUES (?,?,?,?,?,'open',?,?)",
                    (int(count_id), str(item), key,
                     (int(short_qty) if short_qty is not None else None),
                     (int(value_p) if value_p is not None else None), by_user or "", ts))
        return "new"
    if str(row[1]) == "settled":
        settled_at = str(row[2] or "")
        if word_at is None or (settled_at and str(word_at)[:19] <= settled_at[:19]):
            return "settled"
        con.execute("UPDATE claim_line SET state='open', outcome=NULL, settled_by=NULL, "
                    "settled_at=NULL, closed_auto=0, auto_reason=NULL, raised_by=?, raised_at=? "
                    "WHERE id=?", (by_user or "", ts, int(row[0])))
        return "reopened"
    return "already"


def withdraw(con, count_id, item, by_user="", ts=None, why="the word on the line changed"):
    """The owner's word moved off RECOVER.  A live claim is settled 'withdrawn',
    never deleted: the queue is a record of what was asked, not only of what is
    outstanding."""
    ensure(con)
    ts = ts or now_iso()
    key = norm_key(item)
    con.execute("UPDATE claim_line SET state='settled', outcome='withdrawn', note=?, "
                "settled_by=?, settled_at=? WHERE count_id=? AND item_key=? AND state<>'settled'",
                (why, by_user or "", ts, int(count_id), key))


def sync_from_words(con, count_id, pursued_items, by_user="", ts=None):
    """Make the queue agree with the owner's words, both ways, in one call:
    every pursued line has a live claim, and every live claim whose line is no
    longer pursued is withdrawn.  Idempotent; safe to call on every hub read.
    Returns (new, reopened, withdrawn)."""
    ensure(con)
    ts = ts or now_iso()
    want = {}
    for it in pursued_items:
        k = norm_key(it.get("item") if isinstance(it, dict) else it)
        if k:
            want[k] = it
    new = reop = gone = 0
    for k, it in want.items():
        if isinstance(it, dict):
            r = raise_for(con, count_id, it.get("item"), it.get("short_qty"),
                          it.get("value_p"), by_user, ts, it.get("word_at"))
        else:
            r = raise_for(con, count_id, it, None, None, by_user, ts)
        new += (r == "new")
        reop += (r == "reopened")
    for row in con.execute("SELECT item, item_key FROM claim_line WHERE count_id=? AND state<>'settled'",
                           (int(count_id),)).fetchall():
        if row[1] not in want:
            withdraw(con, count_id, row[0], by_user, ts)
            gone += 1
    return new, reop, gone


# ---------------------------------------------------------------- answering

def answer(con, claim_id, ans, note="", by_user="", ts=None):
    """Darpan's tap.  open -> contacted.  He may change his answer while it is
    still contacted; he can never settle.  Returns (ok, message)."""
    ensure(con)
    ts = ts or now_iso()
    if ans not in ANSWERS:
        return False, "that is not one of the answers"
    row = con.execute("SELECT id, state FROM claim_line WHERE id=?", (int(claim_id),)).fetchone()
    if not row:
        return False, "no such claim"
    if str(row[1]) == "settled":
        return False, "yeh claim band ho chuka hai"
    con.execute("UPDATE claim_line SET state='contacted', answer=?, answer_note=?, "
                "contacted_by=?, contacted_at=? WHERE id=?",
                (ans, (note or "")[:300] or None, by_user or "", ts, int(claim_id)))
    return True, "likh liya"


def settle(con, claim_id, outcome, note="", by_user="", ts=None):
    """The owner's tap.  Terminal.  Returns (ok, message)."""
    ensure(con)
    ts = ts or now_iso()
    if outcome not in OUTCOMES:
        return False, "that is not one of the outcomes"
    row = con.execute("SELECT id FROM claim_line WHERE id=?", (int(claim_id),)).fetchone()
    if not row:
        return False, "no such claim"
    con.execute("UPDATE claim_line SET state='settled', outcome=?, note=?, settled_by=?, "
                "settled_at=?, closed_auto=0 WHERE id=?",
                (outcome, (note or "")[:300] or None, by_user or "", ts, int(claim_id)))
    return True, "settled"


# ---------------------------------------------------------------- the sweep

def sweep(con, ts=None):
    """The self-closing half.  Runs on every read; cheap, and it never guesses.

    Rule 1 -- A LATER COUNT (live).  A count sealed after the claim was raised
    that carries this item with no difference is proof the shortage is gone.
    Settles 'found_at_later_count', closed_auto = 1.

    Rule 2 -- A PURCHASE RETURN (asleep; see the module docstring).  Guarded by
    _returns_available().  When a return for the item is stored after the claim
    was raised, it settles 'returned_supplier', closed_auto = 1.

    Rule 3 -- A CREDIT NOTE (a candidate, never a close).  A purchase_bill with
    a negative amount raised after the claim is recorded in `candidate` so it is
    visible on the line.  It names a supplier and an amount and NO item, so it
    cannot say which claim it answers, and it is never allowed to.

    Returns dict(closed_count, closed_return, flagged).
    """
    ensure(con)
    ts = ts or now_iso()
    out = {"closed_count": 0, "closed_return": 0, "flagged": 0}
    live = con.execute("SELECT id, count_id, item, item_key, raised_at FROM claim_line "
                       "WHERE state <> 'settled'").fetchall()
    if not live:
        return out
    have_returns = _returns_available(con)
    for row in live:
        cid, item, key, raised = int(row[1]), str(row[2]), str(row[3]), str(row[4] or "")
        # rule 1 -- a later count
        try:
            if _table(con, "stock_diff") and _table(con, "stock_count"):
                r = con.execute(
                    "SELECT d.id FROM stock_diff d JOIN stock_count c ON c.id = d.count_id "
                    "WHERE d.item = ? AND d.count_id <> ? AND COALESCE(d.diff,0) = 0 "
                    "AND COALESCE(c.submitted_at,'') > ? LIMIT 1",
                    (item, cid, raised)).fetchone()
                if r:
                    con.execute("UPDATE claim_line SET state='settled', outcome='found_at_later_count', "
                                "closed_auto=1, auto_reason='a later count found this item agreeing', "
                                "settled_at=? WHERE id=?", (ts, int(row[0])))
                    out["closed_count"] += 1
                    continue
        except Exception:
            pass
        # rule 2 -- a purchase return (asleep until returns are stored)
        if have_returns:
            try:
                hit = None
                if _table(con, "purchase_return"):
                    hit = con.execute("SELECT 1 FROM purchase_return WHERE item = ? LIMIT 1",
                                      (item,)).fetchone()
                elif _table(con, "purchase_line"):
                    c = _cols(con, "purchase_line")
                    if "direction" in c:
                        hit = con.execute("SELECT 1 FROM purchase_line WHERE item = ? AND "
                                          "UPPER(COALESCE(direction,'')) IN ('RETURN','PRETURN',"
                                          "'PURCHASE_RETURN') LIMIT 1", (item,)).fetchone()
                    if not hit and "qty" in c:
                        hit = con.execute("SELECT 1 FROM purchase_line WHERE item = ? AND qty < 0 "
                                          "LIMIT 1", (item,)).fetchone()
                if hit:
                    con.execute("UPDATE claim_line SET state='settled', outcome='returned_supplier', "
                                "closed_auto=1, auto_reason='a purchase return for this item was "
                                "recorded after the claim', settled_at=? WHERE id=?", (ts, int(row[0])))
                    out["closed_return"] += 1
                    continue
            except Exception:
                pass
        # rule 3 -- a credit note is a candidate, never a close
        try:
            if _table(con, "purchase_bill"):
                b = con.execute("SELECT supplier, bill_no, bill_date, amount_p FROM purchase_bill "
                                "WHERE COALESCE(amount_p,0) < 0 ORDER BY bill_date DESC LIMIT 1").fetchone()
                if b:
                    txt = "credit note %s of %s from %s -- a candidate only; it names no item" % (
                        str(b[1] or "?"), str(b[2] or "?"), str(b[0] or "?"))
                    cur = con.execute("SELECT COALESCE(candidate,'') FROM claim_line WHERE id=?",
                                      (int(row[0]),)).fetchone()
                    if cur and str(cur[0]) != txt:
                        con.execute("UPDATE claim_line SET candidate=? WHERE id=?", (txt, int(row[0])))
                        out["flagged"] += 1
        except Exception:
            pass
    return out


# ---------------------------------------------------------------- reading

def _age_days(raised, now=None):
    try:
        a = dt.datetime.fromisoformat(str(raised)[:19])
        b = dt.datetime.fromisoformat(str(now or now_iso())[:19])
        return max(0, (b - a).days)
    except Exception:
        return 0


def queue(con, limit=50, now=None):
    """Darpan's list.  D471: a claim AGES TO THE TOP AT 14 DAYS -- anything that
    old sorts first, then the rest oldest-first, so a line cannot quietly sink."""
    ensure(con)
    now = now or now_iso()
    rows = con.execute("SELECT id, count_id, item, short_qty, value_p, state, answer, "
                       "answer_note, raised_at, candidate FROM claim_line "
                       "WHERE state <> 'settled' ORDER BY raised_at").fetchall()
    out = []
    for r in rows:
        age = _age_days(r[8], now)
        out.append(dict(id=int(r[0]), count_id=int(r[1]), item=str(r[2]),
                        short_qty=(int(r[3]) if r[3] is not None else None),
                        value_p=(int(r[4]) if r[4] is not None else None),
                        state=str(r[5]), answer=(r[6] or ""),
                        answer_label=ANSWERS.get(r[6] or "", ""),
                        answer_note=(r[7] or ""), raised_at=str(r[8] or ""),
                        age_days=age, aged=(age >= AGE_TO_TOP_DAYS),
                        candidate=(r[9] or "")))
    out.sort(key=lambda x: (0 if x["aged"] else 1, x["raised_at"]))
    return out[:int(limit)]


def summary(con, count_id=None, now=None):
    """What the hub needs to show, and what step 8 needs to decide."""
    ensure(con)
    now = now or now_iso()
    where, args = "", ()
    if count_id is not None:
        where, args = " WHERE count_id = ?", (int(count_id),)
    rows = con.execute("SELECT state, answer, raised_at, closed_auto FROM claim_line" + where,
                       args).fetchall()
    s = dict(total=len(rows), open=0, contacted=0, settled=0, aged=0, auto=0, answers={})
    for r in rows:
        st = str(r[0] or "")
        if st in ("open", "contacted", "settled"):
            s[st] += 1
        if st != "settled" and _age_days(r[2], now) >= AGE_TO_TOP_DAYS:
            s["aged"] += 1
        if int(r[3] or 0):
            s["auto"] += 1
        if r[1]:
            s["answers"][str(r[1])] = s["answers"].get(str(r[1]), 0) + 1
    s["live"] = s["open"] + s["contacted"]
    return s


def lines(con, count_id, limit=40):
    """Every claim of one count, worst first -- what the owner sees beside the
    evidence on hub step 8."""
    ensure(con)
    rows = con.execute("SELECT id, item, short_qty, value_p, state, answer, answer_note, "
                       "outcome, note, raised_at, contacted_by, contacted_at, closed_auto, "
                       "auto_reason, candidate FROM claim_line WHERE count_id=? ",
                       (int(count_id),)).fetchall()
    out = [dict(id=int(r[0]), item=str(r[1]),
                short_qty=(int(r[2]) if r[2] is not None else None),
                value_p=(int(r[3]) if r[3] is not None else None),
                state=str(r[4]), answer=(r[5] or ""),
                answer_label=ANSWERS.get(r[5] or "", ""), answer_note=(r[6] or ""),
                outcome=(r[7] or ""), outcome_label=OUTCOMES.get(r[7] or "", ""),
                note=(r[8] or ""), raised_at=str(r[9] or ""),
                contacted_by=(r[10] or ""), contacted_at=(r[11] or ""),
                closed_auto=int(r[12] or 0), auto_reason=(r[13] or ""),
                candidate=(r[14] or "")) for r in rows]
    order = {"contacted": 0, "open": 1, "settled": 2}
    out.sort(key=lambda x: (order.get(x["state"], 3), -(x["value_p"] or 0), x["item"]))
    return out[:int(limit)]


def step8_state(con, count_id, pursue_lines):
    """D544.  Step 8 is DONE when every pursued line has a claim in a terminal
    state -- which is the first time the hub's last step can finish at all."""
    ensure(con)
    if not pursue_lines:
        return "wait"
    s = summary(con, count_id)
    if s["total"] and s["live"] == 0:
        return "done"
    return "now"
