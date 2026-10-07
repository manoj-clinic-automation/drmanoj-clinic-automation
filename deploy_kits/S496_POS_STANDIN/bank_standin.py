#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bank_standin.py  ·  S496  ·  the POS machine's UPI total, standing in for a bank statement that has not come.

THE OWNER, 07-Oct-2026 12:17 IST (eleven decisions; these are his words, shortened):

    "when the bank's daily statement (MPR) has not come, the staff give the POS machine's UPI total on
     the SAME screen they already use, and it counts only after my confirmation."
    "NO NEW SCREEN for anyone."  "one number, optional, nothing else typed, and it is never a daily duty
     for staff when the bank is on time."
    "A typed figure changes nothing until I confirm it."  "I can also type the figure there myself; mine
     needs no second confirmation."
    "After I confirm, the typed figure stands in for the bank on that day, always marked
     'provisional — POS total, bank not in'."
    "When the bank's statement lands it replaces the typed figure by itself ... A difference beyond the
     tolerance is one line for me (date, typed, bank, difference). The typed row is kept as a record,
     never deleted."
    "If the bank's statement never comes, the confirmed figure keeps standing, marked 'bank statement
     never received', and stays one line on my list."
    "The tolerance and the bank's expected arrival time are settings I can change on screen."
    "Keep the typed figures in one shared table that every unit reads through one function."

WHAT THIS MODULE IS
    ONE table, bank_standin, and ONE function every unit reads: standing(con, unit, date).  It answers the
    confirmed figure for that unit's day -- or None: nothing typed, not yet confirmed, or the bank's own
    statement is in (the bank always wins, the moment its row exists).
    NO MONEY ROW IS WRITTEN HERE OR BECAUSE OF THIS.  The figure is a stand-in for MATCHING; no day_entry,
    cash_movement, upi_statement or upi_txn row is created, changed or removed.  Nothing is ever deleted
    from bank_standin: a figure that is re-typed, rejected, or replaced by the bank stays as a row.

THE UNITS are read from the statement store (upi_statement, finance_upi.MIDS) -- not assumed.
A unit's own pages decide where the one field and the owner's one line are drawn:
    clinic    clinic_money.py   the counter sheet + the morning-match card; the owner on /finance/clinic/money
    medical   darpan_kal.py     Darpan's "Kal ka hisaab" form; the owner on /finance/approvals
    any other unit of the store (today: lab) has no daily page of its own -- the owner types its figure on
    /finance/clinic/money, and the same block is ready for its page when one exists.

WHEN THE FIELD IS OFFERED TO STAFF: only while that day's statement is NOT in AND the bank's expected time
has passed (setting bank_mpr.expect_hhmm, default 10:00 IST on the next morning).  Before that time the
bank is simply not due and nothing is asked.

THE ROW'S LIFE     typed -> confirmed -> replaced           (the bank landed; bank_p and diff_p recorded)
                   typed -> rejected                        (the owner said no; staff may type again)
                   typed -> superseded                      (typed again before he decided)
                   typed -> lapsed                          (the bank landed before he decided)
                   confirmed -> superseded                  (he typed a new figure himself)

No route lives here: each unit's own module posts to its own address (the front gate resolves the unit
from the path).  The table is created on first use inside a request, never at import (F-303).
Standard library only.
"""
import datetime as dt
import os

VERSION = "S496 1.0"

KEY_TOL = "bank_standin.tolerance_p"        # paise; a bank-vs-typed difference beyond it is one line for the owner
KEY_EXPECT = "bank_mpr.expect_hhmm"         # HH:MM IST on D+1 -- bank_mpr_status reads the same key
KEY_OWNER = "bank_standin.owner"            # the one login whose word confirms
KEY_ON = "bank_standin.on"                  # '0' hides the field from staff; the owner's own typing stays
DEF_TOL_P = 10000
DEF_EXPECT = "10:00"
DEF_OWNER = "manoj"
NEVER_AFTER_DAYS = 3                        # no later statement either: after this many days the bank is not coming

LABEL_PROV = "provisional — POS total, bank not in"
LABEL_NEVER = "bank statement never received"

# which page carries a unit's owner line; a unit with no entry rides the clinic money page
OWNER_PAGE = {"clinic": "/finance/clinic/money", "medical": "/finance/approvals"}
UNIT_LABEL = {"clinic": "Clinic", "medical": "Sanjeevni", "lab": "NK Pathology"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS bank_standin (
  id            INTEGER PRIMARY KEY,
  unit          TEXT NOT NULL,
  business_date TEXT NOT NULL,
  amount_p      INTEGER NOT NULL,
  typed_by      TEXT NOT NULL DEFAULT '',
  typed_at      TEXT NOT NULL DEFAULT '',
  by_owner      INTEGER NOT NULL DEFAULT 0,
  status        TEXT NOT NULL DEFAULT 'typed',
  decided_by    TEXT NOT NULL DEFAULT '',
  decided_at    TEXT NOT NULL DEFAULT '',
  note          TEXT NOT NULL DEFAULT '',
  bank_p        INTEGER,
  bank_at       TEXT NOT NULL DEFAULT '',
  diff_p        INTEGER,
  seen_by       TEXT NOT NULL DEFAULT '',
  seen_at       TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_bank_standin_day ON bank_standin(unit, business_date, status);
"""

_schema_done = False
_HOOKS = {}


# ------------------------------------------------------------------ small things
def ensure(con):
    """On first use, inside a request -- never at import (F-303).  Two plain statements, not a script: a script
    would COMMIT whatever the caller has pending.  If the caller is in the middle of a transaction the table rides
    it and this is simply asked again next time."""
    global _schema_done
    if _schema_done:
        return
    pending = bool(getattr(con, "in_transaction", False))
    for stmt in SCHEMA.split(";"):
        if stmt.strip():
            con.execute(stmt)
    if not pending:
        con.commit()
        _schema_done = True


def _now():
    """The box's clock is IST.  BANK_STANDIN_NOW (or CLINIC_MONEY_NOW) pins it for the walk."""
    for k in ("BANK_STANDIN_NOW", "CLINIC_MONEY_NOW"):
        v = os.environ.get(k, "")
        if v:
            try:
                return dt.datetime.fromisoformat(v)
            except ValueError:
                pass
    return dt.datetime.now().replace(microsecond=0)


def _stamp(now=None):
    return (now or _now()).strftime("%Y-%m-%d %H:%M:%S")


def _iso_ok(d):
    try:
        return dt.date(int(d[:4]), int(d[5:7]), int(d[8:10])).isoformat() == d
    except (ValueError, IndexError, TypeError):
        return False


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def rupees(p):
    """12345600 -> '1,23,456' is not attempted: the app writes 123,456 everywhere, and so does this."""
    if p is None:
        return "—"
    p = int(p)
    whole, paise = divmod(abs(p), 100)
    s = "{:,}".format(whole) + ((".%02d" % paise) if paise else "")
    return ("−" if p < 0 else "") + s


def human(iso):
    return dt.date.fromisoformat(iso).strftime("%a %d-%b-%Y") if _iso_ok(iso) else (iso or "—")


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return (r[0] if r and r[0] not in (None, "") else default)
    except Exception:                                    # noqa: BLE001
        return default


def tolerance_p(con):
    try:
        v = int(_setting(con, KEY_TOL, str(DEF_TOL_P)))
        return v if v >= 0 else DEF_TOL_P
    except (TypeError, ValueError):
        return DEF_TOL_P


def parse_hhmm(s):
    """'10:00' -> (10, 0), or None."""
    try:
        h, m = str(s).strip().split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return h, m
    except (ValueError, AttributeError):
        pass
    return None


def expect_hhmm(con):
    return parse_hhmm(_setting(con, KEY_EXPECT, DEF_EXPECT)) or parse_hhmm(DEF_EXPECT)


def expect_text(con):
    return "%02d:%02d" % expect_hhmm(con)


def expected_at(con, d):
    """The moment the bank's statement for business day d is due on the box: the setting's time on d+1."""
    h, m = expect_hhmm(con)
    nxt = dt.date.fromisoformat(d) + dt.timedelta(days=1)
    return dt.datetime(nxt.year, nxt.month, nxt.day, h, m)


def owner_login(con):
    return (_setting(con, KEY_OWNER, DEF_OWNER) or DEF_OWNER).strip().lower()


def is_owner(con, u):
    return str((u or {}).get("user") or "").strip().lower() == owner_login(con)


def is_on(con):
    return str(_setting(con, KEY_ON, "1")).strip() != "0"


def unit_label(con, unit):
    if unit in UNIT_LABEL:
        return UNIT_LABEL[unit]
    try:
        r = con.execute("SELECT name FROM business_unit WHERE code=?", (unit,)).fetchone()
        if r and r[0]:
            return r[0]
    except Exception:                                    # noqa: BLE001
        pass
    return unit


def units(con):
    """Every unit whose bank statement arrives daily -- read from the statement store, never assumed."""
    seen = []
    try:
        for r in con.execute("SELECT DISTINCT unit FROM upi_statement WHERE unit IS NOT NULL AND unit<>''"):
            if r[0] not in seen:
                seen.append(r[0])
    except Exception:                                    # noqa: BLE001
        pass
    try:
        import finance_upi                                       # noqa: PLC0415
        for u in getattr(finance_upi, "MIDS", {}).values():
            if u and u not in seen:
                seen.append(u)
    except Exception:                                    # noqa: BLE001
        pass
    order = {"clinic": 0, "medical": 1}
    return sorted(seen, key=lambda u: (order.get(u, 9), u))


def units_for_page(con, page_unit):
    """The units whose owner line is drawn on page_unit's owner page: its own, and -- on the clinic's --
    every unit of the store that has no page of its own."""
    out = []
    for u in units(con):
        if u == page_unit or (page_unit == "clinic" and u not in OWNER_PAGE):
            out.append(u)
    if page_unit not in out:
        out.insert(0, page_unit)
    return out


def on_change(unit, fn):
    """A unit's module registers fn(con, date): called after a figure for that unit starts or stops
    standing, so the day is worked again.  Fail-soft: a hook that raises never fails the write."""
    _HOOKS[unit] = fn


def _fire(con, unit, d):
    fn = _HOOKS.get(unit)
    if fn is None:
        return
    try:
        fn(con, d)
    except Exception:                                    # noqa: BLE001
        pass


# ------------------------------------------------------------------ the bank's own word
def _has_row(con, unit, d):
    try:
        return con.execute("SELECT 1 FROM upi_statement WHERE unit=? AND statement_date=?", (unit, d)).fetchone() is not None
    except Exception:                                    # noqa: BLE001
        return False


def bank_state(con, unit, d, now=None):
    """applied | late | no_rows | rejected | waiting | not_received -- bank_mpr_status's own answer when it is
    beside us (it knows the raw-file store too), else the statement row and the clock."""
    now = now or _now()
    try:
        import bank_mpr_status                                   # noqa: PLC0415
        res = bank_mpr_status.mpr_state(con, d, unit=unit, now=now)
        if res.get("ok") and res.get("state"):
            return res["state"]
    except Exception:                                    # noqa: BLE001
        pass
    if _has_row(con, unit, d):
        return "applied"
    return "not_received" if now >= expected_at(con, d) else "waiting"


def bank_in(state):
    return state in ("applied", "late", "no_rows")


def bank_total_p(con, unit, d):
    """The bank's figure for the day, as every page of this app totals it: the day's upi_txn rows."""
    try:
        r = con.execute("SELECT COALESCE(SUM(amount_p),0), COUNT(*) FROM upi_txn WHERE unit=? AND txn_date=?", (unit, d)).fetchone()
        if r is not None and r[1]:
            return int(r[0] or 0)
    except Exception:                                    # noqa: BLE001
        pass
    try:
        r = con.execute("SELECT parsed_total_p FROM upi_statement WHERE unit=? AND statement_date=?", (unit, d)).fetchone()
        if r is not None and r[0] is not None:
            return int(r[0])
    except Exception:                                    # noqa: BLE001
        pass
    return 0


def _later_statement(con, unit, d):
    try:
        return con.execute("SELECT 1 FROM upi_statement WHERE unit=? AND statement_date>? LIMIT 1", (unit, d)).fetchone() is not None
    except Exception:                                    # noqa: BLE001
        return False


def never_received(con, unit, d, now=None):
    """The bank has moved on past this day (a later day's statement is in), or enough days have gone."""
    now = now or _now()
    if _later_statement(con, unit, d):
        return True
    return (now.date() - dt.date.fromisoformat(d)).days >= NEVER_AFTER_DAYS


# ------------------------------------------------------------------ rows
def _rows(con, unit, d, status=None):
    q = "SELECT * FROM bank_standin WHERE unit=? AND business_date=?"
    a = [unit, d]
    if status:
        q += " AND status=?"
        a.append(status)
    return [dict(r) for r in con.execute(q + " ORDER BY id DESC", a)]


def sweep(con, now=None):
    """The bank replaces a typed figure BY ITSELF: every open row whose statement is now in is closed with the
    bank's figure and the difference beside it.  Idempotent; called by every read below.  The row stays."""
    ensure(con)
    now = now or _now()
    changed = []
    for r in [dict(x) for x in con.execute("SELECT * FROM bank_standin WHERE status IN ('typed','confirmed') ORDER BY id")]:
        if not bank_in(bank_state(con, r["unit"], r["business_date"], now=now)):
            continue
        bp = bank_total_p(con, r["unit"], r["business_date"])
        con.execute("UPDATE bank_standin SET status=?, bank_p=?, bank_at=?, diff_p=? WHERE id=? AND status=?",
                    ("replaced" if r["status"] == "confirmed" else "lapsed", bp, _stamp(now), bp - int(r["amount_p"]), r["id"], r["status"]))
        if r["status"] == "confirmed":
            changed.append((r["unit"], r["business_date"]))
    con.commit()
    for u, d in dict.fromkeys(changed):
        _fire(con, u, d)
    return len(changed)


def standing(con, unit, d, now=None):
    """THE ONE FUNCTION every unit reads.  The owner-confirmed POS total standing in for the bank on that
    unit's day, or None.  None when nothing is confirmed, and None the moment the bank's statement is in.
    A PURE READ: it creates nothing, writes nothing and commits nothing, so the reconcilers that call it in
    the middle of their own work (clinic_money.match_day, darpan_kal.compute_day) stay exactly as pure as they were."""
    if not _iso_ok(d):
        return None
    now = now or _now()
    try:
        got = _rows(con, unit, d, "confirmed")
    except Exception:                                    # noqa: BLE001 -- the table is not there yet: nothing was ever typed
        return None
    if not got:
        return None
    if bank_in(bank_state(con, unit, d, now=now)):
        return None                                      # the bank wins at once; sweep() closes the row on the next page read
    r = got[0]
    never = never_received(con, unit, d, now=now)
    return dict(id=r["id"], unit=unit, date=d, amount_p=int(r["amount_p"]), typed_by=r["typed_by"], typed_at=r["typed_at"],
                confirmed_by=r["decided_by"], confirmed_at=r["decided_at"], by_owner=bool(r["by_owner"]),
                never=never, label=(LABEL_NEVER if never else LABEL_PROV), tolerance_p=tolerance_p(con))


def day(con, unit, d, now=None):
    """Everything a unit's page needs to draw the one field for one day.
       show   draw the block at all            offer   draw the input for staff
       state  the bank's word                   typed / confirmed / rejected: the row that matters, or None"""
    out = dict(unit=unit, date=d, on=False, show=False, offer=False, bank_in=False, due=False, state="bad_date",
               typed=None, confirmed=None, rejected=None, never=False, label="", tolerance_p=DEF_TOL_P, expect=DEF_EXPECT)
    if not _iso_ok(d):
        return out
    ensure(con)
    now = now or _now()
    st = bank_state(con, unit, d, now=now)
    out.update(on=is_on(con), state=st, bank_in=bank_in(st), due=(st in ("not_received", "rejected")),
               tolerance_p=tolerance_p(con), expect=expect_text(con))
    if out["bank_in"]:
        sweep(con, now=now)
        return out
    rows = _rows(con, unit, d)
    conf = next((r for r in rows if r["status"] == "confirmed"), None)
    typed = next((r for r in rows if r["status"] == "typed"), None)
    out["confirmed"], out["typed"] = conf, typed
    if conf is None and typed is None and rows and rows[0]["status"] == "rejected":
        out["rejected"] = rows[0]
    if conf is not None:
        out["never"] = never_received(con, unit, d, now=now)
        out["label"] = LABEL_NEVER if out["never"] else LABEL_PROV
    has_row = conf is not None or typed is not None or out["rejected"] is not None
    out["offer"] = bool(out["on"] and out["due"] and conf is None)
    out["show"] = bool(out["offer"] or has_row)
    return out


def type_figure(con, unit, d, amount_p, user, owner=False, now=None):
    """One number.  A staff figure waits for the owner; the owner's own stands at once.
    -> (ok, code, row-or-None).  codes: saved | confirmed | bad_date | future | bank_in | not_due | off |
    already_confirmed | bad_amount"""
    ensure(con)
    now = now or _now()
    if not _iso_ok(d):
        return False, "bad_date", None
    if d >= now.date().isoformat():
        return False, "future", None                    # a day's statement cannot be missing before the day is over
    try:
        amount_p = int(amount_p)
    except (TypeError, ValueError):
        return False, "bad_amount", None
    if amount_p < 0 or amount_p > 1_000_000_000:
        return False, "bad_amount", None
    st = bank_state(con, unit, d, now=now)
    if bank_in(st):
        sweep(con, now=now)
        return False, "bank_in", None
    stamp = _stamp(now)
    if owner:
        con.execute("UPDATE bank_standin SET status='superseded', note=CASE WHEN note='' THEN ? ELSE note END "
                    "WHERE unit=? AND business_date=? AND status IN ('typed','confirmed')",
                    ("superseded by %s's own figure, %s" % (user, stamp), unit, d))
        cur = con.execute("INSERT INTO bank_standin (unit, business_date, amount_p, typed_by, typed_at, by_owner, status, decided_by, decided_at) "
                          "VALUES (?,?,?,?,?,1,'confirmed',?,?)", (unit, d, amount_p, user, stamp, user, stamp))
        con.commit()
        row = dict(con.execute("SELECT * FROM bank_standin WHERE id=?", (cur.lastrowid,)).fetchone())
        _fire(con, unit, d)
        return True, "confirmed", row
    if not is_on(con):
        return False, "off", None
    if st not in ("not_received", "rejected"):
        return False, "not_due", None
    if _rows(con, unit, d, "confirmed"):
        return False, "already_confirmed", None
    con.execute("UPDATE bank_standin SET status='superseded', note=CASE WHEN note='' THEN ? ELSE note END "
                "WHERE unit=? AND business_date=? AND status='typed'", ("typed again by %s, %s" % (user, stamp), unit, d))
    cur = con.execute("INSERT INTO bank_standin (unit, business_date, amount_p, typed_by, typed_at, by_owner, status) "
                      "VALUES (?,?,?,?,?,0,'typed')", (unit, d, amount_p, user, stamp))
    con.commit()
    return True, "saved", dict(con.execute("SELECT * FROM bank_standin WHERE id=?", (cur.lastrowid,)).fetchone())


def decide(con, rid, word, user, note="", units_allowed=None, now=None):
    """The owner's word on one row: confirm | reject | seen.  -> (ok, code, row-or-None).
    codes: confirmed | rejected | seen | not_found | not_yours | not_waiting | bank_in | bad_word"""
    ensure(con)
    now = now or _now()
    try:
        rid = int(rid)
    except (TypeError, ValueError):
        return False, "not_found", None
    r = con.execute("SELECT * FROM bank_standin WHERE id=?", (rid,)).fetchone()
    if r is None:
        return False, "not_found", None
    r = dict(r)
    if units_allowed is not None and r["unit"] not in units_allowed:
        return False, "not_yours", r
    stamp = _stamp(now)
    if word == "seen":
        if r["status"] != "replaced":
            return False, "not_waiting", r
        con.execute("UPDATE bank_standin SET seen_by=?, seen_at=? WHERE id=?", (user, stamp, rid))
        con.commit()
        return True, "seen", r
    if word not in ("confirm", "reject"):
        return False, "bad_word", r
    if r["status"] != "typed":
        return False, "not_waiting", r
    if bank_in(bank_state(con, r["unit"], r["business_date"], now=now)):
        sweep(con, now=now)
        return False, "bank_in", r
    if word == "reject":
        con.execute("UPDATE bank_standin SET status='rejected', decided_by=?, decided_at=?, note=? WHERE id=?",
                    (user, stamp, (note or "").strip()[:200], rid))
        con.commit()
        return True, "rejected", r
    con.execute("UPDATE bank_standin SET status='superseded', note=CASE WHEN note='' THEN ? ELSE note END "
                "WHERE unit=? AND business_date=? AND status='confirmed'", ("superseded at %s" % stamp, r["unit"], r["business_date"]))
    con.execute("UPDATE bank_standin SET status='confirmed', decided_by=?, decided_at=? WHERE id=?", (user, stamp, rid))
    con.commit()
    _fire(con, r["unit"], r["business_date"])
    return True, "confirmed", dict(con.execute("SELECT * FROM bank_standin WHERE id=?", (rid,)).fetchone())


def save_settings(con, tol_rupees=None, hhmm=None, on=None):
    """The two settings the owner changes on screen (and the switch).  -> (ok, message)."""
    said = []
    if tol_rupees is not None and str(tol_rupees).strip() != "":
        try:
            t = float(str(tol_rupees).replace(",", "").replace("₹", "").strip())
        except ValueError:
            return False, "The tolerance is not a number."
        if t < 0 or t > 100000:
            return False, "The tolerance must be between ₹0 and ₹1,00,000."
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (KEY_TOL, str(int(round(t * 100))), "S496: a typed POS total vs the bank's own figure -- beyond this, one line for the owner (paise)"))
        said.append("tolerance ₹%s" % rupees(int(round(t * 100))))
    if hhmm is not None and str(hhmm).strip() != "":
        hm = parse_hhmm(str(hhmm).replace(".", ":"))
        if hm is None:
            return False, "The time must read like 10:00."
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (KEY_EXPECT, "%02d:%02d" % hm, "S496: the bank's statement for a day is expected on the box by this time (IST) the next morning"))
        said.append("bank expected by %02d:%02d" % hm)
    if on is not None:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)",
                    (KEY_ON, "1" if on else "0", "S496: 1 = staff are offered the POS-total field while a bank statement is missing"))
        said.append("the staff field is %s" % ("on" if on else "off"))
    con.commit()
    return True, ("Saved: " + " · ".join(said) + ".") if said else "Nothing changed."


# ------------------------------------------------------------------ the owner's lines
def owner_items(con, unit_list=None, now=None):
    """What reaches the owner, one line each, English:
         pos_typed   a staff figure waiting for Confirm / Reject
         pos_diff    the bank landed on a confirmed figure and differs beyond the tolerance (until 'seen')
         pos_never   a confirmed figure still standing, the bank's statement never received (stays)"""
    ensure(con)
    now = now or _now()
    sweep(con, now=now)
    tol = tolerance_p(con)
    q = "SELECT * FROM bank_standin WHERE status IN ('typed','confirmed','replaced')"
    items = []
    for r in [dict(x) for x in con.execute(q + " ORDER BY business_date DESC, id DESC")]:
        if unit_list is not None and r["unit"] not in unit_list:
            continue
        lab, d = unit_label(con, r["unit"]), r["business_date"]
        base = dict(id=r["id"], unit=r["unit"], unit_label=lab, date=d, amount_p=int(r["amount_p"]),
                    typed_by=r["typed_by"], typed_at=r["typed_at"])
        if r["status"] == "typed":
            items.append(dict(base, kind="pos_typed",
                              line="POS total waiting for you — %s · %s · ₹%s · typed by %s, %s"
                                   % (lab, human(d), rupees(r["amount_p"]), r["typed_by"] or "staff", _short(r["typed_at"]))))
        elif r["status"] == "replaced":
            if r["seen_at"] or r["diff_p"] is None or abs(int(r["diff_p"])) <= tol:
                continue
            items.append(dict(base, kind="pos_diff", bank_p=int(r["bank_p"] or 0), diff_p=int(r["diff_p"]),
                              line="Bank statement in — %s · %s · typed ₹%s · bank ₹%s · difference ₹%s (bank %s)"
                                   % (lab, human(d), rupees(r["amount_p"]), rupees(r["bank_p"]), rupees(abs(int(r["diff_p"]))),
                                      "more" if int(r["diff_p"]) > 0 else "less")))
        elif r["status"] == "confirmed" and never_received(con, r["unit"], d, now=now):
            items.append(dict(base, kind="pos_never", amber=True,
                              line="%s · %s · POS total ₹%s standing — %s" % (lab, human(d), rupees(r["amount_p"]), LABEL_NEVER)))
    return items


def recent_days(now=None, n=10):
    """Yesterday first, n days back -- the days a statement can be missing for; his own typing picks from these."""
    now = now or _now()
    return [(now.date() - dt.timedelta(days=i)).isoformat() for i in range(1, n + 1)]


def _short(stamp):
    """'2026-10-07 12:05:11' -> '07-Oct 12:05'."""
    try:
        return dt.datetime.fromisoformat(str(stamp).replace(" ", "T")).strftime("%d-%b %H:%M")
    except (ValueError, TypeError):
        return str(stamp or "")


# ------------------------------------------------------------------ the owner's block, for a no-JavaScript page
def owner_block_html(con, unit_list, can_act, now=None):
    """The card drawn on /finance/clinic/money (clinic_money.py posts it back to owner_post below).
    English.  Lines first; his own typing and the two settings folded under one line."""
    now = now or _now()
    items = owner_items(con, unit_list, now=now)
    out = []
    waiting = [i for i in items if i["kind"] == "pos_typed"]
    diffs = [i for i in items if i["kind"] == "pos_diff"]
    never = [i for i in items if i["kind"] == "pos_never"]
    for i in waiting:
        btn = ("""<form method="post" class="answer"><input type="hidden" name="act" value="standin_decide"><input type="hidden" name="id" value="%d">
              <button type="submit" name="word" value="confirm" class="save">Confirm</button>
              <button type="submit" name="word" value="reject" class="clear" style="margin-left:14px">Reject</button></form>""" % i["id"]) if can_act else \
              "<p class='mut'>Dr Manoj confirms or rejects this.</p>"
        out.append("<div class='flag f_owner'><p class='ftext'><b>%s</b></p>"
                   "<p class='mut'>Until you confirm, the day stands exactly as it does now. After you confirm it reads “%s”.</p>%s</div>"
                   % (_esc(i["line"]), LABEL_PROV, btn))
    for i in diffs:
        btn = ("""<form method="post" class="answer"><input type="hidden" name="act" value="standin_decide"><input type="hidden" name="id" value="%d">
              <button type="submit" name="word" value="seen" class="save">Seen</button></form>""" % i["id"]) if can_act else ""
        out.append("<div class='flag f_expl'><p class='ftext'><b>%s</b></p>"
                   "<p class='mut'>The bank's own figure is now used for that day and the day has been re-matched on it. The typed figure is kept as a record.</p>%s</div>"
                   % (_esc(i["line"]), btn))
    if never:
        out.append("<details class='flag'><summary><b>%d day%s stand%s on a POS total — %s</b></summary><ul class='lines mut'>%s</ul></details>"
                   % (len(never), "" if len(never) == 1 else "s", "s" if len(never) == 1 else "", LABEL_NEVER,
                      "".join("<li>%s</li>" % _esc(i["line"]) for i in never)))
    opts = "".join("<option value='%s'>%s</option>" % (_esc(u), _esc(unit_label(con, u))) for u in unit_list)
    days = "".join("<option value='%s'>%s</option>" % (d, _esc(human(d))) for d in recent_days(now))
    fold = ""
    if can_act:
        fold = """<details><summary>Bank statement missing? Type the POS total yourself · settings</summary>
          <form method="post"><input type="hidden" name="act" value="standin_type">
          <p class="mut">Your own figure stands at once — no second confirmation. It is refused if that day's bank statement is already in.</p>
          <table class="grid entry"><tbody>
            <tr><th class="sec">Unit</th><td><select name="unit" class="note">%s</select></td></tr>
            <tr><th class="sec">Day</th><td><select name="date" class="note">%s</select></td></tr>
            <tr><th class="sec">UPI total on the POS machine (₹)</th><td><input name="amount" inputmode="decimal" autocomplete="off" class="amt" placeholder="0"></td></tr>
          </tbody></table><button type="submit" class="save">Save — it stands in for the bank</button></form>
          <h2 style="margin-top:22px">Settings</h2>
          <form method="post"><input type="hidden" name="act" value="standin_settings">
          <table class="grid entry"><tbody>
            <tr><th class="sec">Tolerance (₹)<br><span class="hint">if the bank's figure differs from the typed one by more than this, you get one line</span></th>
                <td><input name="tolerance" inputmode="decimal" autocomplete="off" class="amt" value="%s"></td></tr>
            <tr><th class="sec">Bank statement expected by (IST, next morning)<br><span class="hint">staff are offered the field only after this time</span></th>
                <td><input name="expect" class="note" value="%s" maxlength="5" placeholder="10:00"></td></tr>
            <tr><th class="sec">Offer the field to staff</th><td><select name="on" class="note"><option value="1"%s>yes</option><option value="0"%s>no — only I type it</option></select></td></tr>
          </tbody></table><button type="submit" class="save">Save settings</button></form></details>""" % (
            opts, days, rupees(tolerance_p(con)).replace(",", ""), expect_text(con),
            " selected" if is_on(con) else "", "" if is_on(con) else " selected")
    if not out and not fold:
        return ""
    head = "<h2>POS total in place of a missing bank statement</h2>" if out else ""
    return "<div class='card' id='postotal'>%s%s%s</div>" % (head, "".join(out), fold)


def owner_post(con, form, user, can_act, unit_list, now=None):
    """The three acts of the block above.  -> a message div (clinic_money's own classes)."""
    if not can_act:
        return "<div class='bad'>Only Dr Manoj's login confirms a POS total.</div>"
    act = form.get("act") or ""
    if act == "standin_decide":
        ok, code, r = decide(con, form.get("id"), form.get("word") or "", user, units_allowed=unit_list, now=now)
        if ok and code == "confirmed":
            return ("<div class='ok'>Confirmed: ₹%s stands in for the bank on %s (%s) — %s. The day has been re-matched on it.</div>"
                    % (rupees(r["amount_p"]), human(r["business_date"]), _esc(unit_label(con, r["unit"])), LABEL_PROV))
        if ok and code == "rejected":
            return "<div class='ok'>Rejected. Nothing changed for that day; staff can type it again.</div>"
        if ok:
            return "<div class='ok'>Noted.</div>"
        return "<div class='bad'>%s</div>" % {
            "bank_in": "The bank's statement for that day has arrived in the meantime — the bank's own figure is used; nothing to confirm.",
            "not_waiting": "That line was already answered.", "not_found": "No such line.",
            "not_yours": "That line belongs to another page."}.get(code, "Nothing happened.")
    if act == "standin_type":
        unit = (form.get("unit") or "").strip()
        if unit not in unit_list:
            return "<div class='bad'>Which unit?</div>"
        d = (form.get("date") or "").strip()[:10]
        amt, e = paise(form.get("amount"))
        if e or amt is None:
            return "<div class='bad'><b>Nothing was saved.</b> The figure is the one thing needed%s.</div>" % ((" — " + e) if e else "")
        ok, code, r = type_figure(con, unit, d, amt, user, owner=True, now=now)
        if ok:
            return ("<div class='ok'>Saved: ₹%s stands in for the bank on %s (%s) — %s.</div>"
                    % (rupees(amt), human(d), _esc(unit_label(con, unit)), LABEL_PROV))
        return "<div class='bad'><b>Nothing was saved.</b> %s</div>" % {
            "bank_in": "The bank's statement for that day is already in — its own figure is used.",
            "future": "That day is not over yet.", "bad_date": "That is not a date.",
            "bad_amount": "That is not an amount."}.get(code, "")
    if act == "standin_settings":
        ok, msg = save_settings(con, form.get("tolerance"), form.get("expect"), (form.get("on") != "0") if form.get("on") is not None else None)
        return "<div class='%s'>%s</div>" % ("ok" if ok else "bad", _esc(msg))
    return "<div class='bad'>Nothing happened.</div>"


def paise(v):
    """A rupee figure typed by a person: blank is None, a non-number is refused, never a quiet 0."""
    s = str(v or "").replace(",", "").replace("₹", "").strip()
    if s == "":
        return None, None
    try:
        f = float(s)
    except ValueError:
        return None, "%r is not a number" % s[:12]
    if f < 0:
        return None, "a negative amount"
    if f > 10_000_000:
        return None, "far too large"
    return int(round(f * 100)), None
