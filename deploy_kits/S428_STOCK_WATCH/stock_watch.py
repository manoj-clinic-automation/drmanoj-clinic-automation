#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
#  stock_watch.py  ·  v1.0  ·  kit S428_STOCK_WATCH  ·  Session 283 (Sanjeevni)  ·  D633
#
#  THE OWNER, 27-Sep-2026: "A full stock check is only possible on a Sunday -- three hours -- coordinated between Amir
#  and Darpan." "Random and purchase-triggered checks: minimum load in one sitting, three mornings a week, the cap
#  flexible in settings; any item can be selected by me or reported by Darpan." "Auto-selected on movement, turnover,
#  purchase and such metrics." "The arrival is tapped in the purchase app by the responsible staff; provisional stock
#  does not depend on Darpan." "When Darpan flags an unusual loss the system should analyse the sale and purchase
#  history since the last matched stock check and narrow down on human errors." "Over 1% is not recoverable but must be
#  explained; full count once in two months, escalate to monthly or downgrade to quarterly."
#
#  WHAT LIVES HERE (its own tables in finance.db; the spine read-only; mounted from stock_app and stockmatch):
#    3.1  stock_point        -- the ONE table every count writes (full_count · spot · darpan · sales_test · receipt)
#    3.2  stock_count_plan   -- full counts: Sundays only, every count.cadence_months; Amir picks, Darpan confirms;
#                               auto-adjust 2 -> 3 (two good counts) / 2 -> 1 (one bad count), one Needs-you line each
#    3.3  stock_spot_roster  -- three mornings a week (spot.days), <= spot.cap items chosen by a weighted rank over the
#                               spine: turnover, movement, arrival, loss history, value, staleness; the owner's asks first;
#                               a seeded tie-break; the 06:30 job (this file, `job`) or the first read of the day
#    3.4  expected stock     -- latest sp_close + purchases - sales (spine) + PROVISIONAL arrivals (purchase_order_line
#                               tapped, not yet in sp_purchase_line); tap != bill -> the owner's line; no entry after
#                               arrival.bill_grace_days -> Amir's line
#    3.5  stock_trace        -- on every flag and every Big-loss line: seven checks from the anchor to now; verdict
#                               explained / partly / unexplained; the fix line for Amir; unexplained -> Needs you
#    3.6  leakage            -- a month's loss points + count write-offs (allowance, small, big; not consumption) at cost
#                               against the month's sales; green / red against leak.budget_pct; the close-watch list
#  QUANTITIES through qty_words (strips + tabs / pcs / bottles / vials; Hindi patte / goli / nag). No "unit(s)" on a screen.
#  EVERY THRESHOLD IS A SETTING (the `setting` table, audited, the second heading "Counts & watch" on the owner's card).
#  Staff pages never show the budget or a percentage.
#
#  No stock_app import at module level: stock_app imports this file while it is itself being imported. Runnable alone
#  (the 06:30 cron job): `python3 -B stock_watch.py job [--db PATH]` -- it opens finance.db and the spine itself.
# =============================================================================
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys

VERSION = "1.0"
KIT = "S428_STOCK_WATCH"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
SPINE_DB = os.environ.get("SPINE_DB") or os.path.join(HERE, "spine", "spine.db")
DAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
SOURCES = ("full_count", "spot", "darpan", "sales_test", "receipt")
POINT_SOURCE_HI = {"full_count": "poori ginti", "spot": "subah ki ginti", "darpan": "Darpan ne bataya", "sales_test": "bikri se saabit", "receipt": "maal aaya"}

SETTINGS = (
    dict(key="count.cadence_months", label="Full count: every N months", kind="num", default="2", seed="2", lo=0.25, hi=12,
         hint="A full count falls due this many months after the last closed full count's day. Auto-adjust moves it: two good counts running -> 3, one bad count -> 1."),
    dict(key="count.window_sundays", label="Full count: Sundays offered", kind="int", default="4", seed="4", lo=1, hi=8,
         hint="How many Sundays Amir may pick from when a count falls due. No Sunday confirmed by the last one -> one Needs-you line."),
    dict(key="count.auto_adjust", label="Full count: auto-adjust the cadence", kind="choice", default="1", seed="1", choices=(("1", "on"), ("0", "off")),
         hint="Two closed counts running with leakage at or under the good mark -> every 3 months; one count at or over the bad mark -> monthly. Each move is one Needs-you line; the setting stays yours."),
    dict(key="count.good_pct", label="Full count: good leakage (%)", kind="pct", default="1.0", seed="1.0", lo=0, hi=100,
         hint="A closed full count whose written-off loss (allowance + small + big, at cost) is at or under this share of the period's sales counts as good."),
    dict(key="count.bad_pct", label="Full count: bad leakage (%)", kind="pct", default="2.0", seed="2.0", lo=0, hi=100,
         hint="A closed full count at or over this share of sales moves the cadence to monthly."),
    dict(key="spot.days", label="Spot counts: mornings", kind="days", default="MON,WED,SAT", seed="MON,WED,SAT",
         hint="The mornings Darpan gets 'Aaj ki ginti' -- three a week, not a daily chore."),
    dict(key="spot.cap", label="Spot counts: items a morning", kind="int", default="2", seed="2", lo=0, hi=20,
         hint="At most this many items in one sitting. 0 = off. The owner's own asks come first and are never dropped."),
    dict(key="spot.watch_size", label="Close-watch list: items", kind="int", default="20", seed="20", lo=5, hi=100,
         hint="The watch list on your desk: the top items by sales value, the costly ones, and items short at two closed counts."),
    dict(key="spot.high_value_p", label="Costly item: MRP per strip / pc", kind="rupees", default="50000", seed="50000",
         hint="An item whose MRP per strip or piece is this or more scores as costly and joins the watch list."),
    dict(key="spot.repeat_gap_days", label="Spot counts: no repeat within (days)", kind="int", default="7", seed="7", lo=0, hi=60,
         hint="An item counted within this many days is not asked again -- unless it is flagged or you ask for it."),
    dict(key="spot.arrival_days", label="Spot counts: arrival window (days)", kind="int", default="3", seed="3", lo=1, hi=30,
         hint="An item received within this many days and not counted since scores as an arrival."),
    dict(key="spot.w_turnover", label="Weight: turnover", kind="int", default="3", seed="3", lo=0, hi=10, hint="Advanced. Sales value since the item's last stock point."),
    dict(key="spot.w_movement", label="Weight: movement", kind="int", default="2", seed="2", lo=0, hi=10, hint="Advanced. Strips or pcs a day."),
    dict(key="spot.w_arrival", label="Weight: arrival", kind="int", default="3", seed="3", lo=0, hi=10, hint="Advanced. Received within the arrival window and not counted since."),
    dict(key="spot.w_loss", label="Weight: loss history", kind="int", default="3", seed="3", lo=0, hi=10, hint="Advanced. Short at the last closed count (twice for two running)."),
    dict(key="spot.w_value", label="Weight: value", kind="int", default="1", seed="1", lo=0, hi=10, hint="Advanced. MRP per strip / pc at or above the costly mark."),
    dict(key="spot.w_stale", label="Weight: staleness", kind="int", default="2", seed="2", lo=0, hi=10, hint="Advanced. Days since the item's last stock point."),
    dict(key="arrival.bill_grace_days", label="Arrival: bill entry grace (days)", kind="int", default="3", seed="3", lo=1, hi=30,
         hint="A tapped arrival with no purchase in the spine after this many days -> a line on Amir's board: bill entry baaki."),
    dict(key="leak.budget_pct", label="Leakage budget (% of sales)", kind="pct", default="1.0", seed="1.0", lo=0, hi=100,
         hint="A month's loss points + count write-offs (allowance, small, big -- not consumption) at cost, against the month's sales. Over the budget is red."),
    dict(key="leak.red_periods", label="Leakage: red months running -> Needs you", kind="int", default="2", seed="2", lo=1, hi=12,
         hint="This many red months in a row puts one line on your Needs you."),
)
SETTING_BY_KEY = {s["key"]: s for s in SETTINGS}
PREFIXES = ("count.", "spot.", "arrival.", "leak.")

SCHEMA = """
CREATE TABLE IF NOT EXISTS stock_point (
  id INTEGER PRIMARY KEY,                  -- S428 (3.1): THE one table every count writes
  item_norm TEXT NOT NULL, item TEXT NOT NULL, at TEXT NOT NULL,
  qty_units REAL NOT NULL,                 -- what was on the shelf (tabs, or pieces)
  source TEXT NOT NULL,                    -- full_count | spot | darpan | sales_test | receipt
  by TEXT, expected_units REAL, gap_units REAL,
  status TEXT NOT NULL DEFAULT 'settled',  -- settled | provisional
  settled_at TEXT, note TEXT,
  count_id INTEGER, roster_id INTEGER, provisional_units REAL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_point_item ON stock_point(item_norm, at);
CREATE TABLE IF NOT EXISTS stock_count_plan (
  id INTEGER PRIMARY KEY,                  -- S428 (3.2): one full count falling due
  due_from TEXT NOT NULL, sunday TEXT, picked_by TEXT, picked_at TEXT, confirmed_by TEXT, confirmed_at TEXT,
  status TEXT NOT NULL,                    -- open | picked | confirmed | declined | done | lapsed
  window_json TEXT, note TEXT
);
CREATE TABLE IF NOT EXISTS stock_spot_roster (
  id INTEGER PRIMARY KEY,                  -- S428 (3.3): the day's items for Darpan
  day TEXT NOT NULL, item_norm TEXT NOT NULL, item TEXT NOT NULL, reason TEXT, reason_hi TEXT, rank INTEGER,
  asked_at TEXT NOT NULL, answered_at TEXT, qty_units REAL, point_id INTEGER, pack INTEGER, packing TEXT, carried INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_roster_day ON stock_spot_roster(day);
CREATE TABLE IF NOT EXISTS stock_watch_ask (
  id INTEGER PRIMARY KEY,                  -- S428: the owner's 'Count this'
  item_norm TEXT NOT NULL, item TEXT NOT NULL, by TEXT, at TEXT NOT NULL, done_at TEXT, roster_id INTEGER
);
CREATE TABLE IF NOT EXISTS stock_trace (
  id INTEGER PRIMARY KEY,                  -- S428 (3.5): one analysis of one item's gap
  item_norm TEXT NOT NULL, item TEXT NOT NULL, opened_at TEXT NOT NULL, trigger TEXT NOT NULL,
  anchor_at TEXT, window_from TEXT, window_to TEXT, gap_units REAL,
  verdict TEXT NOT NULL,                   -- explained | partly | unexplained
  findings_json TEXT NOT NULL, fix_json TEXT, status TEXT NOT NULL DEFAULT 'open',   -- open | seen | fixed
  seen_by TEXT, seen_at TEXT, count_id INTEGER, pack INTEGER, packing TEXT
);
CREATE INDEX IF NOT EXISTS idx_trace_item ON stock_trace(item_norm, opened_at);
CREATE TABLE IF NOT EXISTS stock_watch_loss_line (
  id INTEGER PRIMARY KEY,                  -- S428: a dated loss line under the pinned staff block ('Aaj: TYRO BR 12 patte kam')
  at TEXT NOT NULL, item TEXT NOT NULL, gap_units REAL NOT NULL, pack INTEGER, packing TEXT, mrp_p INTEGER, point_id INTEGER
);
CREATE TABLE IF NOT EXISTS stock_watch_notice (
  id INTEGER PRIMARY KEY,                  -- S428: a dated one-liner (Needs you / Amir / Darpan), kept
  at TEXT NOT NULL, kind TEXT NOT NULL, for_who TEXT NOT NULL, text TEXT NOT NULL, text_hi TEXT, ref TEXT, until TEXT,
  once_key TEXT                            -- the same line is never written twice (kind + once_key)
);
CREATE TABLE IF NOT EXISTS stock_watch_adjust (
  run_id INTEGER PRIMARY KEY,              -- S428: the auto-adjust looked at this closed count once
  at TEXT NOT NULL, leak_pct REAL, verdict TEXT, cadence_from REAL, cadence_to REAL
);
"""
_TABLES = ("stock_point", "stock_count_plan", "stock_spot_roster", "stock_watch_ask", "stock_trace", "stock_watch_loss_line",
           "stock_watch_notice", "stock_watch_adjust")
AUDIT_TABLE = "stock_watch"


# ------------------------------------------------------------------ small helpers
def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def today():
    return dt.date.today()


def _iso(d):
    return d.isoformat() if isinstance(d, (dt.date, dt.datetime)) else str(d or "")[:10]


def dmy(iso):
    s = str(iso or "")[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4])
    return str(iso or "")


def dmy_to_iso(s):
    t = str(s or "").strip()
    p = t.split("-")
    if len(p) == 3 and len(p[2]) == 4:
        return "%s-%02d-%02d" % (p[2], int(p[1]), int(p[0]))
    return t[:10]


def stamp(ts):
    s = str(ts or "").strip()
    if len(s) >= 16 and s[10] in ("T", " "):
        return "%s %s IST" % (dmy(s[:10]), s[11:16])
    return dmy(s)


def rs(p):
    if p is None:
        return "-"
    neg = p < 0
    n = abs(int(round(p)))
    paise, n = n % 100, n // 100
    s = str(n)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + "Rs " + s + ((".%02d" % paise) if paise else "")


def norm_name(s):
    t = re.sub(r"[^A-Z0-9 ]+", " ", str(s or "").upper())
    return re.sub(r"\s+", " ", t).strip()


def pad_norm(s):
    t = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"[.\s]+$", "", t)


def supkey(vendor):
    return re.sub(r"[^A-Z]", "", str(vendor or "").upper())[:8]


def _qwm():
    import qty_words                                          # noqa: PLC0415 -- beside this file (S427)
    return qty_words


def qw(units, pack=1, packing="", name="", lang="en"):
    return _qwm().words(units, packing=packing, pack=pack, name=name, lang=lang)


def _sa():
    import stock_app                                          # noqa: PLC0415 -- beside this file, loaded first by finance_app
    return stock_app


def ensure(con):
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN (%s)" % ",".join("?" * len(_TABLES)), _TABLES)}
    if len(have) < len(_TABLES):
        con.executescript(SCHEMA)


def _audit(con, action, after, who, row_id=0):
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    (AUDIT_TABLE, int(row_id or 0), action, None, json.dumps(after, sort_keys=True, default=str), who or "", now_iso()))
    except Exception:                                         # noqa: BLE001
        pass


def notice(con, kind, for_who, text, text_hi=None, ref=None, days=7, once_key=None):
    """One dated line, kept; once_key stops the same line being written twice (kind + ref)."""
    ensure(con)
    if once_key is not None:
        r = con.execute("SELECT id FROM stock_watch_notice WHERE kind=? AND once_key=?", (kind, str(once_key))).fetchone()
        if r:
            return int(r[0])
    until = (today() + dt.timedelta(days=days)).isoformat()
    cur = con.execute("INSERT INTO stock_watch_notice (at, kind, for_who, text, text_hi, ref, until, once_key) VALUES (?,?,?,?,?,?,?,?)",
                      (now_iso(), kind, for_who, text, text_hi, str(ref if ref is not None else (once_key or "")), until, (str(once_key) if once_key is not None else None)))
    return int(cur.lastrowid)


# ------------------------------------------------------------------ settings
def setting_raw(con, key):
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and str(r[0]).strip() != "":
            return str(r[0]).strip()
    except Exception:                                         # noqa: BLE001
        pass
    return None


def settings(con):
    out = {}
    for s in SETTINGS:
        raw = setting_raw(con, s["key"])
        out[s["key"]] = raw if raw is not None else s["default"]

    def num(k, d, f=float):
        try:
            return f(float(out[k]))
        except (TypeError, ValueError):
            return d
    days = [d.strip().upper()[:3] for d in str(out["spot.days"]).split(",") if d.strip()]
    return dict(raw=out, cadence_months=max(0.5, num("count.cadence_months", 2.0)), window_sundays=max(1, num("count.window_sundays", 4, int)),
                auto_adjust=str(out["count.auto_adjust"]).strip() not in ("0", "off", "no"), good_pct=num("count.good_pct", 1.0), bad_pct=num("count.bad_pct", 2.0),
                spot_days=[d for d in days if d in DAYS], cap=max(0, num("spot.cap", 2, int)), watch_size=max(1, num("spot.watch_size", 20, int)),
                high_value_p=max(0, num("spot.high_value_p", 50000, int)), repeat_gap_days=max(0, num("spot.repeat_gap_days", 7, int)),
                arrival_days=max(1, num("spot.arrival_days", 3, int)),
                weights=dict(turnover=num("spot.w_turnover", 3, int), movement=num("spot.w_movement", 2, int), arrival=num("spot.w_arrival", 3, int),
                             loss=num("spot.w_loss", 3, int), value=num("spot.w_value", 1, int), stale=num("spot.w_stale", 2, int)),
                bill_grace_days=max(1, num("arrival.bill_grace_days", 3, int)), budget_pct=num("leak.budget_pct", 1.0), red_periods=max(1, num("leak.red_periods", 2, int)))


def _shown(s, v):
    if v is None:
        return "not set"
    k = s["kind"]
    if k == "rupees":
        try:
            return rs(int(float(v)))
        except (TypeError, ValueError):
            return str(v)
    if k == "choice":
        return dict(s["choices"]).get(str(v), str(v))
    if k == "pct":
        try:
            return ("%g" % float(v)) + "%"
        except (TypeError, ValueError):
            return str(v)
    if k == "days":
        return ", ".join(d.strip().title() for d in str(v).split(",") if d.strip())
    return str(v)


def settings_view(con):
    rows = []
    for s in SETTINGS:
        raw = setting_raw(con, s["key"])
        v = raw if raw is not None else s["default"]
        rows.append(dict(key=s["key"], label=s["label"], kind=s["kind"], value=v, shown=_shown(s, v), hint=s["hint"],
                         choices=[dict(v=a, t=b) for a, b in s.get("choices", ())], set=(raw is not None),
                         rupees=(None if s["kind"] != "rupees" else int(float(v)) // 100), heading="Counts & watch"))
    return rows


def set_setting(con, key, value, who):
    s = SETTING_BY_KEY.get(key)
    if not s:
        return False, "Not a setting of the watch."
    v = "" if value is None else str(value).strip()
    if s["kind"] == "choice":
        if v not in [a for a, _b in s["choices"]]:
            return False, "Choose one of: %s." % ", ".join(b for _a, b in s["choices"])
    elif s["kind"] == "rupees":
        try:
            r = float(v.replace(",", "").replace("Rs", "").strip())
        except ValueError:
            return False, "Type an amount in rupees."
        if r < 0 or r > 1000000:
            return False, "Type an amount in rupees."
        v = str(int(round(r * 100)))
    elif s["kind"] in ("pct", "num"):
        try:
            f = float(v.replace("%", "").strip())
        except ValueError:
            return False, "Type a number."
        if f < float(s.get("lo", 0)) or f > float(s.get("hi", 100)):
            return False, "Between %g and %g." % (float(s.get("lo", 0)), float(s.get("hi", 100)))
        v = "%g" % f
    elif s["kind"] == "int":
        try:
            n = int(float(v))
        except ValueError:
            return False, "Type a whole number."
        lo, hi = int(s.get("lo", 0)), int(s.get("hi", 100000))
        if n < lo or n > hi:
            return False, "Between %d and %d." % (lo, hi)
        v = str(n)
    elif s["kind"] == "days":
        ds = [d.strip().upper()[:3] for d in v.replace(";", ",").split(",") if d.strip()]
        if not ds or any(d not in DAYS for d in ds):
            return False, "Days as MON, WED, SAT."
        v = ",".join(dict.fromkeys(ds))
    old = setting_raw(con, key)
    if (old or "") == v:
        return True, "No change."
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                (key, v, "S428 stock watch setting: %s" % s["label"]))
    try:
        con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                    ("setting", 0, "stock_setting", json.dumps(dict(key=key, value=old)), json.dumps(dict(key=key, value=v, label=s["label"])), who or "", now_iso()))
    except Exception:                                         # noqa: BLE001
        pass
    con.commit()
    return True, "%s set." % s["label"]


def seed(con, who="S428"):
    wrote = []
    for s in SETTINGS:
        if setting_raw(con, s["key"]) is not None or s["seed"] is None:
            continue
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, note=excluded.note",
                    (s["key"], s["seed"], "S428 stock watch setting: %s (seeded)" % s["label"]))
        try:
            con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                        ("setting", 0, "stock_setting", json.dumps(dict(key=s["key"], value=None)),
                         json.dumps(dict(key=s["key"], value=s["seed"], label=s["label"], seeded=True)), who, now_iso()))
        except Exception:                                     # noqa: BLE001
            pass
        wrote.append(s["key"])
    con.commit()
    return wrote


# ------------------------------------------------------------------ the spine (read-only) and the items
def _k20(name):
    return re.sub(r"\s+", " ", str(name or "").strip())[:20].strip()


class Spine(object):
    def __init__(self, path=None):
        self.ok, self.con, self._alias = False, None, {}
        p = path or SPINE_DB
        try:
            if os.path.exists(p):
                self.con = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
                self.con.row_factory = sqlite3.Row
                self._alias = {r["alias"]: r["k20"] for r in self.con.execute("SELECT alias, k20 FROM sp_alias")}
                self.ok = True
        except sqlite3.Error:
            self.ok, self.con = False, None

    def key(self, name):
        k = _k20(name)
        return self._alias.get(k, k)

    def q(self, s, *a):
        return [dict(r) for r in self.con.execute(s, a).fetchall()] if self.ok else []

    def item(self, name):
        rows = self.q("SELECT name, packing, unit_kind, k20 FROM sp_item WHERE k20=? ORDER BY last_seen DESC LIMIT 1", self.key(name))
        return rows[0] if rows else None

    def items(self):
        return self.q("SELECT k20, name, packing, unit_kind FROM sp_item ORDER BY name")

    def search(self, q, limit=12):
        if not q:
            return []
        like = "%" + re.sub(r"\s+", "%", q.strip().upper()) + "%"
        return self.q("SELECT name, packing, unit_kind FROM sp_item WHERE UPPER(name) LIKE ? GROUP BY name ORDER BY name LIMIT ?", like, int(limit))

    def close(self, name, as_on=None):
        d = as_on or today().isoformat()
        r = self.q("SELECT as_on, units FROM sp_close WHERE k20=? AND as_on<=? ORDER BY as_on DESC LIMIT 1", self.key(name), d)
        return (r[0]["as_on"], float(r[0]["units"] or 0)) if r else (None, None)

    def latest_close_day(self):
        r = self.q("SELECT MAX(as_on) AS d FROM sp_close")
        return r[0]["d"] if r and r[0]["d"] else None

    def sales(self, name, d_from, d_to, incl_from=False):
        op = ">=" if incl_from else ">"
        r = self.q("SELECT COALESCE(SUM(units),0) AS u, COALESCE(SUM(CASE WHEN units<0 THEN -units ELSE 0 END),0) AS ret, "
                   "COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v, COUNT(*) AS n, "
                   "COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%%' THEN units ELSE 0 END),0) AS loose "
                   "FROM sp_sale_line WHERE k20=? AND date %s ? AND date<=?" % op, self.key(name), d_from, d_to)
        return r[0] if r else dict(u=0, ret=0, v=0, n=0, loose=0)

    def purchases(self, name, d_from, d_to, incl_from=False):
        op = ">=" if incl_from else ">"
        return self.q("SELECT supkey, bill, date, qty, free, units, direction, packing FROM sp_purchase_line WHERE k20=? AND date %s ? AND date<=? ORDER BY date" % op,
                      self.key(name), d_from, d_to)

    def purchases_net(self, name, d_from, d_to, incl_from=False):
        return sum((-float(p["units"] or 0) if p["direction"] == "RETURN" else float(p["units"] or 0)) for p in self.purchases(name, d_from, d_to, incl_from))

    def mrp_p(self, name):
        """MRP per strip / piece in paise (the spine's latest fact), or None."""
        it = self.item(name)
        if not it:
            return None
        r = self.q("SELECT value FROM sp_item_fact WHERE name=? AND packing=? AND fact='mrp' ORDER BY as_on DESC LIMIT 1", it["name"], it["packing"])
        try:
            return int(round(float(r[0]["value"]) * 100)) if r else None
        except (TypeError, ValueError):
            return None

    def salt(self, name):
        it = self.item(name)
        if not it:
            return ""
        r = self.q("SELECT value FROM sp_item_fact WHERE name=? AND packing=? AND fact='salt' ORDER BY as_on DESC LIMIT 1", it["name"], it["packing"])
        return (r[0]["value"] or "") if r else ""

    def sales_month(self, ym):
        r = self.q("SELECT COALESCE(SUM(net_p),0) AS p FROM sp_sale_bill WHERE substr(date,1,7)=?", ym)
        return int(r[0]["p"] or 0) if r else 0


def pack_of(packing, pack=None):
    return _qwm().pack_of(packing, pack)


def item_info(con, sp, name):
    """(item as the spine names it, pack, packing, unit_kind) -- the spine first, the count's snapshot next."""
    it = sp.item(name) if sp.ok else None
    if it:
        return dict(item=it["name"], pack=pack_of(it["packing"]), packing=it["packing"] or "", unit_kind=it["unit_kind"] or "")
    try:
        r = con.execute("SELECT item, packing, pack_size FROM stock_snapshot WHERE item=? ORDER BY as_on DESC LIMIT 1", (name,)).fetchone()
        if r:
            return dict(item=r[0], pack=int(r[2] or pack_of(r[1])), packing=r[1] or "", unit_kind="")
    except sqlite3.Error:
        pass
    return dict(item=name, pack=1, packing="", unit_kind="")


# ------------------------------------------------------------------ 3.2 full counts: the plan
def last_full_count(con):
    """(count_id, as_on_iso, closed_at) of the last CLOSED whole-shop count that counts for the cadence: the S428 baseline
    (every closed count before the plan existed) or a count begun on a confirmed Sunday. A count on another day is spot
    points and does not move the cadence."""
    ensure(con)
    try:
        rows = con.execute("SELECT c.id, c.marg_as_on, k.closed_at FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id "
                           "WHERE c.status='submitted' AND c.id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY c.id DESC").fetchall()
    except sqlite3.Error:
        return None
    first_plan = con.execute("SELECT MIN(due_from) FROM stock_count_plan").fetchone()[0]
    confirmed = {r[0] for r in con.execute("SELECT sunday FROM stock_count_plan WHERE status IN ('confirmed','done') AND sunday IS NOT NULL")}
    for cid, as_on, closed in rows:
        iso = dmy_to_iso(as_on)
        if not first_plan or iso < first_plan or iso in confirmed:
            return dict(count_id=int(cid), as_on=iso, closed_at=closed)
    return None


def _add_months(d, months):
    m = d.month - 1 + int(months)
    y = d.year + m // 12
    m = m % 12 + 1
    day = min(d.day, [31, 29 if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    frac = float(months) - int(months)
    return dt.date(y, m, day) + dt.timedelta(days=int(round(frac * 30)))


def _sundays_from(d, n):
    out, x = [], d
    while x.weekday() != 6:
        x += dt.timedelta(days=1)
    for _i in range(n):
        out.append(x.isoformat()); x += dt.timedelta(days=7)
    return out


def plan_state(con, S=None, who="system"):
    """The plan as it stands -- opened when a count falls due; lapsed when the window passes unconfirmed; done when a
    count on its Sunday closes. Reads and, narrowly, writes (the opening and the lapse), audited."""
    ensure(con)
    S = S or settings(con)
    last = last_full_count(con)
    t = today()
    due_from = _add_months(dt.date.fromisoformat(last["as_on"]), S["cadence_months"]) if last else t
    cur = con.execute("SELECT * FROM stock_count_plan WHERE status IN ('open','picked','confirmed') ORDER BY id DESC LIMIT 1").fetchone()
    cur = dict(zip([c[0] for c in con.execute("SELECT * FROM stock_count_plan LIMIT 0").description], cur)) if cur else None
    if cur:
        win = json.loads(cur.get("window_json") or "[]")
        if cur["status"] == "confirmed" and cur["sunday"] and cur["sunday"] < t.isoformat() and last and last["as_on"] >= cur["sunday"]:
            con.execute("UPDATE stock_count_plan SET status='done' WHERE id=?", (cur["id"],)); con.commit(); cur = None
        elif cur["status"] in ("open", "picked") and win and win[-1] < t.isoformat():
            con.execute("UPDATE stock_count_plan SET status='lapsed', note=? WHERE id=?", ("no Sunday confirmed by %s" % dmy(win[-1]), cur["id"])); con.commit()
            notice(con, "plan_lapsed", "owner", "Full count: no Sunday was confirmed by %s -- Amir picks a new one on his board" % dmy(win[-1]),
                   once_key="plan_lapsed:%d" % cur["id"], days=14)
            cur = None
    if not cur and t >= due_from:
        win = _sundays_from(max(t, due_from), S["window_sundays"])
        cur_id = con.execute("INSERT INTO stock_count_plan (due_from, status, window_json) VALUES (?,?,?)", (due_from.isoformat(), "open", json.dumps(win))).lastrowid
        _audit(con, "plan_open", dict(due_from=due_from.isoformat(), window=win), who, cur_id)
        con.commit()
        cur = dict(id=cur_id, due_from=due_from.isoformat(), sunday=None, picked_by=None, picked_at=None, confirmed_by=None, confirmed_at=None, status="open", window_json=json.dumps(win), note=None)
    out = dict(last=last, due_from=due_from.isoformat(), due=(t >= due_from), cadence_months=S["cadence_months"], plan=None, today=t.isoformat())
    if cur:
        win = json.loads(cur.get("window_json") or "[]")
        out["plan"] = dict(id=cur["id"], status=cur["status"], due_from=cur["due_from"], window=win, window_text=[dmy(w) for w in win],
                           sunday=cur["sunday"], sunday_text=dmy(cur["sunday"]) if cur["sunday"] else "", picked_by=cur["picked_by"] or "", picked_at=cur["picked_at"] or "",
                           confirmed_by=cur["confirmed_by"] or "", confirmed_at=cur["confirmed_at"] or "", note=cur.get("note") or "",
                           is_sunday_today=(cur["sunday"] == t.isoformat() and cur["status"] == "confirmed"))
    return out


def plan_pick(con, sunday, who):
    """Amir picks a Sunday from the window ('Ginti ka Sunday chunein')."""
    P = plan_state(con)
    p = P.get("plan")
    if not p:
        return False, "Koi ginti abhi due nahi hai.", 400
    if p["status"] == "confirmed":
        return False, "Darpan ne %s ke liye haan kah diya hai." % p["sunday_text"], 409
    if sunday not in p["window"]:
        return False, "Yeh Sunday list mein nahi hai.", 400
    ts = now_iso()
    con.execute("UPDATE stock_count_plan SET sunday=?, picked_by=?, picked_at=?, status='picked', confirmed_by=NULL, confirmed_at=NULL WHERE id=?", (sunday, who, ts, p["id"]))
    _audit(con, "plan_pick", dict(sunday=sunday), who, p["id"])
    con.commit()
    return True, "Sunday %s chuna -- ab Darpan ki haan chahiye." % dmy(sunday), 200


def plan_answer(con, answer, who):
    """Darpan: 'Theek hai' confirms; 'Nahi ho payega' sends it back to Amir."""
    P = plan_state(con)
    p = P.get("plan")
    if not p or p["status"] not in ("picked", "confirmed"):
        return False, "Abhi koi Sunday chuna nahi gaya.", 400
    ts = now_iso()
    if answer == "ok":
        if p["status"] == "confirmed":
            return True, "Pehle hi haan kah diya hai.", 200
        con.execute("UPDATE stock_count_plan SET status='confirmed', confirmed_by=?, confirmed_at=? WHERE id=?", (who, ts, p["id"]))
        _audit(con, "plan_confirm", dict(sunday=p["sunday"]), who, p["id"])
        notice(con, "plan_confirmed", "owner", "Full count confirmed for Sunday %s (Amir picked, Darpan said yes)" % p["sunday_text"],
               "Poori ginti Sunday %s ko -- Amir aur Darpan dono taiyaar" % p["sunday_text"], once_key="plan_confirmed:%d:%s" % (p["id"], p["sunday"]), days=60)
        con.commit()
        return True, "Theek hai -- Sunday %s ko poori ginti." % p["sunday_text"], 200
    if answer == "no":
        con.execute("UPDATE stock_count_plan SET status='open', sunday=NULL, picked_by=NULL, picked_at=NULL, confirmed_by=NULL, confirmed_at=NULL, note=? WHERE id=?",
                    ("Darpan: %s nahi ho payega (%s)" % (p["sunday_text"], ts[:16]), p["id"]))
        _audit(con, "plan_decline", dict(sunday=p["sunday"]), who, p["id"])
        con.commit()
        return True, "Amir ko wapas -- doosra Sunday chunenge.", 200
    return False, "Theek hai ya Nahi ho payega.", 400


def auto_adjust(con, S=None, who="system"):
    """After each closed full count with a frozen run: leakage = the run's allowance + small + big at cost against the
    period's sales (spine, at sale value). Two good counts running -> cadence 3; one bad -> 1. Each move audited, one
    Needs-you line, the setting the owner's to reset. Looks at each run once."""
    ensure(con)
    S = S or settings(con)
    if not S["auto_adjust"]:
        return None
    try:
        runs = con.execute("SELECT r.id, r.count_id, r.at, r.groups, c.marg_as_on FROM stock_writeoff_run r JOIN stock_count c ON c.id=r.count_id "
                           "WHERE r.id NOT IN (SELECT run_id FROM stock_watch_adjust) ORDER BY r.id").fetchall()
    except sqlite3.Error:
        return None
    sp = Spine()
    out = None
    for rid, cid, at, groups, as_on in runs:
        try:
            g = json.loads(groups)
        except ValueError:
            continue
        if not any(k in g for k in ("allowance", "small", "big")):
            continue
        loss_p = sum((x.get("cost_p") or x.get("mrp_p") or 0) for k in ("allowance", "small", "big") for x in g.get(k, []))
        as_iso = dmy_to_iso(as_on)
        # the period = from the latest closed count BEFORE this one's day (by day, not by row order) to this one's day
        prevs = [dmy_to_iso(r[0]) for r in con.execute("SELECT c.marg_as_on FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id WHERE c.id<>? AND c.id NOT IN (SELECT count_id FROM stock_count_part)", (cid,))]
        prevs = [p for p in prevs if p < as_iso]
        frm = max(prevs) if prevs else (dt.date.fromisoformat(as_iso) - dt.timedelta(days=180)).isoformat()
        sales_p = 0
        if sp.ok:
            r = sp.q("SELECT COALESCE(SUM(net_p),0) AS p FROM sp_sale_bill WHERE date>? AND date<=?", frm, as_iso)
            sales_p = int(r[0]["p"] or 0) if r else 0
        pct = (100.0 * loss_p / sales_p) if sales_p else None
        verdict = "unknown" if pct is None else ("bad" if pct >= S["bad_pct"] else ("good" if pct <= S["good_pct"] else "middle"))
        c_from = S["cadence_months"]; c_to = c_from
        if verdict == "bad" and c_from > 1:
            c_to = 1.0
        elif verdict == "good":
            prev_good = con.execute("SELECT verdict FROM stock_watch_adjust ORDER BY run_id DESC LIMIT 1").fetchone()
            if prev_good and prev_good[0] == "good" and c_from < 3:
                c_to = 3.0
        con.execute("INSERT OR IGNORE INTO stock_watch_adjust (run_id, at, leak_pct, verdict, cadence_from, cadence_to) VALUES (?,?,?,?,?,?)",
                    (rid, now_iso(), pct, verdict, c_from, c_to))
        if c_to != c_from:
            set_setting(con, "count.cadence_months", "%g" % c_to, who)
            word = "monthly" if c_to == 1 else ("every 3 months" if c_to == 3 else "every %g months" % c_to)
            notice(con, "cadence", "owner", "Full count moved to %s: the count of %s lost %.1f%% of sales%s" % (
                word, dmy(as_iso), pct or 0, " (two good counts running)" if verdict == "good" else ""), once_key="cadence:%d" % rid, days=30)
            S = settings(con)
        con.commit()
        out = dict(run_id=rid, pct=pct, verdict=verdict, cadence_from=c_from, cadence_to=c_to)
    return out


# ------------------------------------------------------------------ 3.4 expected stock, provisional arrivals
def _arrivals(con, item, since_iso, sp):
    """Tapped arrivals of the item after since_iso (purchase_order_line, supplied packs x pack_size) with the supplier,
    each marked whether the spine already carries a purchase of the item from that supplier after the tap's order day."""
    out = []
    try:
        keys = {pad_norm(item[:27]), pad_norm(item)}
        for r in con.execute("SELECT l.id, l.item, l.packs, l.pack_size, l.supplied, l.arrived_at, l.arrived_by, l.billed_qty, l.billed_bill_no, o.vendor, o.created_at, o.id "
                             "FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.arrived_at IS NOT NULL AND l.arrived_at>? AND l.supplied>0",
                             (since_iso,)):
            if pad_norm(str(r[1])[:27]) not in keys and pad_norm(r[1]) not in keys:
                continue
            units = float(r[4] or 0) * float(r[3] or 1)
            sk = supkey(r[9])
            in_spine = False
            if sp.ok:
                rows = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", sp.key(item), sk, str(r[10])[:10])
                in_spine = bool(rows and rows[0]["n"])
            out.append(dict(line_id=r[0], item=r[1], packs=int(r[2] or 0), pack_size=int(r[3] or 1), supplied=int(r[4] or 0), units=units, arrived_at=r[5], arrived_by=r[6] or "",
                            billed_qty=r[7], billed_bill_no=r[8] or "", vendor=r[9] or "", supkey=sk, order_id=r[11], order_at=r[10], in_spine=in_spine))
    except sqlite3.Error:
        pass
    return out


def expected_units(con, sp, item):
    """The stock the records say should be on the shelf now: the latest Marg closing (spine) - sales since + purchases
    since (net of returns) + PROVISIONAL tapped arrivals the spine does not yet carry. Returns dict."""
    as_on, close = sp.close(item) if sp.ok else (None, None)
    t = today().isoformat()
    if as_on is None:
        return dict(expected=None, provisional=0.0, as_on=None, close=None, sold=0.0, bought=0.0, terms=[])
    s = sp.sales(item, as_on, t)
    bought = sp.purchases_net(item, as_on, t)
    prov = 0.0
    terms = []
    for a in _arrivals(con, item, as_on, sp):
        if not a["in_spine"]:
            prov += a["units"]
            terms.append(dict(kind="arrival_tap", units=a["units"], vendor=a["vendor"], at=a["arrived_at"], by=a["arrived_by"]))
    exp = float(close) - float(s["u"] or 0) + float(bought) + prov
    return dict(expected=exp, provisional=prov, as_on=as_on, close=float(close), sold=float(s["u"] or 0), bought=float(bought), terms=terms)


def allowance_units(con, item, pack, since_iso, sp):
    """S427's allowance, pro rata: stock.allowance_pct % of the item's own sales since its last point (floor 1 strip / pc)."""
    try:
        import loss_piles                                     # noqa: PLC0415
        LS = loss_piles.settings(con)
        pct, floor = LS["allowance_pct"], LS["allowance_min_strips"]
    except Exception:                                         # noqa: BLE001
        pct, floor = 1.0, 1
    sold = float(sp.sales(item, since_iso, today().isoformat())["u"] or 0) if sp.ok else 0.0
    return max(int(pct / 100.0 * sold), floor * (pack if pack > 1 else 1)), sold


def last_point(con, item_norm, settled_only=False, gap_zero=False):
    q = "SELECT id, at, qty_units, expected_units, gap_units, status, source, by FROM stock_point WHERE item_norm=?"
    if settled_only:
        q += " AND status='settled'"
    if gap_zero:
        q += " AND gap_units=0"
    r = con.execute(q + " ORDER BY at DESC, id DESC LIMIT 1", (item_norm,)).fetchone()
    return dict(id=r[0], at=r[1], qty=r[2], expected=r[3], gap=r[4], status=r[5], source=r[6], by=r[7]) if r else None


def write_point(con, item, qty_units, source, who, roster_id=None, note=None, sp=None, count_id=None, silent=False):
    """ONE stock point: expected from the records (provisional if an arrival term is provisional), the gap, and what
    follows -- a short within the item's allowance is a quiet loss point; a larger one is a dated loss line under the
    staff block and on the owner's watch card; a surplus is noted. Returns the point row."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]
    E = expected_units(con, sp, item)
    ts = now_iso()
    gap = None if E["expected"] is None else round(float(qty_units) - E["expected"], 3)
    status = "provisional" if E["provisional"] else "settled"
    cur = con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, note, count_id, roster_id, provisional_units) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (norm_name(item), item, ts, float(qty_units), source, who or "", E["expected"], gap, status, (ts if status == "settled" else None), note, count_id, roster_id, E["provisional"]))
    pid = int(cur.lastrowid)
    P = dict(id=pid, item=item, pack=info["pack"], packing=info["packing"], qty=float(qty_units), expected=E["expected"], gap=gap, status=status, provisional=E["provisional"],
             qty_text=qw(qty_units, info["pack"], info["packing"], item), qty_hi=qw(qty_units, info["pack"], info["packing"], item, "hi"),
             gap_text=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item)), gap_hi=("" if gap is None else qw(abs(gap), info["pack"], info["packing"], item, "hi")),
             verdict="", verdict_hi="", loss_line=None, trace=None)
    if gap is None:
        P["verdict"], P["verdict_hi"] = "no Marg figure for this item yet -- counted and kept", "Marg mein yeh item nahi mila -- ginti likh li"
    elif gap == 0:
        P["verdict"], P["verdict_hi"] = "matches the records", "Marg se barabar"
    elif gap > 0:
        P["verdict"], P["verdict_hi"] = "%s more than the records -- noted, never a loss" % P["gap_text"], "%s zyada -- likh liya" % P["gap_hi"]
    else:
        lp = last_point(con, norm_name(item))
        since = (lp["at"][:10] if lp and lp["id"] != pid else (E["as_on"] or (today() - dt.timedelta(days=30)).isoformat()))
        allow, sold = allowance_units(con, item, info["pack"], since, sp)
        if abs(gap) <= allow:
            P["verdict"], P["verdict_hi"] = "%s short -- within the allowance, written as a small loss" % P["gap_text"], "%s kam -- thoda hai, likh liya" % P["gap_hi"]
        else:
            mrp = sp.mrp_p(item) if sp.ok else None
            per = (mrp / max(1, info["pack"])) if mrp else None
            mrp_gap = int(round(per * abs(gap))) if per else None
            lid = con.execute("INSERT INTO stock_watch_loss_line (at, item, gap_units, pack, packing, mrp_p, point_id) VALUES (?,?,?,?,?,?,?)",
                              (ts, item, abs(gap), info["pack"], info["packing"], mrp_gap, pid)).lastrowid
            P["loss_line"] = int(lid)
            P["verdict"], P["verdict_hi"] = "%s short -- a loss, written by name" % P["gap_text"], "%s kam -- naam se likh liya" % P["gap_hi"]
            if not silent:
                try:
                    P["trace"] = open_trace(con, item, "point", gap, who, sp=sp, point_id=pid)["id"]
                except Exception:                             # noqa: BLE001
                    P["trace"] = None
    _audit(con, "point", dict(item=item, qty=float(qty_units), source=source, expected=E["expected"], gap=gap, status=status, text="%s: %s counted (%s), %s" % (item, P["qty_text"], source, P["verdict"])), who, pid)
    con.commit()
    return P


def settle_provisional(con, sp=None):
    """A provisional point whose arrival the spine now carries is re-evaluated and settled. Idempotent."""
    ensure(con)
    sp = sp or Spine()
    n = 0
    for r in con.execute("SELECT id, item, qty_units FROM stock_point WHERE status='provisional'").fetchall():
        E = expected_units(con, sp, r[1])
        if E["provisional"]:
            continue
        gap = None if E["expected"] is None else round(float(r[2]) - E["expected"], 3)
        con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, status='settled', settled_at=?, provisional_units=0 WHERE id=?", (E["expected"], gap, now_iso(), r[0]))
        n += 1
    if n:
        con.commit()
    return n


def tap_vs_bill_lines(con):
    """S403's ordered-vs-supplied log, read: a tapped arrival whose Marg bill quantity differs -- the owner's line."""
    out = []
    try:
        for r in con.execute("SELECT l.item, l.supplied, l.billed_qty, l.billed_bill_no, l.pack_size, l.arrived_at, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE l.arrived_at IS NOT NULL AND l.billed_qty IS NOT NULL AND l.supplied IS NOT NULL AND l.billed_qty<>l.supplied ORDER BY l.arrived_at DESC LIMIT 20"):
            ps = int(r[4] or 1)
            out.append(dict(item=r[0], vendor=r[6] or "", tap=int(r[1] or 0), bill=int(r[2] or 0), bill_no=r[3] or "", at=r[5], at_text=stamp(r[5]),
                            text="%s: tap %s, bill %s%s" % (r[0], qw(int(r[1] or 0) * ps, ps, "", r[0]), qw(int(r[2] or 0) * ps, ps, "", r[0]), (" (bill %s)" % r[3]) if r[3] else "")))
    except sqlite3.Error:
        pass
    return out


def bill_pending_lines(con, S=None, sp=None):
    """A tapped arrival with no purchase in the spine after arrival.bill_grace_days -> Amir's line 'bill entry baaki'."""
    S = S or settings(con)
    sp = sp or Spine()
    out = []
    cutoff = (dt.datetime.now() - dt.timedelta(days=S["bill_grace_days"])).replace(microsecond=0).isoformat()
    try:
        rows = con.execute("SELECT l.item, l.supplied, l.pack_size, l.arrived_at, o.vendor, o.created_at, l.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE l.arrived_at IS NOT NULL AND l.arrived_at<? AND l.supplied>0 ORDER BY l.arrived_at", (cutoff,)).fetchall()
    except sqlite3.Error:
        return out
    seen = set()
    for item, supplied, ps, arrived, vendor, created, lid in rows:
        if not sp.ok:
            break
        sk = supkey(vendor)
        n = sp.q("SELECT COUNT(*) AS n FROM sp_purchase_line WHERE k20=? AND supkey=? AND date>=?", sp.key(item), sk, str(created)[:10])
        if n and n[0]["n"]:
            continue
        key = (sk, str(arrived)[:10])
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(vendor=vendor or "", date=str(arrived)[:10], date_text=dmy(str(arrived)[:10]), item=item,
                        text_hi="bill entry baaki: %s %s" % (vendor or "", dmy(str(arrived)[:10])), text="bill entry pending: %s, arrival tapped %s" % (vendor or "", dmy(str(arrived)[:10]))))
    return out


# ------------------------------------------------------------------ 3.3 the roster
def _spot_day(S, d=None):
    d = d or today()
    return DAYS[d.weekday()] in S["spot_days"]


def _candidates(con, sp, S):
    """Every countable item of the spine with its metrics. Countable: packing known; a strip item sold mostly whole
    (loose share under 50% over 90 days) or a WHOLE item."""
    t = today()
    d90 = (t - dt.timedelta(days=90)).isoformat()
    last_fc = last_full_count(con)
    short_last = {}
    if last_fc:
        for r in con.execute("SELECT item, diff FROM stock_diff WHERE count_id=? AND diff<0", (last_fc["count_id"],)):
            short_last[norm_name(r[0])] = -int(r[1])
    points = {}
    for r in con.execute("SELECT item_norm, MAX(at) FROM stock_point GROUP BY item_norm"):
        points[r[0]] = r[1]
    recent_po = {}
    try:
        for r in con.execute("SELECT item, MAX(arrived_at) FROM purchase_order_line WHERE arrived_at IS NOT NULL AND supplied>0 GROUP BY item"):
            recent_po[norm_name(r[0])] = str(r[1])[:10]
    except sqlite3.Error:
        pass
    sales_all = {}
    for r in sp.q("SELECT k20, COALESCE(SUM(units),0) AS u, COALESCE(SUM(CASE WHEN qty_raw LIKE '0:%' THEN units ELSE 0 END),0) AS loose, "
                  "COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v "
                  "FROM sp_sale_line WHERE date>=? GROUP BY k20", d90):
        sales_all[r["k20"]] = r
    purch_recent = {}
    arr_from = (t - dt.timedelta(days=S["arrival_days"])).isoformat()
    for r in sp.q("SELECT k20, MAX(date) AS d FROM sp_purchase_line WHERE date>=? AND direction<>'RETURN' GROUP BY k20", arr_from):
        purch_recent[r["k20"]] = r["d"]
    mrps = {}
    for r in sp.q("SELECT i.k20, f.value FROM sp_item i JOIN sp_item_fact f ON f.name=i.name AND f.packing=i.packing AND f.fact='mrp' ORDER BY f.as_on"):
        try:
            mrps[r["k20"]] = int(round(float(r["value"]) * 100))
        except (TypeError, ValueError):
            pass
    out = {}
    for it in sp.items():
        k = it["k20"]
        if k in out:
            continue
        pack = pack_of(it["packing"])
        if not it["packing"] or (pack <= 1 and (it["unit_kind"] or "") not in ("WHOLE", "LOOSE")):
            continue
        s = sales_all.get(k) or dict(u=0, loose=0, v=0)
        u = float(s["u"] or 0)
        loose_share = (float(s["loose"] or 0) / u) if u > 0 else 0.0
        countable = (it["unit_kind"] == "WHOLE") or (loose_share < 0.5)
        nm = norm_name(it["name"])
        lp = points.get(nm)
        lp_day = lp[:10] if lp else (last_fc["as_on"] if last_fc else d90)
        since_days = max(1, (t - dt.date.fromisoformat(lp_day)).days)
        arrival = purch_recent.get(k) or recent_po.get(nm)
        if arrival and lp and lp[:10] >= arrival:
            arrival = None
        mrp = mrps.get(k)
        out[k] = dict(item=it["name"], k20=k, pack=pack, packing=it["packing"] or "", unit_kind=it["unit_kind"] or "", countable=countable, loose_share=round(loose_share, 3),
                      turnover=float(s["v"] or 0) * min(1.0, since_days / 90.0), movement=(u / max(1, pack)) / 90.0, arrival=1 if arrival else 0, arrival_day=arrival,
                      loss=short_last.get(nm, 0), value=1 if (mrp and mrp >= S["high_value_p"]) else 0, mrp_p=mrp, stale=since_days, last_point=lp)
    return out


def _rank_scores(cands, S):
    """Weighted rank-sum: each metric ranked high-to-low (ties share), scaled to [0, 1], times its weight."""
    W = S["weights"]
    keys = ("turnover", "movement", "arrival", "loss", "value", "stale")
    ks = list(cands)
    n = max(1, len(ks))
    score = {k: 0.0 for k in ks}
    for m in keys:
        if not W.get(m):
            continue
        order = sorted(ks, key=lambda k: -float(cands[k][m] or 0))
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and cands[order[j + 1]][m] == cands[order[i]][m]:
                j += 1
            val = 1.0 - (i + j) / 2.0 / n if float(cands[order[i]][m] or 0) > 0 else 0.0
            for k in order[i:j + 1]:
                score[k] += W[m] * val
            i = j + 1
    return score


def _reasons(c, S):
    en, hi = [], []
    if c["arrival"]:
        en.append("received %s, not counted since" % dmy(c["arrival_day"])); hi.append("abhi aaya (%s)" % dmy(c["arrival_day"]))
    if c["loss"]:
        en.append("short at the last count (%s)" % qw(c["loss"], c["pack"], c["packing"], c["item"])); hi.append("pichhli ginti mein kam tha")
    if c["turnover"] >= 0:
        en.append("sells %s a day" % qw(max(0, round(c["movement"] * c["pack"] if c["pack"] > 1 else c["movement"])), c["pack"], c["packing"], c["item"]) if c["movement"] * (c["pack"] if c["pack"] > 1 else 1) >= 1 else "sells slowly")
        hi.append("bikri tez" if c["movement"] >= 1 else "bikri kam")
    if c["value"]:
        en.append("costly (%s a %s)" % (rs(c["mrp_p"]), "strip" if c["pack"] > 1 else "pc")); hi.append("mehnga")
    if c["stale"] >= 30:
        en.append("%d days since it was counted" % c["stale"]); hi.append("%d din se nahi gina" % c["stale"])
    return " · ".join(en[:3]), " · ".join(hi[:3])


def build_roster(con, day=None, S=None, sp=None, who="system", force=False):
    """The day's roster: the owner's asks first, then yesterday's unanswered (carried), then the ranked items up to the
    cap; nothing counted within repeat_gap_days unless asked; a seeded tie-break so two runs agree. Written once per day."""
    ensure(con)
    S = S or settings(con)
    sp = sp or Spine()
    d = day or today()
    diso = d.isoformat()
    if con.execute("SELECT COUNT(*) FROM stock_spot_roster WHERE day=?", (diso,)).fetchone()[0] and not force:
        return roster_view(con, d, S, sp)
    if not force and not _spot_day(S, d):
        return roster_view(con, d, S, sp)
    ts = now_iso()
    chosen = []
    # 1 -- the owner's asks
    for r in con.execute("SELECT id, item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL ORDER BY id").fetchall():
        info = item_info(con, sp, r[1])
        chosen.append(dict(item=info["item"], pack=info["pack"], packing=info["packing"], reason="you asked for it", reason_hi="Doctor sahab ne kaha", ask_id=r[0], carried=0))
    # 2 -- carried from the last roster day (unanswered)
    prev = con.execute("SELECT day FROM stock_spot_roster WHERE day<? ORDER BY day DESC LIMIT 1", (diso,)).fetchone()
    if prev:
        for r in con.execute("SELECT item, pack, packing, reason, reason_hi FROM stock_spot_roster WHERE day=? AND answered_at IS NULL ORDER BY rank", (prev[0],)).fetchall():
            if not any(x["item"] == r[0] for x in chosen):
                chosen.append(dict(item=r[0], pack=r[1], packing=r[2], reason=(r[3] or "") + " · carried from %s" % dmy(prev[0]), reason_hi=(r[4] or "") + " · %s se baaki" % dmy(prev[0]), ask_id=None, carried=1))
    # 3 -- the ranked items
    cap = S["cap"]
    if cap > 0 and sp.ok:
        cands = _candidates(con, sp, S)
        gap_from = (d - dt.timedelta(days=S["repeat_gap_days"])).isoformat()
        recent = {r[0] for r in con.execute("SELECT DISTINCT item_norm FROM stock_point WHERE at>=?", (gap_from,))}
        recent |= {norm_name(r[0]) for r in con.execute("SELECT item FROM stock_spot_roster WHERE day>=? AND day<?", (gap_from, diso))}
        pool = {k: c for k, c in cands.items() if c["countable"] and norm_name(c["item"]) not in recent and not any(norm_name(x["item"]) == norm_name(c["item"]) for x in chosen)}
        sc = _rank_scores(pool, S)
        seed_ = lambda k: hashlib.md5((diso + "|" + k).encode("utf-8")).hexdigest()   # noqa: E731
        for k in sorted(pool, key=lambda k: (-sc[k], seed_(k))):
            if len([x for x in chosen if not x.get("ask_id")]) >= cap:
                break
            c = pool[k]
            en, hi = _reasons(c, S)
            chosen.append(dict(item=c["item"], pack=c["pack"], packing=c["packing"], reason=en, reason_hi=hi, ask_id=None, carried=0, score=round(sc[k], 3)))
    for i, x in enumerate(chosen, 1):
        rid = con.execute("INSERT INTO stock_spot_roster (day, item_norm, item, reason, reason_hi, rank, asked_at, pack, packing, carried) VALUES (?,?,?,?,?,?,?,?,?,?)",
                          (diso, norm_name(x["item"]), x["item"], x["reason"], x["reason_hi"], i, ts, x["pack"], x["packing"], x.get("carried", 0))).lastrowid
        if x.get("ask_id"):
            con.execute("UPDATE stock_watch_ask SET roster_id=? WHERE id=?", (rid, x["ask_id"]))
    _audit(con, "roster", dict(day=diso, items=[x["item"] for x in chosen]), who)
    con.commit()
    # three misses in a week -> one Needs-you line
    wk = (d - dt.timedelta(days=7)).isoformat()
    misses = con.execute("SELECT COUNT(DISTINCT day) FROM stock_spot_roster WHERE day>=? AND day<? AND answered_at IS NULL", (wk, diso)).fetchone()[0]
    if misses >= 3:
        notice(con, "spot_missed", "owner", "Spot counts: Darpan left the morning list unanswered on %d of the last 7 days" % misses, once_key="spot_missed:%s" % diso, days=7)
        con.commit()
    return roster_view(con, d, S, sp)


def roster_view(con, day=None, S=None, sp=None):
    S = S or settings(con)
    d = day or today()
    rows = [dict(id=r[0], day=r[1], item=r[2], reason=r[3] or "", reason_hi=r[4] or "", rank=r[5], asked_at=r[6], answered_at=r[7], qty=r[8], point_id=r[9], pack=int(r[10] or 1),
                 packing=r[11] or "", carried=int(r[12] or 0), whole_hi=_qwm().whole_word(r[11] or "", None, r[2], int(r[10] or 1), "hi"),
                 qty_hi=(qw(r[8], int(r[10] or 1), r[11] or "", r[2], "hi") if r[8] is not None else ""))
            for r in con.execute("SELECT id, day, item, reason, reason_hi, rank, asked_at, answered_at, qty_units, point_id, pack, packing, carried FROM stock_spot_roster WHERE day=? ORDER BY rank", (d.isoformat(),))]
    for x in rows:
        if x["point_id"]:
            p = con.execute("SELECT gap_units, status, note FROM stock_point WHERE id=?", (x["point_id"],)).fetchone()
            x["gap"] = p[0] if p else None
    return dict(day=d.isoformat(), day_text=dmy(d.isoformat()), is_spot_day=_spot_day(S, d), items=rows, open=sum(1 for x in rows if not x["answered_at"]), cap=S["cap"])


def next_roster_day(S, d=None):
    d = d or today()
    for i in range(1, 8):
        x = d + dt.timedelta(days=i)
        if _spot_day(S, x):
            return x
    return None


def preview_roster(con, day, S=None, sp=None):
    """What the job WOULD write for a day (no write) -- for the owner's card and the report."""
    S = S or settings(con)
    sp = sp or Spine()
    out = []
    for r in con.execute("SELECT item FROM stock_watch_ask WHERE done_at IS NULL AND roster_id IS NULL ORDER BY id"):
        out.append(dict(item=r[0], reason="you asked for it"))
    if S["cap"] > 0 and sp.ok:
        cands = _candidates(con, sp, S)
        gap_from = (day - dt.timedelta(days=S["repeat_gap_days"])).isoformat()
        recent = {r[0] for r in con.execute("SELECT DISTINCT item_norm FROM stock_point WHERE at>=?", (gap_from,))}
        recent |= {norm_name(r[0]) for r in con.execute("SELECT item FROM stock_spot_roster WHERE day>=?", (gap_from,))}
        pool = {k: c for k, c in cands.items() if c["countable"] and norm_name(c["item"]) not in recent}
        sc = _rank_scores(pool, S)
        seed_ = lambda k: hashlib.md5((day.isoformat() + "|" + k).encode("utf-8")).hexdigest()   # noqa: E731
        n = 0
        for k in sorted(pool, key=lambda k: (-sc[k], seed_(k))):
            if n >= S["cap"]:
                break
            en, hi = _reasons(pool[k], S)
            out.append(dict(item=pool[k]["item"], reason=en, reason_hi=hi, score=round(sc[k], 3)))
            n += 1
    return out


def answer_roster(con, roster_id, qty_units, who, sp=None):
    """Darpan's 'Bhej do' on one item of the day's roster -> a spot point."""
    r = con.execute("SELECT id, item, day, answered_at FROM stock_spot_roster WHERE id=?", (int(roster_id),)).fetchone()
    if not r:
        return False, "Yeh item aaj ki list mein nahi hai.", 404, None
    if r[3]:
        return True, "Pehle hi likha hai.", 200, None
    P = write_point(con, r[1], qty_units, "spot", who, roster_id=r[0], sp=sp)
    con.execute("UPDATE stock_spot_roster SET answered_at=?, qty_units=?, point_id=? WHERE id=?", (now_iso(), float(qty_units), P["id"], r[0]))
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE roster_id=? AND done_at IS NULL", (now_iso(), r[0]))
    con.commit()
    return True, "Likh liya: %s — %s. %s" % (r[1], P["qty_hi"], P["verdict_hi"]), 200, P


def ask(con, item, who, sp=None):
    """The owner's 'Count this' -> the head of the next roster."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    if not info["item"]:
        return False, "Name the item.", 400
    if con.execute("SELECT id FROM stock_watch_ask WHERE item_norm=? AND done_at IS NULL", (norm_name(info["item"]),)).fetchone():
        return True, "%s is already on the next list." % info["item"], 200
    con.execute("INSERT INTO stock_watch_ask (item_norm, item, by, at) VALUES (?,?,?,?)", (norm_name(info["item"]), info["item"], who, now_iso()))
    _audit(con, "ask", dict(item=info["item"]), who)
    con.commit()
    return True, "%s goes at the head of Darpan's next morning list." % info["item"], 200


def darpan_point(con, item, qty_units, who, sp=None):
    """'Stock batao' -- any item, any day: a darpan point, counted like a spot answer."""
    sp = sp or Spine()
    info = item_info(con, sp, item)
    if not (sp.ok and sp.item(item)) and not con.execute("SELECT 1 FROM stock_snapshot WHERE item=? LIMIT 1", (item,)).fetchone():
        return False, "Yeh item nahi mila.", 404, None
    P = write_point(con, info["item"], qty_units, "darpan", who, sp=sp)
    con.execute("UPDATE stock_watch_ask SET done_at=? WHERE item_norm=? AND done_at IS NULL", (now_iso(), norm_name(info["item"])))
    con.commit()
    return True, "Likh liya: %s — %s. %s" % (info["item"], P["qty_hi"], P["verdict_hi"]), 200, P


def gadbad(con, item, text, who, qty_units=None, sp=None):
    """'Kuchh gadbad hai' -- Darpan flags an unusual loss: what he sees (free text), his count if he gives one -> a loss
    point (when counted) and THE TRACE from the last clean point to now."""
    sp = sp or Spine()
    info = item_info(con, sp, item)
    if not (sp.ok and sp.item(item)) and not con.execute("SELECT 1 FROM stock_snapshot WHERE item=? LIMIT 1", (item,)).fetchone():
        return False, "Yeh item nahi mila.", 404, None
    t = re.sub(r"\s+", " ", str(text or "")).strip()[:500]
    P = None
    if qty_units is not None:
        P = write_point(con, info["item"], qty_units, "darpan", who, note="gadbad: " + t, sp=sp, silent=True)
        gap = P["gap"]
    else:
        gap = None
    T = open_trace(con, info["item"], "darpan", gap, who, sp=sp, note=t, point_id=(P["id"] if P else None))
    return True, "Likh liya -- system dekh raha hai (%s)." % T["verdict_hi"], 200, dict(point=P, trace=T)


# ------------------------------------------------------------------ 3.5 the trace
def _edit_distance(a, b):
    if abs(len(a) - len(b)) > 2:
        return 3
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def open_trace(con, item, trigger, gap_units, who, sp=None, note=None, point_id=None, count_id=None):
    """Rebuild from the anchor (the last settled point with gap 0, else the last closed full count) to now and run the
    seven checks in order; each explains the gap exactly, in part, or is ruled out. Verdict explained / partly /
    unexplained. The fix is one line for Amir. Unexplained -> Needs you the same day."""
    ensure(con)
    sp = sp or Spine()
    info = item_info(con, sp, item)
    item = info["item"]; pack, packing = info["pack"], info["packing"]
    nm = norm_name(item)
    t = today().isoformat()
    anchor = last_point(con, nm, settled_only=True, gap_zero=True)
    fc = last_full_count(con)
    if anchor:
        anchor_at, anchor_text = anchor["at"], "the point of %s (%s, matched the records)" % (stamp(anchor["at"]), POINT_SOURCE_HI.get(anchor["source"], anchor["source"]))
    elif fc:
        anchor_at, anchor_text = fc["as_on"] + "T00:00:00", "the full count of %s" % dmy(fc["as_on"])
    else:
        anchor_at, anchor_text = (today() - dt.timedelta(days=90)).isoformat() + "T00:00:00", "90 days back (no count on record)"
    w_from = anchor_at[:10]
    gap = None if gap_units is None else float(gap_units)
    if gap is None:
        E = expected_units(con, sp, item)
        lp = last_point(con, nm)
        if lp and lp["expected"] is not None and lp["at"] >= anchor_at:
            gap = float(lp["gap"] or 0)
        else:
            gap = 0.0
    need = abs(gap)
    findings, fixes, explained = [], [], 0.0
    purch = sp.purchases(item, w_from, t, incl_from=True) if sp.ok else []
    sales = sp.sales(item, w_from, t, incl_from=True) if sp.ok else dict(u=0, ret=0, v=0, n=0)
    arrivals = _arrivals(con, item, w_from, sp)
    # 1 -- the same purchase bill twice (supplier + bill + qty)
    seen, dup_units = {}, 0.0
    for p in purch:
        if p["direction"] == "RETURN":
            continue
        k = (p["supkey"], str(p["bill"]).strip(), float(p["qty"] or 0), float(p["units"] or 0))
        if k in seen:
            dup_units += float(p["units"] or 0)
            fixes.append("bill %s (%s) do baar: ek hataayein" % (p["bill"], p["supkey"]))
        seen[k] = p
    findings.append(dict(n=1, check="the same purchase bill twice", ok=(dup_units == 0), explains=dup_units if (gap < 0 and dup_units) else 0.0,
                         text=("bill entered twice: %s counted twice in Marg" % qw(dup_units, pack, packing, item)) if dup_units else "no bill appears twice"))
    # 2 -- an arrival tapped, no entry (the stock is here, Marg does not have it: a surplus explanation)
    tapped_no_entry = sum(a["units"] for a in arrivals if not a["in_spine"])
    findings.append(dict(n=2, check="an arrival tapped, no purchase entry", ok=(tapped_no_entry == 0), explains=tapped_no_entry if (gap > 0 and tapped_no_entry) else 0.0,
                         text=("%s tapped as arrived, not yet entered in Marg (%s)" % (qw(tapped_no_entry, pack, packing, item), ", ".join(sorted({a["vendor"] for a in arrivals if not a["in_spine"]})))) if tapped_no_entry else "every tapped arrival is in Marg"))
    if tapped_no_entry and gap > 0:
        fixes.append("arrival tapped, bill entry baaki: %s" % ", ".join(sorted({a["vendor"] for a in arrivals if not a["in_spine"]})))
    # 3 -- a pack-multiple gap (x pack_size, x10 / x15 strip confusion, boxes read as strips)
    pm = None
    if need and pack > 1:
        for p in purch:
            q = float(p["qty"] or 0)
            for mult, why in ((pack, "boxes read as strips: %g strips x %d" % (q, pack)), (15 if pack == 10 else 10, "a %d-strip pack entered as %d" % (pack, 15 if pack == 10 else 10))):
                if q and abs(q * mult - need) < 0.5 or (q and abs(q * (mult - pack) - need) < 0.5):
                    pm = dict(units=need, text="a pack-multiple gap -- %s (bill %s)" % (why, p["bill"]), fix="bill %s: %s -- Marg mein sudhaarein" % (p["bill"], why))
                    break
            if pm:
                break
        if not pm and need % pack == 0 and need <= 5 * pack:
            pm = dict(units=0.0, text="the gap is exactly %d whole strips -- a strip miscounted as a box?" % int(need // pack), fix=None)
    findings.append(dict(n=3, check="a pack-multiple gap", ok=(pm is None), explains=(pm["units"] if pm else 0.0), text=(pm["text"] if pm else "not a pack multiple")))
    if pm and pm.get("fix"):
        fixes.append(pm["fix"])
    # 4 -- a twin item: an alias, or a name within edit distance 2 / the same salt, with a mirror-image surplus
    twin = None
    if sp.ok and need:
        salt = sp.salt(item)
        k20 = sp.key(item)
        alias_twins = [a for a, k in sp._alias.items() if k == k20 and a != k20]
        cands = []
        for it in sp.items():
            if it["k20"] == k20:
                continue
            if _edit_distance(it["k20"], k20) <= 2 or (salt and sp.salt(it["name"]) == salt):
                cands.append(it["name"])
        mirror = None
        for nm2 in cands[:40]:
            lp2 = last_point(con, norm_name(nm2))
            if lp2 and lp2["gap"] and lp2["at"] >= anchor_at and abs(float(lp2["gap"]) + gap) < 0.5:
                mirror = (nm2, lp2["gap"]); break
            if fc:
                r = con.execute("SELECT diff FROM stock_diff WHERE count_id=? AND item=? AND diff>0", (fc["count_id"], nm2)).fetchone()
                if r and abs(float(r[0]) + gap) < 0.5:
                    mirror = (nm2, float(r[0])); break
        if mirror:
            twin = dict(units=need, text="a twin: %s is %s over -- one billed for the other" % (mirror[0], qw(mirror[1], pack, packing, mirror[0])), fix="%s aur %s: ek ka bill doosre par -- Marg mein adla-badli" % (item, mirror[0]))
        elif alias_twins or cands:
            twin = dict(units=0.0, text="near names: %s -- no mirror surplus found" % ", ".join((alias_twins + cands)[:3]), fix=None)
    findings.append(dict(n=4, check="a twin item", ok=(twin is None or twin["units"] == 0), explains=(twin["units"] if twin else 0.0), text=(twin["text"] if twin else "no twin")))
    if twin and twin.get("fix"):
        fixes.append(twin["fix"])
    # 5 -- scheme strips on a bill not entered (free qty)
    free_units = sum(float(p["free"] or 0) * (pack if pack > 1 else 1) for p in purch if p["direction"] != "RETURN")
    findings.append(dict(n=5, check="scheme strips on a bill", ok=(free_units == 0), explains=(free_units if (gap > 0 and abs(free_units - need) < 0.5) else 0.0),
                         text=("%s free on the bills in the window" % qw(free_units, pack, packing, item)) if free_units else "no scheme quantity on the bills"))
    # 6 -- short delivery (tap < bill)
    sd = [a for a in arrivals if a["billed_qty"] is not None and int(a["billed_qty"]) > int(a["supplied"])]
    sd_units = sum((int(a["billed_qty"]) - int(a["supplied"])) * a["pack_size"] for a in sd)
    findings.append(dict(n=6, check="short delivery (tap under the bill)", ok=(not sd), explains=(sd_units if (gap < 0 and sd_units) else 0.0),
                         text=("; ".join("%s: bill %s, tapped %s" % (a["vendor"], qw(int(a["billed_qty"]) * a["pack_size"], pack, packing, item), qw(a["supplied"] * a["pack_size"], pack, packing, item)) for a in sd)) if sd else "no short delivery"))
    if sd and gap < 0:
        fixes.append("short delivery -- %s se poochhein" % ", ".join(sorted({a["vendor"] for a in sd})))
    # 7 -- a mistyped point (x10 off its neighbours)
    lp = last_point(con, nm)
    mist = None
    if lp and lp["expected"] and lp["expected"] > 0 and lp["qty"] is not None:
        ratio = float(lp["qty"]) / float(lp["expected"])
        if 8.0 <= ratio <= 12.0 or (ratio and 1 / 12.0 <= ratio <= 1 / 8.0):
            mist = "the last point (%s) is about %s the records' figure (%s) -- a typing slip?" % (qw(lp["qty"], pack, packing, item), "ten times" if ratio > 1 else "a tenth of", qw(lp["expected"], pack, packing, item))
    findings.append(dict(n=7, check="a mistyped point", ok=(mist is None), explains=0.0, text=(mist or "the points are of a size")))
    explained = sum(f["explains"] for f in findings)
    if need == 0:
        verdict = "explained"
    elif explained >= need - 0.5:
        verdict = "explained"
    elif explained > 0 or mist or (twin and twin["units"] == 0 and False):
        verdict = "partly"
    else:
        verdict = "unexplained"
    window_to = t
    fix = dict(lines=fixes, for_amir=(fixes[0] if fixes else ""))
    ts = now_iso()
    cur = con.execute("INSERT INTO stock_trace (item_norm, item, opened_at, trigger, anchor_at, window_from, window_to, gap_units, verdict, findings_json, fix_json, status, count_id, pack, packing) "
                      "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                      (nm, item, ts, trigger, anchor_at, w_from, window_to, gap, verdict, json.dumps(dict(anchor=anchor_text, findings=findings, sales=float(sales["u"] or 0), returns=float(sales.get("ret") or 0),
                                                                                                        purchases=sum(float(p["units"] or 0) for p in purch if p["direction"] != "RETURN"), note=note or "", point_id=point_id)),
                       json.dumps(fix), "open", count_id, pack, packing))
    tid = int(cur.lastrowid)
    _audit(con, "trace", dict(item=item, trigger=trigger, gap=gap, verdict=verdict, fixes=fixes, text="%s: trace %s -- %s" % (item, verdict, "; ".join(f["text"] for f in findings if not f["ok"])[:200])), who, tid)
    if verdict == "unexplained" and need:
        notice(con, "trace_unexplained", "owner", "%s: %s short, unexplained -- between %s and %s nothing in the records accounts for it" % (item, qw(need, pack, packing, item), dmy(w_from), dmy(window_to)),
               once_key="trace:%d" % tid, days=7, ref=str(tid))
        n_un = con.execute("SELECT COUNT(*) FROM stock_trace WHERE item_norm=? AND verdict='unexplained' AND opened_at>=?", (nm, (today() - dt.timedelta(days=30)).isoformat())).fetchone()[0]
        if n_un >= 2:
            notice(con, "close_watch", "owner", "%s joins the close-watch list: two unexplained traces within a month" % item, once_key="close_watch:%s:%s" % (nm, t[:7]), days=30, ref=nm)
    con.commit()
    return trace_view(con, tid)


def trace_view(con, tid):
    r = con.execute("SELECT id, item, opened_at, trigger, anchor_at, window_from, window_to, gap_units, verdict, findings_json, fix_json, status, seen_by, seen_at, pack, packing FROM stock_trace WHERE id=?", (int(tid),)).fetchone()
    if not r:
        return None
    F = json.loads(r[9] or "{}"); X = json.loads(r[10] or "{}")
    pack, packing = int(r[14] or 1), r[15] or ""
    gap = r[7]
    entry_error = any(f["explains"] > 0 for f in F.get("findings", []) if f["n"] in (1, 2, 3, 5, 6))
    return dict(id=r[0], item=r[1], opened_at=r[2], opened_text=stamp(r[2]), trigger=r[3], anchor_at=r[4], anchor_text=F.get("anchor", ""), window_from=r[5], window_to=r[6],
                window_text="%s to %s" % (dmy(r[5]), dmy(r[6])), gap=gap, gap_text=("" if gap is None else ("%s %s" % (qw(abs(gap), pack, packing, r[1]), "short" if gap < 0 else "over"))),
                gap_hi=("" if gap is None else ("%s %s" % (qw(abs(gap), pack, packing, r[1], "hi"), "kam" if gap < 0 else "zyada"))),
                verdict=r[8], verdict_text={"explained": "explained", "partly": "partly explained", "unexplained": "unexplained"}.get(r[8], r[8]),
                verdict_hi={"explained": "wajah mil gayi", "partly": "aadhi wajah mili", "unexplained": "wajah nahi mili"}.get(r[8], r[8]),
                findings=F.get("findings", []), sales=F.get("sales"), purchases=F.get("purchases"), returns=F.get("returns"), note=F.get("note") or "",
                fix=X.get("for_amir") or "", fixes=X.get("lines") or [], status=r[11], seen_by=r[12] or "", seen_at=r[13] or "", entry_error=entry_error,
                darpan_text=("Aapki baat sahi thi -- entry ki galti thi" if (entry_error and r[3] == "darpan") else ("Dekh liya" if r[11] != "open" else "")))


def traces(con, limit=30, item=None):
    q = "SELECT id FROM stock_trace" + (" WHERE item_norm=?" if item else "") + " ORDER BY id DESC LIMIT ?"
    args = ((norm_name(item), int(limit)) if item else (int(limit),))
    return [trace_view(con, r[0]) for r in con.execute(q, args)]


def trace_seen(con, tid, who):
    r = con.execute("SELECT id, status FROM stock_trace WHERE id=?", (int(tid),)).fetchone()
    if not r:
        return False, "Nahi mila.", 404
    if r[1] == "open":
        con.execute("UPDATE stock_trace SET status='seen', seen_by=?, seen_at=? WHERE id=?", (who, now_iso(), r[0]))
        _audit(con, "trace_seen", dict(trace=r[0]), who, r[0])
        con.commit()
    return True, "Dekh liya.", 200


def trace_big_losses(con, root, lines, who="system", sp=None):
    """A trace on every Big-loss line of the desk -- once per item per 30 days. Never raises."""
    try:
        ensure(con)
        sp = sp or Spine()
        since = (today() - dt.timedelta(days=30)).isoformat()
        done = {r[0] for r in con.execute("SELECT DISTINCT item_norm FROM stock_trace WHERE opened_at>=? AND trigger='big_loss'", (since,))}
        n = 0
        for l in lines:
            if l.get("bucket") != "bigloss" or norm_name(l["item"]) in done:
                continue
            open_trace(con, l["item"], "big_loss", -float(l.get("short_units") or 0), who, sp=sp, count_id=root)
            n += 1
            if n >= 40:
                break
        return n
    except Exception:                                         # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        return 0


# ------------------------------------------------------------------ 3.6 leakage and the watch list
def month_leak(con, ym, S=None, sp=None):
    """Leakage of a month: loss points (gap < 0, at cost) + count write-offs (allowance, small, big at cost) dated in the
    month, against the month's sales (spine, at sale value). None when nothing can be read."""
    S = S or settings(con)
    sp = sp or Spine()
    ensure(con)
    loss_p = 0
    try:
        for r in con.execute("SELECT id, item, gap_units, at FROM stock_point WHERE substr(at,1,7)=? AND gap_units<0", (ym,)):
            cost = None
            try:
                cost = _sa()._value_p(con, r[1], int(round(float(r[2]))))
            except Exception:                                 # noqa: BLE001 -- no rate on record: the spine's MRP stands in
                cost = None
            if cost:
                loss_p += abs(int(cost))
            else:
                mrp = sp.mrp_p(r[1]) if sp.ok else None
                info = item_info(con, sp, r[1])
                loss_p += int(round((mrp or 0) / max(1, info["pack"]) * abs(float(r[2])))) if mrp else 0
        for r in con.execute("SELECT r.groups, c.marg_as_on FROM stock_writeoff_run r JOIN stock_count c ON c.id=r.count_id"):
            if dmy_to_iso(r[1])[:7] != ym:
                continue
            g = json.loads(r[0])
            loss_p += sum((x.get("cost_p") or x.get("mrp_p") or 0) for k in ("allowance", "small", "big") for x in g.get(k, []))
    except Exception:                                         # noqa: BLE001
        return None
    sales_p = sp.sales_month(ym) if sp.ok else 0
    if not sales_p:
        return dict(ym=ym, loss_p=loss_p, sales_p=0, pct=None, red=False, text="Leakage %s -- no sales on record for the month" % rs(loss_p), budget_pct=S["budget_pct"])
    pct = 100.0 * loss_p / sales_p
    red = pct > S["budget_pct"]
    return dict(ym=ym, loss_p=loss_p, sales_p=sales_p, pct=round(pct, 2), red=red, budget_pct=S["budget_pct"],
                text="Leakage %s = %.1f%% of sales · budget %g%%" % (rs(loss_p), pct, S["budget_pct"]), cls=("red" if red else "green"))


def leak_needs_you(con, S=None, sp=None):
    S = S or settings(con)
    sp = sp or Spine()
    t = today()
    reds = 0
    ym = t.strftime("%Y-%m")
    months = []
    for i in range(S["red_periods"]):
        m = (t.replace(day=1) - dt.timedelta(days=30 * i)).strftime("%Y-%m")
        months.append(m)
    for m in months:
        L = month_leak(con, m, S, sp)
        if L and L.get("pct") is not None and L["red"]:
            reds += 1
    if reds >= S["red_periods"]:
        return [dict(cls="bad", target="stock", text="Leakage over the %g%% budget for %d months running (%s)" % (S["budget_pct"], reds, ", ".join(dmy(m + "-01")[3:] for m in months)))]
    return []


def watch_list(con, S=None, sp=None, root=None):
    """Top spot.watch_size by sales value (90 d) + MRP >= high_value + short at two closed counts (or close-watch by
    two unexplained traces): item, the last three points in strips words, gaps, a monthly trend, Count this."""
    S = S or settings(con)
    sp = sp or Spine()
    if not sp.ok:
        return []
    t = today()
    d90 = (t - dt.timedelta(days=90)).isoformat()
    picked, names = [], set()
    # first the items that earned the watch: two unexplained traces within a month; short at the last two closed counts
    for r in con.execute("SELECT DISTINCT ref FROM stock_watch_notice WHERE kind='close_watch' AND until>=?", (t.isoformat(),)):
        it = con.execute("SELECT item FROM stock_trace WHERE item_norm=? ORDER BY id DESC LIMIT 1", (r[0],)).fetchone()
        if it and r[0] not in names:
            picked.append((it[0], "two unexplained traces within a month", 0)); names.add(r[0])
    closed = [r[0] for r in con.execute("SELECT c.id FROM stock_count c JOIN stock_count_close k ON k.count_id=c.id WHERE c.id NOT IN (SELECT count_id FROM stock_count_part) ORDER BY c.id DESC LIMIT 2")]
    if len(closed) >= 2:
        a = {r[0] for r in con.execute("SELECT item FROM stock_diff WHERE count_id=? AND diff<0", (closed[0],))}
        b = {r[0] for r in con.execute("SELECT item FROM stock_diff WHERE count_id=? AND diff<0", (closed[1],))}
        for nm2 in sorted(a & b):
            if norm_name(nm2) not in names:
                picked.append((nm2, "short at the last two counts", 0)); names.add(norm_name(nm2))
    # then the top items by sales value, then the costly ones, up to the size
    rows = sp.q("SELECT k20, COALESCE(SUM(rate_p*units/NULLIF(CASE WHEN pack LIKE '1*%' THEN CAST(substr(pack,3) AS REAL) ELSE 1 END,0)),0) AS v "
                "FROM sp_sale_line WHERE date>=? GROUP BY k20 ORDER BY v DESC LIMIT ?", d90, S["watch_size"])
    for r in rows:
        it = sp.q("SELECT name FROM sp_item WHERE k20=? ORDER BY last_seen DESC LIMIT 1", r["k20"])
        if it and norm_name(it[0]["name"]) not in names:
            picked.append((it[0]["name"], "top by sales value", int(r["v"] or 0))); names.add(norm_name(it[0]["name"]))
    for it in sp.items():
        if len(picked) >= S["watch_size"] + 20:
            break
        m = sp.mrp_p(it["name"])
        if m and m >= S["high_value_p"] and norm_name(it["name"]) not in names:
            picked.append((it["name"], "costly (%s a %s)" % (rs(m), "strip" if pack_of(it["packing"]) > 1 else "pc"), 0)); names.add(norm_name(it["name"]))
    out = []
    for name, why, v in picked:
        info = item_info(con, sp, name)
        pts = [dict(at=p[0], at_text=dmy(p[0][:10]), qty=p[1], gap=p[2], source=p[3], qty_text=qw(p[1], info["pack"], info["packing"], name),
                    gap_text=("" if p[2] is None else ("%s %s" % (qw(abs(p[2]), info["pack"], info["packing"], name), "short" if p[2] < 0 else ("over" if p[2] > 0 else "= records")))))
               for p in con.execute("SELECT at, qty_units, gap_units, source FROM stock_point WHERE item_norm=? ORDER BY at DESC LIMIT 3", (norm_name(name),))]
        trend = []
        for i in range(2, -1, -1):
            m0 = (t.replace(day=1) - dt.timedelta(days=30 * i)).replace(day=1)
            m1 = (m0 + dt.timedelta(days=32)).replace(day=1)
            s = sp.sales(name, m0.isoformat(), (m1 - dt.timedelta(days=1)).isoformat(), incl_from=True)
            g = con.execute("SELECT COALESCE(SUM(CASE WHEN gap_units<0 THEN -gap_units ELSE 0 END),0) FROM stock_point WHERE item_norm=? AND at>=? AND at<?", (norm_name(name), m0.isoformat(), m1.isoformat())).fetchone()[0]
            trend.append(dict(ym=m0.strftime("%Y-%m"), label=m0.strftime("%b"), sold=qw(s["u"], info["pack"], info["packing"], name), lost=(qw(g, info["pack"], info["packing"], name) if g else "")))
        out.append(dict(item=name, why=why, value_p=v, pack=info["pack"], packing=info["packing"], points=pts, trend=trend, mrp_p=sp.mrp_p(name)))
    return out[:S["watch_size"] + 20]


# ------------------------------------------------------------------ the views
def notices(con, for_who, days=None):
    ensure(con)
    t = today().isoformat()
    return [dict(id=r[0], at=r[1], at_text=stamp(r[1]), kind=r[2], text=r[3], text_hi=r[4] or "", ref=r[5])
            for r in con.execute("SELECT id, at, kind, text, text_hi, ref FROM stock_watch_notice WHERE for_who=? AND until>=? ORDER BY id DESC LIMIT 20", (for_who, t))]


def needs_you_lines(con):
    """The owner's Needs-you lines (sanjeevni_approvals block 14): the confirmed Sunday (or none by the window's end),
    a cadence move, an unexplained trace today, three missed mornings, red leakage months running. Fail-soft."""
    try:
        ensure(con)
        sp = Spine()
        auto_adjust(con, settings(con))                        # may move the cadence: read the settings after it
        S = settings(con)
        out = []
        P = plan_state(con, S)
        p = P.get("plan")
        if p and p["status"] == "confirmed":
            out.append(dict(cls="info", target="stock", text="Full count: Sunday %s (Amir picked, Darpan said yes)" % p["sunday_text"]))
        elif p and p["status"] in ("open", "picked"):
            out.append(dict(cls="warn", target="stock", text="Full count is due (from %s): %s" % (dmy(p["due_from"]), ("Amir picked %s -- Darpan's yes pending" % p["sunday_text"]) if p["sunday"] else "Amir picks a Sunday on his board")))
        for n in notices(con, "owner"):
            if n["kind"] in ("cadence", "plan_lapsed", "trace_unexplained", "spot_missed", "close_watch") and n["at"][:10] >= (today() - dt.timedelta(days=7)).isoformat():
                out.append(dict(cls="warn" if n["kind"] != "close_watch" else "info", target="stock", text=n["text"]))
        out.extend(leak_needs_you(con, S, sp))
        return out
    except Exception:                                         # noqa: BLE001
        return []


def plan_line(con):
    """One line for Shavez's checklist and Darpan's page: the confirmed Sunday, in Hindi."""
    try:
        P = plan_state(con)
        p = P.get("plan")
        if p and p["status"] == "confirmed":
            return dict(ok=True, text_hi="Poori stock ginti: Sunday %s (Amir aur Darpan taiyaar)" % p["sunday_text"], text="Full stock count: Sunday %s" % p["sunday_text"], sunday=p["sunday"])
        if p and p["status"] == "picked":
            return dict(ok=True, text_hi="Poori stock ginti: Amir ne Sunday %s chuna -- Darpan ki haan baaki" % p["sunday_text"], text="Full count: Amir picked %s, Darpan's yes pending" % p["sunday_text"], sunday=p["sunday"])
        if p:
            return dict(ok=True, text_hi="Poori stock ginti due hai -- Amir Sunday chunenge", text="Full count due -- Amir picks a Sunday", sunday=None)
        return dict(ok=True, text_hi="", text="", sunday=None, next_due=P["due_from"])
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, text_hi="", text="", error=str(e)[:120])


def amir_view(con):
    """Amir's board: the Sunday buttons when a count is due, the bill-entry-baaki lines, the traces' fix lines."""
    try:
        ensure(con)
        S = settings(con)
        sp = Spine()
        P = plan_state(con, S)
        fixes = [dict(id=t["id"], item=t["item"], fix=t["fix"], verdict=t["verdict"], at_text=t["opened_text"]) for t in traces(con, 20) if t["fix"] and t["status"] != "fixed"]
        return dict(ok=True, plan=P.get("plan"), due_from=P["due_from"], due=P["due"], last=P["last"], bill_pending=bill_pending_lines(con, S, sp), fixes=fixes,
                    notices=notices(con, "amir"))
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, note=str(e)[:160])


def darpan_view(con, who="darpan"):
    """Stock milaan: today's roster (built on a spot day if the job did not), the plan question, the loss lines under the
    block, the traces to see ('Dekh liya' / 'Aapki baat sahi thi')."""
    try:
        ensure(con)
        S = settings(con)
        sp = Spine()
        R = build_roster(con, today(), S, sp)
        P = plan_state(con, S)
        p = P.get("plan")
        q = None
        if p and p["status"] == "picked":
            q = dict(id=p["id"], sunday=p["sunday"], sunday_text=p["sunday_text"], text_hi="Amir ne poori ginti ke liye Sunday %s chuna hai. Theek hai?" % p["sunday_text"])
        elif p and p["status"] == "confirmed":
            q = dict(id=p["id"], sunday=p["sunday"], sunday_text=p["sunday_text"], text_hi="Poori ginti: Sunday %s -- aapne haan kaha." % p["sunday_text"], confirmed=True)
        losses = [dict(id=r[0], at=r[1], at_text=dmy(r[1][:10]), item=r[2], text_hi="%s: %s %s kam" % ("Aaj" if r[1][:10] == today().isoformat() else dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or "", r[2], "hi")),
                       text="%s: %s %s short" % (dmy(r[1][:10]), r[2], qw(r[3], int(r[4] or 1), r[5] or "", r[2])))
                  for r in con.execute("SELECT id, at, item, gap_units, pack, packing FROM stock_watch_loss_line ORDER BY id DESC LIMIT 12")]
        tr = [t for t in traces(con, 12) if t["trigger"] in ("darpan", "point") and t["status"] == "open"]
        return dict(ok=True, roster=R, plan=q, losses=losses, traces=[dict(id=t["id"], item=t["item"], gap_hi=t["gap_hi"], verdict_hi=t["verdict_hi"], entry_error=t["entry_error"],
                                                                        text_hi=("Aapki baat sahi thi -- entry ki galti thi (%s)" % t["fix"]) if t["entry_error"] else ("%s: %s -- %s" % (t["item"], t["gap_hi"], t["verdict_hi"]))) for t in tr],
                    notices=notices(con, "darpan"), is_spot_day=R["is_spot_day"])
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, note=str(e)[:160])


def owner_view(con, root=None):
    """The owner's watch card on the Loss desk: the plan, today's / the next roster, the watch list, the traces, tap-vs-bill,
    this month's leakage, the settings heading."""
    try:
        ensure(con)
        sp = Spine()
        settle_provisional(con, sp)
        auto_adjust(con, settings(con))                        # may move the cadence: read the settings after it
        S = settings(con)
        P = plan_state(con, S)
        t = today()
        R = roster_view(con, t, S, sp)
        nxt = next_roster_day(S, t)
        ym = t.strftime("%Y-%m")
        return dict(ok=True, plan=P, roster_today=R, next_day=(nxt.isoformat() if nxt else None), next_day_text=(dmy(nxt.isoformat()) if nxt else ""),
                    roster_next=(preview_roster(con, nxt, S, sp) if nxt else []), watch=watch_list(con, S, sp, root), traces=traces(con, 20),
                    tap_vs_bill=tap_vs_bill_lines(con), leak=month_leak(con, ym, S, sp), leak_prev=month_leak(con, (t.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m"), S, sp),
                    settings=settings_view(con), notices=notices(con, "owner"),
                    asks=[dict(id=r[0], item=r[1], by=r[2], at_text=stamp(r[3])) for r in con.execute("SELECT id, item, by, at FROM stock_watch_ask WHERE done_at IS NULL ORDER BY id")],
                    points_n=con.execute("SELECT COUNT(*) FROM stock_point").fetchone()[0], spot_days=S["spot_days"], cap=S["cap"])
    except Exception as e:                                    # noqa: BLE001
        return dict(ok=False, note=str(e)[:160])


def full_count_points(con, root, lines, who="system"):
    """A closed full count writes one point per counted item (source full_count) -- once per count. Never raises."""
    try:
        ensure(con)
        if con.execute("SELECT COUNT(*) FROM stock_point WHERE source='full_count' AND count_id=?", (int(root),)).fetchone()[0]:
            return 0
        as_on = con.execute("SELECT marg_as_on FROM stock_count WHERE id=?", (int(root),)).fetchone()
        ts = (dmy_to_iso(as_on[0]) + "T12:00:00") if as_on else now_iso()
        n = 0
        for r in con.execute("SELECT item, marg_qty, counted_qty FROM stock_count_item WHERE count_id=?", (int(root),)):
            con.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, expected_units, gap_units, status, settled_at, count_id) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (norm_name(r[0]), r[0], ts, float(r[2] or 0), "full_count", who, float(r[1] or 0), float(r[2] or 0) - float(r[1] or 0), "settled", ts, int(root)))
            n += 1
        con.commit()
        return n
    except Exception:                                         # noqa: BLE001
        return 0


# ------------------------------------------------------------------ the job (cron 06:30 IST)
def job(db_path, who="cron"):
    con = sqlite3.connect(db_path, timeout=60)
    ensure(con)
    S = settings(con)
    sp = Spine()
    settle_provisional(con, sp)
    R = build_roster(con, today(), S, sp, who=who)
    P = plan_state(con, S, who=who)
    auto_adjust(con, S, who=who)
    n_bill = len(bill_pending_lines(con, S, sp))
    print("%s stock_watch job: %s%s roster %d item(s) [%s]; plan %s; bill-entry pending %d" % (
        now_iso(), R["day"], "" if R["is_spot_day"] else " (not a spot day)", len(R["items"]), ", ".join(x["item"] for x in R["items"]),
        (P["plan"]["status"] if P.get("plan") else "none due (from %s)" % P["due_from"]), n_bill))
    con.close()
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "job":
        db = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
        if "--db" in args:
            db = args[args.index("--db") + 1]
        sys.exit(job(db))
    print("usage: stock_watch.py job [--db PATH]   (the 06:30 cron job: the day's roster, the plan, the arrivals)")
    sys.exit(2)
