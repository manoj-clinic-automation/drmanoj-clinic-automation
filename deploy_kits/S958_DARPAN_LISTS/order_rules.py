#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  order_rules.py  ·  v1.0  ·  kit S410_MEDICINE_ORDERING  ·  Session 283 (Sanjeevni)  ·  D626
#
#  THE MEDICINE BUYING RULES AS SETTINGS (the owner's sitting of 26-Sep-2026): every number a setting or a per-supplier
#  row on his page, never a constant; fixed order days, not "every N days"; the ordering team's day (prepared at 09:00,
#  reminded at 12 / 15 / 17, silent once all are sent); interim orders when an item would run under lead + safety before
#  its supplier's next order day; the owner's Needs you only for a stuck order, a month running above its average, and
#  the Kedar review. Orthotics are NOT touched (S403's keep-in-stock runs them).
#
#  REUSES, never a second engine: purchase_app (S225) -- _latest_snapshot / _pace / _last_purchase / _in_transit /
#  _carried_shorts / plan_line (every quantity rail intact) / _staff_qty (the owner's 10-then-tens) / _staff_send (the
#  order book + the wa.me link). The cover per order comes from the SUPPLIER'S RULE here (gap to the next order day +
#  lead + safety [+ the single-source extra unless waived], capped) and is handed to plan_line as its cadence so that the
#  engine's own additions cancel exactly.
#
#  WHAT THIS FILE IS
#    * the module porders.init mounts (fail-soft), under the porders unit (its paths all start /finance/porders/):
#        GET  /finance/porders/api/rules/state         the owner's page: rules per supplier, settings, candidates, item rules,
#                                                      the freeze, holidays, the two blocks' counts
#        POST /finance/porders/api/rules/set           {supplier, field, value}  one field, audited (owner)
#        POST /finance/porders/api/rules/item          {item, rule, on, value}   per-item override + the lists (owner)
#                                                      S414: the answer carries counts {item_rules, by_rule, lists} and the row
#        GET  /finance/porders/api/rules/items?q=      S414: <= 20 item names from the stock master for the add box (owner)
#        POST /finance/porders/api/rules/freeze        {on, reason}              (owner)
#        POST /finance/porders/api/rules/holiday       {day, note, remove}       (senders + owner)
#        GET  /finance/porders/api/oos                 out of stock both ends     (owner)
#        GET  /finance/porders/api/new-items?month=    first-ever purchases       (owner)
#        GET  /finance/porders/api/day                 today's proposals          (staff)
#        POST /finance/porders/api/day/send            {proposal_id, lines}      -> the S403 wa.me flow (senders + owner)
#    * the cron worker (venv python, one root line, 05:30 nightly · 09:00 prepare + notice · 12/15/17 reminders):
#        order_rules.py tick            decides by the clock (ORDER_TICK=nightly|prepare|remind for a test)
#        order_rules.py status          what today holds (read-only)
#    * read helpers the other pages call in-process, fail-soft: needs_you_lines(con) · day_summary(con)
#
#  NO phone number, no token, no patient data in this file. The vendor's number stays inside purchase_app's wa.me link.
#  ORDER_TODAY / ORDER_PUSH_STUB / ORDER_TICK serve the walk; the service never sets them.
# =============================================================================
import datetime as dt
import json
import math
import os
import re
import sqlite3
import statistics
import sys

from flask import Blueprint, jsonify, request

VERSION = "1.0"
KIT = "S644_BUYING_MODEL"                                       # the kit that last changed this file (S593 before it); v1.0 was S410_MEDICINE_ORDERING
#  S593 (19-Oct-2026, D743; S308 i, ii, iii, viii and Part A; charter rules 1, 2, 3, 9, 13, 14): THE ENGINE ON THE ONE STOCK FUNCTION AND
#  THE ONE ARRIVALS RULE. _s470_snap takes every item's figure from stock_figure.marg() (Marg's newest usable closing carried by the spine's
#  movements) + taps() + scan_arrivals() since that closing's capture -- the engine's own closing read, equal-share split and arrivals rule
#  (_s470_arrivals) are retired; rhythm() reads Marg's purchase bills from the spine (spine_read.purchases_by_supplier), never purchase_bill;
#  days_left() is the ONE days-left figure (Darpan's tab and his add door call it); send_proposal refuses an 'open' proposal on
#  order.source = darpan (F-738); plan() carries `inputs` (what the stock side stood on; the owner's api/day). No new setting, no new table.
bp = Blueprint("order_rules", __name__)
_db = _require = None
ACCESS_UNIT = "porders"
HERE = os.path.dirname(os.path.abspath(__file__))

# --- S430_DESK_FIRST_READ (D637 / F-650): a quantity in the item's own words -- strips / pcs by its packing, never 'units' ----
try:
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import qty_words as _qty                                   # noqa: PLC0415 -- beside this file (S427)
    QTY_WORDS_OK = True
except Exception:                                              # pragma: no cover
    _qty = None
    QTY_WORDS_OK = False


def _qw(units, s):
    """'12 strips + 4 tabs' / '3 pcs' from the snapshot row's packing and pack size; the bare figure when qty_words is away."""
    if QTY_WORDS_OK:
        return _qty.words(units, packing=(s or {}).get("packing"), pack=(s or {}).get("pack_size"))
    return "%d" % int(units or 0)
# --- S430 end -----------------------------------------------------------------------------------------------------------------
if HERE not in sys.path:
    sys.path.insert(0, HERE)
SPINE_DIR = os.path.join(HERE, "spine")
RULES_JSON = os.path.join(SPINE_DIR, "order_rules.json")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
DOW = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
DOW_WORD = {"MON": "Monday", "TUE": "Tuesday", "WED": "Wednesday", "THU": "Thursday", "FRI": "Friday", "SAT": "Saturday", "SUN": "Sunday"}
CADENCES = ("weekly", "fortnightly", "monthly", "custom")
GAP = {"weekly": 7, "fortnightly": 14, "monthly": 30}
KEDAR = "KEDAR PHARMACEUTICAL"
REPEAT_MIN = 10
SLOTS = {"nightly": (5, 30), "prepare": (9, 0), "remind": ((12, 0), (15, 0), (17, 0))}
SETTINGS = {
    "order.lead_days": ("1", "days from the order to the goods (same-evening delivery); 2 where a supplier's own record shows later"),
    "order.safety_days": ("3", "safety days on top of lead"),
    "order.single_source_extra_days": ("3", "extra cover for an item bought from one supplier only (waived per supplier)"),
    "order.cap_weekly": ("14", "cover cap, days, for a weekly (and Kedar's custom) supplier"),
    "order.cap_fortnightly": ("21", "cover cap, days, fortnightly"),
    "order.cap_monthly": ("45", "cover cap, days, monthly"),
    "order.min_line_p": ("5000", "a line under this (paise) waits, unless the item is out of stock"),
    "order.min_order_p": ("50000", "a proposal under this (paise) waits for the next order day, unless an item is out of stock"),
    "order.blocked_days": ("SUN,THU", "days no order goes out, for every supplier unless its row says otherwise"),
    "order.interim": ("1", "interim orders on / off"),
    "order.interim_from": ("", "interim orders start on this date (set by the seed: one week after go-live)"),
    "order.go_live": ("", "the day the fixed-day orders started (set by the seed)"),
    "order.notice_to": ("darpan,shavez,shivani,alisha", "the ordering team: the notices go to these logins, never the owner"),
    "order.spend_alert_pct": ("25", "Needs you when a supplier's month runs this % above its 90-day average"),
    "order.sunday_line": ("1", "the Sunday one-liner in Needs you"),
    "order.on_demand_min_p": ("20000", "on-demand candidate: unit value at least this (paise)"),
    "order.never_days": ("60", "never-reorder candidate: in stock, no sale for this many days"),
    "order.on_demand_days": ("180", "on-demand candidate: at most order.on_demand_max_sales sales in this many days"),
    "order.on_demand_max_sales": ("2", ""),
    "order.min_bills_for_rhythm": ("3", "fewer bills in 90 days -> the money tiers decide the cadence"),
    "order.tier_weekly_p": ("2000000", "fallback tier: weekly at or above this much a month (paise)"),
    "order.tier_fortnight_p": ("400000", "fallback tier: fortnightly at or above this much a month (paise)"),
    "order.review_weeks": ("4", "Kedar's ramp: the review this many weeks after go-live"),
    "order.freeze": ("", "json {by, at, reason} while all medicine ordering is frozen"),
    "order.darpan_list_time": ("09:30", "S485 (D677): the list opens on Darpan's tab at this time (HH:M0); the proposals are prepared at 09:00 as before"),
}
DDL = (
    "CREATE TABLE IF NOT EXISTS order_supplier_rule ("
    " supplier_norm TEXT PRIMARY KEY, supplier TEXT, cadence TEXT NOT NULL DEFAULT 'weekly', order_days TEXT NOT NULL DEFAULT 'MON',"
    " anchor_date TEXT, blocked_days TEXT, lead_days INTEGER NOT NULL DEFAULT 1, lead_learned INTEGER, lead_n INTEGER NOT NULL DEFAULT 0,"
    " safety_days INTEGER NOT NULL DEFAULT 3, cover_cap_days INTEGER NOT NULL DEFAULT 14, single_source_extra INTEGER NOT NULL DEFAULT 1,"
    " paused INTEGER NOT NULL DEFAULT 0, pause_reason TEXT, review_on TEXT, review_target TEXT, min_order_p INTEGER,"
    " note TEXT, owner_fields TEXT NOT NULL DEFAULT '[]', bills90 INTEGER, rhythm_days REAL, avg_month_p INTEGER, cadence_how TEXT,"
    " seeded_at TEXT, updated_at TEXT)",
    "CREATE TABLE IF NOT EXISTS order_rule_audit (id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT NOT NULL, supplier_norm TEXT,"
    " field TEXT NOT NULL, old TEXT, new TEXT)",
    "CREATE TABLE IF NOT EXISTS order_holiday (day TEXT PRIMARY KEY, note TEXT, set_by TEXT, set_at TEXT)",
    "CREATE TABLE IF NOT EXISTS order_item_rule (item_norm TEXT PRIMARY KEY, item TEXT NOT NULL, rule TEXT NOT NULL, value INTEGER,"
    " set_by TEXT, set_at TEXT, note TEXT)",
    "CREATE TABLE IF NOT EXISTS order_proposal (id INTEGER PRIMARY KEY, day TEXT NOT NULL, supplier_norm TEXT NOT NULL, vendor TEXT NOT NULL,"
    " kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open', lines TEXT NOT NULL, total_p INTEGER NOT NULL DEFAULT 0, reason TEXT,"
    " prepared_at TEXT NOT NULL, sent_order_id INTEGER, sent_at TEXT, sent_by TEXT, merged_into TEXT, carried_from TEXT,"
    " UNIQUE (day, supplier_norm, kind))",
    "CREATE TABLE IF NOT EXISTS order_notice (id INTEGER PRIMARY KEY, day TEXT NOT NULL, slot TEXT NOT NULL, text TEXT NOT NULL,"
    " sent TEXT, at TEXT NOT NULL, UNIQUE (day, slot))",
)
RULE_FIELDS = ("cadence", "order_days", "anchor_date", "blocked_days", "lead_days", "safety_days", "cover_cap_days", "single_source_extra",
               "paused", "pause_reason", "review_on", "review_target", "min_order_p", "note")
ITEM_RULES = ("keep", "never", "on_demand", "max_shelf", "internal")
LIST_OF = {"never": "never_reorder", "on_demand": "on_demand", "internal": "internal_use"}


def init(app, db_getter, require_fn, unit="porders"):
    global _db, _require, ACCESS_UNIT
    _db, _require, ACCESS_UNIT = db_getter, require_fn, unit
    app.register_blueprint(bp)
    return bp


# ------------------------------------------------------------------ small things
def _today():
    v = os.environ.get("ORDER_TODAY", "")
    try:
        return dt.date.fromisoformat(v) if v else dt.date.today()
    except ValueError:
        return dt.date.today()


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _pa():
    import purchase_app                                       # noqa: PLC0415 -- beside this file, mounted first
    return purchase_app


def _dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b-%Y")
    except (TypeError, ValueError):
        return str(iso or "")


def _dmy_short(d):
    return d.strftime("%a %d-%b") if isinstance(d, dt.date) else _dmy(d)


def _rs(p):
    try:
        return _pa()._r(int(p or 0))
    except Exception:                                         # noqa: BLE001
        return "₹%d" % (int(p or 0) // 100)


def _esc(s):
    return str("" if s is None else s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _has(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone() is not None


def ensure(con):
    for d in DDL:
        con.execute(d)
    con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
    for k, (v, note) in SETTINGS.items():
        con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, "S410 D626 -- " + note))
    con.commit()


def _setting(con, key, default=None):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and r[0] is not None and str(r[0]).strip() != "":
            return str(r[0])
    except sqlite3.Error:
        pass
    return SETTINGS.get(key, (default, ""))[0] if default is None else default


def _int_setting(con, key):
    try:
        return int(float(_setting(con, key)))
    except (TypeError, ValueError):
        return int(SETTINGS[key][0] or 0)


def _set_setting(con, key, value, who, note=None):
    old = _setting(con, key, "")
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value), note or ("S410 D626 -- " + SETTINGS.get(key, ("", ""))[1])))
    _audit(con, who, None, key, old, str(value))


def _audit(con, who, supplier_norm, field, old, new):
    con.execute("INSERT INTO order_rule_audit (at, who, supplier_norm, field, old, new) VALUES (?,?,?,?,?,?)",
                (now_iso(), who or "", supplier_norm, field, None if old is None else str(old), None if new is None else str(new)))


def _who(u):
    return str((u or {}).get("user") or (u or {}).get("username") or "")


def _short(vendor):
    """'KEDAR PHARMACEUTICAL' -> 'Kedar' · 'L.K. DRUG HOUSE' -> 'L.K. Drug' -- the notice's short name."""
    w = [x for x in re.split(r"\s+", str(vendor or "").strip()) if x]
    if not w:
        return "?"
    head = w[0]
    if len(head.replace(".", "")) <= 4 and len(w) > 1:
        head = w[0] + " " + w[1]
    return " ".join(p if "." in p else p.capitalize() for p in head.split(" "))


def _ortho_norm(con):
    try:
        import porders                                        # noqa: PLC0415
        return _pa().supplier_key(porders.vendor_of(con))
    except Exception:                                         # noqa: BLE001
        return "YUVIKA SURGICALS"


def _frozen(con):
    raw = _setting(con, "order.freeze", "")
    try:
        j = json.loads(raw) if raw else None
    except ValueError:
        j = None
    return j if (j and j.get("at")) else None


# ------------------------------------------------------------------ the rhythm and the seed
def nearest_cadence(gap_days):
    """The nearest of weekly / fortnightly / monthly to the shop's own gap -- nearest, never rounded up; a tie goes to the faster."""
    best, bd = None, None
    for name in ("weekly", "fortnightly", "monthly"):
        d = abs(float(gap_days) - GAP[name])
        if bd is None or d < bd:
            best, bd = name, d
    return best


def tier_cadence(con, monthly_p):
    if monthly_p >= _int_setting(con, "order.tier_weekly_p"):
        return "weekly"
    if monthly_p >= _int_setting(con, "order.tier_fortnight_p"):
        return "fortnightly"
    return "monthly"


def rhythm(con, today=None):
    """{supplier_norm: dict(supplier, dates, bills90, gap, amount90_p, avg_month_p, cadence, how)} from 90 days of Marg's purchase bills AS
    THE SPINE HOLDS THEM (S593, charter 1: the spine's bill table through spine_read.purchases_by_supplier, direction PURCHASE; the
    supplier's printed name mapped to supplier_norm by pa.supplier_key -- the same key that writes supplier_norm in the tables). amount90_p
    is the report's bill amount (the tables gave the NET amount per bill: the money basis moved, named in the kit's README)."""
    pa = _pa()
    today = today or _today()
    since = (today - dt.timedelta(days=90)).isoformat()
    out = {}
    sp = _s470_spine()
    try:
        rows = sp.purchases_by_supplier(since, today.isoformat())
    finally:
        try:
            sp.con.close()
        except Exception:                                      # noqa: BLE001
            pass
    for r in rows:
        sn = pa.supplier_key(r["supplier"]) if r["supplier"] else ""
        if not sn:
            continue
        e = out.setdefault(sn, dict(supplier=r["supplier"], dates=[], amount90_p=0, bills90=0))
        e["dates"].append(str(r["date"] or "")[:10])
        e["amount90_p"] += int(r["amount_p"] or 0)
        e["bills90"] += int(r["n_bills"] or 0)
        e["supplier"] = r["supplier"] or e["supplier"]
    minb = _int_setting(con, "order.min_bills_for_rhythm")
    for sn, e in out.items():
        ds = sorted(set(e["dates"]))
        dds = []
        for x in ds:
            try:
                dds.append(dt.date.fromisoformat(x))
            except ValueError:
                pass
        e["avg_month_p"] = int(e["amount90_p"] / 3.0)
        e["interval"], e["gap"], e["bill_days90"] = model_interval(dds, today, minb, _s470_days(con, "order.review_default_days"),   # S644: THE one median
                                                                 _s470_days(con, "order.review_min_days"), _s470_days(con, "order.review_max_days"))
        if len(ds) >= minb and e["gap"] is not None:
            e["cadence"], e["how"] = nearest_cadence(e["gap"]), "rhythm: %d bill days in 90, median %.0f days apart" % (len(ds), e["gap"])
        else:
            e["cadence"], e["how"] = tier_cadence(con, e["avg_month_p"]), "money tier (%d bill%s in 90 days): %s a month" % (len(ds), "" if len(ds) == 1 else "s", _rs(e["avg_month_p"]))
    return out


def lead_learned(con, supplier_norm, today=None):
    """(median days from the order to the goods, n) from this supplier's own orders: arrival tap or Marg's bill date."""
    today = today or _today()
    since = (today - dt.timedelta(days=90)).isoformat()
    pa = _pa()
    vals = []
    try:
        for o in con.execute("SELECT id, vendor, created_at FROM purchase_order WHERE status IN ('sent','received') AND created_at>=?", (since,)):
            if pa.supplier_key(o[1]) != supplier_norm:
                continue
            d0 = dt.date.fromisoformat(str(o[2])[:10])
            r = con.execute("SELECT MIN(COALESCE(billed_date, substr(arrived_at,1,10))) FROM purchase_order_line WHERE order_id=? AND (arrived_at IS NOT NULL OR billed_date IS NOT NULL)", (o[0],)).fetchone()
            if r and r[0]:
                try:
                    vals.append(max(0, (dt.date.fromisoformat(str(r[0])[:10]) - d0).days))
                except ValueError:
                    pass
    except sqlite3.Error:
        return None, 0
    if len(vals) < LEAD_MIN_N:                                # S662: one or two orders do not make a lead -- the default stands
        return None, 0
    return int(round(statistics.median(vals))), len(vals)


LEAD_MIN_N = 3                                                # S662: orders needed before a supplier's own lead replaces order.lead_days


def _owner_fields(r):
    try:
        return set(json.loads(r.get("owner_fields") or "[]"))
    except (TypeError, ValueError):
        return set()


def _first_monday_on_or_after(d):
    return d + dt.timedelta(days=(7 - d.weekday()) % 7)


def reseed(con, today=None, who="seed"):
    """Every supplier with bills in 90 days (never the orthotics vendor) gets a row; fields the owner set are never overwritten.
    Kedar's row carries the D626 rulings as owner-set (custom Mon + Fri, Thursday open, extra waived, cap 14, the review)."""
    ensure(con)
    today = today or _today()
    go_live = _setting(con, "order.go_live", "") or today.isoformat()
    try:
        gl = dt.date.fromisoformat(go_live)
    except ValueError:
        gl = today
    ortho = _ortho_norm(con)
    rh = rhythm(con, today)
    default_blocked = _setting(con, "order.blocked_days")
    lead_default = _int_setting(con, "order.lead_days")
    caps = {"weekly": _int_setting(con, "order.cap_weekly"), "fortnightly": _int_setting(con, "order.cap_fortnightly"), "monthly": _int_setting(con, "order.cap_monthly"), "custom": _int_setting(con, "order.cap_weekly")}
    changed = 0
    for sn, e in sorted(rh.items()):
        if sn == ortho:
            continue
        cur = con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (sn,)).fetchone()
        cur = dict(cur) if cur else None
        ll, ln = lead_learned(con, sn, today)
        lead = lead_default if ll is None else (1 if ll <= 1 else 2)
        want = dict(supplier=e["supplier"], cadence=e["cadence"], order_days="MON", anchor_date=_first_monday_on_or_after(gl).isoformat(),
                    blocked_days=default_blocked, lead_days=lead, lead_learned=ll, lead_n=ln, safety_days=_int_setting(con, "order.safety_days"),
                    cover_cap_days=caps[e["cadence"]], single_source_extra=1, min_order_p=_int_setting(con, "order.min_order_p"),
                    bills90=e["bills90"], rhythm_days=e["gap"], avg_month_p=e["avg_month_p"], cadence_how=e["how"])
        owner = set()
        if sn == KEDAR:
            weeks = _int_setting(con, "order.review_weeks")
            want.update(cadence="custom", order_days="MON,FRI", blocked_days="SUN", single_source_extra=0, cover_cap_days=caps["weekly"],
                        review_on=(gl + dt.timedelta(days=7 * weeks)).isoformat(), review_target="weekly",
                        note="D626: twice weekly (Mon + Fri), delivers Thursdays, same-evening delivery; review after %d weeks" % weeks)
            owner = {"cadence", "order_days", "blocked_days", "single_source_extra", "cover_cap_days", "review_on", "review_target", "note"}
        if cur is None:
            cols = ["supplier_norm"] + list(want.keys()) + ["owner_fields", "seeded_at", "updated_at"]
            vals = [sn] + list(want.values()) + [json.dumps(sorted(owner)), now_iso(), now_iso()]
            con.execute("INSERT INTO order_supplier_rule (%s) VALUES (%s)" % (",".join(cols), ",".join("?" * len(cols))), vals)
            _audit(con, who, sn, "seed", None, "%s %s" % (want["cadence"], want["order_days"]))
            changed += 1
            continue
        kept = _owner_fields(cur)
        upd = {}
        for k, v in want.items():
            if k in kept:
                continue
            if k in ("review_on", "review_target", "note") and sn != KEDAR:
                continue
            if str(cur.get(k)) != str(v):
                upd[k] = v
        if upd:
            for k, v in upd.items():
                if k in ("cadence", "order_days", "lead_days", "cover_cap_days", "blocked_days"):
                    _audit(con, who, sn, k, cur.get(k), v)
            sets = ", ".join("%s=?" % k for k in upd) + ", updated_at=?"
            con.execute("UPDATE order_supplier_rule SET %s WHERE supplier_norm=?" % sets, list(upd.values()) + [now_iso(), sn])
            changed += 1
    if not _setting(con, "order.go_live", ""):
        _set_setting(con, "order.go_live", today.isoformat(), who)
    if not _setting(con, "order.interim_from", ""):
        _set_setting(con, "order.interim_from", (today + dt.timedelta(days=7)).isoformat(), who)
    con.commit()
    return changed


def rules(con):
    ensure(con)
    out = []
    for r in con.execute("SELECT * FROM order_supplier_rule ORDER BY (supplier_norm<>?) , supplier_norm", (KEDAR,)):
        r = dict(r)
        r["owner_set"] = sorted(_owner_fields(r))
        r["words"] = rule_words(con, r)
        r["short"] = _short(r["supplier"] or r["supplier_norm"])
        r["gap_days"] = gap_days(r)
        r["cover_days"] = cover_days(con, r, single_source=False)
        r["cover_days_single"] = cover_days(con, r, single_source=True)
        out.append(r)
    return out


def rule_for(con, supplier_norm):
    r = con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone()
    if r:
        return dict(r)
    return dict(supplier_norm=supplier_norm, supplier=supplier_norm, cadence="weekly", order_days="MON", anchor_date=None,
                blocked_days=_setting(con, "order.blocked_days"), lead_days=_int_setting(con, "order.lead_days"), safety_days=_int_setting(con, "order.safety_days"),
                cover_cap_days=_int_setting(con, "order.cap_weekly"), single_source_extra=1, paused=0, pause_reason=None, review_on=None,
                review_target=None, min_order_p=_int_setting(con, "order.min_order_p"), note=None, owner_fields="[]", _default=True)


def rule_words(con, r):
    """One plain line: 'Kedar — Mon & Fri, delivered same evening, cover 8 days, cap 14, Thursday ok; review 24-Oct'."""
    days = [d for d in str(r.get("order_days") or "MON").split(",") if d]
    if r["cadence"] == "weekly":
        w = "%ss" % DOW_WORD.get(days[0], "Monday")
    elif r["cadence"] == "fortnightly":
        w = "alternate %ss%s" % (DOW_WORD.get(days[0], "Monday"), (" (from %s)" % _dmy(r["anchor_date"])) if r.get("anchor_date") else "")
    elif r["cadence"] == "monthly":
        w = "first %s of the month" % DOW_WORD.get(days[0], "Monday")
    else:
        w = " & ".join(d.capitalize() for d in days)
    lead = int(r.get("lead_days") or 1)
    lw = "delivered same evening" if lead <= 1 else "delivered in %d days" % lead
    if r.get("lead_n"):
        lw += " (learned from %d order%s)" % (r["lead_n"], "" if r["lead_n"] == 1 else "s")
    blocked = set(str(r.get("blocked_days") or "").split(","))
    parts = [w, lw, "cover %d days, cap %d" % (cover_days(con, r, single_source=False), int(r.get("cover_cap_days") or 0)),
             "Thursday ok" if "THU" not in blocked else "Thursday blocked"]
    if not int(r.get("single_source_extra") or 0):
        parts.append("single-source extra waived")
    if r.get("min_order_p") and int(r["min_order_p"]) != _int_setting(con, "order.min_order_p"):
        parts.append("min order %s" % _rs(r["min_order_p"]))
    s = "%s — %s" % (_short(r.get("supplier") or r["supplier_norm"]), ", ".join(parts))
    if r.get("review_on"):
        s += "; review %s → %s" % (_dmy(r["review_on"]), r.get("review_target") or "weekly")
    if int(r.get("paused") or 0):
        s += "; PAUSED: %s" % (r.get("pause_reason") or "")
    return s


# ------------------------------------------------------------------ the calendar
def _holidays(con, d0, d1):
    try:
        return {r[0] for r in con.execute("SELECT day FROM order_holiday WHERE day>=? AND day<=?", (d0.isoformat(), d1.isoformat()))}
    except sqlite3.Error:
        return set()


def _blocked_set(r):
    return {x.strip().upper() for x in str(r.get("blocked_days") or "").split(",") if x.strip()}


def _nominal(r, d):
    """Is d a nominal order day of the rule (before holidays and blocks move it)?"""
    days = [x.strip().upper() for x in str(r.get("order_days") or "MON").split(",") if x.strip()]
    dow = DOW[d.weekday()]
    if dow not in days:
        return False
    if r["cadence"] == "fortnightly":
        try:
            a = dt.date.fromisoformat(str(r.get("anchor_date"))[:10])
        except (TypeError, ValueError):
            a = _first_monday_on_or_after(dt.date(2026, 9, 28))
        return ((d - a).days // 7) % 2 == 0
    if r["cadence"] == "monthly":
        return d.day <= 7
    return True


def order_days_between(con, r, d0, d1):
    """The EFFECTIVE order days in [d0, d1]: a nominal day on a holiday or a blocked day moves to the previous working day."""
    hol = _holidays(con, d0 - dt.timedelta(days=10), d1 + dt.timedelta(days=10))
    blocked = _blocked_set(r) | {"SUN"}
    out = set()
    d = d0 - dt.timedelta(days=7)
    while d <= d1 + dt.timedelta(days=7):
        if _nominal(r, d):
            e = d
            n = 0
            while (DOW[e.weekday()] in blocked or e.isoformat() in hol) and n < 7:
                e -= dt.timedelta(days=1)
                n += 1
            if d0 <= e <= d1:
                out.add(e)
        d += dt.timedelta(days=1)
    return sorted(out)


def is_order_day(con, r, d):
    return d in set(order_days_between(con, r, d, d))


def next_order_day(con, r, after):
    ds = order_days_between(con, r, after + dt.timedelta(days=1), after + dt.timedelta(days=60))
    return ds[0] if ds else after + dt.timedelta(days=GAP.get(r["cadence"], 7))


def gap_days(r):
    """Days one order must cover until the next: weekly 7 · fortnightly 14 · monthly 30 · custom = the longest gap in the week cycle."""
    if r["cadence"] in GAP:
        return GAP[r["cadence"]]
    days = sorted({DOW.index(x.strip().upper()) for x in str(r.get("order_days") or "MON").split(",") if x.strip().upper() in DOW})
    if len(days) <= 1:
        return 7
    gaps = [days[i + 1] - days[i] for i in range(len(days) - 1)] + [7 - days[-1] + days[0]]
    return max(gaps)


def cover_days(con, r, single_source):
    c = gap_days(r) + int(r.get("lead_days") or 1) + int(r.get("safety_days") or 3)
    if single_source and int(r.get("single_source_extra") or 0):
        c += _int_setting(con, "order.single_source_extra_days")
    return min(c, int(r.get("cover_cap_days") or 45))


def blocked_today(con, r, d):
    return DOW[d.weekday()] in (_blocked_set(r) | {"SUN"}) or d.isoformat() in _holidays(con, d, d)


# ------------------------------------------------------------------ the lists and the per-item rules
def _k20(n):
    return re.sub(r"\s+", " ", (n or "").strip().upper())[:20].strip()


def load_lists():
    try:
        with open(RULES_JSON, encoding="utf-8") as fh:
            j = json.load(fh)
    except (OSError, ValueError):
        j = {"version": 0, "never_reorder": [], "on_demand": [], "internal_use": [], "orthotics_cycle": []}
    return j


def _write_lists(j):
    os.makedirs(os.path.dirname(RULES_JSON), exist_ok=True)
    tmp = RULES_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(j, fh, indent=1, ensure_ascii=False)
    os.replace(tmp, RULES_JSON)


def item_rules(con):
    ensure(con)
    out = {}
    for r in con.execute("SELECT * FROM order_item_rule"):
        out[r["item_norm"]] = dict(r)
    return out


def held_sets(con):
    """{k20: reason} for every item the lists or the per-item rules hold back."""
    pa = _pa()
    j = load_lists()
    out = {}
    for lst, word in (("never_reorder", "never re-ordered (your list)"), ("internal_use", "internal use, not sold"), ("on_demand", "on demand only (your list)")):
        for n in j.get(lst) or []:
            out[_k20(n)] = word
    for k, r in item_rules(con).items():
        if r["rule"] in ("never", "on_demand", "internal"):
            out[_k20(r["item"])] = {"never": "never re-ordered (your list)", "on_demand": "on demand only (your list)", "internal": "internal use, not sold"}[r["rule"]]
    _ = pa
    return out


def set_item_rule(con, who, item, rule, on=True, value=None):
    pa = _pa()
    ensure(con)
    if rule not in ITEM_RULES:
        return dict(ok=False, error="bad_rule"), 400
    k = pa.norm(item)
    cur = con.execute("SELECT rule, value FROM order_item_rule WHERE item_norm=?", (k,)).fetchone()
    if on:
        con.execute("INSERT INTO order_item_rule (item_norm, item, rule, value, set_by, set_at) VALUES (?,?,?,?,?,?) ON CONFLICT(item_norm) DO UPDATE SET "
                    "item=excluded.item, rule=excluded.rule, value=excluded.value, set_by=excluded.set_by, set_at=excluded.set_at", (k, item, rule, value, who, now_iso()))
    else:
        con.execute("DELETE FROM order_item_rule WHERE item_norm=?", (k,))
    _audit(con, who, None, "item:" + rule, ("%s %s" % (cur[0], cur[1])) if cur else None, ("%s %s" % (rule, value)) if on else "off")
    if rule in LIST_OF:
        j = load_lists()
        lst = LIST_OF[rule]
        names = [n for n in (j.get(lst) or []) if _k20(n) != _k20(item)]
        if on:
            names.append(item)
        j[lst] = names
        for other, ol in LIST_OF.items():
            if other != rule and on:
                j[ol] = [n for n in (j.get(ol) or []) if _k20(n) != _k20(item)]
        j["version"] = int(j.get("version") or 0) + 1        # the key set stays S341's; the audit row says who and when
        j.setdefault("orthotics_cycle", [])
        j["orthotics_cycle"] = []
        _write_lists(j)
    con.commit()
    row = con.execute("SELECT item, rule, value, set_by, set_at FROM order_item_rule WHERE item_norm=?", (k,)).fetchone() if on else None
    return dict(ok=True, item=item, rule=rule, on=bool(on), value=value, lists=load_lists(), counts=rule_counts(con), row=(dict(row) if row else None)), 200


def rule_counts(con):
    """S414 (F-635): what the owner's page shows after a tick WITHOUT a re-fetch -- the per-item rules by rule and the lists' sizes."""
    ensure(con)
    by = {r: 0 for r in ITEM_RULES}
    for rule, n in con.execute("SELECT rule, COUNT(*) FROM order_item_rule GROUP BY rule"):
        if rule in by:
            by[rule] = int(n or 0)
    j = load_lists()
    return dict(item_rules=sum(by.values()), by_rule=by, lists={k: len(j.get(k) or []) for k in ("never_reorder", "on_demand", "internal_use")})


def item_names(con, q, limit=20):
    """S414: item names from the newest stock snapshot (the stock master) for the add box's autocomplete -- every typed word must
    appear in the name; at most `limit` names, in name order."""
    words = [w for w in re.split(r"\s+", str(q or "").strip().upper()) if w]
    _as_on, snap = _pa()._latest_snapshot(con)
    out = []
    for k in sorted(snap, key=lambda x: str(snap[x]["item"]).upper()):
        s = snap[k]
        up = str(s["item"]).upper()
        if all(w in up for w in words):
            out.append(dict(item=s["item"], qty=s["qty"], packing=s.get("packing") or ""))
            if len(out) >= limit:
                break
    return out


def candidates(con, today=None):
    """never-reorder = in stock, no sale in order.never_days · on-demand = at most N sales in 180 days and unit value >= order.on_demand_min_p.
    Orthotics, the internal-use list and already-ticked items are left out."""
    pa = _pa()
    today = today or _today()
    as_on, snap = pa._latest_snapshot(con)
    never_d = _int_setting(con, "order.never_days")
    od_days = _int_setting(con, "order.on_demand_days")
    od_max = _int_setting(con, "order.on_demand_max_sales")
    od_min = _int_setting(con, "order.on_demand_min_p")
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    held = held_sets(con)
    ticked = item_rules(con)
    last = {}
    n180 = {}
    if _has(con, "sale_line_item"):
        for r in con.execute("SELECT item_name, MAX(business_date) FROM sale_line_item WHERE unit='medical' AND is_return=0 GROUP BY item_name"):
            k = pa.norm(r[0])
            if k not in last or r[1] > last[k]:
                last[k] = r[1]
        for r in con.execute("SELECT item_name, COUNT(DISTINCT bill_no) FROM sale_line_item WHERE unit='medical' AND is_return=0 AND business_date>=? GROUP BY item_name",
                             ((today - dt.timedelta(days=od_days)).isoformat(),)):
            n180[pa.norm(r[0])] = n180.get(pa.norm(r[0]), 0) + int(r[1] or 0)
    rate = {}
    if _has(con, "stock_rate"):
        rate = {pa.norm(r[0]): (int(r[1] or 0), int(r[2] or 1)) for r in con.execute("SELECT item, rate_p, pack_size FROM stock_rate")}
    purch = pa._last_purchase(con)
    never, ondem = [], []
    cut = (today - dt.timedelta(days=never_d)).isoformat()
    for k, s in snap.items():
        if k in ortho or _k20(s["item"]) in held or k in ticked:
            continue
        ls = last.get(k)
        if s["qty"] > 0 and (not ls or ls < cut):
            never.append(dict(item=s["item"], qty=s["qty"], last_sale=ls, last_sale_text=_dmy(ls) if ls else "never", packing=s["packing"]))
        n = n180.get(k, 0)
        lp = purch.get(k) or {}
        unit_p = int(lp.get("rate_p") or 0) or (rate[k][0] * rate[k][1] if k in rate else 0)
        if n <= od_max and unit_p >= od_min:
            ondem.append(dict(item=s["item"], qty=s["qty"], sales=n, unit_p=unit_p, unit_rs=_rs(unit_p), packing=s["packing"]))
    never.sort(key=lambda x: (x["last_sale"] or "", x["item"]))
    ondem.sort(key=lambda x: (-x["unit_p"], x["item"]))
    return dict(as_on=as_on, never=never, on_demand=ondem, never_days=never_d, on_demand_days=od_days, on_demand_max_sales=od_max, on_demand_min_rs=_rs(od_min))


# ------------------------------------------------------------------ the engine wrapper
def _on_order_units(con, today, basis=None):
    """{norm(item): dict(units, order_id, sent)} -- units on a SENT order of the last order.on_order_days days (the setting; S593 retired the
    unused constant) whose line nobody has answered yet: on the way, counted as stock so the next morning's interim check does not order them twice."""
    pa = _pa()
    since = (today - dt.timedelta(days=_s470_days(con, "order.on_order_days"))).isoformat()   # S470 (B.8): the setting, 4 as before
    out = {}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.id, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE (o.status='sent'" + (_s454_or_arrived(con) if basis != "count" else _s454_not_tied(con)) + ") AND o.created_at>=? "
                           "AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",          # S454 P3: on count, an order arrived by its scan is in the shelf figure
                           (since,)).fetchall()            # S454 (4.4): arrived by its bill's scan = on the way until Marg answers
    except sqlite3.Error:
        return out
    for item, packs, size, oid, created in rows:
        e = out.setdefault(pa.norm(item), dict(units=0, order_id=oid, sent=str(created or "")[:10]))
        e["units"] += int(packs or 0) * int(size or 1)
    return out


def _snapshot_inputs(con, today):
    pa = _pa()
    as_on, snap = pa._latest_snapshot(con)
    basis = _s454_basis(con)
    if basis == "count":                                       # S454 P3 (9.2): the shelf figure; Marg's figure kept beside it (marg_qty)
        snap = _s454_shelf_snap(con, snap)
    pace = pa._pace(con, snap, today)
    purch = pa._last_purchase(con)
    transit = pa._in_transit(con, today)
    onord = _on_order_units(con, today, "count")             # S454 P3B (18.4): an order that arrived by its scan is on the way ONCE, on marg
    if basis == "count":                                       # too -- in transit (purchase_app._in_transit), never again as on order                                       # an item ON the shelf figure carries what arrived and is not yet in Marg:
        transit, onord = _s454_count_way(con, today, snap, transit, onord)   # only what is still on the way counts; an item with no count as before
    for k, e in onord.items():
        t = transit.setdefault(k, dict(units=0, order_id=e["order_id"], vendor=""))
        t["units"] = int(t.get("units") or 0) + e["units"]
        t["on_way"] = e
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    return as_on, snap, pace, purch, transit, ortho


def days_left(on_hand, per_day):
    """THE ONE days-left figure (S593, charter 2; S308 iii): about how many days the shelf lasts at the line's own pace -- None when the pace
    is not known, 0 when nothing is on hand, else round(on_hand / per_day). The arithmetic darpan_kal._s485_days_left had; every row that
    carries days_left (_line_out, the carried-short row, Darpan's tab and his add door) calls this and nothing else."""
    try:
        oh, pd = float(on_hand), float(per_day)
    except (TypeError, ValueError):
        return None
    if oh <= 0:
        return 0
    return int(round(oh / pd)) if pd > 0 else None


def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):
    unit = pa._unit_word(s.get("packing"), s["pack_size"])
    strips = int(line["order_strips"])
    rounded = pa._staff_qty(strips, unit)
    rate_p = int(round(cost_unit * s["pack_size"]))
    cover_after = (round((s["qty"] + rounded * s["pack_size"]) / p["rate_per_day"], 1) if p["rate_per_day"] > 0 else None)
    why = list(line.get("why") or [])
    if rounded != strips:
        why.append("rounded to %d %ss (the owner's rule: 10, then tens)" % (rounded, unit))
    if why_extra:
        why.extend(why_extra)
    out = dict(item=s["item"], on_hand=it["on_hand"], qty=rounded, unit=unit, pack_size=s["pack_size"], packing=s.get("packing") or "",
               rate_p=rate_p, per_day=round(p["rate_per_day"], 2), cover_after=cover_after, cover_days=line.get("cover_days"),
               value_p=int(rounded * rate_p), confirm=bool(line.get("confirm")), why=why)
    out["days_left"] = days_left(out["on_hand"], out["per_day"])   # S593: the one figure, on the row the screens read
    return out


def plan(con, today=None, suppliers=None):
    """The fixed-day plan: per supplier (never the orthotics vendor, never a held item), the lines the rules would order today."""
    pa = _pa()
    today = today or _today()
    ensure(con)
    as_on, snap, pace, purch, transit, ortho = _snapshot_inputs(con, today)
    ortho_v = _ortho_norm(con)
    held = held_sets(con)
    irules = item_rules(con)
    min_line = _int_setting(con, "order.min_line_p")
    dead_after = _s470_days(con, "order.dead_after_days")       # S470 (B.8): a setting, at its present value
    no_supplier = []                                            # S470 (B.7): sold, never bought -- named, not dropped silently
    vendors = {}
    held_items = []
    rules_cache = {}
    for k, s in snap.items():
        if k in ortho:
            continue
        p = pace.get(k)
        if not p:
            continue
        lp = purch.get(k) or {}
        vn = lp.get("vendor")
        if not vn:                                             # S470 (B.7)
            no_supplier.append(dict(item=s["item"], on_hand=s["qty"], rate_per_day=round(p["rate_per_day"], 2)))
            continue
        if vn == ortho_v:
            continue
        if suppliers is not None and vn not in suppliers:
            continue
        hk = _k20(s["item"])
        if hk in held:
            held_items.append(dict(item=s["item"], vendor=lp.get("vendor_disp") or vn, why=held[hk]))
            continue
        r = rules_cache.get(vn) or rule_for(con, vn)
        rules_cache[vn] = r
        cost_pack = lp.get("rate_p")
        cost_unit = (cost_pack / float(s["pack_size"])) if cost_pack else 0
        if not cost_unit and _has(con, "stock_rate"):
            rr = con.execute("SELECT rate_p FROM stock_rate WHERE item=?", (s["item"],)).fetchone()
            cost_unit = rr[0] if rr else 0
        tr = transit.get(k)
        single = len(lp.get("suppliers") or ()) <= 1
        it = dict(item=s["item"], vendor=lp.get("vendor_disp") or vn, on_hand=s["qty"] + (tr["units"] if tr else 0), rate_per_day=p["rate_per_day"],
                  sell_days=p["sell_days"], peak_share=p["peak_share"], days_since_sale=p.get("days_since_sale", 0), pack_size=s["pack_size"],
                  cost_p=cost_unit, single_source=single, box=lp.get("box") or 0)
        cov = cover_days(con, r, single)
        cad = cov - pa.LEAD_DAYS - pa.SAFETY_DAYS - (pa.SINGLE_SOURCE_EXTRA_DAYS if single else 0)
        line = pa.plan_line(it, cad, dead_after)               # S470 (B.8)
        line["cover_days"] = cov
        _s644_shape(con, s, it, p, lp, r, line, cov, dead_after, cost_unit)   # S644: on levels the floor, the need, the lot; on fixed nothing
        extra = []
        ir = irules.get(k)
        if ir and ir["rule"] == "keep" and ir["value"]:
            want_units = int(ir["value"]) - it["on_hand"] - line["order_strips"] * s["pack_size"]
            if want_units > 0:
                add = int(math.ceil(want_units / float(s["pack_size"])))
                line["order_strips"] += add
                line["value_p"] = int(line["order_strips"] * s["pack_size"] * (cost_unit or 0))
                extra.append("keep-in-stock %s (your rule)" % _qw(int(ir["value"]), s))   # S430: strips / pcs, never 'units'
        if ir and ir["rule"] == "max_shelf" and ir["value"] and line["order_strips"] > 0:
            room = int(ir["value"]) - it["on_hand"]
            cap_strips = max(0, room // s["pack_size"])
            if line["order_strips"] > cap_strips:
                extra.append("max on shelf %s (your rule) -- cut from %s" % (_qw(int(ir["value"]), s), _qw(line["order_strips"] * int(s["pack_size"] or 1), s)))   # S430
                line["order_strips"] = cap_strips
        if line["order_strips"] <= 0:
            continue
        if min_line != pa.MIN_LINE_P and line["order_strips"] * s["pack_size"] * cost_unit < min_line and it["on_hand"] > 0:
            continue
        if tr and tr.get("on_way"):
            extra.append("%s on order #%d (sent %s), not yet received -- counted as stock" % (_qw(tr["on_way"]["units"], s), tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))   # S430
        lo = _line_out(pa, s, dict(on_hand=s["qty"]), line, cost_unit, p, extra)
        lo["vendor_norm"] = vn
        lo["marg_qty"] = s.get("marg_qty", s["qty"])            # S454 P3 (9.2): both figures, for the owner's eyes (no staff screen prints them)
        lo["shelf_qty"] = s["qty"] if "marg_qty" in s else None
        v = vendors.setdefault(vn, dict(vendor=it["vendor"], vendor_norm=vn, lines=[], total_p=0, rule=r))
        v["lines"].append(lo)
        v["total_p"] += lo["value_p"]
    for k, sh in pa._carried_shorts(con, today).items():
        vn = sh["vendor_norm"]
        if vn == ortho_v or (suppliers is not None and vn not in suppliers):
            continue
        s = snap.get(k) or {}
        unit = pa._unit_word(s.get("packing"), s.get("pack_size", 1))
        v = vendors.setdefault(vn, dict(vendor=sh["vendor"], vendor_norm=vn, lines=[], total_p=0, rule=rule_for(con, vn)))
        hit = next((l for l in v["lines"] if pa.norm(l["item"]) == k), None)
        if hit:
            add = pa._staff_qty(hit["qty"] + sh["shortfall"], unit)
            hit["why"].append("plus %d short-supplied on order #%d (%s) — carried" % (sh["shortfall"], sh["order_id"], sh["since"]))
            v["total_p"] += int((add - hit["qty"]) * hit["rate_p"])
            hit["qty"] = add
            hit["value_p"] = int(add * hit["rate_p"])
        else:
            qty = pa._staff_qty(sh["shortfall"], unit)
            size = int(s.get("pack_size") or 1)
            rate_p = int((purch.get(k) or {}).get("rate_p") or 0)
            v["lines"].append(dict(item=sh["item"], on_hand=int(s.get("qty") or 0), qty=qty, unit=unit, pack_size=size, packing=s.get("packing") or "",
                                   rate_p=rate_p, per_day=None, cover_after=None, cover_days=None, days_left=None, value_p=int(qty * rate_p), confirm=False,
                                   why=["short-supplied on order #%d (%s) — carried into this order" % (sh["order_id"], sh["since"])], vendor_norm=vn))
            v["total_p"] += int(qty * rate_p)
    for v in vendors.values():
        v["lines"].sort(key=lambda x: x["item"])
        r = v["rule"]
        mo = int(r.get("min_order_p") or _int_setting(con, "order.min_order_p"))
        out_of_stock = any(int(l["on_hand"] or 0) <= 0 for l in v["lines"])
        v["held"] = ""
        if v["total_p"] < mo and not out_of_stock:
            v["held"] = "under %s -- waits for the next order day" % _rs(mo)
        if int(r.get("paused") or 0):
            v["paused"] = r.get("pause_reason") or "paused"
        v["rule"] = dict(cadence=r["cadence"], order_days=r["order_days"], words=rule_words(con, r) if not r.get("_default") else "no rule yet -- weekly, Mondays")
        v["has_phone"] = bool(pa._wa_digits(pa._phone_for(con, v["vendor"])))
    no_supplier.sort(key=lambda x: x["item"])
    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors, held_items=held_items, no_supplier=no_supplier, engine=_s470_engine(),   # S470
                no_closing=_s470_missing(), inputs=_s470_inputs_note())   # S593: what the stock side stood on


def interim_plan(con, today=None):
    """Items whose cover would fall under lead + safety before their supplier's next order day: the shortfall to that day, per supplier.
    Nothing for a supplier ordering today; nothing on a blocked day; nothing before order.interim_from or while interim is off."""
    pa = _pa()
    today = today or _today()
    ensure(con)
    if _setting(con, "order.interim", "1") != "1":
        return dict(off="interim orders are off", vendors={})
    frm = _setting(con, "order.interim_from", "")
    if not frm or today.isoformat() < frm:
        return dict(off="interim orders start %s" % (_dmy(frm) if frm else "after the first week"), vendors={})
    as_on, snap, pace, purch, transit, ortho = _snapshot_inputs(con, today)
    ortho_v = _ortho_norm(con)
    held = held_sets(con)
    vendors = {}
    cache = {}
    for k, s in snap.items():
        if k in ortho:
            continue
        p = pace.get(k)
        if not p or p["rate_per_day"] <= 0:
            continue
        lp = purch.get(k) or {}
        vn = lp.get("vendor")
        if not vn or vn == ortho_v or _k20(s["item"]) in held:
            continue
        r = cache.get(vn) or rule_for(con, vn)
        cache[vn] = r
        if int(r.get("paused") or 0) or blocked_today(con, r, today) or is_order_day(con, r, today):
            continue
        F = next_order_day(con, r, today)
        lead, safety = int(r.get("lead_days") or 1), int(r.get("safety_days") or 3)
        tr = transit.get(k)
        on_hand = s["qty"] + (tr["units"] if tr else 0)
        cover = on_hand / p["rate_per_day"]
        horizon, strips = _s644_interim(con, r, s, p, on_hand, F, today, lead, safety)   # S644: fixed = today's test and arithmetic, line for line
        if strips <= 0:
            continue
        cost_pack = lp.get("rate_p")
        cost_unit = (cost_pack / float(s["pack_size"])) if cost_pack else 0
        why = ["cover %.1f days, the next %s order is %s -- interim for the shortfall" % (cover, _short(lp.get("vendor_disp") or vn), _dmy_short(F))]
        if tr and tr.get("on_way"):
            why.append("%s on order #%d (sent %s) counted as stock" % (_qw(tr["on_way"]["units"], s), tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))   # S430
        line = dict(order_strips=strips, cover_days=horizon, confirm=False, why=why)
        _s644_interim_keys(con, line, s, p)                    # S644: the model keys on the interim row (owner's eyes only)
        lo = _line_out(pa, s, dict(on_hand=s["qty"]), line, cost_unit, p)
        lo["vendor_norm"] = vn
        v = vendors.setdefault(vn, dict(vendor=lp.get("vendor_disp") or vn, vendor_norm=vn, lines=[], total_p=0, next_order_day=F.isoformat(), rule=dict(cadence=r["cadence"], order_days=r["order_days"]), _r=r))
        v["lines"].append(lo)
        v["total_p"] += lo["value_p"]
    for vn in list(vendors):
        v = vendors[vn]
        r = v.pop("_r")
        mo = int(r.get("min_order_p") or _int_setting(con, "order.min_order_p"))
        if v["total_p"] < mo and not any(int(l["on_hand"] or 0) <= 0 for l in v["lines"]):
            vendors.pop(vn)                                   # under the minimum order and nothing out of stock: it waits for the order day
            continue
        v["lines"].sort(key=lambda x: x["item"])
        v["held"] = ""
        v["has_phone"] = bool(pa._wa_digits(pa._phone_for(con, v["vendor"])))
    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors)


# ------------------------------------------------------------------ the day: prepare, merge, notices
def prepare_day(con, today=None, who="cron"):
    """09:00: one proposal per supplier due today (fixed) + the interim ones; idempotent (a row already there is left alone)."""
    pa = _pa()
    today = today or _today()
    ensure(con)
    due = []
    for r in rules(con):
        if is_order_day(con, r, today):
            due.append(r["supplier_norm"])
    made = dict(fixed=0, interim=0, held=0, skipped=0)
    fixed = plan(con, today, suppliers=set(due)) if due else dict(vendors={})
    for vn in due:
        v = fixed["vendors"].get(vn)
        if not v:
            made["skipped"] += 1
            continue
        if con.execute("SELECT 1 FROM order_proposal WHERE day=? AND supplier_norm=? AND kind='fixed'", (today.isoformat(), vn)).fetchone():
            continue
        carried = [x[0] for x in con.execute("SELECT day FROM order_proposal WHERE supplier_norm=? AND status='merged' AND merged_into=? ORDER BY day", (vn, today.isoformat()))]
        status = "held" if (v["held"] or v.get("paused")) else "open"
        reason = v.get("paused") or v["held"] or ""
        con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at, carried_from) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (today.isoformat(), vn, v["vendor"], "fixed", status, json.dumps(v["lines"], ensure_ascii=False), v["total_p"], reason, now_iso(), ",".join(carried) or None))
        made["held" if status == "held" else "fixed"] += 1
    ip = interim_plan(con, today)
    for vn, v in ip.get("vendors", {}).items():
        if con.execute("SELECT 1 FROM order_proposal WHERE day=? AND supplier_norm=? AND kind='interim'", (today.isoformat(), vn)).fetchone():
            continue
        con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (today.isoformat(), vn, v["vendor"], "interim", "open", json.dumps(v["lines"], ensure_ascii=False), v["total_p"],
                     "Beech ka order -- agla %s order %s ko" % (_short(v["vendor"]), _dmy(v["next_order_day"])), now_iso()))
        made["interim"] += 1
    con.commit()
    _s644_stamp_day(con, today)                               # S644 (B.2a): what the list was made from, in order_notice
    _ = pa
    return made


def nightly(con, today=None, who="cron"):
    """05:30: yesterday's unsent proposals merge into each supplier's next order day (one order, never two); on the 1st the
    cadences re-seed (owner-set fields untouched); the new-items log refreshes."""
    today = today or _today()
    ensure(con)
    merged = 0
    for p in con.execute("SELECT id, supplier_norm, day FROM order_proposal WHERE status IN ('open','darpan_ok') AND day<?", (today.isoformat(),)).fetchall():   # S485
        r = rule_for(con, p[1])
        nxt = next_order_day(con, r, today - dt.timedelta(days=1))
        con.execute("UPDATE order_proposal SET status='merged', merged_into=? WHERE id=?", (nxt.isoformat(), p[0]))
        merged += 1
    reseeded = 0
    if today.day == 1 or not con.execute("SELECT 1 FROM order_supplier_rule LIMIT 1").fetchone():
        reseeded = reseed(con, today, who)
    try:
        _pa()._log_new_items(con, today.strftime("%Y-%m"))
    except Exception:                                         # noqa: BLE001
        pass
    con.commit()
    return dict(merged=merged, reseeded=reseeded)


def day_state(con, today=None):
    """Today's proposals with their state, the contextual text, the freeze and the pauses."""
    today = today or _today()
    ensure(con)
    rows = [dict(r) for r in con.execute("SELECT * FROM order_proposal WHERE day=? ORDER BY kind DESC, vendor", (today.isoformat(),))]
    for r in rows:
        try:
            r["lines"] = json.loads(r["lines"] or "[]")
        except ValueError:
            r["lines"] = []
        r["short"] = _short(r["vendor"])
        r["sent_text"] = _stamp(r["sent_at"]) if r.get("sent_at") else ""
        r["kind_hi"] = "Beech ka order" if r["kind"] == "interim" else "Aaj ka order"
    live = [r for r in rows if r["status"] in ("open", "sent")]
    sent = [r for r in live if r["status"] == "sent"]
    unsent = [r for r in live if r["status"] == "open"]
    text = ""
    if live:
        if unsent:
            text = "Aaj %d order: %d bheja, %d baaki — %s" % (len(live), len(sent), len(unsent), ", ".join(r["short"] for r in unsent))
        else:
            text = "Aaj ke %d order sab bheje ja chuke." % len(live)
    stuck = [dict(r) for r in con.execute("SELECT id, day, vendor, merged_into FROM order_proposal WHERE status='merged' AND merged_into>=? ORDER BY day", (today.isoformat(),))]
    return dict(ok=True, day=today.isoformat(), day_text=_dmy_short(today), n=len(live), sent=len(sent), unsent=len(unsent), text=text,
                proposals=rows, frozen=_frozen(con), interim_from=_setting(con, "order.interim_from", ""), interim_on=_setting(con, "order.interim", "1") == "1",
                rules_ok=_rules_ok(con), merged_ahead=[dict(vendor=_short(s["vendor"]), day=_dmy(s["day"]), into=_dmy(s["merged_into"])) for s in stuck],
                holidays=[dict(r) for r in con.execute("SELECT day, note, set_by FROM order_holiday WHERE day>=? ORDER BY day LIMIT 20", (today.isoformat(),))],
                url="/finance/porders")


def day_summary(con):
    """Darpan's card line and any other page: {ok, n, sent, unsent, text, url}. Fail-soft."""
    try:
        if _s454_source(con) == "marg_sheet":                 # S454: while the sheet decides, the sheet's suppliers still to be ordered
            import order_sheet                                # noqa: PLC0415
            return order_sheet.day_summary(con)
        d = day_state(con)
        if _s454_source(con) == "darpan":                     # S485 (D677): open (his to make pakka) and darpan_ok (reception's to order) both still to go
            rows = [r for r in d["proposals"] if r["status"] in ("open", "darpan_ok", "sent")]
            un = [r for r in rows if r["status"] != "sent"]
            text = (("Aaj %d order: %d bheja, %d baaki — %s" % (len(rows), len(rows) - len(un), len(un), ", ".join(r["short"] for r in un))) if un
                    else ("Aaj ke %d order sab bheje ja chuke." % len(rows) if rows else ""))
            return dict(ok=True, n=len(rows), sent=len(rows) - len(un), unsent=len(un), text=text, frozen=bool(d["frozen"]), url=d["url"])
        return dict(ok=True, n=d["n"], sent=d["sent"], unsent=d["unsent"], text=d["text"], frozen=bool(d["frozen"]), url=d["url"])
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, n=0, sent=0, unsent=0, text="", error=str(e)[:80])


def _stamp(ts):
    try:
        return dt.datetime.fromisoformat(str(ts)[:19]).strftime("%d-%m-%Y %H:%M") + " IST"
    except (TypeError, ValueError):
        return str(ts or "")


def _rules_ok(con):
    try:
        import porders                                        # noqa: PLC0415
        return bool(porders._rules_ok(con))
    except Exception:                                         # noqa: BLE001
        return False


def notice_text(con, today, slot):
    d = day_state(con, today)
    if not d["n"]:
        return None
    if slot == "prepare":
        names = ", ".join(r["short"] for r in d["proposals"] if r["status"] in ("open", "sent"))
        inter = sum(1 for r in d["proposals"] if r["kind"] == "interim" and r["status"] in ("open", "sent"))
        return "Aaj %d order tayyar — %s%s. Purchase orders kholiye." % (d["n"], names, (" (%d beech ka)" % inter) if inter else "")
    if not d["unsent"]:
        return None
    return d["text"]


def _push(user, payload):
    """One Web Push to every phone this login subscribed (portal_push's own store and key), or the stub file for the walk."""
    stub = os.environ.get("ORDER_PUSH_STUB", "")
    if stub:
        with open(stub, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(dict(user=user, payload=payload), ensure_ascii=False) + "\n")
        return 1, 0
    if PORTAL_DIR not in sys.path:
        sys.path.insert(0, PORTAL_DIR)
    import ring_common as rc                                  # noqa: PLC0415
    return rc.push_user(user, payload)


def send_notice(con, today, slot, who="cron", to=None, text=None, url=None, title=None):
    """09:00 / 12:00 / 15:00 / 17:00: the contextual text to the ordering team's phones; silent when all are sent; once per slot."""
    ensure(con)
    key = {"prepare": "0900", "remind12": "1200", "remind15": "1500", "remind17": "1700"}.get(slot, slot)
    if con.execute("SELECT 1 FROM order_notice WHERE day=? AND slot=?", (today.isoformat(), key)).fetchone():
        return dict(ok=True, already=True, slot=key)
    text = text or notice_text(con, today, "prepare" if slot == "prepare" else "remind")
    if not text:
        return dict(ok=True, silent=True, slot=key)
    if to is None:
        to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip()]
    payload = dict(kind="order", title=title or "Purchase orders", body=text, url=url or "/finance/porders", tag="porders", ttl=3600, renotify=True, ts=int(dt.datetime.now().timestamp() * 1000))
    sent = {}
    for u in to:
        try:
            pl = dict(payload, url="/finance/darpan/kal#order") if (url is None and u == "darpan") else payload   # S958: his page, not reception's
            s, f = _push(u, pl)
            sent[u] = dict(sent=s, failed=f)
        except Exception as e:                                # noqa: BLE001
            sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
    con.execute("INSERT OR IGNORE INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (today.isoformat(), key, text, json.dumps(sent), now_iso()))
    con.commit()
    return dict(ok=True, slot=key, text=text, sent=sent)


def darpan_list_time(con):
    """S485 (D677): order.darpan_list_time as HH:MM -- a ':x0' minute, because the tick runs every ten minutes and matches the minute
    exactly; anything else reads as 09:30."""
    v = str(_setting(con, "order.darpan_list_time") or "").strip()
    return v if re.match(r"^([01]\d|2[0-3]):[0-5]0$", v) else "09:30"


def darpan_list_open(con, now=None):
    """S485: has the day's list opened on Darpan's tab? (ORDER_CLOCK = HH:MM is a walk's clock.)"""
    hm = os.environ.get("ORDER_CLOCK", "") or (now or dt.datetime.now()).strftime("%H:%M")
    return hm >= darpan_list_time(con)


def _s485_notice(con, today):
    """S485 (D677): the one notice of the list's hour, to Darpan only, once a day (order_notice UNIQUE(day, slot)); silent unless
    order.source = darpan and a proposal of today is open."""
    src = _s454_source(con)
    if src != "darpan":
        return dict(ok=True, silent=True, slot="0930", why="order.source = %s" % src)
    n = sum(1 for p in con.execute("SELECT supplier_norm FROM order_proposal WHERE day=? AND status='open'", (today.isoformat(),)).fetchall()
            if not int(rule_for(con, p[0]).get("paused") or 0))
    if not n or _frozen(con):
        return dict(ok=True, silent=True, slot="0930", why="no open proposal")
    to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip().lower() == "darpan"]
    return send_notice(con, today, "0930", to=to, text="\u0906\u091c \u0915\u093e \u0911\u0930\u094d\u0921\u0930 \u0924\u0948\u092f\u093e\u0930 \u0939\u0948 \u2014 "
                       "\u0915\u0932 \u0915\u093e \u0939\u093f\u0938\u093e\u092c \u092a\u0947\u091c \u092a\u0930 \u0926\u0947\u0916\u093f\u090f",
                       url="/finance/darpan/kal#order", title="\u0906\u091c \u0915\u093e \u0911\u0930\u094d\u0921\u0930")


def _s500_reports(con, out, now=None):
    """S500 (D694): the morning reports' watch rides the ten-minute tick -- at most one message a day to the owner about each of the two
    reports (wrong on the second try, or not right by the hour).  Never raises; its result is one more key of the tick's own answer."""
    try:
        import reports_watch                                  # noqa: PLC0415
        r = reports_watch.tick(con)
    except Exception as e:                                    # noqa: BLE001
        r = "error: %s" % str(e)[:80]
    if isinstance(out, dict):
        out["reports"] = r
    return out


def tick(con, now=None):
    """The one cron line's worker (S454: every ten minutes, 05:00-21:50): 05:30 nightly · 09:00 prepare (its notice only on
    order.source = system) · the ONE reminder of the day at order.remind_times; and on every tick the order sheet's own work that must
    not wait for a page (order_sheet.cron_pass: the sheets the door took, the WhatsApp line, Marg's clearing, the bill-scan tie)."""
    now = now or dt.datetime.now()
    forced = os.environ.get("ORDER_TICK", "")
    slot = forced
    if not slot:
        hm = (now.hour, now.minute)
        if hm == SLOTS["nightly"]:
            slot = "nightly"
        elif hm == SLOTS["prepare"]:
            slot = "prepare"
        elif "%02d:%02d" % hm == darpan_list_time(con):       # S485 (D677): the list opens on Darpan's tab
            slot = "0930"
    today = _today()
    s454 = _s454_pass(con)                                    # S454: before the notices, so the reminder names what is still due
    _s500_reports(con, s454)                                  # S500: the morning reports' watch (reports_watch.tick)
    try:
        _s644_relist(con, today, now)                         # S644 (B.2a): on levels, the untouched list made again when an input moved
    except Exception:                                         # noqa: BLE001 -- never stops the tick
        pass
    if slot == "nightly":
        return dict(slot=slot, s454=s454, **nightly(con, today))
    if slot == "prepare":
        made = prepare_day(con, today)
        return dict(slot=slot, made=made, s454=s454, notice=(send_notice(con, today, "prepare") if _s454_source(con) == "system"
                                                              else dict(ok=True, silent=True, slot="0900", why="order.source = %s" % _s454_source(con))))
    if slot == "0930":                                        # S485 (D677)
        return dict(slot=slot, s454=s454, notice=_s485_notice(con, today))
    if slot.startswith("remind"):                             # a walk's forced slot: the one reminder at its own hour; 12:00 / 15:00 are gone
        return dict(slot=slot, s454=s454, notice=_s454_remind(con, today, now, force=slot))
    return dict(slot="none", s454=s454, notice=_s454_remind(con, today, now))


# ------------------------------------------------------------------ sending a proposal (the S403 wa.me flow)
def send_proposal(con, u, pid, lines_in):
    pa = _pa()
    ensure(con)
    fr = _frozen(con)
    if fr:
        return dict(ok=False, error="frozen", message="Medicine ordering band hai: %s (%s)" % (fr.get("reason") or "", _stamp(fr.get("at")))), 423
    if not _rules_ok(con):
        return dict(ok=False, error="rules_pending", message="Doctor sahab ke rules ka intezaar."), 403
    p = con.execute("SELECT * FROM order_proposal WHERE id=?", (pid,)).fetchone()
    if not p:
        return dict(ok=False, error="no_such_proposal"), 404
    p = dict(p)
    if p["status"] == "sent":
        return dict(ok=True, already=True, order_id=p["sent_order_id"], message="Yeh order bheja ja chuka hai (%s, %s)." % (_stamp(p["sent_at"]), p["sent_by"] or "")), 200
    if p["status"] not in ("open", "held", "darpan_ok"):       # S485
        return dict(ok=False, error="not_open", message="Yeh order ab %s hai." % p["status"]), 409
    if p["status"] == "open" and _s454_source(con) == "darpan":   # S593 (F-738, S486 Part A): on darpan only the list he made pakka goes out
        return dict(ok=False, error="not_confirmed", message="Darpan ne yeh list abhi pakka nahi ki."), 409
    r = rule_for(con, p["supplier_norm"])
    if int(r.get("paused") or 0):
        return dict(ok=False, error="paused", message="%s ka order roka hua hai: %s" % (_short(p["vendor"]), r.get("pause_reason") or "")), 409
    try:
        base = {l["item"]: l for l in json.loads(p["lines"] or "[]") if not l.get("held")}   # S485: both loops below skip a held line
    except ValueError:
        base = {}
    clean = []
    for ln in (lines_in if isinstance(lines_in, list) else []):
        if not isinstance(ln, dict):
            continue
        item = str(ln.get("item") or "").strip()
        try:
            qty = int(ln.get("qty") or 0)
        except (TypeError, ValueError):
            qty = 0
        b = base.get(item)
        if not b or qty <= 0:
            continue
        clean.append(dict(item=item, qty=qty, pack_size=b.get("pack_size") or 1, packing=b.get("packing") or "", rate_p=b.get("rate_p") or 0,
                          on_hand=b.get("on_hand"), per_day=b.get("per_day"), cover_after=b.get("cover_after")))
    if lines_in is None:
        clean = [dict(item=b["item"], qty=b["qty"], pack_size=b.get("pack_size") or 1, packing=b.get("packing") or "", rate_p=b.get("rate_p") or 0,
                      on_hand=b.get("on_hand"), per_day=b.get("per_day"), cover_after=b.get("cover_after")) for b in base.values()]
    if not clean:
        return dict(ok=False, error="malformed", message="Kuch order karne ko nahi hai."), 400
    recent = con.execute("SELECT id, created_at FROM purchase_order WHERE vendor=? AND status IN ('sent','received') ORDER BY id DESC LIMIT 1", (p["vendor"],)).fetchone()
    if recent and _within(recent[1]) and p["kind"] == "fixed":
        return dict(ok=False, error="already", already=True, order_id=recent[0], message="Is stockist ko abhi order gaya hai (%s)." % _stamp(recent[1])), 409
    resp = pa._staff_send(con, u, dict(vendor=p["vendor"], lines=clean))
    rr, code = (resp if isinstance(resp, tuple) else (resp, 200))
    j = rr.get_json() or {}
    if code != 200 or not j.get("ok"):
        return dict(ok=False, error=j.get("error") or "send_failed", message=j.get("message") or "Order nahi bana."), (code if code != 200 else 500)
    who = _who(u)
    con.execute("UPDATE purchase_order SET section=?, note=? WHERE id=?", ("Medicines", "whatsapp · S410 %s %s" % (p["kind"], p["day"]), j["order_id"]))
    con.execute("UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=?, lines=? WHERE id=?",
                (j["order_id"], now_iso(), who, json.dumps([dict(base.get(c["item"], {}), qty=c["qty"]) for c in clean], ensure_ascii=False), pid))
    con.execute("UPDATE order_proposal SET status='sent', sent_order_id=?, sent_at=?, sent_by=? WHERE supplier_norm=? AND status='merged' AND merged_into<=?",
                (j["order_id"], now_iso(), who, p["supplier_norm"], p["day"]))
    try:
        pa._audit(con, who, "porders_day_sent", j["order_id"], dict(vendor=p["vendor"], kind=p["kind"], day=p["day"], lines=len(clean)))
    except Exception:                                         # noqa: BLE001
        pass
    con.commit()
    return dict(ok=True, order_id=j["order_id"], wa_url=j["wa_url"], sent_text=_stamp(now_iso()), by=who, lines=[dict(item=c["item"], qty=c["qty"]) for c in clean]), 200


def _within(ts, minutes=REPEAT_MIN):
    try:
        return (dt.datetime.now() - dt.datetime.fromisoformat(str(ts)[:19])) <= dt.timedelta(minutes=minutes)
    except (TypeError, ValueError):
        return False


# ------------------------------------------------------------------ the owner's blocks
def oos_both_ends(con, today=None):
    """Items out or thin at the pharmacy (cover < safety) whose supplier said 'Nahi mila' on the last order line for the item;
    cleared by a purchase landing after that, or another supplier's line supplying it."""
    pa = _pa()
    today = today or _today()
    as_on, snap = pa._latest_snapshot(con)
    pace = pa._pace(con, snap, today)
    safety = _int_setting(con, "order.safety_days")
    out = []
    try:
        rows = con.execute("SELECT l.id, l.item, l.missing, l.supplied, l.arrived_at, o.vendor, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE o.status IN ('sent','received') ORDER BY l.id DESC").fetchall()
    except sqlite3.Error:
        return out
    seen = set()
    for lid, item, missing, supplied, arrived_at, vendor, created in rows:
        k = pa.norm(item)
        if k in seen:
            continue
        if supplied is None and not missing:
            continue                                          # an open line is no answer yet; the last ANSWERED line decides
        seen.add(k)
        if not missing:
            continue
        s = snap.get(k)
        if not s:
            continue
        p = pace.get(k) or {}
        rate = p.get("rate_per_day") or 0
        cover = (s["qty"] / rate) if rate > 0 else (999 if s["qty"] > 0 else 0)
        if s["qty"] > 0 and cover >= safety:
            continue
        since = str(arrived_at or created or "")[:10]
        landed = con.execute("SELECT 1 FROM purchase_line l WHERE l.item=? AND l.bill_date>=? AND l.direction='PURCHASE' AND " + pa.EFF_LINE + " LIMIT 1", (item, since)).fetchone()
        if landed:
            continue
        out.append(dict(item=s["item"], qty=s["qty"], packing=s["packing"], cover_days=(round(cover, 1) if rate > 0 else None), vendor=vendor,
                        vendor_short=_short(vendor), said_no=_dmy(since), line_id=lid))
    out.sort(key=lambda x: (x["qty"], x["item"]))
    return out


def new_items(con, month=None):
    """Every item whose FIRST-EVER purchase line falls in the month: name · salt · supplier · manufacturer · MRP · purchase rate · first bill --
    manufacturer and MRP as the spine holds them from Marg's own exports (the lane named), 'not in export' where absent; never guessed."""
    pa = _pa()
    month = month or _today().strftime("%Y-%m")
    try:
        pa._log_new_items(con, month)
    except Exception:                                         # noqa: BLE001
        pass
    rows = []
    try:
        firsts = con.execute("SELECT l.item, MIN(l.bill_date) AS f FROM purchase_line l WHERE l.bill_date IS NOT NULL AND l.direction='PURCHASE' AND l.line_type='ITEMWISE' AND "
                             + pa.EFF_LINE + " GROUP BY l.item HAVING substr(f,1,7)=? ORDER BY f, l.item", (month,)).fetchall()
    except sqlite3.Error:
        return []
    names = {r[0]: r[1] for r in con.execute("SELECT supplier_norm, MAX(supplier) FROM purchase_bill GROUP BY supplier_norm")}
    salts = {}
    if _has(con, "purchase_salt_marg"):
        salts = {r[0]: r[1] for r in con.execute("SELECT item_norm, salt FROM purchase_salt_marg")}
    sp = None
    try:
        sp = sqlite3.connect("file:%s?mode=ro" % os.path.join(SPINE_DIR, "spine.db"), uri=True)
    except sqlite3.Error:
        sp = None
    for item, f in firsts:
        ln = con.execute("SELECT supplier_norm, packing, rate_p, purchase_rate_p, bill_no FROM purchase_line l WHERE l.item=? AND l.bill_date=? AND l.direction='PURCHASE' AND " + pa.EFF_LINE + " ORDER BY l.id LIMIT 1", (item, f)).fetchone()
        sup = names.get(ln[0]) if ln else ""
        rate_p = (ln[3] or ln[2]) if ln else None
        facts = {}
        if sp is not None:
            try:
                for fact, value, as_on, fam in sp.execute("SELECT f.fact, f.value, f.as_on, COALESCE(e.family,'') FROM sp_item_fact f LEFT JOIN sp_export e ON e.md5=f.source_md5 "
                                                          "WHERE (f.name=? OR f.name LIKE ?) AND f.fact IN ('company','mrp') ORDER BY f.as_on", (item, item + "%")):
                    if value not in (None, "", "0", "0.0"):
                        facts[fact] = (value, as_on, fam)
            except sqlite3.Error:
                pass
        rows.append(dict(item=item, first=f, first_text=_dmy(f), supplier=sup or (ln[0] if ln else ""), supplier_short=_short(sup or (ln[0] if ln else "")),
                         packing=(ln[1] if ln else ""), rate_p=rate_p, rate_rs=_rs(rate_p) if rate_p else "not in export", bill_no=(ln[4] if ln else ""),
                         salt=salts.get(pa.norm(item)) or "", manufacturer=(facts["company"][0] if "company" in facts else "not in export"),
                         manufacturer_lane=(facts["company"][2] if "company" in facts else ""),
                         mrp=(("₹" + facts["mrp"][0].rstrip("0").rstrip(".")) if "mrp" in facts else "not in export"), mrp_lane=(facts["mrp"][2] if "mrp" in facts else "")))
    if sp is not None:
        sp.close()
    return rows


def _month_spend(con, today):
    """Per supplier: this month to date against the 90-day monthly average, pro-rated to the day."""
    pa = _pa()
    since = (today - dt.timedelta(days=90)).isoformat()
    m0 = today.replace(day=1).isoformat()
    out = {}
    avg = {r[0]: int((r[1] or 0) / 3.0) for r in con.execute("SELECT b.supplier_norm, SUM(b.amount_p) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND " + pa.EFF_BILL + " GROUP BY b.supplier_norm", (since, today.isoformat()))}
    mtd = {r[0]: int(r[1] or 0) for r in con.execute("SELECT b.supplier_norm, SUM(b.amount_p) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND " + pa.EFF_BILL + " GROUP BY b.supplier_norm", (m0, today.isoformat()))}
    days_in = ((today.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - today.replace(day=1)).days
    for sn, a in avg.items():
        exp = a * today.day / float(days_in)
        got = mtd.get(sn, 0)
        out[sn] = dict(avg_month_p=a, expected_p=int(exp), mtd_p=got, pct=((got - exp) / exp * 100.0) if exp > 0 else None)
    return out


def kedar_review(con, today):
    """The Kedar ramp: on/after review_on, what twice-weekly held -- the peak on-hand of the big four since go-live, in boxes of 10 strips."""
    r = con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (KEDAR,)).fetchone()
    if not r or not r["review_on"] or today.isoformat() < r["review_on"]:
        return None
    pa = _pa()
    gl = _setting(con, "order.go_live", "") or today.isoformat()
    big = [x[0] for x in con.execute("SELECT l.item, SUM(l.qty) q FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_date>=? AND l.direction='PURCHASE' AND " + pa.EFF_LINE +
                                     " GROUP BY l.item ORDER BY q DESC LIMIT 4", (KEDAR, (today - dt.timedelta(days=90)).isoformat()))]
    peak, peak_day = 0, ""
    if big and _has(con, "stock_snapshot"):
        for as_on, in con.execute("SELECT DISTINCT as_on FROM stock_snapshot"):
            k = pa._as_on_key(as_on)
            iso = "%04d-%02d-%02d" % k if k[0] else ""
            if not iso or iso < gl:
                continue
            boxes = 0.0
            for item, qty, ps in con.execute("SELECT item, qty, pack_size FROM stock_snapshot WHERE as_on=? AND item IN (%s)" % ",".join("?" * len(big)), [as_on] + big):
                boxes += (int(qty or 0) / float(max(1, int(ps or 1)))) / 10.0
            if boxes > peak:
                peak, peak_day = boxes, iso
    return dict(review_on=r["review_on"], target=r["review_target"] or "weekly", cadence=r["cadence"], big=big, peak_boxes=int(round(peak)), peak_day=peak_day,
                text="Kedar review (%s): twice-weekly since %s held the big four at a peak of %d boxes (%s). Move Kedar to %s?"
                     % (_dmy(r["review_on"]), _dmy(gl), int(round(peak)), _dmy(peak_day) if peak_day else "no snapshot yet", r["review_target"] or "weekly"))


def needs_you_lines(con):
    """The owner's Needs you, only: an order still unsent on its next order day · a month running above average · the Kedar review · the freeze ·
    the Sunday one-liner. NEEDS_YOU_WITHOUT_S410=1 is set only by an older kit's frozen walk."""
    if os.environ.get("NEEDS_YOU_WITHOUT_S410") == "1":
        return []
    out = []
    try:
        ensure(con)
        today = _today()
        for p in (con.execute("SELECT supplier_norm, vendor, MIN(day), merged_into FROM order_proposal WHERE status='merged' AND merged_into<=? GROUP BY supplier_norm",
                              (today.isoformat(),)) if _s454_source(con) in ("system", "darpan") else ()):    # S454: on marg_sheet the proposals reach no one (S485: darpan as system)
            sent_since = con.execute("SELECT 1 FROM order_proposal WHERE supplier_norm=? AND status='sent' AND day>=? LIMIT 1", (p[0], p[2])).fetchone()
            if not sent_since:
                out.append(dict(cls="warn", target="porders", text="Order not sent: %s — due %s, still open on %s" % (_short(p[1]), _dmy(p[2]), _dmy(p[3]))))
        pct = _int_setting(con, "order.spend_alert_pct")
        if today.day >= 10:
            ortho_v = _ortho_norm(con)
            minb = _int_setting(con, "order.min_bills_for_rhythm")
            steady = {r[0] for r in con.execute("SELECT supplier_norm FROM order_supplier_rule WHERE COALESCE(bills90,0)>=?", (minb,))}
            for sn, s in _month_spend(con, today).items():
                if sn == ortho_v or sn not in steady:          # never the orthotics vendor (S403's); a supplier of 1-2 bills has no pace to run above
                    continue
                if s["pct"] is not None and s["pct"] > pct and s["avg_month_p"] >= 100000:
                    out.append(dict(cls="warn", target="porders", text="%s this month: %s so far, %d%% above its 90-day pace (%s a month)"
                                    % (_short(sn), _rs(s["mtd_p"]), int(round(s["pct"])), _rs(s["avg_month_p"]))))
        kr = kedar_review(con, today)
        if kr:
            out.append(dict(cls="info", target="porders", text=kr["text"], review_supplier=KEDAR, review_target=kr["target"]))
        fr = _frozen(con)
        if fr:
            out.append(dict(cls="info", target="porders", text="Medicine ordering is frozen since %s: %s" % (_stamp(fr.get("at")), fr.get("reason") or "")))
        if today.weekday() == 6 and _setting(con, "order.sunday_line", "1") == "1":
            wk = (today - dt.timedelta(days=6)).isoformat()
            n = con.execute("SELECT COUNT(*), COALESCE(SUM(total_p),0) FROM purchase_order WHERE section='Medicines' AND status IN ('sent','received') AND created_at>=?", (wk,)).fetchone()
            opn = con.execute("SELECT COUNT(*) FROM purchase_order WHERE section='Medicines' AND status='sent' AND created_at>=?", (wk,)).fetchone()[0]
            if n and n[0]:
                out.append(dict(cls="info", target="porders", text="This week: %d medicine order%s, %s, %s" % (n[0], "" if n[0] == 1 else "s", _rs(n[1]), "all arrived" if not opn else "%d still open" % opn)))
    except Exception:                                         # noqa: BLE001
        pass
    return out


# ------------------------------------------------------------------ the owner's edits
def set_rule(con, who, supplier_norm, field, value):
    ensure(con)
    r = con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone()
    if not r:
        return dict(ok=False, error="no_such_supplier"), 404
    r = dict(r)
    upd = {}
    if field == "move_to":
        target = str(value or "").strip().lower()
        if target == "weekly":
            upd = dict(cadence="weekly", order_days="MON", review_on=None, note=(r.get("note") or "") + " · moved to weekly by %s %s" % (who, _dmy(_today())))
        elif target == "custom":
            upd = dict(cadence="custom", order_days="MON,FRI", note=(r.get("note") or "") + " · back to Mon + Fri by %s %s" % (who, _dmy(_today())))
        else:
            return dict(ok=False, error="bad_value"), 400
    elif field in RULE_FIELDS:
        v = value
        if field == "cadence":
            if v not in CADENCES:
                return dict(ok=False, error="bad_value", message="weekly / fortnightly / monthly / custom"), 400
            if v != "custom":
                upd["order_days"] = str(r.get("order_days") or "MON").split(",")[0] or "MON"
            if v in ("weekly", "custom"):
                upd["cover_cap_days"] = _int_setting(con, "order.cap_weekly")
            elif v == "fortnightly":
                upd["cover_cap_days"] = _int_setting(con, "order.cap_fortnightly")
            else:
                upd["cover_cap_days"] = _int_setting(con, "order.cap_monthly")
        elif field in ("order_days", "blocked_days"):
            days = [x.strip().upper() for x in re.split(r"[,\s]+", str(v or "")) if x.strip()]
            if any(d not in DOW for d in days) or (field == "order_days" and not days):
                return dict(ok=False, error="bad_value", message="MON..SUN, comma-separated"), 400
            v = ",".join(days)
        elif field in ("lead_days", "safety_days", "cover_cap_days", "single_source_extra", "paused", "min_order_p"):
            try:
                v = int(v)
            except (TypeError, ValueError):
                return dict(ok=False, error="bad_value"), 400
            if field in ("lead_days", "safety_days", "cover_cap_days") and not (0 <= v <= 60):
                return dict(ok=False, error="bad_value"), 400
            if field in ("single_source_extra", "paused"):
                v = 1 if v else 0
        elif field in ("anchor_date", "review_on"):
            if v:
                try:
                    dt.date.fromisoformat(str(v)[:10])
                except ValueError:
                    return dict(ok=False, error="bad_value", message="a date, YYYY-MM-DD"), 400
            v = str(v)[:10] or None
        else:
            v = str(v or "")[:200] or None
        upd[field] = v
        if field == "paused" and not v:
            upd["pause_reason"] = None
    else:
        return dict(ok=False, error="bad_field"), 400
    owner = _owner_fields(r) | set(upd.keys())
    for k, v in upd.items():
        _audit(con, who, supplier_norm, k, r.get(k), v)
    sets = ", ".join("%s=?" % k for k in upd) + ", owner_fields=?, updated_at=?"
    con.execute("UPDATE order_supplier_rule SET %s WHERE supplier_norm=?" % sets, list(upd.values()) + [json.dumps(sorted(owner)), now_iso(), supplier_norm])
    con.commit()
    nr = dict(con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone())
    return dict(ok=True, supplier=supplier_norm, changed=upd, words=rule_words(con, nr)), 200


def set_freeze(con, who, on, reason):
    ensure(con)
    if on:
        rec = dict(by=who, at=now_iso(), reason=str(reason or "").strip()[:160] or "frozen by the owner")
        _set_setting(con, "order.freeze", json.dumps(rec), who)
    else:
        _set_setting(con, "order.freeze", "", who)
    con.commit()
    return dict(ok=True, frozen=_frozen(con))


def set_holiday(con, who, day, note, remove=False):
    ensure(con)
    try:
        d = dt.date.fromisoformat(str(day)[:10])
    except (TypeError, ValueError):
        return dict(ok=False, error="bad_date"), 400
    if remove:
        con.execute("DELETE FROM order_holiday WHERE day=?", (d.isoformat(),))
        _audit(con, who, None, "holiday", d.isoformat(), "removed")
    else:
        con.execute("INSERT INTO order_holiday (day, note, set_by, set_at) VALUES (?,?,?,?) ON CONFLICT(day) DO UPDATE SET note=excluded.note, set_by=excluded.set_by, set_at=excluded.set_at",
                    (d.isoformat(), str(note or "")[:80], who, now_iso()))
        _audit(con, who, None, "holiday", None, "%s %s" % (d.isoformat(), note or ""))
    con.commit()
    return dict(ok=True, holidays=[dict(r) for r in con.execute("SELECT day, note, set_by FROM order_holiday ORDER BY day")]), 200


def owner_state(con, today=None):
    today = today or _today()
    ensure(con)
    st = {k: _setting(con, k, "") for k in SETTINGS}
    cand = candidates(con, today)
    oos = oos_both_ends(con, today)
    ni = new_items(con, today.strftime("%Y-%m"))
    return dict(ok=True, kit=KIT, version=VERSION, today=today.isoformat(), rules=rules(con), settings=st, frozen=_frozen(con), rules_ok=_rules_ok(con),
                candidates=cand, item_rules=sorted(item_rules(con).values(), key=lambda x: x["item"]), lists=load_lists(),
                holidays=[dict(r) for r in con.execute("SELECT day, note, set_by FROM order_holiday WHERE day>=? ORDER BY day", ((today - dt.timedelta(days=30)).isoformat(),))],
                oos=oos, oos_n=len(oos), new_items_n=len(ni), month=today.strftime("%Y-%m"), day=day_state(con, today),
                kedar_review=kedar_review(con, today), notice_to=st["order.notice_to"],
                audit=[dict(r) for r in con.execute("SELECT at, who, supplier_norm, field, old, new FROM order_rule_audit ORDER BY id DESC LIMIT 40")])


# ------------------------------------------------------------------ routes
def _auth():
    import porders                                            # noqa: PLC0415
    return porders._auth()


@bp.route("/finance/porders/api/rules/state")
def api_rules_state():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    return jsonify(**owner_state(con))


@bp.route("/finance/porders/api/rules/set", methods=["POST"])
def api_rules_set():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    body, code = set_rule(con, _who(u), str(b.get("supplier") or ""), str(b.get("field") or ""), b.get("value"))
    return jsonify(**body), code


@bp.route("/finance/porders/api/rules/item", methods=["POST"])
def api_rules_item():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    try:
        val = int(b["value"]) if b.get("value") not in (None, "") else None
    except (TypeError, ValueError):
        return jsonify(ok=False, error="bad_value"), 400
    body, code = set_item_rule(con, _who(u), str(b.get("item") or "").strip(), str(b.get("rule") or ""), bool(b.get("on", True)), val)
    return jsonify(**body), code


@bp.route("/finance/porders/api/rules/items")
def api_rules_items():
    """S414: the add box's autocomplete -- names only, from the stock master; owner."""
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    return jsonify(ok=True, items=item_names(con, request.args.get("q", "")))


@bp.route("/finance/porders/api/rules/freeze", methods=["POST"])
def api_rules_freeze():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    b = request.get_json(silent=True) or {}
    return jsonify(**set_freeze(con, _who(u), bool(b.get("on")), b.get("reason")))


@bp.route("/finance/porders/api/rules/holiday", methods=["POST"])
def api_rules_holiday():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return jsonify(ok=False, error="view_only", message="Aap sirf dekh sakte hain."), 403
    b = request.get_json(silent=True) or {}
    body, code = set_holiday(con, _who(u), b.get("day"), b.get("note"), bool(b.get("remove")))
    return jsonify(**body), code


@bp.route("/finance/porders/api/oos")
def api_oos():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    o = oos_both_ends(con)
    return jsonify(ok=True, n=len(o), items=o)


@bp.route("/finance/porders/api/new-items")
def api_new_items():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind != "owner":
        return jsonify(ok=False, error="owner_only"), 403
    m = str(request.args.get("month") or _today().strftime("%Y-%m"))
    if not re.match(r"^\d{4}-\d{2}$", m):
        return jsonify(ok=False, error="bad_month"), 400
    rows = new_items(con, m)
    return jsonify(ok=True, month=m, n=len(rows), items=rows)


@bp.route("/finance/porders/api/day")
def api_day():
    u, con, kind, err = _auth()
    if err:
        return err
    d = day_state(con)
    d["inputs"] = _s470_inputs_note(process=True)              # S593: what the stock side of the last plan stood on (nothing of it on Darpan's tab)
    return jsonify(**d)


@bp.route("/finance/porders/api/day/send", methods=["POST"])
def api_day_send():
    u, con, kind, err = _auth()
    if err:
        return err
    if kind not in ("owner", "sender"):
        return jsonify(ok=False, error="view_only", message="Aap sirf dekh sakte hain."), 403
    b = request.get_json(silent=True) or {}
    try:
        pid = int(b.get("proposal_id") or 0)
    except (TypeError, ValueError):
        pid = 0
    body, code = send_proposal(con, u, pid, b.get("lines") if "lines" in b else None)
    return jsonify(**body), code


# ------------------------------------------------------------------ the cron worker
def _con():
    con = sqlite3.connect(os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db")), timeout=60)
    con.row_factory = sqlite3.Row
    return con


def main(argv):
    what = argv[1] if len(argv) > 1 else "tick"
    con = _con()
    try:
        if what == "tick":
            r = tick(con)
            print("%s %s" % (now_iso(), json.dumps(r, ensure_ascii=False)[:600]))
            return 0
        if what == "status":
            d = day_state(con)
            print(json.dumps(dict(day=d["day"], n=d["n"], sent=d["sent"], unsent=d["unsent"], text=d["text"], frozen=bool(d["frozen"])), ensure_ascii=False))
            return 0
        if what == "seed":
            print("reseed: %d rows touched" % reseed(con))
            return 0
        print(__doc__ or "tick | status | seed")
        return 2
    finally:
        con.close()



# =====================================================================================================================
# S454_BILL_REGISTER (part 1, 03-Oct-2026, D666): WHO DECIDES THE ORDER, AND ONE REMINDER A DAY.
#   * order.source = marg_sheet (the default): Darpan's sheet is the order; the proposals are still prepared at 09:00 but shown to no
#     staff -- no 09:00 notice, no "Order not sent" line. order.source = system: S410 as it was, the 09:00 notice included.
#   * The reminders at 12:00 and 15:00 go; ONE push at order.remind_times (default 17:00), only while a supplier is still to be ordered,
#     naming them (order_sheet.reminder_text). Decided once a day, at the first tick at or after that time.
#   * Every tick runs order_sheet.cron_pass: the sheets the door took, the WhatsApp line, Marg's clearing, the bill-scan tie -- so none of
#     them waits for someone to open the page. The cron line runs every ten minutes, 05:00-21:50 (S454's crontab edit).
# =====================================================================================================================
def _s454_source(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        return order_sheet.source(con)
    except Exception:                                         # noqa: BLE001
        return "marg_sheet"


def _s454_or_arrived(con):
    """S454 (4.4): an order that arrived by its bill's scan keeps its open lines on the way until Marg's bill answers them (the next
    interim check does not order them twice). No tie table yet: nothing added."""
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " OR o.id IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)"
    except sqlite3.Error:
        return ""


def _s454_pass(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        out = order_sheet.cron_pass(con, "cron")
        try:                                                  # S454 P3 (9.3): Marg's newest closing beside the shelf figure, once per closing
            import shelf_figure                               # noqa: PLC0415
            out["gaps"] = shelf_figure.record_gaps(con)
        except Exception as e2:                               # noqa: BLE001
            out["gaps"] = "error: %s" % str(e2)[:80]
        return out
    except Exception as e:                                    # noqa: BLE001
        return dict(error=str(e)[:120])


def _s454_remind(con, today, now, force=""):
    """The one reminder of the day: once, at the first tick at or after order.remind_times; silent (but decided) when nothing is pending.
    force = a walk's forced slot ("remind17"): it speaks only when its hour is the remind time's hour -- the 12:00 and 15:00 reminders go."""
    try:
        import order_sheet                                    # noqa: PLC0415
        key, text = order_sheet.reminder_due(con, now)
        if not key:
            return dict(ok=True, silent=True, why="no remind time")
        if force:
            if str(force)[6:8] != key[1:3]:
                return dict(ok=True, silent=True, slot=key, why="S454: no reminder at %s:00" % str(force)[6:8])
            text = order_sheet.reminder_text(con)
        elif text is None and (now.hour, now.minute) < (int(key[1:3]), int(key[3:5])):
            return dict(ok=True, silent=True, why="not yet")
        ensure(con)
        if con.execute("SELECT 1 FROM order_notice WHERE day=? AND slot=?", (today.isoformat(), key)).fetchone():
            return dict(ok=True, already=True, slot=key)
        if not text:
            con.execute("INSERT OR IGNORE INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (today.isoformat(), key, "(silent: nothing pending)", "{}", now_iso()))
            con.commit()
            return dict(ok=True, silent=True, slot=key)
        to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip()]
        payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True,
                       ts=int(dt.datetime.now().timestamp() * 1000))
        sent = {}
        for u in to:
            try:
                s, f = _push(u, payload)
                sent[u] = dict(sent=s, failed=f)
            except Exception as e:                            # noqa: BLE001
                sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
        con.execute("INSERT OR IGNORE INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (today.isoformat(), key, text, json.dumps(sent), now_iso()))
        con.commit()
        return dict(ok=True, slot=key, text=text, sent=sent)
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, error=str(e)[:120])



# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.2, D667): order.stock_basis -- count (the default): the system's own list works from the shelf
# figure (shelf_figure.figures: the newest physical count carried forward by the spine's sales and purchases, plus what arrived and is not
# in Marg); marg: Marg's closing stock, today's plan line for line. An item with no count keeps Marg's figure.
# ==========================================================================================================================================
def _s454_basis(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        v = order_sheet.setting(con, "order.stock_basis")
    except Exception:                                         # noqa: BLE001
        v = "count"
    return v if v in ("count", "marg") else "count"


def _s454_shelf_snap(con, snap, ctx=None):
    """The snapshot with each item's qty replaced by its shelf figure (Marg's kept as marg_qty); fail-soft: the snapshot as it is.
    S593 (R1-C5, R1-C6): the engine's own context (stock_watch.Spine + stock_figure.Ctx) rides into shelf_figure.figures so every item is
    figured once per plan(); marg_qty is Marg's PURE figure (_s470.marg = stock_figure.marg().figure, no arrivals) -- the incoming qty only
    when the row has none (the tables engine)."""
    try:
        import shelf_figure                                   # noqa: PLC0415
        F = shelf_figure.figures(con, sp=(ctx.sp if ctx is not None else None), items=[s["item"] for s in snap.values()], ctx=ctx)
    except Exception:                                         # noqa: BLE001
        return snap
    out = {}
    for k, s in snap.items():
        f = F.get(s["item"]) or {}
        d = dict(s)
        if f.get("shelf") is not None and f.get("named") not in ("no_count", "no_spine"):
            m = (s.get("_s470") or {}).get("marg")
            d["marg_qty"] = int(round(float(m))) if m is not None else s["qty"]
            d["qty"] = int(f["shelf"])
        out[k] = d
    return out


def _s454_count_way(con, today, snap, transit, onord):
    """On count: on the way = a SENT order not yet arrived by its bill's scan, for every item. An order that arrived by its scan is marked
    'received' (order_sheet), so it is counted once -- by Marg's in-transit (purchase_app._in_transit) for an item with no count, and inside
    the shelf figure for an item on it (Marg's in-transit dropped there). On marg the old way stands, which counted such an order twice."""
    shelf = {k for k, s in snap.items() if "marg_qty" in s}
    transit = {k: v for k, v in transit.items() if k not in shelf}
    return transit, _on_order_units(con, today, "count")


def _s454_not_tied(con):
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " AND o.id NOT IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)" + _s825_not_carried(con)
    except sqlite3.Error:
        return ""


def _s825_not_carried(con):
    """S825 (F-1220, D883): ' OR l.id IN (...)' -- the scan-tied open lines the dealer's scanned bill does NOT carry
    (stock_figure.s825_bill_judged False) stay ON ORDER on the count basis: they have not arrived, so they are on the way and the engine does
    not propose them again. Inside the caller's bracket: (o.status='sent' AND o.id NOT IN tied OR l.id IN (...)). '' when none or unreadable."""
    try:
        import stock_figure as SF                             # noqa: PLC0415
        j = SF.s825_bill_judged(con) or {}
        ids = sorted(int(k) for k, v in j.items() if v is False)
    except Exception:                                         # noqa: BLE001
        return ""
    return (" OR l.id IN (%s)" % ",".join(str(i) for i in ids)) if ids else ""
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S470_ORDER_ON_SPINE (04-Oct-2026, D672 / D673; rung 4a of S272_SPINE_ARCHITECTURE): THE ENGINE'S THREE NUMBERS COME FROM THE SPINE.
#   order.engine_source = spine (the default): _snapshot_inputs reads the spine through its ONE read door (spine/spine_read.py) --
#       Marg's stock from the latest accepted closing (closing), the sale rate from the spine's sale lines with returns deducted
#       (sales_daily, last_sale), the supplier, the cost, the box and the lot from its purchase lines (purchase_lines); it reads no sale,
#       stock or purchase figure from sale_line_item, stock_snapshot, stock_feed, purchase_line or purchase_bill. Only the item list --
#       names, packings, pack sizes -- is still Marg's newest stock list (stock_snapshot): the spine keeps a closing by key, not by item.
#       The count basis stays the shelf figure (shelf_figure.figures, untouched).
#   order.engine_source = tables: the four old calls, line for line (purchase_app._latest_snapshot / _pace / _last_purchase / _in_transit).
#       Also the way taken, and said in the plan's "engine", if the spine cannot be read.
#   ARRIVALS NOT YET IN MARG -- S593 (D743): THE ONE RULE is stock_figure's (carried / expired, rules a-e; S583). The engine's own copy
#       (_s470_arrivals) is retired: an uncounted item's figure is stock_figure.marg() + taps + scan_arrivals since its closing's capture;
#       a counted item's arrivals are inside its shelf figure. Only the sent-and-unanswered lines (_on_order_units) ride beside it.
#   A FAMILY (items of Marg's stock list that share one 20-letter key, F-719): the spine knows the family's stock and the family's sales,
#       never a member's own. Each member is planned on the family's cover -- its stock and its rate both shared equally -- and its line
#       carries family = n. The members are counted in Marg's stock list, not in the spine's item table (spine_read.family): that table
#       holds a row for every packing an item ever had and for every way a report spells one.
#   Six numbers that were constants are settings (their values unchanged): order.pace_days, order.dead_after_days, order.on_order_days,
#       order.in_transit_days, order.lot_history_days, order.engine_source. plan() also returns no_supplier (a sold item never bought:
#       still ordered from nobody, but named) and engine (which source made this plan).
# ==========================================================================================================================================
import threading as _s470_threading                             # noqa: E402

SETTINGS.update({
    "order.engine_source": ("spine", "(S470) where the engine's sale rate, stock and supplier come from: spine (the one corrected store) or tables (the old reads -- the fallback)"),
    "order.pace_days": ("28", "(S470) the sale rate is what sold over this many days"),
    "order.dead_after_days": ("60", "(S470) an item with no sale for more than this many days is not reordered"),
    "order.on_order_days": ("4", "(S470) a sent order's unanswered lines count as stock for this many days"),
    "order.in_transit_days": ("14", "(S470) goods received and not yet in Marg count as stock for this many days"),
    "order.lot_history_days": ("180", "(S470) the lot and the free-per-lot are read from the purchases of this many days"),
})
S470_KEYS = ("order.engine_source", "order.pace_days", "order.dead_after_days", "order.on_order_days", "order.in_transit_days", "order.lot_history_days")
_S470 = _s470_threading.local()                                # the last inputs' note, per thread: which source made them
_S470_MOD = {"mtime": None, "mod": None}
_S593_INPUTS = {"val": None}                                    # S593: the process's last inputs note (the owner's api/day reads it)


def _s470_source(con):
    v = _setting(con, "order.engine_source")
    return v if v in ("spine", "tables") else "spine"


def _s470_days(con, key, lo=1):
    """A day-count setting, never below lo (a zero or a word in the row falls back to the default)."""
    n = _int_setting(con, key)
    return n if n >= lo else int(SETTINGS[key][0])


def _s470_engine():
    return getattr(_S470, "engine", "tables")


def _s470_spine():
    """The spine's ONE read door (spine/spine_read.py beside this file), opened read-only on SPINE_DB or spine/spine.db."""
    import importlib.util                                      # noqa: PLC0415
    p = os.path.join(SPINE_DIR, "spine_read.py")
    m = os.path.getmtime(p)
    if _S470_MOD["mod"] is None or _S470_MOD["mtime"] != m:
        spec = importlib.util.spec_from_file_location("spine_read_s470", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _S470_MOD["mod"], _S470_MOD["mtime"] = mod, m
    return _S470_MOD["mod"].Spine(os.environ.get("SPINE_DB") or os.path.join(SPINE_DIR, "spine.db"))


def _s470_pack(packing):
    m = re.match(r"^(\d+)\*(\d+)$", str(packing or "").strip().rstrip("."))
    return max(1, int(m.group(1)) * int(m.group(2))) if m else 1


def _s470_dmy(iso):
    s = str(iso or "")
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if re.match(r"^\d{4}-\d\d-\d\d", s) else s


def _s470_master(con, pa):
    """Marg's item list: the NAMES, packings and pack sizes of the newest stock list (stock_snapshot). No figure is read from it -- the
    spine keeps a closing by key only, and its own item table holds one item twice where two reports spell its packing differently."""
    if not _has(con, "stock_snapshot"):
        raise RuntimeError("no stock list on this server")
    dates = [r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot")]
    if not dates:
        raise RuntimeError("the stock list is empty")
    return [(r[0], r[1] or "", max(1, int(r[2] or 1))) for r in
            con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE as_on=? ORDER BY item", (max(dates, key=pa._as_on_key),))]


def _s593_sf():
    """stock_figure beside this file -- the one stock function (S577 / S583 / S587); imported at call time, as shelf_figure does."""
    import stock_figure                                        # noqa: PLC0415
    return stock_figure


def _s593_sw():
    import stock_watch                                         # noqa: PLC0415
    return stock_watch


def _s470_inputs_note(process=False):
    """plan()['inputs'] -- what the stock side of the last plan on this thread stood on; process=True: the process's last (the owner's
    api/day). None until a plan was made on the spine."""
    if process:
        return _S593_INPUTS.get("val")
    return getattr(_S470, "inputs", None)


def _s470_snap(con, pa, sw, ctx, today):
    """(as_on dd-mm-yyyy, {norm(item): row}, [items with no figure]) -- S593 (S308 i; charter 1, 2, 3; R1-B1, C1-C4): every item of Marg's
    list with its figure from THE ONE STOCK FUNCTION -- stock_figure.marg() (Marg's newest usable closing carried by the spine's movements to
    today) + taps() + scan_arrivals() since that closing's capture (the one arrivals rule, S583) -- never below 0. `sw` is stock_watch.Spine()
    (the handle stock_figure is written for) and `ctx` its stock_figure.Ctx. The key grouping stays only for n = the number of MASTER names
    under the key, which _s470_pace divides the key's sales by (the two must agree; R1-C2). An item no capture holds at all is left out and
    named; an item the closing did not print but the spine knew (by='absent') stands at 0 AND is named (a deliberate change: the engine may
    now list it). as_on is the capture's end day."""
    SF = _s593_sf()
    t = today.isoformat()
    cap = SF.capture_at(sw, t, ctx)
    if cap is None:
        raise RuntimeError("the spine holds no usable closing")
    fam = {}
    for item, packing, size in _s470_master(con, pa):
        fam.setdefault(sw.key(item), []).append((item, packing, size))
    snap, missing = {}, []
    for key, members in fam.items():
        n = len(members)
        for item, packing, size in members:
            m = SF.marg(con, sw, item, at=t, ctx=ctx)
            if m is None:
                missing.append(item)
                continue
            c = m["closing"]
            figure = float(m["figure"] or 0)
            taps = float(m.get("taps") or 0)
            scans = float(SF.scan_arrivals(con, sw, item, c["stamp_iso"], ctx) or 0)
            if c.get("by") == "absent":
                missing.append(item)
            snap[pa.norm(item)] = dict(item=item, qty=max(0, int(round(figure + taps + scans))), packing=packing, pack_size=size,
                                       _s470=dict(key=key, family=n, lot=None, free=None, marg=figure, by=c.get("by"), approx=bool(m.get("approx"))))
    return _s470_dmy(cap["end_day"]), snap, missing


def _s470_pace(sp, snap, today, pace_days):
    """purchase_app._pace's formula on the spine's sale lines: the same window (today - pace_days .. today, both ends), returns
    deducted, units as the spine reads them; every item with any sale in the spine's history gets an entry."""
    since = (today - dt.timedelta(days=pace_days)).isoformat()
    t = today.isoformat()
    out, done = {}, {}
    for k, s in snap.items():
        x = s["_s470"]
        if x["key"] not in done:
            days = {r["date"]: float(r["units"] or 0) for r in sp.sales_daily(s["item"], since, t)}
            done[x["key"]] = (days, sp.last_sale(s["item"]))
        days, ls = done[x["key"]]
        if not days and not ls:
            continue
        n = max(1, int(x["family"]))
        total = max(0.0, sum(days.values())) / n
        peak = (max(days.values()) / n) if days else 0.0
        e = dict(rate_per_day=total / pace_days, sell_days=sum(1 for v in days.values() if v > 0), peak_share=(peak / total) if total > 0 else 0.0)
        if n > 1:
            e["approx_shared"] = n
        if ls:
            try:
                e["days_since_sale"] = (today - dt.date.fromisoformat(ls["date"])).days
            except ValueError:
                e["days_since_sale"] = 999
        out[k] = e
    return out


def _s470_purch(pa, sp, snap, today, lot_days):
    """purchase_app._last_purchase's fields from the spine's PURCHASE lines over all history: vendor (the normalised key every rule,
    proposal and phone lookup is keyed by -- never the spine's supkey), vendor_disp (the printed name), suppliers, rate_p (the latest
    line's cost per pack: net amount / quantity, else amount / quantity), box (the GCD of the quantities; 0 when none). And, from the last
    lot_days only, carried on the line and used by no rail yet: lot (the median quantity bought per line, in units) and free (the median
    free per bought)."""
    since = (today - dt.timedelta(days=lot_days)).isoformat()
    out, done = {}, {}
    for k, s in snap.items():
        x = s["_s470"]
        if x["key"] not in done:
            e = dict(vendor=None, vendor_disp=None, rate_p=None, suppliers=set(), qtys=[], packing=s["packing"])
            lots, frees = [], []
            for l in sp.purchase_lines(s["item"]):
                if l["direction"] != "PURCHASE":
                    continue
                vn = pa.supplier_key(l["supplier"]) if l["supplier"] else ""
                if vn:
                    e["suppliers"].add(vn)
                    e["vendor"], e["vendor_disp"] = vn, l["supplier"]
                q = float(l["qty"] or 0)
                if q:
                    amt = l["net_amount_p"] or l["amount_p"]
                    if amt:
                        e["rate_p"] = int(round(float(amt) / q))
                    e["qtys"].append(int(q))
                    if l["date"] >= since:
                        lots.append(q * s["pack_size"])
                        frees.append(float(l["free"] or 0) / q)
            if e["vendor"] or e["qtys"]:
                g = 0
                for q in e["qtys"]:
                    g = math.gcd(g, q)
                e["box"] = g if g > 1 else 0
                e["lot"] = statistics.median(lots) if lots else None
                e["free"] = round(statistics.median(frees), 3) if frees else None
                done[x["key"]] = e
            else:
                done[x["key"]] = None
        e = done[x["key"]]
        if e:
            out[k] = e
            x["lot"], x["free"] = e["lot"], e["free"]
    return out


def _s470_inputs(con, today):
    """S593 (D743, R1-B1): TWO spine handles -- spine_read's (sales_daily / last_sale / purchase_lines, for _s470_pace and _s470_purch) and
    stock_watch.Spine() (the handle stock_figure is written for: it carries .ok), the latter inside ONE stock_figure.Ctx that _s470_snap and
    _s454_shelf_snap share, so every item is figured once per plan(). The engine's own arrivals rule is gone: transit holds the sent-and-
    unanswered lines only (_on_order_units); every other arrival is inside the one function's figure. The inputs note (plan()['inputs'], the
    owner's api/day) says what the stock side stood on: the sale reach, the closing's capture, the spine's build, the counted / Marg / absent
    counts."""
    pa = _pa()
    SF = _s593_sf()
    sp = _s470_spine()
    sw = _s593_sw().Spine()
    ctx = SF._ctx(con, sw, None)
    try:
        as_on, snap, missing = _s470_snap(con, pa, sw, ctx, today)
        basis = _s454_basis(con)
        if basis == "count":                                     # the shelf figure, through the same context; Marg's pure figure beside it as marg_qty
            snap = _s454_shelf_snap(con, snap, ctx)
        pace = _s470_pace(sp, snap, today, _s470_days(con, "order.pace_days"))
        purch = _s470_purch(pa, sp, snap, today, _s470_days(con, "order.lot_history_days"))
        cap = SF.capture_at(sw, today.isoformat(), ctx) or {}
        try:
            built = str((sw.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
        except Exception:                                        # noqa: BLE001
            built = ""
        note = dict(sales_through=str((SF._reach_once(sw, ctx) or {}).get("last_sale") or ""),
                    capture=dict(md5=str(cap.get("md5") or "")[:8], as_on=cap.get("as_on"), end_day=cap.get("end_day"), stamp=cap.get("stamp")),
                    spine_built=built, counted=sum(1 for s in snap.values() if "marg_qty" in s), marg=sum(1 for s in snap.values() if "marg_qty" not in s),
                    absent=sum(1 for s in snap.values() if (s.get("_s470") or {}).get("by") == "absent"), made_at=now_iso())
    finally:
        for h in (sp, sw):
            try:
                h.con.close()
            except Exception:                                    # noqa: BLE001
                pass
    transit = {}
    for k, e in _on_order_units(con, today, "count").items():    # sent, not yet arrived: on the way, counted as stock (as today)
        t = transit.setdefault(k, dict(units=0, order_id=e["order_id"], vendor=""))
        t["units"] = int(t.get("units") or 0) + e["units"]
        t["on_way"] = e
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    _S470.missing = sorted(m for m in missing if pa.norm(m) not in ortho)   # an orthotic is S403's, never this engine's
    _S470.inputs = note
    _S593_INPUTS["val"] = note
    return as_on, snap, pace, purch, transit, ortho


def _s470_missing():
    return list(getattr(_S470, "missing", None) or [])


_snapshot_inputs_before_s470 = _snapshot_inputs


def _snapshot_inputs(con, today):                                # noqa: F811
    """S470 (B.1): one setting decides the source. On spine the plan is made from the spine; on tables, or when the spine cannot be
    read, the old reads run exactly as they did -- and the plan says which made it."""
    _S470.missing = []
    _S470.inputs = None
    if _s470_source(con) != "spine":
        _S470.engine = "tables"
        return _snapshot_inputs_before_s470(con, today)
    try:
        out = _s470_inputs(con, today)
        _S470.engine = "spine"
        return out
    except Exception as e:                                       # noqa: BLE001 -- ordering never stops for the spine
        _S470.engine = "tables (the spine could not be read: %s)" % (str(e) or type(e).__name__)[:120]
        return _snapshot_inputs_before_s470(con, today)


_line_out_before_s470 = _line_out


def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):   # noqa: F811
    """S470 (B.5, B.6): the line carries its lot and free (read, used by no rail yet) and, for a family member, family = n."""
    lo = _line_out_before_s470(pa, s, it, line, cost_unit, p, why_extra)
    x = s.get("_s470")
    if x:
        lo["lot"], lo["free"] = x.get("lot"), x.get("free")
        if int(x.get("family") or 1) > 1:
            lo["family"] = int(x["family"])
    return lo
# ---- S470 end ---------------------------------------------------------------------------------------------------------------------------


# ==========================================================================================================================================
# S644_BUYING_MODEL (25-Oct-2026, D678 built; brief S486 Part B as re-read by S308 and planned in claude/S350_KIT_II_PLAN.md): THE LEVELS
# MODEL BEHIND ONE SETTING.  order.model = fixed (the default: today's engine, line for line -- every hook below is a pass-through) |
# levels (five rules inside the existing plan() / interim_plan() / prepare_day / tick):
#   1 each supplier at ITS OWN RHYTHM (rhythm_mode learnt: due when today - last buy >= the interval learnt from its bill days, clamped
#     order.review_min_days..review_max_days, or the owner's review_days; rhythm_mode fixed = today's calendar -- Kedar, D626)
#   2 the shop's own LOTS (the median purchase lot of order.lot_history_days, rounded up to whole lots, capped by cover, one lot minimum;
#     a new medicine -- first bought within order.new_item_days -- one lot)
#   3 the RATE ends on the spine's last sale day, never today (long order.pace_days; short order.rate_short_days, counted when it sold on
#     order.rate_short_min_sell_days of them, capped at order.rate_short_cap_pct of the long rate); the list is MADE AGAIN once, before
#     order.relist_until, when any input moved (the sales day, the closing's day, the spine's build) and nobody touched it
#   4 the shelf keeps ONE LARGE SALE (the level is never below the largest single day's sale of order.big_day_days)
#   5 an order BETWEEN REVIEWS goes only when the stock will not last to the next review + lead + order.interim_margin_days
# The arithmetic is PURE (model_* below: no database, no clock); the kit's replay runs the same functions. Nothing of this reaches a staff
# screen: order.source is not written by this kit; the proposals carry `model`; the nightly rehearsal scores them per model (B.8).
# Charter (S308): B.6 'count it' is NOT built; B.5 'supplier not known' stays on the owner's fold; one lot (model_lot), one interval
# (model_interval, inside rhythm()), one days_left (S593); the interval is computed at read, the stored columns are display-only.
# ==========================================================================================================================================
S644_KEYS = ("order.model", "order.rate_short_days", "order.rate_short_cap_pct", "order.rate_short_min_sell_days", "order.big_day_days",
             "order.interim_margin_days", "order.relist_until", "order.new_item_days", "order.review_min_days", "order.review_max_days",
             "order.review_default_days")
SETTINGS.update({
    "order.model": ("fixed", "(S644) how the system's list is made: fixed = fixed order days, as before · levels = each supplier's own rhythm, the shop's lots, yesterday's sales"),
    "order.rate_short_days": ("7", "(S644) the short sale window, days, ending on the last sale day"),
    "order.rate_short_cap_pct": ("200", "(S644) the short rate counts up to this % of the long rate"),
    "order.rate_short_min_sell_days": ("3", "(S644) the short rate counts only when the item sold on this many of its days"),
    "order.big_day_days": ("28", "(S644) the shelf keeps the largest single day's sale of this many days (0 = off)"),
    "order.interim_margin_days": ("1", "(S644) a between-review order goes when the stock will not last to the next review + lead + this"),
    "order.relist_until": ("13:00", "(S644) an untouched list is made again when an input moves, until this time (HH:MM)"),
    "order.new_item_days": ("28", "(S644) a medicine first bought within this many days is new: one lot"),
    "order.review_min_days": ("2", "(S644) a learnt review interval is never shorter than this"),
    "order.review_max_days": ("30", "(S644) a learnt review interval is never longer than this"),
    "order.review_default_days": ("7", "(S644) the review interval while a supplier has fewer bill days than order.min_bills_for_rhythm"),
})
S470_KEYS = tuple(S470_KEYS) + S644_KEYS                         # the owner's settings card (porders_s454) reads this tuple
RULE_FIELDS = tuple(RULE_FIELDS) + ("rhythm_mode", "review_days")
S644_COLS = (("rhythm_mode", "TEXT"), ("review_days", "INTEGER"), ("bill_days90", "INTEGER"), ("rhythm_at", "TEXT"))
_S644 = _s470_threading.local()


# ------------------------------------------------------------------ the pure arithmetic (no database, no clock; the replay runs these)
def model_rate(daily_units, end, long_days, short_days, short_min_sell_days, short_cap_pct):
    """(rate, rate_long, rate_short, sell_days_long, sell_days_short, peak_long) from {date: net units} over two calendar windows that END
    on `end` (inclusive): the divisor is always the whole window (no in-stock correction -- the replay measured none)."""
    def win(w):
        u, sell, peak = 0.0, 0, 0.0
        for n in range(int(w)):
            q = float(daily_units.get(end - dt.timedelta(days=n), 0.0) or 0.0)
            u += q
            if q > 0:
                sell += 1
                peak = max(peak, q)
        return max(0.0, u) / float(w), sell, peak
    rl, sl, pk = win(long_days)
    rs, ss, _ = win(short_days)
    r = rl
    if ss >= int(short_min_sell_days) and rs > rl:
        r = min(rs, rl * float(short_cap_pct) / 100.0) if rl > 0 else rs
    return r, rl, rs, sl, ss, pk


def model_big_day(daily_units, end, days):
    """(units, date) of the largest single day's net sale in the `days` days ending on `end`; (0.0, None) when days is 0 or nothing sold."""
    best, on = 0.0, None
    for n in range(int(days or 0)):
        d = end - dt.timedelta(days=n)
        q = float(daily_units.get(d, 0.0) or 0.0)
        if q > best:
            best, on = q, d
    return best, on


def model_lot(purchase_lines, as_of, history_days):
    """The usual lot in UNITS: the median of the bought units of the PURCHASE lines dated within history_days before as_of (inclusive);
    None with no line. purchase_lines: [(date, units)] with units > 0 for a purchase."""
    since = as_of - dt.timedelta(days=int(history_days))
    lots = [float(u) for d, u in purchase_lines if u and float(u) > 0 and since <= d <= as_of]
    return statistics.median(lots) if lots else None


def model_interval(bill_dates, as_of, min_bill_days, default_days, lo, hi):
    """(interval, median_gap, bill_days) from a supplier's distinct bill days up to as_of: the median gap rounded half-up, clamped lo..hi;
    default_days while there are fewer than min_bill_days bill days (or a single one). median_gap is None with fewer than two days."""
    ds = sorted({d for d in bill_dates if d is not None and d <= as_of})
    gaps = [(b - a).days for a, b in zip(ds, ds[1:])]
    med = statistics.median(gaps) if gaps else None
    if len(ds) < int(min_bill_days) or med is None:
        iv = int(default_days)
    else:
        iv = int(math.floor(float(med) + 0.5))
    return max(int(lo), min(int(hi), iv)), med, len(ds)


def model_cap_days(interval, cap_weekly, cap_fortnightly, cap_monthly):
    return int(cap_weekly) if interval <= 7 else (int(cap_fortnightly) if interval <= 14 else int(cap_monthly))


def model_level(rate, cover_days, big_day_units):
    """The shelf's level in units: rate x cover, never below the largest day's sale."""
    return max(float(rate) * float(cover_days), float(big_day_units or 0.0))


def model_qty(need_units, lot_units, on_hand_units, rate, cap_days, is_new):
    """Units to order in whole lots: at least one lot; a new item one lot; else need rounded up to lots, then the cap as a LIMIT -- the
    largest multiple of the lot that keeps (on_hand + q) / rate within cap_days, never below one lot. (units, notes). cap_days None = no cap."""
    lot = float(lot_units)
    notes = []
    if is_new:
        return lot, ["new medicine -- one lot"]
    q = math.ceil(float(need_units) / lot) * lot
    if q < lot:
        q = lot
    capped = False
    while cap_days is not None and q > lot and rate > 0 and (float(on_hand_units) + q) / float(rate) > float(cap_days):
        q -= lot
        capped = True
    if capped:
        notes.append("cut to the cover cap")
    if rate > 0 and cap_days is not None and (float(on_hand_units) + q) / float(rate) > float(cap_days):
        notes.append("one lot is more than the cover cap")
    return q, notes


def model_interim_due(on_hand_units, rate, days_to_next_review, lead_days, margin_days):
    """True when the stock will not last to the next review + lead + margin."""
    if rate <= 0:
        return False
    return float(on_hand_units) / float(rate) < float(days_to_next_review) + float(lead_days) + float(margin_days)


# ------------------------------------------------------------------ the setting, the columns, the rhythm at read
def _s644_on(con):
    return _setting(con, "order.model", "fixed") == "levels"


def _s644_learnt(con, r):
    """levels AND this supplier's rhythm is learnt (not fixed by the owner): the calendar follows last buy + interval."""
    return _s644_on(con) and str((r or {}).get("rhythm_mode") or "learnt") == "learnt"


def _s644_columns(con):
    """The four columns, lazily (idempotent). At their creation rhythm_mode is 'fixed' for every row whose cadence is custom or whose
    owner_fields hold order_days / cadence (Kedar: the owner's ruling of 26-Sep stays), 'learnt' for the rest."""
    have = {r[1] for r in con.execute("PRAGMA table_info(order_supplier_rule)")}
    fresh = "rhythm_mode" not in have
    for col, typ in S644_COLS:
        if col not in have:
            con.execute("ALTER TABLE order_supplier_rule ADD COLUMN %s %s" % (col, typ))
    if fresh:
        for r in con.execute("SELECT supplier_norm, cadence, owner_fields FROM order_supplier_rule").fetchall():
            of = set()
            try:
                of = set(json.loads(r[2] or "[]"))
            except (TypeError, ValueError):
                pass
            mode = "fixed" if (r[1] == "custom" or of & {"order_days", "cadence"}) else "learnt"
            con.execute("UPDATE order_supplier_rule SET rhythm_mode=? WHERE supplier_norm=?", (mode, r[0]))
        con.commit()


ensure_before_s644 = ensure


def ensure(con):                                              # noqa: F811
    ensure_before_s644(con)
    try:
        _s644_columns(con)
    except sqlite3.Error:
        pass


def _s644_rhythm(con, today):
    """rhythm(con, today) once per thread per minute (one spine read for a whole plan / tick), {supplier_norm: e}."""
    key = (today.isoformat(), dt.datetime.now().strftime("%H:%M"))
    if getattr(_S644, "rh_key", None) != key:
        _S644.rh, _S644.rh_key = rhythm(con, today), key
    return _S644.rh


def review_interval(con, r, today=None):
    """THE one interval of a supplier (days): the owner's review_days when set; else the interval rhythm() learnt (model_interval over its
    90 days of bill days, clamped); else the default. Computed at read -- the stored rhythm_days / bill_days90 are the owner's words only."""
    today = today or _today()
    lo, hi = _s470_days(con, "order.review_min_days"), _s470_days(con, "order.review_max_days")
    rd = r.get("review_days")
    if rd not in (None, "", 0, "0"):
        try:
            return max(lo, min(hi, int(rd)))
        except (TypeError, ValueError):
            pass
    e = _s644_rhythm(con, today).get(r.get("supplier_norm"))
    if e and e.get("interval"):
        return max(lo, min(hi, int(e["interval"])))
    return max(lo, min(hi, _s470_days(con, "order.review_default_days")))


def last_buy(con, r, before, today=None):
    """The newest day strictly before `before` this supplier was bought from: (a) a sent/received purchase_order that is not interim-only;
    (b) a sent order_proposal of kind fixed / darpan; only when neither is within review_max_days, (c) its newest bill day the spine holds.
    None = never (due)."""
    pa = _pa()
    sn = r["supplier_norm"]
    b = before.isoformat()
    best = None
    try:
        for oid, vendor, osn, created in con.execute("SELECT id, vendor, supplier_norm, substr(created_at,1,10) FROM purchase_order WHERE status IN ('sent','received') "
                                                     "AND substr(created_at,1,10)<? ORDER BY created_at DESC LIMIT 400", (b,)).fetchall():
            key = osn or (pa.supplier_key(vendor) if vendor else "")
            if key != sn:
                continue
            kinds = [x[0] for x in con.execute("SELECT kind FROM order_proposal WHERE sent_order_id=?", (oid,)).fetchall()]
            if kinds and all(k == "interim" for k in kinds):
                continue
            best = created
            break
        pr = con.execute("SELECT MAX(substr(sent_at,1,10)) FROM order_proposal WHERE supplier_norm=? AND status='sent' AND kind IN ('fixed','darpan') "
                         "AND substr(sent_at,1,10)<?", (sn, b)).fetchone()
        if pr and pr[0] and (best is None or pr[0] > best):
            best = pr[0]
    except sqlite3.Error:
        pass
    hi = _s470_days(con, "order.review_max_days")
    if best is None or (before - dt.date.fromisoformat(best)).days > hi:
        e = _s644_rhythm(con, today or _today()).get(sn)
        if e:
            ds = [d for d in e.get("dates") or [] if d and d < b]
            if ds and (best is None or max(ds) > best):
                best = max(ds)
    try:
        return dt.date.fromisoformat(best) if best else None
    except ValueError:
        return None


def _s644_allowed(con, r, d):
    hol = _holidays(con, d, d)
    return DOW[d.weekday()] not in (_blocked_set(r) | {"SUN"}) and d.isoformat() not in hol


def _s644_forward(con, r, d):
    """The first allowed day on or after d (at most 14 days on)."""
    n = 0
    while not _s644_allowed(con, r, d) and n < 14:
        d += dt.timedelta(days=1)
        n += 1
    return d


def _s644_due(con, r, d):
    if not _s644_allowed(con, r, d):
        return False
    lb = last_buy(con, r, d)
    return lb is None or (d - lb).days >= review_interval(con, r, d)


def _s644_next(con, r, after):
    lb = last_buy(con, r, after + dt.timedelta(days=1))
    iv = review_interval(con, r, after)
    start = after + dt.timedelta(days=1)
    if lb is not None:
        start = max(start, lb + dt.timedelta(days=iv))
    return _s644_forward(con, r, start)


def cap_days(con, r, today=None):
    """The cover cap of a learnt supplier: the row's own when the owner set it, else by its interval (weekly / fortnightly / monthly caps)."""
    if "cover_cap_days" in _owner_fields(r):
        return int(r.get("cover_cap_days") or 45)
    return model_cap_days(review_interval(con, r, today), _int_setting(con, "order.cap_weekly"), _int_setting(con, "order.cap_fortnightly"), _int_setting(con, "order.cap_monthly"))


is_order_day_before_s644 = is_order_day
next_order_day_before_s644 = next_order_day
gap_days_before_s644 = gap_days
cover_days_before_s644 = cover_days
rule_words_before_s644 = rule_words


def is_order_day(con, r, d):                                    # noqa: F811
    if _s644_learnt(con, r):
        return _s644_due(con, r, d)
    return is_order_day_before_s644(con, r, d)


def next_order_day(con, r, after):                              # noqa: F811
    if _s644_learnt(con, r):
        return _s644_next(con, r, after)
    return next_order_day_before_s644(con, r, after)


def gap_days(r, con=None, today=None):                          # noqa: F811
    """Fixed: 7 / 14 / 30 / the custom cycle as before. Levels + learnt (with con): the first allowed day on or after today + interval, minus today."""
    if con is not None and _s644_learnt(con, r):
        today = today or _today()
        iv = review_interval(con, r, today)
        return (_s644_forward(con, r, today + dt.timedelta(days=iv)) - today).days
    return gap_days_before_s644(r)


def cover_days(con, r, single_source, today=None):              # noqa: F811
    if not _s644_learnt(con, r):
        return cover_days_before_s644(con, r, single_source)
    c = gap_days(r, con, today) + int(r.get("lead_days") or 1) + int(r.get("safety_days") or 3)
    if single_source and int(r.get("single_source_extra") or 0):
        c += _int_setting(con, "order.single_source_extra_days")
    return min(c, cap_days(con, r, today))


def rule_words(con, r):                                         # noqa: F811
    s = rule_words_before_s644(con, r)
    if not _s644_on(con):
        return s
    if str(r.get("rhythm_mode") or "learnt") != "learnt":
        return s + " · fixed days (your ruling)"
    e = _s644_rhythm(con, _today()).get(r.get("supplier_norm")) or {}
    iv = review_interval(con, r)
    if r.get("review_days") not in (None, "", 0, "0"):
        how = "set by you"
    elif e.get("bill_days90", 0) >= _int_setting(con, "order.min_bills_for_rhythm") and e.get("gap") is not None:
        how = "learnt from %d bill days" % int(e["bill_days90"])
    else:
        how = "the default -- too few bills yet"
    return s + " · reviewed every %d day%s (%s), cap %d" % (iv, "" if iv == 1 else "s", how, cap_days(con, r))


# ------------------------------------------------------------------ the rate, the lot, the new item (hooks on the S470 reads)
_s470_pace_before_s644 = _s470_pace
_s470_purch_before_s644 = _s470_purch
_s470_inputs_before_s644 = _s470_inputs


def _s644_opts(con):
    """The model's numbers for this plan, read once; None on fixed."""
    if not _s644_on(con):
        return None
    return dict(short=_s470_days(con, "order.rate_short_days"), cap_pct=_s470_days(con, "order.rate_short_cap_pct", 100),
                min_sell=_s470_days(con, "order.rate_short_min_sell_days"), big=max(0, _int_setting(con, "order.big_day_days")),
                new=_s470_days(con, "order.new_item_days"), margin=max(0, _int_setting(con, "order.interim_margin_days")))


def _s470_pace(sp, snap, today, pace_days, opts=None):          # noqa: F811
    """S644: with opts (levels) the windows END on the spine's last sale day, never today; long = pace_days, short = opts['short'];
    the entry carries rate_long, rate_short, window_end, big_day, big_day_on. Without opts: S470's reads, untouched."""
    if not opts:
        return _s470_pace_before_s644(sp, snap, today, pace_days)
    try:
        lsd = sp.last_sale_day()
    except Exception:                                            # noqa: BLE001 -- an older spine_read: today - 1
        lsd = None
    end = today - dt.timedelta(days=1)
    if lsd:
        try:
            end = min(end, dt.date.fromisoformat(str(lsd)[:10]))
        except ValueError:
            pass
    reach = max(int(pace_days), int(opts["big"] or 0), int(opts["short"]))
    since = (end - dt.timedelta(days=reach)).isoformat()
    out, done = {}, {}
    for k, s in snap.items():
        x = s["_s470"]
        if x["key"] not in done:
            days = {}
            for r in sp.sales_daily(s["item"], since, end.isoformat()):
                try:
                    days[dt.date.fromisoformat(str(r["date"])[:10])] = float(r["units"] or 0)
                except ValueError:
                    pass
            done[x["key"]] = (days, sp.last_sale(s["item"]))
        days, ls = done[x["key"]]
        if not days and not ls:
            continue
        n = max(1, int(x["family"]))
        shared = {d: v / n for d, v in days.items()}
        rate, rl, rs, sl, ss, peak = model_rate(shared, end, pace_days, opts["short"], opts["min_sell"], opts["cap_pct"])
        tot = rl * pace_days
        bd, bd_on = model_big_day(shared, end, opts["big"]) if opts["big"] else (0.0, None)
        e = dict(rate_per_day=rate, sell_days=sl, peak_share=(peak / tot) if tot > 0 else 0.0, rate_long=round(rl, 4), rate_short=round(rs, 4),
                 sell_days_short=ss, window_end=end.isoformat(), big_day=bd, big_day_on=bd_on.isoformat() if bd_on else None)
        if n > 1:
            e["approx_shared"] = n
        if ls:
            try:
                e["days_since_sale"] = (today - dt.date.fromisoformat(ls["date"])).days
            except ValueError:
                e["days_since_sale"] = 999
        out[k] = e
    return out


def _s470_purch(pa, sp, snap, today, lot_days):                 # noqa: F811
    """S644: the lot through model_lot (THE one median; S470's own median line is retired into it) and first_buy -- the item's earliest
    PURCHASE line day (the new-item test). The other fields exactly as S470 read them."""
    out = _s470_purch_before_s644(pa, sp, snap, today, lot_days)
    done = {}
    for k, s in snap.items():
        e = out.get(k)
        if not e:
            continue
        x = s["_s470"]
        if x["key"] not in done:
            lines, first = [], None
            for l in sp.purchase_lines(s["item"]):
                if l["direction"] != "PURCHASE":
                    continue
                q = float(l["qty"] or 0)
                if q <= 0:
                    continue
                try:
                    d = dt.date.fromisoformat(str(l["date"])[:10])
                except ValueError:
                    continue
                first = d if first is None or d < first else first
                lines.append((d, q * s["pack_size"]))
            done[x["key"]] = (model_lot(lines, today, lot_days), first)
        lot, first = done[x["key"]]
        e["lot"], e["first_buy"] = lot, (first.isoformat() if first else None)
        x["lot"] = lot
    return out


def _s470_inputs(con, today):                                   # noqa: F811
    """S644: on levels the pace is model-aware (the windows end on the last sale day) -- one hook, the rest of S593's read untouched."""
    opts = _s644_opts(con)
    if not opts:
        return _s470_inputs_before_s644(con, today)
    _S644.opts = opts
    pa = _pa()
    SF = _s593_sf()
    sp = _s470_spine()
    sw = _s593_sw().Spine()
    ctx = SF._ctx(con, sw, None)
    try:
        as_on, snap, missing = _s470_snap(con, pa, sw, ctx, today)
        basis = _s454_basis(con)
        if basis == "count":
            snap = _s454_shelf_snap(con, snap, ctx)
        pace = _s470_pace(sp, snap, today, _s470_days(con, "order.pace_days"), opts)
        purch = _s470_purch(pa, sp, snap, today, _s470_days(con, "order.lot_history_days"))
        cap = SF.capture_at(sw, today.isoformat(), ctx) or {}
        try:
            built = str((sw.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
        except Exception:                                        # noqa: BLE001
            built = ""
        note = dict(sales_through=str((SF._reach_once(sw, ctx) or {}).get("last_sale") or ""),
                    capture=dict(md5=str(cap.get("md5") or "")[:8], as_on=cap.get("as_on"), end_day=cap.get("end_day"), stamp=cap.get("stamp")),
                    spine_built=built, counted=sum(1 for s in snap.values() if "marg_qty" in s), marg=sum(1 for s in snap.values() if "marg_qty" not in s),
                    absent=sum(1 for s in snap.values() if (s.get("_s470") or {}).get("by") == "absent"), made_at=now_iso(), model="levels",
                    window_end=next((p.get("window_end") for p in pace.values() if p.get("window_end")), None))
    finally:
        for h in (sp, sw):
            try:
                h.con.close()
            except Exception:                                    # noqa: BLE001
                pass
    transit = {}
    for k, e in _on_order_units(con, today, "count").items():
        t = transit.setdefault(k, dict(units=0, order_id=e["order_id"], vendor=""))
        t["units"] = int(t.get("units") or 0) + e["units"]
        t["on_way"] = e
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    _S470.missing = sorted(m for m in missing if pa.norm(m) not in ortho)
    _S470.inputs = note
    _S593_INPUTS["val"] = note
    return as_on, snap, pace, purch, transit, ortho


_on_order_units_before_s644 = _on_order_units


def _on_order_units(con, today, basis=None):                    # noqa: F811
    """S644 (B.4): on levels a sent order's unanswered lines count as stock while they are within max(order.on_order_days, the supplier's
    interval + lead) of its own supplier -- the same rows, read with the vendor, kept per supplier. Fixed: S470's read."""
    if not _s644_on(con):
        return _on_order_units_before_s644(con, today, basis)
    pa = _pa()
    base = _s470_days(con, "order.on_order_days")
    far = (today - dt.timedelta(days=_s470_days(con, "order.review_max_days") + 7)).isoformat()
    out = {}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.id, o.created_at, o.vendor, o.supplier_norm FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE (o.status='sent'" + (_s454_or_arrived(con) if basis != "count" else _s454_not_tied(con)) + ") AND o.created_at>=? "
                           "AND l.supplied IS NULL AND COALESCE(l.missing,0)=0", (far,)).fetchall()
    except sqlite3.Error:
        return out
    cache = {}
    for item, packs, size, oid, created, vendor, osn in rows:
        sn = osn or (pa.supplier_key(vendor) if vendor else "")
        if sn not in cache:
            r = rule_for(con, sn) if sn else {}
            cache[sn] = max(base, (review_interval(con, r, today) if r else 0) + int((r or {}).get("lead_days") or 1))
        try:
            age = (today - dt.date.fromisoformat(str(created)[:10])).days
        except ValueError:
            continue
        if age > cache[sn]:
            continue
        e = out.setdefault(pa.norm(item), dict(units=0, order_id=oid, sent=str(created or "")[:10]))
        e["units"] += int(packs or 0) * int(size or 1)
    return out


# ------------------------------------------------------------------ the quantity (the hook plan() calls after plan_line, before the rails)
def _s644_shape(con, s, it, p, lp, r, line, cov, dead_after, cost_unit):
    """On levels, for a line plan_line judged: the level with its floor, the need, the lot. Mutates `line` (order_strips, value_p, why,
    confirm, lot_based, and the model keys). On fixed: returns at once."""
    if not _s644_on(con):
        return
    pa = _pa()
    opts = getattr(_S644, "opts", None) or _s644_opts(con) or {}
    rate = float(p.get("rate_per_day") or 0)
    size = max(1, int(s["pack_size"] or 1))
    line["model"] = "levels"
    line["rate_long"], line["rate_short"] = p.get("rate_long"), p.get("rate_short")
    line["review_days"] = review_interval(con, r) if not r.get("_default") else None
    line["level_days"] = cov
    line["window_end"] = p.get("window_end")
    if rate <= 0:
        return
    big = float(p.get("big_day") or 0.0)
    level = model_level(rate, min(cov, pa.MAX_COVER_DAYS), big)
    on_hand = float(it["on_hand"])
    if line["order_strips"] <= 0:
        if line.get("why") or it.get("days_since_sale", 0) > (dead_after or pa.DEAD_AFTER_DAYS) or on_hand >= big or big <= 0:
            return                                             # not needed (plan_line's own judgment), dead, or no floor to meet
        line["why"] = list(line.get("why") or []) + ["kept for one large sale (%s on %s)" % (_qw(int(round(big)), s), _dmy(p.get("big_day_on")))]
    elif big > rate * min(cov, pa.MAX_COVER_DAYS):
        line["why"] = list(line.get("why") or []) + ["kept for one large sale (%s on %s)" % (_qw(int(round(big)), s), _dmy(p.get("big_day_on")))]
    need = max(0.0, level - on_hand)
    lot = (s.get("_s470") or {}).get("lot")
    fb = lp.get("first_buy")
    is_new = False
    if fb:
        try:
            is_new = (_today() - dt.date.fromisoformat(fb)).days <= int(opts.get("new", 28))
        except ValueError:
            is_new = False
    if not lot or float(lot) <= 0:
        if line["order_strips"] <= 0:                          # floor-listed, no lot: today's rails on the need
            line["order_strips"] = int(math.ceil(need / float(size)))
            line["value_p"] = int(line["order_strips"] * size * (cost_unit or 0))
        return
    cap = cap_days(con, r) if _s644_learnt(con, r) else int(r.get("cover_cap_days") or 45)
    q_units, notes = model_qty(need, float(lot), on_hand, rate, cap, is_new)
    strips = int(math.ceil(q_units / float(size)))
    if strips <= 0:
        return
    why = list(line.get("why") or [])
    why = [w for w in why if not w.startswith("rounded up from")]   # the lot replaces the box rounding
    if is_new:
        why.append("new medicine (first bought %s) -- one lot of %s" % (_dmy(fb), _qw(int(round(lot)), s)))
    elif strips != line["order_strips"]:
        why.append("usual lot %s: %s instead of %s" % (_qw(int(round(lot)), s), _qw(strips * size, s), _qw(line["order_strips"] * size, s)))
    for n in notes:
        if n == "one lot is more than the cover cap":
            line["confirm"] = True
            why.append("one lot is %s days of sale -- more than the cap of %d" % (("%.0f" % ((on_hand + q_units) / rate)) if rate > 0 else "?", cap))
        elif n == "cut to the cover cap":
            why.append("cut to the cover cap of %d days" % cap)
    fr = (s.get("_s470") or {}).get("free")
    if fr and float(fr) > 0:
        why.append("scheme: about %d free per 100 bought" % int(round(float(fr) * 100)))
    line["order_strips"], line["value_p"], line["why"], line["lot_based"] = strips, int(strips * size * (cost_unit or 0)), why, True
    line["lot_units"] = lot


def _s644_interim(con, r, s, p, on_hand, F, today, lead, safety):
    """(horizon, strips) for interim_plan. Fixed: today's test and arithmetic, line for line. Levels: fire only when the stock will not
    last to the next review + lead + margin; then size to the horizon (with safety) through the lot."""
    rate = float(p["rate_per_day"])
    horizon = (F - today).days + lead + safety
    if not _s644_on(con):
        cover = on_hand / rate
        if cover >= horizon:
            return horizon, 0
        need = rate * horizon - on_hand
        return horizon, int(math.ceil(need / float(s["pack_size"])))
    opts = getattr(_S644, "opts", None) or _s644_opts(con) or {}
    if not model_interim_due(on_hand, rate, (F - today).days, lead, opts.get("margin", 1)):
        return horizon, 0
    size = max(1, int(s["pack_size"] or 1))
    need = max(0.0, model_level(rate, horizon, float(p.get("big_day") or 0.0)) - on_hand)
    lot = (s.get("_s470") or {}).get("lot")
    if lot and float(lot) > 0:
        cap = cap_days(con, r) if _s644_learnt(con, r) else int(r.get("cover_cap_days") or 45)
        q, _ = model_qty(need, float(lot), on_hand, rate, cap, False)
        return horizon, int(math.ceil(q / float(size)))
    return horizon, int(math.ceil(need / float(size)))


def _s644_interim_keys(con, line, s, p):
    if _s644_on(con):
        line["model"] = "levels"
        line["rate_long"], line["rate_short"], line["window_end"] = p.get("rate_long"), p.get("rate_short"), p.get("window_end")
        if (s.get("_s470") or {}).get("lot"):
            line["lot_based"] = True


_line_out_before_s644 = _line_out


class _S644NoRound(object):
    """purchase_app with _staff_qty = identity: a lot-based line is NOT rounded to tens (the lot is the shop's own figure)."""
    def __init__(self, pa):
        self._pa = pa

    def __getattr__(self, name):
        if name == "_staff_qty":
            return lambda strips, unit: int(strips)
        return getattr(self._pa, name)


def _line_out(pa, s, it, line, cost_unit, p, why_extra=None):   # noqa: F811
    """S644: a lot-based line keeps its lot quantity (no 10-then-tens); the model keys ride on the row for the owner's eyes."""
    lo = _line_out_before_s644(_S644NoRound(pa) if line.get("lot_based") else pa, s, it, line, cost_unit, p, why_extra)
    for k in ("model", "rate_long", "rate_short", "review_days", "level_days", "window_end", "lot_based", "lot_units"):
        if k in line:
            lo[k] = line[k]
    if "model" not in lo:
        lo["model"] = "fixed"
    return lo


# ------------------------------------------------------------------ the day's stamp and the relist (B.2a, S308 v)
def _s644_stamp_of(note):
    if not note:
        return None
    cap = note.get("capture") or {}
    return json.dumps(dict(sales_through=note.get("sales_through") or "", end_day=cap.get("end_day") or "", spine_built=note.get("spine_built") or ""), sort_keys=True)


def _s644_stamp_day(con, today):
    """After prepare_day: the inputs the list was made from, in order_notice (slot made_through) -- on levels only."""
    if not _s644_on(con):
        return
    st = _s644_stamp_of(_s470_inputs_note())
    if not st:
        return
    con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                (today.isoformat(), "made_through", st, None, now_iso()))
    con.commit()


def _s644_inputs_now(con, today):
    """The three stamps as they stand now, without a plan: one capture read, one reach read, one sp_meta read."""
    SF = _s593_sf()
    sw = _s593_sw().Spine()
    try:
        ctx = SF._ctx(con, sw, None)
        cap = SF.capture_at(sw, today.isoformat(), ctx) or {}
        reach = SF._reach_once(sw, ctx) or {}
        try:
            built = str((sw.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or "")
        except Exception:                                        # noqa: BLE001
            built = ""
        return json.dumps(dict(sales_through=str(reach.get("last_sale") or ""), end_day=cap.get("end_day") or "", spine_built=built), sort_keys=True)
    finally:
        try:
            sw.con.close()
        except Exception:                                        # noqa: BLE001
            pass


def _s644_untouched(con, today):
    """Nobody has touched today's list: every row open / held, no darpan row, no Darpan edit, no line edit on its rows, no call, no print."""
    t = today.isoformat()
    rows = con.execute("SELECT id, status, kind FROM order_proposal WHERE day=?", (t,)).fetchall()
    if any(r[1] not in ("open", "held") or r[2] == "darpan" for r in rows):
        return False
    try:
        if _has(con, "order_darpan_edit") and con.execute("SELECT 1 FROM order_darpan_edit WHERE day=? LIMIT 1", (t,)).fetchone():
            return False
        ids = [str(r[0]) for r in rows]
        if ids and _has(con, "s454_line_edit") and con.execute("SELECT 1 FROM s454_line_edit WHERE src='proposal' AND ref IN (%s) LIMIT 1" % ",".join("?" * len(ids)), ids).fetchone():
            return False
        if _has(con, "purchase_audit") and con.execute("SELECT 1 FROM purchase_audit WHERE substr(at,1,10)=? AND action IN ('s454_call','s454_sheet_printed','s454_marg_pdf_printed','s454_whatsapp_sent','s454_ordered','order_made_s454') LIMIT 1", (t,)).fetchone():
            return False
    except sqlite3.Error:
        return False
    return True


def _s644_relist(con, today, now):
    """Every tick before order.relist_until, on levels: when the day's stamp differs from the inputs now and the list is untouched, the list is
    made again -- rows UPDATED in place by (day, supplier, kind), never deleted; a supplier no longer in the plan keeps its row; the stamp
    moves. A touched list with moved inputs is marked stale for the owner's fold (slot stale). Returns a word for the log."""
    if not _s644_on(con):
        return "off"
    t = today.isoformat()
    until = _setting(con, "order.relist_until", "13:00")
    if now.strftime("%H:%M") >= until:
        return "past %s" % until
    st = con.execute("SELECT text FROM order_notice WHERE day=? AND slot='made_through'", (t,)).fetchone()
    if not st:
        return "no list yet"
    try:
        cur = _s644_inputs_now(con, today)
    except Exception as e:                                       # noqa: BLE001
        return "inputs unreadable: %s" % str(e)[:60]
    if cur == st[0]:
        return "same"
    if not _s644_untouched(con, today):
        con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                    (t, "stale", "the list was touched before newer inputs landed: " + cur, None, now_iso()))
        con.commit()
        return "touched -- stale"
    due = [r["supplier_norm"] for r in rules(con) if is_order_day(con, r, today)]
    fixed = plan(con, today, suppliers=set(due)) if due else dict(vendors={})
    ip = interim_plan(con, today)
    n = 0
    for kind, vendors in (("fixed", fixed.get("vendors") or {}), ("interim", ip.get("vendors") or {})):
        for vn, v in vendors.items():
            if kind == "fixed" and vn not in due:
                continue
            status = "held" if (v.get("held") or v.get("paused")) else "open"
            reason = v.get("paused") or v.get("held") or ("Beech ka order -- agla %s order %s ko" % (_short(v["vendor"]), _dmy(v["next_order_day"])) if kind == "interim" else "")
            row = con.execute("SELECT id, status FROM order_proposal WHERE day=? AND supplier_norm=? AND kind=?", (t, vn, kind)).fetchone()
            if row:
                if row[1] not in ("open", "held"):
                    continue
                con.execute("UPDATE order_proposal SET lines=?, total_p=?, reason=?, status=?, prepared_at=? WHERE id=?",
                            (json.dumps(v["lines"], ensure_ascii=False), v["total_p"], reason, status, now_iso(), row[0]))
            else:
                con.execute("INSERT INTO order_proposal (day, supplier_norm, vendor, kind, status, lines, total_p, reason, prepared_at) VALUES (?,?,?,?,?,?,?,?,?)",
                            (t, vn, v["vendor"], kind, status, json.dumps(v["lines"], ensure_ascii=False), v["total_p"], reason, now_iso()))
            n += 1
    new_st = _s644_stamp_of(_s470_inputs_note()) or cur
    con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                (t, "made_through", new_st, None, now_iso()))
    con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                (t, "relist", "made again at %s: %d rows, inputs %s" % (now.strftime("%H:%M"), n, new_st), None, now_iso()))
    con.commit()
    return "relisted %d" % n


# ------------------------------------------------------------------ the owner's fold (api/rules/state gains `model`) and the field rules
owner_state_before_s644 = owner_state
set_rule_before_s644 = set_rule


def _s644_owner(con, today=None):
    today = today or _today()
    on = _s644_on(con)
    t = today.isoformat()
    out = dict(value="levels" if on else "fixed",
               words=("Levels -- each supplier's own rhythm, the shop's lots, yesterday's sales" if on else "Fixed days -- as before"),
               other=("fixed" if on else "levels"), other_words=("Fixed days -- as before" if on else "Levels -- each supplier's own rhythm, the shop's lots, yesterday's sales"),
               settings=[dict(key=k, value=_setting(con, k, ""), note=SETTINGS[k][1]) for k in S644_KEYS], inputs=_s470_inputs_note(process=True))
    try:
        for slot in ("made_through", "relist", "stale"):
            r = con.execute("SELECT text, at FROM order_notice WHERE day=? AND slot=?", (t, slot)).fetchone()
            out[slot] = dict(text=r[0], at=r[1]) if r else None
    except sqlite3.Error:
        pass
    try:
        import porders_s454                                      # noqa: PLC0415 -- beside this file; the score line is its (S470)
        out["score"] = porders_s454._s470_score_line()
    except Exception:                                            # noqa: BLE001
        out["score"] = ""
    if on:
        rows = []
        for r in rules(con):
            e = _s644_rhythm(con, today).get(r["supplier_norm"]) or {}
            rows.append(dict(supplier=r["short"], mode=r.get("rhythm_mode") or "learnt", interval=review_interval(con, r, today),
                             bill_days90=e.get("bill_days90", r.get("bill_days90")), median_gap=e.get("gap"), last_buy=(last_buy(con, r, today) or dt.date(1970, 1, 1)).isoformat() if _s644_learnt(con, r) else None,
                             next=next_order_day(con, r, today - dt.timedelta(days=1)).isoformat(), cap=cap_days(con, r, today)))
        out["rhythm"] = rows
    return out


def owner_state(con, today=None):                               # noqa: F811
    d = owner_state_before_s644(con, today)
    try:
        d["model"] = _s644_owner(con, today)
    except Exception as e:                                       # noqa: BLE001 -- the fold never breaks the page
        d["model"] = dict(value=_setting(con, "order.model", "fixed"), error=str(e)[:120])
    return d


def set_rule(con, who, supplier_norm, field, value):            # noqa: F811
    """S644: two more fields -- rhythm_mode (learnt | fixed) and review_days (blank = learnt, else review_min..review_max). The rest as before."""
    if field not in ("rhythm_mode", "review_days"):
        return set_rule_before_s644(con, who, supplier_norm, field, value)
    ensure(con)
    r = con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone()
    if not r:
        return dict(ok=False, error="no_such_supplier"), 404
    r = dict(r)
    if field == "rhythm_mode":
        v = str(value or "").strip().lower()
        if v not in ("learnt", "fixed"):
            return dict(ok=False, error="bad_value", message="learnt or fixed"), 400
    else:
        sv = str(value if value is not None else "").strip()
        if sv == "":
            v = None
        else:
            try:
                v = int(sv)
            except ValueError:
                return dict(ok=False, error="bad_value", message="blank, or a whole number of days"), 400
            lo, hi = _s470_days(con, "order.review_min_days"), _s470_days(con, "order.review_max_days")
            if not (lo <= v <= hi):
                return dict(ok=False, error="bad_value", message="%d to %d days, or blank" % (lo, hi)), 400
    owner = _owner_fields(r) | {field}
    _audit(con, who, supplier_norm, field, r.get(field), v)
    con.execute("UPDATE order_supplier_rule SET %s=?, owner_fields=?, updated_at=? WHERE supplier_norm=?" % field, (v, json.dumps(sorted(owner)), now_iso(), supplier_norm))
    con.commit()
    nr = dict(con.execute("SELECT * FROM order_supplier_rule WHERE supplier_norm=?", (supplier_norm,)).fetchone())
    return dict(ok=True, supplier=supplier_norm, changed={field: v}, words=rule_words(con, nr)), 200


reseed_before_s644 = reseed


def reseed(con, today=None, who="seed"):                        # noqa: F811
    """S644: after the seed, the display columns bill_days90 and rhythm_at (the stored rhythm_days stays reseed's); rhythm_mode is never
    rewritten here (its seeding is the columns' creation, once)."""
    n = reseed_before_s644(con, today, who)
    _s644_refresh_columns(con, today)
    return n


def _s644_refresh_columns(con, today=None):
    """The display columns bill_days90 and rhythm_at from one rhythm() read (the installer runs it once; reseed on the 1st). Fail-soft."""
    try:
        rh = rhythm(con, today or _today())
        for sn, e in rh.items():
            con.execute("UPDATE order_supplier_rule SET bill_days90=?, rhythm_at=? WHERE supplier_norm=?", (e.get("bill_days90"), now_iso(), sn))
        con.commit()
        return len(rh)
    except Exception:                                            # noqa: BLE001
        return 0
# ---- S644 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S704 (F-1028, 03-Nov-2026, Sanjeevni session 383): the owner's fold of the levels model -- display only ------------------------------
#  (c) plan(): a line that carries no model word (a carried short-supplied line, built in plan()'s own loop) takes the day's word --
#      before S704 it fell into "fixed" in the score's per-model split on a levels day. No quantity, supplier or rail changes.
#  (a) the inputs the list stood on are kept beside made_through (order_notice slot inputs_note, one row a day): the fold read only the
#      web process's own last note, which exists only after some page ran plan() (the order card, the sheet compare) -- so the line was
#      mostly not drawn, and when it was, it was that page's plan, not the list's. The kept list's note now wins.
#  (b) the relist / stale lines are said in words, not as the raw JSON stamp. The stored texts are unchanged (the relist compares them).
plan_before_s704 = plan
_s644_stamp_day_before_s704 = _s644_stamp_day
_s644_relist_before_s704 = _s644_relist
_s644_owner_before_s704 = _s644_owner


def plan(con, today=None, suppliers=None):                      # noqa: F811
    d = plan_before_s704(con, today, suppliers)
    try:
        word = "levels" if _s644_on(con) else "fixed"
        for v in (d.get("vendors") or {}).values():
            for l in v.get("lines") or []:
                if isinstance(l, dict) and "model" not in l:
                    l["model"] = word
    except Exception:                                            # noqa: BLE001 -- a word for the owner's eyes never breaks a plan
        pass
    return d


def _s704_keep_note(con, today):
    """The note of the plan just made on this thread, kept as today's inputs_note (fail-soft; one row a day, the newest wins)."""
    try:
        note = _s470_inputs_note()
        if not note:
            return
        con.execute("INSERT INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?) ON CONFLICT(day, slot) DO UPDATE SET text=excluded.text, at=excluded.at",
                    (today.isoformat(), "inputs_note", json.dumps(note, default=str, sort_keys=True, ensure_ascii=False), None, now_iso()))
        con.commit()
    except Exception:                                            # noqa: BLE001
        pass


def _s644_stamp_day(con, today):                                # noqa: F811
    _s644_stamp_day_before_s704(con, today)
    _s704_keep_note(con, today)


def _s644_relist(con, today, now):                              # noqa: F811
    r = _s644_relist_before_s704(con, today, now)
    if str(r).startswith("relisted"):
        _s704_keep_note(con, today)
    return r


def _s704_stamp_words(js):
    """The made_through stamp (JSON) in words; None when it is not one."""
    try:
        d = json.loads(js)
    except (TypeError, ValueError):
        return None
    if not isinstance(d, dict):
        return None
    sb = str(d.get("spine_built") or "")
    built = ("%s %s" % (_dmy(sb[:10]), sb[11:16])).strip() if sb else ""
    return "sales to %s \u00b7 Marg's closing of %s \u00b7 spine built %s" % (_dmy(d.get("sales_through")) or "?", _dmy(d.get("end_day")) or "?", built or "?")


_S704_RELIST = re.compile(r"^made again at (\d{1,2}:\d{2}): (\d+) rows, inputs (\{.*\})\s*$")
_S704_STALE = re.compile(r"^the list was touched before newer inputs landed: (\{.*\})\s*$")


def _s704_words(slot, text):
    """A relist / stale text in words; the text as it was when it is not the shape S644 writes."""
    s = str(text or "")
    m = _S704_RELIST.match(s) if slot == "relist" else _S704_STALE.match(s) if slot == "stale" else None
    if not m:
        return text
    w = _s704_stamp_words(m.group(m.lastindex))
    if not w:
        return text
    if slot == "relist":
        n = int(m.group(2))
        return ("Made again at %s on newer figures, %d supplier list%s: %s" % (m.group(1), n, "" if n == 1 else "s", w) if n else
                "Checked again at %s on newer figures; no supplier list to make again: %s" % (m.group(1), w))
    return "Not made again -- the list was already being worked on when newer figures landed: %s" % w


def _s644_owner(con, today=None):                               # noqa: F811
    out = _s644_owner_before_s704(con, today)
    try:
        t = (today or _today()).isoformat()
        r = con.execute("SELECT day, text FROM order_notice WHERE slot='inputs_note' AND day<=? ORDER BY day DESC LIMIT 1", (t,)).fetchone()
        if r:
            note = json.loads(r[1])
            if isinstance(note, dict):
                note["list_day"] = r[0]
                out["inputs"] = note
    except (sqlite3.Error, TypeError, ValueError):
        pass
    for slot in ("relist", "stale"):
        e = out.get(slot)
        if isinstance(e, dict) and e.get("text"):
            e["text"] = _s704_words(slot, e["text"])
    return out
# ---- S704 end ---------------------------------------------------------------------------------------------------------------------------


# ---- S940_ORDER_MESSAGES (23-Nov-2026, Sanjeevni session 509; D1053) ----------------------------------------------------------------------
#  The tick makes and sends the purchase order flow's messages (order_d1053_msg.tick: A sheet in, B final, C sent, D each delivery) after
#  S454's pass, and the old sheet notice gives way to A while the flow is on (order_d1053_msg.install). Any fault: the tick as before.
_s940_s454_pass_before = _s454_pass


def _s454_pass(con):                                         # noqa: F811 -- S940
    try:
        import order_d1053_msg                               # noqa: PLC0415 -- beside this file
        order_d1053_msg.install()
    except Exception as e:                                   # noqa: BLE001
        print("S940 install failed: %r" % (e,), file=sys.stderr)
    out = _s940_s454_pass_before(con)
    try:
        import order_d1053_msg                               # noqa: PLC0415
        r = order_d1053_msg.tick(con)
        if isinstance(out, dict):
            out["d1053"] = r
    except Exception as e:                                   # noqa: BLE001
        if isinstance(out, dict):
            out["d1053"] = "error: %s" % str(e)[:80]
    return out
# ---- S940 end ---------------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":                                   # S454 P1D: last in the file, so every definition above it exists when the
    sys.exit(main(sys.argv))                                 # cron runs this file as a script (part 1 had appended below it)
