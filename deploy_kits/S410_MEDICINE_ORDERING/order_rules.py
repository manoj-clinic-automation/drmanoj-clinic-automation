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
KIT = "S410_MEDICINE_ORDERING"
bp = Blueprint("order_rules", __name__)
_db = _require = None
ACCESS_UNIT = "porders"
HERE = os.path.dirname(os.path.abspath(__file__))
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
    """{supplier_norm: dict(supplier, dates, bills90, gap, amount90_p, avg_month_p, cadence, how)} from 90 days of effective bills."""
    pa = _pa()
    today = today or _today()
    since = (today - dt.timedelta(days=90)).isoformat()
    out = {}
    rows = con.execute("SELECT b.supplier_norm, MAX(b.supplier), b.bill_date, SUM(b.amount_p) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND "
                       + pa.EFF_BILL + " GROUP BY b.supplier_norm, b.bill_date ORDER BY b.supplier_norm, b.bill_date", (since, today.isoformat())).fetchall()
    for sn, sup, d, amt in rows:
        e = out.setdefault(sn, dict(supplier=sup, dates=[], amount90_p=0, bills90=0))
        e["dates"].append(d)
        e["amount90_p"] += int(amt or 0)
        e["supplier"] = sup or e["supplier"]
    nb = con.execute("SELECT b.supplier_norm, COUNT(*) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND " + pa.EFF_BILL + " GROUP BY b.supplier_norm",
                     (since, today.isoformat())).fetchall()
    for sn, n in nb:
        if sn in out:
            out[sn]["bills90"] = int(n)
    minb = _int_setting(con, "order.min_bills_for_rhythm")
    for sn, e in out.items():
        ds = sorted(set(e["dates"]))
        gaps = []
        for i in range(len(ds) - 1):
            try:
                gaps.append((dt.date.fromisoformat(ds[i + 1]) - dt.date.fromisoformat(ds[i])).days)
            except ValueError:
                pass
        e["avg_month_p"] = int(e["amount90_p"] / 3.0)
        e["gap"] = statistics.median(gaps) if gaps else None
        if len(ds) >= minb and gaps:
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
        for sent, arr, billed in con.execute(
                "SELECT o.created_at, l.arrived_at, l.billed_date FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                "WHERE o.status IN ('sent','received') AND o.created_at>=? AND (l.arrived_at IS NOT NULL OR l.billed_date IS NOT NULL)", (since,)):
            pass
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
    if not vals:
        return None, 0
    return int(round(statistics.median(vals))), len(vals)


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
    return dict(ok=True, item=item, rule=rule, on=bool(on), value=value, lists=load_lists()), 200


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
ON_ORDER_DAYS = 4


def _on_order_units(con, today):
    """{norm(item): dict(units, order_id, sent)} -- units on a SENT order of the last ON_ORDER_DAYS days whose line nobody has answered
    yet: on the way, counted as stock so the next morning's interim check does not order them twice."""
    pa = _pa()
    since = (today - dt.timedelta(days=ON_ORDER_DAYS)).isoformat()
    out = {}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.id, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE o.status='sent' AND o.created_at>=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0", (since,)).fetchall()
    except sqlite3.Error:
        return out
    for item, packs, size, oid, created in rows:
        e = out.setdefault(pa.norm(item), dict(units=0, order_id=oid, sent=str(created or "")[:10]))
        e["units"] += int(packs or 0) * int(size or 1)
    return out


def _snapshot_inputs(con, today):
    pa = _pa()
    as_on, snap = pa._latest_snapshot(con)
    pace = pa._pace(con, snap, today)
    purch = pa._last_purchase(con)
    transit = pa._in_transit(con, today)
    onord = _on_order_units(con, today)
    for k, e in onord.items():
        t = transit.setdefault(k, dict(units=0, order_id=e["order_id"], vendor=""))
        t["units"] = int(t.get("units") or 0) + e["units"]
        t["on_way"] = e
    ortho = {pa.norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    return as_on, snap, pace, purch, transit, ortho


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
    return dict(item=s["item"], on_hand=it["on_hand"], qty=rounded, unit=unit, pack_size=s["pack_size"], packing=s.get("packing") or "",
                rate_p=rate_p, per_day=round(p["rate_per_day"], 2), cover_after=cover_after, cover_days=line.get("cover_days"),
                value_p=int(rounded * rate_p), confirm=bool(line.get("confirm")), why=why)


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
        if not vn or vn == ortho_v:
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
        line = pa.plan_line(it, cad)
        line["cover_days"] = cov
        extra = []
        ir = irules.get(k)
        if ir and ir["rule"] == "keep" and ir["value"]:
            want_units = int(ir["value"]) - it["on_hand"] - line["order_strips"] * s["pack_size"]
            if want_units > 0:
                add = int(math.ceil(want_units / float(s["pack_size"])))
                line["order_strips"] += add
                line["value_p"] = int(line["order_strips"] * s["pack_size"] * (cost_unit or 0))
                extra.append("keep-in-stock %d units (your rule)" % int(ir["value"]))
        if ir and ir["rule"] == "max_shelf" and ir["value"] and line["order_strips"] > 0:
            room = int(ir["value"]) - it["on_hand"]
            cap_strips = max(0, room // s["pack_size"])
            if line["order_strips"] > cap_strips:
                extra.append("max on shelf %d units (your rule) -- cut from %d" % (int(ir["value"]), line["order_strips"]))
                line["order_strips"] = cap_strips
        if line["order_strips"] <= 0:
            continue
        if min_line != pa.MIN_LINE_P and line["order_strips"] * s["pack_size"] * cost_unit < min_line and it["on_hand"] > 0:
            continue
        if tr and tr.get("on_way"):
            extra.append("%d units on order #%d (sent %s), not yet received -- counted as stock" % (tr["on_way"]["units"], tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))
        lo = _line_out(pa, s, dict(on_hand=s["qty"]), line, cost_unit, p, extra)
        lo["vendor_norm"] = vn
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
                                   rate_p=rate_p, per_day=None, cover_after=None, cover_days=None, value_p=int(qty * rate_p), confirm=False,
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
    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors, held_items=held_items)


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
        horizon = (F - today).days + lead + safety
        if cover >= horizon:
            continue
        need = p["rate_per_day"] * horizon - on_hand
        strips = int(math.ceil(need / float(s["pack_size"])))
        if strips <= 0:
            continue
        cost_pack = lp.get("rate_p")
        cost_unit = (cost_pack / float(s["pack_size"])) if cost_pack else 0
        why = ["cover %.1f days, the next %s order is %s -- interim for the shortfall" % (cover, _short(lp.get("vendor_disp") or vn), _dmy_short(F))]
        if tr and tr.get("on_way"):
            why.append("%d units on order #%d (sent %s) counted as stock" % (tr["on_way"]["units"], tr["on_way"]["order_id"], _dmy(tr["on_way"]["sent"])))
        line = dict(order_strips=strips, cover_days=horizon, confirm=False, why=why)
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
    _ = pa
    return made


def nightly(con, today=None, who="cron"):
    """05:30: yesterday's unsent proposals merge into each supplier's next order day (one order, never two); on the 1st the
    cadences re-seed (owner-set fields untouched); the new-items log refreshes."""
    today = today or _today()
    ensure(con)
    merged = 0
    for p in con.execute("SELECT id, supplier_norm, day FROM order_proposal WHERE status='open' AND day<?", (today.isoformat(),)).fetchall():
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
        d = day_state(con)
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


def send_notice(con, today, slot, who="cron"):
    """09:00 / 12:00 / 15:00 / 17:00: the contextual text to the ordering team's phones; silent when all are sent; once per slot."""
    ensure(con)
    key = {"prepare": "0900", "remind12": "1200", "remind15": "1500", "remind17": "1700"}.get(slot, slot)
    if con.execute("SELECT 1 FROM order_notice WHERE day=? AND slot=?", (today.isoformat(), key)).fetchone():
        return dict(ok=True, already=True, slot=key)
    text = notice_text(con, today, "prepare" if slot == "prepare" else "remind")
    if not text:
        return dict(ok=True, silent=True, slot=key)
    to = [x.strip().lower() for x in _setting(con, "order.notice_to").split(",") if x.strip()]
    payload = dict(kind="order", title="Purchase orders", body=text, url="/finance/porders", tag="porders", ttl=3600, renotify=True, ts=int(dt.datetime.now().timestamp() * 1000))
    sent = {}
    for u in to:
        try:
            s, f = _push(u, payload)
            sent[u] = dict(sent=s, failed=f)
        except Exception as e:                                # noqa: BLE001
            sent[u] = dict(sent=0, failed=1, error=type(e).__name__)
    con.execute("INSERT OR IGNORE INTO order_notice (day, slot, text, sent, at) VALUES (?,?,?,?,?)", (today.isoformat(), key, text, json.dumps(sent), now_iso()))
    con.commit()
    return dict(ok=True, slot=key, text=text, sent=sent)


def tick(con, now=None):
    """The one cron line's worker: 05:30 nightly · 09:00 prepare + notice · 12:00 / 15:00 / 17:00 reminders; else nothing."""
    now = now or dt.datetime.now()
    forced = os.environ.get("ORDER_TICK", "")
    slot = forced
    if not slot:
        hm = (now.hour, now.minute)
        if hm == SLOTS["nightly"]:
            slot = "nightly"
        elif hm == SLOTS["prepare"]:
            slot = "prepare"
        elif hm in SLOTS["remind"]:
            slot = "remind%d" % now.hour
    today = _today()
    if slot == "nightly":
        return dict(slot=slot, **nightly(con, today))
    if slot == "prepare":
        made = prepare_day(con, today)
        return dict(slot=slot, made=made, notice=send_notice(con, today, "prepare"))
    if slot.startswith("remind"):
        return dict(slot=slot, notice=send_notice(con, today, slot))
    return dict(slot="none")


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
    if p["status"] not in ("open", "held"):
        return dict(ok=False, error="not_open", message="Yeh order ab %s hai." % p["status"]), 409
    r = rule_for(con, p["supplier_norm"])
    if int(r.get("paused") or 0):
        return dict(ok=False, error="paused", message="%s ka order roka hua hai: %s" % (_short(p["vendor"]), r.get("pause_reason") or "")), 409
    try:
        base = {l["item"]: l for l in json.loads(p["lines"] or "[]")}
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
        for p in con.execute("SELECT supplier_norm, vendor, MIN(day), merged_into FROM order_proposal WHERE status='merged' AND merged_into<=? GROUP BY supplier_norm", (today.isoformat(),)):
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
    return jsonify(**day_state(con))


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


if __name__ == "__main__":
    sys.exit(main(sys.argv))
