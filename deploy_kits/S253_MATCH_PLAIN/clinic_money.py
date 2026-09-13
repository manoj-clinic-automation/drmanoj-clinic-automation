#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clinic_money.py -- S249: the clinic's money, joined into one morning verdict.

THE OWNER, 13-Sep-2026 (five rulings in one day, folded into S249_CLINIC_MONEY_FINAL_PLAN):

    "staff entered the docterz daily collection from yesterday night at end of day, you
     generated its docterz revenue from docterz export and bank mpr of same day, now i want a
     cross match of both, and a human friendly analysis take away to do away the manual
     matching in morning, only your flags will be needed to clarify"

    "reception staff do the morning first pass -- shavez does the first pass when they are
     not available, and shavez is the checker when they do the first pass, i get minimum
     required flags, all flags stay in staff apps till reconciled"

    "Physiotherapy amount is paid to me or dr Bhawna daily, in night, clubbed with the Docterz
     collection, add a backend physiotherapy revenue table ... manoj Bhati also gets this, a
     new pwa member, clinic physiotherapist ... he gets this feed and table and current month
     expanded and previous months collapsed"   /   "Bhati doesn't type in the table, reception
     does it, he only views it"   /   "the data he gets is only and only of the physiotherapy
     part, he does not get any revenue feed of my doctor's patients"

    "the extra upi input box shd have a flow so that it is very easy for staff, icici upi not
     working - paid to other upi - box opens, it accepts odd day outages also for some payment
     in each upi app"

    "reception staff want some loose currency ... 2500 rupees as 10 of 50, 10 of 100, 5 of
     200 ... at end of day put also what is the balance of this amount and what denominations
     and amount they need, so the cash flow and calculation stays stable and accurate"

THE ONE RULE (plan section 0): every rupee has exactly one declared channel, and every channel
says out loud whether an independent record exists for it.

    1 cash            no independent record   counted, never matched
    2 ICICI QR UPI    the MPR, per txn, T+1   MATCHED, transaction by transaction
    3 card            none                    compared against the counter only
    4 Razorpay/portal email only              named, never expected in the MPR
    5 other UPI       none at all             reception's word, said plainly, totalled monthly
    6 physiotherapy   none                    its own table, out of the match
    -- the float      NOT REVENUE             moves the handover, never the collection

WHAT THIS MODULE HOLDS

  the reconciler       match_day(con, date)  -- four passes, cheapest first, then the explanation
                       layer; only what no pattern claims becomes a flag.  Pure: reads, computes,
                       never changes a figure anyone entered, never invents an adjustment.
  the staff card       /finance/clinic/match/<date>  -- reception makes the first pass, the named
                       checker (setting clinic_money.checker, default shavez) the second; when the
                       checker makes the first pass himself the day closes on it, marked
                       "one pass only".  Flags live here until reconciled -- never dismissed,
                       never aged out.
  the owner's line     /finance/clinic/money  -- exactly four things reach him: a flag staff could
                       not explain, a flag where maker and checker disagree, money that never
                       lands, a counter sheet still unfilled after the day has passed.  Plus the
                       running monthly totals of every channel that has no independent record.
  other UPI            the box on the counter sheet (rendered by register_blocks, posted here):
                       amount is the only compulsory field; phone and app remember themselves;
                       one reason per day, three taps.
  the float            issued once by the owner; counted at close on the same denomination grid;
                       change requests and shortfalls recorded; NEVER part of any collection.
  physiotherapy        /finance/physio  -- the revenue table (current month open, earlier months
                       folded).  Reception writes it from the counter sheet; the physiotherapist
                       only reads it; the doctors tap "received".

WHO MAY REACH WHAT -- gated at the SERVER, never by hiding a tile (F-84):
  /finance/clinic/...  the clinic unit's maker/checker roles, as every clinic page already is.
  /finance/physio/...  a NEW unit 'physio' (the schema's role CHECK allows maker/checker/viewer
                       only, so "the physio role" is a unit, not a role word).  Bhati is a viewer
                       there and holds NO row in the clinic unit, so the front gate refuses him
                       every /finance/clinic/... address before any route runs.  The doctors and
                       the desk are seeded into the physio unit by the installer.

NO JAVASCRIPT on any page here.  Tables are created on first request, never at import (F-303).
Every write is audited through the app's audit() when it is passed in.
"""
import datetime as dt
import json
import os

from flask import Blueprint, redirect, request

bp = Blueprint("clinic_money", __name__)
_db = None
_require = None
_audit = None
_unit = "clinic"
PHYSIO_UNIT = "physio"
APP_VERSION = "S253-CLINIC-MONEY-1.2-PLAIN-CARD"

DEFAULT_CHECKER = "shavez"                 # setting clinic_money.checker overrides
CHECKER_SETTING = "clinic_money.checker"
CONSULT_FEES_P = (60000, 50000)            # "whole fee" hints: a multiple of 600 or 500
SMALL_P = 10000                            # under Rs 100: a note, never a flag
MPR_EXPECT_HHMM = (12, 20)                 # bank_mpr_status: the MPR is on the box by ~12:20 on D+1
UNFILLED_OWNER_HHMM = (14, 0)              # a sheet still empty at 14:00 the next day reaches the owner

# the float's standing composition -- the owner's words: 10 x 50, 10 x 100, 5 x 200
FLOAT_NOTES = ((500, "n500"), (200, "n200"), (100, "n100"), (50, "n50"), (20, "n20"), (10, "n10"))
FLOAT_KEYS = [k for _, k in FLOAT_NOTES]
FLOAT_DEFAULT = {"n200": 5, "n100": 10, "n50": 10}

UPI_APPS = ("PhonePe", "Google Pay", "Paytm", "BHIM", "other")
OUTAGE_REASONS = (("just_one", "just this one payment", "sirf yeh ek payment"),
                  ("a_while", "ICICI UPI was down for a while", "kuch der ke liye band tha"),
                  ("all_day", "ICICI UPI was down all day", "poora din band tha"))

# S253: money that Docterz and the counter book under DIFFERENT HEADS by habit -- the owner's own
# facts, one line each: (amount, Docterz head, counter head, what it is).  A head move is never money.
HEAD_MOVES = ((5000, "xray", "proc", "₹50 blood sugar test"),)      # Docterz: under X-ray; the counter: under procedures

ONLINE_MODES = ("Online Payment", "Net Banking", "Patient APP", "Wallet")
CARD_MODES = ("Debit Card", "Credit Card")

SCHEMA = """
CREATE TABLE IF NOT EXISTS clinic_physio_day (
  business_date TEXT PRIMARY KEY,
  cash_p INTEGER NOT NULL DEFAULT 0,
  upi_p  INTEGER NOT NULL DEFAULT 0,
  note TEXT NOT NULL DEFAULT '', entered_by TEXT NOT NULL DEFAULT '',
  entered_at TEXT NOT NULL DEFAULT '', updated_by TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS clinic_other_upi (
  id INTEGER PRIMARY KEY,
  business_date TEXT NOT NULL,
  amount_p INTEGER NOT NULL,
  phone TEXT NOT NULL DEFAULT '',
  app TEXT NOT NULL DEFAULT '',
  bill_no TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  entered_by TEXT NOT NULL DEFAULT '', entered_at TEXT NOT NULL DEFAULT '',
  settled_at TEXT NOT NULL DEFAULT '', settled_by TEXT NOT NULL DEFAULT '',
  settled_to TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS ix_clinic_other_upi_date ON clinic_other_upi(business_date);
CREATE TABLE IF NOT EXISTS clinic_other_upi_day (
  business_date TEXT PRIMARY KEY,
  reason TEXT NOT NULL DEFAULT 'just_one',
  note TEXT NOT NULL DEFAULT '',
  by_whom TEXT NOT NULL DEFAULT '', at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS clinic_float_event (
  id INTEGER PRIMARY KEY,
  business_date TEXT NOT NULL,
  kind TEXT NOT NULL,
  amount_p INTEGER NOT NULL,
  n500 INTEGER NOT NULL DEFAULT 0, n200 INTEGER NOT NULL DEFAULT 0, n100 INTEGER NOT NULL DEFAULT 0,
  n50 INTEGER NOT NULL DEFAULT 0, n20 INTEGER NOT NULL DEFAULT 0, n10 INTEGER NOT NULL DEFAULT 0,
  given_to TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  by_whom TEXT NOT NULL DEFAULT '', at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS clinic_float_day (
  business_date TEXT PRIMARY KEY,
  n500 INTEGER NOT NULL DEFAULT 0, n200 INTEGER NOT NULL DEFAULT 0, n100 INTEGER NOT NULL DEFAULT 0,
  n50 INTEGER NOT NULL DEFAULT 0, n20 INTEGER NOT NULL DEFAULT 0, n10 INTEGER NOT NULL DEFAULT 0,
  kept_p INTEGER NOT NULL DEFAULT 0,
  open_p INTEGER NOT NULL DEFAULT 0,
  standing_p INTEGER NOT NULL DEFAULT 0,
  need TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  by_whom TEXT NOT NULL DEFAULT '', at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS clinic_money_day (
  business_date TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'open',
  maker TEXT NOT NULL DEFAULT '', maker_at TEXT NOT NULL DEFAULT '',
  checker TEXT NOT NULL DEFAULT '', checker_at TEXT NOT NULL DEFAULT '',
  one_pass INTEGER NOT NULL DEFAULT 0,
  closed_at TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS clinic_money_flag (
  id INTEGER PRIMARY KEY,
  business_date TEXT NOT NULL,
  key TEXT NOT NULL,
  code TEXT NOT NULL,
  amount_p INTEGER NOT NULL DEFAULT 0,
  text TEXT NOT NULL DEFAULT '',
  owner INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL DEFAULT 'open',
  explanation TEXT NOT NULL DEFAULT '',
  explained_by TEXT NOT NULL DEFAULT '', explained_at TEXT NOT NULL DEFAULT '',
  checker_word TEXT NOT NULL DEFAULT '',
  checker_by TEXT NOT NULL DEFAULT '', checker_at TEXT NOT NULL DEFAULT '',
  reconciled_by TEXT NOT NULL DEFAULT '', reconciled_at TEXT NOT NULL DEFAULT '',
  owner_note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT '',
  UNIQUE (business_date, key)
);
CREATE INDEX IF NOT EXISTS ix_clinic_money_flag_status ON clinic_money_flag(status, owner);
"""
# physio handover columns -- the table predates this kit (S223), so an existing box needs them.
MIGRATE = ["ALTER TABLE clinic_physio_day ADD COLUMN handed_to TEXT NOT NULL DEFAULT ''",
           "ALTER TABLE clinic_physio_day ADD COLUMN handed_at TEXT NOT NULL DEFAULT ''",
           "ALTER TABLE clinic_physio_day ADD COLUMN received_by TEXT NOT NULL DEFAULT ''",
           "ALTER TABLE clinic_physio_day ADD COLUMN received_at TEXT NOT NULL DEFAULT ''",
           # S252: a change request is closed by the person who hands the notes over
           "ALTER TABLE clinic_float_day ADD COLUMN need_done TEXT NOT NULL DEFAULT ''"]

_schema_done = False


def _ensure(con):
    """On first use, inside a request -- never at import (the S223 outage, F-303)."""
    global _schema_done
    if _schema_done:
        return
    con.executescript(SCHEMA)
    for stmt in MIGRATE:
        try:
            con.execute(stmt)
        except Exception:                        # noqa: BLE001
            pass
    con.commit()
    _schema_done = True


def init(app, db_getter, require_fn, audit_fn=None, unit="clinic", url_prefix=""):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, _unit
    _db, _require, _audit, _unit = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


# ---------------------------------------------------------------- small helpers
def _r(p):
    return "—" if p is None else "{:,}".format(int(round(p / 100.0)))


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _iso_ok(d):
    try:
        return dt.date(int(d[:4]), int(d[5:7]), int(d[8:10])).isoformat() == d
    except (ValueError, IndexError, TypeError):
        return False


def _human(iso):
    return dt.date.fromisoformat(iso).strftime("%d-%b-%Y") if _iso_ok(iso) else (iso or "—")


def _now():
    """The box's clock is IST.  CLINIC_MONEY_NOW=<iso> pins it for the walk."""
    v = os.environ.get("CLINIC_MONEY_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _paise(v):
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


def _setting(con, key, default=""):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        return r["value"] if r and r["value"] else default
    except Exception:                            # noqa: BLE001
        return default


def checker_name(con):
    return (_setting(con, CHECKER_SETTING, DEFAULT_CHECKER) or DEFAULT_CHECKER).strip().lower()


def _table(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _audit_safe(con, table, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, table, row_id, action, before=before, after=after, who=who)
        con.commit()
    except Exception:                            # noqa: BLE001
        pass


def _banking_days_after(d, n):
    """d + n banking days (Sunday is not one), as a date."""
    x = d
    while n > 0:
        x += dt.timedelta(days=1)
        if x.weekday() != 6:
            n -= 1
    return x


# ---------------------------------------------------------------- channel 5: other UPI
def other_upi_rows(con, d):
    _ensure(con)
    return list(con.execute("SELECT * FROM clinic_other_upi WHERE business_date=? ORDER BY id", (d,)))


def other_upi_total_p(con, d):
    """The day's money that went to a personal phone -- NOT in the bank by nature."""
    try:
        _ensure(con)
        r = con.execute("SELECT COALESCE(SUM(amount_p),0) s FROM clinic_other_upi WHERE business_date=?",
                        (d,)).fetchone()
        return int(r["s"] or 0)
    except Exception:                            # noqa: BLE001
        return 0


def other_upi_day(con, d):
    return con.execute("SELECT * FROM clinic_other_upi_day WHERE business_date=?", (d,)).fetchone()


def _remembered(con, col):
    return [r[0] for r in con.execute(
        "SELECT %s FROM clinic_other_upi WHERE %s<>'' GROUP BY %s ORDER BY MAX(id) DESC LIMIT 6" % (col, col, col))]


# ---------------------------------------------------------------- the float
def float_standing_p(con, on=None):
    """The agreed float: what has been ISSUED minus what was taken back, up to a date.  A top-up
    restores a shortfall -- it changes what is physically at the counter, never the standing amount."""
    _ensure(con)
    q = "SELECT kind, amount_p FROM clinic_float_event"
    args = ()
    if on:
        q += " WHERE business_date<=?"
        args = (on,)
    tot = 0
    for r in con.execute(q, args):
        if r["kind"] == "issue":
            tot += r["amount_p"]
        elif r["kind"] == "return":
            tot -= r["amount_p"]
    return max(tot, 0)


def float_day(con, d):
    _ensure(con)
    return con.execute("SELECT * FROM clinic_float_day WHERE business_date=?", (d,)).fetchone()


def float_open_p(con, d):
    """The float at the start of day d: what was kept aside at the last count, plus anything
    issued / topped up / taken back since that count (up to and including d).  With no count
    yet, the standing amount.  Nothing when no float is in use."""
    standing = float_standing_p(con, d)
    if not standing:
        return 0
    prev = con.execute("SELECT kept_p, business_date FROM clinic_float_day WHERE business_date<? "
                       "ORDER BY business_date DESC LIMIT 1", (d,)).fetchone()
    if prev is None:
        return standing
    delta = 0
    for r in con.execute("SELECT kind, amount_p FROM clinic_float_event WHERE business_date>? AND business_date<=?",
                         (prev["business_date"], d)):
        delta += r["amount_p"] if r["kind"] in ("issue", "topup") else -r["amount_p"]
    return max(prev["kept_p"] + delta, 0)


def float_adjust_p(con, d):
    """How much the float moved the handover on day d: open - kept.  Positive = the float was
    released (handover is bigger), negative = the float was restored (handover is smaller).
    None when no float is in use, or it has not been counted for the day."""
    if not float_standing_p(con, d):
        return None
    row = float_day(con, d)
    if row is None:
        return None
    return float_open_p(con, d) - row["kept_p"]


def expected_handover_p(con, d):
    """day's collection (register cash + physio cash, UNCHANGED by the float)
       + float open - float kept.  On a normal day the float appears nowhere."""
    try:
        import clinic_register                                   # noqa: PLC0415  beside this file
        exp = clinic_register.expected_cash_p(con, d)
    except Exception:                            # noqa: BLE001
        exp = None
    if exp is None:
        return None
    adj = float_adjust_p(con, d)
    return exp + (adj or 0)


# ---------------------------------------------------------------- the float: composition, what is owed (S252)
FLOAT_KEEP = ((200, "n200"), (100, "n100"), (50, "n50"))       # the notes the counter actually keeps


def float_composition(con):
    """The agreed notes: what was issued (issue events only), else the owner's stated default."""
    comp = {k: 0 for k in FLOAT_KEYS}
    for ev in con.execute("SELECT * FROM clinic_float_event WHERE kind='issue' ORDER BY id"):
        for k in FLOAT_KEYS:
            comp[k] += ev[k] or 0
    if not any(comp.values()):
        comp.update(FLOAT_DEFAULT)
    return comp


def _comp_words(comp, only=FLOAT_NOTES):
    return ", ".join("%d × ₹%d" % (comp.get(k, 0), rs) for rs, k in only if comp.get(k))


def float_last_count(con):
    _ensure(con)
    return con.execute("SELECT * FROM clinic_float_day ORDER BY business_date DESC, at DESC LIMIT 1").fetchone()


def float_owed(con):
    """What the owner has to give reception, from the LAST count: dict(short_p, notes{k:n}, since, by)
    or None when the float is intact (or was topped up after that count)."""
    standing = float_standing_p(con)
    if not standing:
        return None
    row = float_last_count(con)
    if row is None:
        return None
    short = standing - row["kept_p"]
    if short <= 0:
        return None
    made_up = con.execute("SELECT COALESCE(SUM(amount_p),0) s FROM clinic_float_event WHERE kind='topup' "
                          "AND (business_date>? OR (business_date=? AND at>=?))",
                          (row["business_date"], row["business_date"], row["at"])).fetchone()["s"]
    short -= int(made_up or 0)
    if short <= 0:
        return None
    comp = float_composition(con)
    notes, left = {}, short
    for rs, k in FLOAT_KEEP:                                  # the missing notes, largest first, never more than the agreed count
        n = min(max(comp.get(k, 0) - (row[k] or 0), 0), left // (rs * 100))
        if n > 0:
            notes[k] = n
            left -= n * rs * 100
    for rs, k in FLOAT_KEEP:                                  # any remainder in whatever note fits
        if left <= 0:
            break
        n = left // (rs * 100)
        if n > 0:
            notes[k] = notes.get(k, 0) + n
            left -= n * rs * 100
    return dict(short_p=short, notes=notes, remainder_p=left, since=row["business_date"], by=row["by_whom"], row=row)


def float_change_asked(con):
    """The newest change request nobody has answered yet, or None."""
    _ensure(con)
    return con.execute("SELECT * FROM clinic_float_day WHERE need<>'' AND need_done='' "
                       "ORDER BY business_date DESC, at DESC LIMIT 1").fetchone()


def float_line(con):
    """ONE line about the float, for the owner's page and the day card."""
    standing = float_standing_p(con)
    if not standing:
        return "Float not issued yet."
    owed = float_owed(con)
    ask = float_change_asked(con)
    if owed is None:
        last = float_last_count(con)
        when = (" — last short day %s, made up" % _human(last["business_date"])) if (last is not None and last["standing_p"] - last["kept_p"] > 0) else ""
        line = "Float ₹%s intact%s." % (_r(standing), when)
    else:
        line = "Float ₹%s — ₹%s short since %s (%s). Give reception: %s%s." % (
            _r(standing - owed["short_p"]), _r(owed["short_p"]), _human(owed["since"]), owed["by"] or "reception",
            _comp_words(owed["notes"]) or "—", (" + ₹%s" % _r(owed["remainder_p"])) if owed["remainder_p"] else "")
    if ask is not None:
        line += " Change asked %s: %s." % (_human(ask["business_date"]), ask["need"])
    return line


# ---------------------------------------------------------------- physiotherapy
def physio_row(con, d):
    _ensure(con)
    return con.execute("SELECT * FROM clinic_physio_day WHERE business_date=?", (d,)).fetchone()


def physio_months(con):
    """[(ym, rows)] newest first, each row the day's record."""
    _ensure(con)
    out, cur = [], None
    for r in con.execute("SELECT * FROM clinic_physio_day WHERE cash_p>0 OR upi_p>0 OR handed_to<>'' "
                         "ORDER BY business_date DESC"):
        ym = r["business_date"][:7]
        if cur is None or cur[0] != ym:
            cur = (ym, [])
            out.append(cur)
        cur[1].append(r)
    return out


# ---------------------------------------------------------------- the data the match reads
def _register(con, d):
    if not _table(con, "clinic_register_day"):
        return None
    return con.execute("SELECT * FROM clinic_register_day WHERE business_date=?", (d,)).fetchone()


def _reg_totals(reg):
    heads = {}
    for sec in ("cons", "xray", "proc", "dress"):
        heads[sec] = {t: (reg["%s_%s_p" % (sec, t)] if reg is not None else 0) for t in ("cash", "upi", "card")}
    tender = {t: sum(heads[s][t] for s in heads) for t in ("cash", "upi", "card")}
    by_head = {"consult": sum(heads["cons"].values()),
               "xray": sum(heads["xray"].values()),
               "proc": sum(heads["proc"].values()) + sum(heads["dress"].values())}
    return tender, by_head


def _docterz(con, d):
    """What Docterz says for the day: by tender (split legs resolved) and by head; the online
    entries for pairing; the cash entries by amount.  known=False when no day was read."""
    out = {"known": False, "tender": {"cash": 0, "upi": 0, "card": 0, "other": 0},
           "head": {"consult": 0, "xray": 0, "proc": 0}, "online": [], "cash_by_amt": {}, "cash_entries": []}
    if not _table(con, "clinic_day_line"):
        return out
    rows = list(con.execute("SELECT section, sn, patient, clinic_id, amount_p, mode, shift FROM clinic_day_line "
                            "WHERE business_date=? AND section IN ('consult','xray','proc') ORDER BY section, sn", (d,)))
    if not rows:
        return out
    out["known"] = True
    split_ids = set()
    legs = []
    if _table(con, "clinic_day_tender"):
        legs = list(con.execute("SELECT clinic_id, invoice_no, tender, amount_p FROM clinic_day_tender "
                                "WHERE business_date=? ORDER BY clinic_id, invoice_no", (d,)))
    for l in legs:
        split_ids.add(l["clinic_id"])
        t = l["tender"]
        k = "cash" if t == "Cash" else ("card" if t in CARD_MODES else "upi")
        out["tender"][k] += l["amount_p"]
        if k == "upi":
            out["online"].append(dict(patient="", clinic_id=l["clinic_id"], amount_p=l["amount_p"],
                                      how="%s (part of split bill %s)" % (t, l["invoice_no"] or "")))
        elif k == "cash":
            out["cash_by_amt"][l["amount_p"]] = out["cash_by_amt"].get(l["amount_p"], 0) + 1
            out["cash_entries"].append(dict(patient="", clinic_id=l["clinic_id"], amount_p=l["amount_p"]))
    for r in rows:
        out["head"][r["section"]] += r["amount_p"] or 0
        if r["clinic_id"] in split_ids:
            continue
        m, p = (r["mode"] or "").strip(), r["amount_p"] or 0
        if m == "Cash":
            out["tender"]["cash"] += p
            out["cash_by_amt"][p] = out["cash_by_amt"].get(p, 0) + 1
            out["cash_entries"].append(dict(patient=r["patient"], clinic_id=r["clinic_id"], amount_p=p))
        elif m in CARD_MODES:
            out["tender"]["card"] += p
        elif m in ONLINE_MODES:
            out["tender"]["upi"] += p
            out["online"].append(dict(patient=r["patient"], clinic_id=r["clinic_id"], amount_p=p, how=m))
        elif m == "Split Payment":
            out["tender"]["other"] += p          # its legs were not recorded: counts in the total, not by tender
            out["split_nolegs"] = out.get("split_nolegs", 0) + 1
        else:
            out["tender"]["other"] += p
    return out


def our_online_p(con, d):
    """THE one 'our online' figure (F-459): Docterz online entries + the online halves of split
    bills.  finance_clinic_day.our_online_p is the same definition; this is the fallback."""
    try:
        import finance_clinic_day                                # noqa: PLC0415
        if hasattr(finance_clinic_day, "our_online_p"):
            return finance_clinic_day.our_online_p(con, d)
    except Exception:                            # noqa: BLE001
        pass
    return _docterz(con, d)["tender"]["upi"]


def _bank(con, d):
    """(state dict or None, [txn rows]).  state from bank_mpr_status when it is beside us."""
    state = None
    try:
        import bank_mpr_status                                   # noqa: PLC0415
        state = bank_mpr_status.mpr_state(con, d, unit=_unit)
    except Exception:                            # noqa: BLE001
        state = None
    rows = []
    if _table(con, "upi_txn"):
        rows = [dict(r) for r in con.execute(
            "SELECT txn_time, amount_p, rrn, mode FROM upi_txn WHERE unit=? AND txn_date=? ORDER BY txn_time, id",
            (_unit, d))]
    return state, rows


def _pairs(bank, ours):
    """Pair by amount, first come first served -- the S240 MPR page's rule."""
    left = list(ours)
    pairs, bank_only = [], []
    for b in bank:
        hit = next((i for i, o in enumerate(left) if o["amount_p"] == b["amount_p"]), None)
        if hit is None:
            bank_only.append(b)
        else:
            pairs.append((b, left.pop(hit)))
    return pairs, bank_only, left


def _whole_fee(p):
    a = abs(p)
    for fee in CONSULT_FEES_P:
        if a and a % fee == 0:
            return a // fee, fee
    return None


# ---------------------------------------------------------------- THE RECONCILER
def match_day(con, d, now=None):
    """Four passes, cheapest first, then the explanation layer.  Pure.

    Returns dict(date, filled, doc_known, bank, verdict, lines (the takeaway), explained[],
    flags[], notes[], p1, p2, p3, p4).  A flag is {key, code, amount_p, text, owner}."""
    now = now or _now()
    day = dt.date.fromisoformat(d)
    reg = _register(con, d)
    doc = _docterz(con, d)
    other = other_upi_total_p(con, d)
    other_rows = other_upi_rows(con, d)
    phy = physio_row(con, d)
    state, bank_rows = _bank(con, d)
    bank_state = (state or {}).get("state", "unknown")
    bank_known = bank_state in ("applied", "late", "no_rows")
    bank_p = sum(b["amount_p"] for b in bank_rows) if bank_known else None

    res = dict(date=d, filled=reg is not None, doc_known=doc["known"], bank_state=bank_state,
               bank_known=bank_known, bank_p=bank_p, other_upi_p=other, physio=phy,
               explained=[], flags=[], notes=[], lines=[], verdict="")
    explained, flags, notes = res["explained"], res["flags"], res["notes"]

    def flag(key, code, amount_p, text, owner=False):
        flags.append(dict(key=key, code=code, amount_p=int(amount_p or 0), text=text, owner=bool(owner)))

    def expl(code, amount_p, text):
        explained.append(dict(code=code, amount_p=int(amount_p or 0), text=text))

    # ---- the sheet itself ----------------------------------------------------------
    if reg is None:
        late = now >= dt.datetime.combine(day + dt.timedelta(days=1), dt.time(*UNFILLED_OWNER_HHMM))
        flag("not_filled", "not_filled", 0,
             "The counter sheet for %s has not been filled in%s." % (_human(d), " — the day has passed" if late else ""),
             owner=late)
        res["verdict"] = "not_filled"
        res["lines"] = ["%s: the counter sheet is not filled in yet — nothing can be matched until it is." % dt.date.fromisoformat(d).strftime("%A %d-%b")]
        return res
    if not doc["known"]:
        flag("no_docterz", "no_docterz", 0, "Docterz's day for %s has not been read yet — the sheet is filled, "
             "the match waits for the export." % _human(d))
        res["verdict"] = "waiting_docterz"
        res["lines"] = ["%s: waiting for the Docterz export. Nothing to do yet." % dt.date.fromisoformat(d).strftime("%A %d-%b")]
        return res

    r_t, r_h = _reg_totals(reg)
    d_t, d_h = doc["tender"], doc["head"]
    r_total = sum(r_t.values())
    d_total = sum(d_t.values())

    # ---- pass 1: the day's money ---------------------------------------------------
    diff1 = r_total - d_total
    res["p1"] = dict(counter_p=r_total, docterz_p=d_total, diff_p=diff1)
    # ---- pass 2: by head -----------------------------------------------------------
    p2 = [(h, r_h[h], d_h[h], r_h[h] - d_h[h]) for h in ("consult", "xray", "proc")]
    res["p2"] = p2
    # ---- pass 3: by tender ---------------------------------------------------------
    p3 = [(t, r_t[t], d_t[t], r_t[t] - d_t[t]) for t in ("cash", "upi", "card")]
    res["p3"] = p3
    if doc.get("split_nolegs"):
        notes.append("%d split bill%s ha%s no legs recorded — that money counts in the day's total but not by tender."
                     % (doc["split_nolegs"], "s" if doc["split_nolegs"] > 1 else "", "ve" if doc["split_nolegs"] > 1 else "s"))
    elif d_t["other"]:
        notes.append("Docterz carries ₹%s under a mode this page does not know; it counts in the day's total." % _r(d_t["other"]))

    # known head moves first (S253): the same money booked under different heads by habit
    hd = {h: x for h, _a, _b, x in p2}
    for amt, doc_head, cnt_head, what in HEAD_MOVES:
        n = 0
        while hd.get(doc_head, 0) <= -amt and hd.get(cnt_head, 0) >= amt:
            hd[doc_head] += amt
            hd[cnt_head] -= amt
            n += 1
        if n:
            expl("head_move", amt * n, "%s%s — Docterz counts it under %s, the counter under %s. Same money."
                 % (what, (" × %d" % n) if n > 1 else "", _HEAD[doc_head], _HEAD[cnt_head]))
    res["p2"] = [(h, a, b, hd[h]) for h, a, b, _x in p2]
    head_diffs = [(h, hd[h]) for h, _a, _b, _x in p2 if hd[h]]
    tender_diffs = [(t, x) for t, _a, _b, x in p3 if x]
    if diff1 == 0:
        if head_diffs:
            expl("head_swap", sum(abs(x) for _h, x in head_diffs) // 2,
                 "Same money, different head: " + "; ".join(
                     "%s ₹%s %s on the counter" % (_HEAD[h], _r(abs(x)), "more" if x > 0 else "less") for h, x in head_diffs) + ".")
        if tender_diffs:
            if len(tender_diffs) == 2 and tender_diffs[0][1] == -tender_diffs[1][1]:
                hi = tender_diffs[0] if tender_diffs[0][1] > 0 else tender_diffs[1]
                lo = tender_diffs[1] if hi is tender_diffs[0] else tender_diffs[0]
                expl("tender_swap", abs(hi[1]), "₹%s the counter put under %s, Docterz billed as %s."
                     % (_r(abs(hi[1])), _TENDER[hi[0]], _TENDER[lo[0]]))
            else:
                expl("tender_mix", sum(abs(x) for _t, x in tender_diffs) // 2,
                     "Same total, tenders written differently: " + "; ".join(
                         "%s ₹%s %s on the counter" % (_TENDER[t], _r(abs(x)), "more" if x > 0 else "less") for t, x in tender_diffs) + ".")
    else:
        more = "more" if diff1 > 0 else "less"
        where = "; ".join("%s ₹%s %s" % (_HEAD[h], _r(abs(x)), "more" if x > 0 else "less") for h, x in head_diffs)
        text = "The counter sheet has ₹%s %s than Docterz%s." % (_r(abs(diff1)), more, (" — " + where) if where else "")
        # the likely cause, in one plain sentence
        td = dict(tender_diffs)
        likely = []
        for t in ("card", "upi"):
            if td.get(t, 0) < 0 and td.get("cash", 0) > 0:
                k = min(-td[t], td["cash"])
                likely.append("₹%s paid by %s was written as cash" % (_r(k), _TENDER[t]))
                td["cash"] -= k
        if td.get("cash", 0) < 0 and td.get("upi", 0) > 0:
            k = min(-td["cash"], td["upi"])
            likely.append("₹%s paid in cash was written as UPI" % _r(k))
        wf = _whole_fee(diff1)
        if wf:
            likely.append("the counter has %s consultation%s %s than Docterz" % (
                wf[0] if wf[0] > 1 else "one", "s" if wf[0] > 1 else "", "more" if diff1 > 0 else "fewer"))
        if likely:
            text += " Most likely: " + "; ".join(likely) + "."
        if abs(diff1) < SMALL_P:
            notes.append(text + " Under ₹100 — noted, not flagged.")
        else:
            flag("total:%d" % diff1, "total_diff", diff1, text)

    # ---- pass 4: the bank, transaction by transaction ------------------------------
    expected_bank = d_t["upi"] - other
    res["expected_bank_p"] = expected_bank
    ours = list(doc["online"])
    for o in other_rows:                                   # channel 5 is explained before the bank is even read
        hit = next((i for i, x in enumerate(ours) if x["amount_p"] == o["amount_p"]), None)
        who = " (%s%s)" % (o["app"] or "UPI", (", " + o["phone"]) if o["phone"] else "")
        if hit is not None:
            x = ours.pop(hit)
            expl("other_upi", o["amount_p"], "₹%s went to another UPI%s — %s%s. Not in the bank by nature."
                 % (_r(o["amount_p"]), who, x.get("patient") or "entry", (" · ID " + x["clinic_id"]) if x.get("clinic_id") else ""))
        else:
            expl("other_upi", o["amount_p"], "₹%s went to another UPI%s — no Docterz online entry of that amount; "
                 "it is in the day's cash or card, or the bill is split. Not in the bank by nature." % (_r(o["amount_p"]), who))
    if not bank_known:
        if bank_state in ("waiting",):
            notes.append("The bank's MPR for this day has not arrived yet (expected about 12:20 the next day).")
        elif bank_state == "not_received":
            flag("mpr_missing", "mpr_missing", expected_bank, "The bank's MPR for %s has not arrived and its time has passed — "
                 "₹%s of online money cannot be checked until it does." % (_human(d), _r(expected_bank)))
        elif bank_state == "rejected":
            flag("mpr_rejected", "mpr_rejected", expected_bank, "The bank's MPR for %s was received but refused by the reader — "
                 "see /finance/clinic/bank/mpr/%s." % (_human(d), d))
        else:
            notes.append("The bank's word for this day is not known (%s)." % bank_state)
        res["p4"] = dict(pairs=[], bank_only=[], ours_only=ours)
    else:
        pairs, bank_only, ours_only = _pairs(bank_rows, ours)
        res["p4"] = dict(pairs=pairs, bank_only=bank_only, ours_only=ours_only)
        bdiff = (bank_p or 0) - expected_bank
        res["bank_diff_p"] = bdiff
        # bank rows with no partner but a cash entry of the same amount: rung as cash
        cash_left = dict(doc["cash_by_amt"])
        still_bank = []
        for b in bank_only:
            if cash_left.get(b["amount_p"], 0) > 0:
                cash_left[b["amount_p"]] -= 1
                whose = next((c for c in doc["cash_entries"] if c["amount_p"] == b["amount_p"]), None)
                expl("rung_as_cash", b["amount_p"], "The ₹%s at %s in the bank is almost certainly %s's ₹%s — paid by UPI, "
                     "written down as cash. No money is missing; the drawer will be short by the same."
                     % (_r(b["amount_p"]), b.get("txn_time") or "—", (whose or {}).get("patient") or "a cash entry", _r(b["amount_p"])))
            else:
                still_bank.append(b)
        for b in still_bank:
            flag("bank_extra:%s:%d" % ((b.get("rrn") or "")[-4:], b["amount_p"]), "bank_extra", b["amount_p"],
                 "₹%s reached the bank at %s (UPI ref …%s) and no Docterz entry of that amount exists — money arrived "
                 "that was not billed." % (_r(b["amount_p"]), b.get("txn_time") or "—", (b.get("rrn") or "")[-4:]))
        # our online entries the bank has not shown: unsettled first, missing only after two banking days
        deadline = dt.datetime.combine(_banking_days_after(day, 2), dt.time(*MPR_EXPECT_HHMM))
        for o in ours_only:
            who = "%s%s" % (o.get("patient") or "entry", (" · ID " + o["clinic_id"]) if o.get("clinic_id") else "")
            if now < deadline:
                notes.append("₹%s (%s, %s) is not in the bank yet — still to reach it; tomorrow's file." % (_r(o["amount_p"]), who, o["how"]))
            else:
                flag("not_in_bank:%s:%d" % (o.get("clinic_id") or "", o["amount_p"]), "not_in_bank", o["amount_p"],
                     "₹%s (%s, %s) never reached the ICICI account — two banking days have passed. Looks like portal "
                     "money, a card, or a UPI to another phone that was not recorded." % (_r(o["amount_p"]), who, o["how"]),
                     owner=True)

    if phy is not None and (phy["cash_p"] or phy["upi_p"]):
        notes.append("Physiotherapy ₹%s cash + ₹%s UPI is kept out of this match (its own table)." % (_r(phy["cash_p"]), _r(phy["upi_p"])))
    fl = float_day(con, d)
    if fl is not None:
        short = fl["standing_p"] - fl["kept_p"]
        notes.append("The float was kept aside at ₹%s%s — it is not part of the day's money." % (
            _r(fl["kept_p"]), (" (₹%s short of ₹%s)" % (_r(short), _r(fl["standing_p"]))) if short > 0 else ""))
    dayword = dt.date.fromisoformat(d).strftime("%A %d-%b")
    if not flags:
        res["verdict"] = "nothing_to_do"
        res["lines"] = ["%s: the counter sheet, Docterz and the bank agree. Nothing to do." % dayword]
    else:
        res["verdict"] = "flags"
        tot = next((f for f in flags if f["code"] == "total_diff"), None)
        if tot is not None and len(flags) == 1:
            res["lines"] = ["%s: the counter sheet has ₹%s %s than Docterz. Everything else matches or is explained."
                            % (dayword, _r(abs(tot["amount_p"])), "more" if tot["amount_p"] > 0 else "less")]
        else:
            n = len(flags)
            res["lines"] = ["%s: %d thing%s need%s a person. Everything else matches or is explained." % (dayword, n, "s" if n > 1 else "", "" if n > 1 else "s")]
    return res


_HEAD = {"consult": "consultation", "xray": "X-ray", "proc": "procedures + dressing"}
_HEAD_SHORT = {"consult": "Consult", "xray": "X-ray", "proc": "Proc + dress"}
_TENDER = {"cash": "cash", "upi": "UPI", "card": "card"}


# ---------------------------------------------------------------- flags that persist
def sync_flags(con, d, m):
    """Upsert the computed flags for the day; a flag whose cause has gone from the data is
    marked 'cleared' (never deleted -- the record that it was raised stays)."""
    _ensure(con)
    now = _stamp()
    have = {r["key"]: r for r in con.execute("SELECT * FROM clinic_money_flag WHERE business_date=?", (d,))}
    seen = set()
    for f in m["flags"]:
        seen.add(f["key"])
        r = have.get(f["key"])
        if r is None:
            con.execute("INSERT INTO clinic_money_flag (business_date, key, code, amount_p, text, owner, status, created_at) "
                        "VALUES (?,?,?,?,?,?,'open',?)", (d, f["key"], f["code"], f["amount_p"], f["text"], 1 if f["owner"] else 0, now))
        else:
            if r["status"] == "cleared":
                con.execute("UPDATE clinic_money_flag SET status='open', text=?, owner=? WHERE id=?",
                            (f["text"], 1 if f["owner"] else 0, r["id"]))
            elif r["text"] != f["text"] or bool(r["owner"]) != f["owner"]:
                con.execute("UPDATE clinic_money_flag SET text=?, owner=? WHERE id=?",
                            (f["text"], 1 if (f["owner"] or r["owner"]) else 0, r["id"]))
    for k, r in have.items():
        if k not in seen and r["status"] not in ("reconciled", "cleared"):
            con.execute("UPDATE clinic_money_flag SET status='cleared', reconciled_at=?, reconciled_by='the data' WHERE id=?", (now, r["id"]))
    con.commit()
    return list(con.execute("SELECT * FROM clinic_money_flag WHERE business_date=? ORDER BY owner DESC, id", (d,)))


def day_state(con, d):
    _ensure(con)
    return con.execute("SELECT * FROM clinic_money_day WHERE business_date=?", (d,)).fetchone()


def owner_queue(con):
    """Exactly the four things: unexplained (checker agreed it cannot be explained), maker/checker
    disagreement, money that never lands, a sheet unfilled after the day has passed."""
    _ensure(con)
    return list(con.execute(
        "SELECT * FROM clinic_money_flag WHERE status='to_owner' OR (owner=1 AND status IN ('open','explained','cannot')) "
        "ORDER BY business_date DESC, id"))


# ---------------------------------------------------------------- the counter sheet's blocks
def register_blocks(con, d, u):
    """HTML rendered INTO the counter sheet (clinic_register.py calls this): the other-UPI box and,
    when a float is in use, the float count.  Both post to routes in this module and come back."""
    _ensure(con)
    return _other_upi_block(con, d) + _float_block(con, d)


def _other_upi_block(con, d):
    rows = other_upi_rows(con, d)
    dayrow = other_upi_day(con, d)
    reason = dayrow["reason"] if dayrow is not None else "just_one"
    phones = _remembered(con, "phone")
    apps = _remembered(con, "app")
    listed = []
    for r in rows:
        listed.append("<div style='display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;border:2px solid #8a9aa6;border-radius:9px;padding:10px;margin:8px 0;background:#fff'>"
                      "<span><b>&#8377; %s</b> &middot; %s &middot; %s%s</span>"
                      "<form method='post' action='/finance/clinic/money/%s/other-upi' class='inline noprint' style='margin:0'>"
                      "<input type='hidden' name='del' value='%d'><button type='submit' class='clear' style='padding:6px 12px;margin:0'>remove</button></form></div>"
                      % (_r(r["amount_p"]), _esc(r["app"] or "UPI"), _esc(r["phone"] or "—"),
                         (" &middot; bill " + _esc(r["bill_no"])) if r["bill_no"] else "", d, r["id"]))
    total = sum(r["amount_p"] for r in rows)
    table = ""
    if rows:
        table = ("%s<p class='verdict all_agree'>&#8377; %s to another UPI today &mdash; kept out of the bank match.</p>"
                 % ("".join(listed), _r(total)))
    radios = "".join(
        "<label class='radio' style='display:block;margin:4px 0'><input type='radio' name='reason' value='%s'%s> %s <span class='hint'>(%s)</span></label>"
        % (code, " checked" if code == reason else "", en, hi) for code, en, hi in OUTAGE_REASONS)
    return """
      <div class="card" id="otherupi"><h2>ICICI UPI not working? &rarr; Paid to another UPI</h2>
        <p class="mut">ICICI QR nahi chala aur payment kisi aur phone / app par aaya? Yahan likho. Sirf amount zaroori hai.</p>
        %s
        <form method="post" action="/finance/clinic/money/%s/other-upi">
        <table class="grid entry"><tbody>
          <tr><th class="sec">Amount <span class="hint">(zaroori)</span></th>
              <td><input name="amount" inputmode="numeric" pattern="[0-9]*" autocomplete="off" class="amt" placeholder="0"></td></tr>
          <tr><th class="sec">App</th><td><input name="app" list="upiapps" class="note" placeholder="PhonePe / Google Pay / Paytm" value="%s">
              <datalist id="upiapps">%s</datalist></td></tr>
          <tr><th class="sec">Whose phone</th><td><input name="phone" list="upiphones" class="note" placeholder="e.g. Shivani ka phone" value="%s">
              <datalist id="upiphones">%s</datalist></td></tr>
          <tr><th class="sec">Bill no. <span class="hint">(optional)</span></th><td><input name="bill_no" class="note" inputmode="numeric" placeholder="Docterz bill"></td></tr>
          <tr><th class="sec">Today, ICICI UPI was</th><td class="radios">%s</td></tr>
        </tbody></table>
        <button type="submit" class="save">%s</button>
        </form>
      </div>""" % (table, d, _esc(apps[0]) if apps else "", "".join("<option value='%s'>" % _esc(a) for a in list(dict.fromkeys(apps + list(UPI_APPS)))),
                   _esc(phones[0]) if phones else "", "".join("<option value='%s'>" % _esc(p) for p in phones), radios,
                   "+ add another" if rows else "Add this payment")


def _float_block(con, d):
    """S252: ZERO taps on a normal day.  The card states what to keep aside and what to hand over;
    "poora rakha" is already the answer.  Only when the full float could not be kept do three boxes
    open (?float=short).  Change requests are three buttons."""
    standing = float_standing_p(con, d)
    if not standing:
        return ""
    row = float_day(con, d)
    open_p = float_open_p(con, d)
    comp = float_composition(con)
    try:
        import clinic_register                                   # noqa: PLC0415
        coll = clinic_register.expected_cash_p(con, d)
    except Exception:                            # noqa: BLE001
        coll = None
    hand = None if coll is None else coll + open_p - standing      # the hand-over WHEN the full float is kept
    words = _comp_words(comp, FLOAT_KEEP) or _comp_words(comp)
    line = "<p class='verdict'>Kal ke liye alag rakho: <b>%s</b> (₹ %s).%s</p>" % (
        words, _r(standing),
        (" Baaki <b>₹ %s</b> hand over karo." % _r(hand)) if hand is not None and hand >= 0 else
        (" (Aaj ki cash se ₹ %s ka float poora nahi hoga — jitna rakh sako rakho, neeche batao.)" % _r(standing) if hand is not None else ""))
    if open_p < standing and row is None:
        line += "<p class='mut'>Aaj float ₹ %s se shuru hua (₹ %s kam tha). Poora ₹ %s rakh sako to rakho.</p>" % (_r(open_p), _r(standing - open_p), _r(standing))
    expand = request.args.get("float") == "short"
    status = ""
    if row is not None:
        short = standing - row["kept_p"]
        if short <= 0:
            status = "<p class='verdict all_agree'>✓ Poora ₹ %s alag rakha — %s, %s.</p>" % (_r(row["kept_p"]), _esc(row["by_whom"]), _esc(row["at"][11:16]))
        else:
            status = ("<p class='verdict waiting_bank'>₹ %s rakha — ₹ %s kam. Dr Manoj / Dr Bhawna ko pata chal gaya; agle din mil jayega.</p>"
                      % (_r(row["kept_p"]), _r(short)))
        if row["need"]:
            status += "<p class='mut'>Chutta maanga: <b>%s</b>%s</p>" % (_esc(row["need"]), " — ✓ mil gaya" if row["need_done"] else " — abhi milna baaki")
    if expand or (row is not None and standing - row["kept_p"] > 0):
        boxes = "".join("<tr><th class='sec'>₹ %d</th><td><input name='%s' value='%s' inputmode='numeric' pattern='[0-9]*' autocomplete='off' class='amt'></td>"
                        "<td class='mut'>poora: %d</td></tr>"
                        % (rs, k, _esc("" if row is None else (row[k] or "")), comp.get(k, 0)) for rs, k in FLOAT_KEEP)
        form = """<form method="post" action="/finance/clinic/money/%s/float"><input type="hidden" name="mode" value="short">
          <p class="mut">Kitne note rakh paaye? (sirf yeh teen)</p>
          <table class="grid entry"><thead><tr><th>Note</th><th>Kitne rakhe</th><th></th></tr></thead><tbody>%s</tbody></table>
          <button type="submit" class="save">Save — itna rakha</button></form>""" % (d, boxes)
    else:
        form = ("<p class='navrow'><a class='btn' href='/finance/clinic/register/%s?float=short#float'>Nahi — poora nahi rakh paaye</a></p>" % d
                if row is None else "")
    chg = "".join("<form method='post' action='/finance/clinic/money/%s/float' class='inline'><input type='hidden' name='mode' value='need'>"
                  "<input type='hidden' name='need' value='%s'><button type='submit' class='clear'>₹%d ke note chahiye</button></form>"
                  % (d, k, rs) for rs, k in FLOAT_KEEP)
    return """
      <div class="card" id="float"><h2>The float — reception ka chutta</h2>
        %s%s%s
        <p class="mut" style="margin-top:12px">Chutta kam pad raha hai? Ek tap:</p>%s
        <p class="hint">Yeh ₹ %s din ki kamai ka hissa nahi hai — sirf chutta. Kuch nahi karna agar poora rakha.</p>
      </div>""" % (line, status, form, chg, _r(standing))


@bp.route("/finance/clinic/money/<date>/other-upi", methods=["POST"])
def post_other_upi(date):
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return err
    if not _iso_ok(date):
        return _shell("Not a date", "<div class='card'><h2>Not a date.</h2></div>"), 400
    con = _db()
    _ensure(con)
    who, now = u.get("user", ""), _stamp()
    back = redirect("/finance/clinic/register/%s#otherupi" % date)
    if request.form.get("del"):
        try:
            rid = int(request.form.get("del"))
        except ValueError:
            return back
        before = con.execute("SELECT * FROM clinic_other_upi WHERE id=? AND business_date=?", (rid, date)).fetchone()
        if before is not None:
            con.execute("DELETE FROM clinic_other_upi WHERE id=?", (rid,))
            con.commit()
            _audit_safe(con, "clinic_other_upi", rid, "delete", dict(before), None, who)
        return back
    amt, e = _paise(request.form.get("amount"))
    if e or not amt:
        return _shell("Other UPI", "<div class='card'><div class='bad'><b>Nothing was saved.</b> The amount is the one thing that is "
                      "needed%s.</div><p class='navrow'><a class='btn' href='/finance/clinic/register/%s#otherupi'>back</a></p></div>"
                      % ((" — " + e) if e else "", date)), 400
    reason = request.form.get("reason") or "just_one"
    if reason not in [c for c, _e, _h in OUTAGE_REASONS]:
        reason = "just_one"
    cur = con.execute("INSERT INTO clinic_other_upi (business_date, amount_p, phone, app, bill_no, note, entered_by, entered_at) "
                      "VALUES (?,?,?,?,?,?,?,?)",
                      (date, amt, (request.form.get("phone") or "").strip()[:60], (request.form.get("app") or "").strip()[:40],
                       (request.form.get("bill_no") or "").strip()[:30], (request.form.get("note") or "").strip()[:200], who, now))
    if other_upi_day(con, date) is None:
        con.execute("INSERT INTO clinic_other_upi_day (business_date, reason, by_whom, at) VALUES (?,?,?,?)", (date, reason, who, now))
    else:
        con.execute("UPDATE clinic_other_upi_day SET reason=?, by_whom=?, at=? WHERE business_date=?", (reason, who, now, date))
    con.commit()
    _audit_safe(con, "clinic_other_upi", cur.lastrowid, "insert", None, dict(amount_p=amt, reason=reason), who)
    return back


@bp.route("/finance/clinic/money/<date>/float", methods=["POST"])
def post_float(date):
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return err
    if not _iso_ok(date):
        return _shell("Not a date", "<div class='card'><h2>Not a date.</h2></div>"), 400
    con = _db()
    _ensure(con)
    standing = float_standing_p(con, date)
    if not standing:
        return redirect("/finance/clinic/register/%s" % date)
    who, now = u.get("user", ""), _stamp()
    mode = request.form.get("mode") or "short"
    back = redirect("/finance/clinic/register/%s#float" % date)
    before = float_day(con, date)
    if mode == "need":                                        # a change request: one tap, no count needed
        key = request.form.get("need") or ""
        rs = next((r for r, k in FLOAT_NOTES if k == key), None)
        if rs is None:
            return back
        word = "₹%d ke note" % rs
        if before is None:
            comp = float_composition(con)
            con.execute("INSERT INTO clinic_float_day (business_date, %s, kept_p, open_p, standing_p, need, note, by_whom, at) "
                        "VALUES (?,%s,?,?,?,?,?,?,?)" % (",".join(FLOAT_KEYS), ",".join("?" * len(FLOAT_KEYS))),
                        [date] + [comp.get(k, 0) for k in FLOAT_KEYS] + [standing, float_open_p(con, date), standing, word, "", who, now])
        else:
            need = before["need"]
            if word not in need:
                need = (need + ", " + word) if need else word
            con.execute("UPDATE clinic_float_day SET need=?, need_done='', by_whom=?, at=? WHERE business_date=?", (need, who, now, date))
        con.commit()
        _audit_safe(con, "clinic_float_day", date, "need", None, dict(need=word), who)
        return back
    vals = {k: 0 for k in FLOAT_KEYS}
    comp = float_composition(con)
    if mode == "intact":
        vals.update({k: comp.get(k, 0) for k in FLOAT_KEYS})
    else:
        for _rs, k in FLOAT_KEEP:
            raw = (request.form.get(k) or "").strip()
            if raw == "":
                continue
            if not raw.isdigit():
                return _shell("The float", "<div class='card'><div class='bad'><b>Nothing was saved.</b> Whole numbers of notes only.</div>"
                              "<p class='navrow'><a class='btn' href='/finance/clinic/register/%s?float=short#float'>back</a></p></div>" % date), 400
            vals[k] = int(raw)
    kept = sum(rs * 100 * vals[k] for rs, k in FLOAT_NOTES)
    if kept > standing:
        kept = standing                                       # more than the float is the day's cash, not the float
    open_p = float_open_p(con, date)
    need = before["need"] if before is not None else ""
    if before is None:
        con.execute("INSERT INTO clinic_float_day (business_date, %s, kept_p, open_p, standing_p, need, note, by_whom, at) "
                    "VALUES (?,%s,?,?,?,?,?,?,?)" % (",".join(FLOAT_KEYS), ",".join("?" * len(FLOAT_KEYS))),
                    [date] + [vals[k] for k in FLOAT_KEYS] + [kept, open_p, standing, need, "", who, now])
    else:
        con.execute("UPDATE clinic_float_day SET %s, kept_p=?, open_p=?, standing_p=?, by_whom=?, at=? WHERE business_date=?"
                    % ",".join("%s=?" % k for k in FLOAT_KEYS),
                    [vals[k] for k in FLOAT_KEYS] + [kept, open_p, standing, who, now, date])
    try:
        exp = expected_handover_p(con, date)
        if exp is not None and _table(con, "clinic_drawer_day"):
            con.execute("UPDATE clinic_drawer_day SET expected_p=? WHERE business_date=?", (exp, date))
    except Exception:                            # noqa: BLE001
        pass
    con.commit()
    _audit_safe(con, "clinic_float_day", date, "update" if before is not None else "insert",
                dict(before) if before is not None else None, dict(kept_p=kept, mode=mode), who)
    return back


# ---------------------------------------------------------------- THE STAFF CARD
def _is_named_checker(con, u):
    return (u.get("user") or "").strip().lower() == checker_name(con)


def _is_clinic_checker(u):
    return "checker" in (u.get("roles") or [])


@bp.route("/finance/clinic/match")
def match_index():
    """Land on the day that needs the person: yesterday, or the newest day not yet closed."""
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Morning match", _denied())
    con = _db()
    _ensure(con)
    if _is_clinic_checker(u) and not _is_named_checker(con, u):
        return redirect("/finance/clinic/money")
    y = (_now().date() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/match/%s" % y)


@bp.route("/finance/clinic/match/<date>", methods=["GET", "POST"])
def match_card(date):
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Morning match", _denied())
    if not _iso_ok(date):
        return _shell("Morning match", "<div class='card'><h2>Not a date.</h2></div>")
    con = _db()
    _ensure(con)
    who, now = u.get("user", ""), _stamp()
    named = _is_named_checker(con, u)
    msg = ""
    if request.method == "POST":
        msg = _match_post(con, date, u, named, who, now)
    m = match_day(con, date)
    rows = sync_flags(con, date, m)
    st = day_state(con, date)
    return _shell("Morning match — %s" % _human(date), _match_html(con, date, u, named, m, rows, st, msg))


def _match_post(con, date, u, named, who, now):
    f = request.form
    act = f.get("act") or ""
    st = day_state(con, date)
    if act == "answer":                                  # maker answers one flag
        try:
            fid = int(f.get("flag"))
        except (TypeError, ValueError):
            return "<div class='bad'>Which flag?</div>"
        r = con.execute("SELECT * FROM clinic_money_flag WHERE id=? AND business_date=?", (fid, date)).fetchone()
        if r is None or r["status"] in ("reconciled", "cleared"):
            return "<div class='bad'>That flag is no longer open.</div>"
        text = (f.get("explanation") or "").strip()[:400]
        cannot = f.get("cannot") == "1"
        if not cannot and not text:
            return "<div class='bad'><b>Nothing was saved.</b> Write what happened, or press <i>Cannot explain</i>.</div>"
        con.execute("UPDATE clinic_money_flag SET status=?, explanation=?, explained_by=?, explained_at=? WHERE id=?",
                    ("cannot" if cannot else "explained", text, who, now, fid))
        con.commit()
        _audit_safe(con, "clinic_money_flag", fid, "answer", None, dict(status="cannot" if cannot else "explained", by=who), who)
        return "<div class='ok'>Saved.</div>"
    if act == "verdict":                                 # the checker's word on one flag
        if not named:
            return "<div class='bad'>Only the checker (%s) decides this.</div>" % _esc(checker_name(con))
        try:
            fid = int(f.get("flag"))
        except (TypeError, ValueError):
            return "<div class='bad'>Which flag?</div>"
        r = con.execute("SELECT * FROM clinic_money_flag WHERE id=? AND business_date=?", (fid, date)).fetchone()
        if r is None or r["status"] in ("reconciled", "cleared"):
            return "<div class='bad'>That flag is no longer open.</div>"
        word = f.get("word") or ""
        if word == "agree":
            if r["status"] == "explained" and not r["owner"]:
                new = "reconciled"
            else:
                new = "to_owner"                        # agreed it cannot be explained, or an owner-level flag
            con.execute("UPDATE clinic_money_flag SET status=?, checker_word='agree', checker_by=?, checker_at=?, "
                        "reconciled_by=CASE WHEN ?='reconciled' THEN ? ELSE reconciled_by END, "
                        "reconciled_at=CASE WHEN ?='reconciled' THEN ? ELSE reconciled_at END WHERE id=?",
                        (new, who, now, new, who, new, now, fid))
        elif word == "disagree":
            con.execute("UPDATE clinic_money_flag SET status='to_owner', checker_word='disagree', checker_by=?, checker_at=? WHERE id=?",
                        (who, now, fid))
        else:
            return "<div class='bad'>Agree or disagree.</div>"
        con.commit()
        _audit_safe(con, "clinic_money_flag", fid, "verdict", None, dict(word=word, by=who), who)
        return "<div class='ok'>Saved.</div>"
    if act == "pass1":
        if st is not None and st["status"] != "open":
            return "<div class='bad'>The first pass is already done for this day.</div>"
        m = match_day(con, date)
        rows = sync_flags(con, date, m)
        if any(r["status"] == "open" and not r["owner"] for r in rows):
            return "<div class='bad'><b>Not yet.</b> Answer every flag first — a line each, or <i>Cannot explain</i>.</div>"
        if named:                                        # the checker made the first pass: the day closes on it
            for r in rows:
                if r["status"] == "cannot" or (r["owner"] and r["status"] in ("open", "explained", "cannot")):
                    con.execute("UPDATE clinic_money_flag SET status='to_owner', checker_word='one pass', checker_by=?, checker_at=? WHERE id=?", (who, now, r["id"]))
                elif r["status"] == "explained":
                    con.execute("UPDATE clinic_money_flag SET status='reconciled', checker_word='one pass', checker_by=?, checker_at=?, "
                                "reconciled_by=?, reconciled_at=? WHERE id=?", (who, now, who, now, r["id"]))
            con.execute("INSERT OR REPLACE INTO clinic_money_day (business_date, status, maker, maker_at, checker, checker_at, one_pass, closed_at) "
                        "VALUES (?,?,?,?,?,?,1,?)", (date, "closed", who, now, who, now, now))
            con.commit()
            _audit_safe(con, "clinic_money_day", date, "close_one_pass", None, dict(by=who), who)
            return "<div class='ok'><b>Day closed on one pass — %s.</b> Anything you could not explain has gone to Dr Manoj.</div>" % _esc(who)
        con.execute("INSERT OR REPLACE INTO clinic_money_day (business_date, status, maker, maker_at, checker, checker_at, one_pass, closed_at) "
                    "VALUES (?,?,?,?,'','',0,'')", (date, "maker_done", who, now))
        con.commit()
        _audit_safe(con, "clinic_money_day", date, "pass1", None, dict(by=who), who)
        return "<div class='ok'><b>First pass done.</b> %s will check it.</div>" % _esc(checker_name(con).capitalize())
    if act == "pass2":
        if not named:
            return "<div class='bad'>Only the checker (%s) closes the day.</div>" % _esc(checker_name(con))
        if st is None or st["status"] != "maker_done":
            return "<div class='bad'>The first pass has not been done yet — do it yourself and the day closes on one pass.</div>"
        m = match_day(con, date)
        rows = sync_flags(con, date, m)
        if any(r["status"] in ("open", "explained", "cannot") and not r["owner"] for r in rows):
            return "<div class='bad'><b>Not yet.</b> Give your word on every flag first.</div>"
        for r in rows:
            if r["owner"] and r["status"] in ("open", "explained", "cannot"):
                con.execute("UPDATE clinic_money_flag SET status='to_owner', checker_by=?, checker_at=? WHERE id=?", (who, now, r["id"]))
        con.execute("UPDATE clinic_money_day SET status='closed', checker=?, checker_at=?, closed_at=? WHERE business_date=?",
                    (who, now, now, date))
        con.commit()
        _audit_safe(con, "clinic_money_day", date, "pass2", None, dict(by=who), who)
        return "<div class='ok'><b>Day closed.</b> Two passes: %s, then %s.</div>" % (_esc(st["maker"]), _esc(who))
    if act == "reopen":
        if not named:
            return "<div class='bad'>Only the checker reopens a day.</div>"
        con.execute("UPDATE clinic_money_day SET status='open', maker='', maker_at='', checker='', checker_at='', one_pass=0, closed_at='' "
                    "WHERE business_date=?", (date,))
        con.commit()
        return "<div class='ok'>Reopened. Both passes again.</div>"
    return "<div class='bad'>Nothing happened.</div>"


_STATUS_WORD = {"open": "needs an answer", "explained": "explained — waiting for the checker",
                "cannot": "could not be explained — waiting for the checker", "to_owner": "with Dr Manoj",
                "reconciled": "reconciled", "cleared": "cleared by the data"}


def _match_html(con, date, u, named, m, rows, st, msg):
    """S253: the answer first, the working folded.  The owner, 13-Sep: 'very taxing and cumbersome
    ... to understand your mathematics' -- so one sentence, the flags in plain words with their
    buttons, and everything else behind three collapsed lines."""
    d = dt.date.fromisoformat(date)
    prev, nxt = (d - dt.timedelta(days=1)).isoformat(), (d + dt.timedelta(days=1)).isoformat()
    status = st["status"] if st is not None else "open"
    who = u.get("user", "")
    verdict_cls = {"nothing_to_do": "all_agree", "flags": "all_differ", "not_filled": "not_entered", "waiting_docterz": "waiting_bank"}.get(m["verdict"], "")
    head = ["""
      <div class="card"><h2>Morning match — %s</h2>
        %s
        <p class="verdict %s" style="font-size:21px">%s</p>
        <p class="mut">%s</p>
        <p class="navrow noprint"><a class="btn" href="/finance/clinic/match/%s">&lsaquo; %s</a>
           <a class="btn" href="/finance/clinic/match/%s">%s &rsaquo;</a></p>
      </div>""" % (_human(date), msg, verdict_cls, _esc(" ".join(m["lines"])), _day_line(st, con),
                   prev, _human(prev), nxt, _human(nxt))]
    # flags -- the only thing that asks for a person
    live = [r for r in rows if r["status"] != "cleared"]
    if live:
        head.append("<div class='card'><h2>%s</h2>%s</div>" % (
            "Needs a person" if len(live) == 1 else "Needs a person (%d)" % len(live),
            "".join(_flag_html(r, named, status, who) for r in live)))
    # the pass buttons
    head.append(_pass_html(con, date, named, status, st, live, who))
    # the working, folded
    if m["explained"]:
        head.append("<details class='card'><summary>Explained (%d) — nothing to do</summary><ul class='lines'>%s</ul></details>"
                    % (len(m["explained"]), "".join("<li>%s</li>" % _esc(e["text"]) for e in m["explained"])))
    waiting = [n for n in m["notes"] if "not in the bank yet" in n]
    other_notes = [n for n in m["notes"] if n not in waiting]
    if m.get("p1"):
        if m["bank_known"] and not m.get("expected_bank_p") and not m["bank_p"]:
            bank_line = "No online payments this day."
        elif m["bank_known"]:
            bank_line = "Bank: ₹%s received of ₹%s online%s." % (
                _r(m["bank_p"]), _r(m.get("expected_bank_p")),
                ("; ₹%s still on its way (%d payment%s)" % (_r(sum(o["amount_p"] for o in m["p4"]["ours_only"])), len(m["p4"]["ours_only"]),
                                                            "s" if len(m["p4"]["ours_only"]) != 1 else "")) if m["p4"]["ours_only"] else "")
        else:
            bank_line = "Bank: the file for this day has not arrived yet (%s)." % _esc(m["bank_state"].replace("_", " "))
        if waiting or (m["bank_known"] and m["p4"]["ours_only"]):
            head.append("<details class='card'><summary>Waiting for the bank (%d)</summary><p class='mut'>%s</p><ul class='lines mut'>%s</ul>"
                        "<p class='mut'>Money still on its way is not a flag; it becomes one only if it has not arrived after two banking days.</p></details>"
                        % (len(waiting), _esc(bank_line), "".join("<li>%s</li>" % _esc(n) for n in waiting)))
        else:
            head.append("<p class='mut' style='margin:6px 2px'>%s</p>" % _esc(bank_line))
        p1, p2, p3 = m["p1"], m["p2"], m["p3"]
        head.append("""<details class="card"><summary>Show the numbers</summary><table class="grid nums"><thead><tr><th></th><th class="r">Counter</th>
          <th class="r">Docterz</th><th class="r">Diff</th></tr></thead><tbody>
          <tr><th class="sec">Day's money<br><span class="hint">physio out</span></th><td class="r">%s</td><td class="r">%s</td><td class="r"><b>%s</b></td></tr>
          %s%s
          <tr><th class="sec">Bank expects</th><td class="r">—</td><td class="r">%s</td><td class="r"></td></tr>
          <tr><th class="sec">Bank has</th><td class="r">—</td><td class="r">%s</td><td class="r"><b>%s</b></td></tr>
          </tbody></table><p class="mut">Bank expects = Docterz online − other UPI (₹%s). Bank: %s%s.</p>%s
          <p class="navrow noprint"><a class="btn" href="/finance/clinic/register/%s">the counter sheet</a>
           <a class="btn" href="/finance/clinic/day/%s">Docterz entries</a>
           <a class="btn" href="/finance/clinic/day/%s/mpr">bank MPR</a></p></details>""" % (
            _r(p1["counter_p"]), _r(p1["docterz_p"]), _diff(p1["diff_p"]),
            "".join("<tr><th class='sec'>%s</th><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td></tr>"
                    % (_HEAD_SHORT[h], _r(a), _r(b), _diff(x)) for h, a, b, x in p2),
            "".join("<tr><th class='sec'>%s</th><td class='r'>%s</td><td class='r'>%s</td><td class='r'>%s</td></tr>"
                    % (_TENDER[t].capitalize(), _r(a), _r(b), _diff(x)) for t, a, b, x in p3),
            _r(m.get("expected_bank_p")),
            _r(m["bank_p"]) if m["bank_known"] else "not yet", _diff(m.get("bank_diff_p", 0)) if m["bank_known"] else "",
            _r(m["other_upi_p"]), _esc(m["bank_state"].replace("_", " ")),
            (" · %d paired, %d bank-only, %d ours-only" % (len(m["p4"]["pairs"]), len(m["p4"]["bank_only"]), len(m["p4"]["ours_only"]))) if m.get("p4") and m["bank_known"] else "",
            ("<ul class='lines mut'>%s</ul>" % "".join("<li>%s</li>" % _esc(n) for n in other_notes)) if other_notes else "",
            date, date, date))
    else:
        head.append("<p class='navrow noprint'><a class='btn' href='/finance/clinic/register/%s'>the counter sheet</a>"
                    "<a class='btn' href='/finance/clinic/day/%s'>Docterz entries</a></p>" % (date, date))
    return "".join(head)


def _diff(x):
    if not x:
        return "none"
    return "%s₹ %s" % ("+" if x > 0 else "−", _r(abs(x)))


def _day_line(st, con):
    if st is None or st["status"] == "open":
        return "First pass: reception (or %s when reception is away). Then %s checks." % (checker_name(con).capitalize(), checker_name(con).capitalize())
    if st["status"] == "maker_done":
        return "First pass done by %s at %s. Waiting for %s." % (_esc(st["maker"]), _esc(st["maker_at"]), checker_name(con).capitalize())
    if st["one_pass"]:
        return "Closed — one pass only, %s at %s." % (_esc(st["maker"]), _esc(st["closed_at"]))
    return "Closed — %s, then %s at %s." % (_esc(st["maker"]), _esc(st["checker"]), _esc(st["closed_at"]))


def _flag_html(r, named, day_status, who):
    cls = {"open": "f_open", "explained": "f_expl", "cannot": "f_cannot", "to_owner": "f_owner", "reconciled": "f_done"}.get(r["status"], "")
    out = ["<div class='flag %s'><p class='ftext'><b>%s</b>%s</p>" % (cls, _esc(r["text"]), (" <span class='pill'>Dr Manoj's</span>" if r["owner"] else ""))]
    if r["code"] == "total_diff" and r["status"] == "open":
        out.append("<p class='hint'>Counter sheet mein ₹%s %s hai — kya hua tha, ek line likho, ya <i>Cannot explain</i> dabao.</p>"
                   % (_r(abs(r["amount_p"])), "zyada" if r["amount_p"] > 0 else "kam"))
    out.append("<p class='mut'>%s%s%s</p>" % (
        _STATUS_WORD.get(r["status"], r["status"]),
        (" · %s: “%s”" % (_esc(r["explained_by"]), _esc(r["explanation"]))) if r["explanation"] else "",
        (" · checker %s: %s" % (_esc(r["checker_by"]), _esc(r["checker_word"]))) if r["checker_word"] else ""))
    if r["status"] == "open" and day_status == "open" and r["code"] != "not_filled":
        out.append("""<form method="post" class="answer"><input type="hidden" name="act" value="answer"><input type="hidden" name="flag" value="%d">
          <input name="explanation" class="note" maxlength="400" placeholder="What happened? (kya hua tha)">
          <button type="submit" class="save">Explained</button>
          <button type="submit" name="cannot" value="1" class="clear">Cannot explain</button></form>""" % r["id"])
    elif r["status"] == "open" and r["code"] == "not_filled":
        out.append("<p class='navrow'><a class='btn' href='/finance/clinic/register/%s'>fill the counter sheet</a></p>" % r["business_date"])
    if named and r["status"] in ("explained", "cannot") and day_status == "maker_done":
        out.append("""<form method="post" class="answer"><input type="hidden" name="act" value="verdict"><input type="hidden" name="flag" value="%d">
          <button type="submit" name="word" value="agree" class="save">Agree%s</button>
          <button type="submit" name="word" value="disagree" class="clear">Disagree — to Dr Manoj</button></form>"""
                   % (r["id"], " — reconciled" if (r["status"] == "explained" and not r["owner"]) else " — to Dr Manoj"))
    out.append("</div>")
    return "".join(out)


def _pass_html(con, date, named, status, st, live, who):
    open_left = [r for r in live if r["status"] == "open" and not r["owner"]]
    if status == "open":
        if named:
            label = "Close the day — one pass only (%s)" % who
            note = "Reception has not made the first pass. Yours closes the day and is marked <b>one pass only</b>."
        else:
            label = "First pass done"
            note = "Answer every flag, then press this. %s checks after you." % checker_name(con).capitalize()
        dis = " disabled" if open_left else ""
        return ("<div class='card'><form method='post'><input type='hidden' name='act' value='pass1'>"
                "<button type='submit' class='save'%s>%s</button></form><p class='mut'>%s%s</p></div>"
                % (dis, label, note, (" <b>%d flag%s still unanswered.</b>" % (len(open_left), "s" if len(open_left) > 1 else "")) if open_left else ""))
    if status == "maker_done":
        if named:
            waiting = [r for r in live if r["status"] in ("explained", "cannot") and not r["owner"]]
            dis = " disabled" if waiting else ""
            return ("<div class='card'><form method='post'><input type='hidden' name='act' value='pass2'>"
                    "<button type='submit' class='save'%s>Close the day — checked</button></form>"
                    "<p class='mut'>Give your word on every flag first.%s</p></div>"
                    % (dis, (" <b>%d waiting.</b>" % len(waiting)) if waiting else ""))
        return "<div class='card'><p class='mut'>First pass done. Waiting for %s.</p></div>" % checker_name(con).capitalize()
    reopen = ("<form method='post' class='inline'><input type='hidden' name='act' value='reopen'>"
              "<button type='submit' class='clear'>Reopen this day</button></form>") if named else ""
    return "<div class='card'><p class='verdict all_agree'>This day is closed.</p>%s</div>" % reopen


# ---------------------------------------------------------------- THE OWNER'S LINE
@bp.route("/finance/clinic/money", methods=["GET", "POST"])
def owner_page():
    u, err = _require("checker", unit=_unit)
    if err:
        return _shell("Clinic money", _denied())
    con = _db()
    _ensure(con)
    if _is_named_checker(con, u):                             # S252: the morning-match checker works the staff card, not this page
        return _shell("Clinic money", _denied())
    who, now = u.get("user", ""), _stamp()
    msg = ""
    if request.method == "POST":
        msg = _owner_post(con, u, who, now)
    ym = (request.args.get("m") or _now().strftime("%Y-%m"))[:7]
    return _shell("Clinic money — %s" % ym, _owner_html(con, ym, msg, u))


def _owner_post(con, u, who, now):
    f = request.form
    act = f.get("act") or ""
    if act == "reconcile":
        try:
            fid = int(f.get("flag"))
        except (TypeError, ValueError):
            return "<div class='bad'>Which flag?</div>"
        r = con.execute("SELECT * FROM clinic_money_flag WHERE id=?", (fid,)).fetchone()
        if r is None:
            return "<div class='bad'>No such flag.</div>"
        con.execute("UPDATE clinic_money_flag SET status='reconciled', reconciled_by=?, reconciled_at=?, owner_note=? WHERE id=?",
                    (who, now, (f.get("note") or "").strip()[:300], fid))
        con.commit()
        _audit_safe(con, "clinic_money_flag", fid, "owner_reconciled", None, dict(by=who), who)
        return "<div class='ok'>Reconciled.</div>"
    if act == "settle_upi":
        try:
            rid = int(f.get("row"))
        except (TypeError, ValueError):
            return "<div class='bad'>Which payment?</div>"
        con.execute("UPDATE clinic_other_upi SET settled_at=?, settled_by=?, settled_to=? WHERE id=? AND settled_at=''",
                    (now, who, (f.get("to") or who).strip()[:40], rid))
        con.commit()
        return "<div class='ok'>Marked settled.</div>"
    if act == "float_given":                                  # S252: one tap -- the top-up with the notes already worked out
        owed = float_owed(con)
        if owed is None:
            return "<div class='ok'>The float is already intact — nothing to give.</div>"
        vals = {k: owed["notes"].get(k, 0) for k in FLOAT_KEYS}
        amt = sum(rs * 100 * vals[k] for rs, k in FLOAT_NOTES) + owed["remainder_p"]
        cur = con.execute("INSERT INTO clinic_float_event (business_date, kind, amount_p, %s, given_to, note, by_whom, at) VALUES (?,?,?,%s,?,?,?,?)"
                          % (",".join(FLOAT_KEYS), ",".join("?" * len(FLOAT_KEYS))),
                          [_now().date().isoformat(), "topup", amt] + [vals[k] for k in FLOAT_KEYS] + ["reception", "given (one tap)", who, now])
        con.commit()
        _audit_safe(con, "clinic_float_event", cur.lastrowid, "topup", None, dict(amount_p=amt), who)
        return "<div class='ok'>Recorded: ₹%s given to reception (%s). The float is whole again.</div>" % (_r(amt), _comp_words(owed["notes"]) or "notes")
    if act == "need_given":
        ask = float_change_asked(con)
        if ask is None:
            return "<div class='ok'>No change request is open.</div>"
        con.execute("UPDATE clinic_float_day SET need_done=? WHERE business_date=?", ("%s %s" % (who, now), ask["business_date"]))
        con.commit()
        _audit_safe(con, "clinic_float_day", ask["business_date"], "need_given", None, dict(need=ask["need"]), who)
        return "<div class='ok'>Change given — %s.</div>" % _esc(ask["need"])
    if act == "float":
        kind = f.get("kind") or "issue"
        if kind not in ("issue", "topup", "return"):
            return "<div class='bad'>issue, topup or return.</div>"
        vals, bad = {}, []
        for _rs, k in FLOAT_NOTES:
            raw = (f.get(k) or "").strip()
            if raw == "":
                vals[k] = 0
            elif not raw.isdigit():
                bad.append(k)
            else:
                vals[k] = int(raw)
        if bad:
            return "<div class='bad'>Whole numbers of notes only.</div>"
        amt = sum(rs * 100 * vals[k] for rs, k in FLOAT_NOTES)
        if not amt:
            return "<div class='bad'>Nothing was recorded — no notes given.</div>"
        d = (f.get("date") or _now().date().isoformat())[:10]
        if not _iso_ok(d):
            return "<div class='bad'>Not a date.</div>"
        cur = con.execute("INSERT INTO clinic_float_event (business_date, kind, amount_p, %s, given_to, note, by_whom, at) VALUES (?,?,?,%s,?,?,?,?)"
                          % (",".join(FLOAT_KEYS), ",".join("?" * len(FLOAT_KEYS))),
                          [d, kind, amt] + [vals[k] for k in FLOAT_KEYS] + [(f.get("given_to") or "reception").strip()[:40],
                                                                            (f.get("note") or "").strip()[:200], who, now])
        con.commit()
        _audit_safe(con, "clinic_float_event", cur.lastrowid, kind, None, dict(amount_p=amt), who)
        return "<div class='ok'>Float %s: ₹%s recorded. It is not revenue and not an expense.</div>" % (kind, _r(amt))
    return "<div class='bad'>Nothing happened.</div>"


def _float_card(con):
    """S252: the float in ONE line, and the one tap that answers it."""
    standing = float_standing_p(con)
    if not standing:
        return "<div class='card'><h2>The float</h2><p class='mut'>Not issued yet — see the last card on this page.</p></div>"
    owed = float_owed(con)
    ask = float_change_asked(con)
    cls = "all_agree" if (owed is None and ask is None) else "waiting_bank"
    taps = ""
    if owed is not None:
        taps += ("<form method='post' class='inline'><input type='hidden' name='act' value='float_given'>"
                 "<button type='submit' class='save'>Given — %s%s</button></form>"
                 % (_esc(_comp_words(owed["notes"]) or "the shortfall"), (" + ₹%s" % _r(owed["remainder_p"])) if owed["remainder_p"] else ""))
    if ask is not None:
        taps += ("<form method='post' class='inline'><input type='hidden' name='act' value='need_given'>"
                 "<button type='submit' class='save'>Change given — %s</button></form>" % _esc(ask["need"]))
    return "<div class='card'><h2>The float</h2><p class='verdict %s'>%s</p>%s</div>" % (cls, _esc(float_line(con)), taps)


def _owner_html(con, ym, msg, u):
    first = ym + "-01"
    y, mth = int(ym[:4]), int(ym[5:7])
    last = (dt.date(y + (mth == 12), (mth % 12) + 1, 1) - dt.timedelta(days=1)).isoformat()
    prev = (dt.date(y, mth, 1) - dt.timedelta(days=1)).strftime("%Y-%m")
    nxt = (dt.date.fromisoformat(last) + dt.timedelta(days=1)).strftime("%Y-%m")
    q = owner_queue(con)
    out = [_float_card(con)]
    out.append("""<div class="card"><h2>Clinic money — what needs you</h2>%s
        <p class="mut">Exactly four things reach this page: a flag staff could not explain · a flag where maker and checker
        disagree · money that never lands · a counter sheet still unfilled after the day has passed. Everything else is
        handled on the staff card and stays there until reconciled.</p>""" % msg)
    if not q:
        out.append("<p class='verdict all_agree'>✓ Nothing needs you.</p>")
    else:
        for r in q:
            why = {"disagree": "maker and checker disagree", "agree": "checker agrees it cannot be explained",
                   "one pass": "one pass only"}.get(r["checker_word"], "")
            if r["code"] == "not_in_bank":
                why = "money that never landed"
            if r["code"] == "not_filled":
                why = "sheet unfilled after the day"
            out.append("""<div class="flag f_owner"><p class="ftext"><b>%s</b> — %s</p><p class="mut">%s%s%s</p>
              <form method="post" class="answer"><input type="hidden" name="act" value="reconcile"><input type="hidden" name="flag" value="%d">
              <input name="note" class="note" maxlength="300" placeholder="your note (optional)">
              <button type="submit" class="save">Reconciled</button>
              <a class="btn" href="/finance/clinic/match/%s">open the day</a></form></div>""" % (
                _human(r["business_date"]), _esc(r["text"]), _esc(why),
                (" · %s: “%s”" % (_esc(r["explained_by"]), _esc(r["explanation"]))) if r["explanation"] else "",
                (" · checker %s" % _esc(r["checker_by"])) if r["checker_by"] else "", r["id"], r["business_date"]))
    out.append("</div>")

    # ---- the month: every channel without an independent record, totalled ----
    days = list(con.execute("SELECT * FROM clinic_money_day WHERE business_date BETWEEN ? AND ? ORDER BY business_date", (first, last)))
    one_pass = [x["business_date"] for x in days if x["one_pass"]]
    closed = [x for x in days if x["status"] == "closed"]
    oth = list(con.execute("SELECT * FROM clinic_other_upi WHERE business_date BETWEEN ? AND ? ORDER BY business_date, id", (first, last)))
    oth_total = sum(r["amount_p"] for r in oth)
    oth_unsettled = [r for r in oth if not r["settled_at"]]
    phy = list(con.execute("SELECT * FROM clinic_physio_day WHERE business_date BETWEEN ? AND ? ORDER BY business_date", (first, last)))
    phy_cash, phy_upi = sum(r["cash_p"] for r in phy), sum(r["upi_p"] for r in phy)
    phy_unrec = [r for r in phy if (r["cash_p"] or r["upi_p"]) and not r["received_at"]]
    fl = list(con.execute("SELECT * FROM clinic_float_day WHERE business_date BETWEEN ? AND ? ORDER BY business_date", (first, last)))
    fl_short = [r for r in fl if r["standing_p"] - r["kept_p"] > 0]
    fl_need = [r for r in fl if r["need"]]
    standing = float_standing_p(con)
    out.append("""<div class="card"><h2>%s %d — the channels that have no independent record</h2>
      <p class="navrow noprint"><a class="btn" href="?m=%s">&lsaquo; %s</a><a class="btn" href="?m=%s">%s &rsaquo;</a>
         <a class="btn" href="/finance/physio">physiotherapy table</a><a class="btn" href="/finance/clinic/day?m=%s">Docterz month</a></p>
      <table class="grid"><tbody>
      <tr><th class="sec">Other UPI (personal phones)</th><td class="r">₹ %s</td><td>%d payment%s · %s</td></tr>
      <tr><th class="sec">Physiotherapy</th><td class="r">₹ %s</td><td>cash ₹ %s + UPI ₹ %s · %s</td></tr>
      <tr><th class="sec">The float</th><td class="r">₹ %s</td><td>%s</td></tr>
      <tr><th class="sec">Morning passes</th><td class="r">%d</td><td>days closed%s</td></tr>
      </tbody></table></div>""" % (
        dt.date(y, mth, 1).strftime("%B"), y, prev, prev, nxt, nxt, ym,
        _r(oth_total), len(oth), "s" if len(oth) != 1 else "",
        ("<b>₹ %s not yet settled</b>" % _r(sum(r["amount_p"] for r in oth_unsettled))) if oth_unsettled else "all settled",
        _r(phy_cash + phy_upi), _r(phy_cash), _r(phy_upi),
        ("<b>%d day%s not yet marked received</b>" % (len(phy_unrec), "s" if len(phy_unrec) != 1 else "")) if phy_unrec else "all received",
        _r(standing),
        ("not issued yet — issue it below" if not standing else
         ("short on %d day%s%s%s" % (len(fl_short), "s" if len(fl_short) != 1 else "",
                                    (" (₹ %s made up)" % _r(sum(r["standing_p"] - r["kept_p"] for r in fl_short))) if fl_short else "",
                                    ("; change asked on %d day%s" % (len(fl_need), "s" if len(fl_need) != 1 else "")) if fl_need else ""))),
        len(closed), (" · one pass only on %s" % ", ".join(_human(x) for x in one_pass)) if one_pass else ""))
    if oth_unsettled:
        rows = "".join("<tr><td>%s</td><td class='r'>₹ %s</td><td>%s</td><td>%s</td><td class='noprint'><form method='post' class='inline'>"
                       "<input type='hidden' name='act' value='settle_upi'><input type='hidden' name='row' value='%d'>"
                       "<button type='submit' class='save'>Settled — passed on</button></form></td></tr>"
                       % (_human(r["business_date"]), _r(r["amount_p"]), _esc(r["app"] or "—"), _esc(r["phone"] or "—"), r["id"]) for r in oth_unsettled)
        out.append("<div class='card'><h2>Other UPI — not yet passed on</h2><table class='grid'><thead><tr><th>Day</th><th class='r'>Amount</th>"
                   "<th>App</th><th>Phone</th><th></th></tr></thead><tbody>%s</tbody></table></div>" % rows)
    # the float: a fresh issue or taking it back -- rare, folded away (S252)
    cells = "".join("<tr><th class='sec'>₹ %d</th><td><input name='%s' inputmode='numeric' pattern='[0-9]*' class='amt' value='%s'></td></tr>"
                    % (rs, k, FLOAT_DEFAULT.get(k, "") if not standing else "") for rs, k in FLOAT_NOTES)
    out.append("""<details class="card"><summary>%s</summary>
      <p class="mut">Clinic cash placed at the counter and still clinic cash: not revenue, not an expense, never part of any
      collection. Day to day it is handled by the one line at the top of this page.</p>
      <form method="post"><input type="hidden" name="act" value="float">
      <table class="grid entry"><tbody>%s
        <tr><th class="sec">This is</th><td><select name="kind" class="note"><option value="issue">issued (first time / raising it)</option>
            <option value="return">taken back</option></select></td></tr>
        <tr><th class="sec">Given to</th><td><input name="given_to" class="note" value="reception" maxlength="40"></td></tr>
        <tr><th class="sec">Date</th><td><input name="date" class="note" value="%s" maxlength="10"></td></tr>
      </tbody></table><button type="submit" class="save">Record</button></form></details>""" % (
        ("Issue the float (not issued yet)" if not standing else "Raise or take back the float (rare)"), cells, _now().date().isoformat()))
    return "".join(out)


# ---------------------------------------------------------------- PHYSIOTHERAPY
@bp.route("/finance/physio")
def physio_page():
    u, err = _require("viewer", "maker", "checker", unit=PHYSIO_UNIT)
    if err:
        return _shell("Physiotherapy", _denied_physio())
    con = _db()
    _ensure(con)
    hindi = (u.get("roles") or []) == ["viewer"]
    checker = "checker" in (u.get("roles") or [])
    return _shell("Physiotherapy", _physio_html(con, hindi, checker, u, request.args.get("msg") or ""))


@bp.route("/finance/physio/received/<date>", methods=["POST"])
def physio_received(date):
    u, err = _require("checker", unit=PHYSIO_UNIT)
    if err:
        return err
    if not _iso_ok(date):
        return redirect("/finance/physio")
    con = _db()
    _ensure(con)
    who, now = u.get("user", ""), _stamp()
    r = physio_row(con, date)
    if r is not None and not r["received_at"]:
        con.execute("UPDATE clinic_physio_day SET received_by=?, received_at=? WHERE business_date=?", (who, now, date))
        con.commit()
        _audit_safe(con, "clinic_physio_day", date, "received", None, dict(by=who), who)
    return redirect("/finance/physio?msg=received")


def _physio_html(con, hindi, checker, u, msg):
    months = physio_months(con)
    cur = _now().strftime("%Y-%m")
    L = (dict(title="Physiotherapy ka hisaab", date="Tareekh", cash="Cash", upi="UPI", total="Kul", to="Kisko diya", rec="Mila",
              month="Mahina", year="Saal", none="Abhi koi entry nahi.", got="mil gaya", notyet="abhi nahi",
              note="Reception yeh table bharti hai. Aap sirf dekh sakte hain.")
         if hindi else
         dict(title="Physiotherapy — the revenue table", date="Day", cash="Cash", upi="UPI", total="Total", to="Handed to", rec="Received",
              month="Month", year="Year", none="No entries yet.", got="received", notyet="not yet",
              note="Reception writes this table from the counter sheet. Physiotherapy is out of the bank match — it has no "
                   "software and no MPR — so this table is its record."))
    out = ["<div class='card'><h2>%s</h2><p class='mut'>%s</p>%s</div>" % (
        L["title"], L["note"], "<div class='ok'>✓</div>" if msg else "")]
    if not months:
        out.append("<div class='card'><p>%s</p></div>" % L["none"])
    years = {}
    for ym, rows in months:
        tc, tu = sum(r["cash_p"] for r in rows), sum(r["upi_p"] for r in rows)
        years[ym[:4]] = years.get(ym[:4], 0) + tc + tu
        body = []
        for r in rows:
            rec = ("✓ %s %s" % (L["got"], _esc(r["received_by"]))) if r["received_at"] else L["notyet"]
            if checker and not r["received_at"] and (r["cash_p"] or r["upi_p"]):
                rec = ("<form method='post' action='/finance/physio/received/%s' class='inline'>"
                       "<button type='submit' class='save'>Received</button></form>" % r["business_date"])
            body.append("<tr><td class='d'>%s</td><td class='r'>%s</td><td class='r'>%s</td><td class='r'><b>%s</b></td><td>%s</td><td>%s</td></tr>"
                        % (_human(r["business_date"]), _r(r["cash_p"]), _r(r["upi_p"]), _r(r["cash_p"] + r["upi_p"]),
                           _esc(r["handed_to"] or "—"), rec))
        out.append("""<details class="card"%s><summary><b>%s</b> — ₹ %s <span class="mut">(%d din)</span></summary>
          <table class="grid"><thead><tr><th>%s</th><th class="r">%s</th><th class="r">%s</th><th class="r">%s</th><th>%s</th><th>%s</th></tr></thead>
          <tbody>%s</tbody><tfoot><tr><td>%s</td><td class="r">%s</td><td class="r">%s</td><td class="r">%s</td><td></td><td></td></tr></tfoot></table>
          </details>""" % (" open" if ym == cur else "", dt.date(int(ym[:4]), int(ym[5:7]), 1).strftime("%B %Y"), _r(tc + tu), len(rows),
                           L["date"], L["cash"], L["upi"], L["total"], L["to"], L["rec"], "".join(body),
                           L["month"], _r(tc), _r(tu), _r(tc + tu)))
    if years:
        out.append("<div class='card'><table class='grid'><tbody>%s</tbody></table></div>"
                   % "".join("<tr><th class='sec'>%s %s</th><td class='r'><b>₹ %s</b></td></tr>" % (L["year"], y, _r(v)) for y, v in sorted(years.items(), reverse=True)))
    return "".join(out)


# ---------------------------------------------------------------- shells
def _denied():
    return """<div class="card"><h2>Not permitted</h2><p>This screen belongs to the clinic desk. Your login is not on it.
      If that is wrong, ask Dr Manoj.</p></div>"""


def _denied_physio():
    return """<div class="card"><h2>Not permitted</h2><p>This screen is the physiotherapy table. Your login is not on it.
      If that is wrong, ask Dr Manoj.</p></div>"""


def _shell(title, body):
    """The counter sheet's own large-type, high-contrast look (S223, the owner's eyes)."""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#3c464e;--line:#8a9aa6;--accent:#14456e;--paper:#fffdf7;--bg:#dfe5e9;--entry:#fffbe6}
*{box-sizing:border-box}
body{margin:0;padding:14px;background:var(--bg);color:var(--ink);font:18px/1.6 "Segoe UI",system-ui,-apple-system,sans-serif}
h1{font-size:23px;margin:0 0 12px;color:var(--accent);font-weight:700}
h2{font-size:20px;margin:0 0 10px;color:var(--accent)}
.card{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:16px;margin:0 0 16px;overflow-x:auto}
details.card summary{cursor:pointer;font-size:18px;color:var(--accent);font-weight:600}
.mut{color:var(--mut);font-size:16px}.hint{color:var(--mut);font-size:15px;font-weight:400}
table.grid{width:100%%;border-collapse:collapse;font-size:17px}
.grid th,.grid td{border:2px solid var(--line);padding:9px}
.grid thead th{background:#cfdae3;font-size:16px}
.r{text-align:right;white-space:nowrap}.d{white-space:nowrap;font-weight:600}
.sec{text-align:left;background:#eef2f5;font-size:17px;white-space:normal}
table.nums .sec{width:34%%}
tfoot td{background:#dff0d8;font-weight:700}
.entry input.amt{width:100%%;min-height:52px;font-size:22px;padding:8px 12px;border:2px solid #5b6b76;border-radius:8px;text-align:right;background:var(--entry)}
.note{width:100%%;min-height:48px;padding:9px;border:2px solid #5b6b76;border-radius:8px;font-size:17px;background:var(--entry)}
select.note{background:#fff}
button.save{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:14px 22px;font-size:19px;font-weight:600;cursor:pointer;margin-top:6px}
button.save[disabled]{background:#9aa7b1;cursor:not-allowed}
button.clear{background:var(--paper);color:#8c2f2f;border:2px solid #8c2f2f;border-radius:9px;padding:11px 16px;font-size:17px;cursor:pointer;margin-top:6px}
.inline{display:inline-block;margin-right:10px}
a.btn{display:inline-block;border:2px solid var(--accent);color:var(--accent);border-radius:9px;padding:10px 14px;text-decoration:none;font-size:16px;margin:6px 8px 0 0;background:var(--paper)}
.navrow{margin-top:12px}
.ok{background:#dff0d8;border-left:6px solid #2c6e2f;padding:12px 15px;margin-bottom:14px}
.bad{background:#fadbd8;border-left:6px solid #9c2a20;padding:12px 15px;margin-bottom:14px}
.verdict{font-weight:700;margin:12px 0 6px;font-size:19px}
.all_agree{color:#2c6e2f}.all_differ{color:#9c2a20}.waiting_bank{color:#8a5a00}.not_entered{color:var(--mut)}
.lines li{margin:6px 0}
.flag{border:2px solid var(--line);border-radius:9px;padding:12px;margin:10px 0;background:#fff}
.flag.f_open{border-color:#9c2a20;background:#fff4f2}.flag.f_expl{border-color:#8a5a00;background:#fff9ec}
.flag.f_cannot{border-color:#9c2a20}.flag.f_owner{border-color:#14456e;background:#eef4fb}.flag.f_done{opacity:.7}
.ftext{margin:0 0 6px}
.answer{margin-top:8px}.answer .note{margin-bottom:6px}
.pill{font-size:14px;padding:2px 9px;border-radius:12px;background:#e3e8eb;border:1px solid var(--line);white-space:nowrap}
.radios label.radio{display:block;margin:4px 0}
@media (max-width:620px){body{padding:10px}.card{padding:12px}table.grid{font-size:15px}.grid th,.grid td{padding:6px 5px}.sec{font-size:15px}
 a.btn{display:block;text-align:center;margin:8px 0 0}.inline{display:block;margin:6px 0 0}}
@media print{@page{size:A4 portrait;margin:12mm}.noprint,form{display:none!important}body{background:#fff;padding:0;font-size:12pt}.card{border:none;padding:0}}
</style></head><body><h1>Dr. Manoj Agarwal Clinic — %s</h1>
%s</body></html>""" % (_esc(title), _esc(title), body)
